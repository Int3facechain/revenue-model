export default function StatCard({label, value, note, valueClass = ""}: {
  label: string,
  value: string,
  note: string,
  valueClass?: string
}) {
  return (
    <div className="bg-[#1a1f26] border border-gray-800 rounded-xl p-6 flex flex-col gap-1">
      <span className="text-xs text-gray-400 tracking-wide uppercase">
        {label}
      </span>

      <span className={`text-3xl font-semibold ${valueClass}`}>
        {value}
      </span>

      <span className="text-gray-500 text-sm">
        {note}
      </span>
    </div>
  );
}
