export interface FundingRates {
  [exchangeId: string]: number | undefined;
}

export interface ArbitrageRow {
  asset: string;
  leftRate: number;
  rightRate: number;
  spread: number;
  apy: number;
  strategy: string;
}
