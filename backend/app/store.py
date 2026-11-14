"""Carga y cachea en memoria sites.json y los JSON precalculados.

Si falta un archivo, se registra un aviso y el sitio queda incompleto: el
servidor nunca se cae por datos ausentes.
"""

from __future__ import annotations

import itertools
import json
import logging
import threading
from pathlib import Path

from app.config import PRECOMPUTED_DIR, SITES_FILE

log = logging.getLogger("lunascope.store")
KINDS = ("horizon", "terrain", "timeseries")


def _read(path: Path):
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        log.warning("Falta %s", path)
    except json.JSONDecodeError as e:
        log.error("JSON inválido en %s: %s", path, e)
    return None


class Store:
    def __init__(self) -> None:
        self.sites: dict[str, dict] = {}
        self.data: dict[str, dict[str, dict | None]] = {}
        self.points: dict[str, dict] = {}
        self.kernels_loaded = False
        self._ids = itertools.count(1)
        self._lock = threading.Lock()

    def load_all(self, sites_file: Path = SITES_FILE, precomputed: Path = PRECOMPUTED_DIR) -> None:
        sites = _read(sites_file) or []
        self.sites = {s["id"]: s for s in sites}
        self.data = {sid: {k: _read(precomputed / sid / f"{k}.json") for k in KINDS} for sid in self.sites}
        for sid, d in self.data.items():
            missing = [k for k, v in d.items() if v is None]
            if missing:
                log.warning("Sitio %s incompleto: faltan %s", sid, ", ".join(missing))
        log.info("Cargados %d sitios desde %s", len(self.sites), precomputed)

    def get(self, site_id: str, kind: str) -> dict | None:
        return self.data.get(site_id, {}).get(kind)

    def is_complete(self, site_id: str) -> bool:
        return all(self.data.get(site_id, {}).get(k) is not None for k in KINDS)

    def source(self, site_id: str) -> str:
        d = self.data.get(site_id, {})
        return "mock" if any((v or {}).get("source") == "mock" for v in d.values()) else "real"

    def add_point(self, point: dict) -> str:
        with self._lock:
            pid = f"p-{next(self._ids)}"
            point["point_id"] = pid
            point["site"]["id"] = pid
            for k in KINDS:
                point[k]["site_id"] = pid
            self.points[pid] = point
        return pid


store = Store()
