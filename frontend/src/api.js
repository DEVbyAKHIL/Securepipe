import axios from "axios";

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
