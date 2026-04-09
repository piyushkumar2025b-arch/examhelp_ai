"""
interview_engine.py — Elite Interview Coach v2.0
Role-specific questions · STAR framework · Scoring rubric · Company research
Salary negotiation · Body language coaching · Mock interview with live feedback
"""
from __future__ import annotations

INTERVIEW_TYPES = {
    "Technical (CS/Engineering)": "algorithms, data structures, system design, coding challenges, complexity analysis",
    "Behavioural (STAR Method)":  "situational, teamwork, leadership, conflict resolution, achievements, initiative",
    "HR / Culture Fit":           "company values, motivation, career goals, salary negotiation, work style",
    "Case Interview (Consulting)":"market sizing, business cases, MECE frameworks, Porter's Five Forces, profitability trees",
    "Product Manager":            "product sense, metrics, north star, roadmap, prioritization, execution, go-to-market",
    "Data Science / ML":          "statistics, ML algorithms, A/B testing, SQL, Python analytics, model evaluation",
    "Finance / Investment":       "valuation, DCF, LBO, M&A, market questions, financial modelling, capital structure",
    "Medical / Healthcare":       "clinical scenarios, ethics, patient communication, protocols, multidisciplinary care",
    "Law / Legal":                "case analysis, legal reasoning, statutory interpretation, hypotheticals, ethics",
    "Academic / Research":        "methodology, thesis defense, publication quality, peer review, grant writing",
    "Sales & Business Dev":       "pipeline, objection handling, negotiation, closing, account management, metrics",
    "UX / Design":                "design thinking, user research, critique, portfolio defense, accessibility",
}

EXPERIENCE_LEVELS = ["Fresher/Intern", "Junior (1-3 yrs)", "Mid-level (3-7 yrs)", "Senior (7+ yrs)", "Executive/C-Suite"]

INTERVIEW_SYSTEM = """\
You are the world's most effective Interview Coach — having prepared over 10,000 candidates for Google, McKinsey, Goldman Sachs, Harvard, and top global firms.

YOUR COACHING PHILOSOPHY:
1. REALISTIC SIMULATION — Ask questions EXACTLY as a real interviewer would at that company/level
2. FRAMEWORK TEACHING — Teach STAR, MECE, Situation→Complication→Resolution when relevant
3. DEEP FEEDBACK — After answers: specific strengths, specific gaps, benchmark against top performers
4. BODY LANGUAGE — Include delivery/presentation tips, not just content
5. STRESS TESTING — Follow up on vague answers, push for specifics, just like real interviewers do
6. LEVEL CALIBRATION — Fresher questions are different from Senior/Executive questions

Be direct. Be specific. Be genuinely helpful. No generic advice."""

FEEDBACK_SYSTEM = """\
You are a senior hiring manager at a top-tier company giving brutally honest, constructive feedback.

SCORING RUBRIC:
- Content (40%): Is the answer relevant, specific, and complete?
- Structure (20%): Is it organized? (STAR/clear framework used?)
- Depth (20%): Does it show genuine insight and self-awareness?
- Impact (20%): Were concrete results/metrics mentioned?

Provide:
1. **Score: X/10** with breakdown by dimension
2. **What worked well** (specific phrases/points)
3. **What was missing** (specific gaps)
4. **Model answer** (what a top 10% candidate would say)
5. **Delivery tip** (one practical improvement for next time)
6. **Verdict** (Hire / Maybe / No) with one-line reasoning"""

SALARY_SYSTEM = """\
You are a compensation expert and negotiation coach. Be precise, data-informed, and tactical.
Give market rates, negotiation scripts, and strategic advice. No fluff."""


