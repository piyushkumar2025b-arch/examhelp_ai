"""
notes_engine.py — AI Smart Notes Generator v2.0 ULTRA
Creates high-performance study materials with standardized output quality.
"""
from __future__ import annotations
from utils.ai_engine import generate

def _call_engine(prompt: str, system: str = "") -> str:
    """Unified call to AI engine with notes-specific tuning."""
    return generate(prompt=prompt, system=system, engine_name="notes")

NOTE_FORMATS = {
    "Cornell Notes": "Two-column format: main notes right, key questions/cues left, summary at bottom",
    "Mind Map Text": "Hierarchical tree structure from central topic, branching to subtopics",
    "Bullet Summary": "Dense bullet-point summary, 3-5 levels deep, highlighting key facts",
    "Cheat Sheet": "Ultra-compressed single-page reference with every key fact, formula, and rule",
    "Outline Format": "Traditional I. A. 1. a. hierarchical outline with full detail",
    "Concept Cards": "Each concept: term, definition, example, connections, exam tip",
    "Timeline Notes": "Chronological structure for history/process-heavy content",
    "Comparison Table": "Side-by-side comparison of concepts/items in markdown tables",
    "Question & Answer": "Every key point as a Q&A pair for active recall",
    "Feynman Notes": "Explain as if teaching a 12-year-old, then build complexity",
    "SQ3R Format": "Survey, Question, Read, Recite, Review structure",
    "Flashcard Set": "Comprehensive Q&A flashcard deck with difficulty markers",
    "Spider Diagram": "Central idea with 8 radiating branches, each with sub-points",
    "Two-Column Vocab": "Term | Definition | Example | Etymology table",
    "Process Notes": "Step-by-step numbered process with reasoning for each step",
    "Case Study Analysis": "Problem, Context, Analysis, Solution, Lessons format",
    "Formula Sheet": "All formulas, equations, with derivations and example applications",
    "1-Page Summary": "Everything important on exactly one condensed page",
    "PEEL Paragraph Notes": "Point, Evidence, Explain, Link format for essay prep",
    "Hierarchical Map": "Visual indented structure showing all concept relationships",
}

def generate_notes(
    content: str,
    format_type: str = "Cornell Notes",
    subject: str = "",
    focus: str = "",
) -> str:
    fmt_desc = NOTE_FORMATS.get(format_type, NOTE_FORMATS["Cornell Notes"])
    prompt = f"""Convert this content into {format_type}.
FORMAT STYLE: {fmt_desc}
"""
    if subject: prompt += f"SUBJECT: {subject}\n"
    if focus: prompt += f"FOCUS ON: {focus}\n"
    
    prompt += f"""
CONTENT:
{content[:12000]}

REQUIREMENTS:
- Use markdown for structure
- Include all key concepts/formulas
- Ensure the output strictly follows the 5-part hierarchical standard (Summary, Concepts, Breakdown, Tips, Recap).
"""
    return _call_engine(prompt)


def smart_summarize(
    content: str,
    length: str = "Medium",
    style: str = "Academic",
    preserve: str = "",
) -> str:
    length_map = {
        "Tweet (280 chars)": "Exactly 280 characters or less. Core message only.",
        "Quick (50 words)":  "50 words maximum. Key points only.",
        "Short (150 words)": "150 words. Main ideas with context.",
        "Medium (300 words)":"300 words. Comprehensive but concise.",
        "Long (600 words)":  "600 words. Thorough coverage of all major points.",
        "Executive Summary": "Professional executive summary format: context, findings, recommendations.",
    }
    prompt = f"""Summarize this content.
LENGTH: {length} — {length_map.get(length, '')}
STYLE: {style}
"""
    if preserve: prompt += f"MUST INCLUDE: {preserve}\n"
    prompt += f"\nCONTENT:\n{content[:10000]}"
    return _call_engine(prompt)


def extract_exam_questions(content: str, exam_type: str = "University Exam") -> str:
    prompt = f"""From this content, predict and generate {exam_type} questions.

CONTENT:
{content[:10000]}

Generate:
1. **10 Short Answer Questions** (2-5 marks each) with model answers
2. **5 Long Answer Questions** (10-15 marks each) with answer outlines  
3. **10 MCQ Questions** with 4 options and correct answer explained
4. **3 Case Study / Application Questions** with full solutions
5. **Top 5 Most Likely Exam Topics** from this material
"""
    return _call_engine(prompt)


def build_concept_map(content: str) -> str:
    prompt = f"""Analyze this content and create a concept relationship map.

CONTENT:
{content[:8000]}

Include a Mermaid Diagram code block using 'mindmap' syntax at the end of the response.
"""
    return _call_engine(prompt)


def paraphrase_text(text: str, style: str = "Academic", simplify: bool = False) -> str:
    prompt = f"""Paraphrase this text in {style} style.
{"Make it simpler and easier to understand." if simplify else "Maintain the same sophistication level."}
Avoid plagiarism while preserving all meaning.

ORIGINAL:
{text[:5000]}
"""
    return _call_engine(prompt)

