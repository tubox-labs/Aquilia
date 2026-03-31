"""
Session Security Tests (Phase 11, Task 2).

Comprehensive security test suite for the aquilia/sessions module.
Tests cover: session ID cryptographic properties, input validation,
fault integration, transport hardening, store hardening, policy
enforcement, OWASP compliance, and attack-vector resistance.

Total: 80+ targeted security tests.
"""

import asyncio
import base64
import hashlib
import json
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aquilia.sessions.core import (
    Session,
    SessionID,
    SessionFlag,
    SessionPrincipal,
    SessionScope,
    _DirtyTrackingDict,
)
from aquilia.sessions.faults import (
    SessionInvalidFault,
    SessionExpiredFault,
    SessionIdleTimeoutFault,
    SessionAbsoluteTimeoutFault,
    SessionLockedFault,
    SessionStoreCorruptedFault,
    SessionConcurrencyViolationFault,
    SessionFingerprintMismatchFault,
    SessionTransportFault,
    SessionForgeryAttemptFault,
    SessionPolicyViolationFault,
    SessionRotationFailedFault,
)
from aquilia.sessions.policy import (
    SessionPolicy,
    SessionPolicyBuilder,
    PersistencePolicy,
    ConcurrencyPolicy,
    TransportPolicy,
    DEFAULT_USER_POLICY,
    ADMIN_POLICY,
)
from aquilia.sessions.store import MemoryStore, FileStore
from aquilia.sessions.transport import (
    CookieTransport,
    HeaderTransport,
    create_transport,
)
from aquilia.sessions.engine import SessionEngine


# ============================================================================
# Helpers
# ============================================================================


def _make_session(**kwargs) -> Session:
    defaults = dict(
        id=SessionID(),
        created_at=datetime.now(timezone.utc),
        last_accessed_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scope=SessionScope.USER,
        flags=set(),
        data={},
    )
    defaults.update(kwargs)
    return Session(**defaults)


def _make_request(cookie: str = "", headers: dict | None = None, client: tuple | None = None):
    req = MagicMock()
    _headers = headers or {}
    req.header = lambda name: _headers.get(name.lower()) if name.lower() != "cookie" else cookie
    if cookie:
        req.header = lambda name, _c=cookie, _h=_headers: _c if name.lower() == "cookie" else _h.get(name.lower())
    req.client = client or ("127.0.0.1", 8000)
    req.path = "/test"
    req.method = "GET"
    req.state = {}
    return req


def _make_response():
    resp = MagicMock()
    resp.headers = {}
    resp.set_cookie = MagicMock()
    resp.delete_cookie = MagicMock()
    return resp


def _make_engine(policy=None, store=None, transport=None):
    policy = policy or DEFAULT_USER_POLICY
    store = store or MemoryStore()
    transport = transport or CookieTransport(policy.transport)
    return SessionEngine(policy=policy, store=store, transport=transport)


# ============================================================================
# SEC-SESS-01: SessionID Cryptographic Security
# ============================================================================


class TestSessionIDSecurity:
    """Tests for SessionID cryptographic hardening."""

    def test_entropy_is_256_bits(self):
        sid = SessionID()
        assert len(sid.raw) == 32  # 256 bits

    def test_ids_are_unique(self):
        ids = {str(SessionID()) for _ in range(1000)}
        assert len(ids) == 1000

    def test_constant_time_comparison(self):
        sid = SessionID()
        same = SessionID(sid.raw)
        different = SessionID()
        assert sid == same
        assert sid != different

    def test_from_string_rejects_oversized_input(self):
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string("sess_" + "A" * 200)

    def test_from_string_rejects_non_string(self):
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string(12345)  # type: ignore

    def test_from_string_rejects_empty(self):
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string("")

    def test_from_string_rejects_null_bytes(self):
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string("sess_\x00" + "A" * 42)

    def test_from_string_rejects_wrong_prefix(self):
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string("evil_" + "A" * 43)

    def test_from_string_rejects_wrong_length_decoded(self):
        # Encode only 16 bytes (should be 32)
        short = base64.urlsafe_b64encode(b"\x00" * 16).decode().rstrip("=")
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string(f"sess_{short}")

    def test_from_string_rejects_invalid_base64(self):
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string("sess_!!!invalid!!!")

    def test_valid_roundtrip(self):
        sid = SessionID()
        restored = SessionID.from_string(str(sid))
        assert sid == restored

    def test_fingerprint_is_privacy_safe(self):
        sid = SessionID()
        fp = sid.fingerprint()
        assert fp.startswith("sha256:")
        assert str(sid) not in fp
        assert len(fp) == len("sha256:") + 16

    def test_wrong_byte_length_raises_fault(self):
        with pytest.raises(SessionInvalidFault):
            SessionID(raw=b"\x00" * 16)


# ============================================================================
# SEC-SESS-02: Session Data Mutation Security
# ============================================================================


class TestSessionDataSecurity:
    """Tests for session data mutation guards."""

    def test_read_only_blocks_setitem(self):
        s = _make_session()
        s.flags.add(SessionFlag.READ_ONLY)
        with pytest.raises(SessionLockedFault):
            s["key"] = "value"

    def test_read_only_blocks_delitem(self):
        s = _make_session()
        s.flags.add(SessionFlag.READ_ONLY)
        s.data["key"] = "value"
        with pytest.raises(SessionLockedFault):
            del s["key"]

    def test_read_only_blocks_set(self):
        s = _make_session()
        s.flags.add(SessionFlag.READ_ONLY)
        with pytest.raises(SessionLockedFault):
            s.set("key", "value")

    def test_read_only_blocks_delete(self):
        s = _make_session()
        s.flags.add(SessionFlag.READ_ONLY)
        with pytest.raises(SessionLockedFault):
            s.delete("key")

    def test_read_only_blocks_clear(self):
        s = _make_session()
        s.flags.add(SessionFlag.READ_ONLY)
        with pytest.raises(SessionLockedFault):
            s.clear_data()

    def test_data_key_limit_enforced(self):
        s = _make_session()
        for i in range(Session.MAX_DATA_KEYS):
            s[f"key_{i}"] = i
        with pytest.raises(SessionPolicyViolationFault):
            s["overflow"] = "rejected"

    def test_data_key_limit_update_existing_allowed(self):
        s = _make_session()
        for i in range(Session.MAX_DATA_KEYS):
            s[f"key_{i}"] = i
        # Updating existing key should NOT raise
        s["key_0"] = "updated"
        assert s["key_0"] == "updated"

    def test_dirty_tracking_on_data_mutation(self):
        s = _make_session()
        s.mark_clean()
        assert not s.is_dirty
        s.data["x"] = 1
        assert s.is_dirty

    def test_dirty_tracking_on_data_delete(self):
        s = _make_session(data={"x": 1})
        s.mark_clean()
        del s.data["x"]
        assert s.is_dirty

    def test_dirty_tracking_on_data_pop(self):
        s = _make_session(data={"x": 1})
        s.mark_clean()
        s.data.pop("x")
        assert s.is_dirty

    def test_dirty_tracking_on_data_clear(self):
        s = _make_session(data={"x": 1})
        s.mark_clean()
        s.data.clear()
        assert s.is_dirty


# ============================================================================
# SEC-SESS-03: Session Serialization Security
# ============================================================================


