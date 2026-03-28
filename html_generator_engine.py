"""
html_generator_engine.py — AI HTML Page Generator v2.0
Creates real, production-ready websites from any content.
"""
from __future__ import annotations

HTML_SYSTEM = """\
You are an elite frontend engineer and designer who creates stunning, complete, production-ready single-file HTML pages. Every page you generate must be a REAL website anyone can use immediately.

ABSOLUTE REQUIREMENTS:
1. Complete self-contained HTML (all CSS/JS inline — no external files except CDN links)
2. Beautiful modern design: gradient backgrounds, clean typography, responsive layout
3. Semantic HTML5 with proper meta tags, Open Graph tags, and full accessibility
4. Google Fonts via @import in <style> — pick fonts that match the content
5. Smooth CSS animations and micro-interactions
6. Mobile-responsive with proper viewport settings
7. Navigation if multi-section content
8. CSS custom properties for theming
9. Content-matched color scheme
10. ZERO placeholder content — generate REAL, complete content from what the user provides
11. Include interactive elements where appropriate (tabs, accordions, modals)
12. Proper footer with relevant info
13. Working contact forms styled beautifully (even if non-functional JS stub)

DESIGN QUALITY:
- Think Stripe, Linear, Vercel landing page quality
- Glass morphism, subtle gradients, clean whitespace
- Professional typography hierarchy
- Hover states on all interactive elements
- Loading animations where appropriate
- Dark/light mode toggle if applicable

TECHNICAL:
- Chart.js for data visualizations (load from CDN if charts needed)
- Highlight.js for code blocks (load from CDN if code content)
- Intersection Observer for scroll animations
- CSS Grid + Flexbox for layouts

Output ONLY raw HTML starting with <!DOCTYPE html> — no markdown, no code fences, no explanation.
"""

PAGE_TYPES = {
    "Portfolio / Resume": "Professional portfolio with bio, skills, projects, experience, contact",
    "Landing Page": "Marketing landing with hero, features, social proof, CTA, footer",
    "Blog / Article": "Clean, highly readable article page with great typography and TOC",
    "Report / Document": "Formal report with table of contents, sections, data tables, appendix",
    "Dashboard": "Data dashboard with stats cards, charts (Chart.js), tables, sidebar",
    "Presentation / Slides": "Slide-show style with JS navigation between sections",
    "Product Page": "E-commerce product showcase with gallery, specs, reviews, CTA",
    "Event Page": "Event announcement with countdown timer, agenda, speakers, registration",
    "Notes / Study Guide": "Clean notes with collapsible sections, progress tracker, search",
    "SaaS Landing Page": "Modern SaaS page: hero, features grid, pricing table, testimonials, FAQ",
    "Restaurant / Menu": "Beautiful restaurant page with menu sections, gallery, reservations",
    "Personal Website": "Personal brand site with about, work, writing, contact",
    "Documentation": "Docs site with sidebar navigation, code blocks, search",
    "Company / Organization": "Corporate about page with team, mission, values, contact",
    "Custom (AI decides)": "AI picks best layout and design for the content provided",
}

COLOR_THEMES = {
    "Dark Cosmic (default)": "#080810",
    "Ocean Blue": "#0a1628",
    "Forest Green": "#0a1a0f",
    "Warm Sunset": "#1a0a05",
    "Clean White / Minimal": "#ffffff",
    "Slate Grey": "#1c1c2e",
    "Rose Gold": "#1a0810",
    "Purple Dreams": "#0d0720",
    "Terminal Green": "#001100",
    "Arctic Ice": "#f0f8ff",
    "Warm Paper": "#fdf6e3",
    "Deep Navy": "#0a0e1a",
}

