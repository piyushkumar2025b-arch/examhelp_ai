"""
utils/citation_engine.py — AI-Powered Academic Citation Generator v2.0
FIX-10.5: All 7 academic styles, parallel bulk, DOI lookup, BibTeX export.
"""
from __future__ import annotations
import concurrent.futures
from utils.ai_engine import generate as ai_generate

CITATION_STYLES = {
    "APA 7th":     "American Psychological Association 7th ed. (Author, Year) in-text. Full reference: Author, A. A. (Year). Title. Publisher.",
    "MLA 9th":     "Modern Language Association 9th ed. Author Page# in-text. Works Cited entry.",
    "Chicago 17th":"Chicago/Turabian 17th. Footnote style with full bibliography entry.",
    "Harvard":     "Parenthetical author-date (Author Year). Full reference list at end.",
    "IEEE":        "Bracketed number [n] in-text. Full reference: [n] Author, 'Title,' Journal, vol., no., pp., Year.",
    "Vancouver":   "Numbered superscripts. Used in medical/biomedical contexts. Full reference: n. Author AB. Title. Journal. Year;vol(issue):pages.",
    "Oxford":      "Footnote numbered superscripts (Oxford Referencing). Short note + bibliography.",
}


def generate_citation(source: str, style: str = "APA 7th") -> str:
    """
    Generate a formatted citation using AI.
    Supports all 7 major academic styles with style-specific formatting.
    """
    style_desc = CITATION_STYLES.get(style, "Standard academic style.")

    system = (
        f"You are a specialist academic librarian. Format citations EXACTLY in {style} style. "
        f"Style specification: {style_desc} "
        f"If the source is a URL, infer author/date from what you know. "
        f"If a book or paper title, provide a correctly formatted entry. "
        f"Return ONLY the formatted citation string, nothing else. No preamble."
    )
    try:
        return ai_generate(
            prompt=f"Source: {source}",
            system=system,
            temperature=0.1,
            max_tokens=512,
        ).strip().strip('"')
    except Exception as e:
        return f"[Citation Error: {e}]"


def bulk_generate(sources: list, style: str = "APA 7th") -> str:
    """
    FIX-10.5: Generate multiple citations sequentially.
    Numbers IEEE-style with [n] markers.
    """
    out = []
    for i, src in enumerate(sources, 1):
        if src.strip():
            cit = generate_citation(src, style)
            if style == "IEEE":
                out.append(f"[{i}] {cit}")
            elif style == "Vancouver":
                out.append(f"{i}. {cit}")
            else:
                out.append(f"- {cit}")
    return "\n\n".join(out)


def bulk_generate_parallel(sources: list, style: str = "APA 7th", max_workers: int = 3) -> str:
    """
    FIX-10.5 ADD: Parallel bulk generation using ThreadPoolExecutor.
    Preserves input order in results.
    """
    results = [""] * len(sources)

    def _cite(idx: int, src: str) -> None:
        if src.strip():
            results[idx] = generate_citation(src, style)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_cite, i, s) for i, s in enumerate(sources)]
        concurrent.futures.wait(futures)

    out = []
    for i, (src, cit) in enumerate(zip(sources, results), 1):
        if not src.strip():
            continue
        if style == "IEEE":
            out.append(f"[{i}] {cit}")
        elif style == "Vancouver":
            out.append(f"{i}. {cit}")
        else:
            out.append(f"- {cit}")
    return "\n\n".join(out)


def citation_to_bibtex(source: str) -> str:
    """
    FIX-10.5 ADD: Convert any source to BibTeX format for LaTeX users.
    """
    system = (
        "You are an expert BibTeX formatter. Convert the given source into a complete, valid BibTeX entry. "
        "Generate an appropriate key (AuthorYear format). "
        "Return ONLY the BibTeX entry starting with @article{ or @book{ or @misc{ etc. No preamble."
    )
    try:
        return ai_generate(
            prompt=f"Source: {source}",
            system=system,
            temperature=0.1,
            max_tokens=512,
        ).strip()
    except Exception as e:
        return f"% BibTeX Error: {e}"


def cite_from_doi(doi: str, style: str = "APA 7th") -> str:
    """
    FIX-10.5 ADD: Generate citation from a DOI (uses CrossRef API with AI fallback).
    """
    import requests
    try:
        # Step 1: try CrossRef REST API for metadata
        clean_doi = doi.strip().lstrip("https://doi.org/").lstrip("http://dx.doi.org/")
        url = f"https://api.crossref.org/works/{clean_doi}"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json().get("message", {})
            authors = data.get("author", [])
            author_str = ", ".join(
                f"{a.get('family', '')} {a.get('given', '')[:1]}."
                for a in authors[:3]
            )
            year_parts = data.get("issued", {}).get("date-parts", [[]])
            year = year_parts[0][0] if year_parts and year_parts[0] else "n.d."
            title = data.get("title", [""])[0]
            journal = data.get("container-title", [""])[0]
            source_str = f"{author_str}. ({year}). {title}. {journal}. https://doi.org/{clean_doi}"
            return generate_citation(source_str, style)
    except Exception:
        pass
    # Fallback: let AI handle the DOI directly
    return generate_citation(f"DOI: {doi}", style)

