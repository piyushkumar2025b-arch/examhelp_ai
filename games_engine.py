"""
games_engine.py — Games Arcade Hub for ExamHelp AI
31 games across 5 categories. All state via st.session_state.
"""
from __future__ import annotations
import streamlit as st

# ── Imports from sub-modules ──────────────────────────────────────────────────
from games.board_games import (
    render_tictactoe, render_connect_four, render_chess,
    render_battleship, render_minesweeper, render_sudoku, render_2048,
)
from games.word_games import (
    render_wordle, render_hangman, render_word_scramble,
    render_crossword, render_rhyme_chain, render_story_dice,
)
from games.logic_games import (
    render_number_guess, render_math_sprint, render_mastermind,
    render_memory_matrix, render_pattern_game,
)
from games.ai_games import (
    render_twenty_questions, render_trivia_battle, render_would_you_rather,
    render_debate_me, render_two_truths_one_lie,
    render_story_collab, render_moral_dilemma,
)
from games.arcade_games import (
    render_reaction_timer, render_rps_lizard_spock, render_higher_lower,
    render_true_false_blitz, render_emoji_rebus, render_typing_speed,
    render_color_match, render_quiz_blitz, render_number_chain,
)

# ── Per-category game registry ────────────────────────────────────────────────
BOARD_GAMES = {
    "♟️ Tic-Tac-Toe":  render_tictactoe,
    "🔴 Connect Four":  render_connect_four,
    "♞ Chess":          render_chess,
    "⚓ Battleship":    render_battleship,
    "💣 Minesweeper":   render_minesweeper,
    "🔢 Sudoku":        render_sudoku,
    "🎯 2048":          render_2048,
}
WORD_GAMES = {
    "🟩 Wordle":          render_wordle,
    "🪢 Hangman":         render_hangman,
    "🔀 Word Scramble":   render_word_scramble,
    "✏️ Crossword Lite":  render_crossword,
    "🎵 Rhyme Chain":     render_rhyme_chain,
    "🎲 Story Dice":      render_story_dice,
}
LOGIC_GAMES = {
    "🔢 Number Guess":    render_number_guess,
    "⚡ Math Sprint":     render_math_sprint,
    "🔐 Mastermind":      render_mastermind,
    "🧠 Memory Matrix":   render_memory_matrix,
    "🧩 Pattern Game":    render_pattern_game,
}
AI_GAMES = {
    "❓ 20 Questions":          render_twenty_questions,
    "🏆 Trivia Battle":        render_trivia_battle,
    "🤔 Would You Rather":     render_would_you_rather,
    "🎤 Debate Me":            render_debate_me,
    "🤥 Two Truths One Lie":   render_two_truths_one_lie,
    "📖 Story Collab":         render_story_collab,
    "⚖️ Moral Dilemma":        render_moral_dilemma,
}
ARCADE_GAMES = {
    "⚡ Reaction Timer":           render_reaction_timer,
    "🖖 RPSLS":                    render_rps_lizard_spock,
    "🃏 Higher or Lower":          render_higher_lower,
    "🔥 True/False Blitz":         render_true_false_blitz,
    "🧩 Emoji Rebus":              render_emoji_rebus,
    "⌨️ Typing Speed Test":        render_typing_speed,
    "🎨 Color Match":              render_color_match,
    "⚡ Quiz Blitz (60s)":         render_quiz_blitz,
    "🔗 Number Chain":             render_number_chain,
}

ALL_COUNTS = (
    len(BOARD_GAMES), len(WORD_GAMES), len(LOGIC_GAMES),
    len(AI_GAMES), len(ARCADE_GAMES)
)
TOTAL_GAMES = sum(ALL_COUNTS)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR HIGH SCORE WIDGET
# ─────────────────────────────────────────────────────────────────────────────
def render_games_sidebar():
    """Render high-score mini widget in the sidebar."""
    scores = st.session_state.get("game_scores", {})
    if not scores:
        return
    with st.sidebar:
        st.markdown("### 🏅 My High Scores")
        for game, score in sorted(scores.items(), key=lambda x: -x[1])[:8]:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:.8rem;padding:2px 0;">'
                f'<span style="color:#94a3b8;">{game[:22]}</span>'
                f'<span style="color:#a5b4fc;font-weight:700;">{score}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