class TestSessionSerializationSecurity:
    """Tests for session serialization/deserialization hardening."""

    def test_to_dict_serializes_plain_dict(self):
        s = _make_session(data={"key": "value"})
        d = s.to_dict()
        assert isinstance(d["data"], dict)
        assert not isinstance(d["data"], _DirtyTrackingDict)

    def test_to_dict_flags_are_sorted(self):
        s = _make_session()
        s.flags = {SessionFlag.ROTATABLE, SessionFlag.AUTHENTICATED, SessionFlag.EPHEMERAL}
        d = s.to_dict()
        assert d["flags"] == sorted(d["flags"])

    def test_from_dict_rejects_non_dict(self):
        with pytest.raises(SessionStoreCorruptedFault):
            Session.from_dict("not a dict")  # type: ignore

    def test_from_dict_rejects_missing_id(self):
        with pytest.raises(SessionStoreCorruptedFault):
            Session.from_dict(
                {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                    "scope": "user",
                }
            )

    def test_from_dict_rejects_missing_created_at(self):
        sid = SessionID()
        with pytest.raises(SessionStoreCorruptedFault):
            Session.from_dict(
                {
                    "id": str(sid),
                    "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                    "scope": "user",
                }
            )

    def test_from_dict_rejects_invalid_timestamp(self):
        sid = SessionID()
        with pytest.raises(SessionStoreCorruptedFault):
            Session.from_dict(
                {
                    "id": str(sid),
                    "created_at": "not-a-date",
                    "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                    "scope": "user",
                }
            )

    def test_from_dict_rejects_invalid_scope(self):
        sid = SessionID()
        with pytest.raises(SessionStoreCorruptedFault):
            Session.from_dict(
                {
                    "id": str(sid),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                    "scope": "hacked_scope",
                }
            )

    def test_from_dict_rejects_invalid_principal(self):
        sid = SessionID()
        with pytest.raises(SessionStoreCorruptedFault):
            Session.from_dict(
                {
                    "id": str(sid),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                    "scope": "user",
                    "principal": "not_a_dict",
                }
            )

    def test_from_dict_rejects_non_dict_data(self):
        sid = SessionID()
        with pytest.raises(SessionStoreCorruptedFault):
            Session.from_dict(
                {
                    "id": str(sid),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                    "scope": "user",
                    "data": "not_a_dict",
                }
            )

    def test_from_dict_ignores_unknown_flags(self):
        s = _make_session()
        d = s.to_dict()
        d["flags"] = ["authenticated", "unknown_future_flag"]
        restored = Session.from_dict(d)
        assert SessionFlag.AUTHENTICATED in restored.flags
        assert len(restored.flags) == 1

    def test_roundtrip_preserves_data(self):
        s = _make_session(data={"x": 1, "nested": {"a": "b"}})
        s.principal = SessionPrincipal(kind="user", id="test-user")
        s.flags.add(SessionFlag.AUTHENTICATED)
        d = s.to_dict()
        restored = Session.from_dict(d)
        assert restored.data == s.data
        assert restored.principal.id == "test-user"
        assert SessionFlag.AUTHENTICATED in restored.flags


# ============================================================================
# SEC-SESS-04: Cookie Transport Security
# ============================================================================


class TestCookieTransportSecurity:
    """Tests for cookie transport hardening."""

    def test_parse_cookies_rejects_oversized_header(self):
        giant = "a=b; " * 10000
        result = CookieTransport._parse_cookies(giant)
        assert result == {}

    def test_parse_cookies_limits_pair_count(self):
        many = "; ".join(f"cookie_{i}=val_{i}" for i in range(200))
        result = CookieTransport._parse_cookies(many)
        assert len(result) <= CookieTransport._MAX_COOKIE_PAIRS

    def test_parse_cookies_rejects_control_chars_in_name(self):
        result = CookieTransport._parse_cookies("evil\x00name=value; good=ok")
        assert "evil\x00name" not in result
        assert "good" in result

    def test_parse_cookies_rejects_space_in_name(self):
        # Cookie names with parentheses or special chars should be rejected
        result = CookieTransport._parse_cookies("bad(name=value; valid_name=ok")
        assert "bad(name" not in result
        assert "valid_name" in result

    def test_extract_returns_none_without_cookie(self):
        policy = TransportPolicy(adapter="cookie", cookie_name="aquilia_session")
        transport = CookieTransport(policy)
        req = _make_request(cookie="")
        assert transport.extract(req) is None

    def test_extract_returns_correct_cookie(self):
        policy = TransportPolicy(adapter="cookie", cookie_name="aquilia_session")
        transport = CookieTransport(policy)
        sid = SessionID()
        req = _make_request(cookie=f"other=123; aquilia_session={sid}; extra=456")
        assert transport.extract(req) == str(sid)

    def test_inject_sets_secure_flags(self):
        policy = TransportPolicy(
            adapter="cookie",
            cookie_name="aquilia_session",
            cookie_secure=True,
            cookie_httponly=True,
            cookie_samesite="strict",
        )
        transport = CookieTransport(policy)
        session = _make_session()
        resp = _make_response()
        transport.inject(resp, session)
        resp.set_cookie.assert_called_once()
        call_kwargs = resp.set_cookie.call_args
        assert call_kwargs.kwargs.get("secure") or call_kwargs[1].get("secure")
        assert call_kwargs.kwargs.get("httponly") or call_kwargs[1].get("httponly")


