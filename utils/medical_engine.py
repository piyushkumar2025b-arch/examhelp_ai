"""
medical_engine.py — Advanced Medical Research Engine
Strictly enforces Epidemiology, Pathophysiology structure, and Medical Disclaimers.
"""
import streamlit as st
from utils.ai_engine import generate

def analyze_medical_condition(condition: str) -> str:
    """Analyze a medical condition with a standard clinical framework."""
    prompt = f"""Provide a comprehensive medical overview of: {condition}

REQUIREMENTS:
Strictly structure the response with the following sections (use markdown headers):
1. **Definition & Overview**
2. **Epidemiology** (prevalence, demographics, risk factors)
3. **Pathophysiology** (mechanism of disease)
4. **Clinical Features** (signs & symptoms)
5. **Investigations/Diagnosis** (labs, imaging, diagnostic criteria)
6. **Management Options** (pharmacological & non-pharmacological)
7. **Complications & Prognosis**

Use ICD codes where relevant, drug generic names, and evidence grades (Level I-IV) if applicable.
"""
    try:
        # Uses the medical_research engine config defined in prompts.py
        result = generate(prompt=prompt, engine_name="medical_research")
        return result or "⚠️ Medical overview failed to generate. Please try again."
    except Exception as e:
        return f"⚠️ Error generating medical overview: {e}"

def analyze_drug_interaction(drugs: list) -> str:
    """Analyze interactions between a list of drugs."""
    drug_str = ", ".join(drugs)
    prompt = f"""Analyze the pharmacological interactions between the following drugs:
{drug_str}

Provide a structured report detailing:
1. **Mechanism** (pharmacokinetic/pharmacodynamic)
2. **Severity** (Contraindicated/Major/Moderate/Minor)
3. **Clinical significance and onset**
4. **Management recommendation**
5. **Alternative drugs to consider**
"""
    try:
        result = generate(prompt=prompt, engine_name="drug_interaction")
        return result or "⚠️ Drug interaction analysis failed to generate."
    except Exception as e:
        return f"⚠️ Error generating drug interaction analysis: {e}"
