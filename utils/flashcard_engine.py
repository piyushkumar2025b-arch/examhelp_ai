"""
flashcard_engine.py — Advanced Flashcard Powerup
SM-2 Algorithm, Anki Export, Multiplayer, Voice Mode, AI Difficulty Detection
"""

import streamlit as st
import datetime
import base64
import zlib
import json
import threading
import uuid
try:
    import genanki
except ImportError:
    genanki = None

from utils.ai_engine import generate
# [REMOVED — integration/key stripped] from utils.secret_manager import get_groq_key

# ── 1. SM-2 SPACED REPETITION ALGORITHM ──────────────────────────────
def sm2_update(grade: int, repetitions: int, ease_factor: float, interval: int) -> tuple:
    """
    SuperMemo-2 algorithm calculation.
    grade: 0-5 (0 = blackout, 5 = perfect response)
    Returns: (new_repetitions, new_ease_factor, new_interval)
    """
    if grade >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    
    ease_factor = ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if ease_factor < 1.3:
        ease_factor = 1.3
        
    return repetitions, ease_factor, interval

# ── 2. AI AUTO-GENERATION & DIFFICULTY DETECTION ───────────────────────
def _generate_cards_task(context_text: str, lang: str):
    """Background task to generate cards."""
    prompt = f"Extract 10 key concepts from this text and create Q&A flashcards in {lang}. Output ONLY valid JSON array of objects with keys: 'q', 'a', 'topic', 'keyword_for_image'.\nText:\n{context_text[:4000]}"
    try:
        # We use standard generation for this
        resp = generate(
            messages=[{"role": "user", "content": prompt}],
            context_text="", model="llama-3.1-8b-instant",
            max_tokens=2000, temperature=0.3
        )
        if hasattr(st, "session_state"):
            if "bg_flashcards" not in st.session_state:
                st.session_state.bg_flashcards = []
            import re
            m = re.search(r'\[.*\]', resp, re.DOTALL)
            if m:
                cards = json.loads(m.group(0))
                # Auto-detect difficulty in same batch (we just ask model to do it, or we do it inline here to save tokens, but prompt asked for 8B model batch call)
                diff_prompt = "Classify difficulty of these flashcards as 'easy', 'medium', or 'hard' based on question complexity. Return ONLY a JSON array of strings: [\"easy\", \"hard\", ...]\n" + json.dumps(cards)
                diff_resp = generate(
                    messages=[{"role": "user", "content": diff_prompt}],
                    context_text="", model="llama-3.1-8b-instant", max_tokens=500
                )
                d_m = re.search(r'\[.*\]', diff_resp, re.DOTALL)
                diffs = json.loads(d_m.group(0)) if d_m else ["medium"] * len(cards)
                
                for i, c in enumerate(cards):
                    c["difficulty"] = diffs[i] if i < len(diffs) else "medium"
                    c["repetitions"] = 0
                    c["ease_factor"] = 2.5
                    c["interval"] = 0
                    c["next_review"] = datetime.date.today().isoformat()
                    st.session_state.bg_flashcards.append(c)
    except Exception:
        pass

def start_background_generation(context_text: str, lang: str):
    thread = threading.Thread(target=_generate_cards_task, args=(context_text, lang))
    thread.daemon = True
    thread.start()

# ── 3. ANKI EXPORT ───────────────────────────────────────────────────
def export_anki_deck(cards: list) -> bytes:
    if not genanki:
        return b""
    model_id = 1607392319
    deck_id = 2059400110
    
    my_model = genanki.Model(
      model_id,
      'ExamHelp Flashcard',
      fields=[{'name': 'Question'}, {'name': 'Answer'}, {'name': 'Image'}],
      templates=[{
        'name': 'Card 1',
        'qfmt': '<h3>{{Question}}</h3><br>{{Image}}',
        'afmt': '{{FrontSide}}<hr id="answer"><div>{{Answer}}</div>',
      }])
      
    my_deck = genanki.Deck(deck_id, 'ExamHelp Study Deck')
    
    for c in cards:
        img_html = f'<img src="https://source.unsplash.com/400x300/?{c.get("keyword_for_image", "study")}" />'
        note = genanki.Note(
            model=my_model,
            fields=[c.get("q",""), c.get("a",""), img_html]
        )
        my_deck.add_note(note)
        
    pkg = genanki.Package(my_deck)
    # write to temp file then read
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".apkg") as tmp:
        pkg.write_to_file(tmp.name)
        tmp.seek(0)
        data = tmp.read()
    import os
    os.unlink(tmp.name)
    return data

