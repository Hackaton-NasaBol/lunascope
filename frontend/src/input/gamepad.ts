import { get, set } from "../store";
import type { Action, Analog } from "./types";
import { ZERO } from "./types";

// Mapeo "standard" de Chrome para el mando PS4. Si tu mando usa otros índices, cámbialos AQUÍ.
export const BUTTON_TO_ACTION: Record<number, Action | undefined> = {
  0: "x", 1: "circle", 2: "square", 3: "triangle",
  4: "l1", 5: "r1",
  // 6 / 7: L2 / R2 se leen como analógicos
  8: "share", 9: "options",
  12: "dpad_up", 13: "dpad_down", 14: "dpad_left", 15: "dpad_right",
  16: "ps", 17: "touchpad",
};

const DEADZONE = 0.15;
let prev: boolean[] = [];

function findPad(): Gamepad | null {
  const pads = navigator.getGamepads ? navigator.getGamepads() : [];
  for (const g of pads) if (g && g.connected) return g;
  return null;
}

export function initGamepad() {
  const update = () => {
    const gp = findPad();
    set({ gamepadConnected: !!gp, gamepadStandard: !gp || gp.mapping === "standard" });
  };
  window.addEventListener("gamepadconnected", update);
  window.addEventListener("gamepaddisconnected", () => { prev = []; update(); });
  update();
}

/** Lee el mando: despacha acciones en el flanco de subida y devuelve los analógicos. */
export function pollGamepad(dispatch: (a: Action) => void): Analog {
  const gp = findPad();
  if (!!gp !== get().gamepadConnected) set({ gamepadConnected: !!gp, gamepadStandard: !gp || gp.mapping === "standard" });
  if (!gp) return ZERO;
  gp.buttons.forEach((b, i) => {
    const action = BUTTON_TO_ACTION[i];
    if (b.pressed && !prev[i] && action) dispatch(action);
  });
  prev = gp.buttons.map((b) => b.pressed);
  const dz = (v = 0) => (Math.abs(v) < DEADZONE ? 0 : v);
  return {
    lx: dz(gp.axes[0]), ly: dz(gp.axes[1]), rx: dz(gp.axes[2]), ry: dz(gp.axes[3]),
    l2: gp.buttons[6]?.value ?? 0, r2: gp.buttons[7]?.value ?? 0,
  };
}

export function rumble() {
  const gp = findPad() as (Gamepad & { vibrationActuator?: { playEffect: (t: string, p: object) => Promise<unknown> } }) | null;
  gp?.vibrationActuator?.playEffect("dual-rumble", { duration: 200, strongMagnitude: 0.6, weakMagnitude: 0.3 }).catch(() => {});
}
