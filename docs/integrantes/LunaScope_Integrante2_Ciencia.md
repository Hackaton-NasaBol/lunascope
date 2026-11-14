# LunaScope · Integrante 2 — Motor científico (SPICE)

> **Tu misión:** que los números sean verdad. Calculas dónde están el Sol y la Tierra vistos desde cada sitio lunar, hora por hora, y decides cuándo son visibles teniendo en cuenta el relieve. Eres quien responde las preguntas científicas del jurado.

**Lo que entregas al final:**
1. Paquete `backend/lunascope/science/` con la función `compute_timeseries(...)`, que es parte del contrato.
2. `timeseries.json` de los 3 sitios (lo genera `precompute.py` llamando a tu función).
3. Un informe de validación corto (`docs/validation.md`) que compara tus resultados con JPL Horizons.
4. Apoyo al Integrante 4 para dibujar el Sol y la Tierra en el cielo y orientar la luz de Cesium.

**De quién dependes:** del Integrante 3, que te da la máscara de horizonte (`horizon_el_deg`, 360 valores) y la elevación del sitio.
**Quién depende de ti:** el Integrante 1 (puntuación e informe) y el 4 (gráficos y simulación temporal).

## Parte común: léela completa antes de empezar

Esta sección es **idéntica en los 4 documentos**. Si algo de aquí cambia, lo cambia el Integrante 1 (Tech Lead) y avisa a todos.

### El proyecto en una frase

**LunaScope** es un centro interactivo de planificación lunar en 3D. Usa datos científicos de NASA (SPICE + LOLA) para comparar sitios de aterrizaje en el polo sur de la Luna y recomendar el mejor según el perfil de la misión. Toda la experiencia se controla con un mando PS4.

> No es un videojuego. El mando es la forma de interactuar con una herramienta científica. El nombre ya no lleva "AI": presentamos un **motor de decisión explicable** (reglas y pesos visibles).

### Equipo

| # | Rol | Dueño de | Carpeta del repo |
|---|---|---|---|
| 1 | Backend + motor de decisión | API FastAPI, contrato de datos, puntuación, recomendación, informe, integración | `backend/` |
| 2 | Motor científico | SPICE, posiciones Sol/Tierra, azimut/elevación, cruce con horizonte, ventanas, validación | `backend/lunascope/science/` |
| 3 | Terreno + presentación | DEM LOLA, elevación, pendientes, máscaras de horizonte, coordenadas de los sitios; desde la H22, pitch y video | `backend/lunascope/terrain/` + `pitch/` |
| 4 | Frontend + mando | React + CesiumJS, 3 modos, gráficos, Gamepad API, informe en pantalla | `frontend/` |

### Decisiones cerradas (no se discuten durante el hackathon)

1. **Sitios:** 3 sitios fijos con análisis completo + puntos libres con análisis simplificado (marcados como "estimado").
2. **Origen de los sitios:** 3 de las 9 regiones candidatas de Artemis III anunciadas por NASA en octubre de 2024: Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2 y Slater Plain. **Propuesta inicial:** Malapert Massif, Haworth y Mons Mouton Plateau (se confirma en la H0–3).
3. **Mapa:** globo lunar 3D con CesiumJS + Cesium Moon Terrain (requiere internet y token de Cesium ion).
4. **Modos:** Explore → Mission Time → Mission Selection. El Touchpad pasa al siguiente modo.
5. **Horizonte:** el Integrante 3 produce la máscara de horizonte y el Integrante 2 la cruza con el Sol y la Tierra.
6. **Prioridades de la misión:** perfiles predefinidos que se eligen con la cruceta (ver "Puntuación").
7. **Demo:** backend local + Cesium con internet + video de respaldo. El despliegue público es opcional.

### Convenciones (obligatorias para todos)

Si dos módulos usan convenciones distintas, la integración falla sin dar error. Respeten esto al pie de la letra:

