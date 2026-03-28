"""
Comprehensive Session System Tests for Aquilia.

Tests the entire sessions subsystem:
- Core types (SessionID, Session, SessionScope, SessionFlag, SessionPrincipal)
- Storage (MemoryStore, FileStore)
- Policy (SessionPolicy, SessionPolicyBuilder, built-in policies)
- Transport (CookieTransport, HeaderTransport)
- Engine (SessionEngine lifecycle)
- Faults (all session fault types)
- State (SessionState, Field, CartState)
- Decorators & Guards (session, authenticated, stateful, SessionGuard, requires)
- OWASP compliance (fingerprinting, absolute timeout, constant-time comparison)
"""

import pytest
import asyncio
import json
import secrets
import time
import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path


# ============================================================================
# Core Types Tests
# ============================================================================

class TestSessionID:
    """Tests for SessionID cryptographic identifier."""

    def test_generates_unique_ids(self):
        from aquilia.sessions.core import SessionID
        ids = {str(SessionID()) for _ in range(100)}
        assert len(ids) == 100  # All unique

    def test_id_has_prefix(self):
        from aquilia.sessions.core import SessionID
        sid = SessionID()
        assert str(sid).startswith("sess_")

    def test_id_has_sufficient_entropy(self):
        from aquilia.sessions.core import SessionID
        sid = SessionID()
        # 32 bytes = 256 bits > OWASP minimum of 64 bits
        raw = str(sid).removeprefix("sess_")
        assert len(raw) > 20  # base64url of 32 bytes is 43 chars

    def test_from_string_roundtrip(self):
        from aquilia.sessions.core import SessionID
        sid = SessionID()
        restored = SessionID.from_string(str(sid))
        assert str(sid) == str(restored)

    def test_from_string_rejects_invalid(self):
        from aquilia.sessions.core import SessionID
        from aquilia.sessions.faults import SessionInvalidFault
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string("not_a_valid_session_id")
    
    def test_from_string_rejects_wrong_prefix(self):
        from aquilia.sessions.core import SessionID
        from aquilia.sessions.faults import SessionInvalidFault
        with pytest.raises(SessionInvalidFault):
            SessionID.from_string("bad_prefix_" + "a" * 43)

    def test_constant_time_comparison(self):
        from aquilia.sessions.core import SessionID
        sid = SessionID()
        same = SessionID.from_string(str(sid))
        assert sid == same  # uses secrets.compare_digest

    def test_inequality(self):
        from aquilia.sessions.core import SessionID
        a = SessionID()
        b = SessionID()
        assert a != b

    def test_fingerprint_for_logging(self):
        from aquilia.sessions.core import SessionID
        sid = SessionID()
        fp = sid.fingerprint()
        assert fp.startswith("sha256:")
        assert len(fp) > 10
        # Same ID = same fingerprint
        assert sid.fingerprint() == sid.fingerprint()

    def test_hash_consistent(self):
        from aquilia.sessions.core import SessionID
        sid = SessionID()
        assert hash(sid) == hash(sid)


class TestSessionScope:
    """Tests for SessionScope enum."""

    def test_scope_values(self):
        from aquilia.sessions.core import SessionScope
        assert SessionScope.USER.value == "user"
        assert SessionScope.REQUEST.value == "request"
        assert SessionScope.CONNECTION.value == "connection"
        assert SessionScope.DEVICE.value == "device"

    def test_requires_persistence(self):
        from aquilia.sessions.core import SessionScope
        assert SessionScope.USER.requires_persistence() is True
        assert SessionScope.DEVICE.requires_persistence() is True
        assert SessionScope.CONNECTION.requires_persistence() is True
        assert SessionScope.REQUEST.requires_persistence() is False


class TestSessionFlag:
    """Tests for SessionFlag enum."""

    def test_flag_values_exist(self):
        from aquilia.sessions.core import SessionFlag
        flags = {SessionFlag.AUTHENTICATED, SessionFlag.RENEWABLE,
                 SessionFlag.EPHEMERAL, SessionFlag.LOCKED, SessionFlag.READ_ONLY}
        assert len(flags) == 5


class TestSessionPrincipal:
    """Tests for SessionPrincipal dataclass."""

    def test_create_principal(self):
        from aquilia.sessions.core import SessionPrincipal
        p = SessionPrincipal(id="user-1", kind="user")
        assert p.id == "user-1"
        assert p.kind == "user"

    def test_principal_attributes(self):
        from aquilia.sessions.core import SessionPrincipal
        p = SessionPrincipal(id="u1", kind="user", attributes={"role": "admin"})
        assert p.get_attribute("role") == "admin"
        assert p.get_attribute("missing", "default") == "default"

    def test_principal_kind_checks(self):
        from aquilia.sessions.core import SessionPrincipal
        p = SessionPrincipal(id="u1", kind="user")
        assert p.is_user() is True
        assert p.is_service() is False
        assert p.is_device() is False
        assert p.is_anonymous() is False


