import * as Cesium from "cesium";

/** Coloca la luz de la escena según el azimut/elevación del Sol (SPICE) vistos desde (lat, lon). */
export function setSunLight(viewer: Cesium.Viewer, lat: number, lon: number, azDeg: number, elDeg: number) {
  const ell = Cesium.Ellipsoid.MOON;
  const origin = Cesium.Cartesian3.fromDegrees(lon, lat, 0, ell);
  const enu = Cesium.Transforms.eastNorthUpToFixedFrame(origin, ell);
  const az = Cesium.Math.toRadians(azDeg), el = Cesium.Math.toRadians(elDeg);
  const local = new Cesium.Cartesian3(Math.cos(el) * Math.sin(az), Math.cos(el) * Math.cos(az), Math.sin(el));
  const toSun = Cesium.Matrix4.multiplyByPointAsVector(enu, local, new Cesium.Cartesian3());
  Cesium.Cartesian3.normalize(toSun, toSun);
  viewer.scene.light = new Cesium.DirectionalLight({
    direction: Cesium.Cartesian3.negate(toSun, new Cesium.Cartesian3()), // la luz viaja desde el Sol
    intensity: 2.5,
  });
}

export function setShadows(viewer: Cesium.Viewer, tileset: Cesium.Cesium3DTileset | null, on: boolean) {
  viewer.shadows = on;
  viewer.shadowMap.maximumDistance = 30_000;
  viewer.shadowMap.softShadows = false;
  viewer.shadowMap.darkness = 0.15;
  if (tileset) tileset.shadows = on ? Cesium.ShadowMode.ENABLED : Cesium.ShadowMode.DISABLED;
}
