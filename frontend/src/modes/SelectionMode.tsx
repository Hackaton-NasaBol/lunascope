import { useStore } from "../store";
import ComparisonTable from "../ui/ComparisonTable";
import ScoreDetail from "../ui/ScoreDetail";

export default function SelectionMode() {
  const panel = useStore((s) => s.panel);
  return (
    <div className="pointer-events-auto absolute inset-0 flex items-start justify-center gap-4 overflow-auto px-4 pt-2">
      <ComparisonTable />
      {panel === "score" && <ScoreDetail />}
    </div>
  );
}
