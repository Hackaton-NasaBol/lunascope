"""Pruebas del motor científico (Integrante 2).

Se saltan automáticamente si no hay kernels SPICE descargados.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from lunascope.science import kernels as K

try:
    K.load_kernels()
    HAVE_KERNELS = True
except Exception:  # pragma: no cover
    HAVE_KERNELS = False

needs_kernels = pytest.mark.skipif(not HAVE_KERNELS, reason="faltan kernels SPICE")

from lunascope.science.geometry import az_el_from_vectors, enu_basis, enu_vector, site_vector  # noqa: E402
from lunascope.science.visibility import horizon_at, runs, summarize, visible_fraction  # noqa: E402

START = datetime(2027, 9, 1, tzinfo=timezone.utc)
END = START + timedelta(days=60)
MALAPERT = (-86.0, 0.0, 2.0)


# --------------------------------------------------------------------------- #
# Sin kernels: geometría y visibilidad puras
# --------------------------------------------------------------------------- #
def test_enu_basis_is_orthonormal_and_north_points_away_from_south_pole():
    site = site_vector(-86.0, 30.0, 0.0)
    e, n, u = enu_basis(site)
    m = np.array([e, n, u])
    assert np.allclose(m @ m.T, np.eye(3), atol=1e-12)
    assert n[2] > 0          # en el hemisferio sur, el norte local sube hacia +z
    assert np.allclose(np.cross(e, n), u)  # mano derecha: E × N = U


def test_azimuth_convention_cardinal_points():
    basis = enu_basis(site_vector(-86.0, 0.0, 0.0))
    e, n, u = basis
    vecs = np.array([n, e, -n, -e, u * 0.1 + n])
    az, el = az_el_from_vectors(vecs, basis)
    assert np.allclose(az[:4], [0, 90, 180, 270], atol=1e-9)
    assert el[4] == pytest.approx(np.degrees(np.arctan(0.1)), abs=1e-9)


def test_enu_vector_roundtrip():
    basis = enu_basis(site_vector(-85.0, 45.0, 0.0))
    v_enu = enu_vector(np.array([10.0, 123.0, 300.0]), np.array([1.0, 5.0, -2.0]))
    v = v_enu @ np.array(basis)  # ENU -> MOON_ME
    az, el = az_el_from_vectors(v, basis)
    assert np.allclose(az, [10, 123, 300]) and np.allclose(el, [1, 5, -2])


def test_pole_rejected():
    with pytest.raises(ValueError):
        site_vector(-89.995, 0.0, 0.0)


def test_horizon_interpolation_is_circular_and_infers_step():
    h = np.zeros(360)
    h[359], h[0] = 2.0, 4.0
    assert horizon_at(359.5, h) == pytest.approx(3.0)
    h2 = np.arange(180, dtype=float)  # máscara a 2°
    assert horizon_at(3.0, h2) == pytest.approx(1.5)


def test_visible_fraction_limits():
    r = 0.267
    assert visible_fraction(1.0, 1.0, r) == pytest.approx(0.5)
    assert visible_fraction(1.0 + r, 1.0, r) == pytest.approx(1.0)
    assert visible_fraction(1.0 - r, 1.0, r) == pytest.approx(0.0)
    assert visible_fraction(5.0, 1.0, r) == 1.0 and visible_fraction(-5.0, 1.0, r) == 0.0


def test_runs_and_summary():
    assert runs([0, 1, 1, 0, 1]) == [(1, 2), (4, 4)]
    times = [START + timedelta(hours=k) for k in range(6)]
    s = summarize(times, [1, 1, 1, 0, 0, 1], [1, 1, 0, 0, 1, 1], 1.0)
    assert s["sun_visible_pct"] == pytest.approx(66.7)
    assert s["longest_dark_h"] == 2
    assert s["longest_no_earth_h"] == 2
    assert s["windows"][0] == {"start": "2027-09-01T00:00:00Z", "end": "2027-09-01T01:00:00Z", "hours": 1.0}


# --------------------------------------------------------------------------- #
# Con kernels: comprobaciones físicas del documento del Integrante 2
# --------------------------------------------------------------------------- #
@needs_kernels
def test_earth_moon_distance():
    import spiceypy as sp
    et = sp.str2et("2027-09-01 00:00:00 UTC")
    pos, _ = sp.spkpos("EARTH", et, "MOON_ME", "LT+S", "MOON")
    assert 356_000 < np.linalg.norm(pos) < 407_000


@needs_kernels
def test_contract_shape_and_validates_against_backend_model():
    from app.models import Timeseries
    from lunascope.science import compute_timeseries

    ts = compute_timeseries(*MALAPERT, [1.0] * 360, START, END, 1.0, site_id="malapert")
    Timeseries.model_validate(ts)
    assert len(ts["samples"]) == 1441
    assert ts["samples"][0]["t"] == "2027-09-01T00:00:00Z"
    assert ts["end"] == "2027-10-31T00:00:00Z"
    assert ts["horizon"] == "mask"
    for s in ts["samples"][:50]:
        assert 0 <= s["sun"]["az"] < 360 and 0 <= s["earth"]["az"] < 360
    assert len(ts["summary"]["windows"]) <= 10


@needs_kernels
def test_sun_elevation_range_at_86S():
    from lunascope.science import compute_timeseries
    ts = compute_timeseries(*MALAPERT, None, START, END, 1.0)
    el = np.array([s["sun"]["el"] for s in ts["samples"]])
    # distancia al polo 4° + inclinación ~1,54° -> |el| <= ~5,6°
    assert el.max() < 6.0 and el.min() > -6.0
    assert el.max() > 2.5 and el.min() < -2.5
    assert ts["horizon"] == "none"


@needs_kernels
def test_sun_full_azimuth_turn_in_a_synodic_month():
    from lunascope.science import compute_geometry, time_grid
    _, ets = time_grid(START, END, 1.0)
    g = compute_geometry(*MALAPERT, ets)
    unwrapped = np.degrees(np.unwrap(np.radians(g["sun_az"])))
    turns = abs(unwrapped[-1] - unwrapped[0]) / 360.0
    assert 60 / 29.53 - 0.1 < turns < 60 / 29.53 + 0.1


@needs_kernels
def test_earth_barely_moves_and_is_north_low_at_lon0():
    from lunascope.science import compute_geometry, time_grid
    _, ets = time_grid(START, END, 1.0)
    g = compute_geometry(*MALAPERT, ets)
    az = (g["earth_az"] + 180) % 360 - 180   # centrado en el norte
    assert np.abs(az).max() < 15             # cerca del norte, sin dar vueltas
    assert np.abs(g["earth_el"]).max() < 12  # baja sobre el horizonte (4° + libración)


@needs_kernels
def test_horizon_blocks_sun():
    from lunascope.science import compute_timeseries
    flat = compute_timeseries(*MALAPERT, None, START, END, 1.0)
    wall = compute_timeseries(*MALAPERT, [10.0] * 360, START, END, 1.0)
    assert wall["summary"]["sun_visible_pct"] == 0.0
    assert flat["summary"]["sun_visible_pct"] > 0.0


@needs_kernels
def test_fast_mode_point_under_one_second():
    from lunascope.science import compute_timeseries
    compute_timeseries(*MALAPERT, None, START, START + timedelta(days=1), 1.0)  # calentar
    t0 = time.perf_counter()
    ts = compute_timeseries(-86.1, -3.2, 1500.0, [0.5] * 180, START, END, 2.0)
    assert time.perf_counter() - t0 < 1.0
    assert len(ts["samples"]) == 721
