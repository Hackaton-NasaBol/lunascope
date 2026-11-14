from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any
import numpy as np

from lunascope.terrain.dem import get_coarse_dem, local_axes, MOON_RADIUS_M

log = logging.getLogger("lunascope.terrain.horizon")


def _build_distance_steps(res: float, max_d: float) -> np.ndarray:
    res = max(10.0, float(res))
    s1 = np.arange(res, min(5_000.0, max_d), res)
    s2 = np.arange(5_000.0, min(30_000.0, max_d), 2.0 * res)
    s3 = np.arange(30_000.0, max_d + res, 4.0 * res)
    dists = np.concatenate([s1, s2, s3])
    return np.unique(dists[dists <= max_d])


def compute_horizon(
    lat: float,
    lon: float,
    mode: str = "full",
    observer_height_m: float = 2.0,
    site_id: str = "",
) -> Dict[str, Any]:
    """Calcula la máscara de horizonte angular en 360° de azimut considerando curvatura lunar."""
    if not (-90.0 <= lat <= -80.0):
        raise ValueError("outside_dem")

    try:
        dem = get_coarse_dem()
    except (FileNotFoundError, RuntimeError) as e:
        log.warning("DEM no disponible (%s), usando fallback simulado para horizonte", e)
        from lunascope import mock
        return mock.mock_horizon(lat, lon, mode, site_id=site_id, observer_height_m=observer_height_m)

    if not dem.is_inside(lat, lon):
        raise ValueError("outside_dem")

    (x0, y0), north, east = local_axes(dem, lat, lon)
    z_ground = float(dem.sample([x0], [y0])[0])
    z0 = z_ground + observer_height_m

    max_d = 150_000.0 if mode == "full" else 50_000.0
    step_az = 1.0 if mode == "full" else 2.0

    res = abs(dem.res[0])
    s = _build_distance_steps(res, max_d)
    curv = s**2 / (2.0 * MOON_RADIUS_M)

    az_angles = np.arange(0.0, 360.0, step_az)
    horizon_el: list[float] = []

    for a in az_angles:
        ar = np.radians(a)
        d_dir = north * np.cos(ar) + east * np.sin(ar)

        xs = x0 + d_dir[0] * s
        ys = y0 + d_dir[1] * s
        zs = dem.sample(xs, ys)

        elev_angles = np.degrees(np.arctan2(zs - z0 - curv, s))
        valid = elev_angles[~np.isnan(elev_angles)]
        max_angle = float(np.max(valid)) if valid.size > 0 else 0.0
        horizon_el.append(round(max_angle, 3))

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "site_id": site_id,
        "lat": lat,
        "lon": lon,
        "observer_height_m": observer_height_m,
        "az_step_deg": step_az,
        "horizon_el_deg": horizon_el,
        "max_distance_km": max_d / 1000.0,
        "dem_source": dem.path.name,
        "dem_resolution_m": round(float(res), 1),
        "mode": mode,
        "generated_at": now_iso,
        "source": "real",
    }
