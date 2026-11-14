"""Cruce con la máscara de horizonte, fracción visible del disco y resumen.

Definiciones del contrato:
- visible_fraction = clip((el − horizon_el + r) / (2r), 0, 1)
- "Visible" = visible_fraction ≥ 0.5
- windows = intervalos continuos con Sol Y Tierra visibles, de más largo a más
  corto, máximo 10. ``hours`` = end − start.
- longest_dark_h = racha más larga sin Sol visible (muestras × step_h).
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

SUN_RADIUS_DEG = 0.267
EARTH_RADIUS_DEG = 0.95
VISIBLE_THRESHOLD = 0.5
MAX_WINDOWS = 10


def fmt_utc(t: datetime) -> str:
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def horizon_at(az_deg, horizon_el_deg, az_step_deg: float | None = None) -> np.ndarray:
    """Interpolación lineal circular de la máscara (índice i = azimut i·paso).

    Si no se da el paso, se deduce de la longitud: 360 valores → 1°, 180 → 2°.
    """
    h = np.asarray(horizon_el_deg, dtype=float)
    if h.ndim != 1 or h.size == 0:
        raise ValueError("horizon_el_deg debe ser una lista no vacía")
    step = float(az_step_deg) if az_step_deg else 360.0 / h.size
    x = np.mod(np.asarray(az_deg, dtype=float), 360.0) / step
    i0 = np.floor(x).astype(int) % h.size
    i1 = (i0 + 1) % h.size
    f = x - np.floor(x)
    return h[i0] * (1.0 - f) + h[i1] * f


def visible_fraction(el, horizon_el, r: float) -> np.ndarray:
    return np.clip((np.asarray(el) - np.asarray(horizon_el) + r) / (2.0 * r), 0.0, 1.0)


def runs(mask) -> list[tuple[int, int]]:
    """Rachas de True como pares (inicio, fin) inclusivos. Vectorizado."""
    m = np.asarray(mask, dtype=bool)
    if m.size == 0:
        return []
    d = np.diff(np.concatenate(([0], m.astype(np.int8), [0])))
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1) - 1
    return list(zip(starts.tolist(), ends.tolist()))


def longest_run_h(mask, step_h: float) -> float:
    r = runs(mask)
    return float(max(((b - a + 1) for a, b in r), default=0) * step_h)


def summarize(times: list[datetime], s_vf, e_vf, step_h: float) -> dict:
    sun = np.asarray(s_vf) >= VISIBLE_THRESHOLD
    earth = np.asarray(e_vf) >= VISIBLE_THRESHOLD
    both = sun & earth
    wins = sorted(runs(both), key=lambda ab: (-(ab[1] - ab[0]), ab[0]))[:MAX_WINDOWS]
    return {
        "sun_visible_pct": round(100.0 * float(sun.mean()), 1),
        "earth_visible_pct": round(100.0 * float(earth.mean()), 1),
        "both_visible_pct": round(100.0 * float(both.mean()), 1),
        "longest_dark_h": longest_run_h(~sun, step_h),
        "longest_no_earth_h": longest_run_h(~earth, step_h),
        "windows": [
            {"start": fmt_utc(times[a]), "end": fmt_utc(times[b]), "hours": float((b - a) * step_h)}
            for a, b in wins
        ],
    }

