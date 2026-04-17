"""
medical_engine.py — Clinical Scenario Analysis & Medical Education v2.0
AI-powered medical education, clinical reasoning, pharmacology, and MCQ generator.
Enriched with: Wikipedia (conditions) + PubChem (drugs/compounds) + Disease.sh (stats).
All free, no API key needed.
⚠️ EDUCATIONAL USE ONLY — not medical advice.
"""
from __future__ import annotations
from typing import Dict, List
from utils.ai_engine import quick_generate, generate
from free_apis import (
    get_wikipedia_summary, search_wikipedia,
    get_compound, get_global_disease_stats, get_country_disease_stats,
    search_pubmed, get_chembl_drug, search_chembl,
    search_uniprot, get_protein,
)


DISCLAIMER = "\n\n---\n⚠️ **EDUCATIONAL NOTE**: This analysis is for academic/learning purposes only. Always consult a qualified healthcare professional for actual medical decisions."

MEDICAL_SYSTEM = """\
You are a senior medical educator and clinical consultant with expertise across all major specialties.
Provide rigorous, structured medical education content.
Always:
1. Use proper medical terminology with lay explanations in parentheses
2. Organize responses with clear headers
3. Include differential diagnoses when analyzing symptoms
4. Reference relevant clinical guidelines (NICE, WHO, AHA, etc.)
5. End with an educational disclaimer
Never give actual medical advice — frame all content as educational.
"""

SPECIALTIES = {
    "Internal Medicine":       "General adult medicine, common systemic diseases",
    "Surgery":                 "Pre/peri/post-operative care, surgical anatomy, techniques",
    "Pediatrics":              "Child health, developmental milestones, pediatric diseases",
    "Cardiology":              "Heart diseases, ECG interpretation, cardiac pharmacology",
    "Neurology":               "Nervous system disorders, neuro-anatomy, stroke, epilepsy",
    "Psychiatry":              "Mental health disorders, psychopharmacology, DSM-5",
    "Pharmacology":            "Drug mechanisms, pharmacokinetics, drug interactions",
    "Pathology":               "Disease mechanisms, histopathology, lab interpretation",
    "Anatomy":                 "Human body structure, clinical anatomy correlations",
    "Physiology":              "Body functions, homeostasis, organ system physiology",
    "Biochemistry":            "Metabolic pathways, enzyme kinetics, molecular biology",
    "Orthopedics":             "Bone, joint, and muscle disorders, fractures",
    "Ophthalmology":           "Eye diseases, visual system, optics",
    "Dermatology":             "Skin conditions, dermatology mnemonics, rashes",
    "Emergency Medicine":      "ACLS, trauma management, triage, emergency protocols",
    "Gynecology & Obstetrics": "Female reproductive health, pregnancy, labor",
    "Microbiology":            "Pathogens, antibiotics, infections, immunology",
    "Oncology":                "Cancer biology, staging, treatment modalities",
}


