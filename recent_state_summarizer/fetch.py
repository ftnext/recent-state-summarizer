from __future__ import annotations

import argparse
import json
import logging
import textwrap
from collections.abc import Generator, Iterable
from enum import Enum
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse
from urllib.request import urlopen

import feedparser
import httpx
from bs4 import BeautifulSoup

PARSE_HATENABLOG_KWARGS = {"name": "a", "attrs": {"class": "entry-title-link"}}

logger = logging.getLogger(__name__)


class URLType(Enum):
    """Type of URL for fetching."""

    HATENA_BLOG = "hatena_blog"
    HATENA_BOOKMARK_RSS = "hatena_bookmark_rss"
    UNKNOWN = "unknown"


def _detect_url_type(url: str) -> URLType:
    """Detect the type of URL to determine fetch strategy.

    Args:
        url: URL to analyze

    Returns:
        URLType indicating the fetch strategy to use
    """
    parsed = urlparse(url)
    if (
        parsed.netloc == "b.hatena.ne.jp"
        and parsed.path.startswith("/entrylist/")
        and parsed.path.endswith(".rss")
    ):
        return URLType.HATENA_BOOKMARK_RSS

    if "hatenablog.com" in url or "hateblo.jp" in url:
        return URLType.HATENA_BLOG

    return URLType.UNKNOWN


def _select_fetcher(url_type):
    match url_type:
        case URLType.HATENA_BOOKMARK_RSS:
            return fetch_hatena_bookmark_rss
        case URLType.HATENA_BLOG:
            return _fetch_titles
        case _:
            logger.warning("Unknown URL type: %s", url_type)
            return _fetch_titles  # To pass tests


class TitleTag(TypedDict):
    title: str
    url: str


class BookmarkEntry(TypedDict):
    title: str
    url: str
    description: str


def _main(
    url: str, save_path: str | Path, *, save_as_title_list: bool
) -> None:
    url_type = _detect_url_type(url)
    fetcher = _select_fetcher(url_type)
    title_tags = fetcher(url)
    if save_as_title_list:
        contents = _as_bullet_list(
            title_tag["title"] for title_tag in title_tags
        )
    else:
        contents = _as_json(title_tags)
    _save(save_path, contents)


def fetch_titles_as_bullet_list(url: str) -> str:
    title_tags = _fetch_titles(url)
    return _as_bullet_list(title_tag["title"] for title_tag in title_tags)


def _fetch_titles(url: str) -> Generator[TitleTag, None, None]:
    raw_html = _fetch(url)
    yield from _parse_titles(raw_html)

    soup = BeautifulSoup(raw_html, "html.parser")
    next_link = soup.find("a", class_="test-pager-next")
    if next_link and "href" in next_link.attrs:
        next_url = next_link["href"]
        print(f"Next page found, fetching... {next_url}")
        yield from _fetch_titles(next_url)


def _fetch(url: str) -> str:
    with urlopen(url) as res:
        return res.read()


def _parse_titles(raw_html: str) -> Generator[TitleTag, None, None]:
    soup = BeautifulSoup(raw_html, "html.parser")
    body = soup.body
    title_tags = body.find_all(**PARSE_HATENABLOG_KWARGS)
    for title_tag in title_tags:
        yield {"title": title_tag.text, "url": title_tag["href"]}


def _as_bullet_list(titles: Iterable[str]) -> str:
    return "\n".join(f"- {title}" for title in titles)


def _as_json(title_tags: Iterable[TitleTag]) -> str:
    return "\n".join(
        json.dumps(title_tag, ensure_ascii=False) for title_tag in title_tags
    )


def _save(path: str | Path, contents: str) -> None:
    with open(path, "w", encoding="utf8", newline="") as f:
        f.write(contents)


def fetch_hatena_bookmark_rss(url: str) -> list[BookmarkEntry]:
    """Fetch entries from Hatena Bookmark RSS feed.

    Args:
        url: URL of the Hatena Bookmark RSS feed

    Returns:
        List of bookmark entries with title, url, and description
    """
    response = httpx.get(url)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    entries = []
    for entry in feed.entries:
        entries.append(
            {
                "title": entry.title,
                "url": entry.link,
                "description": entry.description,
            }
        )

    return entries


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    help_message = """
    Retrieve the titles and URLs of articles from a web page specified by URL
    and save them as JSON Lines format.

    Support:
        - はてなブログ（Hatena blog）

    Example:
        python -m recent_state_summarizer.fetch \\
          https://awesome.hatenablog.com/archive/2023 articles.jsonl
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_message),
        add_help=add_help,
    )
    parser.add_argument("url", help="URL of archive page")
    parser.add_argument("save_path", help="Local file path")
    parser.add_argument(
        "--as-title-list",
        action="store_true",
        default=False,
        help="Save as title-only bullet list instead of JSON Lines",
    )
    return parser


def cli():
    parser = build_parser()
    args = parser.parse_args()

    _main(args.url, args.save_path, save_as_title_list=args.as_title_list)


if __name__ == "__main__":
    cli()
