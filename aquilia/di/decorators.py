"""
Decorators and injection helpers for ergonomic DI usage.
"""

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar, get_type_hints

T = TypeVar("T")


@dataclass
class Inject:
    """
    Injection metadata marker.

    Usage:
        def __init__(self, repo: Annotated[UserRepo, Inject(tag="repo")]):
            ...
    """

    token: type | str | None = None
    tag: str | None = None
    optional: bool = False

    # Internal marker for provider introspection
    _inject_token: type | str | None = None
    _inject_tag: str | None = None
    _inject_optional: bool = False

    def __post_init__(self):
        self._inject_token = self.token
        self._inject_tag = self.tag
        self._inject_optional = self.optional


def inject(
    token: type | str | None = None,
    *,
    tag: str | None = None,
    optional: bool = False,
) -> Inject:
    """
    Create injection metadata.

    Args:
        token: Optional explicit token (inferred from type hint if None)
        tag: Optional tag for disambiguation
        optional: If True, inject None if provider not found

    Returns:
        Inject metadata object

    Example:
        def handler(
            db: Annotated[Database, inject(tag="readonly")],
            cache: Annotated[Cache, inject(optional=True)],
        ):
            ...
    """
    return Inject(token=token, tag=tag, optional=optional)


def service(
    *,
    scope: str = "app",
    tag: str | None = None,
    name: str | None = None,
) -> Callable[[type[T]], type[T]]:
    """
    Decorator to mark a class as a DI service.

    Args:
        scope: Service scope (singleton, app, request, transient, pooled, ephemeral)
        tag: Optional tag for disambiguation
        name: Optional explicit service name

    Returns:
        Decorator function

    Example:
        @service(scope="request", tag="primary")
        class UserService:
            def __init__(self, repo: UserRepo):
                self.repo = repo
    """

    def decorator(cls: type[T]) -> type[T]:
        # Attach metadata to class
        cls.__di_scope__ = scope  # type: ignore
        cls.__di_tag__ = tag  # type: ignore
        cls.__di_name__ = name or cls.__name__  # type: ignore
        return cls

    return decorator


def factory(
    *,
    scope: str = "app",
    tag: str | None = None,
    name: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to mark a function as a DI factory.

    Args:
        scope: Service scope
        tag: Optional tag for disambiguation
        name: Optional explicit factory name

    Returns:
        Decorator function

    Example:
        @factory(scope="singleton", name="db_pool")
        async def create_db_pool(config: Config) -> DatabasePool:
            return await DatabasePool.connect(config.db_url)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Attach metadata to function
        func.__di_scope__ = scope  # type: ignore
        func.__di_tag__ = tag  # type: ignore
        func.__di_name__ = name or func.__name__  # type: ignore
        func.__di_factory__ = True  # type: ignore
        return func

    return decorator


def provides(
    token: type | str,
    *,
    scope: str = "app",
    tag: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to explicitly declare what a factory provides.

    Useful when return type annotation is generic or abstract.

    Args:
        token: Type or string key that this factory provides
        scope: Service scope
        tag: Optional tag

    Returns:
        Decorator function

    Example:
        @provides(UserRepository, scope="app", tag="sql")
        def create_sql_repo(db: Database) -> UserRepository:
            return SqlUserRepository(db)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func.__di_provides__ = token  # type: ignore
        func.__di_scope__ = scope  # type: ignore
        func.__di_tag__ = tag  # type: ignore
        func.__di_factory__ = True  # type: ignore
        return func

    return decorator


def auto_inject(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to auto-inject dependencies into a function.

    Looks up dependencies from a thread-local container.

    WARNING: This is convenience sugar with some overhead.
    Prefer explicit dependency passing in hot paths.

    Example:
        @auto_inject
        async def my_handler(request: Request, db: Database):
            # db is automatically resolved from request container
            ...
    """
    from .compat import get_request_container

    sig = func.__signature__ if hasattr(func, "__signature__") else None
    hints = get_type_hints(func) if sig is None else None

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get request container from context
        container = get_request_container()
        if container is None:
            from ..faults.domains import DIResolutionFault

            raise DIResolutionFault(
                provider="auto_inject",
                reason="No request container in context; cannot auto-inject",
            )

        # SEC-DI-12: Warn if auto-injecting from a non-request container
        if hasattr(container, "_scope") and container._scope not in ("request", "ephemeral"):
            import logging as _log

            _log.getLogger("aquilia.di").warning(
                "@auto_inject resolving from %s-scoped container; expected request/ephemeral scope.",
                container._scope,
            )

        # Resolve missing dependencies
        if sig:
            params = sig.parameters
        else:
            import inspect

            params = inspect.signature(func).parameters

        for param_name, param in params.items():
            if param_name in kwargs or param_name == "self":
                continue

            # Get type hint
            type_hint = hints.get(param_name) if hints else param.annotation
            if type_hint is None or type_hint == param.empty:
                continue

            # Resolve from container
            try:
                resolved = await container.resolve_async(type_hint)
                kwargs[param_name] = resolved
            except Exception:
                # Optional or has default - skip
                if param.default != param.empty:
                    continue
                raise

        return await func(*args, **kwargs)

    return wrapper


# Convenience alias
injectable = service
