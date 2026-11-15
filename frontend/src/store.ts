import { create } from "zustand";
import { api, ApiError } from "./api/client";
import type {
  MissionInfo, MissionWindow, PointResponse, Profile, ProfileId, Report, ScoreResponse, SiteOverview, Timeseries,
} from "./api/types";
import { formatUtc } from "./lib/time";
import { localReport, localScore, mockSites, mockTimeseries, PROFILES } from "./mocks";

export type Mode = "explore" | "time" | "selection";
export type Panel = null | "data" | "score" | "menu" | "report" | "mission";

export const MODES: Mode[] = ["explore", "time", "selection"];
export const MODE_NAMES: Record<Mode, string> = {
  explore: "Explore",
  time: "Mission Time",
  selection: "Mission Selection",
};

export interface State {
  // datos
  loading: boolean;
  offline: boolean; // true = API caída, se usan mocks
  sites: SiteOverview[]; // 3 fijos + punto libre al final (si existe)
  timeseries: Record<string, Timeseries>;
  profiles: Profile[];
  score: ScoreResponse | null;
  report: Report | null;
  freePoint: null | { lat: number; lon: number; status: "loading" | "ready" | "error"; data?: PointResponse };
  toast: string | null;

  // interfaz
  mode: Mode;
  siteIndex: number;
  timeIndex: number; // índice fraccionario en samples
  playing: boolean;
  profile: ProfileId;
  shadows: boolean;
  panel: Panel;
  selectionRow: number;
  gamepadConnected: boolean;
  gamepadStandard: boolean;
  globeStatus: "loading" | "terrain" | "ellipsoid" | "error";
  globeMessage: string | null;

  // ventana de la misión (fecha de aterrizaje y duración)
  mission: MissionWindow | null; // null = la ventana por defecto (precalculada)
  missionInfo: MissionInfo | null;
  missionDraft: MissionWindow | null; // lo que se está editando en el panel de fecha

  // capas y sombras
  layer: LayerId;
  layerFromShadows: boolean; // la capa de elevación la puso Triángulo: al apagar las sombras se quita
  layersMeta: LayerMeta[]; // de /layers/layers.json (lo genera backend/scripts/make_layers.py)
  layersBase: BaseLayerMeta | null; // relieve sombreado de fondo
  shadowInfo: ShadowInfo;
}

export type LayerId = "none" | "elevation" | "slope";
export const LAYER_ORDER: LayerId[] = ["none", "elevation", "slope"];

export interface LayerMeta {
  id: Exclude<LayerId, "none">;
  name: string;
  url: string;
  units: string;
  legend: { value: number; color: string }[];
  threshold?: number;
  method: string;
  source: string;
  resolution_m: number;
  rectangle: { west: number; south: number; east: number; north: number };
  status: "real" | "mock";
}

export interface BaseLayerMeta {
  url: string;
  rectangle: LayerMeta["rectangle"];
}

/** Estado de la capa de sombras: "dem" = calculadas con LOLA + SPICE; "approx" = sombras de Cesium. */
export interface ShadowInfo {
  mode: "off" | "loading" | "dem" | "approx";
  siteLitFraction?: number | null;
  sunEl?: number;
  detail?: string;
}

const initial: State = {
  loading: true, offline: false, sites: [], timeseries: {}, profiles: PROFILES, score: null, report: null,
  freePoint: null, toast: null,
  mode: "explore", siteIndex: 0, timeIndex: 0, playing: false, profile: "solar", shadows: false,
  panel: null, selectionRow: 0, gamepadConnected: false, gamepadStandard: true,
  globeStatus: "loading", globeMessage: null,
  mission: null, missionInfo: null, missionDraft: null,
  layer: "none", layerFromShadows: false, layersMeta: [], layersBase: null, shadowInfo: { mode: "off" },
};

