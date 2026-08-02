"""
aquilia.devplatform.profiler.engine — Request-level cProfile capture.

Runs cProfile per-request, activated by:
  - Config: profiler_enabled=True (applies to all requests)
  - Request header: X-Aquilia-Profile: true (per-request override)

Profile output is attached to the active RequestRecord as profile_stats string.
"""

from __future__ import annotations

import cProfile
import io
import pstats
from contextvars import ContextVar
from typing import Any

_ACTIVE_PROFILE: ContextVar[cProfile.Profile | None] = ContextVar("adp_active_profile", default=None)


class cProfilingRunner:
    """
    Per-request cProfile session manager.

    Usage::

        runner = cProfilingRunner()
        runner.start()
        # ... execute request handler ...
        stats_text = runner.stop()
    """

    __slots__ = ("_profile", "_stream")

    def __init__(self) -> None:
        self._profile = cProfile.Profile()
        self._stream = io.StringIO()

    def start(self) -> None:
        """Enable profiling and register in ContextVar."""
        self._stream.truncate(0)
        self._stream.seek(0)
        self._profile.enable()
        _ACTIVE_PROFILE.set(self._profile)

    def stop(self) -> str:
        """Disable profiling, format stats, return as text."""
        self._profile.disable()
        _ACTIVE_PROFILE.set(None)
        stats = pstats.Stats(self._profile, stream=self._stream)
        stats.sort_stats("cumulative")
        stats.print_stats(50)  # top 50 entries
        return self._stream.getvalue()

    @staticmethod
    def is_profiling_requested(request: Any) -> bool:
        """
        Check if the incoming request has requested profiling via header.
        Works with Aquilia Request objects (request.headers dict-like access).
        """
        try:
            header_val = request.headers.get("x-aquilia-profile", "")
            return header_val.lower() in ("true", "1", "yes")
        except Exception:
            return False

    @staticmethod
    def get_active_profile() -> cProfile.Profile | None:
        return _ACTIVE_PROFILE.get()
