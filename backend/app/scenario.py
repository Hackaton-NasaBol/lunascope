"""Escenarios de fecha: la serie de un sitio para cualquier fecha de inicio y duración.

La ventana por defecto (MISSION_START + MISSION_DAYS) sale de los JSON precalculados. Cualquier otra se
calcula al momento con SPICE (≈0,1 s por sitio) sobre la máscara de horizonte y el terreno ya guardados,
y se cachea. Requiere los kernels SPICE en la máquina que sirve la API.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Optional

from app import config
from app.errors import ApiError, not_found
from app.store import store
from lunascope import pipeline

MAX_DAYS = 180
MIN_START = datetime(1950, 1, 1, tzinfo=timezone.utc)   # dentro de la cobertura de de440s (1849–2150)
MAX_END = datetime(2149, 12, 31, tzinfo=timezone.utc)


def step_for(days: int) -> float:
    """Paso de 1 h hasta 90 días; 2 h para ventanas más largas (respuesta más ligera)."""
    return 1.0 if days <= 90 else 2.0


def window(start: Optional[str], days: Optional[int]) -> tuple[datetime, int]:
    """Valida y normaliza la ventana pedida. Sin parámetros → la ventana por defecto."""
    t0 = config.MISSION_START if start is None else _parse(start)
    n = config.MISSION_DAYS if days is None else int(days)
    if not 1 <= n <= MAX_DAYS:
        raise ApiError(422, "invalid_days", f"La duración debe estar entre 1 y {MAX_DAYS} días.")
    if t0 < MIN_START or t0 + timedelta(days=n) > MAX_END:
        raise ApiError(422, "date_out_of_range",
                       f"Fechas fuera de la cobertura de las efemérides ({MIN_START:%Y} – {MAX_END:%Y}).")
    return t0, n


def _parse(s: str) -> datetime:
    try:
        return config.parse_utc(s)
    except ValueError:
        raise ApiError(422, "invalid_date", f"Fecha no válida: '{s}'. Usa ISO 8601, p. ej. 2028-03-01T00:00:00Z.")


def is_default(t0: datetime, days: int) -> bool:
    return t0 == config.MISSION_START and days == config.MISSION_DAYS


def live_available() -> bool:
    return pipeline.SCIENCE is not None and pipeline.kernels_loaded()


def _site_data(site_id: str) -> tuple[dict, dict, dict, Optional[dict]]:
    """(sitio, horizonte, terreno, serie por defecto) de un sitio fijo o de un punto libre."""
    if site_id in store.points:
        p = store.points[site_id]
        return p["site"], p["horizon"], p["terrain"], p["timeseries"]
    if site_id not in store.sites:
        raise not_found("site", site_id)
    hz, terrain = store.get(site_id, "horizon"), store.get(site_id, "terrain")
    if hz is None or terrain is None:
        raise ApiError(503, "data_missing", f"El sitio '{site_id}' no tiene horizonte o terreno precalculados.")
    return store.sites[site_id], hz, terrain, store.get(site_id, "timeseries")


def series(site_id: str, start: Optional[str] = None, days: Optional[int] = None) -> dict:
    """Serie temporal del sitio para la ventana pedida (formato timeseries.json)."""
    t0, n = window(start, days)
    site, hz, terrain, default = _site_data(site_id)
    # Los puntos libres se calculan con paso de 2 h: su serie por defecto ya cubre la ventana estándar.
    if is_default(t0, n) and default is not None:
        return default
    if not live_available():
        raise ApiError(503, "kernels_missing",
                       "Cambiar la fecha necesita los kernels SPICE en el servidor "
                       "(python backend/scripts/download_kernels.py).")
    step = max(step_for(n), config.POINT_STEP_HOURS if site_id in store.points else 0)
    return _cached(site_id, site["lat"], site["lon"], terrain["elevation_m"], tuple(hz["horizon_el_deg"]),
                   hz["az_step_deg"], config.fmt_utc(t0), n, step)


@lru_cache(maxsize=128)
def _cached(site_id: str, lat: float, lon: float, elevation_m: float, horizon: tuple, az_step: float,
            start_iso: str, days: int, step: float) -> dict:
    t0 = config.parse_utc(start_iso)
    hz = {"horizon_el_deg": list(horizon), "az_step_deg": az_step}
    return pipeline.timeseries(lat, lon, elevation_m + config.OBSERVER_HEIGHT_M, hz,
                               t0, t0 + timedelta(days=days), step, site_id=site_id)


def mission_info() -> dict:
    return {
        "default_start": config.fmt_utc(config.MISSION_START),
        "default_days": config.MISSION_DAYS,
        "max_days": MAX_DAYS,
        "min_start": config.fmt_utc(MIN_START),
        "max_end": config.fmt_utc(MAX_END),
        "live_dates": live_available(),
    }
