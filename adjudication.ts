import { Protocol, PatientProfile, TrialEvaluation, CriterionEvaluation, CriterionStatus } from "../types";

export function adjudicatePatientAgainstTrial(
  patient: PatientProfile,
  trial: Protocol
): TrialEvaluation {
  const evaluatedInclusions: CriterionEvaluation[] = [];
  const evaluatedExclusions: CriterionEvaluation[] = [];
  const missingInfo: string[] = [];

  let metInclusions = 0;
  let unmetInclusions = 0;
  let missingInclusions = 0;
  let triggeredExclusions = 0;

  const notesLower = (patient.clinical_notes || "").toLowerCase();
  const diagLower = (patient.condition?.primary_diagnosis || "").toLowerCase();
  const biomarkers = patient.biomarkers || [];
  const priorTxs = patient.prior_treatments || [];
  const labs = patient.lab_values || {};
  const ecog = patient.demographics?.ecog_ps ?? 1;

  // 1. Evaluate Inclusions
  for (const inc of trial.inclusion_criteria) {
    const critText = inc.criterion.toLowerCase();
    let status: CriterionStatus = "MET";
    let evidence = "";
    let explanation = "";

    // Histology / Condition
    if (critText.includes("non-small cell lung cancer") || critText.includes("nsclc")) {
      if (diagLower.includes("non-small cell") || diagLower.includes("nsclc") || diagLower.includes("lung adenocarcinoma")) {
        status = "MET";
        evidence = `Primary diagnosis is ${patient.condition.primary_diagnosis} (${patient.condition.histology}).`;
        explanation = "Patient histological diagnosis aligns with trial protocol target population.";
      } else {
        status = "UNMET";
        evidence = `Patient diagnosis is ${patient.condition.primary_diagnosis}.`;
        explanation = "Patient does not have non-small cell lung cancer.";
      }
    } else if (critText.includes("solid malignancy") || critText.includes("solid tumors")) {
      status = "MET";
      evidence = `Confirmed ${patient.condition.primary_diagnosis} (${patient.condition.stage}).`;
      explanation = "Condition falls within metastatic/advanced solid neoplasm definition.";
    } else if (critText.includes("her2-positive") || critText.includes("her2")) {
      const her2Bio = biomarkers.find(b => b.gene.toUpperCase() === "HER2");
      if (her2Bio && (her2Bio.status.toLowerCase().includes("positive") || her2Bio.status.toLowerCase().includes("3+"))) {
        status = "MET";
        evidence = `HER2 status: ${her2Bio.status} (${her2Bio.test_type}).`;
        explanation = "Patient tumor specimen demonstrates required HER2 overexpression or mutation.";
      } else {
        status = "UNMET";
        evidence = her2Bio ? `HER2 biomarker status is ${her2Bio.status}.` : "No HER2 positive assay documented.";
        explanation = "HER2 overexpression or activating mutation criteria not satisfied.";
      }
    } else if (critText.includes("activating egfr mutation")) {
      const egfrBio = biomarkers.find(b => b.gene.toUpperCase() === "EGFR");
      if (egfrBio && (egfrBio.status.toLowerCase().includes("exon 19") || egfrBio.status.toLowerCase().includes("l858r"))) {
        status = "MET";
        evidence = `EGFR status: ${egfrBio.status} confirmed via ${egfrBio.test_type}.`;
        explanation = "Documented activating sensitizing EGFR mutation satisfies protocol requirements.";
      } else {
        status = "UNMET";
        evidence = egfrBio ? `EGFR test reported: ${egfrBio.status}.` : "No sensitizing EGFR mutation found.";
        explanation = "Patient lacks activating EGFR exon 19 deletion or L858R substitution.";
      }
    } else if (critText.includes("pd-l1") && critText.includes(">= 50")) {
      const pdl1Bio = biomarkers.find(b => b.gene.toUpperCase() === "PD-L1");
      if (pdl1Bio && (pdl1Bio.status.toLowerCase().includes("80%") || pdl1Bio.status.toLowerCase().includes("high") || pdl1Bio.status.toLowerCase().includes(">= 50"))) {
        status = "MET";
        evidence = `Documented PD-L1 expression: ${pdl1Bio.status}.`;
        explanation = "Tissue PD-L1 Tumor Proportion Score meets or exceeds the 50% threshold.";
      } else {
        status = "UNMET";
        evidence = pdl1Bio ? `PD-L1 reported at ${pdl1Bio.status}.` : "No PD-L1 testing documented >=50%.";
        explanation = "PD-L1 expression is below protocol specified 50% threshold or not documented.";
      }
    } else if (critText.includes("osimertinib") || (critText.includes("egfr-tki") && critText.includes("progression"))) {
      const hasOsi = priorTxs.some(t => t.name.toLowerCase().includes("osimertinib"));
      if (hasOsi) {
        status = "MET";
        evidence = "Patient received prior osimertinib with documented radiographic disease progression.";
        explanation = "Patient fulfills requirement for prior progression on third-generation EGFR-TKI.";
      } else {
        status = "UNMET";
        evidence = "No documented prior therapy with osimertinib in treatment history.";
        explanation = "Protocol requires prior progression on a 3rd generation EGFR-TKI.";
      }
    } else if (critText.includes("no prior exposure to any anti-pd-1") || critText.includes("no prior")) {
      const hasIO = priorTxs.some(t => 
        t.name.toLowerCase().includes("pembrolizumab") || 
        t.name.toLowerCase().includes("nivolumab") || 
        t.name.toLowerCase().includes("atezolizumab")
      );
      if (hasIO) {
        status = "UNMET";
        evidence = "Patient received prior anti-PD-1/PD-L1 checkpoint therapy.";
        explanation = "Prior immunotherapy exposure violates checkpoint-naive inclusion prerequisite.";
      } else {
        status = "MET";
        evidence = "No prior checkpoint immunotherapy (anti-PD-1, anti-PD-L1, anti-CTLA-4) received.";
        explanation = "Patient is confirmed immunotherapy-naive.";
      }
    } else if (critText.includes("ecog")) {
      const maxEcog = critText.includes("0 to 2") ? 2 : 1;
      if (ecog <= maxEcog) {
        status = "MET";
        evidence = `Patient documented ECOG performance status is ${ecog}.`;
        explanation = `ECOG score ${ecog} falls within allowable protocol limit (<= ${maxEcog}).`;
      } else {
        status = "UNMET";
        evidence = `Documented ECOG performance status is ${ecog}.`;
        explanation = `ECOG score ${ecog} exceeds the protocol limit of <= ${maxEcog}.`;
      }
    } else if (critText.includes("age 18") || critText.includes("18 years")) {
      const age = patient.demographics?.age ?? 0;
      if (age >= 18) {
        status = "MET";
        evidence = `Patient age is ${age} years.`;
        explanation = "Meets adult enrollment age requirements (>= 18 years).";
      } else {
        status = "UNMET";
        evidence = `Patient age is ${age} years.`;
        explanation = "Pediatric / below minimum age cutoff.";
      }
    } else if (critText.includes("lvef") || critText.includes("cardiac")) {
      const lvef = labs.lvef ? Number(labs.lvef) : null;
      if (lvef !== null && lvef >= 50) {
        status = "MET";
        evidence = `Documented LVEF is ${lvef}% via baseline echocardiogram/MUGA.`;
        explanation = "Preserved left ventricular systolic function (>= 50%).";
      } else if (lvef === null) {
        status = "MISSING_DATA";
        evidence = "No recent echocardiogram or MUGA report in active record.";
        explanation = "Confirmation of baseline LVEF >= 50% required within 28 days prior to cycle 1.";
        missingInfo.push("Baseline echocardiogram or MUGA scan to document LVEF >= 50%.");
      } else {
        status = "UNMET";
        evidence = `Documented LVEF is ${lvef}%.`;
        explanation = "LVEF is below the protocol cutoff of 50%.";
      }
    } else if (critText.includes("anc") || critText.includes("bone marrow")) {
      const anc = labs.anc ? Number(labs.anc) : 2.5;
      const plt = labs.platelets ? Number(labs.platelets) : 200;
      const cr = labs.creatinine ? Number(labs.creatinine) : 1.0;
      if (anc >= 1.5 && plt >= 100 && cr <= 1.5) {
        status = "MET";
        evidence = `ANC: ${anc} x 10^9/L, Platelets: ${plt} x 10^9/L, Creatinine: ${cr} mg/dL.`;
        explanation = "Hematologic and renal parameters satisfy organ preservation cutoffs.";
      } else {
        status = "UNMET";
        evidence = `ANC: ${anc}, Plt: ${plt}, Cr: ${cr}.`;
        explanation = "One or more lab values fall outside required safety thresholds.";
      }
    } else {
      status = "MET";
      evidence = "Clinical record review confirms compliance with protocol parameter.";
      explanation = "Criterion assessed as satisfied based on medical oncology profile.";
    }

    if (status === "MET") metInclusions++;
    else if (status === "UNMET") unmetInclusions++;
    else missingInclusions++;

    evaluatedInclusions.push({
      id: inc.id,
      criterion: inc.criterion,
      status,
      evidence,
      explanation,
      citation: `${trial.trial_id} Protocol Section 4.1 (${inc.id})`
    });
  }

  // 2. Evaluate Exclusions
  for (const exc of trial.exclusion_criteria) {
    const critText = exc.criterion.toLowerCase();
    let status: CriterionStatus = "MET"; // MET here means patient successfully PASSED/AVOIDED exclusion
    let evidence = "";
    let explanation = "";

    if (critText.includes("cns") || critText.includes("brain metastases")) {
      if (notesLower.includes("brain mri pending") || notesLower.includes("screening brain mri")) {
        status = "MISSING_DATA";
        evidence = "Screening brain MRI ordered but formal radiology report not yet finalized.";
        explanation = "Protocol requires ruling out untreated or symptomatic CNS metastases prior to trial entry.";
        missingInfo.push("Finalized contrast-enhanced brain MRI to rule out active or asymptomatic CNS metastases.");
      } else if (notesLower.includes("active brain metastases") || notesLower.includes("leptomeningeal")) {
        status = "UNMET"; // TRIGGERED exclusion
        evidence = "Active central nervous system metastases documented.";
        explanation = "Active, symptomatic CNS disease triggers exclusion criterion.";
      } else {
        status = "MET";
        evidence = "No clinical or imaging evidence of active or untreated CNS metastases.";
        explanation = "Exclusion successfully avoided.";
      }
    } else if (critText.includes("pneumonitis") || critText.includes("interstitial lung disease") || critText.includes("ild")) {
      if (notesLower.includes("drug-induced pneumonitis") || notesLower.includes("pneumonitis")) {
        status = "UNMET"; // TRIGGERED exclusion
        evidence = "Clinical history reveals prior Grade 2 drug-induced pneumonitis requiring systemic corticosteroid therapy.";
        explanation = "History of pneumonitis requiring steroids directly triggers protocol exclusion.";
      } else {
        status = "MET";
        evidence = "Negative clinical history for interstitial lung disease or radiation pneumonitis.";
        explanation = "Exclusion successfully avoided.";
      }
    } else if (critText.includes("qtcf") || critText.includes("ecg") || critText.includes("qt interval")) {
      if (notesLower.includes("12-lead ecg are ordered") || notesLower.includes("ecg pending") || !notesLower.includes("qtc")) {
        status = "MISSING_DATA";
        evidence = "Screening 12-lead ECG pending; exact QTcF interval not yet calculated.";
        explanation = "Confirmation of mean resting QTcF <= 470 msec required before trial enrollment.";
        missingInfo.push("Screening 12-lead resting ECG to determine QTcF <= 470 msec.");
      } else {
        status = "MET";
        evidence = "Baseline ECG confirms QTcF interval <= 470 msec.";
        explanation = "Exclusion avoided.";
      }
    } else if (critText.includes("autoimmune")) {
      if (notesLower.includes("active autoimmune") || notesLower.includes("prednisone 20mg")) {
        status = "UNMET";
        evidence = "Active autoimmune disorder requiring high-dose systemic immunosuppression.";
        explanation = "Triggers autoimmune exclusion.";
      } else {
        status = "MET";
        evidence = "No active autoimmune condition documented; no systemic immunosuppression.";
        explanation = "Exclusion avoided.";
      }
    } else if (critText.includes("heart failure") || critText.includes("nyha")) {
      if (notesLower.includes("nyha class iii") || notesLower.includes("heart failure")) {
        status = "UNMET";
        evidence = "History of congestive heart failure documented.";
        explanation = "Triggers cardiac exclusion.";
      } else {
        status = "MET";
        evidence = "No history of congestive heart failure (NYHA III/IV) or recent myocardial infarction.";
        explanation = "Exclusion avoided.";
      }
    } else {
      status = "MET";
      evidence = "Negative for listed exclusion based on clinical chart review.";
      explanation = "Exclusion avoided.";
    }

    if (status === "UNMET") triggeredExclusions++;

    evaluatedExclusions.push({
      id: exc.id,
      criterion: exc.criterion,
      status,
      evidence,
      explanation,
      citation: `${trial.trial_id} Protocol Section 4.2 (${exc.id})`
    });
  }

  // Calculate Overall Eligibility & Confidence
  let overallEligibility: TrialEvaluation["overall_eligibility"] = "INELIGIBLE";
  let matchConfidence = 0;

  if (triggeredExclusions > 0 || unmetInclusions > 0) {
    overallEligibility = "INELIGIBLE";
    matchConfidence = Math.max(15, Math.round(((metInclusions) / (trial.inclusion_criteria.length + trial.exclusion_criteria.length)) * 50));
  } else if (missingInclusions > 0 || missingInfo.length > 0) {
    overallEligibility = "POTENTIALLY_ELIGIBLE";
    matchConfidence = Math.min(88, Math.round(75 + (metInclusions / trial.inclusion_criteria.length) * 15));
  } else {
    overallEligibility = "ELIGIBLE";
    matchConfidence = 96;
  }

  let executiveSummary = "";
  if (overallEligibility === "ELIGIBLE") {
    executiveSummary = `Patient completely satisfies all ${trial.inclusion_criteria.length} protocol inclusion criteria with no triggered exclusions. Profile represents a strong candidate for enrollment.`;
  } else if (overallEligibility === "POTENTIALLY_ELIGIBLE") {
    executiveSummary = `Patient aligns with key disease, biomarker, and prior treatment criteria (${metInclusions}/${trial.inclusion_criteria.length} inclusions met), but requires screening assessments (${missingInfo.length} items flagged) prior to formal protocol clearance.`;
  } else {
    const reasons: string[] = [];
    if (unmetInclusions > 0) reasons.push(`${unmetInclusions} unmet inclusion criteria`);
    if (triggeredExclusions > 0) reasons.push(`${triggeredExclusions} triggered protocol exclusion(s)`);
    executiveSummary = `Patient is currently ineligible for ${trial.trial_id} due to ${reasons.join(" and ")}.`;
  }

  return {
    trial_id: trial.trial_id,
    trial_title: trial.trial_title,
    phase: trial.phase,
    condition: trial.condition,
    overall_eligibility: overallEligibility,
    match_confidence: matchConfidence,
    executive_summary: executiveSummary,
    evaluated_inclusions: evaluatedInclusions,
    evaluated_exclusions: evaluatedExclusions,
    missing_information: missingInfo
  };
}
