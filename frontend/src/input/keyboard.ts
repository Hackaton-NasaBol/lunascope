import type { Action, Analog } from "./types";

// Equivalencias del contrato: flechas/WASD = joystick izq., Q/E = L1/R1, Z/C = L2/R2, Enter = X,
// Esc = Círculo, I = Cuadrado, T = Triángulo, Tab = Touchpad, M = Options, 1–4 = cruceta.
const KEY_TO_ACTION: Record<string, Action> = {
  q: "l1", e: "r1",
  enter: "x", escape: "circle", i: "square", t: "triangle",
  tab: "touchpad", m: "options", f: "share",
  "1": "dpad_left", "2": "dpad_right", "3": "dpad_up", "4": "dpad_down",
};

export const KEY_LABEL: Partial<Record<Action, string>> = {
  x: "Enter", circle: "Esc", square: "I", triangle: "T", l1: "Q", r1: "E",
  touchpad: "Tab", options: "M", share: "F", dpad_left: "1", dpad_right: "2", dpad_up: "3", dpad_down: "4",
};

const held = new Set<string>();

export function initKeyboard(dispatch: (a: Action) => void) {
  const isTyping = (e: KeyboardEvent) => (e.target as HTMLElement)?.closest?.("input, textarea, select");
  window.addEventListener("keydown", (e) => {
    if (isTyping(e)) return;
    const k = e.key.toLowerCase();
    if (k === "tab" || k.startsWith("arrow") || k === " ") e.preventDefault();
    held.add(k);
    const a = KEY_TO_ACTION[k];
    if (a && !e.repeat) dispatch(a);
  });
  window.addEventListener("keyup", (e) => held.delete(e.key.toLowerCase()));
  window.addEventListener("blur", () => held.clear());
}

export function keyboardAnalog(): Analog {
  const h = (...ks: string[]) => (ks.some((k) => held.has(k)) ? 1 : 0);
  return {
    lx: h("d", "arrowright") - h("a", "arrowleft"),
    ly: h("s", "arrowdown") - h("w", "arrowup"),
    rx: 0, ry: 0,
    l2: h("z"), r2: h("c"),
  };
}
