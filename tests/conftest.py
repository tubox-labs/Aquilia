"""
Root conftest.py — sets up sys.path for the authentication app.
"""

import os
import sys

# Add repo root and authentication app to sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTH_APP = os.path.join(REPO_ROOT, "authentication")

for p in [REPO_ROOT, AUTH_APP]:
    if p not in sys.path:
        sys.path.insert(0, p)


def pytest_sessionfinish(session, exitstatus):
    """Clear native plan caches so nanobind shutdown leak checker doesn't report cached plans."""
    try:
        from aquilia.contracts import _native_plan as c_np

        c_np._PLAN_CACHE.clear()
    except Exception:
        pass
    try:
        from aquilia.models import _native_plan as m_np

        m_np._PLAN_CACHE.clear()
    except Exception:
        pass

