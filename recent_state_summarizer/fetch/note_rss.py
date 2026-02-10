from collections.abc import Generator
from urllib.parse import urlparse

import feedparser
import httpx

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag


def _match_note_rss(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == "note.com" and parsed.path.endswith("/rss")


@register_fetcher(
    name="note RSS",
    matcher=_match_note_rss,
    example="https://note.com/user/rss",
)
def fetch_note_rss(url: str) -> Generator[TitleTag, None, None]:
    response = httpx.get(url)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    for entry in feed.entries:
        yield {"title": entry.title, "url": entry.link}