| Cosa | Convención |
|---|---|
| Tiempo | UTC, ISO 8601 con `Z`. Ejemplo: `2027-09-01T00:00:00Z` |
| Latitud | Grados, −90 a +90 (sur negativo) |
| Longitud | Grados **este**, −180 a +180 |
| Azimut | Grados desde el **norte local**, en sentido horario (hacia el este): N = 0, E = 90, S = 180, O = 270. Rango [0, 360) |
| Elevación angular | Grados sobre el **plano horizontal local** (perpendicular al radio lunar en el sitio) |
| Alturas | Metros respecto a la esfera de referencia de **1 737 400 m** (convención LOLA) |
| Marco de referencia | `MOON_ME` (Mean Earth / Polar Axis), el mismo que usa LOLA |
| Altura del observador | +2 m sobre el terreno (antena o mástil del módulo) |
| Paso de tiempo | 1 hora |
| Ventana de la misión | `MISSION_START` + 60 días. Se fija en la H0–3. Ejemplo: `2027-09-01T00:00:00Z` → `2027-10-31T00:00:00Z` (1441 muestras) |
| Radio angular del Sol | 0,267° |
| Radio angular de la Tierra | 0,95° |
| Umbral de pendiente peligrosa | 10° |
| JSON | `snake_case`, números en grados o metros sin unidades en el valor (las unidades van en el nombre si hay duda: `slope_deg`, `elevation_m`) |

**Ojo con el polo sur:** cerca del polo, "norte" significa "alejándose del polo" en cualquier dirección. Nunca supongas que el norte es "arriba" en el mapa polar estereográfico.

### Arquitectura

```
Mando PS4 ──(Gamepad API)──▶ Frontend (React + CesiumJS) ◀──JSON──▶ Backend FastAPI
                                                                  │
                         ┌────────────────────────────────────────┼──────────────────────┐
                         ▼                                        ▼                      ▼
              terrain/ (Integrante 3)  ──máscara──▶  science/ (Integrante 2)  ──▶  scoring/ (Integrante 1)
              DEM, pendientes, horizonte              Sol/Tierra az/el, visibilidad     perfiles, ranking, textos
```

**Principio clave:** los 3 sitios fijos se **precalculan** y se guardan como JSON en `backend/data/precomputed/<site_id>/`. El backend solo los sirve. Solo los puntos libres se calculan al momento. Así la demo es rápida y no depende de cálculos en vivo.

### Estructura del repositorio

```
lunascope/
├── README.md
├── docs/contract.md              # este contrato, versionado
├── backend/
│   ├── pyproject.toml / requirements.txt
│   ├── app/main.py               # FastAPI (Integrante 1)
│   ├── lunascope/
│   │   ├── science/              # Integrante 2
│   │   ├── terrain/              # Integrante 3
│   │   └── scoring/              # Integrante 1
│   ├── scripts/precompute.py     # genera todo backend/data/precomputed/
│   ├── data/
│   │   ├── sites.json            # los 3 sitios (Integrante 3 rellena coordenadas)
│   │   └── precomputed/<site_id>/{horizon,terrain,timeseries}.json
│   └── tests/
├── kernels/                      # SPICE (en .gitignore, se descargan)
├── dem/                          # GeoTIFF LOLA (en .gitignore, se descargan)
├── frontend/                     # Integrante 4
└── pitch/                        # Integrante 3: guion, slides, video
```

**Git:**
- Ramas: `feat/backend`, `feat/science`, `feat/terrain`, `feat/frontend`.
- `main` siempre funciona: se fusiona por PR y el Integrante 1 revisa.
- Nunca subir kernels, DEM ni el token de Cesium. Van en `.gitignore`; el token, en `frontend/.env.local`.
- Commits pequeños y frecuentes; `git pull --rebase` antes de empezar cada bloque.

### Contrato de datos v1

Se congela en la **H3**. Cualquier cambio posterior lo aprueba el Integrante 1 y se anota en `docs/contract.md` con la hora.

#### Archivo `backend/data/sites.json` (lo rellena el Integrante 3)

