from pathlib import Path

import openai


def _main(titles_path: str | Path) -> str:
    titles = _read_titles(titles_path)
    return summarize_titles(titles)


def summarize_titles(titles: str) -> str:
    prompts = _build_prompts(titles)
    response = _complete_chat(prompts)
    return _parse_response(response)


def _build_prompts(titles: str):
    prompts = [
        {"role": "user", "content": _build_summarize_prompt_text(titles)}
    ]
    return prompts


def _build_summarize_prompt_text(titles_as_list: str) -> str:
    return f"""\
以下は同一人物が最近書いたブログ記事のタイトルの一覧です。
それを読み、この人物が最近何をやっているかを詳しく教えてください。
応答は文ごとに改行して区切ってください。

{titles_as_list}
"""


def _complete_chat(prompts):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=prompts, temperature=0.8
    )


def _parse_response(response) -> str:
    return response["choices"][0]["message"]["content"]


def _read_titles(titles_path: str | Path) -> str:
    with open(titles_path, encoding="utf8", newline="") as f:
        return f.read()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("titles_path")
    args = parser.parse_args()

    print(_main(args.titles_path))
