# Clinical Scenario Workflow - Quick Start Guide

## What's New

Your clinical trial eligibility matcher now supports **Scenario-Based Matching** for synthetic patient research workflows.

## How to Use

### 1. Start the Application
```bash
python -m streamlit run app.py
```

### 2. Select Workflow Mode
When the app opens, you'll see two options:
- **Traditional Patient Profile** (existing workflow)
- **Scenario-Based Matching** (NEW!)

Click **"Scenario-Based Matching"**

### 3. Enter a Patient Scenario
Describe a synthetic patient in natural language:

```
Example:
43-year-old male with hypertension and diabetes. 
Blood pressure is 163/83. He is a non-smoker and has BMI 18.1. 
Evaluate him against the available clinical trials.
```

### 4. Click "Analyze Patient & Find Trials"
The system will:
- Extract patient attributes (age, gender, diagnosis, etc.)
- Search for relevant clinical trials
- Evaluate each trial's eligibility criteria
- Display detailed results

### 5. Review Results
For each trial, you'll see:
- **Overall Status**: Potential Match / Needs Review / Potential Mismatch
- **Inclusion Criteria**: Each criterion shows MATCH ✓ / NOT MATCH ✗ / UNKNOWN ?
- **Exclusion Criteria**: Shows what disqualifying factors patient avoids/triggers
- **Patient Evidence**: What we know about the patient
- **Reasoning**: Why we made each decision
- **Missing Information**: Data needed for further review

### 6. Export Report
Click to download:
- Markdown report (.md)
- Formatted HTML report (.html)

## Key Features

✅ **Never Assumes Missing Data**
- If information isn't in the scenario, it's marked UNKNOWN
- No invented medical information
- Researcher must provide additional data for confirmation

✅ **Evidence-Based Decisions**
- Every criterion decision includes patient evidence
- Every decision includes reasoning
- You can verify conclusions independently

✅ **Research-Grade Terminology**
- "POTENTIAL MATCH" (not "Eligible")
- "POTENTIAL MISMATCH" (not "Ineligible")
- Clear reminder: Final eligibility determined by qualified clinical personnel

✅ **Preserves Existing Functionality**
- Traditional workflow unchanged
- Choose scenario or traditional based on your need
- All existing features work as before

## Example Scenarios

### Scenario 1: Hypertension & Diabetes
```
43-year-old male with hypertension and diabetes. 
Blood pressure is 163/83. He is a non-smoker and has BMI 18.1.
```

### Scenario 2: Breast Cancer
```
55-year-old female diagnosed with breast cancer. 
She is diabetic and currently receiving treatment.
```

### Scenario 3: Lung Cancer (Limited Info)
```
60-year-old male with lung cancer. 
Former smoker. BMI 24.5. No diabetes. 
Treatment information unavailable.
```

## What Gets Extracted

From your scenario, the system automatically identifies:
- **Age** (e.g., "43-year-old" → 43)
- **Gender** (e.g., "male" → Male)
- **Diagnosis** (e.g., "diabetes" → Diabetes)
- **Comorbidities** (e.g., "hypertension" → Hypertension)
- **Smoking Status** (e.g., "non-smoker")
- **Biomarkers** (if mentioned)
- **Prior Treatments** (if mentioned)

Missing information is marked **UNKNOWN** - never assumed.

## Criterion Evaluation Semantics

For each trial criterion:

| Status | Meaning |
|--------|---------|
| **MATCH** | Patient information clearly satisfies this criterion |
| **NOT MATCH** | Patient information conflicts with or fails this criterion |
| **UNKNOWN** | Insufficient patient information to determine |

### Inclusion Criteria Example
- Criterion: "Age >= 18 years"
- Patient: 43 years old
- Status: **MATCH** ✓
- Reasoning: Age 43 meets the required threshold

### Exclusion Criteria Example
- Criterion: "No active brain metastases"
- Patient: "Brain imaging status not mentioned"
- Status: **UNKNOWN** ?
- Reasoning: CNS metastasis status unclear - brain MRI required

## Missing Information

After evaluation, you'll see a section showing what data is needed:

```
⚠️ Information Needed for Further Review:
- ECOG performance status
- Recent CBC with diff and serum creatinine labs
- CNS metastasis status (brain MRI)
```

This helps you know what to collect before final eligibility determination.

## Trial Status Meanings

- **POTENTIAL MATCH** 🟢: Good criterion alignment, likely candidate for further review
- **NEEDS REVIEW** 🟡: Mixed results or missing key information, requires additional work
- **POTENTIAL MISMATCH** 🔴: Significant criterion failures, likely not suitable

## Important Notes

⚠️ **Research Prototype Only**
- This tool is for research and educational use with synthetic patient data
- Final eligibility determination must be made by qualified clinical research personnel
- All decisions should be verified against actual trial protocols
- Not for clinical decision-making on real patients

✅ **Synthetic Data Only**
- Designed strictly for synthetic/de-identified patient scenarios
- Use for research workflow validation
- Supports academic and investigational research

## Testing the Workflow

A test script is included:

```bash
python test_scenario_workflow.py
```

This runs 3 example scenarios and displays results in the terminal.

## Troubleshooting

**"No trials available"**
- Ensure sample_data/sample_protocols.json exists
- Check that protocols are loaded in the sidebar
- Click "Reset to Default 3 Synthetic Trials" if needed

**"UNKNOWN status for many criteria"**
- This is expected! Scenarios don't always have complete medical info
- Use "Information Needed" section to guide follow-up questions
- Collect missing data and re-analyze

**App crashes or errors**
- Check that all imports are working: `python -c "from matcher import evaluate_scenario_against_trials; print('OK')"`
- Verify LLM provider is configured (or use 'local-heuristic')
- Review error message in browser console

## Next Steps

1. ✅ Application is running at http://localhost:8501
2. Select "Scenario-Based Matching" workflow
3. Enter a patient scenario
4. Review results and evidence
5. Export markdown/HTML report
6. Verify with qualified personnel

---

**Ready to test! The scenario workflow is fully functional and integrated into your clinical trial matcher.**
