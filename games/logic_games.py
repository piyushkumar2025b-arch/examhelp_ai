"""
games/logic_games.py — Math & Logic Puzzles (14-18)
14. Number Guess  15. Math Sprint  16. Mastermind
17. Memory Matrix  18. Pattern Game
"""
from __future__ import annotations
import streamlit as st
import random
import time
import json


def _ai_call(prompt: str, max_tokens: int = 256) -> str:
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
# 14. NUMBER GUESSING
# ═══════════════════════════════════════════
def render_number_guess():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#34d399;margin-bottom:8px;">🔢 Number Guess</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">AI picks 1–1000. You guess. Higher/Lower hints. Fewer guesses = better score!</div>', unsafe_allow_html=True)
    if "ng_secret" not in st.session_state or st.session_state.get("ng_rst"):
        st.session_state.ng_secret=random.randint(1,1000); st.session_state.ng_history=[]; st.session_state.ng_lo=1; st.session_state.ng_hi=1000; st.session_state.ng_won=False; st.session_state.ng_rst=False
    secret=st.session_state.ng_secret; attempts=len(st.session_state.ng_history)
    lo,hi=st.session_state.ng_lo,st.session_state.ng_hi
    st.progress((1000-(hi-lo))/1000,text=f"Narrowed range: {lo}–{hi} ({hi-lo+1} possibilities)")
    st.caption(f"Attempts: {attempts}")
    if st.session_state.ng_history:
        st.markdown("History: "+", ".join(f"**{g}**({'✅' if g==secret else '↑' if g<secret else '↓'})" for g in st.session_state.ng_history))
    if not st.session_state.ng_won:
        guess=st.number_input("Your guess (1-1000):",1,1000,500,key=f"ng_in_{attempts}")
        if st.button("🎯 Guess!",type="primary",use_container_width=True,key="ng_guess"):
            st.session_state.ng_history.append(int(guess))
            if int(guess)==secret:
                st.session_state.ng_won=True
                score=max(1, 20-attempts)
                st.success(f"🎉 Correct! {secret} in {attempts+1} guess(es)! Score: {score}")
                _score_update("Number Guess",score); st.balloons()
            elif int(guess)<secret:
                st.info("📈 Too Low! Go higher."); st.session_state.ng_lo=max(lo,int(guess)+1)
            else:
                st.info("📉 Too High! Go lower."); st.session_state.ng_hi=min(hi,int(guess)-1)
            st.rerun()
    if st.button("🔄 New Game",use_container_width=True,key="ng_new"): st.session_state.ng_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 15. MATH SPRINT
# ═══════════════════════════════════════════
def _gen_question(diff):
    if diff=="Easy":
        a,b=random.randint(1,20),random.randint(1,20); op=random.choice(["+","-"]); ans=a+b if op=="+" else a-b
    elif diff=="Medium":
        a,b=random.randint(2,12),random.randint(2,12); op=random.choice(["×","÷"])
        if op=="×": ans=a*b
        else: ans=a; b=random.randint(1,10); a=ans*b
    else:  # Hard
        a,b,c=random.randint(1,15),random.randint(1,10),random.randint(1,5)
        ans=a*b+c; return f"{a} × {b} + {c}",ans
    return f"{a} {op} {b}",ans

def render_math_sprint():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#60a5fa;margin-bottom:8px;">⚡ Math Sprint</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">10 questions. 60 seconds. How many can you get right?</div>', unsafe_allow_html=True)
    diff=st.selectbox("Difficulty",["Easy","Medium","Hard"],key="ms_diff")
    if "ms_qs" not in st.session_state or st.session_state.get("ms_rst"):
        qs=[_gen_question(diff) for _ in range(10)]
        st.session_state.ms_qs=qs; st.session_state.ms_idx=0; st.session_state.ms_correct=0
        st.session_state.ms_start=time.time(); st.session_state.ms_done=False; st.session_state.ms_rst=False
    qs=st.session_state.ms_qs; idx=st.session_state.ms_idx
    elapsed=time.time()-st.session_state.ms_start; remaining=max(0,60-elapsed)
    st.progress(remaining/60,text=f"⏱ {remaining:.0f}s remaining")
    if remaining<=0 or st.session_state.ms_done:
        c=st.session_state.ms_correct; total=idx
        st.success(f"⏱ Time's up! Score: **{c}/{total}** correct | Accuracy: {int(c/max(1,total)*100)}%")
        _score_update("Math Sprint",c)
        if st.button("🔄 Play Again",use_container_width=True,key="ms_new"): st.session_state.ms_rst=True; st.rerun()
        return
    if idx<10:
        q,ans=qs[idx]
        st.markdown(f'<div style="font-size:2rem;font-weight:900;text-align:center;color:#60a5fa;margin:16px 0;">{q} = ?</div>',unsafe_allow_html=True)
        st.caption(f"Question {idx+1}/10")
        user=st.number_input("Answer:",key=f"ms_ans_{idx}",step=1)
        if st.button("Submit →",type="primary",use_container_width=True,key=f"ms_sub_{idx}"):
            if int(user)==ans: st.session_state.ms_correct+=1; st.success("✅ Correct!")
            else: st.error(f"❌ Answer was {ans}")
            st.session_state.ms_idx+=1
            if st.session_state.ms_idx>=10: st.session_state.ms_done=True
            st.rerun()
    if st.button("🔄 New Game",use_container_width=True,key="ms_new2"): st.session_state.ms_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 16. MASTERMIND
