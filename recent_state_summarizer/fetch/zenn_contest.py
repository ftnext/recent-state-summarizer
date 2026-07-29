from collections.abc import Generator
from urllib.parse import urljoin, urlparse

import httpx

from recent_state_summarizer.fetch.registry import register_fetcher
from recent_state_summarizer.fetch.types import TitleTag

ZENN_ORIGIN = "https://zenn.dev"
ZENN_ARTICLES_API_URL = f"{ZENN_ORIGIN}/api/articles"


def _match_zenn_contest(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc == "zenn.dev" and parsed.path.startswith("/contests/")


@register_fetcher(
    name="Zenn Contest (experimental)",
    matcher=_match_zenn_contest,
)
def fetch_zenn_contest(url: str) -> Generator[TitleTag, None, None]:
    """Fetch article titles and URLs submitted to a Zenn contest.

    Zenn provides no RSS feed for contests, so this fetcher depends on the
    undocumented JSON API which Zenn may change without notice.

    Args:
        url: Zenn contest URL (e.g., https://zenn.dev/contests/example-2026)

    Yields:
        TitleTag dictionaries containing title and url
    """
    contest_slug = _extract_contest_slug(url)

    page = 1
    while page:
        response = httpx.get(
            ZENN_ARTICLES_API_URL,
            params={
                "contest_slug": contest_slug,
                "order": "latest",
                "page": page,
            },
        )
        response.raise_for_status()

        paginated_articles = response.json()

        for article in paginated_articles["articles"]:
            yield {
                "title": article["title"],
                "url": urljoin(ZENN_ORIGIN, article["path"]),
            }

        page = paginated_articles["next_page"]


def _extract_contest_slug(url: str) -> str:
    return urlparse(url).path.removeprefix("/contests/").split("/")[0]
