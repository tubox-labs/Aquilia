"""
AquilaCache -- Decorators for declarative caching.

Provides ``@cached``, ``@cache_aside``, and ``@invalidate``
decorators for controller methods and service functions.

Features:
- Automatic cache key generation from function arguments
- Custom key functions for complex key strategies
- Conditional caching (skip caching based on result)
- Module-level CacheService singleton support
- Full introspection metadata on decorated functions

Key generation is delegated to the active ``CacheService``'s own key
builder, so decorator-generated keys carry the configured ``key_prefix``
and ``key_version`` and embed the namespace exactly once -- identical to
keys produced by direct ``cache.get``/``cache.set`` calls.

Functions returning ``None`` are cached: the value is stored as a private
sentinel and restored on read, so a legitimately ``None`` result does not
force recomputation on every call.
"""

from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any, Final, TypeVar

from .key_builder import call_signature

logger = logging.getLogger("aquilia.cache.decorators")

T = TypeVar("T")

#: Marker stored in place of ``None`` so cached ``None`` results are hits.
_NONE_SENTINEL: Final[str] = "__aquilia_cache_none__"

# Module-level cache service registry for decorators
# Set via `set_default_cache_service()` during app startup
_default_cache_service: Any | None = None


def set_default_cache_service(service: Any) -> None:
    """
    Register a module-level CacheService for decorator resolution.

    Called automatically during ``Server._setup_cache()``.
    Enables decorators to work on standalone functions (not just
    controller methods with ``self.cache``).

    Args:
        service: CacheService instance

    Returns:
        ``None``.

    Usage::

        set_default_cache_service(cache_service)
    """
    global _default_cache_service
    _default_cache_service = service


def get_default_cache_service() -> Any | None:
    """
    Return the module-level default CacheService.

    Returns:
        The registered ``CacheService``, or ``None`` if never set.
    """
    return _default_cache_service


