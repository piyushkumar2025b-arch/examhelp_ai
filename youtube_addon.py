"""youtube_addon.py — Step 29: YouTube transcript extractor + AI summarizer + playlist analyzer"""
import streamlit as st, re, urllib.request, json

def _extract_video_id(url: str) -> str:
    patterns = [r"v=([a-zA-Z0-9_-]{11})", r"youtu\.be/([a-zA-Z0-9_-]{11})", r"embed/([a-zA-Z0-9_-]{11})"]
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return ""

def _get_video_info(vid_id: str) -> dict:
    """Fetch basic video info from YouTube oEmbed (no API key)."""
    try:
        url = f"https://www.youtube.com/oembed?url=https://youtu.be/{vid_id}&format=json"
        req = urllib.request.Request(url, headers={"User-Agent":"ExamHelp/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {}

def _get_transcript(vid_id: str) -> str:
    """Try youtube-transcript-api if installed."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.get_transcript(vid_id)
        return " ".join(t["text"] for t in transcript)
    except Exception:
        return ""

def render_youtube_addon():
    ya1, ya2, ya3 = st.tabs(["📝 Transcript & Summary", "📋 Playlist Analyzer", "🎯 Study from Video"])

    with ya1:
        st.markdown("**📝 YouTube Transcript Extractor & AI Summarizer**")
        yt_url = st.text_input("YouTube URL:", placeholder="https://youtube.com/watch?v=...", key="ya_url")
        if yt_url:
            vid_id = _extract_video_id(yt_url)
            if vid_id:
                info = _get_video_info(vid_id)
                if info.get("title"):
                    st.markdown(f"**📺 {info['title']}** — {info.get('author_name','')}")
                st.markdown(f'<iframe width="100%" height="200" src="https://www.youtube.com/embed/{vid_id}" frameborder="0" allowfullscreen style="border-radius:12px;"></iframe>', unsafe_allow_html=True)

                action = st.selectbox("Action:", ["AI Summary (paste transcript)","Generate Study Notes","Create Quiz from Video","Extract Key Points","Generate Flashcards"], key="ya_action")
                transcript_text = st.text_area("Paste video transcript (or describe video content):", height=150, key="ya_transcript", placeholder="Paste the video transcript here, or describe what the video covers...")

                if transcript_text and st.button("🤖 Process with AI", type="primary", use_container_width=True, key="ya_process"):
                    prompts = {
                        "AI Summary (paste transcript)": f"Summarize this video transcript in 5-7 bullet points with key takeaways:\n\n{transcript_text[:4000]}",
                        "Generate Study Notes": f"Convert this video transcript into structured study notes with headings, bullet points, and key definitions:\n\n{transcript_text[:4000]}",
                        "Create Quiz from Video": f"Create 10 multiple choice questions based on this video content:\n\n{transcript_text[:4000]}",
                        "Extract Key Points": f"Extract the 10 most important points from this video transcript:\n\n{transcript_text[:4000]}",
                        "Generate Flashcards": f"Create 15 study flashcards (Q&A format) from this video content:\n\n{transcript_text[:4000]}",
                    }
                    with st.spinner("Processing..."):
                        try:
                            from utils.ai_engine import generate
                            result = generate(prompts[action], max_tokens=2500)
                            st.markdown(result)
                            st.download_button("📥 Save", result, "video_notes.txt", key="ya_dl")
                        except Exception as e: st.error(str(e))

                # Auto-transcript attempt
                if vid_id and st.button("⬇️ Try Auto-Extract Transcript", key="ya_auto_transcript", use_container_width=True):
                    with st.spinner("Attempting extraction..."):
                        tr = _get_transcript(vid_id)
                        if tr:
                            st.session_state.ya_got_transcript = tr
                            st.success(f"✅ Got transcript ({len(tr.split())} words)")
                            st.text_area("Transcript:", tr[:3000], height=200, key="ya_tr_preview")
                        else:
                            st.warning("⚠️ Auto-extract failed. Install: pip install youtube-transcript-api, or paste transcript manually.")
            else:
                st.error("❌ Invalid YouTube URL")

    with ya2:
        st.markdown("**📋 Playlist / Channel Analyzer**")
        pl_desc = st.text_area("Describe the playlist or paste video titles:", height=100, key="ya_playlist", placeholder="e.g. MIT 6.006 Introduction to Algorithms - 20 lecture videos covering sorting, graphs, dynamic programming...")
        if pl_desc and st.button("📋 Analyze Playlist", type="primary", use_container_width=True, key="ya_pl_btn"):
            with st.spinner("Analyzing..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Analyze this educational playlist: {pl_desc}. Provide: 1) Topic overview, 2) Recommended watching order, 3) Prerequisites, 4) Key concepts covered, 5) Estimated study time, 6) How to use this playlist effectively.")
                    st.markdown(ans)
                except Exception as e: st.error(str(e))

    with ya3:
        st.markdown("**🎯 AI-Powered Video Study Plan**")
        topic = st.text_input("What do you want to learn from YouTube?", placeholder="e.g. Machine Learning for beginners", key="ya_study_topic")
        hours = st.number_input("Hours per week available:", min_value=1, max_value=40, value=5, key="ya_hours")
        level = st.selectbox("Your level:", ["Beginner","Intermediate","Advanced"], key="ya_level")
        if topic and st.button("🎯 Find Best Videos + Study Plan", type="primary", use_container_width=True, key="ya_study_btn"):
            with st.spinner("Building your video study plan..."):
                try:
                    from utils.ai_engine import generate
                    ans = generate(f"Create a YouTube-based study plan for '{topic}' at {level} level with {hours} hours/week. Recommend: specific YouTube channels, playlists, video types to watch, weekly schedule, and how to take notes from videos effectively.")
                    st.markdown(ans)
                except Exception as e: st.error(str(e))
