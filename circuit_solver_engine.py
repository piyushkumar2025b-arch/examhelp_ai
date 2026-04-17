"""
circuit_solver_engine.py — AI-Powered Circuit Analysis v2.0
Vision-based detection + KVL/KCL solving + component identification.
New: Text description input, theory mode, component glossary.
"""
from __future__ import annotations
import base64
import json
import re
from typing import Dict, List, Optional
from utils.ai_engine import vision_generate, quick_generate, generate

CIRCUIT_SYSTEM = """\
You are a Senior Electrical Engineering Professor specializing in circuit analysis.
Solve circuits step-by-step using:
- KVL (Kirchhoff's Voltage Law): ΣV = 0 around any closed loop
- KCL (Kirchhoff's Current Law): ΣI = 0 at any node
- Ohm's Law: V = IR
- Node Voltage Method and Mesh Analysis where applicable

Show ALL working. Label every node, component, and current direction.
After solving, state: Total Power Delivered, Total Power Dissipated.
Add a "Key Takeaways" section with real-world implications.
"""

COMPONENT_GLOSSARY = {
    "Resistor":         {"symbol": "R",  "unit": "Ω (Ohm)",   "law": "V = IR",         "emoji": "⬜"},
    "Capacitor":        {"symbol": "C",  "unit": "F (Farad)",  "law": "Q = CV",         "emoji": "⚡"},
    "Inductor":         {"symbol": "L",  "unit": "H (Henry)",  "law": "V = L(dI/dt)",   "emoji": "🌀"},
    "Voltage Source":   {"symbol": "Vs", "unit": "V (Volt)",   "law": "Independent",    "emoji": "🔋"},
    "Current Source":   {"symbol": "Is", "unit": "A (Ampere)", "law": "Independent",    "emoji": "🔌"},
    "Diode":            {"symbol": "D",  "unit": "Forward bias ~0.7V", "law": "Non-linear", "emoji": "🔺"},
    "Transistor (BJT)": {"symbol": "Q",  "unit": "Ic = β·Ib", "law": "Amplifier/Switch", "emoji": "🔲"},
    "Op-Amp":           {"symbol": "A",  "unit": "Infinite gain ideal", "law": "V+ = V-",   "emoji": "🔷"},
    "Ground":           {"symbol": "GND","unit": "0V reference","law": "Reference node",  "emoji": "⏚"},
}

CIRCUIT_TYPES = {
    "DC Circuit":          "Direct current — resistors, voltage/current sources, KVL/KCL",
    "AC Circuit":          "Alternating current — impedance, phasors, resonance",
    "RC Circuit":          "Resistor-Capacitor — charging/discharging, time constant τ=RC",  
    "RL Circuit":          "Resistor-Inductor — transient response, time constant τ=L/R",
    "RLC Circuit":         "Series/parallel RLC — resonance frequency, quality factor",
    "Op-Amp Circuit":      "Operational amplifier — inverting, non-inverting, summing, differentiator",
    "Digital Logic":       "Logic gates, Boolean algebra, truth tables, Karnaugh maps",
    "Power Electronics":   "Diodes, rectifiers, power supply analysis",
}


