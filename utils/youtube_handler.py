import re
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound


def extract_video_id(url: str) -> str | None:
    """
    Extract YouTube video ID from various URL formats.
    Supports: youtube.com/watch?v=, youtu.be/, youtube.com/embed/
    """
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_youtube_transcript(url: str) -> tuple[str, str]:
    """
    Fetch transcript from a YouTube video URL.
    Returns (transcript_text, video_id) or raises an exception with a helpful message.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Could not extract a valid YouTube video ID from this URL.")

    try:
        # Try to get English transcript first, then any available
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        except NoTranscriptFound:
            # Try auto-generated or any other language
            transcript_data = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_data.find_generated_transcript(["en", "en-US", "en-GB"])
            transcript_list = transcript.fetch()

        # Combine all transcript chunks into clean text
        full_text = " ".join(
            chunk["text"].strip()
            for chunk in transcript_list
            if chunk.get("text", "").strip()
        )

        if not full_text:
            raise ValueError("Transcript is empty.")

        return full_text, video_id

    except TranscriptsDisabled:
        raise ValueError("Transcripts are disabled for this video by the creator.")
    except NoTranscriptFound:
        raise ValueError("No transcript found for this video. It may not have captions.")
    except Exception as e:
        raise ValueError(f"Could not fetch transcript: {str(e)}")


def format_transcript_as_context(transcript: str, video_id: str) -> str:
    """
    Format the transcript with metadata for injection into the AI context.
    """
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    return f"YouTube Video Transcript\nSource: {video_url}\n\n{transcript}"
