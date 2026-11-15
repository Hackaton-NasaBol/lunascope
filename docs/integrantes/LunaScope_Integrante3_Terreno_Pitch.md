# LunaScope · Integrante 3 — Terreno LOLA + presentación

> **Tu misión tiene dos partes.** Hasta la H22, conviertes los modelos de elevación de NASA en información útil: dónde están exactamente los sitios, qué tan empinados son y qué parte del cielo tapa el relieve. Desde la H22, eres el dueño del pitch, del guion de la demo y del video de respaldo.

**Lo que entregas al final:**
1. `backend/data/sites.json` con las coordenadas reales de los 3 sitios (antes de la H3).
2. Paquete `backend/lunascope/terrain/` con `compute_horizon`, `compute_terrain_stats` y `sample_elevation` (parte del contrato).
3. `horizon.json` y `terrain.json` de los 3 sitios (los genera `precompute.py`).
4. `pitch/`: guion del pitch, slides, guion de la demo con la secuencia exacta de botones, video de respaldo y preguntas frecuentes del jurado.

**De quién dependes:** de nadie para empezar (solo del DEM descargado).
**Quién depende de ti:** el Integrante 2 (necesita tu máscara de horizonte), el 1 (necesita `terrain.json` y las coordenadas) y todo el equipo para el pitch.

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
| GET | `/illumination/{id}/meta` | rectángulo lat/lon, resolución y método de la capa de sombras del sitio |
| GET | `/illumination/{id}.png?t=…` | PNG de sombras del relieve (DEM LOLA + Sol de la serie) en el instante `t` |
| GET | `/terrain/info` | si el backend tiene el DEM LOLA y cómo pedir el relieve |
| GET | `/terrain/heightmap/{z}/{x}/{y}.bin` | 65×65 alturas float32 (m, esfera 1 737 400 m) para el globo 3D |

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
| `continuity` | `100 × max(0, 1 − longest_dark_h / 720)` (720 h ≈ 30 días sin Sol → 0; cambiado desde 240 h, ver registro de cambios) |
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
| Triángulo | Sombras del relieve on/off | Sombras del relieve on/off | — |
| Cruceta | ↑↓ capa (ninguna / elevación / pendiente) | ←→ ventana anterior / siguiente · ↑↓ capa | Cambiar de perfil |
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

### 1. Antes del hackathon: descargar los DEM (descargas pesadas)

Necesitas **dos niveles de detalle**:

| Uso | Resolución | Cobertura | Por qué |
|---|---|---|---|
| **Horizonte** | 60–120 m/píxel | Todo el polo sur hasta ~80°S (unos 600 × 600 km) | Las crestas a más de 100 km también tapan el Sol, que está a pocos grados de altura |
| **Pendientes** y elección de sitios | 5–20 m/píxel | Unos 20 × 20 km alrededor de cada sitio | La pendiente que importa para aterrizar está a escala de decenas de metros |

Fuentes:
- **NASA PGDA, producto 90**: modelos de elevación LOLA del polo sur en proyección polar estereográfica, en varias resoluciones. `https://pgda.gsfc.nasa.gov/products/90`
- **PDS Geosciences, LRO LOLA (Gridded Data Records, productos polares)**: alternativa si no encuentras la resolución que buscas.

Al descargar, anota en `dem/README.md`: nombre exacto del archivo, resolución, cobertura, URL y **unidades de altura** (en algunos productos la altura viene en km o con un factor de escala).

Instalación:

```bash
pip install rasterio pyproj numpy scipy matplotlib
```

Primer contacto con el archivo:

```python
import rasterio
with rasterio.open("dem/<archivo>.tif") as ds:
    print(ds.crs)          # proyección (debería ser polar estereográfica, Luna)
    print(ds.res)          # metros por píxel
    print(ds.bounds)       # extensión en metros
    print(ds.nodata, ds.dtypes, ds.tags())   # buscar escala/unidades
```

Si la altura no está en metros respecto a la esfera de 1 737 400 m, conviértela **una sola vez** al cargar y documenta la conversión.

### 2. H0–3: elegir las coordenadas de los 3 sitios

Las regiones de Artemis III son **zonas**, no puntos. Tu trabajo es elegir un punto representativo dentro de cada una de las 3 regiones confirmadas.

1. Localiza cada región en el mapa oficial de NASA de las regiones candidatas y en el DEM.
2. Dentro de cada región, calcula la pendiente (sección 4) y elige un punto **alto** (más Sol y más visibilidad de la Tierra) con **pendiente media < 8°** en 100 m a la redonda.
3. Rellena `backend/data/sites.json` con `lat`, `lon` (este, −180 a 180), `elevation_m` y una nota que explique el criterio.
4. Haz una captura del DEM con los 3 puntos marcados y guárdala en `pitch/img/sitios.png`. Sirve para el pitch.

