import {EXCHANGES} from "../../../api/exchanges";
import type {ExchangePair} from "../../../store/exchangeStore";

interface Props {
  pair: ExchangePair;
  setPair: (left: string, right: string) => void;
}

export default function ExchangeSelector({pair, setPair}: Props) {
  return (
    <div className="flex flex-wrap gap-3 mb-6">

      {EXCHANGES.map((left) =>
        EXCHANGES
          .filter((right) => right.id !== left.id)
          .map((right) => {
            const active =
              pair.left === left.id && pair.right === right.id;

            return (
              <button
                key={`${left.id}-${right.id}`}
                onClick={() => setPair(left.id, right.id)}
                className={
                  "px-4 py-2 rounded-lg text-sm font-medium transition " +
                  (active
                    ? "bg-blue-600 text-white shadow-md"
                    : "bg-gray-800 text-gray-300 hover:bg-gray-700")
                }
              >
                {left.short} <span className="opacity-60">vs</span> {right.short}
              </button>
            );
          })
      )}

    </div>
  );
}
