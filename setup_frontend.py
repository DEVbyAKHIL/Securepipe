import os
from pathlib import Path

BASE = Path("frontend/src")
BASE.mkdir(parents=True, exist_ok=True)
(BASE / "components").mkdir(exist_ok=True)
(BASE / "pages").mkdir(exist_ok=True)

def w(path, content):
    Path(path).write_text(content, encoding="utf-8")

# tailwind.config.js
w("frontend/tailwind.config.js", """/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        critical: "#ef4444",
        high:     "#f97316",
        medium:   "#eab308",
        low:      "#22c55e",
      },
    },
  },
  plugins: [],
}
""")

# index.css
w("frontend/src/index.css", """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-950 text-gray-100 min-h-screen;
}
""")

# main.jsx
w("frontend/src/main.jsx", """import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./index.css";

const qc = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
""")

# App.jsx
w("frontend/src/App.jsx", """import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import NewScan from "./pages/NewScan";
import Results from "./pages/Results";
import History from "./pages/History";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <Navbar />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <Routes>
          <Route path="/"            element={<Dashboard />} />
          <Route path="/scan"        element={<NewScan />} />
          <Route path="/results/:id" element={<Results />} />
          <Route path="/history"     element={<History />} />
          <Route path="/settings"    element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
""")

# api.js
w("frontend/src/api.js", """import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const key = localStorage.getItem("sp_api_key");
  if (key) config.headers["X-API-Key"] = key;
  return config;
});

export const triggerScan  = (data)       => api.post("/api/v1/scan", data);
export const triggerAsync = (data)       => api.post("/api/v1/scan/async", data);
export const pollJob      = (jobId)      => api.get("/api/v1/scan/status/" + jobId);
export const getHistory   = (limit = 20) => api.get("/api/v1/scans?limit=" + limit);
export const getHealth    = ()           => api.get("/api/v1/health");

export default api;
""")

# Navbar.jsx
w("frontend/src/components/Navbar.jsx", """import { Link, useLocation } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

const links = [
  { to: "/",         label: "Dashboard" },
  { to: "/scan",     label: "New Scan"  },
  { to: "/history",  label: "History"   },
  { to: "/settings", label: "Settings"  },
];

export default function Navbar() {
  const { pathname } = useLocation();
  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-xl font-bold text-indigo-400">
          <ShieldCheck size={26} />
          SecurePipe
        </Link>
        <div className="flex gap-6">
          {links.map((l) => (
            <Link key={l.to} to={l.to}
              className={
                "text-sm font-medium transition-colors " +
                (pathname === l.to
                  ? "text-indigo-400 border-b-2 border-indigo-400 pb-0.5"
                  : "text-gray-400 hover:text-white")
              }>
              {l.label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
""")

# SeverityBadge.jsx
w("frontend/src/components/SeverityBadge.jsx", """const styles = {
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
""")

# ScoreRing.jsx
w("frontend/src/components/ScoreRing.jsx", """export default function ScoreRing({ score = 0, size = 120 }) {
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
""")

# FindingCard.jsx
w("frontend/src/components/FindingCard.jsx", """import { useState } from "react";
import SeverityBadge from "./SeverityBadge";
import { ChevronDown, ChevronUp } from "lucide-react";

export default function FindingCard({ finding }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-3 text-left">
          <SeverityBadge severity={finding.severity} />
          <span className="text-sm font-medium text-gray-100">{finding.title}</span>
          <span className="text-xs text-gray-500 hidden sm:block">{finding.scanner}</span>
        </div>
        {open
          ? <ChevronUp   size={16} className="text-gray-400 shrink-0" />
          : <ChevronDown size={16} className="text-gray-400 shrink-0" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-gray-800 pt-3">
          <div className="flex flex-wrap gap-4 text-xs text-gray-400">
            <span>File: {finding.file}{finding.line ? ":" + finding.line : ""}</span>
            <span>Scanner: {finding.scanner}</span>
            {finding.cvss && <span>CVSS {finding.cvss}</span>}
          </div>
          <p className="text-sm text-gray-300">{finding.description}</p>
          {finding.code_snippet && (
            <pre className="bg-gray-950 text-green-400 text-xs p-3 rounded overflow-x-auto">
              {finding.code_snippet}
            </pre>
          )}
          <div className="bg-indigo-950/50 border border-indigo-800/40 rounded p-3">
            <p className="text-xs font-semibold text-indigo-300 mb-1">Fix Suggestion</p>
            <p className="text-sm text-gray-300">{finding.fix_suggestion}</p>
          </div>
        </div>
      )}
    </div>
  );
}
""")

