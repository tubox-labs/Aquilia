"""
Aquilia Clearance System — Unique declarative access control.

Unlike DRF's simple ``permission_classes = [...]`` list, Aquilia uses a
*Clearance Matrix* — a multi-dimensional, composable, declarative access
control system that combines:

- **Access Levels**: Hierarchical clearance tiers (PUBLIC → CONFIDENTIAL)
- **Entitlements**: Fine-grained capability tokens (not roles)
- **Conditions**: Runtime predicates evaluated per-request
- **Compartments**: Resource isolation boundaries (multi-tenant)

Usage on a Controller::

    class DocumentController(Controller):
        prefix = "/documents"
        
        clearance = Clearance(
            level=AccessLevel.INTERNAL,
            entitlements=["documents:read"],
            compartment="tenant:{tenant_id}",
        )

        @GET("/")
        @grant(level=AccessLevel.PUBLIC)  # Override: open this route
        async def list_public(self, ctx):
            ...

        @POST("/")
        @grant(
            entitlements=["documents:write"],
            conditions=[is_verified, within_quota],
        )
        async def create(self, ctx):
            ...

        @DELETE("/{doc_id}")
        @grant(
            level=AccessLevel.CONFIDENTIAL,
            entitlements=["documents:delete"],
            conditions=[is_owner_or_admin],
        )
        async def delete(self, ctx, doc_id: str):
            ...

The ``Clearance`` on the class sets baseline requirements. Each ``@grant``
on a method can tighten or relax them. The engine merges class + method
clearances at request time and evaluates the full matrix.
"""

from __future__ import annotations

import enum
import functools
import inspect
import logging
import time
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Optional,
    Protocol,
    Sequence,
    Set,
    Tuple,
    Type,
    Union,
    runtime_checkable,
)


logger = logging.getLogger("aquilia.auth.clearance")


# ============================================================================
# Access Level Hierarchy
# ============================================================================


class AccessLevel(enum.IntEnum):
    """
    Hierarchical access tiers — higher ordinal = stricter.
    
    Each level implicitly grants access to all lower levels.
    A handler at INTERNAL allows identities with INTERNAL, CONFIDENTIAL, 
    or RESTRICTED clearance.
    """
    PUBLIC = 0         # No auth required
    AUTHENTICATED = 10  # Any authenticated identity
    INTERNAL = 20      # Internal/staff identities
    CONFIDENTIAL = 30  # Elevated clearance (managers, leads)
    RESTRICTED = 40    # Highest clearance (admins, security)


# ============================================================================
# Condition Protocol
# ============================================================================


@runtime_checkable
class ClearanceCondition(Protocol):
    """
    A callable predicate evaluated at request time.
    
    Must accept (identity, request, ctx) and return bool.
    Can be sync or async.
    """
    
    def __call__(
        self, identity: Any, request: Any, ctx: Any,
    ) -> Union[bool, Any]:
        ...


# ============================================================================
# Built-in Conditions
# ============================================================================


def is_verified(identity: Any, request: Any, ctx: Any) -> bool:
    """Condition: identity must have 'verified' attribute or status ACTIVE."""
    if identity is None:
        return False
    attrs = getattr(identity, "attributes", {}) or {}
    if attrs.get("email_verified") or attrs.get("verified"):
        return True
    status = getattr(identity, "status", None)
    if status is not None:
        return str(status).upper() in ("ACTIVE", "IDENTITYSTATUS.ACTIVE")
    return False


def is_owner_or_admin(identity: Any, request: Any, ctx: Any) -> bool:
    """Condition: identity is resource owner or has admin role."""
    if identity is None:
        return False
    # Admin check
    roles = getattr(identity, "roles", set()) or set()
    if "admin" in roles or "superuser" in roles:
        return True
    # Owner check — look for resource_owner_id in ctx.state
    state = getattr(ctx, "state", {}) or {}
    owner_id = state.get("resource_owner_id")
    if owner_id is not None:
        identity_id = getattr(identity, "id", None)
        return str(identity_id) == str(owner_id)
    return False


