from fastapi import APIRouter

from app.errors import ApiError, not_found
from app.models import Horizon, SiteOverview, Terrain, Timeseries
from app.store import store

router = APIRouter(tags=["sites"])


@router.get("/sites", response_model=list[SiteOverview])
def list_sites():
    out = []
    for sid, site in store.sites.items():
        ts = store.get(sid, "timeseries")
        out.append({
            **site,
            "quality": "full",
            "complete": store.is_complete(sid),
            "source": store.source(sid),
            "terrain": store.get(sid, "terrain"),
            "summary": ts["summary"] if ts else None,
        })
    return out


def _get(site_id: str, kind: str) -> dict:
    if site_id in store.points:
        return store.points[site_id][kind]
    if site_id not in store.sites:
        raise not_found("site", site_id)
    data = store.get(site_id, kind)
    if data is None:
        raise ApiError(503, "data_missing", f"El sitio '{site_id}' no tiene {kind}.json precalculado.")
    return data


@router.get("/sites/{site_id}/horizon", response_model=Horizon)
def horizon(site_id: str):
    return _get(site_id, "horizon")


@router.get("/sites/{site_id}/terrain", response_model=Terrain)
def terrain(site_id: str):
    return _get(site_id, "terrain")


@router.get("/sites/{site_id}/timeseries", response_model=Timeseries)
def timeseries(site_id: str):
    return _get(site_id, "timeseries")
