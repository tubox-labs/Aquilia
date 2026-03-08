"""
Aquilia Admin — Data Models
============================

Purpose-built models for the Aquilia admin subsystem.

Architecture
------------
Only four tables hit the database:

    aq_admin_users        — operator accounts with role-based access
    aq_admin_audit        — immutable append-only audit trail
    aq_admin_api_keys     — scoped, hashed API keys for programmatic access
    aq_admin_preferences  — per-user UI / workflow preferences (JSON blob)

Permissions live **in memory** (see ``permissions.py``).  The ``AdminUser.role``
column is the single join-point between the persisted identity and the runtime
RBAC matrix — no M2M tables, no extra joins at request time.

Backward Compatibility
----------------------
Legacy names (``ContentType``, ``AdminPermission``, ``AdminGroup``,
``AdminLogEntry``, ``AdminSession``) are kept as thin stubs so that existing
import paths don't break.  Each stub carries ``_HAS_ORM = False`` — the
registry and migration pipeline skip them automatically.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.auth.core import Identity

try:
    from aquilia.models import (
        Model,
        CharField,
        TextField,
        BooleanField,
        IntegerField,
        DateTimeField,
        JSONField,
    )

    _ORM_AVAILABLE = True
except ImportError:
    _ORM_AVAILABLE = False

# Password hashing — use framework's Argon2id/PBKDF2 hasher
try:
    from aquilia.auth.hashing import PasswordHasher as _PasswordHasher

    _pw_hasher = _PasswordHasher()
except Exception:
    _pw_hasher = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Prefix stamped on every raw API key so leaked tokens are easy to grep.
API_KEY_PREFIX = "aq_"

#: Length (bytes) of the random portion of an API key.
API_KEY_ENTROPY = 32

#: Default role assigned to new admin users.
DEFAULT_ROLE = "staff"

#: Roles recognised by the in-memory RBAC matrix.
VALID_ROLES = ("superadmin", "staff", "viewer")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_utc() -> str:
    """ISO-8601 UTC timestamp string suitable for ``CharField`` storage."""
    return datetime.now(timezone.utc).isoformat()


def _generate_api_key() -> str:
    """Return a new raw API key with the ``aq_`` prefix.

    The key is **not** stored — only its SHA-256 hash is persisted.
    """
    return f"{API_KEY_PREFIX}{secrets.token_urlsafe(API_KEY_ENTROPY)}"


def _hash_api_key(raw_key: str) -> str:
    """Deterministic SHA-256 hex digest of a raw API key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
#  ACTIVE ORM MODELS  (4 tables)
# ═══════════════════════════════════════════════════════════════════════════

