from __future__ import annotations

import logging
import os
from collections.abc import Generator
from urllib.parse import parse_qs, urlparse

from recent_state_summarizer.fetch import http_client
from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag

logger = logging.getLogger(__name__)

PLAYLIST_ITEMS_API_URL = (
    "https://youtube.googleapis.com/youtube/v3/playlistItems"
)
VIDEO_WATCH_URL_PREFIX = "https://www.youtube.com/watch?v="
API_KEY_ENV_VAR = "RSS_YOUTUBE_DATA_KEY"
MAX_RESULTS = 50
YOUTUBE_HOSTS = frozenset(
    {"www.youtube.com", "youtube.com", "m.youtube.com"}
)
UNAVAILABLE_TITLES = frozenset({"Deleted video", "Private video"})


def _extract_playlist_id(url: str) -> str | None:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    values = query.get("list")
    if values and values[0]:
        return values[0]
    return None


def _match_youtube_playlist(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc in YOUTUBE_HOSTS
        and parsed.path.rstrip("/") == "/playlist"
        and _extract_playlist_id(url) is not None
    )


def get_api_key() -> str:
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        raise ValueError(
            f"Environment variable {API_KEY_ENV_VAR} is not set."
        )
    return api_key


def fetch_playlist_items(
    playlist_id: str, api_key: str
) -> Generator[TitleTag, None, None]:
    page = 1
    page_token: str | None = None

    while True:
        logger.info("Fetching page %s of playlist %s", page, playlist_id)
        params: dict[str, str | int] = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": MAX_RESULTS,
        }
        if page_token:
            params["pageToken"] = page_token

        response = http_client.get(
            PLAYLIST_ITEMS_API_URL,
            params=params,
            headers={"X-Goog-Api-Key": api_key},
        )
        response.raise_for_status()

        data = response.json()
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            title = snippet.get("title")
            video_id = snippet.get("resourceId", {}).get("videoId")
            if not title or title in UNAVAILABLE_TITLES or not video_id:
                continue
            yield {
                "title": title,
                "url": f"{VIDEO_WATCH_URL_PREFIX}{video_id}",
            }

        page_token = data.get("nextPageToken")
        if not page_token:
            return
        page += 1


@register_fetcher(
    name="YouTube Playlist",
    matcher=_match_youtube_playlist,
)
def fetch_youtube_playlist(url: str) -> Generator[TitleTag, None, None]:
    """Fetch video titles and URLs from a public YouTube playlist."""
    playlist_id = _extract_playlist_id(url)
    if playlist_id is None:
        raise ValueError(f"Missing playlist ID in URL: {url}")

    api_key = get_api_key()
    yield from fetch_playlist_items(playlist_id, api_key)
