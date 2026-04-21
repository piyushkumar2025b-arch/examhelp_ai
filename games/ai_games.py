"""
games/ai_games.py — AI Conversation & Roleplay Games (19-25)
19. 20 Questions  20. Trivia Battle  21. Would You Rather
22. Debate Me  23. Two Truths One Lie  24. Story Collab  25. Moral Dilemma
"""
from __future__ import annotations
import streamlit as st
import random
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

def _parse_json(raw: str) -> dict:
    try:
        s=raw.find("{"); e=raw.rfind("}")+1; return json.loads(raw[s:e])
    except Exception:
        return {}

def _parse_json_list(raw: str) -> list:
    try:
        s=raw.find("["); e=raw.rfind("]")+1; return json.loads(raw[s:e])
    except Exception:
        return []


# ═══════════════════════════════════════════
# 19. 20 QUESTIONS
# ═══════════════════════════════════════════
def render_twenty_questions():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#c4b5fd;margin-bottom:8px;">❓ 20 Questions</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">AI thinks of something. Ask yes/no questions to guess it!</div>', unsafe_allow_html=True)
    if "tq_ans" not in st.session_state or st.session_state.get("tq_rst"):
        with st.spinner("AI picking a secret..."):
            r=_ai("Pick a famous person, animal, or object to think of. Reply ONLY with the single word answer, nothing else.",20)
        st.session_state.tq_ans=r.strip().split()[0] if r.strip() else "elephant"
        st.session_state.tq_qs=[]; st.session_state.tq_won=False; st.session_state.tq_rst=False
    ans=st.session_state.tq_ans; qs=st.session_state.tq_qs; q_count=len(qs); won=st.session_state.tq_won
    st.progress(q_count/20,text=f"Questions: {q_count}/20")
    if qs:
        with st.expander("📋 Q&A History",expanded=True):
            for i,(q,a) in enumerate(qs):
                icon="✅" if "yes" in a.lower() else "❌" if "no" in a.lower() else "❓"
                st.markdown(f"**{i+1}.** {q} → {icon} *{a}*")
    if won: st.success(f"🎉 You got it! The answer was **{ans.upper()}**!"); _score_update("20 Questions",20-q_count)
    elif q_count>=20: st.error(f"😞 Out of questions! It was **{ans.upper()}**!")
    else:
        col_q,col_g=st.columns([3,1])
        with col_q: user_q=st.text_input("Ask a yes/no question:",placeholder="e.g. Is it alive? Can you eat it?",key=f"tq_in_{q_count}")
        with col_g: is_guess=st.checkbox("Guess!",key="tq_guess_mode")
        if st.button("Submit",type="primary",use_container_width=True,key="tq_sub") and user_q.strip():
            if is_guess:
                if user_q.strip().lower() in ans.lower() or ans.lower() in user_q.strip().lower():
                    st.session_state.tq_won=True; qs.append((f"[GUESS] {user_q}","YES! That's it!"))
                else: qs.append((f"[GUESS] {user_q}","No, that's not it."))
            else:
                with st.spinner("AI thinking..."):
                    a_resp=_ai(f"You are thinking of: '{ans}'. Player asks: '{user_q}'. Reply ONLY: 'Yes', 'No', or 'Maybe'.",10)
                qs.append((user_q,a_resp.strip() or "Maybe"))
            st.session_state.tq_qs=qs; st.rerun()
    col_r,col_rev=st.columns(2)
    if col_r.button("🔄 New Game",use_container_width=True,key="tq_new"): st.session_state.tq_rst=True; st.rerun()
    if col_rev.button("💡 Give Up",use_container_width=True,key="tq_rev"): st.info(f"It was: **{ans.upper()}**")


# ═══════════════════════════════════════════
# 20. TRIVIA BATTLE
# ═══════════════════════════════════════════
TRIVIA_CATS=["Science","History","Geography","Sports","Technology","Movies","Literature","Music","Mathematics","General Knowledge"]

