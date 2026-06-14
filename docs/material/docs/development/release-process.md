# Release Process

This document describes how Aquilia is versioned, built, and published to PyPI.

## Versioning Scheme

Aquilia uses **CalVer-inspired Semantic Versioning**:

```
MAJOR.MINOR.PATCH[bN]
```

| Component | Meaning |
|-----------|---------|
| **MAJOR** | Breaking API changes |
| **MINOR** | New features, backwards-compatible |
| **PATCH** | Bug fixes, security patches |
| **bN** | Beta pre-release (removed on stable release) |

### Current Version

The single source of truth for the version is `aquilia/_version.py`:

```python
# aquilia/_version.py
__version__: str = "1.1.2"
VERSION: tuple[int, int, int] = (1, 1, 2)
RELEASE_NAME: str = "Crimson Gale"
WORKSPACE_VERSION: str = "1.0.0"
```

All subsystem `__init__.py` files import from `aquilia._version`. The `WORKSPACE_VERSION` constant is intentionally frozen at `1.0.0` so generated `workspace.py` files are not pinned to the framework release cycle.

### Release Names

Each release gets a pirate-themed moniker. Release names are human-friendly aliases for the numeric version and appear in CLI banners, documentation, and metadata.

Past releases:

| Version | Release Name | Date |
|---------|-------------|------|
| 1.1.2 | Crimson Gale | 2026-06-12 |
| 1.1.1 | Sea Serpent | 2026-06-09 |
| 1.1.0 | Black Pearl | 2026-06-08 |

### Programmatic Version Access

```python
from aquilia._version import __version__, VERSION, RELEASE_NAME

print(__version__)         # "1.1.2"
print(VERSION)             # (1, 1, 2)
print(RELEASE_NAME)        # "Crimson Gale"
```

## Release Checklist

### 1. Verify All Tests Pass

```bash
# Ensure CI is green on the release branch
pytest tests/ -v -x --tb=short

# Verify coverage
pytest tests/ --cov=aquilia --cov-report=term-missing

# Run lint
ruff check aquilia/ --output-format=github
ruff format --check aquilia/
```

### 2. Update the Version

Edit `aquilia/_version.py`:

```python
# aquilia/_version.py

#: Framework version — single source of truth.
__version__: str = "1.1.3"

#: Version tuple for programmatic comparison.
VERSION: tuple[int, int, int] = (1, 1, 3)

#: Human-friendly release name (pirate-themed).
RELEASE_NAME: str = "Kraken's Wrath"
```

Check that `pyproject.toml` uses dynamic versioning (it does — version is read from `aquilia._version.__version__`):

```toml
[tool.setuptools.dynamic]
version = {attr = "aquilia._version.__version__"}
```

### 3. Update the Changelog

Edit `CHANGELOG.md` at the repository root. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/):

```markdown
# Changelog

## [1.1.3] — 2026-XX-XX — "Kraken's Wrath"

### Added
- New `FeatureX` for handling Y scenarios

### Changed
- Refactored `ModuleX` to use new pattern

### Fixed
- Bug where `name 'Entry' is not defined` caused server crash
- Thread safety issue in dotenv loading

### Removed
- Deprecated `old_api_function()`
```

Categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

### 4. Commit and Tag

```bash
# Stage version and changelog changes
git add aquilia/_version.py CHANGELOG.md

# Commit with release message
git commit -m "Bump version to 1.1.3 (Kraken's Wrath)"

# Create an annotated tag
git tag -a v1.1.3 -m "Release v1.1.3 (Kraken's Wrath)"

# Push to remote
git push origin master --tags
```

### 5. Build Distributables

Aquilia uses `setuptools` with `build` for creating distributions:

```bash
# Install build tools
pip install build twine

# Build source distribution and wheel
python -m build

# The above creates:
#   dist/aquilia-1.1.3.tar.gz          (source distribution)
#   dist/aquilia-1.1.3-py3-none-any.whl (universal wheel)
```

### 6. Verify Distributables

```bash
# Check package metadata with twine
twine check dist/*

# Expected output:
#   Checking dist/aquilia-1.1.3.tar.gz: PASSED
#   Checking dist/aquilia-1.1.3-py3-none-any.whl: PASSED

# Inspect package contents
tar -tzf dist/aquilia-1.1.3.tar.gz | head -20
```

### 7. Publish to PyPI (Test)

First, test with TestPyPI:

