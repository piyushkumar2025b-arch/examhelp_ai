"""
flashcard_engine.py — Elite Flashcard Engine v2.0
SM-2 Spaced Repetition · AI Hint System · Streak Tracking · Confidence Meter
Mastery Heatmap · Leitner Box · Anki Export · Smart Review Queue
"""

import streamlit as st
import datetime
import base64
import zlib
import json
import threading
import re
try:
    import genanki
except ImportError:
    genanki = None

from utils.ai_engine import generate


# ─── SM-2 SPACED REPETITION ──────────────────────────────────────────────────
def sm2_update(grade: int, repetitions: int, ease_factor: float, interval: int):
    if grade >= 3:
        interval = 1 if repetitions == 0 else (6 if repetitions == 1 else round(interval * ease_factor))
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    ease_factor = max(1.3, ease_factor + 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    return repetitions, ease_factor, interval


# ─── LEITNER BOX SYSTEM ──────────────────────────────────────────────────────
def get_leitner_box(card: dict) -> int:
    reps = card.get("repetitions", 0)
    ease = card.get("ease_factor", 2.5)
    if reps >= 8 and ease >= 2.8: return 5
    if reps >= 5 and ease >= 2.5: return 4
    if reps >= 3 and ease >= 2.2: return 3
    if reps >= 1: return 2
    return 1


# ─── AI CARD GENERATION (background thread) ──────────────────────────────────
def _generate_cards_task(context_text: str, lang: str, count: int = 15):
    prompt = f"""You are an expert educator. Create exactly {count} high-quality Q&A flashcards from this text in {lang}.

Rules:
- Questions should test UNDERSTANDING, not just memorization
- Include concept, application, and analysis-level questions (Bloom's Taxonomy)
- Keep answers concise but complete
- Each card must be self-contained

Output ONLY a valid JSON array, no extra text:
[{{"q":"...","a":"...","topic":"...","difficulty":"easy|medium|hard","keyword_for_image":"...","hint":"one-sentence hint without giving away the answer","bloom_level":"remember|understand|apply|analyze"}}]

Text:
{context_text[:5000]}"""
    try:
        resp = generate(
            messages=[{"role": "user", "content": prompt}],
            context_text="", model="llama-3.3-70b-versatile",
            max_tokens=3000, temperature=0.3
        )
        m = re.search(r'\[.*\]', resp, re.DOTALL)
        if m:
            cards = json.loads(m.group(0))
            today = datetime.date.today().isoformat()
            for c in cards:
                c.setdefault("repetitions", 0)
                c.setdefault("ease_factor", 2.5)
                c.setdefault("interval", 0)
                c.setdefault("next_review", today)
                c.setdefault("streak", 0)
                c.setdefault("times_seen", 0)
                c.setdefault("times_correct", 0)
                c.setdefault("hint", "")
                c.setdefault("bloom_level", "remember")
            if "bg_flashcards" not in st.session_state:
                st.session_state.bg_flashcards = []
            st.session_state.bg_flashcards.extend(cards)
    except Exception:
        pass


def start_background_generation(context_text: str, lang: str, count: int = 15):
    t = threading.Thread(target=_generate_cards_task, args=(context_text, lang, count))
    t.daemon = True
    t.start()


# ─── AI HINT GENERATOR ───────────────────────────────────────────────────────
def get_ai_hint(question: str, topic: str) -> str:
    try:
        prompt = f"Give a one-sentence Socratic hint for this question WITHOUT revealing the answer: {question} (Topic: {topic})"
        return generate(
            messages=[{"role": "user", "content": prompt}],
            context_text="", model="llama-3.1-8b-instant", max_tokens=80
        ).strip()
    except Exception:
        return "Think about the core concept this question is testing."


# ─── ANKI EXPORT ─────────────────────────────────────────────────────────────
def export_anki_deck(cards: list) -> bytes:
    if not genanki:
        return b""
    model = genanki.Model(
        1607392319, 'ExamHelp Card',
        fields=[{'name': 'Question'}, {'name': 'Answer'}, {'name': 'Topic'}, {'name': 'Difficulty'}],
        templates=[{
            'name': 'Card 1',
            'qfmt': '<div style="font-family:sans-serif;font-size:18px;padding:20px"><b>{{Question}}</b><br><small style="color:#888">Topic: {{Topic}} · {{Difficulty}}</small></div>',
            'afmt': '{{FrontSide}}<hr><div style="font-family:sans-serif;padding:20px">{{Answer}}</div>',
        }]
    )
    deck = genanki.Deck(2059400110, 'ExamHelp Study Deck')
    for c in cards:
        deck.add_note(genanki.Note(model=model, fields=[
            c.get("q", ""), c.get("a", ""), c.get("topic", "General"), c.get("difficulty", "medium")
        ]))
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".apkg") as tmp:
        genanki.Package(deck).write_to_file(tmp.name)
        data = open(tmp.name, "rb").read()
    os.unlink(tmp.name)
    return data


