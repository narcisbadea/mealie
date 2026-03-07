"""
Debug script: simulează fetchul de date pentru un URL YouTube și afișează
exact ce s-ar trimite la OpenAI, fără a apela efectiv API-ul.

Rulare:
    /tmp/debug-venv/bin/python dev/debug_youtube_scrape.py [URL]

Dependențe (instalate în /tmp/debug-venv):
    youtube-transcript-api httpx
"""

import asyncio
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PROMPT_FILE = ROOT / "mealie/services/openai/prompts/recipes/parse-recipe-text.txt"
DEFAULT_URL = "https://www.youtube.com/watch?v=GoNDvwneVVQ&t=3s"

_VIDEO_ID_RE = re.compile(r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/)|youtu\.be/)([a-zA-Z0-9_-]{11})")


def extract_video_id(url: str) -> str | None:
    match = _VIDEO_ID_RE.search(url)
    return match.group(1) if match else None


async def get_video_metadata(url: str) -> dict:
    import httpx

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
    """
    Identic cu mealie/services/scraper/youtube_scraper.py::_fetch_transcript_sync
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Preferă transcript manual; fallback la auto-generated
        transcript = None
        for t in transcript_list:
            print(f"    Transcript disponibil: lang={t.language_code}, generated={t.is_generated}")
            if not t.is_generated:
                transcript = t
                break
        if transcript is None:
            transcript = next(iter(transcript_list))

        print(f"  -> Folosit: lang={transcript.language_code}, generated={transcript.is_generated}")
        fetched = transcript.fetch()
        return " ".join(snippet.text for snippet in fetched)
    except Exception as e:
        print(f"  ⚠️  Eroare la transcript: {type(e).__name__}: {e}")
        return None


def print_section(title: str, content: str, max_chars: int = 2000) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
    if len(content) > max_chars:
        print(content[:max_chars])
        print(f"\n... [TRUNCHIAT — total {len(content)} caractere]")
    else:
        print(content)


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    print(f"\nURL: {url}")

    # ── 1. Video ID ──────────────────────────────────────────────────────────
    video_id = extract_video_id(url)
    print_section("1. VIDEO ID EXTRAS", video_id or "⚠️  Nu s-a putut extrage video ID!")
    if not video_id:
        sys.exit(1)

    # ── 2. Metadata ──────────────────────────────────────────────────────────
    print("\n[*] Fetch metadata de la YouTube oEmbed API ...")
    try:
        metadata = await get_video_metadata(url)
        print_section("2. METADATA", json.dumps(metadata, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"  ⚠️  Eroare la metadata: {e}")
        metadata = {"title": "", "thumbnail_url": None}

    # ── 3. Transcript ────────────────────────────────────────────────────────
    print("\n[*] Fetch transcript ...")
    transcript = _fetch_transcript_sync(video_id)

    if transcript:
        print_section("3. TRANSCRIPT (primele 3000 caractere)", transcript, max_chars=3000)
        print(f"\n  Total transcript: {len(transcript)} caractere / ~{len(transcript.split())} cuvinte")
    else:
        print_section("3. TRANSCRIPT", "⚠️  Nu s-a găsit niciun transcript — importul ar eșua!")

    # ── 4. Combined text (mesajul user trimis la OpenAI) ─────────────────────
    title = metadata.get("title", "")
    if title and transcript:
        combined_text = f"{title}\n\n{transcript}"
    elif transcript:
        combined_text = transcript
    else:
        combined_text = ""

    if combined_text:
        print_section(
            "4. COMBINED TEXT (role=user) — primele 3000 caractere",
            combined_text,
            max_chars=3000,
        )
        print(f"\n  Total combined_text: {len(combined_text)} caractere")
    else:
        print("\n⛔  combined_text gol — ValueError în create_from_youtube.")

    # ── 5. Prompt-ul sistem ──────────────────────────────────────────────────
    try:
        prompt_content = PROMPT_FILE.read_text(encoding="utf-8")
        print_section("5. SYSTEM PROMPT (parse-recipe-text.txt)", prompt_content, max_chars=9999)
    except Exception as e:
        print(f"  ⚠️  Nu s-a putut citi prompt-ul: {e}")

    # ── 6. Structura completă a apelului OpenAI ──────────────────────────────
    if combined_text:
        msg = {
            "messages": [
                {"role": "system", "content": "(prompt de mai sus)"},
                {"role": "user", "content": [{"type": "text", "text": combined_text[:200] + "..."}]},
            ],
            "model": "OPENAI_MODEL din .env",
            "response_format": "OpenAIRecipe (Pydantic structured output)",
        }
        print_section("6. STRUCTURA APELULUI OpenAI", json.dumps(msg, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print("  Simulare completă. Nu s-a apelat OpenAI.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
