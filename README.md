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

### Backend (Python 3.11+)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000/api` · Documentación viva: `http://localhost:8000/docs`
- Los JSON precalculados de los 3 sitios están en git, así que la API funciona **sin kernels ni DEM** (y sin internet).
- Mientras `science/` y `terrain/` no estén listos, los datos son **mocks** con la forma exacta del contrato y llevan `"source": "mock"`.

### Regenerar los datos de los 3 sitios

```bash
cd backend
python scripts/precompute.py --start 2027-09-01T00:00:00Z --days 60
python scripts/precompute.py --site malapert   # solo un sitio
python scripts/precompute.py --mock            # fuerza mocks
```

Usa `lunascope.terrain` y `lunascope.science` si existen; si no, cae a mocks y lo avisa. Valida la salida con los modelos Pydantic antes de escribir.
La ventana de la misión se puede cambiar con `LUNASCOPE_MISSION_START` y `LUNASCOPE_MISSION_DAYS`.

### Pruebas

```bash
cd backend
pytest                          # puntuación + API
python scripts/demo_check.py    # con el servidor arrancado: llama a todos los endpoints
```

### Frontend (Node 20+)

```bash
cd frontend
npm install
cp .env.example .env.local     # VITE_CESIUM_TOKEN=... (token de Cesium ion, no se sube)
npm run dev                    # http://localhost:5173
```

Funciona sin backend (datos de demostración) y sin token (globo liso). Controles y detalles en [frontend/README.md](frontend/README.md).

### Kernels SPICE y DEM LOLA

Pendiente de los Integrantes 2 y 3 (`kernels/` y `dem/` en la raíz del repo, fuera de git).
