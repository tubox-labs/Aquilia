"""
AquilaSessions - Session storage abstraction.

Defines SessionStore protocol and concrete implementations:
- MemoryStore: In-memory storage (dev/testing) - O(1) LRU via OrderedDict
- FileStore: File-based storage (debugging)
"""

from __future__ import annotations

import asyncio
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from aquilia.sessions.core import Session, SessionID
from aquilia.sessions.faults import SessionForgeryAttemptFault, SessionStoreCorruptedFault, SessionStoreUnavailableFault

# ============================================================================
# SessionStore Protocol
# ============================================================================


class SessionStore(Protocol):
    """
    Abstract session storage interface.

    Stores are responsible ONLY for persistence - they do NOT enforce policy.
    All methods must be async and cancellation-safe.
    """

    async def load(self, session_id: SessionID) -> Session | None: ...
    async def save(self, session: Session) -> None: ...
    async def delete(self, session_id: SessionID) -> None: ...
    async def exists(self, session_id: SessionID) -> bool: ...
    async def list_by_principal(self, principal_id: str) -> list[Session]: ...
    async def count_by_principal(self, principal_id: str) -> int: ...
    async def cleanup_expired(self) -> int: ...
    async def shutdown(self) -> None: ...


# ============================================================================
# MemoryStore - In-Memory Storage (O(1) LRU via OrderedDict)
# ============================================================================


class MemoryStore:
    """
    In-memory session storage for development and testing.

    Uses OrderedDict for O(1) LRU eviction instead of O(n) list operations.
    NOT suitable for production (no persistence across restarts).
    """

    def __init__(self, max_sessions: int = 10000):
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._principal_index: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def load(self, session_id: SessionID) -> Session | None:
        async with self._lock:
            session_id_str = str(session_id)
            session = self._sessions.get(session_id_str)
            if session:
                self._sessions.move_to_end(session_id_str)  # O(1) LRU touch
            return session

    async def save(self, session: Session) -> None:
        async with self._lock:
            session_id_str = str(session.id)

            # Evict if at capacity and this is a new session
            if session_id_str not in self._sessions and len(self._sessions) >= self.max_sessions:
                self._evict_lru()

            # Store session (moves to end = most recently used)
            self._sessions[session_id_str] = session
            self._sessions.move_to_end(session_id_str)

            # Update principal index
            if session.principal:
                principal_id = session.principal.id
                if principal_id not in self._principal_index:
                    self._principal_index[principal_id] = set()
                self._principal_index[principal_id].add(session_id_str)

            session.mark_clean()

    async def delete(self, session_id: SessionID) -> None:
        async with self._lock:
            session_id_str = str(session_id)
            session = self._sessions.pop(session_id_str, None)

            if session and session.principal:
                principal_id = session.principal.id
                if principal_id in self._principal_index:
                    self._principal_index[principal_id].discard(session_id_str)
                    if not self._principal_index[principal_id]:
                        del self._principal_index[principal_id]

    async def exists(self, session_id: SessionID) -> bool:
        async with self._lock:
            return str(session_id) in self._sessions

    async def list_by_principal(self, principal_id: str) -> list[Session]:
        async with self._lock:
            session_ids = self._principal_index.get(principal_id, set())
            return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    async def count_by_principal(self, principal_id: str) -> int:
        async with self._lock:
            session_ids = self._principal_index.get(principal_id, set())
            return sum(1 for sid in session_ids if sid in self._sessions)

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired_ids = []

        async with self._lock:
            for session_id, session in list(self._sessions.items()):
                if session.is_expired(now):
                    expired_ids.append(session_id)

            for session_id in expired_ids:
                session = self._sessions.pop(session_id, None)
                if session and session.principal:
                    principal_id = session.principal.id
                    if principal_id in self._principal_index:
                        self._principal_index[principal_id].discard(session_id)
                        if not self._principal_index[principal_id]:
                            del self._principal_index[principal_id]

        return len(expired_ids)

    async def shutdown(self) -> None:
        async with self._lock:
            self._sessions.clear()
            self._principal_index.clear()

    def _evict_lru(self) -> None:
        """Evict least recently used session. O(1) via OrderedDict."""
        if not self._sessions:
            return

        # pop first item = least recently used (O(1))
        oldest_id, session = self._sessions.popitem(last=False)

        if session and session.principal:
            principal_id = session.principal.id
            if principal_id in self._principal_index:
                self._principal_index[principal_id].discard(oldest_id)
                if not self._principal_index[principal_id]:
                    del self._principal_index[principal_id]

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_sessions": len(self._sessions),
            "max_sessions": self.max_sessions,
            "total_principals": len(self._principal_index),
            "utilization": len(self._sessions) / self.max_sessions if self.max_sessions > 0 else 0,
        }

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def web_optimized(cls) -> MemoryStore:
        return cls(max_sessions=25000)

    @classmethod
    def api_optimized(cls) -> MemoryStore:
        return cls(max_sessions=15000)

    @classmethod
    def development_focused(cls) -> MemoryStore:
        return cls(max_sessions=1000)

    @classmethod
    def high_throughput(cls) -> MemoryStore:
        return cls(max_sessions=50000)