def within_quota(identity: Any, request: Any, ctx: Any) -> bool:
    """Condition: identity hasn't exceeded rate/resource quota."""
    state = getattr(ctx, "state", {}) or {}
    quota_exceeded = state.get("quota_exceeded", False)
    return not quota_exceeded


def is_same_tenant(identity: Any, request: Any, ctx: Any) -> bool:
    """Condition: identity's tenant matches resource tenant."""
    if identity is None:
        return False
    identity_tenant = getattr(identity, "tenant_id", None)
    state = getattr(ctx, "state", {}) or {}
    resource_tenant = state.get("resource_tenant_id")
    if identity_tenant and resource_tenant:
        return str(identity_tenant) == str(resource_tenant)
    # If no tenant context, allow (tenant isolation is opt-in)
    return resource_tenant is None


def during_hours(start: int = 9, end: int = 17) -> Callable:
    """Factory: condition that restricts access to business hours (UTC)."""
    def _check(identity: Any, request: Any, ctx: Any) -> bool:
        import datetime
        hour = datetime.datetime.now(datetime.timezone.utc).hour
        return start <= hour < end
    _check.__name__ = f"during_hours({start}-{end})"
    _check.__qualname__ = _check.__name__
    return _check


def require_attribute(key: str, value: Any = None) -> Callable:
    """Factory: condition that requires a specific identity attribute."""
    def _check(identity: Any, request: Any, ctx: Any) -> bool:
        if identity is None:
            return False
        attrs = getattr(identity, "attributes", {}) or {}
        if value is None:
            return key in attrs and attrs[key]
        return attrs.get(key) == value
    _check.__name__ = f"require_attribute({key!r})"
    _check.__qualname__ = _check.__name__
    return _check


def ip_allowlist(*cidrs: str) -> Callable:
    """Factory: condition restricting access to specific IP ranges."""
    import ipaddress
    networks = []
    for cidr in cidrs:
        try:
            networks.append(ipaddress.ip_network(cidr, strict=False))
        except ValueError:
            pass
    
    def _check(identity: Any, request: Any, ctx: Any) -> bool:
        client_ip = None
        if hasattr(request, "client") and request.client:
            client_ip = request.client[0] if isinstance(request.client, tuple) else request.client
        if not client_ip:
            state = getattr(request, "state", {})
            client_ip = state.get("client_ip") if isinstance(state, dict) else None
        if not client_ip:
            return len(networks) == 0  # No IP available - allow only if no restrictions
        try:
            addr = ipaddress.ip_address(client_ip)
            return any(addr in net for net in networks)
        except ValueError:
            return False
    _check.__name__ = f"ip_allowlist({','.join(cidrs)})"
    _check.__qualname__ = _check.__name__
    return _check


# ============================================================================
# Clearance Descriptor
# ============================================================================


