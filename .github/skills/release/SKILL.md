---
name: release
description: Step-by-step release procedure for pydocfix beta versions
---

# Release Procedure

This skill covers cutting a new release of pydocfix end-to-end — from pre-flight checks to the published PyPI package.

---

## Version Scheme

pydocfix follows [PEP 440](https://peps.python.org/pep-0440/) with the pattern:

```
0.1.0aN   # alpha
0.1.0bN   # beta   ← current phase
0.1.0     # stable (future)
```

The version string lives in **exactly two files**:

| File | Line |
|------|------|
| `pyproject.toml` | `version = "X.Y.Z"` |
| `src/pydocfix/__init__.py` | `__version__ = "X.Y.Z"` |

Both files **must be updated together** and kept in sync.

---

## Release Checklist

### 1. Pre-flight checks

Run the full test suite and linter on a clean state:

```bash
uv run ruff check
uv run pytest
```

All checks must pass before proceeding.

### 2. Determine the next version

Increment the beta number. Example: `X.Y.0` → `X.Y.1`.

### 3. Bump the version (two files)

Edit `pyproject.toml`:

```toml
[project]
version = "X.Y.Z"   # ← new version
```

Edit `src/pydocfix/__init__.py`:

```python
__version__ = "X.Y.Z"   # ← same new version
```

Verify both match:

```bash
grep -E 'version\s*=' pyproject.toml src/pydocfix/__init__.py
```

### 4. Commit and open a PR

Create a release branch, commit, and open a PR against `main`:

```bash
git checkout -b release/vX.Y.Z
git add pyproject.toml src/pydocfix/__init__.py
git commit -m "chore: bump version to X.Y.Z"
git push origin release/vX.Y.Z
```

Open a PR from `release/vX.Y.Z` → `main` and merge it once CI passes.

### 5. Create and push the tag

After the PR is merged, pull the latest `main` and tag the merge commit:

```bash
git checkout main
git pull origin main
git tag vX.Y.Z
git push origin vX.Y.Z
```

> The tag **must** match the `v*` pattern to trigger the release workflow.
> Tag from the **merged `main` commit**, not from the release branch.

### 6. Monitor GitHub Actions

The `Release` workflow (`.github/workflows/release.yml`) runs automatically on tag push:

1. **test** job — runs `pytest tests/` on Python 3.13
2. **publish** job — builds the sdist + wheel with `python -m build`, then publishes to PyPI via trusted publishing (OIDC)

Check the Actions tab on GitHub to confirm both jobs succeed.

### 7. Verify on PyPI

After the workflow completes, confirm the new version is visible:

```
https://pypi.org/project/pydocfix/
```

---

## Rollback

If the publish fails after the tag is pushed, delete the tag and fix the issue:

```bash
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```

Then re-run the checklist from step 1.

---

## Quick Reference — Version Files

```
pyproject.toml               version = "X.Y.Z"
src/pydocfix/__init__.py     __version__ = "X.Y.Z"
```

Both files must always contain the **same** version string.
