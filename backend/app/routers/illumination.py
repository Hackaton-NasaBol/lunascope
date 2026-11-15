"""Capa de sombras del relieve (DEM LOLA + Sol de la serie temporal SPICE).

GET /api/illumination/{site_id}/meta      → rectángulo lat/lon y metadatos de la capa
GET /api/illumination/{site_id}.png?t=…   → PNG: negro semitransparente = sombra, transparente = luz
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.config import fmt_utc, parse_utc
from app.errors import ApiError, not_found
from app.store import store

router = APIRouter(tags=["illumination"])
log = logging.getLogger("lunascope.illumination")


def _site(site_id: str) -> tuple[dict, dict]:
    if site_id in store.points:
        p = store.points[site_id]
        return p["site"], p["timeseries"]
    if site_id not in store.sites:
        raise not_found("site", site_id)
    ts = store.get(site_id, "timeseries")
    if ts is None:
        raise ApiError(503, "data_missing", f"El sitio '{site_id}' no tiene timeseries.json.")
    return store.sites[site_id], ts


def _grid(site: dict):
    try:
        from lunascope.terrain.illumination import site_grid
        return site_grid(round(site["lat"], 5), round(site["lon"], 5))
    except (FileNotFoundError, RuntimeError, ImportError) as e:
        raise ApiError(503, "dem_missing", f"Sombras no disponibles: falta el DEM LOLA ({e}).")
    except ValueError as e:
        raise ApiError(422, str(e), "El sitio está fuera de la cobertura del DEM.")


def sun_at(ts: dict, t_iso: str) -> tuple[float, float, str]:
    """Az/el del Sol interpolados en la serie (mismo dato que el gráfico). Devuelve también t normalizado."""
    samples = ts["samples"]
    t0 = parse_utc(samples[0]["t"]).timestamp()
    step = float(ts["step_hours"]) * 3600
    t = parse_utc(t_iso).timestamp()
    x = (t - t0) / step
    if x < 0 or x > len(samples) - 1:
        raise ApiError(422, "time_out_of_range", f"{t_iso} está fuera de la ventana de la misión.")
    i0 = int(x)
    i1 = min(i0 + 1, len(samples) - 1)
    f = x - i0
    a, b = samples[i0]["sun"], samples[i1]["sun"]
    daz = (b["az"] - a["az"] + 180) % 360 - 180
    return (a["az"] + daz * f) % 360, a["el"] + (b["el"] - a["el"]) * f, fmt_utc(parse_utc(t_iso))


@lru_cache(maxsize=256)
def _render(lat: float, lon: float, az: float, el: float) -> tuple[bytes, float | None]:
    from lunascope.terrain.illumination import lit_fraction_at_center, lit_mask, render_png, site_grid

    grid = site_grid(lat, lon)
    mask = lit_mask(grid, az, el)
    return render_png(mask), lit_fraction_at_center(grid, mask)


@router.get("/illumination/{site_id}/meta")
def illumination_meta(site_id: str):
    site, _ = _site(site_id)
    from lunascope.terrain.illumination import metadata

    return {"site_id": site_id, **metadata(_grid(site)), "source": "real"}


@router.get("/illumination/{site_id}.png", response_class=Response)
def illumination_png(site_id: str, t: str = Query(..., description="Instante UTC ISO 8601, p. ej. 2027-09-03T05:00:00Z")):
    site, ts = _site(site_id)
    grid = _grid(site)
    az, el, t_norm = sun_at(ts, t)
    t0 = time.time()
    # Redondeo a 0,1°: el Sol se mueve ~0,5°/h, así se reutiliza la caché al mover el tiempo.
    png, lit_center = _render(grid.lat, grid.lon, round(az, 1), round(el, 1))
    log.info("sombras %s t=%s az=%.1f el=%.2f en %.2fs", site_id, t_norm, az, el, time.time() - t0)
    return Response(
        content=png,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Sun-Az": f"{az:.2f}",
            "X-Sun-El": f"{el:.3f}",
            "X-Site-Lit-Fraction": "" if lit_center is None else f"{lit_center:.2f}",
        },
    )
