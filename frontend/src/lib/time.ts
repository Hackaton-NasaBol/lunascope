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
