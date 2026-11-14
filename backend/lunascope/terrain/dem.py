from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from pyproj import CRS, Transformer
import rasterio
from scipy.ndimage import map_coordinates

log = logging.getLogger("lunascope.terrain.dem")

MOON_GEO = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")
MOON_RADIUS_M = 1_737_400.0

DEM_DIR = Path(__file__).resolve().parent.parent.parent.parent / "dem"
COARSE_DEM_FILENAME = "LDEM_80S_80MPP_ADJ.TIF"
MIN_COARSE_DEM_BYTES = 150 * 1024 * 1024  # El archivo completo de 80 m mide ~180 MB


class Dem:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"DEM file not found: {self.path}")

        if self.path.stat().st_size < MIN_COARSE_DEM_BYTES:
            raise RuntimeError(
                f"DEM file {self.path.name} is incomplete ({self.path.stat().st_size} bytes, "
                f"expected >= {MIN_COARSE_DEM_BYTES} bytes)"
            )

        self.ds = rasterio.open(str(self.path))
        self.res = self.ds.res
        self.bounds = self.ds.bounds
        self.nodata = self.ds.nodata

        # Carga en memoria
        self.z = self.ds.read(1).astype("float32")
        if self.nodata is not None:
            self.z[self.z == self.nodata] = np.nan

        self.to_xy = Transformer.from_crs(MOON_GEO, self.ds.crs, always_xy=True)
        self.to_ll = Transformer.from_crs(self.ds.crs, MOON_GEO, always_xy=True)
        self.inv = ~self.ds.transform

    def is_inside(self, lat: float, lon: float) -> bool:
        """Verifica si el punto cae dentro de la cobertura polar del DEM."""
        if not (-90.0 <= lat <= -80.0):
            return False
        x, y = self.xy(lat, lon)
        return (
            self.bounds.left <= x <= self.bounds.right
            and self.bounds.bottom <= y <= self.bounds.top
        )

    def xy(self, lat: float, lon: float) -> Tuple[float, float]:
        return self.to_xy.transform(lon, lat)

    def ll(self, x: float, y: float) -> Tuple[float, float]:
        lon, lat = self.to_ll.transform(x, y)
        return lat, lon

    def sample(self, xs: np.ndarray | list[float], ys: np.ndarray | list[float]) -> np.ndarray:
        cols, rows = self.inv * (np.asarray(xs), np.asarray(ys))
        return map_coordinates(self.z, [rows - 0.5, cols - 0.5], order=1, mode="nearest")


def local_axes(dem: Dem, lat: float, lon: float, d: float = 0.001) -> Tuple[Tuple[float, float], np.ndarray, np.ndarray]:
    x0, y0 = dem.xy(lat, lon)
    xn, yn = dem.xy(lat + d, lon)
    xe, ye = dem.xy(lat, lon + d)

    north = np.array([xn - x0, yn - y0], dtype=float)
    norm_n = np.linalg.norm(north)
    if norm_n > 0:
        north /= norm_n

    east = np.array([xe - x0, ye - y0], dtype=float)
    norm_e = np.linalg.norm(east)
    if norm_e > 0:
        east /= norm_e

    return (x0, y0), north, east


_CACHED_COARSE_DEM: Optional[Dem] = None


def get_coarse_dem() -> Dem:
    global _CACHED_COARSE_DEM
    if _CACHED_COARSE_DEM is None:
        path = DEM_DIR / COARSE_DEM_FILENAME
        if not path.exists():
            candidates = [
                p for p in list(DEM_DIR.glob("*.TIF")) + list(DEM_DIR.glob("*.tif"))
                if p.stat().st_size >= MIN_COARSE_DEM_BYTES
            ]
            if candidates:
                path = candidates[0]
            else:
                raise FileNotFoundError(
                    f"No se encontró el DEM completo en {DEM_DIR} (se esperan >= {MIN_COARSE_DEM_BYTES // (1024*1024)} MB)"
                )
        log.info("Cargando DEM grueso en memoria desde %s ...", path)
        _CACHED_COARSE_DEM = Dem(path)
    return _CACHED_COARSE_DEM
