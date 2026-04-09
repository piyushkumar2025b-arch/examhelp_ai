# ══════════════════════════════════════════════════════════════════════════════
# EXAMHELP AI v5.0 — 30-STEP UI ELEVATION & FEATURE HARDENING PROMPT
# Pure Additions Only · Zero Breakage · Production-Grade
# ══════════════════════════════════════════════════════════════════════════════
#
# INSTRUCTIONS FOR THE AI ENGINEER / CODE AGENT:
#
# Read the ENTIRE document before writing a single line of code.
# This is an ADDITIVE-ONLY specification. You are NOT refactoring, rewriting,
# or removing any existing code. You are INJECTING new CSS, NEW Python
# functions, and NEW UI blocks that layer on top of the existing `app.py`,
# `new_features.py`, `advanced_features.py`, and `utils/` files.
#
# The existing app runs. Your job is to make it visually extraordinary and
# functionally bulletproof — one surgical step at a time.
#
# GLOBAL ADDITIVE RULES:
#  A1. Never delete existing functions. Only add new ones or patch broken ones
#      with a clearly labelled `# PATCH:` comment above the change.
#  A2. All new CSS must be injected via `st.markdown("<style>…</style>",
#      unsafe_allow_html=True)` at the TOP of the relevant render function,
#      or appended inside the existing giant CSS block in `app.py`.
#  A3. All new session state keys must be added to `init_state()` in `app.py`.
#  A4. All new AI calls MUST use `utils/ai_engine.py → generate()` or
#      `generate_stream()`. Never import `google.generativeai` directly.
#  A5. Every st.button, st.text_input, st.selectbox MUST have a globally unique
#      `key=` parameter. Prefix keys with the step number: e.g. `key="s01_…"`.
#  A6. Every feature that produces AI text output MUST have a copy/download
#      button below the result. Use `st.download_button()`.
#  A7. All try/except blocks MUST show a styled error card, never a raw
#      traceback. Use: `st.error("⚠️ [Feature] failed: " + str(e))`.
#  A8. Use `st.spinner("Descriptive action verb…")` for every AI call.
#  A9. This prompt is ~1000 lines. Implement ALL 30 steps. No step is optional.
#  A10. After completing all 30 steps, append a comment block at the bottom
#       of `app.py`: `# ✅ UI ELEVATION v6.0 — 30 STEPS APPLIED`.
#
# ══════════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────────────
# STEP 01 — ANIMATED GRADIENT HERO HEADER WITH LIVE CLOCK
# File: app.py  |  Location: inside `# MAIN AREA` block, after page-header div
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# Replace the existing static `page-header` div with an upgraded version that
# includes a live clock, a pulsing "AI ACTIVE" badge, and a floating particle
# canvas behind the title text. The entire header must animate on load with a
# slide-down + fade-in entrance.

## CSS TO INJECT (add inside the existing <style> block in app.py):

```css
/* ── STEP 01: Animated Hero Header ── */
.hero-header-v2 {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg,
    rgba(15,23,42,0.95) 0%,
    rgba(30,20,60,0.95) 40%,
    rgba(15,23,42,0.95) 100%);
  border: 1px solid rgba(99,102,241,0.25);
  border-radius: 20px; padding: 32px 40px;
  margin-bottom: 24px;
  animation: heroSlideIn 0.6s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes heroSlideIn {
  from { opacity:0; transform:translateY(-20px); }
  to   { opacity:1; transform:translateY(0); }
}
.hero-header-v2::before {
  content:''; position:absolute; inset:0;
  background: radial-gradient(ellipse 60% 80% at 0% 50%,
    rgba(99,102,241,0.12) 0%, transparent 70%);
  pointer-events:none;
}
.hero-header-v2::after {
  content:''; position:absolute; top:-1px; left:10%; right:10%; height:1px;
  background: linear-gradient(90deg,
    transparent, rgba(99,102,241,0.6), rgba(139,92,246,0.6), transparent);
}
.hero-title-v2 {
  font-family:'Orbitron',monospace; font-size:clamp(22px,3.5vw,42px);
  font-weight:900; letter-spacing:2px;
  background: linear-gradient(135deg,#ffffff 0%,#a5b4fc 40%,#818cf8 70%,#c084fc 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
  filter:drop-shadow(0 0 30px rgba(99,102,241,0.4));
  margin:0; line-height:1.1;
}
.hero-sub-v2 {
  font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:300;
  color:rgba(255,255,255,0.45); letter-spacing:3px; text-transform:uppercase;
  margin-top:6px;
}
.hero-badge-active {
  display:inline-flex; align-items:center; gap:7px;
  background:rgba(34,197,94,0.1); border:1px solid rgba(34,197,94,0.3);
  border-radius:100px; padding:5px 14px;
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px; color:#4ade80;
  animation: badgePulse01 2.5s ease-in-out infinite;
}
@keyframes badgePulse01 {
  0%,100%{box-shadow:0 0 0 rgba(34,197,94,0);} 50%{box-shadow:0 0 16px rgba(34,197,94,0.25);}
}
.badge-dot-green { width:6px;height:6px;background:#4ade80;border-radius:50%;animation:blinkGreen 1.4s ease-in-out infinite; }
@keyframes blinkGreen{0%,100%{opacity:1;}50%{opacity:0.2;}}
.hero-live-clock {
  font-family:'Space Mono',monospace; font-size:12px; color:rgba(255,255,255,0.3);
  letter-spacing:2px; margin-top:14px;
}
```

## PYTHON TO ADD:
# Add this function to `app.py`, before the "MAIN AREA" section:

```python
def render_hero_header_v2():
    """STEP 01: Animated hero header with live clock badge."""
    persona = get_persona_by_name(st.session_state.selected_persona)
    persona_tag = ""
    if persona and st.session_state.selected_persona != "Default (ExamHelp)":
        persona_tag = f' · {persona["emoji"]} {persona["name"]}'

    st.markdown(f"""
    <div class="hero-header-v2">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
        <div>
          <div class="hero-title-v2">ExamHelp AI{persona_tag}</div>
          <div class="hero-sub-v2">Cognitive Force Multiplier · Enterprise v5.0.3</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;">
          <div class="hero-badge-active">
            <div class="badge-dot-green"></div>AI ACTIVE
          </div>
          <div class="hero-live-clock" id="live-clock-01">--:--:--</div>
        </div>
      </div>
    </div>
    <script>
    (function(){{
      function tick(){{
        var d=new Date();
        var t=d.toLocaleTimeString('en-US',{{hour:'2-digit',minute:'2-digit',second:'2-digit'}});
        var el=document.getElementById('live-clock-01');
        if(el) el.textContent=t;
      }}
      tick(); setInterval(tick,1000);
    }})();
    </script>
    """, unsafe_allow_html=True)
```

# Then in the MAIN AREA, replace the call to the old page-header with:
#   render_hero_header_v2()
# (Comment out the old st.markdown page-header block — do not delete it.)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 02 — SIDEBAR COLLAPSIBLE NAVIGATION GROUPS WITH ACTIVE STATE HIGHLIGHT
# File: app.py  |  Location: inside `with st.sidebar:` block
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# The sidebar currently has flat lists of buttons. Wrap each logical group
# (Study Toolbox, Exotic Power Tools, Elite Expert Engines) in a styled
# collapsible container with an active-mode glow highlight so the user can
# always see which tool they are currently in.

## CSS TO INJECT:

```css
/* ── STEP 02: Sidebar Nav Groups ── */
.nav-group-header {
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 14px; border-radius:10px; cursor:pointer;
  background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
  margin-bottom:6px; margin-top:10px;
  font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:700;
  color:rgba(255,255,255,0.7); letter-spacing:1px;
  transition:all 0.25s ease;
  user-select:none;
}
.nav-group-header:hover { background:rgba(99,102,241,0.08); border-color:rgba(99,102,241,0.25); color:#fff; }
.nav-group-count {
  font-family:'Space Mono',monospace; font-size:10px;
  background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.2);
  border-radius:100px; padding:2px 8px; color:#a5b4fc;
}
.active-tool-banner {
  display:flex; align-items:center; gap:8px;
  background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3);
  border-radius:10px; padding:9px 13px; margin-bottom:10px;
  font-family:'Rajdhani',sans-serif; font-size:12px; font-weight:700;
  color:#a5b4fc; letter-spacing:1px;
  animation:activeBannerIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes activeBannerIn {
  from{opacity:0;transform:translateX(-10px);}
  to{opacity:1;transform:translateX(0);}
}
.active-tool-dot { width:7px;height:7px;background:#818cf8;border-radius:50%;animation:blinkGreen 1.6s ease-in-out infinite; }
```

## PYTHON TO ADD:
# In the sidebar, above the Study Toolbox section, add:

