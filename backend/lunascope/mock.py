"""Datos falsos (mocks) que respetan el contrato v1 exactamente.

Sirven para que el frontend y el motor de decisión trabajen antes de que
lleguen los módulos reales de science/ (Integrante 2) y terrain/ (Integrante 3).
Todo lo que sale de aquí lleva "source": "mock".

La geometría es aproximada pero con sentido físico: Sol y Tierra se modelan por
su punto subsolar / subterrestre sobre la Luna (con libración), y la elevación es
90° menos la distancia angular a ese punto. NO es un sustituto de SPICE.
"""

from __future__ import annotations

import zlib
from datetime import datetime, timedelta, timezone

import numpy as np

from app.config import (
    EARTH_RADIUS_DEG,
    OBSERVER_HEIGHT_M,
    SUN_RADIUS_DEG,
    VISIBLE_THRESHOLD,
    fmt_utc,
)

SYNODIC_DAYS = 29.530589
DRACONIC_DAYS = 27.212221
ANOMALISTIC_DAYS = 27.554550
_EPOCH = datetime(2000, 1, 1, 12)  # referencia arbitraria para las fases


def _rng(key: str) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(key.encode()))


def _key(lat: float, lon: float, site_id: str) -> str:
    return site_id or f"{lat:.3f},{lon:.3f}"


# --------------------------------------------------------------------------- #
# Terreno
# --------------------------------------------------------------------------- #
def mock_horizon(lat: float, lon: float, mode: str = "full", site_id: str = "",
                 observer_height_m: float = OBSERVER_HEIGHT_M) -> dict:
    step = 1 if mode == "full" else 2
    rng = _rng(_key(lat, lon, site_id))
    az = np.radians(np.arange(0, 360, step))
    base = rng.uniform(0.3, 1.5)
    h = np.full(az.shape, base)
    for k in (1, 2, 3, 5, 8):
        h += rng.uniform(0.1, 1.2) / k ** 0.5 * np.cos(k * az + rng.uniform(0, 2 * np.pi))
    h = np.clip(h, -1.0, 6.0)
    return {
        "site_id": site_id,
        "lat": lat,
        "lon": lon,
        "observer_height_m": observer_height_m,
        "az_step_deg": step,
        "horizon_el_deg": [round(float(v), 3) for v in h],
        "max_distance_km": 150 if mode == "full" else 50,
        "dem_source": "MOCK (sin DEM)",
        "dem_resolution_m": 60 if mode == "full" else 120,
        "mode": mode,
        "generated_at": fmt_utc(datetime.now(timezone.utc)),
        "source": "mock",
    }


def mock_terrain_stats(lat: float, lon: float, radius_m: float = 100, site_id: str = "") -> dict:
    rng = _rng("terrain:" + _key(lat, lon, site_id))
    mean = float(rng.uniform(2.0, 8.0))
    return {
        "site_id": site_id,
        "elevation_m": round(float(rng.uniform(-500, 6000)), 1),
        "radius_m": radius_m,
        "slope_deg_mean": round(mean, 2),
        "slope_deg_max": round(mean + float(rng.uniform(3, 12)), 2),
        "hazard_pct": round(float(rng.uniform(0, 15)), 2),
        "dem_resolution_m": 20,
        "source": "mock",
    }


# --------------------------------------------------------------------------- #
# Ciencia
# --------------------------------------------------------------------------- #
def _az_el_to_subpoint(lat, lon, sub_lat, sub_lon):
    """Azimut (desde el norte local, horario) y elevación aproximada hacia un
    cuerpo cuyo punto sub-cuerpo está en (sub_lat, sub_lon). Todo en grados."""
    p1, l1 = np.radians(lat), np.radians(lon)
    p2, l2 = np.radians(sub_lat), np.radians(sub_lon)
    dl = l2 - l1
    cos_d = np.sin(p1) * np.sin(p2) + np.cos(p1) * np.cos(p2) * np.cos(dl)
    dist = np.degrees(np.arccos(np.clip(cos_d, -1, 1)))
    az = np.degrees(np.arctan2(np.sin(dl) * np.cos(p2),
                               np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)))
    return np.mod(az, 360.0), 90.0 - dist