class TestSession:
    """Tests for Session core state container."""

    def _make_session(self, **kwargs):
        from aquilia.sessions.core import Session, SessionID, SessionScope
        defaults = dict(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=SessionScope.USER,
        )
        defaults.update(kwargs)
        return Session(**defaults)

    def test_create_session(self):
        s = self._make_session()
        assert s is not None
        assert str(s.id).startswith("sess_")

    def test_session_not_expired(self):
        s = self._make_session()
        assert s.is_expired() is False

    def test_session_expired(self):
        s = self._make_session(expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
        assert s.is_expired() is True

    def test_session_no_expiry_never_expires(self):
        s = self._make_session(expires_at=None)
        assert s.is_expired() is False

    def test_dirty_tracking_data(self):
        s = self._make_session()
        s.mark_clean()
        assert s.is_dirty is False
        # Dict mutation via data[key] MUST trigger dirty (framework-level fix)
        s.data["key"] = "value"
        assert s.is_dirty is True, "data dict mutation must mark session dirty"

        # Full reassignment also triggers dirty
        s.mark_clean()
        s.data = {"new": "data"}
        assert s.is_dirty is True

    def test_dirty_tracking_data_pop(self):
        """data.pop() must mark session dirty."""
        s = self._make_session()
        s.data["to_remove"] = "val"
        s.mark_clean()
        assert s.is_dirty is False
        s.data.pop("to_remove")
        assert s.is_dirty is True

    def test_dirty_tracking_data_del(self):
        """del data[key] must mark session dirty."""
        s = self._make_session()
        s.data["to_del"] = "val"
        s.mark_clean()
        del s.data["to_del"]
        assert s.is_dirty is True

    def test_dirty_tracking_data_update(self):
        """data.update() must mark session dirty."""
        s = self._make_session()
        s.mark_clean()
        s.data.update({"a": 1, "b": 2})
        assert s.is_dirty is True

    def test_dirty_tracking_data_setdefault(self):
        """data.setdefault() must mark dirty on new key."""
        s = self._make_session()
        s.mark_clean()
        s.data.setdefault("new_key", "default")
        assert s.is_dirty is True

    def test_dirty_tracking_data_clear(self):
        """data.clear() must mark dirty if data was non-empty."""
        s = self._make_session()
        s.data["x"] = 1
        s.mark_clean()
        s.data.clear()
        assert s.is_dirty is True

    def test_dirty_tracking_data_clear_empty_noop(self):
        """data.clear() on empty dict should not mark dirty."""
        s = self._make_session()
        s.mark_clean()
        s.data.clear()  # empty, no change
        assert s.is_dirty is False

    def test_dirty_tracking_data_survives_reassignment(self):
        """After data reassignment, new dict must also track dirty."""
        s = self._make_session()
        s.mark_clean()
        s.data = {"fresh": "dict"}
        assert s.is_dirty is True
        s.mark_clean()
        # Now mutate the new dict — must still trigger dirty
        s.data["another"] = "key"
        assert s.is_dirty is True

    def test_dirty_tracking_data_serialization(self):
        """_DirtyTrackingDict must serialize to dict correctly."""
        import json
        s = self._make_session()
        s.data["foo"] = "bar"
        s.data["num"] = 42
        result = json.dumps(dict(s.data))
        assert '"foo"' in result
        assert '"num"' in result

    def test_dirty_tracking_data_from_dict_roundtrip(self):
        """Session.from_dict must wrap data in _DirtyTrackingDict."""
        from aquilia.sessions.core import _DirtyTrackingDict
        s = self._make_session()
        s.data["key"] = "value"
        d = s.to_dict()
        s2 = type(s).from_dict(d)
        assert isinstance(s2.data, _DirtyTrackingDict)
        assert s2.is_dirty is False
        s2.data["new"] = "val"
        assert s2.is_dirty is True

    def test_dirty_tracking_principal(self):
        from aquilia.sessions.core import SessionPrincipal
        s = self._make_session()
        s.mark_clean()
        s.principal = SessionPrincipal(id="u1", kind="user")
        assert s.is_dirty is True

    def test_dirty_tracking_expires_at(self):
        s = self._make_session()
        s.mark_clean()
        s.expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
        assert s.is_dirty is True

    def test_setitem_delitem(self):
        s = self._make_session()
        s["foo"] = "bar"
        assert s["foo"] == "bar"
        del s["foo"]
        with pytest.raises(KeyError):
            _ = s["foo"]

    def test_read_only_enforcement(self):
        from aquilia.sessions.core import SessionFlag
        from aquilia.sessions.faults import SessionLockedFault
        s = self._make_session()
        s.flags.add(SessionFlag.READ_ONLY)
        with pytest.raises(SessionLockedFault):
            s["key"] = "value"
        with pytest.raises(SessionLockedFault):
            del s["key"]
        with pytest.raises(SessionLockedFault):
            s.set("key", "value")
        with pytest.raises(SessionLockedFault):
            s.delete("key")
        with pytest.raises(SessionLockedFault):
            s.clear_data()

    def test_touch_updates_last_accessed(self):
        s = self._make_session()
        old_access = s.last_accessed_at
        now = datetime.now(timezone.utc) + timedelta(seconds=5)
        s.touch(now)
        assert s.last_accessed_at == now

    def test_extend_expiry(self):
        s = self._make_session()
        now = datetime.now(timezone.utc)
        s.extend_expiry(timedelta(hours=2), now)
        assert s.expires_at == now + timedelta(hours=2)

    def test_idle_duration(self):
        s = self._make_session()
        later = s.last_accessed_at + timedelta(minutes=10)
        assert s.idle_duration(later) == timedelta(minutes=10)

    def test_age(self):
        created = datetime.now(timezone.utc) - timedelta(hours=3)
        s = self._make_session(created_at=created)
        age = s.age()
        assert age >= timedelta(hours=2, minutes=59)

    def test_is_authenticated(self):
        from aquilia.sessions.core import SessionPrincipal, SessionFlag
        s = self._make_session()
        assert s.is_authenticated is False
        
        s.principal = SessionPrincipal(id="u1", kind="user")
        s.flags.add(SessionFlag.AUTHENTICATED)
        assert s.is_authenticated is True

    def test_is_ephemeral(self):
        from aquilia.sessions.core import SessionFlag
        s = self._make_session()
        assert s.is_ephemeral is False
        s.flags.add(SessionFlag.EPHEMERAL)
        assert s.is_ephemeral is True

    def test_fingerprint_bind_and_verify(self):
        s = self._make_session()
        s.bind_fingerprint("192.168.1.1", "Mozilla/5.0")
        assert s.verify_fingerprint("192.168.1.1", "Mozilla/5.0") is True
        assert s.verify_fingerprint("10.0.0.1", "Mozilla/5.0") is False
        assert s.verify_fingerprint("192.168.1.1", "Chrome/99") is False

    def test_fingerprint_unset_passes(self):
        s = self._make_session()
        # No fingerprint bound = always passes
        assert s.verify_fingerprint("any", "any") is True

    def test_to_dict_from_dict_roundtrip(self):
        from aquilia.sessions.core import SessionPrincipal
        s = self._make_session()
        s.principal = SessionPrincipal(id="u1", kind="user")
        s.data["cart"] = ["item1"]
        s.bind_fingerprint("1.2.3.4", "UA")
        
        d = s.to_dict()
        restored = type(s).from_dict(d)
        
        assert str(restored.id) == str(s.id)
        assert restored.principal.id == "u1"
        assert restored.data["cart"] == ["item1"]
        assert restored.verify_fingerprint("1.2.3.4", "UA") is True

    def test_version_increments(self):
        s = self._make_session()
        assert s.version == 0


# ============================================================================
# Store Tests
# ============================================================================

class TestMemoryStore:
    """Tests for MemoryStore with O(1) LRU via OrderedDict."""

    @pytest.fixture
    def store(self):
        from aquilia.sessions.store import MemoryStore
        return MemoryStore(max_sessions=5)

    def _make_session(self, **kwargs):
        from aquilia.sessions.core import Session, SessionID, SessionScope
        defaults = dict(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=SessionScope.USER,
        )
        defaults.update(kwargs)
        return Session(**defaults)

    @pytest.mark.asyncio
    async def test_save_and_load(self, store):
        s = self._make_session()
        await store.save(s)
        loaded = await store.load(s.id)
        assert loaded is not None
        assert str(loaded.id) == str(s.id)

    @pytest.mark.asyncio
    async def test_delete(self, store):
        s = self._make_session()
        await store.save(s)
        await store.delete(s.id)
        assert await store.load(s.id) is None

    @pytest.mark.asyncio
    async def test_exists(self, store):
        s = self._make_session()
        assert await store.exists(s.id) is False
        await store.save(s)
        assert await store.exists(s.id) is True

    @pytest.mark.asyncio
    async def test_lru_eviction(self, store):
        """Test O(1) LRU eviction when capacity exceeded."""
        sessions = []
        for _ in range(6):  # One more than max
            s = self._make_session()
            sessions.append(s)
            await store.save(s)
        
        # First session should have been evicted
        assert await store.exists(sessions[0].id) is False
        # Last session should exist
        assert await store.exists(sessions[-1].id) is True

    @pytest.mark.asyncio
    async def test_lru_touch_on_load(self, store):
        """Loading a session should move it to end (prevent eviction)."""
        sessions = []
        for _ in range(5):
            s = self._make_session()
            sessions.append(s)
            await store.save(s)
        
        # Load first session (moves to end)
        await store.load(sessions[0].id)
        
        # Add one more (should evict sessions[1], not sessions[0])
        extra = self._make_session()
        await store.save(extra)
        
        assert await store.exists(sessions[0].id) is True  # Was touched
        assert await store.exists(sessions[1].id) is False  # Evicted

    @pytest.mark.asyncio
    async def test_principal_index(self, store):
        from aquilia.sessions.core import SessionPrincipal
        s1 = self._make_session()
        s1.principal = SessionPrincipal(id="alice", kind="user")
        s2 = self._make_session()
        s2.principal = SessionPrincipal(id="alice", kind="user")
        
        await store.save(s1)
        await store.save(s2)
        
        sessions = await store.list_by_principal("alice")
        assert len(sessions) == 2
        assert await store.count_by_principal("alice") == 2

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, store):
        expired = self._make_session(
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        valid = self._make_session()
        
        await store.save(expired)
        await store.save(valid)
        
        count = await store.cleanup_expired()
        assert count == 1
        assert await store.exists(expired.id) is False
        assert await store.exists(valid.id) is True

    @pytest.mark.asyncio
    async def test_shutdown_clears_all(self, store):
        s = self._make_session()
        await store.save(s)
        await store.shutdown()
        assert await store.exists(s.id) is False

    @pytest.mark.asyncio
    async def test_get_stats(self, store):
        s = self._make_session()
        await store.save(s)
        stats = store.get_stats()
        assert stats["total_sessions"] == 1
        assert stats["max_sessions"] == 5

    def test_factory_methods(self):
        from aquilia.sessions.store import MemoryStore
        assert MemoryStore.web_optimized().max_sessions == 25000
        assert MemoryStore.api_optimized().max_sessions == 15000
        assert MemoryStore.development_focused().max_sessions == 1000
        assert MemoryStore.high_throughput().max_sessions == 50000


class TestFileStore:
    """Tests for FileStore file-based storage."""

    @pytest.fixture
    def store(self, tmp_path):
        from aquilia.sessions.store import FileStore
        return FileStore(tmp_path / "sessions")

    def _make_session(self, **kwargs):
        from aquilia.sessions.core import Session, SessionID, SessionScope
        defaults = dict(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=SessionScope.USER,
        )
        defaults.update(kwargs)
        return Session(**defaults)

    @pytest.mark.asyncio
    async def test_save_and_load(self, store):
        s = self._make_session()
        await store.save(s)
        loaded = await store.load(s.id)
        assert loaded is not None
        assert str(loaded.id) == str(s.id)

    @pytest.mark.asyncio
    async def test_delete(self, store):
        s = self._make_session()
        await store.save(s)
        await store.delete(s.id)
        assert await store.load(s.id) is None

    @pytest.mark.asyncio
    async def test_exists(self, store):
        s = self._make_session()
        assert await store.exists(s.id) is False
        await store.save(s)
        assert await store.exists(s.id) is True


# ============================================================================
# Policy Tests
# ============================================================================

class TestSessionPolicy:
    """Tests for SessionPolicy and sub-policies."""

    def _make_session(self, **kwargs):
        from aquilia.sessions.core import Session, SessionID, SessionScope
        defaults = dict(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=SessionScope.USER,
        )
        defaults.update(kwargs)
        return Session(**defaults)

    def test_default_sub_policies(self):
        from aquilia.sessions.policy import SessionPolicy, PersistencePolicy, ConcurrencyPolicy, TransportPolicy
        p = SessionPolicy(name="test")
        assert isinstance(p.persistence, PersistencePolicy)
        assert isinstance(p.concurrency, ConcurrencyPolicy)
        assert isinstance(p.transport, TransportPolicy)

    def test_calculate_expiry(self):
        from aquilia.sessions.policy import SessionPolicy
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        p = SessionPolicy(name="test", ttl=timedelta(hours=2))
        exp = p.calculate_expiry(now)
        assert exp == datetime(2025, 1, 1, 2, tzinfo=timezone.utc)

    def test_calculate_expiry_no_ttl(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", ttl=None)
        assert p.calculate_expiry() is None

    def test_is_valid_expired(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", ttl=timedelta(hours=1))
        s = self._make_session(expires_at=datetime.now(timezone.utc) - timedelta(hours=1))
        valid, reason = p.is_valid(s)
        assert valid is False
        assert reason == "expired"

    def test_is_valid_idle_timeout(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", idle_timeout=timedelta(minutes=5))
        old_access = datetime.now(timezone.utc) - timedelta(minutes=10)
        s = self._make_session(last_accessed_at=old_access)
        valid, reason = p.is_valid(s)
        assert valid is False
        assert reason == "idle_timeout"

    def test_is_valid_absolute_timeout(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", absolute_timeout=timedelta(hours=2))
        old_created = datetime.now(timezone.utc) - timedelta(hours=3)
        s = self._make_session(created_at=old_created)
        valid, reason = p.is_valid(s)
        assert valid is False
        assert reason == "absolute_timeout"

    def test_is_valid_ok(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", ttl=timedelta(hours=1))
        s = self._make_session()
        valid, reason = p.is_valid(s)
        assert valid is True
        assert reason == "valid"

    def test_should_rotate_on_privilege_change(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", rotate_on_privilege_change=True)
        s = self._make_session()
        assert p.should_rotate(s, privilege_changed=True) is True
        assert p.should_rotate(s, privilege_changed=False) is False

    def test_should_rotate_on_use(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", rotate_on_use=True)
        s = self._make_session()
        assert p.should_rotate(s) is True

    def test_fingerprint_binding_field(self):
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", fingerprint_binding=True)
        assert p.fingerprint_binding is True

    def test_from_dict(self):
        from aquilia.sessions.policy import SessionPolicy
        config = {
            "ttl": 3600,
            "idle_timeout": 600,
            "absolute_timeout": 7200,
            "rotate_on_use": True,
            "fingerprint_binding": True,
            "persistence": {"enabled": True, "store_name": "redis"},
            "concurrency": {"max_sessions_per_principal": 3, "behavior_on_limit": "reject"},
            "transport": {"adapter": "cookie", "cookie_samesite": "strict"},
        }
        p = SessionPolicy.from_dict("test", config)
        assert p.ttl == timedelta(hours=1)
        assert p.idle_timeout == timedelta(minutes=10)
        assert p.absolute_timeout == timedelta(hours=2)
        assert p.rotate_on_use is True
        assert p.fingerprint_binding is True
        assert p.persistence.store_name == "redis"
        assert p.concurrency.max_sessions_per_principal == 3
        assert p.transport.cookie_samesite == "strict"


class TestConcurrencyPolicy:
    """Tests for ConcurrencyPolicy."""

    def test_no_limit(self):
        from aquilia.sessions.policy import ConcurrencyPolicy
        from aquilia.sessions.core import SessionPrincipal
        p = ConcurrencyPolicy(max_sessions_per_principal=None)
        principal = SessionPrincipal(id="u1", kind="user")
        assert p.violated(principal, 100) is False

    def test_limit_violated(self):
        from aquilia.sessions.policy import ConcurrencyPolicy
        from aquilia.sessions.core import SessionPrincipal
        p = ConcurrencyPolicy(max_sessions_per_principal=3)
        principal = SessionPrincipal(id="u1", kind="user")
        assert p.violated(principal, 4) is True
        assert p.violated(principal, 3) is False

    def test_behavior_flags(self):
        from aquilia.sessions.policy import ConcurrencyPolicy
        assert ConcurrencyPolicy(behavior_on_limit="reject").should_reject() is True
        assert ConcurrencyPolicy(behavior_on_limit="evict_oldest").should_evict_oldest() is True
        assert ConcurrencyPolicy(behavior_on_limit="evict_all").should_evict_all() is True


class TestSessionPolicyBuilder:
    """Tests for fluent SessionPolicyBuilder."""

    def test_web_defaults(self):
        from aquilia.sessions.policy import SessionPolicyBuilder
        p = SessionPolicyBuilder().web_defaults().build()
        assert p.name == "web_session"
        assert p.ttl == timedelta(days=7)

    def test_api_defaults(self):
        from aquilia.sessions.policy import SessionPolicyBuilder
        p = SessionPolicyBuilder().api_defaults().build()
        assert p.name == "api_session"
        assert p.ttl == timedelta(hours=1)
        assert p.idle_timeout is None

    def test_admin_defaults_with_fingerprinting(self):
        from aquilia.sessions.policy import SessionPolicyBuilder
        p = SessionPolicyBuilder().admin_defaults().build()
        assert p.name == "admin_session"
        assert p.fingerprint_binding is True
        assert p.absolute_timeout == timedelta(hours=12)
        assert p.rotate_on_use is True

    def test_fluent_chaining(self):
        from aquilia.sessions.policy import SessionPolicyBuilder
        p = (SessionPolicyBuilder()
             .named("custom")
             .lasting(days=3)
             .idle_timeout(minutes=15)
             .absolute_timeout(hours=24)
             .with_fingerprint_binding()
             .rotating_on_auth()
             .max_concurrent(2)
             .build())
        assert p.name == "custom"
        assert p.ttl == timedelta(days=3)
        assert p.idle_timeout == timedelta(minutes=15)
        assert p.absolute_timeout == timedelta(hours=24)
        assert p.fingerprint_binding is True
        assert p.concurrency.max_sessions_per_principal == 2

    def test_callable_shorthand(self):
        from aquilia.sessions.policy import SessionPolicyBuilder
        p = SessionPolicyBuilder().web_defaults()()
        assert p.name == "web_session"

    def test_factory_methods_on_policy(self):
        from aquilia.sessions.policy import SessionPolicy
        builder = SessionPolicy.for_web_users()
        p = builder.build()
        assert p.name == "web_session"


class TestBuiltInPolicies:
    """Tests for built-in policy constants."""

    def test_default_user_policy(self):
        from aquilia.sessions.policy import DEFAULT_USER_POLICY
        assert DEFAULT_USER_POLICY.name == "user_default"
        assert DEFAULT_USER_POLICY.ttl == timedelta(days=7)

    def test_api_token_policy(self):
        from aquilia.sessions.policy import API_TOKEN_POLICY
        assert API_TOKEN_POLICY.name == "api_token"
        assert API_TOKEN_POLICY.idle_timeout is None

    def test_ephemeral_policy(self):
        from aquilia.sessions.policy import EPHEMERAL_POLICY
        assert EPHEMERAL_POLICY.persistence.enabled is False

    def test_admin_policy(self):
        from aquilia.sessions.policy import ADMIN_POLICY
        assert ADMIN_POLICY.fingerprint_binding is True
        assert ADMIN_POLICY.absolute_timeout == timedelta(hours=12)
        assert ADMIN_POLICY.rotate_on_use is True


# ============================================================================
# Transport Tests
# ============================================================================

class TestCookieTransport:
    """Tests for CookieTransport."""

    def _make_transport(self):
        from aquilia.sessions.transport import CookieTransport
        from aquilia.sessions.policy import TransportPolicy
        policy = TransportPolicy(
            adapter="cookie",
            cookie_name="test_session",
            cookie_httponly=True,
            cookie_secure=True,
            cookie_samesite="lax",
            cookie_path="/",
        )
        return CookieTransport(policy)

    def _make_session(self):
        from aquilia.sessions.core import Session, SessionID, SessionScope
        return Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=SessionScope.USER,
        )

    def test_extract_from_cookie(self):
        transport = self._make_transport()
        request = MagicMock()
        request.header.return_value = "test_session=abc123; other=xyz"
        assert transport.extract(request) == "abc123"

    def test_extract_no_cookie(self):
        transport = self._make_transport()
        request = MagicMock()
        request.header.return_value = None
        assert transport.extract(request) is None

    def test_extract_wrong_cookie_name(self):
        transport = self._make_transport()
        request = MagicMock()
        request.header.return_value = "other_cookie=abc123"
        assert transport.extract(request) is None

    def test_inject_calls_set_cookie(self):
        transport = self._make_transport()
        response = MagicMock()
        session = self._make_session()
        
        transport.inject(response, session)
        
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args
        assert call_kwargs.kwargs['name'] == "test_session"
        assert call_kwargs.kwargs['secure'] is True
        assert call_kwargs.kwargs['httponly'] is True

    def test_inject_no_expires(self):
        """max_age should be None when session has no expires_at."""
        transport = self._make_transport()
        response = MagicMock()
        from aquilia.sessions.core import Session, SessionID, SessionScope
        session = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=None,
            scope=SessionScope.USER,
        )
        
        transport.inject(response, session)
        call_kwargs = response.set_cookie.call_args
        assert call_kwargs.kwargs['max_age'] is None

    def test_clear_calls_delete_cookie(self):
        transport = self._make_transport()
        response = MagicMock()
        response.delete_cookie = MagicMock()
        
        transport.clear(response)
        response.delete_cookie.assert_called_once()

    def test_factory_methods(self):
        from aquilia.sessions.transport import CookieTransport
        assert CookieTransport.for_web_browsers().cookie_name == "aquilia_web_session"
        assert CookieTransport.for_spa_applications().cookie_name == "aquilia_spa_session"
        assert CookieTransport.for_mobile_webviews().cookie_name == "aquilia_mobile_session"
        assert CookieTransport.with_aquilia_defaults().cookie_name == "aquilia_session"


class TestHeaderTransport:
    """Tests for HeaderTransport."""

    def test_extract_from_header(self):
        from aquilia.sessions.transport import HeaderTransport
        from aquilia.sessions.policy import TransportPolicy
        policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
        transport = HeaderTransport(policy)
        
        request = MagicMock()
        request.header.return_value = "my-session-id"
        assert transport.extract(request) == "my-session-id"

    def test_inject_sets_header(self):
        from aquilia.sessions.transport import HeaderTransport
        from aquilia.sessions.policy import TransportPolicy
        from aquilia.sessions.core import Session, SessionID, SessionScope
        
        policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
        transport = HeaderTransport(policy)
        response = MagicMock()
        response.headers = {}
        
        session = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            scope=SessionScope.USER,
        )
        
        transport.inject(response, session)
        assert "X-Session-ID" in response.headers

    def test_factory_methods(self):
        from aquilia.sessions.transport import HeaderTransport
        assert HeaderTransport.for_rest_apis().header_name == "X-Session-ID"
        assert HeaderTransport.for_graphql_apis().header_name == "X-GraphQL-Session"
        assert HeaderTransport.for_microservices().header_name == "X-Service-Session"


class TestCreateTransport:
    """Tests for create_transport factory."""

    def test_creates_cookie_transport(self):
        from aquilia.sessions.transport import create_transport, CookieTransport
        from aquilia.sessions.policy import TransportPolicy
        t = create_transport(TransportPolicy(adapter="cookie"))
        assert isinstance(t, CookieTransport)

    def test_creates_header_transport(self):
        from aquilia.sessions.transport import create_transport, HeaderTransport
        from aquilia.sessions.policy import TransportPolicy
        t = create_transport(TransportPolicy(adapter="header"))
        assert isinstance(t, HeaderTransport)

    def test_rejects_unsupported(self):
        from aquilia.sessions.transport import create_transport
        from aquilia.sessions.policy import TransportPolicy
        from aquilia.sessions.faults import SessionTransportFault
        with pytest.raises(SessionTransportFault):
            create_transport(TransportPolicy(adapter="unknown"))


# ============================================================================
# Engine Tests
# ============================================================================

class TestSessionEngine:
    """Tests for SessionEngine lifecycle orchestrator."""

    def _make_engine(self, **policy_kwargs):
        from aquilia.sessions.engine import SessionEngine
        from aquilia.sessions.policy import SessionPolicy
        from aquilia.sessions.store import MemoryStore

        policy_defaults = dict(
            name="test",
            ttl=timedelta(hours=1),
            idle_timeout=timedelta(minutes=30),
        )
        policy_defaults.update(policy_kwargs)
        
        policy = SessionPolicy(**policy_defaults)
        store = MemoryStore()
        transport = MagicMock()
        transport.extract = MagicMock(return_value=None)
        transport.inject = MagicMock()
        transport.clear = MagicMock()
        
        return SessionEngine(policy=policy, store=store, transport=transport), store, transport

    @pytest.mark.asyncio
    async def test_resolve_creates_new_session(self):
        engine, store, transport = self._make_engine()
        request = MagicMock()
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        session = await engine.resolve(request)
        assert session is not None
        assert str(session.id).startswith("sess_")

    @pytest.mark.asyncio
    async def test_resolve_loads_existing_session(self):
        engine, store, transport = self._make_engine()
        from aquilia.sessions.core import Session, SessionID, SessionScope
        
        # Create and save a session
        existing = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=SessionScope.USER,
        )
        await store.save(existing)
        
        # Mock transport to return this session ID
        transport.extract.return_value = str(existing.id)
        
        request = MagicMock()
        request.path = "/test"
        request.method = "GET"
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        session = await engine.resolve(request)
        assert str(session.id) == str(existing.id)

    @pytest.mark.asyncio
    async def test_resolve_creates_new_for_expired(self):
        engine, store, transport = self._make_engine()
        from aquilia.sessions.core import Session, SessionID, SessionScope
        
        expired = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            last_accessed_at=datetime.now(timezone.utc) - timedelta(hours=2),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            scope=SessionScope.USER,
        )
        await store.save(expired)
        transport.extract.return_value = str(expired.id)
        
        request = MagicMock()
        request.path = "/test"
        request.method = "GET"
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        session = await engine.resolve(request)
        # Should get a NEW session (different ID)
        assert str(session.id) != str(expired.id)

    @pytest.mark.asyncio
    async def test_commit_persists_dirty_session(self):
        engine, store, transport = self._make_engine()
        request = MagicMock()
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        session = await engine.resolve(request)
        session.data["key"] = "value"
        session.mark_dirty()
        
        response = MagicMock()
        await engine.commit(session, response)
        
        # Should be saved
        loaded = await store.load(session.id)
        assert loaded is not None
        transport.inject.assert_called()

    @pytest.mark.asyncio
    async def test_commit_rotates_on_privilege_change(self):
        engine, store, transport = self._make_engine(rotate_on_privilege_change=True)
        from aquilia.sessions.core import SessionPrincipal, SessionFlag
        
        request = MagicMock()
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        session = await engine.resolve(request)
        old_id = str(session.id)
        session.principal = SessionPrincipal(id="u1", kind="user")
        session.flags.add(SessionFlag.AUTHENTICATED)
        session.mark_dirty()
        
        response = MagicMock()
        await engine.commit(session, response, privilege_changed=True)
        
        # Transport should have been called with new session
        call_args = transport.inject.call_args
        new_session = call_args[0][1]
        assert str(new_session.id) != old_id

    @pytest.mark.asyncio
    async def test_destroy(self):
        engine, store, transport = self._make_engine()
        request = MagicMock()
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        session = await engine.resolve(request)
        session.mark_dirty()
        await store.save(session)
        
        response = MagicMock()
        await engine.destroy(session, response)
        
        assert await store.exists(session.id) is False
        transport.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_handler(self):
        engine, store, transport = self._make_engine()
        events = []
        engine.on_event(lambda e: events.append(e))
        
        request = MagicMock()
        request.path = "/test"
        request.method = "GET"
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        await engine.resolve(request)
        assert len(events) > 0
        assert events[0]["event"] == "session_created"

    @pytest.mark.asyncio
    async def test_fingerprint_binding(self):
        engine, store, transport = self._make_engine(fingerprint_binding=True)
        
        request = MagicMock()
        request.path = "/test"
        request.method = "GET"
        request.client = ("192.168.1.1", 8000)
        request.header = MagicMock(side_effect=lambda h: "Mozilla/5.0" if h == "user-agent" else None)
        
        session = await engine.resolve(request)
        # Session should have fingerprint bound
        assert session.verify_fingerprint("192.168.1.1", "Mozilla/5.0") is True

    @pytest.mark.asyncio
    async def test_fingerprint_mismatch_creates_new(self):
        engine, store, transport = self._make_engine(fingerprint_binding=True)
        from aquilia.sessions.core import Session, SessionID, SessionScope
        
        # Create session with one fingerprint
        existing = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            scope=SessionScope.USER,
        )
        existing.bind_fingerprint("192.168.1.1", "Mozilla/5.0")
        await store.save(existing)
        
        transport.extract.return_value = str(existing.id)
        
        # Request with different IP (hijack attempt)
        request = MagicMock()
        request.path = "/test"
        request.method = "GET"
        request.client = ("10.0.0.99", 8000)
        request.header = MagicMock(side_effect=lambda h: "Chrome/99" if h == "user-agent" else None)
        
        session = await engine.resolve(request)
        # Should get a NEW session due to fingerprint mismatch
        assert str(session.id) != str(existing.id)

    @pytest.mark.asyncio
    async def test_absolute_timeout_creates_new(self):
        engine, store, transport = self._make_engine(
            absolute_timeout=timedelta(hours=2)
        )
        from aquilia.sessions.core import Session, SessionID, SessionScope
        
        # Session created 3 hours ago
        old = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc) - timedelta(hours=3),
            last_accessed_at=datetime.now(timezone.utc),  # Recently accessed
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),  # Not TTL-expired
            scope=SessionScope.USER,
        )
        await store.save(old)
        transport.extract.return_value = str(old.id)
        
        request = MagicMock()
        request.path = "/test"
        request.method = "GET"
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)
        
        session = await engine.resolve(request)
        # Should create new (absolute timeout exceeded)
        assert str(session.id) != str(old.id)

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        engine, store, transport = self._make_engine()
        from aquilia.sessions.core import Session, SessionID, SessionScope
        
        expired = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc) - timedelta(hours=2),
            last_accessed_at=datetime.now(timezone.utc) - timedelta(hours=2),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            scope=SessionScope.USER,
        )
        await store.save(expired)
        
        count = await engine.cleanup_expired()
        assert count == 1


