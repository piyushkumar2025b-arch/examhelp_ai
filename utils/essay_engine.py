"""
essay_engine.py — AI Essay Writer & Academic Paper Generator
Generates structured essays, research papers, reports with citations.
"""
from __future__ import annotations
import os, re
from utils.debugger_engine import _call_gemini_debug

ESSAY_TYPES = {
    "Argumentative Essay":   "Take a clear stance and build a compelling argument with evidence",
    "Expository Essay":      "Explain a concept objectively with facts, examples, and analysis",
    "Descriptive Essay":     "Paint a vivid picture using rich sensory and illustrative language",
    "Narrative Essay":       "Tell a story with structure, character, and meaningful arc",
    "Compare & Contrast":    "Analyze similarities and differences between two or more subjects",
    "Cause & Effect":        "Explore relationships between events and their consequences",
    "Research Paper":        "Academic paper with thesis, literature review, methodology, findings",
    "Lab Report":            "Scientific report with hypothesis, procedure, results, discussion",
    "Literature Review":     "Survey and critically evaluate existing research on a topic",
    "Case Study Analysis":   "Deep-dive analysis of a specific real-world case",
    "Reflective Journal":    "Personal reflection on learning, experiences, and growth",
    "Business Report":       "Professional report with executive summary, analysis, recommendations",
}

ACADEMIC_LEVELS = ["High School", "Undergraduate", "Postgraduate", "PhD", "Professional"]

CITATION_STYLES = ["APA 7th", "MLA 9th", "Chicago 17th", "Harvard", "IEEE", "Vancouver"]

ESSAY_SYSTEM = """\
You are an ELITE Academic Writer with expertise across all disciplines.

WRITING PROTOCOL:
1. STRUCTURE FIRST: Clear introduction, body paragraphs, conclusion
2. THESIS-DRIVEN: Every essay must have a sharp, arguable thesis
3. EVIDENCE-BASED: Support all claims with examples, data, or logic
4. ACADEMIC TONE: Match the requested academic level precisely
5. TRANSITION MASTERY: Smooth flow between paragraphs and ideas
6. CITATION FORMAT: Use the requested citation style correctly

OUTPUT: Full, publication-ready essay. No meta-commentary. Just the essay.
"""

def generate_essay(
    topic: str,
    essay_type: str,
    word_count: int = 800,
    academic_level: str = "Undergraduate",
    citation_style: str = "APA 7th",
    key_points: str = "",
    context_text: str = "",
) -> str:
    prompt = f"""TASK: Write a complete {essay_type}

TOPIC: {topic}
ACADEMIC LEVEL: {academic_level}
TARGET WORD COUNT: {word_count} words
CITATION STYLE: {citation_style}
ESSAY TYPE GUIDANCE: {ESSAY_TYPES.get(essay_type, '')}
"""
    if key_points.strip():
        prompt += f"\nKEY POINTS TO INCLUDE:\n{key_points}\n"
    if context_text.strip():
        ctx = context_text[:8000]
        prompt += f"\nSOURCE MATERIAL (reference this):\n{ctx}\n"
    
    prompt += "\nWrite the complete essay now. Include a title, all sections, and properly formatted citations/references at the end."
    return _call_gemini_debug(prompt, ESSAY_SYSTEM)


def improve_essay(original: str, instruction: str) -> str:
    prompt = f"""ORIGINAL ESSAY:
{original[:6000]}

IMPROVEMENT INSTRUCTION: {instruction}

Rewrite the essay applying the requested improvements. Return the full improved version."""
    return _call_gemini_debug(prompt, ESSAY_SYSTEM)


def generate_outline(topic: str, essay_type: str, word_count: int = 800) -> str:
    prompt = f"""Create a detailed outline for a {word_count}-word {essay_type} on: "{topic}"

Include:
- Working title
- Thesis statement
- Introduction hook + context
- All body paragraph topics with sub-points and evidence ideas
- Conclusion strategy
- Suggested sources/references to look up"""
    return _call_gemini_debug(prompt, ESSAY_SYSTEM)
