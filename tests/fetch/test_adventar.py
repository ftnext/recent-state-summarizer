import pytest

from recent_state_summarizer.fetch import _main


@pytest.fixture
def adventar_server(httpserver):
    httpserver.expect_request("/calendars/11474").respond_with_data(
        f"""\
<!DOCTYPE html>
<html>
<body>
<ul class="EntryList">
  <li class="item">
    <div class="head">
      <div class="date">12/2</div>
    </div>
    <div class="comment">アニメを見続ける技術</div>
    <div class="article">
      <div class="left">
        <div class="link">
          <a href="{httpserver.url_for('/article1')}">https://example.com/article1</a>
        </div>
        <div>アニメを見続ける技術 あるいは 習慣化について｜こうの</div>
      </div>
    </div>
  </li>
  <li class="item">
    <div class="head">
      <div class="date">12/3</div>
    </div>
    <div class="comment">崎山香織は諦めない</div>
    <div class="article">
      <div class="left">
        <div class="link">
          <a href="{httpserver.url_for('/article2')}">https://example.com/article2</a>
        </div>
        <div>崎山香織は諦めない~決して勝てぬ者こそが届く高み｜keita</div>
      </div>
    </div>
  </li>
  <li class="item">
    <div class="head">
      <div class="date">12/4</div>
    </div>
    <div class="comment">記事なし</div>
  </li>
</ul>
</body>
</html>"""
    )
    return httpserver


def test_fetch_adventar_as_bullet_list(adventar_server, tmp_path):
    _main(
        adventar_server.url_for("/calendars/11474"),
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = """\
- アニメを見続ける技術 あるいは 習慣化について｜こうの
- 崎山香織は諦めない~決して勝てぬ者こそが届く高み｜keita"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


def test_fetch_adventar_as_json(adventar_server, tmp_path):
    _main(
        adventar_server.url_for("/calendars/11474"),
        tmp_path / "titles.jsonl",
        save_as_title_list=False,
    )

    expected = f"""\
{{"title": "アニメを見続ける技術 あるいは 習慣化について｜こうの", "url": "{adventar_server.url_for('/article1')}"}}
{{"title": "崎山香織は諦めない~決して勝てぬ者こそが届く高み｜keita", "url": "{adventar_server.url_for('/article2')}"}}"""
    assert (tmp_path / "titles.jsonl").read_text(encoding="utf8") == expected
