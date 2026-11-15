import type { ReactNode } from "react";
import { nextChangeText, sampleAt } from "../lib/time";
import { activeSite, activeTimeseries, useStore } from "../store";

const fmt = (v: number | undefined, d = 1) => (v === undefined ? "—" : v.toLocaleString("es", { maximumFractionDigits: d, minimumFractionDigits: d }));
/** Azimut en [0, 360): evita mostrar "360,0°" al redondear 359,98°. */
const fmtAz = (v: number) => fmt(Math.round(v * 10) / 10 >= 360 ? 0 : v);

function Row({ k, v }: { k: string; v: ReactNode }) {
  return (
    <div className="flex justify-between gap-6 border-b border-slate-700/60 py-1.5 text-lg">
      <span className="text-slate-400">{k}</span>
      <span className="text-right font-medium text-white">{v}</span>
    </div>
  );
}

/** Cuadrado en Explore (datos del sitio) y en Mission Time (datos en el instante actual). */
export default function SitePanel() {
  const s = useStore();
  const site = activeSite(s), ts = activeTimeseries(s);
  if (!site) return null;
  const t = site.terrain, sum = site.summary;
  const smp = s.mode === "time" && ts ? sampleAt(ts, s.timeIndex) : null;
  return (
    <div className="glass panel-in max-h-full w-[26rem] overflow-y-auto p-5">
      <div className="mb-1 flex items-center gap-2 text-2xl font-semibold text-white">
        {site.name} {site.quality === "estimated" && <span className="badge-amber">estimado</span>}
      </div>
      <div className="mb-3 text-base text-slate-400">{site.region}</div>
      {smp ? (
        <>
          <div className="mb-1 text-sm uppercase tracking-wider text-sky-300">En este instante</div>
          <Row k="Sol: azimut / elevación" v={`${fmtAz(smp.sun.az)}° / ${fmt(smp.sun.el, 2)}°`} />
          <Row k="Horizonte en el azimut del Sol" v={`${fmt(smp.sun.horizon_el, 2)}°`} />
          <Row k="Disco solar visible" v={`${fmt(smp.sun.visible_fraction * 100, 0)} %`} />
          <Row k="Próximo cambio del Sol" v={nextChangeText(ts!, s.timeIndex, "sun").text} />
          <Row k="Tierra: azimut / elevación" v={`${fmtAz(smp.earth.az)}° / ${fmt(smp.earth.el, 2)}°`} />
          <Row k="Horizonte en el azimut de la Tierra" v={`${fmt(smp.earth.horizon_el, 2)}°`} />
          <Row k="Disco terrestre visible" v={`${fmt(smp.earth.visible_fraction * 100, 0)} %`} />
          <Row k="Próximo cambio de la Tierra" v={nextChangeText(ts!, s.timeIndex, "earth").text} />
        </>
      ) : (
        <>
          <Row k="Latitud / longitud" v={`${fmt(site.lat, 3)}° / ${fmt(site.lon, 3)}° E`} />
          <Row k="Elevación (LOLA)" v={`${fmt(t?.elevation_m ?? site.elevation_m, 0)} m`} />
          <Row k="Pendiente media / máx." v={`${fmt(t?.slope_deg_mean)}° / ${fmt(t?.slope_deg_max)}°`} />
          <Row k="Zona peligrosa (> 10°)" v={`${fmt(t?.hazard_pct)} %`} />
          <Row k="Sol visible" v={`${fmt(sum?.sun_visible_pct)} %`} />
          <Row k="Tierra visible" v={`${fmt(sum?.earth_visible_pct)} %`} />
          <Row k="Sol y Tierra a la vez" v={`${fmt(sum?.both_visible_pct)} %`} />
          <Row k="Noche más larga" v={`${fmt(sum?.longest_dark_h, 0)} h`} />
        </>
      )}
      <p className="mt-3 text-sm text-slate-400">Visibilidad geométrica (máscara de horizonte LOLA). No garantiza enlace de radio.</p>
    </div>
  );
}
