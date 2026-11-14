"""Módulo de terreno LOLA (NASA) de LunaScope.

Proporciona máscaras de horizonte, estadísticas de pendientes y elevaciones
a partir de Modelos Digitales de Elevación (DEM) polares de LOLA.
"""

from __future__ import annotations

import logging
import numpy as np

from lunascope.terrain.dem import Dem, get_coarse_dem, local_axes
from lunascope.terrain.horizon import compute_horizon
from lunascope.terrain.stats import compute_terrain_stats

log = logging.getLogger("lunascope.terrain")


def sample_elevation(lat: float, lon: float) -> float:
    """Muestrea la elevación del terreno en metros respecto a la esfera de 1 737 400 m.
    
    Lanza ValueError("outside_dem") si las coordenadas caen fuera de cobertura.
    """
    if not (-90.0 <= lat <= -80.0):
        raise ValueError("outside_dem")

    try:
        dem = get_coarse_dem()
    except (FileNotFoundError, RuntimeError) as e:
        log.warning("DEM no disponible (%s), usando aproximación de altura", e)
        from lunascope import mock
        return float(mock.mock_terrain_stats(lat, lon)["elevation_m"])

    if not dem.is_inside(lat, lon):
        raise ValueError("outside_dem")

    x, y = dem.xy(lat, lon)
    val = float(dem.sample([x], [y])[0])
    if np.isnan(val):
        raise ValueError("outside_dem")
    return round(val, 1)


__all__ = [
    "Dem",
    "get_coarse_dem",
    "local_axes",
    "compute_horizon",
    "compute_terrain_stats",
    "sample_elevation",
]
