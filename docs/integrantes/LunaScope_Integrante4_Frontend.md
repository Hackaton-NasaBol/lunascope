# LunaScope · Integrante 4 — Frontend 3D + mando PS4

> **Tu misión:** lo que el jurado ve y toca. Construyes el globo lunar 3D, los 3 modos, los paneles y los gráficos, y haces que todo se controle con el mando PS4 de forma fluida. Si la demo se ve bien y el mando responde, el proyecto gana puntos de impacto inmediato.

**Lo que entregas al final:**
1. Aplicación web React + TypeScript + Tailwind en `frontend/`.
2. Globo lunar 3D con CesiumJS y los 3 sitios.
3. Los 3 modos (Explore, Mission Time, Mission Selection) con su interfaz.
4. Capa de control unificada: mando PS4 + teclado + mouse.
5. Gráficos temporales (Plotly), panel de comparación, informe imprimible.
6. Leyenda de botones visible en pantalla para cada modo.

**De quién dependes:** del Integrante 1 (API; desde la H3 hay mocks), del 2 (dirección del Sol para la luz y la interpretación de los gráficos).
**Quién depende de ti:** el equipo entero en la demo. El Integrante 3 escribe contigo el guion de la demo.

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

### 1. Antes del hackathon

- [ ] Node 20+ instalado.
- [ ] Cuenta gratuita en **Cesium ion**. Agrega **Cesium Moon Terrain** a tu biblioteca desde el Asset Depot (asset id **2684829**) y crea un token de acceso.
- [ ] Mando PS4 cargado + **cable USB** (más fiable que Bluetooth para la demo).
- [ ] Chrome actualizado con la aceleración por hardware activada (`chrome://settings` → Sistema).
- [ ] Prueba el mando en una página de prueba de Gamepad API y anota qué índice tiene cada botón en tu equipo.

### 2. Arranque del proyecto (H0–3)

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm i cesium zustand react-plotly.js plotly.js-dist-min
npm i -D tailwindcss postcss autoprefixer vite-plugin-cesium @types/react-plotly.js
npx tailwindcss init -p
```

- `vite.config.ts`: añade `cesium()` de `vite-plugin-cesium`. Copia los assets de Cesium y configura `CESIUM_BASE_URL`.
- `frontend/.env.local` (fuera de git): `VITE_CESIUM_TOKEN=...` y `VITE_API_URL=http://localhost:8000/api`.
- **Prueba el mando delante del equipo en la reunión de arranque.**

Estructura recomendada:

```
frontend/src/
├── main.tsx / App.tsx
├── api/client.ts            # fetch tipado contra el contrato
├── api/types.ts             # tipos TS copiados del contrato
├── mocks/                   # JSON de respaldo con la forma del contrato
├── store.ts                 # estado global (zustand)
├── input/
│   ├── gamepad.ts           # lectura del mando + detección de flancos
│   ├── keyboard.ts          # mismo vocabulario de acciones
│   └── actions.ts           # despachador: acción + modo → cambio de estado
├── globe/
│   ├── Globe.tsx            # viewer de Cesium
│   ├── sites.ts             # marcadores
│   └── lighting.ts          # luz y sombras a partir de az/el del Sol
├── modes/
│   ├── ExploreMode.tsx
│   ├── MissionTimeMode.tsx
│   └── SelectionMode.tsx
└── ui/
    ├── ButtonLegend.tsx     # leyenda de botones según el modo
    ├── ControllerStatus.tsx
    ├── SitePanel.tsx
    ├── TimeChart.tsx
    ├── ComparisonTable.tsx
    └── ReportModal.tsx
```

### 3. El globo lunar (CesiumJS)

```ts
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

Cesium.Ion.defaultAccessToken = import.meta.env.VITE_CESIUM_TOKEN;
Cesium.Ellipsoid.default = Cesium.Ellipsoid.MOON;    // ¡antes de crear el viewer!

export async function createViewer(container: HTMLElement) {
  const viewer = new Cesium.Viewer(container, {
    globe: false, baseLayer: false, baseLayerPicker: false, geocoder: false,
    timeline: false, animation: false, homeButton: false, sceneModePicker: false,
    navigationHelpButton: false, fullscreenButton: false, infoBox: false,
    selectionIndicator: false, skyAtmosphere: false,
  });
  const tileset = await Cesium.Cesium3DTileset.fromIonAssetId(2684829);
  viewer.scene.primitives.add(tileset);
  return { viewer, tileset };
}
```

