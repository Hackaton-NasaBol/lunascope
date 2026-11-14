from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import fmt_utc
from app.errors import not_found
from app.models import Report, ReportIn
from app.routers.score import compute_ranking
from app.store import store
from lunascope.scoring import PROFILES

router = APIRouter(tags=["report"])

LIMITATIONS = [
    "Visibilidad geométrica: no incluye enlaces de radio ni cobertura de satélites.",
    "La fracción visible del disco es una aproximación lineal.",
    "Puntos libres: horizonte de menor alcance (50 km) y resolución, paso de 2 h.",
    "La escala de la proyección polar estereográfica varía < 1 % cerca del polo y se ignora.",
    "Las sombras de la escena 3D usan el terreno de Cesium, que no es exactamente el DEM LOLA.",
]


def _lookup(site_id: str):
    if site_id in store.sites:
        return store.sites[site_id], store.get(site_id, "timeseries"), store.source(site_id), None
    if site_id in store.points:
        p = store.points[site_id]
        return p["site"], p["timeseries"], p["timeseries"].get("source", "real"), site_id
    raise not_found("site", site_id)


@router.post("/report", response_model=Report)
def report(body: ReportIn):
    site, ts, source, point_id = _lookup(body.site_id)
    ranking = compute_ranking(body.profile, point_id)
    rows = ranking["ranking"]
    idx = next((i for i, r in enumerate(rows) if r["site_id"] == body.site_id), None)
    if idx is None:
        raise not_found("site_data", body.site_id)
    row = rows[idx]
    windows = (ts or {}).get("summary", {}).get("windows") or []

    if source == "mock":
        data_sources = ["DATOS DE PRUEBA (mock): geometría aproximada, sin SPICE ni DEM reales."]
    else:
        data_sources = [
            "NASA NAIF SPICE (efemérides DE440, marco lunar MOON_ME)",
            "LRO LOLA DEM polar (máscara de horizonte, elevación y pendientes)",
            # TODO(Int. 1, H12): poner aquí los nombres exactos de kernels y productos DEM usados.
        ]

    return {
        "title": f"Informe de planificación — {site['name']}",
        "generated_at": fmt_utc(datetime.now(timezone.utc)),
        "profile": PROFILES[body.profile],
        "site": {k: site[k] for k in ("id", "name", "lat", "lon", "elevation_m")},
        "quality": row["quality"],
        "score": row["score"],
        "rank": idx + 1,
        "breakdown": row["breakdown"],
        "best_window": windows[0] if windows else None,
        "explanation": row["explanation"] + ranking["notes"],
        "comparison": [{"site_id": r["site_id"], "score": r["score"]} for r in rows],
        "data_sources": data_sources,
        "limitations": LIMITATIONS,
    }
