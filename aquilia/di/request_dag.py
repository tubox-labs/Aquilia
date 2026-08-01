"""
RequestDAG -- Compatibility adapter over the unified container DI engine.

Historically Aquilia had two dependency-resolution engines: the container (``core.py``)
and a separate ``RequestDAG`` modelled on FastAPI's ``Depends()``. They are now unified:
the container owns the unified resolution engine (sub-dependency deduplication, parallel
branch execution, and generator teardown). ``RequestDAG`` remains as a stable, developer-facing
adapter that forwards calls to the backing container.

Usage::

    dag = RequestDAG(container, request)
    value = await dag.resolve(dep_descriptor, expected_type)
    await dag.teardown()
"""

from __future__ import annotations

import logging
from typing import Any, get_args, get_origin

from aquilia.di.dep import (
    Body,  # noqa: F401 — re-exported for callers
    Dep,
    Header,  # noqa: F401 — re-exported for callers
    Query,  # noqa: F401 — re-exported for callers
    _unpack_annotation,  # noqa: F401 — re-exported for callers
)

logger = logging.getLogger("aquilia.di.dag")


class RequestDAG:
    """
    Adapter bridging request-scoped dependency DAG resolution to the container engine.

    Args:
        container: The backing Aquilia :class:`~aquilia.di.core.Container` instance.
        request: Optional HTTP/ASGI request context for extracting headers, query,
            cookies, path, or body parameters.

    Returns:
        A :class:`RequestDAG` adapter wrapping the container resolution engine.

    Note:
        ``RequestDAG`` provides backward compatibility while delegating all real
        dependency resolution, cycle detection, in-flight de-duplication, and
        generator teardown directly to ``Container.resolve_dep``.

    Usage::

        dag = RequestDAG(container, request)
        user = await dag.resolve(Dep(get_current_user), User)
        ...
        await dag.teardown()
    """

    __slots__ = ("_container", "_request")

    def __init__(self, container: Any, request: Any = None):
        """
        Initialize a RequestDAG adapter.

        Args:
            container: Backing Aquilia DI container.
            request: Active HTTP/ASGI request instance (optional).

        Returns:
            RequestDAG adapter instance.
        """
        self._container = container
        self._request = request

    # ── Public API ───────────────────────────────────────────────────

    async def resolve(self, dep: Dep, param_type: type) -> Any:
        """
        Resolve a single Dep descriptor via the backing container engine.

        Args:
            dep: The :class:`~aquilia.di.dep.Dep` descriptor to evaluate.
            param_type: Expected return type or Annotated type hint.

        Returns:
            The resolved dependency value or instantiated service.

        Note:
            Calls ``Container.resolve_dep`` under the hood, supporting async
            callables, sync callables, generators, and bare container lookups.

        Usage::

            val = await dag.resolve(Dep(get_db_session), Session)
        """
        return await self._container.resolve_dep(dep, param_type, self._request)

    async def teardown(self) -> None:
        """
        Run generator teardowns accumulated on the backing container in LIFO order.

        Returns:
            None

        Note:
            Ensures all generator dependencies (e.g. database transactions or stream
            locks) opened during request execution are cleanly finalized.

        Usage::

            try:
                result = await handler(...)
            finally:
                await dag.teardown()
        """
        await self._container._run_dep_teardowns()

    # ── Delegating internals (kept for direct callers/tests) ──────────

    async def _resolve_single_sub_dep(self, pname: str, ptype: type, sub_dep: Any) -> Any:
        """
        Resolve a single sub-dependency parameter within a Dep callable.

        Args:
            pname: Parameter name.
            ptype: Parameter type annotation.
            sub_dep: Extractor descriptor (Header/Query/Body/Cookie/Path) or sub-Dep.

        Returns:
            Resolved parameter value.

        Note:
            Forwards execution to ``Container._resolve_single_dep``.
        """
        return await self._container._resolve_single_dep(pname, ptype, sub_dep, self._request)

    async def _resolve_from_container(self, param_type: type, tag: str | None) -> Any:
        """
        Resolve a parameter by type or Annotated alias directly from the container.

        Args:
            param_type: Target type hint or Annotated alias.
            tag: Optional container tag for disambiguation.

        Returns:
            Resolved service instance from container.

        Note:
            Forwards execution to ``Container._resolve_from_container``.
        """
        return await self._container._resolve_from_container(param_type, tag)

    async def _extract_body_value(self, body: Body | None = None) -> Any:
        """
        Extract parsed JSON or form body payload from the active request context.

        Args:
            body: Optional :class:`~aquilia.di.dep.Body` descriptor.

        Returns:
            Parsed request body dictionary or empty dict if unparseable.

        Note:
            Forwards execution to ``Container._extract_body_value``.
        """
        return await self._container._extract_body_value(self._request)


