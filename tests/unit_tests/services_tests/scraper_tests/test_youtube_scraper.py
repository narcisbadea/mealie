import pytest

from mealie.services.scraper import youtube_scraper


def test_extract_video_id_supports_standard_and_short_urls():
    assert youtube_scraper.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert youtube_scraper.extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert youtube_scraper.extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_get_video_context_success(monkeypatch: pytest.MonkeyPatch):
    async def mock_get_video_metadata(url: str):
        return {"title": "Test Video", "thumbnail_url": "https://example.com/thumb.jpg"}

    # 150+ chars to pass minimum transcript length validation
    async def mock_get_transcript(video_id: str):
        return "Step 1. Step 2. This is a long enough transcript for validation to pass the minimum requirement of 100 characters."

    monkeypatch.setattr(youtube_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(youtube_scraper, "get_transcript", mock_get_transcript)

    text, thumbnail = await youtube_scraper.get_video_context("https://youtu.be/dQw4w9WgXcQ")

    assert (
        text
        == "Test Video\n\nStep 1. Step 2. This is a long enough transcript for validation to pass the minimum requirement of 100 characters."
    )
    assert thumbnail == "https://example.com/thumb.jpg"


@pytest.mark.asyncio
async def test_get_video_context_allows_metadata_failure(monkeypatch: pytest.MonkeyPatch):
    async def mock_get_video_metadata(url: str):
        raise RuntimeError("oembed error")

    # 120+ chars to pass minimum transcript length validation
    async def mock_get_transcript(video_id: str):
        return "Recipe transcript that is long enough to pass the validation requirement of at least one hundred characters."

    monkeypatch.setattr(youtube_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(youtube_scraper, "get_transcript", mock_get_transcript)

    text, thumbnail = await youtube_scraper.get_video_context("https://youtu.be/dQw4w9WgXcQ")

    assert (
        text
        == "Recipe transcript that is long enough to pass the validation requirement of at least one hundred characters."
    )
    assert thumbnail is None


@pytest.mark.asyncio
async def test_get_video_context_rejects_invalid_url():
    with pytest.raises(ValueError, match="Invalid YouTube URL"):
        await youtube_scraper.get_video_context("https://example.com/video")


@pytest.mark.asyncio
async def test_get_video_context_raises_on_transcript_error(monkeypatch: pytest.MonkeyPatch):
    async def mock_get_video_metadata(url: str):
        return {"title": "Test Video", "thumbnail_url": "https://example.com/thumb.jpg"}

    async def mock_get_transcript(video_id: str):
        raise youtube_scraper.YouTubeTranscriptError("This video has no captions available.")

    monkeypatch.setattr(youtube_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(youtube_scraper, "get_transcript", mock_get_transcript)

    with pytest.raises(youtube_scraper.YouTubeTranscriptError, match="no captions available"):
        await youtube_scraper.get_video_context("https://youtu.be/dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_get_video_context_rejects_short_transcript(monkeypatch: pytest.MonkeyPatch):
    async def mock_get_video_metadata(url: str):
        return {"title": "Test Video", "thumbnail_url": "https://example.com/thumb.jpg"}

    async def mock_get_transcript(video_id: str):
        return "Short"

    monkeypatch.setattr(youtube_scraper, "get_video_metadata", mock_get_video_metadata)
    monkeypatch.setattr(youtube_scraper, "get_transcript", mock_get_transcript)

    with pytest.raises(ValueError, match="too short"):
        await youtube_scraper.get_video_context("https://youtu.be/dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_get_transcript_truncates_long_transcript(monkeypatch: pytest.MonkeyPatch):
    def mock_fetch_transcript_sync(video_id: str):
        return "x" * 20000

    monkeypatch.setattr(youtube_scraper, "_fetch_transcript_sync", mock_fetch_transcript_sync)

    transcript = await youtube_scraper.get_transcript("dQw4w9WgXcQ")

    assert len(transcript) == 12000
