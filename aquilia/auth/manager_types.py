"""
AquilAuth - Shared Manager Types

Contains auxiliary types consumed by both the legacy AuthManager and the new
AuthManager (auth_manager.py).  Keeping them here prevents circular imports
and gives them a stable home that neither implementation "owns".
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


class RateLimiter:
    """
    In-process authentication rate limiter.

    Tracks failed authentication attempts per key (typically a username or
    IP address) within a sliding time window.  After *max_attempts* failures
    the key is locked out for *lockout_duration* seconds.

    .. warning::
        This implementation is **not shared across processes**.  In a
        horizontally-scaled deployment (multiple Uvicorn workers, Kubernetes
        pods) each process maintains its own counter.  For production
        multi-process deployments swap this for a Redis-backed implementation
        that uses atomic ``INCR`` + ``EXPIRE``.

    Args:
        max_attempts:      Maximum failed attempts before lockout.
        window_seconds:    Rolling window in which attempts are counted.
        lockout_duration:  How long (seconds) a key stays locked after
                           exceeding *max_attempts*.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 900,
        lockout_duration: int = 3600,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_duration = lockout_duration
        self._attempts: dict[str, list[datetime]] = {}
        self._lockouts: dict[str, datetime] = {}

    # ── Internal helpers ────────────────────────────────────────────────────

    def _cleanup_old_attempts(self, key: str) -> None:
        """Discard attempts that fall outside the current time window."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.window_seconds)
        if key in self._attempts:
            self._attempts[key] = [ts for ts in self._attempts[key] if ts > cutoff]

    # ── Public interface ────────────────────────────────────────────────────

    def record_attempt(self, key: str) -> None:
        """
        Record a single failed authentication attempt for *key*.

        If the number of attempts within the window reaches *max_attempts*
        a lockout entry is created automatically.
        """
        self._cleanup_old_attempts(key)
        if key not in self._attempts:
            self._attempts[key] = []
        self._attempts[key].append(datetime.now(timezone.utc))
        if len(self._attempts[key]) >= self.max_attempts:
            self._lockouts[key] = datetime.now(timezone.utc) + timedelta(seconds=self.lockout_duration)

    def is_locked_out(self, key: str) -> bool:
        """
        Return ``True`` when *key* is currently locked out.

        An expired lockout is cleared automatically so subsequent calls
        after the lockout window will return ``False``.
        """
        if self.max_attempts <= 0:
            return True
        if key in self._lockouts:
            if datetime.now(timezone.utc) < self._lockouts[key]:
                return True
            # Lockout expired — clear state.
            del self._lockouts[key]
            self._attempts.pop(key, None)
        return False

    def get_remaining_attempts(self, key: str) -> int:
        """Return the number of attempts remaining before lockout."""
        self._cleanup_old_attempts(key)
        current = len(self._attempts.get(key, []))
        return max(0, self.max_attempts - current)

    def reset(self, key: str) -> None:
        """
        Clear all attempt history for *key*.

        Call this on a successful authentication so that the window resets
        without carrying over prior failures.
        """
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)


__all__ = ["RateLimiter"]
