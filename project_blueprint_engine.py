"""
project_blueprint_engine.py — Advanced Technical Architect & Blueprinting
========================================================================
Full project structures, architectural diagrams, and implementation plans.
"""

from typing import Dict, List, Optional
from utils.ai_engine import quick_generate

class ProjectArchitect:
    """Handles professional technical architecture and project blueprints."""

    @staticmethod
    def generate_blueprint(project_name: str, tech_stack: str, description: str) -> str:
        """Main entry point for generating a full project blueprint."""
        prompt = (f"Project: {project_name}\nStack: {tech_stack}\nDescription: {description}\n\n"
                  "Provide a full file structure, architectural overview, and a phase-by-phase implementation plan.")
        # engine_name="code" gives us the Production Code Architect persona.
        return quick_generate(prompt=prompt, engine_name="code")

    @staticmethod
    def suggest_optimal_stack(requirements: str) -> str:
        """Identify the best technologies for a specific set of requirements."""
        prompt = f"Analyze these requirements and suggest the optimal, production-grade tech stack:\n{requirements}"
        return quick_generate(prompt=prompt, engine_name="code")

    @staticmethod
    def generate_architecture_diagram_code(reqs: str) -> str:
        """Generate Mermaid.js code for a system architecture diagram."""
        prompt = f"Create a complex system architecture diagram (Mermaid.js) based on these requirements:\n{reqs}"
        return quick_generate(prompt=prompt, engine_name="code")
