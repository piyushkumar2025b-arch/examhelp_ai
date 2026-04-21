"""
ui/story_builder.py — AI Story Builder v3.0 (ExamHelp AI)
Full rewrite: genre cards, character builder, streaming, parchment UI,
PDF export, story history, ratings, continue/regenerate actions.
"""
from __future__ import annotations
import streamlit as st
import time
import random
import json
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
GENRES = [
    ("🧙", "Fantasy",           "#818cf8"),
    ("🚀", "Sci-Fi",            "#38bdf8"),
    ("👻", "Horror",            "#ef4444"),
    ("💕", "Romance",           "#f472b6"),
    ("🔍", "Mystery",           "#a78bfa"),
    ("⚔️",  "Adventure",        "#f59e0b"),
    ("🔪", "Thriller",          "#dc2626"),
    ("🏰", "Historical Fiction","#ca8a04"),
]

LENGTHS = [
    ("Short",  500,  "~2 min read"),
    ("Medium", 1500, "~7 min read"),
    ("Long",   3000, "~15 min read"),
]

TONES = ["Dark & Gritty", "Lighthearted", "Emotional", "Suspenseful", "Humorous"]
ROLES = ["Hero", "Villain", "Sidekick", "Mentor", "Love Interest", "Anti-Hero"]

SETTING_SUGGESTIONS = [
    "Medieval Europe", "Futuristic Tokyo", "Post-apocalyptic Mumbai",
    "Victorian London", "Ancient Egypt", "Space Station Omega",
    "Wild West USA", "Underwater City", "Enchanted Forest",
    "Mars Colony 2150",
]


# ─────────────────────────────────────────────────────────────────────────────
# AI HELPER
# ─────────────────────────────────────────────────────────────────────────────
def _ai_stream(prompt: str, system: str = "", max_tokens: int = 4096):
    try:
        from utils import ai_engine
        return ai_engine.generate_stream(prompt=prompt, system=system,
                                         max_tokens=max_tokens, temperature=0.85)
    except Exception as e:
        def _err():
            yield f"[AI Error: {e}]"
        return _err()


def _ai_generate(prompt: str, system: str = "", max_tokens: int = 4096) -> str:
    try:
        from utils import ai_engine
        return ai_engine.generate(prompt=prompt, system=system,
                                  max_tokens=max_tokens, temperature=0.85)
    except Exception as e:
        return f"[AI Error: {e}]"


# ─────────────────────────────────────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────────────────────────────────────
def _story_to_pdf(title: str, story: str) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors
        import io

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=2.5*cm, rightMargin=2.5*cm,
                                topMargin=2.5*cm, bottomMargin=2.5*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "title", parent=styles["Title"],
            fontSize=22, spaceAfter=6, textColor=colors.HexColor("#1a1208")
        )
        author_style = ParagraphStyle(
            "author", parent=styles["Normal"],
            fontSize=10, textColor=colors.grey, spaceAfter=20,
            alignment=1  # center
        )
        body_style = ParagraphStyle(
            "body", parent=styles["BodyText"],
            fontSize=11.5, leading=18, spaceAfter=10,
            fontName="Times-Roman"
        )
        divider_style = ParagraphStyle(
            "divider", parent=styles["Normal"],
            fontSize=14, alignment=1, spaceAfter=12, spaceBefore=12
        )
        story_clean = story.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        parts = story_clean.split("---")
        elements = [
            Paragraph(title, title_style),
            Paragraph("Author: AI Story Engine · ExamHelp AI", author_style),
        ]
        for i, part in enumerate(parts):
            if i > 0:
                elements.append(Paragraph("✦ ─── ✦ ─── ✦", divider_style))
            for para in part.strip().split("\n"):
                para = para.strip()
                if para:
                    elements.append(Paragraph(para, body_style))
                    elements.append(Spacer(1, 4))
        doc.build(elements)
        return buf.getvalue()
    except ImportError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "sb_genre":     "Fantasy",
        "sb_length":    "Medium",
        "sb_length_wc": 1500,
        "sb_tone":      "Emotional",
        "sb_setting":   "",
        "sb_twist":     False,
        "sb_custom":    "",
        "sb_chars":     [],
        "sb_story":     "",
        "sb_title":     "",
        "sb_wc":        0,
        "sb_history":   [],
        "sb_rating":    0,
        "sb_story_id":  0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def _build_story_prompt(seed: int = 0) -> tuple[str, str]:
    genre   = st.session_state.sb_genre
    wc      = st.session_state.sb_length_wc
    setting = st.session_state.sb_setting or "an unspecified world"
    tone    = st.session_state.sb_tone
    chars   = st.session_state.sb_chars
    twist   = st.session_state.sb_twist
    custom  = st.session_state.sb_custom

    chars_json = json.dumps(chars) if chars else "No specific characters defined — create your own."
    twist_line = "Include a major, unexpected plot twist in the final act that recontextualizes the story." if twist else ""
    custom_line = f"Must include this specific element: {custom}" if custom.strip() else ""
    seed_line = f"Random seed for variation: {seed}" if seed else ""

    system = (
        "You are a master storyteller and bestselling author. "
        "Write with cinematic prose, vivid sensory details, sharp dialogue, and emotional depth. "
        "Every sentence must serve the story. Never use clichés. Structure: setup → conflict → climax → resolution."
    )
    prompt = f"""Write a {wc}-word {genre} story set in {setting}.

Characters: {chars_json}
Tone: {tone}
{twist_line}
{custom_line}
{seed_line}

FORMATTING RULES:
1. First line: "TITLE: [Your creative story title]" — then a blank line
2. Use --- on its own line to mark chapter/section breaks (at least 2 breaks for medium/long stories)
3. Use vivid opening hook — grab the reader instantly
4. Every major character from the list must appear
5. End with a satisfying resolution
6. Write exactly the full {wc} words — do not stop early"""
    return prompt, system