- Muestra un estado de carga y un mensaje claro si falla la conexión o el token: *"Sin conexión con Cesium: usa el video de respaldo"*.
- Cámara inicial: sobre el polo sur, inclinada (pitch de unos −45°), a una altura que muestre los 3 sitios.
- Desactiva los controles de mouse que choquen con el mando, o déjalos activos solo cuando no haya mando conectado.

**Aviso importante sobre las alturas.** Hay reportes de usuarios en el foro de Cesium de que la superficie de Cesium Moon aparece unos 2,5 km por encima de las alturas LOLA en las mismas coordenadas. Por eso:
- **No uses `elevation_m` del backend para colocar cosas en 3D.** Usa solo lat/lon y deja que Cesium ponga la altura: `scene.sampleHeightMostDetailed` o `HeightReference.CLAMP_TO_3D_TILE` / `clampToHeightMostDetailed`.
- Muestra `elevation_m` del backend solo como **texto** en los paneles.

Marcadores de los sitios: un punto + etiqueta con el nombre; el sitio activo, más grande y de otro color. Si hay punto libre, en un tercer color con la etiqueta "estimado".

### 4. Luz y sombras a partir del Sol de SPICE (Triángulo)

Cesium calcula su Sol pensando en la Tierra; en la Luna lo controlamos nosotros con los datos del backend:

```ts
export function setSunLight(viewer: Cesium.Viewer, lat: number, lon: number,
                            azDeg: number, elDeg: number) {
  const ell = Cesium.Ellipsoid.MOON;
  const origin = Cesium.Cartesian3.fromDegrees(lon, lat, 0, ell);
  const enu = Cesium.Transforms.eastNorthUpToFixedFrame(origin, ell);
  const az = Cesium.Math.toRadians(azDeg), el = Cesium.Math.toRadians(elDeg);
  const local = new Cesium.Cartesian3(Math.cos(el) * Math.sin(az),
                                      Math.cos(el) * Math.cos(az), Math.sin(el));
  const toSun = Cesium.Matrix4.multiplyByPointAsVector(enu, local, new Cesium.Cartesian3());
  Cesium.Cartesian3.normalize(toSun, toSun);
  viewer.scene.light = new Cesium.DirectionalLight({
    direction: Cesium.Cartesian3.negate(toSun, new Cesium.Cartesian3()),  // la luz viaja desde el Sol
  });
}
```

- Sombras: `viewer.shadows = true`, `tileset.shadows = Cesium.ShadowMode.ENABLED`. Ajusta `viewer.shadowMap.maximumDistance` y `softShadows` hasta encontrar un equilibrio entre calidad y FPS.
- Triángulo activa o desactiva las sombras. Si el rendimiento cae por debajo de unos 30 FPS, desactívalas por defecto.
- Etiqueta en pantalla: *"Sombras visuales aproximadas (terreno Cesium)"*. La visibilidad oficial es la de los gráficos (máscara LOLA).
- Revisa con el Integrante 2 que, a una hora con el Sol tapado según los datos, la escena también muestre el sitio en sombra.

### 5. Estado global (`store.ts`)

```ts
type Mode = "explore" | "time" | "selection";
interface State {
  mode: Mode;
  siteIndex: number;                // 0..2 (+ punto libre al final, si existe)
  timeIndex: number;                // float, índice en samples (se interpola)
  playing: boolean;
  speedHoursPerSec: number;         // depende de L2/R2
  profile: "solar" | "comms" | "safety" | "balanced";
  shadows: boolean;
  panel: null | "data" | "score" | "menu" | "report";
  selectionRow: number;
  freePoint: null | { lat: number; lon: number; data?: PointResponse };
  gamepadConnected: boolean;
}
```

Una sola fuente de verdad: el mando, el teclado y los botones en pantalla llaman a las **mismas** acciones.

### 6. Mando PS4 (Gamepad API)

Mapeo estándar de Chrome (`gamepad.mapping === "standard"`):

| Índice | Botón | Índice | Botón |
|---|---|---|---|
| 0 | X | 9 | Options |
| 1 | Círculo | 10 / 11 | L3 / R3 |
| 2 | Cuadrado | 12 / 13 | Cruceta arriba / abajo |
| 3 | Triángulo | 14 / 15 | Cruceta izquierda / derecha |
| 4 / 5 | L1 / R1 | 16 | PS |
| 6 / 7 | L2 / R2 (analógicos: `.value` de 0 a 1) | 17 | Touchpad (clic) |
| 8 | Share | ejes 0,1 / 2,3 | Joystick izq. X,Y / der. X,Y |

