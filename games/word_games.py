"""
games/word_games.py — Word & Language Games (8-13)
8. Wordle  9. Hangman  10. Word Scramble
11. Crossword Lite  12. Rhyme Chain  13. Story Dice
"""
from __future__ import annotations
import streamlit as st
import random
import time
import json


def _ai_call(prompt: str, max_tokens: int = 300) -> str:
    try:
        from utils import ai_engine
        return ai_engine.generate(prompt, max_tokens=max_tokens)
    except Exception:
        return ""

def _score_update(game, score):
    if "game_scores" not in st.session_state: st.session_state.game_scores = {}
    prev = st.session_state.game_scores.get(game, 0)
    if isinstance(score, (int, float)) and score > prev:
        st.session_state.game_scores[game] = score


# ═══════════════════════════════════════════
# 8. WORDLE (200-word list)
# ═══════════════════════════════════════════
WORDLE_WORDS = [
    "arose","crane","slate","trace","crate","stale","arise","snare","least","steal",
    "alert","alter","learn","earth","heart","reach","teach","beach","peach","leach",
    "place","plane","plant","grant","chant","chart","smart","start","stark","spark",
    "spare","stare","share","shore","store","score","snore","smoke","spoke","spore",
    "sword","wheat","cheat","cheap","clear","clean","cleat","cream","dream","steam",
    "bread","tread","dread","ahead","flame","frame","blame","claim","trail","train",
    "brain","grain","drain","plain","braid","snail","quail","grail","brave","crave",
    "grave","slave","shave","stave","novel","level","devil","civil","rival","tidal",
    "viral","vital","final","tiger","giver","liver","river","diver","miner","finer",
    "liner","diner","siren","token","woken","often","raven","haven","maven","stink",
    "think","drink","blink","brink","bring","spring","sprint","print","point","joint",
    "hoist","moist","noise","poise","voice","twice","price","slice","spice","dance",
    "lance","fence","hence","pence","mince","since","rinse","binge","hinge","plunge",
    "lunge","flint","glint","stint","stunt","blunt","grunt","front","frost","crust",
    "thrust","brush","crush","flush","blush","clash","flash","crash","trash","gnash",
    "smash","latch","batch","match","catch","watch","patch","notch","botch","witch",
    "ditch","pitch","hitch","stitch","blind","grind","groan","moan","blown","known",
    "flown","shown","brown","crown","drown","frown","clown","spawn","drawn","prawn",
    "scrawl","brawl","crawl","drawl","shawl","trawl","sprawl","stall","small","shall",
]

def _wordle_feedback(guess, secret):
    res=["_"]*5; sc=list(secret)
    for i in range(5):
        if guess[i]==sc[i]: res[i]="G"; sc[i]=None
    for i in range(5):
        if res[i]!="G" and guess[i] in sc: res[i]="Y"; sc[sc.index(guess[i])]=None
    return res

def _wordle_tile_row(guess, feedback):
    colors={"G":"#22c55e","Y":"#ca8a04","_":"#334155"}
    html='<div style="display:flex;gap:5px;justify-content:center;margin:3px 0;">'
    for ch,fb in zip(guess.upper().ljust(5),feedback):
        html+=f'<div style="width:48px;height:48px;background:{colors[fb]};border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;font-weight:900;color:#fff;">{ch if ch!=" " else ""}</div>'
    html+="</div>"
    return html