@dataclass(frozen=True, slots=True)
class Clearance:
    """
    Immutable clearance requirement descriptor.
    
    Declaratively specifies the access matrix for a controller or route.
    """
    level: AccessLevel = AccessLevel.AUTHENTICATED
    entitlements: Tuple[str, ...] = ()
    conditions: Tuple[Callable, ...] = ()
    compartment: Optional[str] = None  # Template: "tenant:{tenant_id}"
    deny_message: str = "Insufficient clearance"
    audit: bool = True  # Log access decisions
    
    def __init__(
        self,
        level: AccessLevel = AccessLevel.AUTHENTICATED,
        entitlements: Sequence[str] = (),
        conditions: Sequence[Callable] = (),
        compartment: Optional[str] = None,
        deny_message: str = "Insufficient clearance",
        audit: bool = True,
    ):
        object.__setattr__(self, "level", AccessLevel(level))
        object.__setattr__(self, "entitlements", tuple(entitlements))
        object.__setattr__(self, "conditions", tuple(conditions))
        object.__setattr__(self, "compartment", compartment)
        object.__setattr__(self, "deny_message", deny_message)
        object.__setattr__(self, "audit", audit)
    
    def merge(self, override: Clearance) -> Clearance:
        """
        Merge this (class-level) clearance with an override (method-level).
        
        Rules:
        - Level: override wins if specified (non-AUTHENTICATED default)
        - Entitlements: union of both
        - Conditions: union of both
        - Compartment: override wins if specified
        - Deny message: override wins if different from default
        """
        merged_level = override.level if override.level != AccessLevel.AUTHENTICATED else self.level
        # If override explicitly set level, use it even if AUTHENTICATED
        if override.level != self.level and override.level == AccessLevel.AUTHENTICATED:
            merged_level = self.level
        if override.level != AccessLevel.AUTHENTICATED or self.level == AccessLevel.AUTHENTICATED:
            merged_level = override.level if override.level != AccessLevel.AUTHENTICATED else self.level
        
        # Actually simpler: override always wins for level
        merged_level = override.level
        
        merged_entitlements = tuple(set(self.entitlements) | set(override.entitlements))
        merged_conditions = tuple(list(self.conditions) + [
            c for c in override.conditions if c not in self.conditions
        ])
        merged_compartment = override.compartment or self.compartment
        merged_deny = (
            override.deny_message 
            if override.deny_message != "Insufficient clearance" 
            else self.deny_message
        )
        merged_audit = override.audit
        
        return Clearance(
            level=merged_level,
            entitlements=merged_entitlements,
            conditions=merged_conditions,
            compartment=merged_compartment,
            deny_message=merged_deny,
            audit=merged_audit,
        )


# ============================================================================
# Clearance Verdict (evaluation result)
# ============================================================================


@dataclass(frozen=True, slots=True)
class ClearanceVerdict:
    """Result of a clearance evaluation."""
    granted: bool
    level_ok: bool
    entitlements_ok: bool
    conditions_ok: bool
    compartment_ok: bool
    missing_entitlements: Tuple[str, ...] = ()
    failed_conditions: Tuple[str, ...] = ()
    message: str = ""
    evaluated_at: float = 0.0
    identity_id: Optional[str] = None
    
    def __init__(
        self,
        granted: bool,
        level_ok: bool = True,
        entitlements_ok: bool = True,
        conditions_ok: bool = True,
        compartment_ok: bool = True,
        missing_entitlements: Sequence[str] = (),
        failed_conditions: Sequence[str] = (),
        message: str = "",
        evaluated_at: float = 0.0,
        identity_id: Optional[str] = None,
    ):
        object.__setattr__(self, "granted", granted)
        object.__setattr__(self, "level_ok", level_ok)
        object.__setattr__(self, "entitlements_ok", entitlements_ok)
        object.__setattr__(self, "conditions_ok", conditions_ok)
        object.__setattr__(self, "compartment_ok", compartment_ok)
        object.__setattr__(self, "missing_entitlements", tuple(missing_entitlements))
        object.__setattr__(self, "failed_conditions", tuple(failed_conditions))
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "evaluated_at", evaluated_at or time.time())
        object.__setattr__(self, "identity_id", identity_id)


# ============================================================================
# Grant Decorator (method-level clearance)
# ============================================================================


_CLEARANCE_ATTR = "__aquilia_clearance__"


def grant(
    level: AccessLevel = AccessLevel.AUTHENTICATED,
    entitlements: Sequence[str] = (),
    conditions: Sequence[Callable] = (),
    compartment: Optional[str] = None,
    deny_message: str = "Insufficient clearance",
    audit: bool = True,
) -> Callable:
    """
    Decorator to attach clearance requirements to a route method.
    
    Usage::
    
        @GET("/")
        @grant(level=AccessLevel.INTERNAL, entitlements=["docs:read"])
        async def list_docs(self, ctx):
            ...
    """
    clearance = Clearance(
        level=level,
        entitlements=entitlements,
        conditions=conditions,
        compartment=compartment,
        deny_message=deny_message,
        audit=audit,
    )
    
    def decorator(fn: Callable) -> Callable:
        setattr(fn, _CLEARANCE_ATTR, clearance)
        return fn
    
    return decorator