```python
# STEP 02: Active tool banner
current_mode = st.session_state.get("app_mode", "chat")
mode_labels = {
    "chat": "💬 Chat Mode", "flashcards": "🃏 Flashcards",
    "quiz": "📝 Quiz Mode", "mindmap": "📊 Mind Map",
    "debugger": "🐛 Code Debugger", "essay_writer": "📄 Essay Writer",
    "interview_coach": "🎤 Interview Coach", "legal_expert": "⚖️ Legal Expert",
    "medical_expert": "🩺 Medical Guide", "math_solver": "🎯 Math Solver",
    "stocks": "💹 Stocks Dashboard", "research_pro": "🔬 Research Pro",
    "circuit_solver": "⚡ Circuit Solver", "dictionary": "📚 Dictionary",
}
mode_display = mode_labels.get(current_mode, f"⚙️ {current_mode.replace('_',' ').title()}")
st.markdown(f"""
<div class="active-tool-banner">
  <div class="active-tool-dot"></div>
  ACTIVE: {mode_display}
</div>""", unsafe_allow_html=True)
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 03 — REAL-TIME SESSION STATS MINI-DASHBOARD IN SIDEBAR
# File: app.py  |  Location: sidebar, replacing the existing stat-row block
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# Upgrade the 4-box stat row into an animated dashboard card with progress
# bars showing session intensity, context load %, and a study streak counter.

## CSS TO INJECT:

```css
/* ── STEP 03: Stats Mini Dashboard ── */
.stats-dashboard-card {
  background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.07);
  border-radius:14px; padding:14px 16px; margin:8px 0;
}
.stats-dash-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.stats-dash-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(255,255,255,0.3); text-transform:uppercase; }
.stats-dash-val { font-family:'Orbitron',monospace; font-size:16px; font-weight:700; color:#a5b4fc; }
.stats-mini-bar-wrap { margin-bottom:8px; }
.stats-mini-bar-label { display:flex; justify-content:space-between; font-family:'Rajdhani',sans-serif; font-size:11px; color:rgba(255,255,255,0.4); margin-bottom:4px; }
.stats-mini-bar { height:3px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
.stats-mini-fill { height:100%; border-radius:100px; transition:width 1s cubic-bezier(0.16,1,0.3,1); }
.fill-indigo { background:linear-gradient(90deg,#6366f1,#8b5cf6); }
.fill-cyan   { background:linear-gradient(90deg,#06b6d4,#3b82f6); }
.fill-green  { background:linear-gradient(90deg,#10b981,#06b6d4); }
```

## PYTHON TO ADD:
# Replace the existing `st.markdown(f'<div class="stat-row">…</div>')` with:

```python
def render_stats_dashboard():
    """STEP 03: Animated stats mini-dashboard."""
    msg_count = len(st.session_state.messages)
    src_count = len(st.session_state.context_sources)
    ctx_chars = len(st.session_state.context_text)
    ctx_kb = round(ctx_chars / 1024, 1)
    tok_used = st.session_state.get("total_tokens_used", 0)
    # Context load: cap at 128k chars = 100%
    ctx_pct = min(100, int((ctx_chars / 131072) * 100))
    # Session intensity: messages out of 50
    intensity_pct = min(100, int((msg_count / 50) * 100))
    # Token budget: out of 1M tokens
    token_pct = min(100, int((tok_used / 1_000_000) * 100))

    st.markdown(f"""
    <div class="stats-dashboard-card">
      <div class="stats-dash-row">
        <span class="stats-dash-label">Session Stats</span>
        <span class="stats-dash-val">{msg_count}</span>
      </div>
      <div class="stats-mini-bar-wrap">
        <div class="stats-mini-bar-label"><span>Session Intensity</span><span>{intensity_pct}%</span></div>
        <div class="stats-mini-bar"><div class="stats-mini-fill fill-indigo" style="width:{intensity_pct}%"></div></div>
      </div>
      <div class="stats-mini-bar-wrap">
        <div class="stats-mini-bar-label"><span>Context Load · {ctx_kb}KB</span><span>{ctx_pct}%</span></div>
        <div class="stats-mini-bar"><div class="stats-mini-fill fill-cyan" style="width:{ctx_pct}%"></div></div>
      </div>
      <div class="stats-mini-bar-wrap">
        <div class="stats-mini-bar-label"><span>Token Budget · {tok_used//1000}k</span><span>{token_pct}%</span></div>
        <div class="stats-mini-bar"><div class="stats-mini-fill fill-green" style="width:{token_pct}%"></div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
```

# Call `render_stats_dashboard()` in the sidebar where the old stat-row was.


# ─────────────────────────────────────────────────────────────────────────────
# STEP 04 — FLOATING AI QUICK-ACTIONS TOOLBAR (bottom-center of main area)
# File: app.py  |  Location: inject near end of MAIN AREA, before chat input
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# A slim, floating toolbar pinned near the bottom of the page with 6 one-click
# action icons: New Chat, Export, Focus Mode toggle, Mind Map, Flashcards,
# and Paste Context. The bar uses backdrop-filter and hovers above the content.

## CSS TO INJECT:

```css
/* ── STEP 04: Floating Quick-Actions Toolbar ── */
.float-toolbar {
  display:flex; align-items:center; justify-content:center; gap:6px;
  flex-wrap:wrap; margin:16px auto 8px; max-width:600px;
}
.ftb-btn {
  display:inline-flex; align-items:center; gap:7px;
  padding:8px 16px; border-radius:100px;
  background:rgba(15,23,42,0.85); border:1px solid rgba(255,255,255,0.1);
  font-family:'Rajdhani',sans-serif; font-size:12px; font-weight:700;
  color:rgba(255,255,255,0.6); letter-spacing:1px;
  backdrop-filter:blur(12px); cursor:pointer;
  transition:all 0.25s ease;
  white-space:nowrap;
}
.ftb-btn:hover { background:rgba(99,102,241,0.15); border-color:rgba(99,102,241,0.4); color:#fff; transform:translateY(-2px); }
.ftb-btn-icon { font-size:14px; }
.ftb-separator { width:1px; height:22px; background:rgba(255,255,255,0.08); margin:0 4px; }
```

## PYTHON TO ADD:

```python
def render_quick_actions_toolbar():
    """STEP 04: Floating quick-actions toolbar above the chat input."""
    st.markdown('<div class="float-toolbar">', unsafe_allow_html=True)
    cols = st.columns(6)
    actions = [
        ("🔄", "New Chat",    "s04_new_chat"),
        ("⬇️", "Export",     "s04_export"),
        ("🔒", "Focus",      "s04_focus"),
        ("📊", "Mind Map",   "s04_mindmap"),
        ("🃏", "Cards",      "s04_cards"),
        ("📄", "PDF",        "s04_context"),
    ]
    for i, (icon, label, key) in enumerate(actions):
        with cols[i]:
            if st.button(f"{icon} {label}", key=key, use_container_width=True):
                if key == "s04_new_chat":
                    st.session_state.messages = []
                    st.session_state.total_tokens_used = 0
                    st.rerun()
                elif key == "s04_focus":
                    st.session_state.focus_mode = not st.session_state.get("focus_mode", False)
                    st.rerun()
                elif key == "s04_mindmap":
                    st.session_state.app_mode = "mindmap"; st.rerun()
                elif key == "s04_cards":
                    st.session_state.app_mode = "flashcards"; st.rerun()
                elif key == "s04_context":
                    st.session_state.app_mode = "chat"
                    st.session_state["s04_show_context_panel"] = True
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
```

# Call `render_quick_actions_toolbar()` just above the chat input area in the
# chat mode block (`if app_mode == "chat":` section).


# ─────────────────────────────────────────────────────────────────────────────
# STEP 05 — PREMIUM CHAT MESSAGE BUBBLES WITH REACTIONS & COPY
# File: app.py  |  Location: inside the message rendering loop
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# Replace the raw `st.markdown(msg["content"])` renders with premium styled
# message bubbles. Each AI message gets: a glowing left-border accent, a subtle
# entrance animation, a "⭐ Rate" reaction row (👍 👎 ⭐), and a copy button.
# User messages get a right-aligned pill style with the user's avatar initial.

## CSS TO INJECT:

```css
/* ── STEP 05: Premium Chat Bubbles ── */
.msg-bubble-ai {
  position:relative; padding:18px 22px 14px;
  background:rgba(15,23,42,0.6); border:1px solid rgba(99,102,241,0.15);
  border-left:3px solid rgba(99,102,241,0.6);
  border-radius:4px 16px 16px 16px; margin-bottom:14px;
  animation:bubbleIn 0.35s cubic-bezier(0.16,1,0.3,1) both;
}
.msg-bubble-user {
  position:relative; padding:14px 20px;
  background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.2);
  border-radius:16px 4px 16px 16px; margin-bottom:14px; margin-left:10%;
  animation:bubbleIn 0.3s cubic-bezier(0.16,1,0.3,1) both;
  text-align:right;
}
@keyframes bubbleIn {
  from{opacity:0;transform:translateY(8px);}
  to{opacity:1;transform:translateY(0);}
}
.msg-header {
  display:flex; align-items:center; gap:10px; margin-bottom:10px;
}
.msg-avatar {
  width:28px; height:28px; border-radius:50%; flex-shrink:0;
  display:flex; align-items:center; justify-content:center;
  font-size:13px; font-weight:700;
}
.msg-avatar-ai { background:linear-gradient(135deg,#6366f1,#8b5cf6); color:#fff; }
.msg-avatar-user { background:linear-gradient(135deg,#0ea5e9,#6366f1); color:#fff; }
.msg-name {
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px;
  color:rgba(255,255,255,0.4); text-transform:uppercase;
}
.msg-time { font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,0.2); margin-left:auto; }
.msg-reaction-row {
  display:flex; gap:8px; margin-top:12px; padding-top:10px;
  border-top:1px solid rgba(255,255,255,0.05);
  align-items:center;
}
.msg-react-btn {
  background:none; border:1px solid rgba(255,255,255,0.08);
  border-radius:100px; padding:3px 10px; cursor:pointer;
  font-size:12px; color:rgba(255,255,255,0.35);
  transition:all 0.2s ease;
}
.msg-react-btn:hover { background:rgba(99,102,241,0.1); border-color:rgba(99,102,241,0.3); color:#fff; }
.msg-react-active { background:rgba(99,102,241,0.15)!important; border-color:rgba(99,102,241,0.4)!important; color:#a5b4fc!important; }
.msg-char-count { font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,0.15); margin-left:auto; }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 06 — SMART CONTEXT PANEL WITH DRAG-AND-DROP VISUAL SOURCE CARDS
# File: app.py  |  Location: Context tab / source display block
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# Replace the plain source chip row at the top with a proper Source Card grid.
# Each uploaded source (PDF / YouTube / Web) shows as a card with: type icon,
# truncated filename/URL, character count badge, a "Remove" button, and a
# "Summarize" one-click action that calls the AI to return a 3-sentence summary
# and caches it in `st.session_state["source_summaries"][label]`.

## CSS TO INJECT:

```css
/* ── STEP 06: Source Cards ── */
.source-card-grid { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }
.source-card {
  background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.08);
  border-radius:14px; padding:14px 16px; min-width:200px; max-width:280px;
  position:relative; transition:all 0.25s ease;
  animation:bubbleIn 0.3s cubic-bezier(0.16,1,0.3,1) both;
}
.source-card:hover { border-color:rgba(99,102,241,0.3); transform:translateY(-3px); }
.source-card-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.source-card-icon { font-size:20px; flex-shrink:0; }
.source-card-title { font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:700; color:#fff; word-break:break-all; }
.source-card-meta { font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,0.3); letter-spacing:1px; margin-top:4px; }
.source-card-badge {
  display:inline-block; padding:2px 8px; border-radius:100px;
  font-family:'Space Mono',monospace; font-size:9px; letter-spacing:1px;
  background:rgba(6,182,212,0.1); border:1px solid rgba(6,182,212,0.2); color:#22d3ee;
  margin-top:6px;
}
.source-summary-box {
  margin-top:10px; padding:10px 12px; border-radius:10px;
  background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.12);
  font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.6);
  line-height:1.6;
}
```

## PYTHON TO ADD:

```python
def render_source_cards():
    """STEP 06: Render visual source cards with summarize action."""
    if "source_summaries" not in st.session_state:
        st.session_state["source_summaries"] = {}

    sources = st.session_state.get("context_sources", [])
    if not sources:
        return

    type_icons = {"pdf": "📄", "youtube": "▶️", "web": "🌐", "ocr": "📸", "text": "📝"}
    cols = st.columns(min(len(sources), 3))

    for i, src in enumerate(sources):
        with cols[i % 3]:
            icon = type_icons.get(src.get("type", "text"), "📎")
            label = src.get("label", "Unknown")
            char_count = len(src.get("text", st.session_state.get("context_text", "")))
            st.markdown(f"""
            <div class="source-card">
              <div class="source-card-header">
                <span class="source-card-icon">{icon}</span>
                <span class="source-card-title">{label[:35]}{'…' if len(label)>35 else ''}</span>
              </div>
              <div class="source-card-meta">{src.get("type","text").upper()} SOURCE</div>
              <div class="source-card-badge">{char_count:,} chars</div>
            </div>""", unsafe_allow_html=True)

            if st.button("✨ Summarize", key=f"s06_sum_{i}", use_container_width=True):
                if label not in st.session_state["source_summaries"]:
                    ctx_snippet = st.session_state.get("context_text", "")[:4000]
                    with st.spinner("Distilling key ideas…"):
                        try:
                            from utils import ai_engine
                            summary = ai_engine.generate(
                                prompt=f"Summarize this content in exactly 3 sentences. Be academic and precise:\n\n{ctx_snippet}",
                                system="You are a research summarizer. Return exactly 3 sentences, no more.",
                                max_tokens=200
                            )
                            st.session_state["source_summaries"][label] = summary
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ Summarize failed: {e}")

            if label in st.session_state["source_summaries"]:
                st.markdown(f'<div class="source-summary-box">{st.session_state["source_summaries"][label]}</div>',
                            unsafe_allow_html=True)

            if st.button("🗑 Remove", key=f"s06_rem_{i}"):
                st.session_state.context_sources = [
                    s for j, s in enumerate(sources) if j != i
                ]
                if label in st.session_state["source_summaries"]:
                    del st.session_state["source_summaries"][label]
                if len(st.session_state.context_sources) == 0:
                    st.session_state.context_text = ""
                st.rerun()
```

# Call `render_source_cards()` at the top of the main chat area, replacing the
# existing source-chip row (`chips` / `study-banner`).


# ─────────────────────────────────────────────────────────────────────────────
# STEP 07 — TYPEWRITER STREAMING EFFECT FOR AI RESPONSES
# File: app.py  |  Location: chat message rendering + AI call block
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# When `stream_chat_with_groq()` is streaming, render the text progressively
# inside a styled `st.empty()` container that uses the `msg-bubble-ai` CSS
# class. Add a typing indicator (three-dot pulse) while waiting for first token.

## CSS TO INJECT:

```css
/* ── STEP 07: Typing Indicator ── */
.typing-indicator {
  display:inline-flex; align-items:center; gap:5px;
  padding:10px 18px; border-radius:100px;
  background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.15);
  margin-bottom:14px;
}
.typing-dot {
  width:7px; height:7px; border-radius:50%; background:#818cf8;
  animation:typingBounce 1.2s ease-in-out infinite;
}
.typing-dot:nth-child(2){animation-delay:0.2s;}
.typing-dot:nth-child(3){animation-delay:0.4s;}
@keyframes typingBounce {
  0%,80%,100%{transform:translateY(0);opacity:0.4;}
  40%{transform:translateY(-6px);opacity:1;}
}
.typing-label {
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px;
  color:rgba(255,255,255,0.35); margin-left:6px;
}
```

## PYTHON TO ADD:
# In the AI response generation block, wrap the stream with a typing indicator:

```python
def show_typing_indicator():
    """STEP 07: Show animated typing indicator while AI generates."""
    return st.markdown("""
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <span class="typing-label">AI is thinking…</span>
    </div>""", unsafe_allow_html=True)
```

# PATCH in the existing streaming response loop: Before `response_placeholder`,
# show a typing indicator placeholder, then replace it once the stream begins:
#
#   typing_ph = st.empty()
#   typing_ph.markdown(TYPING_INDICATOR_HTML, unsafe_allow_html=True)
#   # ... streaming begins ...
#   typing_ph.empty()  # clear typing indicator once first token arrives


# ─────────────────────────────────────────────────────────────────────────────
# STEP 08 — PERSONA QUICK-SWITCH CAROUSEL IN MAIN AREA
# File: app.py  |  Location: top of main chat area, below hero header
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# A horizontally scrollable row of persona avatar chips. Clicking one switches
# the persona instantly without needing the sidebar selectbox. Highlight the
# currently active persona with a glow ring. Show first 8 personas only.

## CSS TO INJECT:

```css
/* ── STEP 08: Persona Carousel ── */
.persona-carousel {
  display:flex; gap:10px; overflow-x:auto; padding:6px 2px 10px;
  scrollbar-width:none; -ms-overflow-style:none;
  margin-bottom:16px;
}
.persona-carousel::-webkit-scrollbar { display:none; }
.persona-chip-v2 {
  display:inline-flex; flex-direction:column; align-items:center;
  gap:5px; padding:10px 14px; min-width:72px;
  background:rgba(15,23,42,0.6); border:1px solid rgba(255,255,255,0.07);
  border-radius:14px; cursor:pointer; flex-shrink:0;
  transition:all 0.25s ease;
  font-family:'Rajdhani',sans-serif;
}
.persona-chip-v2:hover { border-color:rgba(99,102,241,0.35); transform:translateY(-3px); }
.persona-chip-active {
  border-color:rgba(99,102,241,0.6)!important;
  background:rgba(99,102,241,0.12)!important;
  box-shadow:0 0 20px rgba(99,102,241,0.2);
}
.persona-chip-emoji { font-size:22px; }
.persona-chip-name { font-size:10px; font-weight:700; color:rgba(255,255,255,0.5); letter-spacing:0.5px; text-align:center; }
.persona-chip-active .persona-chip-name { color:#a5b4fc; }
```

## PYTHON TO ADD:

```python
def render_persona_carousel():
    """STEP 08: Horizontal persona quick-switch carousel."""
    from utils.personas import PERSONAS, get_persona_names, get_persona_by_name
    all_names = get_persona_names()[:9]  # Show first 9
    current = st.session_state.get("selected_persona", "Default (ExamHelp)")

    chips_html = '<div class="persona-carousel">'
    for name in all_names:
        p = get_persona_by_name(name)
        if not p:
            emoji, short = "🤖", name[:8]
        else:
            emoji = p.get("emoji", "🤖")
            short = p.get("name", name)[:9]
        active_cls = "persona-chip-active" if name == current else ""
        chips_html += f"""
        <div class="persona-chip-v2 {active_cls}" title="{name}">
          <span class="persona-chip-emoji">{emoji}</span>
          <span class="persona-chip-name">{short}</span>
        </div>"""
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

    # Selectbox-based switcher (functional driver behind the visual carousel)
    selected = st.selectbox(
        "Switch persona", all_names,
        index=all_names.index(current) if current in all_names else 0,
        label_visibility="collapsed", key="s08_persona_switcher"
    )
    if selected != current:
        st.session_state.selected_persona = selected
        st.rerun()
```

# Call `render_persona_carousel()` just below `render_hero_header_v2()` in the
# main area when `app_mode == "chat"`.


# ─────────────────────────────────────────────────────────────────────────────
# STEP 09 — SMART QUICK-PROMPT SUGGESTION CHIPS
# File: app.py  |  Location: empty-state / before first message
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# When no messages exist, show a 3×3 grid of beautifully styled prompt
# suggestion chips. Each chip is color-coded by category (Exam, Coding,
# Creative, Research, Language). Clicking a chip pre-fills and immediately
# sends the prompt. Chips regenerate based on selected persona.

## CSS TO INJECT:

```css
/* ── STEP 09: Quick Prompt Grid ── */
.qprompt-section { margin:24px 0; }
.qprompt-title {
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:4px;
  color:rgba(255,255,255,0.25); text-transform:uppercase; text-align:center;
  margin-bottom:18px;
}
.qprompt-grid {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
  gap:10px;
}
.qprompt-chip {
  padding:14px 18px; border-radius:14px;
  background:rgba(15,23,42,0.7); border:1px solid var(--qc,rgba(99,102,241,0.2));
  cursor:pointer; transition:all 0.25s ease;
  display:flex; align-items:flex-start; gap:12px;
  animation:bubbleIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
}
.qprompt-chip:hover {
  background:rgba(var(--qcr,99,102,241),0.12); border-color:var(--qc,rgba(99,102,241,0.5));
  transform:translateY(-3px);
}
.qprompt-icon { font-size:18px; flex-shrink:0; margin-top:1px; }
.qprompt-text { font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:600; color:rgba(255,255,255,0.65); line-height:1.4; }
.qprompt-tag { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; color:var(--qc,#818cf8); margin-top:4px; display:block; }
```

## PYTHON TO ADD:

```python
def render_quick_prompts():
    """STEP 09: Context-aware quick prompt suggestion grid."""
    QUICK_PROMPTS = [
        ("🧪", "Explain quantum entanglement with a simple analogy", "PHYSICS",  "--qc:rgba(99,102,241,0.3)"),
        ("🐍", "Write a Python function to reverse a linked list", "CODING",   "--qc:rgba(16,185,129,0.3)"),
        ("⚖️", "Explain the Indian Constitution's Preamble in detail", "LAW",    "--qc:rgba(245,158,11,0.3)"),
        ("🧠", "What are the stages of Piaget's cognitive development?", "PSYCH", "--qc:rgba(239,68,68,0.3)"),
        ("📈", "Explain compound interest with a worked example", "FINANCE",    "--qc:rgba(6,182,212,0.3)"),
        ("🌍", "Summarize the causes of World War I", "HISTORY",              "--qc:rgba(168,85,247,0.3)"),
        ("🔬", "What is CRISPR and how does gene editing work?", "BIO",        "--qc:rgba(34,197,94,0.3)"),
        ("🎨", "Write a short story opening in the style of Kafka", "CREATIVE","--qc:rgba(251,146,60,0.3)"),
        ("🗣️", "Translate 'The early bird catches the worm' into 5 languages", "LANG", "--qc:rgba(244,63,94,0.3)"),
    ]

    st.markdown('<div class="qprompt-section">', unsafe_allow_html=True)
    st.markdown('<div class="qprompt-title">✦ Quick Start — Click to Explore ✦</div>', unsafe_allow_html=True)
    st.markdown('<div class="qprompt-grid">', unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (icon, text, tag, css_var) in enumerate(QUICK_PROMPTS):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="qprompt-chip" style="{css_var}">
              <span class="qprompt-icon">{icon}</span>
              <div>
                <div class="qprompt-text">{text}</div>
                <span class="qprompt-tag">{tag}</span>
              </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"{icon} Ask", key=f"s09_qp_{i}", use_container_width=True):
                st.session_state.queued_prompt = text
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)
```

# Render `render_quick_prompts()` in the empty-state block (`if not messages:`).


# ─────────────────────────────────────────────────────────────────────────────
# STEP 10 — ANIMATED LOADING SCREEN FOR TOOL TRANSITIONS
# File: app.py  |  Location: injected when app_mode changes
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# When the user clicks a sidebar button to switch tools, show a 0.8-second
# animated "Loading [Tool Name]…" splash with a progress bar and tool icon,
# before the new tool's render function runs. Use `st.session_state["_loading"]`
# flag to track the transition state.

## CSS TO INJECT:

```css
/* ── STEP 10: Tool Transition Loader ── */
.tool-loader {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  min-height:280px; gap:20px;
  animation:loaderIn 0.3s ease both;
}
@keyframes loaderIn{from{opacity:0;}to{opacity:1;}}
.tool-loader-icon { font-size:56px; animation:iconSpin 1s ease-in-out; }
@keyframes iconSpin{0%{transform:scale(0.5) rotate(-20deg);opacity:0;}100%{transform:scale(1) rotate(0deg);opacity:1;}}
.tool-loader-title {
  font-family:'Orbitron',monospace; font-size:18px; font-weight:700;
  letter-spacing:3px; color:rgba(255,255,255,0.7);
}
.tool-loader-bar-wrap { width:240px; height:3px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
.tool-loader-bar {
  height:100%; border-radius:100px;
  background:linear-gradient(90deg,#6366f1,#8b5cf6,#06b6d4);
  animation:loadSweep 0.7s cubic-bezier(0.4,0,0.2,1) both;
}
@keyframes loadSweep{from{width:0%;}to{width:100%;}}
```

## PYTHON TO ADD:

```python
def render_tool_loader(tool_name: str, tool_icon: str = "⚙️"):
    """STEP 10: Show animated transition loader for tool switches."""
    st.markdown(f"""
    <div class="tool-loader">
      <div class="tool-loader-icon">{tool_icon}</div>
      <div class="tool-loader-title">Loading {tool_name}</div>
      <div class="tool-loader-bar-wrap">
        <div class="tool-loader-bar"></div>
      </div>
    </div>""", unsafe_allow_html=True)
    import time; time.sleep(0.15)  # Brief render pause for animation
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 11 — CONTEXTUAL AI FOLLOW-UP SUGGESTIONS AFTER EVERY RESPONSE
# File: app.py  |  Location: after each AI message render
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# After every AI response, display 3 AI-generated follow-up suggestion chips.
# These are generated by a lightweight 50-token call asking the AI: "Given this
# response, generate 3 short follow-up questions the student might ask next.
# Return as JSON array." Cache them in `session_state["followup_cache"][msg_id]`.

## CSS TO INJECT:

```css
/* ── STEP 11: Follow-up Suggestion Chips ── */
.followup-row { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; margin-bottom:4px; }
.followup-chip {
  padding:7px 14px; border-radius:100px;
  background:rgba(15,23,42,0.7); border:1px solid rgba(99,102,241,0.2);
  font-family:'Rajdhani',sans-serif; font-size:12px; font-weight:600;
  color:rgba(165,180,252,0.8); cursor:pointer; white-space:nowrap;
  transition:all 0.2s ease;
  animation:chipFadeIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
}
.followup-chip:hover { background:rgba(99,102,241,0.15); border-color:rgba(99,102,241,0.4); color:#fff; transform:translateY(-2px); }
@keyframes chipFadeIn{from{opacity:0;transform:translateY(5px);}to{opacity:1;transform:translateY(0);}}
.followup-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(255,255,255,0.2); margin-bottom:6px; }
```

## PYTHON TO ADD:

```python
def render_followup_suggestions(msg_content: str, msg_idx: int):
    """STEP 11: Render AI-generated follow-up question chips."""
    if "followup_cache" not in st.session_state:
        st.session_state["followup_cache"] = {}

    cache_key = f"fu_{msg_idx}"
    if cache_key not in st.session_state["followup_cache"]:
        # Generate suggestions lazily (only generate for the LAST AI message)
        if msg_idx == len([m for m in st.session_state.messages if m["role"]=="assistant"]) - 1:
            try:
                from utils import ai_engine
                raw = ai_engine.generate(
                    prompt=f"This was an AI study assistant's answer:\n\n{msg_content[:800]}\n\nGenerate 3 short follow-up questions a student might ask. Return ONLY a JSON array of 3 strings, no other text.",
                    system="Return only a valid JSON array of 3 short question strings.",
                    max_tokens=120
                )
                import json, re
                match = re.search(r'\[.*?\]', raw, re.DOTALL)
                if match:
                    suggestions = json.loads(match.group(0))[:3]
                    st.session_state["followup_cache"][cache_key] = suggestions
            except Exception:
                st.session_state["followup_cache"][cache_key] = []

    suggestions = st.session_state["followup_cache"].get(cache_key, [])
    if suggestions:
        st.markdown('<div class="followup-label">ASK NEXT →</div>', unsafe_allow_html=True)
        cols = st.columns(len(suggestions))
        for i, q in enumerate(suggestions):
            with cols[i]:
                if st.button(q[:55], key=f"s11_fu_{msg_idx}_{i}", use_container_width=True):
                    st.session_state.queued_prompt = q
                    st.rerun()
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 12 — GLOBAL KEYBOARD SHORTCUT OVERLAY (? key)
# File: app.py  |  Location: inject in the main area CSS/JS block
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# Inject a JavaScript snippet that listens for the `?` key press and shows a
# styled overlay listing all keyboard shortcuts. The overlay closes on Escape
# or clicking outside. This improves power-user experience significantly.

## CSS + JS TO INJECT (via st.markdown):

```python
SHORTCUT_OVERLAY_CODE = """
<style>
.kbd-overlay {
  display:none; position:fixed; inset:0; z-index:9999;
  background:rgba(0,0,0,0.75); backdrop-filter:blur(8px);
  align-items:center; justify-content:center;
}
.kbd-overlay.visible { display:flex; animation:overlayIn 0.25s ease both; }
@keyframes overlayIn{from{opacity:0;}to{opacity:1;}}
.kbd-card {
  background:rgba(15,23,42,0.97); border:1px solid rgba(99,102,241,0.3);
  border-radius:20px; padding:32px 40px; max-width:520px; width:90%;
  box-shadow:0 40px 120px rgba(0,0,0,0.6);
}
.kbd-title { font-family:'Orbitron',monospace; font-size:16px; font-weight:700; color:#fff; letter-spacing:2px; margin-bottom:20px; }
.kbd-row { display:flex; align-items:center; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05); }
.kbd-row:last-child { border-bottom:none; }
.kbd-action { font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.6); }
.kbd-keys { display:flex; gap:5px; }
.kbd-key {
  padding:4px 10px; border-radius:6px;
  background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15);
  font-family:'Space Mono',monospace; font-size:11px; color:rgba(255,255,255,0.7);
}
.kbd-close-btn { margin-top:20px; width:100%; text-align:center; font-family:'Space Mono',monospace; font-size:10px; letter-spacing:3px; color:rgba(255,255,255,0.3); cursor:pointer; }
</style>
<div class="kbd-overlay" id="kbdOverlay">
  <div class="kbd-card">
    <div class="kbd-title">⌨️ KEYBOARD SHORTCUTS</div>
    <div class="kbd-row"><span class="kbd-action">Show shortcuts</span><div class="kbd-keys"><span class="kbd-key">?</span></div></div>
    <div class="kbd-row"><span class="kbd-action">New chat</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">K</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Focus mode toggle</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">.</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Submit message</span><div class="kbd-keys"><span class="kbd-key">Ctrl</span><span class="kbd-key">Enter</span></div></div>
    <div class="kbd-row"><span class="kbd-action">Close overlays</span><div class="kbd-keys"><span class="kbd-key">Esc</span></div></div>
    <div class="kbd-close-btn" onclick="document.getElementById('kbdOverlay').classList.remove('visible')">PRESS ESC TO CLOSE</div>
  </div>
</div>
<script>
document.addEventListener('keydown', function(e){
  if(e.key==='?' && document.activeElement.tagName!=='INPUT' && document.activeElement.tagName!=='TEXTAREA'){
    document.getElementById('kbdOverlay').classList.toggle('visible');
  }
  if(e.key==='Escape'){
    document.getElementById('kbdOverlay').classList.remove('visible');
  }
});
document.getElementById('kbdOverlay').addEventListener('click',function(e){
  if(e.target===this) this.classList.remove('visible');
});
</script>
"""
st.markdown(SHORTCUT_OVERLAY_CODE, unsafe_allow_html=True)
```

# Inject this block once at the bottom of the MAIN AREA section.


# ─────────────────────────────────────────────────────────────────────────────
# STEP 13 — UPGRADED FLASHCARD BATTLE UI WITH PROGRESS RING
# File: app.py  |  Location: flashcard rendering block (`app_mode == "flashcards"`)
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# The current flashcard UI is plain. Upgrade it with:
# 1. A circular SVG progress ring showing cards-completed / total-cards.
# 2. A card flip animation (CSS 3D perspective transform) for the front/back reveal.
# 3. Mastery color coding: Green = mastered (>2 correct), Yellow = learning, Red = struggling.
# 4. A session summary card at the end with accuracy %, time taken, and a "Save to Notes" button.

## CSS TO INJECT:

```css
/* ── STEP 13: Premium Flashcard UI ── */
.fc-container { max-width:680px; margin:0 auto; padding:16px 0; }
.fc-progress-ring-wrap {
  display:flex; align-items:center; justify-content:center; gap:20px;
  margin-bottom:24px;
}
.fc-ring-svg { transform:rotate(-90deg); }
.fc-ring-bg { fill:none; stroke:rgba(255,255,255,0.06); stroke-width:6; }
.fc-ring-fill { fill:none; stroke:url(#fcGrad); stroke-width:6; stroke-linecap:round; transition:stroke-dashoffset 0.8s cubic-bezier(0.16,1,0.3,1); }
.fc-ring-text { font-family:'Orbitron',monospace; font-size:14px; font-weight:700; fill:#a5b4fc; text-anchor:middle; dominant-baseline:middle; }
.fc-card-scene { perspective:1200px; width:100%; min-height:220px; cursor:pointer; margin-bottom:20px; }
.fc-card { width:100%; min-height:220px; position:relative; transform-style:preserve-3d; transition:transform 0.6s cubic-bezier(0.4,0,0.2,1); border-radius:20px; }
.fc-card.flipped { transform:rotateY(180deg); }
.fc-face { position:absolute; inset:0; backface-visibility:hidden; border-radius:20px; padding:32px 28px; display:flex; flex-direction:column; justify-content:center; align-items:center; text-align:center; }
.fc-front {
  background:rgba(15,23,42,0.8); border:1px solid rgba(99,102,241,0.25);
}
.fc-back {
  background:rgba(30,10,60,0.85); border:1px solid rgba(139,92,246,0.3);
  transform:rotateY(180deg);
}
.fc-q-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:4px; color:rgba(99,102,241,0.6); margin-bottom:12px; }
.fc-q-text { font-family:'Rajdhani',sans-serif; font-size:18px; font-weight:600; color:#fff; line-height:1.5; }
.fc-a-text { font-family:'Rajdhani',sans-serif; font-size:16px; color:rgba(255,255,255,0.8); line-height:1.6; }
.fc-flip-hint { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(255,255,255,0.2); margin-top:auto; padding-top:16px; }
.fc-mastery-easy { border-color:rgba(34,197,94,0.4)!important; }
.fc-mastery-hard  { border-color:rgba(239,68,68,0.4)!important; }
.fc-action-row { display:flex; gap:10px; justify-content:center; }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 14 — QUIZ MODE: ANIMATED ANSWER FEEDBACK WITH SCORE SURGE
# File: app.py  |  Location: quiz rendering block (`app_mode == "quiz"`)
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# When a quiz answer is selected:
# - Correct: Show a green glow burst + confetti-style particle effect + score +10 animation.
# - Wrong: Show a red shake animation on the wrong option + reveal correct answer with explanation.
# Both states use CSS keyframe animations. The score counter animates from old to new value.

## CSS TO INJECT:

```css
/* ── STEP 14: Quiz Feedback Animations ── */
.quiz-option {
  padding:14px 20px; border-radius:12px; cursor:pointer; margin-bottom:8px;
  background:rgba(15,23,42,0.6); border:2px solid rgba(255,255,255,0.08);
  font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:600; color:#fff;
  transition:all 0.2s ease;
}
.quiz-option:hover { border-color:rgba(99,102,241,0.35); background:rgba(99,102,241,0.08); }
.quiz-option-correct {
  border-color:rgba(34,197,94,0.7)!important; background:rgba(34,197,94,0.1)!important;
  color:#4ade80!important; animation:correctPulse 0.5s ease both;
}
@keyframes correctPulse {
  0%{transform:scale(1);}30%{transform:scale(1.03);}100%{transform:scale(1);}
}
.quiz-option-wrong {
  border-color:rgba(239,68,68,0.6)!important; background:rgba(239,68,68,0.08)!important;
  color:#f87171!important; animation:shakeWrong 0.4s ease both;
}
@keyframes shakeWrong {
  0%,100%{transform:translateX(0);}
  20%{transform:translateX(-6px);}40%{transform:translateX(6px);}60%{transform:translateX(-4px);}80%{transform:translateX(4px);}
}
.score-surge {
  display:inline-block; font-family:'Orbitron',monospace; font-size:20px; font-weight:900;
  color:#4ade80; animation:scoreSurge 0.8s cubic-bezier(0.16,1,0.3,1) both;
}
@keyframes scoreSurge {
  0%{opacity:0;transform:translateY(20px) scale(0.8);}
  60%{opacity:1;transform:translateY(-8px) scale(1.2);}
  100%{opacity:1;transform:translateY(0) scale(1);}
}
.explanation-box {
  padding:16px 20px; border-radius:12px; margin-top:14px;
  background:rgba(6,182,212,0.06); border:1px solid rgba(6,182,212,0.2);
  font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.65); line-height:1.6;
  animation:bubbleIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
}
.explanation-box strong { color:#22d3ee; }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 15 — MIND MAP: EXPORT AS PNG + INTERACTIVE NODE CLICK-TO-EXPAND
# File: app.py  |  Location: mindmap block (`app_mode == "mindmap"`)
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# The current mind map shows a Plotly graph. Add:
# 1. A "📥 Export PNG" button using `plotly.io.to_image()` → `st.download_button()`.
# 2. A text input that lets the user click on a node name and "expand" it by
#    generating 4 sub-nodes using AI and re-rendering the graph.
# 3. A toggle for "Dark nodes" vs "Light nodes" color theme.

## PYTHON TO ADD (add inside or after the existing mindmap render block):

```python
def add_mindmap_export_and_expand(fig, topic: str):
    """STEP 15: Export and expand controls for mind map."""
    col1, col2, col3 = st.columns(3)

    with col1:
        try:
            import plotly.io as pio
            img_bytes = pio.to_image(fig, format="png", width=1400, height=900, scale=2)
            st.download_button(
                "📥 Export PNG", data=img_bytes,
                file_name=f"mindmap_{topic[:20].replace(' ','_')}.png",
                mime="image/png", use_container_width=True, key="s15_export_png"
            )
        except Exception as e:
            st.caption(f"PNG export unavailable: {e}")

    with col2:
        expand_node = st.text_input(
            "Expand node", placeholder="Type a node name to expand…",
            key="s15_expand_node", label_visibility="collapsed"
        )
        if st.button("🔭 Expand Node", key="s15_expand_btn", use_container_width=True):
            if expand_node:
                with st.spinner(f"Expanding '{expand_node}'…"):
                    try:
                        from utils import ai_engine
                        raw = ai_engine.generate(
                            prompt=f"For the concept '{expand_node}' in the topic '{topic}', generate exactly 4 sub-concepts as a JSON array of strings. Return ONLY the array.",
                            system="Return only a valid JSON array of 4 short string items.",
                            max_tokens=100
                        )
                        import json, re
                        match = re.search(r'\[.*?\]', raw, re.DOTALL)
                        if match:
                            sub_nodes = json.loads(match.group(0))[:4]
                            if "mindmap_extra_nodes" not in st.session_state:
                                st.session_state["mindmap_extra_nodes"] = {}
                            st.session_state["mindmap_extra_nodes"][expand_node] = sub_nodes
                            st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Expand failed: {e}")

    with col3:
        dark_mode = st.toggle("🌙 Dark Nodes", value=True, key="s15_dark_nodes")
        st.caption("Toggle node color theme")
    return dark_mode
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 16 — STUDY PLANNER: VISUAL CALENDAR HEATMAP + AI SCHEDULE OPTIMIZER
# File: app.py  |  Location: planner block (`app_mode == "planner"`)
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# Replace the plain planner output with:
# 1. A Plotly calendar heatmap showing study hours per day (using `st.session_state["pomodoro_log"]`).
# 2. An "AI Optimize" button that takes the user's current plan text + exam date
#    and returns a rescheduled, prioritized plan using the AI.
# 3. A "Export .ics" button that generates a basic iCal file for import into
#    Google Calendar / Apple Calendar.

## CSS TO INJECT:

```css
/* ── STEP 16: Study Planner Upgrades ── */
.planner-section-label {
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:4px;
  color:rgba(255,255,255,0.3); text-transform:uppercase; margin-bottom:12px; margin-top:20px;
}
.planner-exam-badge {
  display:inline-flex; align-items:center; gap:8px;
  background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.25);
  border-radius:100px; padding:7px 16px;
  font-family:'Space Mono',monospace; font-size:11px; color:#f87171;
  letter-spacing:2px; margin-bottom:16px;
}
```

## PYTHON TO ADD:

```python
def render_planner_heatmap():
    """STEP 16: Pomodoro log calendar heatmap."""
    import datetime
    if px is None:
        st.info("Plotly required for heatmap.")
        return

    pom_log = st.session_state.get("pomodoro_log", [])
    if not pom_log:
        st.caption("📊 Study heatmap will appear after your first Pomodoro session.")
        return

    # Build date → count mapping
    date_counts = {}
    for entry in pom_log:
        if isinstance(entry, dict):
            d = entry.get("date", str(datetime.date.today()))
        else:
            d = str(datetime.date.today())
        date_counts[d] = date_counts.get(d, 0) + 1

    if pd:
        df_heat = pd.DataFrame(
            [{"date": k, "sessions": v} for k, v in date_counts.items()]
        )
        df_heat["date"] = pd.to_datetime(df_heat["date"])
        fig = px.scatter(df_heat, x="date", y="sessions", size="sessions",
                         color="sessions", color_continuous_scale="Viridis",
                         title="📅 Study Session Heatmap",
                         template="plotly_dark")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False, height=220,
            margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)


def export_ics_file(plan_text: str, exam_date) -> str:
    """STEP 16: Generate basic .ics file from planner text."""
    import datetime
    lines = plan_text.split('\n')
    events = []
    for i, line in enumerate(lines[:10]):
        if line.strip():
            event_date = exam_date - datetime.timedelta(days=10 - i)
            dtstart = event_date.strftime('%Y%m%d')
            events.append(f"""BEGIN:VEVENT
DTSTART;VALUE=DATE:{dtstart}
DTEND;VALUE=DATE:{dtstart}
SUMMARY:{line[:60].strip()}
DESCRIPTION:ExamHelp AI Study Planner
END:VEVENT""")
    ics = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//ExamHelp AI//EN\n"
    ics += "\n".join(events)
    ics += "\nEND:VCALENDAR"
    return ics
```

# In the planner app_mode block, add calls to `render_planner_heatmap()` and
# a download button for `export_ics_file(plan_text, exam_date)`.


# ─────────────────────────────────────────────────────────────────────────────
# STEP 17 — CODE DEBUGGER: SIDE-BY-SIDE DIFF VIEW + SEVERITY BADGES
# File: app.py  |  Location: debugger block (`app_mode == "debugger"`)
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# The debugger currently shows raw AI text. Add:
# 1. A structured output parser that extracts: Bug Summary, Root Cause,
#    Fixed Code, Explanation sections from the AI response.
# 2. Severity badge (CRITICAL / WARNING / INFO) auto-assigned based on keywords
#    in the error message ("exception", "crash", "null pointer" → CRITICAL, etc.)
# 3. A side-by-side diff view using Python's `difflib.HtmlDiff` rendered in
#    a scrollable `st.code()` block.
# 4. A "Copy Fixed Code" button and a "Re-run Analysis" button.

## CSS TO INJECT:

```css
/* ── STEP 17: Debugger UI ── */
.debug-severity-badge {
  display:inline-flex; align-items:center; gap:7px;
  padding:5px 14px; border-radius:100px;
  font-family:'Space Mono',monospace; font-size:10px; font-weight:700;
  letter-spacing:2px;
}
.sev-critical { background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); color:#f87171; }
.sev-warning  { background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); color:#fbbf24; }
.sev-info     { background:rgba(6,182,212,0.1);   border:1px solid rgba(6,182,212,0.25); color:#22d3ee; }
.sev-dot { width:6px; height:6px; border-radius:50%; background:currentColor; animation:blinkGreen 1.5s ease-in-out infinite; }
.debug-section-card {
  background:rgba(15,23,42,0.65); border:1px solid rgba(255,255,255,0.07);
  border-radius:14px; padding:16px 20px; margin-bottom:12px;
}
.debug-section-title {
  font-family:'Orbitron',monospace; font-size:11px; font-weight:700;
  letter-spacing:2px; color:rgba(255,255,255,0.5); margin-bottom:10px;
}
.debug-fix-card { border-left:3px solid rgba(34,197,94,0.6); }
.debug-cause-card { border-left:3px solid rgba(239,68,68,0.5); }
```

## PYTHON TO ADD:

```python
def classify_bug_severity(error_text: str) -> tuple:
    """STEP 17: Classify bug severity from error message."""
    error_lower = (error_text or "").lower()
    if any(k in error_lower for k in ["exception", "crash", "segfault", "null pointer", "fatal", "critical", "traceback"]):
        return "CRITICAL", "sev-critical"
    elif any(k in error_lower for k in ["warning", "deprecated", "warn", "undefined", "none", "attribute"]):
        return "WARNING", "sev-warning"
    else:
        return "INFO", "sev-info"


def parse_debug_response(response_text: str) -> dict:
    """STEP 17: Parse structured debugger AI response into sections."""
    import re
    sections = {"summary": "", "root_cause": "", "fixed_code": "", "explanation": ""}
    # Try to extract code blocks
    code_match = re.search(r'```[\w]*\n(.*?)```', response_text, re.DOTALL)
    if code_match:
        sections["fixed_code"] = code_match.group(1).strip()
    # Heuristic section extraction
    lines = response_text.split('\n')
    current = "summary"
    buffer = []
    for line in lines:
        l = line.lower()
        if any(kw in l for kw in ["root cause", "cause:", "problem:"]):
            sections[current] = '\n'.join(buffer).strip(); current = "root_cause"; buffer = []
        elif any(kw in l for kw in ["fixed code", "fix:", "solution:"]):
            sections[current] = '\n'.join(buffer).strip(); current = "fixed_code"; buffer = []
        elif any(kw in l for kw in ["explanation", "why:", "analysis:"]):
            sections[current] = '\n'.join(buffer).strip(); current = "explanation"; buffer = []
        else:
            buffer.append(line)
    sections[current] = '\n'.join(buffer).strip()
    if not sections["summary"]:
        sections["summary"] = response_text[:300]
    return sections


def render_debug_diff(original_code: str, fixed_code: str):
    """STEP 17: Render side-by-side diff of original vs fixed code."""
    import difflib
    if not original_code or not fixed_code:
        return
    orig_lines = original_code.splitlines(keepends=True)
    fix_lines  = fixed_code.splitlines(keepends=True)
    diff = list(difflib.unified_diff(orig_lines, fix_lines, fromfile="Original", tofile="Fixed", lineterm=""))
    if diff:
        st.markdown('<div class="debug-section-title">📊 CODE DIFF</div>', unsafe_allow_html=True)
        st.code('\n'.join(diff[:60]), language="diff")
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 18 — ESSAY WRITER: STRUCTURE VISUALIZER + WORD COUNT LIVE METER
# File: app.py (or utils/essay_engine.py)  |  Location: essay_writer app_mode
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. A live word count meter that updates as the user types in the topic/content
#    inputs. Shows target vs current word count with a colored progress bar.
# 2. An "Essay Structure" preview panel: after the AI generates the essay,
#    parse headings and show a clickable outline tree on the left with the essay
#    body on the right in a two-column layout.
# 3. A "Plagiarism Risk Score" fake-but-styled indicator (0–20 = Low, etc.)
#    based on simple heuristics (common phrases count). Make it visually clear
#    this is an approximation, not a real plagiarism check.

## CSS TO INJECT:

```css
/* ── STEP 18: Essay Writer Enhancements ── */
.essay-wc-bar-wrap { margin:8px 0 16px; }
.essay-wc-row { display:flex; justify-content:space-between; font-family:'Space Mono',monospace; font-size:10px; color:rgba(255,255,255,0.35); margin-bottom:5px; }
.essay-wc-bar { height:3px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
.essay-wc-fill { height:100%; border-radius:100px; background:linear-gradient(90deg,#6366f1,#06b6d4); transition:width 0.5s ease; }
.essay-outline-panel {
  background:rgba(15,23,42,0.6); border:1px solid rgba(99,102,241,0.15);
  border-radius:14px; padding:16px; margin-bottom:12px;
}
.essay-outline-item {
  display:flex; align-items:center; gap:8px; padding:6px 10px; border-radius:8px; cursor:pointer;
  font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.55);
  transition:all 0.2s ease;
}
.essay-outline-item:hover { background:rgba(99,102,241,0.08); color:#fff; }
.essay-outline-dot { width:6px; height:6px; background:#6366f1; border-radius:50%; flex-shrink:0; }
.plag-badge {
  display:inline-flex; align-items:center; gap:8px; padding:8px 16px; border-radius:100px;
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:2px;
}
.plag-low  { background:rgba(34,197,94,0.1);  border:1px solid rgba(34,197,94,0.25);  color:#4ade80; }
.plag-med  { background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.25); color:#fbbf24; }
.plag-high { background:rgba(239,68,68,0.1);  border:1px solid rgba(239,68,68,0.25);  color:#f87171; }
```

## PYTHON TO ADD:

```python
def estimate_plagiarism_risk(text: str) -> tuple:
    """STEP 18: Heuristic plagiarism risk estimation."""
    COMMON_PHRASES = ["in conclusion", "it is important to", "in today's world",
                      "throughout history", "in summary", "it can be seen that",
                      "furthermore", "additionally", "as a result", "for instance"]
    count = sum(1 for p in COMMON_PHRASES if p in text.lower())
    if count <= 2:
        return "LOW RISK", "plag-low", count
    elif count <= 5:
        return "MODERATE", "plag-med", count
    else:
        return "HIGH RISK", "plag-high", count


def render_essay_outline(essay_text: str):
    """STEP 18: Extract and display essay structure outline."""
    import re
    headings = re.findall(r'^#{1,3}\s+(.+)$', essay_text, re.MULTILINE)
    # Also catch bold section titles
    bold_titles = re.findall(r'^\*\*(.+)\*\*$', essay_text, re.MULTILINE)
    all_sections = headings + bold_titles

    if not all_sections:
        return

    st.markdown('<div class="essay-outline-panel">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Space Mono\',monospace;font-size:9px;letter-spacing:3px;color:rgba(255,255,255,0.3);margin-bottom:10px;">ESSAY STRUCTURE</div>', unsafe_allow_html=True)
    for section in all_sections[:8]:
        st.markdown(f'<div class="essay-outline-item"><div class="essay-outline-dot"></div>{section}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 19 — INTERVIEW COACH: REAL-TIME CONFIDENCE METER + ANSWER SCORECARD
# File: app.py (or utils/interview_engine.py)  |  Location: interview_coach mode
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. After the user submits an interview answer, show a scorecard with 4 axes:
#    Clarity, Relevance, STAR Structure, Confidence Level — each as a 0–10
#    score extracted from the AI's feedback JSON.
# 2. A radar chart (Plotly polar) visualizing the 4 scores.
# 3. A "Coach's Tip" highlight box with the single most actionable improvement.
# 4. A session history panel showing all Q&A pairs with their scores in a
#    collapsible expander.

## CSS TO INJECT:

```css
/* ── STEP 19: Interview Coach Scorecard ── */
.scorecard-grid {
  display:grid; grid-template-columns:repeat(2,1fr); gap:12px; margin-bottom:16px;
}
.score-cell {
  padding:16px 18px; border-radius:14px;
  background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.07);
  text-align:center;
}
.score-val { font-family:'Orbitron',monospace; font-size:28px; font-weight:900; line-height:1; margin-bottom:4px; }
.score-dim { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(255,255,255,0.3); text-transform:uppercase; }
.score-high { background:linear-gradient(135deg,#10b981,#059669); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.score-mid  { background:linear-gradient(135deg,#f59e0b,#d97706); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.score-low  { background:linear-gradient(135deg,#ef4444,#dc2626); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.coach-tip-box {
  padding:16px 20px; border-radius:12px; margin-bottom:16px;
  background:rgba(251,146,60,0.06); border:1px solid rgba(251,146,60,0.2);
  border-left:3px solid rgba(251,146,60,0.6);
}
.coach-tip-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(251,146,60,0.7); margin-bottom:8px; }
.coach-tip-text { font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.7); line-height:1.6; }
```

## PYTHON TO ADD:

```python
def render_interview_scorecard(scores: dict, tip: str):
    """STEP 19: Render interview answer scorecard with radar chart."""
    dims = ["Clarity", "Relevance", "STAR Structure", "Confidence"]
    vals = [scores.get(d.lower().replace(" ","_"), 5) for d in dims]

    st.markdown('<div class="scorecard-grid">', unsafe_allow_html=True)
    for dim, val in zip(dims, vals):
        cls = "score-high" if val >= 8 else ("score-mid" if val >= 5 else "score-low")
        st.markdown(f"""
        <div class="score-cell">
          <div class="score-val {cls}">{val}</div>
          <div class="score-dim">{dim}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if tip:
        st.markdown(f"""
        <div class="coach-tip-box">
          <div class="coach-tip-label">🔥 COACH'S TOP TIP</div>
          <div class="coach-tip-text">{tip}</div>
        </div>""", unsafe_allow_html=True)

    if px:
        import plotly.graph_objects as go_local
        fig = go_local.Figure(go_local.Scatterpolar(
            r=vals + [vals[0]],
            theta=dims + [dims[0]],
            fill='toself',
            fillcolor='rgba(99,102,241,0.15)',
            line=dict(color='rgba(99,102,241,0.7)', width=2),
        ))
        fig.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, range=[0,10], color='rgba(255,255,255,0.2)', showticklabels=False),
                angularaxis=dict(color='rgba(255,255,255,0.4)', tickfont=dict(size=11, color='rgba(255,255,255,0.5)'))
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            height=260,
            margin=dict(l=40,r=40,t=20,b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 20 — LEGAL EXPERT: IRAC STRUCTURE RENDERER + JURISDICTION BADGE
# File: new_features.py  |  Location: `render_legal_expert()` function
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# The legal expert outputs plain text. Add:
# 1. A structured IRAC renderer that color-codes the 4 sections (Issue = red,
#    Rule = blue, Application = purple, Conclusion = green).
# 2. A jurisdiction badge (India / UK / US / EU) selected by a flag-emoji radio.
# 3. A "Save to Case File" button that appends the analysis to
#    `st.session_state["legal_case_files"]` list with timestamp.
# 4. A PDF download button for the formatted IRAC analysis.

## CSS TO INJECT (in new_features.py render function):

```css
/* ── STEP 20: Legal IRAC Renderer ── */
.irac-section {
  padding:16px 20px; border-radius:12px; margin-bottom:10px;
  position:relative; overflow:hidden;
}
.irac-section::before {
  content:var(--irac-label); position:absolute; top:12px; right:14px;
  font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px;
  color:var(--irac-color); opacity:0.5; text-transform:uppercase;
}
.irac-I { background:rgba(239,68,68,0.07);  border:1px solid rgba(239,68,68,0.2);  --irac-color:#f87171; --irac-label:'ISSUE'; }
.irac-R { background:rgba(59,130,246,0.07); border:1px solid rgba(59,130,246,0.2); --irac-color:#60a5fa; --irac-label:'RULE'; }
.irac-A { background:rgba(139,92,246,0.07); border:1px solid rgba(139,92,246,0.2); --irac-color:#a78bfa; --irac-label:'APPLICATION'; }
.irac-C { background:rgba(34,197,94,0.07);  border:1px solid rgba(34,197,94,0.2);  --irac-color:#4ade80; --irac-label:'CONCLUSION'; }
.irac-header { font-family:'Orbitron',monospace; font-size:12px; font-weight:700; letter-spacing:2px; margin-bottom:8px; }
.irac-I .irac-header { color:#f87171; }
.irac-R .irac-header { color:#60a5fa; }
.irac-A .irac-header { color:#a78bfa; }
.irac-C .irac-header { color:#4ade80; }
.irac-body { font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.65); line-height:1.7; }
.jurisdiction-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
.juris-chip {
  padding:7px 16px; border-radius:100px; cursor:pointer;
  background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.1);
  font-family:'Rajdhani',sans-serif; font-size:13px; font-weight:700;
  color:rgba(255,255,255,0.5); transition:all 0.2s ease;
}
.juris-chip:hover,.juris-active { background:rgba(99,102,241,0.12)!important; border-color:rgba(99,102,241,0.4)!important; color:#fff!important; }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 21 — MEDICAL EXPERT: CLINICAL SEVERITY INDICATOR + SYMPTOM CHECKLIST
# File: new_features.py  |  Location: `render_medical_expert()` function
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. Before the AI response, show a non-dismissible safety banner (already
#    partially there — ensure it's always visible and styled correctly).
# 2. An interactive "Symptom Checklist" with 8 common symptoms as checkboxes.
#    Selected symptoms are appended to the AI prompt automatically.
# 3. A severity indicator (color-coded scale 1–5) extracted from AI output
#    keywords: "mild" = 1–2, "moderate" = 3, "severe"/"critical" = 4–5.
# 4. An "ICD-11 Code" extraction that looks for ICD codes in the AI response
#    and renders them as styled chips.

## CSS TO INJECT:

```css
/* ── STEP 21: Medical Expert Upgrades ── */
.med-safety-banner {
  padding:14px 20px; border-radius:12px; margin-bottom:20px;
  background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.3);
  border-left:4px solid #ef4444;
  display:flex; align-items:flex-start; gap:12px;
}
.med-safety-icon { font-size:22px; flex-shrink:0; }
.med-safety-text { font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.6); line-height:1.6; }
.med-safety-text strong { color:#f87171; }
.severity-bar-wrap { margin:12px 0 20px; }
.severity-label-row { display:flex; justify-content:space-between; font-family:'Space Mono',monospace; font-size:9px; color:rgba(255,255,255,0.3); margin-bottom:6px; }
.severity-bar { height:6px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
.severity-fill {
  height:100%; border-radius:100px;
  background:linear-gradient(90deg,#10b981,#f59e0b,#ef4444);
  transition:width 1s cubic-bezier(0.16,1,0.3,1);
}
.icd-chip {
  display:inline-block; padding:4px 12px; border-radius:100px; margin:3px;
  background:rgba(6,182,212,0.1); border:1px solid rgba(6,182,212,0.25);
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:1px; color:#22d3ee;
}
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 22 — RESEARCH PRO: CITATION CARD GRID + SOURCE CREDIBILITY BADGES
# File: new_features.py  |  Location: `render_research_pro()` function
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. Parse the AI research output for citation-like patterns (Author, Year, Title)
#    and render each as a styled Citation Card with copy button.
# 2. Add a "Source Credibility" badge system: .edu/.gov domains get "HIGH
#    CREDIBILITY" green badge, .org gets "MODERATE" yellow, others get "UNVERIFIED".
# 3. Add an "Export as BibTeX" button that converts extracted citations to
#    a `.bib` file format for download.
# 4. Add a "Related Questions" panel generated by a second lightweight AI call.

## CSS TO INJECT:

```css
/* ── STEP 22: Research Pro Citation Cards ── */
.citation-card {
  padding:16px 18px; border-radius:14px; margin-bottom:10px;
  background:rgba(15,23,42,0.65); border:1px solid rgba(255,255,255,0.07);
  position:relative; transition:all 0.25s ease;
}
.citation-card:hover { border-color:rgba(99,102,241,0.3); transform:translateX(4px); }
.citation-number {
  position:absolute; top:-10px; left:16px;
  width:22px; height:22px; border-radius:50%;
  background:linear-gradient(135deg,#6366f1,#8b5cf6);
  display:flex; align-items:center; justify-content:center;
  font-family:'Space Mono',monospace; font-size:9px; font-weight:700; color:#fff;
}
.citation-title { font-family:'Rajdhani',sans-serif; font-size:14px; font-weight:700; color:#fff; margin-bottom:4px; }
.citation-meta  { font-family:'Space Mono',monospace; font-size:10px; color:rgba(255,255,255,0.35); letter-spacing:1px; }
.cred-high { background:rgba(34,197,94,0.1);  border:1px solid rgba(34,197,94,0.25);  color:#4ade80; }
.cred-med  { background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.25); color:#fbbf24; }
.cred-low  { background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:rgba(255,255,255,0.35); }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 23 — STOCKS DASHBOARD: SENTIMENT GAUGE + PRICE SPARKLINE CARDS
# File: new_features.py  |  Location: `render_stocks_dashboard()` function
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. A circular sentiment gauge SVG that shows BEARISH ← → BULLISH on a
#    180-degree arc, with a needle that animates to position based on AI
#    sentiment analysis score (-1.0 to 1.0).
# 2. Sparkline mini-charts for each ticker using Plotly's `go.Scatter` with
#    area fill in a compact 80px height card.
# 3. Color-coded change badges: green for positive, red for negative with
#    animated count-up numbers.
# 4. A "Fear & Greed" composite score displayed as a large donut chart.

## CSS TO INJECT:

```css
/* ── STEP 23: Stocks Dashboard Cards ── */
.ticker-card {
  padding:16px 18px; border-radius:14px;
  background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.07);
  transition:all 0.25s ease; position:relative; overflow:hidden;
}
.ticker-card:hover { transform:translateY(-4px); border-color:rgba(99,102,241,0.3); }
.ticker-symbol { font-family:'Orbitron',monospace; font-size:16px; font-weight:700; color:#fff; }
.ticker-price  { font-family:'Space Mono',monospace; font-size:24px; font-weight:700; color:#a5b4fc; }
.ticker-change-pos { color:#4ade80; font-family:'Space Mono',monospace; font-size:13px; font-weight:700; }
.ticker-change-neg { color:#f87171; font-family:'Space Mono',monospace; font-size:13px; font-weight:700; }
.sentiment-gauge-wrap { text-align:center; margin:16px 0; }
.sentiment-gauge-label { font-family:'Orbitron',monospace; font-size:12px; font-weight:700; letter-spacing:3px; margin-top:8px; }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 24 — GLOBAL TOAST NOTIFICATION SYSTEM
# File: app.py  |  Location: inject once in main area CSS/JS
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# A JavaScript-powered toast notification system. Python functions can call
# `show_toast(message, type)` which injects a JS trigger. Toasts appear at the
# top-right, auto-dismiss after 3 seconds, and have slide-in/fade-out animation.
# Types: "success" (green), "error" (red), "info" (blue), "warning" (yellow).

## CSS + JS TO INJECT:

```python
TOAST_SYSTEM_CODE = """
<style>
#toast-container {
  position:fixed; top:24px; right:24px; z-index:99999;
  display:flex; flex-direction:column; gap:10px; pointer-events:none;
}
.toast-item {
  display:flex; align-items:center; gap:12px;
  padding:13px 18px; border-radius:12px; min-width:260px;
  backdrop-filter:blur(16px); pointer-events:all;
  animation:toastIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
  font-family:'Rajdhani',sans-serif; font-size:14px; font-weight:600;
  box-shadow:0 8px 40px rgba(0,0,0,0.4);
}
.toast-success { background:rgba(10,40,20,0.92); border:1px solid rgba(34,197,94,0.35); color:#4ade80; }
.toast-error   { background:rgba(40,10,10,0.92); border:1px solid rgba(239,68,68,0.35);  color:#f87171; }
.toast-info    { background:rgba(10,20,50,0.92); border:1px solid rgba(99,102,241,0.35); color:#a5b4fc; }
.toast-warning { background:rgba(40,30,0,0.92);  border:1px solid rgba(245,158,11,0.35); color:#fbbf24; }
.toast-icon { font-size:16px; flex-shrink:0; }
.toast-hide { animation:toastOut 0.3s ease both; }
@keyframes toastIn  { from{opacity:0;transform:translateX(40px);} to{opacity:1;transform:translateX(0);} }
@keyframes toastOut { from{opacity:1;transform:translateX(0);} to{opacity:0;transform:translateX(40px);} }
</style>
<div id="toast-container"></div>
<script>
window.showToast = function(msg, type='info', duration=3200) {
  const icons = {success:'✅',error:'❌',info:'ℹ️',warning:'⚠️'};
  const c = document.getElementById('toast-container');
  if(!c) return;
  const t = document.createElement('div');
  t.className = `toast-item toast-${type}`;
  t.innerHTML = `<span class="toast-icon">${icons[type]||'ℹ️'}</span><span>${msg}</span>`;
  c.appendChild(t);
  setTimeout(()=>{ t.classList.add('toast-hide'); setTimeout(()=>t.remove(), 350); }, duration);
};
</script>
"""
st.markdown(TOAST_SYSTEM_CODE, unsafe_allow_html=True)
```

# To trigger a toast from Python (after an action):
#   st.markdown('<script>window.showToast("✅ Analysis complete!","success");</script>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 25 — POMODORO TIMER: VISUAL RING COUNTDOWN + SESSION ANALYTICS
# File: advanced_features.py  |  Location: Pomodoro render function
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. Replace text-only timer with an animated SVG ring countdown that visually
#    depletes as time passes. Stroke-dashoffset animates via JavaScript.
# 2. Break vs work mode shows different ring colors (indigo for work, teal for break).
# 3. After each completed session, auto-append to `st.session_state["pomodoro_log"]`
#    with `{"date": today, "duration": 25, "subject": topic_input}`.
# 4. Show a compact "Today's Sessions" bar chart (Plotly) below the timer.

## CSS TO INJECT:

```css
/* ── STEP 25: Pomodoro Ring Timer ── */
.pomo-timer-wrap { display:flex; flex-direction:column; align-items:center; gap:16px; padding:24px 0; }
.pomo-ring-svg { transform:rotate(-90deg); filter:drop-shadow(0 0 16px rgba(99,102,241,0.3)); }
.pomo-ring-bg   { fill:none; stroke:rgba(255,255,255,0.05); stroke-width:8; }
.pomo-ring-fill { fill:none; stroke:url(#pomoGrad); stroke-width:8; stroke-linecap:round; transition:stroke-dashoffset 1s linear; }
.pomo-time-label { font-family:'Orbitron',monospace; font-size:36px; font-weight:900; color:#fff; letter-spacing:4px; }
.pomo-state-label { font-family:'Space Mono',monospace; font-size:10px; letter-spacing:4px; color:rgba(255,255,255,0.4); text-transform:uppercase; }
.pomo-controls { display:flex; gap:12px; }
.pomo-sessions-row { display:flex; gap:8px; margin-top:8px; flex-wrap:wrap; justify-content:center; }
.pomo-session-dot { width:12px; height:12px; border-radius:3px; }
.pomo-done { background:linear-gradient(135deg,#6366f1,#8b5cf6); }
.pomo-pending { background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.1); }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 26 — GLOBAL SEARCH COMMAND PALETTE (Ctrl+K)
# File: app.py  |  Location: inject once in main CSS/JS block
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# A command palette overlay (like VS Code's Ctrl+K) that opens on Ctrl+K.
# It shows a search input and lists all 33 tools/modes. Typing filters the list.
# Clicking a result sets `app_mode` via a hidden Streamlit button (JS click trick).
# The overlay closes on Escape or clicking outside.

## CSS + JS TO INJECT:

```python
COMMAND_PALETTE_CODE = """
<style>
.cmd-overlay {
  display:none; position:fixed; inset:0; z-index:99998;
  background:rgba(0,0,0,0.7); backdrop-filter:blur(8px);
  align-items:flex-start; justify-content:center;
  padding-top:120px;
}
.cmd-overlay.visible { display:flex; animation:overlayIn 0.2s ease both; }
.cmd-palette {
  width:100%; max-width:600px; background:rgba(10,15,30,0.98);
  border:1px solid rgba(99,102,241,0.3); border-radius:18px;
  overflow:hidden; box-shadow:0 40px 120px rgba(0,0,0,0.7);
}
.cmd-input-wrap {
  display:flex; align-items:center; gap:12px; padding:16px 20px;
  border-bottom:1px solid rgba(255,255,255,0.07);
}
.cmd-search-icon { font-size:18px; color:rgba(255,255,255,0.3); }
.cmd-input {
  flex:1; background:none; border:none; outline:none;
  font-family:'Rajdhani',sans-serif; font-size:16px; font-weight:600;
  color:#fff; placeholder-color:rgba(255,255,255,0.3);
}
.cmd-list { max-height:380px; overflow-y:auto; padding:8px; }
.cmd-item {
  display:flex; align-items:center; gap:12px; padding:11px 14px;
  border-radius:10px; cursor:pointer;
  font-family:'Rajdhani',sans-serif; font-size:14px; font-weight:600;
  color:rgba(255,255,255,0.6); transition:all 0.15s ease;
}
.cmd-item:hover,.cmd-item.selected { background:rgba(99,102,241,0.12); color:#fff; }
.cmd-item-icon { font-size:16px; width:24px; text-align:center; flex-shrink:0; }
.cmd-item-cat  { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; color:rgba(99,102,241,0.5); margin-left:auto; }
.cmd-footer { padding:10px 20px; border-top:1px solid rgba(255,255,255,0.05); display:flex; gap:16px; }
.cmd-hint { font-family:'Space Mono',monospace; font-size:10px; color:rgba(255,255,255,0.2); display:flex; align-items:center; gap:6px; }
.cmd-key { padding:2px 7px; border-radius:4px; background:rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.12); }
</style>
<div class="cmd-overlay" id="cmdOverlay">
  <div class="cmd-palette">
    <div class="cmd-input-wrap">
      <span class="cmd-search-icon">⌕</span>
      <input class="cmd-input" id="cmdInput" placeholder="Search tools and features…" autocomplete="off" spellcheck="false"/>
    </div>
    <div class="cmd-list" id="cmdList"></div>
    <div class="cmd-footer">
      <span class="cmd-hint"><span class="cmd-key">↑↓</span> navigate</span>
      <span class="cmd-hint"><span class="cmd-key">Enter</span> select</span>
      <span class="cmd-hint"><span class="cmd-key">Esc</span> close</span>
    </div>
  </div>
</div>
<script>
var CMD_ITEMS = [
  {icon:'💬',label:'Chat Mode',cat:'CORE',mode:'chat'},
  {icon:'🃏',label:'Flashcards',cat:'STUDY',mode:'flashcards'},
  {icon:'📝',label:'Quiz Mode',cat:'STUDY',mode:'quiz'},
  {icon:'📊',label:'Mind Map',cat:'STUDY',mode:'mindmap'},
  {icon:'📅',label:'Study Planner',cat:'STUDY',mode:'planner'},
  {icon:'🐛',label:'Code Debugger',cat:'CODE',mode:'debugger'},
  {icon:'🎓',label:'Learn Coding',cat:'CODE',mode:'learn_coding'},
  {icon:'🔀',label:'Code Converter',cat:'CODE',mode:'code_converter'},
  {icon:'📄',label:'Essay Writer',cat:'WRITING',mode:'essay_writer'},
  {icon:'🎤',label:'Interview Coach',cat:'CAREER',mode:'interview_coach'},
  {icon:'⚖️',label:'Legal Expert',cat:'EXPERT',mode:'legal_expert'},
  {icon:'🩺',label:'Medical Guide',cat:'EXPERT',mode:'medical_expert'},
  {icon:'💹',label:'Stocks Dashboard',cat:'FINANCE',mode:'stocks'},
  {icon:'🎯',label:'Math Solver',cat:'STEM',mode:'math_solver'},
  {icon:'⚡',label:'Circuit Solver',cat:'STEM',mode:'circuit_solver'},
  {icon:'🔬',label:'Research Pro',cat:'RESEARCH',mode:'research_pro'},
  {icon:'📚',label:'AI Dictionary',cat:'LANGUAGE',mode:'dictionary'},
  {icon:'🌍',label:'Language Tools',cat:'LANGUAGE',mode:'language_tools'},
  {icon:'📈',label:'Graph Plotter',cat:'VISUAL',mode:'graph'},
  {icon:'🎯',label:'Presentation AI',cat:'VISUAL',mode:'presentation_builder'},
  {icon:'📰',label:'AI News Hub',cat:'NEWS',mode:'news_hub'},
  {icon:'🛒',label:'Smart Shopping',cat:'TOOLS',mode:'smart_shopping'},
  {icon:'🔬',label:'Context Focus',cat:'TOOLS',mode:'context_focus'},
  {icon:'🏗️',label:'Project Architect',cat:'TOOLS',mode:'project_architect'},
];
var selIdx=0;
function renderList(filter){
  var list=document.getElementById('cmdList'); if(!list)return;
  var filtered=CMD_ITEMS.filter(function(i){return i.label.toLowerCase().includes(filter.toLowerCase())||i.cat.toLowerCase().includes(filter.toLowerCase());});
  list.innerHTML=filtered.map(function(item,i){return '<div class="cmd-item'+(i===0?' selected':'')+'" data-mode="'+item.mode+'" onclick="selectCmd(\''+item.mode+'\')"><span class="cmd-item-icon">'+item.icon+'</span>'+item.label+'<span class="cmd-item-cat">'+item.cat+'</span></div>';}).join('');
  selIdx=0;
}
function selectCmd(mode){
  document.getElementById('cmdOverlay').classList.remove('visible');
  var btn=document.querySelector('[data-cmd-mode="'+mode+'"]');
  if(btn) btn.click();
}
document.addEventListener('DOMContentLoaded',function(){renderList('');});
document.addEventListener('keydown',function(e){
  if(e.key==='k'&&(e.ctrlKey||e.metaKey)){e.preventDefault();document.getElementById('cmdOverlay').classList.toggle('visible');document.getElementById('cmdInput').value='';renderList('');setTimeout(function(){document.getElementById('cmdInput').focus();},100);}
  if(e.key==='Escape'){document.getElementById('cmdOverlay').classList.remove('visible');}
});
var inp=document.getElementById('cmdInput');
if(inp){inp.addEventListener('input',function(){renderList(this.value);selIdx=0;});}
document.getElementById('cmdOverlay').addEventListener('click',function(e){if(e.target===this)this.classList.remove('visible');});
</script>
"""
st.markdown(COMMAND_PALETTE_CODE, unsafe_allow_html=True)
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 27 — SMART NOTES: RICH TEXT FORMATTING + AUTO-TAG EXTRACTION
# File: app.py (or utils/notes_engine.py)  |  Location: smart_notes app_mode
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. After AI generates notes, run a second lightweight AI call to extract
#    5–8 key concept tags and store in `st.session_state["note_tags"]`.
#    Display tags as colored chips above the note.
# 2. A "Simplify" button that re-generates the note at a lower reading level
#    (Grade 8 equivalent) — saves as a variant in session state.
# 3. A "Key Terms" expander that lists bolded/important terms extracted via
#    regex from the note text, formatted as a glossary.
# 4. Export note as a styled HTML file with the app's visual theme.

## CSS TO INJECT:

```css
/* ── STEP 27: Smart Notes UI ── */
.note-tag-strip { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }
.note-tag {
  padding:4px 12px; border-radius:100px;
  font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px;
  transition:all 0.2s ease; cursor:default;
}
.nt1 { background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.25); color:#a5b4fc; }
.nt2 { background:rgba(6,182,212,0.1);  border:1px solid rgba(6,182,212,0.25);  color:#22d3ee; }
.nt3 { background:rgba(34,197,94,0.1);  border:1px solid rgba(34,197,94,0.25);  color:#4ade80; }
.nt4 { background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.25); color:#fbbf24; }
.note-tag:hover { transform:translateY(-2px); filter:brightness(1.3); }
.note-card {
  background:rgba(15,23,42,0.7); border:1px solid rgba(99,102,241,0.15);
  border-radius:16px; padding:24px 28px;
}
.note-simplified-badge {
  display:inline-flex; align-items:center; gap:7px; margin-bottom:12px;
  padding:5px 14px; border-radius:100px;
  background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.2);
  font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:#4ade80;
}
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 28 — LANGUAGE TOOLS: REAL-TIME CHARACTER/WORD COUNTER + PRONUNCIATION GUIDE
# File: utils/language_engine.py  |  Location: render_language_tools()
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. A live word/character counter beneath the translation input that updates
#    via `st.session_state` as the user types.
# 2. After translation, show a "Pronunciation Guide" section with the IPA
#    phonetic transcription requested from the AI.
# 3. A "Back-Translation Check": translate the result back to English and
#    show a similarity warning if the meaning drifted significantly.
# 4. A "Language Fact" card: a short interesting fact about the target language
#    generated by a 50-token AI call, shown as a quote-styled aside.

## CSS TO INJECT:

```css
/* ── STEP 28: Language Tools UI ── */
.lang-counter-row {
  display:flex; gap:16px; font-family:'Space Mono',monospace; font-size:10px;
  color:rgba(255,255,255,0.25); letter-spacing:2px; margin-top:4px; margin-bottom:12px;
}
.lang-counter-val { color:rgba(165,180,252,0.7); font-weight:700; }
.pronunciation-box {
  padding:16px 20px; border-radius:12px; margin-top:12px;
  background:rgba(99,102,241,0.06); border:1px solid rgba(99,102,241,0.15);
  border-left:3px solid rgba(99,102,241,0.5);
}
.pronunciation-label { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:3px; color:rgba(99,102,241,0.6); margin-bottom:8px; }
.pronunciation-ipa { font-family:'Space Mono',monospace; font-size:16px; color:#a5b4fc; letter-spacing:2px; }
.lang-fact-card {
  margin-top:16px; padding:16px 20px; border-radius:12px;
  background:rgba(15,23,42,0.5); border:1px solid rgba(255,255,255,0.07);
  border-left:3px solid rgba(6,182,212,0.5); position:relative;
}
.lang-fact-quote { font-size:32px; color:rgba(6,182,212,0.2); position:absolute; top:8px; left:12px; font-family:Georgia,serif; line-height:1; }
.lang-fact-text { font-family:'Rajdhani',sans-serif; font-size:14px; color:rgba(255,255,255,0.6); line-height:1.6; padding-left:20px; }
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 29 — GRAPH PLOTTER: EQUATION PRESETS + FULLSCREEN BUTTON + SHARE LINK
# File: app.py  |  Location: graph app_mode block
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# 1. A preset equations bar: "Sine Wave", "Parabola", "Normal Distribution",
#    "Logistic Curve", "Damped Oscillation" — clicking pre-fills the equation
#    input and auto-renders.
# 2. A fullscreen button that uses `st.plotly_chart(use_container_width=True)`
#    + custom CSS to expand the chart to fill the viewport.
# 3. An "Annotate" input that lets the user click on a chart point and add a
#    text annotation via Plotly's `fig.add_annotation()`.
# 4. A "Save to Library" button that appends the current equation + screenshot
#    description to `st.session_state["graph_library"]`.

## CSS TO INJECT:

```css
/* ── STEP 29: Graph Plotter Enhancements ── */
.eq-preset-row { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:14px; }
.eq-preset-chip {
  padding:7px 14px; border-radius:100px; cursor:pointer;
  background:rgba(15,23,42,0.7); border:1px solid rgba(99,102,241,0.2);
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:1px; color:#a5b4fc;
  transition:all 0.2s ease;
}
.eq-preset-chip:hover { background:rgba(99,102,241,0.12); border-color:rgba(99,102,241,0.45); color:#fff; transform:translateY(-2px); }
.graph-library-item {
  display:flex; align-items:center; gap:10px; padding:10px 14px;
  background:rgba(15,23,42,0.5); border:1px solid rgba(255,255,255,0.07);
  border-radius:10px; margin-bottom:6px;
  font-family:'Rajdhani',sans-serif; font-size:13px; color:rgba(255,255,255,0.6);
  transition:all 0.2s ease;
}
.graph-library-item:hover { border-color:rgba(99,102,241,0.3); color:#fff; }
.eq-mono { font-family:'Space Mono',monospace; font-size:12px; color:#a5b4fc; }
```

## PYTHON TO ADD:

```python
EQUATION_PRESETS = [
    ("∿ Sine",        "sin(x)"),
    ("⌒ Parabola",    "x**2"),
    ("⊃ Normal Dist", "exp(-x**2/2) / sqrt(2*pi)"),
    ("S Logistic",    "1 / (1 + exp(-x))"),
    ("≈ Damped Osc",  "exp(-0.1*x) * cos(x)"),
    ("∞ Spiral",      "x * sin(x)"),
]

def render_equation_presets():
    """STEP 29: Equation preset quick-fill buttons."""
    if "graph_library" not in st.session_state:
        st.session_state["graph_library"] = []

    st.markdown('<div class="eq-preset-row">', unsafe_allow_html=True)
    cols = st.columns(len(EQUATION_PRESETS))
    for i, (label, eq) in enumerate(EQUATION_PRESETS):
        with cols[i]:
            if st.button(label, key=f"s29_preset_{i}", use_container_width=True):
                st.session_state["graph_eq_input"] = eq
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
```


# ─────────────────────────────────────────────────────────────────────────────
# STEP 30 — AI-POWERED "WHAT TO STUDY NEXT" RECOMMENDATION ENGINE
# File: app.py  |  Location: end of main area, visible in all modes
# ─────────────────────────────────────────────────────────────────────────────

## WHAT TO ADD:
# A persistent "What to Study Next" recommendation card at the bottom of the
# main area. It analyzes the last 5 messages + selected persona + exam date and
# generates 3 personalized study recommendations with:
# - Topic name + subject tag
# - Estimated study time (15/30/45 min)
# - Difficulty badge (Beginner / Intermediate / Advanced)
# - A direct "Start Now" button that queues a prompt about that topic
# Recommendations are cached for 10 minutes in `st.session_state["study_recs"]`.
# Regenerate button with a spinner for manual refresh.

## CSS TO INJECT:

```css
/* ── STEP 30: Study Recommendation Engine ── */
.study-recs-section { margin:24px 0 8px; }
.study-recs-header {
  display:flex; align-items:center; justify-content:space-between;
  margin-bottom:14px;
}
.study-recs-title {
  font-family:'Space Mono',monospace; font-size:10px; letter-spacing:4px;
  color:rgba(255,255,255,0.3); text-transform:uppercase;
}
.rec-card {
  padding:16px 20px; border-radius:14px; margin-bottom:10px;
  background:rgba(15,23,42,0.65); border:1px solid rgba(255,255,255,0.07);
  display:flex; align-items:center; gap:16px;
  transition:all 0.25s ease;
  animation:bubbleIn 0.4s cubic-bezier(0.16,1,0.3,1) both;
  position:relative; overflow:hidden;
}
.rec-card::before {
  content:''; position:absolute; left:0; top:0; bottom:0; width:3px;
  background:var(--rec-color, linear-gradient(180deg,#6366f1,#8b5cf6));
}
.rec-card:hover { border-color:rgba(99,102,241,0.25); transform:translateX(4px); }
.rec-icon { font-size:28px; flex-shrink:0; }
.rec-body { flex:1; min-width:0; }
.rec-topic { font-family:'Rajdhani',sans-serif; font-size:15px; font-weight:700; color:#fff; margin-bottom:4px; }
.rec-meta  { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.rec-tag   { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:2px; color:rgba(255,255,255,0.3); }
.rec-time  { font-family:'Space Mono',monospace; font-size:9px; letter-spacing:1px; color:rgba(6,182,212,0.7); }
.rec-diff-beginner    { background:rgba(34,197,94,0.1);  border:1px solid rgba(34,197,94,0.2);  color:#4ade80;  font-family:'Space Mono',monospace; font-size:8px; letter-spacing:2px; padding:2px 8px; border-radius:100px; }
.rec-diff-intermediate{ background:rgba(245,158,11,0.1); border:1px solid rgba(245,158,11,0.2); color:#fbbf24; font-family:'Space Mono',monospace; font-size:8px; letter-spacing:2px; padding:2px 8px; border-radius:100px; }
.rec-diff-advanced    { background:rgba(239,68,68,0.1);  border:1px solid rgba(239,68,68,0.2);  color:#f87171;  font-family:'Space Mono',monospace; font-size:8px; letter-spacing:2px; padding:2px 8px; border-radius:100px; }
```

## PYTHON TO ADD:

```python
def render_study_recommendations():
    """STEP 30: AI-powered personalized study recommendation engine."""
    import time, json, re

    CACHE_TTL = 600  # 10 minutes
    now = time.time()
    cache = st.session_state.get("study_recs", {})
    cache_time = st.session_state.get("study_recs_time", 0)
    recs = cache.get("items", [])

    show_regen = now - cache_time > CACHE_TTL or not recs

    st.markdown('<div class="study-recs-section">', unsafe_allow_html=True)

    header_cols = st.columns([6, 2])
    with header_cols[0]:
        st.markdown('<div class="study-recs-title">✦ What to Study Next</div>', unsafe_allow_html=True)
    with header_cols[1]:
        regen_clicked = st.button("🔄 Refresh", key="s30_regen_recs", use_container_width=True)

    if show_regen or regen_clicked:
        recent_msgs = st.session_state.get("messages", [])[-6:]
        context_snippet = " | ".join([m["content"][:120] for m in recent_msgs if m.get("role") == "user"])
        persona = st.session_state.get("selected_persona", "Default")
        exam_date = str(st.session_state.get("exam_date", ""))

        prompt = f"""Based on the student's recent activity: "{context_snippet or 'General study session'}"
Persona chosen: {persona}. Exam date: {exam_date}.
Generate exactly 3 personalized study topic recommendations. Return ONLY a JSON array of 3 objects with keys:
"icon" (single emoji), "topic" (string, max 8 words), "subject" (string, 1 word category),
"minutes" (integer: 15, 30, or 45), "difficulty" ("Beginner", "Intermediate", or "Advanced"),
"prompt" (string: exact question to ask the AI to start studying this topic).
Return only valid JSON, no other text."""

        with st.spinner("Personalizing your study path…"):
            try:
                from utils import ai_engine
                raw = ai_engine.generate(
                    prompt=prompt,
                    system="Return only a valid JSON array of exactly 3 objects. No markdown, no prose.",
                    max_tokens=400
                )
                match = re.search(r'\[.*?\]', raw, re.DOTALL)
                if match:
                    recs = json.loads(match.group(0))[:3]
                    st.session_state["study_recs"] = {"items": recs}
                    st.session_state["study_recs_time"] = now
                else:
                    recs = []
            except Exception as e:
                st.error(f"⚠️ Recommendations failed: {e}")
                recs = []

    REC_COLORS = [
        "linear-gradient(180deg,#6366f1,#8b5cf6)",
        "linear-gradient(180deg,#06b6d4,#3b82f6)",
        "linear-gradient(180deg,#10b981,#06b6d4)",
    ]

    for i, rec in enumerate(recs[:3]):
        diff = rec.get("difficulty", "Beginner").lower().replace(" ", "")
        color = REC_COLORS[i % len(REC_COLORS)]
        st.markdown(f"""
        <div class="rec-card" style="--rec-color:{color};">
          <span class="rec-icon">{rec.get("icon","📖")}</span>
          <div class="rec-body">
            <div class="rec-topic">{rec.get("topic","Study Topic")}</div>
            <div class="rec-meta">
              <span class="rec-tag">{rec.get("subject","GENERAL")}</span>
              <span class="rec-time">⏱ {rec.get("minutes",25)} min</span>
              <span class="rec-diff-{diff}">{rec.get("difficulty","Beginner").upper()}</span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        if st.button(f"▶ Start Now", key=f"s30_start_{i}", use_container_width=False):
            st.session_state.queued_prompt = rec.get("prompt", f"Teach me about {rec.get('topic','this topic')}")
            st.session_state.app_mode = "chat"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
```

# Call `render_study_recommendations()` at the BOTTOM of the main chat area,
# BELOW the message display loop but ABOVE the chat input widget.
# Only render when `app_mode == "chat"` to avoid cluttering other tool screens.


# ══════════════════════════════════════════════════════════════════════════════
# FINAL INTEGRATION CHECKLIST
# ══════════════════════════════════════════════════════════════════════════════

## 1. SESSION STATE ADDITIONS (add to init_state() defaults dict):
#
#    "s04_show_context_panel": False,
#    "source_summaries": {},
#    "followup_cache": {},
#    "study_recs": {},
#    "study_recs_time": 0.0,
#    "graph_library": [],
#    "graph_eq_input": "sin(x)",
#    "mindmap_extra_nodes": {},
#    "legal_case_files": [],
#    "note_tags": {},

## 2. CALL ORDER IN MAIN AREA (app_mode == "chat"):
#
#    render_hero_header_v2()          # Step 01
#    st.markdown(SHORTCUT_OVERLAY_CODE, ...)   # Step 12
#    st.markdown(TOAST_SYSTEM_CODE, ...)       # Step 24
#    st.markdown(COMMAND_PALETTE_CODE, ...)    # Step 26
#    render_persona_carousel()        # Step 08
#    render_source_cards()            # Step 06  (replaces old chip row)
#    [message loop with bubble CSS]   # Step 05
#      └── render_followup_suggestions(msg, i)  # Step 11 (last AI msg only)
#    render_quick_prompts()           # Step 09  (empty state only)
#    render_quick_actions_toolbar()   # Step 04
#    [chat input]
#    render_study_recommendations()   # Step 30

## 3. SIDEBAR ADDITIONS:
#
#    render_stats_dashboard()         # Step 03 (replace old stat-row)
#    [active tool banner]             # Step 02

## 4. CSS INJECTION ORDER:
#    All new CSS blocks from Steps 01–30 must be appended into the single
#    existing `st.markdown("<style>…</style>")` block at the top of app.py.
#    Do NOT create separate `st.markdown` calls for each CSS block — this
#    causes Streamlit to re-inject the entire DOM style tag repeatedly.
#    Consolidate all new CSS into ONE addition to the existing block.

## 5. FEATURE-FILE ADDITIONS:
#    Steps 13–15 → app.py flashcard/quiz/mindmap blocks
#    Steps 16–19 → app.py planner/debugger/essay/interview blocks
#    Steps 20–22 → new_features.py legal/medical/research functions
#    Steps 23,25 → new_features.py stocks + advanced_features.py pomodoro
#    Steps 27–29 → language_engine.py, notes_engine.py, graph block in app.py

## 6. VERIFY NO BREAKAGE:
#    After all 30 steps, run: `streamlit run app.py`
#    Confirm: passcode gate works → login → sidebar → chat → each tool mode
#    Check console for zero Python errors on cold start.
#    Check that all `key=` parameters are globally unique (grep for duplicate keys).

# ══════════════════════════════════════════════════════════════════════════════
# ✅ UI ELEVATION v6.0 — 30 STEPS SPECIFICATION COMPLETE
# Total prompt lines: ~1000  |  Steps: 30  |  Files modified: 4  |  New CSS rules: 200+
# New Python functions: 28  |  New session state keys: 10  |  Zero deletions
# ══════════════════════════════════════════════════════════════════════════════
