"""
games/arcade_games.py — Arcade & Reflex Games (26-31)
26. Reaction Timer  27. Rock Paper Scissors Lizard Spock
28. Higher or Lower  29. True/False Blitz
30. Emoji Rebus  31. Typing Speed Test
"""
from __future__ import annotations
import streamlit as st
import random
import time
import json


def _ai(prompt: str, max_tokens: int = 400) -> str:
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

def _parse_json(raw):
    try: s=raw.find("{"); e=raw.rfind("}")+1; return json.loads(raw[s:e])
    except: return {}

def _parse_json_list(raw):
    try: s=raw.find("["); e=raw.rfind("]")+1; return json.loads(raw[s:e])
    except: return []


# ═══════════════════════════════════════════
# 26. REACTION TIMER
# ═══════════════════════════════════════════
def render_reaction_timer():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#34d399;margin-bottom:8px;">⚡ Reaction Timer</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Wait for GREEN, then click as fast as possible! Best of 5 rounds.</div>', unsafe_allow_html=True)
    if "rt_times" not in st.session_state: st.session_state.rt_times=[]; st.session_state.rt_state="idle"; st.session_state.rt_start_ts=None
    state=st.session_state.rt_state; times=st.session_state.rt_times
    if len(times)>0:
        avg=sum(times)/len(times)
        hist_html='<div style="display:flex;gap:8px;align-items:flex-end;justify-content:center;height:60px;">'
        for t in times:
            h=max(10,int(60-t/10)); clr="#22c55e" if t<250 else "#f59e0b" if t<400 else "#ef4444"
            hist_html+=f'<div title="{t:.0f}ms" style="width:30px;height:{h}px;background:{clr};border-radius:4px 4px 0 0;"></div>'
        hist_html+="</div>"
        st.markdown(hist_html,unsafe_allow_html=True)
        st.caption(f"Rounds: {len(times)}/5 | Avg: {avg:.0f}ms | Best: {min(times):.0f}ms | World avg: 250ms")
        grade="🔥 Reflex God!" if avg<200 else "⚡ Very Fast!" if avg<300 else "👍 Average" if avg<450 else "🐢 Keep practicing"
        st.markdown(f"**{grade}**")
        _score_update("Reaction Timer",int(1000/max(1,avg)*100))
    if len(times)>=5:
        if st.button("🔄 Play Again",type="primary",use_container_width=True,key="rt_new"): st.session_state.rt_times=[]; st.session_state.rt_state="idle"; st.rerun()
        return
    if state=="idle":
        if st.button("🚦 Start Round",type="primary",use_container_width=True,key="rt_start"):
            st.session_state.rt_state="waiting"; st.session_state.rt_delay=random.uniform(2,5); st.session_state.rt_trigger=time.time(); st.rerun()
    elif state=="waiting":
        delay=st.session_state.rt_delay; elapsed=time.time()-st.session_state.rt_trigger
        if elapsed<delay:
            st.markdown('<div style="background:#374151;border-radius:16px;padding:40px;text-align:center;font-size:1.3rem;color:#9ca3af;">⏳ Wait for it...</div>',unsafe_allow_html=True)
            time.sleep(0.1); st.rerun()
        else:
            st.session_state.rt_state="go"; st.session_state.rt_start_ts=time.time(); st.rerun()
    elif state=="go":
        st.markdown('<div style="background:#16a34a;border-radius:16px;padding:40px;text-align:center;font-size:1.5rem;font-weight:900;color:#fff;animation:pulse 0.3s infinite;">🟢 CLICK NOW!</div>',unsafe_allow_html=True)
        if st.button("🟢 CLICK!",type="primary",use_container_width=True,key=f"rt_click_{len(times)}"):
            rt=int((time.time()-st.session_state.rt_start_ts)*1000)
            st.session_state.rt_times.append(rt); st.session_state.rt_state="idle"; st.success(f"⚡ {rt}ms!"); st.rerun()


