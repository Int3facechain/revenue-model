import {create} from "zustand";
import type {ArbitrageRow, FundingRates} from "../api/types";

interface ArbitrageStore {
  rates: Record<string, FundingRates>;
  updateRate: (exchange: string, asset: string, rate: number) => void;
  getSpread: (left: string, right: string) => ArbitrageRow[];
}

export const useArbitrageStore = create<ArbitrageStore>((set, get) => ({
  rates: {},

  updateRate(exchange, asset, rate) {
    set((state) => ({
      rates: {
        ...state.rates,
        [asset]: {
          ...state.rates[asset],
          [exchange]: rate,
        },
      },
    }));
  },

  getSpread(left, right) {
    const rates = get().rates;
    const rows: ArbitrageRow[] = [];

    for (const asset in rates) {
      const L = rates[asset][left];
      const R = rates[asset][right];
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
            ? `Long ${right.toUpperCase()} / Short ${left.toUpperCase()}`
            : `Long ${left.toUpperCase()} / Short ${right.toUpperCase()}`,
      });
    }

    return rows.sort((a, b) => b.spread - a.spread);
  },
}));
