"""
dictionary_engine.py — Advanced Multi-Language AI Dictionary v2.0
Full linguistic analysis: definitions, etymology, synonyms, antonyms,
usage examples, word family, collocations, and exam usage tips.
Live data: Free Dictionary API (dictionaryapi.dev) + Datamuse word-finder + MyMemory translation.
All free, no API key needed.
"""
from typing import Dict, List
from utils.ai_engine import quick_generate, generate
from free_apis import (
    get_dictionary as _live_dict, get_random_quote, get_trivia,
    get_synonyms, get_antonyms, get_rhymes, get_word_associations,
    datamuse_words, translate_text,
)


class AIDictionary:
    """Handles end-to-end linguistic lookup and analysis."""

    @staticmethod
    def lookup(word: str, target_lang: str = "English") -> str:
        """Full structured dictionary lookup — live data + AI enrichment."""
        # ── Try Free Dictionary API first (instant, no key) ──────────────────
        if target_lang.lower() in ("english", "en", ""):
            live = _live_dict(word)
            if live and live.get("meanings"):
                return _format_live_entry(live)
        # ── AI fallback for other languages or when API unavailable ──────────
        try:
            prompt = f"Word: '{word}' (Target Language: {target_lang})"
            return quick_generate(prompt=prompt, engine_name="dictionary") or _fallback_lookup(word, target_lang)
        except Exception:
            return _fallback_lookup(word, target_lang)

    @staticmethod
    def get_etymology(word: str) -> str:
        """Historical and linguistic origin of a word."""
        prompt = f"""Give a fascinating, detailed etymology for the word: '{word}'.
Include:
- Language of origin and approximate date of first use
- How the meaning has evolved over centuries
- Any interesting historical stories or connections
- Related words from the same root in other languages
Keep it engaging and educational. Max 150 words."""
        return quick_generate(prompt=prompt, engine_name="researcher") or "Etymology unavailable."

    @staticmethod
    def get_idioms(word: str) -> str:
        """Idioms, metaphors, and cultural phrases."""
        prompt = f"""Provide 5 important idioms or cultural phrases that use the word: '{word}'.

For each:
- **Idiom**: [the phrase]
- **Meaning**: [what it means]
- **Example**: [sentence using it]
- **Region/Culture**: [where it's common]"""
        return quick_generate(prompt=prompt, engine_name="researcher") or "Idioms unavailable."

    @staticmethod
    def get_synonyms_antonyms(word: str) -> Dict:
        """Get rich synonym/antonym data — Datamuse live data + AI nuance notes."""
        # ── Live Datamuse data (free, no key, instant) ─────────────────
        live_syn  = get_synonyms(word, limit=12)
        live_ant  = get_antonyms(word, limit=8)
        live_rhy  = get_rhymes(word, limit=8)
        live_assoc = get_word_associations(word, limit=8)

        live_block = ""
        if live_syn:  live_block += f"\nLive Synonyms: {', '.join(live_syn)}"
        if live_ant:  live_block += f"\nLive Antonyms: {', '.join(live_ant)}"
        if live_rhy:  live_block += f"\nRhymes: {', '.join(live_rhy)}"
        if live_assoc: live_block += f"\nWord Associations: {', '.join(live_assoc)}"

        prompt = f"""For the word '{word}', provide:{live_block}

Now add:
SYNONYMS (8-10): List with brief nuance note for each
ANTONYMS (5-6): List with brief note
NEAR-SYNONYMS: Words that are close but with important differences
REGISTER NOTE: When to use formal vs informal alternatives

Return as plain text with clear sections."""
        result = quick_generate(prompt=prompt, engine_name="dictionary") or ""
        return {"raw": result, "synonyms": live_syn, "antonyms": live_ant,
                "rhymes": live_rhy, "associations": live_assoc}

    @staticmethod
    def get_word_in_context(word: str, subject: str = "general") -> str:
        """Show the word used correctly in multiple academic/professional contexts."""
        prompt = f"""Show '{word}' used correctly in 5 different contexts:
1. Academic essay/paper sentence
2. Business/professional email sentence
3. Creative writing sentence
4. Spoken/conversational sentence
5. {subject.title() if subject != "general" else "Scientific"} context sentence

Then: 3 COMMON MISUSES to avoid (how NOT to use it incorrectly)."""
        return quick_generate(prompt=prompt, engine_name="dictionary") or "Context examples unavailable."

    @staticmethod
    def get_word_family(word: str) -> str:
        """Get the complete word family (noun, verb, adj, adv forms)."""
        prompt = f"""Find the complete word family for '{word}':
- NOUN forms: (e.g., act → action, activity, actor)
- VERB forms: (all tenses/gerunds)
- ADJECTIVE forms: (e.g., active, activated)
- ADVERB forms: (e.g., actively)
- COMPOUND WORDS using this root
- PREFIX/SUFFIX patterns

Show one example sentence for each form."""
        return quick_generate(prompt=prompt, engine_name="dictionary") or "Word family unavailable."

    @staticmethod
    def get_collocations(word: str) -> str:
        """Get common words that naturally go with this word."""
        prompt = f"""List the most important COLLOCATIONS for '{word}':
- Verb + {word}: (e.g., make a decision)
- {word} + Noun: (e.g., decision maker)
- Adjective + {word}: (e.g., difficult decision)
- Preposition + {word}: (e.g., in decision)
- Common phrases: (frequent multi-word expressions)

Give 3-4 examples per category with short sentences."""
        return quick_generate(prompt=prompt, engine_name="dictionary") or "Collocations unavailable."

    @staticmethod
    def get_pronunciation_guide(word: str) -> str:
        """Get IPA pronunciation and syllable breakdown."""
        prompt = f"""For the word '{word}', provide:
- IPA phonetic transcription (British and American English if different)
- Syllable breakdown with stress marked (e.g., de-CI-sion)
- Rhyming words (5)
- Common mispronunciation mistakes to avoid
- Memory tip for correct pronunciation"""
        return quick_generate(prompt=prompt, engine_name="dictionary") or "Pronunciation guide unavailable."

    @staticmethod
    def word_of_the_day() -> Dict:
        """Generate a structured 'Word of the Day'."""
        import datetime
        today = datetime.date.today().isoformat()
        prompt = f"""Generate an interesting, academic 'Word of the Day' for {today}.
Return JSON with:
- "word": the word
- "pronunciation": IPA + syllable breakdown
- "part_of_speech": noun/verb/adj/etc
- "definition": clear, complete definition
- "etymology": brief 1-sentence origin
- "example": excellent example sentence  
- "synonyms": 3 synonyms
- "difficulty": Easy/Medium/Advanced
- "exam_tip": how this word commonly appears in exams

Return ONLY valid JSON."""
        import json, re
        try:
            raw = generate(prompt=prompt, system="Return only valid JSON.", engine_name="dictionary")
            m = re.search(r'\{.*\}', raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        except Exception:
            pass
        return {
            "word": "Perspicacious",
            "pronunciation": "per-spi-KAY-shus",
            "part_of_speech": "adjective",
            "definition": "Having a ready insight into things; shrewd; showing great intelligence or understanding.",
            "etymology": "From Latin perspicax, from perspicere 'see through'.",
            "example": "The perspicacious student quickly identified the flaws in the experimental design.",
            "synonyms": ["astute", "discerning", "shrewd"],
            "difficulty": "Advanced",
            "exam_tip": "Common in GRE Verbal and competitive exam vocabulary sections.",
        }


def _fallback_lookup(word: str, lang: str = "English") -> str:
    """Fallback comprehensive lookup via direct generate call."""
    prompt = f"""Provide a complete dictionary entry for the word: '{word}' in {lang}.

Include:
## Definition(s)
All major meanings, numbered, with part of speech for each.

## Pronunciation
IPA + syllable breakdown

## Examples (5)
Excellent example sentences showing different uses

## Synonyms & Antonyms
5 each with brief nuance notes

## Etymology
Origin story in 2-3 sentences

## Usage Notes
Register (formal/informal), common mistakes, collocations

## Exam Tip
How this word appears in competitive exams"""
    return generate(prompt=prompt, engine_name="dictionary") or f"Could not look up '{word}'"


def _format_live_entry(entry: dict) -> str:
    """Format a Free Dictionary API entry into a rich markdown string."""
    word     = entry.get("word", "")
    phonetic = entry.get("phonetic", "")
    audio    = entry.get("audio_url", "")
    meanings = entry.get("meanings", [])

    lines = []
    lines.append(f"# 📖 {word.capitalize()}")
    if phonetic:
        lines.append(f"**Pronunciation**: `{phonetic}`")
    if audio:
        lines.append(f"🔊 [Listen]({audio})")
    lines.append("")

    for m in meanings:
        pos  = m.get("partOfSpeech", "")
        defs = m.get("definitions", [])
        syns = m.get("synonyms", [])
        ants = m.get("antonyms", [])

        if pos:
            lines.append(f"## *{pos}*")
        for i, d in enumerate(defs[:4], 1):
            defn    = d.get("definition","")
            example = d.get("example","")
            d_syns  = d.get("synonyms", [])
            d_ants  = d.get("antonyms", [])
            lines.append(f"**{i}.** {defn}")
            if example:
                lines.append(f"   > *\"{example}\"*")
            if d_syns:
                lines.append(f"   🔗 Synonyms: {', '.join(d_syns[:5])}")
            if d_ants:
                lines.append(f"   ↔️ Antonyms: {', '.join(d_ants[:4])}")
            lines.append("")

        if syns:
            lines.append(f"**Synonyms**: {', '.join(syns[:8])}")
        if ants:
            lines.append(f"**Antonyms**: {', '.join(ants[:6])}")
        lines.append("---")

    lines.append("> *Source: Free Dictionary API (dictionaryapi.dev)*")
    return "\n".join(lines)
