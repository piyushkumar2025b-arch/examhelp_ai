"""
research_tools_engine.py — Advanced Research & Academic Tools v2.0
Scientific critique, literature review, citation generation, research gap analysis,
methodology assessment, and academic writing assistance.
Free live data: Wikipedia API + Open Library (no key needed).
"""
from __future__ import annotations
from typing import Dict, List
from utils.ai_engine import quick_generate, generate
from free_apis import (
    search_wikipedia, get_wikipedia_summary,
    search_books, duckduckgo_search,
    search_arxiv, search_crossref, search_semantic_scholar,
    get_today_in_history,
    search_google_books, search_zenodo, search_internet_archive,
    get_open_access_paper,
)


RESEARCH_SYSTEM = """\
You are a Senior Research Scientist, Academic Editor, and Peer Reviewer with expertise across 
STEM, Social Sciences, and Humanities. Provide rigorous, publication-standard academic analysis.
Structure all responses with clear headers. Use academic language but remain accessible.
When critiquing: be constructive, specific, and evidence-based.
"""

CITATION_STYLES = {
    "APA 7th":    "Author, A. A. (Year). Title. Journal, Volume(Issue), pages. https://doi.org/...",
    "MLA 9th":    "Author. \"Title.\" Journal, vol. X, no. X, Year, pp. X-X.",
    "Harvard":    "Author (Year) 'Title', Journal, vol. X, no. X, pp. X-X.",
    "Chicago 17": "Author. \"Title.\" Journal X, no. X (Year): X-X. https://doi.org/...",
    "Vancouver":  "Author A, Author B. Title. Journal. Year;Volume(Issue):pages.",
    "IEEE":       "[1] A. Author, \"Title,\" Journal, vol. X, no. X, pp. X-X, Year.",
}

RESEARCH_DOMAINS = {
    "Computer Science & AI":    "CS, ML, AI, software engineering, systems",
    "Medicine & Life Sciences": "Clinical, biology, pharmacology, genetics",
    "Physics & Chemistry":      "Natural sciences, experiments, quantum, materials",
    "Social Sciences":          "Psychology, sociology, economics, political science",
    "Mathematics":              "Pure math, applied math, statistics",
    "Engineering":              "Civil, mechanical, electrical, chemical engineering",
    "Humanities":               "History, literature, philosophy, cultural studies",
    "Business & Management":    "Strategy, finance, organizational behavior, marketing",
    "Education Research":       "Pedagogy, curriculum, learning outcomes, assessment",
    "Environmental Science":    "Climate, ecology, sustainability, environmental policy",
}


