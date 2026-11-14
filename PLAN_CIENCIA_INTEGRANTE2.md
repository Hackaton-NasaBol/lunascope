# Plan de Implementación: Motor Científico (SPICE)
## LunaScope · Integrante 2 (Ciencia)

> **Misión:** Garantizar la precisión científica del proyecto. Calcular con efemérides oficiales de la NASA (SPICE / DE440) la posición aparente y visibilidad del Sol y la Tierra desde el polo sur de la Luna, cruzarla con el relieve topográfico (LOLA DEM) y proveer la serie temporal oficial `timeseries.json` y la función `compute_timeseries(...)`.

---

## 1. Inventario de Archivos Creados y Verificados

```text
lunascope/
├── data/                                               # (Kernels SPICE descargados, en .gitignore)
│   ├── lunascope.tm                                    # Meta-kernel maestro que lista los kernels
│   ├── naif0012.tls                                    # Leapseconds UTC <-> ET
│   ├── pck00011.tpc                                    # Constantes planetarias y elipsoides
│   ├── de440s.bsp                                      # Efemérides planetarias DE440 (~32 MB)
│   ├── moon_pa_de440_200625.bpc                        # Orientación lunar (Principal Axes, ~13 MB)
│   └── moon_de440_250416.tf                            # Marcos lunares (MOON_ME / MOON_PA)
├── kernels -> data                                     # Enlace simbólico a data/ para compatibilidad
├── backend/
│   ├── scripts/
│   │   ├── download_kernels.py                         # Descargador automático de kernels desde NAIF
│   │   └── validate_horizons.py                        # Script de cotejo automático con JPL Horizons
│   ├── tests/
│   │   └── test_science.py                             # Suite de 14 pruebas unitarias para ciencia
│   └── lunascope/
│       └── science/
│           ├── __init__.py                             # Expone compute_timeseries, kernels_loaded, etc.
│           ├── kernels.py                              # Gestor singleton thread-safe (load_kernels)
│           ├── geometry.py                             # site_vector, enu_basis, az_el, sun_light_vector
│           ├── visibility.py                           # horizon_at, visible_fraction, runs, summarize
│           └── timeseries.py                           # time_grid, compute_geometry, compute_timeseries
├── docs/
│   └── validation.md                                   # Reporte de validación formal vs JPL Horizons
└── backend/data/precomputed/
    ├── malapert/timeseries.json                        # Serie temporal real SPICE para Malapert Massif
    ├── haworth/timeseries.json                         # Serie temporal real SPICE para Haworth Crater
    └── mons_mouton_plateau/timeseries.json             # Serie temporal real SPICE para Mons Mouton Plateau
```

---

## 2. Convenciones y Parámetros Científicos

| Parámetro | Valor / Convención | Justificación |
|---|---|---|
| **Marco de Referencia** | `MOON_ME` (Mean Earth / Polar Axis) | El mismo estándar que utiliza el altímetro LOLA. |
| **Esfera Lunar de Referencia** | $R = 1\,737\,400\text{ m}$ ($1\,737.4\text{ km}$) | Radio medio selenocéntrico LOLA/SPICE. |
| **Altura del Observador** | `height_m` = `elevation_m + 2.0` m | Altura total sobre la esfera de referencia (el backend ya suma los $+2\text{ m}$ del mástil). |
| **Paso Temporal** | $1\text{ hora}$ (sitios fijos) / $2\text{ horas}$ (`/point`) | Balance exacto entre resolución y rendimiento. |
| **Ventana de Misión** | $60\text{ días}$ (1441 muestras a paso de 1 h) | Cubre dos días lunares completos (`2027-09-01` a `2027-10-31`). |
| **Radio Angular del Sol** | $0.267^\circ$ | Para cálculo de fracción visible de disco. |
| **Radio Angular de la Tierra** | $0.95^\circ$ | Radio angular aparente medio desde la superficie lunar. |
| **Convención de Azimut** | $0^\circ \text{ a } 360^\circ$, sentido horario desde el Norte local | $N = 0^\circ, E = 90^\circ, S = 180^\circ, W = 270^\circ$. |
| **Criterio de Visibilidad** | $\text{visible\_fraction} \ge 0.5$ | Al menos el 50% del disco sobre el horizonte. |

---

## 3. Estado del Plan de Trabajo Paso a Paso

### Fase 0: Preparación del Entorno y Kernels (Completado ✅)
- [x] Carpeta `lunascope/data/` creada con los 5 kernels de NAIF descargados y verificados (`naif0012.tls`, `pck00011.tpc`, `de440s.bsp`, `moon_pa_de440_200625.bpc`, `moon_de440_250416.tf`).
- [x] Meta-kernel `data/lunascope.tm` generado y script `backend/scripts/download_kernels.py` listo para reproducir la descarga.
- [x] Symlink `kernels -> data` creado en la raíz y `.gitignore` actualizado.

---

### Fase 1: Esqueleto y Geometría Orbital (Completado ✅)
*Rama de trabajo:* `feat/science`

1. **`backend/lunascope/science/kernels.py`:**
   - [x] `load_kernels()` idempotente y *thread-safe* con rutas absolutas (independiente del directorio de trabajo).
   - [x] `kernels_loaded() -> bool` integrado automáticamente con `/api/health` a través de `lunascope/pipeline.py`.

