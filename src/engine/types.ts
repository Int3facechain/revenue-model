export const ASSETS = [
  "BTC",
  "ETH",
  "SOL",
  "AVAX",
  "ARB",
  "LINK",
  "XRP",
  "OP",
  "APT",
  "DOGE",
] as const;

export type AssetSymbol = (typeof ASSETS)[number];

export type ExchangeId = "hyperliquid" | "deriv" | "lighter" | "aster";

export interface FundingUpdate {
  exchangeId: ExchangeId;
  asset: AssetSymbol;
  rate: number; // funding rate or synthetic rate
  markPrice?: number;
  indexPrice?: number;
  timestamp: number;
}

export type FundingUpdateHandler = (update: FundingUpdate) => void;

export interface ExchangeStreamClient {
  start(): void;

  stop(): void;
}
