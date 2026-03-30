"""
Comprehensive test suite for Aquilia Auth System.

Tests cover:
1. Clearance System (unique Aquilia permission system)
2. Audit Trail
3. Security Hardening (CSRF, fingerprinting, headers, token binding)
4. Auth Manager (password auth, API key auth, rate limiting)
5. Token Management (issue, validate, refresh, revoke)
6. Authorization Engines (RBAC, ABAC, AuthzEngine)
7. Password Hashing & Policy
8. Guards & Flow Integration
9. Controller Clearance Wiring
10. Policy DSL
11. OAuth2 Flows
12. MFA (TOTP)
13. Identity & Credential Stores
"""

from __future__ import annotations

import asyncio
import hashlib
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Set
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# 1. CLEARANCE SYSTEM TESTS
# ============================================================================


class TestAccessLevel:
    """Test AccessLevel enum hierarchy."""

    def test_level_ordering(self):
        from aquilia.auth.clearance import AccessLevel

        assert AccessLevel.PUBLIC < AccessLevel.AUTHENTICATED
        assert AccessLevel.AUTHENTICATED < AccessLevel.INTERNAL
        assert AccessLevel.INTERNAL < AccessLevel.CONFIDENTIAL
        assert AccessLevel.CONFIDENTIAL < AccessLevel.RESTRICTED

    def test_level_values(self):
        from aquilia.auth.clearance import AccessLevel

        assert AccessLevel.PUBLIC == 0
        assert AccessLevel.AUTHENTICATED == 10
        assert AccessLevel.INTERNAL == 20
        assert AccessLevel.CONFIDENTIAL == 30
        assert AccessLevel.RESTRICTED == 40

    def test_level_names(self):
        from aquilia.auth.clearance import AccessLevel

        assert AccessLevel.PUBLIC.name == "PUBLIC"
        assert AccessLevel.RESTRICTED.name == "RESTRICTED"

    def test_level_comparison_with_int(self):
        from aquilia.auth.clearance import AccessLevel

        assert AccessLevel.INTERNAL >= 20
        assert AccessLevel.INTERNAL <= 20


class TestClearance:
    """Test Clearance descriptor."""

    def test_default_clearance(self):
        from aquilia.auth.clearance import Clearance, AccessLevel

        c = Clearance()
        assert c.level == AccessLevel.AUTHENTICATED
        assert c.entitlements == ()
        assert c.conditions == ()
        assert c.compartment is None
        assert c.deny_message == "Insufficient clearance"
        assert c.audit is True

    def test_clearance_with_params(self):
        from aquilia.auth.clearance import Clearance, AccessLevel

        c = Clearance(
            level=AccessLevel.CONFIDENTIAL,
            entitlements=["docs:read", "docs:write"],
            compartment="tenant:{tenant_id}",
            deny_message="Custom deny",
        )
        assert c.level == AccessLevel.CONFIDENTIAL
        assert "docs:read" in c.entitlements
        assert "docs:write" in c.entitlements
        assert c.compartment == "tenant:{tenant_id}"
        assert c.deny_message == "Custom deny"

    def test_clearance_is_frozen(self):
        from aquilia.auth.clearance import Clearance

        c = Clearance()
        with pytest.raises(AttributeError):
            c.level = 99  # type: ignore

    def test_clearance_merge_level_override(self):
        from aquilia.auth.clearance import Clearance, AccessLevel

        base = Clearance(level=AccessLevel.INTERNAL)
        override = Clearance(level=AccessLevel.PUBLIC)
        merged = base.merge(override)
        assert merged.level == AccessLevel.PUBLIC

    def test_clearance_merge_entitlements_union(self):
        from aquilia.auth.clearance import Clearance

        base = Clearance(entitlements=["a:read"])
        override = Clearance(entitlements=["b:write"])
        merged = base.merge(override)
        assert "a:read" in merged.entitlements
        assert "b:write" in merged.entitlements

    def test_clearance_merge_conditions_union(self):
        from aquilia.auth.clearance import Clearance, is_verified, within_quota

        base = Clearance(conditions=[is_verified])
        override = Clearance(conditions=[within_quota])
        merged = base.merge(override)
        assert is_verified in merged.conditions
        assert within_quota in merged.conditions

    def test_clearance_merge_compartment_override(self):
        from aquilia.auth.clearance import Clearance

        base = Clearance(compartment="tenant:base")
        override = Clearance(compartment="tenant:override")
        merged = base.merge(override)
        assert merged.compartment == "tenant:override"

    def test_clearance_merge_compartment_fallback(self):
        from aquilia.auth.clearance import Clearance

        base = Clearance(compartment="tenant:base")
        override = Clearance()
        merged = base.merge(override)
        assert merged.compartment == "tenant:base"

    def test_clearance_merge_deny_message_override(self):
        from aquilia.auth.clearance import Clearance

        base = Clearance(deny_message="Base deny")
        override = Clearance(deny_message="Custom override")
        merged = base.merge(override)
        assert merged.deny_message == "Custom override"


class TestClearanceVerdict:
    """Test ClearanceVerdict data structure."""

    def test_granted_verdict(self):
        from aquilia.auth.clearance import ClearanceVerdict

        v = ClearanceVerdict(granted=True, message="Access granted")
        assert v.granted is True
        assert v.level_ok is True
        assert v.entitlements_ok is True
        assert v.conditions_ok is True
        assert v.compartment_ok is True
        assert v.missing_entitlements == ()
        assert v.failed_conditions == ()

    def test_denied_verdict(self):
        from aquilia.auth.clearance import ClearanceVerdict

        v = ClearanceVerdict(
            granted=False,
            level_ok=True,
            entitlements_ok=False,
            missing_entitlements=["docs:write"],
            message="Missing entitlements",
        )
        assert v.granted is False
        assert v.entitlements_ok is False
        assert "docs:write" in v.missing_entitlements

    def test_verdict_has_timestamp(self):
        from aquilia.auth.clearance import ClearanceVerdict

        v = ClearanceVerdict(granted=True)
        assert v.evaluated_at > 0

    def test_verdict_is_frozen(self):
        from aquilia.auth.clearance import ClearanceVerdict

        v = ClearanceVerdict(granted=True)
        with pytest.raises(AttributeError):
            v.granted = False  # type: ignore


class TestGrantDecorator:
    """Test @grant and @exempt decorators."""

    def test_grant_attaches_clearance(self):
        from aquilia.auth.clearance import grant, AccessLevel, get_method_clearance

        @grant(level=AccessLevel.INTERNAL, entitlements=["test:read"])
        async def handler(self, ctx):
            pass

        c = get_method_clearance(handler)
        assert c is not None
        assert c.level == AccessLevel.INTERNAL
        assert "test:read" in c.entitlements

    def test_exempt_sets_public(self):
        from aquilia.auth.clearance import exempt, AccessLevel, get_method_clearance

        @exempt
        async def handler(self, ctx):
            pass

        c = get_method_clearance(handler)
        assert c is not None
        assert c.level == AccessLevel.PUBLIC
        assert c.entitlements == ()
        assert c.audit is False

    def test_get_method_clearance_missing(self):
        from aquilia.auth.clearance import get_method_clearance

        async def handler(self, ctx):
            pass

        assert get_method_clearance(handler) is None


