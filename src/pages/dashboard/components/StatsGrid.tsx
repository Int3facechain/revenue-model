import StatCard from "./StatCard";
import type {ArbitrageRow} from "../../../api/types";

interface Props {
  rows: ArbitrageRow[];
}

export default function StatsGrid({rows}: Props) {
  const found = rows.length;

  const avgSpread =
    rows.length > 0
      ? (rows.reduce((s, r) => s + r.spread, 0) / rows.length) * 100
      : 0;

  const maxSpread =
    rows.length > 0
      ? Math.max(...rows.map((r) => r.spread)) * 100
      : 0;

  return (
    <div className="grid grid-cols-4 gap-6 mt-8">
      <StatCard
        label="Opportunities Found"
        value={found.toString()}
        note="Above minimum spread threshold"
      />

      <StatCard
        label="Avg Spread"
        value={avgSpread.toFixed(4) + "%"}
        valueClass="text-green-400"
        note="All active pairs"
      />

      <StatCard
        label="Max Spread"
        value={maxSpread.toFixed(4) + "%"}
        valueClass="text-green-400"
        note="Best opportunity"
      />

      <StatCard
        label="Last Updated"
        value={new Date().toLocaleTimeString()}
        note=""
      />
    </div>
  );
}
