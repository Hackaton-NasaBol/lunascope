import type { BodySample, Sample, Timeseries } from "../api/types";

const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const pad = (n: number) => String(n).padStart(2, "0");

export function formatUtc(iso: string | number): string {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()} · ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
}

export function formatWindowStart(iso: string): string {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())} UTC`;
}

/** Interpolación de ángulos de azimut respetando el salto 359° → 0°. */
function lerpAz(a: number, b: number, f: number): number {
  let d = b - a;
  if (d > 180) d -= 360;
  if (d < -180) d += 360;
  return (a + d * f + 360) % 360;
}

function lerpBody(a: BodySample, b: BodySample, f: number): BodySample {
  return {
    az: lerpAz(a.az, b.az, f),
    el: a.el + (b.el - a.el) * f,
    horizon_el: a.horizon_el + (b.horizon_el - a.horizon_el) * f,
    visible_fraction: a.visible_fraction + (b.visible_fraction - a.visible_fraction) * f,
  };
}

/** Muestra interpolada en un índice fraccionario. */
export function sampleAt(ts: Timeseries, index: number): Sample & { ms: number } {
  const n = ts.samples.length;
  const i = Math.max(0, Math.min(n - 1, index));
  const i0 = Math.floor(i), i1 = Math.min(n - 1, i0 + 1), f = i - i0;
  const a = ts.samples[i0], b = ts.samples[i1];
  const ms = Date.parse(a.t) + (Date.parse(b.t) - Date.parse(a.t)) * f;
  return { t: new Date(ms).toISOString(), ms, sun: lerpBody(a.sun, b.sun, f), earth: lerpBody(a.earth, b.earth, f) };
}

/** Índice (fraccionario) de un instante ISO dentro de la serie. */
export function indexOf(ts: Timeseries, iso: string): number {
  const t0 = Date.parse(ts.start);
  return (Date.parse(iso) - t0) / (ts.step_hours * 3600_000);
}

export interface NextChange {
  visibleNow: boolean;
  /** Horas hasta el próximo cambio (puesta si visibleNow, salida si no). null = no cambia antes del final de la serie. */
  hours: number | null;
  /** Instante UTC del cambio (ms). */
  atMs: number | null;
  /** Horas que quedan hasta el final de la serie (para decir "más de N h"). */
  remainingHours: number;
}

/**
 * Próxima puesta o salida del Sol o de la Tierra a partir de un índice (fraccionario) de la serie.
 * "Visible" = fracción del disco ≥ 0,5 (misma regla que el backend). El cruce se interpola entre muestras.
 */
export function nextChange(ts: Timeseries, index: number, body: "sun" | "earth"): NextChange {
  const s = ts.samples, n = s.length;
  const step = ts.step_hours;
  const i = Math.max(0, Math.min(n - 1, index));
  const vfAt = (k: number) => s[k][body].visible_fraction;
  const i0 = Math.floor(i), f = i - i0;
  const vfNow = i0 + 1 < n ? vfAt(i0) * (1 - f) + vfAt(i0 + 1) * f : vfAt(i0);
  const visibleNow = vfNow >= 0.5;
  const remainingHours = (n - 1 - i) * step;
  const t0 = Date.parse(s[0].t);
  for (let k = i0 + 1; k < n; k++) {
    if ((vfAt(k) >= 0.5) !== visibleNow) {
      const a = vfAt(k - 1), b = vfAt(k);
      const frac = b !== a ? Math.min(1, Math.max(0, (0.5 - a) / (b - a))) : 1;
      const kx = Math.max(i, k - 1 + frac);
      return { visibleNow, hours: (kx - i) * step, atMs: t0 + kx * step * 3600_000, remainingHours };
    }
  }
  return { visibleNow, hours: null, atMs: null, remainingHours };
}

/** "37 h" o "4 d 13 h" (para tiempos largos en la Luna). */
export function formatDuration(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  if (hours < 48) return `${Math.round(hours)} h`;
  const d = Math.floor(hours / 24), h = Math.round(hours - d * 24);
  return h ? `${d} d ${h} h` : `${d} d`;
}

/** "Puesta en 4 d 6 h · 12 sep 03:00 UTC" / "Sale en 9 h · …" / "Sin puesta en los próximos 30 d". */
export function nextChangeText(ts: Timeseries, index: number, body: "sun" | "earth"): { text: string; soon: boolean } {
  const c = nextChange(ts, index, body);
  const verb = c.visibleNow ? (body === "sun" ? "Puesta del Sol" : "Puesta de la Tierra") : (body === "sun" ? "Sale el Sol" : "Sale la Tierra");
  if (c.hours === null) {
    return {
      text: c.visibleNow ? `Sin puesta en lo que queda (${formatDuration(c.remainingHours)})` : `No sale en lo que queda (${formatDuration(c.remainingHours)})`,
      soon: false,
    };
  }
  return {
    text: `${verb} en ${formatDuration(c.hours)} · ${formatWindowStart(new Date(c.atMs!).toISOString())}`,
    soon: c.visibleNow && c.hours < 24, // aviso: se pierde en menos de 1 día
  };
}
