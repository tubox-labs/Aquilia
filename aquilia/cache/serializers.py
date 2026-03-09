"""
AquilaCache -- Pluggable serializers for cache value encoding.

Supports JSON (default), pickle (fast, Python-only), and msgpack
(compact, cross-language). All serializers include structured error
handling and logging for serialization failures.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from aquilia.faults.domains import CacheFault, ConfigInvalidFault, SecurityFault

logger = logging.getLogger("aquilia.cache.serializers")


class JsonCacheSerializer:
    """
    JSON serializer -- safe, human-readable, cross-language.
    
    Default serializer. Handles most Python primitives and
    containers (dict, list, str, int, float, bool, None).
    Falls back to ``str()`` for non-serializable types.
    """
    
    def serialize(self, value: Any) -> bytes:
        """Serialize value to JSON bytes."""
        try:
            return json.dumps(value, default=str, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError, OverflowError) as e:
            logger.warning(f"JSON serialization failed: {e}")
            raise
    
    def deserialize(self, data: bytes) -> Any:
        """Deserialize JSON bytes to value."""
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"JSON deserialization failed: {e}")
            raise


class PickleCacheSerializer:
    """
    HMAC-signed pickle serializer -- supports arbitrary Python objects.

    **Security:** All serialized payloads are signed with HMAC-SHA256
    using the provided ``secret_key``. Deserialization verifies the
    signature *before* calling ``pickle.loads()``, preventing
    arbitrary-code-execution attacks from tampered cache data.

    A ``secret_key`` **must** be provided. If omitted, instantiation
    raises ``ValueError``.

    Format:  ``<32-byte HMAC> + <pickled payload>``
    """

    _HMAC_SIZE = 32  # SHA-256 digest length in bytes

    def __init__(self, *, secret_key: str | bytes | None = None) -> None:
        if not secret_key:
            raise ConfigInvalidFault(
                key="cache.pickle.secret_key",
                reason="PickleCacheSerializer requires a 'secret_key' argument. "
                "This key is used to HMAC-sign serialized data to prevent "
                "deserialization of tampered payloads. Pass the application "
                "secret key or a dedicated cache-signing key.",
            )
        self._key: bytes = (
            secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        )
        logger.warning(
            "PickleCacheSerializer is enabled. While payloads are now "
            "HMAC-signed, pickle remains a powerful deserialization vector. "
            "Prefer JsonCacheSerializer or MsgpackCacheSerializer unless you "
            "have a specific need for pickle's capabilities."
        )

    def _sign(self, payload: bytes) -> bytes:
        """Return HMAC-SHA256 of *payload*."""
        import hmac as _hmac
        import hashlib as _hashlib
        return _hmac.new(self._key, payload, _hashlib.sha256).digest()

    def serialize(self, value: Any) -> bytes:
        """Serialize value via pickle and prepend HMAC signature."""
        import pickle
        try:
            payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            signature = self._sign(payload)
            return signature + payload
        except (pickle.PicklingError, TypeError) as e:
            logger.warning(f"Pickle serialization failed: {e}")
            raise

    def deserialize(self, data: bytes) -> Any:
        """Verify HMAC signature, then deserialize pickle bytes."""
        import hmac as _hmac
        import pickle
        if len(data) < self._HMAC_SIZE:
            raise CacheFault(
                code="CACHE_PICKLE_MALFORMED",
                message="Pickle payload too short — missing HMAC signature.",
            )
        stored_sig = data[: self._HMAC_SIZE]
        payload = data[self._HMAC_SIZE :]
        expected_sig = self._sign(payload)
        if not _hmac.compare_digest(stored_sig, expected_sig):
            logger.error(
                "HMAC verification failed for pickle cache entry. "
                "The data may have been tampered with. Refusing to deserialize."
            )
            raise SecurityFault(
                code="CACHE_HMAC_TAMPERED",
                message="Pickle HMAC verification failed — refusing to deserialize "
                "potentially tampered data.",
            )
        try:
            return pickle.loads(payload)
        except (pickle.UnpicklingError, EOFError) as e:
            logger.warning(f"Pickle deserialization failed: {e}")
            raise


class MsgpackCacheSerializer:
    """
    MessagePack serializer -- compact binary, cross-language.
    
    Requires `msgpack` package: pip install msgpack
    """
    
    def serialize(self, value: Any) -> bytes:
        """Serialize value to msgpack bytes."""
        try:
            import msgpack
        except ImportError:
            raise ImportError(
                "MsgpackCacheSerializer requires 'msgpack' package. "
                "Install with: pip install msgpack"
            )
        try:
            return msgpack.packb(value, use_bin_type=True, default=str)
        except (TypeError, ValueError) as e:
            logger.warning(f"Msgpack serialization failed: {e}")
            raise
    
    def deserialize(self, data: bytes) -> Any:
        """Deserialize msgpack bytes."""
        try:
            import msgpack
        except ImportError:
            raise ImportError(
                "MsgpackCacheSerializer requires 'msgpack' package. "
                "Install with: pip install msgpack"
            )
        try:
            return msgpack.unpackb(data, raw=False)
        except Exception as e:
            logger.warning(f"Msgpack deserialization failed: {e}")
            raise


def get_serializer(name: str = "json", *, secret_key: str | bytes | None = None):
    """
    Factory for serializer instances.

    Args:
        name: "json", "pickle", or "msgpack"
        secret_key: Required when *name* is ``"pickle"``. Used to
                    HMAC-sign serialized payloads.

    Returns:
        CacheSerializer instance

    Raises:
        ValueError: If *name* is unknown or pickle is requested without
                    a *secret_key*.
    """
    if name == "pickle":
        return PickleCacheSerializer(secret_key=secret_key)

    serializers = {
        "json": JsonCacheSerializer,
        "msgpack": MsgpackCacheSerializer,
    }

    cls = serializers.get(name)
    if cls is None:
        raise ConfigInvalidFault(
            key="cache.serializer",
            reason=f"Unknown serializer: {name!r}. "
            f"Options: {['json', 'pickle', 'msgpack']}",
        )

    return cls()
