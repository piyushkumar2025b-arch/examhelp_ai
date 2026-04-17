"""
notes_engine.py — AI Smart Notes Generator v3.0
Enterprise-grade study material generator with:
- 20 note formats
- Structured output with quality markers
- Exam question extraction
Enriched with: Wikipedia + Open Library + Google Books (all free, no key).
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from utils.ai_engine import generate, quick_generate
from free_apis import (
    search_books as _ob_search,
    get_wikipedia_summary,
    search_google_books,
)

def _call_engine(prompt: str, system: str = "", max_tokens: int = 2500) -> str:
    return generate(prompt=prompt, system=system, engine_name="notes", max_tokens=max_tokens)


NOTE_FORMATS = {
    "Cornell Notes":       "Two-column: main notes right, key questions/cues left, summary at bottom",
    "Mind Map Text":       "Hierarchical tree from central topic to subtopics with emoji markers",
    "Bullet Summary":      "Dense 3-5 level bullet points — every key fact and formula included",
    "Cheat Sheet":         "Ultra-compressed single reference with formulas, rules, and mnemonics",
    "Outline Format":      "Classic I > A > 1 > a hierarchical outline with full detail",
    "Concept Cards":       "Term | Definition | Example | Connections | Exam Tip for each concept",
    "Timeline Notes":      "Chronological structure for history/process-heavy content",
    "Comparison Table":    "Side-by-side markdown tables comparing concepts, methods, or items",
    "Question & Answer":   "Every key point as a Q&A pair with detailed answers for active recall",
    "Feynman Notes":       "Explain simply as if teaching a 12-year-old, then build complexity",
    "SQ3R Format":         "Survey, Question, Read, Recite, Review — full structured study format",
    "Flashcard Set":       "80+ Q&A flashcards with difficulty markers (Easy/Medium/Hard)",
    "Spider Diagram":      "Central idea with 8 radiating branches and sub-points per branch",
    "Two-Column Vocab":    "Term | Definition | Example | Etymology — formatted table",
    "Process Notes":       "Numbered steps with reasoning, prerequisites, and common mistakes each step",
    "Case Study Analysis": "Problem > Context > Analysis > Solution > Lessons Learned",
    "Formula Sheet":       "All formulas with variable definitions, derivation hints, and worked examples",
    "1-Page Summary":      "Complete topic coverage condensed to one scannable page",
    "PEEL Paragraphs":     "Point > Evidence > Explain > Link format for essay and answer prep",
    "Hierarchical Map":    "Indented visual structure showing all concept relationships with depth",
}

STUDY_PROFILES = {
    "Exam Crammer":    "Focus on HIGH-YIELD exam facts. Bold every examinable point. Add probability of appearing (High/Med/Low).",
    "Deep Learner":    "Emphasize understanding over memorization. Include derivations, reasons, and connections.",
    "Visual Learner":  "Use tables, diagrams (ASCII art), and structured visual layouts wherever possible.",
    "Speed Reader":    "Keep it ultra-dense. No fluff. Bold key terms. Numbered lists only.",
    "Essay Writer":    "Focus on arguments, evidence, and analytical frameworks. Include quote-worthy points.",
    "STEM Student":    "Emphasize formulas, proofs, derivations, and worked numerical examples.",
}


def generate_notes(
    content: str,
    format_type: str = "Cornell Notes",
    subject: str = "",
    focus: str = "",
    study_profile: str = "",
    include_summary: bool = True,
    include_exam_tips: bool = True,
) -> str:
    fmt_desc    = NOTE_FORMATS.get(format_type, NOTE_FORMATS["Cornell Notes"])
    profile_str = STUDY_PROFILES.get(study_profile, "") if study_profile else ""

    # ── Free API enrichment: Wikipedia topic seed + Open Library references ──────
    enrichment_block = ""
    try:
        topic_query = subject or focus or content[:50]
        wiki        = get_wikipedia_summary(topic_query)
        if wiki and wiki.get("extract"):
            enrichment_block += f"\n\nWikipedia Summary: {wiki['extract'][:350]}"
    except Exception:
        pass

    try:
        topic_query = subject or focus or content[:40]
        books       = search_books(topic_query, limit=3)
        if books:
            refs = " | ".join(
                f"{b['title']} ({b['authors'][0] if b['authors'] else 'Unknown'}, {b['year']})"
                for b in books if b.get("title")
            )
            enrichment_block += f"\n\nRecommended Books: {refs}"
    except Exception:
        pass

    system = "You are an expert academic note-taker and study coach. Create high-quality, well-structured notes from the given content. Use markdown formatting throughout."

    prompt = f"""Create {format_type} from the following study material.

FORMAT DESCRIPTION: {fmt_desc}
{"SUBJECT: " + subject if subject else ""}
{"FOCUS AREA: " + focus if focus else ""}
{"STUDENT PROFILE: " + profile_str if profile_str else ""}

CONTENT:
{content[:12000]}{enrichment_block}

