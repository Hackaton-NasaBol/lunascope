from typing import Optional

from fastapi import APIRouter

from app.errors import ApiError, not_found
from app.models import Profile, ScoreOut
from app.store import store
from lunascope.scoring import PROFILES, rank

router = APIRouter(tags=["score"])


@router.get("/profiles", response_model=list[Profile])
def profiles():
    return list(PROFILES.values())


def candidates(point_id: Optional[str] = None) -> list[dict]:
    out = []
    for sid, site in store.sites.items():
        ts, terrain = store.get(sid, "timeseries"), store.get(sid, "terrain")
        if ts and terrain:
            out.append({"id": sid, "name": site["name"], "quality": "full",
                        "summary": ts["summary"], "terrain": terrain})
    if point_id:
        p = store.points.get(point_id)
        if p is None:
            raise not_found("point", point_id)
        out.append({"id": point_id, "name": p["site"]["name"], "quality": "estimated",
                    "summary": p["timeseries"]["summary"], "terrain": p["terrain"]})
    return out


def compute_ranking(profile: str, point_id: Optional[str] = None) -> dict:
    if profile not in PROFILES:
        raise ApiError(404, "profile_not_found",
                       f"Perfil '{profile}' desconocido. Opciones: {', '.join(PROFILES)}.")
    cands = candidates(point_id)
    if not any(c["quality"] == "full" for c in cands):
        raise ApiError(503, "data_missing", "Ningún sitio tiene datos precalculados completos.")
    return rank(cands, profile)


@router.get("/score", response_model=ScoreOut)
def score(profile: str = "solar", point_id: Optional[str] = None):
    return compute_ranking(profile, point_id)
