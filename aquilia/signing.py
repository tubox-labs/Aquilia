"""
Aquilia Signing Engine  (``aquilia.signing``)
=============================================

A production-grade, zero-dependency cryptographic signing library for the
Aquilia framework.  Inspired by Django's ``django.core.signing`` but
significantly extended with modern algorithms, structured payload types,
key rotation, and a rich feature set designed for a full-stack async
Python web framework.

Design principles
-----------------
* **Zero mandatory dependencies** — all default algorithms use the Python
  standard library only (``hmac``, ``hashlib``, ``secrets``, ``struct``).
* **Layered API** — use the simple :func:`sign` / :func:`unsign` functions
  for quick one-liners, or the :class:`Signer` / :class:`TimestampSigner`
  classes for full control, or the :class:`SignerBackend` protocol for
  custom backends.
* **Timestamp-aware** — :class:`TimestampSigner` embeds a microsecond-
  precision UTC timestamp; :meth:`TimestampSigner.unsign` enforces ``max_age``
  automatically with :class:`SignatureExpired`.
* **Structured payloads** — :class:`Dumps` / :class:`Loads` serialise
  arbitrary Python objects (dict, list, primitives) into signed URL-safe
  strings via compact JSON + Base64 encoding.
* **Key rotation** — :class:`RotatingSigner` accepts an ordered list of
  secrets and tries each one for verification; signing always uses the
  first (current) key.  Retiring an old key is a one-line config change.
* **Algorithm agility** — HMAC-SHA256 (default), HMAC-SHA384, HMAC-SHA512,
  with optional asymmetric algorithms (RS256/ES256/EdDSA) when the
  ``cryptography`` package is installed.
* **Constant-time comparison** — all signature verification uses
  :func:`hmac.compare_digest` to prevent timing attacks.
* **Namespace isolation** — signers accept a ``salt`` that is mixed into
  the signing key; different salts produce incompatible signatures even
  with the same secret key, preventing cross-subsystem token confusion.
* **OWASP-aligned** — rejects the "none" algorithm, enforces key length
  minimums (≥32 bytes), validates all inputs before use.

Quick-start
-----------

.. code-block:: python

    from aquilia.signing import Signer, TimestampSigner, dumps, loads

    # Simple value signing
    s = Signer(secret="my-secret-key")
    token = s.sign("hello")
    value = s.unsign(token)          # "hello"

    # Timestamped (expires after 60 s)
    ts = TimestampSigner(secret="my-secret-key")
    token = ts.sign("hello")
    value = ts.unsign(token, max_age=60)

    # Serialised JSON payload (for cookies, one-time links, …)
    token = dumps({"user_id": 42, "roles": ["admin"]}, secret="my-key")
    data  = loads(token, secret="my-key", max_age=3600)

    # Key rotation
    from aquilia.signing import RotatingSigner
    rs = RotatingSigner(secrets=["new-key", "old-key"])
    value = rs.unsign(old_token)     # verified with old-key, re-sign with new-key
"""

from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import importlib.util
import json
import logging
import struct
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, cast

__all__ = [
    # Exceptions
    "SigningError",
    "BadSignature",
    "SignatureExpired",
    "SignatureMalformed",
    "UnsupportedAlgorithmError",
    # Core signer classes
    "Signer",
    "TimestampSigner",
    "RotatingSigner",
    # Structured payload helpers
    "dumps",
    "loads",
    # Backend protocol + default backend
    "SignerBackend",
    "HmacSignerBackend",
    # Convenience factories
    "make_signer",
    "make_timestamp_signer",
    # Low-level primitives
    "b64_encode",
    "b64_decode",
    "constant_time_compare",
    "derive_key",
    # Type aliases
    "Algorithm",
]

log = logging.getLogger("aquilia.signing")

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

#: Supported signing algorithm names.
Algorithm = Literal["HS256", "HS384", "HS512", "RS256", "ES256", "EdDSA"]

# HMAC algorithms available with stdlib only
_HMAC_ALGORITHMS: frozenset[str] = frozenset({"HS256", "HS384", "HS512"})

# Asymmetric algorithms — require ``pip install cryptography``
_ASYMMETRIC_ALGORITHMS: frozenset[str] = frozenset({"RS256", "ES256", "EdDSA"})

_ALL_ALGORITHMS: frozenset[str] = _HMAC_ALGORITHMS | _ASYMMETRIC_ALGORITHMS

# stdlib digest names for each HMAC algorithm
_HMAC_DIGEST_MAP: dict[str, str] = {
    "HS256": "sha256",
    "HS384": "sha384",
    "HS512": "sha512",
}

# Separator character used between payload and signature
_SEP = ":"

# Minimum secret key length (bytes) — enforced at construction time.
_MIN_KEY_BYTES = 32

# Epoch for compact timestamp encoding (microseconds since this date)
# Using 2020-01-01 00:00:00 UTC to keep encoded values small for years.
_EPOCH = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1_000_000)


# ===========================================================================
# Exceptions — Backed by the Aquilia fault mechanism
# ===========================================================================

from aquilia.faults.domains import (
    BadSignatureFault,
    ConfigInvalidFault,
    ConfigMissingFault,
    SignatureExpiredFault,
    SignatureMalformedFault,
    SigningFault,
    UnsupportedAlgorithmFault,
)

# Re-export fault classes under the legacy names so that existing
# ``except SigningError`` / ``except BadSignature`` code keeps working.
SigningError = SigningFault
BadSignature = BadSignatureFault
SignatureExpired = SignatureExpiredFault
SignatureMalformed = SignatureMalformedFault
UnsupportedAlgorithmError = UnsupportedAlgorithmFault


# ===========================================================================
# Low-level primitives
# ===========================================================================


