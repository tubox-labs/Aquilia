"""Import-order regression tests.

``aquilia.middleware`` and ``aquilia.faults.engine`` used to form an import
cycle, so importing ``Middleware`` first — instead of via ``AquiliaServer``,
which pulls in ``aquilia.faults`` on the way — raised ImportError.

The old defence was one file, ``aquilia/_middleware_base.py``, kept clean by a
docstring asking people not to import faults into it. The defence is now a
directory boundary: everything under ``aquilia/middleware/core/`` and
``aquilia/middleware/utils/`` is fault-free, and the package ``__init__``
resolves its exports lazily so importing a leaf does not execute the façade.
``test_leaf_zone_boundaries`` is what makes that structural rather than
aspirational.

These must run in a subprocess. ``sys.modules`` caching hides import-order
sensitivity once anything in the package has been imported successfully, so an
in-process test cannot detect a regression here.
"""

import subprocess
import sys

import pytest

# Each entry point must work as the very first touch of the package.
ENTRY_POINTS = [
    "from aquilia.middleware import Middleware",
    "from aquilia import Middleware",
    "from aquilia.faults.engine import FaultMiddleware",
    "import aquilia.faults; from aquilia.middleware import Middleware",
    "from aquilia.middleware.core.base import Middleware",
    "from aquilia.middleware.stack import MiddlewareStack",
    "from aquilia.middleware.builtin import ExceptionMiddleware",
]

# module -> package prefixes it must NOT drag into sys.modules.
#
# The leaf zone must stay free of the fault engine (that is the cycle), and the
# package façade must stay free of the heavy optional subsystems — an eager
# façade would pull debug/inspector in through the package and reintroduce the
# cycle by a different route.
LEAF_BOUNDARIES = [
    ("aquilia.middleware.core.base", ("aquilia.faults", "aquilia.debug", "aquilia.inspector")),
    ("aquilia.middleware.core.types", ("aquilia.faults", "aquilia.debug", "aquilia.inspector")),
    ("aquilia.middleware.core.priority", ("aquilia.faults", "aquilia.debug", "aquilia.inspector")),
    ("aquilia.middleware.utils.ordering", ("aquilia.faults", "aquilia.middleware.stack")),
    ("aquilia.middleware.utils.throttling", ("aquilia.faults", "aquilia.middleware.stack")),
    ("aquilia.middleware.utils.status", ("aquilia.faults", "aquilia.middleware.stack")),
    ("aquilia.middleware.utils.negotiation", ("aquilia.faults", "aquilia.middleware.stack")),
    ("aquilia.middleware", ("aquilia.debug", "aquilia.inspector")),
]

# The deprecated ``aquilia.middleware_ext`` shim must keep resolving to the same
# objects as the canonical modules: user workspace.py files name these as dotted
# strings, so a broken alias is a boot failure in someone else's project.
LEGACY_ALIASES = [
    ("aquilia.middleware_ext", "SecurityHeadersMiddleware", "aquilia.middleware.builtin.security", "SecurityHeadersMiddleware"),
    ("aquilia.middleware_ext", "EffectMiddleware", "aquilia.middleware.builtin.effects", "EffectMiddleware"),
    ("aquilia.middleware_ext", "RateLimitMiddleware", "aquilia.middleware.builtin.rate_limit", "RateLimitMiddleware"),
]


def _run(statement: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", statement],
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.mark.parametrize("statement", ENTRY_POINTS)
def test_middleware_importable_without_faults_first(statement):
    """The documented way to author custom middleware must not need a warm-up import."""
    result = _run(statement)
    assert result.returncode == 0, f"{statement!r} failed:\n{result.stderr}"


@pytest.mark.parametrize("module,forbidden", LEAF_BOUNDARIES)
def test_leaf_zone_boundaries(module, forbidden):
    """Importing a leaf must not drag the forbidden subsystems in with it."""
    statement = (
        "import sys\n"
        f"import {module}\n"
        f"forbidden = {forbidden!r}\n"
        "leaked = sorted(m for m in sys.modules if m.startswith(forbidden))\n"
        f"assert not leaked, '{module} pulled in ' + repr(leaked)\n"
    )
    result = _run(statement)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("old_mod,old_attr,new_mod,new_attr", LEGACY_ALIASES)
def test_legacy_aliases_share_identity(old_mod, old_attr, new_mod, new_attr):
    """Deprecated paths must yield the same objects, so isinstance checks hold."""
    statement = (
        "import warnings\n"
        "warnings.simplefilter('ignore', DeprecationWarning)\n"
        f"from {old_mod} import {old_attr} as A\n"
        f"from {new_mod} import {new_attr} as B\n"
        f"assert A is B, '{old_attr} diverged between {old_mod} and {new_mod}'\n"
    )
    result = _run(statement)
    assert result.returncode == 0, result.stderr


def test_middleware_base_is_shared_identity():
    """``aquilia.middleware.Middleware`` and the core module must be one class."""
    statement = (
        "from aquilia.middleware import Middleware as A\n"
        "from aquilia.middleware.core.base import Middleware as B\n"
        "from aquilia import Middleware as C\n"
        "assert A is B is C, 'Middleware base diverged between modules'\n"
    )
    result = _run(statement)
    assert result.returncode == 0, result.stderr


def test_middleware_facade_is_lazy():
    """The package __init__ must not eagerly import the stack or built-ins.

    An eager façade would execute on any ``aquilia.middleware.core.*`` import
    and pull ``aquilia.faults`` back into the leaf zone's import graph.
    """
    statement = (
        "import sys\n"
        "import aquilia.middleware\n"
        "eager = sorted(m for m in sys.modules if m.startswith(('aquilia.middleware.stack',"
        " 'aquilia.middleware.builtin')))\n"
        "assert not eager, 'facade eagerly imported ' + repr(eager)\n"
        # ...but the attribute still resolves on access.
        "assert aquilia.middleware.MiddlewareStack.__name__ == 'MiddlewareStack'\n"
        "assert 'aquilia.middleware.stack.registry' in sys.modules\n"
    )
    result = _run(statement)
    assert result.returncode == 0, result.stderr
