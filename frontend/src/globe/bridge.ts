// Puente entre la capa de control y el viewer de Cesium (lo rellena Globe.tsx al montarse).
export interface GlobeBridge {
  flyToSite: (lat: number, lon: number, duration?: number) => void;
  pickCenter: () => { lat: number; lon: number } | null;
  move: (lx: number, ly: number, rx: number, ry: number, zoom: number, dt: number) => void;
}

const noop: GlobeBridge = { flyToSite: () => {}, pickCenter: () => null, move: () => {} };
export const globe: GlobeBridge = { ...noop };

export function registerGlobe(b: GlobeBridge) {
  Object.assign(globe, b);
  return () => Object.assign(globe, noop);
}
