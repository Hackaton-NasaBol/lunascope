# LunaScope AI --- Nuevas funcionalidades para el MVP

## Propuesta de ampliación en tres funcionalidades principales

**Contexto:** NASA Space Apps Challenge · 14--15 de noviembre de 2026\
**Objetivo:** diferenciar LunaScope AI de proyectos centrados en
realidad virtual o detección visual, convirtiéndolo en un sistema de
apoyo a decisiones para planificar operaciones lunares.

> **Principio de desarrollo:** priorizar funciones científicamente
> defendibles, demostrables y conectadas al MVP existente. No presentar
> valores simulados como mediciones reales. Toda salida debe indicar
> fuente, unidades, fecha, supuestos y estado de validación.

------------------------------------------------------------------------

# Visión general

LunaScope AI ampliará su MVP con tres funcionalidades:

1.  **Predictive Lunar Environment** --- predecir cómo cambian la
    iluminación, las sombras y la visibilidad del Sol y la Tierra.
2.  **Mission What-If Simulator & AI Optimizer** --- probar escenarios
    de misión y optimizar la selección de sitio y horario según
    objetivos configurables.
3.  **Lunar Digital Twin & Explainable Mission Advisor** --- explorar el
    terreno en 3D y entender, con evidencia, por qué el sistema
    recomienda un sitio.

Las tres funciones reutilizan el núcleo del MVP: tres sitios lunares,
fecha/hora seleccionable, geometría SPICE, DEM LOLA, horizonte local,
ventanas temporales y comparación.

------------------------------------------------------------------------

# 1. Predictive Lunar Environment

## Predicción temporal de iluminación, sombras y visibilidad

### Propósito

Pasar de mostrar las condiciones de un sitio en un instante a calcular
cómo evolucionan durante un intervalo de tiempo. El usuario podrá
seleccionar un sitio y un rango temporal para consultar cuándo tiene
iluminación, cuándo queda oculto el Sol por el relieve y cuándo existe
visibilidad geométrica de la Tierra.

### Capacidades

-   Calcular posiciones aparentes del Sol y la Tierra para una secuencia
    de tiempos usando SPICE.
-   Convertir las posiciones a coordenadas locales del sitio: azimut y
    elevación.
-   Comparar la elevación del Sol con el perfil de horizonte derivado
    del DEM.
-   Estimar intervalos de visibilidad del Sol teniendo en cuenta el
    relieve.
-   Estimar visibilidad geométrica de la Tierra teniendo en cuenta el
    horizonte local.
-   Mostrar una línea temporal con intervalos visibles/no visibles.
-   Mostrar cambios de iluminación y sombras sobre el terreno, si la
    resolución y cobertura del DEM lo permiten.
-   Permitir cambiar fecha, hora, duración del análisis y paso temporal.

### Entradas

-   Identificador y coordenadas del sitio.
-   Fecha/hora inicial y final.
-   Paso temporal de cálculo.
-   Kernels SPICE y configuración de marcos de referencia.
-   DEM LOLA, sistema de coordenadas, resolución y perfil de horizonte.
-   Convenciones de unidades y escala de tiempo.

### Salidas

-   Series temporales de azimut y elevación del Sol y la Tierra.
-   Visibilidad geométrica.
-   Visibilidad condicionada por el horizonte del terreno.
-   Intervalos temporales de iluminación y visibilidad.
-   Metadatos de fuente, resolución, parámetros y estado de validación.

### Interfaz sugerida

-   Selector de sitio y rango temporal.
-   Gráfico temporal del Sol y la Tierra.
-   Banda de tiempo con ventanas visibles y no visibles.
-   Mapa del sitio con el horizonte o las zonas de sombra, si están
    disponibles.
-   Panel de detalles que explique por qué un objeto está oculto:
    elevación por debajo del horizonte local, por ejemplo.

### Implementación técnica