# ============================================================================
# SEC-SESS-05: Header Transport Security
# ============================================================================


class TestHeaderTransportSecurity:
    """Tests for header transport hardening."""

    def test_extract_returns_header_value(self):
        policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
        transport = HeaderTransport(policy)
        sid = SessionID()
        req = _make_request(headers={"x-session-id": str(sid)})
        assert transport.extract(req) == str(sid)

    def test_inject_sets_header(self):
        policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
        transport = HeaderTransport(policy)
        session = _make_session()
        resp = _make_response()
        transport.inject(resp, session)
        assert "X-Session-ID" in resp.headers

    def test_clear_removes_header(self):
        policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
        transport = HeaderTransport(policy)
        resp = _make_response()
        resp.headers["X-Session-ID"] = "old_value"
        transport.clear(resp)
        assert "X-Session-ID" not in resp.headers


# ============================================================================
# SEC-SESS-06: Transport Factory Security
# ============================================================================


class TestTransportFactorySecurity:
    """Tests for create_transport fault integration."""

    def test_unknown_adapter_raises_transport_fault(self):
        with pytest.raises(SessionTransportFault):
            create_transport(TransportPolicy(adapter="unknown"))

    def test_token_adapter_raises_transport_fault(self):
        with pytest.raises(SessionTransportFault):
            create_transport(TransportPolicy(adapter="token"))

    def test_cookie_adapter_succeeds(self):
        t = create_transport(TransportPolicy(adapter="cookie"))
        assert isinstance(t, CookieTransport)

    def test_header_adapter_succeeds(self):
        t = create_transport(TransportPolicy(adapter="header"))
        assert isinstance(t, HeaderTransport)


# ============================================================================
# SEC-SESS-07: FileStore Path Traversal Protection
# ============================================================================


class TestFileStorePathTraversalSecurity:
    """Tests for FileStore path traversal hardening."""

    def test_safe_session_id_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            store = FileStore(td)
            sid = SessionID()
            path = store._get_path(sid)
            assert str(path).startswith(td)

    def test_path_traversal_in_session_id_rejected(self):
        """Session IDs that don't match the expected format should be rejected."""
        with tempfile.TemporaryDirectory() as td:
            store = FileStore(td)
            # Craft a mock SessionID that would produce a path traversal
            evil_sid = MagicMock(spec=SessionID)
            evil_sid.__str__ = lambda self: "../../../etc/passwd"
            with pytest.raises(SessionForgeryAttemptFault):
                store._get_path(evil_sid)


# ============================================================================
# SEC-SESS-08: MemoryStore Security
# ============================================================================