class TestBuiltInConditions:
    """Test built-in clearance conditions."""

    def test_is_verified_with_attributes(self):
        from aquilia.auth.clearance import is_verified

        identity = MagicMock(attributes={"email_verified": True}, status="ACTIVE")
        assert is_verified(identity, None, None) is True

    def test_is_verified_none_identity(self):
        from aquilia.auth.clearance import is_verified

        assert is_verified(None, None, None) is False

    def test_is_verified_active_status(self):
        from aquilia.auth.clearance import is_verified

        identity = MagicMock(attributes={}, status="ACTIVE")
        assert is_verified(identity, None, None) is True

    def test_is_owner_or_admin_admin_role(self):
        from aquilia.auth.clearance import is_owner_or_admin

        identity = MagicMock(roles={"admin"})
        assert is_owner_or_admin(identity, None, None) is True

    def test_is_owner_or_admin_owner(self):
        from aquilia.auth.clearance import is_owner_or_admin

        identity = MagicMock(id="user-1", roles=set())
        ctx = MagicMock(state={"resource_owner_id": "user-1"})
        assert is_owner_or_admin(identity, None, ctx) is True

    def test_is_owner_or_admin_not_owner(self):
        from aquilia.auth.clearance import is_owner_or_admin

        identity = MagicMock(id="user-1", roles=set())
        ctx = MagicMock(state={"resource_owner_id": "user-2"})
        assert is_owner_or_admin(identity, None, ctx) is False

    def test_within_quota_ok(self):
        from aquilia.auth.clearance import within_quota

        ctx = MagicMock(state={"quota_exceeded": False})
        assert within_quota(None, None, ctx) is True

    def test_within_quota_exceeded(self):
        from aquilia.auth.clearance import within_quota

        ctx = MagicMock(state={"quota_exceeded": True})
        assert within_quota(None, None, ctx) is False

    def test_is_same_tenant_match(self):
        from aquilia.auth.clearance import is_same_tenant

        identity = MagicMock(tenant_id="t-1")
        ctx = MagicMock(state={"resource_tenant_id": "t-1"})
        assert is_same_tenant(identity, None, ctx) is True

    def test_is_same_tenant_mismatch(self):
        from aquilia.auth.clearance import is_same_tenant

        identity = MagicMock(tenant_id="t-1")
        ctx = MagicMock(state={"resource_tenant_id": "t-2"})
        assert is_same_tenant(identity, None, ctx) is False

    def test_is_same_tenant_no_resource(self):
        from aquilia.auth.clearance import is_same_tenant

        identity = MagicMock(tenant_id="t-1")
        ctx = MagicMock(state={})
        assert is_same_tenant(identity, None, ctx) is True

    def test_require_attribute_present(self):
        from aquilia.auth.clearance import require_attribute

        cond = require_attribute("verified", True)
        identity = MagicMock(attributes={"verified": True})
        assert cond(identity, None, None) is True

    def test_require_attribute_missing(self):
        from aquilia.auth.clearance import require_attribute

        cond = require_attribute("verified", True)
        identity = MagicMock(attributes={})
        assert cond(identity, None, None) is False

    def test_ip_allowlist_match(self):
        from aquilia.auth.clearance import ip_allowlist

        cond = ip_allowlist("10.0.0.0/8")
        request = MagicMock(client=("10.0.0.5", 8080))
        assert cond(None, request, None) is True

    def test_ip_allowlist_no_match(self):
        from aquilia.auth.clearance import ip_allowlist

        cond = ip_allowlist("10.0.0.0/8")
        request = MagicMock(client=("192.168.1.1", 8080))
        assert cond(None, request, None) is False


