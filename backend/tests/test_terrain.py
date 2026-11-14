"""Pruebas unitarias para el módulo lunascope.terrain (Integrante 3)."""

import pytest
import numpy as np

from app.models import Horizon, Terrain
from lunascope.terrain import (
    compute_horizon,
    compute_terrain_stats,
    get_coarse_dem,
    local_axes,
    sample_elevation,
)


def _has_dem() -> bool:
    try:
        get_coarse_dem()
        return True
    except (FileNotFoundError, RuntimeError):
        return False


# Como en test_science.py con los kernels: sin el DEM (fuera de git) estas pruebas se saltan.
needs_dem = pytest.mark.skipif(not _has_dem(), reason="falta el DEM LOLA en dem/")


@needs_dem
def test_dem_metadata():
    dem = get_coarse_dem()
    assert dem.z.ndim == 2
    assert dem.res[0] > 0
    assert dem.is_inside(-86.0, 0.0)
    assert not dem.is_inside(0.0, 0.0)


@needs_dem
def test_local_axes():
    dem = get_coarse_dem()
    (x0, y0), north, east = local_axes(dem, -86.0, 0.0)
    assert np.isclose(np.linalg.norm(north), 1.0, atol=1e-3)
    assert np.isclose(np.linalg.norm(east), 1.0, atol=1e-3)
    # Deben ser ortogonales
    assert np.isclose(np.dot(north, east), 0.0, atol=1e-2)


@needs_dem
def test_sample_elevation_valid_and_invalid():
    elev = sample_elevation(-85.99, 2.93)
    assert isinstance(elev, float)
    assert 4000 < elev < 6000  # Malapert Massif

    with pytest.raises(ValueError, match="outside_dem"):
        sample_elevation(0.0, 0.0)  # Ecuador


def test_compute_terrain_stats():
    res = compute_terrain_stats(-85.99, 2.93, radius_m=100.0, site_id="malapert")
    Terrain.model_validate(res)
    assert res["site_id"] == "malapert"
    assert res["slope_deg_mean"] >= 0.0
    assert res["slope_deg_max"] >= res["slope_deg_mean"]
    assert 0.0 <= res["hazard_pct"] <= 100.0


def test_compute_horizon_fast():
    res = compute_horizon(-85.99, 2.93, mode="fast", site_id="malapert")
    Horizon.model_validate(res)
    assert res["mode"] == "fast"
    assert res["az_step_deg"] == 2.0
    assert len(res["horizon_el_deg"]) == 180
    assert all(-5.0 <= v <= 15.0 for v in res["horizon_el_deg"])


def test_compute_horizon_full():
    res = compute_horizon(-85.99, 2.93, mode="full", site_id="malapert")
    Horizon.model_validate(res)
    assert res["mode"] == "full"
    assert res["az_step_deg"] == 1.0
    assert len(res["horizon_el_deg"]) == 360
    assert all(-5.0 <= v <= 15.0 for v in res["horizon_el_deg"])


def test_outside_dem_boundary():
    with pytest.raises(ValueError, match="outside_dem"):
        compute_terrain_stats(-50.0, 0.0)

    with pytest.raises(ValueError, match="outside_dem"):
        compute_horizon(-50.0, 0.0)
