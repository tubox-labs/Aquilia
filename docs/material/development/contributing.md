# Contributing to Aquilia

Thank you for considering contributing to Aquilia. This document covers everything you need to participate in the project: code style, commit conventions, the pull request workflow, and where to find issues to work on.

## Code of Conduct

This project and everyone participating in it is governed by the [Aquilia Code of Conduct](https://github.com/axiomchronicles/Aquilia/blob/main/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Where to Start

- **Issue tracker**: [github.com/axiomchronicles/Aquilia/issues](https://github.com/axiomchronicles/Aquilia/issues)
- Labels to look for: `good first issue`, `help wanted`, `bug`, `enhancement`
- **Discussions**: For feature ideas, architecture proposals, and questions, use [GitHub Discussions](https://github.com/axiomchronicles/Aquilia/discussions)

## Development Setup

Aquilia requires **Python 3.10 or higher**.

```bash
# 1. Clone your fork
git clone https://github.com/YOUR_USERNAME/Aquilia.git
cd Aquilia

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"
pip install -r requirements-dev.txt
```

## Code Style

Aquilia uses **Ruff** for both linting and formatting. Configuration lives in `pyproject.toml`.

| Aspect | Tool | Config |
|--------|------|--------|
| **Line length** | ruff | 120 characters |
| **Lint rules** | ruff | `E`, `F`, `W`, `I`, `N`, `UP`, `B`, `SIM` |
| **Formatting** | ruff format | No separate formatter needed |
| **Type checking** | mypy | `disallow_untyped_defs = false`, `warn_return_any = true` |
| **Target Python** | — | 3.10 |

### Lint Commands

```bash
# Check lint (CI authority — must pass before merge)
ruff check aquilia/ --output-format=github

# Check formatting
ruff format --check aquilia/

# Auto-format
ruff format aquilia/

# Run all checks together
ruff check aquilia/ && ruff format --check aquilia/
```

### Per-File Ignore Patterns

- `__init__.py` files allow `F401` (unused imports) — re-exports are intentional
- `.swarm/**/*.py` files allow `N999` — dot-prefixed directories are valid

## Core Development Principles

### 1. Structured Faults, Not Raw Exceptions

All framework-domain errors must use `Fault` subclasses from `aquilia.faults`. **Never** raise raw `ValueError`, `RuntimeError`, `TypeError`, or `KeyError` for framework failures.

When adding error handling to any subsystem:

- Create fault classes in a `faults.py` module within the subsystem
- Use `FaultDomain.custom("name", "description")` for new domains
- Every fault must have: a stable `code`, descriptive `message`, `domain`, and `severity`
- See existing examples: `aquilia/tasks/faults.py`, `aquilia/storage/base.py`, `aquilia/templates/faults.py`

```python
from aquilia.faults.core import Fault
from aquilia.faults.domains import FaultDomain, FaultSeverity

class MyFault(Fault):
    code = "MY_OPERATION_FAILED"
    domain = FaultDomain.custom("my_domain", "My subsystem")
    severity = FaultSeverity.ERROR
    message = "The operation failed due to invalid input"
```

### 2. Manifest-First Module Boundaries

- `workspace.py` is orchestration metadata only — do not add component registration logic there
- Component declarations (controllers, services, middleware) belong in `modules/*/manifest.py` via `AppManifest`
- Avoid deprecated `Module.register_*` patterns

### 3. DI Scope Discipline

Scopes are explicit and immutable after registration:

| Scope | Lifetime | Use for |
|-------|----------|---------|
| `singleton` | Process lifetime | Stateless utilities, connection pools |
| `app` | Application lifetime | Cache service, auth manager |
| `request` | Single HTTP request | Database sessions, request context |

### 4. Async-Native

Everything in the request pipeline is async. All controllers, middleware, and service methods must use `async def`.

### 5. Security Invariants

- **Never** use `pickle.load()` or `pickle.loads()` on untrusted data — use JSON with HMAC verification
- Always validate and normalize file paths (null bytes, `..` traversal, length limits)
- Use parameterized queries — never interpolate user input into SQL strings
- Template rendering must use `SandboxedEnvironment` with autoescape enabled
- Background task resolution must only use the registered task registry

## Testing

The test suite uses **pytest** with **pytest-asyncio** (`asyncio_mode = auto`).

```bash
# Run full test suite (~5,085 tests)
pytest tests/ -v --tb=short -q

# Run a single test
pytest tests/test_controller_system.py::TestMetadata::test_extract_controller_metadata -q

# Fail-fast
pytest tests/ -v -x

# With coverage
pytest tests/ --cov=aquilia --cov-report=term-missing

# With coverage HTML report
pytest tests/ --cov=aquilia --cov-report=html
```

### Test Coverage

Coverage targets `aquilia/` source. Reports exclude:

- Test files themselves (`*/tests/*`, `*/test_*.py`)
- `__repr__` methods
- `AssertionError` / `NotImplementedError` raises
- `if __name__ == "__main__":` guards
- `if TYPE_CHECKING:` blocks

### CI Pipeline

The CI pipeline runs on every PR and push to `main`:

| Platform | Python Versions | Steps |
|----------|-----------------|-------|
| **Ubuntu** | 3.10, 3.11, 3.12, 3.13 | Lint (ruff) → Tests (pytest) |
| **macOS** | 3.13 | Tests (pytest) |
| **Windows** | 3.13 | Tests (pytest) |

Lint must pass before tests run. The lint step uses:
```bash
ruff check aquilia/ --output-format=github
```

## Pull Request Process

### 1. Find an Issue

Check the [issue tracker](https://github.com/axiomchronicles/Aquilia/issues). Issues labeled `good first issue` or `help wanted` are great places to start. Comment on the issue to let others know you're working on it.

### 2. Fork & Branch

```bash
# Fork via GitHub UI, then:
git clone https://github.com/YOUR_USERNAME/Aquilia.git
cd Aquilia

# Branch naming convention
git checkout -b feature/your-feature-name    # For new features
git checkout -b bugfix/your-bugfix-name      # For bug fixes
git checkout -b docs/what-changed            # For documentation
```

### 3. Make Changes

- Follow the code style above
- Add tests for new functionality
- Update any affected documentation
- Run lint and tests locally before pushing

### 4. Commit Messages

Write clean, descriptive commit messages. Use imperative mood:

```
Fix race condition in dotenv loading when multiple threads compete for AQUILIA_ENV

Replace the `bool` flag `_dotenv_lock` with `threading.RLock()` so two
threads loading dotenv simultaneously no longer corrupt `os.environ`.
```

### 5. Submit a Pull Request

- Push to your fork and open a PR against `master`
- Provide a clear description of the problem and solution
- Reference any related issues with `Fixes #123` or `Closes #123`
- Ensure CI checks are green
- Be responsive to review feedback

### 6. Code Review

All PRs require review. Once approved, a maintainer will merge. PRs are squashed on merge — no need to squash manually.

## Reporting Bugs

When filing a bug report, include:

- Aquilia version (`aq --version` or `python -c "import aquilia; print(aquilia.__version__)"`)
- Python version (`python --version`)
- OS platform
- Minimal reproduction steps
- Full traceback if applicable
- Expected vs actual behavior

## Requesting Features

For feature requests, outline:

- The proposed feature
- The problem it solves
- Why it's useful to the broader ecosystem
- Potential alternatives or existing workarounds

## Release Process

See the [Release Process](release-process.md) document for details on versioning, changelog, build, and publishing.

## Versioning

Aquilia uses CalVer-inspired SemVer:

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backwards-compatible
- **PATCH**: Bug fixes, security patches
- **bN**: Beta pre-release suffix (removed on stable release)

Release names follow a pirate theme — each release gets a unique moniker.

## Need Help?

- **Documentation**: [aquilia.dev](https://aquilia.dev)
- **GitHub Discussions**: Ask questions, share ideas
- **Issue tracker**: Report bugs, request features