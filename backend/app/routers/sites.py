from typing import Optional

from fastapi import APIRouter

from app import config, scenario

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
def timeseries(site_id: str, start: Optional[str] = None, days: Optional[int] = None):
    """Sin parámetros: la ventana por defecto (precalculada). Con start/days: calculada con SPICE al momento."""
    return scenario.series(site_id, start, days)


@router.get("/mission")
def mission():
    """Ventana por defecto, límites de fechas y si este servidor puede calcular otras fechas."""
    return scenario.mission_info()


def _next_change_h(samples: list[dict], body: str, step_h: float) -> tuple[bool, Optional[float]]:
    """¿Se ve al inicio? y horas hasta que deja de verse (o empieza a verse). None = no cambia en la ventana."""
    vis = [s[body]["visible_fraction"] >= 0.5 for s in samples]
    for k in range(1, len(vis)):
        if vis[k] != vis[0]:
            a, b = samples[k - 1][body]["visible_fraction"], samples[k][body]["visible_fraction"]
            frac = (0.5 - a) / (b - a) if b != a else 1.0
            return vis[0], round((k - 1 + min(1.0, max(0.0, frac))) * step_h, 1)
    return vis[0], None


@router.get("/scenario")
def scenario_summary(start: Optional[str] = None, days: Optional[int] = None, profile: str = "solar",
                     point_id: Optional[str] = None):
    """Resumen de una fecha de misión para todos los sitios: lo que se ve en el panel de fecha.

    Por sitio: % de Sol y Tierra, noche más larga, mejor ventana, qué pasa al aterrizar (¿hay Sol/Tierra y
    cuánto falta para que cambie?) y la puntuación con el perfil. Más el sitio recomendado.
    """
    from app.routers.score import compute_ranking

    t0, n = scenario.window(start, days)
    pid = point_id if point_id in store.points else None
    ids = [sid for sid in store.sites if store.get(sid, "horizon") and store.get(sid, "terrain")] + ([pid] if pid else [])
    ranking = compute_ranking(profile, pid, start, days)
    scores = {r["site_id"]: r["score"] for r in ranking["ranking"]}
    out, ts = [], None
    for sid in ids:
        ts = scenario.series(sid, start, days)
        s = ts["summary"]
        sun_now, sun_change = _next_change_h(ts["samples"], "sun", ts["step_hours"])
        earth_now, earth_change = _next_change_h(ts["samples"], "earth", ts["step_hours"])
        site = store.points[sid]["site"] if sid in store.points else store.sites[sid]
        out.append({
            "site_id": sid,
            "name": site["name"],
            "quality": "estimated" if sid in store.points else "full",
            "score": scores.get(sid),
            "sun_visible_pct": s["sun_visible_pct"],
            "earth_visible_pct": s["earth_visible_pct"],
            "both_visible_pct": s["both_visible_pct"],
            "longest_dark_h": s["longest_dark_h"],
            "best_window": s["windows"][0] if s["windows"] else None,
            "windows_count": len(s["windows"]),
            "at_landing": {"sun_visible": sun_now, "sun_change_h": sun_change,
                           "earth_visible": earth_now, "earth_change_h": earth_change},
        })
    return {
        "start": ts["start"] if ts else config.fmt_utc(t0),
        "end": ts["end"] if ts else config.fmt_utc(t0),
        "days": n,
        "is_default": scenario.is_default(t0, n),
        "profile": profile,
        "recommended": ranking["recommended"],
        "sites": out,
    }
