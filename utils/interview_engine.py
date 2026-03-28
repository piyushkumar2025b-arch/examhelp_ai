"""
interview_engine.py — AI Interview Coach
Mock interviews, answer frameworks, feedback, and preparation.
"""
from __future__ import annotations
from utils.debugger_engine import _call_gemini_debug

INTERVIEW_TYPES = {
    "Technical (CS/Engineering)": "algorithms, data structures, system design, coding challenges",
    "Behavioural (STAR Method)":  "situational, teamwork, leadership, conflict, achievements",
    "HR / Culture Fit":           "company values, motivation, career goals, salary negotiation",
    "Case Interview (Consulting)":"market sizing, business cases, frameworks (MECE, Porter's Five)",
    "Product Manager":            "product sense, metrics, roadmap, prioritization, execution",
    "Data Science / ML":          "statistics, ML concepts, A/B testing, SQL, Python analytics",
    "Finance / Investment":       "valuation, DCF, LBO, market questions, financial modelling",
    "Medical / Healthcare":       "clinical scenarios, ethics, patient communication, protocols",
    "Law / Legal":                "case analysis, legal reasoning, hypotheticals, ethics",
    "Academic / Research":        "research methodology, thesis defense, publication review",
}

EXPERIENCE_LEVELS = ["Fresher/Intern", "Junior (1-3 yrs)", "Mid-level (3-7 yrs)", "Senior (7+ yrs)", "Executive/C-Suite"]

INTERVIEW_SYSTEM = """\
You are an ELITE Interview Coach who has prepared thousands of candidates for top-tier companies (Google, McKinsey, Goldman Sachs, top universities, etc.).

COACHING PROTOCOL:
1. REALISTIC SIMULATION: Ask questions exactly as a real interviewer would
2. DEEP FEEDBACK: After each answer, give specific, actionable critique
3. FRAMEWORK TEACHING: Teach frameworks (STAR, MECE, etc.) when relevant
4. BENCHMARK AGAINST: Compare answers to what top candidates say
5. BODY LANGUAGE & DELIVERY: Include soft skill tips

Be direct, professional, and genuinely helpful. No fluff.
"""

FEEDBACK_SYSTEM = """\
You are a senior hiring manager giving brutally honest but constructive feedback.
Rate the answer: Score (1-10), Strengths, Weaknesses, Ideal answer sample, One-line verdict.
"""

def generate_questions(
    role: str,
    company: str,
    interview_type: str,
    experience: str,
    num_questions: int = 10,
) -> str:
    prompt = f"""Generate {num_questions} realistic interview questions for:

ROLE: {role}
COMPANY/INDUSTRY: {company}
INTERVIEW TYPE: {interview_type} ({INTERVIEW_TYPES.get(interview_type, '')})
CANDIDATE LEVEL: {experience}

For each question:
1. The question itself
2. What the interviewer is really testing
3. A brief hint on how to approach it

Format clearly with Q1, Q2, etc."""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)


def evaluate_answer(question: str, answer: str, role: str, interview_type: str) -> str:
    prompt = f"""INTERVIEW CONTEXT:
Role: {role}
Type: {interview_type}

QUESTION: {question}

CANDIDATE'S ANSWER: {answer}

Provide detailed feedback:
1. Score (1-10) with justification
2. What was done well
3. What was missing or weak
4. An example of a strong answer to this question
5. Tips for improvement"""
    return _call_gemini_debug(prompt, FEEDBACK_SYSTEM)


def mock_interview_response(
    conversation_history: list,
    role: str,
    interview_type: str,
    mode: str = "ask",  # "ask" or "feedback"
) -> str:
    history_str = "\n".join([
        f"{'Interviewer' if m['role']=='assistant' else 'Candidate'}: {m['content']}"
        for m in conversation_history[-12:]
    ])
    if mode == "ask":
        prompt = f"""You are interviewing a candidate for: {role} ({interview_type})

CONVERSATION SO FAR:
{history_str}

Continue the interview. Ask the next appropriate question. Keep it realistic and professional.
If this is the first message, introduce yourself briefly and ask the first question."""
    else:
        prompt = f"""Interview conversation:
{history_str}

Give comprehensive feedback on the candidate's performance so far:
- Overall rating
- Strongest answers
- Weakest areas  
- Specific improvements
- Likelihood of passing this stage"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)


def generate_company_research(company: str, role: str) -> str:
    prompt = f"""Create a comprehensive interview preparation brief for:
Company: {company}
Role: {role}

Include:
1. Key things to know about this company (business model, culture, recent news)
2. What this company typically looks for in {role} candidates
3. Likely interview questions specific to this company
4. Smart questions to ask the interviewer
5. Red flags to avoid
6. Salary negotiation tips for this role/company"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)