-   **Cálculo orbital y geometría:** SpiceyPy / SPICE.
-   **Procesamiento numérico:** Python, NumPy.
-   **Terreno:** LOLA, Rasterio, GDAL.
-   **API:** FastAPI.
-   **Visualización:** React, TypeScript y biblioteca de gráficos
    existente.
-   **Opcional:** Three.js para representar sombras en el terreno.

### Criterios de aceptación

-   [ ] Para un sitio y una fecha, el sistema devuelve posiciones con
    unidades y marcos de referencia documentados.
-   [ ] La serie temporal contiene muestras para todo el intervalo
    solicitado.
-   [ ] La visibilidad geométrica y la visibilidad condicionada por
    terreno se distinguen claramente.
-   [ ] El gráfico identifica intervalos visibles y no visibles.
-   [ ] Se puede cambiar de sitio y de fecha sin reiniciar la
    aplicación.
-   [ ] Los resultados se pueden reproducir con los mismos kernels,
    datos y parámetros.
-   [ ] Los casos sin datos o con DEM insuficiente se marcan como no
    disponibles, no como visibilidad confirmada.

### Límites científicos que deben comunicarse

-   La visibilidad geométrica de la Tierra no equivale a disponibilidad
    de un enlace de radio.
-   La visibilidad del Sol depende de la calidad del DEM, del perfil de
    horizonte y de la escala espacial analizada.
-   La predicción solo debe cubrir el intervalo temporal para el que las
    fuentes y modelos sean válidos.
-   No afirmar que se modelan sombras subpíxel o iluminación detallada
    si la resolución del terreno no lo permite.

### Responsable principal

**Integrante 2 --- Scientific Engineer**, con apoyo de **Integrante 3
--- Data Engineer** y **Integrante 1 --- Tech Lead**.

### Entregable verificable

Un módulo que genere una serie temporal reproducible para al menos un
sitio, más un gráfico de ventanas de visibilidad consumido por el
frontend.

------------------------------------------------------------------------

# 2. Mission What-If Simulator & AI Optimizer

## Simulador de escenarios y optimización de misiones

### Propósito

Permitir que el usuario cambie los objetivos y restricciones de una
misión y observe cómo cambia la comparación de los tres sitios. El
sistema no debe dar una recomendación fija: debe explicar qué sitio
resulta más conveniente bajo cada conjunto de prioridades.

### Escenarios iniciales

Implementar tres escenarios simples y demostrables:

1.  **Rover solar:** priorizar duración de iluminación y disponibilidad
    energética estimada; penalizar largos periodos de oscuridad y
    terreno no apto.
2.  **Comunicaciones:** priorizar ventanas de visibilidad geométrica de
    la Tierra; considerar el horizonte local como obstrucción.
3.  **Exploración científica:** permitir ponderar accesibilidad del
    terreno, iluminación y otros indicadores científicos disponibles.

Se pueden añadir escenarios de base lunar o exploración de cráteres solo
si existen datos y tiempo suficientes.

### Capacidades

-   Configurar pesos para los criterios de misión.
-   Activar o desactivar restricciones.
-   Definir umbrales, por ejemplo, pendiente máxima admisible.
-   Calcular una puntuación normalizada para cada sitio.
-   Comparar sitios bajo distintos escenarios.
-   Mostrar qué criterios contribuyeron positiva o negativamente al
    resultado.
-   Ejecutar una búsqueda de alternativas con optimización multiobjetivo
    si el tiempo lo permite.
-   Guardar y volver a cargar una configuración de escenario.

### Indicadores candidatos

  -----------------------------------------------------------------------
  Indicador               Uso                     Fuente o cálculo
  ----------------------- ----------------------- -----------------------
  Duración de iluminación Favorecer               Funcionalidad 1
                          disponibilidad solar    

  Duración de ventanas de Favorecer oportunidades Funcionalidad 1
  visibilidad de la       geométricas de          
  Tierra                  comunicación            

  Pendiente del terreno   Penalizar zonas         DEM LOLA
                          difíciles               

  Obstrucción del         Evaluar restricciones   DEM LOLA
  horizonte               locales                 

  Energía solar estimada  Comparar potencial      Iluminación + supuestos
                          energético              del panel

  Confianza de los datos  Evitar recomendaciones  Metadatos y
                          basadas en datos        validaciones
                          débiles                 
  -----------------------------------------------------------------------

