# -*- coding: utf-8 -*-
"""
Clinical Trial Eligibility Matcher
Streamlit Web Application & GenAI Adjudication Interface.

Performance improvements:
- CSS injected only once per session (session state flag).
- Report strings built lazily on download click only.
- Traditional Step 3 uses compare_criteria_for_trials_parallel (concurrent).
- Vector store populated with persist=False (no blocking disk write).
- @st.cache_resource called AFTER authentication to avoid blocking login.
"""

import os
import json
import streamlit as st
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Clinical Trial Eligibility Matcher",
    page_icon=":microscope:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Authentication gate -- must run before any cache_resource calls
# ---------------------------------------------------------------------------
from auth import render_auth_page, render_logout_button

if not st.session_state.get("authenticated", False):
    render_auth_page()
    st.stop()

# ---------------------------------------------------------------------------
# Imports (after auth so startup cost is deferred past login)
# ---------------------------------------------------------------------------
try:
    from llm_client import LLMClient
    from pdf_processing import extract_text_from_pdf, chunk_protocol_text, extract_structured_criteria
    from embeddings import EmbeddingsEngine
    from vector_store import VectorStore
    from matcher import (
        structure_patient_attributes,
        retrieve_relevant_trials,
        compare_criteria_for_trial,
        compare_criteria_for_trials_parallel,
        evaluate_scenario_against_trials,
        compare_criteria_for_trial_scenario,
    )
    from report_generator import generate_markdown_report, generate_html_report
except ImportError as e:
    st.error(f"Import Error: {str(e)}. Run: pip install -r requirements.txt")
    st.stop()

