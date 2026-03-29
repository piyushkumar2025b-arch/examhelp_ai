"""
utils/study_tools.py — Specialized academic study aids.
Formula extractor, Pomodoro, and PYQ analyzer.
"""
from __future__ import annotations
import json, time
from typing import Dict, List, Optional
from utils.ai_engine import generate as ai_generate

def extract_formula_sheet(pdf_text: str) -> str:
    """
    Extract formulas, equations, and key definitions from textbook text.
    """
    prompt = [
        {"role": "system", "content": (
            "You are a technical document analyzer. Scan the following textbook/lecture material and extract "
            "EVERY important mathematical formula, physical law, or essential equation. "
            "Format them clearly using Markdown + LaTeX ($$). Group them by topic. "
            "Provide a brief 1-sentence descriptor for each formula. "
            "Return ONLY the formatted formula sheet."
        )},
        {"role": "user", "content": f"Material: {pdf_text[:15000]}"}
    ]
    try:
        return ai_generate(messages=prompt).strip()
    except Exception as e:
        return f"[Formula Extraction Error: {e}]"

def analyze_pyq_patterns(papers_text: List[str], subject: str = "") -> Dict:
    """
    Analyze past year papers to predict likely topics.
    """
    all_text = "\n\n=== NEXT PAPER ===\n\n".join(papers_text)
    prompt = [
        {"role": "system", "content": (
            f"You are an exam strategy expert. Analyze these past year question papers for {subject}. "
            f"1. Identify the most repeated topics and question types. "
            f"2. Rate topics by probability of appearance (High/Medium/Low). "
            f"3. Predict 5 potential questions for the upcoming FAT/CAT exam. "
            f"Return ONLY strictly valid JSON. Format: {{\"repeated_topics\": [{{ \"topic\": \"...\", \"freq\": \"...\", \"prob\": \"...\" }}], \"predicted_questions\": [\"...\"], \"summary\": \"...\"}}."
        )},
        {"role": "user", "content": f"Past Papers: {all_text[:20000]}"}
    ]
    try:
        res = ai_generate(messages=prompt, json_mode=True).strip()
        return json.loads(res)
    except Exception as e:
        return {"error": f"Analysis failed: {e}"}

class PomodoroTimer:
    """
    Basic session state based Pomodoro timer logic.
    Actual timing is handled by Streamlit's rerun and time.time()
    """
    def __init__(self, work_min=25, break_min=5):
        self.work_time = work_min * 60
        self.break_time = break_min * 60
    
    def get_status(self, start_time: float, mode: str = "work") -> Dict:
        now = time.time()
        elapsed = now - start_time
        target = self.work_time if mode == "work" else self.break_time
        remaining = max(0, target - elapsed)
        
        return {
            "remaining_sec": int(remaining),
            "remaining_fmt": f"{int(remaining // 60):02d}:{int(remaining % 60):02d}",
            "completed": remaining <= 0,
            "progress": min(1.0, elapsed / target) if target > 0 else 1.0
        }
