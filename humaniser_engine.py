"""
humaniser_engine.py — AI Text Humaniser
Converts AI-generated / robotic text into natural, human-sounding writing.
Uses Groq LLaMA via the existing key_manager pipeline.
"""
from __future__ import annotations
from typing import Optional

HUMANISE_SYSTEM = """\
You are an elite text humaniser and editor. Your sole job is to rewrite text so it reads as authentically human — warm, natural, conversational, and free of AI-isms. Never summarise or shorten: rewrite the FULL content with the same information, just humanised.

Rules:
1. Remove all AI filler: "Certainly!", "Great question!", "Of course!", "Absolutely!", "It's worth noting that", "It is important to note", "In conclusion", "To summarise"
2. Vary sentence length: mix short punchy sentences with longer flowing ones
3. Use contractions naturally: "I'm", "don't", "it's", "you'll", "can't"
4. Use casual connectors: "So,", "But honestly,", "The thing is,", "And yeah,", "Look,"
5. Add personality: mild hedges ("I think", "honestly", "pretty much"), occasional rhetorical questions
6. Kill passive voice — make it active and direct
7. Remove robotic enumeration unless it's truly needed (no "Firstly... Secondly... Thirdly...")
8. Keep technical accuracy 100% intact — only the tone changes
9. Match the user's requested tone (formal/casual/academic/professional)
10. Output ONLY the rewritten text — no preamble, no commentary, no "Here is the humanised version:"
"""

TONE_HINTS = {
    "Casual / Friendly":     "Conversational, warm, approachable — like texting a smart friend.",
    "Academic / Formal":     "Scholarly but natural — like a well-written research paper by a real human, not a robot.",
    "Professional / Business": "Polished, confident, direct — like a sharp email from a senior professional.",
    "Creative / Storytelling": "Narrative, vivid, engaging — like a magazine article or blog post.",
    "Gen Z / Youth":         "Chill, contemporary slang okay, short punchy lines, some lowercase for effect.",
}

def humanise_text(
    text: str,
    tone: str = "Casual / Friendly",
    preserve_structure: bool = True,
    extra_instructions: str = "",
) -> str:
    """
    Humanises the given text using Groq LLaMA.
    Returns the humanised text string.
    """
    from utils.groq_client import chat_with_groq

    tone_hint = TONE_HINTS.get(tone, "Natural and human-sounding.")
    struct_hint = (
        "Preserve all headings, bullet points, and paragraph structure — only rewrite the prose."
        if preserve_structure else
        "You may reformat freely for better flow."
    )

    prompt = f"""\
Tone: {tone}
Tone description: {tone_hint}
Structure rule: {struct_hint}
{f"Extra instructions: {extra_instructions}" if extra_instructions else ""}

Text to humanise:
---
{text}
---

Rewrite the text above following all rules. Output ONLY the rewritten text."""

    try:
        result, success = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=HUMANISE_SYSTEM,
            model="llama-4-scout-17b-16e-instruct",
        )
        if success and result:
            # Strip any accidental preamble the model might add
            stripped = result.strip()
            for prefix in ["Here is", "Here's", "Below is", "The humanised", "The rewritten", "Rewritten:"]:
                if stripped.lower().startswith(prefix.lower()):
                    # Remove first line
                    lines = stripped.split("\n", 1)
                    stripped = lines[1].strip() if len(lines) > 1 else stripped
                    break
            return stripped
        return "[Humaniser: AI response was empty. Please try again.]"
    except Exception as e:
        return f"[Humaniser error: {e}]"

def ai_detection_score(text: str) -> dict:
    """
    Heuristic AI-detection scoring (no API call needed).
    Returns a dict with score 0-100 and flags.
    """
    import re
    flags = []
    score = 0

    ai_phrases = [
        "certainly!", "great question", "of course!", "absolutely!", "it's worth noting",
        "it is worth noting", "it is important to note", "it's important to note",
        "in conclusion", "to summarise", "to summarize", "firstly,", "secondly,", "thirdly,",
        "furthermore,", "moreover,", "in addition,", "in summary,", "as mentioned",
        "it should be noted", "needless to say", "without a doubt", "as an ai",
        "i cannot", "i am unable to", "i must emphasize", "delve into", "unleash",
        "revolutionize", "game-changer", "leverage", "synergy", "holistic approach",
        "in today's world", "in today's fast-paced", "tapestry", "realm of", "the world of",
    ]
    lower = text.lower()
    for phrase in ai_phrases:
        if phrase in lower:
            flags.append(f'AI phrase: "{phrase}"')
            score += 8

    # Passive voice check
    passive = len(re.findall(r'\b(is|are|was|were|been|be)\b\s+\w+ed\b', text))
    if passive > 3:
        flags.append(f"High passive voice ({passive} instances)")
        score += min(passive * 3, 20)

    # Uniform sentence length (AI tends to write same-length sentences)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if sentences:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if variance < 20:
            flags.append("Very uniform sentence length (low variance)")
            score += 15

    # Lack of contractions
    contractions = re.findall(r"\b\w+n't\b|\b\w+'s\b|\b\w+'re\b|\b\w+'ll\b|\bI'm\b|\bI'd\b", text)
    words = len(text.split())
    if words > 100 and len(contractions) == 0:
        flags.append("No contractions found")
        score += 12

    score = min(score, 100)

    label = "✅ Likely Human" if score < 30 else ("⚠️ Mixed" if score < 60 else "🤖 Likely AI")
    return {"score": score, "label": label, "flags": flags[:6]}