/** Carga los metadatos de las capas fijas (si no se generaron, no hay capas y no pasa nada). */
export async function loadLayers() {
  try {
    const res = await fetch("/layers/layers.json", { cache: "no-cache" });
    if (!res.ok) return;
    const json = (await res.json()) as { layers: LayerMeta[]; base?: BaseLayerMeta };
    set({ layersMeta: json.layers ?? [], layersBase: json.base ?? null });
  } catch {
    /* sin capas */
  }
}

export const useStore = create<State>(() => initial);
export const get = useStore.getState;
export const set = useStore.setState;

let toastTimer: ReturnType<typeof setTimeout> | undefined;
export function toast(msg: string, ms = 3500) {
  set({ toast: msg });
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => set({ toast: null }), ms);
}

export const activeSite = (s: State = get()) => s.sites[s.siteIndex];
export const activeTimeseries = (s: State = get()) => {
  const site = activeSite(s);
  return site ? s.timeseries[site.id] : undefined;
};
const pointId = () => get().freePoint?.data?.point_id;
/** Ventana a pedir a la API (undefined = la por defecto). */
export const missionWindow = (s: State = get()) => s.mission ?? undefined;
/** Ventana efectiva (la elegida o la por defecto). */
export function effectiveWindow(s: State = get()): MissionWindow | null {
  if (s.mission) return s.mission;
  return s.missionInfo ? { start: s.missionInfo.default_start, days: s.missionInfo.default_days } : null;
}

// ------------------------------------------------------------------ carga
export async function loadAll() {
  set({ loading: true });
  try {
    await api.health();
    const [sites, profiles, missionInfo] = await Promise.all([api.sites(), api.profiles(), api.mission().catch(() => null)]);
    const w = missionWindow();
    const series = await Promise.all(sites.map((s) => api.timeseries(s.id, w)));
    const score = await api.score(get().profile, undefined, w);
    set({
      offline: false, sites, profiles, missionInfo,
      timeseries: Object.fromEntries(series.map((t) => [t.site_id, t])),
      score, loading: false,
    });
  } catch (e) {
    console.warn("API no disponible, uso mocks:", e);
    const sites = await mockSites();
    const series = await Promise.all(sites.map((s) => mockTimeseries(s.id)));
    set({
      offline: true, sites, profiles: PROFILES,
      timeseries: Object.fromEntries(series.map((t) => [t.site_id, t])),
      score: localScore(get().profile), loading: false,
    });
    toast("Datos de demostración: la API no responde");
  }
}

// ------------------------------------------------------------------ puntuación
export async function refreshScore(profile: ProfileId = get().profile) {
  set({ profile });
  const pid = pointId();
  if (get().offline) {
    const fp = get().freePoint?.data;
    set({ score: localScore(profile, fp ? [{ id: fp.point_id, quality: "estimated", summary: fp.timeseries.summary, terrain: fp.terrain }] : []) });
    return;
  }
  try {
    const score = await api.score(profile, pid, missionWindow());
    if (get().profile === profile) set({ score }); // ignora respuestas viejas
  } catch (e) {
    toast(`No se pudo calcular la puntuación: ${(e as Error).message}`);
  }
}

// ------------------------------------------------------------------ informe
export async function openReport(siteId: string) {
  const s = get();
  set({ panel: "report", report: null });
  try {
    const report = s.offline
      ? localReport(s.sites.find((x) => x.id === siteId)!, s.profile, s.score!, s.timeseries[siteId]?.summary.windows[0] ?? null)
      : await api.report(siteId, s.profile, missionWindow(s));
    set({ report });
  } catch (e) {
    set({ panel: null });
    toast(`No se pudo generar el informe: ${(e as Error).message}`);
  }
}

