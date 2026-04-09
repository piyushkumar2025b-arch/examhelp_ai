"""
utils/regex_engine.py — Advanced AI-Powered Regex Builder & Live Tester v2.0
FIX-10.6: Adds explain_regex(), example-based generator, and substitution tester.
"""
from __future__ import annotations
import re, html
from typing import Dict, List, Optional, Tuple
from utils.ai_engine import generate as ai_generate


def generate_regex(description: str, examples: List[str] = None) -> Dict:
    """
    Generate a regex pattern + explanation based on natural language description.
    Returns {'pattern': str, 'explanation': str, 'flags': str}.
    """
    import json as _json
    example_str = f"\nExamples of what to match: {', '.join(examples)}" if examples else ""
    system = (
        "You are a master of regular expressions. Create a regex pattern that matches exactly what is described. "
        "Return ONLY strictly valid JSON. No preamble. "
        'Format: {"pattern": "...", "explanation": "Step-by-step breakdown of each token...", "flags": "g/i/m"}. '
        "Make sure the pattern works across Python, JavaScript, and Java where possible."
    )
    try:
        res = ai_generate(
            prompt=f"Description: {description}{example_str}",
            system=system,
            temperature=0.1,
            max_tokens=512,
        ).strip()
        # Strip markdown fences if present
        if res.startswith("```"):
            res = re.sub(r"```(?:json)?\s*|\s*```", "", res).strip()
        return _json.loads(res)
    except Exception as e:
        return {"pattern": "", "explanation": f"Error: {e}", "flags": ""}


def generate_regex_from_examples(
    match_examples: List[str],
    no_match_examples: List[str] = None,
) -> Dict:
    """
    FIX-10.6 ADD: Few-shot regex generation from examples.
    Finds the minimal pattern that matches all positives and rejects all negatives.
    """
    import json as _json
    positive = "\n".join(f"  MATCH: {e}" for e in match_examples)
    negative = "\n".join(f"  NO MATCH: {e}" for e in (no_match_examples or []))
    system = (
        "You are a regex expert. Find the minimal, most general regex pattern that: "
        "1. Matches ALL provided MATCH examples. "
        "2. Does NOT match any NO MATCH examples. "
        "Return ONLY valid JSON: "
        '{"pattern": "...", "explanation": "Why this pattern works for each example...", "flags": "i"}'
    )
    prompt = f"Examples:\n{positive}\n{negative}"
    try:
        res = ai_generate(prompt=prompt, system=system, temperature=0.1, max_tokens=512).strip()
        if res.startswith("```"):
            res = re.sub(r"```(?:json)?\s*|\s*```", "", res).strip()
        return _json.loads(res)
    except Exception as e:
        return {"pattern": "", "explanation": f"Error: {e}", "flags": ""}


def explain_regex(pattern: str) -> str:
    """
    FIX-10.6 ADD: Explain a regex pattern token-by-token in plain English.
    Returns a detailed Markdown breakdown.
    """
    system = (
        "You are a regex teacher. The user provides a regex pattern. "
        "Break it down EXACTLY, token-by-token, explaining what EACH character/group/quantifier does. "
        "Format as a numbered list. Then add: Common Use Cases and Potential Pitfalls."
    )
    try:
        return ai_generate(
            prompt=f"Explain this regex pattern token by token: `{pattern}`",
            system=system,
            temperature=0.1,
            max_tokens=1024,
        )
    except Exception as e:
        return f"Error explaining pattern: {e}"


def test_regex(pattern: str, test_text: str, flags: str = "") -> Dict:
    """
    Test a regex against text and return matches with HTML highlighting.
    FIX-10.6: Improved highlighting with match index tooltips.
    """
    try:
        re_flags = 0
        if 'i' in flags.lower(): re_flags |= re.IGNORECASE
        if 'm' in flags.lower(): re_flags |= re.MULTILINE
        if 's' in flags.lower(): re_flags |= re.DOTALL

        regex = re.compile(pattern, re_flags)
        matches = list(regex.finditer(test_text))

        highlighted = ""
        last_idx = 0
        match_info = []

        for idx, m in enumerate(matches):
            highlighted += html.escape(test_text[last_idx:m.start()])
            m_text = test_text[m.start():m.end()]
            highlighted += (
                f'<span style="background:rgba(124,106,247,0.35);border-bottom:2px solid #7c6af7;'
                f'color:#f0f0ff;font-weight:600;border-radius:3px;padding:0 2px;" '
                f'title="Match #{idx+1} [{m.start()}:{m.end()}]">{html.escape(m_text)}</span>'
            )
            last_idx = m.end()
            match_info.append({
                "match": m_text,
                "start": m.start(),
                "end": m.end(),
                "groups": m.groups(),
                "index": idx + 1,
            })

        highlighted += html.escape(test_text[last_idx:])

        return {
            "success": True,
            "match_count": len(matches),
            "highlighted_html": highlighted,
            "matches": match_info,
        }
    except re.error as e:
        return {"success": False, "error": f"Invalid regex: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def replace_with_regex(pattern: str, replacement: str, test_text: str, flags: str = "") -> Dict:
    """
    FIX-10.6 ADD: Test regex substitution — shows original → replaced side by side.
    Returns {'original': str, 'replaced': str, 'count': int}.
    """
    try:
        re_flags = 0
        if 'i' in flags.lower(): re_flags |= re.IGNORECASE
        if 'm' in flags.lower(): re_flags |= re.MULTILINE
        replaced, count = re.subn(pattern, replacement, test_text, flags=re_flags)
        return {"success": True, "original": test_text, "replaced": replaced, "count": count}
    except re.error as e:
        return {"success": False, "error": f"Invalid regex: {e}", "original": test_text, "replaced": "", "count": 0}
    except Exception as e:
        return {"success": False, "error": str(e), "original": test_text, "replaced": "", "count": 0}

