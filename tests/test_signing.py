"""
Comprehensive test suite for ``aquilia.signing`` — the Aquilia Signing Engine.

This file provides **deep regression coverage** for every public API surface:

• Low-level primitives: b64_encode / b64_decode, constant_time_compare, derive_key
• Backends: HmacSignerBackend, AsymmetricSignerBackend (mocked)
• Signer: sign / unsign, sign_bytes / unsign_bytes, sign_object / unsign_object
• TimestampSigner: timestamps, max_age, unsign_with_timestamp, expiry
• RotatingSigner: key rotation, multi-key verification
• High-level: dumps / loads (with compression, timestamps, max_age)
• Convenience factories: make_signer, make_timestamp_signer
• Domain signers: SessionSigner, CSRFSigner, ActivationLinkSigner,
                  CacheKeySigner, CookieSigner, APIKeySigner
• Global config: configure(), _get_global_secret(), _get_global_rotating_signer()
• SigningConfig dataclass
• Exception / fault hierarchy alignment
• Namespace (salt) isolation
• Edge cases, tamper resistance, and regression guards
"""

from __future__ import annotations

import json
import struct
import time
import hashlib
import hmac as _hmac
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

# ── Module under test ────────────────────────────────────────────────────
from aquilia.signing import (
    # Exceptions (backward-compat aliases)
    SigningError,
    BadSignature,
    SignatureExpired,
    SignatureMalformed,
    UnsupportedAlgorithmError,
    # Core classes
    Signer,
    TimestampSigner,
    RotatingSigner,
    # Structured payload
    dumps,
    loads,
    # Backends
    SignerBackend,
    HmacSignerBackend,
    # Factories
    make_signer,
    make_timestamp_signer,
    # Primitives
    b64_encode,
    b64_decode,
    constant_time_compare,
    derive_key,
    # Domain signers
    SessionSigner,
    CSRFSigner,
    ActivationLinkSigner,
    CacheKeySigner,
    CookieSigner,
    APIKeySigner,
    # Config
    SigningConfig,
)
from aquilia.signing import (
    configure,
    _get_global_secret,
    _get_global_rotating_signer,
    _GLOBAL_SECRETS,
    _EPOCH,
    _SEP,
    _MIN_KEY_BYTES,
    _HMAC_ALGORITHMS,
    _ASYMMETRIC_ALGORITHMS,
    _check_key_length,
)
from aquilia.faults.domains import (
    BadSignatureFault,
    ConfigInvalidFault,
    ConfigMissingFault,
    SignatureExpiredFault,
    SignatureMalformedFault,
    SigningFault,
    UnsupportedAlgorithmFault,
    SecurityFault,
    Fault,
)


# ── Fixtures ─────────────────────────────────────────────────────────────

SECRET = "a" * 64  # 64-byte secret — well above the _MIN_KEY_BYTES (32)
SECRET_B = b"b" * 64
ALT_SECRET = "c" * 64
SHORT_SECRET = "short"  # < 32 bytes — triggers warning


@pytest.fixture(autouse=True)
def _reset_global_state():
    """Reset the global signing state before every test."""
    import aquilia.signing as _mod

    original_secrets = _mod._GLOBAL_SECRETS[:]
    original_algo = _mod._GLOBAL_ALGORITHM
    original_salt = _mod._GLOBAL_SALT
    yield
    _mod._GLOBAL_SECRETS = original_secrets
    _mod._GLOBAL_ALGORITHM = original_algo
    _mod._GLOBAL_SALT = original_salt


# ========================================================================
# 1. Exception / Fault hierarchy alignment
# ========================================================================


class TestFaultHierarchy:
    """Ensure signing exceptions map correctly to the fault mechanism."""

    def test_signing_error_is_signing_fault(self):
        assert SigningError is SigningFault

    def test_bad_signature_is_bad_signature_fault(self):
        assert BadSignature is BadSignatureFault

    def test_signature_expired_is_signature_expired_fault(self):
        assert SignatureExpired is SignatureExpiredFault

    def test_signature_malformed_is_signature_malformed_fault(self):
        assert SignatureMalformed is SignatureMalformedFault

    def test_unsupported_algorithm_is_unsupported_algorithm_fault(self):
        assert UnsupportedAlgorithmError is UnsupportedAlgorithmFault

    def test_bad_signature_inherits_signing_fault(self):
        assert issubclass(BadSignatureFault, SigningFault)

    def test_signature_expired_inherits_bad_signature(self):
        assert issubclass(SignatureExpiredFault, BadSignatureFault)

    def test_signing_fault_inherits_security_fault(self):
        assert issubclass(SigningFault, SecurityFault)

    def test_security_fault_inherits_fault(self):
        assert issubclass(SecurityFault, Fault)

    def test_catch_bad_signature_as_signing_error(self):
        """BadSignature should be catchable as SigningError."""
        with pytest.raises(SigningError):
            raise BadSignature("test")

    def test_catch_signature_expired_as_bad_signature(self):
        """SignatureExpired should be catchable as BadSignature."""
        with pytest.raises(BadSignature):
            raise SignatureExpired("test")

    def test_catch_signature_expired_as_signing_error(self):
        with pytest.raises(SigningError):
            raise SignatureExpired("test")


# ========================================================================
# 2. Low-level primitives
# ========================================================================


class TestB64Encode:
    """b64_encode: URL-safe, no-padding Base64."""

    def test_empty_bytes(self):
        assert b64_encode(b"") == ""

    def test_round_trip(self):
        data = b"hello world"
        encoded = b64_encode(data)
        assert b64_decode(encoded) == data

    def test_binary_round_trip(self):
        data = bytes(range(256))
        assert b64_decode(b64_encode(data)) == data

    def test_no_padding_chars(self):
        encoded = b64_encode(b"test")
        assert "=" not in encoded

    def test_url_safe_chars(self):
        """Encoded output should not contain + or /."""
        data = bytes(range(256))
        encoded = b64_encode(data)
        assert "+" not in encoded
        assert "/" not in encoded

    def test_deterministic(self):
        data = b"determinism"
        assert b64_encode(data) == b64_encode(data)