2. **`backend/lunascope/science/geometry.py`:**
   - [x] **`site_vector(lat_deg, lon_deg, height_m)`:**
     $$r_{\text{sitio}} = \text{sp.latrec}\left(1737.4 + \frac{\text{height\_m}}{1000}, \lambda_{\text{rad}}, \phi_{\text{rad}}\right)$$
     *(Con guardia `ValueError("too_close_to_pole")` si $|\text{lat}| > 89.99^\circ$).*
   - [x] **`enu_basis(site_vec)`:**
     $$\hat{u} = \frac{r_{\text{sitio}}}{\|r_{\text{sitio}}\|}, \quad \hat{e} = \frac{\hat{z} \times \hat{u}}{\|\hat{z} \times \hat{u}\|}, \quad \hat{n} = \hat{u} \times \hat{e}$$
   - [x] **`az_el(target, ets, site_vec, basis)`:**
     - Posiciones aparentes con `sp.spkpos(target, ets, "MOON_ME", "LT+S", "MOON")` vectorizadas sobre el array `ets`.
     - Proyección en la base ENU:
       $$\text{el} = \arcsin\left(\text{clip}(\hat{v} \cdot \hat{u}, -1, 1)\right) \times \frac{180}{\pi}$$
       $$\text{az} = \text{atan2}(\hat{v} \cdot \hat{e}, \hat{v} \cdot \hat{n}) \times \frac{180}{\pi} \pmod{360^\circ}$$
   - [x] **`enu_vector` / `sun_light_vector` y `sun_light_direction`:**
     - Vector unitario ENU hacia el Sol y su opuesto para orientar la luz direccional en CesiumJS.

---

### Fase 2: Oclusión, Visibilidad y Series Precomputadas (Completado ✅)
1. **`backend/lunascope/science/visibility.py`:**
   - [x] **`horizon_at(az_deg, horizon_el_deg, az_step_deg=None)`:**
     Interpolación circular lineal continua entre $359^\circ$ y $0^\circ$. Deduce automáticamente el paso ($1^\circ$ para 360 valores en modo `full`, $2^\circ$ para 180 valores en modo `fast`).
   - [x] **`visible_fraction(el, hz_el, radius)`:**
     $$\text{vf} = \text{clip}\left(\frac{\text{el} - \text{hz\_el} + r}{2r}, \, 0.0, \, 1.0\right)$$
   - [x] **`summarize(times, sun_vf, earth_vf, step_h)`:**
     - Porcentajes `sun_visible_pct`, `earth_visible_pct`, `both_visible_pct`.
     - Rachas máximas `longest_dark_h` y `longest_no_earth_h` vectorizadas.
     - Top 10 ventanas simultáneas Sol + Tierra (`windows`) ordenadas por duración.

2. **`backend/lunascope/science/timeseries.py`:**
   - [x] **`time_grid(start, end, step_h)`:** Convierte `start` con un único `sp.str2et` y suma $3600 \cdot \text{step\_h} \cdot k$ segundos linealmente.
   - [x] **`compute_timeseries(...)`:** Cumple el contrato `Timeseries` de Pydantic en `backend/app/models.py`, con soporte de respaldo (`horizon_el_deg=None` $\rightarrow$ horizonte plano $0^\circ$ y `"horizon": "none"`).
   - [x] **Series temporales generadas con SPICE real (`scripts/precompute.py`):**
     - `malapert`: 1441 muestras · Sol 55.9% · Tierra 64.3% · noche máx 302 h (0.2 s)
     - `haworth`: 1441 muestras · Sol 49.6% · Tierra 53.2% · noche máx 313 h (0.2 s)
     - `mons_mouton_plateau`: 1441 muestras · Sol 51.8% · Tierra 65.1% · noche máx 333 h (0.2 s)

---

### Fase 3: Integración con Terreno Real LOLA (Listo para cuando el Integrante 3 entregue DEM)
- [x] El pipeline (`backend/lunascope/pipeline.py`) y `scripts/precompute.py` ya enlazan automáticamente `science/` (REAL) con `terrain/`.
- [ ] En cuanto el Integrante 3 suba `lunascope/terrain/` y los GeoTIFF LOLA, ejecutar `python scripts/precompute.py` para regenerar los 3 sitios con las máscaras de horizonte reales y verificar juntos el azimut de una cumbre conocida.

---

### Fase 4: Validación Formal con JPL Horizons (Completado ✅)
- [x] **`backend/scripts/validate_horizons.py`:** Consulta en vivo la API oficial de JPL Horizons (`https://ssd.jpl.nasa.gov/api/horizons.api`) para un observador en `coord@301`.
- [x] **`docs/validation.md` generado:**
  - Separación angular máxima entre LunaScope (SPICE local) y JPL Horizons: **$< 0.0001^\circ$ (`0.0000°` a 4 decimales)** tanto para el Sol como para la Tierra, muy por debajo del umbral de $0.1^\circ$ exigido por el contrato.

---

### Fase 5: Soporte al Frontend y Pruebas Unitarias (Completado ✅)
- [x] **Funciones para CesiumJS:** `sun_light_vector(az_deg, el_deg)` y `sun_light_direction(az_deg, el_deg)` exportadas en `lunascope.science`.
- [x] **Suite de pruebas (`backend/tests/test_science.py`):** 14 tests unitarios y de integración pasando al 100% (y los 42 tests totales del backend en `test_api.py`, `test_science.py` y `test_scoring.py` en verde en 2.7 s).

---

## 4. Comandos Rápidos de Uso (desde `backend/`)

```bash
# 1. Ejecutar todos los tests (ciencia + API + scoring)
.venv/bin/python -m pytest -v

# 2. Regenerar los timeseries.json precomputados de los 3 sitios
.venv/bin/python scripts/precompute.py

# 3. Re-ejecutar validación contra JPL Horizons (requiere internet)
.venv/bin/python scripts/validate_horizons.py
```