def cached(
    ttl: int = 300,
    namespace: str = "default",
    key: str | None = None,
    key_func: Callable[..., str] | None = None,
    tags: tuple[str, ...] = (),
    unless: Callable[..., bool] | None = None,
    condition: Callable[[Any], bool] | None = None,
):
    """
    Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds
        namespace: Cache namespace
        key: Explicit cache key (auto-generated from args if None)
        key_func: Custom key builder ``(func, args, kwargs) → str``
        tags: Tags for group invalidation
        unless: Callable ``(*args, **kwargs) → bool`` -- skip caching if True
        condition: Callable ``(result) → bool`` -- only cache if True.
                   Useful for skipping error results or empty lists.

    Returns:
        A decorator wrapping the target function with cache-aside behaviour.

    Note:
        A ``None`` return value is cached like any other result; it is stored
        as an internal sentinel and restored transparently on read.  Use
        ``condition`` to opt out where recomputation is preferred.

    Usage::

        @cached(ttl=60, namespace="users")
        async def get_user(user_id: int):
            return await db.fetch_user(user_id)

        @cached(ttl=120, key="all_products", tags=("products",))
        async def list_products():
            return await db.fetch_all_products()

        # Custom key function
        @cached(ttl=60, key_func=lambda f, a, kw: f"user:{kw.get('user_id')}")
        async def get_user_profile(user_id: int):
            ...

        # Conditional caching -- don't cache empty results
        @cached(ttl=60, condition=lambda result: result is not None and len(result) > 0)
        async def search_products(query: str):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get cache service from first arg (controller self)
            cache_service = _resolve_cache_service(args)

            if cache_service is None:
                # No cache available -- just call the function
                return await func(*args, **kwargs) if is_async else func(*args, **kwargs)

            # Check unless condition
            if unless and unless(*args, **kwargs):
                return await func(*args, **kwargs) if is_async else func(*args, **kwargs)

            # Build cache key -- the service's own builder is used so decorator
            # keys match manually-built keys exactly (prefix, version, one namespace).
            if key:
                cache_key = key
            elif key_func:
                cache_key = key_func(func, args, kwargs)
            else:
                # Drop the bound instance from the key, but only when the
                # function really is a method. Every Python object has
                # ``__class__``, so testing for it would silently discard the
                # first positional argument of plain functions and make
                # different calls collide on one key.
                skip = 1 if _is_bound_call(func, args) else 0
                cache_key = call_signature(func.__qualname__, args[skip:], kwargs)

            # Try cache
            cached_value = await cache_service.get(cache_key, namespace=namespace)
            if cached_value is not None:
                return None if cached_value == _NONE_SENTINEL else cached_value

            # Cache miss -- compute
            result = await func(*args, **kwargs) if is_async else func(*args, **kwargs)

            # Check condition before caching
            should_cache = True
            if condition is not None:
                try:
                    should_cache = condition(result)
                except Exception:
                    should_cache = False

            if should_cache:
                await cache_service.set(
                    cache_key,
                    _NONE_SENTINEL if result is None else result,
                    ttl=ttl,
                    namespace=namespace,
                    tags=tags,
                )

            return result

        # Attach metadata for introspection
        wrapper.__cached__ = True
        wrapper.__cache_ttl__ = ttl
        wrapper.__cache_namespace__ = namespace
        wrapper.__cache_tags__ = tags

        return wrapper

    return decorator


def cache_aside(
    ttl: int = 300,
    namespace: str = "default",
    tags: tuple[str, ...] = (),
):
    """
    Cache-aside decorator -- identical to @cached but semantically
    indicates the function is the authoritative data source.

    Usage::

        @cache_aside(ttl=120, namespace="products")
        async def find_product(product_id: int):
            return await db.find_product(product_id)
    """
    return cached(ttl=ttl, namespace=namespace, tags=tags)


def invalidate(
    *keys: str,
    namespace: str = "default",
    tags: tuple[str, ...] = (),
):
    """
    Decorator to invalidate cache entries after function execution.

    Useful for write operations that should clear related cache entries.

    Args:
        *keys: Specific cache keys to invalidate
        namespace: Cache namespace
        tags: Tags to invalidate

    Usage::

        @invalidate("all_products", tags=("products",))
        async def create_product(data: dict):
            return await db.insert_product(data)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Execute the function first
            result = await func(*args, **kwargs) if is_async else func(*args, **kwargs)

            # Then invalidate
            cache_service = _resolve_cache_service(args)
            if cache_service:
                # Invalidate specific keys
                for key in keys:
                    await cache_service.delete(key, namespace=namespace)

                # Invalidate by tags
                if tags:
                    await cache_service.invalidate_tags(*tags)

            return result

        wrapper.__invalidates__ = True
        wrapper.__invalidate_keys__ = keys
        wrapper.__invalidate_tags__ = tags

        return wrapper

    return decorator


# ── Helpers ──────────────────────────────────────────────────────────


def _is_bound_call(func: Callable[..., Any], args: tuple[object, ...]) -> bool:
    """
    Report whether ``args[0]`` is the instance a method was called on.

    Args:
        func: The undecorated function.
        args: Positional arguments of the call.

    Returns:
        True when *func* is defined inside a class and the first argument is
        an instance of that class, i.e. the argument is ``self`` and should not
        contribute to the cache key.

    Note:
        The qualified name is used to detect methods; a plain function has no
        dotted owner, so its first argument is always keyed.
    """
    if not args:
        return False
    owner_path = func.__qualname__.rsplit(".", 1)[0] if "." in func.__qualname__ else ""
    if not owner_path or owner_path.endswith("<locals>"):
        return False
    owner_name = owner_path.rsplit(".", 1)[-1]
    return type(args[0]).__name__ == owner_name or any(base.__name__ == owner_name for base in type(args[0]).__mro__)


def _resolve_cache_service(args: tuple):
    """
    Try to find a CacheService from function arguments.

    Resolution order:
    1. ``self.cache`` on the first argument (controller/service)
    2. ``self._cache`` on the first argument
    3. Module-level default (set via ``set_default_cache_service()``)
    """
    from .service import CacheService

    if args and hasattr(args[0], "__class__"):
        obj = args[0]
        # Check for cache attribute on controller/service
        cache = getattr(obj, "cache", None)
        if isinstance(cache, CacheService):
            return cache

        # Check for _cache attribute
        cache = getattr(obj, "_cache", None)
        if isinstance(cache, CacheService):
            return cache

    # Fall back to module-level default
    if _default_cache_service is not None:
        return _default_cache_service

    return None
