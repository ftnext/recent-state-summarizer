from collections.abc import Generator
from urllib.parse import urlparse

import httpx

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag


def _match_qiita_api(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == "qiita.com" and "/api/v2/users/" in parsed.path


@register_fetcher(
    name="Qiita API v2",
    matcher=_match_qiita_api,
    example="https://qiita.com/api/v2/users/user/items",
)
def fetch_qiita_api(url: str) -> Generator[TitleTag, None, None]:
    response = httpx.get(url, params={"per_page": 20})
    response.raise_for_status()

    items = response.json()

    for item in items:
        yield {"title": item["title"], "url": item["url"]}