def render_wordle():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#86efac;margin-bottom:8px;">🟩 Wordle</div><div style="color:#64748b;font-size:.85rem;margin-bottom:12px;">Guess the 5-letter word in 6 tries · 🟩 correct · 🟨 wrong pos · ⬛ not in word</div>', unsafe_allow_html=True)
    if "wrd_secret" not in st.session_state or st.session_state.get("wrd_rst"):
        wl=[w for w in WORDLE_WORDS if len(w)==5]
        st.session_state.wrd_secret=random.choice(wl).lower()
        st.session_state.wrd_guesses=[]; st.session_state.wrd_won=False; st.session_state.wrd_rst=False
    secret=st.session_state.wrd_secret; guesses=st.session_state.wrd_guesses; won=st.session_state.wrd_won
    html_rows=""
    for g,fb in guesses: html_rows+=_wordle_tile_row(g,fb)
    for _ in range(6-len(guesses)): html_rows+=_wordle_tile_row("     ",["_"]*5)
    st.markdown(html_rows,unsafe_allow_html=True)
    if won: st.success(f"🎉 Got it in {len(guesses)} guess(es)! Word: **{secret.upper()}**"); _score_update("Wordle",6-len(guesses)+1)
    elif len(guesses)>=6: st.error(f"😞 The word was **{secret.upper()}**")
    else:
        g_in=st.text_input("Your guess:",max_chars=5,key=f"wrd_in_{len(guesses)}",placeholder="5-letter word").lower().strip()
        if st.button("Submit",type="primary",use_container_width=True,key="wrd_sub"):
            if len(g_in)==5 and g_in.isalpha():
                fb=_wordle_feedback(g_in,secret); guesses.append((g_in,fb))
                if g_in==secret: st.session_state.wrd_won=True
                st.session_state.wrd_guesses=guesses; st.rerun()
            else: st.warning("5 letters only!")
    # Keyboard
    if guesses:
        used={}
        for g,fb in guesses:
            for ch,f in zip(g,fb):
                if f=="G": used[ch]="G"
                elif f=="Y" and used.get(ch)!="G": used[ch]="Y"
                elif f=="_" and ch not in used: used[ch]="_"
        clrs={"G":"#22c55e","Y":"#ca8a04","_":"#475569"}
        kb='<div style="display:flex;flex-wrap:wrap;gap:3px;justify-content:center;margin-top:8px;">'
        for ch in "abcdefghijklmnopqrstuvwxyz":
            c=clrs.get(used.get(ch,""),"#1e293b")
            kb+=f'<span style="background:{c};color:#fff;border-radius:4px;padding:3px 6px;font-size:.75rem;font-weight:700;">{ch.upper()}</span>'
        kb+="</div>"
        st.markdown(kb,unsafe_allow_html=True)
    if st.button("🔄 New Word",use_container_width=True,key="wrd_new"): st.session_state.wrd_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 9. HANGMAN
# ═══════════════════════════════════════════
HANGMAN_WORDS = {
    "Animals": ["elephant","dolphin","penguin","giraffe","cheetah","gorilla","flamingo","kangaroo","rhinoceros","crocodile","butterfly","chameleon","salamander","porcupine","wolverine"],
    "Programming": ["python","javascript","algorithm","recursion","function","variable","boolean","inheritance","polymorphism","debugging","runtime","compiler","interface","framework","repository"],
    "Movies": ["inception","interstellar","parasite","avengers","gladiator","titanic","casablanca","godfather","braveheart","shawshank","pulpfiction","goodfellas","schindler","spotlight","whiplash"],
    "Foods": ["spaghetti","avocado","broccoli","cucumber","strawberry","blueberry","raspberry","pineapple","watermelon","asparagus","artichoke","persimmon","pomegranate","zucchini","aubergine"],
    "Countries": ["argentina","bangladesh","cambodia","denmark","ethiopia","finland","guatemala","honduras","indonesia","jamaica","kazakhstan","luxembourg","mozambique","nicaragua","oman"],
}
GALLOWS = [
    "  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========",
    "  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========",
]

def render_hangman():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#f87171;margin-bottom:8px;">🪢 Hangman</div>', unsafe_allow_html=True)
    cat=st.selectbox("Category",list(HANGMAN_WORDS.keys()),key="hm_cat")
    if "hm_word" not in st.session_state or st.session_state.get("hm_cat_prev")!=cat:
        st.session_state.hm_word=random.choice(HANGMAN_WORDS[cat]).lower()
        st.session_state.hm_guessed=set(); st.session_state.hm_wrong=0; st.session_state.hm_cat_prev=cat; st.session_state.hm_over=False
    word=st.session_state.hm_word; guessed=st.session_state.hm_guessed; wrong=st.session_state.hm_wrong
    col_g,col_w=st.columns([1,2])
    with col_g: st.code(GALLOWS[min(wrong,6)])
    with col_w:
        display=" ".join(c.upper() if c in guessed else "_" for c in word)
        st.markdown(f'<div style="font-size:1.5rem;font-weight:900;letter-spacing:8px;color:#f8fafc;">{display}</div>',unsafe_allow_html=True)
        st.caption(f"Wrong guesses: {wrong}/6 · Guessed: {', '.join(sorted(guessed)).upper()}")
    won=all(c in guessed for c in word); lost=wrong>=6
    if won: st.success(f"🎉 You got it! The word was **{word.upper()}**"); _score_update("Hangman",1); st.session_state.hm_over=True
    elif lost: st.error(f"💀 The word was **{word.upper()}**"); st.session_state.hm_over=True
    elif not st.session_state.hm_over:
        # A-Z buttons
        st.markdown("**Pick a letter:**")
        alphabet="abcdefghijklmnopqrstuvwxyz"
        rows=[alphabet[i:i+9] for i in range(0,26,9)]
        for row in rows:
            cols=st.columns(len(row))
            for i,letter in enumerate(row):
                already=letter in guessed
                if cols[i].button(letter.upper(),key=f"hm_{letter}",disabled=already,use_container_width=True):
                    guessed.add(letter)
                    if letter not in word: st.session_state.hm_wrong+=1
                    st.session_state.hm_guessed=guessed; st.rerun()
    if st.button("🔄 New Word",use_container_width=True,key="hm_new"):
        for k in ["hm_word","hm_guessed","hm_wrong","hm_over"]: st.session_state.pop(k,None); st.rerun()


