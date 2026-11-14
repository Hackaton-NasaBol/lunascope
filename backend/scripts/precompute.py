"""Regenera backend/data/precomputed/<site_id>/{horizon,terrain,timeseries}.json.

Uso (desde backend/):
    python scripts/precompute.py --start 2027-09-01T00:00:00Z --days 60
    python scripts/precompute.py --site malapert          # solo un sitio
    python scripts/precompute.py --mock                   # fuerza mocks (y sí pisa datos reales)

Si terrain/ o science/ no pueden calcular aquí (sin DEM o sin kernels), conserva los JSON
reales que ya existan y solo calcula el resto: nunca sustituye datos reales por mocks.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402
from app.models import Horizon, Terrain, Timeseries  # noqa: E402
from lunascope import pipeline  # noqa: E402


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def keep_real(path: Path, new: dict, same_window: tuple[str, str] | None = None) -> dict:
    """Si `new` es mock y en disco ya hay un JSON real (de la misma ventana), devuelve el de disco."""
    if new.get("source") != "mock" or not path.exists():
        return new
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return new
    if old.get("source", "real") == "mock":
        return new
    if same_window and (old.get("start"), old.get("end")) != same_window:
        print(f"  aviso: {path.parent.name}/{path.name} real es de otra ventana: se sustituye por mock")
        return new
    print(f"  conservo {path.parent.name}/{path.name} (real); aquí falta su módulo/datos")
    return old


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default=config.fmt_utc(config.MISSION_START))
    ap.add_argument("--days", type=int, default=config.MISSION_DAYS)
    ap.add_argument("--site", action="append", help="id de sitio (repetible); por defecto, todos")
    ap.add_argument("--mock", action="store_true", help="usar mocks aunque existan los módulos reales")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.mock:
        pipeline.TERRAIN = pipeline.SCIENCE = None
    print(f"terrain/: {'REAL' if pipeline.TERRAIN else 'MOCK'}   science/: {'REAL' if pipeline.SCIENCE else 'MOCK'}")

    start = config.parse_utc(args.start)
    end = start + timedelta(days=args.days)
    sites = json.loads(config.SITES_FILE.read_text(encoding="utf-8"))
    if args.site:
        sites = [s for s in sites if s["id"] in args.site]
        if not sites:
            print(f"Ningún sitio coincide con {args.site}", file=sys.stderr)
            return 1

    for site in sites:
        t0 = time.time()
        sid, lat, lon = site["id"], site["lat"], site["lon"]
        out = config.PRECOMPUTED_DIR / sid
        hz = pipeline.horizon(lat, lon, "full", config.OBSERVER_HEIGHT_M, site_id=sid)
        terrain = pipeline.terrain_stats(lat, lon, config.TERRAIN_RADIUS_M, site_id=sid)
        if not args.mock:
            # Cada integrante tiene solo sus datos pesados (DEM o kernels): nunca pisar un JSON
            # real con un mock. Se conserva el real y lo demás se calcula a partir de él.
            hz = keep_real(out / "horizon.json", hz)
            terrain = keep_real(out / "terrain.json", terrain)
        ts = pipeline.timeseries(lat, lon, terrain["elevation_m"] + config.OBSERVER_HEIGHT_M, hz,
                                 start, end, config.STEP_HOURS, site_id=sid)
        if not args.mock:
            ts = keep_real(out / "timeseries.json", ts, same_window=(config.fmt_utc(start), config.fmt_utc(end)))
        # Validación contra el contrato antes de escribir nada.
        Horizon.model_validate(hz)
        Terrain.model_validate(terrain)
        Timeseries.model_validate(ts)

        write_json(out / "horizon.json", hz)
        write_json(out / "terrain.json", terrain)
        write_json(out / "timeseries.json", ts)
        s = ts["summary"]
        print(f"[{sid}] {len(ts['samples'])} muestras · Sol {s['sun_visible_pct']} % · "
              f"Tierra {s['earth_visible_pct']} % · noche máx {s['longest_dark_h']} h · "
              f"{time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
