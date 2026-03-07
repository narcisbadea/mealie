"""TikTok video scraper for recipe extraction.

This module provides functionality to extract recipe content from TikTok videos
by fetching video metadata and subtitles/captions via yt-dlp.
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

_TRANSCRIPT_TIMEOUT_SECONDS = 30
_MAX_TRANSCRIPT_CHARS = 12000
_AUDIO_DOWNLOAD_TIMEOUT = 60
_WHISPER_TIMEOUT = 120

# TikTok URL patterns:
# - https://www.tiktok.com/@username/video/1234567890123456789
# - https://vm.tiktok.com/ZMxxxxxxx/ (short URL)
# - https://m.tiktok.com/t/xxxxxxx (mobile short URL)
_VIDEO_ID_RE = re.compile(
    r"(?:tiktok\.com/(?:@[\w.-]+/video/|t/)|vm\.tiktok\.com/|m\.tiktok\.com/t/)([0-9]+|[A-Za-z0-9]+)"
)


def extract_video_id(url: str) -> str | None:
    """Extract the video ID from a TikTok URL.

    Supports:
    - Standard URLs: tiktok.com/@user/video/1234567890
    - Short URLs: vm.tiktok.com/xxxxx
    - Mobile URLs: m.tiktok.com/t/xxxxx
    """
    match = _VIDEO_ID_RE.search(url)
    return match.group(1) if match else None


async def get_video_metadata(url: str) -> dict[str, Any]:
    """Fetch video title and thumbnail URL from the TikTok oEmbed API."""
    oembed_url = f"https://www.tiktok.com/oembed?url={url}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(oembed_url)
        response.raise_for_status()
        data = response.json()
        return {
            "title": data.get("title", ""),
            "thumbnail_url": data.get("thumbnail_url"),
            "author_name": data.get("author_name", ""),
        }


def _fetch_subtitles_sync(url: str) -> str | None:
    """Synchronous subtitle fetch using yt-dlp.

    yt-dlp can extract subtitles from TikTok videos if they are available.
    This runs in an executor to avoid blocking the event loop.
    """
    try:
        import yt_dlp  # type: ignore[import-untyped]

        ydl_opts = {
            "skip_download": True,  # Don't download the video
            "writesubtitles": True,  # Try to get subtitles
            "writeautomaticsub": True,  # Try to get auto-generated subtitles
            "subtitleslangs": ["en", "all"],  # Prefer English, but accept any
            "quiet": True,
            "no_warnings": True,
            "outtmpl": "-",  # Don't write files, just extract info
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                return None

            # Try to get subtitles from the info
            subtitles = info.get("subtitles", {}) or info.get("automatic_captions", {})

            # Prefer English subtitles
            for lang in ["en", "en-US", "en-GB"]:
                if lang in subtitles and subtitles[lang]:
                    # Get the first subtitle track
                    sub_list = subtitles[lang]
                    if sub_list:
                        # Fetch the subtitle content
                        sub_url = sub_list[0].get("url")
                        if sub_url:
                            import urllib.request

                            with urllib.request.urlopen(sub_url, timeout=10) as response:
                                content = response.read().decode("utf-8")
                                return _parse_subtitle_content(content)

            # If no preferred language, try any available
            for _, subs in subtitles.items():
                if subs:
                    sub_url = subs[0].get("url")
                    if sub_url:
                        import urllib.request

                        with urllib.request.urlopen(sub_url, timeout=10) as response:
                            content = response.read().decode("utf-8")
                            return _parse_subtitle_content(content)

            return None

    except Exception:
        return None


def _parse_subtitle_content(content: str) -> str:
    """Parse subtitle content (SRT, VTT, or JSON format) and extract text."""
    # Try JSON format first (TikTok sometimes uses this)
    stripped = content.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            import json

            data = json.loads(content)
            if isinstance(data, list):
                return " ".join(item.get("text", "") for item in data if isinstance(item, dict))
            elif isinstance(data, dict) and "subtitles" in data:
                return " ".join(item.get("text", "") for item in data["subtitles"] if isinstance(item, dict))
        except json.JSONDecodeError:
            pass

    # Parse SRT/VTT format - extract text lines
    lines = content.strip().split("\n")
    text_lines = []
    for line in lines:
        line = line.strip()
        # Skip timestamp lines, sequence numbers, and WEBVTT headers
        if (
            not line
            or line.isdigit()
            or "-->" in line
            or line.startswith("WEBVTT")
            or line.startswith("NOTE")
            or line.startswith("STYLE")
            or re.match(r"<\d{2}:\d{2}:\d{2}", line)
        ):
            continue
        # Clean up any HTML-like tags
        line = re.sub(r"<[^>]+>", "", line)
        if line:
            text_lines.append(line)

    return " ".join(text_lines)


def _download_audio_sync(url: str) -> str | None:
    """Download audio from TikTok video using yt-dlp.

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
        import os

        for file in os.listdir(temp_dir):
            if file.endswith((".mp3", ".m4a", ".webm", ".opus")):
                return os.path.join(temp_dir, file)

        return None

    except Exception as e:
        logger.warning(f"Failed to download audio from TikTok: {e}")
        return None


