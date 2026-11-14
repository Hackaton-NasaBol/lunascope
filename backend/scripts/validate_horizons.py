"""Validación de la geometría contra JPL Horizons (requiere internet).

Compara el azimut/elevación aparentes del Sol y la Tierra calculados con
lunascope.science (SPICE, sin horizonte) con los de la API de JPL Horizons,
para un observador en la superficie lunar. Escribe docs/validation.md.

Uso (desde backend/):
    python scripts/validate_horizons.py                     # Malapert, 3 días cada 6 h
    python scripts/validate_horizons.py --lat -87.4 --lon -5 --site haworth
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lunascope.science import compute_geometry, loaded_kernel_names, load_kernels, time_grid  # noqa: E402

API = "https://ssd.jpl.nasa.gov/api/horizons.api"
REPO_DIR = Path(__file__).resolve().parents[2]
TOLERANCE_DEG = 0.1


def horizons_az_el(target: str, lat: float, lon: float, alt_km: float,
                   start: datetime, stop: datetime, step: str) -> list[tuple[str, float, float]]:
    params = {
        "format": "json",
        "COMMAND": f"'{target}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'coord@301'",
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{lon:.6f},{lat:.6f},{alt_km:.6f}'",
        "START_TIME": f"'{start:%Y-%m-%d %H:%M}'",
        "STOP_TIME": f"'{stop:%Y-%m-%d %H:%M}'",
        "STEP_SIZE": f"'{step}'",
        "QUANTITIES": "'4'",            # azimut y elevación aparentes
        "ANG_FORMAT": "'DEG'",
        "APPARENT": "'AIRLESS'",
        "CSV_FORMAT": "'YES'",
        "EXTRA_PREC": "'YES'",
        "TIME_DIGITS": "'MINUTES'",
    }
    url = API + "?" + urllib.parse.urlencode(params, safe="'@,")
    with urllib.request.urlopen(url, timeout=60) as r:
        data = json.loads(r.read())
    text = data.get("result", "")
    if "$$SOE" not in text:
        raise RuntimeError("Respuesta inesperada de Horizons:\n" + text[:2000])
    rows = []
    for line in text.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines():
        cols = [c.strip() for c in line.split(",")]
        # fecha, marca solar, marca lunar, azimut, elevación
        nums = [c for c in cols[1:] if c and c.replace(".", "", 1).replace("-", "", 1).isdigit()]
        rows.append((cols[0], float(nums[0]), float(nums[1])))
    return rows


def ang_diff(a, b):
    return (np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="malapert")
    ap.add_argument("--lat", type=float, default=-86.0)
    ap.add_argument("--lon", type=float, default=0.0)
    ap.add_argument("--height-m", type=float, default=2.0, help="altura total sobre la esfera de 1737,4 km")
    ap.add_argument("--start", default="2027-09-01T00:00:00Z")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--step-h", type=int, default=6)
    ap.add_argument("--out", default=str(REPO_DIR / "docs" / "validation.md"))
    args = ap.parse_args()

    start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
    stop = start + timedelta(days=args.days)
    load_kernels()
    times, ets = time_grid(start, stop, args.step_h)
    g = compute_geometry(args.lat, args.lon, args.height_m, ets)

    table, max_d = [], {}
    for target, key in (("10", "sun"), ("399", "earth")):
        ref = horizons_az_el(target, args.lat, args.lon, args.height_m / 1000.0, start, stop, f"{args.step_h} h")
        if len(ref) != len(times):
            raise RuntimeError(f"Horizons devolvió {len(ref)} filas, se esperaban {len(times)}")
        az_h = np.array([r[1] for r in ref]); el_h = np.array([r[2] for r in ref])
        daz = ang_diff(g[f"{key}_az"], az_h); del_ = g[f"{key}_el"] - el_h
        # separación angular real (el azimut pesa cos(el))
        sep = np.hypot(daz * np.cos(np.radians(el_h)), del_)
        max_d[key] = (float(np.abs(daz).max()), float(np.abs(del_).max()), float(sep.max()))
        for i, t in enumerate(times):
            table.append((key, t, az_h[i], g[f"{key}_az"][i], el_h[i], g[f"{key}_el"][i], daz[i], del_[i]))

    worst = max(v[2] for v in max_d.values())
    ok = worst < TOLERANCE_DEG
    lines = [
        "# Validación del motor científico contra JPL Horizons",
        "",
        f"Generado automáticamente por `backend/scripts/validate_horizons.py` el "
        f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}.",
        "",
        "## Configuración",
        "",
        f"- Sitio: **{args.site}** — lat {args.lat}°, lon {args.lon}° E, altura {args.height_m} m sobre la esfera de 1 737,4 km.",
        f"- Periodo: {args.start} + {args.days} días, cada {args.step_h} h.",
        "- LunaScope: SPICE (`spkpos`, marco `MOON_ME`, corrección `LT+S` desde el centro lunar), sin máscara de horizonte.",
        f"- Kernels: {', '.join(f'`{k}`' for k in loaded_kernel_names())}.",
        "- Referencia: API de JPL Horizons, observador `coord@301`, cantidad 4 (azimut/elevación aparentes, sin refracción).",
        "",
        "## Resultado",
        "",
        "| Objeto | Δaz máx (°) | Δel máx (°) | Separación angular máx (°) |",
        "|---|---|---|---|",
    ]
    for key, name in (("sun", "Sol"), ("earth", "Tierra")):
        a, e, s = max_d[key]
        lines.append(f"| {name} | {a:.4f} | {e:.4f} | {s:.4f} |")
    lines += [
        "",
        f"**Conclusión:** separación máxima {worst:.4f}° "
        + (f"< {TOLERANCE_DEG}° → ✅ validado." if ok else f"≥ {TOLERANCE_DEG}° → ❌ revisar (marco, signo de longitud, convención de azimut, unidades de altura)."),
        "",
        "> Nota: Δaz se reporta tal cual; cerca del cénit/horizonte la separación angular real es Δaz·cos(el).",
        "> La corrección LT+S se aplica desde el centro de la Luna y no desde el sitio: el error que introduce es muy inferior a 0,01°.",
        "",
        "## Detalle",
        "",
        "| Objeto | Fecha (UTC) | Az Horizons | Az LunaScope | El Horizons | El LunaScope | Δaz | Δel |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for key, t, ah, al, eh, el, da, de in table:
        lines.append(f"| {'Sol' if key == 'sun' else 'Tierra'} | {t:%Y-%m-%d %H:%M} | {ah:.4f} | {al:.4f} | "
                     f"{eh:.4f} | {el:.4f} | {da:+.4f} | {de:+.4f} |")
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[13:19]))
    print(f"\nEscrito {args.out}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

