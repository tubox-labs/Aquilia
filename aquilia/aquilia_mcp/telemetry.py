"""Small structured logging helpers for MCP operations."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RequestLogContext:
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    method: str = ""


def get_logger() -> logging.Logger:
    return logging.getLogger("aquilia.mcp")


def log_event(message: str, *, ctx: RequestLogContext | None = None, **fields: Any) -> None:
    logger = get_logger()
    safe_fields = {k: v for k, v in fields.items() if "secret" not in k.lower() and "token" not in k.lower()}
    if ctx:
        safe_fields["request_id"] = ctx.request_id
        safe_fields["method"] = ctx.method
    logger.info("%s %s", message, safe_fields)
