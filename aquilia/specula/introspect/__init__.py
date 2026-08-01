"""Specula introspection — routes, security, effects, and multi-version specs."""

from aquilia.specula.introspect.effects import EFFECT_DOCS, handler_effects
from aquilia.specula.introspect.routes import enrich_routes
from aquilia.specula.introspect.security import GUARD_SCHEME_MAP, scheme_for_guard
from aquilia.specula.introspect.versions import VersionedSpecBuilder

__all__ = [
    "VersionedSpecBuilder",
    "enrich_routes",
    "handler_effects",
    "EFFECT_DOCS",
    "scheme_for_guard",
    "GUARD_SCHEME_MAP",
]
