import React, { useState } from "react";
import { Protocol } from "../types";
import { Upload, FileText, CheckCircle2, PlusCircle, ArrowRight, Shield } from "lucide-react";

interface Step1ProtocolsProps {
  protocols: Protocol[];
  onAddProtocol: (p: Protocol) => void;
  onNext: () => void;
}

export const Step1Protocols: React.FC<Step1ProtocolsProps> = ({ protocols, onAddProtocol, onNext }) => {
  const [dragOver, setDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploadStatus(`Parsing ${files.length} document(s)...`);
    setTimeout(() => {
      // Simulate PDF parsing into protocol
      const newTrial: Protocol = {
        trial_id: `NCT0${Math.floor(5000000 + Math.random() * 900000)}`,
        trial_title: `Phase II Protocol for ${files[0].name.replace(/\.[^/.]+$/, "")}`,
        phase: "Phase II",
        condition: "Advanced Solid Neoplasms",
        drug_modality: "Targeted Molecular Therapy",
        sponsor: "Academic Medical Center",
        summary: `Structured protocol criteria parsed from ${files[0].name}.`,
        inclusion_criteria: [
          {
            id: "INC-01",
            category: "Histology",
            criterion: "Confirmed metastatic or locally advanced unresectable malignancy.",
            parsed_rules: { variable: "diagnosis", operator: "equals", value: "malignancy", required: true }
          },
          {
            id: "INC-02",
            category: "Performance Status",
            criterion: "ECOG performance status 0 or 1.",
            parsed_rules: { variable: "ecog_ps", operator: "lte", value: 1, required: true }
          }
        ],
        exclusion_criteria: [
          {
            id: "EXC-01",
            category: "Safety",
            criterion: "Active untreated central nervous system metastases.",
            parsed_rules: { variable: "active_cns_metastases", operator: "equals", value: false, required: true }
          }
        ]
      };
      onAddProtocol(newTrial);
      setUploadStatus(`Successfully parsed & indexed ${files[0].name}!`);
      setTimeout(() => setUploadStatus(null), 3000);
    }, 800);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 m-0">Step 1: Clinical Trial Protocol Documents</h2>
          <p className="text-sm text-slate-600 m-0 mt-1">
            Upload new protocol PDFs or review the {protocols.length} indexed oncology trials in the knowledge base.
          </p>
        </div>

        <button
          id="proceed-step-2-btn"
          onClick={onNext}
          className="inline-flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm px-4 py-2.5 rounded-lg shadow-sm transition-all"
        >
          <span>Next: Patient Profile</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Zone */}
        <div className="lg:col-span-1 space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const files = e.dataTransfer.files;
              if (files && files.length > 0) {
                // Reuse the file-input handler by synthesising a ChangeEvent
                const synth = { target: { files } } as unknown as React.ChangeEvent<HTMLInputElement>;
                handleFileUpload(synth);
              }
            }}
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-all bg-white ${
              dragOver ? "border-teal-500 bg-teal-50/50" : "border-slate-300 hover:border-teal-400"
            }`}
          >
            <div className="w-12 h-12 mx-auto rounded-full bg-teal-50 flex items-center justify-center text-teal-600 mb-3">
              <Upload className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-semibold text-slate-800 mb-1">Upload Protocol Documents</h3>
            <p className="text-xs text-slate-500 mb-4">Drag and drop protocol PDFs or click to browse</p>

            <label
              htmlFor="pdf-upload-input"
              className="inline-flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold px-4 py-2 rounded-lg cursor-pointer transition-colors border border-slate-300"
            >
              <PlusCircle className="w-4 h-4 text-teal-600" />
              <span>Select PDF / TXT File</span>
            </label>
            <input
              id="pdf-upload-input"
              type="file"
              accept=".pdf,.txt"
              className="hidden"
              onChange={handleFileUpload}
            />

            {uploadStatus && (
              <div className="mt-3 text-xs text-teal-700 font-medium bg-teal-50 p-2 rounded border border-teal-200">
                {uploadStatus}
              </div>
            )}
          </div>

          <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 text-xs text-slate-600 space-y-2">
            <div className="flex items-center gap-2 font-semibold text-slate-800">
              <Shield className="w-4 h-4 text-teal-600" />
              <span>RAG Protocol Chunking</span>
            </div>
            <p>
              Each uploaded protocol is segmented into criterion chunks, vectorized using clinical semantic embeddings, and stored in the vector database for RAG retrieval.
            </p>
          </div>
        </div>

        {/* Protocols List */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">
              Indexed Protocol Library ({protocols.length})
            </h3>
            <span className="text-xs text-slate-500">Pre-loaded synthetic trials</span>
          </div>

          <div className="space-y-3">
            {protocols.map((p) => (
              <div
                key={p.trial_id}
                className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs hover:shadow-xs transition-shadow"
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-mono font-bold text-teal-700 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded">
                        {p.trial_id}
                      </span>
                      <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                        {p.phase}
                      </span>
                      <span className="text-xs text-slate-500 truncate max-w-xs">
                        {p.drug_modality}
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-slate-900 m-0">
                      {p.trial_title}
                    </h4>
                    <p className="text-xs text-teal-800 font-medium mt-1 mb-2">
                      Indication: {p.condition}
                    </p>
                    <p className="text-xs text-slate-600 line-clamp-2">
                      {p.summary}
                    </p>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-4">
                    <span className="flex items-center gap-1 text-emerald-700 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {p.inclusion_criteria.length} Inclusion Rules
                    </span>
                    <span className="flex items-center gap-1 text-rose-700 font-medium">
                      <FileText className="w-3.5 h-3.5" />
                      {p.exclusion_criteria.length} Exclusion Rules
                    </span>
                  </div>
                  <span className="text-slate-400">Sponsor: {p.sponsor}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
