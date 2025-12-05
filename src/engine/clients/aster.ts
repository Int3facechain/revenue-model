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

    console.log("[Aster] connecting to", this.url);
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

    ws.onmessage = (event) => {
      console.log("[Aster] raw message:", event.data);

      let msg: any;
      try {
        msg = JSON.parse(event.data as string);
      } catch (error) {
        console.error("[Aster] parse error:", error);
        return;
      }

      const data = Array.isArray(msg) ? msg : msg?.data;
      if (!Array.isArray(data)) {
        return;
      }

      for (const entry of data) {
        if (!entry || typeof entry.s !== "string") {
          continue;
        }

        const symbol = String(entry.s).toUpperCase();
        const asset = ASTER_ASSET_BY_SYMBOL[symbol];
        if (!asset || !this.isSupportedAsset(asset)) {
          continue;
        }

        const rateStr = entry.r as string | undefined;
        if (!rateStr) continue;

        const rate = Number(rateStr);
        if (!Number.isFinite(rate)) {
          continue;
        }

        const markPriceStr = entry.p as string | undefined;
        const indexPriceStr = entry.i as string | undefined;

        const markPx =
          markPriceStr != null ? Number(markPriceStr) : undefined;
        const indexPx =
          indexPriceStr != null ? Number(indexPriceStr) : undefined;

        const tsRaw = entry.E;
        const ts =
          typeof tsRaw === "number" && Number.isFinite(tsRaw)
            ? tsRaw
            : Date.now();

        this.onUpdate({
          exchangeId: "aster",
          asset,
          rate,
          markPrice: Number.isFinite(markPx as number)
            ? (markPx as number)
            : undefined,
          indexPrice: Number.isFinite(indexPx as number)
            ? (indexPx as number)
            : undefined,
          timestamp: ts,
        });
      }
    };

    ws.onerror = (err) => {
      console.error("[Aster] ws error:", err);
      ws.close();
    };

    ws.onclose = (ev) => {
      console.warn("[Aster] ws closed:", ev.code, ev.reason);
      this.ws = null;
      if (!this.stopped) {
        setTimeout(() => this.connect(), 5000);
      }
    };
  }

  private isSupportedAsset(asset: string): asset is AssetSymbol {
    return (ASSETS as readonly string[]).includes(asset);
  }
}
