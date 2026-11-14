# LunaScope

Centro interactivo de planificación lunar en 3D: compara sitios de aterrizaje en el polo sur de la Luna con datos de NASA (SPICE + LOLA) y se controla con un mando PS4.

## Documentación del equipo

| Integrante | Rol | Documento |
|---|---|---|
| 1 | Backend + motor de decisión (Tech Lead) | [docs/integrantes/LunaScope_Integrante1_Backend.md](docs/integrantes/LunaScope_Integrante1_Backend.md) |
| 2 | Motor científico (SPICE) | [docs/integrantes/LunaScope_Integrante2_Ciencia.md](docs/integrantes/LunaScope_Integrante2_Ciencia.md) |
| 3 | Terreno LOLA + presentación | [docs/integrantes/LunaScope_Integrante3_Terreno_Pitch.md](docs/integrantes/LunaScope_Integrante3_Terreno_Pitch.md) |
| 4 | Frontend 3D + mando PS4 | [docs/integrantes/LunaScope_Integrante4_Frontend.md](docs/integrantes/LunaScope_Integrante4_Frontend.md) |

El contrato de datos y las convenciones comunes están en [docs/contract.md](docs/contract.md). Cualquier cambio lo aprueba el Integrante 1.

## Estructura

```
backend/    API FastAPI + science/ (Int. 2) + terrain/ (Int. 3) + scoring/ (Int. 1)
frontend/   React + TypeScript + CesiumJS (Int. 4)
pitch/      Guion, slides y video (Int. 3)
docs/       Contrato y documentos por integrante
```

## Ramas

`main` siempre funciona. Cada integrante trabaja en su rama y fusiona por PR:
`feat/backend`, `feat/science`, `feat/terrain`, `feat/frontend`.

## Arranque

Las instrucciones de instalación se completarán durante el hackathon (Integrante 1).
