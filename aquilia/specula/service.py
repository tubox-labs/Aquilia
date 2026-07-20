"""
SpeculaService — singleton DI service owning spec generation and caching.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aquilia.controller.router import ControllerRouter

from .config import SpeculaConfig
from .faults import SpecBuildFault, SpeculaFault
from .introspect.versions import VersionedSpecBuilder
from .schema.builder import SpeculaBuilder

logger = logging.getLogger("aquilia.specula")


class SpeculaService:
    """
    Singleton DI service for Aquilia Specula.

    Owns spec generation, in-process caching, CacheService integration, and
    SSE broadcast for live spec invalidation in dev mode.

    Cache priority in :meth:`get_spec`:
      1. In-process dict (sub-microsecond)
      2. CacheService (Redis / Memory backend)
      3. Fresh generation (guarded by an asyncio.Lock against thundering herd)
    """

    def __init__(
        self,
        router: ControllerRouter,
        config: SpeculaConfig,
        cache: Any = None,
        version_strategy: Any = None,
    ):
        self.router = router
        self.config = config
        self.cache = cache
        self._builder = SpeculaBuilder(config)
        self._versioned = VersionedSpecBuilder(config, version_strategy)
        self._process_cache: dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._sse_queues: list[asyncio.Queue] = []

    # ── Spec access ────────────────────────────────────────────────────

    async def get_spec(self, version: str | None = None) -> dict[str, Any]:
        """
        Get the OpenAPI 3.1.0 spec dict.

        Args:
            version: API version string, or None for the default/latest spec.
        """
        cache_key = self.config.spec_cache_key.format(version=version or "latest")

        # In-process cache hit (dict lookup, no IO)
        cached = self._process_cache.get(cache_key)
        if cached is not None:
            return cached

        # External cache
        if self.cache is not None and self.config.spec_cache_ttl > 0:
            try:
                raw = await self.cache.get(cache_key)
                if raw:
                    spec = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
                    self._process_cache[cache_key] = spec
                    return spec
            except Exception as exc:  # noqa: BLE001 — cache failures are non-fatal
                logger.warning("Specula: CacheService read failed (non-fatal): %s", exc)

        # Generate — lock prevents thundering herd
        async with self._lock:
            cached = self._process_cache.get(cache_key)
            if cached is not None:
                return cached
            return await self._generate_and_cache(version, cache_key)

    async def _generate_and_cache(self, version: str | None, cache_key: str) -> dict[str, Any]:
        try:
            if version:
                spec = self._versioned.build_for_version(self.router, version)
            else:
                spec = self._builder.build(self.router)
        except SpeculaFault:
            raise
        except Exception as exc:
            raise SpecBuildFault(
                f"Specula failed to build OpenAPI spec: {exc}",
                detail={"error": str(exc), "version": version},
            ) from exc

        self._process_cache[cache_key] = spec

        if self.cache is not None and self.config.spec_cache_ttl > 0:
            try:
                await self.cache.set(
                    cache_key,
                    json.dumps(spec, default=str),
                    ttl=self.config.spec_cache_ttl,
                )
            except Exception as exc:  # noqa: BLE001 — cache failures are non-fatal
                logger.warning("Specula: CacheService write failed (non-fatal): %s", exc)

        return spec

    async def get_spec_json(self, version: str | None = None) -> str:
        """Spec serialised as pretty JSON."""
        return json.dumps(await self.get_spec(version), indent=2, default=str)

    async def get_spec_yaml(self, version: str | None = None) -> str:
        """Spec serialised as YAML."""
        spec_dict = await self.get_spec(version)
        try:
            import yaml

            return yaml.dump(spec_dict, default_flow_style=False, allow_unicode=True)
        except ImportError:
            return self._to_simple_yaml(spec_dict)

    def _to_simple_yaml(self, data: Any, indent: int = 0) -> str:
        """Fallback lightweight YAML serializer when pyyaml is not installed."""

        def quote_str(s: str) -> str:
            special_chars = [
                ":",
                "{",
                "}",
                "[",
                "]",
                ",",
                "&",
                "*",
                "#",
                "?",
                "|",
                "-",
                "<",
                ">",
                "=",
                "!",
                "%",
                "@",
                "`",
            ]
            needs_quoting = (
                any(c in s for c in special_chars)
                or s == ""
                or s.lower() in ("true", "false", "null", "yes", "no")
                or s.strip() != s
                or s[0].isdigit()
            )
            if needs_quoting:
                return f'"{s.replace(chr(34), chr(92) + chr(34))}"'
            return s

        if data is None:
            return "null"
        elif isinstance(data, bool):
            return "true" if data else "false"
        elif isinstance(data, (int, float)):
            return str(data)
        elif isinstance(data, str):
            return quote_str(data)
        elif isinstance(data, dict):
            if not data:
                return "{}"
            lines = []
            for k, v in data.items():
                key_str = quote_str(str(k))
                if isinstance(v, (dict, list)):
                    if not v:
                        lines.append(f"{' ' * indent}{key_str}: {v == {} and '{}' or '[]'}")
                    else:
                        lines.append(f"{' ' * indent}{key_str}:")
                        lines.append(self._to_simple_yaml(v, indent + 2))
                else:
                    lines.append(f"{' ' * indent}{key_str}: {self._to_simple_yaml(v, 0)}")
            return "\n".join(lines)
        elif isinstance(data, list):
            if not data:
                return "[]"
            lines = []
            for item in data:
                if isinstance(item, (dict, list)):
                    if isinstance(item, dict):
                        item_lines = self._to_simple_yaml(item, indent + 2).split("\n")
                        first_line = item_lines[0].lstrip()
                        lines.append(f"{' ' * indent}- {first_line}")
                        for line in item_lines[1:]:
                            lines.append(line)
                    else:
                        item_str = self._to_simple_yaml(item, indent + 2)
                        lines.append(f"{' ' * indent}- {item_str.lstrip()}")
                else:
                    lines.append(f"{' ' * indent}- {self._to_simple_yaml(item, 0)}")
            return "\n".join(lines)
        return str(data)

    async def get_all_versions(self) -> dict[str, dict[str, Any]]:
        """Specs for all declared API versions (plus ``latest``)."""
        return self._versioned.build_all(self.router)

    def declared_versions(self) -> list[str]:
        """Declared version strings (without building specs)."""
        return self._versioned.declared_versions()

    # ── Invalidation & SSE ─────────────────────────────────────────────

    def invalidate(self) -> None:
        """
        Clear the in-process spec cache and broadcast to all SSE subscribers.
        Called on hot-reload (dev mode) or explicit cache clear.
        """
        self._process_cache.clear()
        payload = {"type": "spec:invalidated", "reason": "cache_cleared"}
        for queue in list(self._sse_queues):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    def subscribe_sse(self, queue: asyncio.Queue) -> None:
        """Register an SSE subscriber queue."""
        self._sse_queues.append(queue)

    def unsubscribe_sse(self, queue: asyncio.Queue) -> None:
        """Remove an SSE subscriber queue."""
        try:
            self._sse_queues.remove(queue)
        except ValueError:
            pass
