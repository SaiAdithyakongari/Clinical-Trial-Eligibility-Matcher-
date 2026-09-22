# 🔬 Clinical Trial Eligibility Matcher
> **GenAI-Powered Clinical Research Decision-Support System**  
> Streamlit Web Application & RAG Grounding Pipeline for Clinical Protocol Adjudication.

---

## 📌 Project Overview
Clinical trial matching requires comparing patient records against lengthy, dense, and complex inclusion/exclusion criteria. This manual process is slow, error-prone, and causes clinical trial recruitment delays.

The **Clinical Trial Eligibility Matcher** automates this workflow using a **Retrieval-Augmented Generation (RAG)** pipeline grounded in clinical trial protocol documents. It enables researchers to upload protocol PDFs, input synthetic patient profiles, run criterion-by-criterion LLM adjudication with exact citations, flag missing clinical data, and export structured review reports.

---

## 🛠️ Architecture & Tech Stack

- **Core Language**: Python 3.10+
- **Frontend / Web UI**: Streamlit with custom deep navy/teal/white medical-tech styling (`#0B192C`, `#0D9488`, `#FFFFFF`), high-contrast inputs, animated progress tracking, and interactive expandable cards.
- **LLM Abstraction Layer (`llm_client.py`)**: Unified provider interface supporting:
  - **Google Gemini** (`gemini-3.5-flash`, `gemini-3.8-flash`) via `GEMINI_API_KEY`
  - **OpenAI** (`gpt-4o-mini`, `gpt-4o`) via `OPENAI_API_KEY`
  - **Anthropic** (`claude-3-5-sonnet`) via `ANTHROPIC_API_KEY`
  - **Local Heuristic Engine**: Deterministic clinical rule-based adjudication when running completely offline.
- **RAG & Vector Database (`vector_store.py`)**: Embedded cosine similarity search for candidate trial retrieval.
- **Embeddings Engine (`embeddings.py`)**: Supports Google Gemini embeddings (`gemini-embedding-2-preview`), Sentence-Transformers (`all-MiniLM-L6-v2`), and a built-in deterministic clinical semantic vectorizer.
- **PDF Extraction (`pdf_processing.py`)**: Extracts page text, metadata, and leverages LLMs to parse structured inclusion/exclusion criteria.
- **Adjudication Engine (`matcher.py`)**: Structures patient attributes, evaluates criterion-level status (`MET`, `UNMET`, `MISSING_DATA`), generates rationale, cites protocol sections, and computes match confidence.
- **Report Generator (`report_generator.py`)**: Exports comprehensive researcher review reports in Markdown (`.md`) and styled HTML / printable PDF formats.

---

## 📂 Project Structure

```
├── app.py                      # Main Streamlit web application & custom UI
├── pdf_processing.py           # PDF text extraction & LLM criteria parsing
├── embeddings.py               # Embeddings abstraction (Gemini, ST, Dense)
├── vector_store.py             # Vector database & cosine similarity index
├── llm_client.py               # Multi-provider LLM abstraction layer
├── matcher.py                  # Core patient structuring & criteria adjudication
├── report_generator.py         # Markdown & HTML adjudication reports
├── generate_sample_pdfs.py     # Generator for synthetic protocol PDFs
├── test_pipeline.py            # End-to-end pipeline verification test suite
├── requirements.txt            # Pinned dependencies
├── README.md                   # Setup guide and documentation
└── sample_data/
    ├── sample_protocols.json   # 3 curated oncology/solid tumor protocols
    ├── sample_patients.json    # 4 diverse synthetic patient profiles
    ├── NCT05423189_EGFR_NSCLC_Protocol.pdf
    ├── NCT04891120_PDL1_Immunotherapy_Protocol.pdf
    └── NCT05219903_HER2_Targeted_ADC_Protocol.pdf
```

---

## 🚀 How to Run Locally

### 1. Clone or Navigate to Project Directory
```bash
cd /path/to/clinical-trial-matcher
```

### 2. Create and Activate a Virtual Environment
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your LLM API Key (Optional / Recommended)
Set your preferred API key as an environment variable:
```bash
# Google Gemini (Default)
export GEMINI_API_KEY="your-gemini-api-key"

# OR OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# OR Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```
*(Note: You can also enter or override your API key directly in the web app sidebar at runtime, or run without an API key using the built-in local clinical heuristic engine.)*

### 5. Launch the Streamlit Application
```bash
streamlit run app.py
```
The application will open in your browser at `http://localhost:8501`.

---

## 🧪 Running End-to-End Tests
To verify all modules and pipelines without running the web UI:
```bash
python3 test_pipeline.py
```

Expected output:
```
=== [1] Testing PDF Processing ===
Extracted trial: NCT05423189 with 6 inclusions.
=== [2] Testing Embeddings Engine ===
Sim(EGFR, Osimertinib NSCLC): 0.7639 | Sim(EGFR, Diabetes): 0.0260
=== [3] Testing Vector Store ===
Top search result: NCT05423189 with score 0.7721
=== [4] Testing Patient Structuring & Matcher ===
Structured Patient: Age 62, Diagnosis: Non-Small Cell Lung Cancer
=== [5] Testing Trial Adjudication ===
Adjudication Status: POTENTIALLY_ELIGIBLE, Confidence: 85%
=== [6] Testing Report Generation ===
>>> ALL PIPELINE TESTS PASSED END-TO-END! <<<
```

---

## 📋 5-Step Clinical Research Workflow

1. **Step 1: Upload Trial Protocols**
   - Upload PDF trial protocols (or load the 3 included synthetic protocols: EGFRm NSCLC, PD-L1 Basket, and HER2 ADC).
   - Document text is chunked and indexed into the vector database.

2. **Step 2: Enter Patient Profile**
   - Select one of 4 synthetic patient cases (or paste custom clinical notes).
   - Click **"Structure Patient Attributes"** to extract demographics, tumor histology, biomarkers, lines of therapy, and screening labs.

3. **Step 3: Run Matching Pipeline**
   - Click **"Execute Adjudication Pipeline"**.
   - Embeds patient data, retrieves candidate trials, and evaluates every inclusion and exclusion criterion.

4. **Step 4: View Results & Explanations**
   - Review overall status badges (`ELIGIBLE`, `POTENTIALLY ELIGIBLE`, `INELIGIBLE`).
   - Examine match confidence percentages.
   - Expand trial cards to see criterion-by-criterion adjudications with citations (`[MET]`, `[UNMET]`, `[MISSING]`).
   - Review actionable alerts for missing diagnostic labs (e.g., contrast-enhanced brain MRI).

5. **Step 5: Export Review Report**
   - Download the clinical adjudication report in Markdown (`.md`) or formatted HTML / printable PDF.

---

## 🔒 Privacy & Compliance
- **Synthetic Data Only**: All patient profiles and protocol identifiers are synthetic. No Protected Health Information (PHI) is used.
- **Research Decision Support**: Intended for clinical research prescreening. Final protocol enrollment requires Principal Investigator (PI) adjudication.
