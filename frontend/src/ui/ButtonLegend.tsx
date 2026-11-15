import { useEffect, useRef } from "react";
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

/** Publica la altura real de la leyenda en la variable CSS --legend-h (la usa Mission Time para no taparse). */
function useLegendHeight() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      document.documentElement.style.setProperty("--legend-h", `${Math.ceil(el.getBoundingClientRect().height)}px`);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return ref;
}

export default function ButtonLegend() {
  const ref = useLegendHeight();
  const mode = useStore((s) => s.mode);
  const panel = useStore((s) => s.panel);
  const modal = panel === "report" || panel === "menu" || panel === "mission";
  const entries: Entry[] = modal
    ? [["circle", "Cerrar", "Esc"], ["options", "Menú", "M"]]
    : [...LEGEND[mode], ["share", "Fecha", "F"], ["circle", panel ? "Cerrar panel" : "Volver", "Esc"], ["options", "Menú", "M"]];
  // En Mission Time la leyenda es compacta para dejar sitio al gráfico.
  const compact = mode === "time";
  return (
    <div
      ref={ref}
      className={`glass pointer-events-auto flex flex-wrap items-center justify-center print:hidden ${compact ? "gap-x-3.5 gap-y-1 px-3 py-1.5" : "gap-x-5 gap-y-2 px-5 py-3"}`}
    >
      {entries.map(([id, label, key]) => (
        <div key={id + label} className={`flex items-center gap-1.5 text-slate-200 ${compact ? "text-sm" : "text-base"}`}>
          <PadButton id={id} size={compact ? 24 : 30} />
          <span>{label}</span>
          <Kbd>{key}</Kbd>
        </div>
      ))}
    </div>
  );
}
