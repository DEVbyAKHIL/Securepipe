import { useState } from "react";
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
