"""
math_solver_engine.py — Advanced Math Problem Solver v2.0
Hybrid: Newton API + MathJS API (free, no key) + SymPy + LLM Reasoning.
Handles: text input, image upload, step-by-step explanation, formula sheet, graph hints.
"""
from __future__ import annotations
import base64
import json
import re
from typing import Dict, List, Optional
from utils.ai_engine import vision_generate, quick_generate, generate
from free_apis import compute_math, evaluate_expression, NEWTON_OPS

MATH_SYSTEM = """\
You are an expert Mathematics Professor and Olympiad problem solver. 
Solve every problem with crystal-clear, step-by-step working — show ALL steps, no skipping.
Use LaTeX notation for all mathematical expressions (wrap in $...$ or $$...$$).
After the solution, always include:
- A "Concept" note explaining the underlying principle
- A "Common Mistakes" section with 2-3 pitfalls to avoid
- A "Verification" step to check the answer
"""

MATH_TOPICS = {
    "General / Auto-Detect":     "Detect and solve automatically",
    "Algebra":                   "Equations, inequalities, polynomials, factoring, systems of equations",
    "Calculus":                  "Derivatives, integrals, limits, series, differential equations",
    "Trigonometry":              "Identities, equations, inverse trig, wave functions",
    "Statistics & Probability":  "Mean, median, mode, distributions, hypothesis testing, permutations",
    "Number Theory":             "Primes, divisibility, modular arithmetic, Diophantine equations",
    "Linear Algebra":            "Matrices, determinants, eigenvalues, vector spaces, transformations",
    "Geometry":                  "Euclidean geometry, coordinate geometry, solid geometry, proofs",
    "Discrete Mathematics":      "Combinations, graph theory, logic, proof techniques",
    "Physics / Applied Math":    "Kinematics, dynamics, thermodynamics, electromagnetism equations",
}

DIFFICULTY_HINTS = {
    "School (Class 6-10)":    "Use simple notation, detailed explanation, relatable analogies.",
    "High School (11-12)":    "Include all steps, mention board exam techniques, typical marking scheme.",
    "University / College":   "Rigorous proof-based approach, mention theorems used, cite methods.",
    "Competitive / Olympiad": "Show elegant solutions, mention multiple approaches if possible.",
    "PhD / Research":         "Assume high expertise, reference relevant literature or techniques.",
}