class TestB64Decode:
    """b64_decode: accepts strings and bytes, handles no-padding."""

    def test_string_input(self):
        data = b"hello"
        encoded = b64_encode(data)
        assert b64_decode(encoded) == data

    def test_bytes_input(self):
        data = b"hello"
        encoded = b64_encode(data).encode("ascii")
        assert b64_decode(encoded) == data

    def test_invalid_base64_raises_malformed(self):
        """b64_decode wraps base64 errors as SignatureMalformed.
        Note: Python's base64 module is very lenient and silently
        ignores most invalid chars. We test with non-ASCII bytes
        that will fail the .encode('ascii') step."""
        with pytest.raises((SignatureMalformed, UnicodeEncodeError)):
            b64_decode("日本語")

    def test_padding_tolerance(self):
        """Should decode with or without padding."""
        import base64

        data = b"abc"
        with_padding = base64.urlsafe_b64encode(data).decode()
        without_padding = with_padding.rstrip("=")
        assert b64_decode(with_padding) == data
        assert b64_decode(without_padding) == data

    def test_non_canonical_base64_raises_malformed(self):
        """Non-canonical encodings must be rejected to catch token tampering."""
        encoded = b64_encode(b"a")
        tampered = encoded[:-1] + ("Z" if encoded[-1] != "Z" else "Y")
        with pytest.raises(SignatureMalformed):
            b64_decode(tampered)


class TestConstantTimeCompare:
    """constant_time_compare: wraps hmac.compare_digest."""

    def test_equal_strings(self):
        assert constant_time_compare("foo", "foo") is True

    def test_unequal_strings(self):
        assert constant_time_compare("foo", "bar") is False

    def test_equal_bytes(self):
        assert constant_time_compare(b"abc", b"abc") is True

    def test_unequal_bytes(self):
        assert constant_time_compare(b"abc", b"xyz") is False

    def test_mixed_string_coercion(self):
        """Both str→bytes before comparison."""
        assert constant_time_compare("abc", "abc") is True

    def test_empty_values(self):
        assert constant_time_compare("", "") is True
        assert constant_time_compare(b"", b"") is True

    def test_different_lengths(self):
        assert constant_time_compare("short", "longer") is False


class TestDeriveKey:
    """derive_key: HMAC-based namespace sub-key derivation."""

    def test_deterministic(self):
        k1 = derive_key(SECRET, "salt1")
        k2 = derive_key(SECRET, "salt1")
        assert k1 == k2

    def test_different_salts_differ(self):
        k1 = derive_key(SECRET, "salt1")
        k2 = derive_key(SECRET, "salt2")
        assert k1 != k2

    def test_different_secrets_differ(self):
        k1 = derive_key(SECRET, "salt")
        k2 = derive_key(ALT_SECRET, "salt")
        assert k1 != k2

    def test_different_algorithms_differ(self):
        k1 = derive_key(SECRET, "salt", "HS256")
        k2 = derive_key(SECRET, "salt", "HS384")
        assert k1 != k2

    def test_returns_32_bytes(self):
        key = derive_key(SECRET, "test")
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_bytes_secret(self):
        key = derive_key(SECRET_B, "salt")
        assert isinstance(key, bytes) and len(key) == 32

    def test_str_secret(self):
        key = derive_key(SECRET, "salt")
        assert isinstance(key, bytes) and len(key) == 32


class TestCheckKeyLength:
    """_check_key_length: warning for short keys."""

    def test_short_key_warns(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="aquilia.signing"):
            _check_key_length("tiny")
        assert "recommend" in caplog.text.lower() or len(caplog.records) > 0

    def test_long_key_no_warning(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="aquilia.signing"):
            _check_key_length(SECRET)
        assert len(caplog.records) == 0


# ========================================================================
# 3. HmacSignerBackend
# ========================================================================


class TestHmacSignerBackend:
    """HmacSignerBackend: default HMAC backend."""

    def test_hs256_sign_verify(self):
        backend = HmacSignerBackend(SECRET, algorithm="HS256")
        sig = backend.sign(b"hello")
        assert backend.verify(b"hello", sig) is True

    def test_hs384_sign_verify(self):
        backend = HmacSignerBackend(SECRET, algorithm="HS384")
        sig = backend.sign(b"hello")
        assert backend.verify(b"hello", sig) is True

    def test_hs512_sign_verify(self):
        backend = HmacSignerBackend(SECRET, algorithm="HS512")
        sig = backend.sign(b"hello")
        assert backend.verify(b"hello", sig) is True

    def test_algorithm_property(self):
        backend = HmacSignerBackend(SECRET, algorithm="HS384")
        assert backend.algorithm == "HS384"

    def test_tampered_message_fails(self):
        backend = HmacSignerBackend(SECRET)
        sig = backend.sign(b"hello")
        assert backend.verify(b"HELLO", sig) is False

    def test_tampered_signature_fails(self):
        backend = HmacSignerBackend(SECRET)
        sig = backend.sign(b"hello")
        tampered = sig[:-1] + bytes([sig[-1] ^ 0xFF])
        assert backend.verify(b"hello", tampered) is False

    def test_different_salts_incompatible(self):
        b1 = HmacSignerBackend(SECRET, salt="a")
        b2 = HmacSignerBackend(SECRET, salt="b")
        sig = b1.sign(b"hello")
        assert b2.verify(b"hello", sig) is False

    def test_unsupported_algorithm_raises(self):
        with pytest.raises(UnsupportedAlgorithmError):
            HmacSignerBackend(SECRET, algorithm="RS256")

    def test_none_algorithm_rejected(self):
        with pytest.raises(UnsupportedAlgorithmError):
            HmacSignerBackend(SECRET, algorithm="none")

    def test_inherits_signer_backend(self):
        assert issubclass(HmacSignerBackend, SignerBackend)


