import React, { useState, useRef, useCallback } from "react";
import { Protocol, PatientProfile, TrialEvaluation } from "./types";
import { SAMPLE_PROTOCOLS, SAMPLE_PATIENTS } from "./data/sampleData";
import { Header } from "./components/Header";
import { StepProgress } from "./components/StepProgress";
import { Step1Protocols } from "./components/Step1Protocols";
import { Step2PatientProfile } from "./components/Step2PatientProfile";
import { Step3RunMatching } from "./components/Step3RunMatching";
import { Step4Results } from "./components/Step4Results";
import { Step5Export } from "./components/Step5Export";
import { LocalRunModal } from "./components/LocalRunModal";

export default function App() {
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [protocols, setProtocols] = useState<Protocol[]>(SAMPLE_PROTOCOLS);
  const [patient, setPatient] = useState<PatientProfile>(SAMPLE_PATIENTS[0]);
  const [evaluations, setEvaluations] = useState<TrialEvaluation[]>([]);
  const [isLocalModalOpen, setIsLocalModalOpen] = useState<boolean>(false);
  // Track whether current results are stale (patient/protocols changed since last run)
  const [resultsStale, setResultsStale] = useState<boolean>(false);

  // Cache key: if same patient id + same protocol ids → skip re-adjudication
  const lastRunKey = useRef<string>("");

  const buildRunKey = (p: PatientProfile, protos: Protocol[]) =>
    p.id + "|" + protos.map((pr) => pr.trial_id).join(",");

  const handleAddProtocol = useCallback((newTrial: Protocol) => {
    setProtocols((prev) => [newTrial, ...prev]);
    setResultsStale(true);
  }, []);

  const handleChangePatient = useCallback((p: PatientProfile) => {
    setPatient(p);
    setResultsStale(true);
  }, []);

  const handleCompleteMatching = useCallback(
    (results: TrialEvaluation[]) => {
      setEvaluations(results);
      setResultsStale(false);
      lastRunKey.current = buildRunKey(patient, protocols);
    },
    [patient, protocols]
  );

  // Guard: only allow navigating to steps 4/5 if results exist
  const handleSelectStep = useCallback(
    (step: number) => {
      if ((step === 4 || step === 5) && evaluations.length === 0) return;
      setCurrentStep(step);
    },
    [evaluations.length]
  );

  const hasResults = evaluations.length > 0;
  // Results are "fresh" only if the run key matches current state
  const resultsFresh =
    hasResults &&
    !resultsStale &&
    lastRunKey.current === buildRunKey(patient, protocols);

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans antialiased text-slate-900 selection:bg-teal-100 selection:text-teal-900">
      <Header
        onOpenLocalModal={() => setIsLocalModalOpen(true)}
        protocolCount={protocols.length}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <StepProgress
          currentStep={currentStep}
          onSelectStep={handleSelectStep}
          hasResults={hasResults}
          resultsStale={resultsStale}
        />

        <div className="transition-all duration-200">
          {currentStep === 1 && (
            <Step1Protocols
              protocols={protocols}
              onAddProtocol={handleAddProtocol}
              onNext={() => setCurrentStep(2)}
            />
          )}

          {currentStep === 2 && (
            <Step2PatientProfile
              patient={patient}
              onChangePatient={handleChangePatient}
              onPrev={() => setCurrentStep(1)}
              onNext={() => setCurrentStep(3)}
            />
          )}

          {currentStep === 3 && (
            <Step3RunMatching
              patient={patient}
              protocols={protocols}
              onCompleteMatching={handleCompleteMatching}
              onPrev={() => setCurrentStep(2)}
              onNext={() => setCurrentStep(4)}
              hasResults={hasResults}
              resultsStale={resultsStale}
            />
          )}

          {currentStep === 4 && (
            <Step4Results
              evaluations={evaluations}
              patient={patient}
              onPrev={() => setCurrentStep(3)}
              onNext={() => setCurrentStep(5)}
            />
          )}

          {currentStep === 5 && (
            <Step5Export
              patient={patient}
              evaluations={evaluations}
              onPrev={() => setCurrentStep(4)}
            />
          )}
        </div>
      </main>

      <footer className="bg-white border-t border-slate-200 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span>🔬 <strong>Clinical Trial Eligibility Matcher</strong> &bull; GenAI Applied Oncology Decision Support</span>
          </div>
          <div>
            <span>Synthetic clinical data only &bull; Compliant prescreening architecture</span>
          </div>
        </div>
      </footer>

      <LocalRunModal
        isOpen={isLocalModalOpen}
        onClose={() => setIsLocalModalOpen(false)}
      />
    </div>
  );
}
