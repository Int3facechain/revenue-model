import { type ExchangeInfo, EXCHANGES } from "../../../api/exchanges";
import type { ArbitrageRow } from "../../../api/types";
import type { ExchangePair } from "../../../store/exchangeStore";

const COLUMNS =
  "grid grid-cols-[120px_160px_160px_120px_1fr_120px_140px] gap-4 items-center";

/*──────────────────────────────────────────────────────────────
  Helpers
──────────────────────────────────────────────────────────────*/

function getExchangeShort(id: string): string {
  return EXCHANGES.find((e) => e.id === id)?.short ?? id.toUpperCase();
}

function getExchangeColor(id: string): ExchangeInfo["color"] {
  return EXCHANGES.find((e) => e.id === id)?.color ?? "gray";
}

/*──────────────────────────────────────────────────────────────
  Badge
──────────────────────────────────────────────────────────────*/

interface BadgeProps {
  label: string;
  color: ExchangeInfo["color"];
}

function Badge({ label, color }: BadgeProps) {
  const colors: Record<ExchangeInfo["color"], string> = {
    green: "bg-green-600/20 text-green-300 border-green-600/40",
    yellow: "bg-yellow-600/20 text-yellow-300 border-yellow-600/40",
    blue: "bg-blue-600/20 text-blue-300 border-blue-600/40",
    purple: "bg-purple-600/20 text-purple-300 border-purple-600/40",
    gray: "bg-gray-700/40 text-gray-300 border-gray-600",
  };

  return (
    <span
      className={`px-3 py-1 text-xs border rounded-lg flex items-center justify-center ${colors[color]}`}
    >
      {label}
    </span>
  );
}

/*──────────────────────────────────────────────────────────────
  Header
──────────────────────────────────────────────────────────────*/

interface TableHeaderProps {
  pair: ExchangePair;
}

function TableHeader({ pair }: TableHeaderProps) {
  return (
    <div
      className={`${COLUMNS} text-xs uppercase text-gray-400 pb-3 border-b border-gray-700`}
    >
      <span>Asset</span>
      <span>{getExchangeShort(pair.left)} Rate</span>
      <span>{getExchangeShort(pair.right)} Rate</span>
      <span>Spread</span>
      <span>Strategy</span>
      <span>APY</span>
      <span>Actions</span>
    </div>
  );
}

/*──────────────────────────────────────────────────────────────
  Table Row
──────────────────────────────────────────────────────────────*/

interface TableRowProps {
  row: ArbitrageRow;
  pair: ExchangePair;
}

function TableRow({ row, pair }: TableRowProps) {
  const leftShort = getExchangeShort(pair.left);
  const rightShort = getExchangeShort(pair.right);

  const leftColor = getExchangeColor(pair.left);
  const rightColor = getExchangeColor(pair.right);

  return (
    <div
      className={`${COLUMNS} py-3 border-b border-gray-800 hover:bg-gray-800/30 transition`}
    >
      {/* Asset */}
      <span className="font-semibold text-gray-200">{row.asset}</span>

      {/* Left Exchange */}
      <div className="flex items-center gap-2">
        <Badge label={leftShort} color={leftColor} />
        <span className="text-green-300 font-medium">{row.leftRate.toFixed(5)}</span>
      </div>

      {/* Right Exchange */}
      <div className="flex items-center gap-2">
        <Badge label={rightShort} color={rightColor} />
        <span className="text-green-300 font-medium">{row.rightRate.toFixed(5)}</span>
      </div>

      {/* Spread */}
      <span
        className={`w-1/2 px-3 py-1 text-xs border rounded-lg flex items-center justify-center font-medium ${
          row.spread > 0
            ? "text-green-300 bg-green-950 border-green-700/40"
            : "text-red-300 bg-red-950 border-red-700/40"
        }`}
      >
        {row.spread.toFixed(5)}
      </span>

      {/* Strategy */}
      <span className="text-gray-300">{row.strategy}</span>

      {/* APY */}
      <span
        className={`font-semibold ${
          row.apy >= 0 ? "text-green-300" : "text-red-300"
        }`}
      >
        {row.apy.toFixed(2)}%
      </span>

      {/* Actions */}
      <div className="flex gap-2">
        <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm">
          Details
        </button>
        <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-200 text-sm">
          Copy
        </button>
      </div>
    </div>
  );
}

/*──────────────────────────────────────────────────────────────
  Main Table Component
──────────────────────────────────────────────────────────────*/

interface TableProps {
  data: ArbitrageRow[];
  pair: ExchangePair;
}

export default function ArbitrageTable({ data, pair }: TableProps) {
  return (
    <div className="p-6 rounded-xl bg-[#1a1f26] border border-gray-800 mt-8">
      <div className="flex justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-200">
          {getExchangeShort(pair.left)} vs {getExchangeShort(pair.right)} Opportunities
        </h2>

        <div className="flex gap-2">
          <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm">All</button>
          <button className="px-3 py-1 bg-[#1a1f26] hover:bg-gray-800 text-gray-300 rounded-md text-sm">
            Profitable Only
          </button>
          <button className="px-3 py-1 bg-[#1a1f26] hover:bg-gray-800 text-gray-300 rounded-md text-sm">
            High Spread
          </button>
        </div>
      </div>

      <TableHeader pair={pair} />

      {data.map((row) => (
        <TableRow key={row.asset} row={row} pair={pair} />
      ))}
    </div>
  );
}
