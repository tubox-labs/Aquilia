# aq test

Run the project test suite using pytest with Aquilia-aware defaults.

## Usage

```bash
aq test [PATHS...] [OPTIONS]
```

## Arguments

| Argument  | Description                                           |
| --------- | ----------------------------------------------------- |
| `PATHS`   | Specific test file or directory paths (auto-discover if omitted) |

## Options

| Option            | Alias | Description                                  | Default |
| ----------------- | ----- | -------------------------------------------- | ------- |
| `--pattern`       | `-k`  | Only run tests matching pattern expression   | `None`  |
| `--markers`       | `-m`  | Only run tests matching pytest markers       | `None`  |
| `--coverage`      |       | Collect test coverage data                   | `False` |
| `--coverage-html` |       | Generate HTML coverage report                | `False` |
| `--failfast`      | `-x`  | Stop on first failure                        | `False` |

## Auto-Discovery

When no paths are specified, `aq test` auto-discovers test locations:

1. `tests/` directory at workspace root
2. `modules/*/tests/` directories within each module
3. `modules/*/test_*.py` files within each module

## Aquilia-Aware Defaults

`aq test` automatically configures:

- `AQUILIA_ENV=test` environment variable
- `asyncio_mode=auto` for pytest-asyncio
- Coverage source set to `aquilia` with terminal report

## Coverage

```bash
aq test --coverage
```

Generates terminal coverage report:

```
Name                     Stmts   Miss  Cover
----------------------------------------------
aquilia/                  ...
aquilia/cli/              ...
...
----------------------------------------------
TOTAL                     ...     ...   ...%
```

For HTML report:

```bash
aq test --coverage --coverage-html
```

Generates `htmlcov/` directory with interactive coverage reports.

## Examples

```bash
# Run all discovered tests
aq test

# Run specific test file
aq test tests/test_users.py

# Filter by pattern
aq test -k "test_login"

# Filter by marker
aq test -m "slow"

# Fast failure mode
aq test -x -v

# Coverage
aq test --coverage

# Coverage with HTML report
aq test --coverage --coverage-html

# Multiple specific paths
aq test tests/test_users.py tests/test_auth.py
```

## Exit Codes

| Code | Meaning              |
| ---- | -------------------- |
| `0`  | All tests passed     |
| `1`  | Tests failed or error|

## Requirements

- **pytest**: `pip install pytest pytest-asyncio`
- **pytest-cov**: `pip install pytest-cov` (for `--coverage`)

## See Also

- [Development: Testing](/development/testing/) — Testing guide
- [`aq run`](run.md) — Start the development server