"""
utils/citation_engine.py — AI-Powered Academic Citation Generator
Generates IEEE, APA, MLA, and Harvard citations from URLs or raw titles.
"""
from __future__ import annotations
from utils.ai_engine import generate as ai_generate

CITATION_STYLES = {
    "IEEE": "The style used for technical and engineering papers. Uses bracketed numbers [1].",
    "APA": "American Psychological Association style. (Author, Date) format.",
    "MLA": "Modern Language Association style. Author Page # format.",
    "Harvard": "Parenthetical author-date style.",
    "BibTeX": "Standard bibliography format for LaTeX users.",
}

def generate_citation(source: str, style: str = "IEEE") -> str:
    """
    Generate a formatted citation using AI.
    """
    style_desc = CITATION_STYLES.get(style, "Standard academic style.")
    prompt = [
        {"role": "system", "content": (
            f"You are a specialized reference librarian. Generate a precise academic citation in {style} style. "
            f"Style Info: {style_desc} "
            f"If it's a URL, use what you know about the source. If it's a book/paper title, provide a generic but correctly formatted entry. "
            f"Return ONLY the formatted citation string, nothing else."
        )},
        {"role": "user", "content": f"Source: {source}"}
    ]
    try:
        return ai_generate(messages=prompt).strip().strip('"')
    except Exception as e:
        return f"[Citation Error: {e}]"

def bulk_generate(sources: list[str], style: str = "IEEE") -> str:
    """
    Generate multiple citations.
    """
    out = []
    for i, src in enumerate(sources, 1):
        if src.strip():
            cit = generate_citation(src, style)
            if style == "IEEE":
                out.append(f"[{i}] {cit}")
            else:
                out.append(f"- {cit}")
    return "\n\n".join(out)
