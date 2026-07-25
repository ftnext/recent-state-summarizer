import json
from collections.abc import Generator
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag


def _match_qiita_official_event(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == "qiita.com" and parsed.path.startswith(
        "/official-events/"
    )


@register_fetcher(
    name="Qiita Official Event",
    matcher=_match_qiita_official_event,
)
def fetch_qiita_official_event(url: str) -> Generator[TitleTag, None, None]:
    """Fetch article titles and URLs from Qiita official event.

    Args:
        url: Qiita official event URL (e.g., https://qiita.com/official-events/bd14d28b53326d318fec)

    Yields:
        TitleTag dictionaries containing title and url
    """
    page = 1
    while page:
        response = httpx.get(url, params={"page": page})
        response.raise_for_status()

        paginated_articles = _parse_paginated_articles(response.text)
        if paginated_articles is None:
            return

        for item in paginated_articles["items"]:
            yield {"title": item["title"], "url": item["linkUrl"]}

        page = paginated_articles["pageData"]["nextPage"]


def _parse_paginated_articles(raw_html: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(raw_html, "html.parser")
    script_tag = soup.find(
        "script",
        attrs={"data-component-name": "PostingCampaignDetailPage"},
    )
    if not script_tag or not script_tag.string:
        return None

    data = json.loads(script_tag.string)
    return data["postingCampaign"]["paginatedPostingCampaignArticles"]
