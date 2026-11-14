import { useStore } from "../store";

export default function ControllerStatus() {
  const connected = useStore((s) => s.gamepadConnected);
  const standard = useStore((s) => s.gamepadStandard);
  return (
    <div className="glass flex items-center gap-3 px-4 py-2 text-base">
      <svg width="30" height="20" viewBox="0 0 30 20" aria-hidden className={connected ? "text-emerald-400" : "text-slate-500"}>
        <path fill="currentColor" d="M8 1h14c4 0 7 4 8 10s-1 9-4 9c-2 0-3-2-5-4H9c-2 2-3 4-5 4-3 0-5-3-4-9S4 1 8 1Z" />
        <circle cx="8" cy="9" r="2.4" fill="#0f172a" />
        <circle cx="22" cy="9" r="2.4" fill="#0f172a" />
      </svg>
      {connected ? (
        <span className="text-emerald-300">
          Mando conectado{!standard && <span className="text-amber-300"> · mapeo no estándar: usa el teclado</span>}
        </span>
      ) : (
        <span className="animate-pulse text-slate-300">Pulsa cualquier botón del mando</span>
      )}
    </div>
  );
}
