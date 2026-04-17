"""
legal_engine.py — AI Legal Case Analysis & Reasoning v2.0
Professional legal reasoning, case analysis, statute lookup, brief drafting, and exam prep.
⚠️ EDUCATIONAL USE ONLY — not legal advice.
"""
from __future__ import annotations
from typing import Dict, List
from utils.ai_engine import quick_generate, generate

DISCLAIMER = "\n\n---\n⚠️ **DISCLAIMER**: This analysis is for educational purposes only and does not constitute legal advice. Consult a qualified attorney for actual legal matters."

LEGAL_SYSTEM = """\
You are a Senior Counsel and Legal Academic with expertise in multiple jurisdictions.
Provide rigorous, well-structured legal analysis:
1. Apply IRAC (Issue, Rule, Application, Conclusion) or CREAC method
2. Cite relevant legal principles, landmark cases, and statutes by name
3. Analyze both sides (plaintiff & defendant perspectives)
4. Use proper legal terminology with plain-English clarification
5. Note jurisdictional variations where significant
Never give actual legal advice — clearly frame as educational analysis.
"""

JURISDICTIONS = {
    "Common Law / International": "General common law principles applicable internationally",
    "Indian Law":                 "Indian Constitution, IPC, CPC, CrPC, Indian Contract Act, specific Indian statutes",
    "US Law":                     "US Constitution, Federal/State law, UCC, common law principles",
    "UK Law":                     "English common law, UK statutes, ECHR, EU law (historical)",
    "EU Law":                     "European Union law, GDPR, competition law, directives",
    "International Law":          "Public international law, treaties, ICC, UN frameworks",
    "Corporate/Business Law":     "Company law, contracts, IP, employment, mergers & acquisitions",
    "Criminal Law (General)":     "General criminal law principles, actus reus, mens rea, defences",
    "Constitutional Law":         "Fundamental rights, constitutional interpretation, separation of powers",
    "Tort Law":                   "Negligence, strict liability, trespass, damages assessment",
    "Contract Law":               "Offer, acceptance, consideration, breach, remedies",
    "Family Law":                 "Marriage, divorce, custody, adoption, succession",
    "Intellectual Property":      "Copyright, patent, trademark, trade secrets",
    "Cyber / IT Law":             "Data protection, cybercrime, e-commerce, digital contracts",
}

BRIEF_STYLES = {
    "IRAC":  "Issue → Rule → Application → Conclusion",
    "CREAC": "Conclusion → Rule → Explanation → Application → Conclusion",
    "FIRAC": "Facts → Issue → Rule → Application → Conclusion",
}


