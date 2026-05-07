export default function StatCard({ label, value, color = "text-white" }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-1">
      <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      <span className={"text-3xl font-bold " + color}>{value ?? 0}</span>
    </div>
  );
}