# StatCard.jsx
w("frontend/src/components/StatCard.jsx", """export default function StatCard({ label, value, color = "text-white" }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-1">
      <span className="text-xs text-gray-400 uppercase tracking-wide">{label}</span>
      <span className={"text-3xl font-bold " + color}>{value ?? 0}</span>
    </div>
  );
}
""")

# Dashboard.jsx
w("frontend/src/pages/Dashboard.jsx", """import { useQuery } from "@tanstack/react-query";
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
""")

# NewScan.jsx
w("frontend/src/pages/NewScan.jsx", """import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { triggerAsync, pollJob } from "../api";
import { ShieldCheck, Loader2 } from "lucide-react";

const STEPS = [
  "Cloning repo",
  "Running Bandit SAST",
  "Checking dependencies",
  "Scanning for secrets",
  "IaC / Dockerfile analysis",
  "Enriching with AI",
];

export default function NewScan() {
  const nav = useNavigate();
  const [repoUrl, setRepoUrl] = useState("");
  const [branch,  setBranch]  = useState("main");
  const [loading, setLoading] = useState(false);
  const [step,    setStep]    = useState(0);
  const [error,   setError]   = useState("");

  async function handleScan(e) {
    e.preventDefault();
    setError(""); setLoading(true); setStep(0);
    try {
      const { data } = await triggerAsync({ repo_url: repoUrl, branch });
      const jobId = data.job_id;
      let stepIdx = 0;
      const ticker = setInterval(() => {
        stepIdx = Math.min(stepIdx + 1, STEPS.length - 1);
        setStep(stepIdx);
      }, 4000);
      let done = false;
      while (!done) {
        await new Promise((r) => setTimeout(r, 3000));
        const { data: status } = await pollJob(jobId);
        if (status.status === "completed") {
          clearInterval(ticker);
          done = true;
          nav("/results/" + jobId, { state: { result: status } });
        } else if (status.status === "failed") {
          clearInterval(ticker);
          done = true;
          setError(status.error_message || "Scan failed.");
          setLoading(false);
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">New Scan</h1>
        <p className="text-sm text-gray-400 mt-1">Paste a public GitHub, GitLab, or Bitbucket repo URL</p>
      </div>

      <form onSubmit={handleScan} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Repository URL</label>
          <input type="text" required value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Branch</label>
          <input type="text" value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        {error && (
          <p className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2">{error}</p>
        )}
        <button type="submit" disabled={loading}
          className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white font-semibold py-3 rounded-lg transition-colors">
          {loading ? <Loader2 size={18} className="animate-spin" /> : <ShieldCheck size={18} />}
          {loading ? "Scanning..." : "Start Security Scan"}
        </button>
      </form>

      {loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-3">
          <p className="text-sm font-semibold text-white">Scan in progress...</p>
          {STEPS.map((s, i) => (
            <div key={s} className="flex items-center gap-3">
              <div className={
                "w-3 h-3 rounded-full shrink-0 " +
                (i < step  ? "bg-green-400" :
                 i === step ? "bg-indigo-400 animate-pulse" : "bg-gray-700")
              } />
              <span className={"text-sm " + (i <= step ? "text-gray-200" : "text-gray-600")}>{s}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
""")

