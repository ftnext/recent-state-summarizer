from unittest.mock import patch

import pytest
import responses

from recent_state_summarizer.fetch import _main, cli, fetch_hatena_bookmark_rss


@pytest.fixture
def blog_server(httpserver):
    httpserver.expect_request("/archive/2025/06").respond_with_data(
        f"""\
<!DOCTYPE html>
<html>
  <head><title>Archive</title></head>
  <body>
    <h1>Archive</h1>
    <div id="content">
      <div id="content-inner">
        <div id="wrapper">
          <div id="main">
            <div id="main-inner">
              <div class="archive-entries">
                <section class="archive-entry">
                  <a class="entry-title-link" href="{httpserver.url_for('/')}archive/2025/06/03">Title 3</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{httpserver.url_for('/')}archive/2025/06/02">Title 2</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{httpserver.url_for('/')}archive/2025/06/01">Title 1</a>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>"""
    )
    return httpserver


def test_fetch_as_bullet_list(blog_server, tmp_path):
    _main(
        blog_server.url_for("/archive/2025/06"),
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = """\
- Title 3
- Title 2
- Title 1"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


def test_fetch_as_json(blog_server, tmp_path):
    _main(
        blog_server.url_for("/archive/2025/06"),
        tmp_path / "titles.jsonl",
        save_as_title_list=False,
    )

    expected = f"""\
{{"title": "Title 3", "url": "{blog_server.url_for('/archive/2025/06/03')}"}}
{{"title": "Title 2", "url": "{blog_server.url_for('/archive/2025/06/02')}"}}
{{"title": "Title 1", "url": "{blog_server.url_for('/archive/2025/06/01')}"}}"""
    assert (tmp_path / "titles.jsonl").read_text(encoding="utf8") == expected


@pytest.fixture
def multi_page_blog_server(httpserver):
    httpserver.expect_request(
        "/archive/2025/07", query_string="page=2"
    ).respond_with_data(
        f"""\
<!DOCTYPE html>
<html>
  <head><title>Archive (Page 2)</title></head>
  <body>
    <h1>Archive</h1>
    <div id="content">
      <div id="content-inner">
        <div id="wrapper">
          <div id="main">
            <div id="main-inner">
              <div class="archive-entries">
                <section class="archive-entry">
                  <a class="entry-title-link" href="{httpserver.url_for('/')}archive/2025/07/01">Title 1</a>
                </section>
              </div>
              <div class="pager">
                <span class="pager-prev">
                  <a href="{httpserver.url_for('/')}archive/2025/07" class="test-pager-prev" rel="prev">前のページ</a>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>"""
    )
    httpserver.expect_request("/archive/2025/07").respond_with_data(
        f"""\
<!DOCTYPE html>
<html>
  <head><title>Archive</title></head>
  <body>
    <h1>Archive</h1>
    <div id="content">
      <div id="content-inner">
        <div id="wrapper">
          <div id="main">
            <div id="main-inner">
              <div class="archive-entries">
                <section class="archive-entry">
                  <a class="entry-title-link" href="{httpserver.url_for('/')}archive/2025/07/03">Title 3</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{httpserver.url_for('/')}archive/2025/07/02">Title 2</a>
                </section>
              </div>
            </div>
            <div class="pager">
              <span class="pager-next">
                <a href="{httpserver.url_for('/')}archive/2025/07?page=2" class="test-pager-next" rel="next">次のページ</a>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>"""
    )
    return httpserver


def test_fetch_multiple_archive_page(multi_page_blog_server, tmp_path):
    _main(
        multi_page_blog_server.url_for("/archive/2025/07"),
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = """- Title 3
- Title 2
- Title 1"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


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
    @responses.activate
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
        responses.add(
            responses.GET,
            "https://b.hatena.ne.jp/entrylist/it.rss",
            body=rss_feed,
            status=200,
            content_type="application/xml",
        )

        result = fetch_hatena_bookmark_rss("https://b.hatena.ne.jp/entrylist/it.rss")

        assert len(result) == 2
        assert result[0]["title"] == "Sample Article 1"
        assert result[0]["url"] == "https://example.com/article1"
        assert result[0]["description"] == "This is a sample article description 1"
        assert result[1]["title"] == "Sample Article 2"
        assert result[1]["url"] == "https://example.com/article2"
        assert result[1]["description"] == "This is a sample article description 2"