```bash
twine upload --repository testpypi dist/*

# Verify installability from TestPyPI
pip install --index-url https://test.pypi.org/simple/ aquilia==1.1.3
python -c "import aquilia; print(aquilia.__version__)"
```

### 8. Publish to PyPI (Production)

```bash
twine upload dist/*
```

### 9. Verify the Release

```bash
# In a fresh virtual environment
python -m venv /tmp/aquilia-verify
source /tmp/aquilia-verify/bin/activate
pip install aquilia==1.1.3
python -c "import aquilia; print(aquilia.__version__)"  # Should print 1.1.3
aq --version  # Should show the version and release name
```

### 10. Create GitHub Release

1. Go to [GitHub Releases](https://github.com/axiomchronicles/Aquilia/releases)
2. Click "Draft a new release"
3. Choose the tag `v1.1.3`
4. Title: `v1.1.3 — Kraken's Wrath`
5. Copy the relevant section from `CHANGELOG.md` as the description
6. Attach the wheel and source distribution from `dist/`
7. Publish the release

## Full Release Script

Here's a consolidated script for the entire release process:

```bash
#!/bin/bash
set -euo pipefail

VERSION="1.1.3"
RELEASE_NAME="Kraken's Wrath"

echo "=== Release Aquilia v${VERSION} (${RELEASE_NAME}) ==="

# 1. Verify state
echo "1. Running final checks..."
ruff check aquilia/ --output-format=github
ruff format --check aquilia/
pytest tests/ -x -q

# 2. Commit version bump (assuming _version.py and CHANGELOG.md are already updated)
echo "2. Committing version bump..."
git add aquilia/_version.py CHANGELOG.md
git commit -m "Bump version to ${VERSION} (${RELEASE_NAME})"

# 3. Tag
echo "3. Tagging release..."
git tag -a "v${VERSION}" -m "Release v${VERSION} (${RELEASE_NAME})"

# 4. Build
echo "4. Building distributions..."
rm -rf dist/
python -m build
twine check dist/*

# 5. Push
echo "5. Pushing to remote..."
git push origin master --tags

# 6. Upload
echo "6. Uploading to PyPI..."
twine upload dist/*

echo "=== Release complete! ==="
echo "Next: Create GitHub Release at https://github.com/axiomchronicles/Aquilia/releases"
```

## Package Metadata

The `pyproject.toml` file defines all published metadata:

```toml
[project]
name = "aquilia"
dynamic = ["version"]
description = "Async-native Python web framework with flow-first routing"
requires-python = ">=3.10"
license = { text = "MIT" }

[project.urls]
Homepage    = "https://github.com/tubox-labs/Aquilia"
Documentation = "https://github.com/tubox-labs/Aquilia#readme"
Repository  = "https://github.com/tubox-labs/Aquilia"
Issues      = "https://github.com/tubox-labs/Aquilia/issues"
Changelog   = "https://github.com/tubox-labs/Aquilia/blob/main/CHANGELOG.md"
```

### Package Classification

```toml
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Framework :: AsyncIO",
    "Topic :: Internet :: WWW/HTTP",
    "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    "Typing :: Typed",
]
```

### Optional Dependency Groups

The package defines extras for optional functionality:

| Extra | Packages | Purpose |
|-------|----------|---------|
| `auth` | `cryptography`, `argon2-cffi` | Authentication (JWT, password hashing) |
| `redis` | `redis[asyncio]` | Redis cache & socket backends |
| `mail` | `aiosmtplib` | SMTP email |
| `server` | `gunicorn`, `uvicorn[standard]` | Production serving |
| `postgres` | `asyncpg` | Async PostgreSQL |
| `otel` | `opentelemetry-*` | Distributed tracing |
| `dev` | `pytest`, `ruff`, `mypy` | Development tools |
| `full` | (combination) | All optional features |

## Post-Release

After publishing:

1. **Update documentation**: Ensure the docs reflect the new version
2. **Announce**: Post in GitHub Discussions and relevant community channels
3. **Monitor**: Watch for issue reports against the new version
4. **Mergedown**: If releasing from a release branch, merge back to `master`

## Hotfix Releases

For critical bug fixes that need immediate release:

1. Branch from the release tag: `git checkout -b hotfix/1.1.2.1 v1.1.2`
2. Apply the fix, increment PATCH in `_version.py`
3. Follow the checklist above (skip non-applicable steps)
4. Merge the hotfix branch to `master` after release