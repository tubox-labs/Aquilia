"""
Integrity — HMAC-SHA256 signing and verification for artifact envelopes.

Provides tamper detection (not just corruption detection) for artifacts
that need it — principally the frozen registry manifest and schema
snapshots.  Plain corruption detection (via the ``fingerprint`` field in
the envelope) is sufficient for disposable caches like the discovery
cache and MCP knowledge index.

Security note
-------------
HMAC here is an integrity control, not a full security boundary.  An
adversary with filesystem write access can regenerate a valid HMAC if
they can read the key.  The key is derived from ``AQUILIA_CACHE_SECRET``
(if set) or a path-derived fallback that is *not* secret.  Do not
use HMAC signing as a substitute for filesystem access controls.

Key derivation
--------------
1. ``AQUILIA_CACHE_SECRET`` environment variable (highest priority)
2. Caller-supplied ``secret_key`` parameter
3. Path-derived fallback: ``sha256(str(artifact_path))`` — changes when
   the artifact is moved, which is usually desirable for build caches.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path


def _derive_key(artifact_path: str | Path | None, *, secret_key: str | None = None) -> str:
    """
    Derive an HMAC key.

    Priority:
    1. ``AQUILIA_CACHE_SECRET`` env var
    2. ``secret_key`` parameter
    3. Path-derived fallback
    """
    env_secret = os.environ.get("AQUILIA_CACHE_SECRET")
    if env_secret:
        return env_secret
    if secret_key:
        return secret_key
    if artifact_path is not None:
        return hashlib.sha256(str(Path(artifact_path).resolve()).encode()).hexdigest()
    return hashlib.sha256(b"aquilia-artifact-default-fallback").hexdigest()


def sign_payload(
    payload_bytes: bytes,
    *,
    artifact_path: str | Path | None = None,
    secret_key: str | None = None,
) -> str:
    """
    Compute HMAC-SHA256 of ``payload_bytes``.

    Parameters
    ----------
    payload_bytes
        The serialised artifact bytes to sign.
    artifact_path
        Used for path-derived key fallback.
    secret_key
        Explicit HMAC key (overrides path fallback, overridden by env var).

    Returns
    -------
    str
        64-character lowercase hex HMAC digest.
    """
    key = _derive_key(artifact_path, secret_key=secret_key)
    mac = hmac.new(key.encode(), payload_bytes, hashlib.sha256)
    return mac.hexdigest()


def verify_payload(
    payload_bytes: bytes,
    expected_mac: str,
    *,
    artifact_path: str | Path | None = None,
    secret_key: str | None = None,
) -> bool:
    """
    Verify ``payload_bytes`` against a stored HMAC.

    Uses :func:`hmac.compare_digest` for constant-time comparison.

    Parameters
    ----------
    payload_bytes
        The serialised artifact bytes to verify.
    expected_mac
        The HMAC stored in the envelope's ``hmac_signature`` field.
    artifact_path
        Used for path-derived key fallback.
    secret_key
        Explicit HMAC key.

    Returns
    -------
    bool
        ``True`` if the HMAC matches, ``False`` otherwise.
    """
    key = _derive_key(artifact_path, secret_key=secret_key)
    actual_mac = hmac.new(key.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(actual_mac, expected_mac)


def file_format_sign(
    payload_bytes: bytes, *, artifact_path: str | Path | None = None, secret_key: str | None = None
) -> bytes:
    """
    Produce the on-disk format used by :class:`JSONFileBackend` for signed artifacts.

    Format::

        <64-char HMAC hex>\\n<JSON bytes>

    This mirrors the format established by ``JSONBytecodeCache._save()``
    so that migrating the template bytecode cache onto :class:`JSONFileBackend`
    produces identical on-disk files.

    Returns
    -------
    bytes
        ``hmac_hex + b'\\n' + payload_bytes``
    """
    mac = sign_payload(payload_bytes, artifact_path=artifact_path, secret_key=secret_key)
    return mac.encode() + b"\n" + payload_bytes


def file_format_verify(raw: bytes, *, artifact_path: str | Path | None = None, secret_key: str | None = None) -> bytes:
    """
    Verify and strip the HMAC header from a raw signed file.

    Parameters
    ----------
    raw
        Raw bytes read from a signed artifact file.
    artifact_path
        Used for key derivation.
    secret_key
        Explicit HMAC key.

    Returns
    -------
    bytes
        The JSON payload bytes (after the HMAC header line).

    Raises
    ------
    ValueError
        If the format is wrong (no newline at position 64) or the HMAC
        does not match.
    """
    newline_pos = raw.find(b"\n")
    if newline_pos < 0 or newline_pos != 64:
        raise ValueError("Signed artifact has invalid HMAC header format")

    stored_mac = raw[:newline_pos].decode()
    payload_bytes = raw[newline_pos + 1 :]

    if not verify_payload(payload_bytes, stored_mac, artifact_path=artifact_path, secret_key=secret_key):
        raise ValueError("Artifact HMAC verification failed — content may be corrupted or tampered")

    return payload_bytes