# ─────────────────────────────────────────────────────────────────────────────
# STORY DISPLAY
# ─────────────────────────────────────────────────────────────────────────────
def _render_story_display(story: str, title: str, wc: int):
    reading_time = max(1, wc // 200)
    genre_emoji = next((e for e, g, _ in GENRES if g == st.session_state.sb_genre), "📖")

    st.markdown(f"""
<style>
.parchment-container {{
    background: #1a1208;
    border: 1px solid #8B6914;
    border-radius: 16px;
    padding: 2.5rem 3rem;
    font-family: Georgia, 'Times New Roman', serif;
    line-height: 1.9;
    font-size: 1.05rem;
    color: #e8d5a3;
    position: relative;
    box-shadow: 0 0 40px rgba(139,105,20,0.15), inset 0 0 60px rgba(0,0,0,0.3);
}}
.story-title {{
    font-size: 1.9rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(135deg, #f59e0b, #d97706, #b45309);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
    line-height: 1.3;
}}
.story-meta-bar {{
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 1.8rem;
    font-size: 0.78rem;
    color: #8B6914;
    border-bottom: 1px solid #3a2a08;
    padding-bottom: 1rem;
}}
.parchment-divider {{
    text-align: center;
    color: #8B6914;
    font-size: 1.2rem;
    margin: 1.5rem 0;
    letter-spacing: 8px;
}}
.story-badge {{
    position: absolute;
    top: 1.2rem;
    right: 1.5rem;
    background: rgba(139,105,20,0.2);
    border: 1px solid #8B6914;
    border-radius: 100px;
    padding: 4px 12px;
    font-size: .72rem;
    color: #f59e0b;
    font-family: monospace;
}}
</style>
""", unsafe_allow_html=True)

    # Split story into chapters
    parts = story.split("---")
    chapters_html = ""
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if i > 0:
            chapters_html += '<div class="parchment-divider">✦ ─── ✦ ─── ✦</div>'
        paras = part.split("\n")
        for p in paras:
            p = p.strip()
            if p:
                chapters_html += f"<p>{p}</p>"

    st.markdown(f"""
<div class="parchment-container">
  <div class="story-badge">{wc:,} words · ~{reading_time} min read</div>
  <div class="story-title">{title}</div>
  <div class="story-meta-bar">
    <span>{genre_emoji} {st.session_state.sb_genre}</span>
    <span>🎭 {st.session_state.sb_tone}</span>
    <span>🌍 {st.session_state.sb_setting or 'Unspecified'}</span>
    <span>📅 {datetime.now().strftime('%d %b %Y')}</span>
  </div>
  {chapters_html}
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ACTION BAR
# ─────────────────────────────────────────────────────────────────────────────
def _render_action_bar():
    story = st.session_state.sb_story
    title = st.session_state.sb_title
    wc    = st.session_state.sb_wc

    st.markdown("""
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
border-radius:14px;padding:16px 20px;margin-top:16px;">
  <div style="font-size:.75rem;color:#64748b;margin-bottom:10px;text-transform:uppercase;
  letter-spacing:1.5px;">Story Actions</div>
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)

    # Copy via JS
    with c1:
        if st.button("📋 Copy", use_container_width=True, key="sb_copy"):
            escaped = story.replace("`", "\\`")
            st.markdown(
                f'<script>navigator.clipboard.writeText(`{escaped}`)</script>',
                unsafe_allow_html=True
            )
            st.success("Copied!")

    # Download .txt
    with c2:
        st.download_button(
            "📥 .txt",
            data=f"{title}\n{'='*len(title)}\n\n{story}",
            file_name=f"{title[:30].replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True,
            key="sb_dl_txt"
        )

    # Download .pdf
    with c3:
        pdf_bytes = _story_to_pdf(title, story)
        if pdf_bytes:
            st.download_button(
                "📄 .pdf",
                data=pdf_bytes,
                file_name=f"{title[:30].replace(' ','_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="sb_dl_pdf"
            )
        else:
            st.caption("📄 PDF (install reportlab)")

    # Regenerate
    with c4:
        if st.button("🔄 Regenerate", use_container_width=True, key="sb_regen"):
            st.session_state.sb_trigger = "regen"
            st.rerun()

    # Continue
    with c5:
        if st.button("✏️ Continue", use_container_width=True, key="sb_continue"):
            st.session_state.sb_trigger = "continue"
            st.rerun()

    # Star rating
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**🌟 Rate this story:**")
    rating_cols = st.columns(5)
    current_rating = st.session_state.sb_rating
    for i, rc in enumerate(rating_cols, 1):
        star = "⭐" if i <= current_rating else "☆"
        if rc.button(f"{star} {i}", key=f"sb_star_{i}", use_container_width=True):
            st.session_state.sb_rating = i
            st.rerun()
    if current_rating:
        st.caption(f"Your rating: {'⭐' * current_rating} ({current_rating}/5)")


# ─────────────────────────────────────────────────────────────────────────────
# STORY HISTORY
# ─────────────────────────────────────────────────────────────────────────────
def _render_story_history():
    history = st.session_state.sb_history
    if not history:
        return
    with st.expander(f"📚 My Stories ({len(history)})", expanded=False):
        for i, s in enumerate(reversed(history)):
            col_info, col_load = st.columns([4, 1])
            with col_info:
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);'
                    f'border-radius:10px;padding:10px 14px;">'
                    f'<div style="font-weight:700;color:#f8fafc;">{s["title"]}</div>'
                    f'<div style="font-size:.75rem;color:#64748b;">'
                    f'{s["genre"]} · {s["word_count"]:,} words · {s["timestamp"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_load:
                if st.button("Load", key=f"sb_hist_load_{i}", use_container_width=True):
                    st.session_state.sb_story = s["text"]
                    st.session_state.sb_title = s["title"]
                    st.session_state.sb_wc    = s["word_count"]
                    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────
