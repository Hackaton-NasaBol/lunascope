"""Genera las capas fijas de elevación y pendiente del polo sur (80°S–90°S) para el globo 3D.

Uso (desde backend/, con el DEM LOLA en <repo>/dem/):
    python scripts/make_layers.py

Escribe en frontend/public/layers/:
    elevation.jpg, slope.jpg   imágenes lat/lon (equirectangulares) de 8192×2048 px
    hillshade.jpg              relieve sombreado en gris (fondo del modo análisis)
    layers.json                rectángulo, leyendas, unidades, fuente y método

Las imágenes llevan un sombreado de relieve suave solo para que se lean en 3D; los colores
codifican la elevación (m, esfera de 1 737 400 m) y la pendiente (°, umbral peligroso 10°).
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lunascope.terrain.dem import get_coarse_dem  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public" / "layers"
WIDTH, HEIGHT = 8192, 2048           # lon −180..180, lat −80..−90
LAT_TOP, LAT_BOTTOM = -80.0, -90.0
HAZARD_SLOPE_DEG = 10.0

# Escala hipsométrica clásica: verde (bajo) → amarillo → naranja → rojo (alto).
ELEVATION_STOPS = ["#006837", "#1a9850", "#66bd63", "#a6d96a", "#d9ef8b", "#fee08b", "#fdae61", "#f46d43", "#d73027", "#a50026"]
SLOPE_STOPS = [(0, "#166534"), (5, "#84cc16"), (10, "#facc15"), (15, "#f97316"), (25, "#b91c1c")]


def hex_rgb(h: str) -> np.ndarray:
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)


def ramp(values: np.ndarray, stops: list[tuple[float, str]]) -> np.ndarray:
    xs = np.array([s[0] for s in stops], dtype=np.float32)
    cols = np.stack([hex_rgb(s[1]) for s in stops])
    v = np.clip(values, xs[0], xs[-1])
    return np.stack([np.interp(v, xs, cols[:, k]) for k in range(3)], axis=-1)


def hillshade(z: np.ndarray, res: float, az_deg=315.0, alt_deg=40.0) -> np.ndarray:
    dzdy, dzdx = np.gradient(z, res)
    slope = np.arctan(np.hypot(dzdx, dzdy))
    aspect = np.arctan2(-dzdx, dzdy)
    az, alt = np.radians(az_deg), np.radians(alt_deg)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    return np.clip(hs, 0, 1).astype(np.float32)


def main() -> int:
    t0 = time.time()
    dem = get_coarse_dem()
    res = float(abs(dem.res[0]))
    z = dem.z
    print(f"DEM {dem.path.name}: {z.shape[1]}×{z.shape[0]} px a {res:.0f} m/píxel")

    dzdy, dzdx = np.gradient(z, res)
    slope = np.degrees(np.arctan(np.hypot(dzdx, dzdy))).astype(np.float32)
    del dzdx, dzdy
    hs = hillshade(z, res)

    elev_min, elev_max = (float(v) for v in np.nanpercentile(z, [1, 99]))
    elev_stops = [(elev_min + (elev_max - elev_min) * i / (len(ELEVATION_STOPS) - 1), c)
                  for i, c in enumerate(ELEVATION_STOPS)]

    elev_img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    slope_img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    hill_img = np.zeros((HEIGHT, WIDTH), dtype=np.uint8)
    lons = -180.0 + (np.arange(WIDTH) + 0.5) / WIDTH * 360.0
    chunk = 128
    for r0 in range(0, HEIGHT, chunk):
        rows = np.arange(r0, min(r0 + chunk, HEIGHT))
        lats = LAT_TOP - (rows + 0.5) / HEIGHT * (LAT_TOP - LAT_BOTTOM)
        LON, LAT = np.meshgrid(lons, lats)
        x, y = dem.to_xy.transform(LON, LAT)
        c, r = dem.inv @ (np.asarray(x), np.asarray(y))
        coords = [np.asarray(r) - 0.5, np.asarray(c) - 0.5]
        zz = map_coordinates(z, coords, order=1, mode="nearest")
        ss = map_coordinates(slope, coords, order=1, mode="nearest")
        hh = map_coordinates(hs, coords, order=1, mode="nearest")
        shade_e = (0.45 + 0.55 * hh)[..., None]
        shade_s = (0.7 + 0.3 * hh)[..., None]
        elev_img[rows] = np.clip(ramp(zz, elev_stops) * shade_e, 0, 255).astype(np.uint8)
        slope_img[rows] = np.clip(ramp(ss, SLOPE_STOPS) * shade_s, 0, 255).astype(np.uint8)
        hill_img[rows] = np.clip(40 + 190 * hh, 0, 255).astype(np.uint8)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    Image.fromarray(elev_img).save(OUT_DIR / "elevation.jpg", quality=86, optimize=True)
    Image.fromarray(slope_img).save(OUT_DIR / "slope.jpg", quality=86, optimize=True)
    Image.fromarray(hill_img, "L").save(OUT_DIR / "hillshade.jpg", quality=85, optimize=True)

    hazard_pct = float(np.nanmean(slope > HAZARD_SLOPE_DEG) * 100)
    common = {
        "rectangle": {"west": -180.0, "south": LAT_BOTTOM, "east": 180.0, "north": LAT_TOP},
        "source": f"LRO LOLA, NASA PGDA ({dem.path.name})",
        "resolution_m": res,
        "image_px": [WIDTH, HEIGHT],
        "status": "real",
    }
    meta = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "base": {"id": "hillshade", "name": "Relieve sombreado", "url": "/layers/hillshade.jpg",
                 "method": "Sombreado de relieve del DEM (luz fija, solo para leer la forma del terreno).", **common},
        "layers": [
            {
                "id": "elevation", "name": "Elevación", "url": "/layers/elevation.jpg", "units": "m",
                "legend": [{"value": round(v), "color": c} for v, c in elev_stops],
                "method": "Altura sobre la esfera de 1 737 400 m (percentiles 1–99 % del casquete), con sombreado de relieve.",
                **common,
            },
            {
                "id": "slope", "name": "Pendiente", "url": "/layers/slope.jpg", "units": "°",
                "legend": [{"value": v, "color": c} for v, c in SLOPE_STOPS],
                "threshold": HAZARD_SLOPE_DEG,
                "method": f"Gradiente del DEM a {res:.0f} m/píxel; > {HAZARD_SLOPE_DEG:.0f}° = peligrosa "
                          f"({hazard_pct:.1f} % del casquete).",
                **common,
            },
        ],
    }
    (OUT_DIR / "layers.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    for f in ("elevation.jpg", "slope.jpg", "hillshade.jpg"):
        print(f"{f}: {(OUT_DIR / f).stat().st_size / 1e6:.1f} MB")
    print(f"Listo en {time.time() - t0:.0f} s → {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
