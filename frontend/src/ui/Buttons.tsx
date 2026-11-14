import type { ReactNode } from "react";

// Iconos de botones del mando PS4 (dibujados, sin marcas comerciales).
const FACE: Record<string, { glyph: string; color: string }> = {
  x: { glyph: "✕", color: "#7dd3fc" },
  circle: { glyph: "○", color: "#fb7185" },
  square: { glyph: "□", color: "#f0abfc" },
  triangle: { glyph: "△", color: "#6ee7b7" },
};

export type ButtonId =
  | "x" | "circle" | "square" | "triangle" | "l1" | "r1" | "l1r1" | "l2" | "r2" | "l2r2"
  | "ls" | "rs" | "dpad" | "dpad_lr" | "touchpad" | "options";

const TEXT: Partial<Record<ButtonId, string>> = {
  l1: "L1", r1: "R1", l1r1: "L1/R1", l2: "L2", r2: "R2", l2r2: "L2/R2",
  ls: "L", rs: "R", dpad: "✚", dpad_lr: "◀▶", touchpad: "TOUCH", options: "OPT",
};

export function PadButton({ id, size = 34 }: { id: ButtonId; size?: number }) {
  const face = FACE[id];
  if (face) {
    return (
      <span
        className="inline-flex shrink-0 items-center justify-center rounded-full border-2 font-bold"
        style={{ width: size, height: size, borderColor: face.color, color: face.color, fontSize: size * 0.5 }}
      >
        {face.glyph}
      </span>
    );
  }
  const round = id === "ls" || id === "rs";
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center border-2 border-slate-400 px-1.5 font-bold text-slate-100 ${round ? "rounded-full" : "rounded-md"}`}
      style={{ minWidth: size, height: size, fontSize: size * 0.38 }}
    >
      {TEXT[id]}
    </span>
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded border border-slate-600 bg-slate-800/80 px-1.5 py-0.5 font-mono text-xs text-slate-300">
      {children}
    </kbd>
  );
}