```json
[
  {
    "id": "malapert",
    "name": "Malapert Massif",
    "region": "Artemis III candidate region",
    "lat": -86.0,
    "lon": 0.0,
    "elevation_m": 0.0,
    "notes": "Punto representativo elegido con el DEM: zona alta y de poca pendiente dentro de la región"
  }
]
```

> Los valores de `lat`, `lon` y `elevation_m` son **marcadores**. El Integrante 3 pone los reales en la H0–3, elegidos sobre el DEM dentro de cada región oficial.

#### Archivo `horizon.json` (lo produce el Integrante 3)

```json
{
  "site_id": "malapert",
  "lat": -86.0, "lon": 0.0,
  "observer_height_m": 2.0,
  "az_step_deg": 1,
  "horizon_el_deg": [1.23, 1.25, "... 360 valores, índice i = azimut i grados ..."],
  "max_distance_km": 150,
  "dem_source": "nombre del producto LOLA usado",
  "dem_resolution_m": 60,
  "mode": "full",
  "generated_at": "2026-11-15T10:00:00Z"
}
```

`mode` es `"full"` para los sitios fijos y `"fast"` para los puntos libres.

#### Archivo `terrain.json` (lo produce el Integrante 3)

```json
{
  "site_id": "malapert",
  "elevation_m": 4950.0,
  "radius_m": 100,
  "slope_deg_mean": 4.2,
  "slope_deg_max": 11.8,
  "hazard_pct": 3.5,
  "dem_resolution_m": 20
}
```

`hazard_pct` = % de píxeles con pendiente > 10° dentro de `radius_m` alrededor del sitio.

#### Archivo `timeseries.json` (lo produce el Integrante 2)

```json
{
  "site_id": "malapert",
  "start": "2027-09-01T00:00:00Z",
  "end": "2027-10-31T00:00:00Z",
  "step_hours": 1,
  "samples": [
    {
      "t": "2027-09-01T00:00:00Z",
      "sun":   {"az": 123.4, "el": 1.8,  "horizon_el": 0.9, "visible_fraction": 1.0},
      "earth": {"az": 2.1,   "el": 3.5,  "horizon_el": 1.1, "visible_fraction": 1.0}
    }
  ],
  "summary": {
    "sun_visible_pct": 71.3,
    "earth_visible_pct": 58.0,
    "both_visible_pct": 40.2,
    "longest_dark_h": 96,
    "longest_no_earth_h": 240,
    "windows": [
      {"start": "2027-09-03T05:00:00Z", "end": "2027-09-09T17:00:00Z", "hours": 156}
    ]
  }
}
```

Definiciones:
- `visible_fraction` = fracción visible del disco: `clip((el − horizon_el + r) / (2r), 0, 1)`, con `r` = radio angular (Sol 0,267°, Tierra 0,95°). Es una aproximación lineal, suficiente para el proyecto.
- "Visible" (para porcentajes y ventanas) = `visible_fraction ≥ 0.5`.
- `windows` = intervalos continuos en los que el Sol **y** la Tierra son visibles a la vez, ordenados por duración (los más largos primero, máximo 10).
- `longest_dark_h` = racha más larga de horas seguidas sin Sol visible.

#### Endpoints del backend (los implementa el Integrante 1)

Base: `http://localhost:8000/api`

| Método | Ruta | Devuelve |
|---|---|---|
| GET | `/health` | `{"status":"ok","kernels_loaded":true,"sites":3}` |
| GET | `/sites` | contenido de `sites.json` + `terrain` y `summary` de cada sitio |
| GET | `/sites/{id}/horizon` | `horizon.json` |
| GET | `/sites/{id}/terrain` | `terrain.json` |
| GET | `/sites/{id}/timeseries` | `timeseries.json` (completo, el frontend lo recorre localmente) |
| GET | `/profiles` | lista de perfiles con sus pesos |
| GET | `/score?profile=solar` | ranking de los 3 sitios (+ punto libre si se pasa `point_id`) |
| POST | `/point` | body `{"lat":-86.1,"lon":-3.2}` → `{"point_id":"p-1", "quality":"estimated", "site":{...}, "horizon":{...}, "terrain":{...}, "timeseries":{...}}` en < 5 s |
| POST | `/report` | body `{"site_id":"malapert","profile":"solar"}` → informe (ver Integrante 1) |

