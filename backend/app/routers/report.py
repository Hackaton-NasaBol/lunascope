from datetime import datetime, timezone

from fastapi import APIRouter

from app import scenario
from app.config import fmt_utc, parse_utc
from app.errors import not_found
from app.models import Report, ReportIn
from app.routers.score import compute_ranking
from app.store import KINDS, store
from lunascope import pipeline
from lunascope.scoring import PROFILES

router = APIRouter(tags=["report"])


def loaded_kernel_names() -> list[str]:
    try:
        from lunascope.science import loaded_kernel_names as names  # type: ignore
        return names()
    except Exception:
        return []

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


def _data_sources(site_id: str) -> list[str]:
    """Fuentes por componente: Sol/Tierra (science/) y terreno (terrain/) pueden ser reales o mock por separado."""
    d = store.points[site_id] if site_id in store.points else {k: store.get(site_id, k) for k in KINDS}
    is_mock = lambda k: (d.get(k) or {}).get("source") == "mock"  # noqa: E731
    out = []
    if is_mock("timeseries"):
        out.append("Sol y Tierra: DATOS DE PRUEBA (mock), geometría aproximada sin SPICE.")
    else:
        kernels = loaded_kernel_names() if pipeline.SCIENCE else []
        out.append("Sol y Tierra: NASA NAIF SPICE, marco MOON_ME"
                   + (f" ({', '.join(kernels)})" if kernels else " (efemérides DE440)") + ".")
    if is_mock("horizon") or is_mock("terrain"):
        out.append("Terreno (horizonte, elevación, pendientes): DATOS DE PRUEBA (mock), sin DEM LOLA.")
    else:
        h = d.get("horizon") or {}
        out.append(f"Terreno: LRO LOLA DEM ({h.get('dem_source', 'producto polar')}, "
                   f"{h.get('dem_resolution_m', '?')} m/píxel en el horizonte).")
    return out


@router.post("/report", response_model=Report)
def report(body: ReportIn):
    site, _, source, point_id = _lookup(body.site_id)
    ts = scenario.series(body.site_id, body.start, body.days)
    ranking = compute_ranking(body.profile, point_id, body.start, body.days)
    rows = ranking["ranking"]
    idx = next((i for i, r in enumerate(rows) if r["site_id"] == body.site_id), None)
    if idx is None:
        raise not_found("site_data", body.site_id)
    row = rows[idx]
    windows = (ts or {}).get("summary", {}).get("windows") or []

    data_sources = _data_sources(body.site_id)

    return {
        "title": f"Informe de planificación — {site['name']}",
        "generated_at": fmt_utc(datetime.now(timezone.utc)),
        "profile": PROFILES[body.profile],
        # La elevación buena es la del terreno (DEM); la de sites.json puede ser un marcador.
        "site": {**{k: site[k] for k in ("id", "name", "lat", "lon")},
                 "elevation_m": (store.get(body.site_id, "terrain") or {}).get("elevation_m", site["elevation_m"])},
        "quality": row["quality"],
        "score": row["score"],
        "rank": idx + 1,
        "breakdown": row["breakdown"],
        "best_window": windows[0] if windows else None,
        "mission_window": {"start": ts["start"], "end": ts["end"],
                           "hours": (parse_utc(ts["end"]) - parse_utc(ts["start"])).total_seconds() / 3600},
        "explanation": row["explanation"] + ranking["notes"],
        "comparison": [{"site_id": r["site_id"], "score": r["score"]} for r in rows],
        "data_sources": data_sources,
        "limitations": LIMITATIONS,
    }