**Importante:** la energía estimada no debe presentarse como potencia
real sin especificar eficiencia, orientación, área del panel,
temperatura, degradación y demás supuestos. La visibilidad geométrica
tampoco garantiza un enlace de comunicaciones real.

### Modelo de puntuación inicial

Una primera versión puede utilizar una suma ponderada:

`score = sum(weight_i * normalized_metric_i)`

-   Normalizar cada indicador a una escala común, por ejemplo 0--100.
-   Documentar si un indicador alto es favorable o desfavorable.
-   Aplicar restricciones duras por separado de las preferencias
    ponderadas.
-   Validar que los pesos estén dentro de rangos permitidos y que su
    suma sea coherente.
-   Mostrar el desglose de puntuación, no solo el resultado final.

Para criterios de riesgo, invertir la escala o aplicar una penalización
claramente documentada. No mezclar unidades físicas directamente en una
suma.

### Optimización avanzada opcional

Si la puntuación ponderada ya funciona y queda tiempo, incorporar un
algoritmo multiobjetivo como **NSGA-II** para mostrar alternativas no
dominadas (frente de Pareto). Esto permite visualizar compromisos, por
ejemplo, entre iluminación, pendiente y visibilidad de la Tierra.

No es necesario implementar aprendizaje automático ni entrenar un modelo
con datos inexistentes. Un optimizador matemático transparente es más
defendible que una "IA" sin validación.

### Interfaz sugerida

-   Selector de escenario.
-   Controles deslizantes de pesos.
-   Umbrales de restricciones.
-   Tabla o gráfico comparativo de los tres sitios.
-   Desglose de contribución por criterio.
-   Acción "Recalcular misión".
-   Comparación entre escenario base y escenario modificado.
-   Explicación textual automática basada únicamente en métricas
    calculadas.

### Entradas

-   Métricas calculadas por Predictive Lunar Environment.
-   Métricas del terreno.
-   Escenario y pesos configurados.
-   Restricciones y umbrales.
-   Estado de calidad y disponibilidad de cada dato.

### Salidas

-   Puntuación por sitio.
-   Ranking condicionado al escenario.
-   Desglose de criterios.
-   Restricciones incumplidas.
-   Recomendación y explicación.
-   Si se implementa optimización multiobjetivo: conjunto de
    alternativas y visualización del compromiso entre objetivos.

### Criterios de aceptación

-   [ ] Se pueden comparar los tres sitios con el mismo conjunto de
    métricas.
-   [ ] Cambiar los pesos puede cambiar la puntuación y, cuando
    corresponda, el orden.
-   [ ] El sistema explica qué criterios influyeron en la recomendación.
-   [ ] Las restricciones incumplidas se muestran explícitamente.
-   [ ] Los indicadores faltantes no se convierten silenciosamente en
    cero ni en valores favorables.
-   [ ] Los resultados de prueba están etiquetados como simulados.
-   [ ] La misma entrada produce el mismo resultado.
-   [ ] La recomendación no afirma más de lo que respaldan los datos.

### Responsable principal

**Integrante 5 --- Product & Pitch Lead**, con apoyo de **Integrante 1
--- Tech Lead**. Integrantes 2 y 3 validan los indicadores científicos.

### Entregable verificable

Un módulo funcional que permita seleccionar un escenario, modificar
pesos y restricciones, recalcular los tres sitios y mostrar una
explicación basada en el desglose numérico.

------------------------------------------------------------------------

# 3. Lunar Digital Twin & Explainable Mission Advisor

## Gemelo digital interactivo y recomendaciones explicables

