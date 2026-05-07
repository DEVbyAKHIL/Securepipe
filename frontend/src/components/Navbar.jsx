import { Link, useLocation } from "react-router-dom";
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