def generate_html_page(
    content: str,
    page_type: str = "Custom (AI decides)",
    page_title: str = "My Page",
    color_theme: str = "Dark Cosmic (default)",
    include_charts: bool = False,
    extra_instructions: str = "",
    include_animations: bool = True,
    include_dark_mode: bool = False,
) -> str:

    type_desc = PAGE_TYPES.get(page_type, page_type)
    bg_color = COLOR_THEMES.get(color_theme, "#080810")
    is_dark = bg_color not in ["#ffffff", "#fdf6e3", "#f0f8ff"]

    chart_hint = ""
    if include_charts:
        chart_hint = """
CHARTS: Include interactive Chart.js visualizations. Load: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
Create appropriate chart types (bar, line, pie, doughnut, radar) for any data in the content.
Make charts beautiful with gradients, custom colors, smooth animations."""

    anim_hint = """
ANIMATIONS: Use Intersection Observer for scroll-reveal animations. Add CSS @keyframes for entrance effects.
Animate cards, stats, and sections as they enter the viewport.""" if include_animations else ""

    dark_hint = """
DARK MODE: Include a toggle button (☀️/🌙) that switches between dark/light mode using a CSS class on <html>.
Use CSS variables so the toggle works instantly.""" if include_dark_mode else ""

    prompt = f"""Create a stunning, complete, production-ready HTML page.

Page Title: {page_title}
Page Type: {page_type} — {type_desc}
Base Background: {bg_color} ({"dark" if is_dark else "light"} theme)
{chart_hint}
{anim_hint}
{dark_hint}
{f"Additional requirements: {extra_instructions}" if extra_instructions else ""}

Content to build the page from:
---
{content[:9000]}
---

Generate a COMPLETE, stunning HTML file. Make it look like it was built by a top design studio.
Include all sections appropriate for {page_type}.
Output ONLY the HTML, starting with <!DOCTYPE html>."""

    try:
        from utils.ai_engine import generate
        result = generate(
            prompt=prompt,
            system_prompt=HTML_SYSTEM,
            provider="auto",
            max_tokens=8192,
            temperature=0.7,
        )
        if not result: return _fallback_html(page_title, content[:2000])
        
        # Clean up any markdown fences
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1] if "\n" in result else result[3:]
            if result.endswith("```"):
                result = result[:-3]
        result = result.strip()
        if not result.startswith("<!DOCTYPE"):
            # Find the DOCTYPE
            idx = result.lower().find("<!doctype")
            if idx >= 0:
                result = result[idx:]
        return result
    except Exception as e:
        return _fallback_html(page_title, f"Generation error: {e}\n\n{content[:1000]}")


def generate_html_from_file(content: str, file_type: str, filename: str, page_type: str) -> str:
    """Generate HTML from an uploaded file's content."""

    file_hints = {
        "pdf": "Convert this PDF content into a beautifully formatted web document.",
        "docx": "Transform this Word document content into a polished web page.",
        "csv": "Create a beautiful data visualization page from this CSV data. Include sortable tables and charts.",
        "json": "Create a beautiful data presentation from this JSON data.",
        "md": "Convert this Markdown content into a beautifully styled web article.",
        "txt": "Format this plain text into a beautifully designed web page.",
        "xlsx": "Create a beautiful data visualization page from this spreadsheet data.",
    }
    type_desc = PAGE_TYPES.get(page_type, page_type)
    hint = file_hints.get(file_type, "Convert this content into a beautiful web page.")

    prompt = f"""Create a stunning HTML page from this {file_type.upper()} file: "{filename}"

{hint}
Page layout: {page_type} — {type_desc}

File content:
---
{content[:8000]}
---

Generate a complete, production-ready HTML file with:
- Beautiful design matching the content type
- Proper data presentation (tables, charts if data)
- Responsive layout
- Professional styling

Output ONLY the HTML starting with <!DOCTYPE html>."""

    try:
        from utils.ai_engine import generate
        result = generate(
            prompt=prompt,
            system_prompt=HTML_SYSTEM,
            provider="auto",
            max_tokens=8192,
            temperature=0.7,
        )
        if isinstance(result, tuple): result = result[0]
        result = result.strip() if result else ""
        if result.startswith("```"):
            result = result.split("\n", 1)[1] if "\n" in result else result[3:]
            if result.endswith("```"): result = result[:-3]
        return result.strip() if result.strip().startswith("<!DOCTYPE") else _fallback_html(filename, content[:2000])
    except Exception as e:
        return _fallback_html(filename, f"Error: {e}")


def _fallback_html(title: str, content: str) -> str:
    """Simple fallback HTML when AI generation fails."""
    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body{{font-family:'Segoe UI',system-ui,sans-serif;max-width:900px;margin:60px auto;padding:0 24px;background:#080810;color:#f0f0ff;line-height:1.7;}}
h1{{font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#7c6af7,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
pre{{background:#13131f;border:1px solid #1e1e30;border-radius:12px;padding:20px;overflow-x:auto;white-space:pre-wrap;}}
</style>
</head>
<body>
<h1>{title}</h1>
<pre>{safe}</pre>
</body>
</html>"""
