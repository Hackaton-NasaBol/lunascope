# LunaScope · Guía técnica y de pitch

> Documento de referencia para preparar el pitch y responder al jurado. Todas las cifras salen de los datos reales del
> repositorio (`backend/data/precomputed/`, ventana de misión 1 sep – 31 oct 2027). Si se regeneran los datos, revisad
> las tablas de la sección 9.

---

## 1. En una frase

**LunaScope es un planificador de misiones lunares en 3D que, con datos de NASA (efemérides SPICE y relieve LOLA),
calcula cuándo y dónde hay Sol y Tierra visibles en el polo sur de la Luna, y recomienda un sitio de aterrizaje con un
motor de decisión explicable. Todo se maneja con un mando de PS4.**

### Versión de 30 segundos (para abrir)

> "En el polo sur de la Luna el Sol nunca sube más de unos 6 grados. Una montaña a decenas de kilómetros puede dejar
> un módulo a oscuras durante días, sin energía y sin ver la Tierra. Artemis III no solo tiene que decidir *dónde*
> aterrizar, sino *cuándo*. LunaScope cruza las efemérides de NASA con el relieve medido por láser desde órbita para
> responder exactamente eso, hora a hora, y explica con números por qué recomienda cada sitio."

---

## 2. El problema

- El polo sur lunar es el objetivo de **Artemis III**. En octubre de 2024 NASA anunció **9 regiones candidatas** de
  aterrizaje (Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1 y 2,
  de Gerlache Rim 2 y Slater Plain).
- Cerca del polo el Sol va **rozando el horizonte**: en nuestros sitios su elevación máxima es de 4–6°. Cualquier
  relieve, incluso lejano, lo tapa. Por eso hay zonas con luz casi constante a pocos kilómetros de cráteres en
  **sombra permanente** (los que pueden guardar hielo de agua).
- Una misión necesita a la vez:
  - **Sol** para energía y temperatura.
  - **Tierra visible** para comunicarse directamente (sin satélites repetidores).
  - **Terreno poco inclinado** para aterrizar con seguridad.
- Estas tres cosas cambian **con el tiempo** (el Sol da una vuelta al horizonte cada ~29,5 días y la Tierra oscila por
  la libración) y **con el lugar** (unos metros de altura o una ladera cambian el resultado). Hoy esto se analiza con
  herramientas separadas y para especialistas.

**Lo que resolvemos:** juntar geometría orbital, relieve real, evolución temporal y criterios de misión en una sola
herramienta interactiva, verificable y explicable.

---

## 3. Qué hace LunaScope

| Modo | Qué se ve | Para qué sirve |
|---|---|---|
| **Explore** | Globo lunar 3D con los 3 sitios. Capas de **elevación** (verde → rojo) y **pendiente** (> 10° en rojo). Panel con datos del sitio. Análisis de un **punto libre** cualquiera. | Entender el terreno y comparar sitios a simple vista. |
| **Mission Time** | Gráfico de 60 días: elevación del Sol y de la Tierra frente al horizonte real. Ventanas con Sol + Tierra a la vez. **Sombras del relieve** calculadas que se mueven con el tiempo. | Ver *cuándo* hay luz y comunicación, y por qué se pierde. |
| **Mission Selection** | Ranking de los sitios según el perfil de misión (energía solar, comunicaciones, seguridad, equilibrado), con el desglose y las frases que lo explican. | Decidir y justificar. Al confirmar se genera un **informe imprimible** con fuentes y limitaciones. |

Control: mando PS4 (Gamepad API) con equivalente en teclado. El touchpad cambia de modo, los gatillos L2/R2 mueven el
tiempo, la cruceta cambia de perfil o de capa y Triángulo activa las sombras.

---

## 4. De dónde salen los datos

**No usamos ninguna API de datos en vivo durante la demo.** Todo sale de **ficheros oficiales de NASA descargados una
vez** y procesados por nosotros. Lo único que va por internet en la demo es el terreno 3D de Cesium (opcional: hay
respaldo sin internet).