Respuesta de `/score`:

```json
{
  "profile": "solar",
  "recommended": "malapert",
  "ranking": [
    {
      "site_id": "malapert",
      "score": 78.4,
      "quality": "full",
      "breakdown": {"sun": 71.3, "earth": 58.0, "continuity": 80.0, "terrain": 72.0},
      "explanation": [
        "Tiene Sol visible el 71 % del tiempo, el mejor de los 3 sitios.",
        "Su noche más larga dura 96 h, la más corta de los 3."
      ]
    }
  ]
}
```

Errores: HTTP 4xx/5xx con `{"error":"codigo_corto","detail":"texto legible"}`.

### Puntuación (la implementa el Integrante 1; los pesos se votan en la H0–3)

Subpuntuaciones de 0 a 100:

| Subpuntuación | Fórmula |
|---|---|
| `sun` | `sun_visible_pct` |
| `earth` | `earth_visible_pct` |
| `continuity` | `100 × max(0, 1 − longest_dark_h / 240)` (240 h = 10 días sin Sol → 0) |
| `terrain` | `100 × max(0, 1 − slope_deg_mean / 15) × (1 − hazard_pct / 100)` |

`score = Σ peso × subpuntuación` (los pesos de cada perfil suman 1).

| Perfil (`id`) | Nombre en pantalla | sun | earth | continuity | terrain | ¿MVP? |
|---|---|---|---|---|---|---|
| `solar` | Energía solar | 0,50 | 0,15 | 0,20 | 0,15 | Sí |
| `comms` | Comunicaciones | 0,20 | 0,50 | 0,10 | 0,20 | Sí |
| `safety` | Seguridad de aterrizaje | 0,20 | 0,20 | 0,10 | 0,50 | No (segunda prioridad) |
| `balanced` | Equilibrado | 0,25 | 0,25 | 0,25 | 0,25 | No (segunda prioridad) |

### Controles del mando por modo (los implementa el Integrante 4; todos deben conocerlos)

| Control | Explore | Mission Time | Mission Selection |
|---|---|---|---|
| Joystick izquierdo | Mover la retícula | — | Recorrer filas de la comparación |
| Joystick derecho | Orbitar / inclinar cámara | Orbitar / inclinar cámara | — |
| L1 / R1 | Sitio anterior / siguiente | Sitio anterior / siguiente | Sitio anterior / siguiente |
| L2 / R2 | Zoom alejar / acercar | Retroceder / adelantar el tiempo (la presión controla la velocidad) | — |
| X | Marcar punto libre | Pausar / reanudar el tiempo | Confirmar sitio → informe |
| Cuadrado | Panel de datos del sitio | Panel de datos en el instante actual | Detalle de la puntuación |
| Triángulo | Sombras on/off | Sombras on/off | — |
| Cruceta | — | Ventana de visibilidad anterior / siguiente | Cambiar de perfil |
| Círculo | Volver / cerrar panel | Volver / cerrar panel | Volver / cerrar panel |
| Touchpad | Siguiente modo | Siguiente modo | Siguiente modo (vuelve a Explore) |
| Options | Menú (ayuda, reiniciar) | Menú | Menú |

Todo tiene equivalente en teclado: flechas/WASD, `Q`/`E` = L1/R1, `Z`/`C` = L2/R2, `Enter` = X, `Esc` = Círculo, `I` = Cuadrado, `T` = Triángulo, `Tab` = Touchpad, `M` = Options, `1`–`4` = cruceta.

### MVP: lo que debe funcionar en la H22

