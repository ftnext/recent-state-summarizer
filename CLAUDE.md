# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`recent-state-summarizer` (a.k.a. "RSS") is a Python CLI tool that fetches blog article titles from various sources and uses the OpenAI API to summarize what the author has been doing recently. It currently supports:
- Hatena Blog (はてなブログ)
- Hatena Bookmark RSS
- Adventar calendars
- Qiita Advent Calendar

The main CLI command is `omae-douyo` which fetches titles and generates a summary in Japanese.

## Development Commands

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.lock
pip install -e '.[testing]'
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_main.py -v

# Run a specific test
python -m pytest tests/test_main.py::test_main_success_path -v
```

### Using the CLI
```bash
# Set OpenAI API key first
export OPENAI_API_KEY=your-key-here

# Fetch and summarize
omae-douyo https://nikkie-ftnext.hatenablog.com/archive/2023/4

# Fetch only (save as JSON Lines)
omae-douyo fetch https://example.com/archive/2023 articles.jsonl

# Fetch only (save as title list)
omae-douyo fetch https://example.com/archive/2023 titles.txt --as-title-list
```

### Development Sub-commands
```bash
# Run fetch module directly
python -m recent_state_summarizer.fetch -h

# Run summarize module directly (useful for prompt tuning)
python -m recent_state_summarizer.summarize -h
```

## Architecture

### Command Flow

The tool has two main paths:

1. **Full flow (default)**: URL → Fetch titles → Summarize → Print summary
   - Entry: `__main__.py:main()` → `run_cli()`
   - Uses a temporary file to pass titles between fetch and summarize

2. **Fetch-only flow**: URL → Fetch titles → Save to file
   - Entry: `__main__.py:main()` → `fetch_cli()`
   - Saves as JSON Lines or bullet list format

### Argument Normalization

The CLI uses `normalize_argv()` (`__main__.py`) to provide a user-friendly command interface:

- **Empty arguments**: Returns `["--help"]` to show help message
- **Help flags first** (`-h`, `--help`): Passes through unchanged to show appropriate help
- **Unknown subcommand**: Automatically inserts `"run"` subcommand at the beginning
  - Example: `omae-douyo <url>` → `omae-douyo run <url>`
- **Known subcommands**: Passes through unchanged (`run`, `fetch`)

This allows users to omit the `run` subcommand for the most common use case while maintaining explicit subcommand support when needed.

### Fetcher System

The fetcher system uses a registry pattern where each fetcher self-registers:

1. **Registry** (`fetch/registry.py`):
   - `@register_fetcher(name, matcher)`: Decorator for self-registration
   - `get_fetcher(url)`: Returns appropriate fetcher by testing URL against matchers
   - `get_registered_names()`: Returns list of fetcher names for help messages

2. **Fetcher Implementations** (each self-registers via decorator):
   - `hatena_blog.py`: Parses HTML with BeautifulSoup, recursively follows pagination
   - `hatena_bookmark.py`: Parses RSS feeds with feedparser
   - `adventar.py`: Uses httpx + BeautifulSoup to parse Adventar calendar pages
   - `qiita_advent_calendar.py`: Uses httpx + BeautifulSoup to extract JSON data from Qiita Advent Calendar pages

All fetchers yield `TitleTag` TypedDict objects with `title` and `url` keys.

### Adding a New Fetcher

To add support for a new source with minimal merge conflicts:

1. Create a new file `fetch/new_source.py`:
```python
from recent_state_summarizer.fetch.registry import register_fetcher

def _match_new_source(url: str) -> bool:
    return "new-source.com" in url

@register_fetcher(name="New Source", matcher=_match_new_source)
def fetch_new_source(url: str) -> Generator[TitleTag, None, None]:
    ...
```

2. Add one import line to `fetch/__init__.py`:
```python
from recent_state_summarizer.fetch.new_source import fetch_new_source
```

Registration order in `__init__.py` determines matcher priority (specific matchers should be imported before generic ones).

### Summarization

`summarize.py` uses the OpenAI API (legacy v0.28.x):
- Model: `gpt-3.5-turbo`
- Prompt is in Japanese, asks for summary of what the author has been doing
- Temperature: 0.0 (deterministic)
- API uses old `openai.ChatCompletion.create()` interface (pre-v1.0)

### Data Formats

**TitleTag TypedDict**:
```python
{
    "title": str,  # Article title
    "url": str     # Article URL
}
```

**Output formats**:
- JSON Lines: One TitleTag JSON per line
- Bullet list: Plain text with "- " prefix per title

## Testing

Tests use:
- `pytest` as the test runner
- `responses` for mocking OpenAI API calls
- `respx` for mocking httpx calls

Test structure mirrors source code:
- `tests/test_main.py`: End-to-end CLI tests
- `tests/fetch/test_*.py`: Individual fetcher tests
- `tests/fetch/test_core.py`: Registry-based fetcher lookup tests

## Key Dependencies

- `beautifulsoup4`: HTML parsing for Hatena Blog, Adventar, and Qiita Advent Calendar
- `feedparser`: RSS parsing for Hatena Bookmark
- `httpx`: HTTP client for Adventar and Qiita Advent Calendar (supports async, though not currently used)
- `openai<1`: Legacy OpenAI API (pre-v1.0)
- `urllib.request.urlopen`: Used by Hatena Blog fetcher only

## Version Management

Version is stored in `recent_state_summarizer/__init__.py` as `__version__` and referenced by `pyproject.toml` using setuptools dynamic versioning.

### Bumping Version

```bash
# 1. Edit version in recent_state_summarizer/__init__.py
# 2. Commit and tag
git add recent_state_summarizer/__init__.py
git commit -m "chore: Bump up X.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## Development Guidelines

### Code Style

- **Avoid comments**: Express code intent through descriptive function and variable names rather than comments. The code should be self-documenting.
- **Minimize diffs**: Keep code changes minimal and focused. Avoid unnecessary refactoring or reformatting when making specific changes.
