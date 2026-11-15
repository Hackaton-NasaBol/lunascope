import type {
  ApiErrorBody, Health, MissionInfo, MissionWindow, ScenarioSummary, PointResponse, Profile, ProfileId, Report, ScoreResponse, SiteOverview, Timeseries,
} from "./types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api";
export const API_BASE = BASE;

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, detail: string) {
    super(detail);
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit, timeoutMs = 8000): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(BASE + path, {
      ...init,
      signal: ctrl.signal,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
    if (!res.ok) {
      let body: ApiErrorBody = { error: "http_error", detail: res.statusText };
      try { body = await res.json(); } catch { /* cuerpo no JSON */ }
      throw new ApiError(res.status, body.error, body.detail);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

const win = (w?: MissionWindow) => (w ? `start=${encodeURIComponent(w.start)}&days=${w.days}` : "");

export const api = {
  mission: () => request<MissionInfo>("/mission"),
  scenario: (profile: ProfileId, w?: MissionWindow, pointId?: string) =>
    request<ScenarioSummary>(`/scenario?profile=${profile}${w ? `&${win(w)}` : ""}${pointId ? `&point_id=${encodeURIComponent(pointId)}` : ""}`, undefined, 20000),
  health: () => request<Health>("/health", undefined, 2500),
  sites: () => request<SiteOverview[]>("/sites"),
  timeseries: (id: string, w?: MissionWindow) =>
    request<Timeseries>(`/sites/${encodeURIComponent(id)}/timeseries${w ? `?${win(w)}` : ""}`, undefined, 20000),
  profiles: () => request<Profile[]>("/profiles"),
  score: (profile: ProfileId, pointId?: string, w?: MissionWindow) =>
    request<ScoreResponse>(`/score?profile=${profile}${pointId ? `&point_id=${encodeURIComponent(pointId)}` : ""}${w ? `&${win(w)}` : ""}`, undefined, 20000),
  point: (lat: number, lon: number) =>
    request<PointResponse>("/point", { method: "POST", body: JSON.stringify({ lat, lon }) }, 15000),
  report: (siteId: string, profile: ProfileId, w?: MissionWindow) =>
    request<Report>("/report", { method: "POST", body: JSON.stringify({ site_id: siteId, profile, ...(w ?? {}) }) }, 20000),
};
