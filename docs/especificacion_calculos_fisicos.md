# Especificación de los cálculos físicos de LunaScope

> **Para quién:** un agente o desarrollador que tiene que **reproducir, verificar o ampliar** los cálculos de
> visibilidad del Sol y de la Tierra del proyecto LunaScope, sin conocer el resto del proyecto.
> Todo lo necesario está en este documento. Las rutas son relativas a la raíz del repositorio.

---

## 0. Resumen de la tarea

Para un punto de la superficie del **polo sur de la Luna** y un intervalo de tiempo, calcular hora a hora:

1. El **azimut y la elevación** del Sol y de la Tierra vistos desde ese punto (efemérides SPICE de NASA).
2. La **altura del horizonte** en esa dirección (relieve del DEM LOLA de NASA).
3. Si el Sol y la Tierra **se ven** (por encima del relieve) y qué fracción de su disco se ve.
4. Un **resumen**: % del tiempo con Sol, con Tierra, con ambos; noche más larga; y las **ventanas** (intervalos
   continuos con Sol y Tierra a la vez).

**No se usa machine learning ni ningún modelo estadístico.** Es geometría determinista: la "predicción" del futuro
viene de las efemérides DE440 de JPL, que ya modelan el movimiento del sistema solar (integración numérica ajustada a
décadas de observaciones). Mismas entradas → mismo resultado, bit a bit.

---

## 1. Datos de entrada

### 1.1 Kernels SPICE (NASA NAIF / JPL)

Carpeta `data/` (o `kernels/`, enlace a `data/`; o la ruta de la variable de entorno `LUNASCOPE_KERNELS_DIR`).
Descarga: `python backend/scripts/download_kernels.py` desde https://naif.jpl.nasa.gov/pub/naif/generic_kernels/

| Tipo | Archivo | Contenido | Carpeta en NAIF |
|---|---|---|---|
| LSK | `naif0012.tls` | Segundos intercalares (UTC ↔ ET/TDB) | `lsk/` |
| PCK (texto) | `pck00011.tpc` | Constantes y radios de los cuerpos | `pck/` |
| PCK (binario) | `moon_pa_de440_200625.bpc` | Orientación de la Luna en el tiempo (incluye libración), marco `MOON_PA` | `pck/` |
| FK | `moon_de440_250416.tf` | Define el marco **`MOON_ME`** (Mean Earth / Polar Axis) a partir de `MOON_PA` | `fk/satellites/` |
| SPK | `de440s.bsp` | Efemérides DE440 del Sol, la Tierra, la Luna y los planetas, 1849-12-25 → 2150-01-21 | `spk/planets/` |

Orden de carga: **tiempo → constantes → orientación → marcos → efemérides** (el orden de la tabla).
Implementación de referencia: `backend/lunascope/science/kernels.py`.

### 1.2 DEM LOLA (NASA Goddard, PGDA producto 90)

- Archivo: `dem/LDEM_80S_80MPP_ADJ.TIF` (~190 MB). Descarga: `python backend/scripts/download_dem.py`
  (https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF).
- GeoTIFF en **proyección polar estereográfica sur**, 7600 × 7600 píxeles, **80 m/píxel**, cubre de 80°S al polo.
- Valores: **altura en metros sobre una esfera de radio R = 1 737 400 m**. NoData → NaN.
- Lectura: Rasterio. Conversión lat/lon ↔ x/y del DEM: pyproj, con el CRS geográfico lunar
  `+proj=longlat +R=1737400 +no_defs` (en pyproj, orden **lon, lat**).
- Implementación de referencia: `backend/lunascope/terrain/dem.py`.

### 1.3 Sitios

`backend/data/sites.json`:

| id | lat (°) | lon (° E) | elevación DEM (m) |
|---|---|---|---|
| `malapert` | −85,99 | 2,93 | 5126,6 |
| `haworth` | −87,45 | −5,10 | −3313,0 |
| `mons_mouton_plateau` | −85,40 | 31,50 | 6413,0 |

### 1.4 Ventana de la misión

- Inicio `2027-09-01T00:00:00Z`, duración **60 días** → fin `2027-10-31T00:00:00Z`.
- Paso **1 h** → **1441 muestras** (ambos extremos incluidos: `n = floor((fin − inicio) / paso) + 1`).
- Configurable con `LUNASCOPE_MISSION_START` y `LUNASCOPE_MISSION_DAYS` (`backend/app/config.py`).

---

## 2. Convenciones (obligatorias)

