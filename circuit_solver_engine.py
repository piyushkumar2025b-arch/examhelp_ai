"""
circuit_solver_engine.py — AI-Powered Circuit Analysis from Image
================================================================
Vision-based detection + Symbolic Solvers (KVL/KCL).
"""

import base64
import json
import re
from typing import Dict, List, Optional, Tuple
import numpy as np
from utils.ai_engine import vision_generate, quick_generate

class CircuitSolver:
    """Handles the end-to-end pipeline from Image -> Solved Circuit."""

    @staticmethod
    def solve_from_image(image_bytes: bytes, mime_type: str = "image/png") -> Dict:
        """Main entry point for circuit solving."""
        try:
            # 1. Vision Phase: Use Gemini to extract the circuit topography
            # We treat the LLM as a "Visual Graph Extractor"
            b64_image = base64.b64encode(image_bytes).decode()
            
            prompt = """
            Analyze this circuit diagram and extract all components and their connections.
            Identify:
            - Resistors (values in Ohms)
            - Voltage Sources (values in Volts)
            - Current Sources (values in Amps)
            - Nodes/Junctions (labeled 0, 1, 2...)
            
            Return ONLY a valid JSON object with this structure:
            {
              "components": [{"type": "resistor", "value": 10, "nodes": [0, 1]}, ...],
              "detected_text": "extracted raw text here",
              "topology_summary": "brief text description"
            }
            """
            
            vision_result = vision_generate(prompt=prompt, image_b64=b64_image, mime=mime_type)
            
            # Clean JSON from response
            json_match = re.search(r'\{.*\}', vision_result, re.DOTALL)
            if not json_match:
                return {"success": False, "error": "Could not parse circuit topography from image."}
            
            circuit_data = json.loads(json_match.group())
            
            # 2. Reasoning Phase: Generate step-by-step solution
            explanation_prompt = f"""
            Solve this electrical circuit step-by-step:
            {json.dumps(circuit_data, indent=2)}
            
            Use KVL (Kirchhoff's Voltage Law) or KCL (Kirchhoff's Current Law).
            Explain each node and loop.
            Provide final values for Current (I), Voltage (V) across each component.
            """
            
            solution = quick_generate(prompt=explanation_prompt, system="You are an Electrical Engineering Professor. Be precise.")
            
            return {
                "success": True,
                "data": circuit_data,
                "solution": solution
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

def get_solver_output_html(result: Dict) -> str:
    """Format the solver result into beautiful Streamlit-ready HTML."""
    if not result.get("success"):
        return f"<div style='color: #ff4b4b; padding: 10px; border-radius: 5px; background: #fee;'>❌ Error: {result.get('error')}</div>"
    
    data = result["data"]
    sol = result["solution"]
    
    components_html = "".join([
        f"<li><b>{c['type'].capitalize()}</b>: {c['value']} units between nodes {c['nodes']}</li>"
        for c in data.get("components", [])
    ])
    
    return f"""
    <div style="font-family: sans-serif; line-height: 1.6;">
        <h3 style="color: #1f77b4;">📝 Detected Components</h3>
        <ul>{components_html}</ul>
        <hr/>
        <h3 style="color: #2ca02c;">⚡ Step-by-Step Solution</h3>
        <div style="background: #f8f9fa; padding: 15px; border-left: 5px solid #2ca02c; border-radius: 5px;">
            {sol.replace('\n', '<br>')}
        </div>
    </div>
    """
