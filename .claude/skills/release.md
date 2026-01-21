---
name: release
description: Bumps version and creates git tag for release
invocations:
  - release
---

# Version Management

Version is stored in `recent_state_summarizer/__init__.py` as `__version__` and referenced by `pyproject.toml` using setuptools dynamic versioning.

## Bumping Version

Follow these steps to bump the version:

```bash
# 1. Edit version in recent_state_summarizer/__init__.py
# 2. Commit and tag
git add recent_state_summarizer/__init__.py
git commit -m "chore: Bump up X.Y.Z"
git tag vX.Y.Z
git push origin main --tags
```

## Instructions

If the user provided a version number (e.g., `/release 0.1.0`), use that. Otherwise, ask the user for the new version number.

Execute the steps above, replacing X.Y.Z with the specified version.
