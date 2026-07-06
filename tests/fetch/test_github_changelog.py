import httpx
import respx

from recent_state_summarizer.fetch.github_changelog import (
    fetch_github_changelog,
)


class TestGitHubChangelog:
    @respx.mock
    def test_fetch_github_changelog(self):
        rss_feed = """\
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
  <item>
    <title>Changelog entry 1</title>
    <link>https://github.blog/changelog/2026-07-01-entry-1/</link>
    <dc:creator><![CDATA[Author 1]]></dc:creator>
    <description><![CDATA[<p>Description 1</p>]]></description>
    <content:encoded><![CDATA[<p>Content 1</p>]]></content:encoded>
  </item>
  <item>
    <title>Changelog entry 2</title>
    <link>https://github.blog/changelog/2026-07-02-entry-2/</link>
    <dc:creator><![CDATA[Author 2]]></dc:creator>
    <description><![CDATA[<p>Description 2</p>]]></description>
    <content:encoded><![CDATA[<p>Content 2</p>]]></content:encoded>
  </item>
</channel>
</rss>"""
        respx.get("https://github.blog/changelog/feed/").mock(
            return_value=httpx.Response(
                status_code=200,
                content=rss_feed.encode("utf-8"),
                headers={"content-type": "application/rss+xml"},
            )
        )

        result = list(
            fetch_github_changelog("https://github.blog/changelog/feed/")
        )

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