if _ORM_AVAILABLE:

    # -------------------------------------------------------------------
    #  AdminUser
    # -------------------------------------------------------------------

    class AdminUser(Model):
        """Operator account for the Aquilia admin panel.

        Design notes
        ~~~~~~~~~~~~
        * ``role`` is a plain ``CharField`` whose value must be one of
          :data:`VALID_ROLES`.  All fine-grained permission checks are
          delegated to the in-memory RBAC matrix in ``permissions.py``.
        * ``password_hash`` stores an Argon2id (or PBKDF2-SHA256 fallback)
          digest — never the plaintext password.
        * ``display_name`` replaces the legacy ``first_name`` / ``last_name``
          pair.  Compatibility properties are provided for callers that
          still reference the old field names.
        * ``login_count`` and ``last_active_at`` give the superadmin a
          quick health signal without querying the audit table.
        """

        class Meta:
            table_name = "aq_admin_users"

        username = CharField(max_length=150, unique=True)
        email = CharField(max_length=254, unique=True)
        display_name = CharField(max_length=200, default="")
        password_hash = CharField(max_length=512)
        role = CharField(max_length=32, default=DEFAULT_ROLE)
        is_active = BooleanField(default=True)

        # Profile fields (used by controller profile views) ----------------
        first_name = CharField(max_length=100, default="")
        last_name = CharField(max_length=100, default="")
        bio = TextField(default="")
        phone = CharField(max_length=32, default="")
        timezone = CharField(max_length=64, default="UTC")
        locale = CharField(max_length=16, default="en")

        # Tracking -----------------------------------------------------------
        login_count = IntegerField(default=0)
        last_login_at = CharField(max_length=64, default="")
        last_active_at = CharField(max_length=64, default="")
        created_at = CharField(max_length=64, default="")
        updated_at = CharField(max_length=64, default="")

        # Optional metadata ---------------------------------------------------
        avatar_url = CharField(max_length=512, default="")
        notes = TextField(default="")

        # ── Compatibility aliases ────────────────────────────────────────

        @property
        def avatar_path(self) -> str:
            """Alias for ``avatar_url`` — controller templates use this name."""
            return self.avatar_url

        @avatar_path.setter
        def avatar_path(self, value: str) -> None:
            self.avatar_url = value

        @property
        def last_login(self) -> str:
            """Alias for ``last_login_at``."""
            return self.last_login_at

        @property
        def date_joined(self) -> str:
            """Alias for ``created_at``."""
            return self.created_at

        # ── Computed properties ──────────────────────────────────────────

        @property
        def is_superuser(self) -> bool:
            """``True`` when the user's role is ``superadmin``."""
            return self.role == "superadmin"

        @property
        def is_staff(self) -> bool:
            """``True`` for roles that may access the admin panel."""
            return self.role in ("superadmin", "staff")

        @property
        def is_viewer(self) -> bool:
            return self.role == "viewer"

        # ── Password management ──────────────────────────────────────────

        def set_password(self, raw_password: str) -> None:
            """Hash *raw_password* and store it in ``password_hash``.

            Uses Argon2id (preferred) or PBKDF2-SHA256 fallback.
            Caller is responsible for calling ``.save()`` afterward.
            """
            if _pw_hasher is None:
                raise RuntimeError(
                    "Password hashing unavailable — "
                    "install argon2-cffi or check aquilia.auth.hashing"
                )
            self.password_hash = _pw_hasher.hash(raw_password)

        def check_password(self, raw_password: str) -> bool:
            """Verify *raw_password* against the stored hash."""
            if _pw_hasher is None or not self.password_hash:
                return False
            try:
                return _pw_hasher.verify(self.password_hash, raw_password)
            except Exception:
                return False

        # ── Permission bridge ────────────────────────────────────────────

        def has_perm(self, permission: str) -> bool:
            """Check a fine-grained permission against the RBAC matrix."""
            try:
                from aquilia.admin.permissions import (
                    AdminRole,
                    AdminPermission,
                    has_admin_permission,
                )

                role_enum = AdminRole(self.role)
                perm_enum = AdminPermission(permission)
                return has_admin_permission(role_enum, perm_enum)
            except (ValueError, KeyError):
                return False

        def has_perms(self, permissions: List[str]) -> bool:
            """Return ``True`` only if the user holds **every** permission."""
            return all(self.has_perm(p) for p in permissions)

        def has_model_perm(self, model_name: str, action: str) -> bool:
            """Convenience wrapper for model-level CRUD checks."""
            try:
                from aquilia.admin.permissions import (
                    AdminRole,
                    has_model_permission,
                )

                role_enum = AdminRole(self.role)
                return has_model_permission(role_enum, model_name, action)
            except (ValueError, KeyError):
                return False

        # ── Lifecycle helpers ────────────────────────────────────────────

        def record_login(self) -> None:
            """Bump login statistics.  Caller is responsible for ``.save()``."""
            self.login_count = (self.login_count or 0) + 1
            self.last_login_at = _now_utc()
            self.last_active_at = _now_utc()

        def touch(self) -> None:
            """Update ``last_active_at``.  Caller is responsible for ``.save()``."""
            self.last_active_at = _now_utc()

        def set_role(self, role: str) -> None:
            """Validate and assign a new role."""
            if role not in VALID_ROLES:
                raise ValueError(
                    f"Invalid role {role!r}. Must be one of {VALID_ROLES}"
                )
            self.role = role

        def deactivate(self) -> None:
            self.is_active = False

        def activate(self) -> None:
            self.is_active = True

        # ── Identity bridge (for session auth) ───────────────────────────

        def to_identity(self) -> "Identity":
            """Convert this admin user to an ``Identity`` for session storage."""
            from aquilia.auth.core import Identity, IdentityType, IdentityStatus

            return Identity(
                id=str(getattr(self, "id", None) or getattr(self, "pk", "?")),
                type=IdentityType.USER,
                attributes={
                    "name": self.display_name or f"{self.first_name} {self.last_name}".strip() or self.username,
                    "username": self.username,
                    "email": self.email,
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "roles": [self.role],
                    "is_superuser": self.is_superuser,
                    "is_staff": self.is_staff,
                    "admin_role": self.role,
                    "avatar_url": self.avatar_url,
                },
                status=IdentityStatus.ACTIVE,
            )

        # ── Class-level factories ────────────────────────────────────────

        @classmethod
        async def create_superuser(
            cls,
            username: str,
            password: str,
            email: str,
            **extra_fields: Any,
        ) -> "AdminUser":
            """Create and persist a superadmin user.

            Accepts optional ``first_name``, ``last_name``, ``bio``,
            ``phone``, ``timezone``, ``locale`` in *extra_fields*.
            """
            return await cls._create_user(
                username=username,
                password=password,
                email=email,
                role="superadmin",
                **extra_fields,
            )

        @classmethod
        async def create_staff_user(
            cls,
            username: str,
            password: str,
            email: str,
            **extra_fields: Any,
        ) -> "AdminUser":
            """Create and persist a staff user."""
            return await cls._create_user(
                username=username,
                password=password,
                email=email,
                role="staff",
                **extra_fields,
            )

        @classmethod
        async def _create_user(
            cls,
            *,
            username: str,
            password: str,
            email: str,
            role: str = DEFAULT_ROLE,
            **extra_fields: Any,
        ) -> "AdminUser":
            """Internal factory shared by ``create_superuser`` / ``create_staff_user``."""
            if _pw_hasher is None:
                raise RuntimeError(
                    "Password hashing unavailable — "
                    "install argon2-cffi or check aquilia.auth.hashing"
                )
            now = _now_utc()
            user = cls(
                username=username.strip(),
                email=email.strip(),
                password_hash=_pw_hasher.hash(password),
                role=role,
                is_active=True,
                first_name=extra_fields.get("first_name", ""),
                last_name=extra_fields.get("last_name", ""),
                display_name=extra_fields.get(
                    "display_name",
                    f"{extra_fields.get('first_name', '')} {extra_fields.get('last_name', '')}".strip(),
                ),
                bio=extra_fields.get("bio", ""),
                phone=extra_fields.get("phone", ""),
                timezone=extra_fields.get("timezone", "UTC"),
                locale=extra_fields.get("locale", "en"),
                login_count=0,
                last_login_at="",
                last_active_at="",
                created_at=now,
                updated_at=now,
                avatar_url=extra_fields.get("avatar_url", extra_fields.get("avatar_path", "")),
                notes="",
            )
            await user.save()
            return user

        # ── Authentication ───────────────────────────────────────────────

        @classmethod
        async def authenticate(
            cls, username: str, password: str
        ) -> Optional["AdminUser"]:
            """Look up a user by username and verify the password.

            Returns the ``AdminUser`` instance on success, ``None`` on failure.
            """
            try:
                user = await cls.filter(username=username).first()
            except Exception:
                return None

            if user is None or not user.is_active:
                return None

            if not user.check_password(password):
                return None

            # Bump login stats (best-effort)
            try:
                user.record_login()
                await user.save()
            except Exception:
                pass

            return user

        # ── Serialisation ────────────────────────────────────────────────

        def to_safe_dict(self) -> Dict[str, Any]:
            """Return a JSON-safe dict **without** the password hash."""
            return {
                "id": getattr(self, "id", None),
                "username": self.username,
                "email": self.email,
                "display_name": self.display_name,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "role": self.role,
                "is_active": self.is_active,
                "is_superuser": self.is_superuser,
                "is_staff": self.is_staff,
                "login_count": self.login_count,
                "last_login_at": self.last_login_at,
                "last_active_at": self.last_active_at,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "avatar_url": self.avatar_url,
            }

        def __repr__(self) -> str:
            return f"<AdminUser {self.username!r} role={self.role!r}>"

        def __str__(self) -> str:
            return self.display_name or self.username

    # -------------------------------------------------------------------
    #  AdminAuditEntry
    # -------------------------------------------------------------------

    class AdminAuditEntry(Model):
        """Immutable append-only audit record.

        Every state-changing admin action creates one row.  This replaces
        *both* the legacy ``AdminLogEntry`` and the old ``AdminAuditEntry``.

        The table is **append-only** — no ``UPDATE`` or ``DELETE`` in
        application code.
        """

        class Meta:
            table_name = "aq_admin_audit"

        # Who ----------------------------------------------------------------
        user_id = IntegerField(default=0)
        username = CharField(max_length=150, default="system")
        ip_address = CharField(max_length=45, default="")
        user_agent = CharField(max_length=512, default="")

        # What ---------------------------------------------------------------
        action = CharField(max_length=64)          # e.g. "create", "update", "delete", "login", "export"
        resource_type = CharField(max_length=128, default="")   # model or subsystem name
        resource_id = CharField(max_length=128, default="")     # PK of affected object
        summary = CharField(max_length=512, default="")         # human-readable description

        # Detail (JSON) ------------------------------------------------------
        detail = TextField(default="{}")            # arbitrary JSON payload
        diff = TextField(default="{}")              # before/after snapshot

        # When ----------------------------------------------------------------
        timestamp = CharField(max_length=64, default="")

        # Severity / category -------------------------------------------------
        severity = CharField(max_length=16, default="info")     # info | warning | critical
        category = CharField(max_length=64, default="admin")    # admin | auth | data | config | system

        # ── Factory ──────────────────────────────────────────────────────

        @classmethod
        async def create_entry(
            cls,
            *,
            action: str,
            user: Optional["AdminUser"] = None,
            user_id: int = 0,
            username: str = "system",
            ip_address: str = "",
            user_agent: str = "",
            resource_type: str = "",
            resource_id: str = "",
            summary: str = "",
            detail: Optional[Dict[str, Any]] = None,
            diff: Optional[Dict[str, Any]] = None,
            severity: str = "info",
            category: str = "admin",
        ) -> "AdminAuditEntry":
            """High-level factory that normalises inputs and persists a row."""
            if user is not None:
                user_id = getattr(user, "id", 0) or 0
                username = getattr(user, "username", "system") or "system"

            entry = cls(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id),
                summary=summary[:512] if summary else "",
                detail=json.dumps(detail or {}, default=str),
                diff=json.dumps(diff or {}, default=str),
                timestamp=_now_utc(),
                severity=severity,
                category=category,
            )
            try:
                await entry.save()
            except Exception:
                pass  # audit must never crash the request
            return entry

        # ── Convenience aliases matching legacy AdminLogEntry ────────────

        @classmethod
        async def log_action(
            cls,
            user: Optional["AdminUser"] = None,
            action: str = "",
            resource_type: str = "",
            resource_id: str = "",
            summary: str = "",
            **kwargs: Any,
        ) -> "AdminAuditEntry":
            """Drop-in replacement for ``AdminLogEntry.log_action()``."""
            return await cls.create_entry(
                action=action,
                user=user,
                resource_type=resource_type,
                resource_id=resource_id,
                summary=summary,
                **kwargs,
            )

        # ── Serialisation ────────────────────────────────────────────────

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": getattr(self, "id", None),
                "user_id": self.user_id,
                "username": self.username,
                "ip_address": self.ip_address,
                "action": self.action,
                "resource_type": self.resource_type,
                "resource_id": self.resource_id,
                "summary": self.summary,
                "detail": self.detail,
                "diff": self.diff,
                "timestamp": self.timestamp,
                "severity": self.severity,
                "category": self.category,
            }

        def __repr__(self) -> str:
            return (
                f"<AdminAuditEntry action={self.action!r} "
                f"user={self.username!r} ts={self.timestamp!r}>"
            )

    # -------------------------------------------------------------------
    #  AdminAPIKey
    # -------------------------------------------------------------------

    class AdminAPIKey(Model):
        """Scoped, hashed API key for programmatic admin access.

        Design notes
        ~~~~~~~~~~~~
        * The raw key is shown **once** on creation and then discarded.
          Only its SHA-256 hash (``key_hash``) is persisted.
        * ``prefix`` stores the first 8 characters of the raw key so
          operators can identify which key is which without exposing the
          full secret.
        * ``scopes`` is a JSON list of permission strings.  An empty list
          means "inherit all permissions from the owning user's role".
        """

        class Meta:
            table_name = "aq_admin_api_keys"

        user_id = IntegerField()
        name = CharField(max_length=200)
        prefix = CharField(max_length=16)            # first N chars for identification
        key_hash = CharField(max_length=128, unique=True)
        scopes = TextField(default="[]")             # JSON list of permission strings
        is_active = BooleanField(default=True)
        last_used_at = CharField(max_length=64, default="")
        expires_at = CharField(max_length=64, default="")  # empty = never
        created_at = CharField(max_length=64, default="")

        # ── Factory ──────────────────────────────────────────────────────

        @classmethod
        def generate(
            cls,
            *,
            user_id: int,
            name: str,
            scopes: Optional[List[str]] = None,
            expires_at: str = "",
        ) -> tuple["AdminAPIKey", str]:
            """Create an ``AdminAPIKey`` instance **and** return the raw key.

            Returns ``(instance, raw_key)``.  The caller must ``await
            instance.save()`` and display ``raw_key`` to the user *once*.
            """
            raw_key = _generate_api_key()
            instance = cls(
                user_id=user_id,
                name=name,
                prefix=raw_key[: len(API_KEY_PREFIX) + 8],
                key_hash=_hash_api_key(raw_key),
                scopes=json.dumps(scopes or [], default=str),
                is_active=True,
                last_used_at="",
                expires_at=expires_at,
                created_at=_now_utc(),
            )
            return instance, raw_key

        # ── Lookup ───────────────────────────────────────────────────────

        @classmethod
        async def verify(cls, raw_key: str) -> Optional["AdminAPIKey"]:
            """Look up a key by its hash and check expiry / active flag.

            Returns the ``AdminAPIKey`` row if valid, else ``None``.
            """
            h = _hash_api_key(raw_key)
            try:
                key_obj = await cls.filter(key_hash=h).first()
            except Exception:
                return None

            if key_obj is None or not key_obj.is_active:
                return None

            if key_obj.expires_at:
                try:
                    exp = datetime.fromisoformat(key_obj.expires_at)
                    if datetime.now(timezone.utc) > exp:
                        return None
                except ValueError:
                    pass  # malformed date — treat as "no expiry"

            # Stamp last-used (fire-and-forget, best-effort)
            key_obj.last_used_at = _now_utc()
            try:
                await key_obj.save()
            except Exception:
                pass
            return key_obj

        # ── Helpers ──────────────────────────────────────────────────────

        def get_scopes(self) -> List[str]:
            """Return the decoded scope list."""
            try:
                return json.loads(self.scopes or "[]")
            except (json.JSONDecodeError, TypeError):
                return []

        def has_scope(self, scope: str) -> bool:
            scopes = self.get_scopes()
            return len(scopes) == 0 or scope in scopes  # empty = wildcard

        @property
        def is_expired(self) -> bool:
            if not self.expires_at:
                return False
            try:
                exp = datetime.fromisoformat(self.expires_at)
                return datetime.now(timezone.utc) > exp
            except ValueError:
                return False

        def revoke(self) -> None:
            """Mark the key as inactive.  Caller must ``.save()``."""
            self.is_active = False

        def to_safe_dict(self) -> Dict[str, Any]:
            return {
                "id": getattr(self, "id", None),
                "user_id": self.user_id,
                "name": self.name,
                "prefix": self.prefix,
                "scopes": self.get_scopes(),
                "is_active": self.is_active,
                "is_expired": self.is_expired,
                "last_used_at": self.last_used_at,
                "expires_at": self.expires_at,
                "created_at": self.created_at,
            }

        def __repr__(self) -> str:
            return f"<AdminAPIKey {self.prefix!r} user_id={self.user_id}>"

    # -------------------------------------------------------------------
    #  AdminPreference
    # -------------------------------------------------------------------

    class AdminPreference(Model):
        """Per-user key-value preferences (JSON blob).

        Instead of bolting dozens of boolean columns onto ``AdminUser``,
        UI settings (theme, sidebar state, locale, notification prefs,
        dashboard layout, etc.) are stored as an opaque JSON document
        keyed by ``(user_id, namespace)``.

        Example namespaces: ``"ui"``, ``"notifications"``, ``"dashboard"``.
        """

        class Meta:
            table_name = "aq_admin_preferences"

        user_id = IntegerField()
        namespace = CharField(max_length=64, default="ui")
        data = TextField(default="{}")
        updated_at = CharField(max_length=64, default="")

        # ── Accessors ────────────────────────────────────────────────────

        def get_data(self) -> Dict[str, Any]:
            try:
                return json.loads(self.data or "{}")
            except (json.JSONDecodeError, TypeError):
                return {}

        def set_data(self, payload: Dict[str, Any]) -> None:
            self.data = json.dumps(payload, default=str)
            self.updated_at = _now_utc()

        def get_value(self, key: str, default: Any = None) -> Any:
            return self.get_data().get(key, default)

        def set_value(self, key: str, value: Any) -> None:
            d = self.get_data()
            d[key] = value
            self.set_data(d)

        def merge(self, patch: Dict[str, Any]) -> None:
            """Shallow-merge *patch* into the existing data."""
            d = self.get_data()
            d.update(patch)
            self.set_data(d)

        # ── Factory ──────────────────────────────────────────────────────

        @classmethod
        async def get_or_create(
            cls, *, user_id: int, namespace: str = "ui"
        ) -> "AdminPreference":
            """Fetch the preference row or create an empty one."""
            try:
                existing = await cls.filter(
                    user_id=user_id, namespace=namespace
                ).first()
                if existing is not None:
                    return existing
            except Exception:
                pass
            pref = cls(
                user_id=user_id,
                namespace=namespace,
                data="{}",
                updated_at=_now_utc(),
            )
            try:
                await pref.save()
            except Exception:
                pass
            return pref

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": getattr(self, "id", None),
                "user_id": self.user_id,
                "namespace": self.namespace,
                "data": self.get_data(),
                "updated_at": self.updated_at,
            }

        def __repr__(self) -> str:
            return (
                f"<AdminPreference user_id={self.user_id} "
                f"ns={self.namespace!r}>"
            )


