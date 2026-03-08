# Contributing to Aquilia

First off, thank you for considering contributing to Aquilia! It's people like you that make Aquilia such a great tool.

Below are the guidelines and steps to contribute to the project.

## Code of Conduct
This project and everyone participating in it is governed by the [Aquilia Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Submitting Contributions

### 1. Find an Issue to Work On
Check our [issue tracker](https://github.com/axiomchronicles/aquilia/issues) on GitHub. Issues labeled `good first issue` or `help wanted` are great places to start.

### 2. Fork & Branch
Fork the repository on GitHub and clone it locally. Then, create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
```
or 
```bash
git checkout -b bugfix/your-bugfix-name
```

### 3. Local Development Setup
Aquilia requires Python 3.10 or higher.
We recommend using a virtual environment:

```bash
python -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`
```

Install the dependencies, including the development ones:
```bash
pip install -e ".[dev,templates,auth,db,files]"
pip install -r requirements-dev.txt
```

### 4. Making Changes
Make your code changes, following our style guides.
* Aquilia adopts standard Python PEP 8 style formatting.
* We recommend using `ruff` for linting and formatting.
* Ensure all your changes are typed properly.
* **Use structured Faults, not raw exceptions.** All errors should use `aquilia.faults.core.Fault` subclasses with proper domain, code, and severity. See `aquilia/faults/domains.py` for examples.

### 5. Fault System Guidelines
When adding error handling to any subsystem:
- Create fault classes in a `faults.py` module within the subsystem
- Use `FaultDomain.custom("name", "description")` for new domains
- Every fault must have a stable `code` (e.g., `"TASK_SCHEDULE_INVALID"`), descriptive `message`, and appropriate `severity`
- Never raise raw `ValueError`, `RuntimeError`, `TypeError`, or `KeyError` — wrap them in a Fault subclass
- See existing examples: `aquilia/tasks/faults.py`, `aquilia/storage/base.py`, `aquilia/templates/faults.py`, `aquilia/admin/faults.py`

### 6. Security Guidelines
- Never use `pickle.load()` or `pickle.loads()` on untrusted data — use JSON with HMAC verification
- Always validate and normalize file paths (null bytes, `..` traversal, length limits)
- Use parameterized queries — never interpolate user input into SQL strings
- Template rendering must use `SandboxedEnvironment` with autoescape enabled
- Background task resolution must only use the registered task registry

### 7. Testing
Before submitting, run our test suite using `pytest`:

```bash
pytest tests/ -q
```

The full suite has 5,085+ tests and should complete in under 60 seconds.
Ensure all tests pass and consider adding new tests to cover any new logic or edge cases you introduce. Use `pytest --cov=aquilia` to check coverage.

### 8. Submit a Pull Request
Push your branch to your forked repository and submit a Pull Request against the `master` branch.
Provide a clear description of the problem your PR solves or feature it adds.

## Reporting Bugs
- Make sure you are on the latest version of Aquilia.
- Provide a clear and descriptive title.
- Describe the exact steps which reproduce the problem in as many details as possible.
- Include Python version, OS platform, and any relevant traceback errors.

## Requesting Features
- Outline the proposed feature, the problem it solves, and why it's useful to the broader ecosystem.
- Discuss potential alternatives or existing workarounds if applicable.
