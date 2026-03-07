"""YouTube video scraper for recipe extraction.

This module provides functionality to extract recipe content from YouTube videos
by fetching video metadata and subtitles/captions via youtube-transcript-api.
If no captions are available, it falls back to transcribing audio via OpenAI Whisper
or faster-whisper (local).
"""

import asyncio
import logging
import os
import re
import tempfile
from typing import Any

import httpx

from mealie.core.config import get_app_settings

logger = logging.getLogger(__name__)

_TRANSCRIPT_TIMEOUT_SECONDS = 20
_MAX_TRANSCRIPT_CHARS = 12000
_AUDIO_DOWNLOAD_TIMEOUT = 120
_WHISPER_TIMEOUT = 180

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


def _download_audio_sync(url: str) -> str | None:
    """Download audio from YouTube video using yt-dlp.

    Returns the path to the downloaded audio file, or None if download fails.
    """
    try:
        import yt_dlp  # type: ignore[import-untyped]

        # Create a temporary file for the audio
        temp_dir = tempfile.mkdtemp()
        output_template = f"{temp_dir}/audio.%(ext)s"

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "64",  # Lower quality is fine for transcription
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded audio file
        for file in os.listdir(temp_dir):
            if file.endswith((".mp3", ".m4a", ".webm", ".opus")):
                return os.path.join(temp_dir, file)

        return None

    except Exception as e:
        logger.warning(f"Failed to download audio from YouTube: {e}")
        return None


def _transcribe_audio_sync(audio_path: str) -> str | None:
    """Transcribe audio file using OpenAI Whisper API."""
    from openai import OpenAI

    try:
        settings = get_app_settings()

        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured, cannot transcribe audio")
            return None

        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )

        return transcript

    except Exception as e:
        logger.warning(f"Failed to transcribe audio with OpenAI Whisper: {e}")
        return None


def _transcribe_with_faster_whisper_sync(audio_path: str) -> str | None:
    """Transcribe audio file using faster-whisper (local).

    This runs locally on CPU/GPU without requiring an API key.
    Supports models: tiny, base, small, medium, large-v3
    For Romanian, 'medium' or 'large-v3' is recommended.
    """
    try:
        from faster_whisper import WhisperModel  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("faster-whisper is not installed. Install with: pip install mealie[whisper]")
        return None

    try:
        settings = get_app_settings()
        model_size = settings.WHISPER_MODEL

        logger.info(f"Loading faster-whisper model '{model_size}' for transcription...")

        # Use CPU with int8 quantization for broader compatibility
        compute_type = "int8"

        model = WhisperModel(model_size, device="cpu", compute_type=compute_type)

        # Transcribe with language detection and beam search for better accuracy
        segments, info = model.transcribe(audio_path, language=None, beam_size=5)

        # Log detected language for debugging
        logger.info(f"Detected language: {info.language} (probability: {info.language_probability:.2f})")

        # Combine all segments into a single transcript
        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text)

        transcript = " ".join(transcript_parts).strip()
        return transcript[:_MAX_TRANSCRIPT_CHARS] if transcript else None

    except Exception as e:
        logger.warning(f"Failed to transcribe audio with faster-whisper: {e}")
        return None


async def transcribe_audio_with_whisper(url: str) -> str | None:
    """Download audio from YouTube and transcribe using configured Whisper provider.

    This is used as a fallback when no captions are available.

    The provider is determined by WHISPER_PROVIDER setting:
    - "openai": Use OpenAI Whisper API (requires API key)
    - "faster-whisper": Use local faster-whisper (no API key needed)
    - "none": Disable transcription
    """
    settings = get_app_settings()
    provider = settings.WHISPER_PROVIDER.lower()

    if provider == "none":
        logger.info("Whisper transcription is disabled (WHISPER_PROVIDER=none)")
        return None

    loop = asyncio.get_running_loop()

    try:
        # Download audio
        logger.info("Downloading audio from YouTube for Whisper transcription...")
        audio_path = await asyncio.wait_for(
            loop.run_in_executor(None, _download_audio_sync, url),
            timeout=_AUDIO_DOWNLOAD_TIMEOUT,
        )

        if not audio_path:
            return None

        # Choose transcription provider
        if provider == "faster-whisper":
            logger.info("Using faster-whisper for local transcription")
            transcript = await asyncio.wait_for(
                loop.run_in_executor(None, _transcribe_with_faster_whisper_sync, audio_path),
                timeout=_WHISPER_TIMEOUT,
            )
        elif provider == "openai":
            logger.info("Using OpenAI Whisper API for transcription")
            transcript = await asyncio.wait_for(
                loop.run_in_executor(None, _transcribe_audio_sync, audio_path),
                timeout=_WHISPER_TIMEOUT,
            )
        else:
            logger.warning(f"Unknown WHISPER_PROVIDER: {provider}. Use 'openai', 'faster-whisper', or 'none'")
            transcript = None

        # Cleanup temporary file
        try:
            import shutil

            shutil.rmtree(os.path.dirname(audio_path), ignore_errors=True)
        except Exception:
            pass

        return transcript

    except TimeoutError:
        logger.warning("Timeout while transcribing YouTube audio")
        return None
    except Exception as e:
        logger.warning(f"Error in Whisper transcription: {e}")
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

    # If no captions found, try to transcribe audio with Whisper
    if not transcript:
        logger.info(f"No captions found for YouTube video {video_id}, trying Whisper transcription...")
        transcript = await transcribe_audio_with_whisper(url)

    if not transcript:
        raise ValueError("No transcript found for this video. Please try a video with captions enabled.")

    title = metadata.get("title", "")
    thumbnail_url = metadata.get("thumbnail_url")

    combined_text = f"{title}\n\n{transcript}" if title else transcript
    return combined_text, thumbnail_url
