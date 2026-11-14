import logging
import time

from fastapi import APIRouter

from app import config
from app.errors import ApiError
from app.models import PointIn, PointOut
from app.store import store
from lunascope import pipeline

router = APIRouter(tags=["point"])
log = logging.getLogger("lunascope.point")


@router.post("/point", response_model=PointOut)
def point(body: PointIn):
    t0 = time.time()
    if pipeline.outside_dem(body.lat, body.lon):
        raise ApiError(422, "outside_dem", "El punto está fuera de la cobertura del DEM LOLA.")
    try:
        terrain = pipeline.terrain_stats(body.lat, body.lon, config.TERRAIN_RADIUS_M)
        horizon = pipeline.horizon(body.lat, body.lon, "fast", config.OBSERVER_HEIGHT_M)
        ts = pipeline.timeseries(body.lat, body.lon, terrain["elevation_m"] + config.OBSERVER_HEIGHT_M,
                                 horizon, config.MISSION_START, config.MISSION_END,
                                 config.POINT_STEP_HOURS)
    except ValueError as e:
        if str(e) == "outside_dem":
            raise ApiError(422, "outside_dem", "El punto está fuera de la cobertura del DEM LOLA.")
        if str(e) == "too_close_to_pole":  # science/: la base ENU no está definida en el polo exacto
            raise ApiError(422, "too_close_to_pole", "El punto está demasiado cerca del polo (< 0,01°).")
        raise
    site = {
        "id": "",
        "name": f"Punto libre ({body.lat:.2f}°, {body.lon:.2f}°)",
        "region": "Punto libre (estimado)",
        "lat": body.lat,
        "lon": body.lon,
        "elevation_m": terrain["elevation_m"],
        "notes": "Análisis simplificado: horizonte de 50 km y paso de 2 h.",
    }
    p = {"quality": "estimated", "site": site, "horizon": horizon, "terrain": terrain, "timeseries": ts}
    pid = store.add_point(p)
    elapsed = round(time.time() - t0, 2)
    log.info("point %s en %.2fs", pid, elapsed)
    return {**p, "elapsed_s": elapsed}