| Dato | Fuente (organismo) | Qué es | Cómo lo usamos |
|---|---|---|---|
| **Kernels SPICE** | NASA NAIF (JPL) | Ficheros con las posiciones del Sol, la Tierra y la Luna, y la orientación de la Luna | Calcular hacia dónde y a qué altura se ven el Sol y la Tierra desde cada sitio, cada hora |
| **DEM LOLA** `LDEM_80S_80MPP_ADJ.TIF` | NASA Goddard, PGDA (producto 90), misión LRO | Mapa de alturas del polo sur (80°S–90°S) a 80 m/píxel | Horizonte de cada sitio, pendientes, relieve 3D, sombras y capas |
| **Regiones candidatas Artemis III** | NASA (anuncio de oct. 2024) | Las 9 zonas propuestas | Elegimos 3 regiones; el punto exacto se escogió sobre el DEM |
| **Cesium Moon Terrain** (asset 2684829) | Cesium ion (basado en datos de NASA) | Terreno 3D de la Luna con textura | Vista "bonita" por defecto (necesita internet y token) |
| **Mosaico de color LROC WAC** | NASA SVS, "CGI Moon Kit" (dominio público) | Textura global de la Luna | Respaldo visual sin internet |
| **JPL Horizons** | NASA JPL | Servicio de efemérides de referencia | **Solo para validar** nuestros cálculos (no se usa en la demo) |

### Los 5 kernels SPICE que usamos

| Kernel | Qué contiene |
|---|---|
| `naif0012.tls` | Segundos intercalares: convertir hora UTC a tiempo de efemérides |
| `pck00011.tpc` | Constantes físicas de los cuerpos (radios, etc.) |
| `de440s.bsp` | Efemérides planetarias DE440 (posiciones del Sol, la Tierra y la Luna, 1849–2150) |
| `moon_pa_de440_200625.bpc` | Orientación precisa de la Luna (incluida la libración) |
| `moon_de440_250416.tf` | Define el marco **MOON_ME** ("Mean Earth / Polar Axis"), el mismo que usa LOLA |

Usar el **mismo marco (MOON_ME)** que el DEM es clave: si no, el horizonte y el Sol estarían girados entre sí.

---

## 5. ¿Qué es el DEM LOLA?

- **DEM** = *Digital Elevation Model*, un mapa donde cada píxel guarda una **altura**.
- **LOLA** = *Lunar Orbiter Laser Altimeter*, el altímetro láser a bordo de la sonda **LRO** (*Lunar Reconnaissance
  Orbiter*) de NASA, en órbita lunar desde 2009. Dispara pulsos láser hacia la superficie y mide cuánto tardan en
  volver: así obtiene la altura con precisión de metros. Con miles de millones de medidas se construye el mapa.
- Ventaja en el polo: el láser **no necesita luz solar**, así que mide también el fondo de los cráteres en sombra
  permanente, donde las cámaras no ven nada.
- El fichero que usamos, `LDEM_80S_80MPP_ADJ.TIF`:
  - Cubre del **80°S al polo**, en proyección **polar estereográfica**.
  - **7600 × 7600 píxeles a 80 m/píxel** (~190 MB).
  - Alturas en **metros sobre una esfera de 1 737 400 m** (la convención de LOLA).
  - Lo publica NASA Goddard (PGDA, producto 90).

---

## 6. ¿Qué es SPICE?

**SPICE** es el sistema de NASA (NAIF, en JPL) que usan las misiones reales para saber **dónde está cada cuerpo y cómo
está orientado** en cualquier instante. Se compone de "kernels" (los ficheros de la tabla anterior) y una librería de
funciones. Nosotros lo usamos desde Python con **SpiceyPy**.

---

## 7. Los cálculos, paso a paso

### 7.1 Posición del Sol y de la Tierra desde un sitio (Integrante 2, `backend/lunascope/science/`)

