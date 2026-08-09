"""Transport-agnostic middleware utilities.

Everything here is shared between the HTTP stack and
``aquilia.sockets.middleware`` — ordering rules, rate-limit accounting, content
negotiation, fault-to-status mapping. The hard rule that made these useful as
underscore-prefixed leaf modules still applies: **import nothing from the rest
of the framework.**

That constraint is why the socket stack can use them without dragging HTTP
middleware into its import graph.
"""

from aquilia.middleware.utils.negotiation import accept_header, wants_html
from aquilia.middleware.utils.ordering import collision_message, find_collision, scope_rank
from aquilia.middleware.utils.status import DOMAIN_STATUS, fault_to_status
from aquilia.middleware.utils.throttling import (
    NEVER_REFILLS_RETRY_AFTER,
    BucketStore,
    SlidingWindowCounter,
    TokenBucket,
)

__all__ = [
    "scope_rank",
    "find_collision",
    "collision_message",
    "TokenBucket",
    "SlidingWindowCounter",
    "BucketStore",
    "NEVER_REFILLS_RETRY_AFTER",
    "accept_header",
    "wants_html",
    "fault_to_status",
    "DOMAIN_STATUS",
]
