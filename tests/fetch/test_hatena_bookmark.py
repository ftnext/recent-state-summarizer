import httpx
import respx

from recent_state_summarizer.fetch import fetch_hatena_bookmark_rss


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
