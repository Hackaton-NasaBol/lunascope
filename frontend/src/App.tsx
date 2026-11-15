import { useEffect } from "react";
import Globe from "./globe/Globe";
import { startInput } from "./input/loop";
import ExploreMode from "./modes/ExploreMode";
import MissionTimeMode from "./modes/MissionTimeMode";
import SelectionMode from "./modes/SelectionMode";
import { loadAll, loadLayers, useStore } from "./store";
import ButtonLegend from "./ui/ButtonLegend";
import Menu from "./ui/Menu";
import MissionPanel from "./ui/MissionPanel";
import ReportModal from "./ui/ReportModal";
import TopBar from "./ui/TopBar";

export default function App() {
  const mode = useStore((s) => s.mode);
  const panel = useStore((s) => s.panel);
  const loading = useStore((s) => s.loading);
  const toast = useStore((s) => s.toast);
  const globeStatus = useStore((s) => s.globeStatus);
  const globeMessage = useStore((s) => s.globeMessage);

  useEffect(() => {
    void loadAll();
    void loadLayers();
    startInput();
  }, []);

  return (
    <div className="relative h-full w-full select-none overflow-hidden bg-slate-950">
      {/* Globo: pantalla completa; en Mission Time ocupa la mitad superior */}
      <div className="absolute inset-x-0 top-0 transition-[bottom] duration-200" style={{ bottom: mode === "time" ? "50%" : 0 }}>
        <Globe />
        {mode === "explore" && <div className="reticle" />}
      </div>

      <div className="pointer-events-none absolute inset-0 flex flex-col">
        <div className="pointer-events-auto"><TopBar /></div>
        <div className="relative min-h-0 flex-1">
          {mode === "explore" && <ExploreMode />}
          {mode === "time" && <MissionTimeMode />}
          {mode === "selection" && <SelectionMode />}
        </div>
        <div className="flex justify-center p-4"><ButtonLegend /></div>
      </div>

      {(globeStatus === "loading" || loading) && (
        <div className="glass absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 px-6 py-4 text-xl">
          {loading ? "Cargando datos…" : "Cargando globo lunar…"}
        </div>
      )}
      {globeMessage && mode === "explore" && (
        <div className="glass absolute left-4 top-32 max-w-sm px-4 py-2 text-sm text-amber-300 print:hidden">{globeMessage}</div>
      )}
      {toast && (
        <div className="glass panel-in absolute left-1/2 top-28 -translate-x-1/2 px-5 py-3 text-lg text-white print:hidden">{toast}</div>
      )}
      {panel === "menu" && <Menu />}
      {panel === "mission" && <MissionPanel />}
      {panel === "report" && <ReportModal />}
    </div>
  );
}