class LegalEngine:
    """Professional legal analysis and hypothetical scenario reasoning."""

    @staticmethod
    def analyze_case(
        case_text: str,
        jurisdiction: str = "Common Law / International",
        analysis_depth: str = "Full IRAC",
    ) -> str:
        """Full structured legal case analysis."""
        j_desc = JURISDICTIONS.get(jurisdiction, "General common law")
        result = generate(
            prompt=f"""JURISDICTION: {jurisdiction} — {j_desc}

CASE/FACT SCENARIO:
{case_text}

Provide a complete legal analysis:

## Issues Identified
(List all legal issues — number each one)

## Applicable Law & Rules
(Statutes, principles, landmark cases for each issue)

## IRAC Analysis
For each issue:
**Issue N**: [state the legal question]
**Rule**: applicable law
**Application**: apply rule to facts
**Conclusion**: outcome for this issue

## Defenses & Counterarguments
(Arguments available to each party)

## Likely Outcome & Reasoning
## Remedies Available
## Relevant Landmark Cases
## Exam Notes 🎯
(High-yield points, common MCQ traps on this area of law)""",
            system=LEGAL_SYSTEM,
            engine_name="legal_expert",
            max_tokens=2500,
        )
        return (result or "Analysis unavailable.") + DISCLAIMER

    @staticmethod
    def check_compliance(
        fact_pattern: str,
        rule: str,
        jurisdiction: str = "Common Law / International",
    ) -> str:
        """Check if a fact pattern complies with a specific law."""
        j_desc = JURISDICTIONS.get(jurisdiction, "")
        result = generate(
            prompt=f"""Jurisdiction: {jurisdiction} — {j_desc}

FACT PATTERN:
{fact_pattern}

RULE/LAW/REGULATION:
{rule}

Analyze:
## Elements of the Rule
(Break the rule into every required element)

## Compliance Check
| Element | Satisfied? | Facts Supporting/Against |
|---------|-----------|--------------------------|

## Verdict: COMPLIANT / NON-COMPLIANT / UNCLEAR
## Liability Exposure
## Steps to Achieve Compliance
## Jurisdictional Variations""",
            system=LEGAL_SYSTEM,
            engine_name="legal_expert",
            max_tokens=1500,
        )
        return (result or "Compliance check unavailable.") + DISCLAIMER

    @staticmethod
    def generate_legal_brief(
        facts: str,
        issue: str,
        party: str = "Claimant/Plaintiff",
        jurisdiction: str = "Common Law / International",
        style: str = "IRAC",
    ) -> str:
        """Generate a structured legal brief draft."""
        style_desc = BRIEF_STYLES.get(style, "IRAC")
        j_desc = JURISDICTIONS.get(jurisdiction, "")
        result = generate(
            prompt=f"""Draft a professional legal brief using {style} ({style_desc}).

Jurisdiction: {jurisdiction} — {j_desc}
Acting for: {party}
Facts: {facts}
Legal Issue: {issue}

BRIEF STRUCTURE:
1. **Case Summary** (1 paragraph)
2. **Statement of Facts** (chronological, legally relevant only)
3. **Legal Issues** (numbered)
4. **Argument** ({style} for each issue, advocate for {party})
5. **Authorities** (cases, statutes, principles cited)
6. **Relief Sought** (specific remedies requested)
7. **Conclusion** (1 strong closing paragraph)

Write in formal legal prose. Cite authorities properly.""",
            system=LEGAL_SYSTEM,
            engine_name="legal_expert",
            max_tokens=2500,
        )
        return (result or "Brief unavailable.") + DISCLAIMER

    @staticmethod
    def explain_legal_concept(concept: str, jurisdiction: str = "Common Law / International") -> str:
        """Explain a legal concept for exam preparation."""
        j_desc = JURISDICTIONS.get(jurisdiction, "")
        result = generate(
            prompt=f"""Explain the legal concept: "{concept}"
Jurisdiction: {jurisdiction} — {j_desc}

Structure:
## Definition
## Historical Development
## Essential Elements / Requirements
## Key Cases (landmark judgments)
## Exceptions & Limitations
## Comparison with Similar Concepts
## Real-World Application
## Exam Tips 🎯 (common questions, traps, buzzwords)
## Example Hypothetical (with mini-analysis)""",
            system=LEGAL_SYSTEM,
            engine_name="legal_expert",
            max_tokens=2000,
        )
        return (result or "Explanation unavailable.") + DISCLAIMER

    @staticmethod
    def generate_legal_mcq(
        topic: str,
        jurisdiction: str = "Common Law / International",
        count: int = 5,
    ) -> str:
        """Generate legal MCQs in problem-based format."""
        return generate(
            prompt=f"""Generate {count} law MCQs for: {topic} ({jurisdiction})

Format each:
**Q**: [factual scenario — 3-5 sentences]
A) option
B) option
C) option
D) option

**Correct**: X
**Explanation**: Why X is right. Why others are wrong (one line each).

Use realistic fact patterns. Include classic traps and landmark case applications.""",
            system=LEGAL_SYSTEM,
            engine_name="legal_expert",
            max_tokens=2500,
        ) or "MCQ generation unavailable."

    @staticmethod
    def contract_review_checklist(contract_description: str) -> str:
        """Quick checklist for contract review red flags."""
        result = generate(
            prompt=f"""Contract Review Checklist for:
{contract_description}

Check:
## Essential Elements Present?
- [ ] Offer clearly defined?
- [ ] Acceptance unambiguous?
- [ ] Consideration stated?
- [ ] Parties have capacity?
- [ ] Legality of object?

## Key Clauses to Verify
- Termination clause, Limitation of liability, Governing law, Jurisdiction, Dispute resolution

## Red Flags Identified
(List any missing, vague, or potentially unfavorable terms)

## Recommendations
(What to negotiate or clarify)""",
            system=LEGAL_SYSTEM,
            engine_name="legal_expert",
            max_tokens=1500,
        )
        return (result or "Checklist unavailable.") + DISCLAIMER
