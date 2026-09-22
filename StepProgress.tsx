import React from "react";
import { FileText, UserCheck, Play, CheckCircle2, Download, AlertTriangle } from "lucide-react";

interface StepProgressProps {
  currentStep: number;
  onSelectStep: (step: number) => void;
  hasResults: boolean;
  resultsStale: boolean;
}

const steps = [
  { num: 1, label: "Protocols", icon: FileText },
  { num: 2, label: "Patient Profile", icon: UserCheck },
  { num: 3, label: "Run Matching", icon: Play },
  { num: 4, label: "Results", icon: CheckCircle2 },
  { num: 5, label: "Export Report", icon: Download },
];

export const StepProgress: React.FC<StepProgressProps> = ({
  currentStep,
  onSelectStep,
  hasResults,
  resultsStale,
}) => {
  const isLocked = (stepNum: number) =>
    (stepNum === 4 || stepNum === 5) && !hasResults;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-3 mb-6">
      <div className="grid grid-cols-5 gap-1.5">
        {steps.map((s) => {
          const Icon = s.icon;
          const isActive = currentStep === s.num;
          const isCompleted = currentStep > s.num;
          const locked = isLocked(s.num);
          // Step 3 shows a stale warning badge when results exist but are outdated
          const showStale = s.num === 3 && hasResults && resultsStale;

          return (
            <button
              key={s.num}
              id={`step-nav-btn-${s.num}`}
              onClick={() => !locked && onSelectStep(s.num)}
              disabled={locked}
              title={locked ? "Complete matching first" : undefined}
              className={[
                "relative flex items-center justify-center sm:justify-start gap-2 py-2.5 px-2 sm:px-3 rounded-lg text-xs md:text-sm font-semibold transition-all",
                isActive
                  ? "bg-teal-50 text-teal-800 border border-teal-200 shadow-sm"
                  : isCompleted && !locked
                  ? "text-slate-700 hover:bg-slate-50 cursor-pointer"
                  : locked
                  ? "text-slate-300 cursor-not-allowed opacity-60"
                  : "text-slate-400 hover:text-slate-600 hover:bg-slate-50 cursor-pointer",
              ].join(" ")}
            >
              {/* Step number circle */}
              <div
                className={[
                  "w-6 h-6 rounded-full flex items-center justify-center text-xs shrink-0 font-bold transition-colors",
                  isActive
                    ? "bg-teal-600 text-white"
                    : isCompleted && !locked
                    ? "bg-emerald-100 text-emerald-700"
                    : locked
                    ? "bg-slate-100 text-slate-300"
                    : "bg-slate-100 text-slate-500",
                ].join(" ")}
              >
                {isCompleted && !isActive && !locked ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                ) : (
                  s.num
                )}
              </div>

              <span className="hidden sm:inline truncate">{s.label}</span>

              {/* Stale badge on Step 3 */}
              {showStale && (
                <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-amber-400 flex items-center justify-center shadow-sm">
                  <AlertTriangle className="w-2.5 h-2.5 text-white" />
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Stale results notice */}
      {hasResults && resultsStale && (
        <div className="mt-2 mx-1 flex items-center gap-1.5 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5">
          <AlertTriangle className="w-3 h-3 shrink-0" />
          <span>Patient or protocol data changed — re-run matching to refresh results.</span>
        </div>
      )}
    </div>
  );
};
