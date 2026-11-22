import logging

import httpx
import pytest
import respx

from recent_state_summarizer.fetch import youtube_playlist
from recent_state_summarizer.fetch.youtube_playlist import (
    API_KEY_ENV_VAR,
    PLAYLIST_ITEMS_API_URL,
    fetch_youtube_playlist,
)

PLAYLIST_ID = "PLB0XQUsk_w8Q"
PLAYLIST_URL = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
TEST_API_KEY = "test-youtube-api-key"


def build_playlist_item(title: str, video_id: str) -> dict:
    return {
        "snippet": {
            "title": title,
            "resourceId": {"videoId": video_id},
        }
    }


def build_playlist_response(
    items: list[dict], next_page_token: str | None = None
) -> httpx.Response:
    payload: dict = {"items": items}
    if next_page_token is not None:
        payload["nextPageToken"] = next_page_token
    return httpx.Response(
        status_code=200,
        json=payload,
        headers={"content-type": "application/json"},
    )


@pytest.fixture
def youtube_api_key(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, TEST_API_KEY)


class TestYouTubePlaylist:
    @respx.mock
    def test_fetch_youtube_playlist(self, youtube_api_key):
        route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response(
                [
                    build_playlist_item("Video 1", "vid1"),
                    build_playlist_item("Video 2", "vid2"),
                ]
            )
        )

        result = list(fetch_youtube_playlist(PLAYLIST_URL))

        assert result == [
            {
                "title": "Video 1",
                "url": "https://www.youtube.com/watch?v=vid1",
            },
            {
                "title": "Video 2",
                "url": "https://www.youtube.com/watch?v=vid2",
            },
        ]
        assert len(route.calls) == 1
        request = route.calls[0].request
        assert dict(request.url.params) == {
            "part": "snippet",
            "playlistId": PLAYLIST_ID,
            "maxResults": "50",
        }
        assert "key" not in request.url.params
        assert request.headers["X-Goog-Api-Key"] == TEST_API_KEY

    @respx.mock
    def test_follows_pagination(self, youtube_api_key, caplog):
        caplog.set_level(logging.INFO)
        route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
            side_effect=[
                build_playlist_response(
                    [build_playlist_item("Page 1 Video", "p1")],
                    next_page_token="token-page-2",
                ),
                build_playlist_response(
                    [build_playlist_item("Page 2 Video", "p2")]
                ),
            ]
        )

        result = list(fetch_youtube_playlist(PLAYLIST_URL))

        assert result == [
            {
                "title": "Page 1 Video",
                "url": "https://www.youtube.com/watch?v=p1",
            },
            {
                "title": "Page 2 Video",
                "url": "https://www.youtube.com/watch?v=p2",
            },
        ]
        assert len(route.calls) == 2
        assert "pageToken" not in route.calls[0].request.url.params
        assert route.calls[1].request.url.params["pageToken"] == "token-page-2"
        assert [
            record.getMessage()
            for record in caplog.records
            if record.name == youtube_playlist.__name__
        ] == [
            f"Fetching page 1 of playlist {PLAYLIST_ID}",
            f"Fetching page 2 of playlist {PLAYLIST_ID}",
        ]

    @respx.mock
    def test_skips_deleted_and_private_videos(self, youtube_api_key):
        respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response(
                [
                    build_playlist_item("Deleted video", "deleted1"),
                    build_playlist_item("Valid Video", "valid1"),
                    build_playlist_item("Private video", "private1"),
                ]
            )
        )

        result = list(fetch_youtube_playlist(PLAYLIST_URL))

        assert result == [
            {
                "title": "Valid Video",
                "url": "https://www.youtube.com/watch?v=valid1",
            }
        ]

    @respx.mock
    @pytest.mark.parametrize("env_value", [None, "", "   "])
    def test_missing_api_key_raises(self, monkeypatch, env_value):
        if env_value is None:
            monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
        else:
            monkeypatch.setenv(API_KEY_ENV_VAR, env_value)
        route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response([])
        )

        with pytest.raises(ValueError, match=API_KEY_ENV_VAR):
            list(fetch_youtube_playlist(PLAYLIST_URL))

        assert not route.called

    def test_missing_playlist_id_raises(self, youtube_api_key):
        with pytest.raises(ValueError, match="Missing playlist ID"):
            list(fetch_youtube_playlist("https://www.youtube.com/playlist"))

    @respx.mock
    @pytest.mark.parametrize("status_code", [403, 404])
    def test_http_error_propagates(self, youtube_api_key, status_code):
        respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=httpx.Response(status_code=status_code)
        )

        with pytest.raises(httpx.HTTPStatusError):
            list(fetch_youtube_playlist(PLAYLIST_URL))
