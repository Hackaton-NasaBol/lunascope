"""Relieve del DEM LOLA para el globo 3D (Cesium CustomHeightmapTerrainProvider).

GET /api/terrain/info                      → si hay DEM, tamaño de tesela y cobertura
GET /api/terrain/heightmap/{z}/{x}/{y}.bin → 65×65 alturas float32 (little-endian, metros sobre la
                                             esfera de 1 737 400 m), filas de norte a sur

Esquema de teselas: GeographicTilingScheme de Cesium (2×1 teselas en el nivel 0). Fuera del
casquete del DEM (al norte de 80°S) la altura es 0: el globo queda en la esfera de referencia.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
from fastapi import APIRouter
from fastapi.responses import Response

from app.errors import ApiError

router = APIRouter(tags=["terrain"])

TILE_SIZE = 65
DEM_NORTH_LIMIT = -80.0


def _dem():
    try:
        from lunascope.terrain import get_coarse_dem

        return get_coarse_dem()
    except (FileNotFoundError, RuntimeError, ImportError) as e:
        raise ApiError(503, "dem_missing", f"Relieve LOLA no disponible: falta el DEM ({e}).")


@router.get("/terrain/info")
def terrain_info():
    try:
        dem = _dem()
    except ApiError:
        return {"available": False}
    return {
        "available": True,
        "tile_size": TILE_SIZE,
        "tiling_scheme": "geographic",
        "coverage": {"west": -180, "south": -90, "east": 180, "north": DEM_NORTH_LIMIT},
        "resolution_m": float(abs(dem.res[0])),
        "dem_source": dem.path.name,
        "height_reference": "esfera de 1 737 400 m",
    }


@lru_cache(maxsize=4096)
def _tile(z: int, x: int, y: int) -> bytes:
    n_lat = 2 ** z
    dlon, dlat = 360.0 / (2 * n_lat), 180.0 / n_lat
    west, north = -180.0 + x * dlon, 90.0 - y * dlat
    south = north - dlat
    heights = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float32)
    if south < DEM_NORTH_LIMIT:
        dem = _dem()
        lons = west + np.linspace(0, dlon, TILE_SIZE)
        lats = north - np.linspace(0, dlat, TILE_SIZE)
        LON, LAT = np.meshgrid(lons, lats)
        inside = LAT <= DEM_NORTH_LIMIT
        if inside.any():
            from scipy.ndimage import map_coordinates

            xs, ys = dem.to_xy.transform(LON[inside], LAT[inside])
            c, r = dem.inv @ (np.asarray(xs), np.asarray(ys))
            vals = map_coordinates(dem.z, [np.asarray(r) - 0.5, np.asarray(c) - 0.5], order=1, mode="nearest")
            heights[inside] = np.nan_to_num(vals, nan=0.0)
    return heights.astype("<f4").tobytes()


@router.get("/terrain/heightmap/{z}/{x}/{y}.bin", response_class=Response)
def heightmap(z: int, x: int, y: int):
    if not (0 <= z <= 14 and 0 <= x < 2 ** (z + 1) and 0 <= y < 2 ** z):
        raise ApiError(422, "invalid_tile", f"Tesela {z}/{x}/{y} fuera del esquema geográfico.")
    return Response(_tile(z, x, y), media_type="application/octet-stream",
                    headers={"Cache-Control": "public, max-age=86400"})
