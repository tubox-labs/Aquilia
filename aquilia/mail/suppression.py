"""
AquilaMail — suppression list: recipients that must not be emailed again.

A suppression list is the difference between a mail setup that stays
deliverable and one that gets an entire sending domain blocked.  Providers
judge senders on bounce and complaint rates; continuing to send to an address
that hard-bounced, or to someone who marked mail as spam, is the fastest way
to lose reputation for every other message.  Amazon SES suspends accounts for
it outright.

Two suppression kinds, deliberately distinguished:
    **Permanent** — hard bounce (mailbox does not exist), spam complaint, or
    an explicit unsubscribe.  Never send again without operator action.

    **Temporary** — soft bounce (mailbox full, server down).  Expires, because
    the address will most likely work again and permanently suppressing it
    would silently lose legitimate mail.

Enforcement happens in :class:`~aquilia.mail.service.MailService` before any
provider is contacted, so a suppressed recipient costs nothing and cannot
damage sender reputation.

Examples::

    suppression = MemorySuppressionList()
    await suppression.suppress("bounced@example.com", reason=SuppressionReason.HARD_BOUNCE)

    if await suppression.is_suppressed("bounced@example.com"):
        ...   # skip delivery
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from aquilia.db import get_database

logger = logging.getLogger("aquilia.mail.suppression")

__all__ = [
    "MemorySuppressionList",
    "SQLSuppressionList",
    "SuppressionEntry",
    "SuppressionList",
    "SuppressionReason",
]


class SuppressionReason(str, Enum):
    """
    Why an address is suppressed.

    Attributes:
        HARD_BOUNCE: Address does not exist.  Permanent.
        SOFT_BOUNCE: Temporary failure (mailbox full, server down).  Expires.
        COMPLAINT: Recipient marked mail as spam.  Permanent, and the most
            reputation-damaging signal a provider tracks.
        UNSUBSCRIBE: Recipient opted out.  Permanent.
        MANUAL: Operator-added.  Permanent.
    """

    HARD_BOUNCE = "hard_bounce"
    SOFT_BOUNCE = "soft_bounce"
    COMPLAINT = "complaint"
    UNSUBSCRIBE = "unsubscribe"
    MANUAL = "manual"

    @property
    def is_permanent(self) -> bool:
        """Whether this reason suppresses the address indefinitely."""
        return self is not SuppressionReason.SOFT_BOUNCE


@dataclass
class SuppressionEntry:
    """
    One suppressed recipient.

    Attributes:
        email: Normalised (lower-cased, trimmed) address.
        reason: Why it was suppressed.
        created_at: When suppression began.
        expires_at: When it lapses; ``None`` means permanent.
        provider: Provider that reported the event, when known.
        detail: Provider diagnostic text, for operator debugging.
    """

    email: str
    reason: SuppressionReason
    created_at: datetime
    expires_at: datetime | None = None
    provider: str | None = None
    detail: str | None = None

    @property
    def is_active(self) -> bool:
        """Whether this entry currently blocks delivery."""
        if self.expires_at is None:
            return True
        return datetime.now(timezone.utc) < self.expires_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "email": self.email,
            "reason": self.reason.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "provider": self.provider,
            "detail": self.detail,
            "is_active": self.is_active,
        }


def normalize_email(email: str) -> str:
    """
    Normalise an address for suppression lookups.

    Lower-cases and trims, and unwraps ``Display Name <addr>`` form so that
    suppressing ``a@b.co`` also blocks ``Alice <A@B.co>`` — otherwise a
    display name would be enough to bypass the list.
    """
    email = email.strip()
    if "<" in email and email.endswith(">"):
        email = email.rsplit("<", 1)[1].rstrip(">").strip()
    return email.lower()


class SuppressionList(ABC):
    """Storage contract for suppressed recipients."""

    is_persistent: bool = False

    async def initialize(self) -> None:
        """Prepare storage.  Default: no-op."""
        return None

    @abstractmethod
    async def suppress(
        self,
        email: str,
        *,
        reason: SuppressionReason,
        expires_in: float | None = None,
        provider: str | None = None,
        detail: str | None = None,
    ) -> SuppressionEntry:
        """
        Add or refresh a suppression.

        Args:
            email: Recipient address; normalised before storage.
            reason: Why the address is suppressed.
            expires_in: Seconds until it lapses.  Ignored for permanent
                reasons; defaults to 24 hours for soft bounces.
            provider: Reporting provider.
            detail: Provider diagnostic text.

        Returns:
            The stored entry.
        """

    @abstractmethod
    async def unsuppress(self, email: str) -> bool:
        """Remove a suppression.  Returns whether an entry existed."""

    @abstractmethod
    async def get(self, email: str) -> SuppressionEntry | None:
        """Return the entry for an address, active or not."""

    @abstractmethod
    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[SuppressionEntry]:
        """List entries, newest first."""

    @abstractmethod
    async def cleanup(self) -> int:
        """Delete lapsed temporary entries.  Returns the count removed."""

    async def is_suppressed(self, email: str) -> bool:
        """
        Whether delivery to this address must be skipped.

        Returns ``False`` for a lapsed temporary suppression, so a mailbox
        that was merely full becomes reachable again on its own.
        """
        entry = await self.get(email)
        return entry is not None and entry.is_active

    async def filter_recipients(self, emails: list[str]) -> tuple[list[str], list[str]]:
        """
        Split recipients into deliverable and suppressed.

        Lets a message to several recipients still reach the good ones rather
        than being dropped wholesale because one address bounced earlier.

        Returns:
            ``(deliverable, suppressed)``.
        """
        deliverable: list[str] = []
        suppressed: list[str] = []
        for email in emails:
            if await self.is_suppressed(email):
                suppressed.append(email)
            else:
                deliverable.append(email)
        return deliverable, suppressed


class MemorySuppressionList(SuppressionList):
    """
    In-process suppression list.

    Fine for development and single-process deployments.  Because it is lost
    on restart, a production deployment should use
    :class:`SQLSuppressionList` — otherwise every restart re-enables sending
    to addresses that already bounced.

    Examples::

        suppression = MemorySuppressionList()
        await suppression.suppress("x@y.co", reason=SuppressionReason.COMPLAINT)
        assert await suppression.is_suppressed("X@Y.co")   # normalised
    """

    is_persistent = False

    def __init__(self) -> None:
        self._entries: dict[str, SuppressionEntry] = {}

    async def suppress(
        self,
        email: str,
        *,
        reason: SuppressionReason,
        expires_in: float | None = None,
        provider: str | None = None,
        detail: str | None = None,
    ) -> SuppressionEntry:
        key = normalize_email(email)
        now = datetime.now(timezone.utc)
        expires_at = None
        if not reason.is_permanent:
            expires_at = now + timedelta(seconds=expires_in if expires_in is not None else 86400)

        entry = SuppressionEntry(
            email=key,
            reason=reason,
            created_at=now,
            expires_at=expires_at,
            provider=provider,
            detail=detail,
        )
        self._entries[key] = entry
        logger.info("Suppressed %s (%s)", key, reason.value)
        return entry

    async def unsuppress(self, email: str) -> bool:
        return self._entries.pop(normalize_email(email), None) is not None

    async def get(self, email: str) -> SuppressionEntry | None:
        return self._entries.get(normalize_email(email))

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[SuppressionEntry]:
        entries = sorted(self._entries.values(), key=lambda e: e.created_at, reverse=True)
        return entries[offset : offset + limit]

    async def cleanup(self) -> int:
        stale = [k for k, e in self._entries.items() if not e.is_active]
        for key in stale:
            del self._entries[key]
        return len(stale)

    def __repr__(self) -> str:
        return f"MemorySuppressionList(count={len(self._entries)})"


class SQLSuppressionList(SuppressionList):
    """
    Durable suppression list on the application's database.

    The right choice for production: suppression must outlive the process, or
    a restart resumes sending to addresses that already hard-bounced and the
    sending domain's reputation degrades again.

    Schema (created on :meth:`initialize`)::

        aquilia_mail_suppressions(
            email TEXT PRIMARY KEY, reason TEXT, created_at TEXT,
            expires_at TEXT, provider TEXT, detail TEXT
        )

    Args:
        database: An :class:`~aquilia.db.engine.AquiliaDatabase`; resolved
            from the app when omitted.
        table: Table name.

    Examples::

        suppression = SQLSuppressionList(database=db)
        await suppression.initialize()
    """

    is_persistent = True

    def __init__(self, database: Any = None, *, table: str = "aquilia_mail_suppressions") -> None:
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
        """Create the suppression table if absent."""
        if self._initialized:
            return
        db = await self._database()
        await db.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                email TEXT PRIMARY KEY,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                provider TEXT,
                detail TEXT
            )
            """
        )
        self._initialized = True

    async def _ready(self) -> Any:
        if not self._initialized:
            await self.initialize()
        return await self._database()

    def _row_to_entry(self, row: dict[str, Any]) -> SuppressionEntry:
        expires = row.get("expires_at")
        return SuppressionEntry(
            email=row["email"],
            reason=SuppressionReason(row["reason"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(expires) if expires else None,
            provider=row.get("provider"),
            detail=row.get("detail"),
        )

    async def suppress(
        self,
        email: str,
        *,
        reason: SuppressionReason,
        expires_in: float | None = None,
        provider: str | None = None,
        detail: str | None = None,
    ) -> SuppressionEntry:
        db = await self._ready()
        key = normalize_email(email)
        now = datetime.now(timezone.utc)
        expires_at = None
        if not reason.is_permanent:
            expires_at = now + timedelta(seconds=expires_in if expires_in is not None else 86400)

        params = [
            reason.value,
            now.isoformat(),
            expires_at.isoformat() if expires_at else None,
            provider,
            detail,
        ]
        result = await db.execute(
            f"""
            UPDATE {self.table}
               SET reason = ?, created_at = ?, expires_at = ?, provider = ?, detail = ?
             WHERE email = ?
            """,
            [*params, key],
        )
        if not getattr(result, "rowcount", 0):
            await db.execute(
                f"""
                INSERT INTO {self.table} (email, reason, created_at, expires_at, provider, detail)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [key, *params],
            )

        logger.info("Suppressed %s (%s)", key, reason.value)
        return SuppressionEntry(
            email=key,
            reason=reason,
            created_at=now,
            expires_at=expires_at,
            provider=provider,
            detail=detail,
        )

    async def unsuppress(self, email: str) -> bool:
        db = await self._ready()
        result = await db.execute(f"DELETE FROM {self.table} WHERE email = ?", [normalize_email(email)])
        return bool(getattr(result, "rowcount", 0))

    async def get(self, email: str) -> SuppressionEntry | None:
        db = await self._ready()
        row = await db.fetch_one(f"SELECT * FROM {self.table} WHERE email = ?", [normalize_email(email)])
        return self._row_to_entry(row) if row else None

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[SuppressionEntry]:
        db = await self._ready()
        rows = await db.fetch_all(
            f"SELECT * FROM {self.table} ORDER BY created_at DESC LIMIT {int(limit)} OFFSET {int(offset)}"
        )
        return [self._row_to_entry(r) for r in rows]

    async def cleanup(self) -> int:
        db = await self._ready()
        result = await db.execute(
            f"DELETE FROM {self.table} WHERE expires_at IS NOT NULL AND expires_at <= ?",
            [datetime.now(timezone.utc).isoformat()],
        )
        return int(getattr(result, "rowcount", 0) or 0)

    def __repr__(self) -> str:
        return f"SQLSuppressionList(table={self.table!r})"
