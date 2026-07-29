"""
Bytecode Cache - Template compilation caching system.

Supports:
- In-memory cache (dev/testing)
- JSON-backed persistent cache (production)
- Optional Redis cache (high-throughput deployments)
"""

import base64
import contextlib
import hashlib
import json
import os
import warnings
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import BytecodeCache as Jinja2BytecodeCache
from jinja2.bccache import Bucket


class BytecodeCache(Jinja2BytecodeCache):
    """
    Abstract base for bytecode caching.

    Implements Jinja2's BytecodeCache interface with async extensions.
    """

    async def load_bytecode_async(self, key: str) -> bytes | None:
        """Load bytecode asynchronously (optional optimization)."""
        return self.load_bytecode(key)

    async def store_bytecode_async(self, key: str, data: bytes) -> None:
        """Store bytecode asynchronously (optional optimization)."""
        self.dump_bytecode(data)

    async def clear_async(self) -> None:
        """Clear cache asynchronously."""
        self.clear()


class InMemoryBytecodeCache(BytecodeCache):
    """
    In-memory bytecode cache.

    Fast, non-persistent cache for development and testing.
    LRU eviction with configurable capacity.

    Args:
        capacity: Maximum number of compiled templates to cache
    """

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self._cache: dict[str, bytes] = {}
        self._access_order: list[str] = []

    def load_bytecode(self, bucket: Bucket) -> None:
        """Load bytecode from cache."""
        key = bucket.key
        if key in self._cache:
            # Update access order
            self._access_order.remove(key)
            self._access_order.append(key)

            bucket.bytecode_from_string(self._cache[key])

    def dump_bytecode(self, bucket: Bucket) -> None:
        """Store bytecode in cache."""
        key = bucket.key
        bytecode = bucket.bytecode_to_string()

        # Check capacity
        if len(self._cache) >= self.capacity and key not in self._cache:
            # Evict least recently used
            if self._access_order:
                evict_key = self._access_order.pop(0)
                del self._cache[evict_key]

        self._cache[key] = bytecode

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def clear(self) -> None:
        """Clear all cached bytecode."""
        self._cache.clear()
        self._access_order.clear()

    def invalidate(self, key: str) -> None:
        """Invalidate specific template cache."""
        if key in self._cache:
            del self._cache[key]
            self._access_order.remove(key)


