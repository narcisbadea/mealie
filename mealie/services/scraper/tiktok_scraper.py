import asyncio
import json
import re
from collections.abc import Iterable
from typing import Any

import httpx
from bs4 import BeautifulSoup

_TIKTOK_URL_RE = re.compile(r"^https?://(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com|vt\.tiktok\.com)/", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_JSON_IDS = {"__UNIVERSAL_DATA_FOR_REHYDRATION__", "__NEXT_DATA__", "SIGI_STATE"}
_TIMESTAMP_LINE_RE = re.compile(r"^\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3}\s+-->\s+\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3}$")


def _normalize_text(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip()


def _looks_like_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _is_tiktok_url(url: str) -> bool:
    return bool(_TIKTOK_URL_RE.match(url.strip()))


def _safe_json_loads(text: str) -> Any | None:
    try:
        return json.loads(text)
    except Exception:
        return None


def _collect_text_candidates(payload: Any, path: tuple[str, ...] = ()) -> list[str]:
    values: list[str] = []
    text_keys = {"desc", "description", "text", "title", "sharetitle", "sharedesc", "caption"}

    if isinstance(payload, dict):
        for raw_key, value in payload.items():
            key = str(raw_key).lower()
            key_path = (*path, key)

            if isinstance(value, str):
                normalized = _normalize_text(value)
                if normalized and not _looks_like_url(normalized):
                    if key in text_keys or "subtitle" in key or "caption" in key:
                        values.append(normalized)
            else:
                values.extend(_collect_text_candidates(value, key_path))

    elif isinstance(payload, list):
        for item in payload:
            values.extend(_collect_text_candidates(item, path))

    return values


def _collect_subtitle_urls(payload: Any, path: tuple[str, ...] = ()) -> list[str]:
    urls: list[str] = []

    if isinstance(payload, dict):
        for raw_key, value in payload.items():
            key = str(raw_key).lower()
            key_path = (*path, key)
            path_text = "/".join(key_path)

            if isinstance(value, str) and _looks_like_url(value):
                if "subtitle" in path_text or "caption" in path_text:
                    urls.append(value)
            else:
                urls.extend(_collect_subtitle_urls(value, key_path))

    elif isinstance(payload, list):
        for item in payload:
            urls.extend(_collect_subtitle_urls(item, path))

    return urls


def _dedupe_keep_order(values: Iterable[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()

    for value in values:
        normalized = _normalize_text(value)
        if not normalized:
            continue
        if normalized in seen:
            continue
        deduped.append(normalized)
        seen.add(normalized)

    return deduped


def _limit_text_candidates(values: list[str], max_items: int = 20, max_chars: int = 5000) -> list[str]:
    limited: list[str] = []
    char_count = 0

    for value in values:
        snippet = value[:800]
        if len(snippet) < 10:
            continue
        if char_count + len(snippet) > max_chars:
            break
        limited.append(snippet)
        char_count += len(snippet)
        if len(limited) >= max_items:
            break

    return limited


def _extract_json_from_html(soup: BeautifulSoup) -> list[Any]:
    payloads: list[Any] = []
    for script in soup.find_all("script"):
        script_id = (script.get("id") or "").strip()
        script_type = (script.get("type") or "").strip().lower()
        script_body = (script.string or script.get_text() or "").strip()

        if not script_body:
            continue

        if script_id in _SCRIPT_JSON_IDS or script_type == "application/json":
            parsed = _safe_json_loads(script_body)
            if parsed is not None:
                payloads.append(parsed)

    return payloads


def _extract_meta_content(soup: BeautifulSoup, attr_name: str, attr_value: str) -> str | None:
    tag = soup.find("meta", attrs={attr_name: attr_value})
    content = tag.get("content") if tag else None
    if not isinstance(content, str):
        return None
    content = _normalize_text(content)
    return content or None


def _parse_subtitle_payload(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None

    # Try JSON subtitles first.
    payload = _safe_json_loads(raw)
    if payload is not None:
        candidates = _collect_text_candidates(payload)
        return " ".join(_dedupe_keep_order(candidates)) if candidates else None

    lines: list[str] = []
    for line in raw.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if candidate == "WEBVTT":
            continue
        if candidate.isdigit():
            continue
        if _TIMESTAMP_LINE_RE.match(candidate):
            continue

        candidate = _HTML_TAG_RE.sub("", candidate)
        candidate = _normalize_text(candidate)
        if candidate:
            lines.append(candidate)

    if not lines:
        return None

    return " ".join(_dedupe_keep_order(lines))


def extract_context_from_html(html: str) -> tuple[list[str], list[str], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    text_candidates: list[str] = []

    for attr_name, attr_value in (
        ("property", "og:title"),
        ("property", "og:description"),
        ("name", "description"),
    ):
        meta_content = _extract_meta_content(soup, attr_name, attr_value)
        if meta_content:
            text_candidates.append(meta_content)

    image_url = _extract_meta_content(soup, "property", "og:image")

    subtitle_urls: list[str] = []
    for payload in _extract_json_from_html(soup):
        text_candidates.extend(_collect_text_candidates(payload))
        subtitle_urls.extend(_collect_subtitle_urls(payload))

    deduped_text = _dedupe_keep_order(text_candidates)
    limited_text = _limit_text_candidates(deduped_text)
    return limited_text, _dedupe_keep_order(subtitle_urls), image_url


async def _fetch_video_page_context(url: str) -> tuple[list[str], list[str], str | None]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )
    }
    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        return extract_context_from_html(response.text)


async def _fetch_first_subtitle(subtitle_urls: list[str]) -> str | None:
    if not subtitle_urls:
        return None

    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        for subtitle_url in subtitle_urls[:3]:
            try:
                response = await client.get(subtitle_url)
                response.raise_for_status()
                transcript = _parse_subtitle_payload(response.text)
                if transcript:
                    return transcript
            except Exception:
                continue

    return None


async def get_video_metadata(url: str) -> dict[str, Any]:
    oembed_url = f"https://www.tiktok.com/oembed?url={url}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(oembed_url)
        response.raise_for_status()
        data = response.json()
        return {
            "title": data.get("title", ""),
            "thumbnail_url": data.get("thumbnail_url"),
        }


async def get_video_context(url: str) -> tuple[str, str | None]:
    if not _is_tiktok_url(url):
        raise ValueError("Invalid TikTok URL. Please provide a valid TikTok video link.")

    page_task = asyncio.create_task(_fetch_video_page_context(url))
    metadata_task = asyncio.create_task(get_video_metadata(url))

    metadata: dict[str, Any] = {}
    try:
        metadata = await metadata_task
    except Exception:
        metadata = {}

    text_candidates: list[str] = []
    subtitle_urls: list[str] = []
    og_image: str | None = None
    try:
        text_candidates, subtitle_urls, og_image = await page_task
    except Exception as e:
        if not metadata:
            raise ValueError("Unable to access TikTok video details.") from e

    transcript = await _fetch_first_subtitle(subtitle_urls)
    if transcript:
        transcript = transcript[:8000]

    combined_parts = _dedupe_keep_order([metadata.get("title", ""), *text_candidates, transcript or ""])

    if not combined_parts:
        raise ValueError("No captions or textual context were found for this TikTok video. Please try another video.")

    thumbnail_url = metadata.get("thumbnail_url") or og_image
    return "\n\n".join(combined_parts), thumbnail_url
