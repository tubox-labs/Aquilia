"""
Canonical serialization — deterministic, cross-platform JSON fingerprinting.

Generalises ``FingerprintGenerator._build_canonical_repr`` / ``_canonicalize_dict``
from ``aquilia.aquilary.fingerprint`` into a format-agnostic utility usable
by any artifact producer.

Design goals
------------
* **Deterministic** across Python versions, OSes, timezones, and dict
  insertion order.
* **Stable across schema additions**: new keys added to a payload do *not*
  change the fingerprint of existing artifacts when those keys are excluded
  via the ``exclude_keys`` parameter.
* **Explicit exclusions**: callers declare which keys to ignore (e.g.
  ``"created_at"``, ``"fingerprint"``, ``"hmac_signature"``).  This makes
  the exclusion contract visible at the call site, not buried in the hash
  function.
* **No external deps**: only ``hashlib`` and ``json``.

Usage::

    from aquilia.artifacts.canonical import canonicalize, fingerprint

    payload = {"apps": [...], "version": "1.0", "generated_at": "..."}
    fp = fingerprint(payload, exclude_keys={"generated_at"})
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

# Keys always excluded from fingerprinting unless the caller explicitly
# re-includes them by not passing exclude_keys.
_DEFAULT_EXCLUDE: frozenset[str] = frozenset(
    {
        # Envelope-level metadata — always changes across writes
        "created_at",
        "fingerprint",
        "hmac_signature",
        # Common timestamp aliases used by various artifact producers
        "generated_at",
        "updated_at",
        "timestamp",
    }
)


def canonicalize(
    obj: Any,
    *,
    exclude_keys: frozenset[str] | set[str] | None = None,
) -> bytes:
    """
    Produce a deterministic, UTF-8–encoded, sorted-key JSON representation
    of ``obj`` suitable for hashing.

    Parameters
    ----------
    obj
        Any JSON-serialisable value (dict, list, str, int, float, bool, None).
    exclude_keys
        Top-level *and recursive* dict keys to omit before serialising.
        Defaults to :data:`_DEFAULT_EXCLUDE`.

    Returns
    -------
    bytes
        UTF-8 JSON with sorted keys, no extra whitespace.
    """
    _excl = _DEFAULT_EXCLUDE if exclude_keys is None else frozenset(exclude_keys)
    canonical = _normalize(obj, _excl)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def fingerprint(
    obj: Any,
    *,
    exclude_keys: frozenset[str] | set[str] | None = None,
    prefix: str = "sha256:",
) -> str:
    """
    Compute a deterministic SHA-256 fingerprint of ``obj``.

    Parameters
    ----------
    obj
        Any JSON-serialisable value.
    exclude_keys
        Keys to exclude before hashing.  Defaults to :data:`_DEFAULT_EXCLUDE`.
    prefix
        String prepended to the hex digest.  Default ``"sha256:"``.
        Pass ``""`` for a bare hex digest (for backward compatibility with
        existing producers that used bare digests).

    Returns
    -------
    str
        ``prefix + sha256_hex_digest``.
    """
    raw = canonicalize(obj, exclude_keys=exclude_keys)
    digest = hashlib.sha256(raw).hexdigest()
    return f"{prefix}{digest}"


def bare_fingerprint(
    obj: Any,
    *,
    exclude_keys: frozenset[str] | set[str] | None = None,
) -> str:
    """
    Convenience wrapper: SHA-256 hex digest with no prefix.

    Matches the behaviour of the legacy ``_compute_checksum()`` in
    ``aquilia.models.schema_snapshot`` and the raw digest used by
    ``FingerprintGenerator.generate()``.
    """
    return fingerprint(obj, exclude_keys=exclude_keys, prefix="")


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────


def _normalize(obj: Any, exclude_keys: frozenset[str]) -> Any:
    """
    Recursively normalise ``obj`` for deterministic serialisation.

    - Dicts: keys are sorted; excluded keys are dropped.
    - Lists/tuples: elements are normalised in order; tuples become lists.
    - Sets: converted to sorted lists (natural ordering where possible).
    - Everything else: returned as-is (JSON encoder handles the rest).
    """
    if isinstance(obj, dict):
        return {k: _normalize(v, exclude_keys) for k, v in sorted(obj.items()) if k not in exclude_keys}

    if isinstance(obj, (list, tuple)):
        return [_normalize(item, exclude_keys) for item in obj]

    if isinstance(obj, set):
        # Best-effort sort; falls back to str() for mixed-type sets
        try:
            return sorted(_normalize(item, exclude_keys) for item in obj)
        except TypeError:
            return sorted(str(_normalize(item, exclude_keys)) for item in obj)

    return obj
