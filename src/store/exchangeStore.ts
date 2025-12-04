import {create} from "zustand";

export interface ExchangePair {
  left: string;
  right: string;
}

interface ExchangeStore {
  pair: ExchangePair;
  setPair: (left: string, right: string) => void;
}

export const useExchangeStore = create<ExchangeStore>((set) => ({
  pair: {left: "hyperliquid", right: "deriv"},

  setPair(left, right) {
    set({pair: {left, right}});
  },
}));
