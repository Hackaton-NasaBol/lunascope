from __future__ import annotations

import logging
from typing import Dict, Any
import numpy as np

from lunascope.terrain.dem import get_coarse_dem

log = logging.getLogger("lunascope.terrain.stats")


def compute_terrain_stats(lat: float, lon: float, radius_m: float = 100.0, site_id: str = "") -> Dict[str, Any]:
    """Calcula la elevación, pendiente media/máxima y porcentaje de riesgo (>10°) dentro del radio especificado."""
    if not (-90.0 <= lat <= -80.0):
        raise ValueError("outside_dem")

    try:
        dem = get_coarse_dem()
    except (FileNotFoundError, RuntimeError) as e:
        log.warning("DEM no disponible (%s), usando fallback simulado para terreno", e)
        from lunascope import mock
        return mock.mock_terrain_stats(lat, lon, radius_m, site_id=site_id)

    if not dem.is_inside(lat, lon):
        raise ValueError("outside_dem")

    x0, y0 = dem.xy(lat, lon)
    z0 = float(dem.sample([x0], [y0])[0])

    res_x, res_y = abs(dem.res[0]), abs(dem.res[1])
    margin = radius_m + 2.0 * max(res_x, res_y)

    col_c, row_c = dem.inv * (x0, y0)
    col_c, row_c = float(col_c), float(row_c)

    span_x = int(np.ceil(margin / res_x))
    span_y = int(np.ceil(margin / res_y))

    r_min = max(0, int(row_c - span_y))
    r_max = min(dem.z.shape[0], int(row_c + span_y + 1))
    c_min = max(0, int(col_c - span_x))
    c_max = min(dem.z.shape[1], int(col_c + span_x + 1))

    window_z = dem.z[r_min:r_max, c_min:c_max]
    if window_z.size == 0 or np.isnan(window_z).all():
        raise ValueError("outside_dem")

    dz_dy, dz_dx = np.gradient(window_z, res_y, res_x)
    slopes = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))

    rows_idx = np.arange(r_min, r_max)
    cols_idx = np.arange(c_min, c_max)
    cc, rr = np.meshgrid(cols_idx, rows_idx)

    dx = (cc - col_c) * res_x
    dy = (rr - row_c) * res_y
    dist = np.hypot(dx, dy)

    mask = (dist <= radius_m) & (~np.isnan(slopes))
    valid_slopes = slopes[mask]

    if valid_slopes.size == 0:
        valid_slopes = np.array([float(np.nanmean(slopes)) if not np.isnan(slopes).all() else 0.0])

    slope_mean = float(np.mean(valid_slopes))
    slope_max = float(np.max(valid_slopes))
    hazard_count = int(np.count_nonzero(valid_slopes > 10.0))
    hazard_pct = float(hazard_count / valid_slopes.size * 100.0)

    return {
        "site_id": site_id,
        "elevation_m": round(z0, 1),
        "radius_m": float(radius_m),
        "slope_deg_mean": round(slope_mean, 2),
        "slope_deg_max": round(slope_max, 2),
        "hazard_pct": round(hazard_pct, 2),
        "dem_resolution_m": round(float(res_x), 1),
        "source": "real",
    }
