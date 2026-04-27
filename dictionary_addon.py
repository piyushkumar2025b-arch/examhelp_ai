"""
dictionary_addon.py
Additions to dictionary_engine.py:
  - Word of the Day (Free Dictionary API)
  - Etymology explorer
  - Synonyms/Antonyms visual map
  - Pronunciation guide
  - Word in different languages (LibreTranslate)
  - Vocabulary quiz generator
"""
import streamlit as st
import urllib.request
import urllib.parse
import json
import random

WORD_OF_DAY_FALLBACK = [
    {"word":"ephemeral","meaning":"Lasting for a very short time","example":"The ephemeral beauty of cherry blossoms","etymology":"Greek ephemeros - lasting a day"},
    {"word":"perspicacious","meaning":"Having a ready insight; shrewd","example":"Her perspicacious analysis impressed everyone","etymology":"Latin perspicax - sharp-sighted"},
    {"word":"sycophant","meaning":"A person who acts obsequiously toward someone important","example":"The politician was surrounded by sycophants","etymology":"Greek sykophantes - informer"},
    {"word":"mellifluous","meaning":"Sweet or musical; pleasant to hear","example":"Her mellifluous voice filled the hall","etymology":"Latin mel (honey) + fluere (to flow)"},
    {"word":"ubiquitous","meaning":"Present, appearing, or found everywhere","example":"Smartphones have become ubiquitous","etymology":"Latin ubique - everywhere"},
    {"word":"serendipity","meaning":"The occurrence of fortunate events by chance","example":"Finding the job was pure serendipity","etymology":"Coined by Horace Walpole from a fairy tale"},
    {"word":"eloquent","meaning":"Fluent or persuasive in speaking or writing","example":"An eloquent speech moved the audience","etymology":"Latin eloqui - to speak out"},
    {"word":"luminous","meaning":"Bright or shining, especially in the dark","example":"Her luminous smile lit up the room","etymology":"Latin lumen - light"},
]