# ═══════════════════════════════════════════════════════════════════════════
#  FALLBACK STUBS  (ORM not available)
# ═══════════════════════════════════════════════════════════════════════════

else:

    class _StubMeta:
        table_name = ""

    class AdminUser:  # type: ignore[no-redef]
        _HAS_ORM = False
        Meta = _StubMeta

        def __init__(self, **kw: Any) -> None:
            for k, v in kw.items():
                setattr(self, k, v)

        @property
        def is_superuser(self) -> bool:
            return getattr(self, "role", "") == "superadmin"

        @property
        def is_staff(self) -> bool:
            return getattr(self, "role", "") in ("superadmin", "staff")

        def has_perm(self, perm: str) -> bool:
            return self.is_superuser

        def has_perms(self, perms: List[str]) -> bool:
            return self.is_superuser

        def set_password(self, raw_password: str) -> None:
            if _pw_hasher is not None:
                self.password_hash = _pw_hasher.hash(raw_password)

        def check_password(self, raw_password: str) -> bool:
            if _pw_hasher is None:
                return False
            try:
                return _pw_hasher.verify(
                    getattr(self, "password_hash", ""), raw_password
                )
            except Exception:
                return False

        def to_identity(self) -> Any:
            try:
                from aquilia.auth.core import Identity, IdentityType, IdentityStatus
                return Identity(
                    id=str(getattr(self, "id", "?")),
                    type=IdentityType.USER,
                    attributes={
                        "name": getattr(self, "username", "admin"),
                        "username": getattr(self, "username", ""),
                        "roles": [getattr(self, "role", "staff")],
                        "is_superuser": self.is_superuser,
                        "is_staff": self.is_staff,
                        "admin_role": getattr(self, "role", "staff"),
                    },
                    status=IdentityStatus.ACTIVE,
                )
            except Exception:
                return None

        @classmethod
        async def create_superuser(cls, username: str, password: str, email: str, **kw: Any) -> "AdminUser":
            raise RuntimeError("ORM not available — cannot create superuser without database models")

        @classmethod
        async def create_staff_user(cls, username: str, password: str, email: str, **kw: Any) -> "AdminUser":
            raise RuntimeError("ORM not available — cannot create staff user without database models")

        @classmethod
        async def authenticate(cls, username: str, password: str) -> Optional["AdminUser"]:
            return None

        def __repr__(self) -> str:
            return f"<AdminUser(stub) {getattr(self, 'username', '?')!r}>"

    class AdminAuditEntry:  # type: ignore[no-redef]
        _HAS_ORM = False
        Meta = _StubMeta

        def __init__(self, **kw: Any) -> None:
            for k, v in kw.items():
                setattr(self, k, v)

        @classmethod
        async def create_entry(cls, **kw: Any) -> "AdminAuditEntry":
            return cls(**kw)

        @classmethod
        async def log_action(cls, **kw: Any) -> "AdminAuditEntry":
            return cls(**kw)

    class AdminAPIKey:  # type: ignore[no-redef]
        _HAS_ORM = False
        Meta = _StubMeta

    class AdminPreference:  # type: ignore[no-redef]
        _HAS_ORM = False
        Meta = _StubMeta


