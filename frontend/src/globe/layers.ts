// Capas sobre el terreno: elevación y pendiente (imágenes fijas del DEM LOLA) y sombras del
// relieve calculadas en el backend (DEM LOLA + Sol SPICE) para el sitio y el instante activos.
import * as Cesium from "cesium";
import { API_BASE } from "../api/client";
import { sampleAt } from "../lib/time";
import { activeSite, activeTimeseries, get, set, type LayerId, type State } from "../store";
import { setShadows } from "./lighting";

type Target = Cesium.ImageryLayerCollection;

interface ShadowMeta {
  rectangle: { west: number; south: number; east: number; north: number };
}

const HOUR = 3600_000;

export class LayerManager {
  private target: Target | null = null;
  private staticLayers = new Map<LayerId, Cesium.ImageryLayer>();
  private baseLayer: Cesium.ImageryLayer | null = null;
  private baseLoading = false;
  private staticLoading = new Set<string>();
  private shadowLayer: Cesium.ImageryLayer | null = null;
  private shadowObjectUrl: string | null = null;
  private shadowKey = "";
  private shadowSeq = 0;
  private inFlight = false;
  private pending: { siteId: string; t: string } | null = null;
  private shadowTimer: ReturnType<typeof setTimeout> | undefined;
  private metaCache = new Map<string, Promise<ShadowMeta | null>>();
  private demUnavailable = false;
  private viewer: Cesium.Viewer;
  private tileset: () => Cesium.Cesium3DTileset | null;

  constructor(viewer: Cesium.Viewer, tileset: () => Cesium.Cesium3DTileset | null) {
    this.viewer = viewer;
    this.tileset = tileset;
  }

  /** Dónde se pintan las capas: sobre el terreno 3D (Moon Terrain) o sobre el globo liso de respaldo. */
  setTarget(target: Target) {
    if (this.target === target) return;
    this.clear();
    this.target = target;
    this.sync(get());
  }

  sync(s: State) {
    if (!this.target) return;
    this.syncStatic(s);
    this.syncShadows(s);
  }

  // ---------------------------------------------------------------- capas fijas
  private syncStatic(s: State) {
    if (s.layersBase && !this.baseLayer && !this.baseLoading) {
      this.baseLoading = true;
      const target = this.target!;
      const r = s.layersBase.rectangle;
      Cesium.SingleTileImageryProvider.fromUrl(s.layersBase.url, { rectangle: Cesium.Rectangle.fromDegrees(r.west, r.south, r.east, r.north) })
        .then((provider) => {
          if (this.target !== target) return;
          this.baseLayer = new Cesium.ImageryLayer(provider);
          target.add(this.baseLayer);
          target.lowerToBottom(this.baseLayer);
          target.raise(this.baseLayer); // justo encima de la textura global LRO
        })
        .catch((e) => console.warn("No se pudo cargar el relieve sombreado:", e))
        .finally(() => (this.baseLoading = false));
    }
    for (const meta of s.layersMeta) {
      const want = s.layer === meta.id;
      const existing = this.staticLayers.get(meta.id);
      if (existing) {
        existing.show = want;
        continue;
      }
      if (!want || this.staticLoading.has(meta.id)) continue;
      this.staticLoading.add(meta.id);
      const target = this.target!;
      const r = meta.rectangle;
      Cesium.SingleTileImageryProvider.fromUrl(meta.url, { rectangle: Cesium.Rectangle.fromDegrees(r.west, r.south, r.east, r.north) })
        .then((provider) => {
          if (this.target !== target) return;
          const layer = new Cesium.ImageryLayer(provider, { alpha: 0.85 });
          target.add(layer);
          this.staticLayers.set(meta.id, layer);
          layer.show = get().layer === meta.id;
          this.raiseShadow();
        })
        .catch((e) => console.warn(`No se pudo cargar la capa ${meta.id}:`, e))
        .finally(() => this.staticLoading.delete(meta.id));
    }
  }

