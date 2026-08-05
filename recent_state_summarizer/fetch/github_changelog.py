import logging
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import feedparser
import httpx

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag

logger = logging.getLogger(__name__)

RECENT_DAYS = 30
FEED_URL = "https://github.blog/changelog/feed/"


def _match_github_changelog(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.netloc == "github.blog"
        and parsed.path.rstrip("/") == "/changelog/feed"
    )


def _recent_cutoff(days: int = RECENT_DAYS) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def _published_at(entry) -> datetime:
    return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)


@register_fetcher(name="GitHub Changelog", matcher=_match_github_changelog)
def fetch_github_changelog(
    url: str, *, days: int = RECENT_DAYS
) -> Generator[TitleTag, None, None]:
    """Fetch changelog entries published within the recent days.

    The feed returns 10 entries per page and ignores per-page size
    parameters, so entries older than the cutoff are reached by walking
    `?paged=N` until the cutoff, an empty page or a 404 response.

    Redirects are followed because `?paged=1` and the URL without a
    trailing slash are answered with 301 to their canonical form.

    Args:
        url: GitHub Changelog feed URL (https://github.blog/changelog/feed/)
        days: Number of recent days to fetch entries from

    Yields:
        TitleTag dictionaries containing title and url
    """
    cutoff = _recent_cutoff(days)

    page = 1
    while True:
        logger.info("Fetching page %s of %s", page, url)
        response = httpx.get(
            url, params={"paged": page}, follow_redirects=True
        )
        if response.status_code == httpx.codes.NOT_FOUND:
            return
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        if not feed.entries:
            return

        for entry in feed.entries:
            if _published_at(entry) < cutoff:
                return
            yield {"title": entry.title, "url": entry.link}

        page += 1
