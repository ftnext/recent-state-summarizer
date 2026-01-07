import httpx
import respx

from recent_state_summarizer.fetch import _main


@respx.mock
def test_fetch_qiita_advent_calendar_as_bullet_list(tmp_path):
    html_response = """\
<!DOCTYPE html>
<html>
<head>
<script id="js-react-on-rails-context" type="application/json">
{
  "advencalApp": {
    "calendar": {
      "items": [
        {
          "date": 1,
          "article": {
            "title": "Python型ヒントの基礎",
            "url": "https://qiita.com/user1/items/abc123"
          }
        },
        {
          "date": 2,
          "article": {
            "title": "Genericsを使いこなす",
            "url": "https://qiita.com/user2/items/def456"
          }
        },
        {
          "date": 3,
          "comment": "記事なし"
        }
      ]
    }
  }
}
</script>
</head>
<body>
</body>
</html>"""
    respx.get(
        "https://qiita.com/advent-calendar/2025/python-type-hints"
    ).mock(
        return_value=httpx.Response(
            status_code=200,
            text=html_response,
        )
    )

    _main(
        "https://qiita.com/advent-calendar/2025/python-type-hints",
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = """\
- Python型ヒントの基礎
- Genericsを使いこなす"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_qiita_advent_calendar_as_json(tmp_path):
    html_response = """\
<!DOCTYPE html>
<html>
<head>
<script id="js-react-on-rails-context" type="application/json">
{
  "advencalApp": {
    "calendar": {
      "items": [
        {
          "date": 1,
          "article": {
            "title": "Python型ヒントの基礎",
            "url": "https://qiita.com/user1/items/abc123"
          }
        },
        {
          "date": 2,
          "article": {
            "title": "Genericsを使いこなす",
            "url": "https://qiita.com/user2/items/def456"
          }
        },
        {
          "date": 3,
          "comment": "記事なし"
        }
      ]
    }
  }
}
</script>
</head>
<body>
</body>
</html>"""
    respx.get(
        "https://qiita.com/advent-calendar/2025/python-type-hints"
    ).mock(
        return_value=httpx.Response(
            status_code=200,
            text=html_response,
        )
    )

    _main(
        "https://qiita.com/advent-calendar/2025/python-type-hints",
        tmp_path / "titles.jsonl",
        save_as_title_list=False,
    )

    expected = """\
{"title": "Python型ヒントの基礎", "url": "https://qiita.com/user1/items/abc123"}
{"title": "Genericsを使いこなす", "url": "https://qiita.com/user2/items/def456"}"""
    assert (tmp_path / "titles.jsonl").read_text(encoding="utf8") == expected