def generate_questions(role: str, company: str, interview_type: str, experience: str, num_questions: int = 10) -> str:
    from utils.debugger_engine import _call_gemini_debug

    # FIX-6.1: Role-specific technical depth injection
    is_technical = any(kw in interview_type.lower() for kw in ("technical", "cs", "data science", "ml", "ux", "product"))
    level_map = {
        "Fresher/Intern": "Junior",
        "Junior (1-3 yrs)": "Junior",
        "Mid-level (3-7 yrs)": "Mid",
        "Senior (7+ yrs)": "Senior",
        "Executive/C-Suite": "Staff",
    }
    level = level_map.get(experience, "Mid")

    if is_technical:
        mix = "40% technical questions, 30% system design, 30% behavioural."
    else:
        mix = "20% role-specific knowledge questions, 80% behavioural (STAR format)."

    prompt = f"""Generate {num_questions} realistic, role-specific interview questions for:

Role: {role}
Company: {company or 'a top-tier company'}
Interview Type: {interview_type} ({INTERVIEW_TYPES.get(interview_type, '')})
Level: {level} ({experience})

Question mix: {mix}
Technical questions MUST include expected answers with code snippets where relevant.
Behavioural questions MUST use STAR format in model answers.

For EACH question provide:
**Q[n]. [Question text]**
- *What the interviewer is testing:* [specific competency]
- *Difficulty:* Easy/Medium/Hard
- *Model Answer:* [gold-standard response, with code if technical]
- *Pitfalls:* [what bad answers look like]

After all questions, add:
**Top 5 Smart Questions to Ask the Interviewer** (tailored to {company or 'this company'}/{role})"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)


def evaluate_answer(question: str, answer: str, role: str, interview_type: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""INTERVIEW CONTEXT:
Role: {role} | Type: {interview_type}

QUESTION ASKED: {question}

CANDIDATE'S ANSWER:
{answer}

Apply the full scoring rubric. Be specific — quote actual phrases from the answer when praising or critiquing.
Include the model answer so the candidate can learn the gold standard."""
    return _call_gemini_debug(prompt, FEEDBACK_SYSTEM)


def mock_interview_response(conversation_history: list, role: str, company: str = "", interview_type: str = "", mode: str = "ask") -> str:
    """
    FIX-6.2: Full conversational interview with memory — probes vague answers, raises bar after strong ones.
    After 5 exchanges, provides a detailed evaluation scorecard.
    """
    from utils.debugger_engine import _call_gemini_debug

    # Always include the full history for context
    history_str = "\n".join([
        f"{'Interviewer' if m['role'] == 'assistant' else 'Candidate'}: {m['content']}"
        for m in conversation_history
    ])
    exchange_count = len([m for m in conversation_history if m["role"] == "user"])

    if mode == "ask":
        system = f"""You are a tough but fair interviewer at {company or 'a top-tier company'} for a {role} position.
You have completed {exchange_count} exchanges so far.
Rules:
- Ask ONE follow-up question based on the candidate's last answer.
- If the answer was vague, probe deeper: "Can you be more specific about..."
- If the answer was strong, raise the bar: "Interesting. How would you handle X?"
- After 5+ exchanges, provide a detailed evaluation scorecard (overall score, strengths, gaps, hire verdict).
- NEVER repeat a question already asked."""
        prompt = f"""CONVERSATION SO FAR:
{history_str}

Continue the interview. {"If this is the first message, introduce yourself briefly and ask the first question." if not conversation_history else "React naturally to the last answer."}"""
    else:
        system = INTERVIEW_SYSTEM
        prompt = f"""Review this complete interview conversation and give comprehensive performance feedback:

{history_str}

Provide:
1. **Overall Performance Rating:** X/10
2. **Best Moments** (specific quotes)
3. **Weakest Answers** (which questions and why)
4. **Pattern Analysis** (recurring issues)
5. **Specific Skills to Practice** (3-5 targeted exercises)
6. **Pass/Fail Prediction** with confidence %
7. **Next Steps** (what to do before next interview)"""

    return _call_gemini_debug(prompt, system)


