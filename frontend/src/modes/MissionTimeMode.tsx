import { useStore } from "../store";
import Indicators from "../ui/Indicators";
import LayerLegend from "../ui/LayerLegend";
import SitePanel from "../ui/SitePanel";
import TimeChart from "../ui/TimeChart";

export default function MissionTimeMode() {
  const panel = useStore((s) => s.panel);
  return (
    <>
      <div className="pointer-events-auto absolute left-4 top-2"><LayerLegend /></div>
      {panel === "data" && <div className="pointer-events-auto absolute bottom-[calc(40vh-4.5rem)] right-4 top-2 flex"><SitePanel /></div>}
      {/* El 40 % inferior de la pantalla (el globo ocupa el 60 % superior) */}
      <div className="pointer-events-auto fixed inset-x-0 bottom-0 flex h-[40%] flex-col border-t border-slate-700/60 bg-slate-950/95 px-4 pb-24 pt-3">
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