- [ ] Globo 3D con los 3 sitios marcados
- [ ] Sol y Tierra (SPICE) cruzados con la máscara de horizonte, para los 3 sitios
- [ ] Gráfico temporal de visibilidad por sitio
- [ ] Puntuación con los perfiles `solar` y `comms`
- [ ] Mando: L1/R1, L2/R2, X, Círculo y Touchpad
- [ ] Confirmación con X + informe básico

**Segunda prioridad (H22–32):** puntos libres, sombras visuales, perfiles `safety` y `balanced`, panel de estado del mando, informe completo.
**Fuera de alcance:** descenso de la nave, rover, despliegue público obligatorio, sombras calculadas en tiempo real sobre todo el DEM.

### Calendario común y puntos de control

| Hora | Punto de control | Qué se comprueba (todos presentes, 15 min máximo) |
|---|---|---|
| Antes de empezar | Descargas | Kernels SPICE, DEM LOLA, token de Cesium ion, Node y Python instalados |
| **H3** | Arranque | Repo creado, contrato congelado, 3 sitios con coordenadas, pesos votados, mando probado en Chrome, ventana de la misión fijada |
| **H12** | Primeros datos reales | Cada módulo produce salida real para **1 sitio**; el frontend funciona con mocks |
| **H22** | MVP | Todo el MVP funciona de punta a punta en `main` |
| **H32** | Segunda prioridad | Puntos libres, sombras y 4 perfiles. **Congelación de funciones en la H36** |
| **H40** | Congelación de código | Solo arreglos de errores. Video de respaldo grabado |
| **H48** | Entrega | Pitch ensayado 3 veces, repo limpio, README completo |

### Reglas del equipo

- **Bloqueado más de 30 minutos → avisa en el grupo.** No se pierden horas en silencio.
- **Nadie espera a nadie:** todos trabajan contra **datos falsos (mocks) que respetan el contrato** hasta que llegan los reales.
- **Ante la duda sobre el contrato, decide el Integrante 1.** Ante la duda científica, el Integrante 2 (Sol/Tierra) o el 3 (terreno).
- **Dormir:** cada uno duerme al menos 4 horas, en turnos. El equipo nunca queda vacío entre la H12 y la H40.
- **Honestidad científica:** todo lo aproximado se etiqueta como aproximado, en pantalla y en el pitch.

## Parte específica: tu trabajo paso a paso

### 1. Antes del hackathon: descargar los kernels

Desde el repositorio público de NAIF: `https://naif.jpl.nasa.gov/pub/naif/generic_kernels/`

| Kernel | Ruta en NAIF | Para qué sirve |
|---|---|---|
| Leapseconds | `lsk/naif0012.tls` | Convertir UTC ↔ tiempo de efemérides (ET) |
| Constantes planetarias | `pck/pck00011.tpc` | Radios y orientación de cuerpos |
| Efemérides | `spk/planets/de440s.bsp` (~32 MB) | Posiciones del Sol, la Tierra y la Luna |
| Orientación lunar precisa | `pck/moon_pa_de440_200625.bpc` | Orientación de la Luna (marco PA) |
| Marcos lunares | `fk/satellites/moon_de440_220930.tf` | Define `MOON_ME` y `MOON_PA` |

> Los nombres con fecha pueden haber cambiado: entra a cada carpeta y descarga la versión más reciente compatible con DE440. Si cambias alguno, actualiza el meta-kernel.

Guárdalos en `kernels/` (fuera de git) y crea el meta-kernel `kernels/lunascope.tm`:

```
KPL/MK
\begindata
PATH_VALUES  = ( 'kernels' )
PATH_SYMBOLS = ( 'K' )
KERNELS_TO_LOAD = (
  '$K/naif0012.tls'
  '$K/pck00011.tpc'
  '$K/de440s.bsp'
  '$K/moon_pa_de440_200625.bpc'
  '$K/moon_de440_220930.tf'
)
\begintext
```

`PATH_VALUES` es relativo al directorio desde donde se ejecuta Python. Ejecuta siempre desde la raíz del repo, o pon una ruta absoluta.

Prueba rápida (debe imprimir una distancia de unos 384 000 km):

