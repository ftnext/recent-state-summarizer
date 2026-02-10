from __future__ import annotations

from recent_state_summarizer.fetch.adventar import fetch_adventar_calendar
from recent_state_summarizer.fetch.hatena_blog import _fetch_titles

# Fetcher registration imports (required for @register_fetcher decorator)
from recent_state_summarizer.fetch.hatena_bookmark import (
    fetch_hatena_bookmark_rss,
)
from recent_state_summarizer.fetch.note_rss import fetch_note_rss
from recent_state_summarizer.fetch.qiita_advent_calendar import (
    fetch_qiita_advent_calendar,
)
from recent_state_summarizer.fetch.qiita_api import fetch_qiita_api
from recent_state_summarizer.fetch.qiita_rss import fetch_qiita_rss
