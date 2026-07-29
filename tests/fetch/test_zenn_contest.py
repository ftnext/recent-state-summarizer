import json

import httpx
import respx

from recent_state_summarizer.fetch.cli import _main

CONTEST_URL = "https://zenn.dev/contests/splunk-opentelemetry-2026"
ARTICLES_API_URL = "https://zenn.dev/api/articles"
CONTEST_SLUG = "splunk-opentelemetry-2026"


def build_api_response(articles, next_page):
    return json.dumps(
        {
            "articles": [
                {"title": title, "path": path} for title, path in articles
            ],
            "next_page": next_page,
            "total_count": None,
        }
    )


def mock_api_page(page, articles, next_page):
    respx.get(
        ARTICLES_API_URL,
        params={
            "contest_slug": CONTEST_SLUG,
            "order": "latest",
            "page": page,
        },
    ).mock(
        return_value=httpx.Response(
            status_code=200,
            text=build_api_response(articles, next_page),
            headers={"content-type": "application/json"},
        )
    )


@respx.mock
def test_fetch_zenn_contest_as_bullet_list(tmp_path):
    mock_api_page(
        1,
        [("OpenTelemetry入門", "/user1/articles/abc123")],
        next_page=None,
    )

    _main(CONTEST_URL, tmp_path / "titles.txt", save_as_title_list=True)

    expected = "- OpenTelemetry入門"
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_zenn_contest_as_json(tmp_path):
    mock_api_page(
        1,
        [("OpenTelemetry入門", "/user1/articles/abc123")],
        next_page=None,
    )

    _main(CONTEST_URL, tmp_path / "titles.jsonl", save_as_title_list=False)

    expected = (
        '{"title": "OpenTelemetry入門", '
        '"url": "https://zenn.dev/user1/articles/abc123"}'
    )
    assert (tmp_path / "titles.jsonl").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_zenn_contest_follows_pagination(tmp_path):
    mock_api_page(
        1, [("1ページ目の記事", "/user1/articles/abc123")], next_page=2
    )
    mock_api_page(
        2, [("2ページ目の記事", "/user2/articles/def456")], next_page=None
    )

    _main(CONTEST_URL, tmp_path / "titles.txt", save_as_title_list=True)

    expected = """\
- 1ページ目の記事
- 2ページ目の記事"""
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected


@respx.mock
def test_fetch_zenn_contest_with_tab_query(tmp_path):
    mock_api_page(
        1,
        [("OpenTelemetry入門", "/user1/articles/abc123")],
        next_page=None,
    )

    _main(
        f"{CONTEST_URL}?tab=articles",
        tmp_path / "titles.txt",
        save_as_title_list=True,
    )

    expected = "- OpenTelemetry入門"
    assert (tmp_path / "titles.txt").read_text(encoding="utf8") == expected