// ------------------------------------------------------------------ punto libre
export async function analyzePoint(lat: number, lon: number) {
  const s = get();
  if (s.freePoint?.status === "loading") return;
  if (s.offline) {
    toast("Punto libre no disponible sin conexión con la API");
    return;
  }
  set({ freePoint: { lat, lon, status: "loading" } });
  toast("Analizando punto… (estimado)", 15000);
  try {
    const data = await api.point(lat, lon);
    const w = missionWindow();
    if (w) data.timeseries = await api.timeseries(data.point_id, w); // misma ventana que los sitios
    const site: SiteOverview = {
      ...data.site, quality: "estimated", complete: true,
      source: data.timeseries.source ?? "real", terrain: data.terrain, summary: data.timeseries.summary,
    };
    const fixed = get().sites.filter((x) => x.quality === "full");
    set({
      freePoint: { lat, lon, status: "ready", data },
      sites: [...fixed, site],
      timeseries: { ...get().timeseries, [data.point_id]: data.timeseries },
      siteIndex: fixed.length,
    });
    toast(`Punto libre analizado en ${data.elapsed_s.toFixed(1)} s (estimado)`);
    await refreshScore();
  } catch (e) {
    set({ freePoint: null });
    if (e instanceof ApiError && e.code === "outside_dem") toast("Ese punto está fuera de la cobertura del DEM LOLA");
    else toast(`No se pudo analizar el punto: ${(e as Error).message}`);
  }
}

// ------------------------------------------------------------------ fecha de la misión
const DAY = 86_400_000;
/** Mes lunar sinódico (de una salida del Sol a la siguiente en el mismo sitio). */
export const SYNODIC_MS = 29.530589 * DAY;

export function isoDay(ms: number): string {
  return new Date(ms).toISOString().replace(/\.\d+Z$/, "Z");
}

/** Abre el panel de fecha con la ventana actual como borrador. */
export function openMissionPanel() {
  const w = effectiveWindow();
  if (!w) return toast("La API no informa de la ventana de la misión");
  set({ panel: "mission", missionDraft: { ...w } });
}

/** Mueve el borrador: días (±1) o meses lunares (±1); duración con dDays. */
export function nudgeMissionDraft(deltaMs: number, dDays = 0) {
  const s = get();
  const d = s.missionDraft, info = s.missionInfo;
  if (!d || !info) return;
  const days = Math.max(1, Math.min(info.max_days, d.days + dDays));
  let start = Math.round((Date.parse(d.start) + deltaMs) / 3_600_000) * 3_600_000; // a la hora en punto
  start = Math.max(Date.parse(info.min_start), Math.min(Date.parse(info.max_end) - days * DAY, start));
  set({ missionDraft: { start: isoDay(start), days } });
}

/** Aplica una ventana de misión: recalcula las series de todos los sitios y la puntuación. */
export async function applyMission(w: MissionWindow) {
  const s = get();
  if (s.offline) return toast("Cambiar la fecha necesita la API (ahora hay datos de demostración)");
  if (s.missionInfo && !s.missionInfo.live_dates) {
    return toast("El servidor no tiene los kernels SPICE: solo está disponible la fecha por defecto");
  }
  const isDefault = s.missionInfo && w.start === s.missionInfo.default_start && w.days === s.missionInfo.default_days;
  const req = isDefault ? undefined : w;
  set({ loading: true, panel: null, playing: false });
  try {
    const series = await Promise.all(get().sites.map((x) => api.timeseries(x.id, req)));
    const score = await api.score(get().profile, pointId(), req);
    set({
      mission: req ?? null,
      timeseries: Object.fromEntries(series.map((t) => [t.site_id, t])),
      sites: get().sites.map((x) => {
        const t = series.find((y) => y.site_id === x.id);
        return t ? { ...x, summary: t.summary } : x;
      }),
      score, timeIndex: 0, loading: false,
    });
    const end = Date.parse(w.start) + w.days * DAY;
    const day = (ms: number) => formatUtc(ms).split(" · ")[0];
    toast(`Misión: ${day(Date.parse(w.start))} → ${day(end)} (${w.days} d)`);
  } catch (e) {
    set({ loading: false });
    toast(`No se pudo cambiar la fecha: ${(e as Error).message}`);
  }
}
