import {useArbitrageStore} from "../store/arbitrageStore";
import {EXCHANGES} from "../api/exchanges";

let started = false;

const ASSETS = [
  "BTC", "ETH", "SOL", "AVAX", "ARB",
  "LINK", "XRP", "OP", "APT", "DOGE"
];

function randomRate(): number {
  return Math.random() * 0.0006 - 0.0003;
}

export function startEngineMock(): void {
  if (started) return;
  started = true;

  const update = useArbitrageStore.getState().updateRate;

  console.log("⚡ Mock arbitrage engine started");

  setInterval(() => {
    ASSETS.forEach((asset) => {
      EXCHANGES.forEach((ex) => {
        update(ex.id, asset, randomRate());
      });
    });
  }, 500);
}
