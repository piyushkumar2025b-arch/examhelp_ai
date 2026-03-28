"""
humaniser_engine.py — AI Text Humaniser v2.0 ULTRA
Next-level AI detection bypass + multiple humanisation strategies.
"""
from __future__ import annotations
import re
from typing import Dict, List, Tuple

HUMANISE_SYSTEM = """\
You are the world's most skilled text humaniser and ghostwriter. Transform AI-generated text into writing indistinguishable from human writing — passing GPTZero, Turnitin, Winston AI, and all detectors.

TRANSFORMATION RULES:
1. REMOVE all AI filler: "Certainly!", "Great question!", "Of course!", "Absolutely!", "It's worth noting", "In conclusion", "To summarize", "Furthermore", "Moreover", "Additionally", "In essence", "Notably", "Undoubtedly"
2. VARY sentence structure — short punchy sentences next to longer flowing ones
3. USE contractions naturally: I'm, don't, it's, you'll, can't, won't, that's
4. ADD personality: "Look,", "The thing is,", "Honestly,", "Here's the deal —"
5. KILL passive voice — make everything active and direct
6. INJECT natural imperfections: conversational asides, mild hedging ("roughly", "about")
7. USE varied vocabulary — never repeat same word twice in a paragraph
8. ADD rhetorical questions where natural: "Why does this matter?"
9. VARY paragraph length — mix one-sentence and multi-sentence paragraphs
10. REMOVE robotic enumeration (no "Firstly..., Secondly..., Thirdly...")
11. PRESERVE all technical accuracy — only tone/style changes
12. Output ONLY the rewritten text — zero preamble, no "Here is the humanised version:"
"""

ADVANCED_TONES = {
    "Casual / Friendly": "Warm, conversational — like explaining to a smart friend over coffee.",
    "Academic / Scholarly": "Scholarly but authentic — passionate researcher, not a robot.",
    "Professional / Business": "Confident, direct, polished — sharp memo from a senior exec.",
    "Creative / Narrative": "Vivid, engaging with personality — reads like a magazine feature.",
    "Gen Z / Youth": "Contemporary, punchy, some slang where natural. Energy.",
    "Technical / Expert": "Precise but human — engineer who cares about clarity. Concrete examples.",
    "Journalistic": "News-style: punchy lede, direct, factual but engaging.",
    "Social Media": "Punchy, hook-first, scannable. Emoji-friendly structure.",
    "Teacher / Educator": "Patient, clear, builds understanding step by step.",
    "Sales / Marketing": "Benefit-focused, persuasive, creates desire through specifics.",
}

AI_PATTERNS = [
    (r'\bCertainly[!,]?\b', 'FILLER'), (r'\bGreat question[!,]?\b', 'FILLER'),
    (r'\bOf course[!,]?\b', 'FILLER'), (r'\bAbsolutely[!,]?\b', 'FILLER'),
    (r"\bIt'?s worth noting\b", 'FILLER'), (r'\bIt is important to note\b', 'FILLER'),
    (r'\bIn conclusion\b', 'FILLER'), (r'\bTo summarize\b', 'FILLER'),
    (r'\bFurthermore\b', 'TRANSITION'), (r'\bMoreover\b', 'TRANSITION'),
    (r'\bAdditionally\b', 'TRANSITION'), (r'\bIn essence\b', 'FILLER'),
    (r'\bNotably\b', 'FILLER'), (r'\bUndoubtedly\b', 'FILLER'),
    (r'\bFirstly\b', 'ENUM'), (r'\bSecondly\b', 'ENUM'), (r'\bThirdly\b', 'ENUM'),
    (r'\bDelve into\b', 'AI_WORD'), (r'\bComprehensive\b', 'AI_WORD'),
    (r'\bFacilitate\b', 'AI_WORD'), (r'\bLeverage\b', 'AI_WORD'),
    (r'\bRobust\b', 'AI_WORD'), (r'\bUtilize\b', 'AI_WORD'),
    (r'\bSeamlessly\b', 'AI_WORD'), (r'\bMultifaceted\b', 'AI_WORD'),
]

