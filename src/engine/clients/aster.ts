import {ASSETS, type AssetSymbol, type ExchangeStreamClient, type FundingUpdateHandler,} from "../types";

const ASTER_SYMBOL_BY_ASSET: Partial<Record<AssetSymbol, string>> = {
  BTC: "BTCUSDT",
  ETH: "ETHUSDT",
  SOL: "SOLUSDT",
  AVAX: "AVAXUSDT",
  ARB: "ARBUSDT",
  LINK: "LINKUSDT",
  XRP: "XRPUSDT",
  OP: "OPUSDT",
  APT: "APTUSDT",
  DOGE: "DOGEUSDT",
};

const ASTER_ASSET_BY_SYMBOL: Record<string, AssetSymbol> = {};
for (const asset of ASSETS) {
  const symbol = ASTER_SYMBOL_BY_ASSET[asset];
  if (symbol) {
    ASTER_ASSET_BY_SYMBOL[symbol.toUpperCase()] = asset;
  }
}

export class AsterClient implements ExchangeStreamClient {
  private ws: WebSocket | null = null;
  private stopped = false;
  private readonly url = "wss://fstream.asterdex.com/stream";

  private readonly onUpdate: FundingUpdateHandler;

  constructor(onUpdate: FundingUpdateHandler) {
    this.onUpdate = onUpdate;
  }

  start(): void {
    this.stopped = false;
    this.connect();
  }

  stop(): void {
    this.stopped = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private connect(): void {
    if (this.stopped) return;

    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.onopen = () => {
      const payload = {
        method: "SUBSCRIBE",
        params: ["!markPrice@arr@1s"],
        id: 1,
      };
      ws.send(JSON.stringify(payload));
    };

    ws.onmessage = event => {
      try {
        const msg = JSON.parse(event.data as string);

        const data = Array.isArray(msg) ? msg : msg.data;
        if (!Array.isArray(data)) {
          return;
        }

        for (const entry of data) {
          if (!entry || typeof entry.s !== "string") continue;

          const symbol = (entry.s as string).toUpperCase();
          const asset = ASTER_ASSET_BY_SYMBOL[symbol];
          if (!asset) continue;

          const rateStr = entry.r as string | undefined;
          if (!rateStr) continue;

          const rate = Number(rateStr);
          if (!Number.isFinite(rate)) continue;

          const markPriceStr = entry.p as string | undefined;
          const indexPriceStr = entry.i as string | undefined;

          this.onUpdate({
            exchangeId: "aster",
            asset,
            rate,
            markPrice: markPriceStr ? Number(markPriceStr) : undefined,
            indexPrice: indexPriceStr ? Number(indexPriceStr) : undefined,
            timestamp: typeof entry.E === "number" ? entry.E : Date.now(),
          });
        }
      } catch (error) {
        console.error("aster ws parse error", error);
      }
    };

    ws.onclose = () => {
      this.ws = null;
      if (!this.stopped) {
        setTimeout(() => this.connect(), 5000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }
}
