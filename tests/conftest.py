"""
Root conftest.py
"""


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

