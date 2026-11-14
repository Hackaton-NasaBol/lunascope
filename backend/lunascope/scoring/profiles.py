"""Perfiles de misión. Pesos propuestos en el contrato; se votan en la H0–3."""

SUBSCORES = ("sun", "earth", "continuity", "terrain")

SUBSCORE_NAMES = {
    "sun": "el Sol",
    "earth": "la Tierra",
    "continuity": "la continuidad de la luz",
    "terrain": "el terreno",
}

PROFILES: dict[str, dict] = {
    "solar": {
        "id": "solar",
        "name": "Energía solar",
        "weights": {"sun": 0.50, "earth": 0.15, "continuity": 0.20, "terrain": 0.15},
        "mvp": True,
    },
    "comms": {
        "id": "comms",
        "name": "Comunicaciones",
        "weights": {"sun": 0.20, "earth": 0.50, "continuity": 0.10, "terrain": 0.20},
        "mvp": True,
    },
    "safety": {
        "id": "safety",
        "name": "Seguridad de aterrizaje",
        "weights": {"sun": 0.20, "earth": 0.20, "continuity": 0.10, "terrain": 0.50},
        "mvp": False,
    },
    "balanced": {
        "id": "balanced",
        "name": "Equilibrado",
        "weights": {"sun": 0.25, "earth": 0.25, "continuity": 0.25, "terrain": 0.25},
        "mvp": False,
    },
}
