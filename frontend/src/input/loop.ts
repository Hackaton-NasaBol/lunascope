// Bucle único de requestAnimationFrame: mando + teclado + avance del tiempo.
import { continuous, handle } from "./actions";
import { initGamepad, pollGamepad } from "./gamepad";
import { initKeyboard, keyboardAnalog } from "./keyboard";

const clamp = (v: number) => Math.max(-1, Math.min(1, v));
let started = false;

export function startInput() {
  if (started) return;
  started = true;
  initGamepad();
  initKeyboard(handle);
  let last = performance.now();
  const frame = (now: number) => {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    const g = pollGamepad(handle);
    const k = keyboardAnalog();
    continuous({
      lx: clamp(g.lx + k.lx), ly: clamp(g.ly + k.ly),
      rx: clamp(g.rx + k.rx), ry: clamp(g.ry + k.ry),
      l2: Math.max(g.l2, k.l2), r2: Math.max(g.r2, k.r2),
    }, dt);
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}
