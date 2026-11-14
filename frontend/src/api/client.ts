import type {
  ApiErrorBody, Health, PointResponse, Profile, ProfileId, Report, ScoreResponse, SiteOverview, Timeseries,
} from "./types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api";

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

export const api = {
  health: () => request<Health>("/health", undefined, 2500),
  sites: () => request<SiteOverview[]>("/sites"),
  timeseries: (id: string) => request<Timeseries>(`/sites/${encodeURIComponent(id)}/timeseries`),
  profiles: () => request<Profile[]>("/profiles"),
  score: (profile: ProfileId, pointId?: string) =>
    request<ScoreResponse>(`/score?profile=${profile}${pointId ? `&point_id=${encodeURIComponent(pointId)}` : ""}`),
  point: (lat: number, lon: number) =>
    request<PointResponse>("/point", { method: "POST", body: JSON.stringify({ lat, lon }) }, 15000),
  report: (siteId: string, profile: ProfileId) =>
    request<Report>("/report", { method: "POST", body: JSON.stringify({ site_id: siteId, profile }) }),
};
