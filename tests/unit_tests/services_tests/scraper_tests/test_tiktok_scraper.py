import pytest

from mealie.services.scraper import tiktok_scraper


def test_extract_video_id_supports_standard_urls():
    """Test extraction from standard TikTok URLs."""
    assert (
        tiktok_scraper.extract_video_id("https://www.tiktok.com/@username/video/1234567890123456789")
        == "1234567890123456789"
    )
    assert (
        tiktok_scraper.extract_video_id("https://tiktok.com/@chef/video/9876543210987654321") == "9876543210987654321"
    )


def test_extract_video_id_supports_short_urls():
    """Test extraction from short TikTok URLs."""
    assert tiktok_scraper.extract_video_id("https://vm.tiktok.com/ZMxxxxxxx/") == "ZMxxxxxxx"
    assert tiktok_scraper.extract_video_id("https://m.tiktok.com/t/abc123") == "abc123"


def test_extract_video_id_returns_none_for_invalid_urls():
    """Test that invalid URLs return None."""
    assert tiktok_scraper.extract_video_id("https://example.com/video") is None
    assert tiktok_scraper.extract_video_id("not a url") is None
    assert tiktok_scraper.extract_video_id("https://youtube.com/watch?v=123") is None


@pytest.mark.asyncio
async def test_get_video_context_success(monkeypatch: pytest.MonkeyPatch):
    """Test successful video context extraction."""

    async def mock_get_video_metadata(url: str):
        return {
            "title": "Test TikTok Recipe",
            "thumbnail_url": "https://example.com/thumb.jpg",
            "author_name": "testuser",
        }

    async def mock_get_transcript(url: str):
        return "Step 1: Mix ingredients. Step 2: Cook."

    monkeypatch.setattr(tiktok_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(tiktok_scraper, "get_transcript", mock_get_transcript)

    text, thumbnail = await tiktok_scraper.get_video_context("https://www.tiktok.com/@user/video/1234567890123456789")

    assert text == "Test TikTok Recipe\n\nStep 1: Mix ingredients. Step 2: Cook."
    assert thumbnail == "https://example.com/thumb.jpg"


@pytest.mark.asyncio
async def test_get_video_context_allows_metadata_failure(monkeypatch: pytest.MonkeyPatch):
    """Test that metadata failure doesn't prevent context extraction."""

    async def mock_get_video_metadata(url: str):
        raise RuntimeError("oembed error")

    async def mock_get_transcript(url: str):
        return "Recipe transcript from captions"

    monkeypatch.setattr(tiktok_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(tiktok_scraper, "get_transcript", mock_get_transcript)

    text, thumbnail = await tiktok_scraper.get_video_context("https://www.tiktok.com/@user/video/1234567890123456789")

    assert text == "Recipe transcript from captions"
    assert thumbnail is None


@pytest.mark.asyncio
async def test_get_video_context_rejects_invalid_url():
    """Test that invalid URLs raise ValueError."""
    with pytest.raises(ValueError, match="Invalid TikTok URL"):
        await tiktok_scraper.get_video_context("https://example.com/video")


@pytest.mark.asyncio
async def test_get_video_context_rejects_missing_transcript(monkeypatch: pytest.MonkeyPatch):
    """Test that missing transcript raises ValueError."""

    async def mock_get_video_metadata(url: str):
        return {"title": "Test Video", "thumbnail_url": "https://example.com/thumb.jpg"}

    async def mock_get_transcript(url: str):
        return None

    monkeypatch.setattr(tiktok_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(tiktok_scraper, "get_transcript", mock_get_transcript)

    with pytest.raises(ValueError, match="No captions found"):
        await tiktok_scraper.get_video_context("https://www.tiktok.com/@user/video/1234567890123456789")


@pytest.mark.asyncio
async def test_get_transcript_truncates_long_transcript(monkeypatch: pytest.MonkeyPatch):
    """Test that very long transcripts are truncated."""

    def mock_fetch_subtitles_sync(url: str):
        return "x" * 20000

    monkeypatch.setattr(tiktok_scraper, "_fetch_subtitles_sync", mock_fetch_subtitles_sync)

    transcript = await tiktok_scraper.get_transcript("https://www.tiktok.com/@user/video/1234567890123456789")

    assert transcript is not None
    assert len(transcript) == 12000


def test_parse_subtitle_content_srt_format():
    """Test parsing SRT subtitle format."""
    srt_content = """1
00:00:00,000 --> 00:00:02,000
First subtitle line

2
00:00:02,000 --> 00:00:04,000
Second subtitle line
"""
    result = tiktok_scraper._parse_subtitle_content(srt_content)
    assert "First subtitle line" in result
    assert "Second subtitle line" in result


def test_parse_subtitle_content_json_format():
    """Test parsing JSON subtitle format."""
    json_content = '[{"text": "Hello"}, {"text": "World"}]'
    result = tiktok_scraper._parse_subtitle_content(json_content)
    assert result == "Hello World"
