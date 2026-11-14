"""Modelos Pydantic que reflejan el contrato de datos v1 (docs/contract.md).

Se usan como response_model: si un módulo rompe el formato, FastAPI falla al
serializar y se ve al instante.
"""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Source = Literal["real", "mock"]
Quality = Literal["full", "estimated"]


class Site(BaseModel):
    id: str
    name: str
    region: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    elevation_m: float
    notes: str = ""


class Horizon(BaseModel):
    site_id: str
    lat: float
    lon: float
    observer_height_m: float
    az_step_deg: float
    horizon_el_deg: list[float]
    max_distance_km: float
    dem_source: str
    dem_resolution_m: float
    mode: Literal["full", "fast"]
    generated_at: str
    source: Source = "real"


class Terrain(BaseModel):
    site_id: str
    elevation_m: float
    radius_m: float
    slope_deg_mean: float
    slope_deg_max: float
    hazard_pct: float = Field(ge=0, le=100)
    dem_resolution_m: float
    source: Source = "real"


class BodySample(BaseModel):
    az: float
    el: float
    horizon_el: float
    visible_fraction: float = Field(ge=0, le=1)


class Sample(BaseModel):
    t: str
    sun: BodySample
    earth: BodySample


class Window(BaseModel):
    start: str
    end: str
    hours: float


class Summary(BaseModel):
    sun_visible_pct: float = Field(ge=0, le=100)
    earth_visible_pct: float = Field(ge=0, le=100)
    both_visible_pct: float = Field(ge=0, le=100)
    longest_dark_h: float
    longest_no_earth_h: float
    windows: list[Window]


class Timeseries(BaseModel):
    site_id: str
    start: str
    end: str
    step_hours: float
    samples: list[Sample]
    summary: Summary
    source: Source = "real"


class SiteOverview(Site):
    """Elemento de GET /sites: sitio + terrain + summary."""

    quality: Quality = "full"
    complete: bool
    source: Source
    terrain: Optional[Terrain] = None
    summary: Optional[Summary] = None


class Health(BaseModel):
    status: str
    kernels_loaded: bool
    sites: int


class Profile(BaseModel):
    id: str
    name: str
    weights: dict[str, float]
    mvp: bool


class Breakdown(BaseModel):
    sun: float
    earth: float
    continuity: float
    terrain: float


class RankingRow(BaseModel):
    site_id: str
    score: float
    quality: Quality
    breakdown: Breakdown
    explanation: list[str]


class ScoreOut(BaseModel):
    profile: str
    recommended: str
    ranking: list[RankingRow]
    notes: list[str] = []


class PointIn(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class PointOut(BaseModel):
    point_id: str
    quality: Literal["estimated"] = "estimated"
    site: Site
    horizon: Horizon
    terrain: Terrain
    timeseries: Timeseries
    elapsed_s: float


class ReportIn(BaseModel):
    site_id: str
    profile: str


class ReportSite(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    elevation_m: float


class ComparisonRow(BaseModel):
    site_id: str
    score: float


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    generated_at: str
    profile: Profile
    site: ReportSite
    quality: Quality
    score: float
    rank: int
    breakdown: Breakdown
    best_window: Optional[Window]
    explanation: list[str]
    comparison: list[ComparisonRow]
    data_sources: list[str]
    limitations: list[str]


class ErrorOut(BaseModel):
    error: str
    detail: str