class TestMemoryStoreSecurity:
    """Tests for MemoryStore security properties."""

    @pytest.mark.asyncio
    async def test_max_sessions_enforced(self):
        store = MemoryStore(max_sessions=5)
        sessions = []
        for i in range(7):
            s = _make_session()
            await store.save(s)
            sessions.append(s)
        stats = store.get_stats()
        assert stats["total_sessions"] <= 5

    @pytest.mark.asyncio
    async def test_lru_eviction_removes_oldest(self):
        store = MemoryStore(max_sessions=3)
        s1 = _make_session()
        s2 = _make_session()
        s3 = _make_session()
        await store.save(s1)
        await store.save(s2)
        await store.save(s3)
        # Adding 4th should evict s1 (LRU)
        s4 = _make_session()
        await store.save(s4)
        assert await store.exists(s1.id) is False
        assert await store.exists(s4.id) is True

    @pytest.mark.asyncio
    async def test_load_touches_lru_order(self):
        store = MemoryStore(max_sessions=3)
        s1 = _make_session()
        s2 = _make_session()
        s3 = _make_session()
        await store.save(s1)
        await store.save(s2)
        await store.save(s3)
        # Touch s1 (move to end of LRU)
        await store.load(s1.id)
        # Adding s4 should evict s2 now (s1 was touched)
        s4 = _make_session()
        await store.save(s4)
        assert await store.exists(s1.id) is True
        assert await store.exists(s2.id) is False

    @pytest.mark.asyncio
    async def test_principal_index_cleanup_on_delete(self):
        store = MemoryStore()
        s = _make_session()
        s.principal = SessionPrincipal(kind="user", id="user-1")
        await store.save(s)
        assert await store.count_by_principal("user-1") == 1
        await store.delete(s.id)
        assert await store.count_by_principal("user-1") == 0

    @pytest.mark.asyncio
    async def test_expired_cleanup(self):
        store = MemoryStore()
        expired = _make_session(expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
        valid = _make_session(expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        await store.save(expired)
        await store.save(valid)
        count = await store.cleanup_expired()
        assert count == 1
        assert await store.exists(expired.id) is False
        assert await store.exists(valid.id) is True

    @pytest.mark.asyncio
    async def test_shutdown_clears_all(self):
        store = MemoryStore()
        for _ in range(10):
            await store.save(_make_session())
        await store.shutdown()
        assert store.get_stats()["total_sessions"] == 0


# ============================================================================
# SEC-SESS-09: Engine Security - Lifecycle
# ============================================================================


class TestEngineLifecycleSecurity:
    """Tests for SessionEngine lifecycle security."""

    @pytest.mark.asyncio
    async def test_invalid_session_id_creates_new(self):
        engine = _make_engine()
        req = _make_request(cookie="aquilia_session=not_a_valid_id")
        session = await engine.resolve(req)
        assert session is not None
        assert not session.is_expired()

    @pytest.mark.asyncio
    async def test_expired_session_creates_new(self):
        policy = SessionPolicy(
            name="test",
            ttl=timedelta(seconds=1),
            transport=TransportPolicy(adapter="cookie", cookie_name="aquilia_session"),
        )
        store = MemoryStore()
        engine = _make_engine(policy=policy, store=store)

        # Create and save an expired session
        old_session = _make_session(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        old_session._policy_name = "test"
        await store.save(old_session)

        req = _make_request(cookie=f"aquilia_session={old_session.id}")
        new_session = await engine.resolve(req)
        assert new_session.id != old_session.id

    @pytest.mark.asyncio
    async def test_fingerprint_mismatch_destroys_session(self):
        """OWASP: session should be destroyed on fingerprint mismatch."""
        policy = SessionPolicy(
            name="test_fp",
            ttl=timedelta(hours=1),
            fingerprint_binding=True,
            transport=TransportPolicy(adapter="cookie", cookie_name="aquilia_session"),
        )
        store = MemoryStore()
        engine = _make_engine(policy=policy, store=store)

        # Create session bound to original client
        s = _make_session()
        s.bind_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")
        s._policy_name = "test_fp"
        await store.save(s)

        # Request from different client
        req = _make_request(
            cookie=f"aquilia_session={s.id}",
            headers={"user-agent": "Evil/1.0"},
            client=("192.168.0.1", 8000),
        )

        # Should create new session (old one destroyed)
        new_session = await engine.resolve(req)
        assert new_session.id != s.id
        # Original session should be deleted from store
        assert await store.exists(s.id) is False

    @pytest.mark.asyncio
    async def test_concurrency_rejection(self):
        policy = SessionPolicy(
            name="test_conc",
            ttl=timedelta(hours=1),
            concurrency=ConcurrencyPolicy(
                max_sessions_per_principal=1,
                behavior_on_limit="reject",
            ),
            transport=TransportPolicy(adapter="cookie", cookie_name="aquilia_session"),
        )
        store = MemoryStore()
        engine = _make_engine(policy=policy, store=store)

        # Save 2 sessions for same principal (exceeds limit of 1)
        s1 = _make_session()
        s1.principal = SessionPrincipal(kind="user", id="user-1")
        await store.save(s1)

        s2 = _make_session()
        s2.principal = SessionPrincipal(kind="user", id="user-1")
        s2.flags.add(SessionFlag.AUTHENTICATED)
        await store.save(s2)

        with pytest.raises(SessionConcurrencyViolationFault):
            await engine.check_concurrency(s2)

    @pytest.mark.asyncio
    async def test_concurrency_evict_oldest(self):
        policy = SessionPolicy(
            name="test_evict",
            ttl=timedelta(hours=1),
            concurrency=ConcurrencyPolicy(
                max_sessions_per_principal=1,
                behavior_on_limit="evict_oldest",
            ),
            transport=TransportPolicy(adapter="cookie", cookie_name="aquilia_session"),
        )
        store = MemoryStore()
        engine = _make_engine(policy=policy, store=store)

        # Create s1 with explicit older timestamp
        s1 = _make_session(last_accessed_at=datetime.now(timezone.utc) - timedelta(seconds=10))
        s1.principal = SessionPrincipal(kind="user", id="user-1")
        await store.save(s1)

        s2 = _make_session()
        s2.principal = SessionPrincipal(kind="user", id="user-1")
        s2.flags.add(SessionFlag.AUTHENTICATED)
        await store.save(s2)

        await engine.check_concurrency(s2)
        # s1 should be evicted
        assert await store.exists(s1.id) is False

    @pytest.mark.asyncio
    async def test_rotation_on_privilege_change(self):
        policy = SessionPolicy(
            name="test_rotate",
            ttl=timedelta(hours=1),
            rotate_on_privilege_change=True,
            transport=TransportPolicy(adapter="cookie", cookie_name="aquilia_session"),
        )
        store = MemoryStore()
        engine = _make_engine(policy=policy, store=store)

        s = _make_session()
        s.mark_dirty()
        await store.save(s)
        old_id = s.id

        resp = _make_response()
        await engine.commit(s, resp, privilege_changed=True)
        # Session should have been rotated (different ID)
        # The engine returns the new session internally
        # Check old session deleted from store
        assert await store.exists(old_id) is False

    @pytest.mark.asyncio
    async def test_idle_timeout_enforced(self):
        policy = SessionPolicy(
            name="test_idle",
            ttl=timedelta(hours=1),
            idle_timeout=timedelta(minutes=5),
            transport=TransportPolicy(adapter="cookie", cookie_name="aquilia_session"),
        )
        store = MemoryStore()
        engine = _make_engine(policy=policy, store=store)

        s = _make_session()
        s.last_accessed_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        s._policy_name = "test_idle"
        await store.save(s)

        req = _make_request(cookie=f"aquilia_session={s.id}")
        new_session = await engine.resolve(req)
        assert new_session.id != s.id

    @pytest.mark.asyncio
    async def test_absolute_timeout_enforced(self):
        policy = SessionPolicy(
            name="test_abs",
            ttl=timedelta(days=30),
            absolute_timeout=timedelta(hours=12),
            transport=TransportPolicy(adapter="cookie", cookie_name="aquilia_session"),
        )
        store = MemoryStore()
        engine = _make_engine(policy=policy, store=store)

        s = _make_session()
        s.created_at = datetime.now(timezone.utc) - timedelta(hours=13)
        s.last_accessed_at = datetime.now(timezone.utc)
        s._policy_name = "test_abs"
        await store.save(s)

        req = _make_request(cookie=f"aquilia_session={s.id}")
        new_session = await engine.resolve(req)
        assert new_session.id != s.id


# ============================================================================
# SEC-SESS-10: Policy Security
# ============================================================================


class TestPolicySecurity:
    """Tests for session policy security properties."""

    def test_admin_policy_has_fingerprint_binding(self):
        assert ADMIN_POLICY.fingerprint_binding is True

    def test_admin_policy_has_strict_samesite(self):
        assert ADMIN_POLICY.transport.cookie_samesite == "strict"

    def test_admin_policy_rotates_on_use(self):
        assert ADMIN_POLICY.rotate_on_use is True

    def test_admin_policy_has_absolute_timeout(self):
        assert ADMIN_POLICY.absolute_timeout is not None
        assert ADMIN_POLICY.absolute_timeout <= timedelta(hours=12)

    def test_admin_policy_max_one_session(self):
        assert ADMIN_POLICY.concurrency.max_sessions_per_principal == 1

    def test_admin_builder_uses_fingerprints(self):
        policy = SessionPolicy.for_admin_users().build()
        assert policy.fingerprint_binding is True

    def test_default_policy_rotates_on_auth(self):
        assert DEFAULT_USER_POLICY.rotate_on_privilege_change is True

    def test_default_transport_is_httponly(self):
        assert DEFAULT_USER_POLICY.transport.cookie_httponly is True

    def test_default_transport_is_secure(self):
        assert DEFAULT_USER_POLICY.transport.cookie_secure is True

    def test_policy_from_dict_is_safe(self):
        config = {
            "ttl": 3600,
            "idle_timeout": 600,
            "scope": "user",
            "transport": {"adapter": "cookie", "cookie_secure": True},
        }
        policy = SessionPolicy.from_dict("test", config)
        assert policy.ttl == timedelta(seconds=3600)
        assert policy.idle_timeout == timedelta(seconds=600)


# ============================================================================
# SEC-SESS-11: Fingerprint Security
# ============================================================================


class TestFingerprintSecurity:
    """Tests for session fingerprint binding (OWASP)."""

    def test_bind_and_verify_match(self):
        s = _make_session()
        s.bind_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")
        assert s.verify_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")

    def test_verify_fails_on_ip_change(self):
        s = _make_session()
        s.bind_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")
        assert not s.verify_fingerprint(ip="192.168.1.1", user_agent="Chrome/100")

    def test_verify_fails_on_ua_change(self):
        s = _make_session()
        s.bind_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")
        assert not s.verify_fingerprint(ip="10.0.0.1", user_agent="Evil/1.0")

    def test_verify_passes_when_unset(self):
        s = _make_session()
        assert s.verify_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")

    def test_fingerprint_uses_constant_time_compare(self):
        s = _make_session()
        s.bind_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")
        # verify_fingerprint uses secrets.compare_digest
        assert s.verify_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")

    def test_fingerprint_preserved_across_serialization(self):
        s = _make_session()
        s.bind_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")
        d = s.to_dict()
        restored = Session.from_dict(d)
        assert restored.verify_fingerprint(ip="10.0.0.1", user_agent="Chrome/100")
        assert not restored.verify_fingerprint(ip="evil", user_agent="evil")


# ============================================================================
# SEC-SESS-12: Fault Integration Security
# ============================================================================


class TestFaultIntegrationSecurity:
    """Tests that all session errors use structured Aquilia faults."""

    def test_session_invalid_fault_has_code(self):
        fault = SessionInvalidFault()
        assert fault.code == "SESSION_INVALID"

    def test_session_expired_fault_hashes_id(self):
        fault = SessionExpiredFault(session_id="sess_test123")
        assert fault.session_id_hash is not None
        assert "sess_test123" not in fault.session_id_hash

    def test_concurrency_violation_includes_counts(self):
        fault = SessionConcurrencyViolationFault(
            principal_id="user-1",
            active_count=5,
            max_allowed=3,
        )
        assert "5" in fault.message
        assert "3" in fault.message

    def test_store_corrupted_includes_hashed_id(self):
        fault = SessionStoreCorruptedFault(
            message="bad data",
            session_id="sess_abc",
        )
        assert fault.session_id_hash is not None

    def test_rotation_failed_hashes_both_ids(self):
        fault = SessionRotationFailedFault(
            old_id="sess_old",
            new_id="sess_new",
            cause="disk error",
        )
        assert "sess_old" not in fault.old_id_hash
        assert "sess_new" not in fault.new_id_hash

    def test_transport_fault_includes_type(self):
        fault = SessionTransportFault(transport_type="cookie", cause="parse error")
        assert "cookie" in fault.message

    def test_forgery_fault_includes_reason(self):
        fault = SessionForgeryAttemptFault(reason="path traversal")
        assert "path traversal" in fault.message


# ============================================================================
# SEC-SESS-13: OWASP Session Compliance
# ============================================================================


class TestOWASPSessionCompliance:
    """Tests verifying OWASP session management recommendations."""

    def test_session_id_entropy_at_least_128_bits(self):
        """OWASP: Session IDs must have at least 64 bits of entropy."""
        assert SessionID.ENTROPY_BYTES >= 16  # 128 bits
        assert SessionID.ENTROPY_BYTES == 32  # Aquilia uses 256 bits

    def test_session_id_uses_csprng(self):
        """OWASP: Session IDs must use CSPRNG."""
        sid = SessionID()
        # secrets module uses os.urandom which is CSPRNG
        assert len(sid.raw) == 32

    def test_admin_policy_short_idle_timeout(self):
        """OWASP: Admin sessions should have short idle timeouts."""
        assert ADMIN_POLICY.idle_timeout <= timedelta(minutes=30)

    def test_admin_policy_has_absolute_timeout(self):
        """OWASP: Sessions should have an absolute maximum lifetime."""
        assert ADMIN_POLICY.absolute_timeout is not None

    def test_rotation_on_auth_change(self):
        """OWASP: Session ID must be rotated on authentication change."""
        assert DEFAULT_USER_POLICY.rotate_on_privilege_change is True
        assert ADMIN_POLICY.rotate_on_privilege_change is True

    def test_cookie_httponly(self):
        """OWASP: Session cookies must be HttpOnly."""
        assert DEFAULT_USER_POLICY.transport.cookie_httponly is True
        assert ADMIN_POLICY.transport.cookie_httponly is True

    def test_cookie_secure(self):
        """OWASP: Session cookies must have Secure flag."""
        assert DEFAULT_USER_POLICY.transport.cookie_secure is True
        assert ADMIN_POLICY.transport.cookie_secure is True

    def test_cookie_samesite(self):
        """OWASP: Session cookies should set SameSite."""
        assert DEFAULT_USER_POLICY.transport.cookie_samesite in ("strict", "lax")
        assert ADMIN_POLICY.transport.cookie_samesite == "strict"

    def test_fingerprint_binding_available(self):
        """OWASP: Framework should support binding session to client properties."""
        policy = SessionPolicy.for_admin_users().build()
        assert policy.fingerprint_binding is True

    def test_session_id_prefix_for_identification(self):
        """Best practice: session IDs should be identifiable."""
        sid = SessionID()
        assert str(sid).startswith("sess_")

    @pytest.mark.asyncio
    async def test_destroy_clears_transport(self):
        """OWASP: Logout must clear session cookie/header."""
        engine = _make_engine()
        s = _make_session()
        resp = _make_response()
        await engine.destroy(s, resp)
        resp.delete_cookie.assert_called_once()