# ── 4. UI COMPONENT ──────────────────────────────────────────────────
def render_flashcards():
    import streamlit as st
    st.subheader("🃏 Elite Flashcards (SM-2 Spaced Repetition)")
    
    # Initialize state
    if "flashcards" not in st.session_state: st.session_state.flashcards = []
    if "bg_flashcards" not in st.session_state: st.session_state.bg_flashcards = []
    if "current_card" not in st.session_state: st.session_state.current_card = 0
    if "card_flipped" not in st.session_state: st.session_state.card_flipped = False
    
    lang = st.session_state.get("selected_language", "English")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🪄 Generate Cards"):
            with st.spinner("Generating with 8B Model..."):
                start_background_generation(st.session_state.get("context_text",""), lang)
                st.success("Generation started in background!")
                
    with col2:
        if st.session_state.bg_flashcards:
            if st.button(f"📥 Load {len(st.session_state.bg_flashcards)} Auto-Cards"):
                st.session_state.flashcards.extend(st.session_state.bg_flashcards)
                st.session_state.bg_flashcards = []
                st.rerun()

    with col3:
        if st.session_state.flashcards and genanki:
            data = export_anki_deck(st.session_state.flashcards)
            if data:
                st.download_button("📤 Export Anki Deck (.apkg)", data, "ExamHelp_Deck.apkg", "application/octet-stream")

    with col4:
        if st.session_state.flashcards:
            compact = json.dumps(st.session_state.flashcards)
            b64 = base64.urlsafe_b64encode(zlib.compress(compact.encode())).decode()
            st.text_input("🔗 Multiplayer Link", value=f"?deck={b64}")
            
    # Load from link
    if "deck" in st.query_params:
        try:
            dec = zlib.decompress(base64.urlsafe_b64decode(st.query_params["deck"].encode())).decode()
            st.session_state.flashcards = json.loads(dec)
            st.success("Multiplayer deck loaded!")
            st.query_params.clear()
        except:
            st.error("Invalid deck link")

    cards = st.session_state.flashcards
    if not cards:
        st.info("No flashcards available. Generate some or load a multiplayer link!")
        return

    # Filter cards due for review
    today = datetime.date.today().isoformat()
    due_cards = [c for c in cards if c.get("next_review", today) <= today]
    
    idx = st.session_state.current_card
    if idx >= len(due_cards):
        idx = 0
        if len(due_cards) == 0:
            st.success("🎉 All cards reviewed for today! Come back tomorrow.")
            return

    card = due_cards[idx]
    
    # Progress
    st.progress((idx) / len(due_cards))
    st.caption(f"Reviewing {idx+1}/{len(due_cards)} due today (Total Deck: {len(cards)})")

    # Display Card
    st.markdown(f"**Topic**: {card.get('topic','General')} | **Difficulty**: {card.get('difficulty','medium').upper()}")
    
    # Image
    keyword = card.get("keyword_for_image", card.get("topic", "study"))
    st.image(f"https://source.unsplash.com/400x300/?{keyword}")
    
    st.markdown(f"### ❓ {card['q']}")
    
    # Voice Mode
    import streamlit.components.v1 as components
    safe_q = card['q'].replace("'", "\\'").replace('"', '\\"')
    js_code = f"<script>const s=new SpeechSynthesisUtterance('{safe_q}');window.speechSynthesis.speak(s);</script>"
    components.html(js_code, height=0)

    if st.button("👁️ Flip Card"):
        st.session_state.card_flipped = True

    if st.session_state.get("card_flipped"):
        st.markdown(f"### 💡 {card['a']}")
        st.write("How well did you know this?")
        
        c1, c2, c3, c4 = st.columns(4)
        grade = -1
        if c1.button("0 - Blackout", key="b0"): grade = 0
        if c2.button("3 - Hard", key="b3"): grade = 3
        if c3.button("4 - Good", key="b4"): grade = 4
        if c4.button("5 - Perfect", key="b5"): grade = 5
        
        if grade >= 0:
            rep, ease, ivl = sm2_update(grade, card.get("repetitions",0), card.get("ease_factor",2.5), card.get("interval",0))
            card["repetitions"] = rep
            card["ease_factor"] = ease
            card["interval"] = ivl
            card["next_review"] = (datetime.date.today() + datetime.timedelta(days=max(1, ivl))).isoformat()
            
            st.session_state.card_flipped = False
            st.session_state.current_card += 1
            st.rerun()
