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

### Registro de cambios del contrato

| Fecha / hora | Cambio | Aprobado por |
|---|---|---|
| 2026-11-14 (antes de la H3) | Campo opcional `source: "real" \| "mock"` en `horizon.json`, `terrain.json` y `timeseries.json` (por defecto `"real"`). Los módulos reales no tienen que ponerlo. | Integrante 1 |
| 2026-11-14 (antes de la H3) | Cada elemento de `GET /sites` añade `quality` (`"full"`), `complete` (bool: tiene los 3 JSON) y `source`. `terrain`/`summary` pueden ser `null` si falta el archivo. | Integrante 1 |
| 2026-11-14 (antes de la H3) | `GET /score` añade `notes: [...]` (p. ej. "El punto libre puntúa más alto, pero su análisis es aproximado."). Perfil desconocido → 404 `profile_not_found`. | Integrante 1 |
| 2026-11-14 (antes de la H3) | `POST /point` añade `elapsed_s`. Los `point_id` (`p-1`, `p-2`…) también sirven en `/sites/{id}/horizon\|terrain\|timeseries` y en `/report`. Body inválido → 422 `invalid_request`; fuera del DEM → 422 `outside_dem`. | Integrante 1 |
| 2026-11-14 (antes de la H3) | `POST /report` añade `quality` (`"full"` o `"estimated"`). | Integrante 1 |
| 2026-11-14 (tras integrar SPICE + LOLA reales) | `continuity`: el límite de la noche más larga pasa de **240 h a 720 h** (`100 × max(0, 1 − longest_dark_h / 720)`). Con 240 h los 3 sitios reales puntuaban 0 (noches de 328–1441 h) y la columna no distinguía nada. Constante `CONTINUITY_MAX_DARK_H` en `backend/lunascope/scoring/engine.py` (y su copia en `frontend/src/mocks/index.ts`). | Integrante 1 |
| 2026-11-15 | Capas del terreno y sombras: endpoints `/illumination/{id}/meta`, `/illumination/{id}.png?t=…`, `/terrain/info` y `/terrain/heightmap/{z}/{x}/{y}.bin`. Capas fijas `frontend/public/layers/` (elevación, pendiente, relieve sombreado) generadas con `backend/scripts/make_layers.py`. Controles: Triángulo = sombras del relieve; cruceta ↑↓ = capa en Explore y Mission Time. | Integrante 1 |