# ═══════════════════════════════════════════
# 10. WORD SCRAMBLE
# ═══════════════════════════════════════════
SCRAMBLE_WORDS=["python","algorithm","streamlit","keyboard","umbrella","chocolate","knowledge","telescope","dinosaur","chemistry","geography","astronomy","democracy","philosophy","electricity","biology","mathematics","literature","engineering","architecture"]

def render_word_scramble():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fde68a;margin-bottom:8px;">🔀 Word Scramble</div>', unsafe_allow_html=True)
    if "scr_word" not in st.session_state or st.session_state.get("scr_rst"):
        w=random.choice(SCRAMBLE_WORDS)
        s=list(w); random.shuffle(s)
        while "".join(s)==w: random.shuffle(s)
        st.session_state.scr_word=w; st.session_state.scr_scr="".join(s)
        st.session_state.scr_score=st.session_state.get("scr_score",0)
        st.session_state.scr_hint_used=False; st.session_state.scr_rst=False; st.session_state.scr_start=time.time()
    w=st.session_state.scr_word; scr=st.session_state.scr_scr
    st.markdown(f'<div style="font-size:2rem;font-weight:900;letter-spacing:8px;text-align:center;color:#fbbf24;margin:12px 0;">{scr.upper()}</div>',unsafe_allow_html=True)
    st.caption(f"Score: {st.session_state.scr_score} · Time: {int(time.time()-st.session_state.scr_start)}s")
    ans=st.text_input("Unscramble it:",key=f"scr_in_{scr}",placeholder="Type the original word...").lower().strip()
    c1,c2=st.columns(2)
    if c1.button("✅ Submit",type="primary",use_container_width=True,key="scr_sub"):
        if ans==w:
            pts=10-(3 if st.session_state.scr_hint_used else 0)
            st.session_state.scr_score+=pts; st.success(f"🎉 Correct! +{pts} pts"); _score_update("Word Scramble",st.session_state.scr_score)
            st.session_state.scr_rst=True; st.rerun()
        else: st.error(f"❌ Wrong! Try again.")
    if c2.button("💡 Hint (-3 pts)",use_container_width=True,key="scr_hint"):
        with st.spinner("Getting hint..."): h=_ai_call(f"Give a one-word clue about the meaning of '{w}'. Just one word.",50)
        st.info(f"Hint: {h or w[0].upper()+'...'}"); st.session_state.scr_hint_used=True
    if st.button("⏭ Skip",use_container_width=True,key="scr_skip"): st.session_state.scr_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 11. CROSSWORD LITE
