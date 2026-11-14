"""Descarga los kernels SPICE de NAIF a <repo>/data (y crea el enlace <repo>/kernels).

Uso (desde cualquier carpeta):
    python backend/scripts/download_kernels.py

Para los kernels con fecha en el nombre (moon_de440_*.tf, moon_pa_de440_*.bpc)
busca en el listado de NAIF la versión más reciente.
"""

from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]
DEST = REPO_DIR / "data"
BASE = "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/"

# (carpeta en NAIF, nombre fijo o regex para elegir el más reciente)
KERNELS = [
    ("lsk/", "naif0012.tls"),
    ("pck/", "pck00011.tpc"),
    ("spk/planets/", "de440s.bsp"),
    ("pck/", re.compile(r"moon_pa_de440_\d+\.bpc")),
    ("fk/satellites/", re.compile(r"moon_de440_\d+\.tf")),
]

UA = {"User-Agent": "LunaScope/1.0"}


def _get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def _latest(folder: str, pattern: re.Pattern) -> str:
    html = _get(BASE + folder).decode("utf-8", "replace")
    names = sorted(set(m.group(0) for m in pattern.finditer(html)))
    if not names:
        raise RuntimeError(f"No hay kernels que coincidan con {pattern.pattern} en {folder}")
    return names[-1]


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    names = []
    for folder, spec in KERNELS:
        name = spec if isinstance(spec, str) else _latest(folder, spec)
        names.append(name)
        out = DEST / name
        if out.exists() and out.stat().st_size > 0:
            print(f"ok   {name} ({out.stat().st_size / 1e6:.1f} MB, ya existe)")
            continue
        print(f"get  {BASE}{folder}{name}")
        tmp = out.with_suffix(out.suffix + ".part")
        tmp.write_bytes(_get(BASE + folder + name))
        tmp.rename(out)
        print(f"ok   {name} ({out.stat().st_size / 1e6:.1f} MB)")

    # Meta-kernel (rutas relativas a la raíz del repo; el código usa rutas absolutas).
    mk = "KPL/MK\n\\begindata\nPATH_VALUES  = ( 'data' )\nPATH_SYMBOLS = ( 'K' )\nKERNELS_TO_LOAD = (\n"
    mk += "".join(f"  '$K/{n}'\n" for n in names) + ")\n\\begintext\n"
    (DEST / "lunascope.tm").write_text(mk)

    link = REPO_DIR / "kernels"
    if not link.exists():
        try:
            link.symlink_to("data", target_is_directory=True)
        except OSError:
            print("aviso: no se pudo crear el enlace kernels -> data (usa LUNASCOPE_KERNELS_DIR)")
    print("Listo:", DEST)
    return 0


if __name__ == "__main__":
    sys.exit(main())