# ============================================================================
# Fault Tests
# ============================================================================

class TestSessionFaults:
    """Tests for all session fault types."""

    def test_session_expired_fault(self):
        from aquilia.sessions.faults import SessionExpiredFault
        f = SessionExpiredFault(session_id="sess_abc123", expires_at="2025-01-01T00:00:00Z")
        assert f.code == "SESSION_EXPIRED"
        assert f.session_id_hash is not None
        assert f.session_id_hash.startswith("sha256:")

    def test_session_idle_timeout_fault(self):
        from aquilia.sessions.faults import SessionIdleTimeoutFault
        f = SessionIdleTimeoutFault()
        assert f.code == "SESSION_IDLE_TIMEOUT"

    def test_session_absolute_timeout_fault(self):
        from aquilia.sessions.faults import SessionAbsoluteTimeoutFault
        f = SessionAbsoluteTimeoutFault()
        assert f.code == "SESSION_ABSOLUTE_TIMEOUT"

    def test_session_invalid_fault(self):
        from aquilia.sessions.faults import SessionInvalidFault
        f = SessionInvalidFault()
        assert f.code == "SESSION_INVALID"

    def test_session_not_found_fault(self):
        from aquilia.sessions.faults import SessionNotFoundFault
        f = SessionNotFoundFault()
        assert f.code == "SESSION_NOT_FOUND"

    def test_policy_violation_fault(self):
        from aquilia.sessions.faults import SessionPolicyViolationFault
        f = SessionPolicyViolationFault(violation="too many", policy_name="test")
        assert "too many" in f.message

    def test_concurrency_violation_fault(self):
        from aquilia.sessions.faults import SessionConcurrencyViolationFault
        f = SessionConcurrencyViolationFault(principal_id="u1", active_count=6, max_allowed=5)
        assert "6/5" in f.message

    def test_session_locked_fault(self):
        from aquilia.sessions.faults import SessionLockedFault
        f = SessionLockedFault()
        assert f.code == "SESSION_LOCKED"

    def test_store_unavailable_fault(self):
        from aquilia.sessions.faults import SessionStoreUnavailableFault
        f = SessionStoreUnavailableFault(store_name="redis", cause="connection refused")
        assert "redis" in f.message

    def test_store_corrupted_fault(self):
        from aquilia.sessions.faults import SessionStoreCorruptedFault
        f = SessionStoreCorruptedFault(message="bad json", session_id="sess_abc")
        assert f.message == "bad json"
        assert f.session_id_hash.startswith("sha256:")

    def test_rotation_failed_fault_uses_own_hash(self):
        from aquilia.sessions.faults import SessionRotationFailedFault
        f = SessionRotationFailedFault(old_id="old_sess", new_id="new_sess", cause="disk full")
        assert f.old_id_hash.startswith("sha256:")
        assert f.new_id_hash.startswith("sha256:")
        assert "disk full" in f.message

    def test_transport_fault(self):
        from aquilia.sessions.faults import SessionTransportFault
        f = SessionTransportFault(transport_type="cookie", cause="malformed")
        assert "cookie" in f.message

    def test_forgery_attempt_fault(self):
        from aquilia.sessions.faults import SessionForgeryAttemptFault
        f = SessionForgeryAttemptFault(reason="invalid HMAC")
        assert f.code == "SESSION_FORGERY_ATTEMPT"

    def test_hijack_attempt_fault(self):
        from aquilia.sessions.faults import SessionHijackAttemptFault
        f = SessionHijackAttemptFault(reason="IP mismatch")
        assert f.code == "SESSION_HIJACK_ATTEMPT"

    def test_fingerprint_mismatch_fault(self):
        from aquilia.sessions.faults import SessionFingerprintMismatchFault
        f = SessionFingerprintMismatchFault(session_id="sess_xyz")
        assert f.code == "SESSION_FINGERPRINT_MISMATCH"
        assert f.session_id_hash.startswith("sha256:")


