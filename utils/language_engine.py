"""
language_engine.py — AI Language Translator + Language Learning
Multi-language translation, grammar check, language learning, pronunciation guides.
"""
from __future__ import annotations
from utils.debugger_engine import _call_gemini_debug

LANGUAGES = [
    "English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali",
    "Marathi", "Gujarati", "Punjabi", "Urdu", "French", "Spanish", "German",
    "Italian", "Portuguese", "Japanese", "Chinese (Mandarin)", "Korean",
    "Arabic", "Russian", "Dutch", "Swedish", "Turkish", "Vietnamese",
    "Thai", "Indonesian", "Malay", "Swahili", "Greek", "Hebrew", "Polish",
]

TRANSLATION_MODES = {
    "Literal":          "Translate word-for-word preserving exact structure",
    "Natural":          "Translate naturally as a native speaker would say it",
    "Formal/Academic":  "Translate in formal, academic, or official register",
    "Casual/Spoken":    "Translate in everyday conversational style",
    "Literary":         "Translate preserving literary style, rhythm, and tone",
    "Technical":        "Translate technical/scientific content with precision",
}

TRANS_SYSTEM = """\
You are a MASTER Linguist and Certified Translator fluent in 30+ languages.
Your translations are culturally accurate, contextually appropriate, and beautifully expressed.
You explain nuances, idiomatic differences, and cultural context.
"""

GRAMMAR_SYSTEM = """\
You are a strict but helpful grammar teacher and language coach.
Identify ALL errors, explain each one clearly, and provide the corrected version.
Also suggest improvements for style and clarity.
"""

def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    mode: str = "Natural",
    explain: bool = True,
) -> str:
    mode_desc = TRANSLATION_MODES.get(mode, TRANSLATION_MODES["Natural"])
    prompt = f"""Translate the following from {source_lang} to {target_lang}.
Translation mode: {mode} — {mode_desc}

SOURCE TEXT:
{text}

Provide:
1. **Translation** — The {mode.lower()} {target_lang} translation
"""
    if explain:
        prompt += """2. **Pronunciation Guide** — For each sentence (if non-Latin script)
3. **Cultural Notes** — Any idioms, cultural context, or important nuances
4. **Alternative Translations** — 1-2 alternative ways to express key phrases"""
    return _call_gemini_debug(prompt, TRANS_SYSTEM)


def grammar_check(text: str, language: str) -> str:
    prompt = f"""Perform a comprehensive grammar and style check on this {language} text:

TEXT: {text}

Provide:
1. **Error List** — Every grammar, spelling, punctuation error with explanation
2. **Corrected Version** — Full corrected text with changes highlighted using **bold**
3. **Style Improvements** — Suggestions for better phrasing, word choice, flow
4. **Grammar Score** — /100 with breakdown
5. **Most Common Mistake Pattern** — What recurring error to watch out for"""
    return _call_gemini_debug(prompt, GRAMMAR_SYSTEM)


def teach_language_basics(language: str, topic: str, native_lang: str = "English") -> str:
    prompt = f"""Teach {topic} in {language} for a {native_lang} speaker.

Include:
1. **Vocabulary** — 15 essential words/phrases with pronunciation
2. **Grammar Rule** — The core grammatical concept
3. **Example Sentences** — 5 examples from simple to complex
4. **Common Mistakes** — What {native_lang} speakers get wrong
5. **Memory Tricks** — Mnemonics and tips to remember
6. **Practice Exercise** — 3 fill-in-the-blank exercises with answers
7. **Cultural Tip** — Relevant cultural context"""
    return _call_gemini_debug(prompt, TRANS_SYSTEM)


def explain_idioms(text: str, language: str) -> str:
    prompt = f"""Identify and explain all idioms, proverbs, slang, and expressions in this {language} text:

TEXT: {text}

For each expression found:
- The expression itself
- Literal translation (if applicable)
- Actual meaning
- Example usage in context
- English equivalent (if exists)
- Register (formal/informal/slang)"""
    return _call_gemini_debug(prompt, TRANS_SYSTEM)


def generate_language_quiz(language: str, topic: str, level: str = "Beginner") -> str:
    prompt = f"""Create a {level}-level language quiz for {language} on the topic: {topic}

Include:
1. 5 vocabulary multiple choice questions
2. 3 fill-in-the-blank grammar questions  
3. 2 translation questions (to and from {language})
4. 1 reading comprehension (short paragraph + 2 questions)

Format each question clearly. Include answers at the end with explanations."""
    return _call_gemini_debug(prompt, TRANS_SYSTEM)


def analyze_morphology_syntax(text: str, language: str) -> str:
    """Provides a full linguistic breakdown: morphology, syntax tree, glossing."""
    prompt = f"""Provide a professional, university-level linguistic morphology and syntax breakdown for the following {language} text.

TEXT: {text}

Include:
1. **Clause Structure (Syntax Tree Breakdown):** Analyze how the clauses are constructed.
2. **Morphological Parsing (Interlinear Glossing):** Provide standard linguistic glossing (root, affixes, tense, case, gender, etc.) for each word.
3. **Lexical Analysis:** Highlight the origins (etymology) or interesting phonetic processes occurring.
4. **Pragmatics/Register:** Note the perceived level of formality, politeness markers, or cultural inferences embedded in the grammar.
"""
    return _call_gemini_debug(prompt, TRANS_SYSTEM)
