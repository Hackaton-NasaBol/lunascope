import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { MissionWindow, ScenarioSite, ScenarioSummary } from "../api/types";
import { formatDuration, formatUtc, formatWindowStart } from "../lib/time";
import { applyMission, nudgeMissionDraft, set, SYNODIC_MS, useStore } from "../store";
import { Kbd, PadButton } from "./Buttons";

const DAY = 86_400_000;
const DURATIONS = [15, 30, 60, 90, 120, 180];
const day = (iso: string | number) => formatUtc(iso).split(" · ")[0];
const n1 = (v: number) => v.toLocaleString("es", { maximumFractionDigits: 1 });

/** Diferencia con la fecha actual: verde si mejora, rojo si empeora. */
function Delta({ now, before, higherIsBetter = true, unit = "" }: { now: number | null; before?: number | null; higherIsBetter?: boolean; unit?: string }) {
  if (now === null || before === null || before === undefined) return null;
  const d = now - before;
  if (Math.abs(d) < 0.05) return <span className="ml-1 text-xs text-slate-500">=</span>;
  const good = higherIsBetter ? d > 0 : d < 0;
  return (
    <span className={`ml-1 text-xs font-semibold ${good ? "text-emerald-300" : "text-rose-300"}`}>
      {d > 0 ? "▲" : "▼"} {n1(Math.abs(d))}{unit}
    </span>
  );
}

function Landing({ s }: { s: ScenarioSite }) {
  const a = s.at_landing;
  const line = (icon: string, visible: boolean, change: number | null) =>
    visible
      ? <span className="text-emerald-300">{icon} Sí · {change === null ? "sin puesta" : `puesta en ${formatDuration(change)}`}</span>
      : <span className="text-rose-300">{icon} No · {change === null ? "no sale" : `sale en ${formatDuration(change)}`}</span>;
  return (
    <div className="space-y-0.5 text-sm">
      <div>{line("☀", a.sun_visible, a.sun_change_h)}</div>
      <div>{line("🌍", a.earth_visible, a.earth_change_h)}</div>
    </div>
  );
}

