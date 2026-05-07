const styles = {
  critical: "bg-red-500/20 text-red-400 border border-red-500/30",
  high:     "bg-orange-500/20 text-orange-400 border border-orange-500/30",
  medium:   "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
  low:      "bg-green-500/20 text-green-400 border border-green-500/30",
  info:     "bg-blue-500/20 text-blue-400 border border-blue-500/30",
};

export default function SeverityBadge({ severity }) {
  const s = (severity || "info").toLowerCase();
  return (
    <span className={"text-xs font-semibold px-2 py-0.5 rounded-full uppercase " + (styles[s] || styles.info)}>
      {s}
    </span>
  );
}
