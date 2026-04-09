"""
essay_engine.py — Elite Essay Writer v2.0
Multi-format · Academic levels · Citation support · Outline → Draft → Polish pipeline
Plagiarism-aware phrasing · Argument strength scorer · Tone analyzer
"""
from __future__ import annotations
import re

ESSAY_TYPES = {
    "Argumentative Essay":   "Take a clear, defensible stance. Build a compelling argument with evidence, counter-arguments, and rebuttals.",
    "Expository Essay":      "Explain a concept objectively with facts, examples, definitions, and clear analysis.",
    "Descriptive Essay":     "Paint a vivid, immersive picture using rich sensory detail, metaphor, and illustrative language.",
    "Narrative Essay":       "Tell a compelling story with structure, character development, conflict, and a meaningful arc.",
    "Compare & Contrast":    "Systematically analyze similarities AND differences using either point-by-point or block structure.",
    "Cause & Effect":        "Explore causal relationships — trace root causes and downstream consequences with clarity.",
    "Research Paper":        "Academic paper with abstract, thesis, literature review, methodology, findings, discussion, and proper citations.",
    "Lab Report":            "Scientific report: hypothesis, materials, procedure, data, results, discussion, conclusion.",
    "Literature Review":     "Critically survey existing scholarship — synthesize, compare, and evaluate research trends.",
    "Case Study Analysis":   "Structured deep-dive: context, problem identification, analysis using theory/frameworks, recommendations.",
    "Reflective Journal":    "Personal critical reflection using Gibbs/Kolb/ERA cycle — what happened, what it means, what to do differently.",
    "Business Report":       "Professional report: executive summary, situation analysis, findings, recommendations, action plan.",
    "Persuasive Essay":      "Persuade the reader using ethos, pathos, logos — emotional hooks, credible evidence, logical reasoning.",
    "Critical Analysis":     "Evaluate strengths, weaknesses, assumptions, and implications of a text, argument, or work.",
}

ACADEMIC_LEVELS = ["High School", "Undergraduate", "Postgraduate", "PhD / Doctoral", "Professional / Industry"]
CITATION_STYLES = ["APA 7th", "MLA 9th", "Chicago 17th", "Harvard", "IEEE", "Vancouver", "Oxford"]

ESSAY_SYSTEM = """\
You are a world-class Academic Writer and published scholar with expertise across all disciplines.

YOUR MANDATE:
1. THESIS — Every essay must have a sharp, original, arguable thesis that guides the entire piece.
2. STRUCTURE — Rigorous structure: compelling hook → context → thesis → body (with clear topic sentences) → counter-argument → conclusion with broader implications.
3. EVIDENCE — All claims backed by specific examples, data, case studies, or citations. No vague generalities.
4. ARGUMENTATION — Anticipate and address counter-arguments. Demonstrate intellectual depth.
5. ACADEMIC VOICE — Match the exact register of the requested level (HS = clear/accessible, PhD = scholarly/precise).
6. CITATIONS — Format citations exactly as requested. Include a full References/Works Cited section.
7. TRANSITIONS — Masterful paragraph flow. Each paragraph ends with a bridge to the next.
8. ORIGINALITY — Fresh angles, unexpected examples, non-obvious insights.

OUTPUT: Deliver the complete, polished, publication-ready essay ONLY. No preamble, no meta-commentary."""

OUTLINE_SYSTEM = """\
You are a master essay architect. Create the most strategic, detailed, and actionable outline possible.
Every section must have: topic sentence template, 2-3 evidence bullet points, transition strategy."""

IMPROVE_SYSTEM = """\
You are a senior academic editor. Surgically improve the essay. Preserve the author's voice while:
- Strengthening the thesis
- Tightening arguments  
- Improving paragraph structure
- Enhancing transitions
- Elevating vocabulary (without losing clarity)
- Fixing any logical gaps
Return the complete improved essay with tracked-change-style comments using [EDITED: reason] inline."""


def generate_essay(
    topic: str,
    essay_type: str,
    word_count: int = 800,
    academic_level: str = "Undergraduate",
    citation_style: str = "APA 7th",
    key_points: str = "",
    context_text: str = "",
    tone: str = "Academic",
    audience: str = "",
) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""TASK: Write a complete, polished {essay_type}

