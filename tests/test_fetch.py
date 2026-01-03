from unittest.mock import patch

import httpx
import respx

from recent_state_summarizer.fetch import (
    URLType,
    _detect_url_type,
    cli,
    fetch_hatena_bookmark_rss,
)


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


class TestHatenaBookmarkRSS:
    @respx.mock
    def test_fetch_hatena_bookmark_rss(self):
        rss_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>はてなブックマーク - IT</title>
    <link>https://b.hatena.ne.jp/entrylist/it</link>
    <item>
      <title>Sample Article 1</title>
      <link>https://example.com/article1</link>
      <description>This is a sample article description 1</description>
    </item>
    <item>
      <title>Sample Article 2</title>
      <link>https://example.com/article2</link>
      <description>This is a sample article description 2</description>
    </item>
  </channel>
</rss>"""
        respx.get("https://b.hatena.ne.jp/entrylist/it.rss").mock(
            return_value=httpx.Response(
                status_code=200,
                content=rss_feed.encode("utf-8"),
                headers={"content-type": "application/xml"},
            )
        )

        result = list(
            fetch_hatena_bookmark_rss(
                "https://b.hatena.ne.jp/entrylist/it.rss"
            )
        )

        assert len(result) == 2
        assert result[0]["title"] == "Sample Article 1"
        assert result[0]["url"] == "https://example.com/article1"
        assert (
            result[0]["description"]
            == "This is a sample article description 1"
        )
        assert result[1]["title"] == "Sample Article 2"
        assert result[1]["url"] == "https://example.com/article2"
        assert (
            result[1]["description"]
            == "This is a sample article description 2"
        )


class TestDetectUrlType:
    def test_hatena_bookmark_rss(self):
        url = "https://b.hatena.ne.jp/entrylist/it.rss"
        assert _detect_url_type(url) == URLType.HATENA_BOOKMARK_RSS

    def test_hatena_blog_hatenablog_com(self):
        url = "https://example.hatenablog.com/archive/2023"
        assert _detect_url_type(url) == URLType.HATENA_BLOG

    def test_hatena_blog_hateblo_jp(self):
        url = "https://example.hateblo.jp/archive/2023"
        assert _detect_url_type(url) == URLType.HATENA_BLOG

    def test_unknown_url(self):
        url = "https://example.com/blog"
        assert _detect_url_type(url) == URLType.UNKNOWN