class MathSolver:
    """End-to-end math solving: Image/Text → Parsed → Solved → Explained."""

    @staticmethod
    def solve(
        query_text: str = "",
        image_bytes: Optional[bytes] = None,
        mime_type: str = "image/png",
        topic: str = "General / Auto-Detect",
        difficulty: str = "High School (11-12)",
        show_graph_hints: bool = False,
    ) -> Dict:
        """Main entry point — text or image input."""
        try:
            topic_desc = MATH_TOPICS.get(topic, "")
            diff_hint  = DIFFICULTY_HINTS.get(difficulty, "")

            if image_bytes:
                b64 = base64.b64encode(image_bytes).decode()
                parse_prompt = f"""Analyze this math problem image carefully.
Return ONLY valid JSON:
{{
  "raw_text": "exact problem text extracted",
  "latex": "LaTeX expression",
  "topic": "{topic}",
  "complexity_level": "Elementary/Algebra/Calculus/Advanced",
  "has_graph": false
}}"""
                raw = vision_generate(prompt=parse_prompt, image_b64=b64, mime=mime_type)
            else:
                parse_prompt = f"""Parse this math problem: '{query_text}'
Return ONLY valid JSON:
{{
  "raw_text": "{query_text}",
  "latex": "LaTeX form",
  "topic": "{topic}",
  "complexity_level": "auto-detected",
  "has_graph": false
}}"""
                raw = quick_generate(prompt=parse_prompt)

            math_data = {}
            try:
                m = re.search(r'\{.*\}', raw or "", re.DOTALL)
                if m:
                    math_data = json.loads(m.group())
            except Exception:
                pass

            problem = math_data.get("raw_text", query_text)
            latex   = math_data.get("latex", "")

            # ── Fast pre-solve: Newton API + MathJS (free, no key, instant) ──────
            fast_result = ""
            expr_clean  = re.sub(r'\s+', '', problem[:200])
            if not image_bytes and expr_clean:
                # Try numeric evaluation first (MathJS)
                try:
                    numeric = evaluate_expression(expr_clean)
                    if numeric and numeric.strip():
                        fast_result = f"\n\n**Quick Numeric Result** (MathJS API): `{expr_clean} = {numeric.strip()}`"
                except Exception:
                    pass

                # Try symbolic operation (Newton API) if expression looks algebraic
                if not fast_result:
                    for op in ["simplify", "factor", "derive", "integrate"]:
                        try:
                            newton = compute_math(expr_clean, op)
                            if newton and newton.get("result") and newton["result"] != expr_clean:
                                fast_result = f"\n\n**Symbolic Result** ({op.capitalize()}, Newton API): `{newton['result']}`"
                                break
                        except Exception:
                            continue

            graph_hint = ""
            if show_graph_hints:
                graph_hint = "\n\nAlso describe what a graph of this problem/solution would look like — axes, shape, key points."

            solution = generate(
                prompt=f"""TOPIC: {topic} — {topic_desc}
DIFFICULTY: {difficulty} — {diff_hint}

PROBLEM: {problem}
{"LATEX: " + latex if latex else ""}
{fast_result}

Solve this completely, step-by-step.{graph_hint}""",
                system=MATH_SYSTEM,
                engine_name="solver",
                max_tokens=2000,
            )

            return {
                "success":    True,
                "data":       math_data,
                "problem":    problem,
                "latex":      latex,
                "fast_result": fast_result.strip(),
                "solution":   solution or "Solution not available.",
                "topic":      topic,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def generate_practice_problems(topic: str, difficulty: str, count: int = 5) -> str:
        """Generate practice problems with answers for a given topic."""
        diff_hint = DIFFICULTY_HINTS.get(difficulty, "")
        return generate(
            prompt=f"""Generate {count} practice problems for: {topic}
Difficulty: {difficulty} — {diff_hint}

Format each as:
**Problem N**: [clear problem statement]
💡 **Hint**: [one-line hint]
✅ **Answer**: [final answer only — show working separately]

Make problems progressively harder.""",
            engine_name="solver",
            max_tokens=2000,
        ) or "Practice problems unavailable."

    @staticmethod
    def explain_concept(concept: str, level: str = "High School (11-12)") -> str:
        """Explain a math concept from scratch."""
        diff = DIFFICULTY_HINTS.get(level, "")
        return generate(
            prompt=f"""Explain the concept: "{concept}"
Level: {level} — {diff}

Structure:
## What is it?
## Why does it work? (Intuition)
## Key Formula(s)
## Worked Example (fully solved)
## When to use it
## Common mistakes""",
            engine_name="solver",
            max_tokens=1500,
        ) or "Explanation unavailable."

    @staticmethod
    def check_solution(problem: str, student_answer: str) -> str:
        """Check if a student's answer is correct and give feedback."""
        return generate(
            prompt=f"""A student solved this math problem:

PROBLEM: {problem}
STUDENT'S ANSWER: {student_answer}

Evaluate:
1. ✅ Is the answer CORRECT or ❌ INCORRECT?
2. If incorrect — what specific mistake was made?
3. Show the CORRECT complete solution
4. Give a tip to avoid this mistake in future""",
            engine_name="solver",
            max_tokens=1500,
        ) or "Check unavailable."

    @staticmethod
    def formula_sheet(topic: str) -> str:
        """Generate a comprehensive formula sheet for a topic."""
        return generate(
            prompt=f"""Create a complete, exam-ready formula sheet for: {topic}

Format:
## [Sub-topic]
| Formula | Name/Description | When to Use |
|---------|-----------------|-------------|

Cover every important formula. Include conditions/constraints.
End with: **Key Tips** and **Common Exam Traps**""",
            engine_name="solver",
            max_tokens=3000,
        ) or "Formula sheet unavailable."


def get_math_output_html(result: Dict) -> str:
    """Format math result into styled HTML."""
    if not result.get("success"):
        return f"""<div style='
            font-family:"Rajdhani",sans-serif;
            color:#ef4444;padding:16px 20px;
            background:rgba(239,68,68,0.08);
            border:1px solid rgba(239,68,68,0.2);
            border-left:3px solid #ef4444;
            border-radius:12px;'>
            ❌ Error: {result.get("error","Unknown error")}
        </div>"""

    data = result.get("data", {})
    sol  = result.get("solution", "")
    prob = result.get("problem", "")
    lt   = result.get("latex", "")

    return f"""
    <div style="font-family:'Rajdhani',sans-serif;line-height:1.7;">
        <div style="background:rgba(167,139,250,0.08);border:1px solid rgba(167,139,250,0.2);
            border-left:3px solid #a78bfa;border-radius:12px;padding:14px 18px;margin-bottom:14px;">
            <div style="font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.3);margin-bottom:6px;">PROBLEM</div>
            <div style="font-size:15px;color:#f0eaf8;">{prob}</div>
            {f'<code style="font-size:12px;color:#a78bfa;display:block;margin-top:6px;">{lt}</code>' if lt else ""}
        </div>
        <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15);
            border-left:3px solid #10b981;border-radius:12px;padding:16px 18px;">
            <div style="font-size:10px;letter-spacing:3px;color:rgba(255,255,255,0.3);margin-bottom:8px;">STEP-BY-STEP SOLUTION</div>
            <div style="font-size:14px;color:rgba(255,255,255,0.82);">{sol.replace(chr(10),"<br>")}</div>
        </div>
    </div>"""