### Propósito

Crear una representación interactiva del terreno lunar que conecte el
mapa, la elevación, el horizonte y las condiciones calculadas. El gemelo
digital debe ayudar a comprender los resultados y no ser solamente un
modelo 3D decorativo.

### Capacidades del gemelo digital

-   Visualizar el DEM como superficie 3D cuando los datos lo permitan.
-   Mostrar los tres sitios candidatos y permitir seleccionarlos.
-   Representar elevación y pendiente mediante capas.
-   Mostrar orientación y elevación del Sol y la Tierra calculadas para
    el instante seleccionado.
-   Representar zonas iluminadas y sombreadas solo cuando el modelo de
    terreno y el método de cálculo lo permitan.
-   Vincular el movimiento temporal con la línea de tiempo de la
    funcionalidad 1.
-   Permitir alternar entre vista 2D y 3D.
-   Mantener una alternativa 2D funcional para equipos con bajo
    rendimiento.

### Explainable Mission Advisor

Añadir un panel que traduzca los resultados del optimizador a
explicaciones claras.

Ejemplos de estructura de explicación:

-   "Este sitio obtiene una puntuación mayor en el escenario Rover solar
    porque presenta más tiempo de iluminación estimado durante el
    intervalo analizado".
-   "Este sitio recibe una penalización por pendiente porque supera el
    umbral configurado".
-   "La comparación de visibilidad de la Tierra no está completa porque
    falta validar el perfil de horizonte".
-   "La recomendación cambia al aumentar la prioridad de
    comunicaciones".

Las explicaciones deben construirse a partir de indicadores y reglas
verificables. No permitir que un modelo de lenguaje invente causas o
resultados.

### Scientific Confidence --- Confianza y trazabilidad

Cada indicador debe mostrar:

-   Fuente del dato.
-   Resolución espacial o temporal, cuando aplique.
-   Fecha o versión de los datos.
-   Unidades.
-   Método de cálculo.
-   Estado: verificado, provisional, simulado o no disponible.
-   Limitaciones conocidas.

La confianza no debe confundirse con exactitud estadística. Si no existe
un modelo de incertidumbre cuantificado, mostrar calidad y estado de los
datos en vez de inventar un porcentaje de confianza.

### Tecnología sugerida

-   **Frontend:** React + TypeScript.
-   **3D:** Three.js o React Three Fiber.
-   **Terreno:** DEM LOLA procesado.
-   **Gráficos:** biblioteca ya utilizada en el MVP.
-   **API:** endpoints del Tech Lead.
-   **Explicaciones:** plantillas y reglas deterministas a partir de los
    resultados del optimizador.

### Interfaz sugerida

-   Panel central con mapa 2D/terreno 3D.
-   Selector de sitio.
-   Selector de fecha y hora.
-   Capas para elevación, pendiente, horizonte e iluminación.
-   Línea de tiempo sincronizada.
-   Panel lateral de recomendación.
-   Desglose de puntuación.
-   Ficha de fuentes y calidad de datos.

### Criterios de aceptación

-   [ ] El usuario puede alternar entre los tres sitios.
-   [ ] La vista 3D utiliza un DEM real identificado o, si usa datos de
    prueba, lo indica claramente.
-   [ ] La selección temporal actualiza las capas que tengan datos
    calculados para ese instante.
-   [ ] La recomendación muestra los indicadores que la sustentan.
-   [ ] Cada indicador importante permite consultar fuente, unidad y
    estado.
-   [ ] La vista 2D sigue disponible si falla la visualización 3D.
-   [ ] Las explicaciones no contienen datos que no existan en la
    respuesta de la API.

### Responsable principal

**Integrante 4 --- Frontend Developer**, con apoyo de **Integrante 5 ---
Product & Pitch Lead**, **Integrante 3 --- Data Engineer** e
**Integrante 1 --- Tech Lead**.

### Entregable verificable

