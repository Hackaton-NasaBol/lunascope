import { useStore, type Mode } from "../store";
import { Kbd, PadButton, type ButtonId } from "./Buttons";

type Entry = [ButtonId, string, string]; // botón, acción, tecla equivalente

const LEGEND: Record<Mode, Entry[]> = {
  explore: [
    ["ls", "Mover", "WASD"], ["rs", "Orbitar", "ratón"], ["l2r2", "Zoom", "Z/C"], ["l1r1", "Sitio", "Q/E"],
    ["x", "Punto libre", "Enter"], ["square", "Datos", "I"], ["triangle", "Sombras", "T"], ["dpad_ud", "Capa", "3/4"],
    ["touchpad", "Siguiente modo", "Tab"],
  ],
  time: [
    ["l2r2", "Tiempo −/+", "Z/C"], ["x", "Pausa / play", "Enter"], ["dpad_lr", "Ventana ant./sig.", "1/2"],
    ["l1r1", "Sitio", "Q/E"], ["rs", "Orbitar", "ratón"], ["square", "Datos", "I"], ["triangle", "Sombras", "T"],
    ["dpad_ud", "Capa", "3/4"], ["touchpad", "Siguiente modo", "Tab"],
  ],
  selection: [
    ["ls", "Filas", "W/S"], ["dpad", "Perfil", "1–4"], ["x", "Confirmar → informe", "Enter"],
    ["square", "Detalle", "I"], ["l1r1", "Sitio", "Q/E"], ["touchpad", "Volver a Explore", "Tab"],
  ],
};

export default function ButtonLegend() {
  const mode = useStore((s) => s.mode);
  const panel = useStore((s) => s.panel);
  const modal = panel === "report" || panel === "menu";
  const entries: Entry[] = modal
    ? [["circle", "Cerrar", "Esc"], ["options", "Menú", "M"]]
    : [...LEGEND[mode], ["circle", panel ? "Cerrar panel" : "Volver", "Esc"], ["options", "Menú", "M"]];
  return (
    <div className="glass pointer-events-auto flex flex-wrap items-center justify-center gap-x-5 gap-y-2 px-5 py-3 print:hidden">
      {entries.map(([id, label, key]) => (
        <div key={id + label} className="flex items-center gap-2 text-base text-slate-200">
          <PadButton id={id} size={30} />
          <span>{label}</span>
          <Kbd>{key}</Kbd>
        </div>
      ))}
    </div>
  );
}
