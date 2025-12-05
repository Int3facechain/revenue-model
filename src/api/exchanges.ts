export interface ExchangeInfo {
  id: string;
  label: string;
  short: string;
  color: "green" | "yellow" | "blue" | "purple" | "gray";
}

export const EXCHANGES: ExchangeInfo[] = [
  {id: "hyperliquid", label: "Hyperliquid", short: "HL", color: "green"},
  {id: "lighter", label: "Lighter", short: "LGT", color: "blue"},
  {id: "aster", label: "Aster", short: "AST", color: "purple"},
];
