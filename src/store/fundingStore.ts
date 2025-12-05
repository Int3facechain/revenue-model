import { create } from "zustand";
import {
  aggregatedRateSeries, computeFundingViews,
} from "../engine/formula";
import type { FundingUpdate } from "../engine/types";
import type {ArbitrageRow} from "../api/types.ts";

interface Series {
  rates: number[];
  timestamps: number[];
}

interface FundingHistory {
  [exchange: string]: {
    [asset: string]: Series;
  };
}

interface FundingStore {
  history: FundingHistory;
  maxPoints: number;

  updateFunding: (update: FundingUpdate) => void;

  getAggregatedSpread: (
    leftId: string,
    rightId: string,
    windowSize: number
  ) => ArbitrageRow[];
}

export const useFundingStore = create<FundingStore>((set, get) => ({
  history: {},
  maxPoints: 500,

  updateFunding(update) {
    const { exchangeId, asset, rate, timestamp } = update;

    set((state) => {
      const byExchange = state.history[exchangeId] || {};
      const series = byExchange[asset] || {
        rates: [],
        timestamps: [],
      };

      const newRates = [...series.rates, rate];
      const newTimestamps = [...series.timestamps, timestamp];

      const { maxPoints } = state;
      const clippedRates =
        newRates.length > maxPoints
          ? newRates.slice(newRates.length - maxPoints)
          : newRates;
      const clippedTimestamps =
        newTimestamps.length > maxPoints
          ? newTimestamps.slice(newTimestamps.length - maxPoints)
          : newTimestamps;

      return {
        history: {
          ...state.history,
          [exchangeId]: {
            ...byExchange,
            [asset]: {
              rates: clippedRates,
              timestamps: clippedTimestamps,
            },
          },
        },
      };
    });
  },

  getAggregatedSpread(leftId, rightId, windowSize) {
    const { history } = get();

    const left = history[leftId] || {};
    const right = history[rightId] || {};

    const rows: ArbitrageRow[] = [];

    for (const asset of Object.keys(left)) {
      if (!right[asset]) continue;

      const leftSeries = left[asset];
      const rightSeries = right[asset];

      if (
        !leftSeries ||
        !rightSeries ||
        leftSeries.rates.length === 0 ||
        rightSeries.rates.length === 0
      ) {
        continue;
      }

      const leftAgg = aggregatedRateSeries(
        leftSeries.rates,
        windowSize
      );
      const rightAgg = aggregatedRateSeries(
        rightSeries.rates,
        windowSize
      );

      if (leftAgg.length === 0 || rightAgg.length === 0) {
        continue;
      }

      const leftViews = computeFundingViews(leftSeries.rates, 1, windowSize);
      const rightViews = computeFundingViews(rightSeries.rates, 1, windowSize);

      const leftAggRates = leftViews.aggregatedRates;
      const rightAggRates = rightViews.aggregatedRates;

      const lastLeftAgg = leftAggRates[leftAggRates.length - 1];
      const lastRightAgg = rightAggRates[rightAggRates.length - 1];

      const denomLeft = Math.min(windowSize, leftSeries.rates.length);
      const denomRight = Math.min(windowSize, rightSeries.rates.length);

      const leftRate = lastLeftAgg / denomLeft;
      const rightRate = lastRightAgg / denomRight;

      const spread = leftRate - rightRate;
      const apy = spread * 24 * 365 * 100;

      const strategy =
        spread > 0
          ? `Long ${rightId.toUpperCase()} / Short ${leftId.toUpperCase()}`
          : `Long ${leftId.toUpperCase()} / Short ${rightId.toUpperCase()}`;

      rows.push({
        asset,
        leftRate,
        rightRate,
        spread,
        apy,
        strategy,
      });
    }

    return rows.sort((a, b) => b.spread - a.spread);
  },
}));
