import httpx
import respx

from recent_state_summarizer.fetch.qiita_rss import fetch_qiita_rss


class TestQiitaRSS:
    @respx.mock
    def test_fetch_qiita_rss(self):
        atom_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xml:lang="ja-JP" xmlns="http://www.w3.org/2005/Atom">
  <id>tag:qiita.com,2005:/ftnext/feed</id>
  <link rel="alternate" type="text/html" href="https://qiita.com"/>
  <link rel="self" type="application/atom+xml" href="https://qiita.com/ftnext/feed.atom"/>
  <title>ftnextの記事 - Qiita</title>
  <description>Qiitaでユーザーftnextによる最近の記事</description>
  <updated>2022-10-01T19:34:17+09:00</updated>
  <link>https://qiita.com/ftnext</link>
  <entry>
    <id>tag:qiita.com,2005:PublicArticle/1627276</id>
    <published>2025-01-14T10:00:00Z</published>
    <updated>2025-01-14T10:00:00Z</updated>
    <link rel="alternate" type="text/html" href="https://qiita.com/ftnext/items/abc123"/>
    <url>https://qiita.com/ftnext/items/abc123</url>
    <title>Sample Qiita Article 1</title>
    <content type="text">1行目
2行目...</content>
    <author>
      <name>ftnext</name>
    </author>
  </entry>
  <entry>
    <id>tag:qiita.com,2005:PublicArticle/1567368</id>
    <published>2022-10-01T19:34:17+09:00</published>
    <updated>2022-10-08T17:23:09+09:00</updated>
    <link rel="alternate" href="https://qiita.com/ftnext/items/def456"/>
    <url>https://qiita.com/ftnext/items/def456</url>
    <title>Sample Qiita Article 2</title>
    <content type="text">こんにちは
この記事は...</content>
  </entry>
</feed>"""
        respx.get("https://qiita.com/ftnext/feed.atom").mock(
            return_value=httpx.Response(
                status_code=200,
                content=atom_feed.encode("utf-8"),
                headers={"content-type": "application/atom+xml"},
            )
        )

        result = list(fetch_qiita_rss("https://qiita.com/ftnext/feed.atom"))

        assert len(result) == 2
        assert result[0]["title"] == "Sample Qiita Article 1"
        assert result[0]["url"] == "https://qiita.com/ftnext/items/abc123"
        assert result[1]["title"] == "Sample Qiita Article 2"
        assert result[1]["url"] == "https://qiita.com/ftnext/items/def456"
