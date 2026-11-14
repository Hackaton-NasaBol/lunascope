import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import { useEffect, useRef } from "react";
import { sampleAt } from "../lib/time";
import { activeSite, activeTimeseries, get, set, useStore } from "../store";
import { registerGlobe } from "./bridge";
import { setShadows, setSunLight } from "./lighting";
import { syncMarkers } from "./sites";

const MOON = Cesium.Ellipsoid.MOON;
const MOON_TERRAIN_ASSET = 2684829;
const TOKEN = import.meta.env.VITE_CESIUM_TOKEN as string | undefined;
const MIN_H = 1_500, MAX_H = 3_000_000;

Cesium.Ellipsoid.default = MOON; // ¡antes de crear el viewer!
if (TOKEN) Cesium.Ion.defaultAccessToken = TOKEN;

function initialView(camera: Cesium.Camera) {
  camera.setView({
    destination: Cesium.Cartesian3.fromDegrees(8, -79.5, 260_000, MOON),
    orientation: { heading: Cesium.Math.toRadians(180), pitch: Cesium.Math.toRadians(-45), roll: 0 },
  });
}

export default function Globe() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let destroyed = false;
    let tileset: Cesium.Cesium3DTileset | null = null;
    const viewer = new Cesium.Viewer(ref.current!, {
      globe: new Cesium.Globe(MOON),
      baseLayer: false, baseLayerPicker: false, geocoder: false, timeline: false, animation: false,
      homeButton: false, sceneModePicker: false, navigationHelpButton: false, fullscreenButton: false,
      infoBox: false, selectionIndicator: false, skyAtmosphere: false,
      contextOptions: { webgl: { preserveDrawingBuffer: true } },
    });
    const scene = viewer.scene;
    scene.globe.baseColor = Cesium.Color.fromCssColorString("#9ca3af");
    scene.globe.enableLighting = false; // globo liso de respaldo: sin relieve, la luz solo crea artefactos
    scene.globe.showGroundAtmosphere = false;
    scene.globe.depthTestAgainstTerrain = true;
    if (scene.sun) scene.sun.show = false; // el Sol de Cesium está pensado para la Tierra
    if (scene.moon) scene.moon.show = false;
    scene.backgroundColor = Cesium.Color.fromCssColorString("#020617");
    (viewer.cesiumWidget.creditContainer as HTMLElement).style.display = "none";
    initialView(scene.camera);

    // ---------- terreno Cesium Moon (requiere token e internet)
    if (!TOKEN) {
      set({ globeStatus: "ellipsoid", globeMessage: "Sin token de Cesium ion: globo liso sin relieve (añade VITE_CESIUM_TOKEN en .env.local)." });
    } else {
      Cesium.Cesium3DTileset.fromIonAssetId(MOON_TERRAIN_ASSET)
        .then((ts) => {
          if (destroyed) return;
          tileset = ts;
          scene.primitives.add(ts);
          scene.globe.show = false;
          setShadows(viewer, tileset, get().shadows);
          set({ globeStatus: "terrain", globeMessage: null });
        })
        .catch((e) => {
          console.error(e);
          set({ globeStatus: "ellipsoid", globeMessage: "Sin conexión con Cesium: usa el video de respaldo (se muestra un globo liso)." });
        });
    }

    // ---------- puente para la capa de control
    const pickCartesian = (): Cesium.Cartesian3 | undefined => {
      const c = new Cesium.Cartesian2(scene.canvas.clientWidth / 2, scene.canvas.clientHeight / 2);
      if (tileset && scene.pickPositionSupported) {
        const p = scene.pickPosition(c);
        if (p) return p;
      }
      return scene.camera.pickEllipsoid(c, MOON);
    };

    const unregister = registerGlobe({
      flyToSite(lat, lon, duration = 1.2) {
        const center = Cesium.Cartesian3.fromDegrees(lon, lat, 0, MOON);
        scene.camera.flyToBoundingSphere(new Cesium.BoundingSphere(center, 500), {
          offset: new Cesium.HeadingPitchRange(scene.camera.heading, Cesium.Math.toRadians(-40), 45_000),
          duration,
        });
      },
      pickCenter() {
        const p = pickCartesian();
        if (!p) return null;
        const c = Cesium.Cartographic.fromCartesian(p, MOON);
        return { lat: Cesium.Math.toDegrees(c.latitude), lon: Cesium.Math.toDegrees(c.longitude) };
      },
      move(lx, ly, rx, ry, zoom, dt) {
        const cam = scene.camera;
        const h = Cesium.Cartographic.fromCartesian(cam.position, MOON).height;
        if (lx || ly) {
          const up = MOON.geodeticSurfaceNormal(cam.position, new Cesium.Cartesian3());
          const right = Cesium.Cartesian3.clone(cam.right);
          Cesium.Cartesian3.subtract(right, Cesium.Cartesian3.multiplyByScalar(up, Cesium.Cartesian3.dot(right, up), new Cesium.Cartesian3()), right);
          Cesium.Cartesian3.normalize(right, right);
          const fwd = Cesium.Cartesian3.cross(up, right, new Cesium.Cartesian3());
          const speed = Math.max(h, 5_000) * 0.9 * dt;
          const { heading, pitch, roll } = cam;
          cam.move(fwd, -ly * speed);
          cam.move(right, lx * speed);
          const c = Cesium.Cartographic.fromCartesian(cam.position, MOON);
          cam.setView({ destination: Cesium.Cartesian3.fromRadians(c.longitude, c.latitude, h, MOON), orientation: { heading, pitch, roll } });
        }
        if (rx || ry) {
          const target = pickCartesian();
          if (target) {
            cam.lookAtTransform(Cesium.Transforms.eastNorthUpToFixedFrame(target, MOON));
            cam.rotateRight(rx * 1.5 * dt);
            cam.rotateUp(-ry * 1.0 * dt);
            cam.lookAtTransform(Cesium.Matrix4.IDENTITY);
          }
        }
        if (zoom) {
          const amount = zoom * Math.max(h, 2_000) * 1.2 * dt;
          if ((zoom > 0 && h - amount > MIN_H) || (zoom < 0 && h < MAX_H)) cam.zoomIn(amount);
        }
      },
    });

    // ---------- sincronización con el estado
    const applyState = () => {
      const s = get();
      syncMarkers(viewer, s.sites, s.siteIndex);
      const site = activeSite(s), ts = activeTimeseries(s);
      if (site && ts) {
        const smp = sampleAt(ts, s.timeIndex);
        setSunLight(viewer, site.lat, site.lon, smp.sun.az, smp.sun.el);
      }
      setShadows(viewer, tileset, s.shadows);
      scene.screenSpaceCameraController.enableInputs = !s.gamepadConnected;
    };
    applyState();
    const unsub = useStore.subscribe((s, p) => {
      if (s.sites !== p.sites || s.siteIndex !== p.siteIndex || s.timeIndex !== p.timeIndex ||
          s.shadows !== p.shadows || s.gamepadConnected !== p.gamepadConnected) applyState();
    });

    return () => {
      destroyed = true;
      unsub();
      unregister();
      viewer.destroy();
    };
  }, []);

  return <div ref={ref} className="absolute inset-0" />;
}
