"""
Jinja2 template extensions used by Aquilia templates.

Provides production-safe asset URL tags compatible with:

    {% static 'css/app.css' %}
    {% static 'css/app.css' as css_url %}
    {% asset 'js/app.js' %}
    {% media 'avatars/user.png' as avatar_url %}
"""

from __future__ import annotations

from typing import Any

from jinja2 import nodes, pass_context
from jinja2.ext import Extension


def _normalize_asset_path(path: Any) -> str:
    """Normalize template-provided asset paths into a safe URL segment."""
    text = "" if path is None else str(path)
    text = text.strip().replace("\\", "/").replace("\x00", "")

    suffix = ""
    q_pos = text.find("?")
    h_pos = text.find("#")
    cut_positions = [p for p in (q_pos, h_pos) if p != -1]
    if cut_positions:
        cut_at = min(cut_positions)
        suffix = text[cut_at:]
        text = text[:cut_at]

    # Drop empty/current/traversal segments so generated URLs stay canonical.
    segments = [segment for segment in text.split("/") if segment not in ("", ".", "..")]
    normalized = "/".join(segments)
    return f"{normalized}{suffix}"


def _call_context_or_global(context, environment, names: list[str], arg: str) -> str | None:
    """Resolve URL helper function by name from context first, then environment globals."""
    for name in names:
        context_func = context.get(name)
        if callable(context_func):
            return str(context_func(arg))

    for name in names:
        env_func = environment.globals.get(name)
        if callable(env_func):
            return str(env_func(arg))

    return None


def _prefixed_url(prefix: str, path: str) -> str:
    base = prefix.rstrip("/")
    return f"{base}/{path}" if path else f"{base}/"


class StaticTagExtension(Extension):
    """Provide first-class Aquilia asset tags for templates."""

    tags = {"static", "asset", "media"}

    def parse(self, parser):
        token = next(parser.stream)
        lineno = token.lineno
        tag_name = token.value

        # Accept quoted strings or expressions, e.g. {% static asset_path %}
        path_expr = parser.parse_expression()
        tag_call = self.call_method("_resolve_tag", [nodes.Const(tag_name), path_expr], lineno=lineno)

        # Optional assignment form: {% static 'css/app.css' as app_css %}
        if parser.stream.skip_if("name:as"):
            target = parser.parse_assign_target(name_only=True)
            return nodes.Assign(target, tag_call, lineno=lineno)

        return nodes.Output([tag_call], lineno=lineno)

    @pass_context
    def _resolve_tag(self, context, tag_name: str, path: Any) -> str:
        normalized = _normalize_asset_path(path)

        if tag_name in {"static", "asset"}:
            resolved = _call_context_or_global(
                context,
                self.environment,
                names=["static", "static_url", "asset", "asset_url"],
                arg=normalized,
            )
            if resolved is not None:
                return resolved

            prefix = getattr(self.environment, "aquilia_static_prefix", "/static")
            return _prefixed_url(prefix, normalized)

        if tag_name == "media":
            resolved = _call_context_or_global(
                context,
                self.environment,
                names=["media", "media_url"],
                arg=normalized,
            )
            if resolved is not None:
                return resolved

            prefix = getattr(self.environment, "aquilia_media_prefix", "/media")
            return _prefixed_url(prefix, normalized)

        # Defensive fallback for unknown tags in case parser extensions change.
        return normalized
