import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getHistory } from "../api";

export default function History() {
  const { data, isLoading } = useQuery({
    queryKey: ["history", 50],
    queryFn: () => getHistory(50).then((r) => r.data),
    refetchInterval: 20000,
  });

  const scans = data || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Scan History</h1>
        <p className="text-sm text-gray-400 mt-1">{scans.length} scans total</p>
      </div>

      {isLoading ? (
        <div className="text-gray-500 text-center py-12">Loading...</div>
      ) : scans.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-10 text-center text-gray-500">
          No history yet.{" "}
          <Link to="/scan" className="text-indigo-400 hover:underline">Run a scan</Link>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-sm">
            <thead className="bg-gray-900 text-gray-400 text-xs uppercase">
              <tr>
                {["Repo","Branch","Score","C","H","M","L","Status","Date"].map((h) => (
                  <th key={h} className="px-4 py-3 text-left">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.scan_id} className="border-t border-gray-800 hover:bg-gray-900/60 transition-colors">
                  <td className="px-4 py-3 text-indigo-400 font-medium truncate max-w-[160px]">{s.repo_name}</td>
                  <td className="px-4 py-3 text-gray-400">{s.branch}</td>
                  <td className="px-4 py-3 font-bold text-white">{s.score ?? "--"}</td>
                  <td className="px-4 py-3 text-red-400">{s.counts?.critical ?? 0}</td>
                  <td className="px-4 py-3 text-orange-400">{s.counts?.high ?? 0}</td>
                  <td className="px-4 py-3 text-yellow-400">{s.counts?.medium ?? 0}</td>
                  <td className="px-4 py-3 text-green-400">{s.counts?.low ?? 0}</td>
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
  );
}
