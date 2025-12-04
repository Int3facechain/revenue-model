import {create} from "zustand";

export type SortMode = "spread_desc" | "spread_asc";

interface SettingsStore {
  minSpread: number;
  refreshInterval: number;
  sortMode: SortMode;
  setMinSpread: (v: number) => void;
  setRefreshInterval: (v: number) => void;
  setSortMode: (m: SortMode) => void;
}

export const useSettingsStore = create<SettingsStore>((set) => ({
  minSpread: 0.05,
  refreshInterval: 5,
  sortMode: "spread_desc",

  setMinSpread: (v) => set({minSpread: v}),
  setRefreshInterval: (v) => set({refreshInterval: v}),
  setSortMode: (m) => set({sortMode: m}),
}));
