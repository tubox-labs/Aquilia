"""
SMTP Provider -- Production-grade async SMTP delivery via aiosmtplib.

Features:
- Async SMTP with STARTTLS / direct SSL
- MIME construction shared with the SES provider (:mod:`aquilia.mail.mime`)
- AUTH LOGIN/PLAIN and XOAUTH2 (Gmail, Microsoft 365)
- Optional DKIM signing of the outgoing message
- Connection pooling with keep-alive and reconnect logic
- Configurable timeouts, retries, source-address binding
- TLS certificate validation (customisable)
- Health-check via NOOP / EHLO
- Proper multipart MIME with inline images (Content-ID)
- Batch send with connection reuse
- Detailed structured logging and metrics
- Graceful shutdown with connection draining

Dependencies:
    pip install aiosmtplib   (required)
    pip install dkimpy       (only when DKIM signing is enabled)

Usage::

    provider = SMTPProvider(
        name="primary-smtp",
        host="smtp.example.com",
        port=587,
        username="user@example.com",
        password="secret",
        use_tls=True,
    )
    await provider.initialize()
    result = await provider.send(envelope)
    await provider.shutdown()

    # OAuth2 (Gmail / Microsoft 365)
    provider = SMTPProvider(
        name="gmail",
        host="smtp.gmail.com",
        port=587,
        username="user@gmail.com",
        oauth2_token=current_access_token,
    )
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import logging
import ssl
import time
from collections.abc import Sequence
from email.message import Message
from typing import Any

from aquilia.mail.envelope import MailEnvelope
from aquilia.mail.mime import build_mime_message, sign_dkim
from aquilia.mail.providers import ProviderResult, ProviderResultStatus

logger = logging.getLogger("aquilia.mail.providers.smtp")

# ── Transient SMTP error codes (safe to retry) ─────────────────────
_TRANSIENT_CODES = frozenset(
    {
        421,  # Service not available, closing channel
        450,  # Mailbox unavailable (busy / blocked)
        451,  # Local error in processing
        452,  # Insufficient storage
    }
)

# ── Permanent SMTP error codes (do NOT retry) ──────────────────────
_PERMANENT_CODES = frozenset(
    {
        550,  # Mailbox unavailable (not found / no access)
        551,  # User not local
        552,  # Exceeded storage allocation
        553,  # Mailbox name not allowed
        554,  # Transaction failed
        555,  # Parameters not recognised
    }
)


class SMTPProvider:
    """
    Async SMTP mail provider backed by ``aiosmtplib``.

    Supports STARTTLS, direct SSL, AUTH LOGIN/PLAIN, XOAUTH2, connection
    pooling, DKIM signing, and full MIME construction.

    Lifecycle:
        :meth:`initialize` pre-warms one connection so bad credentials or
        TLS settings surface at startup instead of on the first send;
        :meth:`shutdown` drains the pool.

    Async-safety:
        The pool is guarded by an ``asyncio.Lock``.  A connection is owned
        exclusively by one send while checked out, so concurrent sends never
        interleave on the same socket.

    Performance:
        Pooled connections avoid a TCP + TLS + AUTH round trip per message;
        :meth:`send_batch` reuses a single connection across a batch.
        Connections older than ``pool_recycle`` are discarded, since most
        SMTP servers drop idle sessions unilaterally.

    Args:
        name: Provider name used in config, logs and failover ordering.
        host: SMTP server hostname.
        port: SMTP port (587 STARTTLS, 465 implicit SSL, 25 plain).
        username: Account identifier for AUTH.
        password: Password for AUTH LOGIN/PLAIN.  Ignored when
            ``oauth2_token`` is supplied.
        use_tls: Upgrade the connection with STARTTLS.
        use_ssl: Connect with implicit TLS (port 465).
        timeout: Per-operation socket timeout in seconds.
        oauth2_token: OAuth2 access token; when present, XOAUTH2 is used
            instead of password auth (required by Gmail and Microsoft 365,
            which have retired basic auth for SMTP).
        source_address: Local address to bind for outbound connections.
        local_hostname: Name sent in EHLO.
        validate_certs: Verify the server certificate chain.
        client_cert: Client certificate path for mutual TLS.
        client_key: Client private key path for mutual TLS.
        pool_size: Maximum idle connections retained.
        pool_recycle: Seconds after which an idle connection is discarded.
        priority: Failover order; lower is preferred.
        rate_limit_per_min: Advisory send rate enforced by
            :class:`~aquilia.mail.service.MailService`; 0 disables it.
        security: ``MailConfig.security`` used for DKIM signing; ``None``
            disables signing for this provider.

    Attributes:
        supports_batching: Always ``True`` — see :meth:`send_batch`.
        max_batch_size: Largest batch accepted in one connection.

    Examples::

        provider = SMTPProvider(name="mailhog", host="localhost", port=1025,
                                use_tls=False)
        await provider.initialize()
        result = await provider.send(envelope)
        assert result.is_success
    """

    name: str
    provider_type: str = "smtp"
    supports_batching: bool = True
    max_batch_size: int = 100

    def __init__(
        self,
        name: str = "smtp",
        host: str = "localhost",
        port: int = 587,
        username: str | None = None,
        password: str | None = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: float = 30.0,
        *,
        # Advanced options
        oauth2_token: str | None = None,
        source_address: str | None = None,
        local_hostname: str | None = None,
        validate_certs: bool = True,
        client_cert: str | None = None,
        client_key: str | None = None,
        pool_size: int = 3,
        pool_recycle: float = 300.0,
        priority: int = 10,
        rate_limit_per_min: int = 600,
        security: Any = None,
    ):
        self.name = name
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.oauth2_token = oauth2_token
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout
        self.source_address = source_address
        self.local_hostname = local_hostname
        self.validate_certs = validate_certs
        self.client_cert = client_cert
        self.client_key = client_key
        self.pool_size = pool_size
        self.pool_recycle = pool_recycle
        self.priority = priority
        self.rate_limit_per_min = rate_limit_per_min
        self.security = security

        # Connection pool state
        self._pool: list[Any] = []
        self._pool_lock = asyncio.Lock()
        self._pool_created: dict[int, float] = {}  # id(conn) → timestamp
        self._initialized = False

        # Metrics
        self._total_sent = 0
        self._total_errors = 0

    # ── Lifecycle ───────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Pre-warm the connection pool."""
        if self._initialized:
            return
        # Pre-warm one connection to validate settings early
        try:
            conn = await self._create_connection()
            self._pool.append(conn)
            self._pool_created[id(conn)] = time.monotonic()
        except Exception as e:
            logger.warning(f"SMTP pool pre-warm failed (will retry on send): {e}")
        self._initialized = True

    async def shutdown(self) -> None:
        """Drain and close all pooled connections."""
        async with self._pool_lock:
            for conn in self._pool:
                await self._close_connection(conn)
            self._pool.clear()
            self._pool_created.clear()
        self._initialized = False

    # ── Connection Management ───────────────────────────────────────

    def _build_tls_context(self) -> ssl.SSLContext | None:
        """Build an SSL context for TLS/SSL connections."""
        if not self.use_tls and not self.use_ssl:
            return None
        ctx = ssl.create_default_context()
        # On macOS the system cert store is often empty for Python;
        # fall back to the certifi CA bundle when available.
        if ctx.cert_store_stats()["x509_ca"] == 0:
            try:
                import certifi

                ctx.load_verify_locations(certifi.where())
            except (ImportError, OSError):
                pass  # best-effort; user can set validate_certs=False
        if not self.validate_certs:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        if self.client_cert:
            ctx.load_cert_chain(
                certfile=self.client_cert,
                keyfile=self.client_key,
            )
        return ctx

    def _xoauth2_string(self) -> str:
        """
        Build the base64 SASL XOAUTH2 initial-response string.

        Format per Google/Microsoft: ``user=<addr>^Aauth=Bearer <token>^A^A``
        where ``^A`` is ``\\x01``, base64-encoded.

        Raises:
            ValueError: If no username is configured — XOAUTH2 identifies the
                mailbox by address, so a token alone is not sufficient.
        """
        if not self.username:
            raise ValueError("XOAUTH2 requires a username (the mailbox address) alongside the access token")
        raw = f"user={self.username}\x01auth=Bearer {self.oauth2_token}\x01\x01"
        return base64.b64encode(raw.encode()).decode()

    async def _authenticate(self, smtp: Any) -> None:
        """
        Authenticate a freshly connected SMTP session.

        Prefers XOAUTH2 when an OAuth2 token is configured, since Gmail and
        Microsoft 365 no longer accept password auth for SMTP.  Falls back to
        the library's AUTH LOGIN/PLAIN negotiation, and stays anonymous when
        no credentials are set (valid for internal relays).
        """
        if self.oauth2_token:
            await smtp.execute_command(b"AUTH", b"XOAUTH2", self._xoauth2_string().encode())
            return
        if self.username and self.password:
            await smtp.login(self.username, self.password)

    async def _create_connection(self) -> Any:
        """
        Create and authenticate a new ``aiosmtplib`` SMTP connection.

        Raises:
            ImportError: If ``aiosmtplib`` is not installed.
        """
        try:
            import aiosmtplib
        except ImportError:
            raise ImportError("aiosmtplib is required for the SMTP provider. Install it with: pip install aiosmtplib")

        tls_context = self._build_tls_context()

        smtp = aiosmtplib.SMTP(
            hostname=self.host,
            port=self.port,
            use_tls=self.use_ssl,  # use_tls in aiosmtplib = connect with SSL
            start_tls=self.use_tls and not self.use_ssl,
            timeout=self.timeout,
            source_address=self.source_address,
            local_hostname=self.local_hostname,
            tls_context=tls_context,
        )

        await smtp.connect()
        await self._authenticate(smtp)

        return smtp

    async def _acquire_connection(self) -> Any:
        """Acquire a connection from the pool (or create a new one)."""
        async with self._pool_lock:
            now = time.monotonic()
            # Try to find a non-expired connection
            while self._pool:
                conn = self._pool.pop(0)
                created = self._pool_created.pop(id(conn), 0)
                # Check if connection is expired
                if (now - created) > self.pool_recycle:
                    await self._close_connection(conn)
                    continue
                # Test if connection is still alive
                try:
                    await conn.noop()
                    return conn
                except Exception:
                    await self._close_connection(conn)
                    continue

        # Pool exhausted -- create a new connection
        conn = await self._create_connection()
        self._pool_created[id(conn)] = time.monotonic()
        return conn

    async def _release_connection(self, conn: Any) -> None:
        """Return a connection to the pool."""
        async with self._pool_lock:
            if len(self._pool) < self.pool_size:
                self._pool.append(conn)
                self._pool_created[id(conn)] = time.monotonic()
            else:
                await self._close_connection(conn)

    async def _close_connection(self, conn: Any) -> None:
        """Safely close an SMTP connection."""
        try:
            await conn.quit()
        except Exception:
            with contextlib.suppress(Exception):
                conn.close()

    # ── MIME Message Construction ───────────────────────────────────

    def _build_mime_message(self, envelope: MailEnvelope) -> Message:
        """
        Build a MIME message for an envelope.

        Delegates to :func:`aquilia.mail.mime.build_mime_message` so SMTP and
        SES produce byte-identical messages for the same envelope.
        """
        return build_mime_message(envelope)

    async def _transmit(self, conn: Any, envelope: MailEnvelope) -> tuple[Message, Any]:
        """
        Send one envelope over an established connection.

        When DKIM signing is configured the message is serialized and signed
        first, then sent with ``sendmail`` — ``send_message`` would re-render
        the message object and invalidate the signature.

        Returns:
            ``(mime_message, server_response)``.
        """
        mime_msg = self._build_mime_message(envelope)
        recipients = envelope.all_recipients()

        if self.security is not None and getattr(self.security, "dkim_enabled", False):
            raw = sign_dkim(mime_msg.as_bytes(), self.security)
            _errors, response = await conn.sendmail(envelope.from_email, recipients, raw)
        else:
            _errors, response = await conn.send_message(
                mime_msg,
                sender=envelope.from_email,
                recipients=recipients,
            )
        return mime_msg, response

    # ── Send ────────────────────────────────────────────────────────

    async def send(self, envelope: MailEnvelope) -> ProviderResult:
        """
        Send a single envelope via SMTP.

        Acquires a pooled connection, builds (and optionally DKIM-signs) the
        MIME message, transmits it, and returns a structured result.  Errors
        are classified into transient / permanent / rate-limited rather than
        raised, so the service layer can decide whether to fail over or retry.

        Args:
            envelope: Envelope to deliver.

        Returns:
            A :class:`~aquilia.mail.providers.ProviderResult`.

        Examples::

            result = await provider.send(envelope)
            if result.should_retry:
                await asyncio.sleep(result.retry_after or 30)
        """
        conn = None
        try:
            conn = await self._acquire_connection()
            mime_msg, response = await self._transmit(conn, envelope)

            self._total_sent += 1

            return ProviderResult(
                status=ProviderResultStatus.SUCCESS,
                provider_message_id=mime_msg["Message-ID"],
                raw_response={"smtp_response": str(response)},
            )

        except Exception as e:
            self._total_errors += 1
            status, retry_after = self._classify_error(e)
            logger.warning(
                f"SMTP send error via {self.name}: {e} (status={status.value})",
            )
            return ProviderResult(
                status=status,
                error_message=str(e),
                retry_after=retry_after,
            )
        finally:
            if conn is not None:
                with contextlib.suppress(Exception):
                    await self._release_connection(conn)

    async def send_batch(
        self,
        envelopes: Sequence[MailEnvelope],
    ) -> list[ProviderResult]:
        """
        Send a batch of envelopes over a single connection.

        A per-envelope failure is recorded and the batch continues.  A
        connection-level failure aborts the remainder as transient, because
        every subsequent send on that socket would fail the same way.

        Args:
            envelopes: Envelopes to deliver, in order.

        Returns:
            One result per input envelope, positionally aligned.
        """
        results: list[ProviderResult] = []
        conn = None
        try:
            conn = await self._acquire_connection()
            for envelope in envelopes:
                try:
                    mime_msg, _response = await self._transmit(conn, envelope)
                    self._total_sent += 1
                    results.append(
                        ProviderResult(
                            status=ProviderResultStatus.SUCCESS,
                            provider_message_id=mime_msg["Message-ID"],
                        )
                    )
                except Exception as e:
                    self._total_errors += 1
                    status, retry_after = self._classify_error(e)
                    results.append(
                        ProviderResult(
                            status=status,
                            error_message=str(e),
                            retry_after=retry_after,
                        )
                    )
                    # If connection-level error, break out of batch
                    if self._is_connection_error(e):
                        conn = None
                        for _remaining in envelopes[len(results) :]:
                            results.append(
                                ProviderResult(
                                    status=ProviderResultStatus.TRANSIENT_FAILURE,
                                    error_message="Batch aborted due to connection error",
                                )
                            )
                        break
        except Exception as e:
            # Connection acquisition failed entirely
            for _ in envelopes[len(results) :]:
                results.append(
                    ProviderResult(
                        status=ProviderResultStatus.TRANSIENT_FAILURE,
                        error_message=f"Connection failed: {e}",
                    )
                )
        finally:
            if conn is not None:
                with contextlib.suppress(Exception):
                    await self._release_connection(conn)

        return results

    async def health_check(self) -> bool:
        """Check SMTP connectivity via NOOP."""
        try:
            conn = await self._acquire_connection()
            await conn.noop()
            await self._release_connection(conn)
            return True
        except Exception:
            return False

    # ── Error Classification ────────────────────────────────────────

    def _classify_error(self, error: Exception) -> tuple:
        """
        Classify an SMTP error into ProviderResultStatus + retry_after.

        Returns:
            (status, retry_after_seconds or None)
        """
        error_str = str(error)

        # Check for SMTP response codes
        code = self._extract_smtp_code(error)
        if code is not None:
            if code in _TRANSIENT_CODES:
                return ProviderResultStatus.TRANSIENT_FAILURE, 60.0
            if code in _PERMANENT_CODES:
                return ProviderResultStatus.PERMANENT_FAILURE, None
            if 400 <= code < 500:
                return ProviderResultStatus.TRANSIENT_FAILURE, 30.0
            if code >= 500:
                return ProviderResultStatus.PERMANENT_FAILURE, None

        # Connection-level errors are transient
        if self._is_connection_error(error):
            return ProviderResultStatus.TRANSIENT_FAILURE, 10.0

        # Rate limiting keywords
        lower = error_str.lower()
        if "rate" in lower and ("limit" in lower or "exceeded" in lower):
            return ProviderResultStatus.RATE_LIMITED, 120.0
        if "throttl" in lower:
            return ProviderResultStatus.RATE_LIMITED, 60.0

        # Default to transient (assume retry is worth trying)
        return ProviderResultStatus.TRANSIENT_FAILURE, 30.0

    @staticmethod
    def _extract_smtp_code(error: Exception) -> int | None:
        """Try to extract SMTP status code from an error."""
        # aiosmtplib stores code as .code attribute
        if hasattr(error, "code"):
            try:
                return int(error.code)
            except (ValueError, TypeError):
                pass
        # Try parsing from string "421 ..."
        parts = str(error).split()
        if parts:
            try:
                return int(parts[0])
            except ValueError:
                pass
        return None

    @staticmethod
    def _is_connection_error(error: Exception) -> bool:
        """Check if the error is a connection-level failure."""
        return isinstance(
            error,
            (
                ConnectionRefusedError,
                ConnectionResetError,
                ConnectionAbortedError,
                TimeoutError,
                asyncio.TimeoutError,
                OSError,
            ),
        )

    def to_dict(self) -> dict:
        """
        Serialize to a provider config dict for ``MailIntegration``.

        Reports the provider's real ``rate_limit_per_min`` rather than a
        constant, so the admin dashboard shows the limit actually enforced.
        """
        d = {
            "type": self.provider_type,
            "name": self.name,
            "enabled": True,
            "rate_limit_per_min": self.rate_limit_per_min,
            "priority": self.priority,
            "host": self.host,
            "port": self.port,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "timeout": self.timeout,
        }
        if self.username:
            d["username"] = self.username
        if self.password:
            d["password"] = self.password
        extras = {}
        for attr in (
            "source_address",
            "local_hostname",
            "validate_certs",
            "client_cert",
            "client_key",
            "pool_size",
            "pool_recycle",
        ):
            val = getattr(self, attr, None)
            if val is not None:
                extras[attr] = val
        if extras:
            d["config"] = extras
        return d

    def __repr__(self) -> str:
        return f"SMTPProvider(name={self.name!r}, host={self.host!r}, port={self.port}, tls={self.use_tls})"