> Comprueba este mapeo con tu mando en la H0–3. Si `mapping` no es `"standard"` (puede pasar en otros navegadores o con Bluetooth), muestra un aviso y usa el teclado.

Lectura con detección de flancos (solo el **momento** de pulsar):

```ts
const DEADZONE = 0.15;
let prev: boolean[] = [];

export function pollGamepad(dispatch: (a: Action) => void, analog: (a: Analog) => void) {
  const gp = navigator.getGamepads().find(g => g && g.connected);
  if (!gp) return;
  gp.buttons.forEach((b, i) => {
    if (b.pressed && !prev[i]) dispatch(BUTTON_TO_ACTION[i]);   // flanco de subida
  });
  prev = gp.buttons.map(b => b.pressed);
  const dz = (v: number) => (Math.abs(v) < DEADZONE ? 0 : v);
  analog({
    lx: dz(gp.axes[0]), ly: dz(gp.axes[1]), rx: dz(gp.axes[2]), ry: dz(gp.axes[3]),
    l2: gp.buttons[6].value, r2: gp.buttons[7].value,
  });
}
// llamarlo en un único bucle requestAnimationFrame junto con el avance del tiempo
```

- El navegador **no detecta el mando hasta que se pulsa un botón** después de cargar la página. Muestra *"Pulsa cualquier botón del mando"* mientras `gamepadConnected` sea falso.
- Escucha `gamepadconnected` / `gamepaddisconnected` para actualizar `ControllerStatus`.
- Vibración al confirmar con X: `gp.vibrationActuator?.playEffect("dual-rumble", {duration: 200, strongMagnitude: 0.6, weakMagnitude: 0.3})`. Es opcional: si no está disponible, no pasa nada.

### 7. Despachador de acciones por modo (`actions.ts`)

Implementa **exactamente** la tabla de controles de la parte común. Esquema:

```ts
export function handle(action: Action, s: State): Partial<State> | void {
  // globales
  if (action === "touchpad") return { mode: next(s.mode), panel: null };
  if (action === "circle")   return { panel: null };
  if (action === "options")  return { panel: s.panel === "menu" ? null : "menu" };
  switch (s.mode) {
    case "explore":   return explore(action, s);
    case "time":      return missionTime(action, s);
    case "selection": return selection(action, s);
  }
}
```

Comportamiento continuo (en el bucle de animación, no como acción):
- **Explore:** el joystick izquierdo desplaza la cámara sobre la superficie; la retícula queda fija en el centro de la pantalla. El joystick derecho orbita e inclina. L2/R2 hacen zoom.
- **Mission Time:** `timeIndex += (r2 − l2) × velocidadMáx × dt`, con una velocidad máxima de unas 48 h simuladas por segundo; se limita a [0, n−1]. Si está en reproducción (X), avanza a 6 h/s aunque no se toquen los gatillos.
- Cada vez que cambia `timeIndex` o el sitio: interpolar az/el del Sol entre muestras y llamar a `setSunLight`.

**Punto libre** (segunda prioridad): X en Explore → `scene.pickPosition(centroPantalla)` → `Cartographic.fromCartesian(p, Ellipsoid.MOON)` → lat/lon en grados → `POST /api/point`. Mientras responde, muestra *"Analizando punto… (estimado)"*. Si devuelve `outside_dem`, avisa.

### 8. Pantallas por modo

**Siempre visible:** nombre del modo (arriba a la izquierda), sitio activo, fecha y hora UTC, `ControllerStatus` (icono + "Mando conectado"/"Pulsa un botón") y `ButtonLegend` (abajo, con los iconos de los botones del modo actual).

**Explore Mode**
- Globo a pantalla completa, retícula en el centro.
- Cuadrado → `SitePanel` lateral: nombre, región, lat/lon, elevación (texto), pendiente media/máxima, % de peligro, % de Sol y de Tierra visibles.

**Mission Time Mode**
- Globo arriba (~60 %) y `TimeChart` abajo (~40 %).
- `TimeChart` (Plotly) para el sitio activo, eje X = tiempo:
  - Línea: elevación del Sol. Línea discontinua: horizonte en el azimut del Sol.
  - Línea: elevación de la Tierra. Línea discontinua: horizonte en el azimut de la Tierra.
  - Bandas sombreadas: ventanas con Sol y Tierra a la vez.
  - Línea vertical: instante actual (se mueve con L2/R2).
