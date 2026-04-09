"""
utils/vit_engine.py — VIT Chennai Academic Infrastructure Module
Specialized tools for CGPA, attendance, and slot-based timetabling.
FIX-10.8: Complete CGPA calculator with classification + credit planner.
"""
from __future__ import annotations
import math, json
from typing import Dict, List, Optional, Tuple

# VIT Grading Points — S: 10, A: 9, B: 8, C: 7, D: 6, E: 5, F: 0
VIT_GRADES = {"S": 10, "A": 9, "B": 8, "C": 7, "D": 6, "E": 5, "F": 0, "N": 0}


def calculate_cgpa(courses: List[Dict]) -> Dict:
    """
    FIX-10.8: VIT CGPA calculator per official grade scale.
    courses: [{"name": str, "credits": int, "grade": str}]
    VIT Grade Scale: S=10, A=9, B=8, C=7, D=6, E=5, F=0
    """
    grade_map = {"S": 10, "A": 9, "B": 8, "C": 7, "D": 6, "E": 5, "F": 0, "N": 0}
    total_credits = sum(c.get("credits", 0) for c in courses)
    total_points = sum(
        c.get("credits", 0) * grade_map.get(str(c.get("grade", "F")).upper(), 0)
        for c in courses
    )
    cgpa = total_points / total_credits if total_credits > 0 else 0.0
    classification = (
        "First Class with Distinction" if cgpa >= 8.5 else
        "First Class" if cgpa >= 7.5 else
        "Second Class" if cgpa >= 6.0 else
        "Pass"
    )
    return {
        "cgpa": round(cgpa, 2),
        "total_credits": total_credits,
        "grade_points": total_points,
        "classification": classification,
    }


def cgpa_credit_planner(current_courses: List[Dict], target_cgpa: float) -> Dict:
    """
    ADD-10.8: Credit Planner — shows minimum credits at S/A grade needed to reach target CGPA.
    """
    current = calculate_cgpa(current_courses)
    current_cgpa = current["cgpa"]
    current_credits = current["total_credits"]
    current_points = current["grade_points"]

    if current_cgpa >= target_cgpa:
        return {"message": f"✅ Already at {current_cgpa} CGPA — target reached!", "needed_credits": 0}

    # Calculate credits needed at S (10 points) to reach target
    # target = (current_points + needed_credits * 10) / (current_credits + needed_credits)
    # target * (current_credits + x) = current_points + 10x
    # target * current_credits + target * x = current_points + 10x
    # target * current_credits - current_points = x * (10 - target)
    denom = 10 - target_cgpa
    if denom <= 0:
        return {"message": "Target CGPA cannot exceed 10.", "needed_credits": 0}
    credits_at_s = math.ceil((target_cgpa * current_credits - current_points) / denom)

    # Also calculate at A (9 points)
    denom_a = 9 - target_cgpa
    credits_at_a = math.ceil((target_cgpa * current_credits - current_points) / denom_a) if denom_a > 0 else float("inf")

    return {
        "current_cgpa": current_cgpa,
        "target_cgpa": target_cgpa,
        "credits_needed_at_S": max(0, credits_at_s),
        "credits_needed_at_A": max(0, credits_at_a) if denom_a > 0 else "Not achievable at A grade alone",
        "message": f"You need {max(0, credits_at_s)} credits of S grade to reach {target_cgpa} CGPA.",
    }


def calculate_gpa(courses: List[Dict]) -> Dict:
    """Legacy: Calculate SGPA for a semester. Expects [{'credits': 4, 'grade': 'S'}]."""
    return calculate_cgpa(courses)


def attendance_status(attended: int, total: int) -> Dict:
    """Check attendance percentage and requirements for 75%."""
    if total <= 0:
        return {"percentage": 0, "status": "No data", "required_more": 0}
    pct = (attended / total) * 100
    safe = pct >= 75
    req = 0
    if not safe:
        req = math.ceil((0.75 * total - attended) / 0.25)
    return {
        "percentage": round(pct, 2),
        "safe": safe,
        "required_more": max(0, req),
        "status": "✅ Above 75%" if safe else "🚨 Warning: Low Attendance",
    }


# VIT Slot Timetable Mapping
VIT_SLOT_TIMINGS = {
    "A1": "Mon 08:00 - 08:50", "B1": "Mon 09:00 - 09:50", "C1": "Mon 10:00 - 10:50",
    "A2": "Mon 14:00 - 14:50", "B2": "Mon 15:00 - 15:50", "C2": "Mon 16:00 - 16:50",
    "L1": "Lab Mode", "L2": "Lab Mode",
}


def parse_slot_timetable(slots: List[str]) -> List[Dict]:
    """Map slot codes to actual time/day."""
    return [
        {"slot": s.upper().strip(), "time": VIT_SLOT_TIMINGS.get(s.upper().strip(), "Custom Slot (Refer VTOP)")}
        for s in slots
    ]


def calculate_gpa(courses: List[Dict[str, any]]) -> Dict:
    """
    Calculate SGPA for a semester.
    Expects courses: [{"credits": 4, "grade": "S"}]
    """
    total_credits = 0
    total_points = 0
    for c in courses:
        creds = float(c.get("credits", 0))
        grade = c.get("grade", "F").upper().strip()
        points = VIT_GRADES.get(grade, 0)
        total_credits += creds
        total_points += (creds * points)
    
    sgpa = total_points / total_credits if total_credits > 0 else 0.0
    return {
        "sgpa": round(sgpa, 2),
        "total_credits": total_credits,
        "total_points": total_points
    }

def attendance_status(attended: int, total: int) -> Dict:
    """
    Check attendance percentage and requirements for 75%.
    """
    if total <= 0: return {"percentage": 0, "status": "No data", "required_more": 0}
    
    pct = (attended / total) * 100
    safe = pct >= 75
    
    # Calculate how many more classes needed if below 75%
    req = 0
    if not safe:
        # 0.75 = (attended + req) / (total + req)
        # 0.75*total + 0.75*req = attended + req
        # 0.75*total - attended = req - 0.75*req
        # 0.75*total - attended = 0.25*req
        # req = (0.75*total - attended) / 0.25
        req = math.ceil((0.75 * total - attended) / 0.25)
        
    return {
        "percentage": round(pct, 2),
        "safe": safe,
        "required_more": max(0, req),
        "status": "✅ Above 75%" if safe else "🚨 Warning: Low Attendance"
    }

# VIT Slot Timetable Mapping (Simplified example)
VIT_SLOT_TIMINGS = {
    "A1": "Mon 08:00 - 08:50", "B1": "Mon 09:00 - 09:50", "C1": "Mon 10:00 - 10:50",
    "A2": "Mon 14:00 - 14:50", "B2": "Mon 15:00 - 15:50", "C2": "Mon 16:00 - 16:50",
    "L1": "Lab Mode", "L2": "Lab Mode",
}

def parse_slot_timetable(slots: List[str]) -> List[Dict]:
    """
    Map slot codes to actual time/day.
    """
    res = []
    for s in slots:
        s = s.upper().strip()
        if s in VIT_SLOT_TIMINGS:
            res.append({"slot": s, "time": VIT_SLOT_TIMINGS[s]})
        else:
            res.append({"slot": s, "time": "Custom Slot (Refer VTOP)"})
    return res
