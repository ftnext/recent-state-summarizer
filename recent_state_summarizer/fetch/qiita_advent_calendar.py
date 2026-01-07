import json
from collections.abc import Generator
from typing import TypedDict

import httpx
from bs4 import BeautifulSoup


class TitleTag(TypedDict):
    title: str
    url: str


def _fetch(url: str) -> str:
    response = httpx.get(url)
    response.raise_for_status()
    return response.text


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
    script_tag = soup.find("script", id="js-react-on-rails-context")
    if not script_tag or not script_tag.string:
        return

    data = json.loads(script_tag.string)
    calendar_data = data.get("advencalApp", {})
    items = calendar_data.get("calendar", {}).get("items", [])

    for item in items:
        article = item.get("article")
        if not article:
            continue

        title = article.get("title")
        article_url = article.get("url")

        if title and article_url:
            yield {"title": title, "url": article_url}