- Indicadores grandes: "☀ Sol visible: SÍ/NO (fracción)" y "🌍 Tierra visible: SÍ/NO".
- Cruceta izquierda/derecha → salta al inicio de la ventana anterior/siguiente.
- Plotly es pesado: no lo vuelvas a renderizar en cada fotograma. Mueve solo la línea del instante (con `Plotly.relayout` sobre `shapes`) o limita las actualizaciones a ~10 por segundo.

**Mission Selection Mode**
- `ComparisonTable`: una fila por sitio (+ punto libre con la etiqueta "estimado"), columnas: puntuación total, sol, tierra, continuidad, terreno. Fila seleccionada con el joystick izquierdo; el recomendado, destacado.
- Selector de perfil arriba (cruceta); al cambiar → `GET /api/score?profile=...` → la tabla se reordena con una animación breve. **Es un momento clave de la demo.**
- Cuadrado → detalle: las frases de `explanation`.
- X → `POST /api/report` → `ReportModal` con todos los campos, incluidas fuentes y limitaciones, y un botón "Imprimir / PDF" (`window.print()` con estilos `@media print`).

### 9. Diseño visual

- Tema oscuro (espacio), un color de acento para lo seleccionado y lo recomendado.
- Tipografía grande: el jurado ve la pantalla desde lejos. Mínimo 16 px en paneles y 24 px en indicadores.
- Paneles semitransparentes sobre el globo, con fondo borroso.
- Transiciones cortas (150–250 ms). Nada debe tardar más de 300 ms en reaccionar a un botón.
- Todo lo aproximado lleva la etiqueta "estimado" o "aproximado".

### 10. Datos y API

- `api/types.ts`: tipos TypeScript **copiados del contrato**. Si el contrato cambia, se actualizan aquí primero.
- Al iniciar: `GET /sites`, después `GET /sites/{id}/timeseries` de los 3 (en paralelo) y `GET /score?profile=solar`. Guárdalo todo en memoria: la simulación temporal es 100 % local.
- Si la API no responde, carga `src/mocks/` y muestra un aviso discreto "Datos de demostración".

### 11. Tu horario

| Bloque | Tareas |
|---|---|
| Antes | Token de Cesium, Moon Terrain en la biblioteca, mando probado, Node |
| H0–3 | Proyecto Vite, mando probado delante del equipo, globo lunar visible |
| H3–12 | Store, gamepad + teclado + despachador, 3 modos con mocks, marcadores, leyenda de botones. **H12:** se navega por los 3 sitios con el mando |
| H12–22 | Conectar la API real, `TimeChart`, Mission Time con L2/R2, tabla de comparación, confirmar con X + informe básico. **MVP** |
| H22–32 | Luz y sombras, punto libre, 4 perfiles, panel de estado del mando, pulido visual |
| H32–40 | Ensayar el guion de la demo con el Integrante 3, medir FPS, corregir errores, ayudar a grabar el video |
| H40–48 | Eres quien maneja el mando en la demo: ensaya hasta que salga sin mirar los botones |

### 12. Riesgos

| Riesgo | Qué hacer |
|---|---|
| Cesium tarda en cargar o falla | Precargar la vista inicial antes de presentar; si falla, video de respaldo |
| FPS bajos con sombras | Sombras desactivadas por defecto, `maximumDistance` menor, ventana más pequeña |
| El mando no se detecta en el momento de la demo | Cable USB, pulsar un botón tras cargar, recargar la página; teclado como plan B (el guion de la demo tiene las teclas equivalentes) |
| Botones con otro índice | Tabla `BUTTON_TO_ACTION` en un único archivo, fácil de cambiar |
| Marcadores flotando o enterrados | Altura de Cesium (`clampTo...`), nunca la de LOLA |
| Plotly congela la interfaz | Actualizar solo la línea del instante, a ~10 Hz |

### 13. Definición de terminado

- [ ] El globo lunar 3D carga y muestra los 3 sitios bien colocados.
- [ ] Toda la tabla de controles funciona con el mando **y** con el teclado.
- [ ] Mission Time: L2/R2 mueven el tiempo con suavidad; el gráfico y la luz se sincronizan.
- [ ] Mission Selection: cambiar de perfil reordena la tabla; X genera el informe imprimible.
- [ ] Leyenda de botones y estado del mando siempre visibles.
- [ ] Funciona con mocks si la API falla.
- [ ] La demo completa se hace en menos de 2 minutos sin errores, 3 veces seguidas.
