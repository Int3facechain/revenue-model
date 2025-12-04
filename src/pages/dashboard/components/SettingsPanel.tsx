import SettingField from "./SettingField";
import {useSettingsStore} from "../../../store/settingsStore";

export default function SettingsPanel() {
  const minSpread = useSettingsStore((s) => s.minSpread);
  const refreshInterval = useSettingsStore((s) => s.refreshInterval);
  const sortMode = useSettingsStore((s) => s.sortMode);

  const setMinSpread = useSettingsStore((s) => s.setMinSpread);
  const setRefreshInterval = useSettingsStore((s) => s.setRefreshInterval);
  const setSortMode = useSettingsStore((s) => s.setSortMode);

  return (
    <div className="grid grid-cols-4 gap-6 items-end">

      {/* Minimum Spread */}
      <SettingField label="Minimum Spread (%)">
        <input
          type="number"
          value={minSpread}
          onChange={(e) => setMinSpread(Number(e.target.value))}
          className="bg-[#1a1f26] border border-gray-800 text-white rounded px-3 py-2 h-[42px] focus:outline-none focus:border-blue-600"
        />
      </SettingField>

      {/* Refresh Interval */}
      <SettingField label="Refresh Interval (s)">
        <input
          type="number"
          value={refreshInterval}
          onChange={(e) => setRefreshInterval(Number(e.target.value))}
          className="bg-[#1a1f26] border border-gray-800 text-white rounded px-3 py-2 h-[42px] focus:outline-none focus:border-blue-600"
        />
      </SettingField>

      {/* Sort Mode */}
      <SettingField label="Sort By">
        <select
          value={sortMode}
          onChange={(e) => setSortMode(e.target.value as any)}
          className="bg-[#1a1f26] border border-gray-800 text-white rounded px-3 py-2 h-[42px] focus:outline-none focus:border-blue-600"
        >
          <option value="spread_desc">Spread (Highest)</option>
          <option value="spread_asc">Spread (Lowest)</option>
        </select>
      </SettingField>

      {/* Buttons */}
      <SettingField>
        <div className="flex gap-3">
          <button
            className="h-[42px] flex-1 flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white px-4 rounded whitespace-nowrap"
          >
            🔄 Refresh Now
          </button>

          <button
            className="h-[42px] flex-1 flex items-center justify-center bg-gray-800 hover:bg-gray-700 text-gray-200 px-4 rounded whitespace-nowrap"
          >
            📥 Export CSV
          </button>
        </div>
      </SettingField>

    </div>
  );
}
