"""
humaniser_engine.py — AI Text Humaniser v3.0 ULTRA
Strongest AI-detection bypass with:
- Multi-pass humanisation strategy
- Sentence-level variance analysis
- Pre/post detection scoring with gauge
- Side-by-side diff view (word counts)
- 10 tone presets + custom instructions
"""
from __future__ import annotations
import re
from typing import Dict, List, Tuple

HUMANISE_SYSTEM = """\
You are the world's most skilled ghostwriter and text humaniser. Transform AI-generated text into writing that is completely indistinguishable from authentic human writing — designed to pass GPTZero, Turnitin, Winston AI, ZeroGPT, and all AI detectors at the highest accuracy level.

TRANSFORMATION RULES (apply all, no exceptions):
1. REMOVE every AI filler phrase: "Certainly!", "Great question!", "Of course!", "Absolutely!", "It's worth noting", "It is important to note", "In conclusion", "To summarize", "Furthermore", "Moreover", "Additionally", "In essence", "Notably", "Undoubtedly", "Needless to say", "As mentioned", "Having said that"
2. VARY sentence structure aggressively — mix 6-word punchy sentences with flowing 25-word sentences
3. USE contractions naturally throughout: I'm, don't, it's, you'll, can't, won't, that's, we're, they've
4. ADD personality markers: "Look,", "The thing is,", "Honestly,", "Here's the deal —", "What's interesting is"
5. CONVERT passive voice to active — be ruthless about this
6. INJECT natural hedging: "roughly", "about", "I'd say", "probably", "seems like"
7. VARY vocabulary — never use the same word twice in consecutive paragraphs
8. ADD rhetorical questions where they flow naturally
9. CREATE paragraph length variety — 1-sentence, 3-sentence, and longer paragraphs in sequence
10. REMOVE robotic enumeration (Firstly, Secondly, Thirdly → natural flow)
11. PRESERVE all technical accuracy — only tone/style changes
12. Output ONLY the rewritten text — zero preamble, no "Here is the humanised version:"
13. MATCH the requested tone perfectly
14. MAKE it feel like a real person wrote it at their keyboard, not an AI
"""

ADVANCED_TONES = {
    "Casual / Friendly":   "Warm, conversational — like explaining to a smart friend over coffee. Use contractions freely.",
    "Academic / Scholarly":"Scholarly but authentic — passionate researcher's voice, not robotic. Intellectual but human.",
    "Professional / Business":"Confident, direct, polished — sharp memo from a senior exec. No-nonsense, action-oriented.",
    "Creative / Narrative":"Vivid storytelling with personality — reads like a magazine feature or blog post.",
    "Gen Z / Youth":       "Contemporary and punchy. Natural Gen Z phrasing, energy, occasional slang.",
    "Technical / Expert":  "Precise and human — an engineer who values clarity. Rich in examples, concrete.",
    "Journalistic":        "Punchy lede, direct, factual but engaging. Inverted pyramid. Quotes where natural.",
    "Social Media":        "Hook-first, scannable, punchy. Emoji-friendly. Designed for shares.",
    "Teacher / Educator":  "Patient, clear, encouraging — builds understanding step-by-step. Uses analogies.",
    "Sales / Marketing":   "Benefit-focused, persuasive. Creates desire through specifics. Action-oriented CTAs.",
}

STRENGTH_HINTS = {
    "Light Touch":    "Minimal changes — remove obvious AI phrases, keep 80% of original phrasing intact.",
    "Standard":       "Full humanisation — completely transform style while preserving all meaning.",
    "Maximum":        "Deep transformation — rewrite every sentence. Maximum personality. Unmistakably human.",
    "Academic Safe":  "Humanise while keeping academic register — scholarly personality, no robotic patterns.",
}

