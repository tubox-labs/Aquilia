"""
aquilia.inspector — Request Inspector (dev-tools subsystem)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Captures, stores, and streams per-request execution traces that include
middleware timing, dependency resolution, database queries, external HTTP
calls, and exceptions.

Enabled automatically in debug mode; controllable via
``Workspace.inspector()`` or ``InspectorConfig``.

Public API::

    from aquilia.inspector import (
        InspectorConfig,
        InspectorCollector,
        RequestTrace,
        Span,
        Lane,
        SpanStatus,
        get_collector,
    )

.. versionadded:: 1.3.0
"""

from aquilia.inspector.collector import InspectorCollector, get_collector
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.trace import Lane, RequestTrace, Span, SpanStatus

__all__ = [
    "InspectorConfig",
    "InspectorCollector",
    "RequestTrace",
    "Span",
    "Lane",
    "SpanStatus",
    "get_collector",
]
