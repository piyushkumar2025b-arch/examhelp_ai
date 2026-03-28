"""
notes_engine.py — AI Smart Notes Generator
Converts any content into beautiful study notes, summaries, cheat sheets.
"""
from __future__ import annotations
from utils.debugger_engine import _call_gemini_debug

NOTES_SYSTEM = """\
You are a MASTER Note-Taker who creates the most effective study materials.
Your notes are: concise, memorable, logically structured, exam-focused.
You use visual markers, hierarchical structure, and memory devices.
"""

NOTE_FORMATS = {
    "Cornell Notes":        "Two-column format: main notes right, key questions/cues left, summary at bottom",
    "Mind Map Text":        "Hierarchical tree structure starting from central topic, branching to subtopics",
    "Bullet Summary":       "Dense bullet-point summary, 3-5 levels deep, highlighting key facts",
    "Cheat Sheet":          "Ultra-compressed single-page reference with every key fact",
    "Outline Format":       "Traditional I. A. 1. a. hierarchical outline",
    "Concept Cards":        "Each concept gets its own mini card: term, definition, example, connections",
    "Timeline Notes":       "Chronological structure for history/process-heavy content",
    "Comparison Table":     "Side-by-side comparison of multiple concepts/items",
    "Question & Answer":    "Every key point converted to a Q&A pair for active recall",
    "Feynman Notes":        "Explain everything as if teaching a 12-year-old, then build complexity",
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
    if subject:
        prompt += f"SUBJECT: {subject}\n"
    if focus:
        prompt += f"FOCUS ON: {focus}\n"
    prompt += f"""
CONTENT:
{content[:12000]}

Create comprehensive, exam-ready {format_type}. Include:
- All key concepts and definitions
- Important formulas/rules/laws
- Examples where helpful
- Memory tricks (acronyms, mnemonics)
- Exam tips and common question types"""
    return _call_gemini_debug(prompt, NOTES_SYSTEM)


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
    if preserve:
        prompt += f"MUST INCLUDE: {preserve}\n"
    prompt += f"\nCONTENT:\n{content[:10000]}"
    return _call_gemini_debug(prompt, NOTES_SYSTEM)


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

Format for easy printing/studying."""
    return _call_gemini_debug(prompt, NOTES_SYSTEM)


def build_concept_map(content: str) -> str:
    prompt = f"""Analyze this content and create a concept relationship map.

CONTENT:
{content[:8000]}

Produce:
1. **Central Concept** — the main theme
2. **Primary Branches** — 5-8 major concepts  
3. **Secondary Nodes** — sub-concepts under each branch
4. **Connections** — show how concepts relate to each other
5. **Mermaid Diagram Code** — a proper mindmap diagram:

```mermaid
mindmap
  root((Central Topic))
    Branch1
      Sub1
      Sub2
    Branch2
      Sub1
```

6. **Key Relationships** — explain 5 most important concept connections"""
    return _call_gemini_debug(prompt, NOTES_SYSTEM)


def paraphrase_text(text: str, style: str = "Academic", simplify: bool = False) -> str:
    prompt = f"""Paraphrase this text in {style} style.
{"Make it simpler and easier to understand." if simplify else "Maintain the same sophistication level."}
Avoid plagiarism while preserving all meaning.

ORIGINAL:
{text[:5000]}

Provide the paraphrased version, then explain 3 key changes you made."""
    return _call_gemini_debug(prompt, NOTES_SYSTEM)
