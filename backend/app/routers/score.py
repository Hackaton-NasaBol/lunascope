from typing import Optional

from fastapi import APIRouter

from app import scenario
from app.errors import ApiError, not_found
from app.models import Profile, ScoreOut
from app.store import store
from lunascope.scoring import PROFILES, rank

router = APIRouter(tags=["score"])


@router.get("/profiles", response_model=list[Profile])
def profiles():
    return list(PROFILES.values())


def candidates(point_id: Optional[str] = None, start: Optional[str] = None, days: Optional[int] = None) -> list[dict]:
    """Candidatos con el resumen de la ventana pedida (por defecto, la precalculada)."""
    out = []
    for sid, site in store.sites.items():
        terrain = store.get(sid, "terrain")
        if not terrain or not store.get(sid, "horizon"):
            continue
        ts = scenario.series(sid, start, days)
        out.append({"id": sid, "name": site["name"], "quality": "full",
                    "summary": ts["summary"], "terrain": terrain})
    if point_id:
        p = store.points.get(point_id)
        if p is None:
            raise not_found("point", point_id)
        out.append({"id": point_id, "name": p["site"]["name"], "quality": "estimated",
                    "summary": scenario.series(point_id, start, days)["summary"], "terrain": p["terrain"]})
    return out


def compute_ranking(profile: str, point_id: Optional[str] = None,
                    start: Optional[str] = None, days: Optional[int] = None) -> dict:
    if profile not in PROFILES:
        raise ApiError(404, "profile_not_found",
                       f"Perfil '{profile}' desconocido. Opciones: {', '.join(PROFILES)}.")
    cands = candidates(point_id, start, days)
    if not any(c["quality"] == "full" for c in cands):
        raise ApiError(503, "data_missing", "Ningún sitio tiene datos precalculados completos.")
    return rank(cands, profile)


@router.get("/score", response_model=ScoreOut)
def score(profile: str = "solar", point_id: Optional[str] = None,
          start: Optional[str] = None, days: Optional[int] = None):
    return compute_ranking(profile, point_id, start, days)
