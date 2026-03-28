"""youtube_handler.py — Fetch and format YouTube video transcripts."""

from __future__ import annotations
import re
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _HAS_YT_API = True
except ImportError:
    YouTubeTranscriptApi = None
    _HAS_YT_API = False

MAX_CHARS = 30_000   # increased to allow longer videos
TIMESTAMP_INTERVAL = 60  # add a timestamp marker every N seconds


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
    """Convert seconds to MM:SS or H:MM:SS string."""
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def get_youtube_transcript(url: str) -> tuple[list[dict], str]:
    """
    Fetch the transcript for a YouTube video.
    Tries English first, then auto-generated, then any available language.

    Returns:
        (transcript_list, video_id)

    Raises:
        ValueError on any failure.
    """
    video_id = extract_video_id(url)
    try:
        # Try to get the best available transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Priority: manual English > auto English > any manual > any auto
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
            # Fall back to first available language and translate to English
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
        else:
            raise ValueError("No transcript found for this video.")

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not fetch transcript for {video_id}: {e}")


def format_transcript_as_context(transcript: list[dict], video_id: str) -> str:
    """
    Format transcript segments with timestamps into a readable context block.
    Groups nearby segments and adds timestamp markers every TIMESTAMP_INTERVAL seconds.
    """
    lines = [
        f"YouTube Video Transcript",
        f"Video URL: https://www.youtube.com/watch?v={video_id}",
        f"Total segments: {len(transcript)}",
        "—" * 40,
        "",
    ]

    last_timestamp_mark = -TIMESTAMP_INTERVAL
    paragraph: list[str] = []

    for entry in transcript:
        start = entry.get("start", 0)
        text = entry.get("text", "").strip()

        if not text:
            continue

        # Add a timestamp marker periodically
        if start - last_timestamp_mark >= TIMESTAMP_INTERVAL:
            if paragraph:
                lines.append(" ".join(paragraph))
                paragraph = []
            lines.append(f"\n[{_fmt_time(start)}]")
            last_timestamp_mark = start

        paragraph.append(text)

    # Flush remaining
    if paragraph:
        lines.append(" ".join(paragraph))

    full = "\n".join(lines)
    return full[:MAX_CHARS]


def get_transcript_stats(transcript: list[dict]) -> dict:
    """Return stats about a transcript for UI display."""
    if not transcript:
        return {}
    duration = transcript[-1].get("start", 0) + transcript[-1].get("duration", 0)
    word_count = sum(len(e.get("text", "").split()) for e in transcript)
    return {
        "duration_minutes": round(duration / 60, 1),
        "segment_count": len(transcript),
        "word_count": word_count,
    }