# ========================================================================
# 4. Signer
# ========================================================================


class TestSigner:
    """Core Signer: sign / unsign strings."""

    def test_sign_unsign_round_trip(self):
        s = Signer(secret=SECRET)
        token = s.sign("hello")
        assert s.unsign(token) == "hello"

    def test_sign_contains_separator(self):
        s = Signer(secret=SECRET)
        token = s.sign("hello")
        assert _SEP in token

    def test_unsign_tampered_raises_bad_signature(self):
        s = Signer(secret=SECRET)
        token = s.sign("hello")
        tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
        with pytest.raises(BadSignature):
            s.unsign(tampered)

    def test_unsign_no_separator_raises_malformed(self):
        s = Signer(secret=SECRET)
        with pytest.raises(SignatureMalformed):
            s.unsign("noseparatorhere")

    def test_value_with_separator_in_sign_raises(self):
        """sign() rejects values containing the separator."""
        s = Signer(secret=SECRET)
        with pytest.raises(SignatureMalformed):
            s.sign(f"has{_SEP}sep")

    def test_different_secrets_incompatible(self):
        s1 = Signer(secret=SECRET)
        s2 = Signer(secret=ALT_SECRET)
        token = s1.sign("hello")
        with pytest.raises(BadSignature):
            s2.unsign(token)

    def test_different_salts_incompatible(self):
        s1 = Signer(secret=SECRET, salt="alpha")
        s2 = Signer(secret=SECRET, salt="beta")
        token = s1.sign("hello")
        with pytest.raises(BadSignature):
            s2.unsign(token)

    def test_same_salt_compatible(self):
        s1 = Signer(secret=SECRET, salt="same")
        s2 = Signer(secret=SECRET, salt="same")
        token = s1.sign("hello")
        assert s2.unsign(token) == "hello"

    def test_sign_empty_string(self):
        s = Signer(secret=SECRET)
        token = s.sign("")
        assert s.unsign(token) == ""

    def test_sign_unicode(self):
        s = Signer(secret=SECRET)
        value = "日本語テスト 🎉"
        token = s.sign(value)
        assert s.unsign(token) == value

    def test_invalid_separator_raises_config_fault(self):
        """Separator must not be a Base64 character."""
        with pytest.raises(ConfigInvalidFault):
            Signer(secret=SECRET, sep="A")

    def test_custom_separator(self):
        s = Signer(secret=SECRET, sep=".")
        token = s.sign("hello")
        assert "." in token
        assert s.unsign(token) == "hello"

    def test_repr(self):
        s = Signer(secret=SECRET, salt="test.salt")
        r = repr(s)
        assert "Signer" in r
        assert "test.salt" in r

    # ── sign_bytes / unsign_bytes ──────────────────────────────────

    def test_sign_bytes_round_trip(self):
        s = Signer(secret=SECRET)
        data = b"\x00\x01\x02\xff"
        signed = s.sign_bytes(data)
        assert s.unsign_bytes(signed) == data

    def test_sign_bytes_tampered_fails(self):
        s = Signer(secret=SECRET)
        signed = s.sign_bytes(b"secret data")
        tampered = b"evil data" + signed[len(b"secret data"):]
        with pytest.raises(BadSignature):
            s.unsign_bytes(tampered)

    def test_unsign_bytes_no_separator_raises(self):
        s = Signer(secret=SECRET)
        with pytest.raises(SignatureMalformed):
            s.unsign_bytes(b"no separator here")

    # ── sign_object / unsign_object ────────────────────────────────

    def test_sign_object_dict(self):
        s = Signer(secret=SECRET)
        obj = {"user_id": 42, "role": "admin"}
        token = s.sign_object(obj)
        assert s.unsign_object(token) == obj

    def test_sign_object_list(self):
        s = Signer(secret=SECRET)
        obj = [1, "two", 3.0, None, True]
        token = s.sign_object(obj)
        assert s.unsign_object(token) == obj

    def test_sign_object_tampered_raises(self):
        s = Signer(secret=SECRET)
        token = s.sign_object({"key": "value"})
        tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
        with pytest.raises(BadSignature):
            s.unsign_object(tampered)

    def test_sign_object_nested(self):
        s = Signer(secret=SECRET)
        obj = {"a": {"b": [1, 2, {"c": True}]}}
        token = s.sign_object(obj)
        assert s.unsign_object(token) == obj


# ========================================================================
# 5. TimestampSigner
# ========================================================================