def generate_video_script(role: str, company: str, experience: str) -> str:
    """
    ADD-6.2a: Generate a 90-second 'Tell Me About Yourself' verbal script optimized for impact.
    """
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Create a compelling 90-second "Tell Me About Yourself" script for:
Role: {role} | Company: {company or 'a top company'} | Level: {experience}

Structure the script as:
1. **Hook** (15 sec): Memorable opening — professional identity + unique angle
2. **Journey** (30 sec): Key career milestones most relevant to this role
3. **Achievement** (20 sec): ONE specific, quantified highlight that sets them apart
4. **Why This Role** (15 sec): Genuine connection to company/role
5. **Close** (10 sec): Forward-looking statement that invites conversation

Include:
- Exact words to say (not bullet points)
- [Pause here] markers for natural delivery
- Delivery tips: pacing, eye contact, energy cues
- Word count: ~200-220 words (perfect for 90 seconds at a natural pace)"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)


def generate_salary_benchmark(role: str, location: str, years_exp: int, current_offer: str = "") -> str:
    """
    ADD-6.2b: Salary benchmark + full negotiation strategy with scripts.
    """
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Salary negotiation deep-dive:
Role: {role} | Location: {location} | Experience: {years_exp} years
{f"Current Offer: {current_offer}" if current_offer else ""}

Provide:
1. **Market Range** (Low / Median / High) for this exact role/location/level
2. **Negotiation Script** — exact words to say when they make an offer
3. **Red Lines** — what NOT to accept and why
4. **Counter-Offer Template** — word-for-word email/verbal response
5. **Beyond Base Salary** — what else to negotiate (signing bonus, equity, remote days, title, review timeline)
6. **Walk-Away Number** — how to calculate it and when to walk
7. **Common Objections + Responses** (e.g., "That's our standard offer")"""
    return _call_gemini_debug(prompt, SALARY_SYSTEM)


def generate_company_research_brief(company: str, role: str) -> str:
    """
    ADD-6.2c: One-page company research brief with culture, pain points, and questions to ask.
    """
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Create a concise 1-page interview research brief for:
Company: {company} | Role: {role}

Sections:
1. **Company DNA** (business model, culture, recent news angles that matter for interview small talk)
2. **Likely Pain Points** (challenges this company probably faces — useful for framing your value)
3. **What They Value** (signals from job descriptions, Glassdoor, company statements)
4. **5 Impressive Questions to Ask** (show deep research, not generic questions)
5. **Red Flags to Watch** (based on company reputation — what to probe during the interview)
6. **Culture Fit Angle** (how to frame your story to align with their stated values)"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)


def generate_salary_negotiation(role: str, company: str, experience: str, current_offer: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Salary negotiation coaching:
Role: {role} | Company: {company} | Level: {experience} | Current Offer: {current_offer}

1. **Market Range** (base, bonus, equity for this role/company/level)
2. **Your Leverage** (what gives you negotiating power)
3. **Opening Script** (exact words to use when countering)
4. **Negotiation Tactics** (anchoring, bundling, time pressure)
5. **Objection Responses** (scripts for "budget is fixed", "it's our standard offer")
6. **Beyond Salary** (what else to negotiate: signing bonus, equity, PTO, remote days, title)
7. **Walk-Away Number** (how to know when to stop)
8. **Final Script** (how to accept gracefully after negotiating)"""
    return _call_gemini_debug(prompt, SALARY_SYSTEM)


