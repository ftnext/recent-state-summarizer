import httpx
import respx

from recent_state_summarizer.fetch.cli import _main

EVENT_URL = "https://qiita.com/official-events/bd14d28b53326d318fec"


def build_html_response(items, next_page):
    articles = ",".join(f"""{{
              "title": "{title}",
              "linkUrl": "{url}"
            }}""" for title, url in items)
    return f"""\
<!DOCTYPE html>
<html>
<body>
<script type="application/json" data-component-name="PostingCampaignDetailPage">
{{
  "postingCampaign": {{
    "paginatedPostingCampaignArticles": {{
      "items": [{articles}],
      "pageData": {{"nextPage": {next_page}}}
    }}
  }}
}}
</script>
</body>
</html>"""


@respx.mock
def test_fetch_qiita_official_event_as_bullet_list(tmp_path):
    respx.get(EVENT_URL, params={"page": 1}).mock(
        return_value=httpx.Response(
            status_code=200,
            text=build_html_response(
                [
                    (
                        "さくらのAI Engineを試す",
                        "https://qiita.com/user1/items/abc123",
                    )
                ],
                next_page="null",
            ),
        )
    )

    _main(EVENT_URL, tmp_path / "titles.txt", save_as_title_list=True)

    expected = "- さくらのAI Engineを試す"
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_qiita_official_event_as_json(tmp_path):
    respx.get(EVENT_URL, params={"page": 1}).mock(
        return_value=httpx.Response(
            status_code=200,
            text=build_html_response(
                [
                    (
                        "さくらのAI Engineを試す",
                        "https://qiita.com/user1/items/abc123",
                    )
                ],
                next_page="null",
            ),
        )
    )

    _main(EVENT_URL, tmp_path / "titles.jsonl", save_as_title_list=False)

    expected = (
        '{"title": "さくらのAI Engineを試す", '
        '"url": "https://qiita.com/user1/items/abc123"}'
    )
    assert (tmp_path / "titles.jsonl").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_qiita_official_event_follows_pagination(tmp_path):
    respx.get(EVENT_URL, params={"page": 1}).mock(
        return_value=httpx.Response(
            status_code=200,
            text=build_html_response(
                [("1ページ目の記事", "https://qiita.com/user1/items/abc123")],
                next_page="2",
            ),
        )
    )
    respx.get(EVENT_URL, params={"page": 2}).mock(
        return_value=httpx.Response(
            status_code=200,
            text=build_html_response(
                [("2ページ目の記事", "https://qiita.com/user2/items/def456")],
                next_page="null",
            ),
        )
    )

    _main(EVENT_URL, tmp_path / "titles.txt", save_as_title_list=True)

    expected = """\
- 1ページ目の記事
- 2ページ目の記事"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_qiita_official_event_with_fragment(tmp_path):
    respx.get(EVENT_URL, params={"page": 1}).mock(
        return_value=httpx.Response(
            status_code=200,
            text=build_html_response(
                [
                    (
                        "さくらのAI Engineを試す",
                        "https://qiita.com/user1/items/abc123",
                    )
                ],
                next_page="null",
            ),
        )
    )

    _main(
        f"{EVENT_URL}#posted-articles",
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = "- さくらのAI Engineを試す"
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected
