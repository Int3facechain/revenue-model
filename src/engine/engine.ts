import {useArbitrageStore} from "../store/arbitrageStore";
import type {ExchangeStreamClient, FundingUpdateHandler,} from "./types";
import {HyperliquidClient} from "./clients/hyperliquid";
import {AsterClient} from "./clients/aster";
import {LighterClient} from "./clients/lighter";
import {DerivClient} from "./clients/deriv";

let started = false;
let clients: ExchangeStreamClient[] = [];

export function startEngine(): void {
  if (started) return;
  started = true;

  console.log("[engine] starting...");

  const updateRate = useArbitrageStore.getState().updateRate;

  const handler: FundingUpdateHandler = (u) => {
    updateRate(u.exchangeId, u.asset, u.rate);
  };

  clients = [
    new HyperliquidClient(handler),
    new AsterClient(handler),
    new LighterClient(handler),
    new DerivClient(handler),
  ];

  clients.forEach((c) => {
    c.start();
  });
}
