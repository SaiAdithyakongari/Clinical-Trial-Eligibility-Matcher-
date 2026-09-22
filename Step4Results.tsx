import React, { useState } from "react";
import { TrialEvaluation, CriterionStatus, PatientProfile } from "../types";
import { generateMarkdownExport, downloadFile } from "../utils/reportExport";
import {
  CheckCircle2,
  AlertCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  FileCheck,
  ArrowRight,
  ArrowLeft,
  Filter,
  Download,
  FileText
} from "lucide-react";

interface Step4ResultsProps {
  evaluations: TrialEvaluation[];
  patient?: PatientProfile;
  onPrev: () => void;
  onNext?: () => void;
}

export const Step4Results: React.FC<Step4ResultsProps> = ({ evaluations, patient, onPrev, onNext }) => {
  const [filter, setFilter] = useState<"ALL" | "ELIGIBLE" | "POTENTIALLY_ELIGIBLE" | "INELIGIBLE">("ALL");
  const [expandedId, setExpandedId] = useState<string | null>(evaluations[0]?.trial_id || null);

  const eligibleCount = evaluations.filter((e) => e.overall_eligibility === "ELIGIBLE").length;
  const potentialCount = evaluations.filter((e) => e.overall_eligibility === "POTENTIALLY_ELIGIBLE").length;
  const ineligibleCount = evaluations.filter((e) => e.overall_eligibility === "INELIGIBLE").length;

  const filtered = evaluations.filter((e) => {
    if (filter === "ALL") return true;
    return e.overall_eligibility === filter;
  });

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  const handleDownloadMarkdown = () => {
    const dummyPatient: PatientProfile = patient || {
      id: "SYNTHETIC-PT-8092",
      name: "Synthetic Patient",
      demographics: { age: 62, gender: "Female", ecog_ps: 1 },
      condition: { primary_diagnosis: "Non-Small Cell Lung Cancer", stage: "Stage IV", histology: "Adenocarcinoma" },
      biomarkers: [],
      prior_treatments: [],
      laboratory_values: {},
      raw_notes: ""
    };
    const mdContent = generateMarkdownExport(dummyPatient, evaluations);
    downloadFile(mdContent, `clinical_trial_adjudication_${dummyPatient.id}.md`, "text/markdown");
  };

  const handleDownloadHtml = () => {
    const dummyPatient: PatientProfile = patient || {
      id: "SYNTHETIC-PT-8092",
      name: "Synthetic Patient",
      demographics: { age: 62, gender: "Female", ecog_ps: 1 },
      condition: { primary_diagnosis: "Non-Small Cell Lung Cancer", stage: "Stage IV", histology: "Adenocarcinoma" },
      biomarkers: [],
      prior_treatments: [],
      laboratory_values: {},
      raw_notes: ""
    };

    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Clinical Trial Eligibility Matcher - ${dummyPatient.id}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; color: #1E293B; max-width: 850px; margin: 40px auto; padding: 0 20px; }
    h1, h2, h3 { color: #0B192C; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .badge-eligible { background: #DCFCE7; color: #166534; }
    .badge-potential { background: #FEF3C7; color: #92400E; }
    .badge-ineligible { background: #FEE2E2; color: #991B1B; }
    .card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin-bottom: 20px; }
    .warning { background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 12px 16px; margin: 12px 0; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
    th { background: #F1F5F9; text-align: left; padding: 8px; border-bottom: 2px solid #CBD5E1; }
    td { padding: 8px; border-bottom: 1px solid #E2E8F0; }
  </style>
</head>
<body>
  <h1>Clinical Trial Adjudication Report</h1>
  <p><strong>Patient:</strong> ${dummyPatient.id} (${dummyPatient.name}) | <strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
  <p><strong>Diagnosis:</strong> ${dummyPatient.condition.primary_diagnosis} (${dummyPatient.condition.stage})</p>
  <hr>
  <h2>Evaluated Trials Summary</h2>
  ${evaluations.map(e => `
    <div class="card">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h3>${e.trial_id}: ${e.trial_title}</h3>
        <span class="badge ${e.overall_eligibility === 'ELIGIBLE' ? 'badge-eligible' : (e.overall_eligibility === 'POTENTIALLY_ELIGIBLE' ? 'badge-potential' : 'badge-ineligible')}">
          ${e.overall_eligibility} (${e.match_confidence}% Match)
        </span>
      </div>
      <p><strong>Clinical Review Rationale:</strong> ${e.executive_summary}</p>
      ${e.missing_information && e.missing_information.length > 0 ? `
        <div class="warning">
          <strong>⚠️ Missing Information Needed to Confirm Eligibility:</strong>
          <ul>${e.missing_information.map(m => `<li>${m}</li>`).join('')}</ul>
        </div>
      ` : ''}
    </div>
  `).join('')}
</body>
</html>`;
    downloadFile(html, `clinical_trial_adjudication_${dummyPatient.id}.html`, "text/html");
  };

  const getStatusBadge = (status: TrialEvaluation["overall_eligibility"]) => {
    if (status === "ELIGIBLE") {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Likely Eligible
        </span>
      );
    }
    if (status === "POTENTIALLY_ELIGIBLE") {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-100 text-amber-900 border border-amber-300">
          <AlertTriangle className="w-3.5 h-3.5" />
          Insufficient Data / Potential
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-300">
        <XCircle className="w-3.5 h-3.5" />
        Likely Ineligible
      </span>
    );
  };

  const getCriterionBadge = (status: CriterionStatus, isExclusion: boolean = false) => {
    if (status === "MET") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="w-3.5 h-3.5" />
          {isExclusion ? "✅ Passed (not excluded)" : "✅ Matched"}
        </span>
      );
    }
    if (status === "UNMET") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
          <XCircle className="w-3.5 h-3.5" />
          {isExclusion ? "❌ Failed (excluded)" : "❌ Not Matched"}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
        <AlertCircle className="w-3.5 h-3.5" />
        {isExclusion ? "⚠️ Needs Verification" : "⚠️ Missing Data"}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header and Nav */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 m-0">Step 4: Adjudication Results & Clinical Explanations</h2>
          <p className="text-sm text-slate-600 m-0 mt-1">
            Review detailed criterion matching, confidence scores, evidence rationales, and protocol citations.
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
            id="proceed-step-5-btn"
            onClick={onNext}
            className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold px-4 py-2 rounded-lg shadow-sm transition-all"
          >
            <span>Next: Export Report</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs">
          <div className="text-xs font-semibold text-slate-500 uppercase">Evaluated Protocols</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{evaluations.length}</div>
          <div className="text-xs text-slate-400 mt-0.5">Full criteria comparisons</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-emerald-200 shadow-2xs">
          <div className="text-xs font-semibold text-emerald-700 uppercase">Eligible Matches</div>
          <div className="text-2xl font-bold text-emerald-800 mt-1">{eligibleCount}</div>
          <div className="text-xs text-emerald-600 mt-0.5">All criteria satisfied</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-amber-200 shadow-2xs">
          <div className="text-xs font-semibold text-amber-700 uppercase">Action Required</div>
          <div className="text-2xl font-bold text-amber-800 mt-1">{potentialCount}</div>
          <div className="text-xs text-amber-600 mt-0.5">Missing labs or scans</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 shadow-2xs">
          <div className="text-xs font-semibold text-rose-700 uppercase">Ineligible</div>
          <div className="text-2xl font-bold text-rose-800 mt-1">{ineligibleCount}</div>
          <div className="text-xs text-rose-600 mt-0.5">Unmet or exclusion hit</div>
        </div>
      </div>

      {/* Top Download Report Action Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h4 className="text-sm font-bold text-slate-900 m-0">📥 Download Consolidated Clinical Adjudication Report</h4>
          <p className="text-xs text-slate-500 m-0 mt-0.5">
            Export all matching results, eligibility criteria comparisons, and citations directly from this page.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownloadMarkdown}
            className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 text-xs font-semibold px-3 py-2 rounded-lg transition-colors"
          >
            <FileText className="w-3.5 h-3.5 text-slate-500" />
            <span>Markdown (.md)</span>
          </button>
          <button
            onClick={handleDownloadHtml}
            className="inline-flex items-center gap-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-2xs transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>HTML / Printable</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 pb-1 border-b border-slate-200">
        <Filter className="w-4 h-4 text-slate-400 mr-1" />
        {(["ALL", "ELIGIBLE", "POTENTIALLY_ELIGIBLE", "INELIGIBLE"] as const).map((tab) => (
          <button
            key={tab}
            id={`filter-tab-${tab}`}
            onClick={() => setFilter(tab)}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors ${
              filter === tab
                ? "bg-slate-900 text-white"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {tab === "ALL" ? "All Trials" : tab.replace("_", " ")}
          </button>
        ))}
      </div>

      {/* Trial Cards */}
      <div className="space-y-4">
        {filtered.map((evalItem) => {
          const isExpanded = expandedId === evalItem.trial_id;

          const summaryLine = evalItem.overall_eligibility === "ELIGIBLE"
            ? "Likely Eligible — All evaluated inclusion criteria are satisfied with zero triggered exclusion conditions."
            : evalItem.overall_eligibility === "POTENTIALLY_ELIGIBLE"
            ? "Insufficient Data / Action Required — Potential candidate pending supplementary diagnostic or laboratory workup."
            : "Likely Ineligible — Core inclusion criteria unmet or disqualifying exclusion conditions present.";

          const summaryBg = evalItem.overall_eligibility === "ELIGIBLE"
            ? "bg-emerald-50/80 border-emerald-200 text-emerald-900"
            : evalItem.overall_eligibility === "POTENTIALLY_ELIGIBLE"
            ? "bg-amber-50/80 border-amber-200 text-amber-900"
            : "bg-rose-50/80 border-rose-200 text-rose-900";

          return (
            <div
              key={evalItem.trial_id}
              className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden transition-all"
            >
              {/* Overall Summary Line at top of each trial card */}
              <div className={`px-5 py-2.5 text-xs font-semibold border-b ${summaryBg} flex items-center justify-between`}>
                <span>{summaryLine}</span>
                <span className="text-[11px] font-bold opacity-80 uppercase tracking-wider">
                  {evalItem.overall_eligibility.replace("_", " ")}
                </span>
              </div>

              {/* Card Header Summary */}
              <div
                onClick={() => toggleExpand(evalItem.trial_id)}
                className="p-5 cursor-pointer hover:bg-slate-50/50 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 max-w-3xl">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-teal-800 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded">
                      {evalItem.trial_id}
                    </span>
                    <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                      {evalItem.phase}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">
                      {evalItem.condition}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 m-0">
                    {evalItem.trial_title}
                  </h3>
                  <p className="text-xs text-slate-600 m-0">
                    <strong>Review Rationale:</strong> {evalItem.executive_summary}
                  </p>
                </div>

                <div className="flex items-center justify-between md:justify-end gap-5 shrink-0 border-t md:border-t-0 pt-3 md:pt-0 border-slate-100">
                  <div className="text-right">
                    {getStatusBadge(evalItem.overall_eligibility)}
                    <div className="text-xs font-bold text-slate-700 mt-1.5 flex items-center justify-end gap-1.5">
                      <span>Match Confidence:</span>
                      <strong className="text-slate-900">{evalItem.match_confidence}%</strong>
                    </div>
                  </div>

                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>
              </div>

      {/* Match Progress Bar */}
              <div className="w-full bg-slate-100 h-1.5 overflow-hidden">
                <div
                  className={`h-full transition-all duration-700 ease-out ${
                    evalItem.overall_eligibility === "ELIGIBLE"
                      ? "bg-emerald-500"
                      : evalItem.overall_eligibility === "POTENTIALLY_ELIGIBLE"
                      ? "bg-amber-500"
                      : "bg-rose-400"
                  }`}
                  style={{ width: `${evalItem.match_confidence}%` }}
                />
              </div>

              {/* Expandable Criteria Details */}
              {isExpanded && (
                <div className="p-5 border-t border-slate-100 bg-slate-50/40 space-y-6">
                  {/* Missing Info Callout */}
                  {evalItem.missing_information && evalItem.missing_information.length > 0 && (
                    <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg">
                      <div className="flex items-center gap-2 text-amber-900 font-bold text-xs uppercase tracking-wider mb-1">
                        <AlertTriangle className="w-4 h-4 text-amber-600" />
                        <span>Required Actions & Missing Diagnostic Tests</span>
                      </div>
                      <ul className="text-xs text-amber-800 space-y-1 list-disc list-inside m-0">
                        {evalItem.missing_information.map((item, idx) => (
                          <li key={idx}><strong>{item}</strong></li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Inclusion Criteria Table */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-teal-600" />
                      <h4 className="text-sm font-bold text-slate-900 m-0">
                        Inclusion Criteria Breakdown ({evalItem.evaluated_inclusions.length})
                      </h4>
                    </div>

                    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs">
                      <div className="divide-y divide-slate-100">
                        {evalItem.evaluated_inclusions.map((inc) => (
                          <div key={inc.id} className="p-3.5 space-y-1.5 text-xs">
                            <div className="flex items-start justify-between gap-3">
                              <div className="font-semibold text-slate-800">
                                <span className="font-mono text-slate-500 mr-2">[{inc.id}]</span>
                                {inc.criterion}
                              </div>
                              {getCriterionBadge(inc.status, false)}
                            </div>
                            <div className="text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 space-y-0.5">
                              <div><strong>Patient Evidence:</strong> {inc.evidence}</div>
                              <div><strong>Clinical Rationale:</strong> {inc.explanation}</div>
                            </div>
                            <div className="text-[11px] text-slate-400 italic">
                              Citation: {inc.citation}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Exclusion Criteria Table */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <FileCheck className="w-4 h-4 text-teal-600" />
                      <h4 className="text-sm font-bold text-slate-900 m-0">
                        Exclusion Criteria Breakdown ({evalItem.evaluated_exclusions.length})
                      </h4>
                    </div>

                    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-2xs">
                      <div className="divide-y divide-slate-100">
                        {evalItem.evaluated_exclusions.map((exc) => (
                          <div key={exc.id} className="p-3.5 space-y-1.5 text-xs">
                            <div className="flex items-start justify-between gap-3">
                              <div className="font-semibold text-slate-800">
                                <span className="font-mono text-slate-500 mr-2">[{exc.id}]</span>
                                {exc.criterion}
                              </div>
                              {getCriterionBadge(exc.status, true)}
                            </div>
                            <div className="text-slate-600 bg-slate-50 p-2 rounded border border-slate-100 space-y-0.5">
                              <div><strong>Patient Evidence:</strong> {exc.evidence}</div>
                              <div><strong>Clinical Rationale:</strong> {exc.explanation}</div>
                            </div>
                            <div className="text-[11px] text-slate-400 italic">
                              Citation: {exc.citation}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

    </div>
  );
};
