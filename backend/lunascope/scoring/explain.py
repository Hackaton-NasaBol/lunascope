"""Explicaciones en texto generadas con plantillas a partir de los números.

Nada de texto inventado: cada frase cita un valor del resumen o del terreno.
"""

from app.config import parse_utc
from lunascope.scoring.profiles import PROFILES, SUBSCORE_NAMES

ESTIMATED_TOP_NOTE = "El punto libre puntúa más alto, pero su análisis es aproximado."

_MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _num(x: float, nd: int = 1) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def fmt_date(iso: str) -> str:
    t = parse_utc(iso)
    return f"{t.day} {_MONTHS[t.month - 1]} {t:%H:%M} UTC"


def _fact(key: str, row: dict) -> str:
    s, b = row["_summary"], row["breakdown"]
    if key == "sun":
        return f"tiene Sol visible el {s['sun_visible_pct']:.0f} % del tiempo"
    if key == "earth":
        return f"ve la Tierra el {s['earth_visible_pct']:.0f} % del tiempo"
    if key == "continuity":
        return f"su noche más larga dura {s['longest_dark_h']:.0f} h"
    return f"su terreno puntúa {b['terrain']:.0f}/100 (pendiente y zonas de más de 10°)"


def _position(key: str, row: dict, rows: list[dict]) -> tuple[int, int]:
    """Puesto (1 = mejor) del candidato en esa subpuntuación; 0 si todos empatan."""
    vals = sorted((r["breakdown"][key] for r in rows), reverse=True)
    if vals[0] == vals[-1]:
        return 0, len(rows)
    return vals.index(row["breakdown"][key]) + 1, len(rows)


def _pos_text(pos: int, n: int, group: str) -> str:
    if n == 1:
        return ""
    if pos == 0:
        return f" (en esto empatan los {n} {group})"
    if pos == 1:
        return f", el mejor de los {n} {group}"
    if pos == n:
        return f", el peor de los {n} {group}"
    return f", puesto {pos} de {n}"


def explain(row: dict, rows: list[dict], profile_id: str, recommended: str | None) -> list[str]:
    profile = PROFILES[profile_id]
    group = "sitios" if all(r["quality"] == "full" for r in rows) else "candidatos"
    b = row["breakdown"]
    out = []

    best = max(b, key=b.get)
    pos, n = _position(best, row, rows)
    out.append(f"Su punto fuerte: {_fact(best, row)}{_pos_text(pos, n, group)}.")

    worst = min(b, key=b.get)
    if worst != best:
        pos, n = _position(worst, row, rows)
        out.append(f"Punto débil: {_fact(worst, row)}{_pos_text(pos, n, group)}.")

    if row["quality"] != "full":
        is_top = rows[0] is row
        out.append(ESTIMATED_TOP_NOTE if is_top and recommended
                   else "Punto libre: análisis aproximado (horizonte de menor alcance y resolución).")
    else:
        key = max(profile["weights"], key=profile["weights"].get)
        out.append(
            f"Con el perfil {profile['name']}, {SUBSCORE_NAMES[key]} pesa un "
            f"{profile['weights'][key] * 100:.0f} %."
        )

    windows = row["_summary"].get("windows") or []
    if windows:
        w = windows[0]
        out.append(f"Mejor ventana con Sol y Tierra a la vez: {fmt_date(w['start'])}, {_num(w['hours'], 0)} h.")
    else:
        out.append("No hay ninguna ventana con Sol y Tierra visibles a la vez durante la misión.")
    return out
