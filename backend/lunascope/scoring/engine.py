"""Motor de decisión explicable: subpuntuaciones, puntuación y ranking."""

from lunascope.scoring.explain import ESTIMATED_TOP_NOTE, explain
from lunascope.scoring.profiles import PROFILES


def subscores(summary: dict, terrain: dict) -> dict:
    return {
        "sun": round(float(summary["sun_visible_pct"]), 1),
        "earth": round(float(summary["earth_visible_pct"]), 1),
        "continuity": round(100 * max(0.0, 1 - summary["longest_dark_h"] / 240), 1),
        "terrain": round(
            100 * max(0.0, 1 - terrain["slope_deg_mean"] / 15) * (1 - terrain["hazard_pct"] / 100), 1
        ),
    }


def score_site(sub: dict, weights: dict) -> float:
    return round(sum(weights[k] * sub[k] for k in weights), 1)


def rank(candidates: list[dict], profile_id: str) -> dict:
    """candidates: [{"id", "name", "quality", "summary", "terrain"}, ...].

    Un candidato "estimated" puede aparecer en el ranking pero nunca es
    "recommended".
    """
    if profile_id not in PROFILES:
        raise KeyError(profile_id)
    w = PROFILES[profile_id]["weights"]
    rows = []
    for c in candidates:
        sub = subscores(c["summary"], c["terrain"])
        rows.append({
            "site_id": c["id"],
            "score": score_site(sub, w),
            "quality": c.get("quality", "full"),
            "breakdown": sub,
            "_summary": c["summary"],
            "_name": c.get("name", c["id"]),
        })
    rows.sort(key=lambda r: r["score"], reverse=True)

    full = [r for r in rows if r["quality"] == "full"]
    recommended = full[0]["site_id"] if full else None
    notes = []
    if rows and rows[0]["quality"] != "full" and full:
        notes.append(ESTIMATED_TOP_NOTE)

    for r in rows:
        r["explanation"] = explain(r, rows, profile_id, recommended)
    for r in rows:
        r.pop("_summary")
        r.pop("_name")
    return {"profile": profile_id, "recommended": recommended, "ranking": rows, "notes": notes}
