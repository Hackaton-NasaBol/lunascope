import { formatUtc, sampleAt } from "../lib/time";
import { activeSite, activeTimeseries, effectiveWindow, MODE_NAMES, MODES, openMissionPanel, useStore } from "../store";
import ControllerStatus from "./ControllerStatus";

export default function TopBar() {
  const s = useStore();
  const site = activeSite(s);
  const ts = activeTimeseries(s);
  const now = ts ? formatUtc(sampleAt(ts, s.timeIndex).ms) : "—";
  const win = effectiveWindow(s);
  const winText = win
    ? `${formatUtc(win.start).split(" · ")[0]} → ${formatUtc(Date.parse(win.start) + win.days * 86_400_000).split(" · ")[0]} (${win.days} d)`
    : "";
  return (
    <div className="flex items-start justify-between gap-4 p-4 print:hidden">
      <div className="glass flex items-center gap-5 px-5 py-3">
        <div>
          <div className="text-sm uppercase tracking-[0.2em] text-sky-300">LunaScope</div>
          <div className="text-3xl font-semibold text-white">{MODE_NAMES[s.mode]}</div>
          <div className="mt-1 flex gap-1.5">
            {MODES.map((m) => (
              <span key={m} className={`h-1.5 w-8 rounded-full transition-colors ${m === s.mode ? "bg-sky-400" : "bg-slate-600"}`} />
            ))}
          </div>
        </div>
        <div className="h-14 w-px bg-slate-600" />
        <div>
          <div className="flex items-center gap-2 text-2xl font-medium text-white">
            {site?.name ?? "Cargando…"}
            {site?.quality === "estimated" && <span className="badge-amber">estimado</span>}
          </div>
          <div className="font-mono text-lg text-slate-300">{now}</div>
          {win && (
            <button
              onClick={openMissionPanel}
              className="mt-1 flex items-center gap-2 rounded-md bg-slate-800/80 px-2 py-0.5 text-sm text-slate-300 hover:bg-slate-700"
              title="Cambiar la fecha de la misión (Share / F)"
            >
              <span>🗓 Misión: {winText}</span>
              <span className={s.mission ? "text-sky-300" : "text-slate-500"}>{s.mission ? "· otra fecha" : "· por defecto"}</span>
            </button>
          )}
        </div>
      </div>
      <div className="flex flex-col items-end gap-2">
        <ControllerStatus />
        {s.offline && <div className="glass px-3 py-1 text-sm text-amber-300">Datos de demostración (sin API)</div>}
        {!s.offline && site?.source === "mock" && (
          <div className="glass px-3 py-1 text-sm text-amber-300">Datos de prueba (mock) del backend</div>
        )}
      </div>
    </div>
  );
}
