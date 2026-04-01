"""
medical_engine.py — Clinical Scenario Analysis & Medical Guide
============================================================
AI-powered clinical reasoning and medical education assistance.
"""

from typing import Dict, List, Optional
from utils.ai_engine import quick_generate

class MedicalEngine:
    """Handles medical education analysis and clinical reasoning."""

    @staticmethod
    def analyze_symptoms(symptom_list: List[str], patient_info: str = "General") -> str:
        """Analyze a list of symptoms for educational purposes."""
        prompt = f"Patient Info: {patient_info}\nSymptoms: {', '.join(symptom_list)}"
        # engine_name="medical_expert" in prompts.py gives us the Clinical Advisor persona with strict disclaimers.
        return quick_generate(prompt=prompt, engine_name="medical_expert")

    @staticmethod
    def explain_condition(condition: str, level: str = "Patient Friendly") -> str:
        """Fetch a clinical explanation for a specific medical condition."""
        prompt = f"Explain the etiology, pathophysiology, and management of: {condition}. Explanation level: {level}."
        return quick_generate(prompt=prompt, engine_name="medical_expert")

    @staticmethod
    def pharmacokinetics_check(drug_list: List[str]) -> str:
        """Check for possible interactions or drug profiles."""
        prompt = f"Analyze the pharmacokinetics and possible drug-drug interactions for: {', '.join(drug_list)}."
        return quick_generate(prompt=prompt, engine_name="medical_expert")