1. Posición del sitio en el marco MOON_ME: latitud, longitud y altura (terreno + **2 m** de antena).
2. Posición aparente del Sol y de la Tierra cada hora con `spkpos` (marco MOON_ME, corrección `LT+S`: tiempo de
   luz y aberración).
3. Vector sitio → objeto, proyectado en los ejes locales **Este–Norte–Arriba** del sitio:
   - **Azimut** = ángulo desde el norte local, en sentido horario (N = 0°, E = 90°).
   - **Elevación** = ángulo sobre el plano horizontal local.
4. Resultado: **1441 muestras** (1 por hora durante 60 días) para cada sitio.

### 7.2 Máscara de horizonte (Integrante 3, `backend/lunascope/terrain/horizon.py`)

Para cada azimut de 0° a 359° se recorre el DEM en línea recta **hasta 150 km** y se calcula el ángulo más alto que
forma el relieve visto desde el sitio:

```
ángulo(s) = atan( (z(s) − z0 − h_obs − s² / (2R)) / s )      horizonte(az) = máximo de ángulo(s)
```

- `z(s)`: altura del terreno a distancia `s`; `z0`: altura del sitio; `h_obs` = 2 m; `R` = 1 737 400 m.
- `s² / 2R` es la **caída por la curvatura lunar**: a 100 km el suelo "baja" **~2,9 km**. Sin esta corrección todos
  los horizontes saldrían demasiado altos.

### 7.3 ¿Se ve el Sol? ¿Se ve la Tierra?

- Se compara la elevación del objeto con el horizonte **en su mismo azimut**.
- **Fracción visible del disco** (aproximación lineal): `clip((el − horizonte + r) / (2r), 0, 1)`, con `r` = radio
  angular (Sol 0,267°, Tierra 0,95°).
- "Visible" = al menos la mitad del disco (≥ 0,5).
- A partir de ahí: % del tiempo con Sol, % con Tierra, % con ambos, **noche más larga**, y las **ventanas** continuas
  con Sol y Tierra a la vez (las 10 más largas).

### 7.4 Terreno del sitio (Integrante 3, `backend/lunascope/terrain/stats.py`)

- **Pendiente** = gradiente del DEM: `pendiente = atan(√(dz/dx² + dz/dy²))`.
- En un radio de 100 m: pendiente media, máxima y **% peligroso** (píxeles con más de **10°**).

### 7.5 Puntuación y recomendación (Integrante 1, `backend/lunascope/scoring/`)

Cuatro subpuntuaciones de 0 a 100:

| Subpuntuación | Fórmula |
|---|---|
| Sol | % del tiempo con Sol visible |
| Tierra | % del tiempo con Tierra visible |
| Continuidad | `100 × max(0, 1 − noche_más_larga / 720 h)` (30 días sin Sol → 0) |
| Terreno | `100 × max(0, 1 − pendiente_media / 15°) × (1 − %peligro / 100)` |

`Puntuación = Σ peso × subpuntuación`, con pesos según el perfil:

| Perfil | Sol | Tierra | Continuidad | Terreno |
|---|---|---|---|---|
| Energía solar | 50 % | 15 % | 20 % | 15 % |
| Comunicaciones | 20 % | 50 % | 10 % | 20 % |
| Seguridad de aterrizaje | 20 % | 20 % | 10 % | 50 % |
| Equilibrado | 25 % | 25 % | 25 % | 25 % |

- Las **explicaciones** se generan con plantillas a partir de los números ("su punto fuerte…", "punto débil…",
  "mejor ventana: 4 oct 10:00 UTC, 384 h"). **No hay texto inventado ni modelo de lenguaje.**
- Un **punto libre** (analizado al momento) puede aparecer en el ranking pero **nunca** sale como recomendado: su
  análisis es aproximado (horizonte a 50 km y paso de 2 h).

### 7.6 Sombras del relieve (`backend/lunascope/terrain/illumination.py`)

Para el sitio activo y el instante elegido, el backend calcula qué parte del terreno está en sombra en ±35 km:

