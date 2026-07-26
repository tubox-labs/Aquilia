"""
AquilaCache -- DI provider registration.

Registers CacheService and backend in Aquilia's DI container
for seamless injection into controllers and services.
"""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from aquilia.faults.domains import ConfigInvalidFault

from .backends.memory import MemoryBackend
from .backends.null import NullBackend
from .core import CacheBackend, CacheConfig
from .service import CacheService

logger = logging.getLogger("aquilia.cache.di")


def create_cache_backend(config: CacheConfig) -> CacheBackend:
    """
    Factory: create cache backend from configuration.

    Args:
        config: CacheConfig instance

    Returns:
        Configured CacheBackend

    Raises:
        ConfigInvalidFault: If ``config.backend`` is unknown, or if
            ``serializer="pickle"`` is requested without a
            ``serializer_secret_key``.

    Usage::

        backend = create_cache_backend(CacheConfig(backend="redis"))
    """
    backend_type = config.backend.lower()

    if backend_type == "memory":
        return MemoryBackend(
            max_size=config.max_size,
            eviction_policy=config.eviction_policy,
            capacity_warning_threshold=config.capacity_warning_threshold,
        )

    elif backend_type == "redis":
        from .backends.redis import RedisBackend

        return RedisBackend(
            url=config.redis_url,
            max_connections=config.redis_max_connections,
            socket_timeout=config.redis_socket_timeout,
            connect_timeout=config.redis_socket_connect_timeout,
            retry_on_timeout=config.redis_retry_on_timeout,
            key_prefix=config.key_prefix,
            serializer=_build_serializer(config),
        )

    elif backend_type == "composite":
        from .backends.composite import CompositeBackend

        l1 = MemoryBackend(
            max_size=config.l1_max_size,
            eviction_policy=config.eviction_policy,
            capacity_warning_threshold=config.capacity_warning_threshold,
        )

        if config.l2_backend == "redis":
            from .backends.redis import RedisBackend

            l2 = RedisBackend(
                url=config.redis_url,
                max_connections=config.redis_max_connections,
                key_prefix=config.key_prefix,
                serializer=_build_serializer(config),
            )
        else:
            l2 = MemoryBackend(max_size=config.max_size)

        return CompositeBackend(
            l1=l1,
            l2=l2,
            async_l2_write=config.l2_async_write,
        )

    elif backend_type == "null":
        return NullBackend()

    else:
        raise ConfigInvalidFault(
            key="cache.backend",
            reason=f"Unknown cache backend: {backend_type}",
        )


def _build_serializer(config: CacheConfig) -> object:
    """
    Build the configured serializer, supplying the HMAC key when required.

    Args:
        config: Cache configuration.

    Returns:
        A serializer exposing ``serialize``/``deserialize``.

    Raises:
        ConfigInvalidFault: If ``serializer="pickle"`` is configured without
            ``serializer_secret_key``, since unsigned pickle payloads are a
            remote-code-execution vector.
    """
    from .serializers import get_serializer

    secret = config.serializer_secret_key or None
    if config.serializer == "pickle" and not secret:
        raise ConfigInvalidFault(
            key="cache.serializer_secret_key",
            reason=(
                "serializer='pickle' requires cache.serializer_secret_key. "
                "The key HMAC-signs cached payloads so tampered data is never "
                "unpickled. Use the application secret or a dedicated cache key, "
                "or switch to serializer='json' / 'msgpack'."
            ),
        )
    return get_serializer(config.serializer, secret_key=secret)


def create_cache_service(config: CacheConfig) -> CacheService:
    """
    Factory: create CacheService from configuration.

    Args:
        config: CacheConfig instance

    Returns:
        Configured CacheService
    """
    backend = create_cache_backend(config)
    return CacheService(backend=backend, config=config)