> Si en la H3 no tienes los puntos definitivos, entrega puntos provisionales y avisa. **Nunca bloquees al equipo.**

### 3. Conversión de coordenadas (la base de todo)

```python
from pyproj import CRS, Transformer

MOON_GEO = CRS.from_proj4("+proj=longlat +R=1737400 +no_defs")

class Dem:
    def __init__(self, path):
        self.ds = rasterio.open(path)
        self.z = self.ds.read(1).astype("float32")     # en memoria (cabe: ~100–400 MB)
        self.z[self.z == self.ds.nodata] = np.nan
        self.to_xy = Transformer.from_crs(MOON_GEO, self.ds.crs, always_xy=True)
        self.to_ll = Transformer.from_crs(self.ds.crs, MOON_GEO, always_xy=True)
        self.inv = ~self.ds.transform                   # (x, y) → (col, fila)

    def xy(self, lat, lon):
        return self.to_xy.transform(lon, lat)           # ¡orden lon, lat!

    def sample(self, xs, ys):
        cols, rows = self.inv * (np.asarray(xs), np.asarray(ys))
        return map_coordinates(self.z, [rows - 0.5, cols - 0.5], order=1, mode="nearest")
```

> El `−0.5` es porque la transformación afín de rasterio apunta a la esquina del píxel y `map_coordinates` al centro. Si tus alturas parecen desplazadas medio píxel, revisa esto.

**Dirección norte y este en el plano del DEM.** No la supongas. Calcúlala numéricamente para cada sitio:

```python
def local_axes(dem, lat, lon, d=0.001):
    x0, y0 = dem.xy(lat, lon)
    xn, yn = dem.xy(lat + d, lon)          # un poco hacia el norte (hacia el ecuador)
    xe, ye = dem.xy(lat, lon + d)          # un poco hacia el este
    north = np.array([xn - x0, yn - y0]); north /= np.linalg.norm(north)
    east  = np.array([xe - x0, ye - y0]); east  /= np.linalg.norm(east)
    return (x0, y0), north, east
```

Así funciona con cualquier proyección y convención del archivo. Es la clave para que tu azimut coincida con el del Integrante 2.

### 4. Pendientes y estadísticas (`compute_terrain_stats`)

Firma del contrato:

```python
def compute_terrain_stats(lat: float, lon: float, radius_m: float = 100) -> dict:
    ...
    return {"site_id": "", "elevation_m": ..., "radius_m": radius_m,
            "slope_deg_mean": ..., "slope_deg_max": ..., "hazard_pct": ...,
            "dem_resolution_m": ...}
```

Método (con el DEM de alta resolución):
1. Recorta una ventana de ±(radius_m + 2 píxeles) alrededor del punto.
2. `dzdy, dzdx = np.gradient(z, res)` → `slope = degrees(arctan(hypot(dzdx, dzdy)))`.
3. Quédate con los píxeles dentro del círculo de `radius_m`.
4. Media, máximo y `hazard_pct` = % con pendiente > 10°.

> Con 5 m/píxel, 100 m de radio son unos 1250 píxeles: suficiente. Con 60 m/píxel serían ~9 píxeles: poco fiable. Usa siempre el DEM fino para las pendientes.

### 5. Máscara de horizonte (`compute_horizon`): tu pieza más importante

Firma del contrato:

```python
def compute_horizon(lat: float, lon: float, mode: str = "full",
                    observer_height_m: float = 2.0) -> dict:
    # mode="full": 150 km, paso de azimut 1°
    # mode="fast": 50 km, paso de azimut 2° (puntos libres, < 1 s)
```

Algoritmo, para cada azimut `a`:
1. Dirección en el plano: `d = north·cos(a) + east·sin(a)`.
2. Distancias de muestreo `s` desde ~1 píxel hasta `max_distance`, con paso creciente: 1 píxel hasta 5 km, 2 píxeles hasta 30 km y 4 píxeles después. Así ahorras tiempo sin perder las crestas cercanas.
3. Alturas `z(s)` muestreadas a lo largo del rayo (bilineal).
4. **Corrección por curvatura lunar:** el terreno lejano "cae" `s² / (2R)`, con `R` = 1 737 400 m. A 100 km son ~2,9 km de caída: **no es opcional**.
5. Ángulo de elevación: `atan2(z(s) − z0 − h_obs − s²/(2R), s)`.
6. `horizon_el_deg[a]` = el máximo de esos ángulos.