```python
import spiceypy as sp, numpy as np
sp.furnsh("kernels/lunascope.tm")
et = sp.str2et("2027-09-01T00:00:00")
pos, lt = sp.spkpos("EARTH", et, "MOON_ME", "LT+S", "MOON")
print(np.linalg.norm(pos), "km")
```

### 2. Geometría: cómo pasar de vectores a azimut y elevación

1. **Vector del sitio** en `MOON_ME` (km): `sp.latrec(R + h, lon_rad, lat_rad)`, con `R = 1737.4` km y `h` = elevación del sitio + 2 m, en km.
2. **Vector del objetivo** (Sol o Tierra) desde el centro de la Luna, en `MOON_ME`: `sp.spkpos(target, et, "MOON_ME", "LT+S", "MOON")`.
3. **Vector sitio → objetivo** = objetivo − sitio.
4. **Base local ENU** (este, norte, arriba), con la Luna como esfera:
   - `up` = sitio normalizado
   - `east` = `ẑ × up`, normalizado (ẑ = eje polar del marco)
   - `north` = `up × east`
5. **Elevación** = `asin(v̂ · up)`. **Azimut** = `atan2(v̂ · east, v̂ · north)` llevado a [0°, 360°).

Esto cumple la convención del contrato: azimut desde el norte en sentido horario hacia el este. Cerca del polo sur "norte" apunta hacia afuera del polo; la fórmula lo resuelve sola. **No funciona exactamente en el polo** (lat = −90°), pero ningún sitio está ahí. Si alguien elige un punto libre a menos de 0,01° del polo, devuelve un error.

> **Nota de precisión:** aplicar `LT+S` desde el centro de la Luna en vez de desde el sitio introduce un error despreciable (muy por debajo de 0,01°). Si quieres la versión más estricta, usa `sp.spkcpo` con el sitio como observador de posición constante. Menciónalo en la validación; es un buen detalle para el jurado.

### 3. Estructura del paquete

```
science/
├── __init__.py          # exporta compute_timeseries
├── kernels.py           # load_kernels() idempotente (furnsh una sola vez)
├── geometry.py          # site_vector, enu_basis, az_el (vectorizados)
├── visibility.py        # horizon_at(az), visible_fraction, summary, windows
└── timeseries.py        # compute_timeseries (orquesta todo)
```

### 4. Código de referencia

`geometry.py`:

```python
import numpy as np
import spiceypy as sp

R_MOON_KM = 1737.4

def site_vector(lat_deg, lon_deg, height_m):
    return np.array(sp.latrec(R_MOON_KM + height_m / 1000.0,
                              np.radians(lon_deg), np.radians(lat_deg)))

def enu_basis(site):
    up = site / np.linalg.norm(site)
    east = np.cross([0.0, 0.0, 1.0], up)
    east /= np.linalg.norm(east)
    north = np.cross(up, east)
    return east, north, up

def az_el(target, ets, site, basis):
    """ets: array de tiempos ET. Devuelve (az_deg, el_deg) como arrays."""
    pos, _ = sp.spkpos(target, ets, "MOON_ME", "LT+S", "MOON")   # (N, 3) km
    v = np.asarray(pos) - site
    v /= np.linalg.norm(v, axis=1, keepdims=True)
    e, n, u = basis
    el = np.degrees(np.arcsin(np.clip(v @ u, -1, 1)))
    az = np.degrees(np.arctan2(v @ e, v @ n)) % 360.0
    return az, el
```

`visibility.py`:

```python
SUN_RADIUS_DEG = 0.267
EARTH_RADIUS_DEG = 0.95

def horizon_at(az_deg, horizon_el_deg):
    """Interpolación lineal circular en la máscara de 360 valores (paso 1°)."""
    h = np.asarray(horizon_el_deg)
    i0 = np.floor(az_deg).astype(int) % 360
    i1 = (i0 + 1) % 360
    f = az_deg - np.floor(az_deg)
    return h[i0] * (1 - f) + h[i1] * f

def visible_fraction(el, hz, r):
    return np.clip((el - hz + r) / (2 * r), 0.0, 1.0)
```

