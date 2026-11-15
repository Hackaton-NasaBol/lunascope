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
    <div className="glass flex min-w-0 flex-1 flex-col justify-center gap-0.5 px-3 py-1.5 text-sm text-slate-300">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5">
        <span className="text-slate-400">
          {custom ? "Fecha elegida" : "Fecha por defecto"}: <b className="text-white">{day(ts.start)} → {day(ts.end)}</b>
        </span>
        <button onClick={openMissionPanel} className="flex items-center gap-1.5 rounded-md bg-sky-500/20 px-2 py-0.5 text-sky-200 hover:bg-sky-500/30">
          <PadButton id="share" size={18} /> ¿Otra fecha? <Kbd>F</Kbd>
        </button>
      </div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5">
        <span>☀ Sol <b className="text-white">{n1(s.sun_visible_pct)} %</b></span>
        <span>🌍 Tierra <b className="text-white">{n1(s.earth_visible_pct)} %</b></span>
        <span>Noche más larga <b className="text-white">{formatDuration(s.longest_dark_h)}</b></span>
        <span>
          Mejor ventana{" "}
          {w ? <b className="text-emerald-300">{formatWindowStart(w.start)} · {formatDuration(w.hours)}</b> : <b className="text-rose-300">ninguna</b>}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-x-4 text-xs text-slate-400">
        <span><span className="mr-1 inline-block h-2.5 w-4 rounded-sm bg-emerald-400/30 align-middle" />banda verde = ventana Sol + Tierra</span>
        <span>línea punteada = horizonte LOLA en ese azimut</span>
      </div>
    </div>
  );
}

export default function MissionTimeMode() {
  const panel = useStore((s) => s.panel);
  return (
    <>
      <div className="pointer-events-auto absolute left-4 top-2"><LayerLegend /></div>
      {panel === "data" && (
        // Altura máxima = la parte visible del globo; si no cabe, se desplaza en vez de cortarse.
        <div className="pointer-events-auto absolute right-4 top-2 flex max-h-[calc(50vh-10.5rem)]"><SitePanel /></div>
      )}
      {/* Mitad inferior: resumen + indicadores en una fila y el gráfico con todo el espacio restante.
          Se reserva justo la altura real de la leyenda de botones (--legend-h, la mide ButtonLegend). */}
      <div
        className="pointer-events-auto fixed inset-x-0 bottom-0 flex h-[50%] flex-col gap-2 border-t border-slate-700/60 bg-slate-950/95 px-4 pt-2"
        style={{ paddingBottom: "calc(var(--legend-h, 5rem) + 1.5rem)" }}
      >
        <div className="flex items-stretch gap-2">
          <Indicators />
          <WindowSummary />
        </div>
        <div className="min-h-[140px] flex-1"><TimeChart /></div>
      </div>
    </>
  );
}
