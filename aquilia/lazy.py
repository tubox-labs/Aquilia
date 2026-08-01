"""Deferred import primitives for Aquilia.

Aquilia exposes a large public surface (~580 names spanning 56 subsystems) from
its top-level package. Binding all of those eagerly forces every subsystem --
ORM, admin, sockets, tasks, storage, mail -- into memory on ``import aquilia``,
even for a workspace that enables none of them. This module provides the small
set of primitives used to defer that work until a name is actually touched.

The module deliberately depends on nothing but the standard library. It is
imported by :mod:`aquilia` itself before any subsystem exists, so any internal
import here would reintroduce the eager graph it is meant to remove -- and would
be a hard import cycle besides. For the same reason it raises builtin
exceptions rather than :class:`aquilia.faults.Fault` subclasses: the fault
system is one of the subsystems being deferred.

Primitives:
    :func:`install_lazy_exports`
        Turns an ``__init__`` barrel into an on-demand one. This is the primary
        entry point and the one with measurable impact.
    :func:`lazy_import`
        A module proxy for expensive or rarely-taken module-level imports.
    :func:`lazy_attr`
        An object proxy for a single deferred class, callable, or singleton.
    :func:`require`
        Imports an optional third-party dependency with an actionable error.

Example:
    Deferring a package barrel::

        from aquilia.lazy import install_lazy_exports

        install_lazy_exports(
            __name__,
            globals(),
            {"Controller": (".controller", "Controller")},
        )
"""

from __future__ import annotations

import importlib
import threading
from collections.abc import Callable, Iterable, Mapping
from typing import Any, TypeVar

__all__ = [
    "LazyModule",
    "LazyObject",
    "install_lazy_exports",
    "lazy_attr",
    "lazy_import",
    "require",
]

_T = TypeVar("_T")

# Guards the one-shot resolution of every proxy in the process. Resolution is
# short and uncontended, so a single lock is cheaper than per-proxy locks; the
# double-checked read below keeps the steady-state path lock-free.
_RESOLVE_LOCK = threading.Lock()


def _import(module: str, package: str | None = None) -> Any:
    """Import ``module``, translating failures into an actionable error.

    Args:
        module: Absolute or relative (leading-dot) module name.
        package: Anchor package for relative names.

    Returns:
        The imported module object.

    Raises:
        ImportError: If the module cannot be imported. The original error is
            chained so the underlying cause stays visible.
    """
    try:
        return importlib.import_module(module, package)
    except ImportError as exc:
        anchor = f" (relative to {package!r})" if package and module.startswith(".") else ""
        raise ImportError(f"Aquilia could not import {module!r}{anchor}: {exc}") from exc


class LazyModule:
    """A module placeholder that imports its target on first attribute access.

    Use for module-level imports that are expensive and only needed on some
    code paths. The proxy is transparent for attribute access, which covers
    effectively all module usage; it is not a substitute for the real module in
    ``isinstance`` checks or in code that inspects ``type()``.

    Attributes:
        __wrapped__: The resolved module, once imported.

    Example:
        >>> yaml = LazyModule("yaml")
        >>> yaml.safe_load("a: 1")  # 'yaml' imported here, not above
        {'a': 1}
    """

    __slots__ = ("_module", "_package", "_resolved")

    def __init__(self, module: str, package: str | None = None) -> None:
        """Initialize the proxy.

        Args:
            module: Absolute or relative module name to import on first use.
            package: Anchor package, required for relative ``module`` names.
        """
        object.__setattr__(self, "_module", module)
        object.__setattr__(self, "_package", package)
        object.__setattr__(self, "_resolved", None)

    def __resolve__(self) -> Any:
        """Import and cache the target module.

        Returns:
            The imported module object.
        """
        resolved = object.__getattribute__(self, "_resolved")
        if resolved is None:
            with _RESOLVE_LOCK:
                resolved = object.__getattribute__(self, "_resolved")
                if resolved is None:
                    resolved = _import(
                        object.__getattribute__(self, "_module"),
                        object.__getattribute__(self, "_package"),
                    )
                    object.__setattr__(self, "_resolved", resolved)
        return resolved

    @property
    def __wrapped__(self) -> Any:
        """The resolved module, importing it if necessary."""
        return self.__resolve__()

    def __getattr__(self, name: str) -> Any:
        """Resolve the module and delegate attribute access to it.

        Args:
            name: Attribute to read from the target module.

        Returns:
            The attribute value.
        """
        return getattr(self.__resolve__(), name)

    def __dir__(self) -> Iterable[str]:
        """Return the target module's namespace."""
        return dir(self.__resolve__())

    def __repr__(self) -> str:
        """Return a representation that does not trigger the import."""
        state = "resolved" if object.__getattribute__(self, "_resolved") else "pending"
        return f"<LazyModule {object.__getattribute__(self, '_module')!r} {state}>"


