from typing import Generator
from urllib.parse import urlparse

import feedparser
import httpx

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag


def _match_qiita_rss(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == "qiita.com" and parsed.path.endswith("/feed.atom")


@register_fetcher(name="Qiita RSS", matcher=_match_qiita_rss)
def fetch_qiita_rss(url: str) -> Generator[TitleTag, None, None]:
    response = httpx.get(url)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    for entry in feed.entries:
        yield {"title": entry.title, "url": entry.link}
