import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getHistory, getHealth } from "../api";
import ScoreRing from "../components/ScoreRing";
import StatCard from "../components/StatCard";
import { PlusCircle } from "lucide-react";

export default function Dashboard() {
  const { data: histData } = useQuery({
    queryKey: ["history"],
    queryFn: () => getHistory(10).then((r) => r.data),
    refetchInterval: 15000,
  });

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: () => getHealth().then((r) => r.data),
  });

  const scans  = histData || [];
  const latest = scans[0];

  const totals = scans.reduce(
    (acc, s) => ({
      critical: acc.critical + (s.counts?.critical || 0),
      high:     acc.high     + (s.counts?.high     || 0),
      medium:   acc.medium   + (s.counts?.medium   || 0),
      low:      acc.low      + (s.counts?.low      || 0),
    }),
    { critical: 0, high: 0, medium: 0, low: 0 }
  );

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-400 mt-1">
            {health
              ? <span className="text-green-400">Backend connected - v{health.version}</span>
              : <span className="text-red-400">Backend not reachable</span>}
          </p>
        </div>
        <Link to="/scan"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
          <PlusCircle size={16} /> New Scan
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 items-center">
        <div className="col-span-2 md:col-span-1 flex justify-center">
          <ScoreRing score={latest?.score} />
        </div>
        <StatCard label="Critical" value={totals.critical} color="text-red-400" />
        <StatCard label="High"     value={totals.high}     color="text-orange-400" />
        <StatCard label="Medium"   value={totals.medium}   color="text-yellow-400" />
        <StatCard label="Low"      value={totals.low}      color="text-green-400" />
      </div>

      <div>
        <h2 className="text-lg font-semibold text-white mb-3">Recent Scans</h2>
        {scans.length === 0 ? (
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
            No scans yet.{" "}
            <Link to="/scan" className="text-indigo-400 hover:underline">Run your first scan</Link>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-sm">
              <thead className="bg-gray-900 text-gray-400 text-xs uppercase">
                <tr>
                  {["Repo","Branch","Score","Critical","High","Status","Date"].map((h) => (
                    <th key={h} className="px-4 py-3 text-left">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.scan_id} className="border-t border-gray-800 hover:bg-gray-900 transition-colors">
                    <td className="px-4 py-3 text-indigo-400 font-medium truncate max-w-[180px]">{s.repo_name}</td>
                    <td className="px-4 py-3 text-gray-300">{s.branch}</td>
                    <td className="px-4 py-3 font-bold text-white">{s.score ?? "--"}</td>
                    <td className="px-4 py-3 text-red-400">{s.counts?.critical ?? 0}</td>
                    <td className="px-4 py-3 text-orange-400">{s.counts?.high ?? 0}</td>
                    <td className="px-4 py-3">
                      <span className={
                        "text-xs px-2 py-0.5 rounded-full font-medium " +
                        (s.status === "completed" ? "bg-green-500/20 text-green-400" :
                         s.status === "failed"    ? "bg-red-500/20 text-red-400" :
                                                    "bg-yellow-500/20 text-yellow-400")
                      }>{s.status}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {s.completed_at ? new Date(s.completed_at).toLocaleDateString() : "--"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
