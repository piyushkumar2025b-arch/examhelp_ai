"""
youtube_player_addon.py — Coming Soon placeholder
"""
import streamlit as st


def render_youtube_player():
    st.markdown("""
<style>
.yt-soon{background:linear-gradient(135deg,#09090f,#111128);
  border:1px solid rgba(124,110,247,.25);border-radius:20px;
  padding:60px 40px;text-align:center;margin:20px 0}
.yt-icon{font-size:72px;margin-bottom:16px}
.yt-title{font-size:26px;font-weight:800;
  background:linear-gradient(90deg,#7c6ef7,#f76e6e);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:8px}
.yt-sub{color:#6a6a8a;font-size:14px;margin-bottom:20px}
.yt-badge{display:inline-block;padding:6px 20px;border-radius:100px;
  background:rgba(124,110,247,.12);border:1px solid rgba(124,110,247,.3);
  color:#a5a0ff;font-size:12px;letter-spacing:2px}
</style>
<div class="yt-soon">
  <div class="yt-icon">🎵</div>
  <div class="yt-title">YouTube Music Player</div>
  <div class="yt-sub">This feature is currently being built and will be available soon.<br>
  Search, stream and queue songs directly from YouTube — inside the app.</div>
  <div class="yt-badge">🔨 &nbsp; COMING SOON</div>
</div>
""", unsafe_allow_html=True)

    st.info("💡 **What's coming:** Search any song → stream live from YouTube → queue & history system → categories like Lo-Fi, Pop, Bollywood, EDM and more.", icon="🎧")
