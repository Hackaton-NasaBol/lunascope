"""Carga idempotente de los kernels SPICE.

Busca los kernels en este orden:
  1. Variable de entorno ``LUNASCOPE_KERNELS_DIR``.
  2. ``<repo>/kernels``  (convención del contrato; en este repo es un enlace a ``data/``).
  3. ``<repo>/data``.

No depende del directorio de trabajo: cada kernel se carga con su ruta absoluta
(el meta-kernel ``lunascope.tm`` usa rutas relativas y solo funciona desde la raíz).
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

import spiceypy as sp

REPO_DIR = Path(__file__).resolve().parents[3]

# Orden de carga: tiempo -> constantes -> orientación -> marcos -> efemérides.
# Se aceptan versiones más nuevas con el mismo patrón (p. ej. moon_de440_*.tf).
KERNEL_PATTERNS = (
    "naif*.tls",
    "pck*.tpc",
    "moon_pa_de440*.bpc",
    "moon_de440*.tf",
    "de440*.bsp",
)

_lock = threading.Lock()
_loaded: list[str] = []


class KernelsNotFoundError(RuntimeError):
    pass


def _candidate_dirs() -> list[Path]:
    dirs = []
    env = os.environ.get("LUNASCOPE_KERNELS_DIR")
    if env:
        dirs.append(Path(env))
    dirs += [REPO_DIR / "kernels", REPO_DIR / "data"]
    return dirs


def find_kernels() -> list[Path]:
    """Devuelve la lista ordenada de kernels del primer directorio completo."""
    tried = []
    for d in _candidate_dirs():
        tried.append(str(d))
        if not d.is_dir():
            continue
        found = []
        for pat in KERNEL_PATTERNS:
            matches = sorted(d.glob(pat))
            if not matches:
                break
            found.append(matches[-1])  # la versión más reciente por nombre
        else:
            return found
    raise KernelsNotFoundError(
        "No se encontraron los 5 kernels SPICE (tls, tpc, bpc, tf, bsp) en: "
        + ", ".join(tried)
        + ". Ejecuta backend/scripts/download_kernels.py."
    )


def load_kernels() -> list[str]:
    """Carga los kernels una sola vez por proceso. Devuelve las rutas cargadas."""
    if _loaded:
        return list(_loaded)
    with _lock:
        if not _loaded:
            for k in find_kernels():
                sp.furnsh(str(k))
                _loaded.append(str(k))
    return list(_loaded)


def kernels_loaded() -> bool:
    """True si los kernels están (o pueden estar) cargados. Lo usa /api/health."""
    try:
        load_kernels()
        return True
    except Exception:
        return False


def loaded_kernel_names() -> list[str]:
    """Nombres de archivo cargados (para el informe y la validación)."""
    return [Path(k).name for k in _loaded]