def horizon_at(az_deg, horizon_el_deg, az_step_deg: float = 1.0):
    """Interpolación lineal de la máscara de horizonte en un azimut cualquiera."""
    h = np.asarray(horizon_el_deg, dtype=float)
    x = np.mod(np.asarray(az_deg), 360.0) / az_step_deg
    i0 = np.floor(x).astype(int) % len(h)
    i1 = (i0 + 1) % len(h)
    f = x - np.floor(x)
    return h[i0] * (1 - f) + h[i1] * f


def visible_fraction(el, hz, r):
    return np.clip((el - hz + r) / (2 * r), 0.0, 1.0)


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Rachas de True como (inicio, fin) inclusivos."""
    runs, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def summarize(times: list[datetime], s_vf, e_vf, step_h: float) -> dict:
    """Resumen según las definiciones del contrato."""
    sun = np.asarray(s_vf) >= VISIBLE_THRESHOLD
    earth = np.asarray(e_vf) >= VISIBLE_THRESHOLD
    both = sun & earth

    def longest(mask):
        r = _runs(mask)
        return max(((b - a + 1) for a, b in r), default=0) * step_h

    windows = sorted(_runs(both), key=lambda ab: ab[1] - ab[0], reverse=True)[:10]
    return {
        "sun_visible_pct": round(100 * float(sun.mean()), 1),
        "earth_visible_pct": round(100 * float(earth.mean()), 1),
        "both_visible_pct": round(100 * float(both.mean()), 1),
        "longest_dark_h": longest(~sun),
        "longest_no_earth_h": longest(~earth),
        "windows": [
            {"start": fmt_utc(times[a]), "end": fmt_utc(times[b]), "hours": (b - a) * step_h}
            for a, b in windows
        ],
    }


def mock_timeseries(lat: float, lon: float, height_m: float, horizon_el_deg,
                    start: datetime, end: datetime, step_h: float = 1.0,
                    site_id: str = "", az_step_deg: float | None = None) -> dict:
    n = int((end - start).total_seconds() // (3600 * step_h)) + 1
    times = [start + timedelta(hours=step_h * k) for k in range(n)]
    days = np.array([(t.replace(tzinfo=None) - _EPOCH).total_seconds() / 86400 for t in times])

    # Sol: el punto subsolar recorre la Luna hacia el oeste en un mes sinódico.
    sun_sub_lon = np.mod(180 - 360 * days / SYNODIC_DAYS + 180, 360) - 180
    sun_sub_lat = 1.54 * np.sin(2 * np.pi * days / DRACONIC_DAYS)
    # Tierra: casi fija sobre (0, 0), con libración en latitud y longitud.
    earth_sub_lat = 6.7 * np.sin(2 * np.pi * days / DRACONIC_DAYS)
    earth_sub_lon = 7.9 * np.sin(2 * np.pi * days / ANOMALISTIC_DAYS)

    s_az, s_el = _az_el_to_subpoint(lat, lon, sun_sub_lat, sun_sub_lon)
    e_az, e_el = _az_el_to_subpoint(lat, lon, earth_sub_lat, earth_sub_lon)

    hz = horizon_el_deg or [0.0] * 360
    step = az_step_deg or 360 / len(hz)
    s_hz, e_hz = horizon_at(s_az, hz, step), horizon_at(e_az, hz, step)
    s_vf = visible_fraction(s_el, s_hz, SUN_RADIUS_DEG)
    e_vf = visible_fraction(e_el, e_hz, EARTH_RADIUS_DEG)

    r3 = lambda v: round(float(v), 3)  # noqa: E731
    samples = [
        {
            "t": fmt_utc(times[i]),
            "sun": {"az": r3(s_az[i]), "el": r3(s_el[i]), "horizon_el": r3(s_hz[i]),
                    "visible_fraction": r3(s_vf[i])},
            "earth": {"az": r3(e_az[i]), "el": r3(e_el[i]), "horizon_el": r3(e_hz[i]),
                      "visible_fraction": r3(e_vf[i])},
        }
        for i in range(n)
    ]
    return {
        "site_id": site_id,
        "start": fmt_utc(start),
        "end": fmt_utc(end),
        "step_hours": step_h,
        "samples": samples,
        "summary": summarize(times, s_vf, e_vf, step_h),
        "source": "mock",
    }


def mock_outside_dem(lat: float, lon: float) -> bool:
    """Cobertura aproximada de los DEM polares LOLA: al sur de 80°S."""
    return lat > -80.0