def render_trivia_battle():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fde68a;margin-bottom:8px;">🏆 Trivia Battle</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">You vs AI — same question, who scores more? Best of 10!</div>', unsafe_allow_html=True)
    if "tb_scores" not in st.session_state: st.session_state.tb_scores={"You":0,"AI":0}; st.session_state.tb_q=None; st.session_state.tb_res=None; st.session_state.tb_round=0
    sc=st.session_state.tb_scores; c1,c2,c3=st.columns(3)
    c1.metric("🧑 You",sc["You"]); c2.metric("🤖 AI",sc["AI"]); c3.metric("Round",f"{st.session_state.tb_round}/10")
    cat=st.selectbox("Category",TRIVIA_CATS,key="tb_cat")
    if st.session_state.tb_q is None:
        if st.session_state.tb_round>=10:
            winner="You" if sc["You"]>sc["AI"] else "AI" if sc["AI"]>sc["You"] else "Tie"
            st.success(f"🏁 Game over! Winner: **{winner}** | You: {sc['You']} | AI: {sc['AI']}")
            _score_update("Trivia Battle",sc["You"])
            if st.button("🔄 Rematch",use_container_width=True,key="tb_rematch"):
                st.session_state.tb_scores={"You":0,"AI":0}; st.session_state.tb_round=0; st.rerun()
            return
        if st.button("🎲 Next Question",type="primary",use_container_width=True,key="tb_gen"):
            with st.spinner("Generating question..."):
                raw=_ai(f'Generate a trivia question about {cat}. Return ONLY valid JSON: {{"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"answer":"A","explanation":"..."}}',400)
                st.session_state.tb_q=_parse_json(raw); st.session_state.tb_res=None; st.rerun()
    else:
        qd=st.session_state.tb_q
        st.markdown(f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:18px;margin:10px 0;"><div style="font-size:.75rem;color:#64748b;margin-bottom:6px;">ROUND {st.session_state.tb_round+1} · {cat.upper()}</div><div style="font-size:1.05rem;font-weight:700;color:#f8fafc;">{qd.get("question","")}</div></div>',unsafe_allow_html=True)
        opts=[f"{k}) {v}" for k,v in qd.get("options",{}).items()]
        if st.session_state.tb_res is None:
            choice=st.radio("Your answer:",opts,key=f"tb_radio_{st.session_state.tb_round}")
            user_letter=choice[0] if choice else "A"
            if st.button("✅ Lock In Answer",type="primary",use_container_width=True,key="tb_submit"):
                with st.spinner("AI answering..."):
                    ai_raw=_ai(f"Question: {qd.get('question','')} Options: {qd.get('options',{})}. Reply ONLY the letter (A/B/C/D).",5)
                ai_letter=ai_raw.strip().upper()[0] if ai_raw.strip() else random.choice(["A","B","C","D"])
                correct=qd.get("answer","A")
                u_ok=user_letter==correct; a_ok=ai_letter==correct
                if u_ok: st.session_state.tb_scores["You"]+=1
                if a_ok: st.session_state.tb_scores["AI"]+=1
                st.session_state.tb_res={"user":user_letter,"ai":ai_letter,"correct":correct,"u_ok":u_ok,"a_ok":a_ok}
                st.session_state.tb_round+=1; st.rerun()
        else:
            res=st.session_state.tb_res
            c_opt=next((f"{k}) {v}" for k,v in qd.get("options",{}).items() if k==res["correct"]),res["correct"])
            cc1,cc2=st.columns(2)
            with cc1:
                clr="#22c55e22" if res["u_ok"] else "#ef444422"
                bc="#22c55e" if res["u_ok"] else "#ef4444"
                st.markdown(f'<div style="background:{clr};border:1px solid {bc};border-radius:12px;padding:14px;text-align:center;"><div style="font-size:1.5rem;">{"✅" if res["u_ok"] else "❌"}</div><div style="font-weight:700;color:#f8fafc;">You: {res["user"]}</div></div>',unsafe_allow_html=True)
            with cc2:
                clr="#22c55e22" if res["a_ok"] else "#ef444422"
                bc="#22c55e" if res["a_ok"] else "#ef4444"
                st.markdown(f'<div style="background:{clr};border:1px solid {bc};border-radius:12px;padding:14px;text-align:center;"><div style="font-size:1.5rem;">🤖{"✅" if res["a_ok"] else "❌"}</div><div style="font-weight:700;color:#f8fafc;">AI: {res["ai"]}</div></div>',unsafe_allow_html=True)
            st.info(f"✅ Correct: {c_opt} — {qd.get('explanation','')}")
            if st.button("▶ Next",type="primary",use_container_width=True,key="tb_next"): st.session_state.tb_q=None; st.rerun()
    if st.button("🔄 Reset",use_container_width=True,key="tb_reset"): st.session_state.tb_scores={"You":0,"AI":0}; st.session_state.tb_q=None; st.session_state.tb_round=0; st.rerun()


# ═══════════════════════════════════════════
# 21. WOULD YOU RATHER
# ═══════════════════════════════════════════
def render_would_you_rather():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#f9a8d4;margin-bottom:8px;">🤔 Would You Rather</div>', unsafe_allow_html=True)
    if "wyr_data" not in st.session_state or st.session_state.get("wyr_rst"):
        st.session_state.wyr_data=None; st.session_state.wyr_chose=None; st.session_state.wyr_rst=False
    if st.button("🎲 New Dilemma",type="primary",use_container_width=True,key="wyr_gen"):
        with st.spinner("AI generating dilemma..."):
            raw=_ai('Generate a funny/interesting "Would you rather" question. Return ONLY valid JSON: {"option_a":"...","option_b":"..."}',150)
            st.session_state.wyr_data=_parse_json(raw); st.session_state.wyr_chose=None; st.rerun()
    if st.session_state.wyr_data:
        d=st.session_state.wyr_data; a=d.get("option_a","Option A"); b=d.get("option_b","Option B")
        st.markdown(f'<div style="background:rgba(249,168,212,0.05);border:1px solid rgba(249,168,212,0.15);border-radius:16px;padding:20px;margin:12px 0;text-align:center;"><div style="font-size:1rem;font-weight:700;color:#f8fafc;">Would you rather...</div></div>',unsafe_allow_html=True)
        cc1,cc2=st.columns(2)
        with cc1:
            st.markdown(f'<div style="background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.3);border-radius:12px;padding:16px;text-align:center;min-height:80px;display:flex;align-items:center;justify-content:center;">{a}</div>',unsafe_allow_html=True)
            if st.button("Choose A",use_container_width=True,key="wyr_a"): st.session_state.wyr_chose="A"; st.rerun()
        with cc2:
            st.markdown(f'<div style="background:rgba(236,72,153,0.1);border:1px solid rgba(236,72,153,0.3);border-radius:12px;padding:16px;text-align:center;min-height:80px;display:flex;align-items:center;justify-content:center;">{b}</div>',unsafe_allow_html=True)
            if st.button("Choose B",use_container_width=True,key="wyr_b"): st.session_state.wyr_chose="B"; st.rerun()
        if st.session_state.wyr_chose:
            chosen_txt=a if st.session_state.wyr_chose=="A" else b
            with st.spinner("AI picking too..."):
                ai_resp=_ai(f'Would you rather: A) "{a}" OR B) "{b}"? Pick one and explain briefly. Reply: "I choose A/B because..."',150)
            sim_pct=random.randint(45,75) if st.session_state.wyr_chose=="A" else random.randint(25,55)
            st.success(f"You chose: **{chosen_txt}**")
            st.info(f"🤖 AI says: {ai_resp}")
            st.caption(f"📊 Simulated stat: {sim_pct}% of people chose {'A' if st.session_state.wyr_chose=='A' else 'B'}")


# ═══════════════════════════════════════════
# 22. DEBATE ME
# ═══════════════════════════════════════════
DEBATE_TOPICS=["Social media does more harm than good","AI will replace human jobs","Homework should be abolished","Space exploration is worth the cost","Remote work is better than office work","Video games cause violence","Nuclear energy is the future","Universal basic income should be implemented"]

def render_debate_me():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#34d399;margin-bottom:8px;">🎤 Debate Me</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">Pick a topic & your side. Go 3 rounds. AI judges the winner!</div>', unsafe_allow_html=True)
    if "db_transcript" not in st.session_state or st.session_state.get("db_rst"):
        st.session_state.db_transcript=[]; st.session_state.db_round=0; st.session_state.db_verdict=None; st.session_state.db_rst=False
    topic=st.selectbox("Topic",DEBATE_TOPICS+["Custom..."],key="db_topic")
    if topic=="Custom...": topic=st.text_input("Custom topic:",key="db_custom",placeholder="AI is overhyped")
    side=st.radio("Your side:",["For (Agree)","Against (Disagree)"],horizontal=True,key="db_side")
    ai_side="Against" if "For" in side else "For"
    rnd=st.session_state.db_round; transcript=st.session_state.db_transcript
    if transcript:
        with st.expander("📜 Debate Transcript",expanded=True):
            for speaker,text in transcript: st.markdown(f"**{'🧑 You' if speaker=='You' else '🤖 AI'}:** {text}")
    if st.session_state.db_verdict:
        st.markdown(f"### ⚖️ Verdict"); st.info(st.session_state.db_verdict)
        _score_update("Debate Me",1)
        if st.button("🔄 New Debate",use_container_width=True,key="db_new"): st.session_state.db_rst=True; st.rerun()
        return
    if rnd<3:
        st.caption(f"Round {rnd+1}/3")
        arg=st.text_area(f"Your argument (Round {rnd+1}):",height=100,key=f"db_arg_{rnd}",placeholder="Make your case...")
        if st.button(f"Submit Round {rnd+1}",type="primary",use_container_width=True,key=f"db_sub_{rnd}") and arg.strip():
            transcript.append(("You",arg.strip()))
            with st.spinner("AI is arguing..."):
                prompt=f"Topic: '{topic}'. You argue {ai_side}. Respond to: '{arg}'. Keep it under 100 words. Be persuasive."
                ai_arg=_ai(prompt,200)
            transcript.append(("AI",ai_arg))
            st.session_state.db_transcript=transcript; st.session_state.db_round+=1; st.rerun()
    else:
        if st.button("⚖️ Judge Winner",type="primary",use_container_width=True,key="db_judge"):
            trans_text="\n".join(f"{'You' if s=='You' else 'AI'}: {t}" for s,t in transcript)
            prompt=f"Topic: '{topic}'. You ({side}) vs AI ({ai_side}).\nTranscript:\n{trans_text}\n\nWho made the stronger case? Give a fair 2-sentence verdict."
            with st.spinner("AI judging..."): v=_ai(prompt,300)
            st.session_state.db_verdict=v; st.rerun()


# ═══════════════════════════════════════════
# 23. TWO TRUTHS ONE LIE
# ═══════════════════════════════════════════
TTOL_TOPICS=["Space","Ancient History","Animals","Human Body","Technology","Famous Scientists","World Records","Oceans","Mathematics","Sports"]

def render_two_truths_one_lie():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#fb923c;margin-bottom:8px;">🤥 Two Truths One Lie</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">AI gives 3 statements. Spot the lie!</div>', unsafe_allow_html=True)
    if "ttol_data" not in st.session_state or st.session_state.get("ttol_rst"):
        st.session_state.ttol_data=None; st.session_state.ttol_chosen=None; st.session_state.ttol_rst=False; st.session_state.ttol_score=st.session_state.get("ttol_score",0)
    topic=st.selectbox("Topic",TTOL_TOPICS,key="ttol_topic")
    if st.button("🎲 Generate Statements",type="primary",use_container_width=True,key="ttol_gen"):
        with st.spinner("AI crafting statements..."):
            raw=_ai(f'Give 2 true facts and 1 false fact about {topic}. Make the lie plausible. Return ONLY valid JSON: {{"statements":["...","...","..."],"lie_index":1,"explanation":"why the lie is false"}}',400)
            st.session_state.ttol_data=_parse_json(raw); st.session_state.ttol_chosen=None; st.rerun()
    if st.session_state.ttol_data:
        d=st.session_state.ttol_data; stmts=d.get("statements",["Fact A","Fact B","Lie"]); lie_idx=d.get("lie_index",2)
        st.markdown("**Which one is the LIE?**")
        for i,(s) in enumerate(stmts):
            col_s,col_b=st.columns([5,1])
            col_s.markdown(f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:12px;margin:4px 0;">{i+1}. {s}</div>',unsafe_allow_html=True)
            if col_b.button(f"#{i+1}",key=f"ttol_{i}",use_container_width=True): st.session_state.ttol_chosen=i; st.rerun()
        if st.session_state.ttol_chosen is not None:
            chosen=st.session_state.ttol_chosen
            if chosen==lie_idx:
                st.success(f"🎉 Correct! #{chosen+1} was the lie!"); st.session_state.ttol_score+=1; _score_update("Two Truths One Lie",st.session_state.ttol_score)
            else:
                st.error(f"❌ Wrong! The lie was #{lie_idx+1}.")
            st.info(f"Explanation: {d.get('explanation','')}")
    if st.session_state.ttol_data:
        if st.button("🔄 Next Round",use_container_width=True,key="ttol_new"): st.session_state.ttol_rst=True; st.rerun()


# ═══════════════════════════════════════════
# 24. COLLABORATIVE STORY
# ═══════════════════════════════════════════
def render_story_collab():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#a78bfa;margin-bottom:8px;">📖 Story Collab</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">You write a sentence, AI continues. Alternate for 8 turns!</div>', unsafe_allow_html=True)
    if "sc_story" not in st.session_state or st.session_state.get("sc_rst"):
        st.session_state.sc_story=[]; st.session_state.sc_turn=0; st.session_state.sc_rating=None; st.session_state.sc_rst=False
    story=st.session_state.sc_story; turn=st.session_state.sc_turn
    if story:
        for speaker,text in story:
            icon="🧑" if speaker=="You" else "🤖"
            st.markdown(f'<div style="background:rgba(255,255,255,0.02);border-radius:8px;padding:8px 12px;margin:4px 0;"><span style="font-weight:700;color:#a78bfa;">{icon}</span> {text}</div>',unsafe_allow_html=True)
    if st.session_state.sc_rating:
        r=st.session_state.sc_rating; total=r.get("plot",0)+r.get("creativity",0)+r.get("consistency",0)
        st.markdown("### 📊 Story Ratings")
        c1,c2,c3=st.columns(3)
        c1.metric("📖 Plot",f"{r.get('plot',0)}/10"); c2.metric("🎨 Creativity",f"{r.get('creativity',0)}/10"); c3.metric("🔗 Consistency",f"{r.get('consistency',0)}/10")
        _score_update("Story Collab",total)
        full_text="\n".join(f"{s}: {t}" for s,t in story)
        st.download_button("📥 Download Story",full_text,"our_story.txt","text/plain",use_container_width=True,key="sc_dl")
        if st.button("🔄 New Story",use_container_width=True,key="sc_new"): st.session_state.sc_rst=True; st.rerun()
        return
    if turn>=8:
        with st.spinner("AI writing conclusion..."):
            context=" ".join(t for _,t in story[-4:])
            concl=_ai(f"Story so far: {context}. Write a satisfying 2-sentence conclusion.",150)
        story.append(("AI (Conclusion)",concl)); st.session_state.sc_story=story
        with st.spinner("Rating story..."):
            full="\n".join(f"{s}: {t}" for s,t in story)
            raw=_ai(f"Rate this collaborative story: {full}\nReturn ONLY valid JSON: {{\"plot\":8,\"creativity\":7,\"consistency\":9}}",100)
            st.session_state.sc_rating=_parse_json(raw) or {"plot":7,"creativity":7,"consistency":7}
        st.rerun(); return
    if turn%2==0:
        st.caption(f"Your turn ({turn//2+1}/4)")
        inp=st.text_input("Continue the story:",key=f"sc_in_{turn}",placeholder="Write 1-2 sentences...")
        if st.button("Submit",type="primary",use_container_width=True,key=f"sc_sub_{turn}") and inp.strip():
            story.append(("You",inp.strip()))
            context=" ".join(t for _,t in story[-3:])
            with st.spinner("AI continues..."):
                ai_txt=_ai(f"Continue this story in 1-2 sentences: {context}",120)
            story.append(("AI",ai_txt)); st.session_state.sc_story=story; st.session_state.sc_turn+=2; st.rerun()
    st.caption(f"Turns: {turn}/8")


# ═══════════════════════════════════════════
# 25. MORAL DILEMMA
# ═══════════════════════════════════════════
def render_moral_dilemma():
    st.markdown('<div style="font-size:1.4rem;font-weight:900;color:#f87171;margin-bottom:8px;">⚖️ Moral Dilemma</div><div style="color:#64748b;font-size:.85rem;margin-bottom:10px;">AI presents an ethical scenario. You choose, then get philosophical analysis.</div>', unsafe_allow_html=True)
    if "md_data" not in st.session_state or st.session_state.get("md_rst"):
        st.session_state.md_data=None; st.session_state.md_choice=None; st.session_state.md_reason=""; st.session_state.md_analysis=None; st.session_state.md_rst=False
    if st.button("🎲 New Dilemma",type="primary",use_container_width=True,key="md_gen"):
        with st.spinner("AI generating ethical scenario..."):
            raw=_ai('Create a thought-provoking moral dilemma with 2 clear choices. Return ONLY valid JSON: {"scenario":"...","choice_a":"...","choice_b":"..."}',250)
            st.session_state.md_data=_parse_json(raw); st.session_state.md_choice=None; st.session_state.md_analysis=None; st.rerun()
    if st.session_state.md_data:
        d=st.session_state.md_data
        st.markdown(f'<div style="background:rgba(248,113,113,0.05);border:1px solid rgba(248,113,113,0.15);border-radius:16px;padding:20px;margin:10px 0;font-style:italic;color:#f8fafc;">{d.get("scenario","")}</div>',unsafe_allow_html=True)
        cc1,cc2=st.columns(2)
        with cc1:
            st.markdown(f'<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);border-radius:12px;padding:14px;text-align:center;">🅰️ {d.get("choice_a","")}</div>',unsafe_allow_html=True)
            if st.button("Choose A",use_container_width=True,key="md_ca"): st.session_state.md_choice="A"; st.rerun()
        with cc2:
            st.markdown(f'<div style="background:rgba(236,72,153,0.08);border:1px solid rgba(236,72,153,0.2);border-radius:12px;padding:14px;text-align:center;">🅱️ {d.get("choice_b","")}</div>',unsafe_allow_html=True)
            if st.button("Choose B",use_container_width=True,key="md_cb"): st.session_state.md_choice="B"; st.rerun()
        if st.session_state.md_choice:
            chosen=d.get("choice_a") if st.session_state.md_choice=="A" else d.get("choice_b")
            reason=st.text_area("Explain your reasoning:",key="md_reason",placeholder="Why did you choose this?")
            if st.button("🔬 Analyse",type="primary",use_container_width=True,key="md_analyse"):
                prompt=(f"Scenario: {d.get('scenario','')} User chose: {chosen}. Reason: {reason}.\n"
                        f"Analyse from 3 perspectives (2 sentences each): utilitarian, deontological, virtue ethics. "
                        f"End with: which famous philosopher would agree with this choice and why.")
                with st.spinner("Philosophical analysis..."):
                    st.session_state.md_analysis=_ai(prompt,500)
                st.rerun()
        if st.session_state.md_analysis:
            st.markdown("### 🏛️ Philosophical Analysis"); st.markdown(st.session_state.md_analysis); _score_update("Moral Dilemma",1)