# ─────────────────────────────────────────────────────────────────────────────
# LOBBY HEADER
# ─────────────────────────────────────────────────────────────────────────────
def _render_header():
    st.markdown(f"""
<style>
.games-header {{
    background: linear-gradient(135deg,rgba(99,102,241,0.1) 0%,rgba(16,185,129,0.06) 50%,rgba(251,146,60,0.08) 100%);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 20px;
}}
.game-cat-stat {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 12px 16px;
    text-align: center;
}}
.game-cat-val {{
    font-size: 1.5rem;
    font-weight: 900;
    color: #a5b4fc;
}}
.game-cat-lbl {{
    font-size: .72rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
</style>
<div class="games-header">
  <div style="font-family:monospace;font-size:10px;letter-spacing:4px;
  color:rgba(99,102,241,.6);text-transform:uppercase;margin-bottom:8px;">
    AI-POWERED · {TOTAL_GAMES} GAMES ACROSS 5 CATEGORIES
  </div>
  <div style="font-size:2rem;font-weight:900;color:#fff;margin-bottom:6px;">
    🎮 Games Arcade
  </div>
  <div style="color:rgba(255,255,255,0.4);font-size:.9rem;">
    Board & Strategy · Word Games · Math & Logic · AI Chat · Arcade
  </div>
</div>
""", unsafe_allow_html=True)

    # Stats row
    cat_names = ["🏆 Board", "📝 Word", "🧮 Logic", "🤖 AI Chat", "🕹️ Arcade"]
    cols = st.columns(5)
    for col, name, count in zip(cols, cat_names, ALL_COUNTS):
        col.markdown(
            f'<div class="game-cat-stat">'
            f'<div class="game-cat-val">{count}</div>'
            f'<div class="game-cat-lbl">{name}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    st.markdown("")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def render_games_page():
    """Main entry point — registered in app.py as app_mode == 'games'."""

    # Initialize high-scores dict
    if "game_scores" not in st.session_state:
        st.session_state.game_scores = {}

    _render_header()

    # ── Sidebar high scores ───────────────────────────────────────────────────
    render_games_sidebar()

    # ── Category Tabs ─────────────────────────────────────────────────────────
    tab_board, tab_word, tab_logic, tab_ai, tab_arcade = st.tabs([
        f"🏆 Board & Strategy ({len(BOARD_GAMES)})",
        f"📝 Word Games ({len(WORD_GAMES)})",
        f"🧮 Math & Logic ({len(LOGIC_GAMES)})",
        f"🤖 AI Chat Games ({len(AI_GAMES)})",
        f"🕹️ Arcade ({len(ARCADE_GAMES)})",
    ])

    # ── Board & Strategy ──────────────────────────────────────────────────────
    with tab_board:
        selected = st.selectbox(
            "Pick a game:",
            list(BOARD_GAMES.keys()),
            key="sel_board"
        )
        st.markdown("---")
        BOARD_GAMES[selected]()

    # ── Word Games ────────────────────────────────────────────────────────────
    with tab_word:
        selected = st.selectbox(
            "Pick a game:",
            list(WORD_GAMES.keys()),
            key="sel_word"
        )
        st.markdown("---")
        WORD_GAMES[selected]()

    # ── Math & Logic ──────────────────────────────────────────────────────────
    with tab_logic:
        selected = st.selectbox(
            "Pick a game:",
            list(LOGIC_GAMES.keys()),
            key="sel_logic"
        )
        st.markdown("---")
        LOGIC_GAMES[selected]()

    # ── AI Chat Games ─────────────────────────────────────────────────────────
    with tab_ai:
        selected = st.selectbox(
            "Pick a game:",
            list(AI_GAMES.keys()),
            key="sel_ai"
        )
        st.markdown("---")
        AI_GAMES[selected]()

    # ── Arcade ────────────────────────────────────────────────────────────────
    with tab_arcade:
        selected = st.selectbox(
            "Pick a game:",
            list(ARCADE_GAMES.keys()),
            key="sel_arcade"
        )
        st.markdown("---")
        ARCADE_GAMES[selected]()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    col_back, col_scores = st.columns(2)
    with col_back:
        if st.button("💬 Back to Chat", use_container_width=True, key="games_back"):
            st.session_state.app_mode = "chat"
            st.rerun()
    with col_scores:
        scores = st.session_state.get("game_scores", {})
        if scores and st.button(
            f"🏅 My Scores ({len(scores)} games played)",
            use_container_width=True,
            key="games_scores_btn"
        ):
            st.markdown("#### 🏅 All High Scores")
            for game, score in sorted(scores.items(), key=lambda x: -x[1]):
                st.markdown(f"- **{game}**: {score}")


# ── FREE API ADDITIONS ───────────────────────────────────────────────────────

def fetch_trivia_question(category_id: str = "18", difficulty: str = "medium") -> dict:
    """Fetch a live trivia question from Open Trivia DB (free, no key)."""
    import urllib.request, json, html
    try:
        url = f"https://opentdb.com/api.php?amount=1&category={category_id}&difficulty={difficulty}&type=multiple"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        results = data.get("results", [])
        if results:
            q = results[0]
            return {
                "question": html.unescape(q.get("question", "")),
                "correct": html.unescape(q.get("correct_answer", "")),
                "incorrect": [html.unescape(a) for a in q.get("incorrect_answers", [])],
                "difficulty": q.get("difficulty", ""),
                "category": q.get("category", ""),
            }
    except Exception:
        pass
    return {}


def fetch_trivia_batch(n: int = 5, category_id: str = "18") -> list:
    """Fetch multiple trivia questions at once (Open Trivia DB, free)."""
    import urllib.request, json, html
    try:
        url = f"https://opentdb.com/api.php?amount={n}&category={category_id}&type=multiple"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())
        results = []
        for q in data.get("results", []):
            results.append({
                "question": html.unescape(q.get("question", "")),
                "correct": html.unescape(q.get("correct_answer", "")),
                "incorrect": [html.unescape(a) for a in q.get("incorrect_answers", [])],
                "difficulty": q.get("difficulty", ""),
            })
        return results
    except Exception:
        return []


def fetch_joke(category: str = "Programming") -> str:
    """Fetch a joke from JokeAPI for fun breaks (free, no key)."""
    import urllib.request, json
    try:
        url = f"https://v2.jokeapi.dev/joke/{category}?safe-mode"
        req = urllib.request.Request(url, headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
        if data.get("type") == "single":
            return data.get("joke", "")
        return f"{data.get('setup', '')} ... {data.get('delivery', '')}"
    except Exception:
        return "Why do programmers prefer dark mode? Because light attracts bugs! 🐛"


def fetch_random_activity() -> dict:
    """Fetch a random activity suggestion from Bored API (free, no key)."""
    import urllib.request, json
    try:
        req = urllib.request.Request("https://www.boredapi.com/api/activity", headers={"User-Agent": "ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {"activity": "Take a 5-minute walk to refresh your mind!", "type": "relaxation"}