def exempt(fn: Callable) -> Callable:
    """
    Decorator to exempt a route from class-level clearance.
    
    Sets the clearance level to PUBLIC with no other requirements.
    
    Usage::
    
        @GET("/health")
        @exempt
        async def health(self, ctx):
            return {"status": "ok"}
    """
    setattr(fn, _CLEARANCE_ATTR, Clearance(
        level=AccessLevel.PUBLIC,
        entitlements=(),
        conditions=(),
        audit=False,
    ))
    return fn


def get_method_clearance(method: Any) -> Optional[Clearance]:
    """Extract clearance from a decorated method."""
    return getattr(method, _CLEARANCE_ATTR, None)


# ============================================================================
# Clearance Engine
# ============================================================================


class ClearanceEngine:
    """
    Evaluates clearance requirements against request context.
    
    Thread-safe, stateless evaluator. Instantiate once at app level.
    """
    
    _identity_level_cache: ClassVar[Dict[str, AccessLevel]] = {}
    
    def __init__(
        self,
        role_level_map: Optional[Dict[str, AccessLevel]] = None,
        entitlement_resolver: Optional[Callable] = None,
        audit_logger: Optional[logging.Logger] = None,
        deny_by_default: bool = True,
    ):
        """
        Args:
            role_level_map: Maps role names to access levels.
                            Default: {"admin": RESTRICTED, "staff": INTERNAL, ...}
            entitlement_resolver: Custom callable to resolve entitlements
                                  from identity. Receives (identity) -> Set[str].
            audit_logger: Logger for access decisions.
            deny_by_default: If True, deny when no clearance is specified.
        """
        self.role_level_map = role_level_map or {
            "superuser": AccessLevel.RESTRICTED,
            "admin": AccessLevel.RESTRICTED,
            "manager": AccessLevel.CONFIDENTIAL,
            "staff": AccessLevel.INTERNAL,
            "user": AccessLevel.AUTHENTICATED,
        }
        self.entitlement_resolver = entitlement_resolver
        self.audit_logger = audit_logger or logger
        self.deny_by_default = deny_by_default
    
    def resolve_identity_level(self, identity: Any) -> AccessLevel:
        """Determine the highest AccessLevel an identity holds."""
        if identity is None:
            return AccessLevel.PUBLIC
        
        # Check cache
        identity_id = str(getattr(identity, "id", id(identity)))
        cached = self._identity_level_cache.get(identity_id)
        if cached is not None:
            return cached
        
        # Determine from roles
        roles = getattr(identity, "roles", set()) or set()
        highest = AccessLevel.AUTHENTICATED  # Any identity gets at least this
        
        for role in roles:
            role_str = str(role).lower()
            mapped = self.role_level_map.get(role_str, AccessLevel.AUTHENTICATED)
            if mapped > highest:
                highest = mapped
        
        # Check identity attributes for explicit level
        attrs = getattr(identity, "attributes", {}) or {}
        explicit_level = attrs.get("access_level") or attrs.get("clearance_level")
        if explicit_level is not None:
            try:
                explicit = AccessLevel(int(explicit_level))
                if explicit > highest:
                    highest = explicit
            except (ValueError, TypeError):
                pass
        
        self._identity_level_cache[identity_id] = highest
        return highest
    
    def resolve_entitlements(self, identity: Any) -> Set[str]:
        """Resolve the set of entitlements an identity holds."""
        if identity is None:
            return set()
        
        # Custom resolver
        if self.entitlement_resolver:
            result = self.entitlement_resolver(identity)
            return set(result) if result else set()
        
        # Default: combine scopes + permissions from roles
        entitlements: Set[str] = set()
        
        # Scopes (OAuth-style)
        scopes = getattr(identity, "scopes", set()) or set()
        entitlements.update(str(s) for s in scopes)
        
        # Permissions (RBAC-style, from authz engine)
        permissions = getattr(identity, "permissions", set()) or set()
        entitlements.update(str(p) for p in permissions)
        
        # Attributes may carry entitlements
        attrs = getattr(identity, "attributes", {}) or {}
        attr_entitlements = attrs.get("entitlements") or attrs.get("capabilities")
        if attr_entitlements:
            if isinstance(attr_entitlements, (list, tuple, set, frozenset)):
                entitlements.update(str(e) for e in attr_entitlements)
            elif isinstance(attr_entitlements, str):
                entitlements.update(attr_entitlements.split(","))
        
        return entitlements
    
    def resolve_compartment(
        self,
        compartment_template: Optional[str],
        identity: Any,
        request: Any,
        ctx: Any,
    ) -> Optional[str]:
        """Resolve a compartment template to a concrete value."""
        if not compartment_template:
            return None
        
        # Gather substitution values
        values: Dict[str, str] = {}
        
        # From identity
        if identity:
            values["identity_id"] = str(getattr(identity, "id", ""))
            values["tenant_id"] = str(getattr(identity, "tenant_id", "") or "")
            for k, v in (getattr(identity, "attributes", {}) or {}).items():
                values[f"identity.{k}"] = str(v)
        
        # From request state
        state = getattr(ctx, "state", {}) or {}
        if isinstance(state, dict):
            for k, v in state.items():
                values[k] = str(v)
        
        # From path params
        if hasattr(request, "path_params"):
            for k, v in (request.path_params or {}).items():
                values[k] = str(v)
        
        # Substitute
        try:
            resolved = compartment_template.format(**values)
        except (KeyError, IndexError):
            resolved = compartment_template
        
        return resolved
    
    async def evaluate(
        self,
        clearance: Clearance,
        identity: Any,
        request: Any,
        ctx: Any,
    ) -> ClearanceVerdict:
        """
        Evaluate a clearance requirement against the current context.
        
        Returns a ClearanceVerdict with detailed results.
        """
        identity_id = str(getattr(identity, "id", None))
        
        # 1. Level check
        identity_level = self.resolve_identity_level(identity)
        level_ok = identity_level >= clearance.level
        
        # PUBLIC level means no auth needed
        if clearance.level == AccessLevel.PUBLIC:
            level_ok = True
        
        # 2. Entitlements check
        missing_entitlements: List[str] = []
        if clearance.entitlements:
            held = self.resolve_entitlements(identity)
            for required in clearance.entitlements:
                # Support wildcard: "documents:*" matches "documents:read"
                if required.endswith(":*"):
                    prefix = required[:-1]  # "documents:"
                    if not any(e.startswith(prefix) for e in held):
                        missing_entitlements.append(required)
                elif required not in held:
                    missing_entitlements.append(required)
        entitlements_ok = len(missing_entitlements) == 0
        
        # 3. Conditions check
        failed_conditions: List[str] = []
        if clearance.conditions:
            for cond in clearance.conditions:
                try:
                    if inspect.iscoroutinefunction(cond):
                        result = await cond(identity, request, ctx)
                    else:
                        result = cond(identity, request, ctx)
                    if not result:
                        name = getattr(cond, "__name__", str(cond))
                        failed_conditions.append(name)
                except Exception as e:
                    name = getattr(cond, "__name__", str(cond))
                    failed_conditions.append(f"{name}(error:{e})")
        conditions_ok = len(failed_conditions) == 0
        
        # 4. Compartment check
        compartment_ok = True
        if clearance.compartment:
            resolved = self.resolve_compartment(
                clearance.compartment, identity, request, ctx,
            )
            if resolved and identity:
                # Check that identity belongs to this compartment
                identity_tenant = str(getattr(identity, "tenant_id", "") or "")
                if "tenant:" in (clearance.compartment or ""):
                    if resolved.startswith("tenant:"):
                        expected_tenant = resolved[7:]  # After "tenant:"
                        compartment_ok = identity_tenant == expected_tenant
        
        # Overall verdict
        granted = level_ok and entitlements_ok and conditions_ok and compartment_ok
        
        # Build message
        if granted:
            message = "Access granted"
        else:
            parts = []
            if not level_ok:
                parts.append(
                    f"requires {clearance.level.name} (identity has {identity_level.name})"
                )
            if missing_entitlements:
                parts.append(f"missing entitlements: {', '.join(missing_entitlements)}")
            if failed_conditions:
                parts.append(f"failed conditions: {', '.join(failed_conditions)}")
            if not compartment_ok:
                parts.append("compartment mismatch")
            message = clearance.deny_message + " — " + "; ".join(parts)
        
        verdict = ClearanceVerdict(
            granted=granted,
            level_ok=level_ok,
            entitlements_ok=entitlements_ok,
            conditions_ok=conditions_ok,
            compartment_ok=compartment_ok,
            missing_entitlements=missing_entitlements,
            failed_conditions=failed_conditions,
            message=message,
            identity_id=identity_id,
        )
        
        # Audit log
        if clearance.audit:
            action = "GRANTED" if granted else "DENIED"
            self.audit_logger.info(
                f"Clearance {action} | identity={identity_id} "
                f"level={clearance.level.name} "
                f"entitlements={clearance.entitlements} "
                f"message={message}"
            )
        
        return verdict
    
    def clear_cache(self) -> None:
        """Clear identity level cache."""
        self._identity_level_cache.clear()


