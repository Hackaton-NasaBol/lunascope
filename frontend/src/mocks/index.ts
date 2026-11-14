// Datos de respaldo cuando la API no responde ("Datos de demostración").
// Los JSON se copian del backend con `npm run sync-mocks`.
import type {
  Profile, ProfileId, RankingRow, Report, ScoreResponse, Site, SiteOverview, Summary, Terrain, Timeseries,
} from "../api/types";
import { formatWindowStart } from "../lib/time";

const sitesJson = import.meta.glob<Site[]>("./data/sites.json", { eager: true, import: "default" });
const terrainJson = import.meta.glob<Terrain>("./data/*/terrain.json", { eager: true, import: "default" });
const tsLoaders = import.meta.glob<Timeseries>("./data/*/timeseries.json", { import: "default" });

const SITES: Site[] = Object.values(sitesJson)[0] ?? [];
const terrainOf = (id: string) => terrainJson[`./data/${id}/terrain.json`] ?? null;

export const PROFILES: Profile[] = [
  { id: "solar", name: "Energía solar", weights: { sun: 0.5, earth: 0.15, continuity: 0.2, terrain: 0.15 }, mvp: true },
  { id: "comms", name: "Comunicaciones", weights: { sun: 0.2, earth: 0.5, continuity: 0.1, terrain: 0.2 }, mvp: true },
  { id: "safety", name: "Seguridad de aterrizaje", weights: { sun: 0.2, earth: 0.2, continuity: 0.1, terrain: 0.5 }, mvp: false },
  { id: "balanced", name: "Equilibrado", weights: { sun: 0.25, earth: 0.25, continuity: 0.25, terrain: 0.25 }, mvp: false },
];

const summaries = new Map<string, Summary>();

export async function mockTimeseries(id: string): Promise<Timeseries> {
  const load = tsLoaders[`./data/${id}/timeseries.json`];
  if (!load) throw new Error(`Sin mock para ${id}`);
  const ts = await load();
  summaries.set(id, ts.summary);
  return ts;
}

export async function mockSites(): Promise<SiteOverview[]> {
  const out: SiteOverview[] = [];
  for (const s of SITES) {
    const ts = await mockTimeseries(s.id).catch(() => null);
    out.push({ ...s, quality: "full", complete: !!ts, source: "mock", terrain: terrainOf(s.id), summary: ts?.summary ?? null });
  }
  return out;
}

// Puerto en TS del motor de backend/lunascope/scoring (versión simplificada de las explicaciones).
const r1 = (x: number) => Math.round(x * 10) / 10;

function subscores(s: Summary, t: Terrain) {
  return {
    sun: r1(s.sun_visible_pct),
    earth: r1(s.earth_visible_pct),
    continuity: r1(100 * Math.max(0, 1 - s.longest_dark_h / 240)),
    terrain: r1(100 * Math.max(0, 1 - t.slope_deg_mean / 15) * (1 - t.hazard_pct / 100)),
  };
}

export interface Candidate { id: string; quality: "full" | "estimated"; summary: Summary; terrain: Terrain }

export function localScore(profileId: ProfileId, extra: Candidate[] = []): ScoreResponse {
  const p = PROFILES.find((x) => x.id === profileId)!;
  const cands: Candidate[] = SITES.flatMap((s): Candidate[] => {
    const sum = summaries.get(s.id), ter = terrainOf(s.id);
    return sum && ter ? [{ id: s.id, quality: "full", summary: sum, terrain: ter }] : [];
  }).concat(extra);

  const rows: RankingRow[] = cands.map((c) => {
    const b = subscores(c.summary, c.terrain);
    const score = r1((Object.keys(p.weights) as (keyof typeof b)[]).reduce((acc, k) => acc + p.weights[k] * b[k], 0));
    const w = c.summary.windows[0];
    return {
      site_id: c.id, score, quality: c.quality, breakdown: b,
      explanation: [
        `Tiene Sol visible el ${c.summary.sun_visible_pct.toFixed(0)} % del tiempo y ve la Tierra el ${c.summary.earth_visible_pct.toFixed(0)} %.`,
        `Su noche más larga dura ${c.summary.longest_dark_h.toFixed(0)} h.`,
        w ? `Mejor ventana con Sol y Tierra a la vez: ${formatWindowStart(w.start)}, ${w.hours.toFixed(0)} h.`
          : "No hay ninguna ventana con Sol y Tierra visibles a la vez.",
        "(Calculado en el navegador: datos de demostración.)",
      ],
    };
  });
  rows.sort((a, b) => b.score - a.score);
  const full = rows.filter((r) => r.quality === "full");
  const notes = rows[0] && rows[0].quality !== "full" && full.length
    ? ["El punto libre puntúa más alto, pero su análisis es aproximado."] : [];
  return { profile: profileId, recommended: full[0]?.site_id ?? "", ranking: rows, notes };
}

export function localReport(site: Site, profileId: ProfileId, score: ScoreResponse, best: Report["best_window"]): Report {
  const idx = score.ranking.findIndex((r) => r.site_id === site.id);
  const row = score.ranking[idx];
  return {
    title: `Informe de planificación — ${site.name}`,
    generated_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    profile: PROFILES.find((p) => p.id === profileId)!,
    site: { id: site.id, name: site.name, lat: site.lat, lon: site.lon, elevation_m: site.elevation_m },
    quality: row.quality, score: row.score, rank: idx + 1, breakdown: row.breakdown, best_window: best,
    explanation: row.explanation.concat(score.notes),
    comparison: score.ranking.map((r) => ({ site_id: r.site_id, score: r.score })),
    data_sources: ["DATOS DE DEMOSTRACIÓN (sin conexión con la API)."],
    limitations: [
      "Visibilidad geométrica: no incluye enlaces de radio ni cobertura de satélites.",
      "La fracción visible del disco es una aproximación lineal.",
      "Informe generado sin backend: datos de prueba.",
    ],
  };
}
