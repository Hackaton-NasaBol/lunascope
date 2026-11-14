import { useLayoutEffect, useRef } from "react";
import { useStore } from "../store";

const COLS = [
  ["sun", "Sol"], ["earth", "Tierra"], ["continuity", "Continuidad"], ["terrain", "Terreno"],
] as const;

/** Tabla de comparación. Al cambiar de perfil, las filas se reordenan con una animación FLIP corta. */
export default function ComparisonTable() {
  const score = useStore((s) => s.score);
  const profiles = useStore((s) => s.profiles);
  const profile = useStore((s) => s.profile);
  const row = useStore((s) => s.selectionRow);
  const sites = useStore((s) => s.sites);
  const rowsRef = useRef(new Map<string, HTMLTableRowElement>());
  const prevTop = useRef(new Map<string, number>());

  useLayoutEffect(() => {
    rowsRef.current.forEach((el, id) => {
      const top = el.getBoundingClientRect().top;
      const before = prevTop.current.get(id);
      if (before !== undefined && before !== top) {
        el.animate([{ transform: `translateY(${before - top}px)` }, { transform: "translateY(0)" }],
          { duration: 250, easing: "cubic-bezier(.2,.8,.2,1)" });
      }
      prevTop.current.set(id, top);
    });
  }, [score]);

  const p = profiles.find((x) => x.id === profile);
  const name = (id: string) => sites.find((s) => s.id === id)?.name ?? id;

  return (
    <div className="glass panel-in w-[min(64rem,94vw)] p-5">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="mr-2 text-lg text-slate-400">Perfil de misión</span>
        {profiles.map((x) => (
          <span
            key={x.id}
            className={`rounded-full px-4 py-1.5 text-lg transition-colors ${x.id === profile ? "bg-sky-500 text-slate-950 font-semibold" : "bg-slate-800 text-slate-300"}`}
          >
            {x.name}
          </span>
        ))}
      </div>
      {p && (
        <div className="mb-3 text-base text-slate-400">
          Pesos: {COLS.map(([k, l]) => `${l} ${Math.round(p.weights[k] * 100)} %`).join(" · ")}
        </div>
      )}
      <table className="w-full border-separate border-spacing-y-1.5 text-left text-xl">
        <thead>
          <tr className="text-base text-slate-400">
            <th className="px-3">#</th><th className="px-3">Sitio</th><th className="px-3 text-right">Puntuación</th>
            {COLS.map(([k, l]) => <th key={k} className="px-3 text-right">{l}</th>)}
          </tr>
        </thead>
        <tbody>
          {score?.ranking.map((r, i) => {
            const rec = r.site_id === score.recommended;
            const sel = i === row;
            return (
              <tr
                key={r.site_id}
                ref={(el) => { if (el) rowsRef.current.set(r.site_id, el); else rowsRef.current.delete(r.site_id); }}
                className={`transition-colors ${sel ? "bg-sky-500/25 outline-2 outline-sky-400" : "bg-slate-800/60"}`}
              >
                <td className="rounded-l-lg px-3 py-2.5 text-slate-400">{i + 1}</td>
                <td className="px-3 py-2.5 font-medium text-white">
                  {name(r.site_id)}
                  {rec && <span className="ml-2 rounded bg-emerald-400 px-2 py-0.5 text-sm font-bold text-slate-950">RECOMENDADO</span>}
                  {r.quality === "estimated" && <span className="badge-amber ml-2">estimado</span>}
                </td>
                <td className={`px-3 py-2.5 text-right text-2xl font-bold ${rec ? "text-emerald-300" : "text-white"}`}>{r.score.toFixed(1)}</td>
                {COLS.map(([k]) => (
                  <td key={k} className="px-3 py-2.5 text-right text-slate-200 last:rounded-r-lg">
                    <div>{r.breakdown[k].toFixed(0)}</div>
                    <div className="ml-auto mt-1 h-1.5 w-16 rounded-full bg-slate-700">
                      <div className="h-full rounded-full bg-sky-400" style={{ width: `${Math.min(100, r.breakdown[k])}%` }} />
                    </div>
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
      {score?.notes.map((n) => <p key={n} className="mt-3 text-base text-amber-300">{n}</p>)}
      <p className="mt-3 text-sm text-slate-400">Motor de decisión explicable: puntuación = Σ peso × subpuntuación (0–100).</p>
    </div>
  );
}