# AI pattern detector
AI_PATTERNS = [
    (r'\bCertainly[!,]?\b',            'FILLER',     8),
    (r'\bGreat question[!,]?\b',       'FILLER',     8),
    (r'\bOf course[!,]?\b',            'FILLER',     7),
    (r'\bAbsolutely[!,]?\b',           'FILLER',     7),
    (r"\bIt'?s worth noting\b",        'FILLER',     7),
    (r'\bIt is important to note\b',   'FILLER',     7),
    (r'\bIn conclusion\b',             'FILLER',     6),
    (r'\bTo summarize\b',              'FILLER',     5),
    (r'\bFurthermore\b',               'TRANSITION', 4),
    (r'\bMoreover\b',                  'TRANSITION', 4),
    (r'\bAdditionally\b',              'TRANSITION', 3),
    (r'\bIn essence\b',                'FILLER',     5),
    (r'\bNotably\b',                   'FILLER',     4),
    (r'\bUndoubtedly\b',               'FILLER',     5),
    (r'\bNeedless to say\b',           'FILLER',     5),
    (r'\bHaving said that\b',          'FILLER',     4),
    (r'\bFirstly\b',                   'ENUM',       6),
    (r'\bSecondly\b',                  'ENUM',       6),
    (r'\bThirdly\b',                   'ENUM',       6),
    (r'\bDelve into\b',                'AI_WORD',    6),
    (r'\bComprehensive\b',             'AI_WORD',    4),
    (r'\bFacilitate\b',                'AI_WORD',    4),
    (r'\bLeverage\b',                  'AI_WORD',    4),
    (r'\bRobust\b',                    'AI_WORD',    4),
    (r'\bUtilize\b',                   'AI_WORD',    3),
    (r'\bSeamlessly\b',                'AI_WORD',    4),
    (r'\bMultifaceted\b',              'AI_WORD',    5),
    (r'\bWith that being said\b',      'FILLER',     5),
    (r'\bAs an AI\b',                  'AI_WORD',    20),
    (r'\bI cannot\b',                  'AI_WORD',    3),
]


def ai_detection_score(text: str) -> Dict:
    """Estimate AI detection risk with detailed flags."""
    score  = 0
    flags  = []

    for pattern, category, weight in AI_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            flag_label = {
                'FILLER':     f"🚨 AI filler: '{matches[0]}'",
                'AI_WORD':    f"⚠️ AI buzzword: '{matches[0]}'",
                'ENUM':       f"⚠️ Robotic enum: '{matches[0]}'",
                'TRANSITION': f"⚠️ Overused transition: '{matches[0]}'",
            }.get(category, f"⚠️ '{matches[0]}'")
            flags.append(flag_label)
            score += weight * min(len(matches), 3)

    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 10]
    if len(sentences) > 3:
        lengths  = [len(s.split()) for s in sentences]
        avg      = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if variance < 15:
            score += 18; flags.append("⚠️ Very uniform sentence lengths (strong AI signal)")
        elif variance < 40:
            score += 8;  flags.append("⚠️ Low sentence variety")

    passive_count = len(re.findall(r'\b(is|are|was|were|be|been|being)\s+\w+ed\b', text, re.IGNORECASE))
    if passive_count > 3:
        score += min(passive_count * 3, 18)
        flags.append(f"⚠️ Heavy passive voice ({passive_count} instances)")

    words = text.split()
    word_count = len(words)
    contraction_count = len(re.findall(r"\b\w+'\w+\b", text))
    if word_count > 60 and contraction_count < word_count * 0.018:
        score += 13; flags.append("⚠️ Very few contractions — reads robotic")

    hedge_count = len(re.findall(
        r'\b(maybe|perhaps|might|could|probably|roughly|approximately|I think|I believe|I feel|seems like|sort of|kind of)\b',
        text, re.IGNORECASE
    ))
    if word_count > 100 and hedge_count == 0:
        score += 10; flags.append("⚠️ Zero natural hedging — over-confident AI writing")

    # Paragraph count and lengths
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
    if len(paragraphs) > 2:
        p_lengths = [len(p.split()) for p in paragraphs]
        p_var = sum((l - sum(p_lengths)/len(p_lengths))**2 for l in p_lengths) / len(p_lengths)
        if p_var < 100:
            score += 8; flags.append("⚠️ Uniform paragraph lengths")

    score = min(score, 100)
    if score >= 75:   label = "🔴 Very High AI Risk — likely to be flagged"
    elif score >= 50: label = "🟠 High AI Risk — will be detected"
    elif score >= 30: label = "🟡 Moderate Risk — borderline"
    elif score >= 15: label = "🟢 Low Risk — mostly human-sounding"
    else:             label = "✅ Very Low Risk — reads as authentic human"

    return {
        "score":              score,
        "label":              label,
        "flags":              flags[:10],
        "word_count":         word_count,
        "passive_instances":  passive_count,
        "contraction_count":  contraction_count,
        "sentence_count":     len(sentences),
        "hedge_count":        hedge_count,
    }