def _transcribe_audio_sync(audio_path: str) -> str | None:
    """Transcribe audio file using OpenAI Whisper API."""
    from openai import OpenAI

    try:
        settings = get_app_settings()

        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured, cannot transcribe audio")
            return None

        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
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
        # For large-v3 model, use float16 if available, otherwise int8
        compute_type = "int8"
        if model_size.startswith("large"):
            # Large models benefit from float16 but require more RAM
            # int8 works but may be slightly less accurate
            compute_type = "int8"

        model = WhisperModel(model_size, device="cpu", compute_type=compute_type)

        # Transcribe with language detection
        # For better Romanian results, we let it auto-detect
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
    """Download audio from TikTok and transcribe using configured Whisper provider.

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
        logger.warning("Timeout while transcribing TikTok audio")
        return None
    except Exception as e:
        logger.warning(f"Error in Whisper transcription: {e}")
        return None


async def get_transcript(url: str) -> str | None:
    """Fetch and join all transcript segments for a TikTok video (async wrapper)."""
    loop = asyncio.get_running_loop()
    try:
        transcript = await asyncio.wait_for(
            loop.run_in_executor(None, _fetch_subtitles_sync, url),
            timeout=_TRANSCRIPT_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        return None

    if not transcript:
        return None

    return transcript[:_MAX_TRANSCRIPT_CHARS]


async def get_video_context(url: str) -> tuple[str, str | None]:
    """Orchestrate metadata + transcript extraction for a TikTok URL.

    Returns:
        A tuple of (combined_text, thumbnail_url) where combined_text is
        "{title}\\n\\n{transcript}".

    Raises:
        ValueError: For invalid URLs or videos with no available transcript.
    """
    # Normalize URL - ensure it has a scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid TikTok URL. Please provide a valid TikTok video link.")

    # For short URLs, we need to resolve them first to get the canonical URL
    # yt-dlp handles this automatically in _fetch_subtitles_sync

    metadata_task = asyncio.create_task(get_video_metadata(url))
    transcript_task = asyncio.create_task(get_transcript(url))

    try:
        metadata = await metadata_task
    except Exception:
        metadata = {}

    transcript = await transcript_task

    # If no captions found, try to transcribe audio with Whisper
    if not transcript:
        logger.info(f"No captions found for TikTok video {video_id}, trying Whisper transcription...")
        transcript = await transcribe_audio_with_whisper(url)

    if not transcript:
        raise ValueError("No captions found for this TikTok video. Please try a video with captions enabled.")

    title = metadata.get("title", "")
    thumbnail_url = metadata.get("thumbnail_url")

    combined_text = f"{title}\n\n{transcript}" if title else transcript
    return combined_text, thumbnail_url