# ═══════════════════════════════════════════
def render_crossword():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#67e8f9;margin-bottom:8px;">✏️ Crossword Lite</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">AI generates a 5×5 mini-crossword. Fill in the cells then check!</div>', unsafe_allow_html=True)
    if "xw_data" not in st.session_state: st.session_state.xw_data=None; st.session_state.xw_uservals={}
    if st.session_state.xw_data is None:
        if st.button("🎲 Generate Crossword",type="primary",use_container_width=True,key="xw_gen"):
            with st.spinner("AI building crossword..."):
                prompt=('Create a 5x5 crossword with 3 across and 3 down words. '
                        'Return ONLY valid JSON: {"clues":{"across":[{"num":1,"clue":"...","answer":"WORD","row":0,"col":0}],"down":[{"num":1,"clue":"...","answer":"WORD","row":0,"col":0}]}}')
                raw=_ai_call(prompt,600)
                try:
                    s=raw.find("{"); e=raw.rfind("}")+1
                    st.session_state.xw_data=json.loads(raw[s:e])
                    st.session_state.xw_uservals={}
                    st.rerun()
                except Exception: st.error("AI couldn't generate puzzle. Try again.")
        return
    data=st.session_state.xw_data
    # Build answer grid
    ans_grid=[[" "]*5 for _ in range(5)]
    for entry in data.get("clues",{}).get("across",[])+data.get("clues",{}).get("down",[]):
        r,c,word=entry.get("row",0),entry.get("col",0),entry.get("answer","")
        for i,ch in enumerate(word):
            is_across=entry in data.get("clues",{}).get("across",[])
            if is_across:
                if c+i<5: ans_grid[r][c+i]=ch.upper()
            else:
                if r+i<5: ans_grid[r+i][c]=ch.upper()
    st.markdown("**Fill in the grid:**")
    user_grid=[[" "]*5 for _ in range(5)]
    for r in range(5):
        cols_ui=st.columns(5)
        for c in range(5):
            if ans_grid[r][c]==" ":
                cols_ui[c].markdown('<div style="width:40px;height:40px;background:#0f172a;border-radius:4px;"></div>',unsafe_allow_html=True)
            else:
                v=cols_ui[c].text_input(" ",value=st.session_state.xw_uservals.get(f"{r}{c}",""),max_chars=1,key=f"xw_{r}_{c}",label_visibility="collapsed")
                st.session_state.xw_uservals[f"{r}{c}"]=v; user_grid[r][c]=v.upper()
    col_a,col_b=st.columns(2)
    # Clues
    with col_a:
        st.markdown("**Across:**")
        for e in data.get("clues",{}).get("across",[]): st.caption(f"{e.get('num','')}. {e.get('clue','')}")
    with col_b:
        st.markdown("**Down:**")
        for e in data.get("clues",{}).get("down",[]): st.caption(f"{e.get('num','')}. {e.get('clue','')}")
    if st.button("✅ Check Answers",use_container_width=True,key="xw_check"):
        correct=sum(1 for r in range(5) for c in range(5) if user_grid[r][c]==ans_grid[r][c] and ans_grid[r][c]!=" ")
        total=sum(1 for r in range(5) for c in range(5) if ans_grid[r][c]!=" ")
        st.success(f"✅ {correct}/{total} correct!") if correct==total else st.warning(f"⚠️ {correct}/{total} correct — keep trying!")
        _score_update("Crossword",correct)
    if st.button("🔄 New Puzzle",use_container_width=True,key="xw_new"): st.session_state.xw_data=None; st.session_state.xw_uservals={}; st.rerun()


# ═══════════════════════════════════════════
# 12. RHYME CHAIN
# ═══════════════════════════════════════════
def render_rhyme_chain():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#c084fc;margin-bottom:8px;">🎵 Rhyme Chain</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">You say a word → AI rhymes it → You rhyme AI\'s word → Keep the chain going!</div>', unsafe_allow_html=True)
    if "rhyme_chain" not in st.session_state:
        st.session_state.rhyme_chain=[]; st.session_state.rhyme_streak=0; st.session_state.rhyme_best=0; st.session_state.rhyme_over=False; st.session_state.rhyme_ai_word=""
    chain=st.session_state.rhyme_chain; streak=st.session_state.rhyme_streak
    st.metric("🔥 Streak",streak,delta=None); st.caption(f"Best: {st.session_state.rhyme_best}")
    if chain:
        st.markdown("**Chain so far:**")
        st.markdown(" → ".join(f'**{w}**' for w in chain[-6:]))
    if not st.session_state.rhyme_over:
        ai_word=st.session_state.rhyme_ai_word
        if ai_word: st.info(f"AI said: **{ai_word.upper()}** — Your rhyme?")
        else: st.caption("Start the chain with any word!")
        player_word=st.text_input("Your word:",key=f"rhyme_in_{streak}",placeholder="Type a rhyming word...").strip().lower()
        if st.button("Submit Rhyme",type="primary",use_container_width=True,key="rhyme_sub") and player_word:
            if ai_word:
                judge=_ai_call(f"Does '{player_word}' rhyme with '{ai_word}'? Reply ONLY 'Yes' or 'No'.",10)
                if "yes" not in judge.lower():
                    st.session_state.rhyme_over=True; st.error(f"❌ '{player_word}' doesn't rhyme with '{ai_word}'! Game over!")
                    if streak>st.session_state.rhyme_best: st.session_state.rhyme_best=streak
                    _score_update("Rhyme Chain",streak); return
            chain.append(player_word)
            with st.spinner("AI rhyming..."):
                ai_resp=_ai_call(f"Give ONE word that rhymes with '{player_word}'. Reply ONLY the rhyming word, nothing else.",20)
            ai_new=ai_resp.strip().lower().split()[0] if ai_resp.strip() else "cat"
            chain.append(ai_new); st.session_state.rhyme_ai_word=ai_new
            st.session_state.rhyme_streak+=1; st.session_state.rhyme_chain=chain; st.rerun()
    else:
        if st.button("🔄 New Game",use_container_width=True,key="rhyme_new"):
            for k in ["rhyme_chain","rhyme_streak","rhyme_over","rhyme_ai_word"]: st.session_state.pop(k,None); st.rerun()


