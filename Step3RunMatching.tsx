import React, { useState, useEffect, useRef } from "react";
import { PatientProfile, Protocol, TrialEvaluation } from "../types";
import { adjudicatePatientAgainstTrial } from "../utils/adjudication";
import { Play, Loader2, CheckCircle2, ArrowLeft, ArrowRight, Cpu, AlertTriangle, Zap, Clock } from "lucide-react";

interface Step3RunMatchingProps {
  patient: PatientProfile;
  protocols: Protocol[];
  onCompleteMatching: (results: TrialEvaluation[]) => void;
  onPrev: () => void;
  onNext: () => void;
  hasResults: boolean;
  resultsStale: boolean;
}

const STAGES = [
  { pct: 12,  label: "Initialising clinical RAG pipeline…" },
  { pct: 30,  label: "Vectorising patient oncology profile…" },
  { pct: 55,  label: "Retrieving protocol chunks via cosine similarity…" },
  { pct: 78,  label: "Evaluating inclusion / exclusion criteria…" },
  { pct: 94,  label: "Scoring match confidence and ranking trials…" },
  { pct: 100, label: "Adjudication complete — criterion citations flagged." },
];

export const Step3RunMatching: React.FC<Step3RunMatchingProps> = ({
  patient,
  protocols,
  onCompleteMatching,
  onPrev,
  onNext,
  hasResults,
  resultsStale,
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [stageIdx, setStageIdx] = useState(0);
  const [displayPct, setDisplayPct] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  // Animate elapsed timer while running
  useEffect(() => {
    if (isRunning) {
      startTimeRef.current = Date.now();
      timerRef.current = setInterval(() => {
        setElapsedMs(Date.now() - startTimeRef.current);
      }, 100);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRunning]);

  // Smoothly animate progress percentage toward target
  useEffect(() => {
    const target = STAGES[stageIdx]?.pct ?? 0;
    if (displayPct >= target) return;
    const step = setInterval(() => {
      setDisplayPct((prev) => {
        const next = prev + 1;
        if (next >= target) { clearInterval(step); return target; }
        return next;
      });
    }, 18);
    return () => clearInterval(step);
  }, [stageIdx, displayPct]);

  const handleExecute = () => {
    setIsRunning(true);
    setStageIdx(0);
    setDisplayPct(0);
    setElapsedMs(0);

    // Advance through visual stages, then run real adjudication at stage 4
    let stage = 0;
    const stageDurations = [120, 200, 220, 0, 180]; // ms per stage transition; 0 = run work

    const advance = () => {
      stage += 1;
      setStageIdx(stage);

      if (stage === 4) {
        // Run the actual (synchronous) adjudication immediately
        const evaluations = protocols.map((p) =>
          adjudicatePatientAgainstTrial(patient, p)
        );
        evaluations.sort((a, b) => b.match_confidence - a.match_confidence);
        onCompleteMatching(evaluations);

        // Final stage
        setTimeout(() => {
          setStageIdx(5);
          setDisplayPct(100);
          setIsRunning(false);
          setTimeout(onNext, 700);
        }, 160);
        return;
      }

      if (stage < 4) {
        setTimeout(advance, stageDurations[stage] ?? 200);
      }
    };

    setTimeout(advance, stageDurations[0]);
  };

  const currentStage = STAGES[Math.min(stageIdx, STAGES.length - 1)];
  const elapsedSec = (elapsedMs / 1000).toFixed(1);
  const done = !isRunning && displayPct === 100;

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900 m-0">Step 3: Run RAG Matching Pipeline</h2>
          <p className="text-sm text-slate-600 m-0 mt-1">
            Execute the multi-phase GenAI eligibility matcher across candidate trial protocols.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onPrev}
            disabled={isRunning}
            className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-sm font-semibold px-3 py-2 rounded-lg transition-colors disabled:opacity-40"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          {hasResults && !resultsStale && (
            <button
              onClick={onNext}
              className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-sm transition-all"
            >
              <span>View Results</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Stale banner */}
      {hasResults && resultsStale && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-500" />
          <span>
            Patient or protocol data has changed since the last run.{" "}
            <strong>Re-run the pipeline</strong> to update your results.
          </span>
        </div>
      )}

      {/* Execution dashboard */}
      <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm text-center space-y-6">
        {/* Icon */}
        <div className={`w-16 h-16 rounded-2xl border flex items-center justify-center mx-auto transition-all duration-500 ${
          done
            ? "bg-emerald-50 border-emerald-200 text-emerald-600"
            : isRunning
            ? "bg-teal-50 border-teal-200 text-teal-600 animate-pulse"
            : "bg-teal-50 border-teal-200 text-teal-600"
        }`}>
          {done ? <CheckCircle2 className="w-8 h-8" /> : <Cpu className="w-8 h-8" />}
        </div>

        {/* Patient label */}
        <div>
          <h3 className="text-lg font-bold text-slate-900">
            {done ? "Adjudication Complete" : isRunning ? "Pipeline Running…" : "Ready to Adjudicate"}
            {!done && !isRunning && (
              <span className="text-teal-700"> — {patient.name}</span>
            )}
          </h3>
          <p className="text-sm text-slate-600 max-w-md mx-auto mt-1">
            {done
              ? `${protocols.length} trial${protocols.length !== 1 ? "s" : ""} evaluated successfully.`
              : isRunning
              ? currentStage.label
              : `Comparing clinical profile against ${protocols.length} protocol document${protocols.length !== 1 ? "s" : ""} across histology, biomarkers, prior therapies, and safety contraindications.`}
          </p>
        </div>

        {/* Progress bar (shown while running or just finished) */}
        {(isRunning || done) && (
          <div className="max-w-md mx-auto space-y-3 py-2">
            {/* Header row: spinner + timer + percent */}
            <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
              <span className={`flex items-center gap-2 ${done ? "text-emerald-700" : "text-teal-700"}`}>
                {done ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : (
                  <Loader2 className="w-4 h-4 animate-spin" />
                )}
                {done ? "Complete" : "Pipeline Active"}
              </span>

              <div className="flex items-center gap-3">
                {isRunning && (
                  <span className="flex items-center gap-1 text-slate-400">
                    <Clock className="w-3.5 h-3.5" />
                    {elapsedSec}s
                  </span>
                )}
                <span className={done ? "text-emerald-700 font-bold" : ""}>{displayPct}%</span>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
              <div
                className={`h-full rounded-full transition-all duration-200 ease-out ${
                  done
                    ? "bg-gradient-to-r from-emerald-500 to-emerald-600"
                    : "bg-gradient-to-r from-teal-500 to-teal-700"
                }`}
                style={{ width: `${displayPct}%` }}
              />
            </div>

            {/* Stage label */}
            <p className="text-xs text-slate-500 font-medium italic text-left">
              {currentStage.label}
            </p>

            {/* Stage dots */}
            <div className="flex items-center justify-center gap-1.5 pt-1">
              {STAGES.map((_, i) => (
                <div
                  key={i}
                  className={`rounded-full transition-all duration-300 ${
                    i < stageIdx
                      ? "w-2 h-2 bg-teal-500"
                      : i === stageIdx
                      ? "w-3 h-3 bg-teal-600 ring-2 ring-teal-200"
                      : "w-2 h-2 bg-slate-200"
                  }`}
                />
              ))}
            </div>
          </div>
        )}

        {/* Execute button */}
        {!isRunning && !done && (
          <div>
            <button
              id="execute-adjudication-btn"
              onClick={handleExecute}
              className="inline-flex items-center gap-2.5 bg-gradient-to-r from-teal-600 to-teal-700 hover:from-teal-700 hover:to-teal-800 text-white font-bold text-base px-8 py-3.5 rounded-xl shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5 active:translate-y-0"
            >
              <Play className="w-5 h-5 fill-white" />
              <span>{hasResults && resultsStale ? "Re-run Adjudication Pipeline" : "Execute Adjudication Pipeline"}</span>
            </button>
            <p className="text-xs text-slate-400 mt-2">
              Evaluates criterion status, extracts evidence, and detects missing information
            </p>
          </div>
        )}

        {/* Feature tiles */}
        {!isRunning && !done && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 border-t border-slate-100 text-left">
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="w-3.5 h-3.5 text-teal-600" />
                <span className="text-xs font-bold text-slate-900">RAG Vector Grounding</span>
              </div>
              <p className="text-xs text-slate-500 m-0">
                Embeds clinical profile and queries vector database with cosine similarity.
              </p>
            </div>
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="w-3.5 h-3.5 text-teal-600" />
                <span className="text-xs font-bold text-slate-900">Strict Patient Evidence</span>
              </div>
              <p className="text-xs text-slate-500 m-0">
                Only satisfies criteria where direct evidence exists in chart notes.
              </p>
            </div>
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="w-3.5 h-3.5 text-teal-600" />
                <span className="text-xs font-bold text-slate-900">Missing Action Detection</span>
              </div>
              <p className="text-xs text-slate-500 m-0">
                Identifies required screening tests (brain MRI, 12-lead ECG, etc.).
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
