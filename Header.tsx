import React from "react";
import { Activity, Terminal, ShieldCheck, Database, Wifi } from "lucide-react";

interface HeaderProps {
  onOpenLocalModal: () => void;
  protocolCount: number;
}

export const Header: React.FC<HeaderProps> = ({ onOpenLocalModal, protocolCount }) => {
  return (
    <header className="bg-[#0B192C] text-white border-b border-slate-800 sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-teal-600/20 border border-teal-500/40 flex items-center justify-center text-teal-400 shrink-0">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg font-bold tracking-tight text-white m-0 leading-none">
                Clinical Trial Eligibility Matcher
              </h1>
              <span className="hidden sm:inline-flex text-[11px] font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30 px-2 py-0.5 rounded-full leading-none">
                GenAI RAG Pipeline
              </span>
            </div>
            <p className="text-xs text-slate-400 m-0 hidden md:block mt-0.5">
              Criterion-by-criterion oncology protocol adjudication &amp; missing information detection
            </p>
          </div>
        </div>

        {/* Right: status badges + button */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Protocol count */}
          <div className="hidden lg:flex items-center gap-2 text-xs bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-md text-slate-300">
            <Database className="w-3.5 h-3.5 text-teal-400" />
            <span>
              Protocols: <strong className="text-white">{protocolCount}</strong>
            </span>
          </div>

          {/* Live indicator */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/50 px-2.5 py-1.5 rounded-md">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Synthetic Data</span>
          </div>

          {/* Local run guide */}
          <button
            id="local-run-instructions-btn"
            onClick={onOpenLocalModal}
            className="flex items-center gap-1.5 text-xs font-semibold bg-teal-600 hover:bg-teal-500 text-white px-3 py-1.5 rounded-md transition-colors shadow-sm"
            title="View Streamlit local run commands"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Local Python Guide</span>
            <span className="sm:hidden">Guide</span>
          </button>
        </div>
      </div>
    </header>
  );
};
