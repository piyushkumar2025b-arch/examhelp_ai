"""
legal_engine.py — Advanced Legal Analysis Engine (IRAC Framework)
Enforces Jurisdiction, Case Precedents, and IRAC structure.
"""
import streamlit as st
from utils.ai_engine import generate

def analyze_legal_case(scenario: str, jurisdiction: str = "General/International") -> str:
    """Analyze a legal scenario using the IRAC method."""
    prompt = f"""Analyze the following legal scenario:

SCENARIO:
{scenario}

JURISDICTION: {jurisdiction}

REQUIREMENTS:
1. Identify the applicable legal framework or governing law.
2. Structure the analysis strictly using the IRAC method:
   - **Issue:** The main legal question(s).
   - **Rule:** Relevant statutes, doctrines, or case precedents.
   - **Application:** Applying the rules to the specific facts.
   - **Conclusion:** The most likely legal outcome.
3. Note any dissenting views, ambiguities, or missing facts.
"""
    try:
        # Uses the legal_analyser engine config defined in prompts.py
        result = generate(prompt=prompt, engine_name="legal_analyser")
        return result or "⚠️ Legal analysis failed to generate. Please try again."
    except Exception as e:
        return f"⚠️ Error generating legal analysis: {e}"

def generate_legal_document_template(doc_type: str, parties: list, jurisdiction: str) -> str:
    """Generate a template for standard legal documents."""
    party_str = ", ".join(parties)
    prompt = f"""Generate a standard legal template for: {doc_type}
Jurisdiction: {jurisdiction}
Involved Parties: {party_str}

REQUIREMENTS:
- Standard legal headings and clauses.
- Placeholder brackets [LIKE THIS] for specific dates, amounts, and signatures.
- Highlight common boilerplate clauses (Severability, Governing Law, Entire Agreement).
"""
    try:
        result = generate(prompt=prompt, engine_name="legal_analyser")
        return result or "⚠️ Template generation failed."
    except Exception as e:
        return f"⚠️ Error generating template: {e}"