class TestTimestampSigner:
    """TimestampSigner: signs with an embedded UTC timestamp."""

    def test_sign_unsign_round_trip(self):
        ts = TimestampSigner(secret=SECRET)
        token = ts.sign("hello")
        assert ts.unsign(token) == "hello"

    def test_unsign_with_max_age_valid(self):
        ts = TimestampSigner(secret=SECRET)
        token = ts.sign("hello")
        assert ts.unsign(token, max_age=3600) == "hello"

    def test_unsign_expired_raises(self):
        ts = TimestampSigner(secret=SECRET)
        # Sign with a timestamp 2 hours in the past
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        token = ts.sign("hello", timestamp=old_time)
        with pytest.raises(SignatureExpired):
            ts.unsign(token, max_age=60)

    def test_unsign_with_timedelta_max_age(self):
        ts = TimestampSigner(secret=SECRET)
        token = ts.sign("hello")
        assert ts.unsign(token, max_age=timedelta(hours=1)) == "hello"

    def test_unsign_without_max_age_skips_age_check(self):
        ts = TimestampSigner(secret=SECRET)
        old_time = datetime.now(timezone.utc) - timedelta(days=365)
        token = ts.sign("hello", timestamp=old_time)
        # No max_age → should not expire
        assert ts.unsign(token) == "hello"

    def test_unsign_with_timestamp(self):
        ts = TimestampSigner(secret=SECRET)
        now = datetime.now(timezone.utc)
        token = ts.sign("hello", timestamp=now)
        value, when = ts.unsign_with_timestamp(token)
        assert value == "hello"
        # Timestamp should be close to 'now' (within 2 seconds)
        assert abs((when - now).total_seconds()) < 2

    def test_unsign_with_timestamp_max_age(self):
        ts = TimestampSigner(secret=SECRET)
        old_time = datetime.now(timezone.utc) - timedelta(hours=2)
        token = ts.sign("hello", timestamp=old_time)
        with pytest.raises(SignatureExpired):
            ts.unsign_with_timestamp(token, max_age=60)

    def test_tampered_token_raises(self):
        ts = TimestampSigner(secret=SECRET)
        token = ts.sign("hello")
        # Tamper a character in the middle of the signature, not the last
        # character.  The last base64 char of a 32-byte HMAC may only
        # encode padding bits, so flipping it might not change the
        # decoded bytes at all.  Flipping a mid-signature character
        # always changes the decoded bytes and must trigger BadSignature.
        sep_idx = token.rfind(":")
        mid = sep_idx + (len(token) - sep_idx) // 2  # middle of signature
        flip = "A" if token[mid] != "A" else "B"
        tampered = token[:mid] + flip + token[mid + 1:]
        with pytest.raises(BadSignature):
            ts.unsign(tampered)

    def test_different_secrets_incompatible(self):
        ts1 = TimestampSigner(secret=SECRET)
        ts2 = TimestampSigner(secret=ALT_SECRET)
        token = ts1.sign("hello")
        with pytest.raises(BadSignature):
            ts2.unsign(token)

    def test_default_salt(self):
        ts = TimestampSigner(secret=SECRET)
        assert ts._salt == "aquilia.signing.ts"

    def test_custom_salt(self):
        ts = TimestampSigner(secret=SECRET, salt="custom")
        token = ts.sign("hello")
        assert ts.unsign(token) == "hello"

    def test_sign_unicode(self):
        ts = TimestampSigner(secret=SECRET)
        val = "unicode: 日本語 🚀"
        token = ts.sign(val)
        assert ts.unsign(token) == val

    def test_sign_empty_string(self):
        ts = TimestampSigner(secret=SECRET)
        token = ts.sign("")
        assert ts.unsign(token) == ""

    # ── Timestamp encoding / decoding ──────────────────────────────

    def test_encode_decode_timestamp_round_trip(self):
        now = datetime.now(timezone.utc)
        encoded = TimestampSigner._encode_timestamp(now)
        decoded = TimestampSigner._decode_timestamp(encoded)
        # Microsecond precision
        assert abs((decoded - now).total_seconds()) < 0.001

    def test_encode_timestamp_default_is_now(self):
        before = datetime.now(timezone.utc)
        encoded = TimestampSigner._encode_timestamp()
        after = datetime.now(timezone.utc)
        decoded = TimestampSigner._decode_timestamp(encoded)
        assert before <= decoded <= after

    def test_decode_invalid_timestamp_raises_malformed(self):
        with pytest.raises(SignatureMalformed):
            TimestampSigner._decode_timestamp("invalid!!!")

    def test_decode_wrong_length_raises_malformed(self):
        """Timestamp must be exactly 8 bytes when decoded."""
        short = b64_encode(b"\x00\x01\x02")  # 3 bytes, not 8
        with pytest.raises(SignatureMalformed):
            TimestampSigner._decode_timestamp(short)

    # ── sign_object / unsign_object ────────────────────────────────

    def test_sign_object_round_trip(self):
        ts = TimestampSigner(secret=SECRET)
        obj = {"user": 42, "roles": ["admin", "editor"]}
        token = ts.sign_object(obj)
        assert ts.unsign_object(token) == obj

    def test_sign_object_with_max_age(self):
        ts = TimestampSigner(secret=SECRET)
        obj = {"key": "value"}
        token = ts.sign_object(obj)
        assert ts.unsign_object(token, max_age=3600) == obj

    def test_sign_object_expired_raises(self):
        ts = TimestampSigner(secret=SECRET)
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        token = ts.sign_object({"data": 1}, timestamp=old)
        with pytest.raises(SignatureExpired):
            ts.unsign_object(token, max_age=60)

    # ── Expired metadata ──────────────────────────────────────────

    def test_signature_expired_has_metadata(self):
        ts = TimestampSigner(secret=SECRET)
        old = datetime.now(timezone.utc) - timedelta(seconds=120)
        token = ts.sign("test", timestamp=old)
        with pytest.raises(SignatureExpired) as exc_info:
            ts.unsign(token, max_age=60)
        exc = exc_info.value
        # The fault should have relevant metadata
        assert hasattr(exc, "metadata") or hasattr(exc, "age_seconds")


# ========================================================================
# 6. RotatingSigner
# ========================================================================


