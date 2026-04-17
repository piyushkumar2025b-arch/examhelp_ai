"""
project_blueprint_engine.py — Advanced Technical Architect & Blueprinting v2.0
Full project structures, architecture diagrams, stack recommendations,
API design, database schema, and implementation roadmaps.
"""
from __future__ import annotations
from typing import Dict, List
from utils.ai_engine import quick_generate, generate

ARCHITECT_SYSTEM = """\
You are a Principal Software Architect and Senior Engineering Lead with experience at FAANG-level companies.
Create production-grade, scalable, maintainable technical blueprints.
Your recommendations should be:
- Battle-tested and industry-proven
- Specific, not generic (name exact tools, libraries, versions where relevant)
- Structured for a team of developers to act on immediately
- Include security, scalability, and observability from day one
Use markdown with code blocks, tables, and diagrams (Mermaid.js).
"""

PROJECT_TYPES = {
    "Web App (Full Stack)":    "React/Next.js frontend + Node/Python/Go backend + database",
    "Mobile App":              "React Native / Flutter cross-platform + backend APIs",
    "REST API / Microservice": "API-first service design with OpenAPI spec",
    "Data/ML Pipeline":        "ETL pipeline, feature engineering, model training, serving",
    "DevOps / Infrastructure": "CI/CD, Kubernetes, Terraform, monitoring, GitOps",
    "SaaS Platform":           "Multi-tenant SaaS with billing, auth, analytics",
    "CLI Tool":                "Command-line application with packaging and distribution",
    "Browser Extension":       "Chrome/Firefox extension with modern Manifest v3",
    "Discord/Slack Bot":       "Chatbot/automation bot with event handling",
    "Game Development":        "Game architecture, entity systems, physics, rendering",
    "Embedded/IoT":            "Firmware, hardware interface, data telemetry",
    "Blockchain/Web3":         "Smart contracts, DeFi, NFT platforms",
}

SCALE_TARGETS = {
    "MVP / Prototype":   "Simple, fast to build — minimal infrastructure",
    "Small (< 1K users)":"Single server, simple DB, basic CI/CD",
    "Medium (10K users)":"Horizontal scaling, caching layer, proper monitoring",
    "Large (100K+ users)":"Distributed systems, CDN, database sharding, autoscaling",
    "Enterprise":        "High availability, disaster recovery, compliance, SLAs",
}