class TestClearanceEngine:
    """Test ClearanceEngine evaluation."""

    def _make_identity(
        self,
        id: str = "id-1",
        roles: set = None,
        scopes: set = None,
        status: str = "ACTIVE",
        tenant_id: str = None,
        attributes: dict = None,
    ):
        identity = MagicMock()
        identity.id = id
        identity.roles = roles or set()
        identity.scopes = scopes or set()
        identity.status = status
        identity.tenant_id = tenant_id
        identity.attributes = attributes or {}
        identity.permissions = set()
        return identity

    @pytest.mark.asyncio
    async def test_public_level_no_auth_required(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.PUBLIC)
        verdict = await engine.evaluate(c, None, None, None)
        assert verdict.granted is True
        assert verdict.level_ok is True

    @pytest.mark.asyncio
    async def test_authenticated_level_requires_identity(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.AUTHENTICATED)
        # No identity
        verdict = await engine.evaluate(c, None, None, None)
        assert verdict.granted is False
        assert verdict.level_ok is False

    @pytest.mark.asyncio
    async def test_authenticated_level_with_identity(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.AUTHENTICATED)
        identity = self._make_identity()
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    @pytest.mark.asyncio
    async def test_internal_level_requires_staff_role(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.INTERNAL)
        # User without staff role
        identity = self._make_identity(id="user-no-staff", roles={"user"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is False
        # User with staff role (different id to avoid cache collision)
        identity = self._make_identity(id="user-with-staff", roles={"staff"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True
        engine.clear_cache()

    @pytest.mark.asyncio
    async def test_restricted_level_requires_admin(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.RESTRICTED)
        identity = self._make_identity(roles={"admin"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    @pytest.mark.asyncio
    async def test_entitlement_check_pass(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(entitlements=["docs:read"])
        identity = self._make_identity(scopes={"docs:read"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True
        assert verdict.entitlements_ok is True

    @pytest.mark.asyncio
    async def test_entitlement_check_fail(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(entitlements=["docs:write"])
        identity = self._make_identity(scopes={"docs:read"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is False
        assert verdict.entitlements_ok is False
        assert "docs:write" in verdict.missing_entitlements

    @pytest.mark.asyncio
    async def test_wildcard_entitlement(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(entitlements=["docs:*"])
        identity = self._make_identity(scopes={"docs:read", "docs:write"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    @pytest.mark.asyncio
    async def test_wildcard_entitlement_fail(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(entitlements=["docs:*"])
        identity = self._make_identity(scopes={"users:read"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is False

    @pytest.mark.asyncio
    async def test_condition_check_pass(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()

        def always_true(identity, request, ctx):
            return True

        c = Clearance(conditions=[always_true])
        identity = self._make_identity()
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True
        assert verdict.conditions_ok is True

    @pytest.mark.asyncio
    async def test_condition_check_fail(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()

        def always_false(identity, request, ctx):
            return False

        c = Clearance(conditions=[always_false])
        identity = self._make_identity()
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is False
        assert verdict.conditions_ok is False
        assert "always_false" in verdict.failed_conditions

    @pytest.mark.asyncio
    async def test_async_condition(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()

        async def async_check(identity, request, ctx):
            return True

        c = Clearance(conditions=[async_check])
        identity = self._make_identity()
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    @pytest.mark.asyncio
    async def test_condition_exception_treated_as_failure(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()

        def exploding(identity, request, ctx):
            raise RuntimeError("boom")

        c = Clearance(conditions=[exploding])
        identity = self._make_identity()
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is False
        assert any("error" in f for f in verdict.failed_conditions)

    @pytest.mark.asyncio
    async def test_compartment_check_pass(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(compartment="tenant:{tenant_id}")
        identity = self._make_identity(tenant_id="t-abc")
        ctx = MagicMock(state={"tenant_id": "t-abc"})
        verdict = await engine.evaluate(c, identity, None, ctx)
        assert verdict.compartment_ok is True

    @pytest.mark.asyncio
    async def test_compartment_check_fail(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(compartment="tenant:{tenant_id}")
        identity = self._make_identity(tenant_id="t-abc")
        ctx = MagicMock(state={"tenant_id": "t-xyz"})
        verdict = await engine.evaluate(c, identity, None, ctx)
        assert verdict.compartment_ok is False

    @pytest.mark.asyncio
    async def test_combined_requirements(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(
            level=AccessLevel.INTERNAL,
            entitlements=["docs:read"],
            conditions=[lambda i, r, c: True],
        )
        identity = self._make_identity(roles={"staff"}, scopes={"docs:read"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    @pytest.mark.asyncio
    async def test_custom_entitlement_resolver(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        def resolver(identity):
            return {"custom:special"}

        engine = ClearanceEngine(entitlement_resolver=resolver)
        c = Clearance(entitlements=["custom:special"])
        identity = self._make_identity()
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    @pytest.mark.asyncio
    async def test_custom_role_level_map(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine(role_level_map={"vip": AccessLevel.CONFIDENTIAL})
        c = Clearance(level=AccessLevel.CONFIDENTIAL)
        identity = self._make_identity(roles={"vip"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    def test_cache_clear(self):
        from aquilia.auth.clearance import ClearanceEngine

        engine = ClearanceEngine()
        engine._identity_level_cache["test"] = "value"
        engine.clear_cache()
        assert "test" not in engine._identity_level_cache

    @pytest.mark.asyncio
    async def test_verdict_message_includes_details(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(
            level=AccessLevel.RESTRICTED,
            entitlements=["admin:manage"],
            deny_message="Access denied",
        )
        identity = self._make_identity(roles={"user"})
        verdict = await engine.evaluate(c, identity, None, None)
        assert "RESTRICTED" in verdict.message
        assert "admin:manage" in verdict.message


class TestClearanceGuard:
    """Test ClearanceGuard pipeline integration."""

    @pytest.mark.asyncio
    async def test_guard_grants_access(self):
        from aquilia.auth.clearance import ClearanceGuard, Clearance, AccessLevel

        guard = ClearanceGuard(Clearance(level=AccessLevel.PUBLIC))
        result = await guard(request=None, ctx=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_guard_denies_access(self):
        from aquilia.auth.clearance import ClearanceGuard, Clearance, AccessLevel

        guard = ClearanceGuard(Clearance(level=AccessLevel.RESTRICTED))
        ctx = MagicMock(identity=None, state={})
        result = await guard(request=None, ctx=ctx)
        # Should return a Response, not True
        assert result is not True
        assert hasattr(result, "status")

    @pytest.mark.asyncio
    async def test_guard_denies_access_as_html_when_accepts_html(self):
        from aquilia.auth.clearance import AccessLevel, Clearance, ClearanceGuard

        guard = ClearanceGuard(Clearance(level=AccessLevel.RESTRICTED))
        request = MagicMock()
        request.header.return_value = "text/html"
        ctx = MagicMock(identity=None, state={})

        result = await guard(request=request, ctx=ctx)

        assert result.status == 401
        assert result.headers.get("content-type") == "text/html; charset=utf-8"
        assert "<!DOCTYPE html>" in str(result._content)

    @pytest.mark.asyncio
    async def test_guard_denies_access_as_json_for_non_html_accept(self):
        from aquilia.auth.clearance import AccessLevel, Clearance, ClearanceGuard

        guard = ClearanceGuard(Clearance(level=AccessLevel.RESTRICTED))
        request = MagicMock()
        request.header.return_value = "application/json"
        ctx = MagicMock(identity=None, state={})

        result = await guard(request=request, ctx=ctx)

        assert result.status == 401
        assert result.headers.get("content-type") == "application/json; charset=utf-8"
        assert '"CLEARANCE_DENIED"' in str(result._content)

    @pytest.mark.asyncio
    async def test_guard_stores_verdict_in_state(self):
        from aquilia.auth.clearance import ClearanceGuard, Clearance, AccessLevel

        guard = ClearanceGuard(Clearance(level=AccessLevel.PUBLIC))
        ctx = MagicMock(identity=None, state={})
        await guard(request=None, ctx=ctx)
        assert "clearance_verdict" in ctx.state

    def test_guard_for_controller_returns_self(self):
        from aquilia.auth.clearance import ClearanceGuard, Clearance

        guard = ClearanceGuard(Clearance())
        assert guard.for_controller() is guard


class TestBuildMergedClearance:
    """Test build_merged_clearance helper."""

    def test_no_clearance(self):
        from aquilia.auth.clearance import build_merged_clearance

        class MyController:
            pass

        async def handler():
            pass

        assert build_merged_clearance(MyController, handler) is None

    def test_class_only(self):
        from aquilia.auth.clearance import build_merged_clearance, Clearance, AccessLevel

        class MyController:
            clearance = Clearance(level=AccessLevel.INTERNAL)

        async def handler():
            pass

        merged = build_merged_clearance(MyController, handler)
        assert merged is not None
        assert merged.level == AccessLevel.INTERNAL

    def test_method_only(self):
        from aquilia.auth.clearance import build_merged_clearance, Clearance, AccessLevel, grant

        class MyController:
            pass

        @grant(level=AccessLevel.CONFIDENTIAL, entitlements=["test:read"])
        async def handler():
            pass

        merged = build_merged_clearance(MyController, handler)
        assert merged is not None
        assert merged.level == AccessLevel.CONFIDENTIAL

    def test_class_and_method_merged(self):
        from aquilia.auth.clearance import build_merged_clearance, Clearance, AccessLevel, grant

        class MyController:
            clearance = Clearance(
                level=AccessLevel.INTERNAL,
                entitlements=["base:read"],
            )

        @grant(level=AccessLevel.CONFIDENTIAL, entitlements=["extra:write"])
        async def handler():
            pass

        merged = build_merged_clearance(MyController, handler)
        assert merged.level == AccessLevel.CONFIDENTIAL
        assert "base:read" in merged.entitlements
        assert "extra:write" in merged.entitlements


# ============================================================================
# 2. AUDIT TRAIL TESTS
# ============================================================================


class TestAuditEventType:
    """Test audit event type enum."""

    def test_auth_events_exist(self):
        from aquilia.auth.audit import AuditEventType

        assert AuditEventType.AUTH_LOGIN_SUCCESS.value == "auth.login.success"
        assert AuditEventType.AUTH_LOGIN_FAILURE.value == "auth.login.failure"
        assert AuditEventType.AUTH_LOGOUT.value == "auth.logout"

    def test_authz_events_exist(self):
        from aquilia.auth.audit import AuditEventType

        assert AuditEventType.AUTHZ_ACCESS_GRANTED.value == "authz.access.granted"
        assert AuditEventType.AUTHZ_CLEARANCE_DENIED.value == "authz.clearance.denied"

    def test_session_events_exist(self):
        from aquilia.auth.audit import AuditEventType

        assert AuditEventType.SESSION_CREATED.value == "session.created"
        assert AuditEventType.SESSION_HIJACK_ATTEMPT.value == "session.hijack_attempt"


class TestAuditEvent:
    """Test AuditEvent data class."""

    def test_event_creation(self):
        from aquilia.auth.audit import AuditEvent, AuditEventType, AuditSeverity

        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            identity_id="user-1",
        )
        assert event.event_type == AuditEventType.AUTH_LOGIN_SUCCESS
        assert event.identity_id == "user-1"
        assert event.timestamp > 0

    def test_event_to_dict(self):
        from aquilia.auth.audit import AuditEvent, AuditEventType, AuditSeverity

        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            severity=AuditSeverity.WARNING,
            identity_id="user-2",
            ip_address="10.0.0.1",
        )
        d = event.to_dict()
        assert d["event_type"] == "auth.login.failure"
        assert d["severity"] == "warning"
        assert d["identity_id"] == "user-2"
        assert d["ip_address"] == "10.0.0.1"

    def test_event_to_json(self):
        import json
        from aquilia.auth.audit import AuditEvent, AuditEventType, AuditSeverity

        event = AuditEvent(
            event_type=AuditEventType.AUTH_TOKEN_ISSUED,
            severity=AuditSeverity.INFO,
        )
        j = event.to_json()
        parsed = json.loads(j)
        assert parsed["event_type"] == "auth.token.issued"

    def test_event_iso_timestamp(self):
        from aquilia.auth.audit import AuditEvent, AuditEventType, AuditSeverity

        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGOUT,
            severity=AuditSeverity.INFO,
            timestamp=1700000000.0,
        )
        assert "2023" in event.timestamp_iso


class TestMemoryAuditStore:
    """Test in-memory audit store."""

    @pytest.mark.asyncio
    async def test_emit_and_query(self):
        from aquilia.auth.audit import (
            MemoryAuditStore,
            AuditEvent,
            AuditEventType,
            AuditSeverity,
        )

        store = MemoryAuditStore()
        event = AuditEvent(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            identity_id="user-1",
        )
        await store.emit(event)
        results = await store.query(identity_id="user-1")
        assert len(results) == 1
        assert results[0].identity_id == "user-1"

    @pytest.mark.asyncio
    async def test_query_by_event_type(self):
        from aquilia.auth.audit import (
            MemoryAuditStore,
            AuditEvent,
            AuditEventType,
            AuditSeverity,
        )

        store = MemoryAuditStore()
        await store.emit(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
                severity=AuditSeverity.INFO,
            )
        )
        await store.emit(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                severity=AuditSeverity.WARNING,
            )
        )
        results = await store.query(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
        )
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_ring_buffer_eviction(self):
        from aquilia.auth.audit import (
            MemoryAuditStore,
            AuditEvent,
            AuditEventType,
            AuditSeverity,
        )

        store = MemoryAuditStore(max_events=5)
        for i in range(10):
            await store.emit(
                AuditEvent(
                    event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
                    severity=AuditSeverity.INFO,
                    identity_id=f"user-{i}",
                )
            )
        assert len(store.events) == 5

    @pytest.mark.asyncio
    async def test_clear(self):
        from aquilia.auth.audit import (
            MemoryAuditStore,
            AuditEvent,
            AuditEventType,
            AuditSeverity,
        )

        store = MemoryAuditStore()
        await store.emit(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGOUT,
                severity=AuditSeverity.INFO,
            )
        )
        store.clear()
        assert len(store.events) == 0


class TestAuditTrail:
    """Test AuditTrail convenience methods."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        from aquilia.auth.audit import AuditTrail, MemoryAuditStore, AuditEventType

        store = MemoryAuditStore()
        trail = AuditTrail(stores=[store])
        await trail.login_success("user-1")
        events = await store.query()
        assert len(events) == 1
        assert events[0].event_type == AuditEventType.AUTH_LOGIN_SUCCESS

    @pytest.mark.asyncio
    async def test_login_failure(self):
        from aquilia.auth.audit import AuditTrail, MemoryAuditStore, AuditEventType

        store = MemoryAuditStore()
        trail = AuditTrail(stores=[store])
        await trail.login_failure("user-2", reason="invalid_credentials")
        events = await store.query()
        assert events[0].event_type == AuditEventType.AUTH_LOGIN_FAILURE
        assert events[0].details["reason"] == "invalid_credentials"

    @pytest.mark.asyncio
    async def test_access_denied(self):
        from aquilia.auth.audit import AuditTrail, MemoryAuditStore

        store = MemoryAuditStore()
        trail = AuditTrail(stores=[store])
        await trail.access_denied("user-1", resource="/admin")
        events = await store.query()
        assert events[0].resource == "/admin"
        assert events[0].outcome == "failure"

    @pytest.mark.asyncio
    async def test_clearance_evaluated(self):
        from aquilia.auth.audit import AuditTrail, MemoryAuditStore, AuditEventType

        store = MemoryAuditStore()
        trail = AuditTrail(stores=[store])
        await trail.clearance_evaluated("user-1", "/docs", granted=True)
        events = await store.query()
        assert events[0].event_type == AuditEventType.AUTHZ_CLEARANCE_GRANTED

    @pytest.mark.asyncio
    async def test_account_locked(self):
        from aquilia.auth.audit import AuditTrail, MemoryAuditStore, AuditSeverity

        store = MemoryAuditStore()
        trail = AuditTrail(stores=[store])
        await trail.account_locked("user-1")
        events = await store.query()
        assert events[0].severity == AuditSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_multiple_stores(self):
        from aquilia.auth.audit import AuditTrail, MemoryAuditStore

        store1 = MemoryAuditStore()
        store2 = MemoryAuditStore()
        trail = AuditTrail(stores=[store1, store2])
        await trail.login_success("user-1")
        assert len(store1.events) == 1
        assert len(store2.events) == 1

    @pytest.mark.asyncio
    async def test_extract_request_info(self):
        from aquilia.auth.audit import AuditTrail, MemoryAuditStore

        store = MemoryAuditStore()
        trail = AuditTrail(stores=[store])
        request = MagicMock()
        request.client = ("10.0.0.1", 8080)
        request.state = {"request_id": "req-123"}
        request.headers = MagicMock()
        request.headers.get = lambda key, default="": {
            "user-agent": "TestAgent/1.0",
        }.get(key, default)

        await trail.login_success("user-1", request=request)
        events = await store.query()
        assert events[0].ip_address == "10.0.0.1"


# ============================================================================
# 3. SECURITY HARDENING TESTS
# ============================================================================


class TestConstantTimeCompare:
    """Test constant-time comparison."""

    def test_equal_strings(self):
        from aquilia.auth.hardening import constant_time_compare

        assert constant_time_compare("hello", "hello") is True

    def test_unequal_strings(self):
        from aquilia.auth.hardening import constant_time_compare

        assert constant_time_compare("hello", "world") is False

    def test_equal_bytes(self):
        from aquilia.auth.hardening import constant_time_compare

        assert constant_time_compare(b"abc", b"abc") is True

    def test_empty_strings(self):
        from aquilia.auth.hardening import constant_time_compare

        assert constant_time_compare("", "") is True

    def test_mixed_types(self):
        from aquilia.auth.hardening import constant_time_compare

        assert constant_time_compare("abc", b"abc") is True


class TestCSRFProtection:
    """Test CSRF token generation and validation."""

    def test_generate_token(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        assert token
        assert ":" in token

    def test_validate_valid_token(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        assert csrf.validate_token(token) is True

    def test_validate_invalid_token(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection(secret="test-secret")
        assert csrf.validate_token("invalid") is False

    def test_validate_tampered_token(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection(secret="test-secret")
        token = csrf.generate_token()
        # Tamper with signature
        parts = token.rsplit(":", 1)
        tampered = parts[0] + ":0000000000"
        assert csrf.validate_token(tampered) is False

    def test_validate_expired_token(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection(secret="test-secret", max_age=0)
        token = csrf.generate_token()
        # Token is immediately expired (max_age=0)
        time.sleep(0.01)
        assert csrf.validate_token(token) is False

    def test_validate_empty_token(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection(secret="test-secret")
        assert csrf.validate_token("") is False

    def test_requires_validation_post(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection()
        assert csrf.requires_validation("POST") is True
        assert csrf.requires_validation("PUT") is True
        assert csrf.requires_validation("DELETE") is True

    def test_safe_methods_skip_validation(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection()
        assert csrf.requires_validation("GET") is False
        assert csrf.requires_validation("HEAD") is False
        assert csrf.requires_validation("OPTIONS") is False

    def test_different_secrets_reject(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf1 = CSRFProtection(secret="secret-1")
        csrf2 = CSRFProtection(secret="secret-2")
        token = csrf1.generate_token()
        assert csrf2.validate_token(token) is False


class TestRequestFingerprint:
    """Test request fingerprinting."""

    def test_fingerprint_creation(self):
        from aquilia.auth.hardening import RequestFingerprint

        request = MagicMock()
        request.client = ("10.0.0.1", 8080)
        request.headers = MagicMock()
        request.headers.get = lambda key, default="": {
            "user-agent": "TestBrowser/1.0",
            "accept-language": "en-US",
        }.get(key, default)

        fp = RequestFingerprint.from_request(request)
        assert fp.ip_hash
        assert fp.ua_hash
        assert fp.accept_hash

    def test_fingerprint_match(self):
        from aquilia.auth.hardening import RequestFingerprint

        fp1 = RequestFingerprint(ip_hash="a", ua_hash="b", accept_hash="c")
        fp2 = RequestFingerprint(ip_hash="a", ua_hash="b", accept_hash="c")
        assert fp1.matches(fp2, strict=True) is True

    def test_fingerprint_partial_match(self):
        from aquilia.auth.hardening import RequestFingerprint

        # IP changed but UA and Accept same — non-strict allows
        fp1 = RequestFingerprint(ip_hash="a", ua_hash="b", accept_hash="c")
        fp2 = RequestFingerprint(ip_hash="x", ua_hash="b", accept_hash="c")
        assert fp1.matches(fp2, strict=False) is True
        assert fp1.matches(fp2, strict=True) is False

    def test_fingerprint_no_match(self):
        from aquilia.auth.hardening import RequestFingerprint

        fp1 = RequestFingerprint(ip_hash="a", ua_hash="b", accept_hash="c")
        fp2 = RequestFingerprint(ip_hash="x", ua_hash="y", accept_hash="z")
        assert fp1.matches(fp2) is False

    def test_fingerprint_serialization(self):
        from aquilia.auth.hardening import RequestFingerprint

        fp = RequestFingerprint(ip_hash="abc", ua_hash="def", accept_hash="ghi")
        s = fp.to_string()
        restored = RequestFingerprint.from_string(s)
        assert restored is not None
        assert restored.ip_hash == "abc"
        assert restored.ua_hash == "def"

    def test_fingerprint_from_invalid_string(self):
        from aquilia.auth.hardening import RequestFingerprint

        assert RequestFingerprint.from_string("invalid") is None


class TestSecurityHeaders:
    """Test security headers."""

    def test_default_headers(self):
        from aquilia.auth.hardening import SecurityHeaders

        headers = SecurityHeaders()
        d = headers.to_dict()
        assert "Content-Security-Policy" in d
        assert "Strict-Transport-Security" in d
        assert "X-Content-Type-Options" in d
        assert d["X-Content-Type-Options"] == "nosniff"
        assert d["X-Frame-Options"] == "DENY"

    def test_custom_csp(self):
        from aquilia.auth.hardening import SecurityHeaders

        headers = SecurityHeaders(content_security_policy="default-src 'self'; script-src 'self'")
        assert "script-src" in headers.to_dict()["Content-Security-Policy"]

    def test_apply_to_response(self):
        from aquilia.auth.hardening import SecurityHeaders

        headers = SecurityHeaders()
        response = MagicMock()
        response.headers = {}
        headers.apply(response)
        assert "X-Frame-Options" in response.headers


class TestTokenBinder:
    """Test token binding for proof-of-possession."""

    def test_create_and_verify_binding(self):
        from aquilia.auth.hardening import TokenBinder, RequestFingerprint

        binder = TokenBinder(secret="test-secret")
        fp = RequestFingerprint(ip_hash="a", ua_hash="b", accept_hash="c")
        token = "access_token_123"

        binding = binder.create_binding(token, fp)
        assert binder.verify_binding(token, fp, binding) is True

    def test_binding_fails_different_token(self):
        from aquilia.auth.hardening import TokenBinder, RequestFingerprint

        binder = TokenBinder(secret="test-secret")
        fp = RequestFingerprint(ip_hash="a", ua_hash="b", accept_hash="c")

        binding = binder.create_binding("token-1", fp)
        assert binder.verify_binding("token-2", fp, binding) is False

    def test_binding_fails_different_fingerprint(self):
        from aquilia.auth.hardening import TokenBinder, RequestFingerprint

        binder = TokenBinder(secret="test-secret")
        fp1 = RequestFingerprint(ip_hash="a", ua_hash="b", accept_hash="c")
        fp2 = RequestFingerprint(ip_hash="x", ua_hash="y", accept_hash="z")

        binding = binder.create_binding("token", fp1)
        assert binder.verify_binding("token", fp2, binding) is False


class TestSecureTokenGeneration:
    """Test secure token utilities."""

    def test_generate_secure_token(self):
        from aquilia.auth.hardening import generate_secure_token

        token = generate_secure_token()
        assert len(token) > 20

    def test_generate_opaque_id(self):
        from aquilia.auth.hardening import generate_opaque_id

        oid = generate_opaque_id("usr")
        assert oid.startswith("usr_")
        assert len(oid) > 10

    def test_hash_token(self):
        from aquilia.auth.hardening import hash_token

        h = hash_token("my-secret-token")
        assert len(h) == 64  # SHA-256 hex
        assert h == hash_token("my-secret-token")  # Deterministic

    def test_hash_sensitive(self):
        from aquilia.auth.hardening import hash_sensitive

        h = hash_sensitive("value", salt="salt")
        assert len(h) == 64


# ============================================================================
# 4. AUTH MANAGER TESTS
# ============================================================================


class TestRateLimiter:
    """Test RateLimiter."""

    def test_not_locked_initially(self):
        from aquilia.auth.manager import RateLimiter

        rl = RateLimiter(max_attempts=3)
        assert rl.is_locked_out("user-1") is False

    def test_lockout_after_max_attempts(self):
        from aquilia.auth.manager import RateLimiter

        rl = RateLimiter(max_attempts=3, window_seconds=60, lockout_duration=60)
        for _ in range(3):
            rl.record_attempt("user-1")
        assert rl.is_locked_out("user-1") is True

    def test_remaining_attempts(self):
        from aquilia.auth.manager import RateLimiter

        rl = RateLimiter(max_attempts=5)
        rl.record_attempt("user-1")
        rl.record_attempt("user-1")
        assert rl.get_remaining_attempts("user-1") == 3

    def test_reset_clears_attempts(self):
        from aquilia.auth.manager import RateLimiter

        rl = RateLimiter(max_attempts=3)
        for _ in range(3):
            rl.record_attempt("user-1")
        rl.reset("user-1")
        assert rl.is_locked_out("user-1") is False
        assert rl.get_remaining_attempts("user-1") == 3

    def test_zero_max_attempts_always_locked(self):
        from aquilia.auth.manager import RateLimiter

        rl = RateLimiter(max_attempts=0)
        assert rl.is_locked_out("user-1") is True


class TestAuthManager:
    """Test AuthManager authentication flows."""

    @pytest.fixture
    def setup_auth(self):
        from aquilia.auth.stores import (
            MemoryIdentityStore,
            MemoryCredentialStore,
            MemoryTokenStore,
        )
        from aquilia.auth.manager import AuthManager, RateLimiter
        from aquilia.auth.tokens import TokenManager, KeyRing, KeyDescriptor, TokenConfig
        from aquilia.auth.hashing import PasswordHasher
        from aquilia.auth.core import Identity, IdentityStatus, IdentityType

        identity_store = MemoryIdentityStore()
        credential_store = MemoryCredentialStore()
        token_store = MemoryTokenStore()
        hasher = PasswordHasher()
        key = KeyDescriptor(
            kid="auth-key",
            algorithm="RS256",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        key_ring = KeyRing(keys=[key])
        token_mgr = TokenManager(
            key_ring=key_ring,
            token_store=token_store,
        )
        rate_limiter = RateLimiter(max_attempts=5)

        manager = AuthManager(
            identity_store=identity_store,
            credential_store=credential_store,
            token_manager=token_mgr,
            password_hasher=hasher,
            rate_limiter=rate_limiter,
        )

        return {
            "manager": manager,
            "identity_store": identity_store,
            "credential_store": credential_store,
            "token_store": token_store,
            "hasher": hasher,
        }

    @pytest.mark.asyncio
    async def test_manager_instantiation(self, setup_auth):
        manager = setup_auth["manager"]
        assert manager is not None


# ============================================================================
# 5. TOKEN MANAGEMENT TESTS
# ============================================================================


class TestKeyRing:
    """Test KeyRing key management."""

    def _make_key(self, kid="test-key-1", status="active"):
        from aquilia.auth.tokens import KeyDescriptor

        return KeyDescriptor(
            kid=kid,
            algorithm="RS256",
            public_key_pem="pub",
            private_key_pem="priv",
            status=status,
        )

    def test_keyring_creation(self):
        from aquilia.auth.tokens import KeyRing

        kr = KeyRing(keys=[self._make_key()])
        assert kr is not None

    def test_keyring_active_key(self):
        from aquilia.auth.tokens import KeyRing

        kr = KeyRing(keys=[self._make_key(kid="test-key-1")])
        active = kr.get_signing_key()
        assert active is not None
        assert active.kid == "test-key-1"

    def test_keyring_get_by_kid(self):
        from aquilia.auth.tokens import KeyRing

        kr = KeyRing(keys=[self._make_key(kid="key-abc")])
        found = kr.get_verification_key("key-abc")
        assert found is not None
        assert found.kid == "key-abc"

    def test_keyring_revoke(self):
        from aquilia.auth.tokens import KeyRing, KeyStatus

        kr = KeyRing(keys=[self._make_key(kid="key-rev")])
        kr.revoke_key("key-rev")
        found = kr.keys.get("key-rev")
        assert found.status == KeyStatus.REVOKED


class TestTokenManager:
    """Test TokenManager token operations."""

    def test_token_manager_creation(self):
        from aquilia.auth.tokens import TokenManager, KeyRing, KeyDescriptor
        from aquilia.auth.stores import MemoryTokenStore

        key = KeyDescriptor(
            kid="tm-key",
            algorithm="RS256",
            public_key_pem="pub",
            private_key_pem="priv",
        )
        kr = KeyRing(keys=[key])
        store = MemoryTokenStore()
        mgr = TokenManager(key_ring=kr, token_store=store)
        assert mgr is not None


# ============================================================================
# 6. AUTHORIZATION ENGINE TESTS
# ============================================================================


class TestRBACEngine:
    """Test RBAC authorization engine."""

    def test_rbac_creation(self):
        from aquilia.auth.authz import RBACEngine

        rbac = RBACEngine()
        assert rbac is not None

    def test_add_role_permissions(self):
        from aquilia.auth.authz import RBACEngine

        rbac = RBACEngine()
        rbac.define_role("editor", permissions=["docs:read", "docs:write"])
        perms = rbac.get_permissions("editor")
        assert "docs:read" in perms
        assert "docs:write" in perms

    def test_role_hierarchy(self):
        from aquilia.auth.authz import RBACEngine

        rbac = RBACEngine()
        rbac.define_role("viewer", permissions=["docs:read"])
        rbac.define_role("editor", permissions=["docs:write"], inherits=["viewer"])
        perms = rbac.get_permissions("editor")
        assert "docs:read" in perms  # Inherited
        assert "docs:write" in perms

    def test_check_permission(self):
        from aquilia.auth.authz import RBACEngine

        rbac = RBACEngine()
        rbac.define_role("admin", permissions=["*"])
        assert rbac.check_permission(["admin"], "*") is True


class TestABACEngine:
    """Test ABAC authorization engine."""

    def test_abac_creation(self):
        from aquilia.auth.authz import ABACEngine

        abac = ABACEngine()
        assert abac is not None

    def test_register_and_evaluate_policy(self):
        from aquilia.auth.authz import ABACEngine, AuthzContext, AuthzResult, Decision
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        abac = ABACEngine()

        def allow_active_users(ctx: AuthzContext) -> AuthzResult:
            if ctx.attributes.get("status") == "active":
                return AuthzResult(decision=Decision.ALLOW)
            return AuthzResult(decision=Decision.DENY)

        abac.register_policy("allow_active", allow_active_users)

        identity = Identity(
            id="u1",
            type=IdentityType.USER,
            attributes={},
            status=IdentityStatus.ACTIVE,
        )
        ctx = AuthzContext(
            identity=identity,
            resource="test",
            action="read",
            attributes={"status": "active"},
        )
        result = abac.evaluate(ctx, "allow_active")
        assert result.decision == Decision.ALLOW

    def test_deny_policy(self):
        from aquilia.auth.authz import ABACEngine, AuthzContext, AuthzResult, Decision
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        abac = ABACEngine()

        def deny_suspended(ctx: AuthzContext) -> AuthzResult:
            if ctx.attributes.get("status") == "suspended":
                return AuthzResult(decision=Decision.DENY)
            return AuthzResult(decision=Decision.ALLOW)

        abac.register_policy("deny_suspended", deny_suspended)

        identity = Identity(
            id="u1",
            type=IdentityType.USER,
            attributes={},
            status=IdentityStatus.ACTIVE,
        )
        ctx = AuthzContext(
            identity=identity,
            resource="test",
            action="read",
            attributes={"status": "suspended"},
        )
        result = abac.evaluate(ctx, "deny_suspended")
        assert result.decision == Decision.DENY


class TestAuthzEngine:
    """Test unified AuthzEngine."""

    def test_authz_engine_creation(self):
        from aquilia.auth.authz import AuthzEngine, RBACEngine, ABACEngine

        rbac = RBACEngine()
        abac = ABACEngine()
        engine = AuthzEngine(rbac=rbac, abac=abac)
        assert engine is not None

    def test_check_role(self):
        from aquilia.auth.authz import AuthzEngine, RBACEngine, ABACEngine, AuthzContext
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        rbac = RBACEngine()
        abac = ABACEngine()
        engine = AuthzEngine(rbac=rbac, abac=abac)

        identity = Identity(
            id="u1",
            type=IdentityType.USER,
            attributes={},
            status=IdentityStatus.ACTIVE,
        )
        ctx = AuthzContext(
            identity=identity,
            resource="test",
            action="read",
            roles=["admin"],
        )
        # Should not raise
        engine.check_role(ctx, ["admin"])
        # Should raise for missing role
        ctx_no_role = AuthzContext(
            identity=identity,
            resource="test",
            action="read",
            roles=["user"],
        )
        with pytest.raises(Exception):
            engine.check_role(ctx_no_role, ["superadmin"])

    def test_check_scope(self):
        from aquilia.auth.authz import AuthzEngine, RBACEngine, ABACEngine, AuthzContext
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        rbac = RBACEngine()
        abac = ABACEngine()
        engine = AuthzEngine(rbac=rbac, abac=abac)

        identity = Identity(
            id="u1",
            type=IdentityType.USER,
            attributes={},
            status=IdentityStatus.ACTIVE,
        )
        ctx = AuthzContext(
            identity=identity,
            resource="test",
            action="read",
            scopes=["read", "write"],
        )
        # Should not raise
        engine.check_scope(ctx, ["read"])
        # Should raise for missing scope
        with pytest.raises(Exception):
            engine.check_scope(ctx, ["delete"])


# ============================================================================
# 7. PASSWORD HASHING & POLICY TESTS
# ============================================================================


class TestPasswordHasher:
    """Test password hashing."""

    @pytest.mark.asyncio
    async def test_hash_and_verify(self):
        from aquilia.auth.hashing import PasswordHasher

        hasher = PasswordHasher()
        hashed = await hasher.hash_async("mysecretpassword")
        assert hashed != "mysecretpassword"
        assert await hasher.verify_async(hashed, "mysecretpassword") is True

    @pytest.mark.asyncio
    async def test_wrong_password_fails(self):
        from aquilia.auth.hashing import PasswordHasher

        hasher = PasswordHasher()
        hashed = await hasher.hash_async("correct-password")
        assert await hasher.verify_async(hashed, "wrong-password") is False

    def test_sync_hash_and_verify(self):
        from aquilia.auth.hashing import PasswordHasher

        hasher = PasswordHasher()
        hashed = hasher.hash("password123")
        assert hasher.verify(hashed, "password123") is True
        assert hasher.verify(hashed, "wrong") is False


class TestPasswordPolicy:
    """Test password policy validation."""

    def test_default_policy(self):
        from aquilia.auth.hashing import PasswordPolicy

        policy = PasswordPolicy()
        assert policy.min_length > 0

    def test_short_password_rejected(self):
        from aquilia.auth.hashing import PasswordPolicy

        policy = PasswordPolicy(min_length=8)
        is_valid, errors = policy.validate("short")
        assert is_valid is False
        assert len(errors) > 0

    def test_valid_password_accepted(self):
        from aquilia.auth.hashing import PasswordPolicy

        policy = PasswordPolicy(
            min_length=8,
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
            require_special=False,
        )
        is_valid, errors = policy.validate("a-long-enough-password")
        assert is_valid is True
        assert len(errors) == 0


# ============================================================================
# 8. GUARDS & FLOW INTEGRATION TESTS
# ============================================================================


class TestFlowGuards:
    """Test auth flow guards."""

    def test_require_auth_guard_creation(self):
        from aquilia.auth.integration.flow_guards import RequireAuthGuard

        guard = RequireAuthGuard()
        assert guard is not None

    def test_require_scopes_guard_creation(self):
        from aquilia.auth.integration.flow_guards import RequireScopesGuard

        guard = RequireScopesGuard("read", "write")
        assert guard is not None

    def test_require_roles_guard_creation(self):
        from aquilia.auth.integration.flow_guards import RequireRolesGuard

        guard = RequireRolesGuard("admin")
        assert guard is not None

    @pytest.mark.asyncio
    async def test_require_auth_guard_denies_unauthenticated(self):
        from aquilia.auth.integration.flow_guards import RequireAuthGuard

        guard = RequireAuthGuard()
        context = {"identity": None}

        with pytest.raises(Exception):
            await guard(context)

    @staticmethod
    def _build_guard_context(
        *, header_map: dict[str, str] | None = None, session: Any = None, auth_manager: Any = None
    ):
        from aquilia.auth.manager import AuthManager
        from aquilia.di import Container
        from aquilia.di.providers import ValueProvider

        request = MagicMock()
        request.state = {}
        if session is not None:
            request.state["session"] = session

        headers = header_map or {}
        request.header = lambda name, default="": headers.get(name, default)

        container = Container(scope="request")
        if auth_manager is not None:
            container.register(
                ValueProvider(
                    value=auth_manager,
                    token=AuthManager,
                    scope="request",
                    name="auth_manager_for_flow_guard_tests",
                )
            )

        return {"request": request, "container": container}

    @pytest.mark.asyncio
    async def test_require_token_auth_guard_resolves_auth_manager_from_context_container(self):
        from aquilia.auth.integration.flow_guards import RequireTokenAuthGuard

        fake_identity = object()
        fake_claims = {"sub": "u-1"}

        auth_manager = AsyncMock()
        auth_manager.get_identity_from_token.return_value = fake_identity
        auth_manager.verify_token.return_value = fake_claims

        guard = RequireTokenAuthGuard()
        context = self._build_guard_context(
            header_map={"authorization": "Bearer token-1"},
            auth_manager=auth_manager,
        )

        result = await guard(context)

        assert result["token_claims"] == fake_claims
        assert context["request"].state["identity"] is fake_identity
        assert context["request"].state["authenticated"] is True

    @pytest.mark.asyncio
    async def test_require_session_auth_guard_resolves_auth_manager_from_context_container(self):
        from aquilia.auth.integration.flow_guards import RequireSessionAuthGuard

        fake_session = MagicMock()
        fake_identity = object()

        auth_manager = AsyncMock()
        auth_manager.identity_store.get_identity.return_value = fake_identity

        with patch("aquilia.auth.integration.flow_guards.get_identity_id", return_value="identity-1"):
            guard = RequireSessionAuthGuard()
            context = self._build_guard_context(session=fake_session, auth_manager=auth_manager)
            await guard(context)

        assert context["request"].state["identity"] is fake_identity
        assert context["request"].state["authenticated"] is True

    @pytest.mark.asyncio
    async def test_require_api_key_guard_without_provider_raises_di_resolution_fault(self):
        from aquilia.auth.integration.flow_guards import RequireApiKeyGuard
        from aquilia.faults.domains import DIResolutionFault

        guard = RequireApiKeyGuard()
        context = self._build_guard_context(header_map={"x-api-key": "k1"}, auth_manager=None)

        with pytest.raises(DIResolutionFault, match="AuthManager"):
            await guard(context)


class TestCoreAuthGuards:
    """Test core auth guards in direct/dict flow contexts."""

    @staticmethod
    def _build_context(*, auth_header: str = "", auth_manager: Any = None) -> dict[str, Any]:
        from aquilia.auth.manager import AuthManager
        from aquilia.di import Container
        from aquilia.di.providers import ValueProvider

        request = MagicMock()
        request.headers = {"authorization": auth_header}

        container = Container(scope="request")
        if auth_manager is not None:
            container.register(
                ValueProvider(
                    value=auth_manager,
                    token=AuthManager,
                    scope="request",
                    name="auth_manager_for_core_guard_tests",
                )
            )

        return {"request": request, "container": container}

    @pytest.mark.asyncio
    async def test_auth_guard_resolves_auth_manager_from_context_container(self):
        from aquilia.auth.guards import AuthGuard

        fake_identity = object()
        fake_claims = {"sub": "u-1"}

        auth_manager = AsyncMock()
        auth_manager.get_identity_from_token.return_value = fake_identity
        auth_manager.verify_token.return_value = fake_claims

        guard = AuthGuard()
        context = self._build_context(auth_header="Bearer token-123", auth_manager=auth_manager)

        result = await guard(context)

        assert result["identity"] is fake_identity
        assert result["token_claims"] == fake_claims

    @pytest.mark.asyncio
    async def test_auth_guard_without_provider_raises_di_resolution_fault(self):
        from aquilia.auth.guards import AuthGuard
        from aquilia.faults.domains import DIResolutionFault

        guard = AuthGuard()
        context = self._build_context(auth_header="Bearer token-123", auth_manager=None)

        with pytest.raises(DIResolutionFault, match="AuthManager"):
            await guard(context)


# ============================================================================
# 9. CONTROLLER CLEARANCE WIRING TESTS
# ============================================================================


class TestControllerClearanceWiring:
    """Test that clearance is properly wired into controller engine."""

    def test_engine_accepts_clearance_engine(self):
        from aquilia.controller.engine import ControllerEngine
        from aquilia.auth.clearance import ClearanceEngine

        factory = MagicMock()
        ce = ClearanceEngine()
        engine = ControllerEngine(factory=factory, clearance_engine=ce)
        assert engine.clearance_engine is ce

    def test_engine_has_clearance_cache(self):
        from aquilia.controller.engine import ControllerEngine

        assert hasattr(ControllerEngine, "_clearance_cache")

    def test_extract_controller_clearance(self):
        from aquilia.auth.clearance import extract_controller_clearance, Clearance, AccessLevel

        class MyController:
            clearance = Clearance(level=AccessLevel.INTERNAL)

        c = extract_controller_clearance(MyController)
        assert c is not None
        assert c.level == AccessLevel.INTERNAL

    def test_extract_no_clearance(self):
        from aquilia.auth.clearance import extract_controller_clearance

        class MyController:
            pass

        assert extract_controller_clearance(MyController) is None

    @pytest.mark.asyncio
    async def test_controller_engine_clearance_denied_renders_html_for_browser_accept(self):
        from aquilia.auth.clearance import AccessLevel, Clearance
        from aquilia.controller.engine import ControllerEngine

        class MyController:
            clearance = Clearance(level=AccessLevel.RESTRICTED)

        async def handler(self, ctx):
            return None

        engine = ControllerEngine(factory=MagicMock())
        route = MagicMock()
        request = MagicMock()
        request.header.return_value = "text/html"
        ctx = MagicMock(identity=None, state={})

        response = await engine._evaluate_clearance(route, MyController, handler, request, ctx)

        assert response is not None
        assert response.status == 401
        assert response.headers.get("content-type") == "text/html; charset=utf-8"
        assert "<!DOCTYPE html>" in str(response._content)


# ============================================================================
# 10. POLICY DSL TESTS
# ============================================================================


class TestPolicyDSL:
    """Test Policy DSL."""

    def test_policy_creation(self):
        from aquilia.auth.policy import Policy

        class DocumentPolicy(Policy):
            resource = "document"

        p = DocumentPolicy()
        assert p.resource == "document"

    def test_policy_registry(self):
        from aquilia.auth.policy import PolicyRegistry, Policy

        class TestPolicy(Policy):
            resource = "test_item"

        registry = PolicyRegistry()
        policy_instance = TestPolicy()
        registry.register(policy_instance)
        found = registry.get("test_item")
        assert found is policy_instance

    def test_allow_deny_helpers(self):
        from aquilia.auth.policy import Allow, Deny, Abstain, PolicyDecision

        allowed = Allow()
        assert allowed.decision == PolicyDecision.ALLOW

        denied = Deny("forbidden")
        assert denied.decision == PolicyDecision.DENY
        assert denied.reason == "forbidden"

        abstained = Abstain()
        assert abstained.decision == PolicyDecision.ABSTAIN

    def test_rule_decorator(self):
        from aquilia.auth.policy import Policy, rule, Allow, Deny

        class ItemPolicy(Policy):
            resource = "item"

            @rule
            def can_read(self, identity, resource, **kwargs):
                return Allow()

            @rule
            def can_delete(self, identity, resource, **kwargs):
                if getattr(identity, "is_admin", False):
                    return Allow()
                return Deny("not admin")

        policy = ItemPolicy()
        identity = MagicMock(is_admin=False)

        result = policy.can_read(identity, None)
        assert result.decision.name == "ALLOW"

        result = policy.can_delete(identity, None)
        assert result.decision.name == "DENY"


# ============================================================================
# 11. IDENTITY & CREDENTIAL STORE TESTS
# ============================================================================


class TestMemoryIdentityStore:
    """Test MemoryIdentityStore."""

    @pytest.mark.asyncio
    async def test_create_and_get(self):
        from aquilia.auth.stores import MemoryIdentityStore
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        store = MemoryIdentityStore()
        identity = Identity(
            id="user-1",
            type=IdentityType.USER,
            status=IdentityStatus.ACTIVE,
            attributes={"roles": ["user"], "scopes": ["read"]},
        )
        await store.create(identity)

        found = await store.get("user-1")
        assert found is not None
        assert found.id == "user-1"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        from aquilia.auth.stores import MemoryIdentityStore

        store = MemoryIdentityStore()
        found = await store.get("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_delete(self):
        from aquilia.auth.stores import MemoryIdentityStore
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        store = MemoryIdentityStore()
        identity = Identity(
            id="user-del",
            type=IdentityType.USER,
            attributes={},
            status=IdentityStatus.ACTIVE,
        )
        await store.create(identity)
        await store.delete("user-del")
        found = await store.get("user-del")
        # Soft delete — identity status should be DELETED
        assert found is not None
        assert found.status == IdentityStatus.DELETED


class TestMemoryCredentialStore:
    """Test MemoryCredentialStore."""

    @pytest.mark.asyncio
    async def test_store_and_get_password(self):
        from aquilia.auth.stores import MemoryCredentialStore
        from aquilia.auth.core import PasswordCredential

        store = MemoryCredentialStore()
        cred = PasswordCredential(
            identity_id="user-1",
            password_hash="hashed_pw",
        )
        await store.save_password(cred)

        found = await store.get_password("user-1")
        assert found is not None
        assert found.password_hash == "hashed_pw"


class TestMemoryTokenStore:
    """Test MemoryTokenStore."""

    @pytest.mark.asyncio
    async def test_store_and_get_refresh_token(self):
        from aquilia.auth.stores import MemoryTokenStore

        store = MemoryTokenStore()

        await store.save_refresh_token(
            token_id="rt-1",
            identity_id="user-1",
            scopes=["read"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        found = await store.get_refresh_token("rt-1")
        assert found is not None

    @pytest.mark.asyncio
    async def test_revoke_token(self):
        from aquilia.auth.stores import MemoryTokenStore

        store = MemoryTokenStore()

        await store.save_refresh_token(
            token_id="rt-2",
            identity_id="user-1",
            scopes=["read"],
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        await store.revoke_refresh_token("rt-2")
        is_revoked = await store.is_token_revoked("rt-2")
        assert is_revoked is True


# ============================================================================
# 12. AUTH FAULTS TESTS
# ============================================================================


class TestAuthFaults:
    """Test auth fault classes."""

    def test_invalid_credentials_fault(self):
        from aquilia.auth.faults import AUTH_INVALID_CREDENTIALS

        assert isinstance(AUTH_INVALID_CREDENTIALS, type)

    def test_rate_limited_fault(self):
        from aquilia.auth.faults import AUTH_RATE_LIMITED

        assert isinstance(AUTH_RATE_LIMITED, type)

    def test_token_expired_fault(self):
        from aquilia.auth.faults import AUTH_TOKEN_EXPIRED

        assert isinstance(AUTH_TOKEN_EXPIRED, type)

    def test_session_required_fault(self):
        from aquilia.auth.faults import AUTH_SESSION_REQUIRED

        assert isinstance(AUTH_SESSION_REQUIRED, type)

    def test_authz_policy_denied(self):
        from aquilia.auth.faults import AUTHZ_POLICY_DENIED

        assert isinstance(AUTHZ_POLICY_DENIED, type)

    def test_mfa_required(self):
        from aquilia.auth.faults import AUTH_MFA_REQUIRED

        assert isinstance(AUTH_MFA_REQUIRED, type)


# ============================================================================
# 13. DI PROVIDER TESTS
# ============================================================================


class TestDIProviders:
    """Test DI provider registration."""

    def test_auth_config_builder(self):
        from aquilia.auth.integration.di_providers import AuthConfig

        config = AuthConfig()
        config.rate_limit(max_attempts=10)
        config.sessions(ttl_days=14)
        config.tokens(access_ttl_minutes=30)
        config.mfa(enabled=True)
        config.oauth(enabled=True)

        built = config.build()
        assert built["rate_limit"]["max_attempts"] == 10
        assert built["session"]["ttl_days"] == 14
        assert built["tokens"]["access_ttl_minutes"] == 30
        assert built["mfa"]["enabled"] is True
        assert built["oauth"]["enabled"] is True


# ============================================================================
# 14. INTEGRATION TESTS (Middleware + Sessions + Auth)
# ============================================================================


class TestAuthMiddlewareIntegration:
    """Test auth middleware components exist and are wired."""

    def test_auth_middleware_class(self):
        from aquilia.auth.integration.middleware import AquilAuthMiddleware

        assert AquilAuthMiddleware is not None

    def test_optional_auth_middleware(self):
        from aquilia.auth.integration.middleware import OptionalAuthMiddleware

        assert OptionalAuthMiddleware is not None

    def test_session_middleware_class(self):
        from aquilia.auth.integration.middleware import SessionMiddleware

        assert SessionMiddleware is not None

    def test_create_auth_middleware_stack(self):
        from aquilia.auth.integration.middleware import create_auth_middleware_stack

        assert callable(create_auth_middleware_stack)


class TestSessionAuthBridge:
    """Test session-auth integration."""

    def test_auth_principal_creation(self):
        from aquilia.auth.integration.aquila_sessions import AuthPrincipal

        principal = AuthPrincipal(
            identity_id="user-1",
            roles=["admin"],
            scopes=["read"],
        )
        assert principal.id == "user-1"
        assert "admin" in principal.roles


# ============================================================================
# 15. TOP-LEVEL EXPORT TESTS
# ============================================================================


class TestTopLevelExports:
    """Test that all new modules are properly exported from aquilia."""

    def test_clearance_exports(self):
        from aquilia import (
            AccessLevel,
            Clearance,
            ClearanceVerdict,
            ClearanceEngine,
            ClearanceGuard,
            grant,
            exempt,
        )

        assert AccessLevel.PUBLIC == 0
        assert Clearance is not None
        assert ClearanceVerdict is not None

    def test_audit_exports(self):
        from aquilia import (
            AuditEventType,
            AuditSeverity,
            AuditEvent,
            AuditTrail,
            MemoryAuditStore,
        )

        assert AuditEventType.AUTH_LOGIN_SUCCESS is not None
        assert AuditTrail is not None

    def test_hardening_exports(self):
        from aquilia import (
            CSRFProtection,
            RequestFingerprint,
            SecurityHeaders,
            TokenBinder,
            constant_time_compare,
            generate_secure_token,
        )

        assert CSRFProtection is not None
        assert constant_time_compare("a", "a") is True

    def test_condition_exports(self):
        from aquilia import (
            is_verified,
            is_owner_or_admin,
            within_quota,
            is_same_tenant,
        )

        assert callable(is_verified)
        assert callable(is_owner_or_admin)

    def test_auth_submodule_exports(self):
        from aquilia.auth import (
            AccessLevel,
            Clearance,
            ClearanceEngine,
            AuditTrail,
            MemoryAuditStore,
            CSRFProtection,
            SecurityHeaders,
            RequestFingerprint,
            constant_time_compare,
        )

        assert AccessLevel.RESTRICTED == 40


# ============================================================================
# 16. STRESS / EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_clearance_with_empty_identity_roles(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.INTERNAL)
        identity = MagicMock(id="1", roles=set(), scopes=set(), attributes={}, permissions=set())
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is False

    @pytest.mark.asyncio
    async def test_clearance_with_none_roles(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.AUTHENTICATED)
        identity = MagicMock(id="1", roles=None, scopes=None, attributes=None, permissions=None)
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True  # Any identity satisfies AUTHENTICATED

    @pytest.mark.asyncio
    async def test_multiple_conditions_all_must_pass(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()

        c = Clearance(
            conditions=[
                lambda i, r, c: True,
                lambda i, r, c: True,
                lambda i, r, c: False,
            ]
        )
        identity = MagicMock(id="1", roles=set(), scopes=set(), attributes={}, permissions=set())
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is False
        assert len(verdict.failed_conditions) == 1

    @pytest.mark.asyncio
    async def test_entitlements_from_attributes(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(entitlements=["special:access"])
        identity = MagicMock(
            id="1",
            roles=set(),
            scopes=set(),
            permissions=set(),
            attributes={"entitlements": ["special:access"]},
        )
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.granted is True

    def test_csrf_token_uniqueness(self):
        from aquilia.auth.hardening import CSRFProtection

        csrf = CSRFProtection(secret="test")
        tokens = {csrf.generate_token() for _ in range(100)}
        assert len(tokens) == 100  # All unique

    @pytest.mark.asyncio
    async def test_audit_trail_with_failing_store(self):
        from aquilia.auth.audit import AuditTrail, AuditStore, AuditEvent, AuditEventType, AuditSeverity

        class FailingStore(AuditStore):
            async def emit(self, event):
                raise RuntimeError("Store failed")

        trail = AuditTrail(stores=[FailingStore()])
        # Should not raise
        await trail.login_success("user-1")

    def test_fingerprint_from_minimal_request(self):
        from aquilia.auth.hardening import RequestFingerprint

        request = MagicMock(spec=[])  # No attributes
        fp = RequestFingerprint.from_request(request)
        assert fp.ip_hash  # Should still produce a hash (of empty string)

    @pytest.mark.asyncio
    async def test_audit_query_with_time_range(self):
        from aquilia.auth.audit import (
            MemoryAuditStore,
            AuditEvent,
            AuditEventType,
            AuditSeverity,
        )

        store = MemoryAuditStore()
        t1 = time.time()
        await store.emit(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
                severity=AuditSeverity.INFO,
                timestamp=t1,
            )
        )
        t2 = t1 + 100
        await store.emit(
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                severity=AuditSeverity.WARNING,
                timestamp=t2,
            )
        )
        results = await store.query(since=t1 + 50)
        assert len(results) == 1

    def test_security_headers_cache_control(self):
        from aquilia.auth.hardening import SecurityHeaders

        h = SecurityHeaders()
        d = h.to_dict()
        assert "no-store" in d["Cache-Control"]
        assert "no-cache" in d["Pragma"]

    @pytest.mark.asyncio
    async def test_clearance_verdict_identity_id(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance, AccessLevel

        engine = ClearanceEngine()
        c = Clearance(level=AccessLevel.PUBLIC)
        identity = MagicMock(id="user-xyz")
        verdict = await engine.evaluate(c, identity, None, None)
        assert verdict.identity_id == "user-xyz"

    @pytest.mark.asyncio
    async def test_clearance_compartment_no_tenant(self):
        from aquilia.auth.clearance import ClearanceEngine, Clearance

        engine = ClearanceEngine()
        c = Clearance(compartment="org:{org_id}")
        identity = MagicMock(id="1", tenant_id=None, attributes={}, roles=set(), scopes=set(), permissions=set())
        ctx = MagicMock(state={"org_id": "org-1"})
        verdict = await engine.evaluate(c, identity, None, ctx)
        # No tenant: template without "tenant:" pattern skips tenant check
        assert verdict.compartment_ok is True

    def test_rate_limiter_lockout_duration(self):
        from aquilia.auth.manager import RateLimiter

        rl = RateLimiter(max_attempts=2, lockout_duration=0)
        rl.record_attempt("test")
        rl.record_attempt("test")
        # Lockout duration is 0, should be expired immediately
        assert rl.is_locked_out("test") is False