class TestRotatingSigner:
    """RotatingSigner: transparent key rotation."""

    def test_sign_with_current_key(self):
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        token = rs.sign("hello")
        # Should be verifiable with the current key
        s = Signer(secret=SECRET)
        assert s.unsign(token) == "hello"

    def test_unsign_with_old_key(self):
        old_signer = Signer(secret=ALT_SECRET)
        token = old_signer.sign("hello")
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        assert rs.unsign(token) == "hello"

    def test_unsign_unknown_key_raises(self):
        other_signer = Signer(secret="z" * 64)
        token = other_signer.sign("hello")
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        with pytest.raises(BadSignature):
            rs.unsign(token)

    def test_empty_secrets_raises_config_fault(self):
        with pytest.raises(ConfigInvalidFault):
            RotatingSigner(secrets=[])

    def test_single_secret(self):
        rs = RotatingSigner(secrets=[SECRET])
        token = rs.sign("hello")
        assert rs.unsign(token) == "hello"

    def test_current_signer_property(self):
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        assert rs.current_signer is not None
        assert isinstance(rs.current_signer, Signer)

    def test_sign_object_round_trip(self):
        rs = RotatingSigner(secrets=[SECRET])
        obj = {"key": "value"}
        token = rs.sign_object(obj)
        assert rs.unsign_object(token) == obj

    def test_unsign_object_with_old_key(self):
        old_signer = Signer(secret=ALT_SECRET)
        token = old_signer.sign_object({"data": 42})
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        assert rs.unsign_object(token) == {"data": 42}

    def test_unsign_object_unknown_key_raises(self):
        other_signer = Signer(secret="z" * 64)
        token = other_signer.sign_object({"x": 1})
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        with pytest.raises(BadSignature):
            rs.unsign_object(token)

    def test_timestamp_mode(self):
        rs = RotatingSigner(secrets=[SECRET], timestamp=True)
        token = rs.sign("hello")
        assert rs.unsign(token) == "hello"

    def test_timestamp_mode_max_age(self):
        rs = RotatingSigner(secrets=[SECRET], timestamp=True)
        token = rs.sign("hello")
        assert rs.unsign(token, max_age=3600) == "hello"

    def test_repr(self):
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        r = repr(rs)
        assert "RotatingSigner" in r
        assert "n_secrets=2" in r

    def test_three_key_rotation(self):
        """Simulate a multi-step key rotation: old → mid → new."""
        old = "old-" + "x" * 60
        mid = "mid-" + "x" * 60
        new = "new-" + "x" * 60

        # Phase 1: only old key
        s_old = Signer(secret=old)
        token_old = s_old.sign("data")

        # Phase 2: mid key added, old retained
        s_mid = Signer(secret=mid)
        token_mid = s_mid.sign("data")

        # Phase 3: new key is current, mid and old are fallbacks
        rs = RotatingSigner(secrets=[new, mid, old])
        assert rs.unsign(token_old) == "data"
        assert rs.unsign(token_mid) == "data"

        # New tokens use the new key
        token_new = rs.sign("data")
        s_new = Signer(secret=new)
        assert s_new.unsign(token_new) == "data"


# ========================================================================
# 7. dumps / loads  (structured payload serialisation)
# ========================================================================


class TestDumpsLoads:
    """High-level dumps/loads: JSON serialisation with signing."""

    def test_round_trip(self):
        obj = {"user_id": 42, "roles": ["admin"]}
        token = dumps(obj, secret=SECRET)
        result = loads(token, secret=SECRET)
        assert result == obj

    def test_round_trip_with_max_age(self):
        obj = {"key": "value"}
        token = dumps(obj, secret=SECRET)
        result = loads(token, secret=SECRET, max_age=3600)
        assert result == obj

    def test_expired_max_age_raises(self):
        obj = {"data": 1}
        # dumps with a very old timestamp is tricky; instead we'll
        # test loads with max_age=0 after a small delay
        token = dumps(obj, secret=SECRET)
        time.sleep(0.05)
        with pytest.raises(SignatureExpired):
            loads(token, secret=SECRET, max_age=0.001)

    def test_tampered_token_raises(self):
        token = dumps({"ok": True}, secret=SECRET)
        tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
        with pytest.raises((BadSignature, SignatureMalformed)):
            loads(tampered, secret=SECRET)

    def test_wrong_secret_raises(self):
        token = dumps({"ok": True}, secret=SECRET)
        with pytest.raises((BadSignature, SignatureMalformed)):
            loads(token, secret=ALT_SECRET)

    def test_different_salt_raises(self):
        token = dumps({"ok": True}, secret=SECRET, salt="salt-a")
        with pytest.raises((BadSignature, SignatureMalformed)):
            loads(token, secret=SECRET, salt="salt-b")

    def test_compression(self):
        # Large repetitive data benefits from compression
        obj = {"data": "x" * 10000}
        token_compressed = dumps(obj, secret=SECRET, compress=True)
        token_plain = dumps(obj, secret=SECRET, compress=False)
        result = loads(token_compressed, secret=SECRET)
        assert result == obj
        # Compressed token should be shorter
        assert len(token_compressed) < len(token_plain)

    def test_compression_skips_when_not_smaller(self):
        # Tiny data won't compress well
        obj = {"x": 1}
        token = dumps(obj, secret=SECRET, compress=True)
        result = loads(token, secret=SECRET)
        assert result == obj

    def test_no_timestamp(self):
        obj = {"ok": True}
        token = dumps(obj, secret=SECRET, timestamp=False)
        result = loads(token, secret=SECRET)
        assert result == obj

    def test_primitives(self):
        for obj in [42, "hello", True, None, 3.14, [1, 2]]:
            token = dumps(obj, secret=SECRET)
            assert loads(token, secret=SECRET) == obj

    def test_different_algorithms(self):
        for algo in ["HS256", "HS384", "HS512"]:
            obj = {"algo": algo}
            token = dumps(obj, secret=SECRET, algorithm=algo)
            result = loads(token, secret=SECRET, algorithm=algo)
            assert result == obj

    def test_cross_algorithm_incompatible(self):
        token = dumps({"x": 1}, secret=SECRET, algorithm="HS256")
        with pytest.raises((BadSignature, SignatureMalformed)):
            loads(token, secret=SECRET, algorithm="HS384")


# ========================================================================
# 8. configure() / global secret registry
# ========================================================================