def build_cache_config(config_dict: dict[str, Any]) -> CacheConfig:
    """
    Build CacheConfig from dictionary (e.g., from ConfigLoader).

    Args:
        config_dict: Raw configuration dictionary

    Returns:
        CacheConfig instance
    """
    return CacheConfig(
        enabled=config_dict.get("enabled", True),
        backend=config_dict.get("backend", "memory"),
        default_ttl=config_dict.get("default_ttl", 300),
        max_size=config_dict.get("max_size", 10000),
        eviction_policy=config_dict.get("eviction_policy", "lru"),
        namespace=config_dict.get("namespace", "default"),
        key_prefix=config_dict.get("key_prefix", "aq:"),
        key_builder=config_dict.get("key_builder", "default"),
        serializer=config_dict.get("serializer", "json"),
        serializer_secret_key=config_dict.get("serializer_secret_key", ""),
        ttl_jitter=config_dict.get("ttl_jitter", True),
        ttl_jitter_percent=config_dict.get("ttl_jitter_percent", 0.1),
        stampede_prevention=config_dict.get("stampede_prevention", True),
        stampede_timeout=config_dict.get("stampede_timeout", 30.0),
        distributed_stampede_lock=config_dict.get("distributed_stampede_lock", True),
        stampede_lock_ttl=config_dict.get("stampede_lock_ttl", 30.0),
        stampede_poll_interval=config_dict.get("stampede_poll_interval", 0.05),
        health_check_interval=config_dict.get("health_check_interval", 60.0),
        capacity_warning_threshold=config_dict.get("capacity_warning_threshold", 0.85),
        key_version=config_dict.get("key_version", 1),
        redis_url=config_dict.get("redis_url", "redis://localhost:6379/0"),
        redis_max_connections=config_dict.get("redis_max_connections", 10),
        redis_socket_timeout=config_dict.get("redis_socket_timeout", 5.0),
        redis_socket_connect_timeout=config_dict.get("redis_socket_connect_timeout", 5.0),
        redis_retry_on_timeout=config_dict.get("redis_retry_on_timeout", True),
        redis_decode_responses=config_dict.get("redis_decode_responses", True),
        l1_max_size=config_dict.get("l1_max_size", 1000),
        l1_ttl=config_dict.get("l1_ttl", 60),
        l2_backend=config_dict.get("l2_backend", "redis"),
        l2_async_write=config_dict.get("l2_async_write", False),
        middleware_enabled=config_dict.get("middleware_enabled", False),
        middleware_cacheable_methods=tuple(config_dict.get("middleware_cacheable_methods", ("GET", "HEAD"))),
        middleware_default_ttl=config_dict.get("middleware_default_ttl", 60),
        middleware_vary_headers=tuple(config_dict.get("middleware_vary_headers", ("Accept", "Accept-Encoding"))),
        middleware_stale_while_revalidate=config_dict.get("middleware_stale_while_revalidate", 0),
        trace_enabled=config_dict.get("trace_enabled", True),
        metrics_enabled=config_dict.get("metrics_enabled", True),
        log_level=config_dict.get("log_level", "WARNING"),
    )


def register_cache_providers(container: Any, cache_service: CacheService) -> None:
    """
    Register cache providers in a DI container.

    Args:
        container: Aquilia DI Container
        cache_service: Configured CacheService instance
    """
    from aquilia.di.providers import ValueProvider
    from aquilia.faults.domains import DIFault

    # Register the CacheService singleton
    try:
        container.register(
            ValueProvider(
                value=cache_service,
                token=CacheService,
                scope="app",
                name="cache_service",
            )
        )
    except DIFault:
        pass  # Already registered

    # Register the backend for direct access
    with contextlib.suppress(DIFault):
        container.register(
            ValueProvider(
                value=cache_service.backend,
                token=CacheBackend,
                scope="app",
                name="cache_backend",
            )
        )

    # Register by string token for compatibility
    with contextlib.suppress(DIFault):
        container.register(
            ValueProvider(
                value=cache_service,
                token="aquilia.cache.CacheService",
                scope="app",
                name="cache_service_str",
            )
        )