# ═══════════════════════════════════════════════════════════════════════════
#  BACKWARD-COMPATIBILITY STUBS
# ═══════════════════════════════════════════════════════════════════════════
#
#  These names are imported in various places across the admin subsystem.
#  They are intentionally **not** ORM models — they exist only so that
#  ``from aquilia.admin.models import ContentType`` doesn't blow up.
#  The registry skips anything with ``_HAS_ORM = False``.
# ═══════════════════════════════════════════════════════════════════════════


class ContentType:
    """Stub — Aquilia does not use a Django-style ContentType table.

    Model metadata is available at runtime via the model registry.
    """

    _HAS_ORM = False

    def __init__(self, **kw: Any) -> None:
        self.app_label: str = kw.get("app_label", "")
        self.model: str = kw.get("model", "")

    @classmethod
    def get_for_model(cls, model: Any) -> "ContentType":
        name = getattr(model, "__name__", str(model))
        return cls(app_label="admin", model=name.lower())

    def __repr__(self) -> str:
        return f"<ContentType(stub) {self.app_label}.{self.model}>"

    def __str__(self) -> str:
        return f"{self.app_label}.{self.model}"


class AdminPermission:
    """Stub — permissions live in ``permissions.py`` as an in-memory enum."""

    _HAS_ORM = False

    def __init__(self, **kw: Any) -> None:
        self.codename: str = kw.get("codename", "")
        self.name: str = kw.get("name", "")

    def __repr__(self) -> str:
        return f"<AdminPermission(stub) {self.codename!r}>"


