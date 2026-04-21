"""
youtube_handler.py — YouTube Transcript + Video Finder for ExamHelp AI
Original: transcript fetching
NEW in v2.0:
  - find_best_youtube_videos(topic, yt_api_key, filters) → ranked videos
  - Categorizes: Beginner / Deep Dive / Quick
  - YouTube Data API v3 with scrape fallback (no key needed)
  - render_youtube_finder() — full Streamlit UI
"""
from __future__ import annotations
import re
import json
import urllib.parse
import requests
from typing import Optional, List, Dict

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _HAS_YT_API = True
except ImportError:
    YouTubeTranscriptApi = None
    _HAS_YT_API = False

MAX_CHARS = 30_000
TIMESTAMP_INTERVAL = 60


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL TRANSCRIPT FUNCTIONS (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str:
    """Parse a YouTube URL and return the video ID."""
    patterns = [
        r"(?:v=)([A-Za-z0-9_\-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_\-]{11})",
        r"(?:embed/)([A-Za-z0-9_\-]{11})",
        r"(?:shorts/)([A-Za-z0-9_\-]{11})",
        r"(?:live/)([A-Za-z0-9_\-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def get_youtube_transcript(url: str) -> tuple[list, str]:
    """
    Fetch transcript for a YouTube video.
    Returns (transcript_list, video_id). Raises ValueError on failure.
    """
    video_id = extract_video_id(url)
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        try:
            transcript = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
        except Exception:
            pass
        if not transcript:
            try:
                transcript = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
            except Exception:
                pass
        if not transcript:
            try:
                for t in transcript_list:
                    transcript = t
                    if t.is_translatable:
                        transcript = t.translate("en")
                    break
            except Exception:
                pass
        if transcript:
            return transcript.fetch(), video_id
        raise ValueError("No transcript found for this video.")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not fetch transcript for {video_id}: {e}")


def format_transcript_as_context(transcript: list, video_id: str) -> str:
    lines = [
        "YouTube Video Transcript",
        f"Video URL: https://www.youtube.com/watch?v={video_id}",
        f"Total segments: {len(transcript)}",
        "—" * 40, "",
    ]
    last_timestamp_mark = -TIMESTAMP_INTERVAL
    paragraph: list = []
    for entry in transcript:
        start = entry.get("start", 0)
        text = entry.get("text", "").strip()
        if not text:
            continue
        if start - last_timestamp_mark >= TIMESTAMP_INTERVAL:
            if paragraph:
                lines.append(" ".join(paragraph))
                paragraph = []
            lines.append(f"\n[{_fmt_time(start)}]")
            last_timestamp_mark = start
        paragraph.append(text)
    if paragraph:
        lines.append(" ".join(paragraph))
    return "\n".join(lines)[:MAX_CHARS]


def get_transcript_stats(transcript: list) -> dict:
    if not transcript:
        return {}
    duration = transcript[-1].get("start", 0) + transcript[-1].get("duration", 0)
    word_count = sum(len(e.get("text", "").split()) for e in transcript)
    return {
        "duration_minutes": round(duration / 60, 1),
        "segment_count": len(transcript),
        "word_count": word_count,
    }


# ─────────────────────────────────────────────────────────────────────────────
# NEW: VIDEO CATEGORIZATION
# ─────────────────────────────────────────────────────────────────────────────

def _categorize_video(title: str, duration_seconds: int = 0) -> str:
    """Categorize video as Beginner / Deep Dive / Quick based on title + duration."""
    t = title.lower()
    if any(kw in t for kw in ["intro", "introduc", "basics", "beginner", "start", "what is",
                               "explained", "for beginners", "101", "getting started", "learn"]):
        return "Beginner"
    if any(kw in t for kw in ["advanced", "complete", "full course", "masterclass",
                               "in depth", "deep dive", "comprehensive", "ultimate", "expert"]):
        return "Deep Dive"
    if duration_seconds > 0 and duration_seconds < 600:
        return "Quick"
    return "Beginner"


def _parse_duration_seconds(iso_duration: str) -> int:
    """Parse ISO 8601 duration (PT1H2M3S) to seconds."""
    try:
        h = int(re.search(r"(\d+)H", iso_duration).group(1)) if "H" in iso_duration else 0
        m = int(re.search(r"(\d+)M", iso_duration).group(1)) if "M" in iso_duration else 0
        s = int(re.search(r"(\d+)S", iso_duration).group(1)) if "S" in iso_duration else 0
        return h * 3600 + m * 60 + s
    except Exception:
        return 0


def _fmt_duration(seconds: int) -> str:
    if seconds <= 0:
        return "Unknown"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s}s"


# ─────────────────────────────────────────────────────────────────────────────
# NEW: VIDEO FINDER — with YouTube Data API v3 + scrape fallback
# ─────────────────────────────────────────────────────────────────────────────

def find_best_youtube_videos(
    topic: str,
    yt_api_key: Optional[str] = None,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Find the best YouTube videos for a topic.
    Returns list of video dicts sorted by relevance score.
    Uses YouTube Data API v3 if key provided, else scrape fallback.
    """
    if filters is None:
        filters = {}

    if yt_api_key:
        return _find_videos_with_api(topic, yt_api_key, filters)
    else:
        return _find_videos_scrape(topic, filters)


def _find_videos_with_api(topic: str, api_key: str, filters: dict) -> List[Dict]:
    """YouTube Data API v3 search + statistics."""
    videos = []
    try:
        duration_map = {
            "Short (<4 min)": "short",
            "Medium (4-20 min)": "medium",
            "Long (>20 min)": "long",
            "Any": "any",
        }
        duration_val = duration_map.get(filters.get("duration", "Any"), "any")

        search_params = {
            "part": "snippet",
            "q": f"{topic} tutorial learn",
            "type": "video",
            "order": "relevance",
            "maxResults": 15,
            "relevanceLanguage": filters.get("lang", "en"),
            "key": api_key,
        }
        if duration_val != "any":
            search_params["videoDuration"] = duration_val

        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params=search_params,
            timeout=8
        )
        if r.status_code != 200:
            return _find_videos_scrape(topic, filters)

        search_data = r.json()
        items = search_data.get("items", [])
        if not items:
            return _find_videos_scrape(topic, filters)

        video_ids = [it["id"]["videoId"] for it in items if "videoId" in it.get("id", {})]

        # Get statistics and duration via videos.list
        stats_r = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": api_key
            },
            timeout=8
        )
        stats_map = {}
        if stats_r.status_code == 200:
            for v in stats_r.json().get("items", []):
                stats_map[v["id"]] = {
                    "views": int(v.get("statistics", {}).get("viewCount", 0)),
                    "likes": int(v.get("statistics", {}).get("likeCount", 0)),
                    "duration_iso": v.get("contentDetails", {}).get("duration", ""),
                }

        for it in items:
            vid_id = it.get("id", {}).get("videoId", "")
            snippet = it.get("snippet", {})
            if not vid_id:
                continue

            stat = stats_map.get(vid_id, {})
            views = stat.get("views", 0)
            likes = stat.get("likes", 0)
            dur_secs = _parse_duration_seconds(stat.get("duration_iso", ""))

            import datetime
            pub_date = snippet.get("publishedAt", "")
            days_old = 9999
            if pub_date:
                try:
                    pub = datetime.datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    days_old = (datetime.datetime.now(datetime.timezone.utc) - pub).days
                except Exception:
                    pass
            recency_score = max(0, 100 - days_old / 30)

            score = (min(views, 10_000_000) / 10_000_000 * 40 +
                     min(likes, 500_000) / 500_000 * 30 +
                     recency_score * 0.30)

            title = snippet.get("title", "")
            videos.append({
                "title": title,
                "channel": snippet.get("channelTitle", ""),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
                "views": views,
                "duration": _fmt_duration(dur_secs),
                "duration_seconds": dur_secs,
                "category": _categorize_video(title, dur_secs),
                "relevance_score": round(score, 2),
                "published": pub_date[:10] if pub_date else "",
            })

        videos.sort(key=lambda x: x["relevance_score"], reverse=True)

    except Exception:
        return _find_videos_scrape(topic, filters)

    return videos[:12]


def _find_videos_scrape(topic: str, filters: dict) -> List[Dict]:
    """Scrape YouTube search page as fallback (no API key needed)."""
    videos = []
    try:
        query = urllib.parse.quote(f"{topic} tutorial")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(
            f"https://www.youtube.com/results?search_query={query}",
            headers=headers,
            timeout=10
        )
        if r.status_code != 200:
            return []

        # Extract ytInitialData JSON
        match = re.search(r"var ytInitialData\s*=\s*(\{.*?\});\s*</script>", r.text, re.DOTALL)
        if not match:
            # Try alternative pattern
            match = re.search(r"ytInitialData\s*=\s*(\{.+?\});\s*(?:var |window\[)", r.text, re.DOTALL)
        if not match:
            return _fallback_oembed(topic)

        try:
            data = json.loads(match.group(1))
        except Exception:
            # JSON too large or malformed — try to extract video IDs directly
            video_ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', r.text)
            titles = re.findall(r'"text":"([^"]{10,100})"', r.text)
            channels = re.findall(r'"ownerText":.*?"text":"([^"]+)"', r.text)
            seen = set()
            for i, vid_id in enumerate(video_ids[:12]):
                if vid_id in seen:
                    continue
                seen.add(vid_id)
                title = titles[i] if i < len(titles) else topic
                channel = channels[i // 2] if i // 2 < len(channels) else "Unknown"
                videos.append({
                    "title": title,
                    "channel": channel,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "thumbnail": f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg",
                    "views": 0,
                    "duration": "Unknown",
                    "duration_seconds": 0,
                    "category": _categorize_video(title),
                    "relevance_score": 50.0 - i,
                    "published": "",
                })
            return videos[:12]

        # Navigate JSON for video renderers
        try:
            contents = (data.get("contents", {})
                        .get("twoColumnSearchResultsRenderer", {})
                        .get("primaryContents", {})
                        .get("sectionListRenderer", {})
                        .get("contents", []))
        except Exception:
            return _fallback_oembed(topic)

        for section in contents:
            items = (section.get("itemSectionRenderer", {}).get("contents", []))
            for item in items:
                vr = item.get("videoRenderer", {})
                if not vr:
                    continue
                vid_id = vr.get("videoId", "")
                if not vid_id:
                    continue
                title_runs = vr.get("title", {}).get("runs", [])
                title = " ".join(r.get("text", "") for r in title_runs)
                channel_runs = (vr.get("ownerText", {}).get("runs", []) or
                                vr.get("longBylineText", {}).get("runs", []))
                channel = " ".join(r.get("text", "") for r in channel_runs)
                thumbnail = (vr.get("thumbnail", {}).get("thumbnails", [{}])[-1].get("url", "")
                             or f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg")
                view_text = (vr.get("viewCountText", {}).get("simpleText", "") or
                             vr.get("viewCountText", {}).get("runs", [{}])[0].get("text", ""))
                views = _parse_view_count(view_text)
                dur_text = vr.get("lengthText", {}).get("simpleText", "")
                dur_secs = _parse_dur_text(dur_text)

                videos.append({
                    "title": title,
                    "channel": channel,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "thumbnail": thumbnail,
                    "views": views,
                    "duration": dur_text or "Unknown",
                    "duration_seconds": dur_secs,
                    "category": _categorize_video(title, dur_secs),
                    "relevance_score": float(50 - len(videos)),
                    "published": "",
                })
                if len(videos) >= 12:
                    break
            if len(videos) >= 12:
                break

    except Exception:
        return _fallback_oembed(topic)

    return videos


def _fallback_oembed(topic: str) -> List[Dict]:
    """Absolute fallback — return blank search link list."""
    query = urllib.parse.quote(topic)
    return [{
        "title": f"Search YouTube for: {topic}",
        "channel": "YouTube Search",
        "url": f"https://www.youtube.com/results?search_query={query}+tutorial",
        "thumbnail": "",
        "views": 0,
        "duration": "Unknown",
        "duration_seconds": 0,
        "category": "Beginner",
        "relevance_score": 0.0,
        "published": "",
    }]


def _parse_view_count(text: str) -> int:
    try:
        text = text.lower().replace(",", "").replace(" views", "").strip()
        if "k" in text:
            return int(float(text.replace("k", "")) * 1000)
        if "m" in text:
            return int(float(text.replace("m", "")) * 1_000_000)
        if "b" in text:
            return int(float(text.replace("b", "")) * 1_000_000_000)
        return int(text)
    except Exception:
        return 0


def _parse_dur_text(text: str) -> int:
    """Parse MM:SS or H:MM:SS to seconds."""
    try:
        parts = text.strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    except Exception:
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────────────────────────────────────────

def render_youtube_finder():
    """Full Streamlit YouTube Video Finder page."""
    import streamlit as st

    st.markdown("""
<div style="background:linear-gradient(135deg,rgba(239,68,68,0.08),rgba(239,68,68,0.03));
border:1px solid rgba(239,68,68,0.2);border-radius:20px;padding:28px 32px;margin-bottom:24px;">
  <div style="font-family:monospace;font-size:10px;letter-spacing:4px;
  color:rgba(239,68,68,0.6);text-transform:uppercase;margin-bottom:8px;">AI VIDEO DISCOVERY</div>
  <div style="font-size:1.8rem;font-weight:900;color:#fff;margin-bottom:6px;">📺 YouTube Video Finder</div>
  <div style="color:rgba(255,255,255,0.45);font-size:.9rem;">
    Find the best videos to learn any topic · Ranked by views & relevance · No API key needed (optional for better results)
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Inputs ─────────────────────────────────────────────────────────────
    col_topic, col_dur = st.columns([3, 1])
    with col_topic:
        topic = st.text_input(
            "🔍 What do you want to learn?",
            placeholder="e.g. Machine Learning, React.js, Organic Chemistry, Piano chords...",
            key="yt_topic"
        )
    with col_dur:
        duration_filter = st.selectbox(
            "Duration",
            ["Any", "Short (<4 min)", "Medium (4-20 min)", "Long (>20 min)"],
            key="yt_duration"
        )

    with st.expander("🔑 Optional: YouTube API Key (for more accurate results)"):
        yt_key = st.text_input(
            "YouTube Data API v3 Key",
            type="password",
            placeholder="AIza...",
            key="yt_api_key_input",
            help="Get free key from console.cloud.google.com → YouTube Data API v3"
        )
        st.caption("Without a key, we scrape YouTube directly (still works, may be slower).")

    search_btn = st.button("🎬 Find Best Videos", type="primary", use_container_width=True, key="yt_search")

    if search_btn and topic.strip():
        with st.spinner(f"Searching YouTube for '{topic}'..."):
            api_key = yt_key.strip() if yt_key.strip() else None
            filters = {"duration": duration_filter, "lang": "en"}
            videos = find_best_youtube_videos(topic.strip(), api_key, filters)

        if not videos:
            st.warning("No videos found. Try a different topic.")
            return

        st.success(f"Found **{len(videos)}** videos ranked by relevance!")

        # Categorize
        beginners  = [v for v in videos if v["category"] == "Beginner"]
        deep_dives = [v for v in videos if v["category"] == "Deep Dive"]
        quicks     = [v for v in videos if v["category"] == "Quick"]
        others     = [v for v in videos if v["category"] not in ("Beginner", "Deep Dive", "Quick")]
        all_vids   = beginners + quicks + deep_dives + others

        tab_all, tab_beg, tab_deep, tab_quick = st.tabs([
            f"🎬 All ({len(videos)})",
            f"🟢 Beginner ({len(beginners)})",
            f"🔵 Deep Dive ({len(deep_dives)})",
            f"⚡ Quick ({len(quicks)})",
        ])

        def _render_video_grid(vids):
            if not vids:
                st.info("No videos in this category.")
                return
            cols = st.columns(3)
            for i, v in enumerate(vids):
                with cols[i % 3]:
                    cat_colors = {"Beginner": "#22c55e", "Deep Dive": "#3b82f6", "Quick": "#f59e0b"}
                    cat_color = cat_colors.get(v["category"], "#6b7280")
                    if v.get("thumbnail"):
                        st.image(v["thumbnail"], use_column_width=True)
                    views_str = f"{v['views']:,}" if v["views"] > 0 else "N/A"
                    st.markdown(f"""
<div style="background:rgba(15,23,42,0.7);border:1px solid rgba(255,255,255,0.08);
border-radius:12px;padding:12px;margin-bottom:12px;">
  <div style="font-weight:700;font-size:.88rem;color:#f8fafc;line-height:1.4;margin-bottom:6px;">
    {v['title'][:70]}{'...' if len(v['title']) > 70 else ''}
  </div>
  <div style="font-size:.75rem;color:#94a3b8;margin-bottom:6px;">📺 {v['channel']}</div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
    <span style="background:{cat_color}22;color:{cat_color};border-radius:100px;
    padding:2px 10px;font-size:.7rem;font-weight:700;">{v['category']}</span>
    <span style="color:#94a3b8;font-size:.72rem;">⏱ {v['duration']}</span>
    <span style="color:#94a3b8;font-size:.72rem;">👁 {views_str} views</span>
  </div>
  <a href="{v['url']}" target="_blank" style="display:block;text-align:center;
  background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff;border-radius:8px;
  padding:7px;font-size:.8rem;font-weight:700;text-decoration:none;">▶ Watch Now</a>
</div>
""", unsafe_allow_html=True)

        with tab_all:
            _render_video_grid(all_vids)
        with tab_beg:
            _render_video_grid(beginners)
        with tab_deep:
            _render_video_grid(deep_dives)
        with tab_quick:
            _render_video_grid(quicks)

        # Related resources search links
        query_enc = urllib.parse.quote(topic)
        st.markdown("---")
        st.markdown("#### 📚 Also Explore")
        rel_cols = st.columns(3)
        with rel_cols[0]:
            st.markdown(f"[🔗 Search Full Courses](https://www.youtube.com/results?search_query={query_enc}+full+course)")
        with rel_cols[1]:
            st.markdown(f"[🔗 Search Playlists](https://www.youtube.com/results?search_query={query_enc}+playlist&sp=EgIQAw%3D%3D)")
        with rel_cols[2]:
            st.markdown(f"[🔗 Search Roadmaps](https://www.youtube.com/results?search_query={query_enc}+roadmap)")

    elif search_btn and not topic.strip():
        st.warning("Please enter a topic to search.")

    st.markdown("---")
    if st.button("💬 Back to Chat", use_container_width=True, key="yt_back"):
        st.session_state.app_mode = "chat"
        st.rerun()