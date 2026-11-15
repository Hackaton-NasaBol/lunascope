import { globe } from "../globe/bridge";
import { loadAll, set, useStore } from "../store";

export default function Menu() {
  const s = useStore();
  const restart = () => {
    set({ mode: "explore", panel: null, siteIndex: 0, timeIndex: 0, playing: false, selectionRow: 0 });
    const first = s.sites[0];
    if (first) globe.flyToSite(first.lat, first.lon);
  };
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm">
      <div className="glass panel-in w-[36rem] p-7 text-lg text-slate-200">
        <h2 className="mb-4 text-2xl font-semibold text-white">Menú</h2>
        <p className="mb-3">
          <b>Explore</b> → <b>Mission Time</b> → <b>Mission Selection</b>. El touchpad (Tab) pasa al siguiente modo.
        </p>
        <ul className="mb-5 list-disc space-y-1 pl-6 text-base text-slate-300">
          <li>L1/R1 (Q/E): sitio anterior / siguiente, en todos los modos.</li>
          <li>Mission Time: L2/R2 (Z/C) mueven el tiempo; la presión controla la velocidad.</li>
          <li>Mission Selection: la cruceta (1–4) cambia el perfil; X (Enter) confirma y genera el informe.</li>
          <li>Triángulo (T): sombras del relieve calculadas con el DEM LOLA y el Sol SPICE. Cruceta ↑↓ (3/4): capa de elevación o pendiente.</li>
          <li>La visibilidad oficial de la antena es la de los gráficos (máscara de horizonte LOLA).</li>
        </ul>
        <div className="mb-5 text-sm text-slate-400">
          Globo: {s.globeStatus === "terrain" ? "Cesium Moon Terrain" : s.globeStatus === "ellipsoid" ? "elipsoide liso (sin relieve)" : "cargando"} ·
          Datos: {s.offline ? "demostración (sin API)" : "API LunaScope"}
        </div>
        <div className="flex gap-3">
          <button className="rounded-lg bg-sky-500 px-4 py-2 font-semibold text-slate-950" onClick={restart}>Reiniciar demo</button>
          <button className="rounded-lg bg-slate-700 px-4 py-2 text-white" onClick={() => void loadAll()}>Recargar datos</button>
          <button className="rounded-lg bg-slate-700 px-4 py-2 text-white" onClick={() => set({ panel: null })}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}
