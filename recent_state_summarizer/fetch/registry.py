from __future__ import annotations

from collections.abc import Callable, Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from recent_state_summarizer.fetch.types import TitleTag

Fetcher = Callable[[str], Generator["TitleTag", None, None]]
URLMatcher = Callable[[str], bool]

_registry: list[tuple[str, URLMatcher, Fetcher]] = []


def register_fetcher(
    name: str,
    matcher: URLMatcher,
) -> Callable[[Fetcher], Fetcher]:
    """Decorator to register a fetcher with a URL matcher.

    Args:
        name: Human-readable name for the fetcher (used in help messages)
        matcher: Function that takes a URL and returns True if this fetcher handles it
    """

    def decorator(func: Fetcher) -> Fetcher:
        _registry.append((name, matcher, func))
        return func

    return decorator


def get_fetcher(url: str) -> Fetcher:
    """Get the appropriate fetcher for a URL.

    Raises:
        ValueError: If no fetcher matches the URL
    """
    for name, matcher, fetcher in _registry:
        if matcher(url):
            return fetcher
    raise ValueError(f"Unsupported URL: {url}")


def get_registered_names() -> list[str]:
    """Get list of registered fetcher names for help messages."""
    return [name for name, _, _ in _registry]