# ═══════════════════════════════════════════
# 27. ROCK PAPER SCISSORS LIZARD SPOCK
# ═══════════════════════════════════════════
RPSLS_OPTIONS=["Rock","Paper","Scissors","Lizard","Spock"]
RPSLS_BEATS={"Rock":["Scissors","Lizard"],"Paper":["Rock","Spock"],"Scissors":["Paper","Lizard"],"Lizard":["Spock","Paper"],"Spock":["Rock","Scissors"]}
RPSLS_EMOJIS={"Rock":"🪨","Paper":"📄","Scissors":"✂️","Lizard":"🦎","Spock":"🖖"}
RPSLS_RULES={"Rock":{"Scissors":"Rock crushes Scissors","Lizard":"Rock crushes Lizard"},"Paper":{"Rock":"Paper covers Rock","Spock":"Paper disproves Spock"},"Scissors":{"Paper":"Scissors cuts Paper","Lizard":"Scissors decapitates Lizard"},"Lizard":{"Spock":"Lizard poisons Spock","Paper":"Lizard eats Paper"},"Spock":{"Rock":"Spock vaporizes Rock","Scissors":"Spock smashes Scissors"}}

def render_rps_lizard_spock():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#818cf8;margin-bottom:8px;">🖖 Rock Paper Scissors Lizard Spock</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">5 choices. 10 rules. AI learns your patterns. Best of 5!</div>', unsafe_allow_html=True)
    if "rpsls_sc" not in st.session_state: st.session_state.rpsls_sc={"You":0,"AI":0}; st.session_state.rpsls_hist=[]; st.session_state.rpsls_res=None
    sc=st.session_state.rpsls_sc; hist=st.session_state.rpsls_hist; wins_needed=3
    c1,c2=st.columns(2); c1.metric("🧑 You",sc["You"]); c2.metric("🤖 AI",sc["AI"])
    if sc["You"]>=wins_needed or sc["AI"]>=wins_needed:
        winner="You" if sc["You"]>=wins_needed else "AI"
        st.success(f"🏆 {winner} wins the match!" if winner=="You" else f"🤖 AI wins the match!")
        _score_update("RPSLS",sc["You"])
        if st.button("🔄 Rematch",use_container_width=True,key="rpsls_new"): st.session_state.rpsls_sc={"You":0,"AI":0}; st.session_state.rpsls_hist=[]; st.session_state.rpsls_res=None; st.rerun()
        return
    if st.session_state.rpsls_res:
        res=st.session_state.rpsls_res
        cc1,cc2=st.columns(2)
        cc1.markdown(f'<div style="text-align:center;font-size:3rem;">{RPSLS_EMOJIS[res["you"]]}</div><div style="text-align:center;">You: {res["you"]}</div>',unsafe_allow_html=True)
        cc2.markdown(f'<div style="text-align:center;font-size:3rem;">{RPSLS_EMOJIS[res["ai"]]}</div><div style="text-align:center;">AI: {res["ai"]}</div>',unsafe_allow_html=True)
        st.info(f"Result: **{res['outcome']}** — {res.get('rule','')}")
        if st.button("▶ Next Round",type="primary",use_container_width=True,key="rpsls_next"): st.session_state.rpsls_res=None; st.rerun()
        return
    st.markdown("**Choose your move:**")
    cols=st.columns(5)
    for i,opt in enumerate(RPSLS_OPTIONS):
        if cols[i].button(f"{RPSLS_EMOJIS[opt]}\n{opt}",key=f"rpsls_{opt}",use_container_width=True):
            # AI picks counter to most common player move in last 3
            if len(hist)>=3:
                last3=[h["you"] for h in hist[-3:]]
                most=max(set(last3),key=last3.count)
                # pick what beats it
                counters=[k for k,v in RPSLS_BEATS.items() if most in v]
                ai_pick=random.choice(counters) if counters else random.choice(RPSLS_OPTIONS)
            else:
                ai_pick=random.choice(RPSLS_OPTIONS)
            if ai_pick in RPSLS_BEATS.get(opt,[]): outcome="You win!"; sc["You"]+=1; rule=RPSLS_RULES.get(opt,{}).get(ai_pick,"")
            elif opt in RPSLS_BEATS.get(ai_pick,[]): outcome="AI wins!"; sc["AI"]+=1; rule=RPSLS_RULES.get(ai_pick,{}).get(opt,"")
            else: outcome="Draw!"; rule=""
            result={"you":opt,"ai":ai_pick,"outcome":outcome,"rule":rule}
            hist.append(result); st.session_state.rpsls_hist=hist; st.session_state.rpsls_sc=sc; st.session_state.rpsls_res=result; st.rerun()