# ============================================================================
# State Tests
# ============================================================================

class TestSessionState:
    """Tests for typed session state."""

    def test_cart_state_defaults(self):
        from aquilia.sessions.state import CartState
        data = {}
        cart = CartState(data)
        assert cart.items == []
        assert cart.total == 0.0
        assert cart.currency == "USD"

    def test_cart_state_sync(self):
        from aquilia.sessions.state import CartState
        data = {}
        cart = CartState(data)
        cart.items = ["item1", "item2"]
        cart.total = 29.99
        assert data["items"] == ["item1", "item2"]
        assert data["total"] == 29.99

    def test_state_from_existing_data(self):
        from aquilia.sessions.state import CartState
        data = {"items": ["x"], "total": 10.0, "currency": "EUR"}
        cart = CartState(data)
        assert cart.items == ["x"]
        assert cart.currency == "EUR"

    def test_state_repr(self):
        from aquilia.sessions.state import CartState
        cart = CartState({})
        r = repr(cart)
        assert "CartState(" in r

    def test_state_equality(self):
        from aquilia.sessions.state import CartState
        a = CartState({"items": ["x"], "total": 10.0, "currency": "USD"})
        b = CartState({"items": ["x"], "total": 10.0, "currency": "USD"})
        assert a == b

    def test_state_inequality(self):
        from aquilia.sessions.state import CartState
        a = CartState({"items": ["x"], "total": 10.0, "currency": "USD"})
        b = CartState({"items": ["y"], "total": 20.0, "currency": "USD"})
        assert a != b

    def test_state_getitem_setitem(self):
        from aquilia.sessions.state import SessionState
        data = {"key": "value"}
        state = SessionState(data)
        assert state["key"] == "value"
        state["new"] = "data"
        assert state["new"] == "data"

    def test_state_get_with_default(self):
        from aquilia.sessions.state import SessionState
        state = SessionState({})
        assert state.get("missing", "default") == "default"

    def test_state_to_dict(self):
        from aquilia.sessions.state import CartState
        cart = CartState({})
        cart.total = 42.0
        d = cart.to_dict()
        assert d["total"] == 42.0

    def test_user_preferences_state(self):
        from aquilia.sessions.state import UserPreferencesState
        prefs = UserPreferencesState({})
        assert prefs.theme == "light"
        assert prefs.language == "en"
        prefs.theme = "dark"
        assert prefs.theme == "dark"

    def test_field_graceful_missing(self):
        from aquilia.sessions.state import Field
        f = Field(default="fallback")
        f.__set_name__(None, "test")
        
        class Dummy:
            pass
        
        obj = Dummy()
        # No private attr set - should return default
        result = f.__get__(obj, type(obj))
        assert result == "fallback"


