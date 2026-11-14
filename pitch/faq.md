# LunaScope · Preguntas Frecuentes del Jurado (FAQ)

Respuestas breves y precisas (1 a 2 frases) asignadas al integrante especialista.

---

### 1. ¿Por qué no utilizan un modelo de Inteligencia Artificial / Red Neuronal para la recomendación?
**Responde: Integrante 1 (Tech Lead)**  
> *"En la planificación de misiones espaciales críticas, la explicabilidad es un requisito innegociable. LunaScope utiliza un motor de decisión determinista basado en reglas científicas y ponderaciones explícitas, donde cada puntuación puede rastrearse numéricamente hasta las mediciones de los sensores de NASA."*

---

### 2. ¿Qué tan confiables y precisos son los cálculos astronómicos?
**Responde: Integrante 2 (Motor Científico)**  
> *"Utilizamos el toolkit SPICE de NASA NAIF con efemérides de alta precisión del sistema solar y librationes de la Luna. Nuestros resultados han sido contrastados directamente contra el sistema NASA JPL Horizons, garantizando discrepancias menores a 0.05 grados en azimut y elevación."*

---

### 3. ¿Cómo seleccionaron las coordenadas exactas de estos 3 sitios?
**Responde: Integrante 3 (Terreno)**  
> *"Las 9 regiones anunciadas por NASA para Artemis III abarcan cientos de kilómetros cuadrados; nosotros analizamos los modelos digitales de elevación LOLA para ubicar crestas y altiplanicies prominentes que combinan pendientes de aterrizaje inferiores al umbral seguro de 8 grados con la máxima elevación relativa para despejar el horizonte."*

---

### 4. ¿Qué resolución espacial tienen los modelos de terreno y cómo impacta en las sombras?
**Responde: Integrante 3 (Terreno)**  
> *"El cálculo del horizonte lejano utiliza un DEM polar de LOLA a 80 metros por píxel hasta 150 km de distancia con corrección estricta de curvatura esférica lunar ($s^2 / 2R$). Para la evaluación local de pendiente y riesgo de aterrizaje dentro de un radio de 100 m, se utilizan sub-ventanas de alta resolución."*

---

### 5. ¿Por qué utilizaron un mando de PlayStation 4 en lugar de un mouse estándar?
**Responde: Integrante 4 (Frontend)**  
> *"La planificación lunar involucra navegar de forma multidimensional en espacio (órbita 3D) y en tiempo (60 días continuos). Los joysticks dobles y los gatillos analógicos sensibles a la presión permiten un control analógico de la velocidad temporal y de la perspectiva visual mucho más orgánico y directo que controles tradicionales de pantalla."*

---

### 6. ¿Qué capacidades añadirían con dos semanas adicionales de desarrollo?
**Responde: Integrante 3 o Integrante 1**  
> *"Integraríamos simulación dinámica de trayectorias de descenso orbital, cálculo de iluminación pixel por pixel en GPU para micro-sombras en rocas, y soporte para el cálculo de enlace de comunicaciones con la futura estación lunar Lunar Gateway."*
