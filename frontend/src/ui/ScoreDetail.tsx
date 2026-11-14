import { useStore } from "../store";

/** Cuadrado en Mission Selection: frases de explanation del sitio seleccionado. */
export default function ScoreDetail() {
  const score = useStore((s) => s.score);
  const rowIdx = useStore((s) => s.selectionRow);
  const sites = useStore((s) => s.sites);
  const row = score?.ranking[rowIdx];
  if (!row) return null;
  const name = sites.find((s) => s.id === row.site_id)?.name ?? row.site_id;
  return (
    <div className="glass panel-in w-[30rem] p-5">
      <div className="text-sm uppercase tracking-wider text-sky-300">Por qué esta puntuación</div>
      <div className="mb-3 text-2xl font-semibold text-white">
        {name} · {row.score.toFixed(1)}
        {row.quality === "estimated" && <span className="badge-amber ml-2">estimado</span>}
      </div>
      <ul className="space-y-2 text-lg text-slate-200">
        {row.explanation.map((e) => (
          <li key={e} className="flex gap-2"><span className="text-sky-400">›</span>{e}</li>
        ))}
      </ul>
    </div>
  );
}
