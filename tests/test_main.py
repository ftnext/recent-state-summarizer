import json
from unittest.mock import patch

import httpx
import responses
import respx

from recent_state_summarizer.__main__ import main, normalize_argv


@respx.mock
@responses.activate
def test_main_success_path(monkeypatch, capsys):
    html_response = """\
<!DOCTYPE html>
<html>
  <body>
    <div class="archive-entries">
      <section class="archive-entry">
        <a class="entry-title-link" href="https://nikkie-ftnext.hatenablog.com/entry/post1">Pythonのテストについて学ぶ</a>
      </section>
      <section class="archive-entry">
        <a class="entry-title-link" href="https://nikkie-ftnext.hatenablog.com/entry/post2">pytest入門</a>
      </section>
      <section class="archive-entry">
        <a class="entry-title-link" href="https://nikkie-ftnext.hatenablog.com/entry/post3">モックとフィクスチャの使い方</a>
      </section>
    </div>
  </body>
</html>"""
    respx.get("https://nikkie-ftnext.hatenablog.com/archive/2025").mock(
        return_value=httpx.Response(
            status_code=200,
            text=html_response,
        )
    )

    monkeypatch.setattr("openai.api_key", "sk-test-dummy-key-for-testing")

    monkeypatch.setattr(
        "sys.argv",
        ["omae-douyo", "https://nikkie-ftnext.hatenablog.com/archive/2025"],
    )

    expected_summary = """\
このユーザーは最近、Pythonのテストについて学習しています。
具体的には、pytestの入門やモック・フィクスチャの使い方について記事を書いています。
テストコードを書くスキルを向上させようとしていることが伺えます。"""

    responses.add(
        responses.POST,
        "https://api.openai.com/v1/chat/completions",
        json={
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": expected_summary,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        },
        status=200,
        headers={"Content-Type": "application/json"},
    )

    main()

    captured = capsys.readouterr()
    assert expected_summary in captured.out

    assert len(responses.calls) == 1
    api_call = responses.calls[0]
    assert api_call.request.url == "https://api.openai.com/v1/chat/completions"
    assert api_call.request.method == "POST"
    request_body = json.loads(api_call.request.body)
    assert (
        "- Pythonのテストについて学ぶ\n- pytest入門\n- モックとフィクスチャの使い方"
        in request_body["messages"][0]["content"]
    )


@patch("recent_state_summarizer.__main__.fetch_main")
def test_fetch_subcommand(fetch_main, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["omae-douyo", "fetch", "https://example.com", "articles.jsonl"],
    )

    main()

    fetch_main.assert_called_once_with(
        "https://example.com", "articles.jsonl", save_as_title_list=False
    )


class TestHelpMessage:
    def test_fetch_help(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["omae-douyo", "fetch", "--help"])
        assert normalize_argv() == ["omae-douyo", "fetch", "--help"]

    def test_run_help(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["omae-douyo", "run", "--help"])
        assert normalize_argv() == ["omae-douyo", "run", "--help"]

    def test_help_only(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["omae-douyo", "--help"])
        assert normalize_argv() == ["omae-douyo", "--help"]

    def test_command_only(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["omae-douyo"])
        assert normalize_argv() == ["omae-douyo", "--help"]