class LazyObject:
    """A proxy for a single object resolved from a module on first use.

    Suitable for a deferred class, function, factory, registry, or
    module-level singleton. Attribute access, calling, indexing, iteration and
    ``bool`` all force resolution and delegate to the real object.

    ``isinstance(x, SomeLazyObject)`` does not work, because the proxy is not
    the class. Where a real class object is required -- base classes, ``except``
    clauses, ``isinstance`` -- resolve explicitly via :attr:`__wrapped__`.

    Attributes:
        __wrapped__: The resolved object, once loaded.

    Example:
        >>> engine = LazyObject("aquilia.templates", "TemplateEngine")
        >>> instance = engine()  # imported and instantiated here
    """

    __slots__ = ("_attr", "_module", "_package", "_resolved", "_sentinel")

    def __init__(self, module: str, attr: str, package: str | None = None) -> None:
        """Initialize the proxy.

        Args:
            module: Module to import when the object is first used.
            attr: Attribute name to read from that module.
            package: Anchor package, required for relative ``module`` names.
        """
        object.__setattr__(self, "_module", module)
        object.__setattr__(self, "_attr", attr)
        object.__setattr__(self, "_package", package)
        object.__setattr__(self, "_sentinel", object())
        object.__setattr__(self, "_resolved", object.__getattribute__(self, "_sentinel"))

    def __resolve__(self) -> Any:
        """Import the module, read the attribute, and cache the result.

        Returns:
            The resolved object.

        Raises:
            AttributeError: If the module does not define the attribute.
        """
        sentinel = object.__getattribute__(self, "_sentinel")
        resolved = object.__getattribute__(self, "_resolved")
        if resolved is sentinel:
            with _RESOLVE_LOCK:
                resolved = object.__getattribute__(self, "_resolved")
                if resolved is sentinel:
                    module_name = object.__getattribute__(self, "_module")
                    attr = object.__getattribute__(self, "_attr")
                    module = _import(module_name, object.__getattribute__(self, "_package"))
                    try:
                        resolved = getattr(module, attr)
                    except AttributeError as exc:
                        raise AttributeError(f"{module_name!r} has no attribute {attr!r}") from exc
                    object.__setattr__(self, "_resolved", resolved)
        return resolved

    @property
    def __wrapped__(self) -> Any:
        """The resolved object, loading it if necessary."""
        return self.__resolve__()

    def __getattr__(self, name: str) -> Any:
        """Resolve the target and delegate attribute access.

        Args:
            name: Attribute to read from the resolved object.

        Returns:
            The attribute value.
        """
        return getattr(self.__resolve__(), name)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Resolve the target and call it.

        Args:
            *args: Positional arguments forwarded to the target.
            **kwargs: Keyword arguments forwarded to the target.

        Returns:
            Whatever the target returns.
        """
        return self.__resolve__()(*args, **kwargs)

    def __getitem__(self, key: Any) -> Any:
        """Resolve the target and index into it.

        Args:
            key: Index or key to look up.

        Returns:
            The indexed value.
        """
        return self.__resolve__()[key]

    def __iter__(self) -> Any:
        """Resolve the target and iterate over it."""
        return iter(self.__resolve__())

    def __bool__(self) -> bool:
        """Resolve the target and evaluate its truthiness."""
        return bool(self.__resolve__())

    def __dir__(self) -> Iterable[str]:
        """Return the resolved object's namespace."""
        return dir(self.__resolve__())

    def __repr__(self) -> str:
        """Return a representation that does not trigger resolution."""
        pending = object.__getattribute__(self, "_resolved") is object.__getattribute__(self, "_sentinel")
        module_name = object.__getattribute__(self, "_module")
        attr = object.__getattribute__(self, "_attr")
        return f"<LazyObject {module_name}.{attr} {'pending' if pending else 'resolved'}>"


