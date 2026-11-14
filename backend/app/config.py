"""Rutas, ventana de la misión y constantes del contrato (docs/contract.md)."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
SITES_FILE = DATA_DIR / "sites.json"
PRECOMPUTED_DIR = DATA_DIR / "precomputed"
KERNELS_DIR = REPO_DIR / "kernels"
DEM_DIR = REPO_DIR / "dem"


def parse_utc(s: str) -> datetime:
    """'2027-09-01T00:00:00Z' -> datetime con tz UTC."""
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def fmt_utc(t: datetime) -> str:
    """datetime -> '2027-09-01T00:00:00Z' (convención del contrato)."""
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Ventana de la misión: se fija en la reunión de la H0–3. Se puede cambiar
# con variables de entorno sin tocar el código.
MISSION_START = parse_utc(os.environ.get("LUNASCOPE_MISSION_START", "2027-09-01T00:00:00Z"))
MISSION_DAYS = int(os.environ.get("LUNASCOPE_MISSION_DAYS", "60"))
MISSION_END = MISSION_START + timedelta(days=MISSION_DAYS)

STEP_HOURS = 1
POINT_STEP_HOURS = 2  # puntos libres: análisis simplificado

OBSERVER_HEIGHT_M = 2.0
MOON_RADIUS_M = 1_737_400.0
SUN_RADIUS_DEG = 0.267
EARTH_RADIUS_DEG = 0.95
HAZARD_SLOPE_DEG = 10.0
VISIBLE_THRESHOLD = 0.5
TERRAIN_RADIUS_M = 100

CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
