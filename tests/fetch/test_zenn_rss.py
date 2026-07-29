import httpx
import respx

from recent_state_summarizer.fetch.zenn_rss import fetch_zenn_rss


class TestZennRSS:
    @respx.mock
    def test_fetch_zenn_rss(self):
        rss_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>nikkieさんのフィード</title>
    <description>Zennのnikkieさん（@ftnext）のRSSフィードです</description>
    <link>https://zenn.dev/ftnext</link>
    <generator>zenn.dev</generator>
    <lastBuildDate>Sun, 18 Jan 2026 02:11:47 GMT</lastBuildDate>
    <atom:link href="https://zenn.dev/ftnext/feed" rel="self" type="application/rss+xml"/>
    <language>ja</language>
    <item>
      <title>Zennの記事タイトル1</title>
      <description>記事1です...</description>
      <link>https://zenn.dev/ftnext/articles/abc123</link>
      <guid isPermaLink="true">https://zenn.dev/ftnext/articles/abc123</guid>
      <pubDate>Thu, 18 Dec 2025 23:44:21 GMT</pubDate>
      <dc:creator>nikkie</dc:creator>
    </item>
    <item>
      <title>Zennの記事タイトル2</title>
      <description>記事2です...</description>
      <link>https://zenn.dev/ftnext/articles/def456</link>
      <guid isPermaLink="true">https://zenn.dev/ftnext/articles/def456</guid>
      <pubDate>Thu, 18 Nov 2025 14:09:57 GMT</pubDate>
      <dc:creator>nikkie</dc:creator>
    </item>
  </channel>
</rss>"""
        respx.get("https://zenn.dev/ftnext/feed", params={"all": "1"}).mock(
            return_value=httpx.Response(
                status_code=200,
                content=rss_feed.encode("utf-8"),
                headers={"content-type": "application/rss+xml"},
            )
        )

        result = list(fetch_zenn_rss("https://zenn.dev/ftnext/feed?all=1"))

        assert len(result) == 2
        assert result[0]["title"] == "Zennの記事タイトル1"
        assert result[0]["url"] == "https://zenn.dev/ftnext/articles/abc123"
        assert result[1]["title"] == "Zennの記事タイトル2"
        assert result[1]["url"] == "https://zenn.dev/ftnext/articles/def456"
