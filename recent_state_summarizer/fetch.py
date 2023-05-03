from __future__ import annotations

from collections.abc import Generator, Iterable
from pathlib import Path
from urllib.request import urlopen

from bs4 import BeautifulSoup

PARSE_HATENABLOG_KWARGS = {"name": "a", "attrs": {"class": "entry-title-link"}}


def _main(url: str, save_path: str | Path) -> None:
    contents = fetch_titles_as_bullet_list(url)
    _save(save_path, contents)


def fetch_titles_as_bullet_list(url: str) -> str:
    return _as_bullet_list(_fetch_titles(url))


def _fetch_titles(url: str) -> Generator[str, None, None]:
    raw_html = _fetch(url)
    yield from _parse_titles(raw_html)


def _fetch(url: str) -> str:
    with urlopen(url) as res:
        return res.read()


def _parse_titles(raw_html: str) -> Generator[str, None, None]:
    soup = BeautifulSoup(raw_html, "html.parser")
    body = soup.body
    title_tags = body.find_all(**PARSE_HATENABLOG_KWARGS)
    for title_tag in title_tags:
        yield title_tag.text


def _as_bullet_list(titles: Iterable[str]) -> str:
    return "\n".join(f"- {title}" for title in titles)


def _save(path: str | Path, contents: str) -> None:
    with open(path, "w", encoding="utf8", newline="") as f:
        f.write(contents)


if __name__ == "__main__":
    import argparse
    import textwrap

    help_message = """
    Retrieve the titles of articles from a specified URL page
    and save them as a list.

    Support:
        - はてなブログ（Hatena blog）

    Example:
        python -m recent_state_summarizer.fetch \\
          https://awesome.hatenablog.com/archive/2023 awesome_titles.txt
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_message),
    )
    parser.add_argument("url", help="URL of archive page")
    parser.add_argument("save_path", help="Local file path")
    args = parser.parse_args()

    _main(args.url, args.save_path)