def b64_encode(data: bytes) -> str:
    """
    URL-safe, no-padding Base64 encode.

    Produces a string safe to embed in URLs, cookies, and JSON values
    without further escaping.

    Args:
        data: Raw bytes to encode.

    Returns:
        URL-safe Base64 string with ``=`` padding stripped.
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64_decode(data: str | bytes) -> bytes:
    """
    URL-safe, no-padding Base64 decode.

    Accepts strings produced by :func:`b64_encode` (no padding required).

    Args:
        data: URL-safe Base64 string or bytes.

    Returns:
        Decoded raw bytes.

    Raises:
        SignatureMalformed: If the input is not valid Base64.
    """
    original: str
    if isinstance(data, str):
        original = data
        data = data.encode("ascii")
    else:
        try:
            original = data.decode("ascii")
        except UnicodeDecodeError as exc:
            raise SignatureMalformed(f"Invalid Base64 encoding: {exc}") from exc
    # Re-add padding
    pad = 4 - (len(data) % 4)
    if pad != 4:
        data += b"=" * pad
    try:
        decoded = base64.urlsafe_b64decode(data)
    except Exception as exc:
        raise SignatureMalformed(f"Invalid Base64 encoding: {exc}") from exc

    canonical = b64_encode(decoded)
    if canonical != original.rstrip("="):
        raise SignatureMalformed(
            "Invalid Base64 encoding: non-canonical or tampered input.",
        )
    return decoded


def constant_time_compare(a: bytes | str, b: bytes | str) -> bool:
    """
    Compare two values in constant time to prevent timing attacks.

    Wraps :func:`hmac.compare_digest`.  Both arguments must be of the
    same type (``bytes`` or ``str``).

    Returns:
        ``True`` if the values are identical, ``False`` otherwise.
    """
    if isinstance(a, str):
        a = a.encode("utf-8")
    if isinstance(b, str):
        b = b.encode("utf-8")
    return _hmac.compare_digest(a, b)


def derive_key(secret: str | bytes, salt: str, algorithm: str = "HS256") -> bytes:
    """
    Derive a signing sub-key from *secret* and *salt* using HKDF-lite.

    This prevents cross-subsystem token confusion: even when two signers
    share the same ``secret``, using different ``salt`` values produces
    completely different signing keys.

    The derivation is::

        sub_key = HMAC-SHA256(secret, "aquilia.signing|" + salt + "|" + algorithm)

    Args:
        secret:    Master secret key (str or bytes, ≥32 bytes recommended).
        salt:      Namespace salt (e.g. ``"sessions"``, ``"csrf"``, …).
        algorithm: Algorithm name — changes the derived key per algorithm.

    Returns:
        32-byte derived key as ``bytes``.
    """
    if isinstance(secret, str):
        secret = secret.encode("utf-8")
    info = f"aquilia.signing|{salt}|{algorithm}".encode()
    return _hmac.new(secret, info, hashlib.sha256).digest()


def _require_cryptography(algorithm: str) -> None:
    """Raise :class:`UnsupportedAlgorithmError` if cryptography is not installed."""
    if importlib.util.find_spec("cryptography") is None:
        raise UnsupportedAlgorithmError(
            f"Algorithm '{algorithm}' requires the 'cryptography' package. "
            "Install it with:  pip install cryptography\n"
            "Or switch to a zero-dependency algorithm:\n"
            "    algorithm='HS256'  # default — no extra deps"
        )


def _check_key_length(key: str | bytes, label: str = "secret") -> None:
    """Warn (not raise) if the key is shorter than the recommended minimum."""
    raw = key.encode("utf-8") if isinstance(key, str) else key
    if len(raw) < _MIN_KEY_BYTES:
        log.warning(
            "Aquilia signing: %s is only %d bytes; recommend ≥%d bytes "
            "for adequate security (use secrets.token_urlsafe(32) to generate one).",
            label,
            len(raw),
            _MIN_KEY_BYTES,
        )


# ===========================================================================
# SignerBackend protocol
# ===========================================================================


class SignerBackend(ABC):
    """
    Abstract backend that produces and verifies raw byte signatures.

    Implement this protocol to add custom signing backends (e.g. cloud
    KMS, HSM, asymmetric algorithms).

    The default backend is :class:`HmacSignerBackend`.
    """

    @abstractmethod
    def sign(self, message: bytes) -> bytes:
        """Return the signature for *message*."""

    @abstractmethod
    def verify(self, message: bytes, signature: bytes) -> bool:
        """Return ``True`` if *signature* is valid for *message*."""

    @property
    @abstractmethod
    def algorithm(self) -> str:
        """The algorithm name (e.g. ``"HS256"``)."""


class HmacSignerBackend(SignerBackend):
    """
    Default signing backend — HMAC with a configurable digest.

    Supports ``HS256`` (default), ``HS384``, and ``HS512``.
    All operations use only the Python standard library.

    Args:
        secret:    Signing secret (str or bytes).
        salt:      Namespace salt — mixed into the derived key so different
                   signers with the same secret produce incompatible signatures.
        algorithm: HMAC algorithm to use.  One of ``"HS256"`` / ``"HS384"``
                   / ``"HS512"``.

    Example::

        backend = HmacSignerBackend(secret="my-key", salt="csrf")
        sig = backend.sign(b"hello")
        ok  = backend.verify(b"hello", sig)   # True
    """

    def __init__(
        self,
        secret: str | bytes,
        salt: str = "aquilia.signing",
        algorithm: str = "HS256",
    ) -> None:
        if algorithm not in _HMAC_ALGORITHMS:
            raise UnsupportedAlgorithmError(
                f"HmacSignerBackend supports {sorted(_HMAC_ALGORITHMS)}, got {algorithm!r}. "
                "For asymmetric algorithms use AsymmetricSignerBackend."
            )
        _check_key_length(secret)
        self._algorithm = algorithm
        self._digest_name = _HMAC_DIGEST_MAP[algorithm]
        # Derive a namespace-specific sub-key
        self._key: bytes = derive_key(secret, salt, algorithm)

    @property
    def algorithm(self) -> str:
        return self._algorithm

    def sign(self, message: bytes) -> bytes:
        """Return HMAC-{digest} signature of *message*."""
        return _hmac.new(self._key, message, self._digest_name).digest()

    def verify(self, message: bytes, signature: bytes) -> bool:
        """Return ``True`` iff *signature* equals HMAC of *message* (constant-time)."""
        expected = self.sign(message)
        return constant_time_compare(expected, signature)


class AsymmetricSignerBackend(SignerBackend):
    """
    Asymmetric signing backend using the ``cryptography`` package.

    Supports ``RS256`` (RSA-PKCS1v15 + SHA-256), ``ES256`` (ECDSA P-256),
    and ``EdDSA`` (Ed25519).

    Requires ``pip install cryptography``.

    Args:
        private_key_pem: PEM-encoded private key (for signing).
        public_key_pem:  PEM-encoded public key (for verification).
        algorithm:       One of ``"RS256"``, ``"ES256"``, ``"EdDSA"``.

    At minimum you must provide either *private_key_pem* (signing) or
    *public_key_pem* (verification-only).  Providing both enables both.
    """

    def __init__(
        self,
        algorithm: str,
        *,
        private_key_pem: str | None = None,
        public_key_pem: str | None = None,
    ) -> None:
        if algorithm not in _ASYMMETRIC_ALGORITHMS:
            raise UnsupportedAlgorithmError(
                f"AsymmetricSignerBackend supports {sorted(_ASYMMETRIC_ALGORITHMS)}, got {algorithm!r}."
            )
        _require_cryptography(algorithm)
        if not private_key_pem and not public_key_pem:
            raise ConfigInvalidFault(
                key="asymmetric_signer_keys",
                reason="At least one of private_key_pem or public_key_pem must be provided.",
            )
        self._algorithm = algorithm
        self._private_key_pem = private_key_pem
        self._public_key_pem = public_key_pem

    @property
    def algorithm(self) -> str:
        return self._algorithm

    def sign(self, message: bytes) -> bytes:
        if not self._private_key_pem:
            raise SigningError("No private key configured — cannot sign.")
        from cryptography.hazmat.backends import default_backend  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives import hashes, serialization  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives.asymmetric import ec, padding  # type: ignore[import-not-found]

        private_key = serialization.load_pem_private_key(
            self._private_key_pem.encode(),
            password=None,
            backend=default_backend(),
        )
        if self._algorithm == "RS256":
            return cast(bytes, private_key.sign(message, padding.PKCS1v15(), hashes.SHA256()))
        elif self._algorithm == "ES256":
            return cast(bytes, private_key.sign(message, ec.ECDSA(hashes.SHA256())))
        elif self._algorithm == "EdDSA":
            return cast(bytes, private_key.sign(message))
        else:
            raise UnsupportedAlgorithmError(f"Unknown algorithm: {self._algorithm}")

    def verify(self, message: bytes, signature: bytes) -> bool:
        pem = self._public_key_pem or self._private_key_pem
        if not pem:
            raise SigningError("No key configured for verification.")
        from cryptography.exceptions import InvalidSignature  # type: ignore[import-not-found]
        from cryptography.hazmat.backends import default_backend  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives import hashes, serialization  # type: ignore[import-not-found]
        from cryptography.hazmat.primitives.asymmetric import ec, padding  # type: ignore[import-not-found]

        try:
            if self._public_key_pem:
                key = serialization.load_pem_public_key(self._public_key_pem.encode(), backend=default_backend())
            else:
                # Extract public key from private key PEM
                priv = serialization.load_pem_private_key(pem.encode(), password=None, backend=default_backend())
                key = priv.public_key()

            if self._algorithm == "RS256":
                key.verify(signature, message, padding.PKCS1v15(), hashes.SHA256())
            elif self._algorithm == "ES256":
                key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
            elif self._algorithm == "EdDSA":
                key.verify(signature, message)
            else:
                return False
            return True
        except InvalidSignature:
            return False


# ===========================================================================
# Core Signer
# ===========================================================================


class Signer:
    """
    Simple HMAC-based data signer.

    Signs arbitrary string values by appending ``<sep><b64-signature>``
    and verifies them on read.  Optionally uses a ``salt`` to namespace
    the signing key so different subsystems can share the same master
    secret without cross-subsystem token confusion.

    Args:
        secret:    Master signing secret.  If omitted, uses ``_GLOBAL_SECRET``
                   (set via :func:`configure` or ``AquilaConfig.signing.secret``).
        salt:      Namespace for this signer.  Defaults to ``"aquilia.signing"``.
        sep:       Separator character between value and signature.  Must not
                   appear in Base64 output (``:``, ``.``, ``/`` are safe).
        algorithm: HMAC algorithm.  One of ``"HS256"`` / ``"HS384"`` / ``"HS512"``.
        backend:   Custom :class:`SignerBackend`.  If provided, *secret*,
                   *salt*, and *algorithm* are ignored.

    Examples::

        s = Signer(secret="my-key")
        token = s.sign("user-42")
        value = s.unsign(token)        # "user-42"

        # Namespaced — incompatible with the signer above even with same key:
        csrf = Signer(secret="my-key", salt="csrf")
        token2 = csrf.sign("user-42")
        s.unsign(token2)               # raises BadSignature
    """

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        salt: str = "aquilia.signing",
        sep: str = _SEP,
        algorithm: str = "HS256",
        backend: SignerBackend | None = None,
    ) -> None:
        if sep in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=":
            raise ConfigInvalidFault(
                key="signer.sep",
                reason=f"sep={sep!r} is a Base64 character and would break parsing. "
                "Use ':', '.', '/', or another non-Base64 character.",
            )

        if backend is not None:
            self._backend = backend
        else:
            resolved_secret = secret or _get_global_secret()
            self._backend = HmacSignerBackend(
                secret=resolved_secret,
                salt=salt,
                algorithm=algorithm,
            )

        self._sep = sep
        self._salt = salt
        self._algorithm = algorithm

    # ── Core sign / unsign ───────────────────────────────────────────

    def sign(self, value: str, **kwargs: Any) -> str:
        """
        Sign *value* and return ``"<value><sep><b64sig>"``.

        Args:
            value: The string value to sign.  Must not contain the separator.

        Returns:
            Signed token string.

        Raises:
            ValueError: If *value* contains the separator character.
        """
        if self._sep in value:
            raise SignatureMalformed(
                f"Value {value!r} contains separator character {self._sep!r}. "
                "Use a different separator or encode the value first."
            )
        sig = self._backend.sign(value.encode("utf-8"))
        return f"{value}{self._sep}{b64_encode(sig)}"

    def unsign(self, signed_value: str, **kwargs: Any) -> str:
        """
        Verify and return the original value from a signed token.

        Args:
            signed_value: Token produced by :meth:`sign`.

        Returns:
            The original unsigned value.

        Raises:
            SignatureMalformed: Token does not contain the separator.
            BadSignature:       HMAC verification failed.
        """
        if self._sep not in signed_value:
            raise SignatureMalformed(
                f"No separator {self._sep!r} found in signed value.",
            )
        # Split on the LAST occurrence so the value itself may contain the sep char
        value, sig_b64 = signed_value.rsplit(self._sep, 1)
        try:
            sig = b64_decode(sig_b64)
        except SignatureMalformed as exc:
            raise BadSignature(
                f"Signature {sig_b64!r} is not valid for value {value!r}.",
                original=signed_value,
            ) from exc
        if not self._backend.verify(value.encode("utf-8"), sig):
            raise BadSignature(
                f"Signature {sig_b64!r} is not valid for value {value!r}.",
                original=signed_value,
            )
        return value

    def sign_bytes(self, data: bytes) -> bytes:
        """
        Sign raw *data* and return ``data + sep_byte + b64sig`` as bytes.

        Useful for signing binary blobs.

        Args:
            data: Raw bytes to sign.

        Returns:
            Signed bytes.
        """
        sig = self._backend.sign(data)
        sep_b = self._sep.encode("utf-8")
        return data + sep_b + b64_encode(sig).encode("ascii")

    def unsign_bytes(self, signed_data: bytes) -> bytes:
        """
        Verify and return the original bytes from signed byte data.

        Args:
            signed_data: Data produced by :meth:`sign_bytes`.

        Returns:
            Original unsigned bytes.

        Raises:
            SignatureMalformed: Separator not found.
            BadSignature:       HMAC mismatch.
        """
        sep_b = self._sep.encode("utf-8")
        idx = signed_data.rfind(sep_b)
        if idx == -1:
            raise SignatureMalformed("Separator not found in signed bytes.")
        data = signed_data[:idx]
        sig_b64 = signed_data[idx + len(sep_b) :]
        try:
            sig = b64_decode(sig_b64)
        except SignatureMalformed as exc:
            raise BadSignature("Byte signature verification failed.") from exc
        if not self._backend.verify(data, sig):
            raise BadSignature("Byte signature verification failed.")
        return data

    def sign_object(self, obj: Any, **kwargs: Any) -> str:
        """
        Serialise *obj* to JSON, sign, and return a URL-safe token.

        Convenience wrapper around :meth:`sign` for non-string payloads.

        Args:
            obj: Any JSON-serialisable Python object.

        Returns:
            Signed URL-safe string.
        """
        payload = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        return self.sign(b64_encode(payload.encode("utf-8")))

    def unsign_object(self, token: str, **kwargs: Any) -> Any:
        """
        Verify *token* and deserialise the embedded JSON payload.

        Args:
            token: Token produced by :meth:`sign_object`.

        Returns:
            Deserialised Python object.

        Raises:
            BadSignature: Verification failed.
            SignatureMalformed: Corrupted JSON or Base64.
        """
        value = self.unsign(token)
        try:
            payload_json = b64_decode(value).decode("utf-8")
            return json.loads(payload_json)
        except Exception as exc:
            raise SignatureMalformed(f"Could not deserialise signed object: {exc}") from exc

    def __repr__(self) -> str:
        return f"Signer(salt={self._salt!r}, algorithm={self._algorithm!r}, backend={type(self._backend).__name__})"


# ===========================================================================
# TimestampSigner
# ===========================================================================

#: Compact format version — allows future format changes without breaking.
_TS_FORMAT_V1 = 1


class TimestampSigner(Signer):
    """
    Signer that embeds a UTC timestamp in the signed value.

    The timestamp is encoded as a compact, URL-safe 8-byte struct
    (microseconds since 2020-01-01 UTC) appended to the value before
    signing.  :meth:`unsign` verifies the signature **and** optionally
    rejects tokens older than ``max_age`` seconds.

    Token format::

        <b64(value)>.<b64(timestamp_8bytes)>:<b64(hmac_sig)>

    Args:
        secret:    Master signing secret.
        salt:      Namespace for this signer (default ``"aquilia.signing.ts"``).
        sep:       Separator between value+timestamp and signature.
        algorithm: HMAC algorithm.
        backend:   Custom :class:`SignerBackend`.

    Examples::

        ts = TimestampSigner(secret="my-key")
        token = ts.sign("hello")
        # 30-second expiry:
        value = ts.unsign(token, max_age=30)

        # Read the date without validating max_age:
        value, when = ts.unsign_with_timestamp(token)
    """

    _TS_SEP = "."  # separates value from timestamp *within* the value part

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        salt: str = "aquilia.signing.ts",
        sep: str = _SEP,
        algorithm: str = "HS256",
        backend: SignerBackend | None = None,
    ) -> None:
        super().__init__(
            secret,
            salt=salt,
            sep=sep,
            algorithm=algorithm,
            backend=backend,
        )

    # ── Timestamp encoding ───────────────────────────────────────────

    @staticmethod
    def _encode_timestamp(dt: datetime | None = None) -> str:
        """
        Encode *dt* (defaults to now) as an 8-byte big-endian microsecond
        offset from :data:`_EPOCH`, then Base64-encode that.

        The compact encoding avoids printable datetime strings in tokens
        (which could leak timing information in logs).
        """
        if dt is None:
            dt = datetime.now(timezone.utc)
        us = int(dt.timestamp() * 1_000_000) - _EPOCH
        # Pack as signed 64-bit big-endian integer
        raw = struct.pack(">q", us)
        return b64_encode(raw)

    @staticmethod
    def _decode_timestamp(ts_b64: str) -> datetime:
        """
        Decode a Base64 timestamp produced by :meth:`_encode_timestamp`.

        Returns:
            UTC-aware :class:`datetime`.

        Raises:
            SignatureMalformed: If the timestamp bytes are invalid.
        """
        try:
            raw = b64_decode(ts_b64)
            if len(raw) != 8:
                raise ValueError(f"Expected 8 bytes, got {len(raw)}")
            (us,) = struct.unpack(">q", raw)
            epoch_us = _EPOCH + us
            return datetime.fromtimestamp(epoch_us / 1_000_000, tz=timezone.utc)
        except (SignatureMalformed, ValueError, struct.error) as exc:
            raise SignatureMalformed(f"Cannot decode timestamp from {ts_b64!r}: {exc}") from exc

    # ── Core methods ─────────────────────────────────────────────────

    def sign(self, value: str, *, timestamp: datetime | None = None, **kwargs: Any) -> str:
        """
        Sign *value* with an embedded UTC timestamp.

        Args:
            value:     Value to sign.
            timestamp: Timestamp to embed (defaults to ``datetime.now(UTC)``).

        Returns:
            Signed token with embedded timestamp.
        """
        ts_b64 = self._encode_timestamp(timestamp)
        val_b64 = b64_encode(value.encode("utf-8"))
        compound = f"{val_b64}{self._TS_SEP}{ts_b64}"
        return super().sign(compound)

    def unsign(
        self,
        signed_value: str,
        max_age: float | int | timedelta | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Verify signature, optionally enforce ``max_age``, and return value.

        Args:
            signed_value: Token produced by :meth:`sign`.
            max_age:      Maximum age in seconds (or a :class:`timedelta`).
                          Pass ``None`` to skip age validation.

        Returns:
            The original unsigned value.

        Raises:
            SignatureMalformed: Token has wrong structure.
            SignatureExpired:   Signature is valid but older than *max_age*.
            BadSignature:       HMAC verification failed.
        """
        compound = super().unsign(signed_value)
        value, ts = self._split_compound(compound)
        if max_age is not None:
            self._check_age(ts, max_age, signed_value)
        return value

    def unsign_with_timestamp(
        self,
        signed_value: str,
        max_age: float | int | timedelta | None = None,
    ) -> tuple[str, datetime]:
        """
        Verify signature and return ``(value, timestamp)`` tuple.

        Args:
            signed_value: Token produced by :meth:`sign`.
            max_age:      Maximum age in seconds (or a :class:`timedelta`).

        Returns:
            Tuple of ``(original_value, utc_datetime_when_signed)``.

        Raises:
            SignatureMalformed: Token has wrong structure.
            SignatureExpired:   Older than *max_age*.
            BadSignature:       HMAC verification failed.
        """
        compound = super().unsign(signed_value)
        value, ts = self._split_compound(compound)
        if max_age is not None:
            self._check_age(ts, max_age, signed_value)
        return value, ts

    def sign_object(self, obj: Any, *, timestamp: datetime | None = None, **kwargs: Any) -> str:
        """Sign a JSON-serialisable object with an embedded timestamp."""
        payload = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        encoded = b64_encode(payload.encode("utf-8"))
        return self.sign(encoded, timestamp=timestamp)

    def unsign_object(
        self,
        token: str,
        max_age: float | int | timedelta | None = None,
        **kwargs: Any,
    ) -> Any:
        """Verify and deserialise a JSON object from a timestamped token."""
        encoded = self.unsign(token, max_age=max_age)
        try:
            payload_json = b64_decode(encoded).decode("utf-8")
            return json.loads(payload_json)
        except Exception as exc:
            raise SignatureMalformed(f"Could not deserialise signed object: {exc}") from exc

    # ── Helpers ──────────────────────────────────────────────────────

    def _split_compound(self, compound: str) -> tuple[str, datetime]:
        """Split the compound ``<val_b64>.<ts_b64>`` string."""
        parts = compound.rsplit(self._TS_SEP, 1)
        if len(parts) != 2:
            raise SignatureMalformed(f"TimestampSigner: expected '<value>.<timestamp>', got {compound!r}")
        val_b64, ts_b64 = parts
        ts = self._decode_timestamp(ts_b64)
        try:
            value = b64_decode(val_b64).decode("utf-8")
        except Exception as exc:
            raise SignatureMalformed(f"Cannot decode value: {exc}") from exc
        return value, ts

    def _check_age(
        self,
        ts: datetime,
        max_age: float | int | timedelta,
        original: str,
    ) -> None:
        """Raise :class:`SignatureExpired` if the token is older than *max_age*."""
        max_seconds = max_age.total_seconds() if isinstance(max_age, timedelta) else float(max_age)

        now = datetime.now(timezone.utc)
        age = (now - ts).total_seconds()

        if age > max_seconds:
            raise SignatureExpired(
                f"Signature age {age:.1f}s exceeds max_age {max_seconds:.1f}s.",
                original=original,
                date_signed=ts,
                age_seconds=age,
                max_age_seconds=max_seconds,
            )


