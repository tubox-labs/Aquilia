"""Import-order regression tests.

``aquilia.middleware`` and ``aquilia.faults.engine`` used to form an import
cycle, so importing ``Middleware`` first — instead of via ``AquiliaServer``,
which pulls in ``aquilia.faults`` on the way — raised ImportError.

These must run in a subprocess. ``sys.modules`` caching hides import-order
sensitivity once anything in the package has been imported successfully, so an
in-process test cannot detect a regression here.
"""

import subprocess
import sys

# Each entry point must work as the very first touch of the package.
ENTRY_POINTS = [
    "from aquilia.middleware import Middleware",
    "from aquilia import Middleware",
    "from aquilia.faults.engine import FaultMiddleware",
    "import aquilia.faults; from aquilia.middleware import Middleware",
]


def _import_in_subprocess(statement: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", statement],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_middleware_importable_without_faults_first():
    """The documented way to author custom middleware must not need a warm-up import."""
    for statement in ENTRY_POINTS:
        result = _import_in_subprocess(statement)
        assert result.returncode == 0, f"{statement!r} failed:\n{result.stderr}"


def test_middleware_base_is_shared_identity():
    """Both import paths must yield the same class, so isinstance checks hold."""
    statement = (
        "from aquilia._middleware_base import Middleware as A\n"
        "from aquilia.middleware import Middleware as B\n"
        "assert A is B, 'Middleware base diverged between modules'\n"
    )
    result = _import_in_subprocess(statement)
    assert result.returncode == 0, result.stderr


def test_middleware_base_module_stays_a_leaf():
    """The base module must not import aquilia.faults, or the cycle returns."""
    statement = (
        "import sys\n"
        "import aquilia._middleware_base\n"
        "leaked = [m for m in sys.modules if m.startswith('aquilia.faults')]\n"
        "assert not leaked, f'base module pulled in {leaked}'\n"
    )
    result = _import_in_subprocess(statement)
    assert result.returncode == 0, result.stderr
