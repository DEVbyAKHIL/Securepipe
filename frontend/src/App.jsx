import { Routes, Route } from "react-router-dom";
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
