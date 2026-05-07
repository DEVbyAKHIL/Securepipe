import { useState } from "react";
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
