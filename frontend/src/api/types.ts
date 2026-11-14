// Tipos copiados del contrato v1 (docs/contract.md). Si el contrato cambia, se cambian aquí primero.

export type Source = "real" | "mock";
export type Quality = "full" | "estimated";
export type ProfileId = "solar" | "comms" | "safety" | "balanced";

export interface Site {
  id: string;
  name: string;
  region: string;
  lat: number;
  lon: number;
  elevation_m: number;
  notes: string;
}

export interface Horizon {
  site_id: string;
  lat: number;
  lon: number;
  observer_height_m: number;
  az_step_deg: number;
  horizon_el_deg: number[];
  max_distance_km: number;
  dem_source: string;
  dem_resolution_m: number;
  mode: "full" | "fast";
  generated_at: string;
  source?: Source;
}

export interface Terrain {
  site_id: string;
  elevation_m: number;
  radius_m: number;
  slope_deg_mean: number;
  slope_deg_max: number;
  hazard_pct: number;
  dem_resolution_m: number;
  source?: Source;
}

export interface BodySample {
  az: number;
  el: number;
  horizon_el: number;
  visible_fraction: number;
}

export interface Sample {
  t: string;
  sun: BodySample;
  earth: BodySample;
}

export interface Window {
  start: string;
  end: string;
  hours: number;
}

export interface Summary {
  sun_visible_pct: number;
  earth_visible_pct: number;
  both_visible_pct: number;
  longest_dark_h: number;
  longest_no_earth_h: number;
  windows: Window[];
}

export interface Timeseries {
  site_id: string;
  start: string;
  end: string;
  step_hours: number;
  samples: Sample[];
  summary: Summary;
  source?: Source;
}

export interface SiteOverview extends Site {
  quality: Quality;
  complete: boolean;
  source: Source;
  terrain: Terrain | null;
  summary: Summary | null;
}

export interface Health {
  status: string;
  kernels_loaded: boolean;
  sites: number;
}

export type Weights = Record<"sun" | "earth" | "continuity" | "terrain", number>;

export interface Profile {
  id: ProfileId;
  name: string;
  weights: Weights;
  mvp: boolean;
}

export type Breakdown = Weights;

export interface RankingRow {
  site_id: string;
  score: number;
  quality: Quality;
  breakdown: Breakdown;
  explanation: string[];
}

export interface ScoreResponse {
  profile: ProfileId;
  recommended: string;
  ranking: RankingRow[];
  notes: string[];
}

export interface PointResponse {
  point_id: string;
  quality: "estimated";
  site: Site;
  horizon: Horizon;
  terrain: Terrain;
  timeseries: Timeseries;
  elapsed_s: number;
}

export interface Report {
  title: string;
  generated_at: string;
  profile: Profile;
  site: Pick<Site, "id" | "name" | "lat" | "lon" | "elevation_m">;
  quality: Quality;
  score: number;
  rank: number;
  breakdown: Breakdown;
  best_window: Window | null;
  explanation: string[];
  comparison: { site_id: string; score: number }[];
  data_sources: string[];
  limitations: string[];
}

export interface ApiErrorBody {
  error: string;
  detail: string;
}
