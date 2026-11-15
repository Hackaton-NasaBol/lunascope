import { useStore, type LayerMeta } from "../store";

function ColorBar({ meta }: { meta: LayerMeta }) {
  const stops = meta.legend;
  const min = stops[0].value, max = stops[stops.length - 1].value;
  const pos = (v: number) => ((v - min) / (max - min)) * 100;
  const gradient = `linear-gradient(to right, ${stops.map((s) => `${s.color} ${pos(s.value)}%`).join(", ")})`;
  const fmt = (v: number) =>
    meta.units === "m"
      ? `${(v / 1000).toLocaleString("es", { maximumFractionDigits: 1, minimumFractionDigits: 1 })} km`
      : `${Math.round(v)}°`;
  // Como mucho 5 marcas, repartidas por el rango, para que no se amontonen.
  const ticks = stops.length <= 5 ? stops.map((s) => s.value) : [0, 0.25, 0.5, 0.75, 1].map((f) => min + f * (max - min));
  return (
    <div>
      <div className="relative h-3 w-full rounded" style={{ background: gradient }}>
        {meta.threshold !== undefined && (
          <div className="absolute -top-1 h-5 w-0.5 bg-white shadow" style={{ left: `${pos(meta.threshold)}%` }} title="Umbral peligroso" />
        )}
      </div>
      <div className="mt-1 flex justify-between font-mono text-xs text-slate-300">
        {ticks.map((v) => <span key={v}>{fmt(v)}</span>)}
      </div>
      {meta.units === "m" && <div className="mt-0.5 flex justify-between text-xs text-slate-400"><span>bajo</span><span>alto</span></div>}
    </div>
  );
}

/** Leyenda de la capa activa (elevación/pendiente) y del estado de las sombras. */
export default function LayerLegend() {
  const layer = useStore((s) => s.layer);
  const metas = useStore((s) => s.layersMeta);
  const shadows = useStore((s) => s.shadows);
  const info = useStore((s) => s.shadowInfo);
  const auto = useStore((s) => s.layerFromShadows);
  const meta = metas.find((m) => m.id === layer);
  if (!meta && !shadows) return null;

  return (
    <div className="glass panel-in w-80 space-y-3 p-4 text-sm text-slate-300">
      {meta && (
        <div>
          <div className="mb-1.5 flex items-baseline justify-between">
            <span className="text-base font-semibold text-white">{meta.name}</span>
            <span className="text-xs">{meta.units === "m" ? "altura sobre la esfera de 1 737,4 km" : "grados"}</span>
          </div>
          <ColorBar meta={meta} />
          {meta.threshold !== undefined && (
            <div className="mt-1 text-xs">Línea blanca: {meta.threshold}° (pendiente peligrosa)</div>
          )}
          <div className="mt-1 text-xs text-slate-400">{meta.source} · {meta.resolution_m.toFixed(0)} m/píxel · {meta.status === "real" ? "dato real" : "simulado"}</div>
        </div>
      )}
      <div className="rounded-md bg-slate-800/70 px-2 py-1.5 text-xs text-slate-300">
        Modo análisis (relieve LOLA). Para volver a la vista normal de la Luna:
        {shadows && <> <b className="text-white">△ / T</b>{auto ? "" : " apaga las sombras"}</>}
        {shadows && meta && !auto && " y"}
        {meta && !(shadows && auto) && <> <b className="text-white">▲▼ / 3·4</b> hasta «sin capa»</>}.
      </div>
      {shadows && (
        <div className={meta ? "border-t border-slate-700 pt-3" : ""}>
          <div className="flex items-center gap-2">
            <span className="inline-block h-4 w-6 rounded-sm border border-slate-500 bg-slate-950/80" />
            <span className="text-base font-semibold text-white">Sombras del relieve</span>
          </div>
          {info.mode === "dem" && (
            <div className="mt-1 text-xs">
              Calculadas con DEM LOLA (80 m) y Sol SPICE{info.sunEl !== undefined && ` · Sol a ${info.sunEl.toFixed(1)}°`}.
              Muestra el suelo en ±35 km del sitio; la visibilidad oficial de la antena (+2 m) es la del gráfico.
            </div>
          )}
          {info.mode === "loading" && <div className="mt-1 text-xs">Calculando sombras…</div>}
          {info.mode === "approx" && (
            <div className="mt-1 text-xs text-amber-300">Sombras visuales aproximadas (terreno Cesium). {info.detail}</div>
          )}
        </div>
      )}
    </div>
  );
}