| Magnitud | Convención |
|---|---|
| Tiempo | UTC, ISO 8601 con `Z` (p. ej. `2027-09-01T00:00:00Z`) |
| Latitud | grados, −90 a +90 (sur negativo) |
| Longitud | grados **este**, −180 a +180 |
| Azimut | grados desde el **norte local**, sentido **horario**: N = 0, E = 90, S = 180, O = 270; rango [0, 360) |
| Elevación | grados sobre el **plano horizontal local** (perpendicular al radio lunar en el sitio) |
| Alturas | metros sobre la esfera de **1 737 400 m** |
| Marco | **`MOON_ME`** (el mismo que LOLA). No usar `IAU_MOON`: difiere del orden de cientos de metros en superficie |
| Observador | **+2 m** sobre el terreno (antena del módulo) |
| Radio angular | Sol **0,267°**, Tierra **0,95°** |
| Umbral de visible | fracción del disco ≥ **0,5** |

**Cuidado cerca del polo:** "norte" es la dirección que **se aleja del polo** (hacia el ecuador), sea cual sea el
lado. En el mapa polar estereográfico el norte no es "arriba": hay que calcularlo en cada sitio (ver 3.3 y 4.1).

---

## 3. Geometría del Sol y de la Tierra (SPICE)

Implementación de referencia: `backend/lunascope/science/geometry.py` y `timeseries.py` (librería **SpiceyPy**).

### 3.1 Tiempos

```python
et0 = spice.str2et("2027-09-01 00:00:00 UTC")        # segundos TDB desde J2000
ets = et0 + 3600.0 * step_h * np.arange(n)           # ET es lineal: no hace falta str2et en bucle
```

### 3.2 Posición del observador en MOON_ME (km)

```
h_total_m = elevación_DEM_m + 2.0                    # terreno + antena
r_km      = 1737.4 + h_total_m / 1000
site      = spice.latrec(r_km, radians(lon), radians(lat))   # vector (x, y, z) en km
```

Rechazar puntos con |lat| > 89,99° (la base local no está definida en el polo exacto).

### 3.3 Base local Este–Norte–Arriba (Luna como esfera)

```
up    = site / |site|
east  = normalize( ẑ × up )          con ẑ = (0, 0, 1)
north = up × east
```

### 3.4 Posición aparente del objetivo

```python
pos, _ = spice.spkpos(target, ets, "MOON_ME", "LT+S", "MOON")   # target = "SUN" o "EARTH"; (N, 3) km
v = pos - site                                                   # vector sitio → objetivo
```

- `LT+S` = corrección por tiempo de luz + aberración estelar. Se aplica **desde el centro de la Luna**, no desde el
  sitio; el error que introduce es < 0,01° (despreciable).
- Observador `"MOON"` (centro). Se resta `site` para pasar al sitio.

### 3.5 Azimut y elevación

```
v̂   = v / |v|
el  = degrees( asin( v̂ · up ) )
az  = degrees( atan2( v̂ · east, v̂ · north ) ) mod 360
```

---

## 4. Máscara de horizonte (DEM LOLA)

Implementación de referencia: `backend/lunascope/terrain/horizon.py`. Es **fija** (no depende del tiempo); se calcula
una vez por sitio y se guarda en `backend/data/precomputed/<sitio>/horizon.json`.

### 4.1 Ejes locales en el plano del DEM

```
(x0, y0) = proyectar(lat, lon)
north    = normalize( proyectar(lat + 0.001, lon) − (x0, y0) )
east     = normalize( proyectar(lat, lon + 0.001) − (x0, y0) )
```

### 4.2 Para cada azimut a (0°, 1°, …, 359°; modo "fast": paso 2°)

```
d      = north · cos(a) + east · sin(a)                    # dirección en el plano del DEM
s      = distancias: cada 1 px (80 m) hasta 5 km, cada 2 px hasta 30 km, cada 4 px hasta 150 km
z(s)   = DEM muestreado con interpolación bilineal en (x0, y0) + s · d
z0     = DEM(x0, y0) + 2 m
ángulo = degrees( atan2( z(s) − z0 − s² / (2R), s ) )      # R = 1 737 400 m
horizonte[a] = clip( max(ángulo ignorando NaN), −5°, 15° )
```

- `s² / (2R)` es la **caída por curvatura lunar**: a 100 km ≈ 2,9 km. **Es obligatoria**: sin ella todo el horizonte
  sale demasiado alto.
- Alcance: 150 km en modo "full" (sitios fijos), 50 km en "fast" (puntos libres).
- El recorte a [−5°, 15°] **sí actúa** en Mons Mouton Plateau (4 azimuts en −5,00°). Documentarlo si se cambia.

### 4.3 Interpolación del horizonte en un azimut cualquiera