Un dashboard con terreno 2D/3D, selección de sitio y tiempo, capas
disponibles y panel de recomendación explicable con trazabilidad de
datos.

------------------------------------------------------------------------

# Arquitectura e integración

## Flujo general

``` text
SPICE + kernels
      |
      v
Predictive Lunar Environment <----- DEM LOLA
      |                                |
      | series temporales              | elevación, pendiente,
      | visibilidad                    | horizonte
      v                                v
             API / FastAPI
                   |
                   v
       Mission What-If Simulator
          & AI Optimizer
                   |
          puntuación y explicación
                   |
                   v
      Lunar Digital Twin & Advisor
                   |
                   v
       Dashboard React / Three.js
```

## Endpoints propuestos

  --------------------------------------------------------------------------------------
  Método y endpoint                      Función                 Responsable
  -------------------------------------- ----------------------- -----------------------
  `GET /api/sites`                       Listar los tres sitios  Integrante 1

  `GET /api/environment/timeseries`      Obtener series          Integrantes 1 y 2
                                         temporales              

  `GET /api/terrain/{site_id}`           Obtener datos           Integrantes 1 y 3
                                         topográficos            

  `POST /api/scenarios/evaluate`         Evaluar un escenario y  Integrantes 1 y 5
                                         sus pesos               

  `GET /api/recommendations/{site_id}`   Obtener explicación y   Integrantes 1 y 5
                                         trazabilidad            

  `GET /api/data-quality/{site_id}`      Consultar fuentes y     Integrantes 1, 3 y 5
                                         estado de datos         
  --------------------------------------------------------------------------------------

Los nombres y esquemas definitivos deben acordarse antes de integrar.
Mantener un contrato JSON compartido, con unidades y estados explícitos.

## Contrato mínimo de respuesta

``` json
{
  "site_id": "site_a",
  "time_utc": "2026-11-15T00:00:00Z",
  "environment": {
    "sun_azimuth_deg": null,
    "sun_elevation_deg": null,
    "sun_terrain_visible": null,
    "earth_azimuth_deg": null,
    "earth_elevation_deg": null,
    "earth_terrain_visible": null
  },
  "terrain": {
    "elevation_m": null,
    "slope_deg": null,
    "horizon_profile_status": "pending"
  },
  "data_quality": {
    "source": "pending",
    "status": "not_verified",
    "limitations": []
  }
}
```

Los valores `null` son marcadores de datos aún no disponibles, no
resultados científicos.

------------------------------------------------------------------------

# Plan de ejecución para el hackathon

## Orden de prioridad

  -----------------------------------------------------------------------
  Prioridad         Trabajo           Responsable       Entregable
  ----------------- ----------------- ----------------- -----------------
  P0                Acordar contratos 1 + 2 + 3 + 5     Esquemas API y
                    y métricas                          diccionario de
                                                        indicadores

  P0                Calcular una      2                 Resultado SPICE
                    serie temporal                      reproducible
                    para un sitio                       

  P0                Obtener terreno y 3                 Perfil
                    horizonte de                        topográfico
                    prueba                              validado

  P1                Integrar ventanas 1 + 2 + 4         Gráfico temporal
                    temporales en API                   conectado
                    y frontend                          

  P1                Implementar       5 + 1             Comparador
                    scoring                             funcional
                    configurable y                      
                    escenarios                          

  P1                Añadir            5                 Recomendación
                    explicaciones                       justificable
                    basadas en                          
                    métricas                            

  P2                Visualización 3D  4 + 3             Gemelo digital
                    del DEM                             básico

  P2                Optimización      5 + 1             Alternativas
                    multiobjetivo                       Pareto, si hay
                                                        tiempo

  P2                Pulir controles y 4 + 5             Demo integrada
                    presentación                        
  -----------------------------------------------------------------------

## Reparto por integrante

### 1. Tech Lead

-   Cerrar contratos API y modelos de datos.
-   Integrar SPICE y DEM mediante servicios separados.
-   Implementar endpoints de series temporales y evaluación de
    escenarios.