class AdminGroup:
    """Stub — roles are defined in ``permissions.AdminRole``."""

    _HAS_ORM = False

    def __init__(self, **kw: Any) -> None:
        self.name: str = kw.get("name", "")

    def __repr__(self) -> str:
        return f"<AdminGroup(stub) {self.name!r}>"


class AdminLogEntry:
    """Stub — use :class:`AdminAuditEntry` instead.

    ``AdminLogEntry.log_action()`` delegates to
    ``AdminAuditEntry.log_action()`` for backward compatibility.
    """

    _HAS_ORM = False

    def __init__(self, **kw: Any) -> None:
        for k, v in kw.items():
            setattr(self, k, v)

    @classmethod
    async def log_action(cls, **kw: Any) -> "AdminAuditEntry":
        """Proxy to :meth:`AdminAuditEntry.log_action`."""
        return await AdminAuditEntry.log_action(**kw)

    def __repr__(self) -> str:
        return f"<AdminLogEntry(stub→AdminAuditEntry)>"


class AdminSession:
    """Stub — sessions are managed by ``aquilia.sessions`` at the framework level."""

    _HAS_ORM = False

    def __init__(self, **kw: Any) -> None:
        for k, v in kw.items():
            setattr(self, k, v)

    def __repr__(self) -> str:
        return f"<AdminSession(stub)>"


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Active models
    "AdminUser",
    "AdminAuditEntry",
    "AdminAPIKey",
    "AdminPreference",
    # Backward-compat stubs
    "ContentType",
    "AdminPermission",
    "AdminGroup",
    "AdminLogEntry",
    "AdminSession",
    # Constants
    "VALID_ROLES",
    "DEFAULT_ROLE",
    "API_KEY_PREFIX",
    # Internal flags
    "_ORM_AVAILABLE",
    "_HAS_ORM",
    # Helpers
    "_generate_api_key",
    "_hash_api_key",
]

# Alias for backward compat — registry.py and blueprints.py import _HAS_ORM
_HAS_ORM = _ORM_AVAILABLE
