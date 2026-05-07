export default function ScoreRing({ score = 0, size = 120 }) {
  const r = 45;
  const circ = 2 * Math.PI * r;
  const fill = ((score || 0) / 100) * circ;
  const color =
    score >= 80 ? "#22c55e" :
    score >= 50 ? "#eab308" :
    score >= 25 ? "#f97316" : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#1f2937" strokeWidth="10" />
        <circle
          cx="50" cy="50" r={r} fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={circ}
          strokeDashoffset={circ - fill}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
        <text x="50" y="50" textAnchor="middle" dominantBaseline="central"
          fill={color} fontSize="20" fontWeight="bold">
          {score ?? "--"}
        </text>
      </svg>
      <span className="text-xs text-gray-400">Security Score</span>
    </div>
  );
}
