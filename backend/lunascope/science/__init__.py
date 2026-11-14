"""Motor científico de LunaScope (Integrante 2).

API pública (parte del contrato):
- ``compute_timeseries(lat, lon, height_m, horizon_el_deg, start, end, step_h, site_id)``
- ``kernels_loaded()`` → bool, lo usa /api/health.
"""

from .geometry import enu_vector, sun_light_direction, sun_light_vector
from .kernels import kernels_loaded, load_kernels, loaded_kernel_names
from .timeseries import compute_geometry, compute_timeseries, time_grid

__all__ = [
    "compute_timeseries",
    "compute_geometry",
    "time_grid",
    "kernels_loaded",
    "load_kernels",
    "loaded_kernel_names",
    "enu_vector",
    "sun_light_vector",
    "sun_light_direction",
]