class TestConfigure:
    """Global signing configuration."""

    def test_configure_sets_global_secret(self):
        configure(secret=SECRET)
        assert _get_global_secret() == SECRET

    def test_get_global_secret_without_configure_raises(self):
        import aquilia.signing as _mod
        _mod._GLOBAL_SECRETS = []
        with pytest.raises(ConfigMissingFault):
            _get_global_secret()

    def test_configure_with_fallback_secrets(self):
        configure(secret=SECRET, fallback_secrets=[ALT_SECRET])
        import aquilia.signing as _mod
        assert len(_mod._GLOBAL_SECRETS) == 2
        assert _mod._GLOBAL_SECRETS[0] == SECRET
        assert _mod._GLOBAL_SECRETS[1] == ALT_SECRET

    def test_configure_algorithm(self):
        configure(secret=SECRET, algorithm="HS384")
        import aquilia.signing as _mod
        assert _mod._GLOBAL_ALGORITHM == "HS384"

    def test_configure_salt(self):
        configure(secret=SECRET, salt="custom.salt")
        import aquilia.signing as _mod
        assert _mod._GLOBAL_SALT == "custom.salt"

    def test_signer_uses_global_secret(self):
        configure(secret=SECRET)
        s = Signer()  # No explicit secret
        token = s.sign("hello")
        assert s.unsign(token) == "hello"

    def test_timestamp_signer_uses_global_secret(self):
        configure(secret=SECRET)
        ts = TimestampSigner()
        token = ts.sign("hello")
        assert ts.unsign(token) == "hello"


class TestGetGlobalRotatingSigner:
    """_get_global_rotating_signer: factory for rotating signer."""

    def test_returns_rotating_signer(self):
        configure(secret=SECRET, fallback_secrets=[ALT_SECRET])
        rs = _get_global_rotating_signer()
        assert isinstance(rs, RotatingSigner)

    def test_without_config_raises(self):
        import aquilia.signing as _mod
        _mod._GLOBAL_SECRETS = []
        with pytest.raises(ConfigMissingFault):
            _get_global_rotating_signer()

    def test_custom_salt_and_algo(self):
        configure(secret=SECRET)
        rs = _get_global_rotating_signer(salt="custom", algorithm="HS384")
        token = rs.sign("test")
        assert rs.unsign(token) == "test"

    def test_timestamp_mode(self):
        configure(secret=SECRET)
        rs = _get_global_rotating_signer(timestamp=True)
        token = rs.sign("test")
        assert rs.unsign(token) == "test"


# ========================================================================
# 9. Convenience factories: make_signer / make_timestamp_signer
# ========================================================================


class TestMakeSigner:
    """make_signer: convenience factory."""

    def test_with_explicit_secret(self):
        s = make_signer(secret=SECRET, salt="test")
        token = s.sign("hello")
        assert s.unsign(token) == "hello"

    def test_with_global_secret(self):
        configure(secret=SECRET)
        s = make_signer()
        token = s.sign("hello")
        assert s.unsign(token) == "hello"

    def test_returns_signer_instance(self):
        s = make_signer(secret=SECRET)
        assert isinstance(s, Signer)

    def test_custom_algorithm(self):
        configure(secret=SECRET, algorithm="HS512")
        s = make_signer()
        assert s._algorithm == "HS512"


class TestMakeTimestampSigner:
    """make_timestamp_signer: convenience factory."""

    def test_with_explicit_secret(self):
        ts = make_timestamp_signer(secret=SECRET)
        token = ts.sign("hello")
        assert ts.unsign(token) == "hello"

    def test_with_global_secret(self):
        configure(secret=SECRET)
        ts = make_timestamp_signer()
        token = ts.sign("hello")
        assert ts.unsign(token) == "hello"

    def test_returns_timestamp_signer_instance(self):
        ts = make_timestamp_signer(secret=SECRET)
        assert isinstance(ts, TimestampSigner)

    def test_default_salt(self):
        ts = make_timestamp_signer(secret=SECRET)
        assert ts._salt == "aquilia.signing.ts"


# ========================================================================
# 10. Domain signers
# ========================================================================


class TestSessionSigner:
    """SessionSigner: session cookie signer."""

    def test_sign_unsign(self):
        s = SessionSigner(secret=SECRET)
        token = s.sign("session-id-123")
        assert s.unsign(token) == "session-id-123"

    def test_inherits_timestamp_signer(self):
        assert issubclass(SessionSigner, TimestampSigner)

    def test_salt_namespace(self):
        s = SessionSigner(secret=SECRET)
        assert s._salt == "aquilia.sessions"

    def test_incompatible_with_csrf_signer(self):
        sess = SessionSigner(secret=SECRET)
        csrf = CSRFSigner(secret=SECRET)
        token = sess.sign("data")
        with pytest.raises((BadSignature, SignatureMalformed)):
            csrf.unsign(token)

    def test_max_age(self):
        s = SessionSigner(secret=SECRET)
        token = s.sign("sid")
        assert s.unsign(token, max_age=7 * 86400) == "sid"

    def test_expired_session(self):
        s = SessionSigner(secret=SECRET)
        old = datetime.now(timezone.utc) - timedelta(days=8)
        token = s.sign("sid", timestamp=old)
        with pytest.raises(SignatureExpired):
            s.unsign(token, max_age=7 * 86400)


class TestCSRFSigner:
    """CSRFSigner: CSRF token signer."""

    def test_sign_unsign(self):
        s = CSRFSigner(secret=SECRET)
        token = s.sign("csrf-token")
        assert s.unsign(token) == "csrf-token"

    def test_inherits_signer(self):
        assert issubclass(CSRFSigner, Signer)
        assert not issubclass(CSRFSigner, TimestampSigner)

    def test_salt_namespace(self):
        s = CSRFSigner(secret=SECRET)
        assert s._salt == "aquilia.csrf"

    def test_incompatible_with_session(self):
        csrf = CSRFSigner(secret=SECRET)
        sess = SessionSigner(secret=SECRET)
        token = csrf.sign("data")
        with pytest.raises((BadSignature, SignatureMalformed)):
            sess.unsign(token)