def humanise_text(
    text: str,
    tone: str = "Casual / Friendly",
    preserve_structure: bool = True,
    strength: str = "Standard",
    extra_instructions: str = "",
    target_audience: str = "",
    preserve_keywords: str = "",
) -> str:
    from utils.ai_engine import generate
    tone_hint    = ADVANCED_TONES.get(tone, "Natural and human-sounding.")
    struct_hint  = (
        "Preserve all headings, bullet points, and paragraph structure — only rewrite prose."
        if preserve_structure else
        "Completely reformat for best flow — merge, split, restructure as needed."
    )
    kw_hint = f"PRESERVE THESE KEYWORDS exactly as-is: {preserve_keywords}" if preserve_keywords else ""
    prompt = f"""
TARGET TONE: {tone} — {tone_hint}
STRENGTH: {strength} — {STRENGTH_HINTS.get(strength, '')}
STRUCTURE: {struct_hint}
{f"EXTRA INSTRUCTIONS: {extra_instructions}" if extra_instructions else ""}
{f"AUDIENCE: {target_audience}" if target_audience else ""}
{kw_hint}

TEXT TO HUMANISE:
---
{text}
---
"""
    try:
        result = generate(prompt=prompt, system=HUMANISE_SYSTEM, engine_name="humaniser")
        return result.strip() if result else text
    except Exception as e:
        return f"Humanisation error: {e}"


def compare_versions(original: str, humanised: str) -> Dict:
    """Compare original vs humanised text with detailed metrics."""
    orig_s    = ai_detection_score(original)
    human_s   = ai_detection_score(humanised)
    orig_w    = original.split()
    human_w   = humanised.split()
    orig_ttr  = len(set(w.lower() for w in orig_w))  / max(1, len(orig_w))
    human_ttr = len(set(w.lower() for w in human_w)) / max(1, len(human_w))
    reduction = orig_s["score"] - human_s["score"]
    return {
        "original_score":        orig_s["score"],
        "humanised_score":       human_s["score"],
        "score_reduction":       reduction,
        "improvement_pct":       round((reduction / max(1, orig_s["score"])) * 100, 1),
        "original_words":        len(orig_w),
        "humanised_words":       len(human_w),
        "original_vocab_richness":   round(orig_ttr  * 100, 1),
        "humanised_vocab_richness":  round(human_ttr * 100, 1),
        "original_label":        orig_s["label"],
        "humanised_label":       human_s["label"],
        "original_flags":        orig_s["flags"],
        "humanised_flags":       human_s["flags"],
    }


def detect_only(text: str) -> Dict:
    """Run only the detection score — no humanisation."""
    return ai_detection_score(text)


def get_risk_color(score: int) -> str:
    """Return a color hex for the risk score."""
    if score >= 75: return "#ef4444"
    if score >= 50: return "#f97316"
    if score >= 30: return "#fbbf24"
    if score >= 15: return "#4ade80"
    return "#34d399"


# Legacy export
TONE_HINTS = ADVANCED_TONES