1. Toma el DEM en ±60 km y corrige la curvatura respecto al plano tangente del sitio (`z − d²/2R`).
2. Toma la dirección del Sol de la **misma serie SPICE** que pinta el gráfico (coinciden siempre).
3. Gira la rejilla para que la luz viaje a lo largo de las columnas y la **barre** manteniendo la "línea de sombra":
   un punto está iluminado si queda por encima de la sombra que proyecta todo lo que tiene delante.
4. Comprueba además que el Sol esté sobre el horizonte local de cada punto.
5. Devuelve una imagen (PNG) que el globo pinta sobre el relieve. Tarda unos 0,4 s por instante.

### 7.7 Capas del globo (`backend/scripts/make_layers.py`)

Del mismo DEM se generan tres imágenes para el globo: **elevación** (escala hipsométrica verde → amarillo → rojo),
**pendiente** (verde < 5°, amarillo ~10°, rojo > 15°) y un **relieve sombreado** de fondo. Al activar una capa o las
sombras, el globo pasa a "modo análisis": muestra el **relieve 3D del propio DEM LOLA**, servido por el backend. Así el
3D, el horizonte, la pendiente y las sombras salen **del mismo dato**.

---

## 8. Validación (lo que podemos demostrar)

| Qué | Cómo | Resultado |
|---|---|---|
| Posición del Sol y la Tierra | Comparación con **JPL Horizons** (Malapert, 3 días, cada 6 h) | Diferencia máxima **0,0000°** (`docs/validation.md`) |
| Convención de azimut entre ciencia y terreno | Horizonte recalculado con los ejes de las sombras frente a la máscara del Integrante 3 | Error medio **0,04°**, sin giro |
| Sombras frente al gráfico | Iluminación del sitio en el mapa de sombras frente a la serie SPICE + horizonte, cada 12 h | Coinciden el **96 %** (Malapert), **100 %** (Haworth) y **87 %** (Mons Mouton) de las veces |
| Reproducibilidad | Regenerar los datos con los mismos kernels y DEM | Resultado **idéntico byte a byte** |
| Contrato de datos | Modelos Pydantic + **56 pruebas automáticas** | Todas pasan |

Por qué las sombras no coinciden al 100 % en Mons Mouton: el mapa de sombras pinta **el suelo** a 80 m, y el gráfico
mide **la antena a +2 m** en el punto exacto. En una ladera de ~10° con el Sol a 1–2°, esa diferencia basta. Por eso
en pantalla la visibilidad "oficial" del sitio es la del gráfico, y lo decimos en la leyenda.

---

## 9. Resultados actuales (ventana 1 sep – 31 oct 2027)

| Sitio | Coordenadas | Altura | Pendiente media | Sol visible | Tierra visible | Noche más larga | Mejor ventana Sol + Tierra |
|---|---|---|---|---|---|---|---|
| **Malapert Massif** | 85,99°S, 2,93°E | 5127 m | 4,4° | **51,6 %** | **100 %** | 328 h | 4 oct 10:00 UTC, **384 h** |
| **Mons Mouton Plateau** | 85,40°S, 31,50°E | 6413 m | 10,1° | **52,0 %** | **100 %** | 336 h | 9 oct 15:00 UTC, 382 h |
| **Haworth** | 87,45°S, 5,10°O | −3313 m | 4,8° | **0 %** | **0 %** | 1441 h (todo) | ninguna |

Puntuación por perfil:

| Perfil | Malapert | Mons Mouton | Haworth |
|---|---|---|---|
| Energía solar | **62,3** | 54,1 | 10,2 |
| Comunicaciones | **79,9** | 69,0 | 13,6 |
| Seguridad | **71,0** | 43,9 | 34,0 |
| Equilibrado | **69,1** | 55,4 | 17,0 |

