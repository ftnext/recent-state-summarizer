from __future__ import annotations

import logging
from collections.abc import Generator
from urllib.parse import urlparse

from recent_state_summarizer.fetch import http_client
from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag
from recent_state_summarizer.fetch.youtube_playlist import (
    API_KEY_ENV_VAR,
    YOUTUBE_HOSTS,
    fetch_playlist_items,
    get_api_key,
)

logger = logging.getLogger(__name__)

CHANNELS_API_URL = "https://youtube.googleapis.com/youtube/v3/channels"


def _extract_channel_handle(url: str) -> str | None:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if path.startswith("/@") and "/" not in path[1:] and len(path) > 2:
        return path[1:]
    return None


def _match_youtube_channel(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc in YOUTUBE_HOSTS
        and _extract_channel_handle(url) is not None
    )


def _fetch_uploads_playlist_id(handle: str, api_key: str) -> str:
    logger.info("Fetching uploads playlist ID for channel %s", handle)
    response = http_client.get(
        CHANNELS_API_URL,
        params={"part": "contentDetails", "forHandle": handle},
        headers={"X-Goog-Api-Key": api_key},
    )
    response.raise_for_status()

    items = response.json().get("items") or []
    if not items:
        raise ValueError(f"Channel not found for handle: {handle}")

    uploads_id = (
        items[0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )
    if not uploads_id:
        raise ValueError(f"Uploads playlist not found for handle: {handle}")
    return uploads_id


@register_fetcher(
    name="YouTube Channel",
    matcher=_match_youtube_channel,
)
def fetch_youtube_channel(url: str) -> Generator[TitleTag, None, None]:
    """Fetch public video titles and URLs from a YouTube channel."""
    handle = _extract_channel_handle(url)
    if handle is None:
        raise ValueError(f"Missing channel handle in URL: {url}")

    api_key = get_api_key()
    uploads_playlist_id = _fetch_uploads_playlist_id(handle, api_key)
    yield from fetch_playlist_items(uploads_playlist_id, api_key)
