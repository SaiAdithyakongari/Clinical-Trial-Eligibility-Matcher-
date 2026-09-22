export type CriterionStatus = "MET" | "UNMET" | "MISSING_DATA";

export type OverallEligibility = "ELIGIBLE" | "POTENTIALLY_ELIGIBLE" | "INELIGIBLE";

export interface Criterion {
  id: string;
  category: string;
  criterion: string;
  parsed_rules: {
    variable: string;
    operator: string;
    value: string | number | boolean;
    required: boolean;
  };
}

export interface Protocol {
  trial_id: string;
  trial_title: string;
  phase: string;
  condition: string;
  drug_modality: string;
  sponsor: string;
  summary: string;
  inclusion_criteria: Criterion[];
  exclusion_criteria: Criterion[];
}

export interface PatientProfile {
  id: string;
  name: string;
  demographics: {
    age: number;
    gender: string;
    ecog_ps: number;
  };
  condition: {
    primary_diagnosis: string;
    stage: string;
    histology: string;
  };
  biomarkers: Array<{
    gene: string;
    status: string;
    test_type: string;
  }>;
  prior_treatments: Array<{
    name: string;
    type: string;
    response: string;
  }>;
  lab_values: Record<string, string | number>;
  cns_metastases?: string;
  description?: string;
  clinical_notes: string;
}

export interface CriterionEvaluation {
  id: string;
  criterion: string;
  status: CriterionStatus;
  evidence: string;
  explanation: string;
  citation: string;
}

export interface TrialEvaluation {
  trial_id: string;
  trial_title: string;
  phase: string;
  condition: string;
  overall_eligibility: OverallEligibility;
  match_confidence: number;
  executive_summary: string;
  evaluated_inclusions: CriterionEvaluation[];
  evaluated_exclusions: CriterionEvaluation[];
  missing_information: string[];
}