# ═══════════════════════════════════════════
def _mm_feedback(secret, guess):
    black=sum(s==g for s,g in zip(secret,guess))
    white=sum(min(secret.count(d),guess.count(d)) for d in set(guess))-black
    return black,white

def render_mastermind():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#e879f9;margin-bottom:8px;">🔐 Mastermind</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Crack the 4-digit code (digits 1-6). ⚫=right digit+position  ⚪=right digit+wrong position</div>', unsafe_allow_html=True)
    if "mm_secret" not in st.session_state or st.session_state.get("mm_rst"):
        st.session_state.mm_secret=[random.randint(1,6) for _ in range(4)]; st.session_state.mm_history=[]; st.session_state.mm_won=False; st.session_state.mm_rst=False
    secret=st.session_state.mm_secret; history=st.session_state.mm_history; attempts=len(history)
    # Show history
    if history:
        for g,fb in history:
            b,w=fb
            st.markdown(f'`{"".join(map(str,g))}` → {"⚫"*b}{"⚪"*w}{" (no match)" if b+w==0 else ""}')
    if not st.session_state.mm_won and attempts<10:
        g_in=st.text_input(f"Guess #{attempts+1} (4 digits, 1-6 each):",max_chars=4,placeholder="e.g. 1234",key=f"mm_in_{attempts}")
        if st.button("🔍 Check",type="primary",use_container_width=True,key=f"mm_chk_{attempts}"):
            if len(g_in)==4 and g_in.isdigit() and all(1<=int(d)<=6 for d in g_in):
                guess=[int(d) for d in g_in]; fb=_mm_feedback(secret,guess)
                history.append((guess,fb)); st.session_state.mm_history=history
                if fb[0]==4: st.session_state.mm_won=True
                st.rerun()
            else: st.warning("Enter exactly 4 digits, each 1-6.")
    if st.session_state.mm_won:
        st.success(f"🎉 Cracked it in {len(history)} tries! Code: {''.join(map(str,secret))}"); _score_update("Mastermind",10-len(history)); st.balloons()
    elif attempts>=10:
        st.error(f"💀 Out of guesses! Code was: {''.join(map(str,secret))}")
    if st.button("🔄 New Game",use_container_width=True,key="mm_new"): st.session_state.mm_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 17. MEMORY MATRIX
