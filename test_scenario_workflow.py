#!/usr/bin/env python
"""
Test script for the Clinical Scenario workflow
Tests scenario extraction, trial retrieval, and eligibility analysis
"""

import json
import os
from llm_client import LLMClient
from vector_store import VectorStore
from matcher import (
    structure_patient_attributes,
    evaluate_scenario_against_trials,
    compare_criteria_for_trial_scenario,
)

def load_sample_protocols():
    """Load sample trial protocols"""
    sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "sample_protocols.json")
    if os.path.exists(sample_path):
        with open(sample_path, "r") as f:
            return json.load(f)
    return []

def setup_vector_store(protocols):
    """Setup and populate vector store with protocols"""
    vs = VectorStore(persist_path=None)
    docs = []
    for p in protocols:
        text_repr = f"TRIAL: {p['trial_id']} - {p['trial_title']}. Condition: {p['condition']}. Phase: {p['phase']}.\n"
        text_repr += "INCLUSIONS:\n" + "\n".join([f"- {i['criterion']}" for i in p.get("inclusion_criteria", [])])
        text_repr += "\nEXCLUSIONS:\n" + "\n".join([f"- {e['criterion']}" for e in p.get("exclusion_criteria", [])])
        docs.append({
            "text": text_repr,
            "metadata": {
                "trial_id": p["trial_id"],
                "trial_title": p["trial_title"],
                "phase": p["phase"],
                "condition": p["condition"]
            }
        })
    vs.add_documents(docs)
    return vs

def test_scenario_1():
    """Test Scenario 1: Hypertension and Diabetes"""
    print("\n" + "="*70)
    print("TEST SCENARIO 1: Hypertension & Diabetes")
    print("="*70)
    
    scenario = """43-year-old male with hypertension and diabetes. 
Blood pressure is 163/83. He is a non-smoker and has BMI 18.1. 
Evaluate him against the available clinical trials."""
    
    print(f"\nScenario Input:\n{scenario}")
    
    # Load protocols and setup
    protocols = load_sample_protocols()
    vs = setup_vector_store(protocols)
    
    print(f"\n✓ Loaded {len(protocols)} trial protocols")
    
    # Initialize LLM (will use heuristic if no API key)
    llm = LLMClient(provider="local-heuristic")
    
    # Test patient attribute extraction
    print("\n--- Step 1: Extracting Patient Attributes ---")
    patient = structure_patient_attributes(scenario, llm_client=llm)
    print(f"Extracted Age: {patient.get('demographics', {}).get('age')}")
    print(f"Extracted Gender: {patient.get('demographics', {}).get('gender')}")
    print(f"Extracted Diagnosis: {patient.get('condition', {}).get('primary_diagnosis')}")
    print(f"Extracted Comorbidities: {patient.get('comorbidities', [])}")
    
    # Test scenario-based evaluation
    print("\n--- Step 2: Evaluating Against Trials ---")
    results = evaluate_scenario_against_trials(scenario, vs, protocols, llm_client=llm)
    
    print(f"\nTotal Trials Evaluated: {results.get('total_trials_evaluated')}")
    print(f"Total Trials Available: {results.get('total_trials_available')}")
    
    # Display trial results
    for i, trial_result in enumerate(results.get('trials_evaluated', []), 1):
        trial = trial_result['trial']
        evaluation = trial_result['scenario_evaluation']
        
        print(f"\n--- Trial {i}: {trial.get('trial_id')} ---")
        print(f"Title: {trial.get('trial_title')}")
        print(f"Status: {evaluation.get('overall_status')}")
        
        inc_match = sum(1 for inc in evaluation.get('evaluated_inclusions', []) if inc['status'] == 'MATCH')
        inc_not_match = sum(1 for inc in evaluation.get('evaluated_inclusions', []) if inc['status'] == 'NOT MATCH')
        inc_unknown = sum(1 for inc in evaluation.get('evaluated_inclusions', []) if inc['status'] == 'UNKNOWN')
        
        print(f"Inclusion Criteria: {inc_match} MATCH, {inc_not_match} NOT MATCH, {inc_unknown} UNKNOWN")
        
        missing = evaluation.get('missing_information', [])
        if missing:
            print(f"Missing Info: {', '.join(missing[:2])}")
        
        # Show sample inclusion criterion
        inclusions = evaluation.get('evaluated_inclusions', [])
        if inclusions:
            inc = inclusions[0]
            print(f"\nSample Inclusion Criterion [{inc.get('id')}]:")
            print(f"  Criterion: {inc.get('criterion', '')[:100]}...")
            print(f"  Status: {inc.get('status')}")
            print(f"  Evidence: {inc.get('patient_evidence', '')[:100]}...")

def test_scenario_2():
    """Test Scenario 2: Breast Cancer with Diabetes"""
    print("\n" + "="*70)
    print("TEST SCENARIO 2: Breast Cancer with Diabetes")
    print("="*70)
    
    scenario = """55-year-old female diagnosed with breast cancer. 
She is diabetic and currently receiving treatment. 
Find potentially relevant clinical trials."""
    
    print(f"\nScenario Input:\n{scenario}")
    
    protocols = load_sample_protocols()
    vs = setup_vector_store(protocols)
    llm = LLMClient(provider="local-heuristic")
    
    print(f"\n✓ Loaded {len(protocols)} trial protocols")
    
    print("\n--- Extracting Patient Attributes ---")
    patient = structure_patient_attributes(scenario, llm_client=llm)
    print(f"Age: {patient.get('demographics', {}).get('age')}")
    print(f"Gender: {patient.get('demographics', {}).get('gender')}")
    print(f"Diagnosis: {patient.get('condition', {}).get('primary_diagnosis')}")
    print(f"Comorbidities: {patient.get('comorbidities', [])}")

def test_scenario_3():
    """Test Scenario 3: Lung Cancer with Limited Info"""
    print("\n" + "="*70)
    print("TEST SCENARIO 3: Lung Cancer (Limited Information)")
    print("="*70)
    
    scenario = """60-year-old male with lung cancer. 
Former smoker. BMI 24.5. No diabetes. 
Current treatment information is unavailable."""
    
    print(f"\nScenario Input:\n{scenario}")
    
    protocols = load_sample_protocols()
    vs = setup_vector_store(protocols)
    llm = LLMClient(provider="local-heuristic")
    
    print(f"\n✓ Loaded {len(protocols)} trial protocols")
    
    print("\n--- Extracting Patient Attributes ---")
    patient = structure_patient_attributes(scenario, llm_client=llm)
    print(f"Age: {patient.get('demographics', {}).get('age')}")
    print(f"Gender: {patient.get('demographics', {}).get('gender')}")
    print(f"Diagnosis: {patient.get('condition', {}).get('primary_diagnosis')}")
    print(f"Prior Treatments: {patient.get('prior_treatments', [])}")
    
    print("\n✓ Note: Missing treatment information should result in UNKNOWN status for treatment-related criteria")

def main():
    print("\n🔬 Clinical Trial Scenario-Based Matching - Test Suite")
    print("="*70)
    
    try:
        test_scenario_1()
        test_scenario_2()
        test_scenario_3()
        
        print("\n" + "="*70)
        print("✓ All tests completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
