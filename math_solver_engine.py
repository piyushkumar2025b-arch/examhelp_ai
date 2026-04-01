"""
math_solver_engine.py — Advanced Math Problem Solver (Image + Text)
===================================================================
Hybrid Symbolic (SymPy) + Numerical (NumPy) + Reasoning (LLM).
"""

import base64
import json
import re
from typing import Dict, List, Optional, Tuple
import numpy as np
from utils.ai_engine import vision_generate, quick_generate

# Late import for optimization
_sympy_loaded = False
def _import_sympy():
    global _sympy_loaded, sp
    if not _sympy_loaded:
        import sympy as sp
        _sympy_loaded = True

class MathSolver:
    """Handles end-to-end math solving: Image/Text -> Solution."""

    @staticmethod
    def solve(query_text: str = "", image_bytes: Optional[bytes] = None, mime_type: str = "image/png") -> Dict:
        """Main entry point for math solving."""
        try:
            # 1. Parsing Phase: Convert input (image or text) into standard LaTeX/Expressions
            if image_bytes:
                b64_image = base64.b64encode(image_bytes).decode()
                parse_prompt = """
                Analyze this math problem image and extract exactly what's written.
                Return ONLY a valid JSON object with this structure:
                {
                  "raw_text": "The extracted prompt",
                  "latex": "The mathematical expression in LaTeX format",
                  "complexity_level": "Elementary/Algebra/Calculus/Advanced",
                  "is_solvable_locally": true
                }
                """
                parsing_result = vision_generate(prompt=parse_prompt, image_b64=b64_image, mime=mime_type)
            else:
                parse_prompt = f"Convert this math problem into a cleaner JSON description: '{query_text}'. Same JSON structure as vision extraction."
                parsing_result = quick_generate(prompt=parse_prompt)

            # Clean JSON
            json_match = re.search(r'\{.*\}', parsing_result, re.DOTALL)
            if not json_match:
                return {"success": False, "error": "Could not parse mathematical structure."}
            
            math_data = json.loads(json_match.group())
            problem_text = math_data.get("raw_text", query_text)

            # 2. Solving Phase: Generate step-by-step solution
            # engine_name="solver" in prompts.py gives us the Step-by-Step Problem Solver persona.
            solution = quick_generate(
                prompt=f"Solve this math problem: '{problem_text}'. Use LaTeX: {math_data.get('latex','')}",
                engine_name="solver"
            )

            return {
                "success": True,
                "data": math_data,
                "solution": solution
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

def get_math_output_html(result: Dict) -> str:
    """Format math result into Streamlit-ready HTML with LaTeX support."""
    if not result.get("success"):
        return f"<div style='color: #ff4b4b; padding: 10px; background: #fee;'>❌ Error: {result.get('error')}</div>"
    
    data = result["data"]
    sol = result["solution"]
    
    return f"""
    <div style="font-family: 'Segoe UI', serif; line-height: 1.6;">
        <h3 style="color: #6c5ce7;">🎯 Problem Parsed</h3>
        <code style="background: #f1f2f6; padding: 5px; border-radius: 4px;">{data.get('latex', data.get('raw_text', ''))}</code>
        <hr/>
        <h3 style="color: #2e86de;">💡 Step-by-Step Solution</h3>
        <div style="background: #f8f9fa; padding: 15px; border-left: 5px solid #6c5ce7; border-radius: 8px;">
            {sol.replace('\n', '<br>')}
        </div>
    </div>
    """
