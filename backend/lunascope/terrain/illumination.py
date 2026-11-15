"""Sombras proyectadas por el relieve, calculadas con el DEM LOLA y el Sol de SPICE.

Para un sitio y un instante:
1. Se toma una ventana del DEM de ±COMPUTE_RADIUS_M alrededor del sitio y se corrige la
   curvatura lunar respecto al plano tangente en el centro: z' = z − d² / (2R).
2. La dirección del Sol (azimut/elevación en el sitio, SPICE) se pasa a la rejilla del DEM con
   los ejes norte/este locales de ``local_axes``.
3. Se remuestrea la ventana girada de modo que la luz viaje a lo largo de las columnas y se
   barre en ese sentido manteniendo la "línea de sombra": un píxel está iluminado si su altura
   supera la sombra que proyecta todo lo que tiene delante (algoritmo de barrido O(N)).
4. Además, el Sol tiene que estar sobre el horizonte geométrico local de cada píxel
   (la elevación del Sol cambia ~1° por cada 30 km de desplazamiento hacia/desde el Sol).
5. El resultado se reproyecta a una rejilla lat/lon (lo que necesita Cesium) y se devuelve como
   PNG: negro semitransparente = sombra, transparente = iluminado.

Limitaciones (se comunican en la interfaz): resolución del DEM (80 m/píxel), relieve más allá de
COMPUTE_RADIUS_M ignorado, Sol tratado como un punto (sin penumbra) y misma dirección del Sol en
toda la ventana salvo la corrección de elevación por curvatura.
"""

from __future__ import annotations

import io
import logging
import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from scipy.ndimage import map_coordinates

from lunascope.terrain.dem import Dem, get_coarse_dem, local_axes

log = logging.getLogger("lunascope.terrain.illumination")

MOON_RADIUS_M = 1_737_400.0
COMPUTE_RADIUS_M = 60_000.0   # relieve que puede proyectar sombra sobre la zona mostrada
DISPLAY_RADIUS_M = 35_000.0   # zona que se pinta alrededor del sitio
OUT_SIZE = 768                # píxeles del PNG (lado)
SUN_RADIUS_DEG = 0.267
SHADOW_RGBA = (2, 6, 23, 185)  # sombra: casi negro, semitransparente


@dataclass
class SiteGrid:
    dem: Dem
    lat: float
    lon: float
    res_m: float
    n: int                       # semiancho de la ventana en píxeles
    zplane: np.ndarray           # ventana con corrección de curvatura (2n+1, 2n+1)
    north_idx: np.ndarray        # vector unitario "norte" en índices (fila, col)
    east_idx: np.ndarray         # vector unitario "este" en índices (fila, col)
    rect: tuple[float, float, float, float]  # oeste, sur, este, norte (grados)
    out_r: np.ndarray            # posición de cada píxel de salida en la ventana (fila, relativa al centro)
    out_c: np.ndarray            # idem columna
    out_mask: np.ndarray         # píxeles de salida dentro de la zona mostrada


def _xy_to_idx_vec(dem: Dem, vx: float, vy: float) -> np.ndarray:
    """Vector en metros (x, y de la proyección) → vector en índices (fila, columna), unitario."""
    a, b, _, d, e, _ = dem.inv.a, dem.inv.b, dem.inv.c, dem.inv.d, dem.inv.e, dem.inv.f
    dc = a * vx + b * vy
    dr = d * vx + e * vy
    v = np.array([dr, dc], dtype=float)
    return v / np.linalg.norm(v)


@lru_cache(maxsize=16)
def site_grid(lat: float, lon: float) -> SiteGrid:
    """Prepara (una vez por sitio) la ventana del DEM y la rejilla lat/lon de salida."""
    dem = get_coarse_dem()
    if not dem.is_inside(lat, lon):
        raise ValueError("outside_dem")
    res = float(abs(dem.res[0]))
    n = int(math.ceil(COMPUTE_RADIUS_M / res))

    x0, y0 = dem.xy(lat, lon)
    c0, r0 = dem.inv @ (x0, y0)
    c0, r0 = c0 - 0.5, r0 - 0.5          # mismo convenio de centro de píxel que Dem.sample
    rr, cc = np.mgrid[-n:n + 1, -n:n + 1].astype(np.float32)
    z = map_coordinates(dem.z, [r0 + rr, c0 + cc], order=1, mode="constant", cval=np.nan)
    d2 = ((rr * res) ** 2 + (cc * res) ** 2)
    zplane = (z - d2 / (2 * MOON_RADIUS_M)).astype(np.float32)

    (_, _), north, east = local_axes(dem, lat, lon)
    north_idx = _xy_to_idx_vec(dem, *north)
    east_idx = _xy_to_idx_vec(dem, *east)

    # Rectángulo lat/lon que contiene el cuadrado mostrado (±DISPLAY_RADIUS_M).
    t = np.linspace(-1, 1, 81) * DISPLAY_RADIUS_M
    edge = np.concatenate([
        np.stack([t, np.full_like(t, -DISPLAY_RADIUS_M)], 1), np.stack([t, np.full_like(t, DISPLAY_RADIUS_M)], 1),
        np.stack([np.full_like(t, -DISPLAY_RADIUS_M), t], 1), np.stack([np.full_like(t, DISPLAY_RADIUS_M), t], 1),
    ])
    elon, elat = dem.to_ll.transform(x0 + edge[:, 0], y0 + edge[:, 1])
    elon = (np.asarray(elon) - lon + 180.0) % 360.0 - 180.0 + lon   # sin saltos en ±180
    west, east_deg = float(elon.min()), float(elon.max())
    south, north_deg = float(np.min(elat)), float(np.max(elat))

    lons = west + (np.arange(OUT_SIZE) + 0.5) / OUT_SIZE * (east_deg - west)
    lats = north_deg - (np.arange(OUT_SIZE) + 0.5) / OUT_SIZE * (north_deg - south)
    LON, LAT = np.meshgrid(lons, lats)
    ox, oy = dem.to_xy.transform(LON, LAT)
    ox, oy = np.asarray(ox), np.asarray(oy)
    oc, orr = dem.inv @ (ox, oy)
    out_r = (np.asarray(orr) - 0.5 - r0).astype(np.float32)
    out_c = (np.asarray(oc) - 0.5 - c0).astype(np.float32)
    out_mask = (np.abs(ox - x0) <= DISPLAY_RADIUS_M) & (np.abs(oy - y0) <= DISPLAY_RADIUS_M)

    log.info("Rejilla de sombras para (%.3f, %.3f): ventana %d px, rectángulo %s", lat, lon, 2 * n + 1,
             (round(west, 3), round(south, 3), round(east_deg, 3), round(north_deg, 3)))
    return SiteGrid(dem, lat, lon, res, n, zplane, north_idx, east_idx,
                    (west, south, east_deg, north_deg), out_r, out_c, out_mask)


