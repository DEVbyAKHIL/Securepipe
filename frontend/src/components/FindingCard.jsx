import { useState } from "react";
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