Si la máscara es `None` (el terreno aún no está listo), usa un horizonte plano de 0° y marca `"horizon":"none"` en la salida. Así nunca bloqueas al Integrante 1.

Si la máscara tiene paso de 2° (modo `fast`), adapta `horizon_at` usando `az_step_deg`.

`timeseries.py`, con la firma del contrato:

```python
def compute_timeseries(lat_deg: float, lon_deg: float, height_m: float,
                       horizon_el_deg: list[float] | None,
                       start: datetime, end: datetime, step_h: float = 1.0,
                       site_id: str = "") -> dict:
    load_kernels()
    times = [start + timedelta(hours=step_h * k)
             for k in range(int((end - start).total_seconds() // (3600 * step_h)) + 1)]
    ets = np.array([sp.str2et(t.strftime("%Y-%m-%dT%H:%M:%S")) for t in times])
    site = site_vector(lat_deg, lon_deg, height_m)
    basis = enu_basis(site)
    s_az, s_el = az_el("SUN", ets, site, basis)
    e_az, e_el = az_el("EARTH", ets, site, basis)
    hz = horizon_el_deg or [0.0] * 360
    s_hz, e_hz = horizon_at(s_az, hz), horizon_at(e_az, hz)
    s_vf = visible_fraction(s_el, s_hz, SUN_RADIUS_DEG)
    e_vf = visible_fraction(e_el, e_hz, EARTH_RADIUS_DEG)
    samples = [...]   # redondear a 3 decimales; formato exacto del contrato
    return {"site_id": site_id, "start": ..., "end": ..., "step_hours": step_h,
            "samples": samples, "summary": summarize(times, s_vf, e_vf, step_h)}
```

`summarize`:
- `sun_visible_pct` = % de muestras con `s_vf ≥ 0.5`. Lo mismo para la Tierra y para "ambos".
- `longest_dark_h` = racha más larga de `s_vf < 0.5` × `step_h`. Lo mismo para `longest_no_earth_h`.
- `windows` = rachas con ambos visibles, convertidas a `{start, end, hours}`, ordenadas de mayor a menor duración, máximo 10.

Rendimiento: 1441 muestras × 2 objetivos debe tardar menos de 1 s. Si `str2et` en bucle es lento, calcula `et0` una vez y suma `3600 × k` segundos (ET es lineal en segundos).

### 5. Validación con JPL Horizons (obligatoria, H12–32)

Es tu mejor argumento frente al jurado: "nuestros cálculos coinciden con los de JPL".

1. En JPL Horizons (interfaz web o API), elige:
   - Objetivo: `Sun` (luego `Earth`).
   - Ubicación del observador: un sitio en la superficie de la Luna (cuerpo 301) con las coordenadas del sitio (longitud este, latitud, altura).
   - Cantidad: azimut y elevación aparentes.
   - Las mismas fechas que tu serie, cada 6 h durante 3 días.
2. Compara con tu salida **sin horizonte** (geometría pura).
3. **Tolerancia:** diferencias menores que 0,1°. Si son mayores, revisa en este orden: marco (`MOON_ME` frente a otro), signo de la longitud, convención del azimut, unidades de altura (m frente a km).
4. Documenta en `docs/validation.md`: una tabla con 5–10 filas, la diferencia máxima y la conclusión.

Comprobaciones de cordura adicionales:
- [ ] En un sitio a 86°S, la elevación del Sol oscila aproximadamente entre −5,6° y +5,6° (distancia al polo + inclinación del eje lunar, ~1,5°).
- [ ] El Sol da una vuelta completa de azimut en ~29,5 días (un día lunar).
- [ ] La Tierra apenas se mueve en el cielo: oscila unos pocos grados por la libración, sin dar vueltas.
- [ ] En un sitio con longitud cercana a 0°, la Tierra aparece cerca del azimut 0° (norte) y baja sobre el horizonte, a pocos grados de elevación.

