import Plotly from "plotly.js-dist-min";
import { useEffect, useRef } from "react";
import type { Timeseries } from "../api/types";
import { sampleAt } from "../lib/time";
import { activeTimeseries, get, useStore } from "../store";

const SUN = "#facc15", EARTH = "#38bdf8";

function nowShape(ts: Timeseries, idx: number): Partial<Plotly.Shape> {
  const x = new Date(sampleAt(ts, idx).ms).toISOString();
  return { type: "line", xref: "x", yref: "paper", x0: x, x1: x, y0: 0, y1: 1, line: { color: "#f8fafc", width: 2 } };
}

function windowShapes(ts: Timeseries): Partial<Plotly.Shape>[] {
  return ts.summary.windows.map((w) => ({
    type: "rect", xref: "x", yref: "paper", x0: w.start, x1: w.end, y0: 0, y1: 1,
    fillcolor: "rgba(52, 211, 153, 0.14)", line: { width: 0 }, layer: "below",
  }));
}

/** Gráfico temporal del sitio activo. Solo se redibuja al cambiar de sitio; la línea del instante va a ~10 Hz. */
export default function TimeChart() {
  const ref = useRef<HTMLDivElement>(null);
  const ts = useStore((s) => activeTimeseries(s));

  useEffect(() => {
    const el = ref.current;
    if (!el || !ts) return;
    const x = ts.samples.map((p) => p.t);
    const trace = (y: number[], name: string, color: string, dash?: "dot") => ({
      x, y, name, type: "scattergl" as const, mode: "lines" as const,
      line: { color, width: dash ? 1.5 : 2.5, dash: (dash ?? "solid") as Plotly.Dash },
      hovertemplate: "%{y:.2f}°<extra>" + name + "</extra>",
    });
    const data = [
      trace(ts.samples.map((p) => p.sun.el), "Elevación del Sol", SUN),
      trace(ts.samples.map((p) => p.sun.horizon_el), "Horizonte (az. del Sol)", SUN, "dot"),
      trace(ts.samples.map((p) => p.earth.el), "Elevación de la Tierra", EARTH),
      trace(ts.samples.map((p) => p.earth.horizon_el), "Horizonte (az. de la Tierra)", EARTH, "dot"),
    ];
    const layout: Partial<Plotly.Layout> = {
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#cbd5e1", size: 14, family: "Inter, system-ui, sans-serif" },
      margin: { l: 56, r: 16, t: 34, b: 40 },
      xaxis: { type: "date", gridcolor: "#1e293b", tickformat: "%d %b", hoverformat: "%d %b %H:%M UTC" },
      yaxis: { title: { text: "Elevación (°)" }, gridcolor: "#1e293b", zerolinecolor: "#475569" },
      legend: { orientation: "h", x: 0, y: 1.0, yanchor: "bottom", font: { size: 14 } },
      shapes: [...windowShapes(ts), nowShape(ts, get().timeIndex)],
      hovermode: "x unified",
    };
    void Plotly.react(el, data, layout, { displayModeBar: false, responsive: true });

    let last = 0, pending = false;
    const unsub = useStore.subscribe((s, p) => {
      if (s.timeIndex === p.timeIndex || pending) return;
      const wait = Math.max(0, 100 - (performance.now() - last));
      pending = true;
      setTimeout(() => {
        pending = false;
        last = performance.now();
        void Plotly.relayout(el, { shapes: [...windowShapes(ts), nowShape(ts, get().timeIndex)] });
      }, wait);
    });
    return unsub;
  }, [ts]);

  useEffect(() => () => { if (ref.current) Plotly.purge(ref.current); }, []);

  return <div ref={ref} className="h-full w-full" />;
}
