"""Middleware registration, validation, and chain compilation.

Layer boundary: this subpackage may import :mod:`aquilia.faults`;
:mod:`aquilia.middleware.core` may not. Concrete middleware under ``builtin/``
must not import from here — they depend on ``core`` only, so the stack can
import them without a cycle.
"""

from aquilia.middleware.stack.builder import ChainBuilder, enforce_contract
from aquilia.middleware.stack.errors import (
    MiddlewareContractFault,
    MiddlewarePriorityCollisionFault,
    MiddlewareRegistrationFault,
)
from aquilia.middleware.stack.registry import MiddlewareStack
from aquilia.middleware.stack.validation import is_noop, validate, validate_hooks

__all__ = [
    "MiddlewareStack",
    "ChainBuilder",
    "enforce_contract",
    "MiddlewareRegistrationFault",
    "MiddlewarePriorityCollisionFault",
    "MiddlewareContractFault",
    "validate",
    "validate_hooks",
    "is_noop",
]
