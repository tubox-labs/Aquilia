"""
RequestDAG -- thin compatibility shim over the unified container engine.

Historically Aquilia had **two** dependency-resolution engines: the
container (``core.py``) and a separate ``RequestDAG`` modelled on
FastAPI's ``Depends()``. They are now unified — the container owns the
one and only resolution engine (sub-dependency dedup, parallel branches,
generator teardown). ``RequestDAG`` remains as a stable, developer-facing
adapter that forwards every call to the backing container.

Usage (unchanged)::

    dag = RequestDAG(container, request)
    value = await dag.resolve(dep_descriptor, expected_type)
    await dag.teardown()
"""

from __future__ import annotations

import logging
from typing import Any, get_args, get_origin

from .dep import (
    Body,  # noqa: F401 — re-exported for callers
    Dep,
    Header,  # noqa: F401 — re-exported for callers
    Query,  # noqa: F401 — re-exported for callers
    _unpack_annotation,  # noqa: F401 — re-exported for callers
)

logger = logging.getLogger("aquilia.di.dag")


class RequestDAG:
    """Adapter that forwards Dep() resolution to the container engine.

    Retained for backwards compatibility. All real work happens in
    ``Container.resolve_dep`` / ``Container._run_dep_teardowns``.
    """

    __slots__ = ("_container", "_request")

    def __init__(self, container: Any, request: Any = None):
        self._container = container
        self._request = request

    # ── Public API ───────────────────────────────────────────────────

    async def resolve(self, dep: Dep, param_type: type) -> Any:
        """Resolve a single Dep descriptor via the container engine."""
        return await self._container.resolve_dep(dep, param_type, self._request)

    async def teardown(self) -> None:
        """Run generator teardowns (LIFO) accumulated on the container."""
        await self._container._run_dep_teardowns()

    # ── Delegating internals (kept for direct callers/tests) ──────────

    async def _resolve_single_sub_dep(self, pname: str, ptype: type, sub_dep: Any) -> Any:
        return await self._container._resolve_single_dep(pname, ptype, sub_dep, self._request)

    async def _resolve_from_container(self, param_type: type, tag: str | None) -> Any:
        return await self._container._resolve_from_container(param_type, tag)

    async def _extract_body_value(self, body: Body | None = None) -> Any:
        return await self._container._extract_body_value(self._request)


# ── Module-level helpers (imported by core.py and controller layer) ───


def _extract_header_from_type(annotation: Any) -> Header | None:
    """Check if annotation is Annotated[T, Header(...)]."""
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
    """Check if annotation is Annotated[T, Query(...)]."""
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
    """Check if annotation is Annotated[T, Body(...)]."""
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
    """Unwrap Annotated[T, ...] → T."""
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
    """Check if type is a Contract subclass."""
    try:
        from aquilia.contracts.core import Contract

        return isinstance(annotation, type) and issubclass(annotation, Contract) and annotation is not Contract
    except ImportError:
        return False