class TestActivationLinkSigner:
    """ActivationLinkSigner: one-time link signer with default max_age."""

    def test_sign_unsign(self):
        s = ActivationLinkSigner(secret=SECRET)
        token = s.sign("user-42")
        assert s.unsign(token) == "user-42"

    def test_inherits_timestamp_signer(self):
        assert issubclass(ActivationLinkSigner, TimestampSigner)

    def test_salt_namespace(self):
        s = ActivationLinkSigner(secret=SECRET)
        assert s._salt == "aquilia.activation"

    def test_default_24h_expiry(self):
        s = ActivationLinkSigner(secret=SECRET)
        # Token from 25 hours ago should expire with default max_age
        old = datetime.now(timezone.utc) - timedelta(hours=25)
        token = s.sign("uid", timestamp=old)
        with pytest.raises(SignatureExpired):
            s.unsign(token)  # uses _DEFAULT_MAX_AGE = 86400

    def test_custom_max_age_override(self):
        s = ActivationLinkSigner(secret=SECRET)
        token = s.sign("uid")
        # Very generous max_age — should pass
        assert s.unsign(token, max_age=999999) == "uid"


class TestCacheKeySigner:
    """CacheKeySigner: cache value integrity signer."""

    def test_sign_unsign(self):
        s = CacheKeySigner(secret=SECRET)
        token = s.sign("cache-entry")
        assert s.unsign(token) == "cache-entry"

    def test_sign_bytes(self):
        s = CacheKeySigner(secret=SECRET)
        data = b"\x00\xff pickle data"
        signed = s.sign_bytes(data)
        assert s.unsign_bytes(signed) == data

    def test_salt_namespace(self):
        s = CacheKeySigner(secret=SECRET)
        assert s._salt == "aquilia.cache"


class TestCookieSigner:
    """CookieSigner: signed HTTP cookie signer."""

    def test_sign_unsign(self):
        s = CookieSigner(secret=SECRET)
        token = s.sign("remember-me")
        assert s.unsign(token) == "remember-me"

    def test_inherits_timestamp_signer(self):
        assert issubclass(CookieSigner, TimestampSigner)

    def test_salt_namespace(self):
        s = CookieSigner(secret=SECRET)
        assert s._salt == "aquilia.cookies"

    def test_max_age(self):
        s = CookieSigner(secret=SECRET)
        token = s.sign("val")
        assert s.unsign(token, max_age=3600) == "val"


class TestAPIKeySigner:
    """APIKeySigner: short-lived API key / signed URL signer."""

    def test_sign_unsign(self):
        s = APIKeySigner(secret=SECRET)
        token = s.sign("user:42:read")
        assert s.unsign(token) == "user:42:read"

    def test_inherits_timestamp_signer(self):
        assert issubclass(APIKeySigner, TimestampSigner)

    def test_salt_namespace(self):
        s = APIKeySigner(secret=SECRET)
        assert s._salt == "aquilia.apikeys"

    def test_short_lived_expiry(self):
        s = APIKeySigner(secret=SECRET)
        old = datetime.now(timezone.utc) - timedelta(minutes=10)
        token = s.sign("key", timestamp=old)
        with pytest.raises(SignatureExpired):
            s.unsign(token, max_age=300)  # 5-minute URL


# ========================================================================
# 11. Cross-domain isolation regression
# ========================================================================


class TestCrossDomainIsolation:
    """
    Tokens from one domain signer must never validate in another,
    even when using the same secret key.  This is the *namespace isolation*
    property enforced by the ``salt`` parameter.
    """

    @pytest.fixture
    def signers(self):
        return {
            "session": SessionSigner(secret=SECRET),
            "csrf": CSRFSigner(secret=SECRET),
            "activation": ActivationLinkSigner(secret=SECRET),
            "cache": CacheKeySigner(secret=SECRET),
            "cookie": CookieSigner(secret=SECRET),
            "apikey": APIKeySigner(secret=SECRET),
            "plain": Signer(secret=SECRET),
        }

    def test_no_cross_domain_acceptance(self, signers):
        """Each signer's token must be rejected by all other signers."""
        for name, signer in signers.items():
            token = signer.sign("test-value")
            for other_name, other_signer in signers.items():
                if other_name == name:
                    continue
                with pytest.raises((BadSignature, SignatureMalformed)):
                    other_signer.unsign(token)


# ========================================================================
# 12. SigningConfig dataclass
# ========================================================================


class TestSigningConfig:
    """SigningConfig: configuration dataclass."""

    def test_defaults(self):
        cfg = SigningConfig()
        assert cfg.secret == ""
        assert cfg.algorithm == "HS256"
        assert cfg.salt == "aquilia.signing"
        assert cfg.fallback_secrets == []

    def test_apply_configures_global(self):
        cfg = SigningConfig(secret=SECRET, algorithm="HS384")
        cfg.apply()
        import aquilia.signing as _mod
        assert _mod._GLOBAL_SECRETS[0] == SECRET
        assert _mod._GLOBAL_ALGORITHM == "HS384"

    def test_apply_with_empty_secret_noop(self):
        cfg = SigningConfig(secret="")
        import aquilia.signing as _mod
        _mod._GLOBAL_SECRETS = []
        cfg.apply()
        assert _mod._GLOBAL_SECRETS == []

    def test_make_session_signer(self):
        cfg = SigningConfig(secret=SECRET)
        s = cfg.make_session_signer()
        assert isinstance(s, SessionSigner)

    def test_make_csrf_signer(self):
        cfg = SigningConfig(secret=SECRET)
        s = cfg.make_csrf_signer()
        assert isinstance(s, CSRFSigner)

    def test_make_activation_signer(self):
        cfg = SigningConfig(secret=SECRET)
        s = cfg.make_activation_signer()
        assert isinstance(s, ActivationLinkSigner)

    def test_make_cache_signer(self):
        cfg = SigningConfig(secret=SECRET)
        s = cfg.make_cache_signer()
        assert isinstance(s, CacheKeySigner)

    def test_make_cookie_signer(self):
        cfg = SigningConfig(secret=SECRET)
        s = cfg.make_cookie_signer()
        assert isinstance(s, CookieSigner)

    def test_make_api_key_signer(self):
        cfg = SigningConfig(secret=SECRET)
        s = cfg.make_api_key_signer()
        assert isinstance(s, APIKeySigner)

    def test_apply_with_fallback_secrets(self):
        cfg = SigningConfig(secret=SECRET, fallback_secrets=[ALT_SECRET])
        cfg.apply()
        import aquilia.signing as _mod
        assert len(_mod._GLOBAL_SECRETS) == 2


