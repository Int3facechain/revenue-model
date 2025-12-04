import {ASSETS, type AssetSymbol, type ExchangeStreamClient, type FundingUpdateHandler,} from "../types";

// Lighter market_index per asset from explorer.elliot.ai/api/markets
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
      (id): id is number => typeof id === "number",
    );

    if (markets.length === 0) {
      console.warn("Lighter markets are not configured, skipping Lighter client");
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

    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.onopen = () => {
      markets.forEach(marketId => {
        const payload = {
          type: "subscribe",
          channel: `market_stats/${marketId}`,
        };
        ws.send(JSON.stringify(payload));
      });
    };

    ws.onmessage = event => {
      try {
        const msg = JSON.parse(event.data as string);

        if (msg.type !== "update/market_stats" || !msg.market_stats) {
          return;
        }

        const stats = msg.market_stats as {
          market_id: number;
          current_funding_rate?: string;
          funding_rate?: string;
          mark_price?: string;
          index_price?: string;
        };

        const asset = getAssetByMarketId(stats.market_id);
        if (!asset) {
          return;
        }

        const src =
          stats.current_funding_rate ?? stats.funding_rate ?? undefined;
        if (!src) return;

        const rate = Number(src);
        if (!Number.isFinite(rate)) return;

        this.onUpdate({
          exchangeId: "lighter",
          asset,
          rate,
          markPrice: stats.mark_price ? Number(stats.mark_price) : undefined,
          indexPrice: stats.index_price ? Number(stats.index_price) : undefined,
          timestamp: Date.now(),
        });
      } catch (error) {
        console.error("lighter ws parse error", error);
      }
    };

    ws.onclose = () => {
      this.ws = null;
      if (!this.stopped) {
        setTimeout(() => this.connect(markets), 5000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }
}
