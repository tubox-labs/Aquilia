"""
AquilaMail — envelope store: durable record of outbound mail.

An :class:`EnvelopeStore` holds every envelope the application has accepted,
independently of whether it has been delivered yet.  That separation is what
makes queued delivery honest: ``asend_mail()`` can return as soon as the
envelope is *recorded*, and a worker delivers it later, because the record
survives the request — and, with :class:`SQLEnvelopeStore`, the process.

Relationship to the task queue:
    The store holds mail *state*; :mod:`aquilia.tasks` schedules the *work*.
    Mail deliberately does not implement its own scheduler, retry policy, or
    worker pool — those exist in the task engine and would only drift if
    duplicated here.  The delivery task carries an envelope **ID**; the worker
    loads the envelope from the store.  That indirection is what lets mail run
    on a distributed task backend, where a live object could not cross the
    process boundary.

Implementations:
    :class:`MemoryEnvelopeStore`
        Process-local.  Default; adequate when the task backend is also
        in-memory, since neither survives a restart anyway.
    :class:`SQLEnvelopeStore`
        Durable, on the application's own database.  Use with a persistent
        task backend so an accepted email is never lost to a restart.

Examples::

    store = SQLEnvelopeStore(database=db)
    await store.initialize()
    await store.save(envelope)
    pending = await store.list_by_status(EnvelopeStatus.QUEUED)
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

from aquilia.db import get_database
from aquilia.mail.envelope import EnvelopeStatus, MailEnvelope

logger = logging.getLogger("aquilia.mail.store")

__all__ = ["EnvelopeStore", "MemoryEnvelopeStore", "SQLEnvelopeStore"]


class EnvelopeStore(ABC):
    """
    Storage contract for mail envelopes.

    Attributes:
        is_persistent: Whether stored envelopes survive a process restart.
            The mail service reports this so an operator can see whether
            "queued" actually means durable.
    """

    is_persistent: bool = False

    async def initialize(self) -> None:
        """Prepare the store (connect, create schema).  Default: no-op."""
        return None

    async def shutdown(self) -> None:
        """Release store resources.  Default: no-op."""
        return None

    @abstractmethod
    async def save(self, envelope: MailEnvelope) -> None:
        """Insert or update an envelope."""

    @abstractmethod
    async def get(self, envelope_id: str) -> MailEnvelope | None:
        """Fetch an envelope by ID, or ``None`` if unknown."""

    @abstractmethod
    async def list_by_status(
        self,
        status: EnvelopeStatus,
        *,
        limit: int = 100,
    ) -> list[MailEnvelope]:
        """Return envelopes in ``status``, oldest first."""

    @abstractmethod
    async def find_by_digest(self, digest: str, *, within_seconds: float) -> MailEnvelope | None:
        """
        Find a recent envelope with the same content digest.

        Powers send-side deduplication: a retried HTTP request that would
        send the same message twice can be collapsed into one delivery.

        Args:
            digest: Content digest from :meth:`MailEnvelope.compute_digest`.
            within_seconds: How far back to look.  Bounded so identical
                mail *is* sendable again later — a monthly report with
                unchanged content must not be suppressed forever.
        """

    @abstractmethod
    async def find_by_idempotency_key(self, key: str) -> MailEnvelope | None:
        """Find an envelope by caller-supplied idempotency key."""

    @abstractmethod
    async def cleanup(self, max_age_seconds: float) -> int:
        """Delete delivered/failed envelopes older than the cutoff."""

    @abstractmethod
    async def stats(self) -> dict[str, Any]:
        """Counts by status, for the admin dashboard."""


class MemoryEnvelopeStore(EnvelopeStore):
    """
    In-process envelope store.

    Suitable for development and for deployments whose task backend is also
    in-memory.  Envelopes are lost on restart, so a queued-but-unsent message
    disappears with the process — pair with :class:`SQLEnvelopeStore` when
    that matters.

    Args:
        max_envelopes: Retention cap.  Oldest delivered envelopes are evicted
            first so a long-running process cannot grow without bound.

    Examples::

        store = MemoryEnvelopeStore(max_envelopes=5000)
        await store.save(envelope)
    """

    is_persistent = False

    def __init__(self, *, max_envelopes: int = 10000) -> None:
        self._envelopes: dict[str, MailEnvelope] = {}
        self.max_envelopes = max_envelopes

    async def save(self, envelope: MailEnvelope) -> None:
        self._envelopes[envelope.id] = envelope
        if len(self._envelopes) > self.max_envelopes:
            self._evict()

    def _evict(self) -> None:
        """Drop the oldest terminal envelopes; never evict undelivered mail."""
        terminal = [
            e
            for e in self._envelopes.values()
            if e.status in (EnvelopeStatus.SENT, EnvelopeStatus.FAILED, EnvelopeStatus.CANCELLED)
        ]
        terminal.sort(key=lambda e: e.created_at)
        for envelope in terminal[: len(self._envelopes) - self.max_envelopes]:
            self._envelopes.pop(envelope.id, None)

    async def get(self, envelope_id: str) -> MailEnvelope | None:
        return self._envelopes.get(envelope_id)

    async def list_by_status(self, status: EnvelopeStatus, *, limit: int = 100) -> list[MailEnvelope]:
        matched = [e for e in self._envelopes.values() if e.status == status]
        matched.sort(key=lambda e: e.created_at)
        return matched[:limit]

    async def find_by_digest(self, digest: str, *, within_seconds: float) -> MailEnvelope | None:
        if not digest:
            return None
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
        for envelope in self._envelopes.values():
            if envelope.digest == digest and envelope.created_at >= cutoff:
                return envelope
        return None

    async def find_by_idempotency_key(self, key: str) -> MailEnvelope | None:
        if not key:
            return None
        for envelope in self._envelopes.values():
            if envelope.idempotency_key == key:
                return envelope
        return None

    async def cleanup(self, max_age_seconds: float) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        stale = [
            eid
            for eid, e in self._envelopes.items()
            if e.status in (EnvelopeStatus.SENT, EnvelopeStatus.FAILED, EnvelopeStatus.CANCELLED)
            and e.created_at < cutoff
        ]
        for eid in stale:
            del self._envelopes[eid]
        return len(stale)

    async def stats(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for envelope in self._envelopes.values():
            counts[envelope.status.value] = counts.get(envelope.status.value, 0) + 1
        return {"total": len(self._envelopes), "by_status": counts, "persistent": False}

    def __repr__(self) -> str:
        return f"MemoryEnvelopeStore(count={len(self._envelopes)})"


class SQLEnvelopeStore(EnvelopeStore):
    """
    Durable envelope store on the application's database.

    Accepted mail survives a restart, so an outage between "request returned
    200" and "SMTP accepted the message" does not silently lose the email.

    Schema (created on :meth:`initialize`)::

        aquilia_mail_envelopes(
            id TEXT PRIMARY KEY, status TEXT, digest TEXT,
            idempotency_key TEXT, tenant_id TEXT,
            payload TEXT,                      -- full JSON envelope
            created_at TEXT, attempts INTEGER, next_attempt_at TEXT
        )

    Args:
        database: An :class:`~aquilia.db.engine.AquiliaDatabase`.  Resolved
            lazily from the app when omitted.
        table: Table name, for schemas that namespace framework tables.

    Examples::

        store = SQLEnvelopeStore(database=db)
        await store.initialize()
    """

    is_persistent = True

    def __init__(self, database: Any = None, *, table: str = "aquilia_mail_envelopes") -> None:
        if not table.replace("_", "").isalnum():
            raise ValueError(f"Invalid table name: {table!r}")
        self._db = database
        self.table = table
        self._initialized = False

    async def _database(self) -> Any:
        if self._db is not None:
            return self._db

        self._db = get_database()
        return self._db

    async def initialize(self) -> None:
        """Create the envelope table and its lookup indexes if absent."""
        if self._initialized:
            return
        db = await self._database()
        await db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                digest TEXT,
                idempotency_key TEXT,
                tenant_id TEXT,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt_at TEXT
            )
            """
        )
        await db.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table}_status ON {self.table} (status, created_at)")
        await db.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table}_digest ON {self.table} (digest, created_at)")
        await db.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table}_idem ON {self.table} (idempotency_key)")
        self._initialized = True

    async def _ready(self) -> Any:
        if not self._initialized:
            await self.initialize()
        return await self._database()

    async def save(self, envelope: MailEnvelope) -> None:
        """Insert or update an envelope (portable upsert: UPDATE, then INSERT)."""
        db = await self._ready()
        payload = json.dumps(envelope.to_dict())
        result = await db.execute(
            f"""
            UPDATE {self.table}
               SET status = ?, digest = ?, idempotency_key = ?, tenant_id = ?,
                   payload = ?, attempts = ?, next_attempt_at = ?
             WHERE id = ?
            """,
            [
                envelope.status.value,
                envelope.digest,
                envelope.idempotency_key,
                envelope.tenant_id,
                payload,
                envelope.attempts,
                envelope.next_attempt_at.isoformat() if envelope.next_attempt_at else None,
                envelope.id,
            ],
        )
        if getattr(result, "rowcount", 0):
            return

        await db.execute(
            f"""
            INSERT INTO {self.table}
                (id, status, digest, idempotency_key, tenant_id, payload,
                 created_at, attempts, next_attempt_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                envelope.id,
                envelope.status.value,
                envelope.digest,
                envelope.idempotency_key,
                envelope.tenant_id,
                payload,
                envelope.created_at.isoformat(),
                envelope.attempts,
                envelope.next_attempt_at.isoformat() if envelope.next_attempt_at else None,
            ],
        )

    async def get(self, envelope_id: str) -> MailEnvelope | None:
        db = await self._ready()
        row = await db.fetch_one(f"SELECT payload FROM {self.table} WHERE id = ?", [envelope_id])
        return MailEnvelope.from_dict(json.loads(row["payload"])) if row else None

    async def list_by_status(self, status: EnvelopeStatus, *, limit: int = 100) -> list[MailEnvelope]:
        db = await self._ready()
        rows = await db.fetch_all(
            f"SELECT payload FROM {self.table} WHERE status = ? ORDER BY created_at ASC LIMIT {int(limit)}",
            [status.value],
        )
        return [MailEnvelope.from_dict(json.loads(r["payload"])) for r in rows]

    async def find_by_digest(self, digest: str, *, within_seconds: float) -> MailEnvelope | None:
        if not digest:
            return None
        db = await self._ready()
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
        row = await db.fetch_one(
            f"SELECT payload FROM {self.table} WHERE digest = ? AND created_at >= ? ORDER BY created_at DESC LIMIT 1",
            [digest, cutoff.isoformat()],
        )
        return MailEnvelope.from_dict(json.loads(row["payload"])) if row else None

    async def find_by_idempotency_key(self, key: str) -> MailEnvelope | None:
        if not key:
            return None
        db = await self._ready()
        row = await db.fetch_one(
            f"SELECT payload FROM {self.table} WHERE idempotency_key = ? ORDER BY created_at DESC LIMIT 1",
            [key],
        )
        return MailEnvelope.from_dict(json.loads(row["payload"])) if row else None

    async def cleanup(self, max_age_seconds: float) -> int:
        db = await self._ready()
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        result = await db.execute(
            f"DELETE FROM {self.table} WHERE status IN (?, ?, ?) AND created_at < ?",
            [
                EnvelopeStatus.SENT.value,
                EnvelopeStatus.FAILED.value,
                EnvelopeStatus.CANCELLED.value,
                cutoff.isoformat(),
            ],
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def stats(self) -> dict[str, Any]:
        db = await self._ready()
        rows = await db.fetch_all(f"SELECT status, COUNT(*) AS n FROM {self.table} GROUP BY status")
        counts = {r["status"]: int(r["n"]) for r in rows}
        return {"total": sum(counts.values()), "by_status": counts, "persistent": True}

    def __repr__(self) -> str:
        return f"SQLEnvelopeStore(table={self.table!r})"