# ============================================================================
# FileStore - File-Based Storage
# ============================================================================


class FileStore:
    """
    File-based session storage for debugging and development.
    NOT suitable for production.
    """

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    # Pattern: sess_ followed by base64url characters (A-Z, a-z, 0-9, -, _)
    _SAFE_ID_PATTERN = re.compile(r"^sess_[A-Za-z0-9_-]{20,64}$")

    def _get_path(self, session_id: SessionID) -> Path:
        sid_str = str(session_id)
        # Guard: reject session IDs that don't match expected format
        if not self._SAFE_ID_PATTERN.match(sid_str):
            raise SessionForgeryAttemptFault(
                reason="Session ID contains invalid characters",
            )
        path = self.directory / f"{sid_str}.json"
        # Guard: ensure resolved path stays within the session directory
        try:
            path.resolve().relative_to(self.directory.resolve())
        except ValueError:
            raise SessionForgeryAttemptFault(
                reason="Session ID attempted path traversal",
            )
        return path

    async def load(self, session_id: SessionID) -> Session | None:
        path = self._get_path(session_id)
        if not path.exists():
            return None

        try:
            async with self._lock:
                data = path.read_text(encoding="utf-8")
                session_dict = json.loads(data)
                return Session.from_dict(session_dict)
        except json.JSONDecodeError as e:
            raise SessionStoreCorruptedFault(message=f"Session file corrupted: {e}", session_id=str(session_id))
        except SessionStoreCorruptedFault:
            raise
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="file", cause=str(e))

    async def save(self, session: Session) -> None:
        path = self._get_path(session.id)
        try:
            async with self._lock:
                session_dict = session.to_dict()
                data = json.dumps(session_dict, indent=2)
                temp_path = path.with_suffix(".tmp")
                temp_path.write_text(data, encoding="utf-8")
                temp_path.rename(path)
                session.mark_clean()
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="file", cause=str(e))

    async def delete(self, session_id: SessionID) -> None:
        path = self._get_path(session_id)
        try:
            async with self._lock:
                if path.exists():
                    path.unlink()
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="file", cause=str(e))

    async def exists(self, session_id: SessionID) -> bool:
        return self._get_path(session_id).exists()

    async def list_by_principal(self, principal_id: str) -> list[Session]:
        sessions = []
        async with self._lock:
            for path in self.directory.glob("sess_*.json"):
                try:
                    data = path.read_text(encoding="utf-8")
                    session_dict = json.loads(data)
                    if session_dict.get("principal") and session_dict["principal"]["id"] == principal_id:
                        sessions.append(Session.from_dict(session_dict))
                except Exception:
                    continue
        return sessions

    async def count_by_principal(self, principal_id: str) -> int:
        return len(await self.list_by_principal(principal_id))

    async def cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        removed = 0
        async with self._lock:
            for path in self.directory.glob("sess_*.json"):
                try:
                    data = path.read_text(encoding="utf-8")
                    session_dict = json.loads(data)
                    session = Session.from_dict(session_dict)
                    if session.is_expired(now):
                        path.unlink()
                        removed += 1
                except Exception:
                    continue
        return removed

    async def shutdown(self) -> None:
        pass

    def get_stats(self) -> dict[str, Any]:
        files = list(self.directory.glob("sess_*.json"))
        return {
            "total_sessions": len(files),
            "total_size_bytes": sum(p.stat().st_size for p in files),
            "directory": str(self.directory),
        }


