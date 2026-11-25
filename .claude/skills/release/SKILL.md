---
name: release
description: Bumps the version, tags the commit, and prepares a draft GitHub Release for manual publication
disable-model-invocation: true
argument-hint: "[version-number]"
---

# Release Preparation

Version is stored in `recent_state_summarizer/__init__.py` as `__version__` and referenced by `pyproject.toml` using setuptools dynamic versioning.

The skill ends at a GitHub Release draft. A human reviews the draft and publishes it in the GitHub UI. Never publish a release or trigger PyPI publication from this skill. Publishing the GitHub Release starts the PyPI workflow in `.github/workflows/publish.yml`.

## Prepare the Local Commit and Tag

Check the current branch with `git branch --show-current`. Run the release preparation on `main` after the changes intended for this release have been merged.

Use the version supplied by the user, or increment the patch version in `recent_state_summarizer/__init__.py`. Edit `__version__`, then commit the version file and create the tag. Replace `X.Y.Z` with the selected version.

```bash
git add recent_state_summarizer/__init__.py
git commit --only -m "chore: Bump up X.Y.Z" -- recent_state_summarizer/__init__.py
git tag vX.Y.Z
```

## Confirm the Push

For a release request, the default is to push `main` and the release tag, then create a GitHub Release draft. After creating the local commit and tag, confirm the push unless the user already authorized it. State in the confirmation that the draft follows the push and publication is manual.

In this release flow, a reply such as 「push お願いします」 confirms the push and lets the draft preparation proceed. If the user explicitly requests only a push, stop after pushing. If they defer the push, report the local commit and tag.

Push only the release branch and tag:

```bash
git push --atomic origin refs/heads/main:refs/heads/main refs/tags/vX.Y.Z:refs/tags/vX.Y.Z
```

## Create and Hand Off the Draft

After confirming the tag is on GitHub, create the release with `--draft` and `--verify-tag`. If a release already exists for the tag, report its URL and status without changing it.

```bash
gh release create vX.Y.Z --draft --verify-tag --title vX.Y.Z --generate-notes
gh release view vX.Y.Z --json isDraft,url
```

Verify that `isDraft` is `true`, share the draft URL, and hand off to the human to review the notes and click **Publish release** in GitHub.
