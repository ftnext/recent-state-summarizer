import logging

import httpx
import pytest
import respx

from recent_state_summarizer.fetch import youtube_channel, youtube_playlist
from recent_state_summarizer.fetch.youtube_channel import (
    API_KEY_ENV_VAR,
    CHANNELS_API_URL,
    fetch_youtube_channel,
)
from recent_state_summarizer.fetch.youtube_playlist import (
    PLAYLIST_ITEMS_API_URL,
)
from tests.fetch.test_youtube_playlist import (
    build_playlist_item,
    build_playlist_response,
)

CHANNEL_HANDLE = "@startpythonclub9441"
CHANNEL_URL = f"https://www.youtube.com/{CHANNEL_HANDLE}"
UPLOADS_PLAYLIST_ID = "UU_uploads_playlist_id"
TEST_API_KEY = "test-youtube-api-key"


def build_channel_response(uploads_id: str | None = UPLOADS_PLAYLIST_ID):
    related_playlists = {}
    if uploads_id is not None:
        related_playlists["uploads"] = uploads_id
    return httpx.Response(
        status_code=200,
        json={
            "items": [
                {
                    "contentDetails": {
                        "relatedPlaylists": related_playlists,
                    }
                }
            ]
        },
        headers={"content-type": "application/json"},
    )


@pytest.fixture
def youtube_api_key(monkeypatch):
    monkeypatch.setenv(API_KEY_ENV_VAR, TEST_API_KEY)


class TestYouTubeChannel:
    @respx.mock
    def test_fetch_youtube_channel(self, youtube_api_key):
        channels_route = respx.get(CHANNELS_API_URL).mock(
            return_value=build_channel_response()
        )
        playlist_route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response(
                [
                    build_playlist_item("Video 1", "vid1"),
                    build_playlist_item("Video 2", "vid2"),
                ]
            )
        )

        result = list(fetch_youtube_channel(CHANNEL_URL))

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
        assert len(channels_route.calls) == 1
        channel_request = channels_route.calls[0].request
        assert dict(channel_request.url.params) == {
            "part": "contentDetails",
            "forHandle": CHANNEL_HANDLE,
        }
        assert "key" not in channel_request.url.params
        assert channel_request.headers["X-Goog-Api-Key"] == TEST_API_KEY

        assert len(playlist_route.calls) == 1
        playlist_request = playlist_route.calls[0].request
        assert dict(playlist_request.url.params) == {
            "part": "snippet",
            "playlistId": UPLOADS_PLAYLIST_ID,
            "maxResults": "50",
        }
        assert "key" not in playlist_request.url.params
        assert playlist_request.headers["X-Goog-Api-Key"] == TEST_API_KEY

    @respx.mock
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/@%E6%97%A5%E6%9C%AC%E8%AA%9E",
            "https://www.youtube.com/@日本語",
        ],
    )
    def test_decodes_percent_encoded_handle(self, youtube_api_key, url):
        channels_route = respx.get(CHANNELS_API_URL).mock(
            return_value=build_channel_response()
        )
        respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response(
                [build_playlist_item("Video 1", "vid1")]
            )
        )

        result = list(fetch_youtube_channel(url))

        assert result == [
            {
                "title": "Video 1",
                "url": "https://www.youtube.com/watch?v=vid1",
            }
        ]
        assert (
            channels_route.calls[0].request.url.params["forHandle"]
            == "@日本語"
        )

    @respx.mock
    def test_follows_pagination(self, youtube_api_key, caplog):
        caplog.set_level(logging.INFO)
        respx.get(CHANNELS_API_URL).mock(return_value=build_channel_response())
        playlist_route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
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

        result = list(fetch_youtube_channel(CHANNEL_URL))

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
        assert len(playlist_route.calls) == 2
        assert "pageToken" not in playlist_route.calls[0].request.url.params
        assert (
            playlist_route.calls[1].request.url.params["pageToken"]
            == "token-page-2"
        )
        assert [
            record.getMessage()
            for record in caplog.records
            if record.name
            in {youtube_channel.__name__, youtube_playlist.__name__}
        ] == [
            f"Fetching uploads playlist ID for channel {CHANNEL_HANDLE}",
            f"Fetching page 1 of playlist {UPLOADS_PLAYLIST_ID}",
            f"Fetching page 2 of playlist {UPLOADS_PLAYLIST_ID}",
        ]

    @respx.mock
    def test_skips_deleted_and_private_videos(self, youtube_api_key):
        respx.get(CHANNELS_API_URL).mock(return_value=build_channel_response())
        respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response(
                [
                    build_playlist_item("Deleted video", "deleted1"),
                    build_playlist_item("Valid Video", "valid1"),
                    build_playlist_item("Private video", "private1"),
                ]
            )
        )

        result = list(fetch_youtube_channel(CHANNEL_URL))

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
        channels_route = respx.get(CHANNELS_API_URL).mock(
            return_value=build_channel_response()
        )
        playlist_route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response([])
        )

        with pytest.raises(ValueError, match=API_KEY_ENV_VAR):
            list(fetch_youtube_channel(CHANNEL_URL))

        assert not channels_route.called
        assert not playlist_route.called

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/@",
            "https://www.youtube.com/channel/UC1234567890",
        ],
    )
    def test_missing_channel_handle_raises(self, youtube_api_key, url):
        with pytest.raises(ValueError, match="Missing channel handle"):
            list(fetch_youtube_channel(url))

    @respx.mock
    @pytest.mark.parametrize("payload", [{"items": []}, {}])
    def test_channel_not_found_raises(self, youtube_api_key, payload):
        respx.get(CHANNELS_API_URL).mock(
            return_value=httpx.Response(
                status_code=200,
                json=payload,
                headers={"content-type": "application/json"},
            )
        )
        playlist_route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response([])
        )

        with pytest.raises(ValueError, match="Channel not found"):
            list(fetch_youtube_channel(CHANNEL_URL))

        assert not playlist_route.called

    @respx.mock
    def test_missing_uploads_playlist_raises(self, youtube_api_key):
        respx.get(CHANNELS_API_URL).mock(
            return_value=build_channel_response(uploads_id=None)
        )
        playlist_route = respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=build_playlist_response([])
        )

        with pytest.raises(ValueError, match="Uploads playlist not found"):
            list(fetch_youtube_channel(CHANNEL_URL))

        assert not playlist_route.called

    @respx.mock
    @pytest.mark.parametrize("status_code", [403, 404])
    def test_channels_api_http_error_propagates(
        self, youtube_api_key, status_code
    ):
        respx.get(CHANNELS_API_URL).mock(
            return_value=httpx.Response(status_code=status_code)
        )

        with pytest.raises(httpx.HTTPStatusError):
            list(fetch_youtube_channel(CHANNEL_URL))

    @respx.mock
    @pytest.mark.parametrize("status_code", [403, 404])
    def test_playlist_items_api_http_error_propagates(
        self, youtube_api_key, status_code
    ):
        respx.get(CHANNELS_API_URL).mock(return_value=build_channel_response())
        respx.get(PLAYLIST_ITEMS_API_URL).mock(
            return_value=httpx.Response(status_code=status_code)
        )

        with pytest.raises(httpx.HTTPStatusError):
            list(fetch_youtube_channel(CHANNEL_URL))
