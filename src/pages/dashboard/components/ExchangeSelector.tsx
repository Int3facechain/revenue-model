import type {JSX} from "react";
import type {ExchangePair} from "../../../store/exchangeStore";
import {cn} from "../../../utils/cn.ts";
import {EXCHANGES} from "../../../api/exchanges";

interface Props {
  pair: ExchangePair;
  setPair: (left: string, right: string) => void;
}

export default function ExchangeSelector({pair, setPair}: Props) {
  const buttons = EXCHANGES.reduce<JSX.Element[]>((acc, left) => {
    EXCHANGES.forEach((right) => {
      if (right.id === left.id) return;

      const active =
        pair.left === left.id && pair.right === right.id;

      acc.push(
        <button
          key={`${left.id}-${right.id}`}
          onClick={() => setPair(left.id, right.id)}
          className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium transition",
            active
              ? "bg-blue-600 text-white shadow-md"
              : "bg-gray-800 text-gray-300 hover:bg-gray-700"
          )}
        >
          {left.short} <span className="opacity-60">vs</span> {right.short}
        </button>
      );
    });

    return acc;
  }, []);

  return <div className="flex flex-wrap gap-3 mb-6">{buttons}</div>;
}