TOPIC: {topic}
ACADEMIC LEVEL: {academic_level}
TARGET WORD COUNT: {word_count} words (stay within ±10%)
CITATION STYLE: {citation_style}
TONE: {tone}
{f"TARGET AUDIENCE: {audience}" if audience else ""}
ESSAY TYPE GUIDANCE: {ESSAY_TYPES.get(essay_type, '')}

{f"KEY POINTS TO INCLUDE:{chr(10)}{key_points}" if key_points.strip() else ""}
{f"SOURCE MATERIAL (cite and reference):{chr(10)}{context_text[:7000]}" if context_text.strip() else "Generate relevant examples and citations from your knowledge."}

REQUIREMENTS:
- Start with a compelling hook sentence
- Write a clear, arguable thesis in the introduction
- Each body paragraph: topic sentence → evidence → analysis → transition
- Include at least one counter-argument and rebuttal
- End with implications beyond the immediate topic
- Include a properly formatted References/Bibliography section
- Use formal {citation_style} in-text citations throughout

Write the complete essay now:"""
    return _call_gemini_debug(prompt, ESSAY_SYSTEM)


def generate_outline(topic: str, essay_type: str, word_count: int = 800, academic_level: str = "Undergraduate") -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Create a comprehensive, strategic essay outline:

ESSAY TYPE: {essay_type}
TOPIC: {topic}
WORD COUNT TARGET: {word_count}
ACADEMIC LEVEL: {academic_level}
TYPE GUIDANCE: {ESSAY_TYPES.get(essay_type, '')}

Provide:
1. **Working Title** (compelling, specific)
2. **Thesis Statement** (arguable, specific, preview of structure)
3. **Introduction Strategy** (hook type + context + thesis placement)
4. **Body Paragraphs** (for each: topic sentence template, 2-3 evidence ideas, transition to next)
5. **Counter-Argument Section** (what to anticipate + rebuttal strategy)
6. **Conclusion Strategy** (synthesis + broader implications + final impact)
7. **Suggested Sources/Citations** (5-8 credible references to look up)
8. **Writing Tips** (3 specific tips for this essay type and topic)"""
    return _call_gemini_debug(prompt, OUTLINE_SYSTEM)