```python
R = 1_737_400.0

def compute_horizon(lat, lon, mode="full", observer_height_m=2.0):
    dem = DEM_COARSE                             # el de 60–120 m/píxel, cargado una vez
    (x0, y0), north, east = local_axes(dem, lat, lon)
    z0 = float(dem.sample([x0], [y0])[0]) + observer_height_m
    max_d = 150_000 if mode == "full" else 50_000
    step_az = 1 if mode == "full" else 2
    s = distances(dem.res[0], max_d)             # array creciente
    out = []
    for a in np.arange(0, 360, step_az):
        ar = np.radians(a)
        d = north * np.cos(ar) + east * np.sin(ar)
        z = dem.sample(x0 + d[0] * s, y0 + d[1] * s)
        ang = np.degrees(np.arctan2(z - z0 - s**2 / (2 * R), s))
        out.append(float(np.nanmax(ang)))
    return {"lat": lat, "lon": lon, "observer_height_m": observer_height_m,
            "az_step_deg": step_az, "horizon_el_deg": [round(v, 3) for v in out],
            "max_distance_km": max_d / 1000, "mode": mode, ...}
```

Detalles importantes:
- **Bordes del DEM:** si el rayo sale de la cobertura, corta ahí (valores `NaN` → ignorados por `nanmax`) y anótalo en el log. Si un sitio está a menos de 100 km del borde, avisa: su horizonte en esa dirección será incompleto.
- **Distorsión de la proyección:** en polar estereográfica la escala varía un poco (< 1 % cerca del polo). Se puede ignorar; menciónalo como limitación.
- **Altura del sitio:** muestréala del DEM fino (más exacto), no del grueso.

Validación (obligatoria):
- [ ] Dibuja la máscara (azimut en X, elevación en Y) de cada sitio y guárdala en `pitch/img/horizonte_<sitio>.png`. Es un gráfico excelente para el pitch.
- [ ] **Prueba de convención con el Integrante 2:** elige una montaña visible en el DEM, mide a mano su dirección desde el sitio y comprueba que la máscara sube en ese azimut. Si aparece desplazada 90° o 180°, el error está en `north`/`east`.
- [ ] Valores típicos: entre 0° y unos pocos grados. Un sitio en un pico tendrá valores bajos o incluso negativos (ve "por encima" de la curvatura).
- [ ] Tiempo: `full` < 10 s por sitio; `fast` < 1 s.

### 6. `sample_elevation` y puntos libres

```python
def sample_elevation(lat: float, lon: float) -> float:
    # DEM fino si el punto está dentro de su cobertura; si no, DEM grueso
```

El Integrante 1 llama a `compute_terrain_stats` + `compute_horizon(mode="fast")` para los puntos libres. Si el punto está fuera de ambos DEM, lanza `ValueError("outside_dem")`.

### 7. Sombras: segunda prioridad, compartida con el Integrante 4

Las sombras visuales las hace el **frontend**, usando la iluminación de Cesium orientada con la dirección del Sol del Integrante 2. Tu aporte es confirmar que se ven coherentes: si tu máscara dice que el Sol está tapado a cierta hora, la escena 3D debería mostrar el sitio en sombra. Si no coincide, documéntalo como limitación (el terreno de Cesium no es exactamente el mismo DEM).

### 8. Segunda parte (desde la H22): pitch, demo y video

A partir de aquí tu código está casi terminado y el resto del equipo está en plena integración. Tú preparas lo que ve el jurado.

#### 8.1 Guion del pitch (`pitch/pitch.md`), 3–5 minutos según las reglas del reto

| Tiempo | Bloque | Quién habla | Contenido |
|---|---|---|---|
| 0:00–0:30 | Problema | Tú | Por qué aterrizar en el polo sur es difícil: Sol rasante, sombras largas, la Tierra baja en el horizonte |
| 0:30–1:00 | Solución | Tú | LunaScope en una frase + qué decide (dónde y cuándo) |
| 1:00–3:00 | **Demo en vivo con el mando** | Integrante 4 al mando, tú narras | Ver el guion de la demo |
| 3:00–3:45 | Ciencia | Integrante 2 (+ tú en terreno) | SPICE + LOLA, validación con Horizons, máscara de horizonte |
| 3:45–4:15 | Arquitectura y decisión | Integrante 1 | Diagrama, precálculo, perfiles y pesos visibles |
| 4:15–4:45 | Cierre | Tú | Qué aporta, limitaciones honestas, siguientes pasos |

Ajusta los tiempos a la duración exacta que pida el reto.

#### 8.2 Guion de la demo (`pitch/demo.md`): secuencia exacta de botones

Escríbelo con el Integrante 4 y ensáyalo hasta que salga sin pensar. Ejemplo:

