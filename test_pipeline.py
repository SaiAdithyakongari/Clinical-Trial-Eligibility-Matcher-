"""
End-to-End Pipeline Verification Test
Verifies all modules (pdf_processing, embeddings, vector_store, llm_client, matcher, report_generator).
"""

import os
import json
from pdf_processing import extract_text_from_pdf, chunk_protocol_text, extract_structured_criteria
from embeddings import EmbeddingsEngine
from vector_store import VectorStore
from llm_client import LLMClient
from matcher import (
    structure_patient_attributes,
    retrieve_relevant_trials,
    compare_criteria_for_trial,
)
from report_generator import generate_markdown_report, generate_html_report

def run_tests():
    print("=== [1] Testing PDF Processing ===")
    sample_pdf = "sample_data/NCT05423189_EGFR_NSCLC_Protocol.pdf"
    assert os.path.exists(sample_pdf), f"Sample PDF missing: {sample_pdf}"
    pdf_res = extract_text_from_pdf(sample_pdf)
    assert len(pdf_res["full_text"]) > 50, "Extracted text should not be empty"
    print(f"Extracted {len(pdf_res['full_text'])} chars from sample PDF.")

    chunks = chunk_protocol_text("NCT05423189", pdf_res["full_text"])
    print(f"Generated {len(chunks)} chunks.")

    structured_trial = extract_structured_criteria(pdf_res["full_text"], protocol_name="NCT05423189.pdf")
    assert "inclusion_criteria" in structured_trial, "Structured trial must have inclusion_criteria"
    print(f"Extracted trial: {structured_trial.get('trial_id')} with {len(structured_trial.get('inclusion_criteria', []))} inclusions.")

    print("\n=== [2] Testing Embeddings Engine ===")
    embed_engine = EmbeddingsEngine(provider="local-dense")
    vec1 = embed_engine.embed_text("EGFR exon 19 deletion lung adenocarcinoma")
    vec2 = embed_engine.embed_text("Osimertinib metastatic NSCLC")
    vec3 = embed_engine.embed_text("Type 2 diabetes insulin metformin")
    sim1_2 = EmbeddingsEngine.cosine_similarity(vec1, vec2)
    sim1_3 = EmbeddingsEngine.cosine_similarity(vec1, vec3)
    print(f"Sim(EGFR, Osimertinib NSCLC): {sim1_2:.4f}")
    print(f"Sim(EGFR, Diabetes): {sim1_3:.4f}")
    assert sim1_2 > sim1_3, "Oncology terms should be more similar than diabetes"

    print("\n=== [3] Testing Vector Store ===")
    vstore = VectorStore(embeddings_engine=embed_engine, persist_path=None)
    with open("sample_data/sample_protocols.json", "r") as f:
        protocols = json.load(f)
    docs = []
    for p in protocols:
        docs.append({
            "text": f"{p['trial_id']} {p['trial_title']} {p['condition']} {' '.join([i['criterion'] for i in p['inclusion_criteria']])}",
            "metadata": {"trial_id": p["trial_id"], "trial_title": p["trial_title"], "phase": p["phase"], "condition": p["condition"]}
        })
    vstore.add_documents(docs)
    assert vstore.count() == len(protocols), "All protocols indexed"
    search_res = vstore.similarity_search("EGFR mutation osimertinib progression", k=2)
    print(f"Top search result: {search_res[0]['document']['metadata']['trial_id']} with score {search_res[0]['score']}")
    assert search_res[0]["document"]["metadata"]["trial_id"] == "NCT05423189", "Top match for EGFR should be NCT05423189"

    print("\n=== [4] Testing Patient Structuring & Matcher ===")
    with open("sample_data/sample_patients.json", "r") as f:
        patients = json.load(f)
    pt_a = patients[0]
    structured_pt = structure_patient_attributes(pt_a["clinical_notes"])
    print(f"Structured Patient: Age {structured_pt.get('demographics', {}).get('age')}, Diagnosis: {structured_pt.get('condition', {}).get('primary_diagnosis')}")
    assert structured_pt.get("demographics", {}).get("age") == 62, "Patient age should be 62"

    print("\n=== [5] Testing Trial Adjudication ===")
    top_trials = retrieve_relevant_trials(structured_pt, vstore, top_n=3)
    print(f"Retrieved {len(top_trials)} candidate trials.")
    
    # Adjudicate against NCT05423189
    egfr_trial = next(p for p in protocols if p["trial_id"] == "NCT05423189")
    adjudication = compare_criteria_for_trial(structured_pt, egfr_trial)
    print(f"Adjudication Status: {adjudication.get('overall_eligibility')}, Confidence: {adjudication.get('match_confidence')}%")
    print(f"Evaluated Inclusions: {len(adjudication.get('evaluated_inclusions', []))}")
    print(f"Missing Info: {adjudication.get('missing_information')}")
    assert adjudication.get("match_confidence") >= 70, "EGFR patient should have high match confidence"

    print("\n=== [6] Testing Report Generation ===")
    matching_bundle = [{"trial": egfr_trial, "evaluation": adjudication}]
    md_rep = generate_markdown_report(structured_pt, matching_bundle, patient_identifier=pt_a["id"])
    html_rep = generate_html_report(structured_pt, matching_bundle, patient_identifier=pt_a["id"])
    assert len(md_rep) > 200, "Markdown report should be substantive"
    assert len(html_rep) > 500, "HTML report should be substantive"
    print("Markdown and HTML reports generated successfully.")

    print("\n>>> ALL PIPELINE TESTS PASSED END-TO-END! <<<")

if __name__ == "__main__":
    run_tests()
