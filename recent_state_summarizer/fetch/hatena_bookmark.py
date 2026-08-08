from typing import Generator, TypedDict
from urllib.parse import urlparse

import feedparser
import httpx

from recent_state_summarizer.fetch.registry import register_fetcher


def _match_hatena_bookmark_rss(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc == "b.hatena.ne.jp"
        and parsed.path.startswith("/entrylist/")
        and parsed.path.endswith(".rss")
    )


class BookmarkEntry(TypedDict):
    title: str
    url: str
    description: str


@register_fetcher(
    name="はてなブックマークRSS",
    matcher=_match_hatena_bookmark_rss,
    example="https://b.hatena.ne.jp/entrylist/user.rss",
)
def fetch_hatena_bookmark_rss(
    url: str,
) -> Generator[BookmarkEntry, None, None]:
    """Fetch entries from Hatena Bookmark RSS feed.

    Args:
        url: URL of the Hatena Bookmark RSS feed

    Yields:
        Bookmark entries with title, url, and description
    """
    response = httpx.get(url)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    for entry in feed.entries:
        yield {
            "title": entry.title,
            "url": entry.link,
            "description": entry.description,
        }
