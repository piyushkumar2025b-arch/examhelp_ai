"""
dictionary_engine.py — Advanced Multi-Language AI Dictionary
============================================================
Linguistic analysis + Historical Context + Usage Examples.
"""

from typing import Dict, List, Optional
from utils.ai_engine import quick_generate

class AIDictionary:
    """Handles end-to-end linguistic lookup and analysis."""

    @staticmethod
    def lookup(word: str, target_lang: str = "English") -> str:
        """Main entry point for dictionary lookup."""
        try:
            # engine_name="dictionary" in prompts.py gives us the Advanced Linguist persona.
            prompt = f"Word: '{word}' (Target Language: {target_lang})"
            result = quick_generate(prompt=prompt, engine_name="dictionary")
            return result
        except Exception as e:
            return f"❌ Lookup error: {str(e)}"

    @staticmethod
    def get_etymology(word: str) -> str:
        """Fetch historical and linguistic origin of a word."""
        prompt = f"Provide a fascinating, brief historical and linguistic etymology for the word: '{word}'."
        return quick_generate(prompt=prompt, engine_name="researcher")

    @staticmethod
    def get_idioms(word: str) -> str:
        """Fetch metaphors, idioms, and cultural phrases."""
        prompt = f"Provide 5 major idioms or cultural metaphors using the word: '{word}'."
        return quick_generate(prompt=prompt, engine_name="researcher")
