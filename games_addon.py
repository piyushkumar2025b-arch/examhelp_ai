"""games_addon.py — Steps 25-26: Typing Speed game + Memory Cards + Leaderboard"""
import streamlit as st, random, time, datetime

WORDS_EASY = ["apple","chair","light","bread","cloud","storm","brain","water","music","phone"]
WORDS_MED  = ["algorithm","frequency","establish","knowledge","ambitious","curiosity","brilliant"]
WORDS_HARD = ["serendipity","ephemeral","perspicacious","ubiquitous","magnanimous","circumspect"]

MEMORY_EMOJIS = ["🎯","🚀","🎨","⚡","🌊","🔥","💎","🌸","🎭","🏆","🦋","🌙"]

def render_games_addon():
    g1, g2, g3 = st.tabs(["⌨️ Typing Speed Test", "🧩 Memory Cards", "🏆 Leaderboard"])

    with g1:
        st.markdown("**⌨️ Typing Speed Test (WPM)**")
        level = st.selectbox("Difficulty:", ["Easy","Medium","Hard"], key="ga_typ_lvl")
        word_pool = {"Easy":WORDS_EASY,"Medium":WORDS_MED,"Hard":WORDS_HARD}[level]

        if st.button("🎯 New Test", key="ga_new_test", use_container_width=True, type="primary"):
            st.session_state.ga_test_words = random.sample(word_pool*4, min(20,len(word_pool*4)))
            st.session_state.ga_test_start = None
            st.session_state.ga_test_done = False
            st.rerun()

        if st.session_state.get("ga_test_words"):
            target = " ".join(st.session_state.ga_test_words)
            st.markdown(f"""
            <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(99,102,241,0.25);
                border-radius:14px;padding:18px;font-family:'JetBrains Mono',monospace;
                font-size:1rem;color:#c7d2fe;line-height:1.8;letter-spacing:1px;">{target}</div>
            """, unsafe_allow_html=True)
            typed = st.text_area("Type the text above:", height=80, key="ga_typed")
            if st.button("✅ Submit", key="ga_submit", use_container_width=True):
                typed_words = typed.strip().split()
                target_words = st.session_state.ga_test_words
                correct = sum(1 for a,b in zip(typed_words, target_words) if a==b)
                total = len(target_words); accuracy = correct/max(total,1)*100
                # estimate 1 min test
                wpm = correct
                st.success(f"✅ WPM: **{wpm}** · Accuracy: **{accuracy:.1f}%** · Correct: {correct}/{total}")
                # Save to leaderboard
                lb = st.session_state.get("ga_leaderboard", [])
                lb.append({"name": st.session_state.get("ga_player","You"),
                           "wpm": wpm, "acc": round(accuracy,1),
                           "level": level, "date": str(datetime.date.today())})
                lb.sort(key=lambda x: x["wpm"], reverse=True)
                st.session_state.ga_leaderboard = lb[:20]

    with g2:
        st.markdown("**🧩 Memory Card Game**")
        grid_size = st.selectbox("Grid:", ["2×2 (Easy)","3×4 (Medium)","4×4 (Hard)"], key="ga_mem_grid")
        pairs_needed = {"2×2 (Easy)":2,"3×4 (Medium)":6,"4×4 (Hard)":8}[grid_size]
        cols_count = {"2×2 (Easy)":2,"3×4 (Medium)":4,"4×4 (Hard)":4}[grid_size]

        if st.button("🔀 New Game", key="ga_mem_new", use_container_width=True, type="primary"):
            emojis = random.sample(MEMORY_EMOJIS, pairs_needed)
            board = emojis * 2; random.shuffle(board)
            st.session_state.ga_mem_board = board
            st.session_state.ga_mem_revealed = [False]*len(board)
            st.session_state.ga_mem_matched = [False]*len(board)
            st.session_state.ga_mem_flipped = []
            st.session_state.ga_mem_moves = 0
            st.rerun()

        if st.session_state.get("ga_mem_board"):
            board = st.session_state.ga_mem_board
            revealed = st.session_state.ga_mem_revealed
            matched = st.session_state.ga_mem_matched
            flipped = st.session_state.ga_mem_flipped
            moves = st.session_state.ga_mem_moves

            st.markdown(f"**Moves: {moves}** · Matches: {sum(matched)//2}/{len(board)//2}")
            bcols = st.columns(cols_count)
            for i in range(len(board)):
                with bcols[i%cols_count]:
                    if matched[i]:
                        st.markdown(f'<div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:20px;text-align:center;font-size:1.8rem;">{board[i]}</div>', unsafe_allow_html=True)
                    elif revealed[i] or i in flipped:
                        st.markdown(f'<div style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);border-radius:12px;padding:20px;text-align:center;font-size:1.8rem;">{board[i]}</div>', unsafe_allow_html=True)
                    else:
                        if st.button("❓", key=f"ga_card_{i}", use_container_width=True):
                            if i not in flipped and len(flipped)<2 and not matched[i]:
                                flipped.append(i)
                                st.session_state.ga_mem_flipped = flipped
                                if len(flipped)==2:
                                    st.session_state.ga_mem_moves += 1
                                    if board[flipped[0]]==board[flipped[1]]:
                                        matched[flipped[0]]=matched[flipped[1]]=True
                                        st.session_state.ga_mem_matched=matched
                                    st.session_state.ga_mem_flipped=[]
                                st.rerun()

            if all(matched):
                st.balloons(); st.success(f"🎉 You matched all cards in {moves} moves!")

    with g3:
        st.markdown("**🏆 Typing Speed Leaderboard**")
        lb = st.session_state.get("ga_leaderboard", [])
        player_name = st.text_input("Your display name:", value="Player", key="ga_player")
        if lb:
            for i, entry in enumerate(lb[:10]):
                medal = ["🥇","🥈","🥉"][i] if i<3 else f"#{i+1}"
                st.markdown(f"""
                <div style="background:rgba(10,14,30,{'0.9' if i==0 else '0.6'});border:1px solid rgba({'245,158,11' if i==0 else '255,255,255'},{'0.35' if i==0 else '0.07'});border-radius:12px;padding:12px 18px;margin-bottom:6px;display:flex;align-items:center;gap:14px;">
                    <span style="font-size:1.3rem;">{medal}</span>
                    <div style="flex:1;font-weight:700;color:rgba(255,255,255,0.9);">{entry['name']}</div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:#818cf8;">{entry['wpm']} WPM</div>
                    <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);">{entry['acc']}%</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No scores yet. Play a typing test to add to the leaderboard!")