1. Pantalla inicial: globo lunar, polo sur, 3 sitios marcados. *"Estas son 3 de las regiones candidatas de Artemis III."*
2. **R1** dos veces → recorre los sitios. **Cuadrado** → panel de datos de Malapert.
3. **Touchpad** → Mission Time. **R2** a fondo → el tiempo avanza y el Sol gira; **Triángulo** → sombras. *"El relieve tapa el Sol aquí durante 4 días."*
4. **Cruceta derecha** → salta a la mejor ventana con Sol y Tierra a la vez.
5. **Touchpad** → Mission Selection. **Cruceta** → perfil Comunicaciones: el ranking cambia. *"Las prioridades de la misión cambian la recomendación."*
6. **X** → confirmar → informe en pantalla con fuentes y limitaciones.

Cada paso con un tiempo objetivo. Total: menos de 2 minutos.

#### 8.3 Video de respaldo (antes de la H40)

- Graba la demo completa con OBS (pantalla + audio), en 1080p.
- Graba también un video corto de las manos con el mando: es lo que hace distinto al proyecto.
- Guárdalo en local **y** en la nube. Si falla internet o Cesium, se reproduce el video y se sigue narrando igual.

#### 8.4 Slides (`pitch/slides`), 6–8 como máximo

1. Título + frase.
2. El problema (imagen del polo sur con sombras).
3. Cómo funciona (diagrama de arquitectura).
4. (Demo en vivo; sin diapositiva.)
5. Ciencia: tus gráficos de horizonte + la tabla de validación del Integrante 2.
6. Resultados: ranking de los 3 sitios con 2 perfiles.
7. Limitaciones y siguientes pasos.
8. Equipo.

Solo imágenes con licencia libre o propias. Las de NASA suelen ser de dominio público, pero revisa los créditos y cítalos.

#### 8.5 Preguntas frecuentes del jurado (`pitch/faq.md`)

Prepara una respuesta de 1–2 frases para cada una y repártelas entre el equipo:
- ¿Por qué no usan IA? → Motor de decisión explicable: cada número se puede rastrear.
- ¿Qué tan precisos son los datos? → (Integrante 2) Validación con Horizons.
- ¿Por qué estos 3 sitios? → (Tú) Regiones oficiales de Artemis III; punto elegido por altura y pendiente.
- ¿Qué resolución tiene el terreno? → (Tú) Valores reales del DEM utilizado.
- ¿Por qué un mando PS4? → Explorar tiempo y espacio a la vez es más natural con dos joysticks y gatillos analógicos.
- ¿Qué harían con más tiempo? → Simulación de descenso, más sitios, enlaces de comunicación reales, iluminación por píxel.

### 9. Tu horario

| Bloque | Tareas |
|---|---|
| Antes | Descargar los DEM, abrirlos con rasterio, anotar unidades |
| H0–3 | **Coordenadas de los 3 sitios en `sites.json`**, reunión de arranque |
| H3–12 | `Dem`, `local_axes`, `compute_terrain_stats`, `compute_horizon`. **H12:** horizonte real de 1 sitio para el Integrante 2 |
| H12–22 | 3 sitios, prueba de convención con el Integrante 2, modo `fast`, gráficos de horizonte. **MVP** |
| H22–32 | Pitch, guion de la demo, slides, FAQ. Resolver errores de terreno si aparecen |
| H32–40 | Ensayos con el mando, **grabar el video de respaldo** |
| H40–48 | Dirigir 3 ensayos completos con cronómetro y entregar |

### 10. Riesgos

| Riesgo | Qué hacer |
|---|---|
| El DEM es enorme y no cabe en memoria | Recorta a la zona útil con `rasterio.windows` y guarda el recorte; o usa una resolución menor para el horizonte |
| Unidades de altura raras | Leer metadatos y `dem/README.md`; comparar con una altura conocida de la zona |
| Azimut desplazado respecto al Integrante 2 | Prueba de la montaña conocida; revisar `local_axes` |
| No hay tiempo para el pitch | El pitch es parte del MVP del equipo: a partir de la H22 tiene prioridad sobre las mejoras de terreno |

### 11. Definición de terminado

- [ ] `sites.json` con coordenadas reales y su justificación.
- [ ] `compute_horizon` y `compute_terrain_stats` cumplen las firmas y los tiempos.
- [ ] Horizonte de los 3 sitios validado en convención con el Integrante 2.
- [ ] Gráficos de horizonte en `pitch/img/`.
- [ ] Pitch, guion de la demo, slides y FAQ listos y ensayados 3 veces.
- [ ] Video de respaldo grabado y guardado en dos lugares.
