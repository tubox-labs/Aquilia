"""Priority constants and the ordering sort key.

Ascending priority = outer = runs first. The framework's assignments used to
live in a docstring table in ``server.py`` with a comment asking humans to keep
it in step with the ``add()`` calls below it. They live here now, where a wrong
value is a diff instead of a stale comment.

Import nothing but :mod:`aquilia.middleware.utils.ordering` here — this module
is inside the fault-free leaf zone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.middleware.utils.ordering import scope_rank

if TYPE_CHECKING:
    from aquilia.middleware.core.descriptor import MiddlewareDescriptor

# Ordering bands. The prefix before ``:`` in a scope string selects the band;
# unknown bands sort last (rank 99) so foreign middleware still runs, just after
# the framework tiers.
SCOPE_ORDER: dict[str, int] = {"global": 0, "app": 1, "controller": 2, "route": 3}


class Priority:
    """Framework middleware priorities.

    These are the exact values the framework registers today. The relative
    order is load-bearing for the security controls, not cosmetic — the
    constraints are noted per entry.

    Reserved bands:

    ==================  =========================================
    ``0-9``             framework plumbing (faults, request scope)
    ``10-29``           security controls
    ``30-49``           framework features
    ``50-99``           application middleware
    ==================  =========================================
    """

    # ── Plumbing ──────────────────────────────────────────────────────────
    EXCEPTION = 1
    FAULTS = 2
    PROXY_FIX = 3  # must precede anything IP-dependent
    HTTPS_REDIRECT = 4
    REQUEST_SCOPE = 5
    #: Known collision with ``REQUEST_SCOPE``. Both register at
    #: ``global``/5, so their relative order falls back to registration
    #: order and the stack warns at boot. Preserved as-is because changing
    #: it would silently reorder an existing deployment; naming it here is
    #: what makes the clash visible instead of buried in two call sites.
    VERSIONING = 5
    STATIC = 6  # serve files before heavy processing

    # ── Security ──────────────────────────────────────────────────────────
    SECURITY_HEADERS = 7
    HSTS = 8
    CSP = 9
    REQUEST_ID = 10
    CORS = 11
    RATE_LIMIT_ANON = 12  # anonymous/IP rules only
    INSPECTOR = 13
    INSPECTOR_TOOLBAR = 14
    AUTH = 15  # AquilAuthMiddleware / SessionMiddleware
    RATE_LIMIT_IDENTITY = 16  # identity rules; must follow AUTH
    CSRF = 20  # needs the session established by AUTH

    # ── Framework features ────────────────────────────────────────────────
    I18N = 24  # after AUTH (locale may come from the user), before TEMPLATES
    TEMPLATES = 25
    CACHE = 26

    # ── Applications ──────────────────────────────────────────────────────
    APPLICATION_DEFAULT = 50


PLUMBING_BAND = range(0, 10)
SECURITY_BAND = range(10, 30)
FRAMEWORK_BAND = range(30, 50)
APPLICATION_BAND = range(50, 100)


def sort_key(descriptor: MiddlewareDescriptor) -> tuple[int, int]:
    """Ordering key: ``(scope_rank, priority)``, both ascending.

    The sort is stable, so same-``(scope, priority)`` pairs fall back to
    registration order. That is an implementation detail rather than a
    guarantee, which is exactly why the registry reports collisions.
    """
    return (scope_rank(str(descriptor.scope), SCOPE_ORDER), descriptor.priority)


__all__ = [
    "SCOPE_ORDER",
    "Priority",
    "PLUMBING_BAND",
    "SECURITY_BAND",
    "FRAMEWORK_BAND",
    "APPLICATION_BAND",
    "sort_key",
]
