"""story_addon.py — Step 31: AI character generator, plot twist engine, story exporter"""
import streamlit as st, random

GENRES = ["Fantasy","Sci-Fi","Mystery","Romance","Thriller","Horror","Historical","Adventure","Literary Fiction","Dystopian"]
ARCHETYPES = ["Hero","Mentor","Trickster","Shadow/Villain","Herald","Shapeshifter","Guardian","Ally"]
PLOT_TWISTS = [
    "The villain was secretly helping the hero all along.",
    "The protagonist is actually the antagonist's long-lost child.",
    "Everything that happened was a simulation/dream.",
    "The narrator has been unreliable — half the story is false.",
    "The hero discovers they have been the villain in someone else's story.",
    "The magical artifact has no power — the real power was belief.",
    "Two characters who hated each other are revealed to be the same person.",
    "The world was saved before the story even began — the quest was a lie.",
    "The mentor figure is the one who caused the original tragedy.",
    "Time loops back — the hero becomes the very villain from the beginning.",
]

def render_story_addon():
    sa1, sa2, sa3, sa4 = st.tabs(["👤 Character Creator","🌀 Plot Twist Engine","📖 Story Expander","📥 Story Exporter"])

    with sa1:
        st.markdown("**👤 AI Character Generator**")
        c1,c2 = st.columns(2)
        char_genre = c1.selectbox("Genre:", GENRES, key="st_char_genre")
        char_arch  = c2.selectbox("Archetype:", ARCHETYPES, key="st_char_arch")
        char_traits = st.text_input("Key traits (optional):", placeholder="e.g. brave, sarcastic, haunted by past", key="st_char_traits")
        char_name   = st.text_input("Name (leave blank for AI to choose):", key="st_char_name")
        if st.button("👤 Generate Character", type="primary", use_container_width=True, key="st_char_btn"):
            with st.spinner("Creating character..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Create a rich {char_genre} {char_arch} character{' named '+char_name if char_name else ''}. Traits: {char_traits or 'your choice'}. Include: full name, age, appearance (3 sentences), backstory (4 sentences), personality (5 traits with explanation), motivations, fatal flaw, unique skill, and a memorable quirk."
                    char = generate(p, max_tokens=1500, temperature=0.85)
                    st.markdown(f"""
                    <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(139,92,246,0.25);
                        border-radius:18px;padding:24px;font-size:0.9rem;color:rgba(255,255,255,0.8);line-height:1.85;">{char}</div>
                    """, unsafe_allow_html=True)
                    st.session_state["st_last_char"] = char
                    st.download_button("📥 Save Character", char, "character.txt", key="st_char_dl")
                except Exception as e: st.error(str(e))

    with sa2:
        st.markdown("**🌀 Plot Twist Engine**")
        st.markdown("*Stuck in your story? Generate an unexpected twist!*")
        twist_genre = st.selectbox("Genre:", GENRES, key="st_twist_genre")
        story_context = st.text_area("Describe your story so far:", height=80, key="st_twist_ctx", placeholder="Optional — leave blank for a random twist")
        col_a, col_b = st.columns(2)
        if col_a.button("🎲 Random Twist", key="st_random_twist", use_container_width=True, type="primary"):
            twist = random.choice(PLOT_TWISTS)
            st.markdown(f"""
            <div style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.3);
                border-radius:16px;padding:22px;font-size:1.05rem;font-weight:500;
                color:#ddd6fe;line-height:1.7;text-align:center;">🌀 {twist}</div>
            """, unsafe_allow_html=True)
        if col_b.button("🤖 AI Custom Twist", key="st_ai_twist", use_container_width=True):
            with st.spinner("Crafting twist..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Create 3 unique, unexpected plot twists for a {twist_genre} story. Context: {story_context or 'a general story'}. Make each twist surprising, logical in hindsight, and emotionally impactful."
                    twists = generate(p, max_tokens=800, temperature=0.9)
                    st.markdown(twists)
                except Exception as e: st.error(str(e))

    with sa3:
        st.markdown("**📖 AI Story Expander**")
        story_seed = st.text_area("Your story premise or partial story:", height=120, key="st_expand_seed", placeholder="e.g. A young wizard discovers she is the last of her bloodline and must recover a stolen artifact before the winter solstice...")
        expand_type = st.selectbox("Expand with:", ["Next chapter","Dialogue scene","Action sequence","Emotional scene","Backstory reveal","Climax scene","Epilogue"], key="st_expand_type")
        word_count = st.selectbox("Length:", ["~200 words","~500 words","~1000 words"], key="st_expand_len")
        if story_seed and st.button("✍️ Expand Story", type="primary", use_container_width=True, key="st_expand_btn"):
            with st.spinner("Writing..."):
                try:
                    from utils.ai_engine import generate
                    p = f"Continue this story with a {expand_type} of {word_count}. Maintain tone and style. Story: {story_seed[:2000]}"
                    result = generate(p, max_tokens=2000, temperature=0.85)
                    st.markdown(f"""
                    <div style="background:rgba(10,14,30,0.85);border:1px solid rgba(99,102,241,0.2);
                        border-radius:16px;padding:22px;font-size:0.92rem;color:rgba(255,255,255,0.8);
                        line-height:1.9;font-style:italic;">{result}</div>
                    """, unsafe_allow_html=True)
                    prev = st.session_state.get("st_full_story","")
                    st.session_state.st_full_story = prev + "\n\n" + result
                    st.download_button("📥 Save This Section", result, "story_section.txt", key="st_expand_dl")
                except Exception as e: st.error(str(e))

    with sa4:
        st.markdown("**📥 Export Full Story**")
        full_story = st.session_state.get("st_full_story","")
        manual = st.text_area("Or paste your complete story:", value=full_story, height=200, key="st_export_txt")
        title = st.text_input("Story Title:", value="My Story", key="st_title")
        author = st.text_input("Author Name:", key="st_author")

        c1, c2 = st.columns(2)
        if c1.button("📄 Export as TXT", key="st_exp_txt", use_container_width=True, type="primary"):
            content = f"{title}\nBy {author}\n{'='*40}\n\n{manual}"
            st.download_button("⬇️ Download TXT", content, f"{title}.txt", key="st_dl_txt2")
        if c2.button("📄 Export as Markdown", key="st_exp_md", use_container_width=True):
            content = f"# {title}\n**By {author}**\n\n---\n\n{manual}"
            st.download_button("⬇️ Download MD", content, f"{title}.md", "text/markdown", key="st_dl_md2")
