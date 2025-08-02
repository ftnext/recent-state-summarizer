from textwrap import dedent

from recent_state_summarizer.fetch import _main


def test_fetch_as_bullet_list(httpserver, tmp_path):
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

    _main(
        httpserver.url_for("/archive/2025/06"),
        tmp_path / "titles.txt",
        save_as_json=False,
    )

    expected = """\
- Title 3
- Title 2
- Title 1"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected
