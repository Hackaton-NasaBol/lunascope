"""Une terrain/ (Int. 3) + science/ (Int. 2) con plan B en mocks.

Si un módulo real todavía no existe o falla al importarse, se usa el mock y se
avisa en el log. Nunca bloquea la demo.
"""

from __future__ import annotations

import logging
from datetime import datetime

from lunascope import mock

log = logging.getLogger("lunascope.pipeline")


def _import_terrain():
    try:
        from lunascope.terrain import compute_horizon, compute_terrain_stats  # type: ignore
        return compute_horizon, compute_terrain_stats
    except Exception as e:  # ImportError o un error dentro del módulo
        log.warning("terrain/ no disponible (%s): se usan mocks", e)
        return None


def _import_science():
    try:
        from lunascope.science import compute_timeseries  # type: ignore
        return compute_timeseries
    except Exception as e:
        log.warning("science/ no disponible (%s): se usan mocks", e)
        return None


TERRAIN = _import_terrain()
SCIENCE = _import_science()


def kernels_loaded() -> bool:
    if SCIENCE is None:
        return False
    try:
        import lunascope.science as sci  # type: ignore
        flag = getattr(sci, "kernels_loaded", False)
        return bool(flag() if callable(flag) else flag)
    except Exception:
        return False


def terrain_stats(lat: float, lon: float, radius_m: float, site_id: str = "") -> dict:
    if TERRAIN:
        out = dict(TERRAIN[1](lat, lon, radius_m=radius_m))
        out.setdefault("source", "real")
    else:
        out = mock.mock_terrain_stats(lat, lon, radius_m, site_id=site_id)
    out["site_id"] = site_id
    return out


def horizon(lat: float, lon: float, mode: str, observer_height_m: float, site_id: str = "") -> dict:
    if TERRAIN:
        out = dict(TERRAIN[0](lat, lon, mode=mode, observer_height_m=observer_height_m))
        out.setdefault("source", "real")
    else:
        out = mock.mock_horizon(lat, lon, mode, site_id=site_id, observer_height_m=observer_height_m)
    out["site_id"] = site_id
    return out


def timeseries(lat: float, lon: float, height_m: float, hz: dict, start: datetime,
               end: datetime, step_h: float, site_id: str = "") -> dict:
    # science/ puede importarse sin kernels (p. ej. un clon recién hecho): entonces, mock.
    if SCIENCE and not kernels_loaded():
        log.warning("science/ disponible pero sin kernels SPICE: se usa el mock "
                    "(ejecuta backend/scripts/download_kernels.py)")
    if SCIENCE and kernels_loaded():
        out = dict(SCIENCE(lat, lon, height_m, hz["horizon_el_deg"], start, end,
                           step_h=step_h, site_id=site_id))
        out.setdefault("source", "real")
    else:
        out = mock.mock_timeseries(lat, lon, height_m, hz["horizon_el_deg"], start, end,
                                   step_h=step_h, site_id=site_id, az_step_deg=hz["az_step_deg"])
    out["site_id"] = site_id
    return out


def outside_dem(lat: float, lon: float) -> bool:
    """Con terreno real, el propio módulo lanza ValueError('outside_dem')."""
    return TERRAIN is None and mock.mock_outside_dem(lat, lon)
