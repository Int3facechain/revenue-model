import {useEffect} from "react";
import {startEngineMock} from "../../engine/wsEngine";

import {useExchangeStore} from "../../store/exchangeStore";
import {useArbitrageStore} from "../../store/arbitrageStore";

import ExchangeSelector from "./components/ExchangeSelector";
import SettingsPanel from "./components/SettingsPanel";
import StatsGrid from "./components/StatsGrid";
import ArbitrageTable from "./components/ArbitrageTable";

export default function Dashboard() {
  useEffect(() => {
    startEngineMock();
  }, []);

  const pair = useExchangeStore((s) => s.pair);
  const setPair = useExchangeStore((s) => s.setPair);

  useArbitrageStore((s) => s.rates);
  const getSpread = useArbitrageStore.getState().getSpread;

  const rows = getSpread(pair.left, pair.right);

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
