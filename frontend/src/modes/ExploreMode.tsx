import { useStore } from "../store";
import LayerLegend from "../ui/LayerLegend";
import SitePanel from "../ui/SitePanel";

export default function ExploreMode() {
  const panel = useStore((s) => s.panel);
  const fp = useStore((s) => s.freePoint);
  return (
    <>
      {panel === "data" && <div className="pointer-events-auto absolute right-4 top-2"><SitePanel /></div>}
      <div className="absolute bottom-2 left-4 flex flex-col gap-2">
        <LayerLegend />
        {fp?.status === "loading" && <div className="glass px-3 py-1.5 text-base text-amber-300">Analizando punto… (estimado)</div>}
      </div>
    </>
  );
}
