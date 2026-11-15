"""Descarga el DEM LOLA del polo sur (80°S–90°S, 80 m/píxel, ~190 MB) a <repo>/dem/.

Uso (desde cualquier carpeta):
    python backend/scripts/download_dem.py

Fuente: NASA Goddard PGDA, producto 90 (https://pgda.gsfc.nasa.gov/products/90).
Descarga por bloques y reanuda si se corta (útil con conexiones lentas).
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

URL = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF"
DEST = Path(__file__).resolve().parents[2] / "dem" / "LDEM_80S_80MPP_ADJ.TIF"
UA = {"User-Agent": "LunaScope/1.0"}
CHUNK = 1 << 20


def total_size() -> int:
    req = urllib.request.Request(URL, method="HEAD", headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def main() -> int:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    size = total_size()
    part = DEST.with_suffix(".TIF.part")
    if DEST.exists() and DEST.stat().st_size == size:
        print(f"ok   {DEST.name} ya existe ({size / 1e6:.0f} MB)")
        return 0
    for attempt in range(1, 11):
        done = part.stat().st_size if part.exists() else 0
        if done >= size:
            break
        headers = {**UA, "Range": f"bytes={done}-"}
        try:
            with urllib.request.urlopen(urllib.request.Request(URL, headers=headers), timeout=120) as r, part.open("ab") as f:
                while chunk := r.read(CHUNK):
                    f.write(chunk)
                    done += len(chunk)
                    print(f"\r{done / 1e6:6.0f} / {size / 1e6:.0f} MB", end="", flush=True)
        except OSError as e:
            print(f"\nCorte ({e}); reintento {attempt}/10 desde {done / 1e6:.0f} MB")
    print()
    if part.stat().st_size != size:
        print("No se pudo completar la descarga.", file=sys.stderr)
        return 1
    part.replace(DEST)
    print(f"Listo: {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