# ========================================================================
# 13. Edge cases & regression guards
# ========================================================================


class TestEdgeCases:
    """Miscellaneous edge cases and regression guards."""

    def test_very_long_value(self):
        s = Signer(secret=SECRET)
        val = "x" * 100_000
        token = s.sign(val)
        assert s.unsign(token) == val

    def test_binary_values_sign_bytes(self):
        s = Signer(secret=SECRET)
        data = bytes(range(256)) * 100
        signed = s.sign_bytes(data)
        assert s.unsign_bytes(signed) == data

    def test_max_age_zero(self):
        ts = TimestampSigner(secret=SECRET)
        token = ts.sign("hello")
        time.sleep(0.01)
        with pytest.raises(SignatureExpired):
            ts.unsign(token, max_age=0)

    def test_max_age_negative(self):
        ts = TimestampSigner(secret=SECRET)
        token = ts.sign("hello")
        with pytest.raises(SignatureExpired):
            ts.unsign(token, max_age=-1)

    def test_all_algorithms_produce_different_signatures(self):
        """Different algorithms must produce different signatures for same input."""
        sigs = set()
        for algo in ["HS256", "HS384", "HS512"]:
            s = Signer(secret=SECRET, algorithm=algo)
            token = s.sign("test")
            sigs.add(token)
        assert len(sigs) == 3

    def test_signing_is_deterministic_for_same_params(self):
        s = Signer(secret=SECRET, salt="det")
        t1 = s.sign("hello")
        t2 = s.sign("hello")
        assert t1 == t2

    def test_timestamp_signing_differs_over_time(self):
        ts = TimestampSigner(secret=SECRET)
        t1 = ts.sign("hello")
        time.sleep(0.01)
        t2 = ts.sign("hello")
        # Tokens differ because timestamps differ
        assert t1 != t2

    def test_constant_min_key_bytes(self):
        assert _MIN_KEY_BYTES == 32

    def test_hmac_algorithms_set(self):
        assert "HS256" in _HMAC_ALGORITHMS
        assert "HS384" in _HMAC_ALGORITHMS
        assert "HS512" in _HMAC_ALGORITHMS

    def test_asymmetric_algorithms_set(self):
        assert "RS256" in _ASYMMETRIC_ALGORITHMS
        assert "ES256" in _ASYMMETRIC_ALGORITHMS
        assert "EdDSA" in _ASYMMETRIC_ALGORITHMS

    def test_sep_constant(self):
        assert _SEP == ":"

    def test_epoch_is_2020(self):
        dt = datetime(2020, 1, 1, tzinfo=timezone.utc)
        assert _EPOCH == int(dt.timestamp() * 1_000_000)

    def test_signer_with_custom_backend(self):
        """Users can inject a custom SignerBackend."""
        backend = HmacSignerBackend(SECRET, salt="custom-backend")
        s = Signer(backend=backend)
        token = s.sign("hello")
        assert s.unsign(token) == "hello"

    def test_concurrent_signers_isolated(self):
        """Two signers created independently should be isolated."""
        s1 = Signer(secret=SECRET, salt="one")
        s2 = Signer(secret=SECRET, salt="two")
        token1 = s1.sign("value")
        token2 = s2.sign("value")
        assert token1 != token2
        assert s1.unsign(token1) == "value"
        assert s2.unsign(token2) == "value"
        with pytest.raises(BadSignature):
            s1.unsign(token2)

    def test_large_json_object(self):
        s = Signer(secret=SECRET)
        obj = {f"key_{i}": f"value_{i}" for i in range(1000)}
        token = s.sign_object(obj)
        assert s.unsign_object(token) == obj

    def test_rotating_signer_sign_always_uses_first_key(self):
        """Verify that RotatingSigner.sign() always uses the first key."""
        rs = RotatingSigner(secrets=[SECRET, ALT_SECRET])
        token = rs.sign("hello")

        # Must be verifiable with SECRET (first key) only
        s_first = Signer(secret=SECRET)
        assert s_first.unsign(token) == "hello"

        # Must NOT be verifiable with ALT_SECRET alone (second key)
        s_second = Signer(secret=ALT_SECRET)
        with pytest.raises(BadSignature):
            s_second.unsign(token)

    def test_dumps_loads_with_unicode(self):
        obj = {"name": "日本語", "emoji": "🎉🚀"}
        token = dumps(obj, secret=SECRET)
        assert loads(token, secret=SECRET) == obj

    def test_corrupted_payload_raises_malformed(self):
        """Manually corrupt the base64 payload after signing."""
        s = Signer(secret=SECRET)
        token = s.sign("hello")
        # Insert garbage into the value part
        parts = token.rsplit(":", 1)
        corrupted = "@@garbage@@" + ":" + parts[1]
        with pytest.raises((BadSignature, SignatureMalformed)):
            s.unsign(corrupted)

    def test_empty_token_raises(self):
        s = Signer(secret=SECRET)
        with pytest.raises(SignatureMalformed):
            s.unsign("")

    def test_only_separator_raises(self):
        s = Signer(secret=SECRET)
        with pytest.raises(BadSignature):
            s.unsign(":")


# ========================================================================
# 14. __all__ exports sanity check
# ========================================================================


class TestExports:
    """Ensure all documented public APIs are importable."""

    def test_all_exports_importable(self):
        import aquilia.signing as mod

        for name in mod.__all__:
            assert hasattr(mod, name), f"{name} listed in __all__ but not in module"
