import { formatUtc } from "../lib/time";
import { set, useStore } from "../store";

const LABELS = { sun: "Sol", earth: "Tierra", continuity: "Continuidad", terrain: "Terreno" } as const;

export default function ReportModal() {
  const report = useStore((s) => s.report);
  const sites = useStore((s) => s.sites);
  const name = (id: string) => sites.find((x) => x.id === id)?.name ?? id;

  return (
    <div className="report-backdrop fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-6 backdrop-blur-sm">
      <div className="report glass panel-in max-h-[88vh] w-[min(56rem,96vw)] overflow-y-auto p-8 text-lg">
        {!report ? (
          <div className="py-16 text-center text-2xl text-slate-300">Generando informe…</div>
        ) : (
          <>
            <div className="mb-1 text-sm uppercase tracking-[0.2em] text-sky-300">Informe de misión · LunaScope</div>
            <h1 className="text-3xl font-semibold text-white">{report.title}</h1>
            <div className="mt-1 text-base text-slate-400">Generado: {formatUtc(report.generated_at)} · Perfil: {report.profile.name}</div>
            {report.mission_window && (
              <div className="text-base text-slate-300">
                Ventana analizada: {formatUtc(report.mission_window.start)} → {formatUtc(report.mission_window.end)}
              </div>
            )}
            {report.quality === "estimated" && (
              <p className="mt-2 text-amber-300">Punto libre: análisis estimado (horizonte de menor alcance y resolución).</p>
            )}

            <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
              <Stat k="Puntuación" v={report.score.toFixed(1)} big />
              <Stat k="Puesto" v={`${report.rank} de ${report.comparison.length}`} big />
              <Stat k="Lat / lon" v={`${report.site.lat.toFixed(3)}° / ${report.site.lon.toFixed(3)}° E`} />
              <Stat k="Elevación (LOLA)" v={`${Math.round(report.site.elevation_m)} m`} />
            </div>

            <Section title="Desglose">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                {(Object.keys(LABELS) as (keyof typeof LABELS)[]).map((k) => (
                  <Stat key={k} k={`${LABELS[k]} (peso ${Math.round(report.profile.weights[k] * 100)} %)`} v={report.breakdown[k].toFixed(1)} />
                ))}
              </div>
            </Section>

            <Section title="Mejor ventana con Sol y Tierra a la vez">
              {report.best_window
                ? <p>{formatUtc(report.best_window.start)} → {formatUtc(report.best_window.end)} · <b>{report.best_window.hours} h</b></p>
                : <p>No hay ventanas con Sol y Tierra visibles a la vez.</p>}
            </Section>

            <Section title="Explicación">
              <ul className="list-disc space-y-1 pl-6">{report.explanation.map((e) => <li key={e}>{e}</li>)}</ul>
            </Section>

            <Section title="Comparación">
              <table className="w-full text-left">
                <tbody>
                  {report.comparison.map((c, i) => (
                    <tr key={c.site_id} className={c.site_id === report.site.id ? "font-semibold text-sky-300" : ""}>
                      <td className="py-1 pr-4">{i + 1}.</td><td className="py-1 pr-4">{name(c.site_id)}</td><td className="py-1 text-right">{c.score.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>

            <Section title="Fuentes de datos">
              <ul className="list-disc pl-6">{report.data_sources.map((d) => <li key={d}>{d}</li>)}</ul>
            </Section>
            <Section title="Limitaciones">
              <ul className="list-disc pl-6 text-slate-300">{report.limitations.map((d) => <li key={d}>{d}</li>)}</ul>
            </Section>

            <div className="mt-8 flex gap-3 print:hidden">
              <button className="rounded-lg bg-sky-500 px-5 py-2.5 font-semibold text-slate-950 hover:bg-sky-400" onClick={() => window.print()}>
                Imprimir / PDF
              </button>
              <button className="rounded-lg bg-slate-700 px-5 py-2.5 text-white hover:bg-slate-600" onClick={() => set({ panel: null })}>
                Cerrar (○ / Esc)
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Stat({ k, v, big }: { k: string; v: string; big?: boolean }) {
  return (
    <div className="rounded-lg bg-slate-800/70 p-3">
      <div className="text-sm text-slate-400">{k}</div>
      <div className={big ? "text-3xl font-bold text-white" : "text-xl font-medium text-white"}>{v}</div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-6 break-inside-avoid">
      <h2 className="mb-2 text-xl font-semibold text-sky-300">{title}</h2>
      <div className="text-slate-200">{children}</div>
    </section>
  );
}