class ResearchTools:
    """Professional academic research and critique."""

    @staticmethod
    def critique_paper(
        abstract_or_text: str,
        domain: str = "Computer Science & AI",
        review_type: str = "Peer Review",
    ) -> str:
        """Rigorous scientific peer-review critique."""
        domain_desc = RESEARCH_DOMAINS.get(domain, domain)
        return generate(
            prompt=f"""Perform a {review_type} of this academic work:

DOMAIN: {domain} — {domain_desc}

ABSTRACT/TEXT:
{abstract_or_text[:6000]}

REVIEW STRUCTURE:
## Summary (3-4 sentences)
## Strengths
(Specific strong points with justification)

## Weaknesses & Limitations
| Issue | Severity (High/Med/Low) | Suggested Fix |
|-------|------------------------|---------------|

## Methodology Assessment
- Data collection: adequate/inadequate — explain
- Statistical methods: appropriate/issues — explain
- Controls/comparisons: present/missing

## Novelty & Contribution
(How does this advance the field? Gap it fills?)

## Quality of Evidence
(Strength of claims vs evidence presented)

## Missing References / Comparisons
## Recommended Revisions
(Minor / Major / Reject with reasons)

## Overall Verdict
**Decision**: Accept / Minor Revision / Major Revision / Reject
**Confidence**: High / Medium
**Summary sentence**: [one-line verdict]""",
            system=RESEARCH_SYSTEM,
            engine_name="researcher",
            max_tokens=2500,
        ) or "Critique unavailable."

    @staticmethod
    def generate_lit_review(
        topics: List[str],
        focus_area: str = "General",
        domain: str = "Computer Science & AI",
        years_range: str = "2018-2024",
    ) -> str:
        """Literature review — multi-source academic grounding then AI-expanded."""
        topics_str  = ", ".join(topics) if isinstance(topics, list) else topics
        domain_desc = RESEARCH_DOMAINS.get(domain, domain)

        # ── 1. Wikipedia background extracts ───────────────────────────────
        wiki_context = []
        topic_list   = topics if isinstance(topics, list) else [topics]
        for topic in topic_list[:3]:
            try:
                wiki = get_wikipedia_summary(topic)
                if wiki and wiki.get("extract"):
                    wiki_context.append(f"[{topic}]: {wiki['extract'][:300]}")
            except Exception:
                pass

        # ── 2. DuckDuckGo contextual overview ─────────────────────────────
        ddg_context = ""
        try:
            ddg = duckduckgo_search(topics_str)
            if ddg and ddg.get("abstract"):
                ddg_context = f"\nContextual Overview: {ddg['abstract'][:400]}"
        except Exception:
            pass

        # ── 3. arXiv live papers ─────────────────────────────────────────
        arxiv_block = ""
        try:
            papers = search_arxiv(topics_str, max_results=4)
            if papers:
                arxiv_lines = []
                for p in papers[:4]:
                    authors = ", ".join(p["authors"][:2]) + (" et al." if len(p["authors"]) > 2 else "")
                    arxiv_lines.append(f"- {p['title']} ({authors}, {p['published'][:4]}) [{', '.join(p['categories'][:2])}]")
                arxiv_block = "\n\narXiv Recent Papers:\n" + "\n".join(arxiv_lines)
        except Exception:
            pass

        # ── 4. Semantic Scholar / CrossRef papers ─────────────────────────
        scholar_block = ""
        try:
            s2_papers = search_semantic_scholar(topics_str, limit=4)
            if s2_papers:
                s2_lines = []
                for p in s2_papers[:4]:
                    authors = ", ".join(p["authors"][:2]) + (" et al." if len(p["authors"]) > 2 else "")
                    s2_lines.append(f"- {p['title']} ({authors}, {p['year']}) [{p['citations']} citations]"
                                    + (f" DOI:{p['doi']}" if p.get("doi") else ""))
                scholar_block = "\n\nSemantic Scholar Results:\n" + "\n".join(s2_lines)
        except Exception:
            try:
                cr_papers = search_crossref(topics_str, limit=4, year_from=2015)
                if cr_papers:
                    cr_lines = [f"- {p['title']} ({', '.join(p['authors'][:2])}, {p['year']}) {p['journal']}" for p in cr_papers[:4]]
                    scholar_block = "\n\nCrossRef Papers:\n" + "\n".join(cr_lines)
            except Exception:
                pass

        wiki_block = "\n".join(wiki_context)
        seed = ""
        if wiki_block or ddg_context:
            seed += f"\n\nBackground (Wikipedia):\n{wiki_block}{ddg_context}"
        if arxiv_block:
            seed += arxiv_block
        if scholar_block:
            seed += scholar_block

        return generate(
            prompt=f"""Write a structured Literature Review for:

Topics: {topics_str}
Focus Area: {focus_area}
Domain: {domain} — {domain_desc}
Publication Period: {years_range}{seed}

STRUCTURE:
## Introduction to the Literature
(Set the scene, explain why this area matters)

## Thematic Analysis
(Group papers by theme, not chronology)
### Theme 1: [name]
- Key findings, agreements, contradictions
- Landmark papers in this theme

### Theme 2: [name]
### Theme N: [name]

## Methodological Trends
(What methods dominate? What's emerging?)

## Key Debates & Controversies
(Where do researchers disagree? Why?)

## Critical Synthesis
(What does the collective literature tell us?)

## Research Gaps Identified
(What questions remain unanswered?)

## Transition to Current Study
(Lead into how your research addresses the gaps)

Use academic language. Reference specific authors/years where appropriate.""",
            system=RESEARCH_SYSTEM,
            engine_name="researcher",
            max_tokens=3000,
        ) or "Literature review unavailable."

    @staticmethod
    def suggest_research_gap(
        literature_summary: str,
        domain: str = "Computer Science & AI",
    ) -> str:
        """Identify potential research gaps with novelty assessment."""
        domain_desc = RESEARCH_DOMAINS.get(domain, domain)
        return generate(
            prompt=f"""Analyze this literature summary and identify research gaps.

Domain: {domain} — {domain_desc}

LITERATURE SUMMARY:
{literature_summary[:5000]}

Provide:
## Identified Research Gaps
For each gap:
**Gap N**: [clear description of what's missing]
- **Evidence**: which papers reveal this gap
- **Significance**: why this matters
- **Feasibility**: can it be studied? What resources needed?
- **Novelty Score**: High / Medium / Low
- **Suggested Research Question**: [precise research question to address it]

## Methodological Gaps
(Not just topic gaps — methods not yet applied)

## Geographic/Population Gaps
(Under-studied regions, demographics)

## Recommended Research Designs
(Best approaches to fill the most significant gaps)

## Interdisciplinary Opportunities
(Connections to adjacent fields that could unlock new insights)""",
            system=RESEARCH_SYSTEM,
            engine_name="researcher",
            max_tokens=2000,
        ) or "Gap analysis unavailable."

    @staticmethod
    def generate_citation(
        title: str,
        authors: str,
        year: str,
        journal: str = "",
        doi: str = "",
        volume: str = "",
        issue: str = "",
        pages: str = "",
        style: str = "APA 7th",
    ) -> Dict[str, str]:
        """Generate citations in multiple formats."""
        results = {}
        for s, template in CITATION_STYLES.items():
            result = quick_generate(
                prompt=f"""Format this reference in {s} citation style:
Title: {title}
Authors: {authors}
Year: {year}
Journal: {journal}
DOI: {doi}
Volume: {volume}, Issue: {issue}, Pages: {pages}

Return ONLY the formatted citation string. No explanation. Follow {s} exactly: {template}""",
                engine_name="researcher",
            )
            results[s] = result.strip() if result else f"[{authors} ({year}). {title}. {journal}]"
        return results

    @staticmethod
    def write_abstract(
        research_summary: str,
        word_limit: int = 250,
        structure: str = "IMRaD",
    ) -> str:
        """Write a formatted academic abstract."""
        structures = {
            "IMRaD": "Introduction, Methods, Results and Discussion",
            "Structured": "Background, Objectives, Methods, Results, Conclusions",
            "Unstructured": "Flowing paragraph without subheadings",
        }
        return generate(
            prompt=f"""Write a professional academic abstract ({word_limit} words max).
Structure: {structure} ({structures.get(structure, '')})

Research Summary:
{research_summary[:3000]}

Requirements:
- Exactly follow {structure} structure
- Include: research problem, methodology, key results, conclusion
- Use active voice where possible
- No citations in abstract
- End with significance / implications statement
- Exactly {word_limit} words or fewer""",
            system=RESEARCH_SYSTEM,
            engine_name="researcher",
            max_tokens=600,
        ) or "Abstract unavailable."

    @staticmethod
    def methodology_advisor(
        research_question: str,
        domain: str = "Computer Science & AI",
        constraints: str = "",
    ) -> str:
        """Recommend the best research methodology for a given question."""
        domain_desc = RESEARCH_DOMAINS.get(domain, domain)
        return generate(
            prompt=f"""Recommend the optimal research methodology for:

Research Question: {research_question}
Domain: {domain} — {domain_desc}
{f"Constraints: {constraints}" if constraints else ""}

Provide:
## Recommended Methodology
(Primary approach with justification)

## Rationale
(Why this is the strongest approach for this question)

## Research Design
(Specific design: experimental/quasi-experimental/survey/case study/etc.)

## Data Collection Methods
(What data to collect, how, from whom)

## Sample / Data Requirements
(Sample size guidance, data sources, inclusion/exclusion criteria)

## Analysis Methods
(Statistical or qualitative analysis techniques)

## Alternative Approaches
(2-3 alternatives with pros/cons)

## Validity & Reliability Strategies
(How to ensure rigorous, credible results)

## Ethical Considerations
(IRB needs, consent, data privacy)

## Timeline Estimate
(Rough phases for a 6-12 month study)""",
            system=RESEARCH_SYSTEM,
            engine_name="researcher",
            max_tokens=2000,
        ) or "Methodology advice unavailable."

    @staticmethod
    def paraphrase_academic(text: str, style: str = "Academic") -> str:
        """Paraphrase academic text while preserving technical meaning."""
        return generate(
            prompt=f"""Paraphrase this academic text in {style} style.
Rules: Preserve ALL technical accuracy. Change sentence structures significantly. 
Do not lose any nuance. Keep the same level of formality. No plagiarism.
Output ONLY the paraphrased text.

TEXT:
{text[:4000]}""",
            system=RESEARCH_SYSTEM,
            engine_name="researcher",
            max_tokens=2000,
        ) or text
