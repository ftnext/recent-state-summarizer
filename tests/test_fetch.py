from textwrap import dedent

import pytest

from recent_state_summarizer.fetch import _main


@pytest.fixture
def blog_server(httpserver):
    httpserver.expect_request("/archive/2025/06").respond_with_data(
        dedent(
            f"""
        <!DOCTYPE html>
        <html>
          <head><title>Archive</title></head>
          <body>
            <h1>Archive</h1>
            <div id="content">
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
          </body>
        </html>
        """
        )
    )
    return httpserver


def test_fetch_as_bullet_list(blog_server, tmp_path):
    _main(
        blog_server.url_for("/archive/2025/06"),
        tmp_path / "titles.txt",
        save_as_json=False,
    )

    expected = """\
- Title 3
- Title 2
- Title 1"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


def test_fetch_as_json(blog_server, tmp_path):
    _main(
        blog_server.url_for("/archive/2025/06"),
        tmp_path / "titles.json",
        save_as_json=True,
    )

    expected = f"""\
{{"title": "Title 3", "url": "{blog_server.url_for('/archive/2025/06/03')}"}}
{{"title": "Title 2", "url": "{blog_server.url_for('/archive/2025/06/02')}"}}
{{"title": "Title 1", "url": "{blog_server.url_for('/archive/2025/06/01')}"}}"""
    assert (tmp_path / "titles.json").read_text(encoding="utf8") == expected