# Results.jsx
w("frontend/src/pages/Results.jsx", """import { useLocation, useParams } from "react-router-dom";
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
""")

# History.jsx
w("frontend/src/pages/History.jsx", """import { useQuery } from "@tanstack/react-query";
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
""")

# Settings.jsx
w("frontend/src/pages/Settings.jsx", """import { useState } from "react";
import { getHealth } from "../api";
import { CheckCircle, XCircle } from "lucide-react";

export default function Settings() {
  const [apiUrl, setApiUrl] = useState(localStorage.getItem("sp_api_url") || "");
  const [apiKey, setApiKey] = useState(localStorage.getItem("sp_api_key") || "");
  const [saved,  setSaved]  = useState(false);
  const [health, setHealth] = useState(null);

  function handleSave(e) {
    e.preventDefault();
    if (apiUrl) localStorage.setItem("sp_api_url", apiUrl);
    if (apiKey) localStorage.setItem("sp_api_key", apiKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  async function testConnection() {
    try {
      const { data } = await getHealth();
      setHealth({ ok: true, data });
    } catch {
      setHealth({ ok: false });
    }
  }

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sm text-gray-400 mt-1">Configure your backend connection</p>
      </div>

      <form onSubmit={handleSave} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Backend API URL</label>
          <input type="text" value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            placeholder="https://xxxx.ngrok.io  or  http://localhost:8000"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
          <p className="text-xs text-gray-500 mt-1">Paste your Colab ngrok URL here when backend is running</p>
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">API Key (optional)</label>
          <input type="password" value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="your-api-key"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div className="flex gap-3">
          <button type="submit"
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 rounded-lg transition-colors">
            {saved ? "Saved!" : "Save Settings"}
          </button>
          <button type="button" onClick={testConnection}
            className="flex-1 bg-gray-800 hover:bg-gray-700 text-white font-semibold py-2.5 rounded-lg transition-colors">
            Test Connection
          </button>
        </div>
      </form>

      {health && (
        <div className={
          "border rounded-xl p-4 flex items-start gap-3 " +
          (health.ok ? "bg-green-500/10 border-green-500/30" : "bg-red-500/10 border-red-500/30")
        }>
          {health.ok
            ? <CheckCircle className="text-green-400 shrink-0 mt-0.5" size={18} />
            : <XCircle     className="text-red-400 shrink-0 mt-0.5"    size={18} />}
          <div className="text-sm">
            {health.ok ? (
              <>
                <p className="font-semibold text-green-400">Backend Connected</p>
                <p className="text-gray-400 mt-1">
                  Version: {health.data.version} | AI: {health.data.ai_enabled ? "ON" : "OFF"} | DB: {health.data.db_connected ? "Connected" : "Not connected"}
                </p>
              </>
            ) : (
              <p className="font-semibold text-red-400">Cannot reach backend. Check the URL.</p>
            )}
          </div>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-sm text-gray-400 space-y-2">
        <p className="font-semibold text-white text-base">How to connect backend</p>
        <p>1. Run the Master Restart Cell in Google Colab</p>
        <p>2. Copy the ngrok URL it prints</p>
        <p>3. Paste it above and click Save Settings</p>
        <p>4. Click Test Connection to verify</p>
      </div>
    </div>
  );
}
""")

w("frontend/.env.local", "VITE_API_URL=http://localhost:8000\n")
w("frontend/.gitignore", "node_modules\ndist\n.env.local\n.DS_Store\n")

print("\n=== ALL FILES WRITTEN SUCCESSFULLY ===")
for root, dirs, files in os.walk("frontend/src"):
    dirs[:] = [d for d in dirs if d != "node_modules"]
    level = root.replace("frontend/src", "").count(os.sep)
    print("  " + "  " * level + os.path.basename(root) + "/")
    for f in files:
        print("  " + "  " * (level+1) + f)
print("\nNext: cd frontend && npm run dev")