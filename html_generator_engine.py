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
    "Portfolio / Resume":    "Professional portfolio with bio, skills, projects, experience, contact",
    "Landing Page":          "Marketing landing with hero, features, social proof, CTA, footer",
    "Blog / Article":        "Clean, highly readable article page with great typography and TOC",
    "Report / Document":     "Formal report with table of contents, sections, data tables, appendix",
    "Dashboard":             "Data dashboard with stats cards, charts (Chart.js), tables, sidebar",
    "Presentation / Slides": "Slide-show style with JS navigation between sections",
    "Product Page":          "E-commerce product showcase with gallery, specs, reviews, CTA",
    "Event Page":            "Event with countdown timer, agenda, speakers, registration",
    "Notes / Study Guide":   "Clean notes with collapsible sections, progress tracker, search",
    "SaaS Landing Page":     "Modern SaaS: hero, features grid, pricing table, testimonials, FAQ",
    "Restaurant / Menu":     "Restaurant page with menu sections, gallery, reservations",
    "Personal Website":      "Personal brand site with about, work, writing, contact",
    "Documentation":         "Docs site with sidebar navigation, code blocks, search",
    "Company / Organization":"Corporate about page with team, mission, values, contact",
    "Quiz / Interactive":    "Interactive quiz or form with JS scoring and results display",
    "FAQ Page":              "Expandable accordion FAQ with search/filter functionality",
    "Invoice / Receipt":     "Professional invoice or receipt formatted for printing/PDF",
    "Email Template":        "HTML email template compatible with major email clients",
    "Custom (AI decides)":   "AI picks best layout and design for the content provided",
}

COMPONENT_LIBS = {
    "None (Pure CSS)":   "",
    "Bootstrap 5":       '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">',
    "Tailwind CDN":      '<script src="https://cdn.tailwindcss.com"></script>',
    "Bulma":             '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">',
}

COLOR_THEMES = {
    "Dark Cosmic (default)": "#080810",
    "Ocean Blue":            "#0a1628",
    "Forest Green":          "#0a1a0f",
    "Warm Sunset":           "#1a0a05",
    "Clean White / Minimal": "#ffffff",
    "Slate Grey":            "#1c1c2e",
    "Rose Gold":             "#1a0810",
    "Purple Dreams":         "#0d0720",
    "Terminal Green":        "#001100",
    "Arctic Ice":            "#f0f8ff",
    "Warm Paper":            "#fdf6e3",
    "Deep Navy":             "#0a0e1a",
    "Midnight Indigo":       "#0a0a1e",
    "Burnt Copper":          "#1a0e00",
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
    include_seo: bool = True,
    meta_description: str = "",
    component_lib: str = "None (Pure CSS)",
) -> str:

    type_desc  = PAGE_TYPES.get(page_type, page_type)
    bg_color   = COLOR_THEMES.get(color_theme, "#080810")
    is_dark    = bg_color not in ["#ffffff", "#fdf6e3", "#f0f8ff"]
    lib_tag    = COMPONENT_LIBS.get(component_lib, "")

    chart_hint = ""
    if include_charts:
        chart_hint = """
CHARTS: Load Chart.js from CDN: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
Create beautiful chart visualizations (bar, line, pie, doughnut, radar) for any data in the content.
Use gradient fills, custom colors, smooth animations."""

    anim_hint = """
ANIMATIONS: Intersection Observer for scroll-reveal. CSS @keyframes for smooth entrances.
Animate hero, cards, stats as they enter viewport. Add hover micro-interactions everywhere.""" if include_animations else ""

    dark_hint = """
DARK MODE TOGGLE: Add ☀️/🌙 button that switches via CSS class on <html>.
Use CSS variables so toggle is instant. Remember user preference in localStorage.""" if include_dark_mode else ""

    seo_hint = f"""
SEO: Include <meta name="description" content="{meta_description or page_title}">
<meta property="og:title" content="{page_title}">
<meta property="og:description" content="{meta_description or page_title}">
<meta name="twitter:card" content="summary_large_image">
Proper semantic H1 > H2 > H3 hierarchy. Alt text on all images.""" if include_seo else ""

    lib_hint = f"\nCOMPONENT LIBRARY: Use {component_lib} for UI components. CDN tag: {lib_tag}" if lib_tag else ""

    prompt = f"""Create a stunning, complete, production-ready HTML page.

Page Title: {page_title}
Page Type: {page_type} — {type_desc}
Base Background: {bg_color} ({"dark" if is_dark else "light"} theme)
{chart_hint}
{anim_hint}
{dark_hint}
{seo_hint}
{lib_hint}
{f"Additional requirements: {extra_instructions}" if extra_instructions else ""}

Content to build the page from:
---
{content[:9000]}
---

Generate a COMPLETE, stunning HTML file — think Stripe/Linear/Vercel design quality.
Include ALL sections appropriate for {page_type}.
Output ONLY the HTML, starting with <!DOCTYPE html>."""

    try:
        from utils.ai_engine import generate
        result = generate(prompt=prompt, engine_name="html_builder")
        if not result:
            return _fallback_html(page_title, content[:2000])
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1] if "\n" in result else result[3:]
            if result.endswith("```"):
                result = result[:-3]
        result = result.strip()
        if not result.startswith("<!DOCTYPE"):
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
            engine_name="html_builder"
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
    """Premium fallback HTML when AI generation fails."""
    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Rajdhani:wght@400;600;700&display=swap');