REQUIREMENTS:
1. Follow the {format_type} format strictly
2. Use markdown (headers, bold, tables, code blocks as appropriate)
3. Include ALL key concepts, definitions, and formulas
4. {"Add 3-5 targeted EXAM TIPS at the end" if include_exam_tips else ""}
5. {"Add a concise SUMMARY section at the beginning" if include_summary else ""}
6. Highlight critical points with ⭐ or > [!IMPORTANT]
7. Quality: clear, comprehensive, exam-ready
"""
    return _call_engine(prompt, system=system)


def smart_summarize(
    content: str,
    length: str = "Medium (300 words)",
    style: str = "Academic",
    preserve: str = "",
    output_language: str = "English",
) -> str:
    length_map = {
        "Tweet (280 chars)":    "Exactly 280 characters. Core message only.",
        "Quick (50 words)":     "50 words max. Key points only.",
        "Short (150 words)":    "150 words. Main ideas with context.",
        "Medium (300 words)":   "300 words. Comprehensive but concise.",
        "Long (600 words)":     "600 words. Thorough, all major points.",
        "Executive Summary":    "Professional format: context, findings, recommendations.",
        "Abstract (100 words)": "Academic abstract style: background, method, finding, conclusion.",
    }
    prompt = f"""Summarize the following content.
LENGTH: {length} — {length_map.get(length, '')}
STYLE: {style}
LANGUAGE: {output_language}
{"MUST INCLUDE: " + preserve if preserve else ""}

CONTENT:
{content[:10000]}

Output only the summary. No preamble."""
    return _call_engine(prompt)


def extract_exam_questions(
    content: str,
    exam_type: str = "University Exam",
    num_short: int = 10,
    num_long: int = 5,
    num_mcq: int = 10,
) -> str:
    prompt = f"""Generate realistic {exam_type} questions from this content.

CONTENT:
{content[:10000]}

Generate:
## Short Answer Questions ({num_short} questions, 2-5 marks each)
- Question
- ✅ Model Answer (3-4 sentences)

## Long Answer Questions ({num_long} questions, 10-15 marks)
- Question
- ✅ Answer Outline (key points to cover)

## MCQ Questions ({num_mcq} questions)
- Question
- A) B) C) D) options
- ✅ Correct: X — Brief explanation

## Case Study / Application Questions (3 questions)
- Scenario-based question
- ✅ Full solution framework

## 🎯 Top 5 Most Likely Exam Topics
Ranked by probability of appearing

Be thorough and exam-accurate."""
    return _call_engine(prompt, max_tokens=4000)


def build_concept_map(content: str, topic: str = "") -> str:
    system = "You are an expert in visual learning and concept mapping. Create clear, comprehensive concept maps."
    prompt = f"""Analyze this content and create a detailed concept relationship map.
{"TOPIC: " + topic if topic else ""}

CONTENT:
{content[:8000]}

DELIVERABLES:
1. **Concept Overview** — List all major concepts with one-line descriptions
2. **Key Relationships** — How concepts connect (use arrows: A → B means "leads to")
3. **Hierarchy** — Main topics > Sub-topics > Details
4. **Mermaid Mind Map** — Include a proper mermaid mindmap code block at the end

Use this Mermaid format:
```mermaid
mindmap
  root((Main Topic))
    Branch1
      Sub1
      Sub2
    Branch2
      Sub3
```"""
    return _call_engine(prompt, system=system)


def paraphrase_text(
    text: str,
    style: str = "Academic",
    simplify: bool = False,
    target_grade: str = "",
) -> str:
    grade_hint = f"Target reading level: {target_grade}." if target_grade else ""
    prompt = f"""Paraphrase this text in {style} style.
{"Make it significantly simpler and easier to understand." if simplify else "Maintain the same sophistication level."}
{grade_hint}
Avoid plagiarism while preserving all meaning and technical accuracy.
Do NOT add any introduction or closing remarks — output only the paraphrased text.

ORIGINAL:
{text[:5000]}
"""
    return _call_engine(prompt)


def improve_writing(
    text: str,
    goal: str = "clarity",
    preserve_length: bool = True,
) -> str:
    """Improve writing quality with specific goal."""
    goal_map = {
        "clarity":      "Make every sentence clearer and more direct. Remove ambiguity.",
        "conciseness":  "Cut unnecessary words. Say the same thing in 30% fewer words.",
        "flow":         "Improve transitions and sentence variety for better reading flow.",
        "vocabulary":   "Elevate vocabulary. Replace weak/common words with stronger alternatives.",
        "structure":    "Reorganize paragraphs for logical flow. Better topic sentences.",
        "formality":    "Make the tone more formal and academic in style.",
        "engagement":   "Make it more engaging and interesting to read.",
    }
    prompt = f"""Improve this text for: {goal_map.get(goal, goal)}.
{"Keep similar length to the original." if preserve_length else "Length can change as needed."}
Output only the improved text — no explanations.

TEXT:
{text[:6000]}
"""
    return _call_engine(prompt)


def generate_mnemonics(content: str, num: int = 5) -> str:
    """Generate creative mnemonics for memorization."""
    prompt = f"""Create {num} powerful, creative, easy-to-remember mnemonics for this content.

CONTENT:
{content[:3000]}

For each mnemonic:
- **What to remember**: [The fact/concept]
- **Mnemonic**: [The mnemonic device — acronym, story, rhyme, visual, etc.]
- **Type**: [ACRONYM/STORY/RHYME/VISUAL/CHUNKING]
- **How it works**: [Brief explanation]

Make them genuinely memorable and creative."""
    return _call_engine(prompt)