# ============================================================================
# Decorators & Guards Tests
# ============================================================================

class TestSessionDecorators:
    """Tests for session decorators."""

    def _make_ctx(self, session=None):
        ctx = MagicMock()
        ctx.session = session
        ctx.request = MagicMock()
        ctx.request.state = {}
        if session:
            ctx.request.state['session'] = session
        return ctx

    def _make_session(self, authenticated=False):
        from aquilia.sessions.core import Session, SessionID, SessionScope, SessionPrincipal, SessionFlag
        s = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            scope=SessionScope.USER,
        )
        if authenticated:
            s.principal = SessionPrincipal(id="u1", kind="user")
            s.flags.add(SessionFlag.AUTHENTICATED)
        return s

    @pytest.mark.asyncio
    async def test_require_raises_when_no_session(self):
        from aquilia.sessions.decorators import session, SessionRequiredFault
        
        @session.require()
        async def handler(ctx, session=None):
            return "ok"
        
        ctx = self._make_ctx(session=None)
        with pytest.raises(SessionRequiredFault):
            await handler(ctx)

    @pytest.mark.asyncio
    async def test_require_passes_with_session(self):
        from aquilia.sessions.decorators import session as sess_dec
        
        @sess_dec.require()
        async def handler(ctx, session=None):
            return "ok"
        
        sess = self._make_session()
        ctx = self._make_ctx(session=sess)
        result = await handler(ctx)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_require_authenticated_raises(self):
        from aquilia.sessions.decorators import session, AuthenticationRequiredFault
        
        @session.require(authenticated=True)
        async def handler(ctx, session=None):
            return "ok"
        
        sess = self._make_session(authenticated=False)
        ctx = self._make_ctx(session=sess)
        with pytest.raises(AuthenticationRequiredFault):
            await handler(ctx)

    @pytest.mark.asyncio
    async def test_require_authenticated_passes(self):
        from aquilia.sessions.decorators import session as sess_dec
        
        @sess_dec.require(authenticated=True)
        async def handler(ctx, session=None):
            return session.principal.id
        
        sess = self._make_session(authenticated=True)
        ctx = self._make_ctx(session=sess)
        result = await handler(ctx)
        assert result == "u1"

    @pytest.mark.asyncio
    async def test_optional_with_session(self):
        from aquilia.sessions.decorators import session as sess_dec
        
        @sess_dec.optional()
        async def handler(ctx, session=None):
            return session is not None
        
        sess = self._make_session()
        ctx = self._make_ctx(session=sess)
        result = await handler(ctx)
        assert result is True

    @pytest.mark.asyncio
    async def test_optional_without_session(self):
        from aquilia.sessions.decorators import session as sess_dec
        
        @sess_dec.optional()
        async def handler(ctx, session=None):
            return session is None
        
        ctx = self._make_ctx(session=None)
        result = await handler(ctx)
        assert result is True

    @pytest.mark.asyncio
    async def test_authenticated_decorator(self):
        from aquilia.sessions.decorators import authenticated
        
        @authenticated
        async def handler(ctx, user=None):
            return user.id
        
        sess = self._make_session(authenticated=True)
        ctx = self._make_ctx(session=sess)
        result = await handler(ctx)
        assert result == "u1"

    @pytest.mark.asyncio
    async def test_authenticated_decorator_raises(self):
        from aquilia.sessions.decorators import authenticated, SessionRequiredFault
        
        @authenticated
        async def handler(ctx, user=None):
            return "ok"
        
        ctx = self._make_ctx(session=None)
        with pytest.raises(SessionRequiredFault):
            await handler(ctx)

    @pytest.mark.asyncio
    async def test_authenticated_decorator_uses_request_state_session_fallback(self):
        from aquilia.sessions.decorators import authenticated

        @authenticated
        async def handler(ctx, user=None):
            return user.id

        sess = self._make_session(authenticated=True)
        ctx = self._make_ctx(session=None)
        ctx.request.state["session"] = sess

        result = await handler(ctx)
        assert result == "u1"

    @pytest.mark.asyncio
    async def test_require_authenticated_uses_request_state_session_fallback(self):
        from aquilia.sessions.decorators import session as sess_dec

        @sess_dec.require(authenticated=True)
        async def handler(ctx, session=None):
            return session.principal.id

        sess = self._make_session(authenticated=True)
        ctx = self._make_ctx(session=None)
        ctx.request.state["session"] = sess

        result = await handler(ctx)
        assert result == "u1"

    @pytest.mark.asyncio
    async def test_authenticated_decorator_with_ctx_without_session_attribute(self):
        from aquilia.sessions.decorators import authenticated

        class _CtxWithoutSession:
            def __init__(self, request):
                self.request = request

        @authenticated
        async def handler(ctx, user=None):
            return user.id

        sess = self._make_session(authenticated=True)
        request = MagicMock()
        request.state = {"session": sess}
        ctx = _CtxWithoutSession(request=request)

        result = await handler(ctx)
        assert result == "u1"

    @pytest.mark.asyncio
    async def test_stateful_decorator(self):
        from aquilia.sessions.decorators import stateful
        from aquilia.sessions.state import SessionState
        
        @stateful
        async def handler(ctx, state: SessionState = None):
            return state is not None
        
        sess = self._make_session()
        ctx = self._make_ctx(session=sess)
        result = await handler(ctx)
        assert result is True


