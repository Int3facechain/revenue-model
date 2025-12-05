import { create } from "zustand";
import type { ArbitrageRow } from "../api/types";

interface ArbitrageStore {
  rates: Record<string, Record<string, number>>;
  updateRate: (exchange: string, asset: string, rate: number) => void;
  getSpread: (left: string, right: string) => ArbitrageRow[];
}

export const useArbitrageStore = create<ArbitrageStore>((set, get) => ({
  rates: {},

  updateRate(exchange, asset, rate) {
    console.log("[updateRate]", exchange, asset, rate);

    set((state) => {
      const ex = state.rates[exchange] || {};

      return {
        rates: {
          ...state.rates,
          [exchange]: {
            ...ex,
            [asset]: rate,
          },
        },
      };
    });
  },

  getSpread(leftId, rightId) {
    const { rates } = get();

    const left = rates[leftId] || {};
    const right = rates[rightId] || {};

    const rows: ArbitrageRow[] = [];

    for (const asset of Object.keys(left)) {
      const L = left[asset];
      const R = right[asset];

      if (L == null || R == null) continue;

      const spread = L - R;
      const apy = spread * 24 * 365 * 100;

      rows.push({
        asset,
        leftRate: L,
        rightRate: R,
        spread,
        apy,
        strategy:
          spread > 0
            ? `Long ${rightId.toUpperCase()} / Short ${leftId.toUpperCase()}`
            : `Long ${leftId.toUpperCase()} / Short ${rightId.toUpperCase()}`,
      });
    }

    return rows.sort((a, b) => b.spread - a.spread);
  },
}));
