"""youtube_handler.py — Fetch and format YouTube video transcripts."""

from __future__ import annotations
import re
from youtube_transcript_api import YouTubeTranscriptApi

MAX_CHARS = 12_000


def extract_video_id(url: str) -> str:
    """Parse a YouTube URL and return the video ID."""
    patterns = [
        r"(?:v=)([A-Za-z0-9_\-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_\-]{11})",
        r"(?:embed/)([A-Za-z0-9_\-]{11})",
        r"(?:shorts/)([A-Za-z0-9_\-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def get_youtube_transcript(url: str) -> tuple[list[dict], str]:
    """
    Fetch the transcript for a YouTube video.

    Returns:
        (transcript_list, video_id)

    Raises:
        ValueError on any failure.
    """
    video_id = extract_video_id(url)
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return transcript, video_id
    except Exception as e:
        raise ValueError(f"Could not fetch transcript for {video_id}: {e}")


def format_transcript_as_context(transcript: list[dict], video_id: str) -> str:
    """Join transcript segments into a single context string."""
    lines = [f"YouTube Video Transcript (ID: {video_id})\n"]
    for entry in transcript:
        lines.append(entry.get("text", ""))
    full = " ".join(lines)
    return full[:MAX_CHARS]