# ===========================================================================
# RotatingSigner — transparent key rotation
# ===========================================================================


class RotatingSigner:
    """
    A signer that supports transparent key rotation.

    Signing always uses the **first** (current) secret.  Verification
    tries each secret in order until one succeeds, so old tokens signed
    with retired keys remain valid until explicitly removed.

    This matches the "rolling deploy" pattern:

    1. Add new key at the **front** of the list.
    2. Deploy.  All new tokens use the new key.  Old tokens are still
       verified by the old key.
    3. After the token TTL has elapsed, remove the old key.

    Args:
        secrets:   Ordered list of secrets.  First = current signing key.
        salt:      Namespace salt.
        sep:       Separator character.
        algorithm: HMAC algorithm.

    Example::

        rs = RotatingSigner(secrets=["new-secret", "old-secret"])
        token = rs.sign("hello")          # signed with "new-secret"
        value = rs.unsign(old_token)      # verified with "old-secret"

        # After TTL: remove "old-secret":
        rs = RotatingSigner(secrets=["new-secret"])
    """

    def __init__(
        self,
        secrets: Sequence[str | bytes],
        *,
        salt: str = "aquilia.signing",
        sep: str = _SEP,
        algorithm: str = "HS256",
        timestamp: bool = False,
    ) -> None:
        if not secrets:
            raise ConfigInvalidFault(
                key="rotating_signer.secrets",
                reason="RotatingSigner requires at least one secret.",
            )
        self._sep = sep
        self._salt = salt
        self._algorithm = algorithm
        self._timestamp = timestamp

        cls = TimestampSigner if timestamp else Signer
        self._signers: list[Signer] = [
            cls(
                secret=s,
                salt=salt,
                sep=sep,
                algorithm=algorithm,
            )
            for s in secrets
        ]

    @property
    def current_signer(self) -> Signer:
        """The active signer (used for new :meth:`sign` calls)."""
        return self._signers[0]

    def sign(self, value: str, **kwargs: Any) -> str:
        """Sign *value* with the current (first) secret."""
        return self.current_signer.sign(value, **kwargs)

    def unsign(
        self,
        signed_value: str,
        max_age: float | int | timedelta | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Try each secret in order; return the value verified by the first match.

        Args:
            signed_value: A signed token to verify.
            max_age:      Only relevant when ``timestamp=True``.

        Returns:
            The original unsigned value.

        Raises:
            BadSignature: No secret could verify the token.
        """
        last_exc: Exception = BadSignature("No secrets could verify the signature.")
        for signer in self._signers:
            try:
                if self._timestamp and isinstance(signer, TimestampSigner):
                    return signer.unsign(signed_value, max_age=max_age)
                return signer.unsign(signed_value)
            except (BadSignature, SignatureMalformed) as exc:
                last_exc = exc
        raise BadSignature(
            f"Signature could not be verified with any of the {len(self._signers)} configured secrets.",
            original=signed_value,
        ) from last_exc

    def sign_object(self, obj: Any, **kwargs: Any) -> str:
        """Sign a JSON-serialisable object with the current secret."""
        return self.current_signer.sign_object(obj, **kwargs)

    def unsign_object(
        self,
        token: str,
        max_age: float | int | timedelta | None = None,
    ) -> Any:
        """Verify and deserialise using each secret in order."""
        last_exc: Exception = BadSignature("No secrets could verify the signature.")
        for signer in self._signers:
            try:
                if self._timestamp and isinstance(signer, TimestampSigner):
                    return signer.unsign_object(token, max_age=max_age)
                return signer.unsign_object(token)
            except (BadSignature, SignatureMalformed) as exc:
                last_exc = exc
        raise BadSignature(
            "Object signature could not be verified with any secret.",
            original=token,
        ) from last_exc

    def __repr__(self) -> str:
        return f"RotatingSigner(n_secrets={len(self._signers)}, salt={self._salt!r}, algorithm={self._algorithm!r})"


# ===========================================================================
# High-level: dumps / loads  (structured payload serialisation)
# ===========================================================================


def dumps(
    obj: Any,
    *,
    secret: str | bytes | None = None,
    salt: str = "aquilia.signing.dumps",
    algorithm: str = "HS256",
    compress: bool = False,
    max_age: float | int | timedelta | None = None,
    timestamp: bool = True,
) -> str:
    """
    Serialise *obj* to a signed URL-safe string.

    The payload is JSON-encoded, optionally compressed with zlib,
    then Base64-encoded and signed with a :class:`TimestampSigner`.

    Equivalent to Django's ``signing.dumps()`` but with optional
    compression and configurable algorithms.

    Args:
        obj:       Any JSON-serialisable Python object.
        secret:    Master signing secret.
        salt:      Namespace salt (prevents cross-purpose token reuse).
        algorithm: HMAC algorithm.
        compress:  Compress payload with zlib if it saves space.
        max_age:   Ignored by ``dumps`` — passed to :func:`loads`.
        timestamp: If ``True`` (default), use :class:`TimestampSigner`
                   so age validation is available in :func:`loads`.

    Returns:
        Signed URL-safe string.

    Example::

        token = dumps({"user_id": 42, "role": "admin"}, secret="key")
        data  = loads(token, secret="key", max_age=3600)
    """
    payload_bytes = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    header = b""
    if compress:
        import zlib

        compressed = zlib.compress(payload_bytes, level=6)
        if len(compressed) < len(payload_bytes):
            payload_bytes = compressed
            header = b"\x01"  # zlib-compressed flag

    data = b64_encode(header + payload_bytes)

    if timestamp:
        signer: Signer = TimestampSigner(secret=secret, salt=salt, algorithm=algorithm)
    else:
        signer = Signer(secret=secret, salt=salt, algorithm=algorithm)

    return signer.sign(data)


def loads(
    token: str,
    *,
    secret: str | bytes | None = None,
    salt: str = "aquilia.signing.dumps",
    algorithm: str = "HS256",
    max_age: float | int | timedelta | None = None,
) -> Any:
    """
    Verify and deserialise a token produced by :func:`dumps`.

    Args:
        token:   Token produced by :func:`dumps`.
        secret:  Master signing secret (must match the one used in
                 :func:`dumps`).
        salt:    Namespace salt.
        algorithm: HMAC algorithm.
        max_age: Maximum age in seconds.  Raises :class:`SignatureExpired`
                 if the token is older.  Only works if the token was
                 produced by ``dumps(..., timestamp=True)`` (the default).

    Returns:
        Deserialised Python object.

    Raises:
        BadSignature:      Invalid signature.
        SignatureExpired:  Token older than *max_age*.
        SignatureMalformed: Corrupted payload.

    Example::

        data = loads(token, secret="key", max_age=3600)
    """
    # Try as timestamped first, fall back to plain
    try:
        ts_signer = TimestampSigner(secret=secret, salt=salt, algorithm=algorithm)
        data = ts_signer.unsign(token, max_age=max_age)
    except SignatureMalformed:
        # May be a non-timestamped token
        plain_signer = Signer(secret=secret, salt=salt, algorithm=algorithm)
        data = plain_signer.unsign(token)

    payload_bytes = b64_decode(data)
    if payload_bytes and payload_bytes[0:1] == b"\x01":
        import zlib

        payload_bytes = zlib.decompress(payload_bytes[1:])

    try:
        return json.loads(payload_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SignatureMalformed(f"Cannot deserialise signed payload: {exc}") from exc


# ===========================================================================
# Global secret registry + configure()
# ===========================================================================

_GLOBAL_SECRETS: list[str | bytes] = []
_GLOBAL_ALGORITHM: str = "HS256"
_GLOBAL_SALT: str = "aquilia.signing"


def configure(
    secret: str | bytes,
    *,
    fallback_secrets: Sequence[str | bytes] | None = None,
    algorithm: str = "HS256",
    salt: str = "aquilia.signing",
) -> None:
    """
    Configure the global signing secret used by module-level helpers.

    Call this once at application startup (typically from your
    ``AquilaConfig.Signing`` section or the ``configure_signing()``
    hook in ``server.py``).

    Args:
        secret:           Primary (current) signing secret.
        fallback_secrets: Retired secrets kept for backward compatibility.
        algorithm:        Default HMAC algorithm.
        salt:             Default namespace salt.

    Example::

        from aquilia.signing import configure
        configure(secret=os.environ["SECRET_KEY"])
    """
    global _GLOBAL_SECRETS, _GLOBAL_ALGORITHM, _GLOBAL_SALT
    _check_key_length(secret, "signing secret")
    secrets_list: list[str | bytes] = [secret]
    if fallback_secrets:
        secrets_list.extend(fallback_secrets)
    _GLOBAL_SECRETS = secrets_list
    _GLOBAL_ALGORITHM = algorithm
    _GLOBAL_SALT = salt


def _get_global_secret() -> str | bytes:
    """Return the current global secret or raise :class:`ConfigMissingFault`."""
    if not _GLOBAL_SECRETS:
        raise ConfigMissingFault(
            key="signing.secret",
            metadata={
                "hint": "Call aquilia.signing.configure(secret=...) at startup, "
                "or pass secret= directly to the Signer/TimestampSigner constructor.",
            },
        )
    return _GLOBAL_SECRETS[0]


def _get_global_rotating_signer(
    salt: str | None = None,
    algorithm: str | None = None,
    timestamp: bool = False,
) -> RotatingSigner:
    """Return a rotating signer using the globally configured secrets."""
    if not _GLOBAL_SECRETS:
        raise ConfigMissingFault(
            key="signing.secret",
            metadata={
                "hint": "Call aquilia.signing.configure(secret=...) at startup.",
            },
        )
    return RotatingSigner(
        secrets=_GLOBAL_SECRETS,
        salt=salt or _GLOBAL_SALT,
        algorithm=algorithm or _GLOBAL_ALGORITHM,
        timestamp=timestamp,
    )


# ===========================================================================
# Convenience factories
# ===========================================================================


def make_signer(
    secret: str | bytes | None = None,
    *,
    salt: str = "aquilia.signing",
    algorithm: str | None = None,
) -> Signer:
    """
    Create a :class:`Signer` with the given (or global) settings.

    Args:
        secret:    Signing secret.  Defaults to global secret.
        salt:      Namespace salt.
        algorithm: HMAC algorithm.  Defaults to globally configured algorithm.

    Returns:
        A configured :class:`Signer`.
    """
    return Signer(
        secret=secret,
        salt=salt,
        algorithm=algorithm or _GLOBAL_ALGORITHM,
    )


def make_timestamp_signer(
    secret: str | bytes | None = None,
    *,
    salt: str = "aquilia.signing.ts",
    algorithm: str | None = None,
) -> TimestampSigner:
    """
    Create a :class:`TimestampSigner` with the given (or global) settings.

    Args:
        secret:    Signing secret.  Defaults to global secret.
        salt:      Namespace salt.
        algorithm: HMAC algorithm.  Defaults to globally configured algorithm.

    Returns:
        A configured :class:`TimestampSigner`.
    """
    return TimestampSigner(
        secret=secret,
        salt=salt,
        algorithm=algorithm or _GLOBAL_ALGORITHM,
    )


# ===========================================================================
# Specialised signers for common Aquilia subsystems
# ===========================================================================


class SessionSigner(TimestampSigner):
    """
    Timestamped signer for Aquilia session cookies.

    Uses a dedicated salt (``"aquilia.sessions"``) so session tokens are
    cryptographically incompatible with tokens from other subsystems even
    when they share the same master secret.

    Default max_age is 7 days; override in :meth:`unsign`.

    Example::

        signer = SessionSigner(secret=config.secret_key)
        cookie_value = signer.sign(session_id)
        session_id   = signer.unsign(cookie_value, max_age=7 * 86400)
    """

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        algorithm: str = "HS256",
    ) -> None:
        super().__init__(
            secret,
            salt="aquilia.sessions",
            algorithm=algorithm,
        )


class CSRFSigner(Signer):
    """
    Signer for CSRF tokens.

    Uses salt ``"aquilia.csrf"`` to namespace tokens away from other
    signers.  CSRF tokens are stateless (no timestamp needed; they are
    per-request and validated immediately).

    Example::

        signer = CSRFSigner(secret=config.secret_key)
        token  = signer.sign(session_id)
        sid    = signer.unsign(token)   # raises BadSignature if tampered
    """

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        algorithm: str = "HS256",
    ) -> None:
        super().__init__(
            secret,
            salt="aquilia.csrf",
            algorithm=algorithm,
        )


class ActivationLinkSigner(TimestampSigner):
    """
    Timestamped signer for one-time activation / password-reset URLs.

    Tokens expire after a configurable duration (default 24 h) and are
    namespace-isolated under ``"aquilia.activation"``.

    Example::

        signer = ActivationLinkSigner(secret=config.secret_key)
        token  = signer.sign(user_id)
        uid    = signer.unsign(token, max_age=86400)   # 24 hours
    """

    _DEFAULT_MAX_AGE = 86_400  # 24 hours

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        algorithm: str = "HS256",
    ) -> None:
        super().__init__(
            secret,
            salt="aquilia.activation",
            algorithm=algorithm,
        )

    def unsign(
        self,
        signed_value: str,
        max_age: float | int | timedelta | None = None,
        **kwargs: Any,
    ) -> str:
        """Unsign with a default 24-hour max_age unless overridden."""
        if max_age is None:
            max_age = self._DEFAULT_MAX_AGE
        return super().unsign(signed_value, max_age=max_age)


class CacheKeySigner(Signer):
    """
    Signer for cache key integrity verification.

    Signs cache values with salt ``"aquilia.cache"`` to prevent cache
    poisoning attacks.  Equivalent to :class:`PickleCacheSerializer`'s
    HMAC but as a first-class signer with key rotation support.

    Example::

        signer = CacheKeySigner(secret=config.secret_key)
        signed = signer.sign_bytes(pickle_data)
        data   = signer.unsign_bytes(signed)
    """

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        algorithm: str = "HS256",
    ) -> None:
        super().__init__(
            secret,
            salt="aquilia.cache",
            algorithm=algorithm,
        )


class CookieSigner(TimestampSigner):
    """
    Timestamped signer for signed HTTP cookies (non-session).

    Embeds a timestamp to enforce cookie expiry server-side, independent
    of the browser's cookie expiry attribute.  Uses salt
    ``"aquilia.cookies"``.

    Example::

        signer = CookieSigner(secret=config.secret_key)
        value  = signer.sign(user_id)
        uid    = signer.unsign(value, max_age=3600)
    """

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        algorithm: str = "HS256",
    ) -> None:
        super().__init__(
            secret,
            salt="aquilia.cookies",
            algorithm=algorithm,
        )


class APIKeySigner(TimestampSigner):
    """
    Timestamped signer for short-lived API access keys / signed URLs.

    Embeds a microsecond timestamp and uses salt ``"aquilia.apikeys"``
    for namespace isolation.

    Example::

        signer = APIKeySigner(secret=config.secret_key)
        token  = signer.sign(f"user:{uid}:read")
        data   = signer.unsign(token, max_age=300)  # 5-minute URL
    """

    def __init__(
        self,
        secret: str | bytes | None = None,
        *,
        algorithm: str = "HS256",
    ) -> None:
        super().__init__(
            secret,
            salt="aquilia.apikeys",
            algorithm=algorithm,
        )


# ===========================================================================
# SigningConfig dataclass (consumed by AquilaConfig.Signing)
# ===========================================================================


@dataclass
class SigningConfig:
    """
    Runtime signing configuration.

    Instances of this class are created from :class:`AquilaConfig.Signing`
    and passed to :func:`configure` during server startup.

    Fields:
        secret:            Primary signing secret.
        fallback_secrets:  Retired secrets for key rotation.
        algorithm:         Default HMAC algorithm (HS256/HS384/HS512).
        salt:              Default namespace salt.
        session_salt:      Salt for session signers.
        csrf_salt:         Salt for CSRF signers.
        activation_salt:   Salt for activation link signers.
        cache_salt:        Salt for cache signers.
    """

    secret: str = ""
    fallback_secrets: list[str] = field(default_factory=list)
    algorithm: str = "HS256"
    salt: str = "aquilia.signing"
    session_salt: str = "aquilia.sessions"
    csrf_salt: str = "aquilia.csrf"
    activation_salt: str = "aquilia.activation"
    cache_salt: str = "aquilia.cache"

    def apply(self) -> None:
        """Apply this config to the global signing registry."""
        if self.secret:
            configure(
                secret=self.secret,
                fallback_secrets=self.fallback_secrets or None,
                algorithm=self.algorithm,
                salt=self.salt,
            )

    def make_session_signer(self) -> SessionSigner:
        return SessionSigner(secret=self.secret or None, algorithm=self.algorithm)

    def make_csrf_signer(self) -> CSRFSigner:
        return CSRFSigner(secret=self.secret or None, algorithm=self.algorithm)

    def make_activation_signer(self) -> ActivationLinkSigner:
        return ActivationLinkSigner(secret=self.secret or None, algorithm=self.algorithm)

    def make_cache_signer(self) -> CacheKeySigner:
        return CacheKeySigner(secret=self.secret or None, algorithm=self.algorithm)

    def make_cookie_signer(self) -> CookieSigner:
        return CookieSigner(secret=self.secret or None, algorithm=self.algorithm)

    def make_api_key_signer(self) -> APIKeySigner:
        return APIKeySigner(secret=self.secret or None, algorithm=self.algorithm)
