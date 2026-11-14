"""Geometría: del vector SPICE al azimut/elevación local.

Convenciones (docs/contract.md):
- Marco ``MOON_ME``; esfera de referencia de 1 737,4 km.
- Azimut desde el norte local, en sentido horario (N=0, E=90, S=180, O=270), [0, 360).
- Elevación sobre el plano horizontal local (perpendicular al radio).
- Cerca del polo sur, "norte" apunta alejándose del polo.
"""

from __future__ import annotations

import numpy as np
import spiceypy as sp

R_MOON_KM = 1737.4
FRAME = "MOON_ME"
ABCORR = "LT+S"
MIN_POLE_DIST_DEG = 0.01  # la base ENU no está definida en el polo exacto


def site_vector(lat_deg: float, lon_deg: float, height_m: float) -> np.ndarray:
    """Posición del observador en MOON_ME (km).

    ``height_m`` es la altura TOTAL del observador sobre la esfera de referencia
    (elevación del terreno + 2 m de mástil). El backend ya suma los 2 m.
    """
    if abs(lat_deg) > 90.0 - MIN_POLE_DIST_DEG:
        raise ValueError("too_close_to_pole")
    return np.array(sp.latrec(R_MOON_KM + height_m / 1000.0,
                              np.radians(lon_deg), np.radians(lat_deg)))


def enu_basis(site: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Base local (este, norte, arriba) con la Luna como esfera."""
    up = site / np.linalg.norm(site)
    east = np.cross([0.0, 0.0, 1.0], up)
    east /= np.linalg.norm(east)
    north = np.cross(up, east)
    return east, north, up


def target_positions(target: str, ets: np.ndarray) -> np.ndarray:
    """Posición aparente (LT+S) de ``target`` desde el centro de la Luna, (N, 3) km."""
    pos, _ = sp.spkpos(target, np.asarray(ets, dtype=float), FRAME, ABCORR, "MOON")
    return np.atleast_2d(np.asarray(pos, dtype=float))


def az_el_from_vectors(v: np.ndarray, basis) -> tuple[np.ndarray, np.ndarray]:
    """Proyecta vectores sitio→objetivo (N, 3) en la base ENU. Devuelve grados."""
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    e, n, u = basis
    el = np.degrees(np.arcsin(np.clip(v @ u, -1.0, 1.0)))
    az = np.degrees(np.arctan2(v @ e, v @ n)) % 360.0
    return az, el


def az_el(target: str, ets: np.ndarray, site: np.ndarray, basis) -> tuple[np.ndarray, np.ndarray]:
    """Azimut y elevación (grados) de ``target`` vistos desde ``site`` en los tiempos ``ets``."""
    return az_el_from_vectors(target_positions(target, ets) - site, basis)


def enu_vector(az_deg, el_deg) -> np.ndarray:
    """Vector unitario ENU hacia un objeto en (az, el). Forma (..., 3).

    Para la luz de Cesium: transformar con ``Transforms.eastNorthUpToFixedFrame``
    y usar el OPUESTO como dirección de la luz (la luz viaja del Sol al suelo).
    """
    az, el = np.radians(az_deg), np.radians(el_deg)
    return np.stack([np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)], axis=-1)


def sun_light_direction(az_deg, el_deg) -> np.ndarray:
    """Dirección de propagación de la luz solar en ENU (= −vector hacia el Sol)."""
    return -enu_vector(az_deg, el_deg)


sun_light_vector = enu_vector