  // ---------------------------------------------------------------- sombras
  private syncShadows(s: State) {
    const site = activeSite(s), ts = activeTimeseries(s);
    if (!s.shadows || !site || !ts) {
      this.removeShadow();
      setShadows(this.viewer, this.tileset(), false);
      if (s.shadowInfo.mode !== "off") set({ shadowInfo: { mode: "off" } });
      return;
    }
    if (s.offline || this.demUnavailable) return this.useApproxShadows();

    // Instante redondeado a la hora: el Sol se mueve ~0,5°/h y así se reutiliza la caché.
    const t = new Date(Math.round(sampleAt(ts, s.timeIndex).ms / HOUR) * HOUR).toISOString().replace(/\.\d+Z$/, "Z");
    const key = `${site.id}|${t}`;
    if (key === this.shadowKey) return;
    this.shadowKey = key;
    this.pending = { siteId: site.id, t };
    clearTimeout(this.shadowTimer);
    this.shadowTimer = setTimeout(() => this.pump(), 80);
  }

  /** Una sola petición en curso: al moverse rápido por el tiempo se salta a la última hora pedida. */
  private pump() {
    if (this.inFlight || !this.pending) return;
    const { siteId, t } = this.pending;
    this.pending = null;
    this.inFlight = true;
    void this.loadShadow(siteId, t).finally(() => {
      this.inFlight = false;
      this.pump();
    });
  }

  private meta(siteId: string): Promise<ShadowMeta | null> {
    let p = this.metaCache.get(siteId);
    if (!p) {
      p = fetch(`${API_BASE}/illumination/${encodeURIComponent(siteId)}/meta`)
        .then(async (r) => {
          if (r.ok) return (await r.json()) as ShadowMeta;
          if (r.status === 503) this.demUnavailable = true; // el backend no tiene el DEM
          return null;
        })
        .catch(() => null);
      this.metaCache.set(siteId, p);
    }
    return p;
  }

  private async loadShadow(siteId: string, t: string) {
    const seq = ++this.shadowSeq;
    const target = this.target!;
    if (get().shadowInfo.mode !== "dem") set({ shadowInfo: { mode: "loading" } });
    const meta = await this.meta(siteId);
    if (!meta) return this.useApproxShadows();
    try {
      const res = await fetch(`${API_BASE}/illumination/${encodeURIComponent(siteId)}.png?t=${encodeURIComponent(t)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const url = URL.createObjectURL(await res.blob());
      const r = meta.rectangle;
      const provider = await Cesium.SingleTileImageryProvider.fromUrl(url, {
        rectangle: Cesium.Rectangle.fromDegrees(r.west, r.south, r.east, r.north),
      });
      // Un fotograma intermedio también vale (está más cerca que el anterior); solo se descarta si
      // cambió el sitio, se apagaron las sombras o hay uno más nuevo ya pintado.
      if (seq !== this.shadowSeq || this.target !== target || !this.shadowKey.startsWith(`${siteId}|`) || !get().shadows) {
        URL.revokeObjectURL(url);
        return;
      }
      const layer = new Cesium.ImageryLayer(provider);
      target.add(layer); // la nueva encima; la vieja se quita después: sin parpadeo
      this.removeShadow();
      this.shadowLayer = layer;
      this.shadowObjectUrl = url;
      setShadows(this.viewer, this.tileset(), false);
      const lit = res.headers.get("X-Site-Lit-Fraction");
      set({
        shadowInfo: {
          mode: "dem",
          siteLitFraction: lit === null || lit === "" ? null : Number(lit),
          sunEl: Number(res.headers.get("X-Sun-El")),
        },
      });
    } catch (e) {
      console.warn("Sombras del DEM no disponibles:", e);
      this.useApproxShadows();
    }
  }

  private useApproxShadows() {
    this.removeShadow();
    setShadows(this.viewer, this.tileset(), true);
    if (get().shadowInfo.mode !== "approx") {
      set({ shadowInfo: { mode: "approx", detail: "El backend no tiene el DEM LOLA: sombras visuales de Cesium." } });
    }
  }

  private raiseShadow() {
    if (this.shadowLayer && this.target?.contains(this.shadowLayer)) this.target.raiseToTop(this.shadowLayer);
  }

  private removeShadow() {
    if (this.shadowLayer && this.target?.contains(this.shadowLayer)) this.target.remove(this.shadowLayer, true);
    this.shadowLayer = null;
    if (this.shadowObjectUrl) URL.revokeObjectURL(this.shadowObjectUrl);
    this.shadowObjectUrl = null;
  }

  clear() {
    this.removeShadow();
    this.shadowKey = "";
    for (const l of this.staticLayers.values()) if (this.target?.contains(l)) this.target.remove(l, true);
    this.staticLayers.clear();
  }
}
