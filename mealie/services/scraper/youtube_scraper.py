import asyncio
import re
from typing import Any

import httpx

_TRANSCRIPT_TIMEOUT_SECONDS = 20
_MAX_TRANSCRIPT_CHARS = 12000
_MIN_TRANSCRIPT_CHARS = 100

_VIDEO_ID_RE = re.compile(r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})")


class YouTubeTranscriptError(Exception):
    """Raised when transcript extraction fails with a user-friendly message."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error


def _get_transcript_error_message(error: Exception) -> str:
    """Map transcript API exceptions to user-friendly messages."""
    error_type = type(error).__name__
    error_messages = {
        "TranscriptsDisabled": "This video has no captions available.",
        "VideoUnavailable": "This video is unavailable, private, or age-restricted.",
        "TooManyRequests": "Rate limited by YouTube. Please try again later.",
        "NoTranscriptFound": "No transcript found for this video.",
        "NotTranslatable": "Transcript translation is not available for this video.",
        "CookieInvalid": "Could not authenticate with YouTube cookies.",
        "FailedToCreateCookieFile": "Could not create cookie file for YouTube authentication.",
    }
    return error_messages.get(error_type, f"Could not retrieve transcript: {error_type}")


def extract_video_id(url: str) -> str | None:
    """Extract the 11-character video ID from any supported YouTube URL format."""
    match = _VIDEO_ID_RE.search(url)
    return match.group(1) if match else None


async def get_video_metadata(url: str) -> dict[str, Any]:
    """Fetch video title and thumbnail URL from the YouTube oEmbed API."""
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(oembed_url)
        response.raise_for_status()
        data = response.json()
        return {
            "title": data.get("title", ""),
            "thumbnail_url": data.get("thumbnail_url"),
        }


def _fetch_transcript_sync(video_id: str) -> str:
    """Synchronous transcript fetch — intended for use inside an executor.

    Tries manually-created transcripts first, then auto-generated ones,
    accepting any available language (not limited to English).

    Raises:
        YouTubeTranscriptError: If transcript extraction fails with a specific error.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore[import-untyped]
        from youtube_transcript_api._errors import (  # type: ignore[import-untyped]
            NoTranscriptFound,
            TooManyRequests,
            TranscriptsDisabled,
            VideoUnavailable,
        )

        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Prefer manually-created transcripts; fall back to auto-generated
        transcript = None
        for t in transcript_list:
            if not t.is_generated:
                transcript = t
                break
        if transcript is None:
            transcript = next(iter(transcript_list))

        fetched = transcript.fetch()
        return " ".join(snippet.text for snippet in fetched)
    except (TranscriptsDisabled, VideoUnavailable, TooManyRequests, NoTranscriptFound) as e:
        raise YouTubeTranscriptError(_get_transcript_error_message(e), e) from e
    except Exception as e:
        raise YouTubeTranscriptError(_get_transcript_error_message(e), e) from e


async def get_transcript(video_id: str) -> str:
    """Fetch and join all transcript segments for a YouTube video (async wrapper).

    Raises:
        YouTubeTranscriptError: If transcript fetch fails.
        TimeoutError: If transcript fetch times out.
    """
    loop = asyncio.get_running_loop()
    try:
        transcript = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch_transcript_sync, video_id),
            timeout=_TRANSCRIPT_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise YouTubeTranscriptError("Transcript fetch timed out. Please try again.") from None

    return transcript[:_MAX_TRANSCRIPT_CHARS]


async def get_video_context(url: str) -> tuple[str, str | None]:
    """Orchestrate metadata + transcript extraction for a YouTube URL.

    Returns:
        A tuple of (combined_text, thumbnail_url) where combined_text is
        "{title}\\n\\n{transcript}".

    Raises:
        ValueError: For invalid URLs.
        YouTubeTranscriptError: For transcript-related errors.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid YouTube URL. Please provide a valid YouTube video link.")

    metadata_task = asyncio.create_task(get_video_metadata(url))
    transcript_task = asyncio.create_task(get_transcript(video_id))

    try:
        metadata = await metadata_task
    except Exception:
        metadata = {}

    # Let YouTubeTranscriptError propagate with its user-friendly message
    transcript = await transcript_task

    if len(transcript) < _MIN_TRANSCRIPT_CHARS:
        raise ValueError(
            f"Video transcript is too short ({len(transcript)} characters) to extract a recipe. "
            "Please try a video with more content."
        )

    title = metadata.get("title", "")
    thumbnail_url = metadata.get("thumbnail_url")

    combined_text = f"{title}\n\n{transcript}" if title else transcript
    return combined_text, thumbnail_url
