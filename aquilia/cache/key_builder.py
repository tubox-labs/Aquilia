"""
AquilaCache -- Cache key builder implementations.

Deterministic, collision-free key generation with namespace
isolation, optional hashing for long keys, and version support
for mass-invalidation.

A single builder instance is owned by :class:`~aquilia.cache.service.CacheService`
and shared with the decorator layer, so manual and declarative caching always
produce byte-identical keys.
"""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable

from aquilia.faults.domains import ConfigInvalidFault


@runtime_checkable
class KeyBuilder(Protocol):
    """
    Contract implemented by every cache key builder.

    Implementations must be deterministic: identical inputs always produce
    identical keys within a process and across restarts.

    Usage::

        def make(builder: KeyBuilder) -> str:
            return builder.build("users", "user:1", "aq:")
    """

    def build(self, namespace: str, key: str, prefix: str = "") -> str:
        """
        Build a fully-qualified cache key.

        Args:
            namespace: Logical namespace isolating this key.
            key: Caller-supplied key within the namespace.
            prefix: Global key prefix from configuration.

        Returns:
            The qualified key string.
        """
        ...

    def from_args(
        self,
        namespace: str,
        func_name: str,
        args: tuple[object, ...] = (),
        kwargs: dict[str, object] | None = None,
        prefix: str = "",
    ) -> str:
        """
        Build a cache key from a function call signature.

        Args:
            namespace: Logical namespace isolating this key.
            func_name: Qualified name of the called function.
            args: Positional call arguments.
            kwargs: Keyword call arguments.
            prefix: Global key prefix from configuration.

        Returns:
            The qualified key string.
        """
        ...


def call_signature(
    func_name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object] | None,
) -> str:
    """
    Render a deterministic, namespace-free signature for a function call.

    Args:
        func_name: Qualified function name.
        args: Positional arguments.
        kwargs: Keyword arguments (order-insensitive).

    Returns:
        A colon-separated signature such as ``mod.fn:1:2:limit=10``.
    """
    parts: list[str] = [func_name]

    if args:
        parts.append(":".join(str(a) for a in args))

    if kwargs:
        parts.append(":".join(f"{k}={v}" for k, v in sorted(kwargs.items())))

    return ":".join(p for p in parts if p)


class DefaultKeyBuilder:
    """
    Default key builder using colon-separated segments.

    Pattern: ``{prefix}v{version}:{namespace}:{key}``

    Example: ``aq:v1:users:user:123``

    Version support enables mass-invalidation by incrementing
    the version number in config, making all old keys invisible.

    Args:
        version: Key version.  When greater than zero the version is embedded
            in every key, so incrementing it invalidates the whole keyspace.

    Usage::

        builder = DefaultKeyBuilder(version=2)
        builder.build("users", "user:1", "aq:")  # 'aq:v2:users:user:1'
    """

    __slots__ = ("_version",)

    def __init__(self, version: int = 0) -> None:
        self._version = version

    @property
    def version(self) -> int:
        """Current key version; ``0`` means versioning is disabled."""
        return self._version

    def build(self, namespace: str, key: str, prefix: str = "") -> str:
        """
        Build a qualified cache key with an optional version segment.

        Args:
            namespace: Logical namespace isolating this key.
            key: Caller-supplied key within the namespace.
            prefix: Global key prefix from configuration.

        Returns:
            The qualified key string.
        """
        if self._version > 0:
            return f"{prefix}v{self._version}:{namespace}:{key}"
        return f"{prefix}{namespace}:{key}"

    def from_args(
        self,
        namespace: str,
        func_name: str,
        args: tuple[object, ...] = (),
        kwargs: dict[str, object] | None = None,
        prefix: str = "",
    ) -> str:
        """
        Build a cache key from function call arguments.

        Used by the ``@cached`` decorator for automatic key generation.
        The namespace is embedded exactly once, by ``build``.

        Args:
            namespace: Logical namespace isolating this key.
            func_name: Qualified name of the called function.
            args: Positional call arguments.
            kwargs: Keyword call arguments.
            prefix: Global key prefix from configuration.

        Returns:
            The qualified key string.
        """
        return self.build(namespace, call_signature(func_name, args, kwargs), prefix)


class HashKeyBuilder:
    """
    Hash-based key builder for long or complex keys.

    Uses SHA-256 to produce fixed-length keys, preventing
    issues with Redis key length limits or memory overhead.

    Pattern: ``{prefix}v{version}:{namespace}:{sha256_hex[:16]}``

    Args:
        hash_length: Length of the hex digest suffix (capped at 64).
        version: Key version for mass-invalidation.

    Usage::

        builder = HashKeyBuilder(hash_length=24, version=1)
        builder.build("reports", very_long_key, "aq:")
    """

    __slots__ = ("_hash_length", "_version")

    def __init__(self, hash_length: int = 16, version: int = 0) -> None:
        self._hash_length = min(hash_length, 64)
        self._version = version

    @property
    def version(self) -> int:
        """Current key version; ``0`` means versioning is disabled."""
        return self._version

    def build(self, namespace: str, key: str, prefix: str = "") -> str:
        """
        Build a hash-based cache key.

        Args:
            namespace: Logical namespace isolating this key.
            key: Caller-supplied key, hashed to a fixed length.
            prefix: Global key prefix from configuration.

        Returns:
            The qualified, hashed key string.
        """
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[: self._hash_length]
        if self._version > 0:
            return f"{prefix}v{self._version}:{namespace}:{key_hash}"
        return f"{prefix}{namespace}:{key_hash}"

    def from_args(
        self,
        namespace: str,
        func_name: str,
        args: tuple[object, ...] = (),
        kwargs: dict[str, object] | None = None,
        prefix: str = "",
    ) -> str:
        """
        Build a hashed key from function call arguments.

        Args:
            namespace: Logical namespace isolating this key.
            func_name: Qualified name of the called function.
            args: Positional call arguments.
            kwargs: Keyword call arguments.
            prefix: Global key prefix from configuration.

        Returns:
            The qualified, hashed key string.
        """
        return self.build(namespace, call_signature(func_name, args, kwargs), prefix)


def build_key_builder(strategy: str = "default", *, version: int = 0) -> KeyBuilder:
    """
    Create a key builder for the configured strategy.

    Args:
        strategy: ``"default"`` for colon-separated keys, ``"hash"`` for
            SHA-256 fixed-length keys.
        version: Key version for mass-invalidation.

    Returns:
        A ready-to-use :class:`KeyBuilder`.

    Raises:
        ConfigInvalidFault: If *strategy* is not recognised.

    Usage::

        builder = build_key_builder("hash", version=3)
    """
    if strategy == "default":
        return DefaultKeyBuilder(version=version)
    if strategy == "hash":
        return HashKeyBuilder(version=version)

    raise ConfigInvalidFault(
        key="cache.key_builder",
        reason=f"Unknown key builder strategy: {strategy!r}. Options: ['default', 'hash']",
    )


__all__: list[str] = [
    "DefaultKeyBuilder",
    "HashKeyBuilder",
    "KeyBuilder",
    "build_key_builder",
    "call_signature",
]