def lit_mask(grid: SiteGrid, sun_az_deg: float, sun_el_deg: float) -> np.ndarray:
    """Máscara (OUT_SIZE, OUT_SIZE): 1 iluminado, 0 en sombra, -1 sin datos/fuera de la zona."""
    az, el = math.radians(sun_az_deg), math.radians(sun_el_deg)
    to_sun = grid.north_idx * math.cos(az) + grid.east_idx * math.sin(az)   # (fila, col)
    to_sun /= np.linalg.norm(to_sun)
    light = -to_sun                                  # sentido en que viaja la luz
    perp = np.array([-light[1], light[0]])
    n = grid.n

    # Ventana girada: eje 0 = u (perpendicular), eje 1 = v (sentido de la luz).
    u, v = np.mgrid[-n:n + 1, -n:n + 1].astype(np.float32)
    rows = n + u * perp[0] + v * light[0]
    cols = n + u * perp[1] + v * light[1]
    zrot = map_coordinates(grid.zplane, [rows, cols], order=1, mode="constant", cval=np.nan)

    drop = grid.res_m * math.tan(el)                 # descenso del rayo por píxel recorrido
    lit = np.zeros(zrot.shape, dtype=bool)
    top = np.full(zrot.shape[0], -np.inf, dtype=np.float32)
    for j in range(zrot.shape[1]):
        z = zrot[:, j]
        shadow_line = top - drop
        lit[:, j] = z >= shadow_line - 0.5
        top = np.fmax(z, shadow_line)
    valid = ~np.isnan(zrot)

    # Píxeles de salida → (u, v) en la ventana girada.
    ou = grid.out_r * perp[0] + grid.out_c * perp[1]
    ov = grid.out_r * light[0] + grid.out_c * light[1]
    iu = np.clip(np.rint(ou + n).astype(int), 0, 2 * n)
    iv = np.clip(np.rint(ov + n).astype(int), 0, 2 * n)
    out = np.where(lit[iu, iv], 1, 0).astype(np.int8)
    out[~valid[iu, iv] | ~grid.out_mask] = -1

    # Horizonte geométrico local: acercarse al Sol una distancia s sube su elevación s/R.
    toward_m = (grid.out_r * to_sun[0] + grid.out_c * to_sun[1]) * grid.res_m
    el_local = sun_el_deg + np.degrees(toward_m / MOON_RADIUS_M)
    out[(out == 1) & (el_local < -SUN_RADIUS_DEG)] = 0
    return out


def lit_fraction_at_center(grid: SiteGrid, mask: np.ndarray) -> float | None:
    """Fracción iluminada en un radio de ~3 píxeles alrededor del sitio (para validar con la serie)."""
    d = np.hypot(grid.out_r, grid.out_c)
    sel = (d <= 3) & (mask >= 0)
    return float(mask[sel].mean()) if sel.any() else None


def render_png(mask: np.ndarray) -> bytes:
    from PIL import Image

    rgba = np.zeros(mask.shape + (4,), dtype=np.uint8)
    rgba[mask == 0] = SHADOW_RGBA
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def metadata(grid: SiteGrid) -> dict:
    west, south, east, north = grid.rect
    return {
        "rectangle": {"west": west, "south": south, "east": east, "north": north},
        "resolution_m": grid.res_m,
        "compute_radius_km": COMPUTE_RADIUS_M / 1000,
        "display_radius_km": DISPLAY_RADIUS_M / 1000,
        "image_size_px": OUT_SIZE,
        "dem_source": grid.dem.path.name,
        "method": "Barrido de línea de sombra sobre DEM LOLA con corrección de curvatura; Sol de SPICE.",
        "limitations": [
            f"Relieve a más de {COMPUTE_RADIUS_M / 1000:.0f} km no proyecta sombra en el cálculo.",
            f"Resolución {grid.res_m:.0f} m/píxel: no hay sombras más finas que eso.",
            "Sol como fuente puntual (sin penumbra).",
        ],
    }
