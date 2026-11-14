# LunaScope · Diapositivas de Presentación (Slides)

Estructura de 8 diapositivas diseñada para el pitch ante el jurado (3 a 5 minutos).

---

## Slide 1: Portada
- **Título:** LunaScope
- **Subtítulo:** Centro Interactivo de Planificación Lunar en 3D
- **Frase clave:** *Evaluando sitios de aterrizaje candidatos de Artemis III mediante topografía LOLA, efemérides SPICE y un motor de decisión explicable controlado por mando PS4.*
- **Equipo:** Integrantes 1 (Tech Lead / Backend), 2 (Ciencia / SPICE), 3 (Terreno / Pitch), 4 (Frontend / Cesium).

---

## Slide 2: El Desafío del Polo Sur Lunar
- **Geometría extrema:** El Sol nunca se eleva más de 1.5° a 3° sobre el horizonte local.
- **Microclimas de sombra:** Una elevación modesta a 100 km de distancia proyecta sombras que pueden sumir a un módulo en noches de cientos de horas.
- **La disyuntiva:** Aterrizar no es solo un problema de terreno plano; es un problema espacio-temporal de supervivencia energética y enlace con la Tierra.
- **Visual:** Imagen del polo sur lunar con sombras rasantes (`pitch/img/sitios.png`).

---

## Slide 3: Arquitectura de la Solución
```
[DEM LOLA (NASA)] ──▶ Máscara de horizonte (360°) ──┐
                                                    ▼
[Kernels SPICE]  ──▶ Azimut y elevación Sol/Tierra ──▶ Visibilidad y Ventanas
                                                            │
                                                            ▼
[Mando PS4] ◀──(Gamepad API)──▶ [CesiumJS 3D] ◀──▶ [Motor de Decisión Explicable]
```
- **Principio:** Datos precalculados para rendimiento en vivo y evaluación de puntos libres en segundos.
- **Sin cajas negras:** Reglas de ponderación transparentes donde cada número se rastrea a datos oficiales de NASA.

---

## Slide 4: Demostración en Vivo (Live Demo)
*(Sin contenido proyectado extenso: la pantalla pasa al globo lunar 3D interactivo)*
- Navegación táctil con mandos analógicos (L1/R1, joysticks).
- Exploración temporal continua de 60 días con gatillos de presión (L2/R2).
- Sombras dinámicas y salto automático a ventanas óptimas de misión.
- Cambio de perfiles de ponderación en tiempo real y generación del informe.

---

## Slide 5: Rigor Científico (Terreno y Astronomía)
- **Topografía LOLA:** DEM polar a 80 metros por píxel hasta 150 km de radio.
- **Corrección de curvatura lunar obligatoria:**
  $$\Delta h_{\text{curv}} = \frac{s^2}{2 \cdot R_{\text{luna}}} \quad (2.9\text{ km de caída a } 100\text{ km})$$
- **Horizonte real:** Máscaras angulares de 360° para los sitios candidatos de Artemis III (`pitch/img/horizonte_malapert.png`).
- **Validación:** Discrepancias menores a 0.05° en efemérides astronómicas contrastadas con JPL Horizons.

---

## Slide 6: Resultados y Comparación de Sitios
| Sitio Candidato | Elevación | Pendiente Media | Ventaja Principal | Mejor Perfil |
|---|---|---|---|---|
| **Malapert Massif** | +5126 m | 4.4° (Seguro) | Máxima insolación (>70%) y enlace DTE | **Energía Solar** |
| **Haworth (Crater)** | -3313 m | 4.8° (Seguro) | Acceso directo a depósitos de hielo (PSR) | **Exploración In Situ** |
| **Mons Mouton** | +6413 m | 10.1° (Meseta) | Altitud dominante sobre el relieve polar | **Comunicaciones** |

- El ranking se adapta dinámicamente según las prioridades de la misión.

---

## Slide 7: Explicabilidad y Trabajo Futuro
- **Honestidad científica:** Etiquetado explícito de aproximaciones en pantalla.
- **Siguientes pasos:**
  - Simulación de trayectorias de descenso orbital y combustible.
  - Cálculo de enlaces con repetidores en órbita (Lunar Gateway).
  - Micro-sombras calculadas por GPU a escala de rocas para rovers.

---

## Slide 8: LunaScope Team
- **Integrante 1:** Tech Lead · Arquitectura FastAPI, motor de decisión y scoring.
- **Integrante 2:** Motor Científico · Efemérides SPICE y visibilidad orbital.
- **Integrante 3:** Terreno y Pitch · Procesamiento LOLA, máscaras de horizonte y narrativa.
- **Integrante 4:** Frontend 3D · CesiumJS, visualización espacial y Gamepad API.

*¡Muchas gracias! Preguntas del jurado.*