class MedicalEngine:
    """Medical education analysis and clinical reasoning."""

    @staticmethod
    def analyze_symptoms(
        symptom_list: List[str],
        patient_info: str = "Adult patient",
        specialty: str = "Internal Medicine",
    ) -> str:
        """Analyze symptoms — educational differential diagnosis."""
        symptoms = ", ".join(symptom_list) if isinstance(symptom_list, list) else symptom_list
        result = generate(
            prompt=f"""EDUCATIONAL CLINICAL ANALYSIS

Patient: {patient_info}
Presenting Symptoms: {symptoms}
Specialty Focus: {specialty}

Provide:
## Chief Complaint Summary
## Differential Diagnosis (most to least likely — 5-8 diagnoses)
| Diagnosis | Key Supporting Features | Key Against |
|-----------|------------------------|-------------|

## Priority Investigations
(list in order: bedside → bloods → imaging → specialist)

## Red Flags to Watch For
(symptoms/signs requiring immediate escalation)

## Initial Management Approach
(general principles only — educational)

## Learning Points
(key clinical pearls for this presentation)""",
            system=MEDICAL_SYSTEM,
            engine_name="medical_expert",
            max_tokens=2000,
        )
        return (result or "Analysis unavailable.") + DISCLAIMER

    @staticmethod
    def explain_condition(condition: str, level: str = "Medical Student", specialty: str = "Internal Medicine") -> str:
        """Full structured explanation — Wikipedia + PubChem (drugs) + AI elaboration."""
        level_map = {
            "Patient Friendly": "Simple language, avoid jargon, use analogies",
            "Medical Student":  "Full medical detail, include pathophysiology, mention exam-relevant points",
            "Junior Doctor":    "Clinical focus, management protocols, prescribing guidelines",
            "USMLE/MBBS Prep":  "High-yield facts, classic presentations, buzzwords, common MCQ traps",
        }
        hint = level_map.get(level, "Medical Student level")

        # ── Wikipedia factual seed ──────────────────────────────────────────
        wiki_seed = ""
        try:
            wiki = get_wikipedia_summary(condition)
            if wiki and wiki.get("extract"):
                wiki_seed = f"\n\nWikipedia Overview: {wiki['extract'][:600]}"
        except Exception:
            pass

        # ── PubChem compound/drug data (if condition looks like a drug name) ───
        pubchem_seed = ""
        try:
            chem = get_compound(condition)
            if chem and chem.get("molecular_formula"):
                pubchem_seed = (
                    f"\n\nPubChem Data: {condition.capitalize()} — "
                    f"Formula: {chem['molecular_formula']}, "
                    f"MW: {chem['molecular_weight']} g/mol, "
                    f"IUPAC: {chem['iupac_name']}"
                )
        except Exception:
            pass

        result = generate(
            prompt=f"""Explain: **{condition}**
Level: {level} — {hint}
Specialty: {specialty}{wiki_seed}{pubchem_seed}

Structure:
## Definition & Epidemiology
## Etiology & Risk Factors
## Pathophysiology (with mechanism)
## Clinical Features (symptoms + signs, classic presentation)
## Investigations (what to order and expected findings)
## Management (medical / surgical / lifestyle)
## Complications
## Prognosis
## High-Yield Exam Points 🎯
## Mnemonics (if applicable)""",
            system=MEDICAL_SYSTEM,
            engine_name="medical_expert",
            max_tokens=2500,
        )
        return (result or "Explanation unavailable.") + DISCLAIMER

    @staticmethod
    def pharmacokinetics_check(drug_list: List[str], context: str = "") -> str:
        """Drug profiles and interaction analysis."""
        drugs = ", ".join(drug_list) if isinstance(drug_list, list) else drug_list
        result = generate(
            prompt=f"""Analyze these drugs for educational purposes: {drugs}
{f"Clinical context: {context}" if context else ""}

Provide:
## Individual Drug Profiles
For each drug:
- **Mechanism**: MOA
- **Pharmacokinetics**: ADME summary
- **Indications**: main uses
- **Side Effects**: common + serious
- **Contraindications**: key ones
- **Monitoring**: what to watch

## Drug-Drug Interactions (if multiple drugs)
| Interaction | Mechanism | Clinical Effect | Management |
|------------|-----------|-----------------|-----------|

## Clinical Pearls 🎯
Key points for prescribing / exam""",
            system=MEDICAL_SYSTEM,
            engine_name="medical_expert",
            max_tokens=2000,
        )
        return (result or "Pharmacology analysis unavailable.") + DISCLAIMER

    @staticmethod
    def generate_mcq(
        topic: str,
        specialty: str = "Internal Medicine",
        difficulty: str = "USMLE Step 1",
        count: int = 5,
    ) -> str:
        """Generate medical MCQs in clinical vignette style."""
        return generate(
            prompt=f"""Generate {count} {difficulty}-style MCQs for: {topic} ({specialty})

Format each:
**Q{{}}: [Clinical vignette — patient scenario, 3-5 sentences]**
A) option
B) option
C) option
D) option
E) option

**Correct Answer**: X
**Explanation**: Why X is correct and why the others are wrong (learning point per distractor)

Make vignettes realistic. Include classic presentations, buzzwords, and typical exam traps.""",
            system=MEDICAL_SYSTEM,
            engine_name="medical_expert",
            max_tokens=3000,
        ) or "MCQ generation unavailable."

    @staticmethod
    def interpret_lab(test_name: str, value: str, patient_context: str = "") -> str:
        """Help interpret a lab result in educational context."""
        result = generate(
            prompt=f"""Educational lab interpretation:
Test: {test_name}
Value: {value}
{f"Patient context: {patient_context}" if patient_context else ""}

Provide:
## Normal Range
## What this value indicates (high/low/normal)
## Common Causes (if abnormal)
## How to investigate further
## Clinical significance
## Exam Tips 🎯""",
            system=MEDICAL_SYSTEM,
            engine_name="medical_expert",
            max_tokens=1000,
        )
        return (result or "Interpretation unavailable.") + DISCLAIMER

    @staticmethod
    def anatomy_quiz(region: str, count: int = 5) -> str:
        """Generate anatomy identification questions."""
        return generate(
            prompt=f"""Generate {count} anatomy questions for: {region}

For each:
**Q**: [clear anatomical question]
✅ **Answer**: [precise anatomical answer]
📌 **Clinical Correlation**: [why this matters clinically — 1 sentence]

Mix: identification, relations, blood supply, nerve supply, clinical applications.""",
            system=MEDICAL_SYSTEM,
            engine_name="medical_expert",
            max_tokens=1500,
        ) or "Anatomy quiz unavailable."
