# LunaScope · Guion del Pitch (3 a 5 minutos)

> **Regla de oro:** El Integrante 3 conduce la narrativa, el Integrante 4 opera el mando en sincronía exacta, el Integrante 2 interviene en la validación científica y el Integrante 1 en la arquitectura del motor de decisión.

---

## Estructura por Tiempos

### 1. El Problema (0:00 – 0:30) · *Voz: Integrante 3*
- **Apertura:** *"En el polo sur de la Luna, el Sol nunca sube más de 2 o 3 grados sobre el horizonte. Una colina a 100 kilómetros de distancia puede proyectar una sombra de días, sumiendo a un módulo de alunizaje en temperaturas de doscientos grados bajo cero y dejándolo sin energía solar."*
- **Desafío:** *"Artemis III no solo debe decidir **dónde** aterrizar, sino **cuándo**. Un sitio seguro a nivel de terreno puede ser inviable si pierde comunicación con la Tierra durante una fase crítica."*

### 2. La Solución (0:30 – 1:00) · *Voz: Integrante 3*
- **Definición:** *"Para resolver esto creamos **LunaScope**: un centro interactivo de planificación lunar en 3D que cruza modelos de elevación de NASA (LOLA) con efemérides astronómicas de alta precisión (SPICE) para comparar sitios de aterrizaje candidatos y recomendar la mejor opción según el perfil de la misión."*
- **Diferenciador:** *"Toda la exploración temporal y espacial se controla de manera táctil con un mando PS4, permitiendo una experiencia fluida e inmersiva sobre datos científicos reales."*

### 3. Demostración en Vivo con Mando (1:00 – 3:00) · *Voz: Int. 3 / Mando: Int. 4*
*(Seguir la secuencia descrita en `pitch/demo.md`)*
- Modo **Explore**: Inspección del globo lunar 3D en Cesium, navegación entre Malapert Massif, Haworth y Mons Mouton Plateau. Apertura del panel de datos topográficos.
- Modo **Mission Time**: El gatillo R2 acelera el tiempo 60 días. Se observa la rotación del Sol, sombras dinámicas y la oscilación de la Tierra. El salto de ventanas ubica el momento óptimo con Sol y Tierra simultáneos.
- Modo **Mission Selection**: Cambio de perfiles de misión con la cruceta (Energía solar vs. Comunicaciones vs. Seguridad). Se demuestra cómo el ranking se reordena de forma transparente.
- Confirmación con el botón **X** y generación del informe final de misión.

### 4. Rigor Científico (3:00 – 3:45) · *Voz: Integrante 2 y 3*
- **Terreno (Int. 3):** *"Procesamos el DEM polar de NASA LOLA a 80 metros por píxel. Para cada sitio generamos una máscara de horizonte de 360 grados considerando rigurosamente la curvatura lunar: a 100 km, el terreno cae 2.9 km por la geometría de la esfera."*
- **Efemérides (Int. 2):** *"Con kernels SPICE calculamos la posición exacta del Sol y de la Tierra a lo largo de una ventana de 60 días, cruzando cada ángulo contra la máscara de horizonte para medir fracciones visibles de disco."*

### 5. Arquitectura y Explicabilidad (3:45 – 4:15) · *Voz: Integrante 1*
- **Precálculo:** *"El backend en FastAPI sirve datos precalculados de alta velocidad y permite evaluar puntos libres en segundos."*
- **Decisión transparente:** *"No usamos modelos de caja negra. El motor de decisión pondera métricas claras y cuantificables: horas de luz, visibilidad continua de la Tierra, noche más larga y rugosidad topográfica, explicando siempre el porqué de cada recomendación."*

### 6. Cierre y Siguientes Pasos (4:15 – 4:45) · *Voz: Integrante 3*
- **Impacto:** *"LunaScope demuestra que los datos científicos de exploración espacial pueden ser accesibles, interactivos y rigurosos al mismo tiempo."*
- **Futuro:** *"Con más tiempo integraríamos simulación de trayectorias de descenso, enlaces con satélites repetidores en órbita lunar y soporte para análisis de rutas de rovers."*
- **Lema final:** *"LunaScope: explorando el polo sur lunar antes de tocar el suelo."*