/** Panel "¿Y si aterrizamos en otra fecha?": elige fecha y duración y muestra el resultado antes de aplicar. */
export default function MissionPanel() {
  const draft = useStore((s) => s.missionDraft);
  const info = useStore((s) => s.missionInfo);
  const mission = useStore((s) => s.mission);
  const profile = useStore((s) => s.profile);
  const profiles = useStore((s) => s.profiles);
  const pointId = useStore((s) => s.freePoint?.data?.point_id);
  // Ojo: no seleccionar un objeto calculado en cada lectura del store (bucle infinito de React).
  const current: MissionWindow | null = mission ?? (info ? { start: info.default_start, days: info.default_days } : null);

  const [baseline, setBaseline] = useState<ScenarioSummary | null>(null);
  const [preview, setPreview] = useState<ScenarioSummary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resultado de la fecha aplicada ahora (para comparar).
  useEffect(() => {
    api.scenario(profile, mission ?? undefined, pointId).then(setBaseline).catch(() => setBaseline(null));
  }, [profile, mission, pointId]);

  // Resultado de la fecha que se está eligiendo (se recalcula al moverla, con un pequeño retardo).
  const draftStart = draft?.start, draftDays = draft?.days;
  // Sin kernels en el servidor solo se puede analizar la fecha por defecto (se deriva, no se guarda en estado).
  const blocked = !!info && !info.live_dates && !(draftStart === info.default_start && draftDays === info.default_days);
  useEffect(() => {
    if (!draftStart || !draftDays || blocked) return;
    const w = { start: draftStart, days: draftDays };
    const t = setTimeout(() => {
      setBusy(true);
      api.scenario(profile, w, pointId)
        .then((r) => { setPreview(r); setError(null); })
        .catch((e) => { setPreview(null); setError((e as Error).message); })
        .finally(() => setBusy(false));
    }, 300);
    return () => clearTimeout(t);
  }, [draftStart, draftDays, profile, pointId, blocked]);

  if (!draft || !info) return null;
  const start = Date.parse(draft.start);
  const end = start + draft.days * DAY;
  const changed = !current || current.start !== draft.start || current.days !== draft.days;
  const before = (id: string) => (changed ? baseline?.sites.find((x) => x.site_id === id) : undefined);
  const shown = blocked ? null : preview;
  const rows = [...(shown?.sites ?? [])].sort((a, b) => (b.score ?? -1) - (a.score ?? -1));
  const best = rows.find((r) => r.site_id === shown?.recommended);
  const profileName = profiles.find((p) => p.id === profile)?.name ?? profile;

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <div className="glass panel-in max-h-[94vh] w-[min(68rem,96vw)] overflow-y-auto p-6 text-base text-slate-200">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-2xl font-semibold text-white">¿Y si aterrizamos en otra fecha?</h2>
          <span className="text-sm text-slate-400">Sol y Tierra recalculados con SPICE · perfil {profileName}</span>
        </div>

        {/* ---------------- controles de fecha */}
        <div className="mt-4 flex flex-wrap items-end gap-4 rounded-xl bg-slate-800/60 p-4">
          <label className="block">
            <span className="text-sm text-slate-400">Fecha de aterrizaje (UTC)</span>
            <input
              type="date"
              value={draft.start.slice(0, 10)}
              min={info.min_start.slice(0, 10)}
              max={info.max_end.slice(0, 10)}
              onChange={(e) => e.target.value && set({ missionDraft: { ...draft, start: `${e.target.value}${draft.start.slice(10)}` } })}
              className="mt-1 block rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-lg text-white"
            />
          </label>
          <div className="flex gap-1.5">
            <button className="rounded-md bg-slate-700 px-3 py-2 hover:bg-slate-600" onClick={() => nudgeMissionDraft(-SYNODIC_MS)} title="−1 mes lunar">◀◀</button>
            <button className="rounded-md bg-slate-700 px-3 py-2 hover:bg-slate-600" onClick={() => nudgeMissionDraft(-DAY)} title="−1 día">◀</button>
            <button className="rounded-md bg-slate-700 px-3 py-2 hover:bg-slate-600" onClick={() => nudgeMissionDraft(DAY)} title="+1 día">▶</button>
            <button className="rounded-md bg-slate-700 px-3 py-2 hover:bg-slate-600" onClick={() => nudgeMissionDraft(SYNODIC_MS)} title="+1 mes lunar">▶▶</button>
          </div>
          <div>
            <span className="text-sm text-slate-400">Analizar durante</span>
            <div className="mt-1 flex gap-1">
              {DURATIONS.map((d) => (
                <button
                  key={d}
                  onClick={() => set({ missionDraft: { ...draft, days: d } })}
                  className={`rounded-md px-2.5 py-2 ${d === draft.days ? "bg-sky-500 font-semibold text-slate-950" : "bg-slate-700 hover:bg-slate-600"}`}
                >
                  {d} d
                </button>
              ))}
            </div>
          </div>
          <button
            className="rounded-md bg-slate-700 px-3 py-2 text-sm hover:bg-slate-600"
            onClick={() => set({ missionDraft: { start: info.default_start, days: info.default_days } })}
          >
            Fecha por defecto
          </button>
        </div>
        <div className="mt-2 text-sm text-slate-400">
          Ventana: <span className="font-mono text-slate-200">{formatUtc(start)} → {formatUtc(end)}</span>
          {" · "}◀◀ ▶▶ = un mes lunar (29,5 d): el Sol vuelve a la misma posición
        </div>

        {/* ---------------- resultado */}
        <div className="mt-5">
          <div className="mb-2 flex flex-wrap items-center gap-3">
            <h3 className="text-lg font-semibold text-sky-300">Resultado para esta fecha</h3>
            {busy && <span className="animate-pulse text-sm text-slate-400">calculando…</span>}
            {changed && baseline && current && (
              <span className="text-sm text-slate-400">▲▼ = diferencia con la fecha que ves ahora ({day(current.start)})</span>
            )}
          </div>

          {blocked && (
            <p className="rounded-lg bg-amber-500/15 p-3 text-amber-300">
              Este servidor no tiene los kernels SPICE: solo se puede analizar la fecha por defecto.
            </p>
          )}
          {!blocked && error && <p className="rounded-lg bg-amber-500/15 p-3 text-amber-300">{error}</p>}

          {best && (
            <p className="mb-3 rounded-lg border border-emerald-400/40 bg-emerald-400/10 p-3 text-lg leading-relaxed">
              Aterrizando el <b className="text-white">{day(start)}</b>, conviene{" "}
              <b className="text-emerald-300">{best.name}</b> ({n1(best.score ?? 0)} pts). Tiene Sol el{" "}
              <b>{n1(best.sun_visible_pct)} %</b> del tiempo
              <Delta now={best.sun_visible_pct} before={before(best.site_id)?.sun_visible_pct} unit=" pts" /> y ve la Tierra el{" "}
              <b>{n1(best.earth_visible_pct)} %</b>.{" "}
              {best.best_window
                ? <>Su mejor ventana con Sol y Tierra empieza el <b>{formatWindowStart(best.best_window.start)}</b> y dura <b>{formatDuration(best.best_window.hours)}</b>. </>
                : <>No tiene ninguna ventana con Sol y Tierra a la vez. </>}
              {best.at_landing.sun_visible
                ? <>Al aterrizar <b className="text-emerald-300">hay Sol</b>{best.at_landing.sun_change_h !== null && <> durante {formatDuration(best.at_landing.sun_change_h)} más</>}.</>
                : <>Al aterrizar <b className="text-rose-300">no hay Sol</b>{best.at_landing.sun_change_h !== null ? <>: sale en {formatDuration(best.at_landing.sun_change_h)}</> : <> en toda la ventana</>}.</>}
            </p>
          )}

          {rows.length > 0 && (
            <table className="w-full border-separate border-spacing-y-1 text-left">
              <thead>
                <tr className="text-sm text-slate-400">
                  <th className="px-2">Sitio</th>
                  <th className="px-2 text-right">Puntuación</th>
                  <th className="px-2 text-right">Sol visible</th>
                  <th className="px-2 text-right">Tierra visible</th>
                  <th className="px-2 text-right">Noche más larga</th>
                  <th className="px-2">Mejor ventana Sol + Tierra</th>
                  <th className="px-2">Al aterrizar</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const b = before(r.site_id);
                  const rec = r.site_id === shown?.recommended;
                  return (
                    <tr key={r.site_id} className={rec ? "bg-emerald-400/10" : "bg-slate-800/60"}>
                      <td className="rounded-l-lg px-2 py-2 font-medium text-white">
                        {rec && <span className="mr-1 text-emerald-300">★</span>}{r.name}
                        {r.quality === "estimated" && <span className="badge-amber ml-2">estimado</span>}
                      </td>
                      <td className="px-2 py-2 text-right text-lg font-bold">{r.score !== null ? n1(r.score) : "—"}<Delta now={r.score} before={b?.score} /></td>
                      <td className="px-2 py-2 text-right">{n1(r.sun_visible_pct)} %<Delta now={r.sun_visible_pct} before={b?.sun_visible_pct} /></td>
                      <td className="px-2 py-2 text-right">{n1(r.earth_visible_pct)} %<Delta now={r.earth_visible_pct} before={b?.earth_visible_pct} /></td>
                      <td className="px-2 py-2 text-right">
                        {formatDuration(r.longest_dark_h)}<Delta now={r.longest_dark_h} before={b?.longest_dark_h} higherIsBetter={false} unit=" h" />
                      </td>
                      <td className="px-2 py-2 text-sm">
                        {r.best_window
                          ? <>{formatWindowStart(r.best_window.start)} · <b>{formatDuration(r.best_window.hours)}</b></>
                          : <span className="text-rose-300">ninguna</span>}
                      </td>
                      <td className="rounded-r-lg px-2 py-2"><Landing s={r} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* ---------------- acciones */}
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            className="rounded-lg bg-sky-500 px-5 py-2.5 font-semibold text-slate-950 disabled:opacity-40"
            disabled={!changed || blocked || !!error}
            onClick={() => void applyMission(draft)}
          >
            Usar esta fecha en el simulador
          </button>
          <button className="rounded-lg bg-slate-700 px-5 py-2.5 text-white" onClick={() => set({ panel: null })}>Cerrar</button>
          {!changed && <span className="text-sm text-slate-400">Es la fecha que ya estás viendo. Muévela para comparar.</span>}
        </div>

        <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 border-t border-slate-700 pt-3 text-sm text-slate-300">
          <span className="flex items-center gap-1.5"><PadButton id="dpad_lr" size={24} /> ±1 día <Kbd>1/2</Kbd></span>
          <span className="flex items-center gap-1.5"><PadButton id="dpad_ud" size={24} /> ±1 mes lunar <Kbd>3/4</Kbd></span>
          <span className="flex items-center gap-1.5"><PadButton id="l1r1" size={24} /> duración <Kbd>Q/E</Kbd></span>
          <span className="flex items-center gap-1.5"><PadButton id="x" size={24} /> usar esta fecha <Kbd>Enter</Kbd></span>
          <span className="flex items-center gap-1.5"><PadButton id="circle" size={24} /> cerrar <Kbd>Esc</Kbd></span>
        </div>
      </div>
    </div>
  );
}