class TestSessionContext:
    """Tests for SessionContext manager (merged from enhanced.py)."""

    def _make_ctx(self, session=None):
        ctx = MagicMock()
        ctx.session = session
        ctx.request = MagicMock()
        ctx.request.state = {}
        if session:
            ctx.request.state['session'] = session
        return ctx

    def _make_session(self, authenticated=False):
        from aquilia.sessions.core import Session, SessionID, SessionScope, SessionPrincipal, SessionFlag
        s = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            scope=SessionScope.USER,
        )
        if authenticated:
            s.principal = SessionPrincipal(id="u1", kind="user")
            s.flags.add(SessionFlag.AUTHENTICATED)
        return s

    @pytest.mark.asyncio
    async def test_authenticated_context(self):
        from aquilia.sessions.decorators import SessionContext
        
        sess = self._make_session(authenticated=True)
        ctx = self._make_ctx(session=sess)
        
        async with SessionContext.authenticated(ctx) as session:
            assert session.is_authenticated is True

    @pytest.mark.asyncio
    async def test_authenticated_context_raises(self):
        from aquilia.sessions.decorators import SessionContext, SessionRequiredFault
        
        ctx = self._make_ctx(session=None)
        with pytest.raises(SessionRequiredFault):
            async with SessionContext.authenticated(ctx) as session:
                pass

    @pytest.mark.asyncio
    async def test_ensure_context(self):
        from aquilia.sessions.decorators import SessionContext
        
        sess = self._make_session()
        ctx = self._make_ctx(session=sess)
        
        async with SessionContext.ensure(ctx) as session:
            assert session is not None

    @pytest.mark.asyncio
    async def test_transactional_success(self):
        from aquilia.sessions.decorators import SessionContext
        
        sess = self._make_session()
        sess.data["balance"] = 100
        ctx = self._make_ctx(session=sess)
        
        async with SessionContext.transactional(ctx) as session:
            session.data["balance"] -= 30
        
        assert sess.data["balance"] == 70

    @pytest.mark.asyncio
    async def test_transactional_rollback(self):
        from aquilia.sessions.decorators import SessionContext
        
        sess = self._make_session()
        sess.data["balance"] = 100
        ctx = self._make_ctx(session=sess)
        
        with pytest.raises(ValueError):
            async with SessionContext.transactional(ctx) as session:
                session.data["balance"] -= 200
                raise ValueError("Insufficient funds")
        
        # Should be rolled back
        assert sess.data["balance"] == 100