class JSONBytecodeCache(BytecodeCache):
    """
    JSON artifact-backed bytecode cache.

    Stores compiled templates in artifacts/templates.bytecode.json
    with fingerprinting and atomic writes via the ArtifactStore backend.

    Envelope format:
    {
        "format": "aquilia-artifact",
        "schema_version": "1.1",
        "artifact_type": "template_bytecode",
        "fingerprint": "sha256:...",
        "created_at": "2026-01-26T...",
        "payload": {
            "bytecode": {
                "template_key": "base64_bytecode",
                ...
            },
            "metadata": {
                "template_key": {
                    "source_path": "...",
                    "source_hash": "sha256:...",
                    "compiled_at": "2026-01-26T...",
                    "size": 12345
                },
                ...
            }
        }
    }

    Args:
        cache_dir: Directory to store cache files
        filename: Cache file name (default: templates.bytecode.json)
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        filename: str = "templates.bytecode.json",
        secret_key: str | None = None,
    ):
        # Resolve canonical artifact root if not explicitly specified.
        # Default: <project>/.aquilia/artifacts (never the legacy "artifacts/" dir).
        if cache_dir is None:
            from aquilia.artifacts.cache_root import resolve_artifact_root

            cache_dir = str(resolve_artifact_root())
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / filename

        # HMAC secret for integrity verification
        self._secret_key = (
            secret_key
            or os.environ.get("AQUILIA_CACHE_SECRET")
            or hashlib.sha256(str(self.cache_file.resolve()).encode()).hexdigest()
        )

        # In-memory cache for performance
        self._cache: dict[str, bytes] = {}
        self._metadata: dict[str, dict] = {}
        self._dirty = False

        # Backend — delegates all serialization + atomic IO
        from aquilia.artifacts.backends.json_file import JSONFileBackend

        self._backend = JSONFileBackend()

        # Load existing cache
        self._load()

    def load_bytecode(self, bucket: Bucket) -> None:
        """Load bytecode from cache."""
        key = bucket.key
        if key in self._cache:
            bucket.bytecode_from_string(self._cache[key])

    def dump_bytecode(self, bucket: Bucket) -> None:
        """Store bytecode in cache."""
        key = bucket.key
        bytecode = bucket.bytecode_to_string()

        self._cache[key] = bytecode
        self._metadata[key] = {
            "source_hash": self._compute_key_hash(key),
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "size": len(bytecode),
        }
        self._dirty = True

    def clear(self) -> None:
        """Clear all cached bytecode."""
        self._cache.clear()
        self._metadata.clear()
        self._dirty = True
        self._save()

    def invalidate(self, key: str) -> None:
        """Invalidate specific template cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._metadata:
                del self._metadata[key]
            self._dirty = True

    def save(self) -> None:
        """Persist cache to disk."""
        if self._dirty:
            self._save()
            self._dirty = False

    def _load(self) -> None:
        """Load cache from disk via ArtifactStore backend (with HMAC verification)."""
        try:
            raw = self._backend.read_sync(
                self.cache_file,
                signed=True,
                artifact_path_for_key=self.cache_file,
                secret_key=self._secret_key,
            )
            if raw is None:
                return

            # Parse envelope — support ArtifactEnvelope format and legacy format
            from aquilia.artifacts.envelope import ArtifactEnvelope

            if raw.get("format") == "aquilia-artifact":
                try:
                    envelope = ArtifactEnvelope.from_dict(raw)
                    payload = envelope.payload
                except Exception:
                    payload = raw.get("payload", {})
            else:
                # Legacy format: __format__ == "json" with payload key
                if not isinstance(raw, dict) or raw.get("__format__") not in ("json", None):
                    return
                payload = raw.get("payload", {})

            # Load bytecode (base64 → bytes)
            bytecode_data = payload.get("bytecode", {})
            for key, encoded in bytecode_data.items():
                with contextlib.suppress(Exception):
                    self._cache[key] = base64.b64decode(encoded)

            # Load metadata
            self._metadata = payload.get("metadata", {})

        except Exception:
            # Cache load failed or integrity check failed, emit warning and start fresh
            warnings.warn(
                f"Bytecode cache {self.cache_file} failed integrity check, ignoring",
                stacklevel=2,
            )
            self._cache.clear()
            self._metadata.clear()

    def _save(self) -> None:
        """Save cache to disk via ArtifactStore backend (atomic write + HMAC signing)."""
        from aquilia.artifacts.envelope import ArtifactEnvelope

        # Build payload — bytecode encoded as base64 for JSON safety
        bytecode_encoded = {key: base64.b64encode(raw_bytes).decode("ascii") for key, raw_bytes in self._cache.items()}

        payload = {
            "bytecode": bytecode_encoded,
            "metadata": self._metadata.copy(),
        }

        fingerprint = self._compute_fingerprint()
        envelope = ArtifactEnvelope.build(
            artifact_type="template_bytecode",
            key="main",
            schema_version="1.1",
            payload=payload,
            fingerprint=fingerprint,
            signed=True,
        )

        # Delegate atomic write + HMAC signing to backend
        # (removed inline hmac/json/tempfile/os.replace duplication)
        self._backend.write_sync(
            self.cache_file,
            envelope.to_dict(),
            signed=True,
            artifact_path_for_key=self.cache_file,
            secret_key=self._secret_key,
        )

    def _compute_fingerprint(self) -> str:
        """Compute cache fingerprint."""
        # Hash all template keys and their source hashes
        items = sorted((key, meta.get("source_hash", "")) for key, meta in self._metadata.items())
        canonical = json.dumps(items, separators=(",", ":"))
        hash_digest = hashlib.sha256(canonical.encode()).hexdigest()
        return f"sha256:{hash_digest}"

    def _compute_key_hash(self, key: str) -> str:
        """Compute hash of template key."""
        hash_digest = hashlib.sha256(key.encode()).hexdigest()
        return f"sha256:{hash_digest}"


class RedisBytecodeCache(BytecodeCache):
    """
    Redis-backed bytecode cache for high-throughput deployments.

    Requires redis-py (optional dependency).

    Args:
        redis_url: Redis connection URL
        key_prefix: Key prefix for cache entries
        ttl: Cache entry TTL in seconds (None = no expiration)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "aquilia:templates:",
        ttl: int | None = None,
    ):
        try:
            import redis.asyncio as aioredis

            self._redis_module = aioredis
        except ImportError:
            raise ImportError("Redis cache requires redis-py. Install with: pip install redis")

        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.ttl = ttl
        self._redis = None

    async def _get_redis(self):
        """Get Redis connection (lazy)."""
        if self._redis is None:
            self._redis = await self._redis_module.from_url(self.redis_url)
        return self._redis

    def load_bytecode(self, bucket: Bucket) -> None:
        """Load bytecode from Redis (sync wrapper)."""
        # Sync loading not ideal for Redis, but required by Jinja2 interface
        # In practice, use async methods
        pass

    def dump_bytecode(self, bucket: Bucket) -> None:
        """Store bytecode in Redis (sync wrapper)."""
        # Sync dumping not ideal for Redis, but required by Jinja2 interface
        pass

    async def load_bytecode_async(self, key: str) -> bytes | None:
        """Load bytecode from Redis asynchronously."""
        redis = await self._get_redis()
        cache_key = f"{self.key_prefix}{key}"
        data = await redis.get(cache_key)
        return data

    async def store_bytecode_async(self, key: str, data: bytes) -> None:
        """Store bytecode in Redis asynchronously."""
        redis = await self._get_redis()
        cache_key = f"{self.key_prefix}{key}"
        if self.ttl:
            await redis.setex(cache_key, self.ttl, data)
        else:
            await redis.set(cache_key, data)

    def clear(self) -> None:
        """Clear all cached bytecode."""
        # Sync clear not ideal for Redis
        pass

    async def clear_async(self) -> None:
        """Clear all cached bytecode asynchronously."""
        redis = await self._get_redis()
        pattern = f"{self.key_prefix}*"
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
