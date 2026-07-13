"""
AquilAuth - Unified Permission Engine

Single authorization system that replaces the five parallel systems that
existed previously (``RBACEngine``, ``ABACEngine``, ``AuthzEngine``,
``ClearanceEngine``, ``PolicyRegistry``).

Design:
    * Roles are flat strings.  Role inheritance is modelled via a directed
      acyclic graph where each parent role implies all child roles.
    * Scopes are plain ``scope:action`` strings.  Wildcard ``"*"`` grants all.
    * Policies are arbitrary callables ``(Identity, resource?) -> bool``.
    * All three checks are exposed through a single ``PermissionEngine``.

Example::

    engine = PermissionEngine()
    engine.define_role("admin", inherits=["editor"])
    engine.define_role("editor", permissions=["posts:write"])
    engine.register_policy("can_publish", lambda identity, _: identity.has_role("editor"))

    # In a guard or controller:
    engine.check_role(identity, "admin")     # raises AUTHZ_INSUFFICIENT_ROLE on fail
    engine.check_scope(identity, "posts:write")  # raises AUTHZ_INSUFFICIENT_SCOPE on fail
    engine.check_policy("can_publish", identity)  # raises AUTHZ_POLICY_DENIED on fail
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .core import Identity


PolicyCallable = Callable[["Identity", Any], bool]


class PermissionEngine:
    """
    Unified authorization engine combining RBAC, scope-based, and policy-based
    access control in a single consistent API.

    All three check methods raise the appropriate auth fault on denial; they
    never return ``False`` — callers do not need to inspect a return value.

    Attributes:
        _roles:    Mapping of role name to its direct parent role names.
        _perms:    Mapping of role name to the set of permissions it grants.
        _policies: Mapping of policy key to its evaluation callable.
    """

    def __init__(self) -> None:
        self._roles: dict[str, set[str]] = {}  # role -> set of parent roles
        self._perms: dict[str, set[str]] = {}  # role -> set of permissions
        self._policies: dict[str, PolicyCallable] = {}

    # ── Role management ──────────────────────────────────────────────────────

    def define_role(
        self,
        role: str,
        *,
        permissions: list[str] | None = None,
        inherits: list[str] | None = None,
    ) -> None:
        """
        Declare a named role with optional permissions and parent roles.

        Args:
            role:        Role name (e.g. ``"admin"``).
            permissions: Permissions directly granted by this role
                         (e.g. ``["users:read", "users:write"]``).
            inherits:    Parent roles whose permissions are also inherited.

        Example::

            engine.define_role("admin", inherits=["editor"])
            engine.define_role("editor", permissions=["posts:write"])
        """
        self._roles[role] = set(inherits or [])
        self._perms[role] = set(permissions or [])

    def role_implies(self, role: str, target: str) -> bool:
        """
        Return ``True`` when *role* implies *target* (directly or transitively).

        Args:
            role:   The role being tested.
            target: The role that must be implied.
        """
        visited: set[str] = set()
        queue = [role]
        while queue:
            current = queue.pop()
            if current in visited:
                continue
            visited.add(current)
            if current == target:
                return True
            queue.extend(self._roles.get(current, set()))
        return False

    # ── Policy management ────────────────────────────────────────────────────

    def register_policy(self, key: str, policy: PolicyCallable) -> None:
        """
        Register a named policy callable.

        Args:
            key:    Unique policy identifier (e.g. ``"can_publish"``).
            policy: Callable ``(identity: Identity, resource: Any = None) -> bool``.
                    Return ``True`` to allow, ``False`` to deny.

        Example::

            engine.register_policy(
                "can_edit_post",
                lambda identity, post: identity.id == post.author_id,
            )
        """
        self._policies[key] = policy

    # ── Authorization checks ─────────────────────────────────────────────────

    def check_role(self, identity: Identity, role: str) -> None:
        """
        Assert that *identity* holds *role* (directly or through inheritance).

        Raises:
            ``AUTHZ_INSUFFICIENT_ROLE``: Identity does not have the required role.
        """
        from .faults import AUTHZ_INSUFFICIENT_ROLE

        identity_roles: list[str] = identity.get_attribute("roles", [])
        for held in identity_roles:
            if held == role or self.role_implies(held, role):
                return
        raise AUTHZ_INSUFFICIENT_ROLE(required_roles=[role])

    def check_scope(self, identity: Identity, scope: str) -> None:
        """
        Assert that *identity* holds *scope* or the wildcard ``"*"`` scope.

        Raises:
            ``AUTHZ_INSUFFICIENT_SCOPE``: Identity does not hold the required scope.
        """
        from .faults import AUTHZ_INSUFFICIENT_SCOPE

        if not identity.has_scope(scope):
            raise AUTHZ_INSUFFICIENT_SCOPE(required_scopes=[scope])

    def check_policy(
        self,
        key: str,
        identity: Identity,
        resource: Any = None,
    ) -> None:
        """
        Evaluate the named policy and raise if it denies access.

        Args:
            key:      Policy key registered via :meth:`register_policy`.
            identity: The authenticated identity to check.
            resource: Optional resource object passed to the policy callable.

        Raises:
            ``AUTHZ_POLICY_DENIED``: Policy returned ``False``.
            ``KeyError``:            Unknown policy key.
        """
        from .faults import AUTHZ_POLICY_DENIED

        policy = self._policies.get(key)
        if policy is None:
            raise KeyError(f"Unknown policy key: {key!r}")

        try:
            result = policy(identity, resource)
        except Exception as exc:
            raise AUTHZ_POLICY_DENIED(policy_id=key, reason=str(exc)) from exc

        if not result:
            raise AUTHZ_POLICY_DENIED(policy_id=key)

    def has_role(self, identity: Identity, role: str) -> bool:
        """Return ``True`` when *identity* holds *role* without raising."""
        try:
            self.check_role(identity, role)
            return True
        except Exception:
            return False

    def has_scope(self, identity: Identity, scope: str) -> bool:
        """Return ``True`` when *identity* holds *scope* without raising."""
        return identity.has_scope(scope)

    def evaluate_policy(
        self,
        key: str,
        identity: Identity,
        resource: Any = None,
    ) -> bool:
        """Return ``True`` when the named policy allows *identity* without raising."""
        try:
            self.check_policy(key, identity, resource)
            return True
        except Exception:
            return False


__all__ = [
    "PermissionEngine",
    "PolicyCallable",
]
