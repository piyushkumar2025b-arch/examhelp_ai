"""
html_generator_engine.py — Powerful AI-Powered HTML File Creator
Generates beautiful, production-ready HTML pages from any content/data.
"""
from __future__ import annotations
from typing import Optional

HTML_SYSTEM = """\
You are an elite frontend engineer and designer who generates stunning, complete, production-ready single-file HTML pages. Every page you generate must:

1. Be a COMPLETE, self-contained HTML file (no external CSS/JS files needed — all inline)
2. Use a beautiful, modern design with gradient backgrounds, clean typography, responsive layout
3. Include semantic HTML5 with proper meta tags, og tags, and accessibility
4. Use Google Fonts (loaded via @import in <style>) — pick fonts appropriate for the content
5. Have smooth CSS animations and micro-interactions where appropriate
6. Be mobile-responsive with proper viewport settings
7. Include navigation if multi-section
8. Use CSS custom properties (variables) for theming
9. Include a tasteful color scheme matching the content's purpose
10. NO placeholder content — generate REAL, complete content from what the user provides

Output ONLY the raw HTML starting with <!DOCTYPE html> — no markdown, no code blocks, no explanation.
"""

PAGE_TYPES = {
    "Portfolio / Resume":     "Professional portfolio or resume page with sections for bio, skills, projects, contact",
    "Landing Page":           "Marketing landing page with hero, features, testimonials, CTA sections",
    "Blog / Article":         "Clean, readable article or blog post page with great typography",
    "Report / Document":      "Formal report with table of contents, sections, data tables",
    "Dashboard":              "Data dashboard with cards, stats, charts (use Chart.js CDN)",
    "Presentation / Slides":  "Slide-show style presentation page with navigation between sections",
    "Product Page":           "E-commerce style product showcase page",
    "Event Page":             "Event announcement/registration page with countdown",
    "Notes / Study Guide":    "Clean notes or study guide with collapsible sections",
    "Custom (AI decides)":    "Let the AI choose the best layout and design for the content",
}

COLOR_THEMES = {
    "Dark Cosmic (default)":   "#080810",
    "Ocean Blue":              "#0a1628",
    "Forest Green":            "#0a1a0f",
    "Warm Sunset":             "#1a0a05",
    "Clean White":             "#ffffff",
    "Slate Grey":              "#1c1c2e",
    "Rose Gold":               "#1a0810",
}

def generate_html_page(
    content: str,
    page_type: str = "Custom (AI decides)",
    page_title: str = "My Page",
    color_theme: str = "Dark Cosmic (default)",
    include_charts: bool = False,
    extra_instructions: str = "",
) -> str:
    """
    Generates a complete HTML page from content using AI.
    Returns the HTML string.
    """
    from utils.groq_client import chat_with_groq

    type_desc = PAGE_TYPES.get(page_type, page_type)
    bg_color = COLOR_THEMES.get(color_theme, "#080810")

    chart_hint = ""
    if include_charts:
        chart_hint = "Include interactive charts using Chart.js (load from CDN: https://cdn.jsdelivr.net/npm/chart.js). Create appropriate visualizations for any data in the content."

    prompt = f"""\
Generate a complete, stunning HTML page.

Page Title: {page_title}
Page Type: {page_type} — {type_desc}
Base Background Color: {bg_color}
{f"Charts: {chart_hint}" if include_charts else ""}
{f"Extra instructions: {extra_instructions}" if extra_instructions else ""}

Content to include:
---
{content[:8000]}
---

Generate a COMPLETE single-file HTML page using the content above. Make it visually exceptional — this should look like a professionally designed website, not a basic HTML document. Use the content provided to fill ALL sections with real information.

Output ONLY the raw HTML starting with <!DOCTYPE html>."""

    try:
        result, success = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=HTML_SYSTEM,
            model="llama-4-scout-17b-16e-instruct",
        )
        if success and result:
            # Extract HTML if wrapped in code blocks
            import re
            match = re.search(r'<!DOCTYPE html>.*', result, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0).strip()
            return result.strip()
        return _fallback_html(page_title, content)
    except Exception as e:
        return _fallback_html(page_title, f"Error generating page: {e}\n\n{content[:2000]}")

def generate_html_from_file(
    file_content: str,
    file_type: str,
    filename: str,
    page_type: str = "Report / Document",
    **kwargs,
) -> str:
    """Generates HTML specifically from an uploaded file's content."""
    from utils.groq_client import chat_with_groq

    prompt = f"""\
Convert the following {file_type.upper()} file content into a beautiful, complete HTML page.
Original filename: {filename}
Page type requested: {page_type}

File content:
---
{file_content[:8000]}
---

Generate a complete, visually stunning single-file HTML page that presents this content beautifully.
Use appropriate layout for {file_type} content (e.g., tables for CSV/spreadsheet data, article layout for text, etc.).
Output ONLY raw HTML starting with <!DOCTYPE html>."""

    try:
        result, success = chat_with_groq(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=HTML_SYSTEM,
            model="llama-4-scout-17b-16e-instruct",
        )
        if success and result:
            import re
            match = re.search(r'<!DOCTYPE html>.*', result, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(0).strip()
            return result.strip()
    except Exception as e:
        pass
    return _fallback_html(filename, file_content[:3000])

def _fallback_html(title: str, content: str) -> str:
    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  :root {{ --bg:#080810; --text:#f0f0ff; --accent:#7c6af7; }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:var(--bg); color:var(--text); font-family:'Inter',sans-serif; padding:48px 24px; line-height:1.7; }}
  h1 {{ font-size:2rem; color:var(--accent); margin-bottom:24px; }}
  pre {{ white-space:pre-wrap; word-wrap:break-word; background:#13131f; padding:24px; border-radius:12px; border:1px solid #1e1e30; }}
</style>
</head>
<body>
<h1>{title}</h1>
<pre>{safe}</pre>
</body>
</html>"""