def generate_company_research(company: str, role: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Create a thorough interview prep brief:
Company: {company} | Role: {role}

1. **Company Profile** (business model, revenue, culture, recent major news, competitors)
2. **What They Look For** in {role} candidates (technical + cultural signals)
3. **Role-Specific Questions** (10 likely questions unique to {company} + this role)
4. **Case/Technical Prep** (what kind of problems to expect)
5. **Culture Fit Signals** (values to mention, stories to prepare)
6. **Smart Questions to Ask** (5 impressive questions that show research)
7. **Red Flags to Avoid** (common interview killers at this company)
8. **Compensation Intelligence** (market rate for {role} at {company}, negotiation leverage)
9. **Interview Process** (typical stages, timeline, what to expect at each round)
10. **90-Day Action Plan** (how to prepare optimally over 90 days)"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)



def evaluate_answer(question: str, answer: str, role: str, interview_type: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""INTERVIEW CONTEXT:
Role: {role} | Type: {interview_type}

QUESTION ASKED: {question}

CANDIDATE'S ANSWER:
{answer}

Apply the full scoring rubric. Be specific — quote actual phrases from the answer when praising or critiquing.
Include the model answer so the candidate can learn the gold standard."""
    return _call_gemini_debug(prompt, FEEDBACK_SYSTEM)


def mock_interview_response(conversation_history: list, role: str, interview_type: str, mode: str = "ask") -> str:
    from utils.debugger_engine import _call_gemini_debug
    history_str = "\n".join([
        f"{'Interviewer' if m['role']=='assistant' else 'Candidate'}: {m['content']}"
        for m in conversation_history[-14:]
    ])
    if mode == "ask":
        prompt = f"""You are interviewing for: {role} ({interview_type})

CONVERSATION SO FAR:
{history_str}

Continue the interview. If this is the first message:
- Briefly introduce yourself as [Interviewer Name], [Title] at [Company]
- Set context (10-15 min technical/behavioral screen)
- Ask your first targeted question

Otherwise: React naturally to the last answer (brief acknowledgment + follow-up or next question).
Be realistic — push back on vague answers with "Can you be more specific?" or "What was your personal contribution?" """
    else:
        prompt = f"""Review this interview conversation and give comprehensive performance feedback:

{history_str}

Provide:
1. **Overall Performance Rating:** X/10
2. **Best Moments** (specific quotes/moments)
3. **Weakest Answers** (which questions and why)  
4. **Pattern Analysis** (recurring issues across answers)
5. **Specific Skills to Practice** (3-5 targeted exercises)
6. **Pass/Fail Prediction** with confidence %
7. **Next Steps** (what to do before next interview)"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)


def generate_company_research(company: str, role: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Create a thorough interview prep brief:
Company: {company} | Role: {role}

1. **Company Profile** (business model, revenue, culture, recent major news, competitors)
2. **What They Look For** in {role} candidates (technical + cultural signals)
3. **Role-Specific Questions** (10 likely questions unique to {company} + this role)
4. **Case/Technical Prep** (what kind of problems to expect)
5. **Culture Fit Signals** (values to mention, stories to prepare)
6. **Smart Questions to Ask** (5 impressive questions that show research)
7. **Red Flags to Avoid** (common interview killers at this company)
8. **Compensation Intelligence** (market rate for {role} at {company}, negotiation leverage)
9. **Interview Process** (typical stages, timeline, what to expect at each round)
10. **90-Day Action Plan** (how to prepare optimally over 90 days)"""
    return _call_gemini_debug(prompt, INTERVIEW_SYSTEM)


def generate_salary_negotiation(role: str, company: str, experience: str, current_offer: str) -> str:
    from utils.debugger_engine import _call_gemini_debug
    prompt = f"""Salary negotiation coaching:
Role: {role} | Company: {company} | Level: {experience} | Current Offer: {current_offer}

1. **Market Range** (base, bonus, equity for this role/company/level)
2. **Your Leverage** (what gives you negotiating power)
3. **Opening Script** (exact words to use when countering)
4. **Negotiation Tactics** (anchoring, bundling, time pressure)
5. **Objection Responses** (scripts for "budget is fixed", "it's our standard offer")
6. **Beyond Salary** (what else to negotiate: signing bonus, equity, PTO, remote days, title)
7. **Walk-Away Number** (how to know when to stop)
8. **Final Script** (how to accept gracefully after negotiating)"""
    return _call_gemini_debug(prompt, SALARY_SYSTEM)
