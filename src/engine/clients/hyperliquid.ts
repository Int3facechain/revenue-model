import {ASSETS, type AssetSymbol, type ExchangeStreamClient, type FundingUpdateHandler,} from "../types";

export class HyperliquidClient implements ExchangeStreamClient {
  private ws: WebSocket | null = null;
  private stopped = false;
  private readonly url = "wss://api.hyperliquid.xyz/ws";
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

    console.log("[HL] connecting to", this.url);
    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.onopen = () => {
      console.log("[HL] ws open, subscribing to assets:", ASSETS);
      ASSETS.forEach((asset) => {
        const payload = {
          method: "subscribe",
          subscription: {
            type: "activeAssetCtx",
            coin: asset,
          },
        };
        ws.send(JSON.stringify(payload));
      });
    };

    ws.onmessage = (event) => {
      console.log("[HL] raw message:", event.data);

      let msg: any;
      try {
        msg = JSON.parse(event.data as string);
      } catch (error) {
        console.error("[HL] parse error:", error);
        return;
      }

      const channel = String(msg.channel || "");
      if (!channel.startsWith("activeAssetCtx")) {
        return;
      }

      const data = msg.data;
      if (!data) {
        return;
      }

      const coin = data.coin as string | undefined;
      const ctx = data.ctx as
        | { funding?: string; markPx?: string; oraclePx?: string }
        | undefined;

      if (!coin || !ctx) {
        return;
      }

      if (!this.isSupportedAsset(coin)) {
        return;
      }

      const rate = Number(ctx.funding);
      if (!Number.isFinite(rate)) {
        return;
      }

      console.log(`[HL] Funding update ${coin}:`, {
        raw: ctx.funding,
        parsed: rate,
      });

      const markPx =
        ctx.markPx != null ? Number(ctx.markPx) : undefined;
      const oraclePx =
        ctx.oraclePx != null ? Number(ctx.oraclePx) : undefined;

      this.onUpdate({
        exchangeId: "hyperliquid",
        asset: coin as AssetSymbol,
        rate,
        markPrice: Number.isFinite(markPx as number)
          ? (markPx as number)
          : undefined,
        indexPrice: Number.isFinite(oraclePx as number)
          ? (oraclePx as number)
          : undefined,
        timestamp: Date.now(),
      });
    };

    ws.onerror = (err) => {
      console.error("[HL] ws error:", err);
      ws.close();
    };

    ws.onclose = (ev) => {
      console.warn("[HL] ws closed:", ev.code, ev.reason);
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