-   Preparar ejecución local y despliegue.
-   Mantener una versión estable para la demo.

### 2. Scientific Engineer

-   Validar kernels y marcos SPICE.
-   Calcular posiciones del Sol y la Tierra.
-   Generar series temporales.
-   Definir la conversión a coordenadas locales.
-   Documentar supuestos y limitaciones geométricas.

### 3. Data Engineer

-   Preparar DEM LOLA.
-   Verificar proyección, resolución y unidades.
-   Calcular pendiente y perfil de horizonte.
-   Proporcionar capas y metadatos al frontend.
-   Identificar limitaciones de cobertura.

### 4. Frontend Developer

-   Integrar gráficos temporales.
-   Construir controles de escenarios.
-   Implementar mapa y gemelo digital 3D básico.
-   Mostrar explicaciones y calidad de datos.
-   Mantener vista 2D y navegación con mouse/teclado como respaldo.

### 5. Product & Pitch Lead

-   Definir escenarios y criterios de misión.
-   Implementar scoring y pesos configurables.
-   Desarrollar explicación basada en indicadores.
-   Diseñar el flujo What-If.
-   Validar que las recomendaciones sean comprensibles.
-   Preparar demo y pitch con resultados reales o claramente etiquetados
    como simulados.

------------------------------------------------------------------------

# Pruebas de integración y validación

-   [ ] Los tres sitios usan el mismo contrato y unidades.
-   [ ] Las posiciones SPICE se pueden reproducir con los mismos kernels
    y parámetros.
-   [ ] La elevación y pendiente del DEM se consultan en las coordenadas
    correctas.
-   [ ] El horizonte local se calcula con una convención documentada.
-   [ ] La visibilidad geométrica se diferencia de la visibilidad
    condicionada por terreno.
-   [ ] Las ventanas temporales coinciden entre API, gráfico y vista 3D.
-   [ ] Cambiar el escenario recalcula el scoring.
-   [ ] Los indicadores faltantes se marcan como no disponibles.
-   [ ] Las explicaciones coinciden con el desglose de puntuación.
-   [ ] El dashboard funciona sin conexión a servicios externos durante
    la demo, usando datos guardados y etiquetados.
-   [ ] Existe un recorrido de demo grabado y una alternativa 2D si
    falla la vista 3D.

------------------------------------------------------------------------

# Demo de respaldo

Preparar un conjunto pequeño y local de datos para los tres sitios:

-   Coordenadas y metadatos de cada sitio.
-   Una serie temporal calculada y validada, si está disponible.
-   Datos de terreno y perfil de horizonte, si están disponibles.
-   Una configuración de escenario.
-   Resultados de scoring reproducibles.
-   Capturas o video del recorrido completo.

Si algún resultado todavía no está validado, etiquetarlo como
**simulado**, **provisional** o **no disponible**. No presentar datos
ficticios como observaciones o cálculos científicos reales.

------------------------------------------------------------------------

# Definición de éxito

La ampliación estará demostrada cuando el jurado pueda:

1.  Seleccionar uno de los tres sitios y un intervalo temporal.
2.  Observar cómo cambian la iluminación y la visibilidad del Sol y la
    Tierra.
3.  Consultar las limitaciones topográficas disponibles.
4.  Elegir un escenario de misión y modificar prioridades.
5.  Recalcular la comparación de los tres sitios.
6.  Entender por qué cambia la recomendación.
7.  Inspeccionar el terreno y consultar la procedencia y el estado de
    los datos.

## Mensaje central del proyecto

**LunaScope AI no se limita a visualizar la Luna: ayuda a anticipar
condiciones, comparar escenarios y justificar decisiones para planificar
operaciones lunares.**

La innovación está en la integración verificable de geometría espacial,
datos topográficos, predicción temporal, optimización multiobjetivo y
visualización explicable; no en añadir IA o 3D sin una función concreta.