def _fetch_free_dictionary(word: str) -> dict:
    """Fetch word data from Free Dictionary API (no key needed)."""
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        req = urllib.request.Request(url, headers={"User-Agent":"ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read().decode())
            if isinstance(data, list) and data:
                return data[0]
    except Exception:
        pass
    return {}

def _fetch_word_of_day() -> dict:
    """Get word of the day - uses Wordnik free API or fallback."""
    try:
        url = "https://api.wordnik.com/v4/words.json/wordOfTheDay?api_key=a2a73e7b947cad4db31&format=json"
        req = urllib.request.Request(url, headers={"User-Agent":"ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            data = json.loads(r.read().decode())
            return {
                "word": data.get("word",""),
                "meaning": data.get("definitions",[{}])[0].get("text","") if data.get("definitions") else "",
                "example": data.get("examples",[{}])[0].get("text","") if data.get("examples") else "",
            }
    except Exception:
        return random.choice(WORD_OF_DAY_FALLBACK)

LANGUAGE_MAP = {
    "Hindi":"hi","Spanish":"es","French":"fr","German":"de",
    "Arabic":"ar","Japanese":"ja","Chinese (Simplified)":"zh",
    "Russian":"ru","Portuguese":"pt","Italian":"it"
}

def render_dictionary_addon():
    """Render addon features for AI Dictionary."""

    st.markdown("""
    <style>
    .dict-wod {
        background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(6,182,212,0.08));
        border: 1px solid rgba(99,102,241,0.25); border-radius: 20px; padding: 24px;
        margin-bottom: 20px; position: relative; overflow: hidden;
    }
    .dict-wod::before { content:''; position:absolute; top:-1px; left:10%; right:10%;
        height:2px; background:linear-gradient(90deg,transparent,#6366f1,#06b6d4,transparent); }
    .dict-wod-word { font-family:'Syne',sans-serif; font-size:2rem; font-weight:800;
        background:linear-gradient(135deg,#fff,#c7d2fe,#818cf8);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
    .dict-syn { display:inline-block; background:rgba(16,185,129,0.1);
        border:1px solid rgba(16,185,129,0.25); border-radius:100px;
        padding:4px 14px; margin:3px; font-size:0.78rem; color:#6ee7b7;
        cursor:pointer; transition:all 0.2s ease; }
    .dict-syn:hover { background:rgba(16,185,129,0.2); transform:translateY(-2px); }
    .dict-ant { display:inline-block; background:rgba(239,68,68,0.08);
        border:1px solid rgba(239,68,68,0.2); border-radius:100px;
        padding:4px 14px; margin:3px; font-size:0.78rem; color:#fca5a5; }
    .dict-phonetic { font-family:'JetBrains Mono',monospace; font-size:1rem;
        color:#818cf8; margin-top:4px; }
    </style>
    """, unsafe_allow_html=True)

    d1, d2, d3, d4, d5 = st.tabs([
        "⭐ Word of the Day", "🔍 Deep Lookup", "🌐 Translate Word", "🎯 Vocab Quiz", "📚 Etymology"
    ])

    # ── Tab 1: Word of the Day ──────────────────────────────
    with d1:
        if "dict_wod" not in st.session_state:
            st.session_state.dict_wod = _fetch_word_of_day()

        wod = st.session_state.dict_wod
        st.markdown(f"""
        <div class="dict-wod">
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;letter-spacing:3px;
                color:#818cf8;margin-bottom:12px;">⭐ WORD OF THE DAY</div>
            <div class="dict-wod-word">{wod.get('word','').title()}</div>
            <div style="font-size:0.95rem;color:rgba(255,255,255,0.65);margin-top:10px;line-height:1.7;">
                {wod.get('meaning','')}</div>
            {f'<div style="margin-top:12px;font-style:italic;color:rgba(255,255,255,0.4);font-size:0.85rem;">"{wod.get("example","")}"</div>' if wod.get('example') else ''}
            {f'<div style="margin-top:10px;font-size:0.78rem;color:rgba(99,102,241,0.8);font-family:JetBrains Mono,monospace;">Etymology: {wod.get("etymology","")}</div>' if wod.get('etymology') else ''}
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 New Word of the Day", key="dict_new_wod", use_container_width=True):
            st.session_state.dict_wod = random.choice(WORD_OF_DAY_FALLBACK)
            st.rerun()

        # Add to vocab list
        if st.button("➕ Add to My Vocabulary", key="dict_add_vocab", use_container_width=True):
            vocab = st.session_state.get("dict_vocab_list", [])
            if wod.get("word") not in [v.get("word") for v in vocab]:
                vocab.append(wod)
                st.session_state.dict_vocab_list = vocab
                st.success(f"✅ '{wod.get('word')}' added to your vocabulary list!")
            else:
                st.info("Already in your list.")

        if st.session_state.get("dict_vocab_list"):
            st.markdown("---")
            st.markdown("**📚 My Vocabulary List:**")
            for v in st.session_state.dict_vocab_list:
                st.markdown(f"• **{v.get('word')}** — {v.get('meaning','')[:80]}")

    # ── Tab 2: Deep Word Lookup ─────────────────────────────
    with d2:
        lookup_word = st.text_input("Enter any English word:", placeholder="e.g. serendipity",
                                    key="dict_lookup_word")
        if lookup_word and st.button("🔍 Deep Lookup", type="primary", key="dict_lookup_btn", use_container_width=True):
            with st.spinner("Fetching word data..."):
                data = _fetch_free_dictionary(lookup_word)

            if data:
                word = data.get("word","")
                phonetics = data.get("phonetics",[])
                phonetic_text = next((p.get("text","") for p in phonetics if p.get("text")), "")
                meanings = data.get("meanings",[])

                st.markdown(f"""
                <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(99,102,241,0.22);
                    border-radius:18px;padding:24px;margin-bottom:16px;">
                    <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;
                        color:#fff;margin-bottom:4px;">{word}</div>
                    <div class="dict-phonetic">{phonetic_text}</div>
                </div>
                """, unsafe_allow_html=True)

                for meaning in meanings[:3]:
                    pos = meaning.get("partOfSpeech","")
                    defs = meaning.get("definitions",[])
                    syns = meaning.get("synonyms",[])
                    ants = meaning.get("antonyms",[])

                    st.markdown(f"**{pos.upper()}**")
                    for d in defs[:3]:
                        st.markdown(f"• {d.get('definition','')}")
                        if d.get("example"):
                            st.markdown(f"  *e.g. \"{d['example']}\"*")

                    if syns:
                        syn_html = "".join(f'<span class="dict-syn">{s}</span>' for s in syns[:8])
                        st.markdown(f'<div>✅ Synonyms: {syn_html}</div>', unsafe_allow_html=True)
                    if ants:
                        ant_html = "".join(f'<span class="dict-ant">{a}</span>' for a in ants[:6])
                        st.markdown(f'<div>❌ Antonyms: {ant_html}</div>', unsafe_allow_html=True)
                    st.markdown("---")
            else:
                # Fallback to AI
                try:
                    from utils.ai_engine import generate
                    ai_def = generate(f"Define '{lookup_word}' comprehensively: meaning, etymology, synonyms, antonyms, usage examples, and interesting facts about the word.")
                    st.markdown(ai_def)
                except Exception as e:
                    st.error(f"Word not found: {e}")

    # ── Tab 3: Translate Word ───────────────────────────────
    with d3:
        tw = st.text_input("Word or phrase to translate:", key="dict_trans_word")
        tl = st.selectbox("Translate to:", list(LANGUAGE_MAP.keys()), key="dict_trans_lang")

        if tw and st.button("🌐 Translate", key="dict_trans_btn", use_container_width=True, type="primary"):
            with st.spinner("Translating..."):
                try:
                    from utils.ai_engine import generate
                    result = generate(f"Translate '{tw}' to {tl}. Also: 1) give pronunciation guide, 2) a usage example in {tl}, 3) back-translation, 4) cultural notes if any.")
                    st.markdown(f"""
                    <div style="background:rgba(10,14,30,0.8);border:1px solid rgba(6,182,212,0.2);
                        border-radius:14px;padding:20px;margin-top:12px;font-size:0.9rem;
                        color:rgba(255,255,255,0.8);line-height:1.8;">{result}</div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(str(e))

    # ── Tab 4: Vocabulary Quiz ──────────────────────────────
    with d4:
        quiz_src = st.selectbox("Quiz source:", ["Random Advanced Words","My Vocabulary List","Custom word list"], key="dict_quiz_src")
        num_q = st.slider("Number of questions:", 3, 10, 5, key="dict_quiz_num")

        if st.button("🎯 Start Vocab Quiz", type="primary", use_container_width=True, key="dict_quiz_start"):
            with st.spinner("Generating quiz..."):
                try:
                    from utils.ai_engine import generate
                    qp = f"Create {num_q} vocabulary quiz questions. For each: give the word, 4 meaning choices (A-D), mark the correct answer. Format:\nWORD: [word]\nA) [meaning]\nB) [meaning]\nC) [meaning]\nD) [meaning]\nANSWER: [letter]\n---"
                    st.session_state.dict_quiz = generate(qp, max_tokens=2000, temperature=0.4)
                except Exception as e:
                    st.error(str(e))

        if st.session_state.get("dict_quiz"):
            blocks = [b.strip() for b in st.session_state.dict_quiz.split("---") if b.strip()]
            for i, block in enumerate(blocks[:num_q]):
                lines = [l.strip() for l in block.split("\n") if l.strip()]
                word_line = next((l for l in lines if l.startswith("WORD:")), "")
                opts = [l for l in lines if l[:2] in ("A)","B)","C)","D)")]
                ans_line = next((l for l in lines if l.startswith("ANSWER:")), "")
                word = word_line.replace("WORD:","").strip()
                ans = ans_line.replace("ANSWER:","").strip()

                st.markdown(f"**Q{i+1}: What does '{word}' mean?**")
                for o in opts:
                    st.markdown(f"  {o}")
                with st.expander(f"Answer"):
                    st.success(f"✅ {ans}")

    # ── Tab 5: Etymology Explorer ───────────────────────────
    with d5:
        etym_word = st.text_input("Explore etymology of:", placeholder="e.g. democracy, biology", key="dict_etym_word")
        if etym_word and st.button("📚 Explore Etymology", key="dict_etym_btn", use_container_width=True, type="primary"):
            with st.spinner("Researching etymology..."):
                try:
                    from utils.ai_engine import generate
                    etym = generate(f"Provide a complete etymology of '{etym_word}': original language(s), root words and their meanings, historical evolution, related words with same root, first recorded use, and how meaning has changed over time. Make it fascinating.")
                    st.markdown(f"""
                    <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(245,158,11,0.2);
                        border-left:3px solid #f59e0b;border-radius:14px;padding:20px;
                        font-size:0.9rem;color:rgba(255,255,255,0.78);line-height:1.85;">{etym}</div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(str(e))
