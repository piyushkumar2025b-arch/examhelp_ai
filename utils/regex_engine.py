"""
utils/regex_engine.py — Advanced AI-Powered Regex Builder & Live Tester
Helps students build, explain, and validate regular expressions.
"""
from __future__ import annotations
import re, html
from typing import Dict, List, Optional, Tuple
from utils.ai_engine import generate as ai_generate

def generate_regex(description: str, examples: List[str] = None) -> Dict:
    """
    Generate a regex pattern + explanation based on description.
    """
    example_str = f"\nExamples of what to match: {', '.join(examples)}" if examples else ""
    prompt = [
        {"role": "system", "content": (
            f"You are a master of regular expressions. Create a regex pattern that matches exactly what is described. "
            f"Return ONLY strictly valid JSON. No preamble. "
            f'Format: {{"pattern": "...", "explanation": "Step-by-step breakdown...", "flags": "g/i/m"}}. '
            f"Make sure the pattern works across multiple programming languages where possible."
        )},
        {"role": "user", "content": f"Description: {description}{example_str}"}
    ]
    try:
        from json import loads
        res = ai_generate(messages=prompt, json_mode=True).strip()
        return loads(res)
    except Exception as e:
        return {"pattern": "", "explanation": f"Error: {e}", "flags": ""}

def test_regex(pattern: str, test_text: str, flags: str = "") -> Dict:
    """
    Test a regex against text and return matches with HTML highlighting.
    """
    try:
        # Determine flags
        re_flags = 0
        if 'i' in flags.lower(): re_flags |= re.IGNORECASE
        if 'm' in flags.lower(): re_flags |= re.MULTILINE
        if 's' in flags.lower(): re_flags |= re.DOTALL

        regex = re.compile(pattern, re_flags)
        matches = list(regex.finditer(test_text))
        
        # Build highlighted HTML
        highlighted = ""
        last_idx = 0
        match_info = []

        for m in matches:
            # Text before match
            highlighted += html.escape(test_text[last_idx:m.start()])
            # The match itself
            m_text = test_text[m.start():m.end()]
            highlighted += f'<span style="background:rgba(124,106,247,0.3);border-bottom:2px solid var(--accent);color:var(--text);font-weight:600;">{html.escape(m_text)}</span>'
            last_idx = m.end()
            match_info.append({
                "match": m_text,
                "start": m.start(),
                "end": m.end(),
                "groups": m.groups()
            })
            
        highlighted += html.escape(test_text[last_idx:])
        
        return {
            "success": True,
            "match_count": len(matches),
            "highlighted_html": highlighted,
            "matches": match_info
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