# ---------------------------------------------------------------------------
# CSS -- injected once per session
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&display=swap');
  html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #1E293B !important; background-color: #F8FAFC !important;
  }
  .stApp, .main .block-container { background-color: #F8FAFC !important; }
  .stApp h1, h1 { font-family: 'Outfit', sans-serif !important; color: #0B192C !important; font-weight: 800 !important; font-size: 1.85rem !important; }
  .stApp h2, h2 { font-family: 'Outfit', sans-serif !important; color: #0F766E !important; font-weight: 800 !important; font-size: 1.45rem !important; }
  .stApp h3, h3 { font-family: 'Outfit', sans-serif !important; color: #0B192C !important; font-weight: 800 !important; font-size: 1.3rem !important; }
  .stApp h4, h4 { font-family: 'Inter', sans-serif !important; color: #0F766E !important; font-weight: 700 !important; }
  div[style*="background: linear-gradient"] h1, div[style*="background: linear-gradient"] h2, div[style*="background: linear-gradient"] h3 { color: #FFFFFF !important; }
  div[style*="background: linear-gradient"] p { color: #CBD5E1 !important; }
  p, .stMarkdown p, span, label { color: #334155 !important; font-size: 14.5px !important; }
  .stCaption, small { color: #64748B !important; font-size: 12.5px !important; }
  strong, b { color: #0F172A !important; font-weight: 700 !important; }
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B192C 0%, #0F2A44 50%, #0F172A 100%) !important;
    border-right: 1px solid rgba(14,165,152,0.15) !important;
  }
  section[data-testid="stSidebar"] h1,
  section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 { color: #F0FDFA !important; font-weight: 700 !important; }
  section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label { color: #CBD5E1 !important; }
  section[data-testid="stSidebar"] strong { color: #5EEAD4 !important; }
  section[data-testid="stSidebar"] .stButton button {
    background: rgba(14,165,152,0.12) !important; color: #5EEAD4 !important;
    border: 1px solid rgba(14,165,152,0.25) !important; border-radius: 8px !important; font-weight: 600 !important;
  }
  section[data-testid="stSidebar"] .stButton button:hover { background: rgba(14,165,152,0.22) !important; }
  .stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #FFFFFF !important; color: #0F172A !important;
    border: 1.5px solid #CBD5E1 !important; border-radius: 10px !important;
    font-size: 14.5px !important; font-weight: 500 !important;
  }
  .stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #0D9488 !important; box-shadow: 0 0 0 3px rgba(13,148,136,0.15) !important;
  }
  .stSelectbox select, div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important; color: #0F172A !important;
    border: 1.5px solid #CBD5E1 !important; border-radius: 10px !important;
  }
  ::placeholder { color: #94A3B8 !important; font-weight: 400 !important; }
  .stButton > button {
    background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%) !important;
    color: #FFFFFF !important; font-weight: 700 !important; border: none !important;
    border-radius: 10px !important; box-shadow: 0 2px 8px rgba(13,148,136,0.25) !important;
    transition: all 0.25s ease !important;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #0F766E 0%, #115E59 100%) !important;
    box-shadow: 0 4px 14px rgba(13,148,136,0.35) !important; transform: translateY(-1px) !important;
  }
  .stTabs [data-baseweb="tab-list"] { gap: 4px !important; background-color: #F1F5F9 !important; border-radius: 10px !important; padding: 4px !important; }
  .stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: #475569 !important; font-weight: 600 !important; }
  .stTabs [aria-selected="true"] { background-color: #FFFFFF !important; color: #0F766E !important; box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important; }
  .streamlit-expanderHeader { color: #0F172A !important; font-weight: 600 !important; background-color: #F8FAFC !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; }
  .stAlert > div { border-radius: 10px !important; font-size: 13.5px !important; }
  hr { border: none !important; height: 1px !important; background: linear-gradient(90deg, transparent, #CBD5E1 30%, #CBD5E1 70%, transparent) !important; margin: 24px 0 !important; }
  .stSpinner > div { border-top-color: #0D9488 !important; }
  .badge { display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 11.5px; font-weight: 700; text-transform: uppercase; }
  .badge-eligible { background: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }
  .badge-potential { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
  .badge-ineligible { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
  .missing-box { background-color: #FFFBEB; border-left: 4px solid #F59E0B; padding: 14px 18px; border-radius: 8px; color: #92400E; margin: 14px 0; }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #F1F5F9; }
  ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
</style>
"""

if not st.session_state.get("_css_injected", False):
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.session_state["_css_injected"] = True


# ---------------------------------------------------------------------------
# Cached resources (called only after auth)
# ---------------------------------------------------------------------------

@st.cache_resource
def init_vector_store():
    """Initialise the in-memory vector store singleton (once per process)."""
    return VectorStore(persist_path=None)


@st.cache_data
def load_default_sample_protocols():
    """Load and cache sample protocols from disk."""
    sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_protocols.json")
    if os.path.exists(sample_path):
        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Failed to load sample protocols: {e}")
    return []


@st.cache_data
def get_sample_patients():
    """Load and cache sample patients from disk."""
    sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_patients.json")
    if os.path.exists(sample_path):
        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Failed to load sample patients: {e}")
    return []


# ---------------------------------------------------------------------------
# Session state initialisation (idempotent)
# ---------------------------------------------------------------------------

_DEFAULTS: Dict[str, Any] = {
    "protocols": None,
    "vector_store": None,
    "patient_raw": "",
    "patient_structured": None,
    "matching_results": [],
    "current_step": 1,
    "scenario_text": "",
    "scenario_results": None,
    "scenario_patient_profile": None,
    "form_patient_name": "",
    "form_patient_age": None,
    "form_patient_gender": "Unknown",
    "form_patient_diagnosis": "",
    "form_patient_bp": "",
    "form_patient_bmi": None,
    "form_patient_diabetes": "Unknown",
    "form_patient_smoking": "Unknown",
    "form_patient_additional": "",
    "form_submitted": False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

if st.session_state.protocols is None:
    st.session_state.protocols = load_default_sample_protocols()
if st.session_state.vector_store is None:
    st.session_state.vector_store = init_vector_store()

# Populate vector store on cold start (persist=False skips disk write)
if not st.session_state.vector_store.documents and st.session_state.protocols:
    try:
        docs = []
        for p in st.session_state.protocols:
            text_repr = (
                f"TRIAL: {p['trial_id']} - {p['trial_title']}. "
                f"Condition: {p['condition']}. Phase: {p['phase']}.\n"
                "INCLUSIONS:\n" + "\n".join([f"- {i['criterion']}" for i in p.get("inclusion_criteria", [])]) +
                "\nEXCLUSIONS:\n" + "\n".join([f"- {e['criterion']}" for e in p.get("exclusion_criteria", [])])
            )
            docs.append({
                "text": text_repr,
                "metadata": {
                    "trial_id": p["trial_id"],
                    "trial_title": p["trial_title"],
                    "phase": p["phase"],
                    "condition": p["condition"],
                }
            })
        st.session_state.vector_store.add_documents(docs, persist=False)
    except Exception as e:
        st.error(f"Failed to index protocols: {e}")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    render_logout_button()
    st.markdown("### System Configuration")
    st.caption("GenAI Applied Healthcare Adjudication Engine")

    llm_provider = st.selectbox(
        "LLM Provider Engine",
        ["auto", "gemini", "openai", "anthropic", "local-heuristic"],
        index=0,
        help="'auto' selects based on available API keys."
    )
    api_key_input = st.text_input(
        "API Key (Optional / Overrides Env)",
        value="", type="password",
        placeholder="Enter API key or use container env"
    )

    st.markdown("---")
    st.markdown("### Indexed Knowledge Base")
    st.write(f"**Loaded Protocols:** {len(st.session_state.protocols)}")
    st.write(f"**Vector Store Documents:** {st.session_state.vector_store.count()}")

    if st.button("Reset to Default 3 Synthetic Trials"):
        st.session_state.protocols = load_default_sample_protocols()
        st.session_state.matching_results = []
        vs = init_vector_store()
        vs.clear()
        st.session_state.vector_store = vs
        st.success("Default protocol library reloaded!")

    st.markdown("---")
    st.caption("Synthetic Data Guarantee: Designed for research workflows using synthetic/de-identified data.")


# ---------------------------------------------------------------------------
# Main Header
# ---------------------------------------------------------------------------

st.markdown("""
<div style="background: linear-gradient(135deg,#0B192C 0%,#1E3A5F 60%,#0F766E 100%);border-radius:16px;padding:28px 32px;margin-bottom:28px;box-shadow:0 4px 20px rgba(11,25,44,0.15);">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:8px;">
    <div style="background:rgba(13,148,136,0.2);border:1px solid rgba(94,234,212,0.3);border-radius:12px;width:46px;height:46px;display:flex;align-items:center;justify-content:center;font-size:24px;">&#128300;</div>
    <h1 style="margin:0;font-size:26px;font-weight:800;color:#FFFFFF;letter-spacing:-0.03em;">Clinical Trial Eligibility Matcher</h1>
  </div>
  <div style="width:50px;height:3px;background:linear-gradient(90deg,#14B8A6,#5EEAD4);border-radius:2px;margin:10px 0 12px 0;"></div>
  <p style="color:#CBD5E1;font-size:14.5px;margin:0;line-height:1.55;max-width:680px;">
    RAG-grounded Generative AI adjudication pipeline comparing patient clinical characteristics against trial protocol eligibility criteria.
  </p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Workflow navigation
# ---------------------------------------------------------------------------

st.markdown("### Workflow Selection")
workflow_mode = st.radio(
    "Select Workflow Mode:",
    ("Traditional Patient Profile", "Form-Based Patient Entry", "Scenario-Based Matching"),
    horizontal=True,
    label_visibility="collapsed"
)

active_key = api_key_input if api_key_input else None
llm_client = LLMClient(provider=llm_provider, api_key=active_key)

if workflow_mode == "Traditional Patient Profile":
    st.markdown("**Traditional Workflow:** Upload trials > Enter patient > Run matching analysis")
    step_cols = st.columns(3)
    steps_nav = [("1. Protocol Upload", 1), ("2. Patient Profile", 2), ("3. Unified Matching & Analysis", 3)]
    for col, (label, s_num) in zip(step_cols, steps_nav):
        is_active = (st.session_state.current_step == s_num) or (s_num == 3 and st.session_state.current_step >= 3)
        btn_label = f">> {label}" if is_active else label
        if col.button(btn_label, key=f"nav_step_{s_num}", use_container_width=True):
            st.session_state.current_step = s_num
elif workflow_mode == "Form-Based Patient Entry":
    st.markdown("**Form-Based Workflow:** Complete structured patient form > Analyse trials instantly")
    if st.button("Go to Patient Information Form", use_container_width=True, key="nav_form"):
        st.session_state.current_step = 100
else:
    st.markdown("**Scenario Workflow:** Natural language patient scenario > Extract attributes > Analyse trials")
    if st.button("Go to Clinical Scenario Analysis", use_container_width=True, key="nav_scenario"):
        st.session_state.current_step = 99


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_patient_id(sp: Dict) -> str:
    return sp.get("demographics", {}).get("patient_id") or "SYNTHETIC-PT-8092"


def _render_download_buttons(results: List[Dict], sp: Dict, key_suffix: str):
    """Renders download buttons; report content built only when clicked."""
    patient_id = _get_patient_id(sp)
    d1, d2 = st.columns(2)
    with d1:
        md_content = generate_markdown_report(sp, results, patient_identifier=patient_id)
        st.download_button(
            label="Download Markdown Report (.md)",
            data=md_content,
            file_name=f"clinical_trial_adjudication_{patient_id}.md",
            mime="text/markdown",
            key=f"dl_md_{key_suffix}",
            use_container_width=True
        )
    with d2:
        html_content = generate_html_report(sp, results, patient_identifier=patient_id)
        st.download_button(
            label="Download HTML / Printable Report",
            data=html_content,
            file_name=f"clinical_trial_adjudication_{patient_id}.html",
            mime="text/html",
            key=f"dl_html_{key_suffix}",
            use_container_width=True
        )


def _criterion_badge(status: str, is_exclusion: bool = False) -> str:
    if status == "MET":
        label = "Passed (not excluded)" if is_exclusion else "Matched"
        return f'<span style="background:#DCFCE7;color:#166534;border:1px solid #BBF7D0;padding:3px 8px;border-radius:4px;font-weight:700;font-size:12px;">&#10003; {label}</span>'
    if status == "UNMET":
        label = "Failed (excluded)" if is_exclusion else "Not Matched"
        return f'<span style="background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;padding:3px 8px;border-radius:4px;font-weight:700;font-size:12px;">&#10007; {label}</span>'
    label = "Needs Verification" if is_exclusion else "Missing Data"
    return f'<span style="background:#FEF3C7;color:#92400E;border:1px solid #FDE68A;padding:3px 8px;border-radius:4px;font-weight:700;font-size:12px;">? {label}</span>'


def _render_criterion_card(crit: Dict, is_exclusion: bool = False):
    badge = _criterion_badge(crit.get("status", "MET"), is_exclusion)
    ev_key = "patient_evidence" if "patient_evidence" in crit else "evidence"
    exp_key = "reason" if "reason" in crit else "explanation"
    st.markdown(f"""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:8px;padding:12px 16px;margin-bottom:10px;">
      <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:6px;">
        <span style="font-weight:600;color:#0F172A;font-size:13.5px;">[{crit.get('id','C')}] {crit.get('criterion','')}</span>
        {badge}
      </div>
      <div style="font-size:12.5px;color:#334155;line-height:1.4;"><strong>Evidence:</strong> {crit.get(ev_key,'No evidence found.')}</div>
      <div style="font-size:12.5px;color:#0F766E;margin-top:3px;"><strong>Rationale:</strong> {crit.get(exp_key,'')}</div>
      <div style="font-size:11px;color:#94A3B8;margin-top:4px;font-style:italic;">Citation: {crit.get('citation','Protocol Specification')}</div>
    </div>""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SCENARIO WORKFLOW (step 99)
# ---------------------------------------------------------------------------

if st.session_state.current_step == 99:
    st.markdown("### Clinical Scenario Analysis")
    st.markdown(
        "Describe a synthetic patient scenario in natural language. "
        "The system extracts attributes, retrieves relevant trials, and evaluates eligibility."
    )
    st.caption("Example: '43-year-old male with hypertension and diabetes. BP 163/83, BMI 18.1. Non-smoker.'")

    scenario_input = st.text_area(
        "Synthetic Patient Scenario",
        value=st.session_state.scenario_text,
        height=180,
        placeholder="43-year-old male with hypertension and diabetes.\nBlood pressure 163/83, BMI 18.1, non-smoker.",
        key="scenario_input_area"
    )
    st.session_state.scenario_text = scenario_input

    if st.button("Analyze Patient & Find Trials", key="analyze_scenario_btn", use_container_width=True):
        if not st.session_state.scenario_text.strip():
            st.warning("Please enter a patient scenario before analysing.")
        else:
            with st.spinner("Extracting patient attributes and analysing trials in parallel..."):
                try:
                    scenario_results = evaluate_scenario_against_trials(
                        st.session_state.scenario_text,
                        st.session_state.vector_store,
                        st.session_state.protocols,
                        llm_client=llm_client
                    )
                    st.session_state.scenario_results = scenario_results
                    st.session_state.scenario_patient_profile = scenario_results.get("patient_profile")
                    st.success("Scenario analysis complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during scenario analysis: {str(e)}")

    if st.session_state.scenario_results:
        results = st.session_state.scenario_results
        profile = st.session_state.scenario_patient_profile

        if profile:
            st.markdown("#### Extracted Patient Profile")
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"**Age**\n\n{profile.get('demographics', {}).get('age', 'N/A')}")
            c2.markdown(f"**Gender**\n\n{profile.get('demographics', {}).get('gender', 'N/A')}")
            c3.markdown(f"**Diagnosis**\n\n{profile.get('condition', {}).get('primary_diagnosis', 'N/A')}")
            c4.markdown(f"**ECOG PS**\n\n{profile.get('demographics', {}).get('ecog_ps', 'N/A')}")
            biomarkers = profile.get("biomarkers", [])
            if biomarkers:
                st.markdown("**Biomarkers:** " + ", ".join([f"{b.get('gene')}: {b.get('status')}" for b in biomarkers]))
            st.markdown("---")

        trials_evaluated = results.get("trials_evaluated", [])
        if trials_evaluated:
            st.markdown(f"#### Trial Analysis Results ({results.get('total_trials_evaluated')} of {results.get('total_trials_available')} evaluated)")
            for idx, trial_result in enumerate(trials_evaluated, 1):
                trial = trial_result["trial"]
                evaluation = trial_result["scenario_evaluation"]
                trial_id = trial.get("trial_id", f"TRIAL-{idx}")
                trial_title = trial.get("trial_title", "Protocol")
                overall_status = evaluation.get("overall_status", "NEEDS REVIEW")

                inc_matches = sum(1 for i in evaluation.get("evaluated_inclusions", []) if i["status"] == "MATCH")
                inc_nm = sum(1 for i in evaluation.get("evaluated_inclusions", []) if i["status"] == "NOT MATCH")
                exc_matches = sum(1 for e in evaluation.get("evaluated_exclusions", []) if e["status"] == "MATCH")
                exc_nm = sum(1 for e in evaluation.get("evaluated_exclusions", []) if e["status"] == "NOT MATCH")

                if overall_status == "POTENTIAL MATCH":
                    status_color, bg_color, border_color = "#166534", "#F0FDF4", "#BBF7D0"
                    status_label = "Potential Match"
                elif overall_status == "NEEDS REVIEW":
                    status_color, bg_color, border_color = "#92400E", "#FEFCE8", "#FDE68A"
                    status_label = "Needs Review"
                else:
                    status_color, bg_color, border_color = "#991B1B", "#FEF2F2", "#FECACA"
                    status_label = "Potential Mismatch"

                with st.expander(f"{trial_id}: {trial_title} -- {status_label}", expanded=(idx == 1)):
                    st.markdown(f"""
                    <div style="background-color:{bg_color};border-left:4px solid {border_color};border-radius:6px;padding:12px 16px;margin-bottom:14px;">
                      <div style="font-size:13px;font-weight:700;color:{status_color};">{overall_status}</div>
                      <div style="font-size:12.5px;color:#475569;margin-top:4px;">{evaluation.get('research_rationale','')}</div>
                    </div>
                    <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:10px 14px;margin-bottom:14px;font-size:13px;">
                      <strong>Criterion Summary:</strong>
                      <span style="background:#DCFCE7;color:#166534;padding:2px 8px;border-radius:4px;margin:0 4px;font-weight:600;">{inc_matches+exc_matches} Match</span>
                      <span style="background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:4px;margin:0 4px;font-weight:600;">{inc_nm+exc_nm} Not Match</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("**Inclusion Criteria**")
                    for inc in evaluation.get("evaluated_inclusions", []):
                        _render_criterion_card(inc, is_exclusion=False)

                    st.markdown("**Exclusion Criteria**")
                    for exc in evaluation.get("evaluated_exclusions", []):
                        _render_criterion_card(exc, is_exclusion=True)

                    missing = evaluation.get("missing_information", [])
                    if missing:
                        items_html = "".join([f'<li style="margin-bottom:3px;">{m}</li>' for m in missing])
                        st.markdown(f'<div style="background:#FFFBEB;border-left:4px solid #F59E0B;padding:12px 16px;border-radius:6px;margin-top:12px;"><strong style="color:#92400E;">Information Needed:</strong><ul style="margin:6px 0 0 18px;color:#92400E;font-size:12.5px;">{items_html}</ul></div>', unsafe_allow_html=True)
        else:
            st.info("No trials available. Please ensure trial protocols are loaded.")

    st.markdown("---")
    if st.button("Back to Workflow Selection", key="back_workflow_scenario"):
        st.session_state.current_step = 1
        st.rerun()


# ---------------------------------------------------------------------------
# FORM-BASED WORKFLOW (step 100)
# ---------------------------------------------------------------------------

elif st.session_state.current_step == 100:
    st.markdown("### Patient Information Form")
    st.info("Synthetic Patient Data -- This form is for clinical research using de-identified data.")

    c1, c2 = st.columns(2)
    with c1:
        fn = st.text_input("Patient Name", value=st.session_state.form_patient_name, placeholder="e.g. John Smith", key="form_name_input")
        st.session_state.form_patient_name = fn
    with c2:
        fa = st.number_input("Age", value=st.session_state.form_patient_age or 0, min_value=0, max_value=120, key="form_age_input")
        st.session_state.form_patient_age = fa if fa > 0 else None

    c1, c2 = st.columns(2)
    with c1:
        fg = st.selectbox("Gender", ["Unknown", "Male", "Female", "Other"],
            index=["Unknown", "Male", "Female", "Other"].index(st.session_state.form_patient_gender), key="form_gender_input")
        st.session_state.form_patient_gender = fg
    with c2:
        fd = st.text_input("Diagnosis", value=st.session_state.form_patient_diagnosis, placeholder="e.g. Hypertension", key="form_diagnosis_input")
        st.session_state.form_patient_diagnosis = fd

    c1, c2 = st.columns(2)
    with c1:
        fb = st.text_input("Blood Pressure", value=st.session_state.form_patient_bp, placeholder="e.g. 163/83", key="form_bp_input")
        st.session_state.form_patient_bp = fb
    with c2:
        fbmi = st.number_input("BMI", value=st.session_state.form_patient_bmi or 0.0, min_value=0.0, max_value=100.0, step=0.1, key="form_bmi_input")
        st.session_state.form_patient_bmi = fbmi if fbmi > 0 else None

    c1, c2 = st.columns(2)
    with c1:
        fdiab = st.selectbox("Diabetes", ["Unknown", "Yes", "No"],
            index=["Unknown", "Yes", "No"].index(st.session_state.form_patient_diabetes), key="form_diabetes_input")
        st.session_state.form_patient_diabetes = fdiab
    with c2:
        fsmoke = st.selectbox("Smoking Status", ["Unknown", "Smoker", "Non-smoker"],
            index=["Unknown", "Smoker", "Non-smoker"].index(st.session_state.form_patient_smoking), key="form_smoking_input")
        st.session_state.form_patient_smoking = fsmoke

    fadd = st.text_area("Additional Clinical Information", value=st.session_state.form_patient_additional, height=120,
        placeholder="Current treatment, medications, symptoms, lab values...", key="form_additional_input")
    st.session_state.form_patient_additional = fadd

    st.markdown("---")
    if st.button("Analyze & Find Matching Trials", use_container_width=True, key="form_submit_btn"):
        if not fn or not st.session_state.form_patient_age:
            st.warning("Please enter at least Patient Name and Age.")
        else:
            st.session_state.form_submitted = True

    if st.session_state.form_submitted:
        st.markdown("---")
        form_patient: Dict[str, Any] = {
            "demographics": {
                "age": st.session_state.form_patient_age,
                "gender": st.session_state.form_patient_gender,
                "patient_id": f"FORM-PT-{abs(hash(st.session_state.form_patient_name)) % 10000:04d}",
            },
            "condition": {"primary_diagnosis": st.session_state.form_patient_diagnosis or "Unknown", "stage": "Unknown", "histology": "Unknown", "progression_status": "Unknown"},
            "biomarkers": [],
            "prior_treatments": [],
            "organ_function_and_labs": {"blood_pressure": st.session_state.form_patient_bp or "Unknown", "bmi": st.session_state.form_patient_bmi, "anc": "Unknown", "platelets": "Unknown", "creatinine": "Unknown"},
            "comorbidities": [],
            "diabetes": st.session_state.form_patient_diabetes,
            "smoking_status": st.session_state.form_patient_smoking,
            "cns_metastases": "Unknown",
            "summary_paragraph": st.session_state.form_patient_additional or "No additional information.",
        }

        with st.spinner("Retrieving relevant trials and analysing eligibility in parallel..."):
            try:
                retrieved_trials = retrieve_relevant_trials(form_patient, st.session_state.vector_store, top_n=5)
                evaluations = compare_criteria_for_trials_parallel(form_patient, retrieved_trials, llm_client=llm_client)
                matching_results = [{"trial": t, "evaluation": e} for t, e in zip(retrieved_trials, evaluations)]

                if matching_results:
                    st.success(f"Analysis complete! Found {len(matching_results)} potentially relevant trials.")
                    _render_download_buttons(matching_results, form_patient, "form_top")
                    st.markdown("#### Potentially Relevant Trials")
                    for idx, res in enumerate(matching_results, 1):
                        trial = res["trial"]
                        ev = res["evaluation"]
                        tid = trial.get("trial_id", f"TRIAL-{idx}")
                        conf = ev.get("match_confidence", 0)
                        status = ev.get("overall_eligibility", "PENDING")
                        with st.expander(f"{tid}: {trial.get('trial_title','Protocol')} -- {conf}% Match", expanded=(idx == 1)):
                            st.markdown(f"**Status:** {status} | **Confidence:** {conf}%")
                            st.markdown("**Rationale:** " + ev.get("executive_summary", ""))
                            st.markdown("**Inclusion Criteria**")
                            for inc in ev.get("evaluated_inclusions", []):
                                _render_criterion_card(inc)
                            st.markdown("**Exclusion Criteria**")
                            for exc in ev.get("evaluated_exclusions", []):
                                _render_criterion_card(exc, is_exclusion=True)
                else:
                    st.warning("No matching trials found for this patient profile.")
            except Exception as e:
                st.error(f"Error during trial analysis: {str(e)}")

        if st.button("Back to Form", key="back_to_form"):
            st.session_state.form_submitted = False
            st.rerun()


# ---------------------------------------------------------------------------
# UNIFIED ANALYSIS RESULTS renderer (Traditional workflow)
# ---------------------------------------------------------------------------

def render_unified_analysis_results(results: List[Dict], sp: Dict):
    if not results:
        st.info("No matching results found. Execute the matching engine above.")
        return

    eligible_n = sum(1 for r in results if r["evaluation"].get("overall_eligibility") == "ELIGIBLE")
    potential_n = sum(1 for r in results if "POTENTIAL" in r["evaluation"].get("overall_eligibility", ""))
    ineligible_n = sum(1 for r in results if r["evaluation"].get("overall_eligibility") == "INELIGIBLE")

    st.markdown("#### Adjudication Portfolio Summary")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Trials Evaluated", len(results))
    k2.metric("Likely Eligible", eligible_n)
    k3.metric("Action Required", potential_n)
    k4.metric("Likely Ineligible", ineligible_n)

    st.markdown("""
    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;padding:14px 18px;margin:16px 0 12px 0;">
      <strong style="color:#0B192C;font-size:15px;">Download Consolidated Adjudication Report</strong>
      <p style="color:#64748B;font-size:13px;margin:2px 0 0 0;">Export the unified report with all evaluated trials and criteria.</p>
    </div>
    """, unsafe_allow_html=True)
    _render_download_buttons(results, sp, "trad_top")

    st.markdown("---")
    st.markdown("### Candidate Trials & Detailed Criteria Adjudication")

    for idx, res in enumerate(results, 1):
        trial = res["trial"]
        ev = res["evaluation"]
        tid = trial.get("trial_id", f"TRIAL-{idx}")
        status = ev.get("overall_eligibility", "PENDING")
        conf = ev.get("match_confidence", 0)

        if status == "ELIGIBLE":
            badge_class, summary_line = "badge-eligible", "Likely Eligible -- All inclusion criteria satisfied, no triggered exclusions."
            s_bg, s_border, s_color = "#F0FDF4", "#BBF7D0", "#166534"
        elif "POTENTIAL" in status:
            badge_class, summary_line = "badge-potential", "Insufficient Data / Action Required -- Pending supplementary diagnostic workup."
            s_bg, s_border, s_color = "#FEFCE8", "#FDE68A", "#92400E"
        else:
            badge_class, summary_line = "badge-ineligible", "Likely Ineligible -- Core inclusion criteria unmet or exclusion triggered."
            s_bg, s_border, s_color = "#FEF2F2", "#FECACA", "#991B1B"

        with st.expander(f"{tid}: {trial.get('trial_title','Protocol')} -- {conf}% ({status})", expanded=True):
            st.markdown(f"""
            <div style="background-color:{s_bg};border-left:4px solid {s_border};border-radius:6px;padding:12px 16px;margin-bottom:14px;">
              <div style="font-size:14px;font-weight:700;color:{s_color};">{summary_line}</div>
              <div style="font-size:12.5px;color:#475569;margin-top:4px;"><strong>Clinical Rationale:</strong> {ev.get('executive_summary','No rationale.')}</div>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:10px 14px;margin-bottom:12px;">
              <div>
                <span style="font-size:12px;font-weight:700;color:#0369A1;background:#E0F2FE;padding:2px 8px;border-radius:4px;">{tid}</span>
                <span style="font-size:13px;color:#334155;margin-left:8px;"><strong>Phase:</strong> {trial.get('phase','N/A')} | <strong>Condition:</strong> {trial.get('condition','N/A')}</span>
              </div>
              <div>
                <span class="badge {badge_class}">{status}</span>
                <span style="font-size:14px;font-weight:700;color:#0B192C;margin-left:10px;">{conf}% Match</span>
              </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(conf / 100.0)

            missing = ev.get("missing_information", [])
            if missing:
                items_html = "".join([f'<li style="margin-bottom:4px;">{m}</li>' for m in missing])
                st.markdown(f'<div class="missing-box"><strong>Missing Patient Information:</strong><ul style="margin:6px 0 0 18px;font-size:13px;">{items_html}</ul></div>', unsafe_allow_html=True)

            st.markdown("#### Inclusion Criteria Evaluation")
            for inc in ev.get("evaluated_inclusions", []):
                _render_criterion_card(inc)

            st.markdown("#### Exclusion Criteria Evaluation")
            for exc in ev.get("evaluated_exclusions", []):
                _render_criterion_card(exc, is_exclusion=True)

    st.markdown("---")
    _render_download_buttons(results, sp, "trad_bottom")


# ---------------------------------------------------------------------------
# TRADITIONAL WORKFLOW -- Step 1
# ---------------------------------------------------------------------------

if st.session_state.current_step == 1 and workflow_mode == "Traditional Patient Profile":
    st.markdown("### Step 1: Upload Trial Protocols & Protocols Library")
    col1, col2 = st.columns([1.5, 1])

    with col1:
        uploaded_files = st.file_uploader("Upload Clinical Protocol PDFs", type=["pdf", "txt"], accept_multiple_files=True)
        if uploaded_files:
            st.success(f"{len(uploaded_files)} file(s) selected")
            if st.button("Parse & Ingest Uploaded Documents"):
                with st.spinner("Processing PDF text and extracting structured criteria..."):
                    new_docs = []
                    for uf in uploaded_files:
                        pdf_data = extract_text_from_pdf(uf)
                        structured = extract_structured_criteria(pdf_data["full_text"], llm_client=llm_client, protocol_name=uf.name)
                        st.session_state.protocols.append(structured)
                        chunks = chunk_protocol_text(structured["trial_id"], pdf_data["full_text"])
                        for c in chunks:
                            new_docs.append({"text": c["text"], "metadata": {"trial_id": structured["trial_id"], "trial_title": structured["trial_title"], "phase": structured["phase"], "condition": structured["condition"]}})
                    if new_docs:
                        st.session_state.vector_store.add_documents(new_docs, persist=True)
                    st.success(f"Successfully processed {len(uploaded_files)} protocol(s)!")

    with col2:
        st.markdown("#### Currently Indexed Protocol Library")
        for p in st.session_state.protocols:
            with st.expander(f"{p.get('trial_id')} - {p.get('phase','N/A')}"):
                st.markdown(f"**Title:** {p.get('trial_title')}")
                st.markdown(f"**Indication:** {p.get('condition')}")
                st.markdown(f"**Inclusions:** {len(p.get('inclusion_criteria', []))} | **Exclusions:** {len(p.get('exclusion_criteria', []))}")

    st.markdown("---")
    if st.button("Proceed to Step 2: Patient Profile"):
        st.session_state.current_step = 2
        st.rerun()


# ---------------------------------------------------------------------------
# TRADITIONAL WORKFLOW -- Step 2
# ---------------------------------------------------------------------------

elif st.session_state.current_step == 2 and workflow_mode == "Traditional Patient Profile":
    st.markdown("### Step 2: Enter or Select Synthetic Patient Profile")

    sample_patients = get_sample_patients()
    options = ["Select a patient..."] + [f"{sp['name']} ({sp['id']})" for sp in sample_patients] + ["Custom Entry"]
    selected_sample = st.selectbox("Load Pre-Configured Synthetic Patient Case", options=options, index=0)

    if selected_sample not in ("Select a patient...", "Custom Entry"):
        chosen = next(sp for sp in sample_patients if f"{sp['name']} ({sp['id']})" == selected_sample)
        st.session_state.patient_raw = chosen["clinical_notes"]
        st.info(f"**Case Description:** {chosen['description']}")
    elif selected_sample == "Custom Entry" and not st.session_state.patient_raw:
        st.session_state.patient_raw = ""

    patient_text = st.text_area(
        "Clinical Patient Summary / Progress Notes",
        value=st.session_state.patient_raw, height=220,
        placeholder="Enter patient age, diagnosis, stage, biomarker testing, prior therapy lines, performance status, and lab values..."
    )
    st.session_state.patient_raw = patient_text

    col_btn1, _ = st.columns([1, 4])
    with col_btn1:
        if st.button("Structure Patient Attributes"):
            with st.spinner("Extracting structured clinical variables..."):
                structured = structure_patient_attributes(patient_text, llm_client=llm_client)
                st.session_state.patient_structured = structured
                st.success("Patient variables structured successfully!")

    if st.session_state.patient_structured:
        ps = st.session_state.patient_structured
        st.markdown("#### Structured Clinical Variables")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Age:** {ps.get('demographics',{}).get('age','N/A')}")
            st.markdown(f"**Sex:** {ps.get('demographics',{}).get('gender','N/A')}")
            st.markdown(f"**ECOG PS:** {ps.get('demographics',{}).get('ecog_ps','N/A')}")
        with c2:
            st.markdown(f"**Diagnosis:** {ps.get('condition',{}).get('primary_diagnosis','N/A')}")
            st.markdown(f"**Stage:** {ps.get('condition',{}).get('stage','N/A')}")
            st.markdown(f"**CNS Metastases:** {ps.get('cns_metastases','Unknown')}")
        with c3:
            bios = [f"{b.get('gene')}: {b.get('status')}" for b in ps.get("biomarkers", [])]
            st.markdown(f"**Biomarkers:** {', '.join(bios) if bios else 'None'}")
            txs = [t.get("name") for t in ps.get("prior_treatments", [])]
            st.markdown(f"**Prior Therapies:** {', '.join(txs) if txs else 'None'}")

    st.markdown("---")
    if st.button("Proceed to Step 3: Run Matching & View Analysis Results"):
        if not st.session_state.patient_structured and st.session_state.patient_raw:
            st.session_state.patient_structured = structure_patient_attributes(st.session_state.patient_raw, llm_client=llm_client)
        st.session_state.current_step = 3
        st.rerun()


# ---------------------------------------------------------------------------
# TRADITIONAL WORKFLOW -- Step 3 (parallel matching)
# ---------------------------------------------------------------------------

elif st.session_state.current_step >= 3 and workflow_mode == "Traditional Patient Profile":
    st.markdown("### Step 3: Unified Trial Matching & Eligibility Analysis")

    if not st.session_state.patient_structured:
        if st.session_state.patient_raw:
            st.session_state.patient_structured = structure_patient_attributes(st.session_state.patient_raw, llm_client=llm_client)
        else:
            st.warning("Please enter a patient profile in Step 2 before running the matching engine.")

    if st.session_state.patient_structured:
        ps = st.session_state.patient_structured
        diag = ps.get("condition", {}).get("primary_diagnosis", "N/A")
        stage = ps.get("condition", {}).get("stage", "N/A")
        age = ps.get("demographics", {}).get("age", "N/A")
        gender = ps.get("demographics", {}).get("gender", "N/A")
        bios = [f"{b.get('gene')}: {b.get('status')}" for b in ps.get("biomarkers", [])]

        st.markdown(f"""
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;padding:14px 18px;margin-bottom:16px;">
          <strong style="color:#0B192C;font-size:15px;">Active Patient: {diag} ({stage})</strong>
          <div style="font-size:12.5px;color:#64748B;margin-top:2px;">
            Age: {age} | Sex: {gender} | Biomarkers: {', '.join(bios) if bios else 'None'} | Trials: {len(st.session_state.protocols)}
          </div>
        </div>
        """, unsafe_allow_html=True)

        btn_label = "Re-run Adjudication Pipeline" if st.session_state.matching_results else "Execute Adjudication Pipeline"
        if st.button(btn_label, key="run_match_btn"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text("Phase 1: Querying vector store for candidate trials...")
            progress_bar.progress(15)

            trials_to_evaluate = st.session_state.protocols
            status_text.text(f"Phase 2: Evaluating {len(trials_to_evaluate)} trials in parallel...")
            progress_bar.progress(30)

            evaluations = compare_criteria_for_trials_parallel(
                st.session_state.patient_structured,
                trials_to_evaluate,
                llm_client=llm_client
            )
            results = [{"trial": t, "evaluation": e} for t, e in zip(trials_to_evaluate, evaluations)]

            progress_bar.progress(95)
            status_text.text("Phase 3: Sorting results by match confidence...")
            results.sort(key=lambda x: x["evaluation"].get("match_confidence", 0), reverse=True)
            st.session_state.matching_results = results
            progress_bar.progress(100)
            status_text.text("Adjudication completed!")
            st.rerun()

        if st.session_state.matching_results:
            render_unified_analysis_results(st.session_state.matching_results, st.session_state.patient_structured)