Lineal y **circular** (359° y 0° son vecinos):

```
x   = (az mod 360) / paso_az
i0  = floor(x) mod N ;  i1 = (i0 + 1) mod N ;  f = x − floor(x)
h(az) = H[i0] · (1 − f) + H[i1] · f
```

---

## 5. Visibilidad y resumen

Implementación de referencia: `backend/lunascope/science/visibility.py`.

### 5.1 Fracción visible del disco (aproximación lineal)

```
vf = clip( (el − h(az) + r) / (2r), 0, 1 )        r = 0,267° (Sol) o 0,95° (Tierra)
visible = vf ≥ 0,5                                 (equivale a: centro del disco por encima del horizonte)
```

### 5.2 Resumen

| Campo | Definición |
|---|---|
| `sun_visible_pct` | 100 × (muestras con Sol visible) / n, redondeado a 0,1 |
| `earth_visible_pct` | ídem con la Tierra |
| `both_visible_pct` | ídem con Sol **y** Tierra a la vez |
| `longest_dark_h` | longitud de la racha más larga de muestras **sin** Sol visible × paso_h |
| `longest_no_earth_h` | ídem sin Tierra |
| `windows` | rachas con Sol **y** Tierra, de más larga a más corta (desempate: la más temprana), **máximo 10**. Cada una: `start` = hora de la primera muestra, `end` = hora de la última, `hours = (índice_fin − índice_inicio) × paso_h` |

Ojo con la diferencia: una racha de *k* muestras cuenta *k × paso* horas en `longest_dark_h`, pero
*(k − 1) × paso* horas en `windows[].hours` (= `end − start`). Es la convención del contrato; mantenerla.

---

## 6. Formato de salida

`backend/data/precomputed/<sitio>/timeseries.json` (contrato completo en `docs/contract.md`):

```json
{
  "site_id": "malapert",
  "start": "2027-09-01T00:00:00Z",
  "end": "2027-10-31T00:00:00Z",
  "step_hours": 1.0,
  "samples": [
    {"t": "2027-09-01T00:00:00Z",
     "sun":   {"az": 176.195, "el": -3.276, "horizon_el": 1.001, "visible_fraction": 0.0},
     "earth": {"az": 359.831, "el": 0.241, "horizon_el": -3.761, "visible_fraction": 1.0}}
  ],
  "summary": {"sun_visible_pct": 51.6, "earth_visible_pct": 100.0, "both_visible_pct": 51.6,
              "longest_dark_h": 328.0, "longest_no_earth_h": 0.0,
              "windows": [{"start": "2027-10-04T10:00:00Z", "end": "2027-10-20T10:00:00Z", "hours": 384.0}]},
  "source": "real",
  "horizon": "mask"
}
```

Valores de muestra redondeados a **3 decimales**. JSON en `snake_case`.

---

## 7. Valores de referencia para comprobar

Con los kernels de la sección 1.1, el DEM de 1.2 y la ventana de 1.4, una implementación correcta debe reproducir
**exactamente** (a 3 decimales) los ficheros actuales:

| Sitio | Muestra | Sol (az, el, horizonte, vf) | Tierra (az, el, horizonte, vf) |
|---|---|---|---|
| malapert | `2027-09-01T00:00:00Z` | 176,195 · −3,276 · 1,001 · 0,0 | 359,831 · 0,241 · −3,761 · 1,0 |
| malapert | `2027-09-11T00:00:00Z` | 54,141 · 3,323 · −1,459 · 1,0 | 359,841 · 1,786 · −3,760 · 1,0 |
| mons_mouton_plateau | `2027-09-01T00:00:00Z` | 147,579 · −3,159 · 2,610 · 0,0 | 331,317 · 0,266 · −2,920 · 1,0 |
| haworth | `2027-09-01T00:00:00Z` | 184,233 · −1,818 · 5,593 · 0,0 | 7,847 · −1,241 · 9,713 · 0,0 |

Horizonte en azimuts 0/90/180/270°:
malapert −3,743 / 0,004 / 1,156 / 4,450 · mons_mouton_plateau −0,374 / 8,299 / −2,708 / −4,336 ·
haworth 9,840 / 4,656 / 5,353 / 7,944.

| Sitio | Sol % | Tierra % | Ambos % | Noche más larga | Mejor ventana |
|---|---|---|---|---|---|
| malapert | 51,6 | 100,0 | 51,6 | 328 h | 2027-10-04T10Z → 2027-10-20T10Z, 384 h |
| mons_mouton_plateau | 52,0 | 100,0 | 52,0 | 336 h | 2027-10-09T15Z → 2027-10-25T13Z, 382 h |
| haworth | 0,0 | 0,0 | 0,0 | 1441 h | ninguna (fondo de cráter en sombra permanente) |

