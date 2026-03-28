"""
research_engine.py — AI Research Assistant
Paper analysis, literature summaries, concept extraction, citation generation.
"""
from __future__ import annotations
from utils.debugger_engine import _call_gemini_debug

RESEARCH_SYSTEM = """\
You are an elite Research Scientist and Academic Librarian with expertise across all fields.
Your analysis is precise, scholarly, and genuinely insightful.
You cite sources accurately, identify research gaps, and synthesize complex literature.
"""

def summarize_paper(text: str, detail_level: str = "Standard") -> str:
    detail_map = {
        "Quick (3 bullets)": "3 bullet points: problem, method, result. Be ultra-concise.",
        "Standard":          "Structured summary: objective, methodology, key findings, limitations, implications (200-300 words)",
        "Deep Analysis":     "Full academic analysis: background, research question, methodology, results, statistical significance, limitations, real-world impact, critique, future directions (500+ words)",
    }
    instr = detail_map.get(detail_level, detail_map["Standard"])
    prompt = f"""Analyze this research paper/text and provide a {detail_level} summary.
INSTRUCTION: {instr}

TEXT:
{text[:12000]}"""
    return _call_gemini_debug(prompt, RESEARCH_SYSTEM)


def extract_concepts(text: str) -> str:
    prompt = f"""From this academic text, extract and explain:

1. **Core Concepts** — Key terms and their definitions as used in this text
2. **Methodologies** — Research methods, frameworks, algorithms used
3. **Key Claims** — Main arguments/findings with evidence
4. **Controversies** — Disputed points or competing views
5. **Connections** — How this relates to broader field/prior work
6. **Glossary** — Technical terms a student should know

TEXT:
{text[:10000]}"""
    return _call_gemini_debug(prompt, RESEARCH_SYSTEM)


def generate_literature_review(topic: str, scope: str, field: str) -> str:
    prompt = f"""Write a comprehensive literature review section for a research paper on:

TOPIC: {topic}
FIELD: {field}
SCOPE: {scope}

Structure:
1. Introduction to the literature landscape
2. Historical development of the field
3. Major theoretical frameworks (cite key authors)
4. Recent empirical studies (2020-2024)
5. Identified research gaps
6. Synthesis and transition to your research

Include properly formatted APA 7th citations throughout. 
Note: Mark synthesized/hypothetical references with [synthesized] since you don't have real-time database access."""
    return _call_gemini_debug(prompt, RESEARCH_SYSTEM)


def critique_methodology(text: str) -> str:
    prompt = f"""Critically evaluate the research methodology described in this text:

TEXT: {text[:8000]}

Assess:
1. Research design appropriateness
2. Sample size and selection validity
3. Data collection methods
4. Statistical analysis correctness
5. Control of confounding variables
6. Internal and external validity
7. Ethical considerations
8. Reproducibility/replication potential
9. Overall methodological rigor score (1-10)
10. Specific improvements recommended"""
    return _call_gemini_debug(prompt, RESEARCH_SYSTEM)


def generate_research_proposal(topic: str, field: str, level: str) -> str:
    prompt = f"""Write a complete research proposal for:
TOPIC: {topic}
FIELD: {field}
LEVEL: {level}

Include all standard sections:
1. Title (compelling and specific)
2. Abstract (150 words)
3. Background & Rationale
4. Research Questions/Hypotheses
5. Literature Gap
6. Methodology (detailed)
7. Expected Outcomes
8. Timeline (Gantt-style breakdown)
9. Budget outline
10. Ethical considerations
11. References (APA 7th)"""
    return _call_gemini_debug(prompt, RESEARCH_SYSTEM)


def explain_statistics(text: str) -> str:
    prompt = f"""Explain all statistical methods and results in this text in plain English:

TEXT: {text[:8000]}

For each statistical element found:
- What test/method was used
- Why it was appropriate (or not)
- What the numbers actually mean
- Whether the conclusions drawn are justified
- A simple analogy to understand it

Make this accessible to someone without a statistics background."""
    return _call_gemini_debug(prompt, RESEARCH_SYSTEM)
