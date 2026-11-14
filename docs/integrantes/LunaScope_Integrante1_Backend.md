# LunaScope · Integrante 1 — Backend + motor de decisión (Tech Lead)

> **Tu misión:** que todas las piezas encajen. Eres dueño del contrato de datos, de la API, de la puntuación y del informe final. Si `main` no funciona, es tu prioridad número uno.

**Lo que entregas al final:**
1. Backend FastAPI que sirve todos los endpoints del contrato.
2. Módulo `scoring/` con perfiles, ranking y explicaciones en texto.
3. Endpoint de informe de misión.
4. Script `precompute.py` que genera todos los datos de los 3 sitios con un solo comando.
5. Repo ordenado, README con instrucciones de arranque y `main` siempre funcionando.

**De quién dependes:** Integrante 2 (`timeseries.json` y la función `compute_timeseries`), Integrante 3 (`sites.json`, `horizon.json`, `terrain.json` y las funciones de terreno).
**Quién depende de ti:** Integrante 4 (consume tu API). Todos dependen del contrato que congelas en la H3.

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

### 1. Antes del hackathon (o en los primeros 30 minutos)

- [ ] Crear el repo `lunascope` en GitHub con la estructura de la parte común y agregar a los 4 integrantes.
- [ ] `.gitignore` con: `kernels/`, `dem/`, `*.tif`, `*.bsp`, `*.bpc`, `node_modules/`, `.env*`, `__pycache__/`, `.venv/`.
- [ ] Copiar la parte común de este documento a `docs/contract.md`.
- [ ] Python 3.11+ y un entorno virtual:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install fastapi "uvicorn[standard]" pydantic numpy spiceypy rasterio pyproj scipy pytest httpx
pip freeze > requirements.txt
```

### 2. H0–3: arranque (tú diriges la reunión)

Agenda de la reunión inicial (máximo 45 min):
1. Leer juntos el enunciado oficial del reto y comprobar que el MVP lo cubre.
2. Confirmar los 3 sitios. El Integrante 3 propone las coordenadas a partir del DEM.
3. Fijar `MISSION_START`.
4. Votar los pesos de los perfiles (la tabla de la parte común es la propuesta).
5. Repasar el contrato campo por campo y **congelarlo**.
6. El Integrante 4 prueba el mando en Chrome delante de todos.

Después:
- [ ] Esqueleto FastAPI con `/api/health` y CORS para `http://localhost:5173`.
- [ ] **Mocks** en `backend/data/precomputed/` para los 3 sitios. Pueden ser inventados, pero deben tener la forma exacta del contrato. Así el Integrante 4 empieza a trabajar ya.
- [ ] Hacer push a `main` y avisar: "API mock lista en :8000".

### 3. Esqueleto del backend

```
backend/app/
├── main.py          # crea la app, CORS, incluye routers
├── config.py        # rutas, MISSION_START, constantes
├── models.py        # modelos Pydantic del contrato
├── store.py         # carga y cachea los JSON precalculados
└── routers/
    ├── sites.py
    ├── score.py
    ├── point.py
    └── report.py
```

`main.py` mínimo:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sites, score, point, report
from app.store import store

