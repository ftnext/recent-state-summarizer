import json
from collections.abc import Generator
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag


def _match_qiita_advent_calendar(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == "qiita.com" and "/advent-calendar/" in parsed.path


def _fetch(url: str) -> str:
    response = httpx.get(url)
    response.raise_for_status()
    return response.text


@register_fetcher(
    name="Qiita Advent Calendar",
    matcher=_match_qiita_advent_calendar,
)
def fetch_qiita_advent_calendar(url: str) -> Generator[TitleTag, None, None]:
    """Fetch article titles and URLs from Qiita Advent Calendar.

    Args:
        url: Qiita Advent Calendar URL (e.g., https://qiita.com/advent-calendar/2025/python-type-hints)

    Yields:
        TitleTag dictionaries containing title and url
    """
    raw_html = _fetch(url)
    yield from _parse_titles(raw_html)


def _parse_titles(raw_html: str) -> Generator[TitleTag, None, None]:
    """Parse titles from Qiita Advent Calendar HTML by extracting JSON data."""
    soup = BeautifulSoup(raw_html, "html.parser")
    script_tag = soup.find(
        "script",
        attrs={"data-js-react-on-rails-store": "AppStoreWithReactOnRails"},
    )
    if not script_tag or not script_tag.string:
        return

    data = json.loads(script_tag.string)
    advent_calendars = data.get("adventCalendars", {})
    table_calendars = advent_calendars.get("tableAdventCalendars", [])
    if not table_calendars:
        return
    items = table_calendars[0].get("items", [])

    for item in items:
        if not item.get("isRevealed", False):
            continue

        title = item.get("comment")
        article_url = item.get("url")

        if title and article_url:
            yield {"title": title, "url": article_url}
