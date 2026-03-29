"""
utils/vit_engine.py — VIT Chennai Academic Infrastructure Module
Specialized tools for CGPA, attendance, and slot-based timetabling.
"""
from __future__ import annotations
import math, json
from typing import Dict, List, Optional, Tuple

# VIT Grading Points
# S: 10, A: 9, B: 8, C: 7, D: 6, E: 5, F: 0, N: 0
VIT_GRADES = {"S": 10, "A": 9, "B": 8, "C": 7, "D": 6, "E": 5, "F": 0, "N": 0}

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
