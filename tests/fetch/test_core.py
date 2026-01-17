from unittest.mock import patch

import pytest

from recent_state_summarizer.fetch import cli
from recent_state_summarizer.fetch.adventar import fetch_adventar_calendar
from recent_state_summarizer.fetch.hatena_blog import _fetch_titles
from recent_state_summarizer.fetch.hatena_bookmark import (
    fetch_hatena_bookmark_rss,
)
from recent_state_summarizer.fetch.qiita_advent_calendar import (
    fetch_qiita_advent_calendar,
)
from recent_state_summarizer.fetch.qiita_rss import fetch_qiita_rss
from recent_state_summarizer.fetch.registry import get_fetcher


@patch("recent_state_summarizer.fetch._main")
class TestCli:
    def test_default_as_json(self, fetch_main, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            [
                "recent_state_summarizer.fetch",
                "https://example.com",
                "output.jsonl",
            ],
        )

        cli()

        fetch_main.assert_called_once_with(
            "https://example.com", "output.jsonl", save_as_title_list=False
        )

    def test_as_title_list(self, fetch_main, monkeypatch):
        monkeypatch.setattr(
            "sys.argv",
            [
                "recent_state_summarizer.fetch",
                "https://example.com",
                "output.txt",
                "--as-title-list",
            ],
        )

        cli()

        fetch_main.assert_called_once_with(
            "https://example.com", "output.txt", save_as_title_list=True
        )


class TestGetFetcher:
    def test_hatena_bookmark_rss(self):
        url = "https://b.hatena.ne.jp/entrylist/it.rss"
        assert get_fetcher(url) == fetch_hatena_bookmark_rss

    def test_hatena_blog_hatenablog_com(self):
        url = "https://example.hatenablog.com/archive/2023"
        assert get_fetcher(url) == _fetch_titles

    def test_hatena_blog_hateblo_jp(self):
        url = "https://example.hateblo.jp/archive/2023"
        assert get_fetcher(url) == _fetch_titles

    def test_adventar(self):
        url = "https://adventar.org/calendars/12345"
        assert get_fetcher(url) == fetch_adventar_calendar

    def test_qiita_advent_calendar(self):
        url = "https://qiita.com/advent-calendar/2025/python"
        assert get_fetcher(url) == fetch_qiita_advent_calendar

    def test_qiita_rss(self):
        url = "https://qiita.com/ftnext/feed.atom"
        assert get_fetcher(url) == fetch_qiita_rss

    def test_unknown_url_raises(self):
        url = "https://example.com/blog"
        with pytest.raises(ValueError, match="Unsupported URL"):
            get_fetcher(url)
