// Despachador: acción + modo → cambio de estado. Implementa la tabla de controles del contrato.
import { globe } from "../globe/bridge";
import { indexOf } from "../lib/time";
import {
  activeSite, activeTimeseries, analyzePoint, get, MODES, openReport, refreshScore, set, toast,
  type Mode, type State,
} from "../store";
import { rumble } from "./gamepad";
import type { Action, Analog } from "./types";

const nextMode = (m: Mode): Mode => MODES[(MODES.indexOf(m) + 1) % MODES.length];

function goToSite(delta: number) {
  const s = get();
  if (!s.sites.length) return;
  const siteIndex = (s.siteIndex + delta + s.sites.length) % s.sites.length;
  const site = s.sites[siteIndex];
  set({ siteIndex, selectionRow: rowOfSite(site.id) });
  globe.flyToSite(site.lat, site.lon);
}

/** Fila de la tabla de comparación (ordenada por puntuación) de un sitio. */
function rowOfSite(id: string, s: State = get()): number {
  const i = s.score?.ranking.findIndex((r) => r.site_id === id) ?? -1;
  return i < 0 ? 0 : i;
}

function setRow(row: number) {
  const s = get();
  const ranking = s.score?.ranking ?? [];
  if (!ranking.length) return;
  const selectionRow = Math.max(0, Math.min(ranking.length - 1, row));
  const siteIndex = s.sites.findIndex((x) => x.id === ranking[selectionRow].site_id);
  set({ selectionRow, siteIndex: siteIndex < 0 ? s.siteIndex : siteIndex });
  if (siteIndex >= 0 && siteIndex !== s.siteIndex) globe.flyToSite(s.sites[siteIndex].lat, s.sites[siteIndex].lon);
}

function jumpWindow(dir: 1 | -1) {
  const ts = activeTimeseries();
  if (!ts) return;
  const starts = ts.summary.windows.map((w) => indexOf(ts, w.start)).sort((a, b) => a - b);
  if (!starts.length) return toast("Este sitio no tiene ventanas con Sol y Tierra a la vez");
  const cur = get().timeIndex;
  const target = dir > 0 ? starts.find((i) => i > cur + 0.5) : [...starts].reverse().find((i) => i < cur - 0.5);
  if (target === undefined) return toast(dir > 0 ? "No hay más ventanas" : "No hay ventanas anteriores");
  set({ timeIndex: target, playing: false });
}

function cycleProfile(delta: number) {
  const s = get();
  const ids = s.profiles.map((p) => p.id);
  const next = ids[(ids.indexOf(s.profile) + delta + ids.length) % ids.length];
  void refreshScore(next).then(() => {
    const site = activeSite();
    if (site) set({ selectionRow: rowOfSite(site.id) });
  });
}

function toggle(panel: State["panel"]) {
  set({ panel: get().panel === panel ? null : panel });
}

export function handle(action: Action) {
  const s = get();
  // globales
  if (action === "touchpad") {
    const mode = nextMode(s.mode);
    const site = activeSite();
    return set({ mode, panel: null, selectionRow: site ? rowOfSite(site.id) : 0 });
  }
  if (action === "circle") return set({ panel: null });
  if (action === "options") return toggle("menu");
  if (s.panel === "report" || s.panel === "menu") return; // con el informe o el menú abiertos solo vale Círculo/Options
  if (action === "l1") return goToSite(-1);
  if (action === "r1") return goToSite(1);

  switch (s.mode) {
    case "explore":
      if (action === "x") {
        const p = globe.pickCenter();
        if (!p) return toast("Apunta la retícula a la superficie lunar");
        return void analyzePoint(p.lat, p.lon);
      }
      if (action === "square") return toggle("data");
      if (action === "triangle") return set({ shadows: !s.shadows });
      return;
    case "time":
      if (action === "x") {
        const ts = activeTimeseries();
        const atEnd = ts && s.timeIndex >= ts.samples.length - 1;
        return set({ playing: !s.playing, timeIndex: atEnd && !s.playing ? 0 : s.timeIndex });
      }
      if (action === "square") return toggle("data");
      if (action === "triangle") return set({ shadows: !s.shadows });
      if (action === "dpad_right") return jumpWindow(1);
      if (action === "dpad_left") return jumpWindow(-1);
      return;
    case "selection":
      if (action === "dpad_right" || action === "dpad_down") return cycleProfile(1);
      if (action === "dpad_left" || action === "dpad_up") return cycleProfile(-1);
      if (action === "square") return toggle("score");
      if (action === "x") {
        const row = s.score?.ranking[s.selectionRow];
        if (!row) return;
        rumble();
        return void openReport(row.site_id);
      }
      return;
  }
}

// ------------------------------------------------------------------ comportamiento continuo
const MAX_HOURS_PER_SEC = 48;
const PLAY_HOURS_PER_SEC = 6;
let rowCooldown = 0;

export function continuous(a: Analog, dt: number) {
  const s = get();
  const modal = s.panel === "report" || s.panel === "menu";
  if (s.mode === "explore") {
    if (!modal) globe.move(a.lx, a.ly, a.rx, a.ry, a.r2 - a.l2, dt);
    return;
  }
  if (s.mode === "time") {
    if (!modal) globe.move(0, 0, a.rx, a.ry, 0, dt);
    const ts = activeTimeseries();
    if (!ts) return;
    const hours = (a.r2 - a.l2) * MAX_HOURS_PER_SEC * dt + (s.playing ? PLAY_HOURS_PER_SEC * dt : 0);
    if (hours === 0) return;
    const last = ts.samples.length - 1;
    const timeIndex = Math.max(0, Math.min(last, s.timeIndex + hours / ts.step_hours));
    set({ timeIndex, playing: s.playing && timeIndex < last });
    return;
  }
  // selection: el joystick izquierdo recorre las filas (con repetición)
  rowCooldown -= dt;
  if (modal || Math.abs(a.ly) < 0.5) {
    if (Math.abs(a.ly) < 0.5) rowCooldown = 0;
    return;
  }
  if (rowCooldown <= 0) {
    setRow(s.selectionRow + Math.sign(a.ly));
    rowCooldown = 0.25;
  }
}