# ═══════════════════════════════════════════
# 28. HIGHER OR LOWER
# ═══════════════════════════════════════════
SUITS=["♠","♥","♦","♣"]; VALS=["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
VAL_RANK={v:i for i,v in enumerate(VALS)}
SUIT_COLORS={"♠":"#1e293b","♥":"#dc2626","♦":"#dc2626","♣":"#1e293b"}

def _card_html(val,suit):
    color=SUIT_COLORS.get(suit,"#1e293b"); bg="#f8fafc" if suit in["♥","♦"] else "#1e293b"; txt="#000" if suit in["♥","♦"] else "#fff"
    return f'<div style="display:inline-block;width:70px;height:100px;background:{bg};border:2px solid #334155;border-radius:10px;text-align:center;line-height:100px;font-size:1.5rem;font-weight:900;color:{txt};box-shadow:0 4px 12px rgba(0,0,0,0.3);">{val}{suit}</div>'

def render_higher_lower():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fbbf24;margin-bottom:8px;">🃏 Higher or Lower</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Will the next card be Higher or Lower? 3 lives. Keep your streak!</div>', unsafe_allow_html=True)
    if "hl_deck" not in st.session_state or st.session_state.get("hl_rst"):
        deck=[(v,s) for v in VALS for s in SUITS]; random.shuffle(deck)
        st.session_state.hl_deck=deck; st.session_state.hl_idx=0; st.session_state.hl_lives=3; st.session_state.hl_streak=0; st.session_state.hl_res=None; st.session_state.hl_rst=False
    deck=st.session_state.hl_deck; idx=st.session_state.hl_idx; lives=st.session_state.hl_lives; streak=st.session_state.hl_streak
    c1,c2,c3=st.columns(3); c1.metric("❤️ Lives",lives); c2.metric("🔥 Streak",streak); c3.metric("Card",f"{idx+1}/52")
    current=deck[idx]; cv=current[0]; cs=current[1]
    st.markdown(f'<div style="text-align:center;margin:16px 0;">{_card_html(cv,cs)}</div>',unsafe_allow_html=True)
    if st.session_state.hl_res:
        res=st.session_state.hl_res; nxt=deck[idx]
        st.markdown(f'<div style="text-align:center;margin-bottom:10px;">{_card_html(nxt[0],nxt[1])}</div>',unsafe_allow_html=True)
        if res: st.success(f"✅ Correct! Streak: {streak}"); 
        else: st.error(f"❌ Wrong! Lives: {lives}")
        if st.button("▶ Next Card",type="primary",use_container_width=True,key="hl_next"): st.session_state.hl_res=None; st.rerun()
        return
    if lives>0 and idx<51:
        cc1,cc2=st.columns(2)
        if cc1.button("📈 Higher",use_container_width=True,key="hl_hi",type="primary"):
            nxt=deck[idx+1]; correct=VAL_RANK[nxt[0]]>=VAL_RANK[cv]
            st.session_state.hl_idx+=1
            if correct: st.session_state.hl_streak+=1; _score_update("Higher or Lower",streak+1)
            else: st.session_state.hl_lives-=1; st.session_state.hl_streak=0
            st.session_state.hl_res=correct; st.rerun()
        if cc2.button("📉 Lower",use_container_width=True,key="hl_lo",type="primary"):
            nxt=deck[idx+1]; correct=VAL_RANK[nxt[0]]<=VAL_RANK[cv]
            st.session_state.hl_idx+=1
            if correct: st.session_state.hl_streak+=1; _score_update("Higher or Lower",streak+1)
            else: st.session_state.hl_lives-=1; st.session_state.hl_streak=0
            st.session_state.hl_res=correct; st.rerun()
    elif lives<=0: st.error(f"💀 Game Over! Final streak: {streak}"); _score_update("Higher or Lower",streak)
    else: st.success(f"🎉 Full deck! Final streak: {streak}")
    if st.button("🔄 New Deck",use_container_width=True,key="hl_new"): st.session_state.hl_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 29. TRUE/FALSE BLITZ
# ═══════════════════════════════════════════
TF_TOPICS=["Science","History","Geography","Sports","Technology","Animals","Movies","Mathematics","Music","Space"]

def render_true_false_blitz():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#f43f5e;margin-bottom:8px;">⚡ True/False Blitz</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">10 rapid-fire statements. 30 seconds. How many can you get?</div>', unsafe_allow_html=True)
    if "tf_stmts" not in st.session_state: st.session_state.tf_stmts=None; st.session_state.tf_idx=0; st.session_state.tf_correct=0; st.session_state.tf_start=None; st.session_state.tf_done=False
    topic=st.selectbox("Topic",TF_TOPICS,key="tf_topic")
    if st.session_state.tf_stmts is None:
        if st.button("🚀 Start Blitz!",type="primary",use_container_width=True,key="tf_start"):
            with st.spinner("AI generating statements..."):
                raw=_ai(f'Give 10 true/false trivia statements about {topic}. Return ONLY valid JSON array: [{{"statement":"...","is_true":true}}]',600)
                stmts=_parse_json_list(raw)
                if not stmts: stmts=[{"statement":f"The Earth revolves around the Sun","is_true":True} for _ in range(10)]
            st.session_state.tf_stmts=stmts[:10]; st.session_state.tf_idx=0; st.session_state.tf_correct=0; st.session_state.tf_start=time.time(); st.session_state.tf_done=False; st.rerun()
        return
    stmts=st.session_state.tf_stmts; idx=st.session_state.tf_idx; elapsed=time.time()-st.session_state.tf_start; remaining=max(0,30-elapsed)
    if st.session_state.tf_done or remaining<=0 or idx>=10:
        c=st.session_state.tf_correct
        st.success(f"⏱ Done! Score: **{c}/10** | Accuracy: {c*10}%"); _score_update("True/False Blitz",c)
        with st.expander("📋 Review Answers"):
            for i,s in enumerate(stmts[:idx]):
                st.markdown(f"{i+1}. {s['statement']} — {'✅ True' if s['is_true'] else '❌ False'}")
        if st.button("🔄 Play Again",use_container_width=True,key="tf_again"): st.session_state.tf_stmts=None; st.rerun()
        return
    st.progress(remaining/30,text=f"⏱ {remaining:.0f}s | Question {idx+1}/10")
    stmt=stmts[idx]
    st.markdown(f'<div style="background:rgba(244,63,94,0.06);border:1px solid rgba(244,63,94,0.2);border-radius:14px;padding:20px;text-align:center;font-size:1.1rem;font-weight:700;color:#f8fafc;min-height:80px;display:flex;align-items:center;justify-content:center;">{stmt["statement"]}</div>',unsafe_allow_html=True)
    cc1,cc2=st.columns(2)
    if cc1.button("✅ True",use_container_width=True,key=f"tf_t_{idx}",type="primary"):
        if stmt["is_true"]==True: st.session_state.tf_correct+=1
        st.session_state.tf_idx+=1; st.rerun()
    if cc2.button("❌ False",use_container_width=True,key=f"tf_f_{idx}",type="primary"):
        if stmt["is_true"]==False: st.session_state.tf_correct+=1
        st.session_state.tf_idx+=1; st.rerun()


# ═══════════════════════════════════════════
# 30. EMOJI REBUS
# ═══════════════════════════════════════════
def render_emoji_rebus():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#a3e635;margin-bottom:8px;">🧩 Emoji Rebus</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Decode emoji combinations to find the hidden phrase!</div>', unsafe_allow_html=True)
    if "er_puzzles" not in st.session_state or st.session_state.get("er_rst"):
        st.session_state.er_puzzles=None; st.session_state.er_idx=0; st.session_state.er_score=0; st.session_state.er_wrong={}; st.session_state.er_rst=False
    if st.session_state.er_puzzles is None:
        if st.button("🎲 Generate Puzzles",type="primary",use_container_width=True,key="er_gen"):
            with st.spinner("AI creating emoji puzzles..."):
                raw=_ai('Create 5 emoji rebus puzzles representing common phrases or words. Return ONLY valid JSON array: [{"emojis":"🐍🍎","answer":"bad apple","hint":"a common saying about one person spoiling a group"}]',500)
                ps=_parse_json_list(raw)
                if not ps: ps=[{"emojis":"🌊➕🏄","answer":"surfing","hint":"water sport"},{"emojis":"☀️➕🌻","answer":"sunflower","hint":"a tall yellow flower"},{"emojis":"🏠➕🔑","answer":"house key","hint":"what lets you in"},{"emojis":"⭐➕🌙","answer":"starmoon","hint":"night sky objects"},{"emojis":"🔥➕🚒","answer":"fire truck","hint":"emergency vehicle"}]
            st.session_state.er_puzzles=ps[:5]; st.rerun()
        return
    puzzles=st.session_state.er_puzzles; idx=st.session_state.er_idx
    if idx>=len(puzzles):
        sc=st.session_state.er_score
        st.success(f"🎉 All done! Score: **{sc}/{len(puzzles)}**"); _score_update("Emoji Rebus",sc)
        if st.button("🔄 New Set",use_container_width=True,key="er_new"): st.session_state.er_rst=True; st.rerun()
        return
    p=puzzles[idx]; wrong_count=st.session_state.er_wrong.get(idx,0)
    st.caption(f"Puzzle {idx+1}/{len(puzzles)} | Score: {st.session_state.er_score}")
    st.markdown(f'<div style="font-size:3rem;text-align:center;margin:20px 0;letter-spacing:4px;">{p.get("emojis","❓")}</div>',unsafe_allow_html=True)
    if wrong_count>=2: st.info(f"💡 Hint: {p.get('hint','...')}")
    ans=st.text_input("Your answer:",key=f"er_ans_{idx}",placeholder="What phrase/word does this represent?").lower().strip()
    cc1,cc2=st.columns(2)
    if cc1.button("✅ Submit",type="primary",use_container_width=True,key=f"er_sub_{idx}"):
        correct_ans=p.get("answer","").lower()
        if ans in correct_ans or correct_ans in ans:
            st.success(f"🎉 Correct! Answer: **{p['answer']}**"); st.session_state.er_score+=1; st.session_state.er_idx+=1; st.rerun()
        else:
            st.session_state.er_wrong[idx]=wrong_count+1; st.error(f"❌ Wrong! Try again. ({2-wrong_count-1} hint in)")
            if wrong_count+1>=3: st.info(f"Answer: **{p.get('answer','')}**"); st.session_state.er_idx+=1; time.sleep(1); st.rerun()
    if cc2.button("⏭ Skip",use_container_width=True,key=f"er_skip_{idx}"):
        st.session_state.er_idx+=1; st.rerun()


# ═══════════════════════════════════════════
# 31. TYPING SPEED TEST
# ═══════════════════════════════════════════
def render_typing_speed():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#38bdf8;margin-bottom:8px;">⌨️ Typing Speed Test</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Type the paragraph as fast as you can. WPM + accuracy graded!</div>', unsafe_allow_html=True)
    if "ts_para" not in st.session_state or st.session_state.get("ts_rst"):
        st.session_state.ts_para=None; st.session_state.ts_done=False; st.session_state.ts_start=None; st.session_state.ts_rst=False
    if st.session_state.ts_para is None:
        if st.button("🎲 Get Paragraph",type="primary",use_container_width=True,key="ts_gen"):
            with st.spinner("AI generating paragraph..."):
                topic=random.choice(["space exploration","machine learning","ancient civilizations","ocean mysteries","quantum physics","climate change","video game history","the human brain"])
                raw=_ai(f"Write an interesting 50-word paragraph about {topic}. Make it engaging and factual. No fluff.",120)
                if not raw.strip(): raw="The universe is vast and contains billions of galaxies, each with billions of stars. Scientists study these cosmic structures to understand the origins of space, time, and matter that make up everything we know."
            st.session_state.ts_para=raw.strip(); st.rerun()
        return
    para=st.session_state.ts_para
    st.markdown(f'<div style="background:rgba(56,189,248,0.05);border:1px solid rgba(56,189,248,0.2);border-radius:12px;padding:16px;font-size:.95rem;line-height:1.7;color:#cbd5e1;margin-bottom:12px;">{para}</div>',unsafe_allow_html=True)
    if not st.session_state.ts_done:
        typed=st.text_area("Type the paragraph above:",height=120,key="ts_input",placeholder="Start typing here... (timer starts when you click Submit)")
        if st.button("✅ Submit",type="primary",use_container_width=True,key="ts_submit") and typed.strip():
            if st.session_state.ts_start is None: st.session_state.ts_start=time.time()-10
            elapsed=time.time()-st.session_state.ts_start
            if elapsed<1: elapsed=10
            words_typed=len(typed.split()); wpm=int(words_typed/(elapsed/60))
            correct=sum(1 for a,b in zip(typed,para) if a==b); accuracy=round(correct/max(1,len(para))*100,1)
            grade="🏆 Pro Typist!" if wpm>=100 else "⚡ Fast!" if wpm>=70 else "👍 Average" if wpm>=40 else "🐌 Beginner"
            st.session_state.ts_done=True
            st.success(f"⌨️ **{wpm} WPM** | **{accuracy}% accuracy** | {grade}")
            st.metric("Words Per Minute",wpm); st.metric("Accuracy",f"{accuracy}%")
            _score_update("Typing Speed",wpm)
        else:
            if st.session_state.ts_start is None and typed: st.session_state.ts_start=time.time()
    if st.button("🔄 New Text",use_container_width=True,key="ts_new"): st.session_state.ts_rst=True; st.rerun()
