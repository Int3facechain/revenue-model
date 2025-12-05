import {ASSETS, type AssetSymbol, type ExchangeStreamClient, type FundingUpdateHandler,} from "../types";

const LIGHTER_MARKET_BY_ASSET: Partial<Record<AssetSymbol, number>> = {
  ETH: 0,
  BTC: 1,
  SOL: 2,
  DOGE: 3,
  XRP: 7,
  LINK: 8,
  AVAX: 9,
  APT: 31,
  ARB: 50,
  OP: 55,
};

function getAssetByMarketId(marketId: number): AssetSymbol | undefined {
  for (const asset of ASSETS) {
    if (LIGHTER_MARKET_BY_ASSET[asset] === marketId) {
      return asset;
    }
  }
  return undefined;
}

export class LighterClient implements ExchangeStreamClient {
  private ws: WebSocket | null = null;
  private stopped = false;
  private readonly url = "wss://mainnet.zklighter.elliot.ai/stream";
  private readonly onUpdate: FundingUpdateHandler;

  constructor(onUpdate: FundingUpdateHandler) {
    this.onUpdate = onUpdate;
  }

  start(): void {
    const markets = Object.values(LIGHTER_MARKET_BY_ASSET).filter(
      (id): id is number => typeof id === "number"
    );

    if (markets.length === 0) {
      console.warn("[Lighter] markets are not configured, skipping client");
      return;
    }

    this.stopped = false;
    this.connect(markets);
  }

  stop(): void {
    this.stopped = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private connect(markets: number[]): void {
    if (this.stopped) return;

    console.log("[Lighter] connecting to", this.url);
    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.onopen = () => {
      console.log("[Lighter] ws open, subscribing to markets:", markets);
      markets.forEach((marketId) => {
        const payload = {
          type: "subscribe",
          channel: `market_stats/${marketId}`,
        };
        ws.send(JSON.stringify(payload));
      });
    };

    ws.onmessage = (event) => {
      console.log("[Lighter] raw message:", event.data);

      let msg: any;
      try {
        msg = JSON.parse(event.data as string);
      } catch (error) {
        console.error("[Lighter] parse error:", error);
        return;
      }

      if (msg.type !== "update/market_stats" || !msg.market_stats) {
        return;
      }

      const stats = msg.market_stats as {
        market_id: number;
        current_funding_rate?: string;
        funding_rate?: string;
        mark_price?: string;
        index_price?: string;
        // no explicit timestamp in docs, so using Date.now()
      };


      const asset = getAssetByMarketId(stats.market_id);
      if (!asset || !this.isSupportedAsset(asset)) {
        return;
      }

      const src =
        stats.funding_rate ??
        undefined;
      if (!src) {
        return;
      }

      console.log("[LGT] funding raw:", {
        rawCurrent: stats.current_funding_rate,
        rawFunding: stats.funding_rate,
        parsed: Number(src),
      });

      const rate = Number(src);
      if (!Number.isFinite(rate)) {
        return;
      }

      const markPx =
        stats.mark_price != null
          ? Number(stats.mark_price)
          : undefined;
      const indexPx =
        stats.index_price != null
          ? Number(stats.index_price)
          : undefined;

      this.onUpdate({
        exchangeId: "lighter",
        asset,
        rate,
        markPrice: Number.isFinite(markPx as number)
          ? (markPx as number)
          : undefined,
        indexPrice: Number.isFinite(indexPx as number)
          ? (indexPx as number)
          : undefined,
        timestamp: Date.now(),
      });
    };

    ws.onerror = (err) => {
      console.error("[Lighter] ws error:", err);
      ws.close();
    };

    ws.onclose = (ev) => {
      console.warn("[Lighter] ws closed:", ev.code, ev.reason);
      this.ws = null;
      if (!this.stopped) {
        setTimeout(() => this.connect(markets), 5000);
      }
    };
  }

  private isSupportedAsset(asset: string): asset is AssetSymbol {
    return (ASSETS as readonly string[]).includes(asset);
  }
}
