import pytest

from mealie.services.scraper import tiktok_scraper


# URL Validation Tests
@pytest.mark.parametrize(
    "url,expected_valid",
    [
        ("https://www.tiktok.com/@user/video/1234567890", True),
        ("https://tiktok.com/@user/video/1234567890", True),
        ("https://vm.tiktok.com/AbCdEfG/", True),
        ("https://vt.tiktok.com/AbCdEfG/", True),
        ("https://m.tiktok.com/v/1234567890.html", True),
        ("http://www.tiktok.com/@user/video/123", True),
        ("https://example.com/tiktok", False),
        ("https://not-tiktok.com/@user/video/123", False),
    ],
)
def test_is_tiktok_url_validation(url: str, expected_valid: bool):
    """Test URL validation for various TikTok URL formats."""
    assert tiktok_scraper._is_tiktok_url(url) == expected_valid


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


# Subtitle URL Discovery Tests
def test_collect_subtitle_urls_by_file_extension():
    """Test that subtitle URLs are detected by file extension when nested in dicts."""
    # Realistic TikTok-like structure where URLs are in objects with explicit keys
    payload = {
        "videoDetail": {
            "resources": [
                {"type": "video", "url": "https://example.com/video.mp4"},
                {"type": "subtitle", "url": "https://example.com/subtitles.vtt"},
                {"type": "caption", "url": "https://example.com/captions.srt"},
            ]
        }
    }

    urls = tiktok_scraper._collect_subtitle_urls(payload)

    assert "https://example.com/subtitles.vtt" in urls
    assert "https://example.com/captions.srt" in urls
    assert "https://example.com/video.mp4" not in urls


def test_collect_subtitle_urls_by_url_path():
    """Test that subtitle URLs are detected by URL path patterns."""
    # URLs with /subtitle/ or /caption/ in the path
    payload = {
        "media": {
            "captionUrls": [
                "https://example.com/subtitle/en.vtt",
                "https://example.com/caption/fr.json",
            ],
            "videoUrl": "https://example.com/video/main.mp4",
        }
    }

    urls = tiktok_scraper._collect_subtitle_urls(payload)

    assert "https://example.com/subtitle/en.vtt" in urls
    assert "https://example.com/caption/fr.json" in urls
    assert "https://example.com/video/main.mp4" not in urls


# Error Message Tests
@pytest.mark.asyncio
async def test_get_video_context_specific_error_no_captions(monkeypatch: pytest.MonkeyPatch):
    """Test specific error message when video has no captions."""
    async def mock_fetch_video_page_context(url: str):
        return ([], [], None)  # No text, no subtitles, no image

    async def mock_get_video_metadata(url: str):
        return {"title": "", "thumbnail_url": None}

    async def mock_fetch_first_subtitle(urls: list[str]):
        return None

    monkeypatch.setattr(tiktok_scraper, "_fetch_video_page_context", mock_fetch_video_page_context)
    monkeypatch.setattr(tiktok_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(tiktok_scraper, "_fetch_first_subtitle", mock_fetch_first_subtitle)

    with pytest.raises(ValueError, match="no captions available"):
        await tiktok_scraper.get_video_context("https://www.tiktok.com/@chef/video/123456789")


@pytest.mark.asyncio
async def test_get_video_context_specific_error_subtitle_fetch_failed(monkeypatch: pytest.MonkeyPatch):
    """Test specific error message when subtitle references exist but fetch fails."""
    async def mock_fetch_video_page_context(url: str):
        return ([], ["https://example.com/subtitle.vtt"], None)  # Subtitle refs but no text

    async def mock_get_video_metadata(url: str):
        return {"title": "", "thumbnail_url": None}

    async def mock_fetch_first_subtitle(urls: list[str]):
        return None  # Fetch failed

    monkeypatch.setattr(tiktok_scraper, "_fetch_video_page_context", mock_fetch_video_page_context)
    monkeypatch.setattr(tiktok_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(tiktok_scraper, "_fetch_first_subtitle", mock_fetch_first_subtitle)

    with pytest.raises(ValueError, match="Found caption references but could not fetch"):
        await tiktok_scraper.get_video_context("https://www.tiktok.com/@chef/video/123456789")
