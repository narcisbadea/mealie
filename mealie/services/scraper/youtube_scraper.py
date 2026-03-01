import asyncio
import re
from typing import Any

import httpx

_TRANSCRIPT_TIMEOUT_SECONDS = 20
_MAX_TRANSCRIPT_CHARS = 12000

_VIDEO_ID_RE = re.compile(r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})")


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


def _fetch_transcript_sync(video_id: str) -> str | None:
    """Synchronous transcript fetch — intended for use inside an executor.

    Tries manually-created transcripts first, then auto-generated ones,
    accepting any available language (not limited to English).
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore[import-untyped]

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
    except Exception:
        return None


async def get_transcript(video_id: str) -> str | None:
    """Fetch and join all transcript segments for a YouTube video (async wrapper)."""
    loop = asyncio.get_running_loop()
    try:
        transcript = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch_transcript_sync, video_id),
            timeout=_TRANSCRIPT_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        return None

    if not transcript:
        return None

    return transcript[:_MAX_TRANSCRIPT_CHARS]


async def get_video_context(url: str) -> tuple[str, str | None]:
    """Orchestrate metadata + transcript extraction for a YouTube URL.

    Returns:
        A tuple of (combined_text, thumbnail_url) where combined_text is
        "{title}\\n\\n{transcript}".

    Raises:
        ValueError: For invalid URLs or videos with no available transcript.
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

    transcript = await transcript_task

    if not transcript:
        raise ValueError("No transcript found for this video. Please try a video with captions enabled.")

    title = metadata.get("title", "")
    thumbnail_url = metadata.get("thumbnail_url")

    combined_text = f"{title}\n\n{transcript}" if title else transcript
    return combined_text, thumbnail_url
