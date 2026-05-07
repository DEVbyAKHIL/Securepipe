import { useLocation, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { pollJob } from "../api";
import ScoreRing from "../components/ScoreRing";
import StatCard from "../components/StatCard";
import FindingCard from "../components/FindingCard";
import { useState } from "react";

export default function Results() {
  const { id } = useParams();
  const { state } = useLocation();
  const [filter, setFilter] = useState("all");

  const { data: polled } = useQuery({
    queryKey: ["result", id],
    queryFn: () => pollJob(id).then((r) => r.data),
    enabled: !state?.result,
    refetchInterval: false,
  });

  const result = state?.result || polled;
  if (!result) return (
    <div className="flex items-center justify-center h-64 text-gray-500">Loading results...</div>
  );

  const findings = result.findings || [];
  const filtered = filter === "all" ? findings : findings.filter((f) => f.severity === filter);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white break-all">{result.repo_name}</h1>
        <p className="text-sm text-gray-400 mt-1">{result.repo_url} - branch: {result.branch}</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 items-center">
        <div className="col-span-2 md:col-span-1 flex justify-center">
          <ScoreRing score={result.score} />
        </div>
        <StatCard label="Critical" value={result.counts?.critical} color="text-red-400" />
        <StatCard label="High"     value={result.counts?.high}     color="text-orange-400" />
        <StatCard label="Medium"   value={result.counts?.medium}   color="text-yellow-400" />
        <StatCard label="Low"      value={result.counts?.low}      color="text-green-400" />
      </div>

      <div className="flex flex-wrap gap-3 text-xs text-gray-400">
        <span>Scanners: {(result.scanners_used || []).join(", ")}</span>
        <span>Duration: {result.duration_seconds}s</span>
        <span>ID: {result.scan_id}</span>
      </div>

      <div className="flex gap-2 flex-wrap">
        {["all","critical","high","medium","low"].map((s) => (
          <button key={s} onClick={() => setFilter(s)}
            className={
              "text-xs px-3 py-1.5 rounded-full font-medium capitalize transition-colors " +
              (filter === s
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700")
            }>
            {s === "all"
              ? "All (" + findings.length + ")"
              : s + " (" + findings.filter((f) => f.severity === s).length + ")"}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No findings for this filter</div>
        ) : (
          filtered.map((f) => <FindingCard key={f.id} finding={f} />)
        )}
      </div>
    </div>
  );
}