### 6. Integración con el terreno (H12–22)

- El Integrante 3 te entrega `compute_horizon(lat, lon, mode)` → `horizon_el_deg`.
- **Antes de integrar, comprobad juntos la convención del azimut:** elegid una montaña conocida en el DEM que esté, por ejemplo, al este del sitio, y verificad que la máscara sube alrededor de 90°. Es el error más probable del proyecto.
- Con los datos reales, mirad juntos un gráfico de `el` del Sol frente al horizonte en su azimut para 30 días. Debe verse que el relieve "corta" parte de las horas de Sol.

### 7. Apoyo al frontend (H12–32)

El Integrante 4 necesita:
- **Dirección del Sol para la luz de Cesium:** dale la fórmula inversa: vector ENU = `(cos(el)·sin(az), cos(el)·cos(az), sin(el))`. Cesium lo transforma a coordenadas globales con `Transforms.eastNorthUpToFixedFrame` sobre el elipsoide lunar. La dirección de la luz es el **opuesto** de ese vector.
- **Interpretación de los gráficos:** qué significa que la curva del Sol cruce la del horizonte.
- Revisa con él que las etiquetas de los paneles sean correctas: "visibilidad geométrica", no "comunicación garantizada".

### 8. Tu horario

| Bloque | Tareas |
|---|---|
| Antes | Descargar kernels, instalar SpiceyPy, ejecutar la prueba rápida |
| H0–3 | Reunión de arranque; confirmar convenciones; esqueleto del paquete |
| H3–12 | `geometry.py` + `visibility.py` + `compute_timeseries` con horizonte plano. **H12:** `timeseries.json` real de 1 sitio |
| H12–22 | Integrar la máscara del Integrante 3, verificar el azimut juntos, 3 sitios. **MVP** |
| H22–32 | Validación con Horizons, `docs/validation.md`, apoyo al frontend (luz y paneles), optimizar para `/point` |
| H32–40 | Correcciones; preparar respuestas científicas para el jurado |
| H40–48 | Ensayo: explicas en 45 s cómo se calcula la visibilidad y cómo se validó |

### 9. Preguntas que te hará el jurado (ten la respuesta preparada)

| Pregunta | Respuesta corta |
|---|---|
| ¿De dónde salen las posiciones? | Efemérides DE440 de JPL leídas con SPICE (toolkit oficial de NASA/NAIF), en el marco lunar `MOON_ME` |
| ¿Qué tan precisas son? | Validadas contra JPL Horizons, con diferencias menores que [tu valor]° |
| ¿Por qué "geométrica"? | Indica si hay línea de vista; no modela antenas, potencia de enlace ni satélites de relevo |
| ¿Cómo tratan el relieve? | Máscara de horizonte de 360° calculada desde el DEM LOLA, con corrección por curvatura lunar |
| ¿Qué simplificaciones hay? | Luna esférica para la base local; fracción del disco lineal; paso de 1 h |

### 10. Riesgos

| Riesgo | Qué hacer |
|---|---|
| Error "frame not found" o "insufficient data" | Falta un kernel o el meta-kernel tiene mal la ruta. Revisa `PATH_VALUES` y el orden de carga |
| Azimut invertido o desfasado 180° | Prueba con la montaña conocida; revisa `east`/`north` y el `atan2(e, n)` |
| La máscara de horizonte no llega | Horizonte plano + `"horizon":"none"`; el MVP sigue funcionando |
| Fechas fuera de la cobertura de `de440s` | Cubre ~1849–2150: no debería pasar; si pasa, revisa la conversión UTC → ET |

### 11. Definición de terminado

- [ ] `compute_timeseries` respeta la firma y el formato del contrato.
- [ ] `timeseries.json` de los 3 sitios con horizonte real.
- [ ] Validación con Horizons documentada, con diferencia máxima < 0,1°.
- [ ] Convención de azimut verificada con el Integrante 3 sobre un accidente real del terreno.
- [ ] El frontend orienta la luz con tus datos.
