"""
legal_engine.py — AI Legal Case Analysis & Reasoning
===================================================
Professional-grade legal reasoning, case analysis, and compliance checking.
"""

from typing import Dict, List, Optional
from utils.ai_engine import quick_generate

class LegalEngine:
    """Handles professional legal analysis and hypothetical scenario reasoning."""

    @staticmethod
    def analyze_case(case_text: str, jurisdiction: str = "Common Law / International") -> str:
        """Main entry point for clinical legal case analysis."""
        prompt = f"Jurisdiction: {jurisdiction}\n\nCase/Fact Scenario: {case_text}"
        # engine_name="legal_expert" gives us the Senior Counsel persona.
        return quick_generate(prompt=prompt, engine_name="legal_expert")

    @staticmethod
    def check_compliance(fact_pattern: str, rule: str) -> str:
        """Analyze a fact pattern against a specific law or regulation."""
        prompt = f"Analyze this fact pattern:\n{fact_pattern}\n\nAgainst this rule/law:\n{rule}"
        return quick_generate(prompt=prompt, engine_name="researcher")

    @staticmethod
    def generate_legal_brief(facts: str, issue: str) -> str:
        """Generate a structured legal brief draft."""
        prompt = f"Generate a structured legal brief.\nFacts: {facts}\nLegal Issue: {issue}"
        return quick_generate(prompt=prompt, engine_name="legal_expert")