# ═══════════════════════════════════════════
# 13. STORY DICE
# ═══════════════════════════════════════════
DICE_EMOJIS=["⚔️","🏰","🧪","💎","🌊","🐉","🚀","🌙","🗡️","🔮","🦁","🌋","🕵️","🧬","🎭","🌺","🏔️","🦅","🌪️","🐺"]

def render_story_dice():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fb923c;margin-bottom:8px;">🎲 Story Dice</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">AI rolls 6 story elements. Write a mini-story using ALL of them, then get scored!</div>', unsafe_allow_html=True)
    if "sd_elements" not in st.session_state or st.session_state.get("sd_rst"):
        st.session_state.sd_rst=False
        with st.spinner("Rolling story dice..."):
            prompt='Give 6 random story elements: character, setting, object, conflict, emotion, twist. Return ONLY valid JSON array of 6 strings, e.g. ["brave knight","haunted castle","magic sword","betrayal","despair","villain was the hero"]'
            raw=_ai_call(prompt,300)
            try:
                s=raw.find("["); e=raw.rfind("]")+1; elems=json.loads(raw[s:e])
            except Exception:
                elems=["hero","forest","sword","dragon","courage","secret door"]
        st.session_state.sd_elements=elems[:6]; st.session_state.sd_score=None
    elems=st.session_state.sd_elements
    emojis=random.sample(DICE_EMOJIS,6)
    html='<div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">'
    for em,el in zip(emojis,elems):
        html+=f'<div style="background:rgba(251,146,60,0.1);border:1px solid rgba(251,146,60,0.3);border-radius:12px;padding:10px 14px;text-align:center;min-width:90px;"><div style="font-size:1.8rem;">{em}</div><div style="font-size:.78rem;color:#f8fafc;margin-top:4px;">{el}</div></div>'
    html+="</div>"
    st.markdown(html,unsafe_allow_html=True)
    story=st.text_area("Write your story using all 6 elements:",height=180,key="sd_story",placeholder="Once upon a time...")
    if st.button("📊 Score My Story",type="primary",use_container_width=True,key="sd_score_btn") and story.strip():
        with st.spinner("AI grading your story..."):
            prompt=(f"Rate this story on 3 criteria (1-10 each): creativity, use of all 6 elements ({', '.join(elems)}), coherence.\n\nStory: {story}\n\nReturn JSON: {{\"creativity\":8,\"elements_used\":7,\"coherence\":9,\"feedback\":\"...\"}}")
            raw=_ai_call(prompt,400)
            try:
                s=raw.find("{"); e=raw.rfind("}")+1; st.session_state.sd_score=json.loads(raw[s:e])
            except Exception: st.session_state.sd_score={"creativity":7,"elements_used":6,"coherence":7,"feedback":"Great story!"}
    if st.session_state.get("sd_score"):
        sc=st.session_state.sd_score
        total=sc.get("creativity",0)+sc.get("elements_used",0)+sc.get("coherence",0)
        c1,c2,c3=st.columns(3)
        c1.metric("🎨 Creativity",f"{sc.get('creativity',0)}/10")
        c2.metric("🎲 Elements",f"{sc.get('elements_used',0)}/10")
        c3.metric("📖 Coherence",f"{sc.get('coherence',0)}/10")
        st.info(sc.get("feedback","Well done!")); _score_update("Story Dice",total)
    if st.button("🔄 New Dice Roll",use_container_width=True,key="sd_new"): st.session_state.sd_rst=True; st.session_state.sd_score=None; st.rerun()
