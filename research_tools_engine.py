"""
research_tools_engine.py — Advanced Peer-Review & Lit-Review AI
============================================================
Scientific critique, citation generation, and literature mapping.
"""

from typing import Dict, List, Optional
from utils.ai_engine import quick_generate

class ResearchTools:
    """Handles professional academic research and critique."""

    @staticmethod
    def critique_paper(abstract_or_text: str) -> str:
        """Main entry point for scientific peer-review critique."""
        prompt = f"Perform a rigorous scientific peer-review critique of this abstract/text:\n{abstract_or_text}"
        # engine_name="researcher" in prompts.py gives us the Research Scientist persona.
        return quick_generate(prompt=prompt, engine_name="researcher")

    @staticmethod
    def generate_lit_review(topics: List[str], focus_area: str = "General") -> str:
        """Fetch and structure a literature review opening."""
        prompt = f"Generate an opening literature review section for these topics: {', '.join(topics)}. Focus: {focus_area}."
        return quick_generate(prompt=prompt, engine_name="researcher")

    @staticmethod
    def suggest_research_gap(literature_summary: str) -> str:
        """Identify potential research gaps from a given summary."""
        prompt = f"Analyze this literature summary and identify 3 critical research gaps:\n{literature_summary}"
        return quick_generate(prompt=prompt, engine_name="researcher")
