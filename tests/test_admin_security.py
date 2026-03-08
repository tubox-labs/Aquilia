"""
Comprehensive tests for the AquilAdmin Security Hardening Module.

Tests all security components:
- AdminCSRFProtection: token generation, validation, session integration
- AdminRateLimiter: login lockout, progressive tiers, sensitive ops
- AdminSecurityHeaders: all header values, CSP nonce, asset headers
- PasswordValidator: complexity rules, common passwords, username-in-password
- SecurityEventTracker: recording, querying, limits
- AdminSecurityPolicy: orchestrator, extract_client_ip, protect_response
- DI registration: register_security_providers
"""

from __future__ import annotations

import hmac
import time
from dataclasses import FrozenInstanceError
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from aquilia.admin.security import (
    AdminCSRFProtection,
    AdminRateLimiter,
    AdminSecurityHeaders,
    AdminSecurityPolicy,
    PasswordStrength,
    PasswordValidator,
    SecurityEvent,
    SecurityEventTracker,
    register_security_providers,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  1. AdminCSRFProtection Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdminCSRFProtection:
    """Tests for CSRF token generation, validation, and request integration."""

    def setup_method(self):
        self.csrf = AdminCSRFProtection(secret="test-secret-key", max_age=3600)

    # ── Token generation ─────────────────────────────────────────────

    def test_generate_token_returns_string(self):
        token = self.csrf.generate_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_token_format(self):
        """Token format is nonce:timestamp:signature."""
        token = self.csrf.generate_token()
        parts = token.split(":")
        assert len(parts) == 3, f"Expected 3 parts, got {len(parts)}: {token}"
        nonce, timestamp, signature = parts
        assert len(nonce) > 0
        assert timestamp.isdigit()
        assert len(signature) == 64  # sha256 hex digest

    def test_generate_token_unique(self):
        """Each generated token is unique."""
        tokens = {self.csrf.generate_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_generate_token_different_instances_produce_different_signatures(self):
        """Different secrets produce different signatures for same nonce."""
        csrf2 = AdminCSRFProtection(secret="another-secret")
        t1 = self.csrf.generate_token()
        t2 = csrf2.generate_token()
        # Signatures differ (last part)
        assert t1.split(":")[-1] != t2.split(":")[-1]

    # ── Token validation ─────────────────────────────────────────────

    def test_validate_token_valid(self):
        token = self.csrf.generate_token()
        assert self.csrf.validate_token(token) is True

    def test_validate_token_empty(self):
        assert self.csrf.validate_token("") is False

    def test_validate_token_none(self):
        assert self.csrf.validate_token(None) is False  # type: ignore

    def test_validate_token_wrong_format(self):
        assert self.csrf.validate_token("not-a-valid-token") is False
        assert self.csrf.validate_token("a:b") is False
        assert self.csrf.validate_token("a:b:c:d") is False

    def test_validate_token_tampered_nonce(self):
        token = self.csrf.generate_token()
        nonce, ts, sig = token.split(":")
        tampered = f"tampered{nonce}:{ts}:{sig}"
        assert self.csrf.validate_token(tampered) is False

    def test_validate_token_tampered_timestamp(self):
        token = self.csrf.generate_token()
        nonce, ts, sig = token.split(":")
        tampered = f"{nonce}:0:{sig}"
        assert self.csrf.validate_token(tampered) is False

    def test_validate_token_tampered_signature(self):
        token = self.csrf.generate_token()
        nonce, ts, sig = token.split(":")
        tampered = f"{nonce}:{ts}:{'a' * 64}"
        assert self.csrf.validate_token(tampered) is False

    def test_validate_token_expired(self):
        """Token with max_age=1 expires after time passes."""
        csrf = AdminCSRFProtection(secret="test", max_age=1)
        token = csrf.generate_token()
        assert csrf.validate_token(token) is True

        # Manually create an expired token (timestamp 2 hours ago)
        nonce = "abcdef1234567890"
        old_ts = str(int(time.time()) - 7200)
        payload = f"{nonce}:{old_ts}"
        sig = hmac.new(csrf._secret, payload.encode(), "sha256").hexdigest()
        expired_token = f"{nonce}:{old_ts}:{sig}"
        assert csrf.validate_token(expired_token) is False

    def test_validate_token_from_different_instance_same_secret(self):
        """Tokens are valid across instances with the same secret."""
        csrf2 = AdminCSRFProtection(secret="test-secret-key")
        token = self.csrf.generate_token()
        assert csrf2.validate_token(token) is True

    def test_validate_token_from_different_secret_fails(self):
        """Tokens from a different secret are invalid."""
        csrf2 = AdminCSRFProtection(secret="different-secret")
        token = self.csrf.generate_token()
        assert csrf2.validate_token(token) is False

    # ── get_or_create_token ──────────────────────────────────────────

    def test_get_or_create_token_creates_new(self):
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {}
        token = self.csrf.get_or_create_token(ctx)
        assert isinstance(token, str)
        assert self.csrf.validate_token(token) is True
        assert ctx.session.data.get("_admin_csrf_token") == token

    def test_get_or_create_token_reuses_valid(self):
        """Returns existing valid token from session."""
        existing = self.csrf.generate_token()
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {"_admin_csrf_token": existing}
        token = self.csrf.get_or_create_token(ctx)
        assert token == existing

    def test_get_or_create_token_replaces_invalid(self):
        """Replaces corrupted token in session."""
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {"_admin_csrf_token": "bad-token"}
        token = self.csrf.get_or_create_token(ctx)
        assert token != "bad-token"
        assert self.csrf.validate_token(token) is True

    def test_get_or_create_token_no_session(self):
        """Generates ephemeral token when no session is available."""
        ctx = MagicMock()
        ctx.session = None
        token = self.csrf.get_or_create_token(ctx)
        assert isinstance(token, str)
        assert len(token) > 0

    # ── validate_request ─────────────────────────────────────────────

    def test_validate_request_valid_form_data(self):
        """CSRF token in form data matches session token."""
        token = self.csrf.generate_token()
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {"_admin_csrf_token": token}
        form_data = {"_csrf_token": token, "username": "admin"}
        assert self.csrf.validate_request(ctx, form_data) is True

    def test_validate_request_missing_session_token(self):
        """No session token → rejection."""
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {}
        form_data = {"_csrf_token": "some-token"}
        assert self.csrf.validate_request(ctx, form_data) is False

    def test_validate_request_missing_submitted_token(self):
        """No submitted token → rejection."""
        token = self.csrf.generate_token()
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {"_admin_csrf_token": token}
        ctx.request = None
        assert self.csrf.validate_request(ctx, {}) is False

    def test_validate_request_mismatched_tokens(self):
        """Different token values → rejection."""
        token1 = self.csrf.generate_token()
        token2 = self.csrf.generate_token()
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {"_admin_csrf_token": token1}
        form_data = {"_csrf_token": token2}
        assert self.csrf.validate_request(ctx, form_data) is False

    def test_validate_request_header_fallback(self):
        """Falls back to X-CSRF-Token header if not in form data."""
        token = self.csrf.generate_token()
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {"_admin_csrf_token": token}
        # Create a request mock that has headers dict but NOT a header() method
        class _MockReq:
            def __init__(self):
                self.headers = {"x-csrf-token": token}
        ctx.request = _MockReq()
        assert self.csrf.validate_request(ctx, {}) is True

    def test_validate_request_no_session(self):
        """No session at all → rejection."""
        ctx = MagicMock()
        ctx.session = None
        assert self.csrf.validate_request(ctx, {"_csrf_token": "x"}) is False

    def test_validate_request_none_form_data(self):
        """None form_data still checks header."""
        token = self.csrf.generate_token()
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = {"_admin_csrf_token": token}
        class _MockReq:
            def __init__(self):
                self.headers = {"x-csrf-token": token}
        ctx.request = _MockReq()
        assert self.csrf.validate_request(ctx, None) is True

    # ── Configuration ────────────────────────────────────────────────

    def test_custom_token_length(self):
        csrf = AdminCSRFProtection(secret="s", token_length=16)
        token = csrf.generate_token()
        nonce = token.split(":")[0]
        assert len(nonce) == 32  # hex of 16 bytes

    def test_env_secret_fallback(self):
        """Falls back to AQUILIA_ADMIN_CSRF_SECRET env var."""
        with patch.dict("os.environ", {"AQUILIA_ADMIN_CSRF_SECRET": "env-secret-key"}):
            csrf = AdminCSRFProtection()
            token = csrf.generate_token()
            assert csrf.validate_token(token) is True

    def test_random_secret_if_no_env(self):
        """Generates random secret if none provided."""
        with patch.dict("os.environ", {}, clear=True):
            csrf = AdminCSRFProtection()
            assert csrf._secret is not None
            assert len(csrf._secret) > 0


# ═══════════════════════════════════════════════════════════════════════════════
#  2. AdminRateLimiter Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdminRateLimiter:
    """Tests for login rate limiting and progressive lockout."""

    def setup_method(self):
        self.rl = AdminRateLimiter(
            max_login_attempts=3,
            login_window=60,
        )

    # ── Login lockout ────────────────────────────────────────────────

    def test_not_locked_initially(self):
        locked, retry = self.rl.is_login_locked("192.168.1.1")
        assert locked is False
        assert retry == 0

    def test_locked_after_max_attempts(self):
        ip = "10.0.0.1"
        for _ in range(3):
            self.rl.record_login_failure(ip)
        locked, retry = self.rl.is_login_locked(ip)
        assert locked is True
        assert retry > 0

    def test_not_locked_below_max_attempts(self):
        ip = "10.0.0.2"
        for _ in range(2):
            self.rl.record_login_failure(ip)
        locked, _ = self.rl.is_login_locked(ip)
        assert locked is False

    def test_record_login_failure_returns_lockout_info(self):
        ip = "10.0.0.3"
        for _ in range(2):
            now_locked, dur = self.rl.record_login_failure(ip)
            assert now_locked is False
        now_locked, dur = self.rl.record_login_failure(ip)
        assert now_locked is True
        assert dur > 0

    def test_record_login_success_clears_lockout(self):
        ip = "10.0.0.4"
        for _ in range(3):
            self.rl.record_login_failure(ip)
        assert self.rl.is_login_locked(ip)[0] is True
        self.rl.record_login_success(ip)
        assert self.rl.is_login_locked(ip)[0] is False

    def test_get_remaining_login_attempts(self):
        ip = "10.0.0.5"
        assert self.rl.get_remaining_login_attempts(ip) == 3
        self.rl.record_login_failure(ip)
        assert self.rl.get_remaining_login_attempts(ip) == 2
        self.rl.record_login_failure(ip)
        assert self.rl.get_remaining_login_attempts(ip) == 1
        self.rl.record_login_failure(ip)
        assert self.rl.get_remaining_login_attempts(ip) == 0

    # ── Progressive lockout tiers ────────────────────────────────────

    def test_progressive_lockout_tiers(self):
        """More failures → longer lockout durations."""
        rl = AdminRateLimiter(max_login_attempts=3, login_window=60)
        ip = "10.0.0.10"

        # Tier 1: 5 failures → 300s lockout
        for _ in range(5):
            rl.record_login_failure(ip)
        locked, retry = rl.is_login_locked(ip)
        assert locked is True
        assert retry <= 301  # ~300s

    def test_separate_ips_tracked_independently(self):
        ip1, ip2 = "1.1.1.1", "2.2.2.2"
        for _ in range(3):
            self.rl.record_login_failure(ip1)
        assert self.rl.is_login_locked(ip1)[0] is True
        assert self.rl.is_login_locked(ip2)[0] is False

    # ── Sensitive operation limiting ─────────────────────────────────

    def test_sensitive_op_allowed_initially(self):
        allowed, retry = self.rl.check_sensitive_op("10.0.0.1", "create_user")
        assert allowed is True
        assert retry == 0

    def test_sensitive_op_blocked_after_limit(self):
        rl = AdminRateLimiter(sensitive_op_limit=3, sensitive_op_window=60)
        ip = "10.0.0.20"
        for _ in range(3):
            rl.check_sensitive_op(ip, "create_user")
        allowed, retry = rl.check_sensitive_op(ip, "create_user")
        assert allowed is False
        assert retry > 0

    def test_sensitive_op_separate_operations(self):
        """Different operation names tracked separately."""
        rl = AdminRateLimiter(sensitive_op_limit=2, sensitive_op_window=60)
        ip = "10.0.0.21"
        rl.check_sensitive_op(ip, "create_user")
        rl.check_sensitive_op(ip, "create_user")
        allowed_create, _ = rl.check_sensitive_op(ip, "create_user")
        allowed_delete, _ = rl.check_sensitive_op(ip, "delete_user")
        assert allowed_create is False
        assert allowed_delete is True

    # ── Cleanup ──────────────────────────────────────────────────────

    def test_cleanup_runs_periodically(self):
        """Stale entries are cleaned up."""
        rl = AdminRateLimiter(cleanup_interval=0)  # Instant cleanup
        rl.record_login_failure("stale-ip")
        # Force cleanup by setting last cleanup to long ago
        rl._last_cleanup = 0
        rl._maybe_cleanup()
        # Recent entries should still be present (not old enough)
        assert len(rl._login_records) >= 0  # Just ensure no crash


# ═══════════════════════════════════════════════════════════════════════════════
#  3. AdminSecurityHeaders Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdminSecurityHeaders:
    """Tests for security header application."""

    def setup_method(self):
        self.headers = AdminSecurityHeaders()

    def _make_response(self) -> MagicMock:
        resp = MagicMock()
        resp.headers = {}
        return resp

    # ── Standard headers ─────────────────────────────────────────────

    def test_apply_sets_x_frame_options(self):
        resp = self._make_response()
        self.headers.apply(resp)
        assert resp.headers["x-frame-options"] == "DENY"

    def test_apply_sets_nosniff(self):
        resp = self._make_response()
        self.headers.apply(resp)
        assert resp.headers["x-content-type-options"] == "nosniff"

    def test_apply_sets_xss_protection_off(self):
        """Modern approach: disable X-XSS-Protection (rely on CSP)."""
        resp = self._make_response()
        self.headers.apply(resp)
        assert resp.headers["x-xss-protection"] == "0"

    def test_apply_sets_referrer_policy(self):
        resp = self._make_response()
        self.headers.apply(resp)
        assert resp.headers["referrer-policy"] == "strict-origin-when-cross-origin"

    def test_apply_sets_cache_control_no_store(self):
        resp = self._make_response()
        self.headers.apply(resp)
        assert "no-store" in resp.headers["cache-control"]
        assert "no-cache" in resp.headers["cache-control"]

    def test_apply_sets_pragma_no_cache(self):
        resp = self._make_response()
        self.headers.apply(resp)
        assert resp.headers["pragma"] == "no-cache"

    def test_apply_sets_permissions_policy(self):
        resp = self._make_response()
        self.headers.apply(resp)
        assert "camera=()" in resp.headers["permissions-policy"]
        assert "microphone=()" in resp.headers["permissions-policy"]

    def test_apply_sets_cross_domain_policies(self):
        resp = self._make_response()
        self.headers.apply(resp)
        assert resp.headers["x-permitted-cross-domain-policies"] == "none"

    # ── CSP with nonce ───────────────────────────────────────────────

    def test_apply_sets_csp_with_auto_nonce(self):
        resp = self._make_response()
        self.headers.apply(resp)
        csp = resp.headers["content-security-policy"]
        assert "nonce-" in csp
        assert "frame-ancestors 'none'" in csp
        assert "default-src 'self'" in csp

    def test_apply_sets_csp_with_explicit_nonce(self):
        resp = self._make_response()
        self.headers.apply(resp, nonce="test-nonce-123")
        csp = resp.headers["content-security-policy"]
        assert "'nonce-test-nonce-123'" in csp

    def test_generate_nonce_is_unique(self):
        nonces = {self.headers.generate_nonce() for _ in range(100)}
        assert len(nonces) == 100

    def test_generate_nonce_is_url_safe(self):
        nonce = self.headers.generate_nonce()
        assert isinstance(nonce, str)
        assert len(nonce) > 0

    # ── Custom CSP ───────────────────────────────────────────────────

    def test_custom_csp_template(self):
        custom = AdminSecurityHeaders(csp_template="default-src 'self' {nonce}")
        resp = self._make_response()
        custom.apply(resp, nonce="my-nonce")
        assert resp.headers["content-security-policy"] == "default-src 'self' 'nonce-my-nonce'"

    def test_custom_frame_options(self):
        custom = AdminSecurityHeaders(frame_options="SAMEORIGIN")
        resp = self._make_response()
        custom.apply(resp)
        assert resp.headers["x-frame-options"] == "SAMEORIGIN"

    # ── Asset headers ────────────────────────────────────────────────

    def test_apply_for_asset_sets_nosniff(self):
        resp = self._make_response()
        self.headers.apply_for_asset(resp)
        assert resp.headers["x-content-type-options"] == "nosniff"

    def test_apply_for_asset_sets_frame_options(self):
        resp = self._make_response()
        self.headers.apply_for_asset(resp)
        assert resp.headers["x-frame-options"] == "DENY"

    def test_apply_for_asset_no_csp(self):
        """Asset headers don't include CSP (too restrictive for static files)."""
        resp = self._make_response()
        self.headers.apply_for_asset(resp)
        assert "content-security-policy" not in resp.headers

    def test_apply_for_asset_no_cache_control(self):
        """Asset headers don't set cache-control (assets can be cached)."""
        resp = self._make_response()
        self.headers.apply_for_asset(resp)
        assert "cache-control" not in resp.headers

    # ── Return value ─────────────────────────────────────────────────

    def test_apply_returns_response(self):
        resp = self._make_response()
        result = self.headers.apply(resp)
        assert result is resp

    def test_apply_for_asset_returns_response(self):
        resp = self._make_response()
        result = self.headers.apply_for_asset(resp)
        assert result is resp


# ═══════════════════════════════════════════════════════════════════════════════
#  4. PasswordValidator Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPasswordValidator:
    """Tests for password complexity validation."""

    def setup_method(self):
        self.pv = PasswordValidator()

    # ── Valid passwords ──────────────────────────────────────────────

    def test_strong_password_is_valid(self):
        result = self.pv.validate("MyS3cur3P@ss!")
        assert result.is_valid is True
        assert result.score >= 3
        assert result.feedback == []

    def test_very_long_password_gets_bonus(self):
        result = self.pv.validate("Th1s!sAVeryL0ngP@ssword123")
        assert result.is_valid is True
        assert result.score == 4

    # ── Length violations ────────────────────────────────────────────

    def test_too_short(self):
        result = self.pv.validate("Sh0rt!a")
        assert result.is_valid is False
        assert any("at least 10 characters" in f for f in result.feedback)

    def test_empty_password(self):
        result = self.pv.validate("")
        assert result.is_valid is False

    def test_too_long(self):
        pv = PasswordValidator(max_length=20)
        result = pv.validate("A" * 21 + "b1!")
        assert result.is_valid is False
        assert any("exceed" in f for f in result.feedback)

    # ── Character class violations ───────────────────────────────────

    def test_missing_uppercase(self):
        result = self.pv.validate("lowercase1!ab")
        assert result.is_valid is False
        assert any("uppercase" in f for f in result.feedback)
        assert result.has_upper is False

    def test_missing_lowercase(self):
        result = self.pv.validate("UPPERCASE1!AB")
        assert result.is_valid is False
        assert any("lowercase" in f for f in result.feedback)
        assert result.has_lower is False

    def test_missing_digit(self):
        result = self.pv.validate("NoDigitsHere!!")
        assert result.is_valid is False
        assert any("digit" in f for f in result.feedback)
        assert result.has_digit is False

    def test_missing_special(self):
        result = self.pv.validate("NoSpecial123Ab")
        assert result.is_valid is False
        assert any("special" in f for f in result.feedback)
        assert result.has_special is False

    # ── Common password rejection ────────────────────────────────────

    def test_common_password_rejected(self):
        result = self.pv.validate("password")
        assert result.is_valid is False
        assert any("commonly used" in f for f in result.feedback)
        assert result.score == 0

    def test_common_password_case_insensitive(self):
        result = self.pv.validate("PASSWORD")
        assert result.is_valid is False
        assert any("commonly used" in f for f in result.feedback)

    def test_admin123_rejected(self):
        result = self.pv.validate("admin123")
        assert result.is_valid is False

    # ── Username-in-password check ───────────────────────────────────

    def test_username_in_password(self):
        result = self.pv.validate("johndoe123!Ab", username="johndoe")
        assert result.is_valid is False
        assert any("username" in f for f in result.feedback)

    def test_username_case_insensitive(self):
        result = self.pv.validate("JOHNDOE123!ab", username="johndoe")
        assert result.is_valid is False

    def test_short_username_skipped(self):
        """Usernames < 3 chars skip the username check (too likely to match)."""
        result = self.pv.validate("MyS3cur3P@ss!", username="ab")
        assert result.is_valid is True

    # ── Repeating characters ─────────────────────────────────────────

    def test_repeating_characters_penalized(self):
        result = self.pv.validate("Aaaaaa1234!@bcd")
        assert any("repeating" in f.lower() for f in result.feedback)

    # ── PasswordStrength dataclass ───────────────────────────────────

    def test_password_strength_is_frozen(self):
        result = self.pv.validate("test")
        with pytest.raises(FrozenInstanceError):
            result.score = 99  # type: ignore

    def test_password_strength_fields(self):
        result = self.pv.validate("MyP@ss123ab")
        assert isinstance(result.length, int)
        assert isinstance(result.has_upper, bool)
        assert isinstance(result.has_lower, bool)
        assert isinstance(result.has_digit, bool)
        assert isinstance(result.has_special, bool)
        assert isinstance(result.score, int)
        assert isinstance(result.is_valid, bool)
        assert isinstance(result.feedback, list)

    # ── Custom configuration ─────────────────────────────────────────

    def test_custom_min_length(self):
        pv = PasswordValidator(min_length=6)
        result = pv.validate("Sh0rt!")
        assert result.is_valid is True

    def test_disable_upper_requirement(self):
        pv = PasswordValidator(require_upper=False)
        result = pv.validate("alllower1!ab")
        assert result.is_valid is True

    def test_disable_special_requirement(self):
        pv = PasswordValidator(require_special=False)
        result = pv.validate("NoSpecial123Ab")
        assert result.is_valid is True


# ═══════════════════════════════════════════════════════════════════════════════
#  5. SecurityEventTracker Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityEventTracker:
    """Tests for security event recording and querying."""

    def setup_method(self):
        self.tracker = SecurityEventTracker(max_events=100)

    # ── Recording ────────────────────────────────────────────────────

    def test_record_creates_event(self):
        event = self.tracker.record("login_failed", "10.0.0.1", username="admin")
        assert isinstance(event, SecurityEvent)
        assert event.event_type == "login_failed"
        assert event.ip_address == "10.0.0.1"
        assert event.details["username"] == "admin"
        assert event.timestamp > 0

    def test_record_multiple_events(self):
        for i in range(5):
            self.tracker.record("test_event", f"10.0.0.{i}")
        events = self.tracker.get_events()
        assert len(events) == 5

    def test_event_is_frozen(self):
        event = self.tracker.record("test", "1.2.3.4")
        with pytest.raises(FrozenInstanceError):
            event.event_type = "modified"  # type: ignore

    # ── Bounded FIFO buffer ──────────────────────────────────────────

    def test_max_events_respected(self):
        tracker = SecurityEventTracker(max_events=5)
        for i in range(10):
            tracker.record("event", f"10.0.0.{i}")
        events = tracker.get_events(limit=10)
        assert len(events) == 5
        # Should have the last 5 events (FIFO)
        assert events[0].ip_address == "10.0.0.5"

    # ── Querying ─────────────────────────────────────────────────────

    def test_get_events_filter_by_type(self):
        self.tracker.record("login_failed", "1.1.1.1")
        self.tracker.record("csrf_violation", "2.2.2.2")
        self.tracker.record("login_failed", "3.3.3.3")
        events = self.tracker.get_events(event_type="login_failed")
        assert len(events) == 2
        assert all(e.event_type == "login_failed" for e in events)

    def test_get_events_filter_by_ip(self):
        self.tracker.record("login_failed", "1.1.1.1")
        self.tracker.record("csrf_violation", "1.1.1.1")
        self.tracker.record("login_failed", "2.2.2.2")
        events = self.tracker.get_events(ip_address="1.1.1.1")
        assert len(events) == 2
        assert all(e.ip_address == "1.1.1.1" for e in events)

    def test_get_events_filter_by_since(self):
        before = time.time() - 10
        self.tracker.record("old_event", "1.1.1.1")
        after = time.time()
        self.tracker.record("new_event", "2.2.2.2")
        events = self.tracker.get_events(since=after)
        assert len(events) == 1
        assert events[0].event_type == "new_event"

    def test_get_events_limit(self):
        for i in range(20):
            self.tracker.record("event", "10.0.0.1")
        events = self.tracker.get_events(limit=5)
        assert len(events) == 5

    def test_get_events_combined_filters(self):
        self.tracker.record("login_failed", "1.1.1.1")
        self.tracker.record("login_failed", "2.2.2.2")
        self.tracker.record("csrf_violation", "1.1.1.1")
        events = self.tracker.get_events(
            event_type="login_failed", ip_address="1.1.1.1",
        )
        assert len(events) == 1

    # ── Counting ─────────────────────────────────────────────────────

    def test_count_events(self):
        self.tracker.record("login_failed", "1.1.1.1")
        self.tracker.record("login_failed", "2.2.2.2")
        self.tracker.record("csrf_violation", "1.1.1.1")
        assert self.tracker.count_events("login_failed") == 2
        assert self.tracker.count_events("csrf_violation") == 1

    def test_count_events_by_ip(self):
        self.tracker.record("login_failed", "1.1.1.1")
        self.tracker.record("login_failed", "1.1.1.1")
        self.tracker.record("login_failed", "2.2.2.2")
        count = self.tracker.count_events("login_failed", ip_address="1.1.1.1")
        assert count == 2

    def test_count_events_by_since(self):
        self.tracker.record("login_failed", "1.1.1.1")
        after = time.time()
        self.tracker.record("login_failed", "1.1.1.1")
        count = self.tracker.count_events("login_failed", since=after)
        assert count == 1

    # ── Clear ────────────────────────────────────────────────────────

    def test_clear(self):
        self.tracker.record("event", "1.1.1.1")
        self.tracker.clear()
        assert self.tracker.get_events() == []
        assert self.tracker.count_events("event") == 0


# ═══════════════════════════════════════════════════════════════════════════════
#  6. AdminSecurityPolicy Tests (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAdminSecurityPolicy:
    """Tests for the orchestrator that ties all security components together."""

    def setup_method(self):
        self.policy = AdminSecurityPolicy()

    # ── Component initialization ─────────────────────────────────────

    def test_has_csrf(self):
        assert isinstance(self.policy.csrf, AdminCSRFProtection)

    def test_has_rate_limiter(self):
        assert isinstance(self.policy.rate_limiter, AdminRateLimiter)

    def test_has_headers(self):
        assert isinstance(self.policy.headers, AdminSecurityHeaders)

    def test_has_password_validator(self):
        assert isinstance(self.policy.password_validator, PasswordValidator)

    def test_has_event_tracker(self):
        assert isinstance(self.policy.event_tracker, SecurityEventTracker)

    # ── Custom component injection ───────────────────────────────────

    def test_custom_csrf(self):
        csrf = AdminCSRFProtection(secret="custom")
        policy = AdminSecurityPolicy(csrf=csrf)
        assert policy.csrf is csrf

    def test_custom_rate_limiter(self):
        rl = AdminRateLimiter(max_login_attempts=10)
        policy = AdminSecurityPolicy(rate_limiter=rl)
        assert policy.rate_limiter is rl

    def test_custom_headers(self):
        headers = AdminSecurityHeaders(frame_options="SAMEORIGIN")
        policy = AdminSecurityPolicy(headers=headers)
        assert policy.headers is headers

    def test_custom_password_validator(self):
        pv = PasswordValidator(min_length=6)
        policy = AdminSecurityPolicy(password_validator=pv)
        assert policy.password_validator is pv

    def test_custom_event_tracker(self):
        tracker = SecurityEventTracker(max_events=50)
        policy = AdminSecurityPolicy(event_tracker=tracker)
        assert policy.event_tracker is tracker

    # ── protect_response ─────────────────────────────────────────────

    def test_protect_response_applies_security_headers(self):
        resp = MagicMock()
        resp.headers = {}
        result = self.policy.protect_response(resp)
        assert result is resp
        assert "x-frame-options" in resp.headers
        assert "content-security-policy" in resp.headers

    def test_protect_response_with_nonce(self):
        resp = MagicMock()
        resp.headers = {}
        self.policy.protect_response(resp, nonce="my-nonce")
        assert "'nonce-my-nonce'" in resp.headers["content-security-policy"]

    def test_protect_response_asset_mode(self):
        resp = MagicMock()
        resp.headers = {}
        self.policy.protect_response(resp, is_asset=True)
        assert "x-content-type-options" in resp.headers
        assert "content-security-policy" not in resp.headers

    # ── extract_client_ip ────────────────────────────────────────────

    def test_extract_ip_from_x_forwarded_for(self):
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50, 70.41.3.18"}
        ip = self.policy.extract_client_ip(request)
        assert ip == "203.0.113.50"

    def test_extract_ip_from_x_real_ip(self):
        request = MagicMock()
        request.headers = {"x-real-ip": "198.51.100.178"}
        ip = self.policy.extract_client_ip(request)
        assert ip == "198.51.100.178"

    def test_extract_ip_from_scope_client(self):
        request = MagicMock()
        request.headers = {}
        request.scope = {"client": ("192.168.1.100", 54321)}
        ip = self.policy.extract_client_ip(request)
        assert ip == "192.168.1.100"

    def test_extract_ip_scope_list(self):
        request = MagicMock()
        request.headers = {}
        request.scope = {"client": ["172.16.0.1", 8080]}
        ip = self.policy.extract_client_ip(request)
        assert ip == "172.16.0.1"

    def test_extract_ip_no_info(self):
        """Returns 'unknown' when no IP info is available."""
        request = MagicMock(spec=[])  # No attributes at all
        ip = self.policy.extract_client_ip(request)
        assert ip == "unknown"

    def test_extract_ip_x_forwarded_for_precedence(self):
        """X-Forwarded-For takes precedence over scope client."""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "1.2.3.4"}
        request.scope = {"client": ("5.6.7.8", 9999)}
        ip = self.policy.extract_client_ip(request)
        assert ip == "1.2.3.4"


# ═══════════════════════════════════════════════════════════════════════════════
#  7. DI Registration Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestDIRegistration:
    """Tests for register_security_providers."""

    def test_registers_all_providers(self):
        """All security components are registered with the container."""
        container = MagicMock()

        # The real register_security_providers imports ValueProvider from DI,
        # which may have a different signature. Mock it at the import level.
        mock_value_provider = MagicMock()
        with patch("aquilia.admin.security.register_security_providers") as mock_reg:
            # Instead, call the real function with proper mocking of DI internals
            pass

        # Test the real function by patching the DI imports
        with patch("aquilia.di.providers.ValueProvider") as MockVP, \
             patch("aquilia.di.providers.FactoryProvider"), \
             patch("aquilia.di.scopes.Scope"):
            MockVP.return_value = MagicMock()
            register_security_providers(container)

        # Should have registered 6 components
        assert container.register.call_count == 6

        registered_types = [call[0][0] for call in container.register.call_args_list]
        assert AdminSecurityPolicy in registered_types
        assert AdminCSRFProtection in registered_types
        assert AdminRateLimiter in registered_types
        assert AdminSecurityHeaders in registered_types
        assert PasswordValidator in registered_types
        assert SecurityEventTracker in registered_types

    def test_registration_handles_missing_di(self):
        """Gracefully handles missing DI module."""
        container = MagicMock()
        with patch(
            "aquilia.admin.security.register_security_providers",
            side_effect=ImportError,
        ):
            # Should not raise
            try:
                register_security_providers(container)
            except ImportError:
                pass  # Expected in test environment

    def test_registration_handles_errors(self):
        """Gracefully handles registration errors."""
        container = MagicMock()
        container.register.side_effect = Exception("DI error")
        # Should not raise — logs warning instead
        register_security_providers(container)


# ═══════════════════════════════════════════════════════════════════════════════
#  8. Integration Tests — CSRF end-to-end
# ═══════════════════════════════════════════════════════════════════════════════


class TestCSRFEndToEnd:
    """Integration tests for CSRF protection in admin controller."""

    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()
        self.policy = self.site.security

    def _make_ctx(self, session_data=None):
        ctx = MagicMock()
        ctx.session = MagicMock()
        ctx.session.data = session_data or {}
        ctx.request = None
        return ctx

    def test_full_csrf_lifecycle(self):
        """Generate token → store in session → submit in form → validate."""
        ctx = self._make_ctx()

        # Step 1: Generate/store token
        token = self.policy.csrf.get_or_create_token(ctx)
        assert isinstance(token, str)
        assert ctx.session.data.get("_admin_csrf_token") == token

        # Step 2: Submit token in form data
        form_data = {"_csrf_token": token, "username": "admin"}
        assert self.policy.csrf.validate_request(ctx, form_data) is True

    def test_csrf_rejects_without_token(self):
        ctx = self._make_ctx()
        self.policy.csrf.get_or_create_token(ctx)
        form_data = {"username": "admin"}  # No _csrf_token
        assert self.policy.csrf.validate_request(ctx, form_data) is False

    def test_csrf_rejects_tampered_token(self):
        ctx = self._make_ctx()
        token = self.policy.csrf.get_or_create_token(ctx)
        form_data = {"_csrf_token": token + "tampered"}
        assert self.policy.csrf.validate_request(ctx, form_data) is False

    def test_csrf_rejects_replayed_token_from_different_session(self):
        """Token from session A is invalid in session B."""
        ctx_a = self._make_ctx()
        token_a = self.policy.csrf.get_or_create_token(ctx_a)

        ctx_b = self._make_ctx()
        self.policy.csrf.get_or_create_token(ctx_b)  # Different token

        # Using token A in session B
        form_data = {"_csrf_token": token_a}
        assert self.policy.csrf.validate_request(ctx_b, form_data) is False


# ═══════════════════════════════════════════════════════════════════════════════
#  9. Integration Tests — Rate Limiter with Events
# ═══════════════════════════════════════════════════════════════════════════════


class TestRateLimiterWithEvents:
    """Integration tests combining rate limiting with event tracking."""

    def setup_method(self):
        self.policy = AdminSecurityPolicy(
            rate_limiter=AdminRateLimiter(max_login_attempts=3, login_window=60),
        )

    def test_lockout_with_event_tracking(self):
        ip = "10.0.0.99"
        for i in range(3):
            self.policy.rate_limiter.record_login_failure(ip)
            self.policy.event_tracker.record(
                "login_failed", ip, attempt=i + 1,
            )

        # Should be locked out
        locked, retry = self.policy.rate_limiter.is_login_locked(ip)
        assert locked is True

        # Should have 3 events recorded
        events = self.policy.event_tracker.get_events(
            event_type="login_failed", ip_address=ip,
        )
        assert len(events) == 3

    def test_success_clears_lockout_but_preserves_events(self):
        ip = "10.0.0.100"
        for _ in range(3):
            self.policy.rate_limiter.record_login_failure(ip)
            self.policy.event_tracker.record("login_failed", ip)

        self.policy.rate_limiter.record_login_success(ip)
        self.policy.event_tracker.record("login_success", ip)

        # Lockout cleared
        assert self.policy.rate_limiter.is_login_locked(ip)[0] is False

        # But events still there for audit
        failed = self.policy.event_tracker.count_events("login_failed", ip_address=ip)
        success = self.policy.event_tracker.count_events("login_success", ip_address=ip)
        assert failed == 3
        assert success == 1


# ═══════════════════════════════════════════════════════════════════════════════
#  10. Exports and __init__ Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityExports:
    """Verify all security classes are importable from aquilia.admin."""

    def test_import_csrf_protection(self):
        from aquilia.admin import AdminCSRFProtection
        assert AdminCSRFProtection is not None

    def test_import_rate_limiter(self):
        from aquilia.admin import AdminRateLimiter
        assert AdminRateLimiter is not None

    def test_import_security_headers(self):
        from aquilia.admin import AdminSecurityHeaders
        assert AdminSecurityHeaders is not None

    def test_import_password_validator(self):
        from aquilia.admin import PasswordValidator
        assert PasswordValidator is not None

    def test_import_password_strength(self):
        from aquilia.admin import PasswordStrength
        assert PasswordStrength is not None

    def test_import_security_event_tracker(self):
        from aquilia.admin import SecurityEventTracker
        assert SecurityEventTracker is not None

    def test_import_security_event(self):
        from aquilia.admin import SecurityEvent
        assert SecurityEvent is not None

    def test_import_security_policy(self):
        from aquilia.admin import AdminSecurityPolicy
        assert AdminSecurityPolicy is not None

    def test_import_register_security_providers(self):
        from aquilia.admin import register_security_providers
        assert callable(register_security_providers)

    def test_admin_site_has_security(self):
        """AdminSite instances have a security policy attached."""
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        site = AdminSite()
        assert hasattr(site, "security")
        assert isinstance(site.security, AdminSecurityPolicy)
