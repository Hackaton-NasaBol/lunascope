import * as Cesium from "cesium";
import type { SiteOverview } from "../api/types";

const COLORS = {
  site: Cesium.Color.fromCssColorString("#cbd5e1"),
  active: Cesium.Color.fromCssColorString("#38bdf8"),
  point: Cesium.Color.fromCssColorString("#f59e0b"),
};

/**
 * Marcadores de los sitios. Solo se usa lat/lon: la altura la pone Cesium (CLAMP_TO_GROUND),
 * nunca elevation_m del backend (Cesium Moon y LOLA difieren ~2,5 km).
 */
export function syncMarkers(viewer: Cesium.Viewer, sites: SiteOverview[], activeIndex: number) {
  const wanted = new Set(sites.map((s) => `site:${s.id}`));
  for (const e of [...viewer.entities.values]) {
    if (e.id.startsWith("site:") && !wanted.has(e.id)) viewer.entities.remove(e);
  }
  sites.forEach((s, i) => {
    const active = i === activeIndex;
    const estimated = s.quality === "estimated";
    const color = estimated ? COLORS.point : active ? COLORS.active : COLORS.site;
    const id = `site:${s.id}`;
    const text = estimated ? `${s.name}\n(estimado)` : s.name;
    let e = viewer.entities.getById(id);
    if (!e) {
      e = viewer.entities.add({
        id,
        position: Cesium.Cartesian3.fromDegrees(s.lon, s.lat, 0, Cesium.Ellipsoid.MOON),
        point: {
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 2,
        },
        label: {
          heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          font: "600 18px Inter, system-ui, sans-serif",
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 4,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          pixelOffset: new Cesium.Cartesian2(0, -18),
        },
      });
    }
    e.point!.pixelSize = new Cesium.ConstantProperty(active ? 22 : 14);
    e.point!.color = new Cesium.ConstantProperty(color);
    e.label!.text = new Cesium.ConstantProperty(text);
    e.label!.fillColor = new Cesium.ConstantProperty(color);
    e.label!.scale = new Cesium.ConstantProperty(active ? 1.15 : 0.9);
  });
}
