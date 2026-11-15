import { formatDuration, formatUtc, formatWindowStart } from "../lib/time";
import { activeTimeseries, openMissionPanel, useStore } from "../store";
import { Kbd, PadButton } from "../ui/Buttons";
import Indicators from "../ui/Indicators";
import LayerLegend from "../ui/LayerLegend";
import SitePanel from "../ui/SitePanel";
import TimeChart from "../ui/TimeChart";

const day = (iso: string) => formatUtc(iso).split(" · ")[0];
const n1 = (v: number) => v.toLocaleString("es", { maximumFractionDigits: 1 });

/** Resumen de la ventana analizada para el sitio activo: lo que "devuelve" la fecha elegida. */
function WindowSummary() {
  const ts = useStore((s) => activeTimeseries(s));
  const custom = useStore((s) => s.mission !== null);
  if (!ts) return null;
  const s = ts.summary, w = s.windows[0];
  return (
    <div className="mb-2 flex flex-wrap items-center gap-x-5 gap-y-1 rounded-lg bg-slate-800/70 px-3 py-1.5 text-sm text-slate-300">
      <span className="text-slate-400">
        {custom ? "Fecha elegida" : "Fecha por defecto"}: <b className="text-white">{day(ts.start)} → {day(ts.end)}</b>
      </span>
      <span>☀ Sol <b className="text-white">{n1(s.sun_visible_pct)} %</b></span>
      <span>🌍 Tierra <b className="text-white">{n1(s.earth_visible_pct)} %</b></span>
      <span>Noche más larga <b className="text-white">{formatDuration(s.longest_dark_h)}</b></span>
      <span>
        Mejor ventana:{" "}
        {w ? <b className="text-emerald-300">{formatWindowStart(w.start)} · {formatDuration(w.hours)}</b> : <b className="text-rose-300">ninguna</b>}
      </span>
      <button onClick={openMissionPanel} className="ml-auto flex items-center gap-1.5 rounded-md bg-sky-500/20 px-2 py-0.5 text-sky-200 hover:bg-sky-500/30">
        <PadButton id="share" size={20} /> ¿Otra fecha? <Kbd>F</Kbd>
      </button>
    </div>
  );
}

export default function MissionTimeMode() {
  const panel = useStore((s) => s.panel);
  return (
    <>
      <div className="pointer-events-auto absolute left-4 top-2"><LayerLegend /></div>
      {panel === "data" && <div className="pointer-events-auto absolute bottom-[calc(46vh-4.5rem)] right-4 top-2 flex"><SitePanel /></div>}
      {/* El 46 % inferior de la pantalla (el globo ocupa el 54 % superior) */}
      <div className="pointer-events-auto fixed inset-x-0 bottom-0 flex h-[46%] flex-col border-t border-slate-700/60 bg-slate-950/95 px-4 pb-24 pt-3">
        <WindowSummary />
        <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
          <Indicators />
          <div className="flex items-center gap-4 text-sm text-slate-400">
            <span><span className="mr-1 inline-block h-3 w-5 rounded-sm bg-emerald-400/30 align-middle" />Ventana Sol + Tierra</span>
            <span>Línea punteada = horizonte LOLA en ese azimut</span>
          </div>
        </div>
        <div className="min-h-0 flex-1"><TimeChart /></div>
      </div>
    </>
  );
}
