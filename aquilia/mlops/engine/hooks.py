"""
Pipeline Hooks -- decorator-based lifecycle and inference hooks.

Hooks are attached to model classes and collected at registration time.
The ``InferencePipeline`` calls them in order at each stage.

Decorators::

    @on_load       -- called after model is loaded
    @on_unload     -- called before model is unloaded
    @preprocess    -- transforms raw inputs before inference
    @postprocess   -- transforms raw outputs after inference
    @before_predict -- cross-cutting hook called before each prediction
    @after_predict  -- cross-cutting hook called after each prediction
    @on_error      -- error handler for inference failures

Usage::

    @model(name="sentiment", version="v1")
    class SentimentModel(AquiliaModel):

        @on_load
        async def warmup(self):
            self.pipeline = load_pipeline(...)

        @preprocess
        async def clean(self, inputs):
            return {"text": inputs["text"].strip()}

        @on_error
        async def handle(self, error, request):
            logger.error("Inference failed: %s", error)
            return {"error": str(error)}
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# ── Hook attribute markers ───────────────────────────────────────────────

_HOOK_ATTR = "__mlops_hook__"


def _mark_hook(kind: str) -> Callable[[F], F]:
    """Create a decorator that marks a method as a specific hook type."""

    def decorator(fn: F) -> F:
        hooks: list[str] = getattr(fn, _HOOK_ATTR, [])
        hooks.append(kind)
        setattr(fn, _HOOK_ATTR, hooks)
        return fn

    return decorator


# ── Public Decorators ────────────────────────────────────────────────────


def on_load(fn: F) -> F:
    """Mark method as a post-load lifecycle hook."""
    return _mark_hook("on_load")(fn)


def on_unload(fn: F) -> F:
    """Mark method as a pre-unload lifecycle hook."""
    return _mark_hook("on_unload")(fn)


def preprocess(fn: F) -> F:
    """Mark method as input preprocessor."""
    return _mark_hook("preprocess")(fn)


def postprocess(fn: F) -> F:
    """Mark method as output postprocessor."""
    return _mark_hook("postprocess")(fn)


def before_predict(fn: F) -> F:
    """Mark method as a before-prediction hook."""
    return _mark_hook("before_predict")(fn)


def after_predict(fn: F) -> F:
    """Mark method as an after-prediction hook."""
    return _mark_hook("after_predict")(fn)


def on_error(fn: F) -> F:
    """Mark method as an inference error handler."""
    return _mark_hook("on_error")(fn)


# ── Hook Collection ──────────────────────────────────────────────────────


class HookRegistry:
    """
    Collected hooks from a model class.

    Each hook kind maps to a list of bound methods (in declaration order).
    """

    __slots__ = (
        "on_load",
        "on_unload",
        "preprocess",
        "postprocess",
        "before_predict",
        "after_predict",
        "on_error",
    )

    def __init__(self) -> None:
        self.on_load: list[Callable] = []
        self.on_unload: list[Callable] = []
        self.preprocess: list[Callable] = []
        self.postprocess: list[Callable] = []
        self.before_predict: list[Callable] = []
        self.after_predict: list[Callable] = []
        self.on_error: list[Callable] = []

    def get(self, kind: str) -> list[Callable]:
        """Get hooks by kind name."""
        return getattr(self, kind, [])

    def has(self, kind: str) -> bool:
        """Check if any hooks of this kind are registered."""
        return bool(self.get(kind))

    def summary(self) -> dict[str, int]:
        """Return counts of registered hooks per kind."""
        return {
            kind: len(self.get(kind))
            for kind in (
                "on_load",
                "on_unload",
                "preprocess",
                "postprocess",
                "before_predict",
                "after_predict",
                "on_error",
            )
        }


def collect_hooks(instance: Any) -> HookRegistry:
    """
    Scan an object instance for decorated hook methods.

    Returns a ``HookRegistry`` with all discovered hooks bound to
    the instance.
    """
    registry = HookRegistry()

    for name in dir(instance):
        if name.startswith("_") and name != "__call__":
            continue
        try:
            method = getattr(instance, name)
        except Exception:
            continue

        if not callable(method):
            continue

        hooks: list[str] = getattr(method, _HOOK_ATTR, [])
        for kind in hooks:
            hook_list = registry.get(kind)
            if hook_list is not None:
                hook_list.append(method)

    return registry
