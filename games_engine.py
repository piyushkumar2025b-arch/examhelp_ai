"""
games_engine.py — AI Games Section for ExamHelp AI
Games:
  1. Tic-Tac-Toe vs AI (Minimax + alpha-beta pruning)
  2. Wordle-style Word Game (5-letter, 6 guesses, color-coded)
  3. 20 Questions (AI thinks of concept, you guess)
  4. AI Trivia Battle (head-to-head vs AI)
"""
from __future__ import annotations
import streamlit as st
import random
import json
import time
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _ai_call(prompt: str, max_tokens: int = 512) -> str:
    """Call the existing AI engine with a prompt."""
    try:
        from utils import ai_engine
        return ai_engine.generate(prompt, max_tokens=max_tokens)
    except Exception:
        try:
            from utils.groq_client import chat_with_groq
            return chat_with_groq([{"role": "user", "content": prompt}], max_tokens=max_tokens)
        except Exception:
            return ""


# ═════════════════════════════════════════════════════════════════════════════
# GAME 1 — TIC-TAC-TOE vs AI (Minimax)
# ═════════════════════════════════════════════════════════════════════════════

def _ttt_check_winner(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b,c in wins:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    if all(board):
        return "Draw"
    return None


def _ttt_minimax(board, is_maximizing, alpha=-float('inf'), beta=float('inf')):
    winner = _ttt_check_winner(board)
    if winner == "O": return 10
    if winner == "X": return -10
    if winner == "Draw": return 0

    if is_maximizing:
        best = -float('inf')
        for i in range(9):
            if not board[i]:
                board[i] = "O"
                best = max(best, _ttt_minimax(board, False, alpha, beta))
                board[i] = ""
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
        return best
    else:
        best = float('inf')
        for i in range(9):
            if not board[i]:
                board[i] = "X"
                best = min(best, _ttt_minimax(board, True, alpha, beta))
                board[i] = ""
                beta = min(beta, best)
                if beta <= alpha:
                    break
        return best


def _ttt_best_move(board):
    best_score = -float('inf')
    move = -1
    for i in range(9):
        if not board[i]:
            board[i] = "O"
            score = _ttt_minimax(board, False)
            board[i] = ""
            if score > best_score:
                best_score = score
                move = i
    return move


def render_tictactoe():
    st.markdown("""
<div style="background:linear-gradient(135deg,#0a0020,#000);border:1px solid rgba(99,102,241,0.3);
border-radius:16px;padding:24px 28px;margin-bottom:20px;">
  <div style="font-size:1.8rem;font-weight:900;color:#a5b4fc;margin-bottom:4px;">🎮 Tic-Tac-Toe vs AI</div>
  <div style="color:#94a3b8;font-size:.9rem;">You are <b style="color:#34d399">X</b> · AI is <b style="color:#f87171">O</b> · AI uses Minimax — it never loses!</div>
</div>
""", unsafe_allow_html=True)

    if "ttt_board" not in st.session_state:
        st.session_state.ttt_board = [""] * 9
        st.session_state.ttt_game_over = False
        st.session_state.ttt_status = ""
        st.session_state.ttt_scores = {"X": 0, "O": 0, "Draw": 0}

    board = st.session_state.ttt_board

    # Score display
    sc = st.session_state.ttt_scores
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("🧑 You (X)", sc["X"])
    col_s2.metric("🤖 AI (O)", sc["O"])
    col_s3.metric("🤝 Draws", sc["Draw"])

    st.markdown("---")

    # Render 3x3 board
    winner = _ttt_check_winner(board)
    game_over = winner is not None or st.session_state.ttt_game_over

    cell_style = {
        "X": "background:rgba(52,211,153,0.15);border:2px solid #34d399;color:#34d399;",
        "O": "background:rgba(248,113,113,0.15);border:2px solid #f87171;color:#f87171;",
        "":  "background:rgba(255,255,255,0.03);border:2px solid rgba(255,255,255,0.1);color:#fff;",
    }

    for row in range(3):
        cols = st.columns(3)
        for col in range(3):
            idx = row * 3 + col
            with cols[col]:
                cell_val = board[idx]
                label = cell_val if cell_val else " "
                btn_disabled = bool(cell_val) or game_over
                if st.button(
                    label,
                    key=f"ttt_{idx}",
                    use_container_width=True,
                    disabled=btn_disabled,
                ):
                    # Player move
                    board[idx] = "X"
                    w = _ttt_check_winner(board)
                    if not w:
                        ai_move = _ttt_best_move(board)
                        if ai_move >= 0:
                            board[ai_move] = "O"
                    st.session_state.ttt_board = board
                    st.rerun()

    # Check result after rendering
    winner = _ttt_check_winner(board)
    if winner:
        if winner == "X":
            st.success("🎉 You Win! (That's rare against Minimax!)")
            st.balloons()
        elif winner == "O":
            st.error("🤖 AI Wins! Try again.")
        else:
            st.info("🤝 It's a Draw!")
        st.session_state.ttt_scores[winner] = st.session_state.ttt_scores.get(winner, 0) + 1
        st.session_state.ttt_game_over = True

    if st.button("🔄 New Game", use_container_width=True, key="ttt_reset"):
        st.session_state.ttt_board = [""] * 9
        st.session_state.ttt_game_over = False
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# GAME 2 — WORDLE-STYLE
# ═════════════════════════════════════════════════════════════════════════════

WORDLE_WORDS = [
    "arose","crane","slate","trace","crate","stale","arise","snare","least","steal",
    "alert","alter","learn","earth","heart","reach","teach","beach","peach","leach",
    "place","plane","plant","grant","rant","chant","chart","smart","start","stark",
    "spark","spare","spare","stare","share","shore","store","score","snore","smoke",
    "spoke","spore","swore","sword","word","world","wrath","wreath","wheat","cheat",
    "cheap","clear","clean","cleat","clean","cream","dream","steam","stream","scream",
    "bread","tread","dread","ahead","bead","dead","lead","read","head","mead",
    "flame","frame","blame","claim","flail","trail","train","brain","grain","drain",
    "plain","plaid","braid","frail","snail","quail","snail","grail","frail","trail",
    "brave","crave","grave","slave","shave","shave","stave","knave","gavel","ravel",
    "novel","hovel","level","devil","civil","rival","tidal","viral","vital","final",
    "tiger","giver","liver","river","diver","miner","finer","liner","diner","siren",
    "token","woken","often","open","oven","even","seven","raven","haven","maven",
    "stink","think","drink","blink","brink","bring","string","spring","sprint","print",
    "point","joint","hoist","moist","foist","noise","poise","voice","choice","twice",
    "price","slice","spice","trice","dance","lance","fence","hence","pence","mince",
    "since","rinse","rinse","binge","hinge","fringe","cringe","plunge","lunge","fungi",
]


def _wordle_feedback(guess: str, secret: str):
    """Return list of 'G', 'Y', '_' for each letter."""
    result = ["_"] * 5
    secret_chars = list(secret)
    guess_chars  = list(guess)
    # First pass — greens
    for i in range(5):
        if guess_chars[i] == secret_chars[i]:
            result[i] = "G"
            secret_chars[i] = None
            guess_chars[i]  = None
    # Second pass — yellows
    for i in range(5):
        if guess_chars[i] and guess_chars[i] in secret_chars:
            result[i] = "Y"
            secret_chars[secret_chars.index(guess_chars[i])] = None
    return result


def _render_wordle_row(guess: str, feedback: list, row_idx: int):
    colors = {"G": "#22c55e", "Y": "#ca8a04", "_": "#334155"}
    html = '<div style="display:flex;gap:6px;justify-content:center;margin:4px 0;">'
    for i, (letter, fb) in enumerate(zip(guess.ljust(5), feedback)):
        html += f'''<div style="width:52px;height:52px;background:{colors[fb]};
border-radius:8px;display:flex;align-items:center;justify-content:center;
font-size:1.4rem;font-weight:900;color:#fff;text-transform:uppercase;
border:2px solid rgba(255,255,255,0.1);">{letter}</div>'''
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_wordle():
    st.markdown("""
<div style="background:linear-gradient(135deg,#0a1a0a,#050f05);border:1px solid rgba(34,197,94,0.3);
border-radius:16px;padding:24px 28px;margin-bottom:20px;">
  <div style="font-size:1.8rem;font-weight:900;color:#86efac;margin-bottom:4px;">🟩 Wordle Challenge</div>
  <div style="color:#94a3b8;font-size:.9rem;">Guess the 5-letter word in 6 tries · 🟩 = correct · 🟨 = wrong position · ⬛ = not in word</div>
</div>
""", unsafe_allow_html=True)

    # Init
    if "wordle_secret" not in st.session_state or st.session_state.get("wordle_reset"):
        st.session_state.wordle_secret = random.choice(WORDLE_WORDS).lower()
        st.session_state.wordle_guesses = []
        st.session_state.wordle_won = False
        st.session_state.wordle_reset = False

    secret = st.session_state.wordle_secret
    guesses = st.session_state.wordle_guesses
    won = st.session_state.wordle_won
    max_guesses = 6

    # Show previous guesses
    for i, (g, fb) in enumerate(guesses):
        _render_wordle_row(g, fb, i)

    # Show empty rows
    for i in range(len(guesses), max_guesses):
        _render_wordle_row("     ", ["_"]*5, i)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if won:
        st.success(f"🎉 You got it in {len(guesses)} guess{'es' if len(guesses) > 1 else ''}! The word was **{secret.upper()}**")
    elif len(guesses) >= max_guesses:
        st.error(f"😞 Out of guesses! The word was **{secret.upper()}**")
    else:
        guess_input = st.text_input(
            "Enter 5-letter word", max_chars=5,
            placeholder="Type your guess...",
            key=f"wordle_input_{len(guesses)}"
        ).lower().strip()

        if st.button("Submit Guess", type="primary", use_container_width=True, key="wordle_submit"):
            if len(guess_input) != 5 or not guess_input.isalpha():
                st.warning("Please enter exactly 5 letters.")
            else:
                fb = _wordle_feedback(guess_input, secret)
                guesses.append((guess_input, fb))
                if guess_input == secret:
                    st.session_state.wordle_won = True
                st.session_state.wordle_guesses = guesses
                st.rerun()

    # Keyboard hint
    if guesses:
        all_letters = {}
        for g, fb in guesses:
            for ch, f in zip(g, fb):
                if f == "G": all_letters[ch] = "G"
                elif f == "Y" and all_letters.get(ch) != "G": all_letters[ch] = "Y"
                elif f == "_" and ch not in all_letters: all_letters[ch] = "_"

        key_html = '<div style="display:flex;flex-wrap:wrap;gap:4px;justify-content:center;margin-top:10px;">'
        for ch in "abcdefghijklmnopqrstuvwxyz":
            fb = all_letters.get(ch, "?")
            c = {"G": "#22c55e", "Y": "#ca8a04", "_": "#475569", "?": "#1e293b"}[fb]
            key_html += f'<div style="background:{c};color:#fff;border-radius:4px;padding:4px 8px;font-size:.75rem;font-weight:700;">{ch.upper()}</div>'
        key_html += "</div>"
        st.markdown(key_html, unsafe_allow_html=True)

    if st.button("🔄 New Word", use_container_width=True, key="wordle_reset_btn"):
        st.session_state.wordle_reset = True
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# GAME 3 — 20 QUESTIONS
# ═════════════════════════════════════════════════════════════════════════════

TWENTY_Q_CONCEPTS = [
    "elephant", "smartphone", "guitar", "volcano", "submarine",
    "telescope", "dinosaur", "refrigerator", "lighthouse", "butterfly",
    "solar panel", "chess board", "hot air balloon", "microscope", "pyramid",
    "black hole", "monsoon", "bonsai tree", "jetpack", "windmill",
]


def render_twenty_questions():
    st.markdown("""
<div style="background:linear-gradient(135deg,#1a0a20,#0a0010);border:1px solid rgba(167,139,250,0.3);
border-radius:16px;padding:24px 28px;margin-bottom:20px;">
  <div style="font-size:1.8rem;font-weight:900;color:#c4b5fd;margin-bottom:4px;">❓ 20 Questions</div>
  <div style="color:#94a3b8;font-size:.9rem;">AI thinks of something. Ask yes/no questions to guess it. You have 20 questions!</div>
</div>
""", unsafe_allow_html=True)

    if "tq_concept" not in st.session_state or st.session_state.get("tq_reset"):
        st.session_state.tq_concept = random.choice(TWENTY_Q_CONCEPTS)
        st.session_state.tq_questions = []
        st.session_state.tq_won = False
        st.session_state.tq_reset = False

    concept = st.session_state.tq_concept
    questions = st.session_state.tq_questions
    q_count = len(questions)
    won = st.session_state.tq_won

    # Progress bar
    st.progress(q_count / 20, text=f"Questions used: {q_count}/20")

    # Show history
    if questions:
        with st.expander(f"📋 Question History ({q_count})", expanded=True):
            for i, (q, a) in enumerate(questions):
                icon = "✅" if "yes" in a.lower() else "❌" if "no" in a.lower() else "❓"
                st.markdown(f"**{i+1}.** {q} → {icon} *{a}*")

    if won:
        st.success(f"🎉 Correct! It was **{concept.upper()}**! You got it in {q_count} questions!")
    elif q_count >= 20:
        st.error(f"😞 Out of questions! It was **{concept.upper()}**!")
    else:
        # Check if user is guessing the concept
        col1, col2 = st.columns([3, 1])
        with col1:
            user_q = st.text_input(
                "Ask a yes/no question or guess the answer:",
                placeholder="e.g. Is it alive? Can you hold it? Is it bigger than a car?",
                key=f"tq_input_{q_count}"
            )
        with col2:
            is_guess = st.checkbox("I'm guessing the answer", key="tq_is_guess")

        if st.button("Submit", type="primary", use_container_width=True, key="tq_submit"):
            if user_q.strip():
                if is_guess:
                    if user_q.strip().lower() in concept.lower() or concept.lower() in user_q.strip().lower():
                        st.session_state.tq_won = True
                        questions.append((f"[GUESS] {user_q}", f"YES! That's it!"))
                    else:
                        questions.append((f"[GUESS] {user_q}", "No, that's not it."))
                else:
                    # Use AI to answer yes/no
                    with st.spinner("Thinking..."):
                        prompt = (
                            f"You are playing a game of 20 Questions. You are thinking of: '{concept}'. "
                            f"The player asks: '{user_q}'. "
                            f"Answer ONLY with: 'Yes', 'No', or 'Sometimes'. "
                            f"Be accurate. One word answer only."
                        )
                        answer = _ai_call(prompt, max_tokens=10).strip()
                        if not answer:
                            answer = "Maybe"
                        questions.append((user_q, answer))
                st.session_state.tq_questions = questions
                st.rerun()

    col_r, col_h = st.columns(2)
    with col_r:
        if st.button("🔄 New Game", use_container_width=True, key="tq_reset_btn"):
            st.session_state.tq_reset = True
            st.rerun()
    with col_h:
        if st.button("💡 Give Up (Reveal)", use_container_width=True, key="tq_reveal"):
            st.info(f"The answer was: **{concept.upper()}**")


# ═════════════════════════════════════════════════════════════════════════════
# GAME 4 — AI TRIVIA BATTLE
# ═════════════════════════════════════════════════════════════════════════════

TRIVIA_CATEGORIES = [
    "Science", "History", "Geography", "Sports", "Technology",
    "Movies", "Literature", "Music", "Mathematics", "General Knowledge"
]


def _get_trivia_question(category: str) -> Optional[dict]:
    """Generate a trivia question via AI."""
    prompt = (
        f"Generate a trivia question about {category}. "
        f"Return ONLY valid JSON in this exact format (no markdown, no explanation): "
        f'{{ "question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], "answer": "A", "explanation": "..." }}'
    )
    raw = _ai_call(prompt, max_tokens=300)
    # Extract JSON from response
    try:
        # Find first { and last }
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:
        pass
    return None


def _ai_pick_answer(question_data: dict) -> str:
    """Have AI pick the correct answer."""
    prompt = (
        f"Question: {question_data.get('question', '')}\n"
        f"Options: {', '.join(question_data.get('options', []))}\n"
        f"What is the correct answer letter (A, B, C, or D)? Reply with ONLY the letter."
    )
    ans = _ai_call(prompt, max_tokens=5).strip().upper()
    if ans and ans[0] in "ABCD":
        return ans[0]
    return random.choice(["A", "B", "C", "D"])


def render_trivia_battle():
    st.markdown("""
<div style="background:linear-gradient(135deg,#1a0a00,#0a0500);border:1px solid rgba(251,191,36,0.3);
border-radius:16px;padding:24px 28px;margin-bottom:20px;">
  <div style="font-size:1.8rem;font-weight:900;color:#fde68a;margin-bottom:4px;">🏆 AI Trivia Battle</div>
  <div style="color:#94a3b8;font-size:.9rem;">You vs AI — answer the same question. Who knows more?</div>
</div>
""", unsafe_allow_html=True)

    if "trivia_scores" not in st.session_state:
        st.session_state.trivia_scores = {"You": 0, "AI": 0}
        st.session_state.trivia_q = None
        st.session_state.trivia_result = None
        st.session_state.trivia_q_count = 0

    scores = st.session_state.trivia_scores

    # Score bar
    c1, c2 = st.columns(2)
    c1.metric("🧑 Your Score", scores["You"])
    c2.metric("🤖 AI Score", scores["AI"])
    st.markdown("---")

    # Category selector
    category = st.selectbox("Choose category", TRIVIA_CATEGORIES, key="trivia_cat")

    if st.session_state.trivia_q is None:
        if st.button("🎲 Generate Question", type="primary", use_container_width=True, key="trivia_gen"):
            with st.spinner("AI generating a trivia question..."):
                q = _get_trivia_question(category)
                if q:
                    st.session_state.trivia_q = q
                    st.session_state.trivia_result = None
                    st.session_state.trivia_q_count += 1
                    st.rerun()
                else:
                    st.error("Could not generate question. Try again.")
    else:
        q_data = st.session_state.trivia_q

        st.markdown(f"""
<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);
border-radius:14px;padding:20px 24px;margin-bottom:16px;">
  <div style="font-size:.8rem;color:#94a3b8;letter-spacing:2px;margin-bottom:8px;">QUESTION #{st.session_state.trivia_q_count} · {category.upper()}</div>
  <div style="font-size:1.1rem;font-weight:700;color:#f8fafc;line-height:1.5;">{q_data.get('question', '')}</div>
</div>
""", unsafe_allow_html=True)

        options = q_data.get("options", [])
        correct = q_data.get("answer", "A")

        if st.session_state.trivia_result is None:
            user_ans = st.radio("Your answer:", options, key=f"trivia_radio_{st.session_state.trivia_q_count}")
            user_letter = user_ans[0] if user_ans else "A"

            if st.button("✅ Submit Answer", type="primary", use_container_width=True, key="trivia_submit"):
                with st.spinner("AI is also answering..."):
                    ai_letter = _ai_pick_answer(q_data)

                user_correct = (user_letter == correct)
                ai_correct   = (ai_letter == correct)

                if user_correct: st.session_state.trivia_scores["You"] += 1
                if ai_correct:   st.session_state.trivia_scores["AI"] += 1

                st.session_state.trivia_result = {
                    "user_ans": user_letter, "ai_ans": ai_letter,
                    "correct": correct, "user_correct": user_correct, "ai_correct": ai_correct
                }
                st.rerun()
        else:
            res = st.session_state.trivia_result
            correct_opt = next((o for o in options if o.startswith(res["correct"])), res["correct"])

            col_u, col_a = st.columns(2)
            with col_u:
                icon = "✅" if res["user_correct"] else "❌"
                st.markdown(f"""
<div style="background:{'rgba(34,197,94,0.1)' if res['user_correct'] else 'rgba(239,68,68,0.1)'};
border:1px solid {'#22c55e' if res['user_correct'] else '#ef4444'};
border-radius:12px;padding:16px;text-align:center;">
  <div style="font-size:2rem;">{icon}</div>
  <div style="font-weight:700;color:#f8fafc;margin:6px 0;">You answered: {res['user_ans']}</div>
  <div style="font-size:.85rem;color:#94a3b8;">{'Correct!' if res['user_correct'] else 'Wrong'}</div>
</div>""", unsafe_allow_html=True)

            with col_a:
                icon = "✅" if res["ai_correct"] else "❌"
                st.markdown(f"""
<div style="background:{'rgba(34,197,94,0.1)' if res['ai_correct'] else 'rgba(239,68,68,0.1)'};
border:1px solid {'#22c55e' if res['ai_correct'] else '#ef4444'};
border-radius:12px;padding:16px;text-align:center;">
  <div style="font-size:2rem;">🤖 {icon}</div>
  <div style="font-weight:700;color:#f8fafc;margin:6px 0;">AI answered: {res['ai_ans']}</div>
  <div style="font-size:.85rem;color:#94a3b8;">{'Correct!' if res['ai_correct'] else 'Wrong'}</div>
</div>""", unsafe_allow_html=True)

            st.markdown(f"""
<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
border-radius:10px;padding:14px;margin-top:12px;">
  <b style="color:#a5b4fc;">✅ Correct Answer:</b> {correct_opt}<br>
  <span style="color:#94a3b8;font-size:.9rem;">{q_data.get('explanation', '')}</span>
</div>""", unsafe_allow_html=True)

            if st.button("▶️ Next Question", type="primary", use_container_width=True, key="trivia_next"):
                st.session_state.trivia_q = None
                st.session_state.trivia_result = None
                st.rerun()

    if st.button("🔄 Reset Scores", use_container_width=True, key="trivia_reset"):
        st.session_state.trivia_scores = {"You": 0, "AI": 0}
        st.session_state.trivia_q = None
        st.session_state.trivia_result = None
        st.session_state.trivia_q_count = 0
        st.rerun()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN GAMES PAGE
# ═════════════════════════════════════════════════════════════════════════════

def render_games_page():
    """Main games hub page."""
    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(167,139,250,0.04));
border:1px solid rgba(99,102,241,0.15);border-radius:20px;padding:28px 32px;margin-bottom:24px;">
  <div style="font-family:monospace;font-size:10px;letter-spacing:4px;color:rgba(99,102,241,0.5);
  text-transform:uppercase;margin-bottom:8px;">STUDY BREAK · GAME ZONE</div>
  <div style="font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:6px;">🎮 AI Games</div>
  <div style="color:rgba(255,255,255,0.45);font-size:.9rem;">
    Challenge yourself and the AI · Tic-Tac-Toe · Wordle · 20 Questions · Trivia Battle
  </div>
</div>
""", unsafe_allow_html=True)

    tab_ttt, tab_wordle, tab_tq, tab_trivia = st.tabs([
        "🎮 Tic-Tac-Toe", "🟩 Wordle", "❓ 20 Questions", "🏆 Trivia Battle"
    ])

    with tab_ttt:
        render_tictactoe()

    with tab_wordle:
        render_wordle()

    with tab_tq:
        render_twenty_questions()

    with tab_trivia:
        render_trivia_battle()

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="games_back"):
        st.session_state.app_mode = "chat"
        st.rerun()
