"""
yt_search.py - Server-side YouTube search using yt-dlp
No API key required. Called from youtube_player_addon.py
"""
def search_youtube(query: str, max_results: int = 20) -> list:
    """Search YouTube using yt-dlp. Returns list of video dicts."""
    try:
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(
                f"ytsearch{max_results}:{query}", download=False
            )
        entries = data.get("entries", []) if data else []
        results = []
        for e in entries:
            if not e:
                continue
            vid_id = e.get("id") or e.get("url", "")
            if not vid_id:
                continue
            results.append({
                "id": vid_id,
                "title": e.get("title", "Untitled"),
                "channel": e.get("uploader") or e.get("channel", ""),
                "duration": _fmt_dur(e.get("duration")),
                "views": e.get("view_count", 0),
                "thumb": f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })
        return results
    except Exception as ex:
        return []


def _fmt_dur(secs):
    if not secs:
        return ""
    try:
        s = int(secs)
        h, rem = divmod(s, 3600)
        m, sc = divmod(rem, 60)
        if h:
            return f"{h}:{m:02d}:{sc:02d}"
        return f"{m}:{sc:02d}"
    except Exception:
        return ""
