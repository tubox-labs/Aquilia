"""
Type definitions for the Aquilia Native Development Platform (ADP).

This module provides type aliases, literals, and TypedDicts used across
``aquilia.devplatform``, following the same per-subsystem file convention
as ``aquilia/typing/auth.py`` and ``aquilia/typing/controller.py``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, TypeAlias, TypedDict

#: Selected HTTP transport engine for the dev server.
AdpTransport: TypeAlias = Literal["auto", "h11"]

#: Selected WebSocket engine mode for the dev server.
AdpWsMode: TypeAlias = Literal["auto", "none"]

#: Logging verbosity for the dev server's own logger.
AdpLogLevel: TypeAlias = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

#: Hot-reload execution strategy chosen by the dependency graph analyzer.
ReloadStrategy: TypeAlias = Literal["full", "partial", "hot_patch"]

#: Generic untyped hook callback registered on AquiliaDevelopmentPlatform.
Hook: TypeAlias = Callable[..., Any]


class SpanDict(TypedDict):
    """Serialized shape of a ``TraceSpan``, as returned by ``RequestRecord.to_dict()``."""

    span_id: str
    name: str
    lane: str
    duration_ms: float
    status: str
    detail: dict[str, Any]
    parent_id: str | None
    source: str | None


class SQLRecordDict(TypedDict):
    """Serialized shape of a ``SQLRecord``, as returned by ``RequestRecord.to_dict()``."""

    sql: str
    duration_ms: float
    explain_plan: str | None


class RequestRecordDict(TypedDict):
    """Serialized shape returned by ``RequestRecord.to_dict()``."""

    trace_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    started_at: float
    client_addr: str | None
    route_pattern: str | None
    controller_class: str | None
    handler_name: str | None
    request_headers: dict[str, str]
    response_headers: dict[str, str]
    query_params: dict[str, list[str]]
    path_params: dict[str, Any]
    request_body_preview: str | None
    app_name: str | None
    auth_type: str | None
    auth_principal_id: str | None
    memory_delta_bytes: int
    n_plus_one_warnings: list[dict[str, Any]]
    spans: list[SpanDict]
    sql_records: list[SQLRecordDict]
    exception_type: str | None
    exception_message: str | None
    profile_stats: str | None


__all__ = [
    "AdpTransport",
    "AdpWsMode",
    "AdpLogLevel",
    "ReloadStrategy",
    "Hook",
    "SpanDict",
    "SQLRecordDict",
    "RequestRecordDict",
]
