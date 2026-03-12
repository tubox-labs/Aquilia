"""
CacheIntegration — typed cache configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheIntegration:
    """
    Typed cache subsystem configuration.

    Example::

        CacheIntegration(backend="redis", redis_url="redis://cache:6379/0")
    """

    _integration_type: str = field(default="cache", init=False, repr=False)

    backend: str = "memory"
    default_ttl: int = 300
    max_size: int = 10000
    eviction_policy: str = "lru"
    namespace: str = "default"
    key_prefix: str = "aq:"
    serializer: str = "json"
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 10
    l1_max_size: int = 1000
    l1_ttl: int = 60
    l2_backend: str = "redis"
    middleware_enabled: bool = False
    middleware_default_ttl: int = 60
    enabled: bool = True

    def __post_init__(self) -> None:
        valid_backends = ("memory", "redis", "composite", "null")
        if self.backend not in valid_backends:
            raise ValueError(f"Invalid cache backend {self.backend!r}. Must be one of {valid_backends}")
        valid_policies = ("lru", "lfu", "fifo", "ttl", "random")
        if self.eviction_policy not in valid_policies:
            raise ValueError(f"Invalid eviction policy {self.eviction_policy!r}. Must be one of {valid_policies}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "cache",
            "enabled": self.enabled,
            "backend": self.backend,
            "default_ttl": self.default_ttl,
            "max_size": self.max_size,
            "eviction_policy": self.eviction_policy,
            "namespace": self.namespace,
            "key_prefix": self.key_prefix,
            "serializer": self.serializer,
            "redis_url": self.redis_url,
            "redis_max_connections": self.redis_max_connections,
            "l1_max_size": self.l1_max_size,
            "l1_ttl": self.l1_ttl,
            "l2_backend": self.l2_backend,
            "middleware_enabled": self.middleware_enabled,
            "middleware_default_ttl": self.middleware_default_ttl,
        }