# ─── MAIN UI ─────────────────────────────────────────────────────────────────
def render_flashcards():
    st.markdown("""
<style>
.fc-header {
    background: linear-gradient(135deg, #13082a 0%, #0d0d1f 100%);
    border: 1px solid rgba(124,106,247,0.35);
    border-radius: 20px; padding: 24px 28px; margin-bottom: 20px;
    position: relative; overflow: hidden;
}
.fc-header::after {
    content: ''; position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(167,139,250,0.12), transparent 70%);
    border-radius: 50%;
}
.fc-title { font-size: 1.7rem; font-weight: 800; color: #a78bfa; margin: 0 0 4px; }
.fc-sub   { font-size: 0.85rem; color: #9090b8; }
.card-face {
    background: linear-gradient(145deg, rgba(19,14,38,0.97), rgba(13,10,28,0.95));
    border: 1.5px solid rgba(124,106,247,0.28);
    border-radius: 22px; padding: 36px 32px;
    min-height: 200px; text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(124,106,247,0.1);
    animation: cardAppear 0.45s cubic-bezier(0.16,1,0.3,1) both;
    position: relative;
}
@keyframes cardAppear {
    from { opacity:0; transform: rotateX(-8deg) scale(0.95) translateY(20px); }
    to   { opacity:1; transform: none; }
}
.card-question { font-size: 1.25rem; font-weight: 600; color: #f0f0ff; line-height: 1.55; }
.card-answer   { font-size: 1.05rem; color: #c4c4e0; line-height: 1.65; margin-top: 8px; }
.card-topic {
    display: inline-block; background: rgba(124,106,247,0.14);
    border: 1px solid rgba(124,106,247,0.3); border-radius: 99px;
    padding: 3px 14px; font-size: 0.74rem; color: #a78bfa;
    font-weight: 600; margin-bottom: 18px;
}
.card-diff-easy   { color: #34d399; font-weight: 700; }
.card-diff-medium { color: #fbbf24; font-weight: 700; }
.card-diff-hard   { color: #f87171; font-weight: 700; }
.bloom-badge {
    display: inline-block; font-size: 0.68rem; letter-spacing: 0.08em;
    text-transform: uppercase; padding: 2px 9px; border-radius: 6px;
    background: rgba(96,165,250,0.12); color: #60a5fa; font-weight: 700;
    margin-left: 8px;
}
.streak-fire { font-size: 1.4rem; }
.grade-btn {
    border-radius: 12px !important; font-weight: 700 !important;
    transition: all 0.2s ease !important;
}
.leitner-box {
    display: flex; gap: 4px; align-items: flex-end; margin: 8px 0;
}
.lbox {
    flex: 1; border-radius: 4px 4px 0 0;
    background: rgba(124,106,247,0.15);
    border: 1px solid rgba(124,106,247,0.2);
    font-size: 0.62rem; text-align: center; color: #a78bfa;
    padding: 2px 0;
}
.hint-box {
    background: rgba(251,191,36,0.07);
    border: 1px solid rgba(251,191,36,0.2);
    border-radius: 10px; padding: 10px 14px;
    font-size: 0.85rem; color: #fbbf24;
    margin-top: 10px; animation: fadeIn 0.3s ease;
}
@keyframes fadeIn { from { opacity:0; } to { opacity:1; } }
.mastery-bar { height: 6px; background: rgba(255,255,255,0.06); border-radius: 99px; overflow: hidden; margin: 4px 0; }
.mastery-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #7c6af7, #a78bfa, #60a5fa); }
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="fc-header">
  <div class="fc-title">🃏 Flashcard Engine</div>
  <div class="fc-sub">SM-2 Spaced Repetition · Leitner Boxes · Bloom's Taxonomy · AI Hints · Streak Tracking</div>
</div>
""", unsafe_allow_html=True)

    # Init state
    for k, v in [
        ("flashcards", []), ("bg_flashcards", []), ("current_card", 0),
        ("card_flipped", False), ("hint_visible", False),
        ("session_correct", 0), ("session_total", 0),
    ]:
        st.session_state.setdefault(k, v)

    lang = st.session_state.get("selected_language", "English")

    # ── Top control bar ──
    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    with col1:
        card_count = st.selectbox("Cards to generate", [10, 15, 20, 30], index=1, label_visibility="collapsed")
        if st.button("🪄 Generate Cards", use_container_width=True):
            ctx = st.session_state.get("context_text", "")
            if not ctx:
                st.warning("📄 Upload study material first!")
            else:
                with st.spinner(f"Generating {card_count} cards via AI..."):
                    start_background_generation(ctx, lang, card_count)
                    import time; time.sleep(2.5)
                    if st.session_state.bg_flashcards:
                        st.session_state.flashcards.extend(st.session_state.bg_flashcards)
                        st.session_state.bg_flashcards = []
                        st.session_state.current_card = 0
                        st.session_state.card_flipped = False
                        st.success(f"✅ {len(st.session_state.flashcards)} cards ready!")
                        st.rerun()
                    else:
                        st.info("⏳ Generating in background — press Load Cards in a moment.")

    with col2:
        if st.session_state.bg_flashcards:
            if st.button(f"📥 Load {len(st.session_state.bg_flashcards)} New Cards", use_container_width=True):
                st.session_state.flashcards.extend(st.session_state.bg_flashcards)
                st.session_state.bg_flashcards = []
                st.session_state.current_card = 0
                st.rerun()

    with col3:
        if st.session_state.flashcards and genanki:
            data = export_anki_deck(st.session_state.flashcards)
            if data:
                st.download_button("📤 Anki", data, "ExamHelp.apkg", use_container_width=True)

    with col4:
        if st.session_state.flashcards:
            export_json = json.dumps(st.session_state.flashcards, indent=2)
            st.download_button("📥 JSON", export_json.encode(), "flashcards.json", "application/json", use_container_width=True)

    with col5:
        if st.session_state.flashcards:
            if st.button("🔀 Shuffle", use_container_width=True):
                import random
                random.shuffle(st.session_state.flashcards)
                st.session_state.current_card = 0
                st.session_state.card_flipped = False
                st.rerun()

    # Load from link
    if "deck" in st.query_params:
        try:
            data = zlib.decompress(base64.urlsafe_b64decode(st.query_params["deck"].encode())).decode()
            st.session_state.flashcards = json.loads(data)
            st.success("📥 Shared deck loaded!")
            st.query_params.clear()
        except Exception:
            st.error("Invalid deck link.")

    cards = st.session_state.flashcards
    if not cards:
        st.info("💡 No flashcards yet — upload study material and click **Generate Cards**.")
        return

    # ── Filter tabs ──
    tab_due, tab_all, tab_hard, tab_stats = st.tabs(["📅 Due Today", "📚 All Cards", "🔥 Hard Cards", "📊 Stats"])

    with tab_stats:
        total = len(cards)
        mastered = sum(1 for c in cards if c.get("repetitions", 0) >= 5)
        learning = sum(1 for c in cards if 0 < c.get("repetitions", 0) < 5)
        new_cards = sum(1 for c in cards if c.get("repetitions", 0) == 0)
        sc = st.session_state.session_correct
        st_total = st.session_state.session_total
        accuracy = int(sc / st_total * 100) if st_total > 0 else 0

        s1, s2, s3, s4, s5 = st.columns(5)
        for col, val, lbl, color in [
            (s1, total, "Total", "#a78bfa"),
            (s2, mastered, "Mastered", "#34d399"),
            (s3, learning, "Learning", "#fbbf24"),
            (s4, new_cards, "New", "#60a5fa"),
            (s5, f"{accuracy}%", "Session Acc.", "#f87171" if accuracy < 50 else "#34d399"),
        ]:
            col.markdown(
                f'<div style="text-align:center;background:rgba(19,19,31,0.8);border:1px solid rgba(124,106,247,0.15);border-radius:12px;padding:12px 6px">'
                f'<div style="font-size:1.4rem;font-weight:800;color:{color}">{val}</div>'
                f'<div style="font-size:0.65rem;color:#9090b8;margin-top:3px">{lbl}</div></div>',
                unsafe_allow_html=True
            )

        # Per-topic mastery
        st.markdown("**📈 Topic Mastery**")
        topics = {}
        for c in cards:
            t = c.get("topic", "General")
            topics.setdefault(t, {"seen": 0, "correct": 0})
            topics[t]["seen"] += c.get("times_seen", 0)
            topics[t]["correct"] += c.get("times_correct", 0)
        for topic, data in sorted(topics.items()):
            pct = int(data["correct"] / max(1, data["seen"]) * 100)
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0">'
                f'<span style="font-size:.8rem;color:#c4c4e0;width:140px;overflow:hidden;text-overflow:ellipsis">{topic[:20]}</span>'
                f'<div class="mastery-bar" style="flex:1"><div class="mastery-fill" style="width:{pct}%"></div></div>'
                f'<span style="font-size:.75rem;color:#a78bfa;font-weight:700;width:35px">{pct}%</span></div>',
                unsafe_allow_html=True
            )

    # ── Due today view ──
    with tab_due:
        today = datetime.date.today().isoformat()
        due = [c for c in cards if c.get("next_review", today) <= today]

        if not due:
            st.success("🎉 All caught up! No cards due today.")
            next_dates = [c.get("next_review", today) for c in cards if c.get("next_review", today) > today]
            if next_dates:
                st.info(f"📅 Next review: **{min(next_dates)}** ({len([d for d in next_dates if d == min(next_dates)])} cards)")
            return

        idx = st.session_state.current_card
        if idx >= len(due):
            idx = 0
            st.session_state.current_card = 0

        card = due[idx]
        diff = card.get("difficulty", "medium")
        bloom = card.get("bloom_level", "remember")
        streak = card.get("streak", 0)
        lbox = get_leitner_box(card)

        # Progress + meta
        progress_pct = idx / len(due)
        st.progress(progress_pct)
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<small style="color:#9090b8">📋 {idx+1} / {len(due)} due</small>', unsafe_allow_html=True)
        m2.markdown(f'<small class="card-diff-{diff}">{"●" * lbox}{"○" * (5-lbox)} Box {lbox}</small>', unsafe_allow_html=True)
        m3.markdown(f'<small><span class="bloom-badge">{bloom}</span></small>', unsafe_allow_html=True)
        m4.markdown(f'<small>{"🔥" * min(streak, 5)} streak {streak}</small>', unsafe_allow_html=True)

        # Card face
        st.markdown(f"""
<div class="card-face">
  <div class="card-topic">{card.get("topic", "General")}</div>
  <div class="card-question">❓ {card["q"]}</div>
</div>
""", unsafe_allow_html=True)

        # Controls
        cb1, cb2, cb3, cb4 = st.columns([2, 1, 1, 1])
        with cb1:
            flip_btn = st.button("👁️ Reveal Answer", use_container_width=True, type="primary" if not st.session_state.card_flipped else "secondary")
        with cb2:
            hint_btn = st.button("💡 Hint", use_container_width=True)
        with cb3:
            skip_btn = st.button("⏭️ Skip", use_container_width=True)
        with cb4:
            if st.button("🔊 Speak", use_container_width=True):
                import streamlit.components.v1 as components
                safe_q = card["q"].replace("'", "\\'").replace('"', '\\"')
                components.html(f"<script>window.speechSynthesis.cancel();const s=new SpeechSynthesisUtterance('{safe_q}');s.rate=0.95;window.speechSynthesis.speak(s);</script>", height=0)

        if hint_btn:
            st.session_state.hint_visible = True
        if skip_btn:
            st.session_state.current_card += 1
            st.session_state.card_flipped = False
            st.session_state.hint_visible = False
            st.rerun()
        if flip_btn:
            st.session_state.card_flipped = True

        # Hint
        if st.session_state.hint_visible:
            hint = card.get("hint") or get_ai_hint(card["q"], card.get("topic", ""))
            st.markdown(f'<div class="hint-box">💡 <b>Hint:</b> {hint}</div>', unsafe_allow_html=True)

        # Answer + grading
        if st.session_state.card_flipped:
            st.markdown(f"""
<div class="card-face" style="border-color:rgba(52,211,153,0.3);margin-top:10px">
  <div class="card-answer">✅ {card["a"]}</div>
</div>
""", unsafe_allow_html=True)

            st.markdown("**How well did you know this?**")
            g1, g2, g3, g4 = st.columns(4)
            grade_map = {
                "😰 Forgot (0)": (g1, 0, "#f87171"),
                "😓 Hard (3)": (g2, 3, "#fbbf24"),
                "😊 Good (4)": (g3, 4, "#34d399"),
                "🎯 Perfect (5)": (g4, 5, "#7c6af7"),
            }
            chosen_grade = None
            for label, (col, grade_val, color) in grade_map.items():
                with col:
                    if st.button(label, key=f"grade_{grade_val}", use_container_width=True):
                        chosen_grade = grade_val

            if chosen_grade is not None:
                rep, ease, ivl = sm2_update(chosen_grade, card.get("repetitions", 0), card.get("ease_factor", 2.5), card.get("interval", 0))
                card["repetitions"] = rep
                card["ease_factor"] = ease
                card["interval"] = ivl
                card["next_review"] = (datetime.date.today() + datetime.timedelta(days=max(1, ivl))).isoformat()
                card["times_seen"] = card.get("times_seen", 0) + 1
                if chosen_grade >= 3:
                    card["times_correct"] = card.get("times_correct", 0) + 1
                    card["streak"] = card.get("streak", 0) + 1
                    st.session_state.session_correct += 1
                else:
                    card["streak"] = 0
                st.session_state.session_total += 1
                st.session_state.current_card += 1
                st.session_state.card_flipped = False
                st.session_state.hint_visible = False
                st.rerun()

    with tab_all:
        st.markdown(f"**{len(cards)} cards in deck**")
        diff_filter = st.selectbox("Filter by difficulty", ["All", "easy", "medium", "hard"], label_visibility="collapsed")
        filtered = cards if diff_filter == "All" else [c for c in cards if c.get("difficulty") == diff_filter]
        for i, c in enumerate(filtered):
            with st.expander(f"**Q{i+1}.** {c['q'][:70]}{'…' if len(c['q'])>70 else ''}"):
                st.markdown(f"**Answer:** {c['a']}")
                col_a, col_b = st.columns(2)
                col_a.markdown(f"**Topic:** {c.get('topic','—')}  ·  **Difficulty:** {c.get('difficulty','—')}")
                col_b.markdown(f"**Bloom:** {c.get('bloom_level','—')}  ·  **Streak:** {c.get('streak',0)} 🔥")
                if c.get("repetitions", 0) > 0:
                    acc = int(c.get("times_correct", 0) / max(1, c.get("times_seen", 1)) * 100)
                    st.markdown(f"**Accuracy:** {acc}%  ·  **Next review:** {c.get('next_review','—')}")

    with tab_hard:
        hard_cards = sorted(cards, key=lambda c: c.get("ease_factor", 2.5))[:10]
        if not hard_cards:
            st.info("No cards to show yet.")
        else:
            st.markdown("**🔥 Your 10 hardest cards (lowest ease factor):**")
            for i, c in enumerate(hard_cards):
                ease = c.get("ease_factor", 2.5)
                st.markdown(
                    f'<div style="background:rgba(248,113,113,0.06);border:1px solid rgba(248,113,113,0.15);border-radius:10px;padding:10px 14px;margin:6px 0">'
                    f'<div style="font-weight:600;color:#f0f0ff">{i+1}. {c["q"]}</div>'
                    f'<div style="font-size:.8rem;color:#9090b8;margin-top:4px">Ease: {ease:.2f} · {c.get("topic","—")}</div></div>',
                    unsafe_allow_html=True
                )