# ── Module-level helpers (imported by core.py and controller layer) ───


def _extract_header_from_type(annotation: Any) -> Header | None:
    """
    Extract a Header descriptor from an Annotated type annotation.

    Args:
        annotation: Type annotation to inspect (e.g. ``Annotated[str, Header("X-Api-Key")]``).

    Returns:
        Extracted :class:`~aquilia.di.dep.Header` instance if present, otherwise ``None``.

    Note:
        Inspects ``Annotated`` metadata args for a ``Header`` instance.

    Usage::

        header_meta = _extract_header_from_type(Annotated[str, Header("Authorization")])
    """
    origin = get_origin(annotation)
    if origin is None:
        return None
    try:
        from typing import Annotated

        if origin is Annotated:
            for meta in get_args(annotation)[1:]:
                if isinstance(meta, Header):
                    return meta
    except ImportError:
        pass
    return None


def _extract_query_from_type(annotation: Any) -> Query | None:
    """
    Extract a Query descriptor from an Annotated type annotation.

    Args:
        annotation: Type annotation to inspect (e.g. ``Annotated[int, Query("page", default=1)]``).

    Returns:
        Extracted :class:`~aquilia.di.dep.Query` instance if present, otherwise ``None``.

    Note:
        Inspects ``Annotated`` metadata args for a ``Query`` instance.

    Usage::

        query_meta = _extract_query_from_type(Annotated[int, Query("page")])
    """
    origin = get_origin(annotation)
    if origin is None:
        return None
    try:
        from typing import Annotated

        if origin is Annotated:
            for meta in get_args(annotation)[1:]:
                if isinstance(meta, Query):
                    return meta
    except ImportError:
        pass
    return None


def _extract_body_from_type(annotation: Any) -> Body | None:
    """
    Extract a Body descriptor from an Annotated type annotation.

    Args:
        annotation: Type annotation to inspect (e.g. ``Annotated[dict, Body()]``).

    Returns:
        Extracted :class:`~aquilia.di.dep.Body` instance if present, otherwise ``None``.

    Note:
        Inspects ``Annotated`` metadata args for a ``Body`` instance.

    Usage::

        body_meta = _extract_body_from_type(Annotated[dict, Body()])
    """
    origin = get_origin(annotation)
    if origin is None:
        return None
    try:
        from typing import Annotated

        if origin is Annotated:
            for meta in get_args(annotation)[1:]:
                if isinstance(meta, Body):
                    return meta
    except ImportError:
        pass
    return None


def _get_base_type(annotation: Any) -> type:
    """
    Unwrap an Annotated type annotation to retrieve its base type.

    Args:
        annotation: Type annotation or Annotated alias (e.g. ``Annotated[UserRepo, Dep()]``).

    Returns:
        The underlying base type (e.g. ``UserRepo``) or the original annotation if not Annotated.

    Note:
        Safely inspects typing origins to extract ``get_args(annotation)[0]``.

    Usage::

        base = _get_base_type(Annotated[UserRepo, Dep()])  # UserRepo
    """
    origin = get_origin(annotation)
    if origin is not None:
        try:
            from typing import Annotated

            if origin is Annotated:
                return get_args(annotation)[0]
        except ImportError:
            pass
    return annotation


def _is_contract_type(annotation: Any) -> bool:
    """
    Determine if a type annotation represents an Aquilia Contract subclass.

    Args:
        annotation: Target type hint to evaluate.

    Returns:
        ``True`` if ``annotation`` is a subclass of ``Contract`` (and not ``Contract`` itself),
        otherwise ``False``.

    Note:
        Used by the request DAG engine to detect payload contracts for auto-binding.

    Usage::

        is_contract = _is_contract_type(CreateUserContract)  # True
    """
    try:
        from aquilia.contracts.core import Contract

        return isinstance(annotation, type) and issubclass(annotation, Contract) and annotation is not Contract
    except ImportError:
        pass
    return False
