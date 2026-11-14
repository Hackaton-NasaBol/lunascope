export type Action =
  | "x" | "circle" | "square" | "triangle"
  | "l1" | "r1"
  | "dpad_up" | "dpad_down" | "dpad_left" | "dpad_right"
  | "touchpad" | "options" | "share" | "ps";

export interface Analog {
  lx: number; ly: number; // joystick izquierdo (−1..1, y hacia abajo positivo)
  rx: number; ry: number; // joystick derecho
  l2: number; r2: number; // gatillos 0..1
}

export const ZERO: Analog = { lx: 0, ly: 0, rx: 0, ry: 0, l2: 0, r2: 0 };
