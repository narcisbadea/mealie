import pytest

from mealie.services.scraper import tiktok_scraper


@pytest.mark.asyncio
async def test_get_video_context_builds_combined_text(monkeypatch: pytest.MonkeyPatch):
    async def mock_fetch_video_page_context(url: str):
        return (
            ["TikTok caption text", "Quick pasta recipe"],
            ["https://example.com/captions.vtt"],
            "https://example.com/og.jpg",
        )

    async def mock_get_video_metadata(url: str):
        return {"title": "My TikTok Recipe", "thumbnail_url": "https://example.com/thumb.jpg"}

    async def mock_fetch_first_subtitle(urls: list[str]):
        return "Step one. Step two."

    monkeypatch.setattr(tiktok_scraper, "_fetch_video_page_context", mock_fetch_video_page_context)
    monkeypatch.setattr(tiktok_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(tiktok_scraper, "_fetch_first_subtitle", mock_fetch_first_subtitle)

    combined_text, thumbnail_url = await tiktok_scraper.get_video_context(
        "https://www.tiktok.com/@chef/video/123456789"
    )

    assert "My TikTok Recipe" in combined_text
    assert "Quick pasta recipe" in combined_text
    assert "Step one. Step two." in combined_text
    assert thumbnail_url == "https://example.com/thumb.jpg"


@pytest.mark.asyncio
async def test_get_video_context_rejects_invalid_url():
    with pytest.raises(ValueError, match="Invalid TikTok URL"):
        await tiktok_scraper.get_video_context("https://example.com/not-tiktok")


def test_extract_context_from_html_collects_text_and_subtitles():
    html = """
    <html>
      <head>
        <meta property=\"og:title\" content=\"Pasta in 10 Minutes\" />
        <meta property=\"og:description\" content=\"Simple pantry pasta\" />
        <meta property=\"og:image\" content=\"https://example.com/cover.jpg\" />
      </head>
      <body>
        <script id=\"__UNIVERSAL_DATA_FOR_REHYDRATION__\" type=\"application/json\">
          {
            "videoDetail": {
              "desc": "Cook with me: garlic pasta"
            },
            "subtitleInfos": [
              {"LanguageCodeName": "en", "Url": "https://example.com/subtitles.vtt"}
            ]
          }
        </script>
      </body>
    </html>
    """

    text_candidates, subtitle_urls, image_url = tiktok_scraper.extract_context_from_html(html)

    assert "Pasta in 10 Minutes" in text_candidates
    assert "Cook with me: garlic pasta" in text_candidates
    assert "https://example.com/subtitles.vtt" in subtitle_urls
    assert image_url == "https://example.com/cover.jpg"


def test_parse_subtitle_payload_from_vtt():
    vtt_payload = """
    WEBVTT

    1
    00:00.000 --> 00:02.000
    1 cup flour

    2
    00:02.000 --> 00:04.000
    Mix well
    """

    transcript = tiktok_scraper._parse_subtitle_payload(vtt_payload)

    assert transcript == "1 cup flour Mix well"
