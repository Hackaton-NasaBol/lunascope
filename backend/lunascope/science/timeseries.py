"""compute_timeseries: función del contrato (la llama backend/lunascope/pipeline.py)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import spiceypy as sp

from .geometry import az_el, enu_basis, site_vector
from .kernels import load_kernels
from .visibility import (
    EARTH_RADIUS_DEG,
    SUN_RADIUS_DEG,
    fmt_utc,
    horizon_at,
    summarize,
    visible_fraction,
)


def _utc(t: datetime) -> datetime:
    return t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)


def time_grid(start: datetime, end: datetime, step_h: float) -> tuple[list[datetime], np.ndarray]:
    """Tiempos UTC y sus ET. ET es lineal en segundos: un solo str2et."""
    load_kernels()
    start, end = _utc(start), _utc(end)
    if end < start:
        raise ValueError("end debe ser posterior a start")
    if step_h <= 0:
        raise ValueError("step_h debe ser positivo")
    n = int((end - start).total_seconds() // (3600 * step_h)) + 1
    times = [start + timedelta(hours=step_h * k) for k in range(n)]
    et0 = sp.str2et(start.strftime("%Y-%m-%d %H:%M:%S") + " UTC")
    ets = et0 + 3600.0 * step_h * np.arange(n)
    return times, ets


def compute_geometry(lat_deg: float, lon_deg: float, height_m: float, ets: np.ndarray) -> dict:
    """Az/el geométricos (sin horizonte) del Sol y la Tierra. Útil para validar."""
    load_kernels()
    site = site_vector(lat_deg, lon_deg, height_m)
    basis = enu_basis(site)
    s_az, s_el = az_el("SUN", ets, site, basis)
    e_az, e_el = az_el("EARTH", ets, site, basis)
    return {"sun_az": s_az, "sun_el": s_el, "earth_az": e_az, "earth_el": e_el}


def compute_timeseries(lat_deg: float, lon_deg: float, height_m: float,
                       horizon_el_deg: list[float] | None,
                       start: datetime, end: datetime, step_h: float = 1.0,
                       site_id: str = "") -> dict:
    """Serie temporal de Sol y Tierra para un sitio, en el formato de timeseries.json.

    Args:
        lat_deg, lon_deg: grados (lon este, −180..180).
        height_m: altura total del observador sobre la esfera de 1 737 400 m
            (elevación del terreno + 2 m).
        horizon_el_deg: máscara de horizonte (360 valores a 1° o 180 a 2°).
            Si es None, se usa horizonte plano a 0° y la salida lleva "horizon": "none".
        start, end: UTC. step_h: paso en horas.
    """
    load_kernels()
    times, ets = time_grid(start, end, step_h)
    g = compute_geometry(lat_deg, lon_deg, height_m, ets)

    has_mask = horizon_el_deg is not None and len(horizon_el_deg) > 0
    hz = horizon_el_deg if has_mask else [0.0] * 360
    s_hz = horizon_at(g["sun_az"], hz)
    e_hz = horizon_at(g["earth_az"], hz)
    s_vf = visible_fraction(g["sun_el"], s_hz, SUN_RADIUS_DEG)
    e_vf = visible_fraction(g["earth_el"], e_hz, EARTH_RADIUS_DEG)

    def body(az, el, h, vf, i):
        return {"az": round(float(az[i]), 3), "el": round(float(el[i]), 3),
                "horizon_el": round(float(h[i]), 3), "visible_fraction": round(float(vf[i]), 3)}

    samples = [
        {
            "t": fmt_utc(times[i]),
            "sun": body(g["sun_az"], g["sun_el"], s_hz, s_vf, i),
            "earth": body(g["earth_az"], g["earth_el"], e_hz, e_vf, i),
        }
        for i in range(len(times))
    ]
    return {
        "site_id": site_id,
        "start": fmt_utc(times[0]),
        "end": fmt_utc(_utc(end)),
        "step_hours": step_h,
        "samples": samples,
        "summary": summarize(times, s_vf, e_vf, step_h),
        "source": "real",
        "horizon": "mask" if has_mask else "none",
    }
