import respx
from httpx import Response

from recent_state_summarizer.fetch import _main


@respx.mock
def test_fetch_as_bullet_list(tmp_path):
    base_url = "https://example.com"

    respx.get(f"{base_url}/archive/2025/06").mock(
        return_value=Response(
            200,
            text=f"""\
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
                  <a class="entry-title-link" href="{base_url}/archive/2025/06/03">Title 3</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{base_url}/archive/2025/06/02">Title 2</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{base_url}/archive/2025/06/01">Title 1</a>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>""",
        )
    )

    _main(
        f"{base_url}/archive/2025/06",
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = """\
- Title 3
- Title 2
- Title 1"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_as_json(tmp_path):
    base_url = "https://example.com"

    respx.get(f"{base_url}/archive/2025/06").mock(
        return_value=Response(
            200,
            text=f"""\
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
                  <a class="entry-title-link" href="{base_url}/archive/2025/06/03">Title 3</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{base_url}/archive/2025/06/02">Title 2</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{base_url}/archive/2025/06/01">Title 1</a>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>""",
        )
    )

    _main(
        f"{base_url}/archive/2025/06",
        tmp_path / "titles.jsonl",
        save_as_title_list=False,
    )

    expected = f"""\
{{"title": "Title 3", "url": "{base_url}/archive/2025/06/03"}}
{{"title": "Title 2", "url": "{base_url}/archive/2025/06/02"}}
{{"title": "Title 1", "url": "{base_url}/archive/2025/06/01"}}"""
    assert (tmp_path / "titles.jsonl").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_multiple_archive_page(tmp_path):
    base_url = "https://example.com"

    respx.get(f"{base_url}/archive/2025/07", params="page=2").mock(
        return_value=Response(
            200,
            text=f"""\
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
                  <a class="entry-title-link" href="{base_url}/archive/2025/07/01">Title 1</a>
                </section>
              </div>
              <div class="pager">
                <span class="pager-prev">
                  <a href="{base_url}/archive/2025/07" class="test-pager-prev" rel="prev">前のページ</a>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>""",
        )
    )

    respx.get(f"{base_url}/archive/2025/07").mock(
        return_value=Response(
            200,
            text=f"""\
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
                  <a class="entry-title-link" href="{base_url}/archive/2025/07/03">Title 3</a>
                </section>
                <section class="archive-entry">
                  <a class="entry-title-link" href="{base_url}/archive/2025/07/02">Title 2</a>
                </section>
              </div>
            </div>
            <div class="pager">
              <span class="pager-next">
                <a href="{base_url}/archive/2025/07?page=2" class="test-pager-next" rel="next">次のページ</a>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>""",
        )
    )

    _main(
        f"{base_url}/archive/2025/07",
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = """- Title 3
- Title 2
- Title 1"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected
