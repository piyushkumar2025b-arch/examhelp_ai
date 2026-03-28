"""
debugger_engine.py — ELITE Multi-Language Code Debugger Engine v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dedicated Gemini key pool for Code Debugger.
Uses GEMINI_DEBUG_KEY_1 … GEMINI_DEBUG_KEY_5 (separate from main pool).
Falls back to main gemini pool, then Groq.

Supports: Python, C, C++, Java, JavaScript, TypeScript, Go, Rust,
          HTML/CSS, SQL, Bash, PHP, Ruby, Kotlin, Swift, R, MATLAB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations
import os, time, json, re
import requests
from typing import Generator, Optional

# ── Load env ────────────────────────────────────────────────────────
def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
_load_env()

# ── Dedicated debug key pool ─────────────────────────────────────────
def _load_debug_keys() -> list[str]:
    keys = []
    try:
        import streamlit as st
        for i in range(1, 6):
            k = (st.secrets.get(f"GEMINI_DEBUG_KEY_{i}", "") or "").strip()
            if k and k not in keys:
                keys.append(k)
    except Exception:
        pass
    # Also check env vars
    for i in range(1, 6):
        k = os.environ.get(f"GEMINI_DEBUG_KEY_{i}", "").strip()
        if k and k not in keys:
            keys.append(k)
    return keys

# ── Language definitions ──────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "Python":       {"ext": "py",   "icon": "🐍", "runner": "python3",  "comment": "#"},
    "C":            {"ext": "c",    "icon": "⚙️", "runner": "gcc",      "comment": "//"},
    "C++":          {"ext": "cpp",  "icon": "⚡", "runner": "g++",      "comment": "//"},
    "Java":         {"ext": "java", "icon": "☕", "runner": "javac",    "comment": "//"},
    "JavaScript":   {"ext": "js",   "icon": "🟨", "runner": "node",     "comment": "//"},
    "TypeScript":   {"ext": "ts",   "icon": "🔷", "runner": "tsc",      "comment": "//"},
    "Go":           {"ext": "go",   "icon": "🐹", "runner": "go run",   "comment": "//"},
    "Rust":         {"ext": "rs",   "icon": "🦀", "runner": "rustc",    "comment": "//"},
    "HTML/CSS":     {"ext": "html", "icon": "🌐", "runner": "browser",  "comment": "<!--"},
    "SQL":          {"ext": "sql",  "icon": "🗄️", "runner": "sqlite3",  "comment": "--"},
    "Bash/Shell":   {"ext": "sh",   "icon": "🖥️", "runner": "bash",     "comment": "#"},
    "PHP":          {"ext": "php",  "icon": "🐘", "runner": "php",      "comment": "//"},
    "Ruby":         {"ext": "rb",   "icon": "💎", "runner": "ruby",     "comment": "#"},
    "Kotlin":       {"ext": "kt",   "icon": "🟣", "runner": "kotlinc",  "comment": "//"},
    "Swift":        {"ext": "swift","icon": "🍎", "runner": "swift",    "comment": "//"},
    "R":            {"ext": "r",    "icon": "📊", "runner": "Rscript",  "comment": "#"},
    "MATLAB":       {"ext": "m",    "icon": "📐", "runner": "matlab",   "comment": "%"},
    "Dart":         {"ext": "dart", "icon": "🎯", "runner": "dart",     "comment": "//"},
    "Lua":          {"ext": "lua",  "icon": "🌙", "runner": "lua",      "comment": "--"},
}

DEBUG_MODEL   = "gemini-2.5-flash-preview-04-17"  # Most capable for code
FALLBACK_MODEL = "gemini-1.5-flash"
_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

DEBUG_SYSTEM_PROMPT = """\
You are an ELITE Code Debugger and Software Engineer with 20+ years of experience across all languages.

DEBUGGING PROTOCOL:
1. INSTANT BUG DETECTION: Identify ALL bugs (syntax, logic, runtime, security, performance)
2. ROOT CAUSE ANALYSIS: Explain exactly WHY each bug occurs
3. PRECISE FIX: Provide the corrected code with minimal changes
4. LINE-BY-LINE DIFF: Show exactly what changed and why
5. PREVENTION: Explain how to avoid this class of bugs in future

OUTPUT FORMAT (strictly follow this):
### 🔍 Bug Analysis
[List every bug found with line numbers]

### 🧠 Root Cause
[Why each bug occurs — deep technical explanation]

### ✅ Fixed Code
```[language]
[complete corrected code here]
```

### 📝 Changes Made
[Bullet list: line X — changed Y to Z because ...]

### ⚡ Performance & Security Notes
[Any additional improvements, edge cases, best practices]

### 🎓 How to Avoid This
[Educational tip to prevent this bug class]

Be FAST, PRECISE, and THOROUGH. No fluff. Pure debugging excellence.
"""

LEARN_SYSTEM_PROMPT = """\
You are a WORLD-CLASS Programming Tutor — patient, clear, and brilliantly effective.

TEACHING PROTOCOL:
1. CONCEPT FIRST: Start with the "why" before the "how"
2. PROGRESSIVE EXAMPLES: Simple → Complex, always with runnable code
3. VISUAL ASCII: Use diagrams/tables where helpful
4. COMMON MISTAKES: Show what NOT to do and why
5. PRACTICE TASKS: Give 2-3 exercises with hints

RESPONSE FORMAT:
### 📖 Concept Overview
### 💻 Code Examples (with comments)
### ⚠️ Common Mistakes
### 🏋️ Practice Exercises
### 🔗 What to Learn Next

Adapt to the student's level. Make learning FUN and EFFECTIVE.
"""


def _call_gemini_debug(
    prompt: str,
    system: str = DEBUG_SYSTEM_PROMPT,
    use_debug_pool: bool = True,
) -> str:
    """Call Gemini with dedicated debug keys, fallback to main pool."""
    
    # Try dedicated debug keys first
    if use_debug_pool:
        debug_keys = _load_debug_keys()
        for key in debug_keys:
            try:
                result = _gemini_request(key, prompt, system, DEBUG_MODEL)
                if result:
                    return result
            except Exception:
                try:
                    result = _gemini_request(key, prompt, system, FALLBACK_MODEL)
                    if result:
                        return result
                except Exception:
                    continue
    
    # Fallback to main gemini pool
    try:
        from utils import gemini_key_manager as gkm
        key_obj = gkm.get_best_key()
        if key_obj:
            result = _gemini_request(key_obj.api_key, prompt, system, FALLBACK_MODEL)
            if result:
                gkm.record_request(key_obj)
                return result
    except Exception:
        pass
    
    # Final fallback: Groq
    try:
        from utils.groq_client import chat_with_groq
        msgs = [{"role": "user", "content": f"{system}\n\n{prompt}"}]
        return chat_with_groq(msgs, "", model="llama-4-scout-17b-16e-instruct")
    except Exception as e:
        raise RuntimeError(f"All debug engines exhausted: {e}")


def _gemini_request(api_key: str, prompt: str, system: str, model: str) -> str:
    url = f"{_BASE_URL}/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,   # Low temp for precise debugging
            "maxOutputTokens": 8192,
        },
    }
    resp = requests.post(url, json=payload, timeout=60)
    if resp.status_code == 429:
        raise RuntimeError("Rate limited")
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("No candidates returned")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def debug_code(
    code: str,
    language: str,
    error_message: str = "",
    expected_behavior: str = "",
    debug_mode: str = "Full Debug",
) -> str:
    """
    Main debug function. Returns formatted debug report.
    """
    lang_info = SUPPORTED_LANGUAGES.get(language, {})
    runner = lang_info.get("runner", "interpreter")
    
    mode_instructions = {
        "Quick Fix":    "Focus ONLY on the critical bug causing the error. Provide the minimal fix. Be concise.",
        "Full Debug":   "Complete analysis: all bugs, root causes, fixed code, and explanations.",
        "Code Review":  "Full code quality review: bugs, style, performance, security, best practices, and refactoring suggestions.",
        "Explain Code": "Don't debug — EXPLAIN what this code does step by step. Great for learning.",
        "Optimize":     "Focus on performance optimization, time/space complexity, and algorithmic improvements.",
    }
    
    mode_instr = mode_instructions.get(debug_mode, mode_instructions["Full Debug"])
    
    prompt = f"""LANGUAGE: {language} ({runner})
DEBUG MODE: {debug_mode}
INSTRUCTION: {mode_instr}

CODE TO DEBUG:
```{language.lower()}
{code}
```
"""
    if error_message.strip():
        prompt += f"\nERROR / EXCEPTION:\n```\n{error_message.strip()}\n```\n"
    if expected_behavior.strip():
        prompt += f"\nEXPECTED BEHAVIOR:\n{expected_behavior.strip()}\n"

    return _call_gemini_debug(prompt, DEBUG_SYSTEM_PROMPT)


def teach_concept(
    topic: str,
    language: str,
    level: str = "Beginner",
    specific_question: str = "",
) -> str:
    """Teach a coding concept using the learn coding mode."""
    prompt = f"""STUDENT LEVEL: {level}