body{{font-family:'Rajdhani',system-ui,sans-serif;max-width:900px;margin:60px auto;padding:0 24px;background:#080810;color:#f0f0ff;line-height:1.7;}}
h1{{font-family:'Orbitron',monospace;font-size:2rem;font-weight:900;background:linear-gradient(135deg,#7c6af7,#a78bfa,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:24px;}}
pre{{background:#0f0f1f;border:1px solid rgba(167,139,250,0.2);border-radius:14px;padding:24px;overflow-x:auto;white-space:pre-wrap;font-size:13px;color:#c4b5fd;}}
.note{{background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);border-radius:10px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#fca5a5;}}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="note">⚠️ AI generation encountered an issue — showing raw content below.</div>
<pre>{safe}</pre>
</body>
</html>"""


def generate_component(component_type: str, description: str, theme: str = "dark") -> str:
    """Generate a standalone HTML/CSS/JS component snippet."""
    components = {
        "Navbar":         "Responsive top navigation with logo, links, hamburger menu",
        "Hero Section":   "Full-width hero with headline, subtext, CTA button, background",
        "Pricing Cards":  "3-tier pricing cards with features list and highlight",
        "Testimonials":   "Testimonial carousel with quotes, names, avatars",
        "FAQ Accordion":  "Expandable FAQ list with smooth animation",
        "Stats Counter":  "Animated number counters for key statistics",
        "Team Grid":      "Team member cards with photos, names, roles, social links",
        "Contact Form":   "Styled contact form with validation and submit handling",
        "Feature Cards":  "Icon + title + description feature grid",
        "Timeline":       "Vertical timeline of events or history",
        "Modal Dialog":   "Trigger button + modal overlay with close",
        "Toast Notification": "Slide-in notification with types (success/error/info)",
    }
    comp_desc = components.get(component_type, description)
    from utils.ai_engine import generate
    result = generate(
        prompt=f"""Create a self-contained HTML component:
Type: {component_type} — {comp_desc}
Description: {description}
Theme: {theme} mode

Return a complete code snippet with:
- HTML structure
- CSS styles (<style> block)
- JS interactions (<script> block if needed)

Make it beautiful, modern, and copy-paste ready. Output ONLY the code, no explanation.""",
        engine_name="html_builder",
        max_tokens=2000,
    )
    return result or ""
