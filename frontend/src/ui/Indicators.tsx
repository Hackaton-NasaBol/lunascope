import type { BodySample } from "../api/types";
import { nextChangeText, sampleAt } from "../lib/time";
import { activeTimeseries, useStore } from "../store";

function Indicator({ icon, label, b, next }: { icon: string; label: string; b: BodySample; next: { text: string; soon: boolean } }) {
  const visible = b.visible_fraction >= 0.5;
  return (
    <div className={`glass flex items-center gap-2.5 px-3 py-1.5 transition-colors ${visible ? "ring-2 ring-emerald-400/60" : "ring-2 ring-rose-500/50"}`}>
      <span className="text-2xl">{icon}</span>
      <div>
        <div className="text-xs text-slate-400">{label}</div>
        <div className={`text-xl font-bold leading-tight ${visible ? "text-emerald-300" : "text-rose-300"}`}>
          {visible ? "SÍ" : "NO"}
          <span className="ml-2 text-sm font-normal text-slate-300">({Math.round(b.visible_fraction * 100)} % del disco)</span>
        </div>
        <div className={`text-xs ${next.soon ? "font-semibold text-amber-300" : "text-slate-300"}`}>
          {next.soon && "⚠ "}{next.text}
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
    <div className="flex shrink-0 items-center gap-2">
      <Indicator icon="☀" label="Sol visible" b={smp.sun} next={nextChangeText(ts, idx, "sun")} />
      <Indicator icon="🌍" label="Tierra visible" b={smp.earth} next={nextChangeText(ts, idx, "earth")} />
      <div className="glass px-3 py-1.5 text-base text-slate-200">{playing ? "▶ 6 h/s" : "⏸ Pausa"}</div>
    </div>
  );
}
