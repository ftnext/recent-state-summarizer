from __future__ import annotations

import argparse
import json
import logging
import textwrap
from collections.abc import Iterable
from pathlib import Path

from recent_state_summarizer.fetch.registry import get_fetcher, get_registered_names

# Import fetchers to trigger registration (order matters: specific matchers first)
# Re-export for backward compatibility
from recent_state_summarizer.fetch.hatena_bookmark import fetch_hatena_bookmark_rss
from recent_state_summarizer.fetch.qiita_advent_calendar import fetch_qiita_advent_calendar
from recent_state_summarizer.fetch.adventar import TitleTag, fetch_adventar_calendar
from recent_state_summarizer.fetch.hatena_blog import _fetch_titles

logger = logging.getLogger(__name__)


def _main(
    url: str, save_path: str | Path, *, save_as_title_list: bool
) -> None:
    fetcher = get_fetcher(url)
    title_tags = fetcher(url)
    if save_as_title_list:
        contents = _as_bullet_list(
            title_tag["title"] for title_tag in title_tags
        )
    else:
        contents = _as_json(title_tags)
    _save(save_path, contents)


def _as_bullet_list(titles: Iterable[str]) -> str:
    return "\n".join(f"- {title}" for title in titles)


def _as_json(title_tags: Iterable[TitleTag]) -> str:
    return "\n".join(
        json.dumps(title_tag, ensure_ascii=False) for title_tag in title_tags
    )


def _save(path: str | Path, contents: str) -> None:
    with open(path, "w", encoding="utf8", newline="") as f:
        f.write(contents)


def _build_support_list() -> str:
    names = get_registered_names()
    return "\n".join(f"        - {name}" for name in names)


def build_parser(add_help: bool = True) -> argparse.ArgumentParser:
    help_message = f"""
    Retrieve the titles and URLs of articles from a web page specified by URL
    and save them as JSON Lines format.

    Support:
{_build_support_list()}

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
