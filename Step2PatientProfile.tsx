import React, { useState } from "react";
import { PatientProfile } from "../types";
import { SAMPLE_PATIENTS } from "../data/sampleData";
import { User, Dna, Activity, ArrowRight, ArrowLeft, Sparkles, Check, RefreshCw } from "lucide-react";

interface Step2PatientProfileProps {
  patient: PatientProfile;
  onChangePatient: (p: PatientProfile) => void;
  onPrev: () => void;
  onNext: () => void;
}

export const Step2PatientProfile: React.FC<Step2PatientProfileProps> = ({
  patient,
  onChangePatient,
  onPrev,
  onNext
}) => {
  const [lastSelected, setLastSelected] = useState<string>(patient.id);

  const handleSelectPreconfigured = (id: string) => {
    const selected = SAMPLE_PATIENTS.find((p) => p.id === id);
    if (selected) {
      setLastSelected(id);
      onChangePatient({ ...selected });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 m-0">Step 2: Enter or Select Synthetic Patient Profile</h2>
          <p className="text-sm text-slate-600 m-0 mt-1">
            Choose from curated synthetic oncology patient profiles or customize clinical narrative notes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onPrev}
            className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-sm font-semibold px-3 py-2 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
          <button
            id="proceed-step-3-btn"
            onClick={onNext}
            className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-sm transition-all"
          >
            <span>Next: Run Matching</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Preset Patient Selector Pills */}
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
          Select Pre-Configured Synthetic Patient Case
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {SAMPLE_PATIENTS.map((sp) => {
            const isSelected = patient.id === sp.id;
            return (
              <button
                key={sp.id}
                id={`select-patient-btn-${sp.id}`}
                onClick={() => handleSelectPreconfigured(sp.id)}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  isSelected
                    ? "bg-teal-50/70 border-teal-500 shadow-xs ring-1 ring-teal-500"
                    : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/50"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-sm text-slate-900">{sp.name}</span>
                  {isSelected && <Check className="w-4 h-4 text-teal-600" />}
                </div>
                <div className="text-xs text-teal-700 font-semibold mb-1">
                  {sp.demographics.age}yo {sp.demographics.gender} &bull; ECOG {sp.demographics.ecog_ps}
                </div>
                <p className="text-xs text-slate-500 line-clamp-2 m-0">
                  {sp.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clinical Narrative Input (High-Contrast, Light Background, Dark Text) */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <label htmlFor="clinical-notes-textarea" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
              Unstructured Clinical Oncology Notes
            </label>
            <span className="text-xs text-slate-500">Synthetic de-identified chart</span>
          </div>

          <textarea
            id="clinical-notes-textarea"
            rows={10}
            value={patient.clinical_notes}
            onChange={(e) => onChangePatient({ ...patient, clinical_notes: e.target.value })}
            placeholder="Type or paste patient age, diagnosis, stage, biomarker findings, prior treatment lines, performance status, and lab values..."
            className="w-full bg-white text-slate-900 placeholder:text-slate-400 font-medium text-sm p-4 rounded-xl border-1.5 border-slate-300 focus:border-teal-600 focus:ring-3 focus:ring-teal-500/20 shadow-xs transition-all leading-relaxed"
          />

          <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
            <span>Character count: {patient.clinical_notes.length}</span>
            <span className="text-teal-700 font-medium">Ready for GenAI RAG parsing</span>
          </div>
        </div>

        {/* Structured Clinical Attributes Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <Sparkles className="w-4 h-4 text-teal-600" />
              <h3 className="text-sm font-bold text-slate-900 m-0">Structured Patient Attributes</h3>
            </div>

            <div>
              <div className="text-xs text-slate-400 font-semibold mb-1">DEMOGRAPHICS</div>
              <div className="text-sm font-semibold text-slate-800">
                {patient.demographics.age} years old &bull; {patient.demographics.gender}
              </div>
              <div className="text-xs text-slate-600 mt-0.5">
                ECOG Performance Status: <span className="font-bold text-slate-900">{patient.demographics.ecog_ps}</span>
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-400 font-semibold mb-1">DIAGNOSIS & STAGE</div>
              <div className="text-sm font-bold text-slate-900">
                {patient.condition.primary_diagnosis}
              </div>
              <div className="text-xs text-teal-800 font-medium">
                {patient.condition.stage} &bull; {patient.condition.histology}
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-400 font-semibold mb-1">BIOMARKER PROFILES</div>
              <div className="space-y-1.5">
                {patient.biomarkers.map((b, idx) => (
                  <div key={idx} className="flex items-center justify-between text-xs bg-slate-50 px-2.5 py-1.5 rounded border border-slate-200">
                    <span className="font-bold text-slate-800">{b.gene}</span>
                    <span className="text-slate-600 font-medium truncate max-w-[140px]">{b.status}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-xs text-slate-400 font-semibold mb-1">PRIOR THERAPY LINES</div>
              <div className="space-y-1">
                {patient.prior_treatments.map((t, idx) => (
                  <div key={idx} className="text-xs text-slate-700">
                    &bull; <strong className="text-slate-900">{t.name}</strong> ({t.type})
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