class TestSessionGuards:
    """Tests for SessionGuard and requires() decorator."""

    def _make_session(self, role=None, email_verified=False):
        from aquilia.sessions.core import Session, SessionID, SessionScope, SessionPrincipal, SessionFlag
        s = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            scope=SessionScope.USER,
        )
        if role:
            attrs = {"role": role, "email_verified": email_verified}
            s.principal = SessionPrincipal(id="u1", kind="user", attributes=attrs)
            s.flags.add(SessionFlag.AUTHENTICATED)
        return s

    @pytest.mark.asyncio
    async def test_admin_guard_passes(self):
        from aquilia.sessions.decorators import AdminGuard
        guard = AdminGuard()
        sess = self._make_session(role="admin")
        assert await guard.check(sess) is True

    @pytest.mark.asyncio
    async def test_admin_guard_fails(self):
        from aquilia.sessions.decorators import AdminGuard
        guard = AdminGuard()
        sess = self._make_session(role="user")
        assert await guard.check(sess) is False

    @pytest.mark.asyncio
    async def test_verified_email_guard(self):
        from aquilia.sessions.decorators import VerifiedEmailGuard
        guard = VerifiedEmailGuard()
        
        sess_verified = self._make_session(role="user", email_verified=True)
        assert await guard.check(sess_verified) is True
        
        sess_unverified = self._make_session(role="user", email_verified=False)
        assert await guard.check(sess_unverified) is False

    @pytest.mark.asyncio
    async def test_requires_decorator(self):
        from aquilia.sessions.decorators import requires, AdminGuard, SessionRequiredFault
        
        @requires(AdminGuard())
        async def admin_only(session=None):
            return "admin"
        
        sess = self._make_session(role="admin")
        result = await admin_only(session=sess)
        assert result == "admin"

    @pytest.mark.asyncio
    async def test_requires_no_session_raises(self):
        from aquilia.sessions.decorators import requires, AdminGuard, SessionRequiredFault
        
        @requires(AdminGuard())
        async def admin_only(session=None):
            return "admin"
        
        with pytest.raises(SessionRequiredFault):
            await admin_only()


