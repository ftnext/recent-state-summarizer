import httpx
import respx

from recent_state_summarizer.fetch.qiita_rss import fetch_qiita_rss


class TestQiitaRSS:
    @respx.mock
    def test_fetch_qiita_rss(self):
        atom_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>ftnext の記事</title>
  <link rel="alternate" href="https://qiita.com/ftnext"/>
  <id>https://qiita.com/ftnext/feed.atom</id>
  <updated>2025-01-15T12:00:00Z</updated>
  <entry>
    <title>Sample Qiita Article 1</title>
    <link rel="alternate" href="https://qiita.com/ftnext/items/abc123"/>
    <id>https://qiita.com/ftnext/items/abc123</id>
    <published>2025-01-15T12:00:00Z</published>
    <updated>2025-01-15T12:00:00Z</updated>
  </entry>
  <entry>
    <title>Sample Qiita Article 2</title>
    <link rel="alternate" href="https://qiita.com/ftnext/items/def456"/>
    <id>https://qiita.com/ftnext/items/def456</id>
    <published>2025-01-14T10:00:00Z</published>
    <updated>2025-01-14T10:00:00Z</updated>
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