def render_story_builder():
    _init_state()

    st.markdown("""
<style>
.genre-card{background:rgba(15,23,42,0.7);border:1.5px solid rgba(255,255,255,0.07);
border-radius:14px;padding:16px 12px;text-align:center;cursor:pointer;
transition:all .2s ease;min-height:80px;}
.genre-card.selected{border-width:2px;}
.genre-card:hover{transform:translateY(-2px);}
.len-card{background:rgba(15,23,42,0.7);border:1.5px solid rgba(255,255,255,0.07);
border-radius:12px;padding:14px;text-align:center;transition:all .2s;}
.len-card.selected{border-color:#6366f1;}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(139,105,20,0.1),rgba(245,158,11,0.05));
border:1px solid rgba(139,105,20,0.25);border-radius:20px;padding:26px 30px;margin-bottom:20px;">
  <div style="font-family:monospace;font-size:10px;letter-spacing:4px;
  color:rgba(245,158,11,0.6);text-transform:uppercase;margin-bottom:8px;">AI CREATIVE ENGINE</div>
  <div style="font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:5px;">📖 Story Builder</div>
  <div style="color:rgba(255,255,255,0.4);font-size:.9rem;">
    Choose your genre, build characters, and let AI write your story
  </div>
</div>
""", unsafe_allow_html=True)

    # ── GENRE SELECTOR ────────────────────────────────────────────────────────
    st.markdown("#### 🎭 Genre")
    genre_cols = st.columns(4)
    for i, (emoji, genre, color) in enumerate(GENRES):
        is_sel = st.session_state.sb_genre == genre
        border = f"2px solid {color}" if is_sel else "1.5px solid rgba(255,255,255,0.07)"
        bg = f"{color}18" if is_sel else "rgba(15,23,42,0.7)"
        with genre_cols[i % 4]:
            if st.button(
                f"{emoji}\n**{genre}**",
                key=f"sb_genre_{genre}",
                use_container_width=True,
                help=f"Select {genre}"
            ):
                st.session_state.sb_genre = genre
                st.rerun()
            if is_sel:
                st.markdown(
                    f'<div style="height:3px;background:{color};border-radius:2px;'
                    f'margin-top:-8px;margin-bottom:4px;"></div>',
                    unsafe_allow_html=True
                )

    st.markdown("")

    # ── TWO COLUMNS: Settings left, Characters right ───────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        # Length
        st.markdown("#### 📏 Story Length")
        len_cols = st.columns(3)
        for i, (label, wc, eta) in enumerate(LENGTHS):
            is_sel = st.session_state.sb_length == label
            with len_cols[i]:
                if st.button(
                    f"**{label}**\n{wc} words\n_{eta}_",
                    key=f"sb_len_{label}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary"
                ):
                    st.session_state.sb_length    = label
                    st.session_state.sb_length_wc = wc
                    st.rerun()

        # Tone
        st.markdown("#### 🎨 Tone")
        tone_cols = st.columns(len(TONES))
        for i, tone in enumerate(TONES):
            is_sel = st.session_state.sb_tone == tone
            with tone_cols[i]:
                if st.button(
                    tone,
                    key=f"sb_tone_{tone}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary"
                ):
                    st.session_state.sb_tone = tone
                    st.rerun()

        # Setting
        st.markdown("#### 🌍 Setting")
        st.session_state.sb_setting = st.text_input(
            "Time period + Location:",
            value=st.session_state.sb_setting,
            placeholder="e.g. Futuristic Tokyo 2087",
            key="sb_setting_input",
            label_visibility="collapsed"
        )
        st.markdown("**Quick picks:**")
        sug_cols = st.columns(3)
        for i, sug in enumerate(SETTING_SUGGESTIONS[:9]):
            with sug_cols[i % 3]:
                if st.button(sug, key=f"sb_sug_{i}", use_container_width=True):
                    st.session_state.sb_setting = sug
                    st.rerun()

        # Options row
        st.markdown("#### ⚙️ Options")
        opt1, opt2 = st.columns(2)
        with opt1:
            st.session_state.sb_twist = st.toggle(
                "🌀 Surprise Plot Twist",
                value=st.session_state.sb_twist,
                key="sb_twist_toggle",
                help="AI will add a shocking twist in the final act"
            )
        with opt2:
            if st.session_state.sb_twist:
                st.info("Twist ON — AI will surprise you!")

        # Custom prompt
        st.session_state.sb_custom = st.text_area(
            "✨ Custom element to include (optional):",
            value=st.session_state.sb_custom,
            height=80,
            placeholder="e.g. A mysterious blue clock that stops time, a betrayal at the feast...",
            key="sb_custom_input"
        )

    with col_right:
        # Character builder
        st.markdown("#### 👥 Characters (up to 5)")
        chars = st.session_state.sb_chars

        with st.form("sb_char_form", clear_on_submit=True):
            c_name  = st.text_input("Name", placeholder="e.g. Aria", key="sb_cname")
            c_role  = st.selectbox("Role", ROLES, key="sb_crole")
            c_trait = st.text_input("Personality trait", placeholder="e.g. fiercely loyal", key="sb_ctrait")
            add_char = st.form_submit_button("➕ Add Character", use_container_width=True)

        if add_char and c_name.strip() and len(chars) < 5:
            chars.append({"name": c_name, "role": c_role, "trait": c_trait})
            st.session_state.sb_chars = chars
            st.rerun()

        if chars:
            for i, ch in enumerate(chars):
                c_card, c_del = st.columns([5, 1])
                with c_card:
                    st.markdown(
                        f'<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);'
                        f'border-radius:10px;padding:8px 12px;margin:3px 0;">'
                        f'<span style="font-weight:700;color:#a5b4fc;">{ch["name"]}</span> '
                        f'<span style="background:rgba(99,102,241,0.2);border-radius:100px;'
                        f'padding:1px 8px;font-size:.72rem;color:#818cf8;">{ch["role"]}</span><br>'
                        f'<span style="font-size:.78rem;color:#94a3b8;">"{ch["trait"]}"</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with c_del:
                    if st.button("🗑", key=f"sb_del_char_{i}"):
                        chars.pop(i)
                        st.session_state.sb_chars = chars
                        st.rerun()
        else:
            st.caption("No characters added — AI will create its own.")

    st.markdown("---")

    # ── GENERATE BUTTON ────────────────────────────────────────────────────────
    gen_label = "✨ Generate Story"
    if st.session_state.get("sb_trigger") == "regen":
        gen_label = "🔄 Regenerating..."
    elif st.session_state.get("sb_trigger") == "continue":
        gen_label = "✏️ Continuing Story..."

    do_generate = st.button(
        gen_label,
        type="primary",
        use_container_width=True,
        key="sb_generate_btn"
    )
    trigger = st.session_state.pop("sb_trigger", None)

    if do_generate or trigger:
        seed = random.randint(1000, 9999) if trigger == "regen" else 0

        if trigger == "continue" and st.session_state.sb_story:
            wc  = st.session_state.sb_length_wc
            prompt = (
                f"Continue this {st.session_state.sb_genre} story for another {wc} words. "
                f"Maintain all characters, tone ({st.session_state.sb_tone}), and narrative consistency.\n\n"
                f"Story so far:\n{st.session_state.sb_story[-3000:]}"
            )
            system = "You are a master storyteller continuing a story. Match the exact style, voice, and tone of the existing narrative."
        else:
            prompt, system = _build_story_prompt(seed=seed)

        # Generate with streaming
        with st.spinner("Crafting your story... ✨"):
            placeholder = st.empty()
            full_text = ""
            try:
                stream = _ai_stream(prompt, system, max_tokens=st.session_state.sb_length_wc * 5)
                for chunk in stream:
                    full_text += chunk
                    placeholder.markdown(
                        f'<div style="background:#0f172a;border:1px solid #1e293b;border-radius:10px;'
                        f'padding:16px;font-family:Georgia;line-height:1.8;color:#cbd5e1;'
                        f'max-height:300px;overflow:hidden;">{full_text[-1000:]}...</div>',
                        unsafe_allow_html=True
                    )
                placeholder.empty()
            except Exception:
                full_text = _ai_generate(prompt, system, max_tokens=st.session_state.sb_length_wc * 5)

        # Parse title
        lines = full_text.strip().split("\n")
        title = st.session_state.sb_genre + " Story"
        story_body = full_text
        if lines and lines[0].upper().startswith("TITLE:"):
            title = lines[0][6:].strip().strip('"').strip("'")
            story_body = "\n".join(lines[1:]).strip()

        if trigger == "continue":
            story_body = st.session_state.sb_story + "\n\n---\n\n" + story_body

        wc = len(story_body.split())
        st.session_state.sb_story = story_body
        st.session_state.sb_title = title
        st.session_state.sb_wc    = wc
        st.session_state.sb_rating = 0
        st.session_state.sb_story_id += 1

        # Save to history
        hist_entry = {
            "title":      title,
            "genre":      st.session_state.sb_genre,
            "word_count": wc,
            "text":       story_body,
            "timestamp":  datetime.now().strftime("%d %b %Y %H:%M"),
        }
        st.session_state.sb_history = ([hist_entry] + st.session_state.sb_history)[:5]
        st.rerun()

    # ── DISPLAY STORY ──────────────────────────────────────────────────────────
    if st.session_state.sb_story:
        _render_story_display(
            st.session_state.sb_story,
            st.session_state.sb_title,
            st.session_state.sb_wc,
        )
        _render_action_bar()

    # ── STORY HISTORY ──────────────────────────────────────────────────────────
    _render_story_history()

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="sb_back"):
        st.session_state.app_mode = "chat"
        st.rerun()