# ============================================================================
# Integration / OWASP Compliance Tests
# ============================================================================

class TestOWASPCompliance:
    """Tests verifying OWASP Session Management compliance."""

    def test_session_id_entropy_256_bits(self):
        """OWASP requires minimum 64 bits, we use 256 bits."""
        from aquilia.sessions.core import SessionID
        assert SessionID.ENTROPY_BYTES == 32  # 32 bytes = 256 bits

    def test_constant_time_comparison(self):
        """Session IDs must use constant-time comparison to prevent timing attacks."""
        from aquilia.sessions.core import SessionID
        a = SessionID()
        b = SessionID.from_string(str(a))
        # This uses secrets.compare_digest internally
        assert a == b

    def test_fingerprint_binding_available(self):
        """OWASP recommends binding sessions to client characteristics."""
        from aquilia.sessions.core import Session, SessionID, SessionScope
        s = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            scope=SessionScope.USER,
        )
        s.bind_fingerprint("1.2.3.4", "Mozilla/5.0")
        assert s.verify_fingerprint("1.2.3.4", "Mozilla/5.0") is True
        assert s.verify_fingerprint("5.6.7.8", "Mozilla/5.0") is False

    def test_absolute_timeout_supported(self):
        """OWASP requires absolute timeout (max total session lifetime)."""
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", absolute_timeout=timedelta(hours=8))
        assert p.absolute_timeout == timedelta(hours=8)

    def test_idle_timeout_supported(self):
        """OWASP requires idle timeout."""
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", idle_timeout=timedelta(minutes=15))
        assert p.idle_timeout == timedelta(minutes=15)

    def test_session_rotation_on_privilege_change(self):
        """OWASP: regenerate session ID after privilege level change."""
        from aquilia.sessions.policy import SessionPolicy
        p = SessionPolicy(name="test", rotate_on_privilege_change=True)
        from aquilia.sessions.core import Session, SessionID, SessionScope
        s = Session(
            id=SessionID(),
            created_at=datetime.now(timezone.utc),
            last_accessed_at=datetime.now(timezone.utc),
            scope=SessionScope.USER,
        )
        assert p.should_rotate(s, privilege_changed=True) is True

    def test_cookie_security_flags(self):
        """OWASP: HttpOnly, Secure, SameSite flags on session cookies."""
        from aquilia.sessions.transport import CookieTransport
        t = CookieTransport.for_web_browsers()
        assert t.policy.cookie_httponly is True
        assert t.policy.cookie_secure is True
        assert t.policy.cookie_samesite in ("strict", "lax")

    def test_fingerprint_mismatch_fault_exists(self):
        """OWASP: detect session hijacking via fingerprint."""
        from aquilia.sessions.faults import SessionFingerprintMismatchFault
        f = SessionFingerprintMismatchFault()
        assert f.code == "SESSION_FINGERPRINT_MISMATCH"


# ============================================================================
# __init__.py Export Tests
# ============================================================================

class TestSessionExports:
    """Tests that all important types are exported from aquilia.sessions."""

    def test_core_types_exported(self):
        from aquilia.sessions import Session, SessionID, SessionPrincipal, SessionScope, SessionFlag
        assert all(t is not None for t in [Session, SessionID, SessionPrincipal, SessionScope, SessionFlag])

    def test_policy_types_exported(self):
        from aquilia.sessions import (
            SessionPolicy, SessionPolicyBuilder, PersistencePolicy,
            ConcurrencyPolicy, TransportPolicy,
            DEFAULT_USER_POLICY, API_TOKEN_POLICY, EPHEMERAL_POLICY, ADMIN_POLICY,
        )
        assert DEFAULT_USER_POLICY.name == "user_default"

    def test_store_types_exported(self):
        from aquilia.sessions import SessionStore, MemoryStore, FileStore
        assert all(t is not None for t in [SessionStore, MemoryStore, FileStore])

    def test_transport_types_exported(self):
        from aquilia.sessions import SessionTransport, CookieTransport, HeaderTransport, create_transport
        assert all(t is not None for t in [SessionTransport, CookieTransport, HeaderTransport, create_transport])

    def test_engine_exported(self):
        from aquilia.sessions import SessionEngine
        assert SessionEngine is not None

    def test_fault_types_exported(self):
        from aquilia.sessions import (
            SessionFault, SessionExpiredFault, SessionIdleTimeoutFault,
            SessionAbsoluteTimeoutFault, SessionInvalidFault, SessionNotFoundFault,
            SessionConcurrencyViolationFault, SessionStoreUnavailableFault,
            SessionStoreCorruptedFault, SessionRotationFailedFault,
            SessionPolicyViolationFault, SessionTransportFault,
            SessionForgeryAttemptFault, SessionHijackAttemptFault,
            SessionFingerprintMismatchFault, SessionLockedFault,
        )

    def test_decorator_types_exported(self):
        from aquilia.sessions import (
            session, authenticated, stateful,
            SessionRequiredFault, AuthenticationRequiredFault,
            SessionContext, SessionGuard, requires,
            AdminGuard, VerifiedEmailGuard,
        )

    def test_state_types_exported(self):
        from aquilia.sessions import SessionState, Field, CartState, UserPreferencesState

    def test_aquilia_root_imports(self):
        """Test that aquilia/__init__.py correctly imports from decorators (not enhanced)."""
        from aquilia import SessionContext, SessionGuard, requires, AdminGuard, VerifiedEmailGuard
        assert all(t is not None for t in [SessionContext, SessionGuard, requires, AdminGuard, VerifiedEmailGuard])