def improve_essay(original: str, instruction: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""ORIGINAL ESSAY:
{original[:7000]}

IMPROVEMENT REQUEST: {instruction}

Rewrite the complete essay with the requested improvements applied.
Use [EDITED: reason] markers inline to show key changes.
Return the full improved version."""
    return _call_gemini_debug(prompt, IMPROVE_SYSTEM)


def score_essay(essay_text: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Evaluate this essay across 6 dimensions. Be specific and actionable.

ESSAY:
{essay_text[:5000]}

Score each dimension 1-10 with brief justification:
1. **Thesis Clarity & Arguability** (X/10) — ...
2. **Evidence Quality & Use** (X/10) — ...
3. **Argument Logic & Structure** (X/10) — ...
4. **Writing Style & Voice** (X/10) — ...
5. **Paragraph Cohesion & Flow** (X/10) — ...
6. **Academic Conventions** (X/10) — ...

**Overall Score: X/10**
**Grade Equivalent:** A/B/C/D/F

**Top 3 Strengths:**
**Top 3 Improvements:**
**One-Sentence Verdict:**"""
    return _call_gemini_debug(prompt, ESSAY_SYSTEM)


def generate_essay_chunked(
    topic: str,
    essay_type: str,
    word_count: int = 2500,
    academic_level: str = "Undergraduate",
    citation_style: str = "APA 7th",
    key_points: str = "",
    context_text: str = "",
    tone: str = "Academic",
    audience: str = "",
) -> str:
    """
    FIX-4.1b: Chunked essay generation for very long essays (>2000 words).
    Pipeline: outline → per-section generation → coherence pass.
    """
    from utils.ai_engine import generate as _gen
    type_guidance = ESSAY_TYPES.get(essay_type, "")

    # Step 1: Generate outline
    outline_prompt = f"""Create a detailed section outline for a {word_count}-word {essay_type} on: {topic}
Academic Level: {academic_level} | Style: {citation_style}
{type_guidance}

Return ONLY a JSON array of sections:
[{{"title": "Introduction", "summary": "one sentence", "target_words": 250}}, ...]"""
    import json as _json
    outline_raw = _gen(
        prompt=outline_prompt,
        system=OUTLINE_SYSTEM,
        max_tokens=1500,
        temperature=0.3,
    )
    try:
        m = re.search(r'\[.*\]', outline_raw, re.DOTALL)
        sections = _json.loads(m.group(0)) if m else []
    except Exception:
        sections = [
            {"title": "Introduction", "summary": "Hook, context, thesis", "target_words": word_count // 5},
            {"title": "Body", "summary": "Main arguments with evidence", "target_words": word_count * 3 // 5},
            {"title": "Counter-argument & Rebuttal", "summary": "Opposing view + refutation", "target_words": word_count // 6},
            {"title": "Conclusion", "summary": "Synthesis and implications", "target_words": word_count // 6},
        ]

    outline_text = "\n".join(f"{s['title']}: {s.get('summary','')}" for s in sections)

    # Step 2: Generate each section independently
    section_texts = []
    for section in sections:
        sec_prompt = f"""Write ONLY the '{section["title"]}' section of a {essay_type} on: {topic}
Target: ~{section.get("target_words", 300)} words | Level: {academic_level}
Essay Outline for context:
{outline_text}
{f"Key points to include: {key_points}" if key_points.strip() else ""}
{f"Source material: {context_text[:3000]}" if context_text.strip() else ""}
Do NOT write other sections. Write ONLY this section now:"""
        sec_text = _gen(
            prompt=sec_prompt,
            system=ESSAY_SYSTEM,
            max_tokens=3000,
            temperature=0.6,
        )
        section_texts.append(sec_text)

    combined = "\n\n".join(section_texts)

    # Step 3: Coherence pass — smooth transitions only
    coherence_prompt = f"""The following essay was written in separate sections. 
Smooth the transitions between sections ONLY — do NOT rewrite the content.
Make it flow as one unified piece.

ESSAY:
{combined[:12000]}

Return the complete smoothed essay:"""
    final = _gen(
        prompt=coherence_prompt,
        system="You are an expert editor. Only improve transitions and flow. Preserve all content.",
        max_tokens=12288,
        temperature=0.3,
    )
    return final


def check_essay_originality(essay_text: str) -> str:
    """
    FIX-4.2: AI-powered originality / plagiarism-style check.
    Returns a styled scorecard with ratings per dimension.
    """
    from utils.ai_engine import generate as _gen
    prompt = f"""Analyze the following essay for signs of AI-generated text or plagiarized style.
Look for: repetitive sentence structures, generic transitions (furthermore, moreover, in conclusion),
unnaturally uniform paragraph lengths, absence of personal voice or specific examples,
excessive hedging language.

Rate each dimension 1-10 (10=most human/original):
- Voice Authenticity: X/10
- Structural Variety: X/10
- Specificity of Examples: X/10
- Transition Naturalness: X/10
- Overall Originality Score: X/10

Then provide 3 specific rewrite suggestions to improve originality.

ESSAY:
{essay_text[:6000]}"""
    return _gen(
        prompt=prompt,
        system="You are a plagiarism detection specialist and academic integrity expert.",
        max_tokens=2048,
        temperature=0.2,
    )


def generate_cowrite_addition(existing_essay: str, section_to_add: str, context_text: str = "") -> tuple:
    """
    FIX-4.3: Co-write AI with full essay context. Returns (new_text, diff_html).
    Uses the FULL existing essay (up to 8000 chars) as context.
    """
    from utils.ai_engine import generate as _gen
    import difflib

    prompt = f"""The following is an existing essay. Do NOT rewrite what already exists.
ONLY write the new '{section_to_add}' that comes AFTER the last sentence.

EXISTING ESSAY (context only — do not reproduce):
{existing_essay[-8000:]}

Now write ONLY the new {section_to_add} content that continues seamlessly:"""

    new_content = _gen(
        prompt=prompt,
        system=ESSAY_SYSTEM,
        max_tokens=4096,
        temperature=0.6,
    )

    # Build diff HTML
    old_lines = existing_essay.splitlines()
    new_lines = (existing_essay + "\n" + new_content).splitlines()
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm="", n=0))
    diff_html_parts = []
    for line in diff:
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+"):
            diff_html_parts.append(f'<ins style="background:#1a3d1a;color:#86efac;text-decoration:none;display:block;padding:1px 4px;">{line[1:]}</ins>')
        elif line.startswith("-"):
            diff_html_parts.append(f'<del style="background:#3d1212;color:#fca5a5;display:block;padding:1px 4px;">{line[1:]}</del>')
    diff_html = "\n".join(diff_html_parts) or f'<ins style="background:#1a3d1a;color:#86efac;display:block;">{new_content}</ins>'

    return new_content, diff_html

