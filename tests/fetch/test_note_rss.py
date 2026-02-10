import httpx
import respx

from recent_state_summarizer.fetch.note_rss import fetch_note_rss


class TestNoteRSS:
    @respx.mock
    def test_fetch_note_rss(self):
        rss_feed = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>ftnext｜note</title>
    <link>https://note.com/ftnext</link>
    <description>ftnextさんの最近の記事</description>
    <item>
      <title>noteの記事タイトル1</title>
      <link>https://note.com/ftnext/n/n1234567890ab</link>
      <description>記事の説明1</description>
    </item>
    <item>
      <title>noteの記事タイトル2</title>
      <link>https://note.com/ftnext/n/ncdef01234567</link>
      <description>記事の説明2</description>
    </item>
  </channel>
</rss>"""
        respx.get("https://note.com/ftnext/rss").mock(
            return_value=httpx.Response(
                status_code=200,
                content=rss_feed.encode("utf-8"),
                headers={"content-type": "application/xml"},
            )
        )

        result = list(fetch_note_rss("https://note.com/ftnext/rss"))

        assert len(result) == 2
        assert result[0]["title"] == "noteの記事タイトル1"
        assert result[0]["url"] == "https://note.com/ftnext/n/n1234567890ab"
        assert result[1]["title"] == "noteの記事タイトル2"
        assert result[1]["url"] == "https://note.com/ftnext/n/ncdef01234567"
