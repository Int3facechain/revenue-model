import {useEffect} from "react";

import {useExchangeStore} from "../../store/exchangeStore";
import {useArbitrageStore} from "../../store/arbitrageStore";

import ExchangeSelector from "./components/ExchangeSelector";
import SettingsPanel from "./components/SettingsPanel";
import StatsGrid from "./components/StatsGrid";
import ArbitrageTable from "./components/ArbitrageTable";
import {startEngine} from "../../engine/engine";

export default function Dashboard() {
  useEffect(() => {
    startEngine();
  }, []);

  const pair = useExchangeStore((s) => s.pair);
  const setPair = useExchangeStore((s) => s.setPair);

  const rates = useArbitrageStore((s) => s.rates);
  const rows = useArbitrageStore.getState().getSpread(pair.left, pair.right);

  console.log("[Dashboard] pair:", pair);
  console.log("[Dashboard] rates:", rates);
  console.log("[Dashboard] rows:", rows);

  return (
    <div className="pt-16">
      <header className="flex flex-col gap-3">
        <h1 className="font-bold text-3xl">⚡ Funding Rate Arbitrage Monitor</h1>
        <h2 className="text-gray-500">
          Compare {pair.left.toUpperCase()} vs {pair.right.toUpperCase()}
        </h2>
      </header>

      <hr className="border-gray-700 my-6"/>

      <ExchangeSelector pair={pair} setPair={setPair}/>
      <SettingsPanel/>
      <StatsGrid rows={rows}/>
      <ArbitrageTable data={rows} pair={pair}/>

      <hr className="border-gray-700 my-6"/>
    </div>
  );
}