**Lectura:** Malapert gana por su terreno suave (4,4°). Mons Mouton tiene la misma luz y la misma visibilidad de la
Tierra, pero su punto está en una ladera de ~10°. Haworth, tal como está colocado (fondo del cráter, −3313 m), está
en **sombra permanente**: el cálculo es correcto, pero es un mal candidato para aterrizar (ver sección 14).

---

## 10. Tecnologías y librerías

### Backend (Python)

| Librería | Para qué |
|---|---|
| **FastAPI** + Uvicorn | API REST (`/api/sites`, `/score`, `/report`, `/point`, `/illumination`, `/terrain`…) con documentación automática en `/docs` |
| **Pydantic** | Modelos del contrato de datos: si alguien rompe el formato, la API falla al instante |
| **SpiceyPy** | Interfaz Python de **NASA SPICE** (efemérides y orientación) |
| **Rasterio** (GDAL) | Leer el GeoTIFF del DEM LOLA |
| **pyproj** | Convertir latitud/longitud ↔ proyección polar estereográfica del DEM |
| **NumPy / SciPy** | Cálculo vectorizado, interpolación bilineal (`map_coordinates`), gradientes |
| **Pillow** | Generar las imágenes de sombras y capas |
| **pytest** | 56 pruebas (puntuación, API, ciencia, terreno, sombras) |

### Frontend (navegador)

| Librería | Para qué |
|---|---|
| **React 19 + TypeScript** (Vite) | Interfaz y lógica |
| **CesiumJS** | Globo 3D con elipsoide lunar, Cesium Moon Terrain y relieve LOLA propio (`CustomHeightmapTerrainProvider`) |
| **Plotly** | Gráfico temporal de 60 días |
| **Zustand** | Estado global único: mando, teclado y ratón llaman a las mismas acciones |
| **Tailwind CSS** | Diseño de los paneles |
| **Gamepad API** (estándar web) | Mando PS4 sin instalar nada |

---

## 11. Arquitectura

```
Mando PS4 / teclado ──▶ Frontend (React + CesiumJS + Plotly) ◀── JSON / imágenes ──▶ Backend FastAPI
                                                                                     │
          ┌──────────────────────────────────────────────────────────────────────────┤
          ▼                                   ▼                                       ▼
  terrain/ (DEM LOLA)            science/ (SPICE)                          scoring/ (motor de decisión)
  horizonte · pendientes ──▶     Sol y Tierra · visibilidad ──▶            perfiles · ranking · explicaciones
  relieve 3D · sombras · capas    ventanas
```

- Los 3 sitios se **precalculan** (`scripts/precompute.py`) y se guardan como JSON: la demo es instantánea y funciona
  **sin internet y sin kernels ni DEM**.
- Solo se calculan al momento los **puntos libres** (< 0,1 s) y las **sombras** (~0,4 s, necesitan el DEM).
- Respaldo en cada capa: sin API → datos de demostración; sin token de Cesium → relieve LOLA o textura NASA; sin
  DEM → sombras aproximadas de Cesium. Siempre se indica en pantalla.

---

## 12. Qué nos diferencia

1. **Datos científicos reales, no simulados**: efemérides de NASA validadas contra JPL Horizons (0,0000°) y relieve
   medido por láser (LOLA). Cada número es trazable hasta un fichero de NASA.
2. **Tiempo + espacio + decisión en una herramienta**: otras herramientas muestran un mapa o una gráfica; aquí se ve
   *dónde* (3D), *cuándo* (60 días hora a hora) y *qué conviene* (ranking por perfil).
3. **Explicable, no caja negra**: pesos visibles, desglose numérico y frases generadas a partir de los datos. El
   jurado puede preguntar "¿por qué?" y la respuesta está en pantalla.
4. **Un solo DEM para todo**: el horizonte, la pendiente, las sombras y el relieve 3D del modo análisis salen del
   mismo modelo LOLA, así que no se contradicen.
5. **Honestidad científica**: cada pantalla dice qué es real, qué es aproximado y qué no cubre (por ejemplo, que ver la
   Tierra no garantiza un enlace de radio).