# ============================================================================
# Clearance Guard (for pipeline integration)
# ============================================================================


class ClearanceGuard:
    """
    Pipeline guard that enforces Clearance requirements.
    
    Integrates with both Flow pipeline and Controller pipeline.
    """
    
    def __init__(
        self,
        clearance: Clearance,
        engine: Optional[ClearanceEngine] = None,
    ):
        self.clearance = clearance
        self.engine = engine or ClearanceEngine()
    
    async def __call__(
        self, request: Any = None, ctx: Any = None, **kwargs
    ) -> Any:
        """Execute as pipeline guard."""
        identity = None
        if ctx is not None:
            identity = getattr(ctx, "identity", None)
        if identity is None and request is not None:
            state = getattr(request, "state", {})
            identity = state.get("identity") if isinstance(state, dict) else None
        
        verdict = await self.engine.evaluate(
            self.clearance, identity, request, ctx,
        )
        
        if not verdict.granted:
            # Store verdict in state for error handlers
            if ctx and hasattr(ctx, "state") and isinstance(ctx.state, dict):
                ctx.state["clearance_verdict"] = verdict
            
            from ..response import Response
            status = 401 if not verdict.level_ok and self.clearance.level > AccessLevel.PUBLIC else 403
            return Response.json(
                {
                    "error": {
                        "code": "CLEARANCE_DENIED",
                        "message": verdict.message,
                        "missing_entitlements": list(verdict.missing_entitlements),
                        "failed_conditions": list(verdict.failed_conditions),
                    }
                },
                status=status,
            )
        
        # Store successful verdict
        if ctx and hasattr(ctx, "state") and isinstance(ctx.state, dict):
            ctx.state["clearance_verdict"] = verdict
        
        return True
    
    def for_controller(self) -> ClearanceGuard:
        """Return self — already works as controller pipeline guard."""
        return self


# ============================================================================
# Controller Clearance Metaclass Hook
# ============================================================================


def extract_controller_clearance(controller_class: type) -> Optional[Clearance]:
    """Extract clearance from controller class."""
    return getattr(controller_class, "clearance", None)


def build_merged_clearance(
    controller_class: type,
    handler_method: Any,
) -> Optional[Clearance]:
    """Build merged clearance from class + method."""
    class_clearance = extract_controller_clearance(controller_class)
    method_clearance = get_method_clearance(handler_method)
    
    if class_clearance is None and method_clearance is None:
        return None
    
    if class_clearance is None:
        return method_clearance
    
    if method_clearance is None:
        return class_clearance
    
    return class_clearance.merge(method_clearance)


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    # Core types
    "AccessLevel",
    "Clearance",
    "ClearanceVerdict",
    "ClearanceEngine",
    "ClearanceGuard",
    "ClearanceCondition",
    # Decorators
    "grant",
    "exempt",
    "get_method_clearance",
    # Helpers
    "extract_controller_clearance",
    "build_merged_clearance",
    # Built-in conditions
    "is_verified",
    "is_owner_or_admin",
    "within_quota",
    "is_same_tenant",
    "during_hours",
    "require_attribute",
    "ip_allowlist",
]
