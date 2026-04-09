import re
import codecs

def patch():
    with codecs.open('EXAMHELP_UI_IMPROVEMENT_30_STEPS.md', 'r', 'utf-8') as f:
        text = f.read()

    css_pattern = r'## CSS TO INJECT:(?:.*?|)```css\n(.*?)```'
    css_blocks = re.findall(css_pattern, text, re.DOTALL | re.IGNORECASE)
    all_css = '\n'.join(css_blocks)

    py_pattern = r'## PYTHON TO ADD:(?:.*?|)```python\n(.*?)```'
    py_blocks = re.findall(py_pattern, text, re.DOTALL | re.IGNORECASE)
    all_py = '\n'.join(py_blocks)

    with codecs.open('app.py', 'r', 'utf-8') as f:
        app_text = f.read()

    if '    </style>' in app_text:
        app_text = app_text.replace('    </style>', all_css + '\n    </style>', 1)
    else:
        app_text = app_text.replace('</style>', all_css + '\n</style>', 1)

    marker = '# ─────────────────────────────────────────────\n# MAIN AREA'
    if marker in app_text:
        app_text = app_text.replace(marker, all_py + '\n\n' + marker, 1)

    # Specific replacements from the steps
    
    # Step 1: Hero header replacement
    hero_old = '''st.markdown(f"""
<div class="page-header">
  <div class="page-header-title">ExamHelp</div>
  <div class="page-header-sub">AI Study Companion{persona_tag}</div>
</div>""", unsafe_allow_html=True)'''
    app_text = app_text.replace(hero_old, 'render_hero_header_v2()')

    # Step 2: Sidebar
    sidebar_marker = 'st.markdown(\'<div class="section-label">🛠️ Study Toolbox</div>\', unsafe_allow_html=True)'
    sidebar_new = '''
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
'''
    if sidebar_marker in app_text:
        app_text = app_text.replace(sidebar_marker, sidebar_new + '\n' + sidebar_marker)

    # Step 3: Stats mini dashboard
    stat_row_old = '<div class="stat-row">' # Replace the block entirely, not just the div.
    # We will search for the loop that renders it:
    # Actually, the python code for stats mini dashboard says: "Replace the existing st.markdown(f'<div class="stat-row">…</div>') with: render_stats_dashboard()"
    # Currently it's 4 tiles
    # Wait, there's a stat-row block in app.py around line 4650. Let's find it.
    
    with codecs.open('app_patched.py', 'w', 'utf-8') as f:
        f.write(app_text)

    print(f"Patched app_patched.py successfully. extracted {len(css_blocks)} css blocks and {len(py_blocks)} py blocks")

if __name__ == '__main__':
    patch()
