from collections.abc import Generator
from urllib.parse import urlparse

import feedparser
import httpx

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag


def _match_github_changelog(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc == "github.blog"
        and parsed.path.rstrip("/") == "/changelog/feed"
    )


@register_fetcher(name="GitHub Changelog", matcher=_match_github_changelog)
def fetch_github_changelog(url: str) -> Generator[TitleTag, None, None]:
    response = httpx.get(url)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    for entry in feed.entries:
        yield {"title": entry.title, "url": entry.link}
