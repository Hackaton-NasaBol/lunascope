"""Sombras del relieve (terrain/illumination.py + /api/illumination). Necesitan el DEM LOLA."""

import json
import math

import numpy as np
import pytest
from fastapi.testclient import TestClient
from scipy.ndimage import map_coordinates

from app.config import DATA_DIR


def _has_dem() -> bool:
    try:
        from lunascope.terrain import get_coarse_dem

        get_coarse_dem()
        return True
    except (FileNotFoundError, RuntimeError):
        return False


pytestmark = pytest.mark.skipif(not _has_dem(), reason="falta el DEM LOLA en dem/")
SITES = {s["id"]: s for s in json.loads((DATA_DIR / "sites.json").read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def grid():
    from lunascope.terrain.illumination import site_grid

    s = SITES["mons_mouton_plateau"]
    return site_grid(round(s["lat"], 5), round(s["lon"], 5))


def test_azimuth_convention_matches_horizon_mask(grid):
    """El horizonte medido con los ejes del barrido coincide con horizon.json (mismo azimut, sin giro)."""
    hz = np.array(json.loads((DATA_DIR / "precomputed/mons_mouton_plateau/horizon.json").read_text())["horizon_el_deg"])
    n = grid.n
    z0 = map_coordinates(grid.zplane, [[n], [n]], order=1)[0] + 2.0
    t = np.arange(1, n)
    ours = []
    for a in range(0, 360, 5):
        d = grid.north_idx * math.cos(math.radians(a)) + grid.east_idx * math.sin(math.radians(a))
        d /= np.linalg.norm(d)
        zz = map_coordinates(grid.zplane, [n + t * d[0], n + t * d[1]], order=1, cval=np.nan)
        ours.append(np.degrees(np.nanmax(np.arctan2(zz - z0, t * grid.res_m))))
    assert np.mean(np.abs(np.array(ours) - hz[::5])) < 0.5


def test_high_sun_lights_most_terrain_and_low_sun_does_not(grid):
    from lunascope.terrain.illumination import lit_mask

    high = lit_mask(grid, 90.0, 25.0)
    below = lit_mask(grid, 90.0, -3.0)
    assert (high[high >= 0] == 1).mean() > 0.9
    assert (below[below >= 0] == 1).mean() < (high[high >= 0] == 1).mean()


def test_api_meta_and_png():
    from app.main import app

    with TestClient(app) as c:
        meta = c.get("/api/illumination/malapert/meta").json()
        r = meta["rectangle"]
        assert r["south"] < SITES["malapert"]["lat"] < r["north"]
        png = c.get("/api/illumination/malapert.png", params={"t": "2027-09-03T05:00:00Z"})
        assert png.status_code == 200 and png.headers["content-type"] == "image/png"
        assert png.content[:8] == b"\x89PNG\r\n\x1a\n"
        assert -90 <= float(png.headers["x-sun-el"]) <= 90
        # Otra fecha (fuera de la serie por defecto): el Sol se calcula con SPICE directamente.
        other = c.get("/api/illumination/malapert.png", params={"t": "2028-03-10T00:00:00Z"})
        assert other.status_code in (200, 503)
        out = c.get("/api/illumination/malapert.png", params={"t": "2200-01-01T00:00:00Z"})
        assert out.status_code == 422 and out.json()["error"] == "date_out_of_range"


def test_terrain_heightmap_tiles():
    import numpy as np

    from app.main import app

    with TestClient(app) as c:
        info = c.get("/api/terrain/info").json()
        assert info["available"] and info["tile_size"] == 65
        z = 8
        n = 2 ** z
        x, y = int((2.93 + 180) / (360 / (2 * n))), int((90 + 85.99) / (180 / n))   # Malapert
        h = np.frombuffer(c.get(f"/api/terrain/heightmap/{z}/{x}/{y}.bin").content, "<f4")
        assert h.size == 65 * 65 and 2000 < h.max() < 7000
        north = np.frombuffer(c.get("/api/terrain/heightmap/2/1/0.bin").content, "<f4")
        assert north.size == 65 * 65 and not north.any()       # fuera del casquete: esfera de referencia
        assert c.get("/api/terrain/heightmap/2/99/0.bin").status_code == 422
