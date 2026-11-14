"""Genera gráficos científicos para la presentación y el pitch en pitch/img/:
1. pitch/img/sitios.png: Mapa polar del polo sur con los 3 sitios candidatos de Artemis III.
2. pitch/img/horizonte_<site_id>.png: Perfil angular de horizonte (azimut vs elevación).
"""

from __future__ import annotations

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
DATA_DIR = BACKEND / "data"
PITCH_IMG_DIR = ROOT / "pitch" / "img"
PITCH_IMG_DIR.mkdir(parents=True, exist_ok=True)


def plot_sites():
    """Genera el mapa 2D esquemático de los 3 sitios en coordenadas polares."""
    sites_file = DATA_DIR / "sites.json"
    if not sites_file.exists():
        print(f"No se encontró {sites_file}")
        return

    sites = json.loads(sites_file.read_text(encoding="utf-8"))

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    ax.set_theta_zero_location("S")  # 0 grados Este abajo
    ax.set_theta_direction(1)  # Sentido horario o antihorario

    # Latitud de -90 (polo, r=0) a -80 (borde, r=10)
    for s in sites:
        lat, lon = s["lat"], s["lon"]
        r = 90.0 + lat  # distancia al polo sur (r=0 en polo sur)
        theta = np.radians(lon)

        ax.scatter(theta, r, s=150, zorder=5, label=f"{s['name']} ({s['lat']}°, {s['lon']}°)")
        ax.text(
            theta,
            r + 0.3,
            f"{s['name']}\n+{s['elevation_m']} m",
            fontsize=10,
            fontweight="bold",
            ha="center",
            va="bottom",
        )

    ax.set_ylim(0, 10.5)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["-88°S", "-86°S", "-84°S", "-82°S", "-80°S"])
    ax.set_title("LunaScope · Sitios Candidatos Artemis III (Polo Sur Lunar)", fontsize=14, pad=20, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="lower left", bbox_to_anchor=(-0.1, -0.1))

    out_path = PITCH_IMG_DIR / "sitios.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Generado: {out_path}")


def plot_horizon(site_id: str, hz_data: dict):
    """Genera la curva de máscara de horizonte para un sitio."""
    az_step = hz_data.get("az_step_deg", 1.0)
    elevations = hz_data.get("horizon_el_deg", [])
    if not elevations:
        return

    azimuths = np.arange(0, len(elevations)) * az_step

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(azimuths, elevations, color="#1f77b4", lw=2, label="Máscara de relieve (LOLA DEM)")
    ax.fill_between(azimuths, -2, elevations, color="#1f77b4", alpha=0.25)

    # Línea de referencia de altura solar rasante en polo sur (~1.5°)
    ax.axhline(1.5, color="#ff7f0e", linestyle="--", label="Elevación media del Sol (~1.5°)")
    ax.axhline(0.0, color="#7f7f7f", linestyle=":", label="Horizonte esférico local (0°)")

    ax.set_xlim(0, 360)
    ax.set_xticks([0, 90, 180, 270, 360])
    ax.set_xticklabels(["0° (Norte)", "90° (Este)", "180° (Sur)", "270° (Oeste)", "360° (Norte)"])

    ax.set_xlabel("Azimut astronómico local (grados)")
    ax.set_ylabel("Elevación angular (°)")
    site_name = site_id.replace("_", " ").title()
    ax.set_title(f"LunaScope · Máscara de Horizonte: {site_name}", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend(loc="upper right")

    out_path = PITCH_IMG_DIR / f"horizonte_{site_id}.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Generado: {out_path}")


def main():
    plot_sites()
    # Generar horizontes a partir de datos precalculados
    precomputed = DATA_DIR / "precomputed"
    if precomputed.exists():
        for site_dir in precomputed.iterdir():
            if site_dir.is_dir():
                hz_file = site_dir / "horizon.json"
                if hz_file.exists():
                    try:
                        hz_data = json.loads(hz_file.read_text(encoding="utf-8"))
                        plot_horizon(site_dir.name, hz_data)
                    except Exception as e:
                        print(f"Error procesando horizonte para {site_dir.name}: {e}")


if __name__ == "__main__":
    main()
