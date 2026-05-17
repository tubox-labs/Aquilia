"""Helpers for formatting source anchors."""

from __future__ import annotations

from ..models import SourceAnchor


def anchor_label(anchor: SourceAnchor) -> str:
    return f"{anchor.path}:{anchor.line} ({anchor.kind} {anchor.name})"


def compact_anchors(anchors: list[SourceAnchor], limit: int = 5) -> list[dict[str, object]]:
    return [anchor.to_dict() for anchor in anchors[:limit]]