def ai_detection_score(text: str) -> Dict:
    score = 0; flags = []
    for pattern, category in AI_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            if category == 'FILLER': flags.append(f"🚨 AI filler: '{matches[0]}'"); score += 8
            elif category == 'AI_WORD': flags.append(f"⚠️ AI buzzword: '{matches[0]}'"); score += 5
            elif category == 'ENUM': flags.append(f"⚠️ Robotic enum: '{matches[0]}'"); score += 6
            elif category == 'TRANSITION': score += 3
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    if len(sentences) > 3:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg)**2 for l in lengths) / len(lengths)
        if variance < 20: score += 15; flags.append("⚠️ Uniform sentence lengths (AI pattern)")
        elif variance < 50: score += 8
    passive_count = len(re.findall(r'\b(is|are|was|were|be|been|being)\s+\w+ed\b', text, re.IGNORECASE))
    if passive_count > 3: score += min(passive_count * 3, 15); flags.append(f"⚠️ Heavy passive voice ({passive_count} instances)")
    word_count = len(text.split())
    contraction_count = len(re.findall(r"\b\w+'\w+\b", text))
    if word_count > 50 and contraction_count < word_count * 0.02:
        score += 12; flags.append("⚠️ Very few contractions")
    hedge_count = len(re.findall(r'\b(maybe|perhaps|might|could|probably|roughly|I think|I believe)\b', text, re.IGNORECASE))
    if word_count > 100 and hedge_count == 0:
        score += 8; flags.append("⚠️ No natural hedging")
    score = min(score, 100)
    if score >= 75: label = "🔴 Very High AI Risk"
    elif score >= 50: label = "🟠 High AI Risk"
    elif score >= 30: label = "🟡 Moderate Risk"
    elif score >= 15: label = "🟢 Low Risk"
    else: label = "✅ Very Low Risk — reads as human"
    return {"score": score, "label": label, "flags": flags[:8], "word_count": word_count, "passive_instances": passive_count, "contraction_count": contraction_count}

def humanise_text(text: str, tone: str = "Casual / Friendly", preserve_structure: bool = True,
                  strength: str = "Standard", extra_instructions: str = "", target_audience: str = "") -> str:
    from utils.ai_engine import generate
    tone_hint = ADVANCED_TONES.get(tone, "Natural and human-sounding.")
    struct_hint = ("Preserve all headings, bullet points, and paragraph structure — only rewrite prose." if preserve_structure
                   else "Completely reformat for best flow — merge, split, restructure freely.")
    strength_hints = {
        "Light Touch": "Minimal changes — remove obvious AI phrases, keep 80% of phrasing.",
        "Standard": "Full humanisation — transform style completely while preserving meaning.",
        "Maximum": "Deep transformation — rewrite every sentence. Maximum personality. Unmistakably human.",
        "Academic Safe": "Humanise while keeping academic register — eliminate robotic patterns, inject scholarly personality.",
    }
    prompt = f"""Humanise strength: {strength}\n{strength_hints.get(strength, '')}\n\nTone: {tone}\n{tone_hint}\n\n{struct_hint}\n{f"Extra: {extra_instructions}" if extra_instructions else ""}{f"\nAudience: {target_audience}" if target_audience else ""}\n\nTEXT TO HUMANISE:\n---\n{text}\n---\n\nOutput ONLY the rewritten text. No preamble."""
    try:
        result = generate(prompt=prompt, system_prompt=HUMANISE_SYSTEM, provider="auto", temperature=0.8)
        if result:
            stripped = result.strip()
            for prefix in ["Here is", "Here's", "Below is", "The humanised", "Rewritten:", "Output:"]:
                if stripped.lower().startswith(prefix.lower()):
                    lines = stripped.split("\n", 1)
                    stripped = lines[1].strip() if len(lines) > 1 else stripped
                    break
            return stripped
        return text
    except Exception as e:
        return f"Humanisation error: {e}"

def compare_versions(original: str, humanised: str) -> Dict:
    orig_score = ai_detection_score(original)
    human_score = ai_detection_score(humanised)
    orig_words = original.split(); human_words = humanised.split()
    orig_ttr = len(set(w.lower() for w in orig_words)) / max(1, len(orig_words))
    human_ttr = len(set(w.lower() for w in human_words)) / max(1, len(human_words))
    return {
        "original_score": orig_score["score"], "humanised_score": human_score["score"],
        "score_reduction": orig_score["score"] - human_score["score"],
        "original_words": len(orig_words), "humanised_words": len(human_words),
        "original_vocab_richness": round(orig_ttr * 100, 1),
        "humanised_vocab_richness": round(human_ttr * 100, 1),
        "original_label": orig_score["label"], "humanised_label": human_score["label"],
    }

# Legacy export
TONE_HINTS = ADVANCED_TONES
