"""LunaScope API. Arranque (desde backend/): uvicorn app.main:app --reload --port 8000"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config, errors
from app.models import Health
from app.routers import point, report, score, sites
from app.store import store
from lunascope import pipeline

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.load_all()  # sites.json + precomputed/* a memoria
    store.kernels_loaded = pipeline.kernels_loaded()
    yield


app = FastAPI(title="LunaScope API", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
errors.install(app)


@app.get("/api/health", response_model=Health, tags=["health"])
def health():
    return {"status": "ok", "kernels_loaded": store.kernels_loaded, "sites": len(store.sites)}


for r in (sites.router, score.router, point.router, report.router):
    app.include_router(r, prefix="/api")