6. **Interacción natural**: con dos joysticks y gatillos analógicos se recorre el espacio y el tiempo a la vez.

---

## 13. Limitaciones (decirlas antes de que las pregunten)

- **Visibilidad geométrica**: ver la Tierra no es lo mismo que tener enlace de radio (no modelamos antenas ni
  satélites repetidores).
- **Fracción del disco** aproximada de forma lineal.
- **Resolución del DEM: 80 m**. No hay sombras ni pendientes más finas que eso. En un radio de 100 m la pendiente se
  calcula con muy pocos píxeles: es indicativa.
- **Sombras**: relieve hasta 60 km, Sol como punto (sin penumbra). Los horizontes de los sitios sí llegan a 150 km.
- **Puntos libres**: horizonte de 50 km y paso de 2 h.
- **Ventana de misión fija**: 60 días desde el 1 sep 2027 (se puede regenerar para otras fechas).
- **Cesium Moon Terrain** está ~2,5 km más alto que LOLA en algunas zonas: por eso las alturas que mostramos son
  siempre las de LOLA y los análisis se hacen sobre nuestro relieve LOLA.

---

## 14. Antes del pitch: correcciones pendientes

### Datos (Integrante 3)

- **Haworth**: el punto está en el fondo del cráter (−3313 m), en sombra permanente → 0 % de Sol y de Tierra y último
  en todos los perfiles. Las regiones de Artemis III están en zonas altas: conviene moverlo al borde o a una cresta.
- **Mons Mouton Plateau**: pendiente media de 10,1° (por encima del umbral de 10°). Conviene buscar un rellano más
  plano en la misma región.
- Ahora **Malapert gana con todos los perfiles**, así que el momento de la demo "cambias de perfil y cambia la
  recomendación" no ocurre. Con los dos cambios anteriores es probable que sí.

### Frases del material actual que no cuadran con los datos

| Dónde | Dice | Corregir a |
|---|---|---|
| `pitch/pitch.md` (apertura) | "el Sol nunca sube más de 2 o 3 grados" | "nunca sube más de unos **6 grados**" (máximo en nuestros sitios: 4,1–6,1°) |
| `pitch/pitch.md` (demo) | "sombras dinámicas" | Correcto ahora: **sombras calculadas con LOLA + SPICE** (Triángulo) |
| `pitch/faq.md` (2) | "discrepancias menores a 0,05°" | "**0,0000°** de diferencia máxima con JPL Horizons" (`docs/validation.md`) |
| `pitch/faq.md` (3) | "umbral seguro de 8 grados" | El umbral del proyecto es **10°** (y Mons Mouton está en 10,1°) |
| `pitch/faq.md` (4) | "sub-ventanas de alta resolución" | La pendiente usa el mismo DEM de **80 m**; es indicativa en 100 m de radio |

---

## 15. Guion sugerido (4–5 minutos)

| Tiempo | Quién | Qué decir / hacer |
|---|---|---|
| 0:00–0:30 | Int. 3 | **Problema**: Sol rasante (máx. ~6°), sombras de días, hielo en cráteres oscuros, Artemis III debe elegir dónde *y cuándo*. |
| 0:30–1:00 | Int. 3 | **Solución**: LunaScope cruza SPICE + LOLA, 3 sitios oficiales de Artemis III, decisión explicable, mando PS4. |
| 1:00–1:40 | Int. 4 (mando) | **Explore**: globo 3D → R1 recorre los sitios → □ panel de datos → ▲▼ capa de **pendiente** ("rojo = peligroso, > 10°") y **elevación**. |
| 1:40–2:40 | Int. 4 | **Mission Time**: R2 acelera el tiempo; el gráfico muestra el Sol cruzando el horizonte real → △ **sombras**: "esta sombra la calcula nuestro backend con el relieve láser de NASA y la posición del Sol de SPICE" → cruceta → salto a la mejor ventana Sol + Tierra. |
| 2:40–3:20 | Int. 4 / Int. 1 | **Mission Selection**: cambiar de perfil con la cruceta → la tabla se reordena → □ explica por qué → ✕ informe con fuentes y limitaciones. |
| 3:20–3:50 | Int. 2 | **Rigor**: SPICE validado contra JPL Horizons con 0,0000° de diferencia; marco MOON_ME, el mismo de LOLA. |
| 3:50–4:15 | Int. 3 | **Terreno**: LOLA a 80 m, horizonte a 150 km con curvatura (2,9 km de caída a 100 km). |
| 4:15–4:40 | Int. 1 | **Decisión explicable**: pesos visibles, sin caja negra; todo funciona sin internet con datos precalculados. |
| 4:40–5:00 | Int. 3 | **Cierre**: "LunaScope: explorar el polo sur lunar antes de tocar el suelo." |

