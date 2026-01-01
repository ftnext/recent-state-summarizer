from __future__ import annotations

import argparse
import json
import textwrap
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import TypedDict
from urllib.request import urlopen

from bs4 import BeautifulSoup

PARSE_HATENABLOG_KWARGS = {"name": "a", "attrs": {"class": "entry-title-link"}}


class TitleTag(TypedDict):
    title: str
    url: str


def _main(url: str, save_path: str | Path, save_as_json: bool) -> None:
    title_tags = _fetch_titles(url)
    if not save_as_json:
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
        "--as-text",
        action="store_true",
        default=False,
        help="Save as title-only bullet list instead of JSON Lines",
    )
    return parser


def cli():
    parser = build_parser()
    args = parser.parse_args()

    _main(args.url, args.save_path, save_as_json=not args.as_text)


if __name__ == "__main__":
    cli()
