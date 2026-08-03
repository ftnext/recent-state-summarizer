from datetime import datetime, timezone

import httpx
import pytest
import respx

from recent_state_summarizer.fetch import github_changelog
from recent_state_summarizer.fetch.github_changelog import (
    fetch_github_changelog,
)

FEED_URL = "https://github.blog/changelog/feed/"
CUTOFF = datetime(2026, 7, 4, tzinfo=timezone.utc)


def build_item(title, link, published):
    return f"""\
  <item>
    <title>{title}</title>
    <link>{link}</link>
    <pubDate>{published}</pubDate>
    <dc:creator><![CDATA[Author]]></dc:creator>
    <description><![CDATA[<p>Description</p>]]></description>
  </item>"""


def build_rss_feed(items):
    entries = "\n".join(build_item(*item) for item in items)
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:atom="http://www.w3.org/2005/Atom"
>
<channel>
  <title>The GitHub Blog: GitHub Changelog</title>
  <link>https://github.blog/changelog</link>
  <description>Subscribe to Changelog</description>
{entries}
</channel>
</rss>"""


def mock_feed_page(page, items):
    return respx.get(FEED_URL, params={"paged": page}).mock(
        return_value=httpx.Response(
            status_code=200,
            content=build_rss_feed(items).encode("utf-8"),
            headers={"content-type": "application/rss+xml"},
        )
    )


def mock_feed_page_not_found(page):
    return respx.get(FEED_URL, params={"paged": page}).mock(
        return_value=httpx.Response(status_code=404)
    )


@pytest.fixture
def fixed_cutoff(monkeypatch):
    monkeypatch.setattr(github_changelog, "_recent_cutoff", lambda: CUTOFF)


class TestGitHubChangelog:
    @respx.mock
    def test_fetch_github_changelog(self, fixed_cutoff):
        mock_feed_page(
            1,
            [
                (
                    "Changelog entry 1",
                    "https://github.blog/changelog/2026-07-01-entry-1/",
                    "Wed, 29 Jul 2026 14:01:07 +0000",
                ),
                (
                    "Changelog entry 2",
                    "https://github.blog/changelog/2026-07-02-entry-2/",
                    "Mon, 27 Jul 2026 17:00:35 +0000",
                ),
            ],
        )
        mock_feed_page_not_found(2)

        result = list(fetch_github_changelog(FEED_URL))

        assert len(result) == 2
        assert result[0]["title"] == "Changelog entry 1"
        assert (
            result[0]["url"]
            == "https://github.blog/changelog/2026-07-01-entry-1/"
        )
        assert result[1]["title"] == "Changelog entry 2"
        assert (
            result[1]["url"]
            == "https://github.blog/changelog/2026-07-02-entry-2/"
        )

    @respx.mock
    def test_follows_pagination(self, fixed_cutoff):
        mock_feed_page(
            1,
            [
                (
                    "1ページ目の記事",
                    "https://github.blog/changelog/2026-07-29-page-1/",
                    "Wed, 29 Jul 2026 14:01:07 +0000",
                )
            ],
        )
        mock_feed_page(
            2,
            [
                (
                    "2ページ目の記事",
                    "https://github.blog/changelog/2026-07-20-page-2/",
                    "Mon, 20 Jul 2026 18:24:14 +0000",
                )
            ],
        )
        mock_feed_page_not_found(3)

        result = list(fetch_github_changelog(FEED_URL))

        assert [title_tag["title"] for title_tag in result] == [
            "1ページ目の記事",
            "2ページ目の記事",
        ]

    @respx.mock
    def test_stops_at_entry_older_than_cutoff(self, fixed_cutoff):
        mock_feed_page(
            1,
            [
                (
                    "直近の記事",
                    "https://github.blog/changelog/2026-07-29-recent/",
                    "Wed, 29 Jul 2026 14:01:07 +0000",
                )
            ],
        )
        mock_feed_page(
            2,
            [
                (
                    "カットオフ内の記事",
                    "https://github.blog/changelog/2026-07-07-in-window/",
                    "Tue, 07 Jul 2026 17:09:29 +0000",
                ),
                (
                    "カットオフより古い記事",
                    "https://github.blog/changelog/2026-07-02-too-old/",
                    "Thu, 02 Jul 2026 08:17:17 +0000",
                ),
            ],
        )
        third_page = mock_feed_page(3, [])

        result = list(fetch_github_changelog(FEED_URL))

        assert [title_tag["title"] for title_tag in result] == [
            "直近の記事",
            "カットオフ内の記事",
        ]
        assert not third_page.called

    @respx.mock
    def test_stops_at_empty_page(self, fixed_cutoff):
        mock_feed_page(
            1,
            [
                (
                    "直近の記事",
                    "https://github.blog/changelog/2026-07-29-recent/",
                    "Wed, 29 Jul 2026 14:01:07 +0000",
                )
            ],
        )
        mock_feed_page(2, [])
        third_page = mock_feed_page(3, [])

        result = list(fetch_github_changelog(FEED_URL))

        assert [title_tag["title"] for title_tag in result] == ["直近の記事"]
        assert not third_page.called

    @respx.mock
    def test_follows_redirect_to_canonical_url(self, fixed_cutoff):
        respx.get(FEED_URL, params={"paged": 1}).mock(
            return_value=httpx.Response(
                status_code=301, headers={"location": FEED_URL}
            )
        )
        mock_feed_page_not_found(2)
        respx.get(FEED_URL).mock(
            return_value=httpx.Response(
                status_code=200,
                content=build_rss_feed(
                    [
                        (
                            "リダイレクト先の記事",
                            "https://github.blog/changelog/2026-07-29-entry/",
                            "Wed, 29 Jul 2026 14:01:07 +0000",
                        )
                    ]
                ).encode("utf-8"),
                headers={"content-type": "application/rss+xml"},
            )
        )

        result = list(fetch_github_changelog(FEED_URL))

        assert [title_tag["title"] for title_tag in result] == [
            "リダイレクト先の記事"
        ]