Controles para la demo (teclado entre paréntesis): Touchpad = siguiente modo (Tab) · L1/R1 = sitio (Q/E) ·
L2/R2 = zoom o tiempo (Z/C) · ✕ = punto libre / pausa / confirmar (Enter) · □ = panel (I) · △ = sombras (T) ·
cruceta ↑↓ = capa (3/4), ←→ = ventana o perfil (1/2) · ○ = cerrar (Esc) · Options = menú (M).

---

## 16. Preguntas probables del jurado

**¿De dónde sacan los datos? ¿Usan alguna API?**
De ficheros oficiales de NASA descargados una vez: kernels SPICE de NAIF/JPL y el DEM LOLA de NASA Goddard (PGDA). En
la demo no dependemos de ninguna API de datos; JPL Horizons solo lo usamos para validar.

**¿Qué precisión tienen?**
La geometría del Sol y la Tierra coincide con JPL Horizons con 0,0000° de diferencia. El límite real es el relieve:
80 m por píxel.

**¿Por qué no usan IA?**
Porque en una misión crítica hay que poder justificar cada decisión. Nuestro motor pondera métricas medibles con pesos
visibles y explica cada recomendación con los números que la sustentan.

**¿Las sombras son reales o un efecto visual?**
Son un cálculo: el backend barre el relieve LOLA con la dirección del Sol de SPICE. Coinciden con la visibilidad del
gráfico en el 87–100 % de los instantes; la diferencia es suelo frente a antena a +2 m.

**¿Por qué Haworth sale a cero?**
Porque ese punto está en el fondo de un cráter en sombra permanente. Es un resultado correcto, y justo el tipo de
riesgo que la herramienta detecta. *(Si el Integrante 3 lo reubica antes del pitch, actualizad esta respuesta.)*

**¿Ver la Tierra garantiza comunicación?**
No. Es visibilidad geométrica: indica cuándo hay línea de visión directa, no si hay enlace de radio.

**¿Qué harían con más tiempo?**
Más sitios y ventanas de misión configurables; simulador "what-if" con pesos y restricciones ajustables; enlaces de
comunicación con satélites repetidores (Lunar Gateway); DEM de mayor resolución (5–20 m) para pendientes de aterrizaje;
rutas de rover.

---

## 17. Glosario

| Término | Significado |
|---|---|
| **Azimut** | Dirección en el horizonte, desde el norte local en sentido horario (E = 90°) |
| **Elevación** | Ángulo sobre el horizonte plano local |
| **Máscara de horizonte** | Altura angular del relieve en cada una de las 360 direcciones |
| **Libración** | Pequeño balanceo aparente de la Luna: hace que la Tierra oscile unos grados en el cielo lunar |
| **MOON_ME** | Marco de referencia "Mean Earth / Polar Axis" de la Luna; el mismo para SPICE y LOLA |
| **Sombra permanente (PSR)** | Zonas del fondo de cráteres polares donde el Sol nunca llega |
| **Ventana** | Intervalo continuo con Sol y Tierra visibles a la vez |
| **Hipsométrico** | Mapa de alturas con escala de colores (verde bajo, rojo alto) |
| **DEM** | Modelo digital de elevación: mapa de alturas |