# ============================================================================
# RedisStore - Redis-backed storage (production, multi-process)
# ============================================================================


class RedisStore:
    """
    Redis-backed session storage.

    The sessions subsystem's documentation always claimed a ``"redis"`` store
    type; until now the name silently fell back to MemoryStore. This is the
    real implementation: one key per session (JSON), a Redis-managed TTL
    aligned to the session's own expiry, and a per-principal set index for
    ``list_by_principal``.

    Layout::

        <prefix>sess:<id>             → JSON session document
        <prefix>principal:<pid>       → SET of session ids for the principal

    Args:
        redis_client: An async Redis client (``redis.asyncio.Redis``).
        key_prefix:   Prefix for all keys (default ``"aquilia:session:"``).
    """

    def __init__(self, redis_client: Any, key_prefix: str = "aquilia:session:"):
        self.redis = redis_client
        self.prefix = key_prefix

    def _session_key(self, session_id: SessionID) -> str:
        return f"{self.prefix}sess:{session_id}"

    def _principal_key(self, principal_id: str) -> str:
        return f"{self.prefix}principal:{principal_id}"

    @staticmethod
    def _decode(raw: Any) -> str:
        return raw.decode() if isinstance(raw, bytes) else raw

    async def load(self, session_id: SessionID) -> Session | None:
        try:
            raw = await self.redis.get(self._session_key(session_id))
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="redis", cause=str(e))
        if raw is None:
            return None
        try:
            return Session.from_dict(json.loads(self._decode(raw)))
        except SessionStoreCorruptedFault:
            raise
        except Exception as e:
            raise SessionStoreCorruptedFault(message=f"Redis session corrupted: {e}", session_id=str(session_id))

    async def save(self, session: Session) -> None:
        try:
            data = json.dumps(session.to_dict())
            ttl = int((session.expires_at - datetime.now(timezone.utc)).total_seconds())
            key = self._session_key(session.id)

            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.set(key, data, ex=max(1, ttl))
                principal = getattr(session, "principal", None)
                if principal is not None:
                    pipe.sadd(self._principal_key(principal.id), str(session.id))
                    pipe.expire(self._principal_key(principal.id), max(1, ttl) + 3600)
                await pipe.execute()
            session.mark_clean()
        except SessionStoreUnavailableFault:
            raise
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="redis", cause=str(e))

    async def delete(self, session_id: SessionID) -> None:
        try:
            raw = await self.redis.get(self._session_key(session_id))
            await self.redis.delete(self._session_key(session_id))
            if raw is not None:
                try:
                    doc = json.loads(self._decode(raw))
                    principal = doc.get("principal")
                    if principal and principal.get("id"):
                        await self.redis.srem(self._principal_key(principal["id"]), str(session_id))
                except Exception:
                    pass
        except SessionStoreUnavailableFault:
            raise
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="redis", cause=str(e))

    async def exists(self, session_id: SessionID) -> bool:
        try:
            return bool(await self.redis.exists(self._session_key(session_id)))
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="redis", cause=str(e))

    async def list_by_principal(self, principal_id: str) -> list[Session]:
        try:
            ids = await self.redis.smembers(self._principal_key(principal_id))
            sessions: list[Session] = []
            for raw in ids or []:
                session_id = self._decode(raw)
                session = await self.load(session_id)
                if session is not None:
                    sessions.append(session)
            return sessions
        except SessionStoreUnavailableFault:
            raise
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="redis", cause=str(e))

    async def count_by_principal(self, principal_id: str) -> int:
        try:
            return int(await self.redis.scard(self._principal_key(principal_id)))
        except Exception as e:
            raise SessionStoreUnavailableFault(store_name="redis", cause=str(e))

    async def cleanup_expired(self) -> int:
        """Redis evicts expired keys natively — nothing to sweep."""
        return 0

    async def shutdown(self) -> None:
        close = getattr(self.redis, "aclose", None) or getattr(self.redis, "close", None)
        if close is not None:
            try:
                result = close()
                if hasattr(result, "__await__"):
                    await result
            except Exception:
                pass

    def get_stats(self) -> dict[str, Any]:
        return {"store": "redis", "prefix": self.prefix}