app = FastAPI(title="LunaScope API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)

@app.on_event("startup")
def load():
    store.load_all()          # lee sites.json y precomputed/* a memoria

@app.get("/api/health")
def health():
    return {"status": "ok", "kernels_loaded": store.kernels_loaded, "sites": len(store.sites)}

for r in (sites.router, score.router, point.router, report.router):
    app.include_router(r, prefix="/api")
```

Arranque: `uvicorn app.main:app --reload --port 8000`.

`store.py`: cargar todo al inicio en diccionarios `{site_id: dict}`. Si un archivo no existe, se registra un aviso y el sitio queda marcado como incompleto; el servidor no debe caerse.

Los modelos Pydantic (`models.py`) deben reflejar el contrato **exactamente**. Úsalos como `response_model` para que FastAPI valide la salida: si alguien rompe el formato, lo verás al instante. La documentación automática en `http://localhost:8000/docs` sirve como referencia viva para el Integrante 4.

### 4. Precálculo (`scripts/precompute.py`)

Un solo comando debe regenerar todo:

```bash
python scripts/precompute.py --start 2027-09-01T00:00:00Z --days 60
```

Lógica:

```python
from lunascope.terrain import compute_horizon, compute_terrain_stats
from lunascope.science import compute_timeseries

for site in load_sites():
    horizon = compute_horizon(site["lat"], site["lon"], mode="full")
    terrain = compute_terrain_stats(site["lat"], site["lon"], radius_m=100)
    ts = compute_timeseries(site["lat"], site["lon"], terrain["elevation_m"] + 2.0,
                            horizon["horizon_el_deg"], start, end, step_h=1)
    write_json(f"data/precomputed/{site['id']}/horizon.json", horizon)
    write_json(f"data/precomputed/{site['id']}/terrain.json", terrain)
    write_json(f"data/precomputed/{site['id']}/timeseries.json", ts)
```

Las firmas de `compute_horizon`, `compute_terrain_stats` y `compute_timeseries` están en los documentos de los Integrantes 2 y 3 y **son parte del contrato**. Si alguno no está listo, el script usa el mock y lo avisa en consola.

Los JSON precalculados **sí se suben a git** (pesan poco), para que cualquiera pueda arrancar la demo sin kernels ni DEM.

### 5. Motor de decisión (`lunascope/scoring/`)

```
scoring/
├── profiles.py      # PROFILES = {"solar": {...}, ...}
├── engine.py        # subscores(), score_site(), rank()
└── explain.py       # genera los textos de explicación
```

`engine.py`:

```python
def subscores(summary: dict, terrain: dict) -> dict:
    return {
        "sun": summary["sun_visible_pct"],
        "earth": summary["earth_visible_pct"],
        "continuity": 100 * max(0.0, 1 - summary["longest_dark_h"] / 240),
        "terrain": 100 * max(0.0, 1 - terrain["slope_deg_mean"] / 15) * (1 - terrain["hazard_pct"] / 100),
    }

def score_site(sub: dict, weights: dict) -> float:
    return round(sum(weights[k] * sub[k] for k in weights), 1)

def rank(candidates: list[dict], profile_id: str) -> dict:
    w = PROFILES[profile_id]["weights"]
    rows = []
    for c in candidates:
        sub = subscores(c["summary"], c["terrain"])
        rows.append({"site_id": c["id"], "score": score_site(sub, w),
                     "quality": c.get("quality", "full"), "breakdown": sub})
    rows.sort(key=lambda r: r["score"], reverse=True)
    for r in rows:
        r["explanation"] = explain(r, rows, profile_id)
    return {"profile": profile_id, "recommended": rows[0]["site_id"], "ranking": rows}
```

Regla: un punto libre (`quality: "estimated"`) **puede aparecer en el ranking, pero nunca puede ser `recommended`**. Si queda primero, se recomienda el mejor sitio `full` y se añade la frase: "El punto libre puntúa más alto, pero su análisis es aproximado".

`explain.py`: entre 2 y 4 frases por sitio, generadas con plantillas a partir de los números (sin texto inventado):
- Su mejor subpuntuación, comparada con los otros sitios ("el mejor de los 3", "el segundo").
- Su peor subpuntuación, como advertencia.
- Una frase sobre el perfil ("Con el perfil Energía solar, el Sol pesa un 50 %").
- La ventana más larga con Sol y Tierra a la vez ("Mejor ventana: 3 sep 05:00 UTC, 156 h").

Pruebas mínimas (`tests/test_scoring.py`):
- [ ] Los pesos de cada perfil suman 1.
- [ ] Un sitio con 100 en todo da 100.
- [ ] Un punto `estimated` nunca es `recommended`.
- [ ] Cambiar de perfil cambia el orden en un caso preparado a propósito.

### 6. Punto libre (`POST /api/point`) — segunda prioridad

```python
@router.post("/point")
def point(body: PointIn):
    t0 = time.time()
    terrain = compute_terrain_stats(body.lat, body.lon, radius_m=100)
    horizon = compute_horizon(body.lat, body.lon, mode="fast")
    ts = compute_timeseries(body.lat, body.lon, terrain["elevation_m"] + 2.0,
                            horizon["horizon_el_deg"], START, END, step_h=2)
    pid = store.add_point(...)   # en memoria, ids p-1, p-2...
    log.info("point %s en %.1fs", pid, time.time() - t0)
    return {...,"quality": "estimated"}
```

- Objetivo: < 5 s. Si tarda más, pide al Integrante 2 un paso de 3 h y al 3 un horizonte más corto.
- Validar que el punto esté dentro de la cobertura del DEM; si no, devolver un 422 con `"error":"outside_dem"`.

### 7. Informe (`POST /api/report`)

Devuelve JSON que el frontend muestra e imprime:

```json
{
  "title": "Informe de planificación — Malapert Massif",
  "generated_at": "2027-...Z",
  "profile": {"id": "solar", "name": "Energía solar", "weights": {...}},
  "site": {"id": "malapert", "name": "...", "lat": ..., "lon": ..., "elevation_m": ...},
  "score": 78.4,
  "rank": 1,
  "breakdown": {...},
  "best_window": {"start": "...", "end": "...", "hours": 156},
  "explanation": ["..."],
  "comparison": [{"site_id": "...", "score": ...}],
  "data_sources": ["NASA NAIF SPICE (de440s, ...)", "LRO LOLA DEM (...)"],
  "limitations": [
    "Visibilidad geométrica: no incluye enlaces de radio ni cobertura de satélites.",
    "La fracción visible del disco es una aproximación lineal.",
    "Puntos libres: horizonte de menor alcance y resolución."
  ]
}
```

Las `limitations` son importantes: muestran rigor al jurado.

### 8. Integración (H12–22): tu bloque más crítico

Orden:
1. **H12:** integrar las funciones reales del Integrante 3 para 1 sitio, luego las del 2. Ejecutar `precompute.py` para ese sitio.
2. Verificar a mano que el JSON cumple el contrato (los modelos Pydantic lo hacen por ti).
3. Extender a los 3 sitios.
4. Conectar el frontend real a los datos reales y revisar con el Integrante 4 que todo se ve.
5. **H22:** demo del MVP de punta a punta delante del equipo.

Comprobaciones de cordura antes de dar por buenos los datos:
- [ ] Los 360 valores del horizonte están entre −5° y +15°.
- [ ] La elevación del Sol nunca supera ±(distancia al polo + 1,6°). Por ejemplo, a 86°S debe estar entre −5,6° y +5,6°.
- [ ] `sun_visible_pct` está entre 0 y 100 y es distinto en cada sitio.
- [ ] Las fechas de `samples` son consecutivas y de 1 h.

### 9. Pruebas y demo (H32–48)

- [ ] `pytest` pasa.
- [ ] Script `scripts/demo_check.py` que llama a todos los endpoints y comprueba códigos 200 y forma básica.
- [ ] Prueba completa con la red Wi-Fi apagada: el backend tiene que funcionar (solo Cesium falla).
- [ ] README: requisitos, cómo descargar kernels y DEM, cómo arrancar backend y frontend, cómo regenerar datos.
- [ ] Etiqueta `v1.0-demo` en `main` en la H40.

### 10. Tu horario

| Bloque | Tareas |
|---|---|
| H0–3 | Reunión de arranque, repo, contrato congelado, API mock funcionando |
| H3–12 | Modelos Pydantic, store, todos los endpoints con mocks, motor de puntuación + pruebas, plantillas de explicación |
| H12–22 | Integración real con 2 y 3, `precompute.py`, informe básico, **MVP** |
| H22–32 | `/point`, perfiles `safety` y `balanced`, informe completo, revisar PRs |
| H32–40 | Pruebas, `demo_check.py`, README, ayudar a quien vaya atrasado |
| H40–48 | Congelación de código, ensayo del pitch (explicas la arquitectura y la puntuación) |

### 11. Riesgos

| Riesgo | Qué hacer |
|---|---|
| Un módulo científico no llega a tiempo | El backend sigue sirviendo mocks marcados como `"source":"mock"`; nunca bloquees la demo |
| `/point` tarda demasiado | Reducir pasos y resolución, o dejar el punto libre fuera del MVP (ya es segunda prioridad) |
| Conflictos de merge | PR pequeños; tú fusionas; nadie fuerza un push a `main` |
| Cambios de contrato a última hora | Solo con tu aprobación y anotados en `docs/contract.md` |

### 12. Definición de terminado

- [ ] Todos los endpoints responden según el contrato, validados con Pydantic.
- [ ] `precompute.py` regenera los 3 sitios sin errores.
- [ ] El ranking cambia con el perfil y las explicaciones citan números reales.
- [ ] El informe incluye fuentes y limitaciones.
- [ ] Un integrante que no eres tú puede arrancar todo siguiendo el README.