### Validación externa (JPL Horizons)

La geometría pura (sin horizonte) se valida contra la API de JPL Horizons (`https://ssd.jpl.nasa.gov/api/horizons.api`,
observador `coord@301`, cantidad 4 = azimut/elevación aparentes, **sin refracción**):
`python backend/scripts/validate_horizons.py --site <id> --lat … --lon … --height-m … --days 60 --step-h 12`.

Resultado actual: **726 comparaciones** (3 sitios × 60 días cada 12 h × Sol y Tierra), diferencia máxima
**< 0,0001°**. Es lo esperado: Horizons usa el mismo modelo (DE440 + orientación lunar DE440). Lo que valida es que las
convenciones (marco, signo de la longitud, azimut, altura, unidades) son correctas. **Tolerancia de aceptación: 0,1°.**

### Pruebas

`cd backend && pytest` (las de ciencia se saltan sin kernels; las de terreno, sin DEM). Comprobaciones de cordura:

- Elevación del Sol siempre dentro de ±(90° − |lat| + 1,6°) (p. ej. 86°S → ±5,6°).
- El Sol da una vuelta completa de azimut en ~29,5 días; la Tierra oscila unos pocos grados (libración), sin dar vueltas.
- Con longitud ≈ 0°, la Tierra aparece cerca del azimut 0° (norte) y a pocos grados de elevación.
- Horizonte: 360 valores en [−5°, 15°]. Muestras horarias consecutivas.

---

## 8. Errores típicos (y cómo se manifiestan)

| Error | Síntoma |
|---|---|
| Usar `IAU_MOON` en vez de `MOON_ME` | Horizonte y Sol desfasados; diferencias de décimas de grado con Horizons |
| Longitud oeste positiva | Azimuts reflejados; validación con Horizons falla por grados |
| Azimut antihorario o desde el este | La máscara aparece girada 90° o reflejada respecto al Sol |
| Mezclar km y m en la altura | Elevaciones con errores de varios grados |
| Olvidar la curvatura `s²/2R` | Horizontes demasiado altos; casi todo en sombra |
| Interpolación de horizonte no circular | Salto entre 359° y 0° |
| `str2et` sin "UTC" o con hora local | Desfase de horas en toda la serie |
| Orden pyproj (lat, lon) en vez de (lon, lat) | Puntos fuera del DEM o en lugares erróneos |
| Contar `windows.hours` como *k × paso* | Ventanas 1 h más largas que la referencia |

---

## 9. Ampliaciones posibles (si se piden)

- **Otras fechas o duraciones**: cambiar `LUNASCOPE_MISSION_START` / `_DAYS` y ejecutar
  `python backend/scripts/precompute.py` (necesita kernels **y** DEM; si falta uno, conserva los JSON reales existentes).
- **Fracción de disco exacta**: sustituir la aproximación lineal por el área visible de un círculo cortado por una
  recta (segmento circular): `A(d)/πr²` con `d = el − h(az)`.
- **Refracción**: no aplica (la Luna no tiene atmósfera).
- **Paralaje solar dentro de la ventana de sombras**: hoy las sombras usan la misma dirección del Sol en ±60 km con
  corrección de elevación por curvatura (`backend/lunascope/terrain/illumination.py`); a 60 km el error es < 0,01°.
- **Energía solar estimada**: requiere fijar supuestos (área, eficiencia, orientación del panel); no presentarla como
  potencia real sin ellos.

---

## 10. Mapa del código

| Paso | Archivo |
|---|---|
| Carga de kernels | `backend/lunascope/science/kernels.py` |
| Geometría (latrec, spkpos, ENU, az/el) | `backend/lunascope/science/geometry.py` |
| Serie temporal (`compute_timeseries`) | `backend/lunascope/science/timeseries.py` |
| Visibilidad, rachas, ventanas | `backend/lunascope/science/visibility.py` |
| DEM y ejes locales | `backend/lunascope/terrain/dem.py` |
| Máscara de horizonte | `backend/lunascope/terrain/horizon.py` |
| Pendientes del sitio | `backend/lunascope/terrain/stats.py` |
| Sombras del relieve | `backend/lunascope/terrain/illumination.py` |
| Orquestación y respaldo sin kernels/DEM | `backend/lunascope/pipeline.py` |
| Generación de los JSON | `backend/scripts/precompute.py` |
| Validación con JPL Horizons | `backend/scripts/validate_horizons.py` |
| Contrato de datos | `docs/contract.md` |