class ProjectArchitect:
    """Professional technical architecture and project blueprints."""

    @staticmethod
    def generate_blueprint(
        project_name: str,
        tech_stack: str,
        description: str,
        project_type: str = "Web App (Full Stack)",
        scale: str = "MVP / Prototype",
        team_size: int = 1,
    ) -> str:
        """Full project blueprint with file structure, architecture, and implementation plan."""
        type_desc  = PROJECT_TYPES.get(project_type, project_type)
        scale_desc = SCALE_TARGETS.get(scale, scale)
        return generate(
            prompt=f"""Create a complete technical blueprint for:

**Project**: {project_name}
**Type**: {project_type} — {type_desc}
**Stack**: {tech_stack}
**Scale Target**: {scale} — {scale_desc}
**Team Size**: {team_size} developer(s)

**Description**: {description}

DELIVERABLES:

## 1. Executive Summary (3-5 sentences)

## 2. System Architecture Overview
(Describe main components and how they interact)

```mermaid
graph TD
    [draw full architecture diagram]
```

## 3. Tech Stack Justification
| Layer | Technology | Why This Choice | Alternatives |
|-------|-----------|-----------------|-------------|

## 4. File/Folder Structure
```
project-name/
├── [complete directory tree]
```

## 5. Database Schema (if applicable)
(Key tables/collections with fields and relationships)

## 6. API Design (if applicable)
(Key endpoints: METHOD /path → description)

## 7. Phase-by-Phase Implementation Plan
| Phase | Duration | Deliverable | Priority Tasks |
|-------|---------|-------------|----------------|

## 8. Security Checklist
- [ ] Authentication method
- [ ] Authorization/RBAC
- [ ] Input validation
- [ ] Data encryption
- [ ] Rate limiting

## 9. Scalability & Performance Strategy
## 10. Monitoring & Observability
## 11. Estimated Complexity
**Overall**: Easy / Medium / Hard / Very Hard
**Estimated timeline for {team_size} dev(s)**: X weeks/months""",
            system=ARCHITECT_SYSTEM,
            engine_name="code",
            max_tokens=4000,
        ) or "Blueprint unavailable."

    @staticmethod
    def suggest_optimal_stack(
        requirements: str,
        project_type: str = "Web App (Full Stack)",
        constraints: str = "",
    ) -> str:
        """Identify the best technologies for specific requirements."""
        type_desc = PROJECT_TYPES.get(project_type, project_type)
        return generate(
            prompt=f"""Recommend the optimal tech stack for:

Project Type: {project_type} — {type_desc}
Requirements: {requirements}
{f"Constraints: {constraints}" if constraints else ""}

Provide:
## Recommended Stack (Primary)
| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|

## Key Libraries & Tools
(Specific packages to use per layer)

## Alternative Stack
(For different trade-offs — e.g., simpler, or more scalable)

## Decision Factors
(What drove these recommendations)

## Stack Comparison
| Factor | Recommended | Alternative |
|--------|-------------|-------------|
| Learning curve | | |
| Performance | | |
| Community | | |
| Hiring pool | | |
| Cost | | |

## Quick Start Commands
```bash
# How to bootstrap this stack in 5 commands
```""",
            system=ARCHITECT_SYSTEM,
            engine_name="code",
            max_tokens=2000,
        ) or "Stack recommendation unavailable."

    @staticmethod
    def generate_architecture_diagram_code(
        requirements: str,
        diagram_type: str = "System Architecture",
    ) -> str:
        """Generate Mermaid.js code for a system architecture diagram."""
        diagram_types = {
            "System Architecture": "graph TD — high-level component diagram",
            "Database ER Diagram": "erDiagram — entity-relationship model",
            "User Flow":          "flowchart LR — user journey / flow",
            "Sequence Diagram":   "sequenceDiagram — API/component interactions",
            "Class Diagram":      "classDiagram — OOP class structure",
            "State Machine":      "stateDiagram-v2 — state transitions",
            "Deployment":         "graph LR — cloud/server deployment topology",
            "Gantt / Timeline":   "gantt — project timeline and milestones",
        }
        d_desc = diagram_types.get(diagram_type, diagram_type)
        return generate(
            prompt=f"""Create a detailed {diagram_type} Mermaid.js diagram.
Type hint: {d_desc}

Requirements:
{requirements}

Rules:
- Use correct Mermaid {diagram_type.split()[0].lower()} syntax
- Be comprehensive — include ALL relevant components
- Use clear, meaningful labels
- Add comments for complex sections

Return ONLY the Mermaid code block (```mermaid ... ```)
Then below: a brief plain-English explanation of the diagram (3-5 sentences)""",
            system=ARCHITECT_SYSTEM,
            engine_name="code",
            max_tokens=2000,
        ) or "Diagram unavailable."

    @staticmethod
    def generate_api_design(
        service_name: str,
        description: str,
        auth_type: str = "JWT Bearer Token",
    ) -> str:
        """Generate a complete REST API design with OpenAPI-style spec."""
        return generate(
            prompt=f"""Design a complete REST API for: {service_name}
Description: {description}
Authentication: {auth_type}

Provide:
## API Overview
Base URL, versioning strategy, content type

## Authentication Flow
(How auth works, token lifecycle)

## Endpoints
### Resource: [Name]
| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|---------|

(cover all CRUD + special operations)

## Error Response Format
```json
{{"error": "...", "code": "...", "details": {{}}}}
```

## Rate Limits & Pagination Strategy
## Webhook Design (if applicable)
## OpenAPI/Swagger snippet for 2 key endpoints""",
            system=ARCHITECT_SYSTEM,
            engine_name="code",
            max_tokens=2500,
        ) or "API design unavailable."

    @staticmethod
    def code_review(code: str, language: str = "Python", context: str = "") -> str:
        """Professional code review with specific actionable feedback."""
        return generate(
            prompt=f"""Perform a senior engineer code review.
Language: {language}
{f"Context: {context}" if context else ""}

CODE:
```{language.lower()}
{code[:5000]}
```

Review:
## Code Quality Score: X/10
## Bugs & Issues 🐛
(Specific line numbers, exact problem, fix suggestion)

## Security Concerns 🔐
(Any injection risks, auth issues, data exposure)

## Performance Issues ⚡
(Inefficient algorithms, N+1 queries, memory leaks)

## Code Style & Best Practices
## Refactored Key Sections
```{language.lower()}
[show improved version of most important parts]
```

## Testing Recommendations
(What tests should be written for this code)""",
            system=ARCHITECT_SYSTEM,
            engine_name="code",
            max_tokens=2500,
        ) or "Code review unavailable."