# ═══════════════════════════════════════════
def render_memory_matrix():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#f472b6;margin-bottom:8px;">🧠 Memory Matrix</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Memorize the 4×4 grid of numbers. They\'ll hide after 3 seconds. Recall as many as you can!</div>', unsafe_allow_html=True)
    if "mm2_grid" not in st.session_state or st.session_state.get("mm2_rst"):
        st.session_state.mm2_grid=[[random.randint(1,9) for _ in range(4)] for _ in range(4)]
        st.session_state.mm2_shown=False; st.session_state.mm2_hide=False; st.session_state.mm2_done=False; st.session_state.mm2_rst=False; st.session_state.mm2_show_until=None
    grid=st.session_state.mm2_grid
    if not st.session_state.mm2_shown:
        if st.button("👁 Show Grid (3 sec)",type="primary",use_container_width=True,key="mm2_show"):
            st.session_state.mm2_shown=True; st.session_state.mm2_show_until=time.time()+3; st.session_state.mm2_hide=False; st.rerun()
        return
    if st.session_state.mm2_shown and not st.session_state.mm2_hide:
        t_left=st.session_state.mm2_show_until-time.time()
        if t_left>0:
            html='<table style="border-collapse:separate;border-spacing:4px;">'
            for row in grid:
                html+="<tr>"+"".join(f'<td style="width:50px;height:50px;background:#1e40af;color:#fff;text-align:center;font-size:1.3rem;font-weight:900;border-radius:8px;">{v}</td>' for v in row)+"</tr>"
            html+="</table>"
            st.markdown(html,unsafe_allow_html=True)
            st.progress(t_left/3,text=f"Memorize! {t_left:.1f}s"); time.sleep(0.5); st.rerun()
        else: st.session_state.mm2_hide=True; st.rerun()
    if st.session_state.mm2_hide and not st.session_state.mm2_done:
        st.markdown("**Now fill in what you remember:**")
        user=[[0]*4 for _ in range(4)]
        for r in range(4):
            cols=st.columns(4)
            for c in range(4):
                user[r][c]=cols[c].number_input(" ",0,9,key=f"mm2_{r}_{c}",label_visibility="collapsed")
        if st.button("✅ Check Answers",type="primary",use_container_width=True,key="mm2_check"):
            correct=sum(1 for r in range(4) for c in range(4) if int(user[r][c])==grid[r][c])
            pct=correct/16*100
            st.success(f"🎉 {correct}/16 correct ({pct:.0f}%)!"); _score_update("Memory Matrix",correct); st.session_state.mm2_done=True
            # Show answers
            html='<table style="border-collapse:separate;border-spacing:4px;">'
            for r,row in enumerate(grid):
                html+="<tr>"+"".join(f'<td style="width:50px;height:50px;background:{"#16a34a" if int(user[r][c])==v else "#dc2626"};color:#fff;text-align:center;font-size:1.1rem;font-weight:900;border-radius:8px;">{v}</td>' for c,v in enumerate(row))+"</tr>"
            html+="</table>"
            st.markdown("**Answer grid (🟢=correct 🔴=wrong):**"); st.markdown(html,unsafe_allow_html=True)
    if st.button("🔄 New game",use_container_width=True,key="mm2_new"): st.session_state.mm2_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 18. PATTERN GAME
# ═══════════════════════════════════════════
def render_pattern_game():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#a3e635;margin-bottom:8px;">🧩 Pattern Game</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">AI generates a sequence with a hidden rule. Guess the next 3 numbers!</div>', unsafe_allow_html=True)
    if "pg_data" not in st.session_state or st.session_state.get("pg_rst"):
        st.session_state.pg_data=None; st.session_state.pg_rst=False; st.session_state.pg_revealed=False
    if st.session_state.pg_data is None:
        if st.button("🎲 Generate Pattern",type="primary",use_container_width=True,key="pg_gen"):
            with st.spinner("AI generating sequence..."):
                prompt='Generate a mathematical number sequence with a hidden rule. Give 5 numbers and what the next 3 should be. Return ONLY valid JSON: {"sequence":[1,4,9,16,25],"next":[36,49,64],"hint":"perfect squares","rule":"n squared"}'
                raw=_ai_call(prompt,300)
                try:
                    s=raw.find("{"); e=raw.rfind("}")+1; st.session_state.pg_data=json.loads(raw[s:e])
                except Exception:
                    st.session_state.pg_data={"sequence":[2,4,8,16,32],"next":[64,128,256],"hint":"doubles","rule":"multiply by 2"}
            st.rerun()
        return
    data=st.session_state.pg_data; seq=data.get("sequence",[]); nxt=data.get("next",[]); hint_txt=data.get("hint",""); rule=data.get("rule","")
    seq_str=" → ".join(f"**{n}**" for n in seq)+" → ❓ → ❓ → ❓"
    st.markdown(f'<div style="font-size:1.2rem;text-align:center;margin:12px 0;">{seq_str}</div>',unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:
        u1=st.number_input("Next value 1:",key="pg_u1",step=1)
        u2=st.number_input("Next value 2:",key="pg_u2",step=1)
        u3=st.number_input("Next value 3:",key="pg_u3",step=1)
    with c2:
        st.markdown(f'<div style="background:rgba(163,230,53,0.08);border:1px solid rgba(163,230,53,0.2);border-radius:12px;padding:14px;margin-top:8px;"><div style="font-size:.78rem;color:#94a3b8;margin-bottom:4px;">💡 HINT</div><div style="color:#a3e635;">{hint_txt}</div></div>',unsafe_allow_html=True)
    if st.button("✅ Check",type="primary",use_container_width=True,key="pg_check"):
        user=[int(u1),int(u2),int(u3)]; correct=sum(u==a for u,a in zip(user,nxt))
        if correct==3: st.success(f"🎉 Perfect! Rule: **{rule}**"); _score_update("Pattern Game",3); st.balloons()
        else:
            st.warning(f"{correct}/3 correct."); st.info(f"Correct: {nxt[0]}, {nxt[1]}, {nxt[2]} — Rule: {rule}")
        st.session_state.pg_revealed=True
    if st.button("🔄 New Pattern",use_container_width=True,key="pg_new"): st.session_state.pg_rst=True; st.rerun()
