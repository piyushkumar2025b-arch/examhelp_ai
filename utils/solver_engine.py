"""
solver_engine.py — AI Math & Science Problem Solver
Step-by-step solutions for math, physics, chemistry, biology problems.
"""
from __future__ import annotations
from utils.debugger_engine import _call_gemini_debug

SUBJECTS = {
    "Mathematics": {
        "icon": "🔢",
        "topics": ["Algebra", "Calculus", "Statistics", "Linear Algebra", "Number Theory",
                   "Trigonometry", "Geometry", "Differential Equations", "Discrete Math",
                   "Probability", "Combinatorics", "Real Analysis", "Complex Analysis"],
    },
    "Physics": {
        "icon": "⚡",
        "topics": ["Mechanics", "Thermodynamics", "Electromagnetism", "Optics", "Quantum",
                   "Relativity", "Waves", "Nuclear Physics", "Fluid Dynamics", "Astrophysics"],
    },
    "Chemistry": {
        "icon": "⚗️",
        "topics": ["Organic Chemistry", "Inorganic Chemistry", "Physical Chemistry",
                   "Electrochemistry", "Thermochemistry", "Kinetics", "Equilibrium",
                   "Acid-Base", "Spectroscopy", "Polymer Chemistry"],
    },
    "Biology": {
        "icon": "🧬",
        "topics": ["Cell Biology", "Genetics", "Ecology", "Evolution", "Physiology",
                   "Biochemistry", "Microbiology", "Neuroscience", "Immunology", "Botany"],
    },
    "Computer Science": {
        "icon": "💻",
        "topics": ["Algorithms", "Data Structures", "Complexity Theory", "Logic Gates",
                   "Boolean Algebra", "Graph Theory", "Automata Theory", "OS Concepts"],
    },
    "Economics": {
        "icon": "📉",
        "topics": ["Microeconomics", "Macroeconomics", "Game Theory", "Econometrics",
                   "International Trade", "Financial Economics", "Labour Economics"],
    },
}

SOLVER_SYSTEM = """\
You are a WORLD-CLASS Science & Mathematics Tutor who teaches like the best professors at MIT/IIT.

SOLVING PROTOCOL:
1. IDENTIFY: Classify the problem type and relevant concepts
2. GIVEN/FIND: List known values and what we need to find
3. FORMULA: State the relevant formula(s) with explanation
4. STEP-BY-STEP WORK: Show EVERY calculation step clearly
5. UNITS: Track units throughout (dimensional analysis)
6. ANSWER: Box the final answer clearly
7. VERIFICATION: Check the answer makes sense
8. CONCEPT LINK: Explain the underlying concept

Use LaTeX math notation: $inline$ and $$display$$
Make it educational, not just an answer machine.
"""

def solve_problem(
    problem: str,
    subject: str,
    show_alternatives: bool = True,
    difficulty: str = "Standard",
) -> str:
    prompt = f"""Solve this {subject} problem completely:

PROBLEM:
{problem}

DIFFICULTY LEVEL: {difficulty}

Solve step-by-step following the full protocol. Show all work.
"""
    if show_alternatives:
        prompt += "\nAlso: Show an alternative solution method if one exists."
    return _call_gemini_debug(prompt, SOLVER_SYSTEM)


def explain_concept(concept: str, subject: str, depth: str = "Standard") -> str:
    depth_map = {
        "Quick Overview": "2-3 paragraphs, intuitive understanding",
        "Standard":       "Full explanation with derivation, examples, and applications",
        "Expert Deep Dive": "Complete treatment: history, proofs, edge cases, research connections, open problems",
    }
    prompt = f"""Explain this concept from {subject}: "{concept}"

DEPTH: {depth} — {depth_map.get(depth, '')}

Include:
1. Intuitive explanation (what it means in plain language)
2. Formal definition/statement
3. Derivation or proof (if applicable)
4. 3 worked examples (easy → hard)
5. Common misconceptions
6. Real-world applications
7. Related concepts to explore next"""
    return _call_gemini_debug(prompt, SOLVER_SYSTEM)


def generate_practice_problems(subject: str, topic: str, difficulty: str, count: int = 5) -> str:
    prompt = f"""Generate {count} {difficulty} practice problems for:
Subject: {subject}
Topic: {topic}

For each problem:
1. The problem statement (clear and unambiguous)
2. Any given data/hints
3. The complete solution with steps
4. The key concept being tested

Vary the problem types and difficulty slightly within {difficulty} level.
Number them clearly: Problem 1, Problem 2, etc."""
    return _call_gemini_debug(prompt, SOLVER_SYSTEM)


def check_solution(problem: str, student_solution: str, subject: str) -> str:
    prompt = f"""A student solved this {subject} problem. Check their work:

PROBLEM: {problem}

STUDENT'S SOLUTION: {student_solution}

Evaluate:
1. Is the final answer correct? (Yes/No/Partially)
2. Are all steps valid?
3. Where did they go wrong (if anywhere)?
4. What concept did they misunderstand?
5. The correct complete solution
6. Score: __ / 10 with justification"""
    return _call_gemini_debug(prompt, SOLVER_SYSTEM)


def formula_sheet(subject: str, topic: str) -> str:
    prompt = f"""Create a comprehensive formula/reference sheet for:
Subject: {subject}
Topic: {topic}

Include:
- All key formulas with variable definitions
- Important constants (with values)
- Common identities and relationships
- Conditions where each formula applies
- Quick memory tricks for hard-to-remember formulas
- Units for each quantity

Format as a clean, exam-ready reference sheet."""
    return _call_gemini_debug(prompt, SOLVER_SYSTEM)