PROGRAMMING LANGUAGE: {language}
TOPIC: {topic}
"""
    if specific_question.strip():
        prompt += f"\nSPECIFIC QUESTION: {specific_question.strip()}\n"
    
    return _call_gemini_debug(prompt, LEARN_SYSTEM_PROMPT)


def auto_detect_language(code: str) -> str:
    """Heuristic auto-detect of language from code."""
    code_lower = code.lower().strip()
    # Check patterns
    if re.search(r'\bimport\s+\w+\b|\bfrom\s+\w+\s+import\b|\bdef\s+\w+\s*\(', code):
        return "Python"
    if re.search(r'#include\s*<.*\.h>', code):
        if "class " in code or "::" in code or "cout" in code or "cin" in code:
            return "C++"
        return "C"
    if re.search(r'\bpublic\s+class\b|\bSystem\.out\.print', code):
        return "Java"
    if re.search(r'const\s+\w+\s*=|let\s+\w+\s*=|=>\s*\{|\bconsole\.log\b', code):
        if ": string" in code or ": number" in code or "interface " in code:
            return "TypeScript"
        return "JavaScript"
    if re.search(r'<html|<!DOCTYPE|<div|<body', code, re.IGNORECASE):
        return "HTML/CSS"
    if re.search(r'\bfunc\s+\w+\s*\(|\bpackage\s+main\b', code):
        return "Go"
    if re.search(r'\bfn\s+\w+\s*\(|\blet\s+mut\b|\bprintln!\b', code):
        return "Rust"
    if re.search(r'\bSELECT\b|\bINSERT\b|\bCREATE TABLE\b', code, re.IGNORECASE):
        return "SQL"
    if re.search(r'#!/bin/bash|#!/bin/sh|\becho\s+', code):
        return "Bash/Shell"
    if re.search(r'<\?php|\becho\s+"|\$\w+\s*=', code):
        return "PHP"
    if re.search(r'\bdef\s+\w+.*\n.*end\b|\bputs\b', code):
        return "Ruby"
    if re.search(r'\bfun\s+\w+\s*\(|\bval\s+\w+|\bvar\s+\w+:', code):
        return "Kotlin"
    return "Python"  # Default


CURRICULUM = {
    "Python": [
        "Variables & Data Types", "Strings & Formatting", "Lists, Tuples, Sets",
        "Dictionaries", "Control Flow (if/else)", "Loops (for/while)",
        "Functions & Lambda", "Classes & OOP", "File I/O", "Error Handling",
        "List Comprehensions", "Generators & Iterators", "Decorators",
        "Modules & Packages", "Regex", "APIs & Requests", "Data Science (NumPy/Pandas)",
        "Async/Await", "Testing with pytest", "Type Hints",
    ],
    "C": [
        "Hello World & Compilation", "Variables & Data Types", "Operators",
        "Control Flow", "Functions", "Arrays & Strings", "Pointers",
        "Structures & Unions", "Dynamic Memory (malloc/free)", "File I/O",
        "Preprocessor Directives", "Bit Manipulation", "Linked Lists",
        "Stack & Queue", "Sorting Algorithms",
    ],
    "C++": [
        "Classes & Objects", "Constructors & Destructors", "Inheritance",
        "Polymorphism", "Templates", "STL (vectors/maps/sets)",
        "Smart Pointers", "Lambda Functions", "Exceptions", "File I/O",
        "Operator Overloading", "Move Semantics", "Concurrency",
    ],
    "JavaScript": [
        "Variables (var/let/const)", "Data Types", "Functions & Arrow Functions",
        "Arrays & Objects", "DOM Manipulation", "Events", "Async/Await & Promises",
        "Fetch API", "Classes & Prototypes", "Modules (ES6)", "Error Handling",
        "Regular Expressions", "LocalStorage", "Web APIs",
    ],
    "Java": [
        "Classes & Objects", "Inheritance & Polymorphism", "Interfaces & Abstract Classes",
        "Collections Framework", "Generics", "Exception Handling", "File I/O",
        "Streams & Lambda", "Multithreading", "Design Patterns",
    ],
    "HTML/CSS": [
        "HTML Structure & Semantics", "Text & Links", "Images & Media",
        "Forms & Inputs", "CSS Selectors", "Box Model", "Flexbox",
        "CSS Grid", "Responsive Design", "Animations & Transitions",
        "CSS Variables", "Media Queries",
    ],
    "SQL": [
        "SELECT Basics", "WHERE & Filtering", "ORDER BY & LIMIT",
        "Aggregations (GROUP BY)", "JOINs (INNER/LEFT/RIGHT)", "Subqueries",
        "INSERT/UPDATE/DELETE", "CREATE TABLE & Constraints",
        "Indexes & Performance", "Transactions",
    ],
}