def lazy_import(module: str, package: str | None = None) -> LazyModule:
    """Return a proxy that imports ``module`` on first attribute access.

    Args:
        module: Absolute or relative module name.
        package: Anchor package, required for relative ``module`` names.

    Returns:
        A :class:`LazyModule` proxy for the module.

    Example:
        >>> jinja = lazy_import("jinja2")
    """
    return LazyModule(module, package)


def lazy_attr(module: str, attr: str, package: str | None = None) -> LazyObject:
    """Return a proxy for ``module.attr`` resolved on first use.

    Args:
        module: Module to import when the object is first used.
        attr: Attribute name to read from that module.
        package: Anchor package, required for relative ``module`` names.

    Returns:
        A :class:`LazyObject` proxy for the attribute.

    Example:
        >>> AuthManager = lazy_attr("aquilia.auth.manager", "AuthManager")
    """
    return LazyObject(module, attr, package)


def require(module: str, *, feature: str, extra: str | None = None) -> Any:
    """Import an optional third-party dependency, or explain how to install it.

    Aquilia keeps heavyweight integrations (Redis, boto3, OpenTelemetry,
    cryptography backends) out of its base dependency set. Call this at the
    point of use so an absent package produces an actionable message instead of
    a bare :class:`ModuleNotFoundError`.

    Args:
        module: Importable module name, for example ``"redis.asyncio"``.
        feature: Human-readable name of the Aquilia feature that needs it, used
            in the error message.
        extra: Pip install target to suggest. Defaults to the top-level
            distribution implied by ``module``.

    Returns:
        The imported module object.

    Raises:
        ImportError: If the dependency is not installed, with an install hint.

    Example:
        >>> redis = require("redis.asyncio", feature="Redis cache backend",
        ...                 extra="aquilia[cache-redis]")
    """
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        target = extra or module.split(".")[0]
        raise ImportError(
            f"{feature} requires the {module.split('.')[0]!r} package, which is not installed. "
            f"Install it with: pip install {target}"
        ) from exc


def install_lazy_exports(
    package: str,
    namespace: dict[str, Any],
    exports: Mapping[str, tuple[str, str]],
    *,
    fallback: Callable[[str], Any] | None = None,
) -> None:
    """Install PEP 562 hooks so a package barrel resolves names on demand.

    Rewrites ``namespace`` with a ``__getattr__``/``__dir__`` pair that imports
    the owning submodule the first time each exported name is read, then caches
    the value directly in ``namespace`` so subsequent reads are plain dict
    lookups with no proxy indirection.

    Names not present in ``exports`` fall back to importing a submodule of the
    same name, which keeps ``import aquilia; aquilia.models`` working exactly as
    it did with an eager barrel.

    Args:
        package: The package's ``__name__``, used as the anchor for relative
            module references in ``exports``.
        namespace: The package's ``globals()`` dict, mutated in place.
        exports: Maps each exported name to a ``(module, attribute)`` pair. The
            module may be relative (leading dot) or absolute.
        fallback: Optional resolver consulted before the submodule fallback,
            for names that need bespoke handling such as an optional dependency
            with a custom error.

    Raises:
        TypeError: If ``exports`` contains a malformed entry.

    Example:
        >>> install_lazy_exports(
        ...     __name__, globals(), {"Controller": (".controller", "Controller")}
        ... )
    """
    for name, target in exports.items():
        if not (isinstance(target, tuple) and len(target) == 2):
            raise TypeError(f"exports[{name!r}] must be a (module, attribute) tuple, got {target!r}")

    def _lazy_getattr(name: str) -> Any:
        target = exports.get(name)
        if target is not None:
            module_name, attr = target
            module = _import(module_name, package)
            try:
                value = getattr(module, attr)
            except AttributeError as exc:
                raise AttributeError(
                    f"{package}.{name} is declared as {module_name}.{attr}, "
                    f"but {module_name!r} does not define {attr!r}"
                ) from exc
            namespace[name] = value
            return value

        if fallback is not None:
            try:
                value = fallback(name)
            except AttributeError:
                pass
            else:
                namespace[name] = value
                return value

        if not name.startswith("_"):
            try:
                value = importlib.import_module(f".{name}", package)
            except ImportError:
                pass
            else:
                namespace[name] = value
                return value

        raise AttributeError(f"module {package!r} has no attribute {name!r}")

    def _lazy_dir() -> list[str]:
        return sorted(set(namespace.get("__all__", ())) | set(exports) | set(namespace))

    namespace["__getattr__"] = _lazy_getattr
    namespace["__dir__"] = _lazy_dir
