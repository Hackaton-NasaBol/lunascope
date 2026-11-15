# LunaScope · Frontend (Integrante 4)

React + TypeScript + Tailwind + CesiumJS + Plotly. Se controla con un mando PS4 (Gamepad API) o con el teclado.

## Arranque

```bash
cd frontend
npm install
cp .env.example .env.local     # pon tu token de Cesium ion (no se sube a git)
npm run dev                    # http://localhost:5173
```

- Con el backend en marcha (`http://localhost:8000/api`), los datos vienen de la API.
- Si la API no responde, se cargan los mocks de `src/mocks/data/` y aparece "Datos de demostración".
- Sin `VITE_CESIUM_TOKEN`, el globo es un elipsoide liso (sin relieve), pero todo lo demás funciona.
- `npm run sync-mocks` vuelve a copiar los JSON de `backend/data/` a `src/mocks/data/`. Ejecútalo cuando lleguen los datos reales.

## Controles

| Control | Teclado | Explore | Mission Time | Mission Selection |
|---|---|---|---|---|
| Joystick izq. | WASD / flechas | Mover la cámara (retícula fija) | — | Recorrer filas |
| Joystick der. | ratón | Orbitar / inclinar | Orbitar / inclinar | — |
| L1 / R1 | Q / E | Sitio ant. / sig. | Sitio ant. / sig. | Sitio ant. / sig. |
| L2 / R2 | Z / C | Zoom | Tiempo −/+ (hasta 48 h/s) | — |
| X | Enter | Punto libre en la retícula | Pausa / play (6 h/s) | Confirmar → informe |
| Cuadrado | I | Panel del sitio | Panel del instante | Detalle de la puntuación |
| Triángulo | T | Sombras del relieve | Sombras del relieve | — |
| Cruceta | 1 ← · 2 → · 3 ↑ · 4 ↓ | ↑↓ capa: ninguna / elevación / pendiente | ←→ ventana ant. / sig. · ↑↓ capa | Cambiar de perfil |
| Círculo | Esc | Cerrar panel | Cerrar panel | Cerrar panel |
| Touchpad | Tab | Siguiente modo | Siguiente modo | Vuelve a Explore |
| Options | M | Menú | Menú | Menú |

Si los índices de los botones de tu mando son distintos, cámbialos en `BUTTON_TO_ACTION` ([src/input/gamepad.ts](src/input/gamepad.ts)).
El ratón mueve la cámara solo cuando no hay mando conectado.

## Estructura

```
src/
├── api/        types.ts (copiados del contrato) + client.ts
├── mocks/      JSON de respaldo + puntuación local (port del motor del backend)
├── store.ts    estado global (zustand): una sola fuente de verdad
├── input/      gamepad.ts, keyboard.ts, actions.ts (tabla de controles), loop.ts (rAF único)
├── globe/      Globe.tsx (viewer), sites.ts (marcadores), lighting.ts (luz del Sol SPICE)
├── modes/      ExploreMode, MissionTimeMode, SelectionMode
└── ui/         TopBar, ButtonLegend, ControllerStatus, SitePanel, TimeChart, ComparisonTable, ScoreDetail, ReportModal, Menu
```

## Capas y sombras (modo análisis)

- Al activar una capa (cruceta ↑↓) o las sombras (Triángulo), el globo pasa a **modo análisis**: se oculta Cesium Moon
  Terrain y se muestra el **relieve del DEM LOLA** servido por el backend (`/api/terrain/heightmap`), con un relieve
  sombreado de fondo. Así el 3D, la pendiente, el horizonte y las sombras salen del mismo DEM.
- **Sombras del relieve:** las calcula el backend (`/api/illumination/{id}.png?t=…`) con el DEM LOLA y el Sol de la serie
  SPICE, en ±35 km alrededor del sitio activo; se piden por horas y hay como mucho una petición en curso.
  Muestran el suelo; la visibilidad oficial del sitio (antena a +2 m) es la del gráfico.
- Si el backend no tiene el DEM, las sombras pasan a las aproximadas de Cesium y se indica en la leyenda.
- Las imágenes de `public/layers/` se generan con `backend/scripts/make_layers.py`.

## Notas

- Los marcadores usan solo lat/lon y `CLAMP_TO_GROUND`: nunca `elevation_m` de LOLA (Cesium Moon está ~2,5 km más alto). La elevación solo se muestra como texto.
- La luz de la escena se orienta con el az/el del Sol del backend. Las sombras están desactivadas por defecto (Triángulo) y se etiquetan como aproximadas.
- El gráfico se dibuja una vez por sitio; la línea del instante se actualiza a ~10 Hz.
