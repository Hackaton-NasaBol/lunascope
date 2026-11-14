import type { BodySample } from "../api/types";
import { sampleAt } from "../lib/time";
import { activeTimeseries, useStore } from "../store";

function Indicator({ icon, label, b }: { icon: string; label: string; b: BodySample }) {
  const visible = b.visible_fraction >= 0.5;
  return (
    <div className={`glass flex items-center gap-3 px-4 py-2 transition-colors ${visible ? "ring-2 ring-emerald-400/60" : "ring-2 ring-rose-500/50"}`}>
      <span className="text-3xl">{icon}</span>
      <div>
        <div className="text-sm text-slate-400">{label}</div>
        <div className={`text-2xl font-bold ${visible ? "text-emerald-300" : "text-rose-300"}`}>
          {visible ? "SÍ" : "NO"}
          <span className="ml-2 text-base font-normal text-slate-300">({Math.round(b.visible_fraction * 100)} % del disco)</span>
        </div>
      </div>
    </div>
  );
}

export default function Indicators() {
  const ts = useStore((s) => activeTimeseries(s));
  const idx = useStore((s) => s.timeIndex);
  const playing = useStore((s) => s.playing);
  if (!ts) return null;
  const smp = sampleAt(ts, idx);
  return (
    <div className="flex items-center gap-3">
      <Indicator icon="☀" label="Sol visible" b={smp.sun} />
      <Indicator icon="🌍" label="Tierra visible" b={smp.earth} />
      <div className="glass px-3 py-2 text-lg text-slate-200">{playing ? "▶ 6 h/s" : "⏸ Pausa"}</div>
    </div>
  );
}
