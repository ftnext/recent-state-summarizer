# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`recent-state-summarizer` (a.k.a. "RSS") is a Python CLI tool that fetches blog article titles from various sources and uses the OpenAI API to summarize what the author has been doing recently. It currently supports:
- Hatena Blog (はてなブログ)
- Hatena Bookmark RSS
- Adventar calendars
- Qiita Advent Calendar
- Qiita RSS (user feeds)

The main CLI command is `omae-douyo` which fetches titles and generates a summary in Japanese.

## Development Commands

### Environment Setup

**Note**: Claude Code users have this automatically handled by the SessionStart hook. Manual setup is only needed for human developers or when the hook fails.

```bash
python -m venv venv --upgrade-deps
source venv/bin/activate
pip install -r requirements.lock
pip install -e '.[testing]'
```

### Running Tests
```bash
# Run all tests
python -m pytest -v

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
omae-douyo https://qiita.com/ftnext/feed.atom

# Fetch only (save as JSON Lines)
omae-douyo fetch https://nikkie-ftnext.hatenablog.com/archive/2023/4 articles.jsonl
omae-douyo fetch https://qiita.com/ftnext/feed.atom articles.jsonl

# Fetch only (save as title list)
omae-douyo fetch https://nikkie-ftnext.hatenablog.com/archive/2023/4 titles.txt --as-title-list
```

### Development Sub-commands
```bash
# Run fetch module directly
python -m recent_state_summarizer.fetch -h

# Run summarize module directly (useful for prompt tuning)
python -m recent_state_summarizer.summarize -h
```

### Code Formatting
```bash
# Format code with black
uvx black -l 79 .

# Sort imports with isort (using black-compatible profile)
uvx isort --profile black -l 79 .
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
   - `qiita_rss.py`: Parses Atom feeds with feedparser (user RSS feeds)

All fetchers yield `TitleTag` TypedDict objects with `title` and `url` keys.

3. **CLI Interface** (`fetch/cli.py`):
   - `_main(url, save_path, save_as_title_list)`: Core fetch logic that gets the appropriate fetcher, fetches titles, and saves to file
   - `build_parser(add_help)`: Builds argparse parser with dynamic help message using `get_registered_names()`
   - `cli()`: Entry point for `python -m recent_state_summarizer.fetch`
   - Called by `__main__.py:fetch_cli()` when using `omae-douyo fetch` subcommand

### Adding a New Fetcher

To add support for a new source with minimal merge conflicts:

1. Create a new file `fetch/new_source.py`:
```python
from urllib.parse import urlparse
from recent_state_summarizer.fetch.registry import register_fetcher

def _match_new_source(url: str) -> bool:
    # Use exact domain matching to avoid false positives
    netloc = urlparse(url).netloc
    return netloc == "new-source.com" or netloc.endswith(".new-source.com")

@register_fetcher(name="New Source", matcher=_match_new_source)
def fetch_new_source(url: str) -> Generator[TitleTag, None, None]:
    ...
```

2. Add one import line to `fetch/__init__.py`:
```python
from recent_state_summarizer.fetch.new_source import fetch_new_source
```

**Important**: The import is required to trigger the `@register_fetcher` decorator at module load time. Without this import, the fetcher will not be registered and `get_fetcher()` will raise "Unsupported URL" errors.

**Note on `fetch/__init__.py` structure**: All fetchers must be imported in this file. Some imports may have a comment like `# Fetcher registration imports` but all imports serve the same purpose: triggering decorator registration. Registration order determines matcher priority (specific matchers should be imported before generic ones).

### Dynamic Help Messages

The fetcher registry enables dynamic help message generation. When creating subparsers in `__main__.py`, ensure help messages reflect all registered fetchers:

**Important**: argparse's `parents` parameter inherits arguments but **not** `description`. To show the dynamic fetcher list in help:

```python
# __main__.py
fetch_parser_template = build_fetch_parser(add_help=False)
fetch_parser = subparsers.add_parser(
    "fetch",
    parents=[fetch_parser_template],
    description=fetch_parser_template.description,  # Explicitly set description
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
```

The `build_fetch_parser()` in `fetch/__init__.py` uses `get_registered_names()` to dynamically generate the fetcher list, ensuring new fetchers automatically appear in help without manual updates.

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

Use the `/release` skill to bump the version and create a git tag:

```bash
/release X.Y.Z
```

## Development Guidelines

### Issue Workflow

When working on an issue, follow this workflow:

1. **Implement the feature/fix**: Make the necessary code changes
2. **Format code**: Run black and isort to ensure code style consistency
   ```bash
   uvx black -l 79 .
   uvx isort --profile black -l 79 .
   ```
3. **Run tests**: Ensure all tests pass before proceeding
   ```bash
   python -m pytest -v
   ```
4. **Update CLAUDE.md**: If the changes introduce new patterns, architecture decisions, or development practices, update this file using the `/init` skill
   ```bash
   /init
   ```
5. **Create a Pull Request**: Use `gh` CLI to create a PR
   ```bash
   gh pr create -R owner/repo --title "..." --body "..."
   ```

**Important**: Do not create a PR until all tests pass. CLAUDE.md updates should be included in the same PR as the implementation.

### Code Style

- **Avoid comments**: Express code intent through descriptive function and variable names rather than comments. The code should be self-documenting.
- **Minimize diffs**: Keep code changes minimal and focused. Avoid unnecessary refactoring or reformatting when making specific changes.

### GitHub CLI

When using `gh` commands, always specify the `-R` flag to explicitly set the repository:

```bash
gh pr create -R owner/repo ...
gh issue list -R owner/repo ...
```

This is required in environments where the git remote URL uses a local proxy (such as Claude Code on the Web), as `gh` cannot automatically detect the repository from the git remote.