class CircuitSolver:
    """End-to-end circuit analysis: Image/Text → Components → Solution."""

    @staticmethod
    def solve_from_image(image_bytes: bytes, mime_type: str = "image/png",
                         circuit_type: str = "DC Circuit") -> Dict:
        """Vision-based circuit solving from an uploaded image."""
        try:
            b64 = base64.b64encode(image_bytes).decode()
            prompt = f"""Analyze this {circuit_type} diagram carefully.

Extract ALL circuit components and their connections.
Return ONLY valid JSON:
{{
  "components": [
    {{"type": "resistor|capacitor|inductor|voltage_source|current_source|diode|transistor|op_amp",
      "label": "R1",
      "value": 10,
      "unit": "Ω",
      "nodes": [1, 2]}}
  ],
  "nodes": [0, 1, 2],
  "topology": "series|parallel|mixed",
  "circuit_type": "{circuit_type}",
  "detected_text": "any visible text/labels",
  "topology_summary": "brief plain-English description of the circuit"
}}"""
            raw = vision_generate(prompt=prompt, image_b64=b64, mime=mime_type)

            circuit_data = {}
            try:
                m = re.search(r'\{.*\}', raw or "", re.DOTALL)
                if m:
                    circuit_data = json.loads(m.group())
            except Exception:
                circuit_data = {
                    "detected_text": raw or "",
                    "topology_summary": "Circuit detected — analyzing...",
                    "circuit_type": circuit_type,
                }

            solution = generate(
                prompt=f"""Solve this {circuit_type} step-by-step:

Circuit Description: {circuit_data.get('topology_summary','')}
Components: {json.dumps(circuit_data.get('components', []), indent=2)}

Apply {circuit_type} analysis methods. Show every calculation.
Use KVL/KCL/Ohm's Law as appropriate.
Finally: state all node voltages, branch currents, and power for each component.""",
                system=CIRCUIT_SYSTEM,
                engine_name="solver",
                max_tokens=2000,
            )

            return {
                "success":        True,
                "data":           circuit_data,
                "solution":       solution or "Solution unavailable.",
                "circuit_type":   circuit_type,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def solve_from_text(description: str, circuit_type: str = "DC Circuit") -> Dict:
        """Solve a circuit described in text (no image needed)."""
        try:
            solution = generate(
                prompt=f"""Circuit Type: {circuit_type}
Description: {description}

Solve completely:
1. Draw the circuit topology (describe using node-branch notation)
2. Apply KVL/KCL equations
3. Solve for all unknowns
4. Verify with power balance (ΣP_delivered = ΣP_absorbed)
5. State final answers clearly""",
                system=CIRCUIT_SYSTEM,
                engine_name="solver",
                max_tokens=2000,
            )
            return {
                "success":      True,
                "data":         {"topology_summary": description},
                "solution":     solution or "Solution unavailable.",
                "circuit_type": circuit_type,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def explain_concept(concept: str) -> str:
        """Explain a circuit theory concept from scratch."""
        return generate(
            prompt=f"""Explain this electrical engineering concept: "{concept}"

Structure:
## Definition
## Physical Intuition (what's really happening)
## Mathematical Formula(s)
## Worked Example
## Real-World Application
## Common Exam Questions on this topic""",
            system="You are an expert EE professor. Be precise but accessible.",
            engine_name="solver",
            max_tokens=1500,
        ) or "Explanation unavailable."

    @staticmethod
    def generate_practice_circuit(circuit_type: str, difficulty: str = "Intermediate") -> str:
        """Generate a practice circuit problem."""
        return generate(
            prompt=f"""Generate a {difficulty} {circuit_type} practice problem.

Include:
- **Circuit Description**: specific component values and connections
- **Find**: what to solve for
- 💡 **Hint**: one hint without giving away the answer
- ✅ **Complete Solution**: fully worked out step-by-step""",
            engine_name="solver",
            max_tokens=1500,
        ) or "Practice problem unavailable."


def get_solver_output_html(result: Dict) -> str:
    """Format circuit solver output into styled HTML."""
    if not result.get("success"):
        return f"""<div style='font-family:"Rajdhani",sans-serif;color:#ef4444;padding:16px;
            background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
            border-left:3px solid #ef4444;border-radius:12px;'>
            ❌ Error: {result.get("error","Unknown error")}
        </div>"""

    data = result.get("data", {})
    sol  = result.get("solution", "")
    ct   = result.get("circuit_type", "Circuit")

    components = data.get("components", [])
    comp_html  = ""
    if components:
        rows = "".join(
            f"<tr><td style='padding:6px 12px;color:#a78bfa;font-weight:700;'>{c.get('label',c.get('type',''))}</td>"
            f"<td style='padding:6px 12px;color:rgba(255,255,255,0.7);'>{c.get('type','').title()}</td>"
            f"<td style='padding:6px 12px;color:#34d399;font-family:monospace;'>{c.get('value','')} {c.get('unit','')}</td>"
            f"<td style='padding:6px 12px;color:rgba(255,255,255,0.4);'>Nodes {c.get('nodes',[])}</td></tr>"
            for c in components[:15]
        )
        comp_html = f"""
        <table style="width:100%;border-collapse:collapse;margin-bottom:14px;">
            <thead><tr style="border-bottom:1px solid rgba(255,255,255,0.08);">
                <th style="padding:8px 12px;text-align:left;font-size:9px;letter-spacing:2px;color:rgba(255,255,255,0.3);">LABEL</th>
                <th style="padding:8px 12px;text-align:left;font-size:9px;letter-spacing:2px;color:rgba(255,255,255,0.3);">TYPE</th>
                <th style="padding:8px 12px;text-align:left;font-size:9px;letter-spacing:2px;color:rgba(255,255,255,0.3);">VALUE</th>
                <th style="padding:8px 12px;text-align:left;font-size:9px;letter-spacing:2px;color:rgba(255,255,255,0.3);">POSITION</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>"""

    topology = data.get("topology_summary", "")

    return f"""
    <div style="font-family:'Rajdhani',sans-serif;line-height:1.7;">
        {f'''<div style="background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);
            border-left:3px solid #60a5fa;border-radius:12px;padding:14px 18px;margin-bottom:14px;">
            <div style="font-size:9px;letter-spacing:3px;color:rgba(255,255,255,0.3);margin-bottom:6px;">CIRCUIT — {ct.upper()}</div>
            <div style="font-size:14px;color:rgba(255,255,255,0.75);">{topology}</div>
        </div>''' if topology else ""}
        {f'<div style="margin-bottom:14px;">{comp_html}</div>' if components else ""}
        <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15);
            border-left:3px solid #10b981;border-radius:12px;padding:16px 18px;">
            <div style="font-size:9px;letter-spacing:3px;color:rgba(255,255,255,0.3);margin-bottom:8px;">⚡ STEP-BY-STEP SOLUTION</div>
            <div style="font-size:14px;color:rgba(255,255,255,0.82);">{sol.replace(chr(10),"<br>")}</div>
        </div>
    </div>"""
