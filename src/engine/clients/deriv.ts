// src/engine/clients/derivClient.ts

import {ASSETS, type AssetSymbol, type ExchangeStreamClient, type FundingUpdateHandler,} from "../types";

// NOTE: Deriv has no funding; we treat its rate as 0 baseline.

const DERIV_APP_ID = ""; // TODO: put your Deriv app id here

const DERIV_SYMBOL_BY_ASSET: Partial<Record<AssetSymbol, string>> = {
  BTC: "cryBTCUSD",
  ETH: "cryETHUSD",
  SOL: "crySOLUSD",
  AVAX: "cryAVAXUSD",
  ARB: "cryARBUSD",
  LINK: "cryLINKUSD",
  XRP: "cryXRPUSD",
  OP: "cryOPUSD",
  APT: "cryAPTUSD",
  DOGE: "cryDOGEUSD",
};

function getAssetBySymbol(symbol: string): AssetSymbol | undefined {
  const upper = symbol.toUpperCase();
  for (const asset of ASSETS) {
    const code = DERIV_SYMBOL_BY_ASSET[asset];
    if (code && code.toUpperCase() === upper) {
      return asset;
    }
  }
  return undefined;
}

export class DerivClient implements ExchangeStreamClient {
  private ws: WebSocket | null = null;
  private stopped = false;

  private readonly onUpdate: FundingUpdateHandler;

  constructor(onUpdate: FundingUpdateHandler) {
    this.onUpdate = onUpdate;
  }

  start(): void {
    if (!DERIV_APP_ID) {
      console.warn("DERIV_APP_ID is not set, skipping Deriv client");
      return;
    }

    const assets = ASSETS.filter(a => DERIV_SYMBOL_BY_ASSET[a]);
    if (assets.length === 0) {
      return;
    }

    this.stopped = false;
    this.connect(assets);
  }

  stop(): void {
    this.stopped = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private connect(assets: AssetSymbol[]): void {
    if (this.stopped) return;

    const url = `wss://ws.derivws.com/websockets/v3?app_id=${DERIV_APP_ID}`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => {
      assets.forEach(asset => {
        const symbol = DERIV_SYMBOL_BY_ASSET[asset];
        if (!symbol) return;

        const payload = {
          ticks: symbol,
          subscribe: 1,
        };
        ws.send(JSON.stringify(payload));
      });
    };

    ws.onmessage = event => {
      try {
        const msg = JSON.parse(event.data as string);

        if (msg.msg_type !== "tick" || !msg.tick) {
          return;
        }

        const tick = msg.tick as { symbol: string };
        const asset = getAssetBySymbol(tick.symbol);
        if (!asset) return;

        this.onUpdate({
          exchangeId: "deriv",
          asset,
          rate: 0,
          timestamp: Date.now(),
        });
      } catch (error) {
        console.error("deriv ws parse error", error);
      }
    };

    ws.onclose = () => {
      this.ws = null;
      if (!this.stopped) {
        setTimeout(() => this.connect(assets), 5000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }
}
