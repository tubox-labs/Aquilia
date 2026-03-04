"""
AquilAdmin -- Comprehensive Admin Models.

Provides a full-featured admin model hierarchy:

    - ``ContentType``      -- tracks every model/table in the project
    - ``AdminPermission``  -- codename-based permissions tied to content types
    - ``AdminGroup``       -- named groups with M2M permissions
    - ``AdminUser``        -- staff/superuser accounts with groups & permissions
    - ``AdminLogEntry``    -- immutable audit trail of every admin action
    - ``AdminSession``     -- server-side session storage for admin auth

All models use the Aquilia ORM with proper relationships (ForeignKey,
ManyToManyField), composite indexes, unique constraints, and db_index
for optimal query performance.

**Important**: These models are NOT auto-migrated. Users must run::

    aq db makemigrations
    aq db migrate

to create the underlying tables before using the admin system.

Usage::

    from aquilia.admin.models import (
        AdminUser, AdminGroup, AdminPermission,
        ContentType, AdminLogEntry, AdminSession,
    )

    # Create a superuser
    user = await AdminUser.create_superuser("admin", "s3cret", email="admin@site.com")

    # Authenticate
    user = await AdminUser.authenticate("admin", "s3cret")

    # Check permissions
    has_perm = await user.has_perm("myapp.change_user")
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Tuple, Type

# ── ORM imports (with graceful fallback for test isolation) ──────────────────

try:
    from aquilia.models.base import Model
    from aquilia.models.fields_module import (
        AutoField,
        BigAutoField,
        CharField,
        TextField,
        EmailField,
        BooleanField,
        IntegerField,
        DateTimeField,
        ForeignKey,
        ManyToManyField,
        SmallIntegerField,
        UUIDField,
        Index,
        UniqueConstraint,
    )
    _HAS_ORM = True
except Exception:  # pragma: no cover
    _HAS_ORM = False

# ── Password hashing helpers ────────────────────────────────────────────────

try:
    from aquilia.auth.hashing import PasswordHasher as _PH
    _hasher = _PH()
except Exception:
    _hasher = None  # type: ignore[assignment]


def _hash_password(raw_password: str) -> str:
    """Hash a raw password using the best available algorithm (Argon2id preferred)."""
    if _hasher is not None:
        return _hasher.hash(raw_password)
    # Minimal fallback using PBKDF2-SHA256 (600k iterations)
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt.encode(), 600_000)
    return f"$pbkdf2_sha256$600000${salt}${dk.hex()}"


def _verify_password(password_hash: str, raw_password: str) -> bool:
    """Verify a raw password against a stored hash."""
    if _hasher is not None:
        return _hasher.verify(password_hash, raw_password)
    # Minimal fallback
    if not password_hash.startswith("$pbkdf2_sha256$"):
        return False
    parts = password_hash.split("$")
    if len(parts) != 5:
        return False
    iterations = int(parts[2])
    salt = parts[3]
    expected_hash = parts[4]
    dk = hashlib.pbkdf2_hmac("sha256", raw_password.encode(), salt.encode(), iterations)
    return dk.hex() == expected_hash


# ═══════════════════════════════════════════════════════════════════════════
# ORM-backed models (only when the full ORM is available)
# ═══════════════════════════════════════════════════════════════════════════

if _HAS_ORM:

    # ── ContentType ──────────────────────────────────────────────────────

    class ContentType(Model):
        """
        Tracks every model registered in the project.

        Used by AdminPermission and AdminLogEntry to reference models generically.
        """

        table = "admin_content_types"

        app_label = CharField(max_length=100, db_index=True)
        model = CharField(max_length=100, db_index=True)

        class Meta:
            ordering = ["app_label", "model"]
            verbose_name = "Content Type"
            verbose_name_plural = "Content Types"
            constraints = [
                UniqueConstraint(fields=["app_label", "model"], name="uq_content_type_app_model"),
            ]
            indexes = [
                Index(fields=["app_label", "model"], name="idx_content_type_lookup"),
            ]

        def __str__(self) -> str:
            return f"{self.app_label}.{self.model}"

        @property
        def name(self) -> str:
            """Human-readable name derived from model name."""
            model_name = getattr(self, "model", "") or ""
            return model_name.replace("_", " ").title()

        @classmethod
        async def get_for_model(cls, model_cls: type) -> "ContentType":
            """Get or create a ContentType for a given Model class."""
            model_name = model_cls.__name__.lower()
            app_label = "default"
            meta = getattr(model_cls, "Meta", None) or getattr(model_cls, "_meta", None)
            if meta:
                app_label = getattr(meta, "app_label", None) or "default"
            if app_label == "default":
                module = getattr(model_cls, "__module__", "")
                parts = module.split(".")
                if len(parts) >= 2:
                    app_label = parts[-2] if parts[-1] == "models" else parts[-1]
                else:
                    app_label = parts[0] if parts else "default"
            try:
                ct = await cls.objects.get(app_label=app_label, model=model_name)
                if ct is not None:
                    return ct
            except Exception:
                pass
            return await cls.create(app_label=app_label, model=model_name)

    # ── AdminPermission ──────────────────────────────────────────────────

    class AdminPermission(Model):
        """
        A single permission tied to a ContentType.

        Pattern:
            codename = "change_user"
            name     = "Can change user"
            content_type → ContentType (app_label="auth", model="user")
        """

        table = "admin_permissions"

        name = CharField(max_length=255, help_text="Human-readable permission name")
        codename = CharField(max_length=100, db_index=True, help_text="Machine-readable code")
        content_type = ForeignKey(
            "ContentType",
            related_name="permissions",
            on_delete="CASCADE",
            db_index=True,
        )

        class Meta:
            ordering = ["content_type", "codename"]
            verbose_name = "Permission"
            verbose_name_plural = "Permissions"
            constraints = [
                UniqueConstraint(
                    fields=["content_type_id", "codename"],
                    name="uq_permission_ct_codename",
                ),
            ]
            indexes = [
                Index(fields=["codename"], name="idx_permission_codename"),
            ]

        def __str__(self) -> str:
            return f"{self.codename}"

        @classmethod
        async def create_for_model(
            cls, model_cls: type, codename: str, name: str,
        ) -> "AdminPermission":
            """Create a permission for a model, auto-resolving the ContentType."""
            ct = await ContentType.get_for_model(model_cls)
            return await cls.create(name=name, codename=codename, content_type=ct.pk)

    # ── AdminGroup ───────────────────────────────────────────────────────

    class AdminGroup(Model):
        """
        Named group of permissions.

        Users can belong to multiple groups, inheriting all group permissions.
        """

        table = "admin_groups"

        name = CharField(max_length=150, unique=True, help_text="Group name (must be unique)")
        permissions = ManyToManyField(
            "AdminPermission",
            related_name="groups",
            db_table="admin_group_permissions",
        )

        class Meta:
            ordering = ["name"]
            verbose_name = "Group"
            verbose_name_plural = "Groups"

        def __str__(self) -> str:
            return self.name or repr(self)

    # ── AdminUser ────────────────────────────────────────────────────────

    class AdminUser(Model):
        """
        Admin user stored in the database.

        Full-featured user model with:
        - Password hashing (Argon2id / PBKDF2)
        - Group membership (M2M → AdminGroup)
        - Direct permissions (M2M → AdminPermission)
        - Superuser / staff flags
        - Activity tracking (last_login, date_joined)
        """

        table = "admin_users"

        username = CharField(max_length=150, unique=True)
        email = EmailField(max_length=254, blank=True, default="")
        password_hash = TextField()
        first_name = CharField(max_length=150, blank=True, default="")
        last_name = CharField(max_length=150, blank=True, default="")
        is_superuser = BooleanField(default=False)
        is_staff = BooleanField(default=True)
        is_active = BooleanField(default=True)
        last_login = DateTimeField(null=True, blank=True)
        date_joined = DateTimeField(auto_now_add=True)
        # ── Extended profile fields ────────────────────────────────────
        # Relative path inside .aquilia/admin/profile/, e.g. "<uuid>.png"
        avatar_path = CharField(max_length=512, blank=True, default="", null=True)
        bio = TextField(blank=True, default="", null=True)
        phone = CharField(max_length=32, blank=True, default="", null=True)
        timezone = CharField(max_length=64, blank=True, default="UTC", null=True)
        locale = CharField(max_length=16, blank=True, default="en", null=True)

        groups = ManyToManyField(
            "AdminGroup",
            related_name="users",
            db_table="admin_user_groups",
        )
        user_permissions = ManyToManyField(
            "AdminPermission",
            related_name="users",
            db_table="admin_user_permissions",
        )

        class Meta:
            ordering = ["-date_joined"]
            verbose_name = "Admin User"
            verbose_name_plural = "Admin Users"
            get_latest_by = "date_joined"
            indexes = [
                Index(fields=["username"], name="idx_admin_user_username"),
                Index(fields=["email"], name="idx_admin_user_email"),
                Index(fields=["is_active", "is_staff"], name="idx_admin_user_active_staff"),
            ]

        def __str__(self) -> str:
            return self.username or repr(self)

        def get_full_name(self) -> str:
            parts = [
                getattr(self, "first_name", "") or "",
                getattr(self, "last_name", "") or "",
            ]
            return " ".join(p for p in parts if p).strip() or self.username

        def get_short_name(self) -> str:
            return getattr(self, "first_name", "") or self.username

        def set_password(self, raw_password: str) -> None:
            self.password_hash = _hash_password(raw_password)

        def check_password(self, raw_password: str) -> bool:
            return _verify_password(self.password_hash, raw_password)

        async def has_perm(self, perm_codename: str) -> bool:
            """Check if user has a specific permission (superusers have all)."""
            if getattr(self, "is_superuser", False):
                return True
            if not getattr(self, "is_active", True):
                return False
            try:
                direct = await AdminPermission.objects.filter(codename=perm_codename).all()
                if direct:
                    return True
            except Exception:
                pass
            return False

        async def has_perms(self, perm_list: Sequence[str]) -> bool:
            for perm in perm_list:
                if not await self.has_perm(perm):
                    return False
            return True

        async def has_module_perms(self, app_label: str) -> bool:
            if getattr(self, "is_superuser", False):
                return True
            return getattr(self, "is_active", True)

        def to_identity(self) -> "Identity":
            from aquilia.auth.core import Identity, IdentityType, IdentityStatus
            roles: list[str] = []
            if getattr(self, "is_superuser", False):
                roles.append("superadmin")
            if getattr(self, "is_staff", False):
                roles.append("staff")
            return Identity(
                id=str(self.pk),
                type=IdentityType.USER,
                attributes={
                    "name": self.get_full_name(),
                    "username": self.username,
                    "email": getattr(self, "email", ""),
                    "roles": roles,
                    "is_superuser": getattr(self, "is_superuser", False),
                    "is_staff": getattr(self, "is_staff", False),
                    "admin_role": "superadmin" if getattr(self, "is_superuser", False) else "staff",
                    "avatar_path": getattr(self, "avatar_path", "") or "",
                    "bio": getattr(self, "bio", "") or "",
                    "phone": getattr(self, "phone", "") or "",
                    "timezone": getattr(self, "timezone", "UTC") or "UTC",
                    "locale": getattr(self, "locale", "en") or "en",
                },
                status=IdentityStatus.ACTIVE if getattr(self, "is_active", True) else IdentityStatus.SUSPENDED,
            )

        @classmethod
        async def create_superuser(
            cls, username: str, password: str, email: str = "", **extra_fields: Any,
        ) -> "AdminUser":
            hashed = _hash_password(password)
            return await cls.create(
                username=username, email=email, password_hash=hashed,
                is_superuser=True, is_staff=True, is_active=True,
                first_name=extra_fields.pop("first_name", ""),
                last_name=extra_fields.pop("last_name", ""),
                **extra_fields,
            )

        @classmethod
        async def create_staff_user(
            cls, username: str, password: str, email: str = "", **extra_fields: Any,
        ) -> "AdminUser":
            hashed = _hash_password(password)
            return await cls.create(
                username=username, email=email, password_hash=hashed,
                is_superuser=False, is_staff=True, is_active=True,
                first_name=extra_fields.pop("first_name", ""),
                last_name=extra_fields.pop("last_name", ""),
                **extra_fields,
            )

        @classmethod
        async def authenticate(
            cls, username: str, password: str,
        ) -> Optional["AdminUser"]:
            try:
                user = await cls.objects.get(username=username)
            except Exception:
                return None
            if user is None:
                return None
            if not getattr(user, "is_active", True):
                return None
            if not _verify_password(user.password_hash, password):
                return None
            try:
                await cls.objects.filter(pk=user.pk).update(
                    {"last_login": datetime.now(timezone.utc)}
                )
            except Exception:
                pass
            return user

    # ── AdminLogEntry ────────────────────────────────────────────────────

    class AdminLogEntry(Model):
        """
        Immutable audit log entry for every admin action.

        action_flag: 1=ADDITION, 2=CHANGE, 3=DELETION
        """

        ADDITION = 1
        CHANGE = 2
        DELETION = 3

        ACTION_FLAG_CHOICES = (
            (ADDITION, "Addition"),
            (CHANGE, "Change"),
            (DELETION, "Deletion"),
        )

        table = "admin_log_entries"

        action_time = DateTimeField(auto_now_add=True, db_index=True)
        user = ForeignKey(
            "AdminUser", related_name="log_entries",
            on_delete="CASCADE", db_index=True,
        )
        content_type = ForeignKey(
            "ContentType", related_name="log_entries",
            on_delete="SET NULL", null=True, blank=True, db_index=True,
        )
        object_id = TextField(null=True, blank=True)
        object_repr = CharField(max_length=200, blank=True, default="")
        action_flag = IntegerField(choices=ACTION_FLAG_CHOICES)
        change_message = TextField(blank=True, default="")

        class Meta:
            ordering = ["-action_time"]
            verbose_name = "Log Entry"
            verbose_name_plural = "Log Entries"
            get_latest_by = "action_time"
            indexes = [
                Index(fields=["action_time"], name="idx_log_entry_time"),
                Index(fields=["user_id", "action_time"], name="idx_log_entry_user_time"),
                Index(fields=["content_type_id", "object_id"], name="idx_log_entry_ct_obj"),
            ]

        def __str__(self) -> str:
            action_names = {1: "Added", 2: "Changed", 3: "Deleted"}
            action = action_names.get(getattr(self, "action_flag", 0), "Unknown")
            return f"{action} {self.object_repr!r}"

        @property
        def is_addition(self) -> bool:
            return getattr(self, "action_flag", 0) == self.ADDITION

        @property
        def is_change(self) -> bool:
            return getattr(self, "action_flag", 0) == self.CHANGE

        @property
        def is_deletion(self) -> bool:
            return getattr(self, "action_flag", 0) == self.DELETION

        def get_change_message(self) -> str:
            import json as _json
            msg = getattr(self, "change_message", "")
            if not msg:
                return ""
            try:
                data = _json.loads(msg)
                if isinstance(data, list):
                    return "; ".join(str(d) for d in data)
                return str(data)
            except (ValueError, TypeError):
                return str(msg)

        @classmethod
        async def log_action(
            cls, user_id: int, content_type_id: Optional[int],
            object_id: Optional[str], object_repr: str,
            action_flag: int, change_message: str = "",
        ) -> "AdminLogEntry":
            return await cls.create(
                user=user_id, content_type=content_type_id,
                object_id=object_id, object_repr=object_repr[:200],
                action_flag=action_flag, change_message=change_message,
            )

    # ── AdminAuditEntry ──────────────────────────────────────────────────

    class AdminAuditEntry(Model):
        """
        Persistent, model-backed audit log entry for every admin action.

        Replaces the in-memory AdminAuditLog list so audit history
        survives server restarts and user logouts.

        Fields mirror the AdminAuditEntry dataclass in audit.py so
        existing serialization / rendering code continues to work.
        """

        table = "admin_audit_entries"

        entry_id = CharField(max_length=32, unique=True, db_index=True)
        timestamp = DateTimeField(auto_now_add=True, db_index=True)
        user_id = CharField(max_length=255, db_index=True, blank=True, default="")
        username = CharField(max_length=255, blank=True, default="")
        role = CharField(max_length=100, blank=True, default="")
        action = CharField(max_length=50, db_index=True)
        model_name = CharField(max_length=255, null=True, blank=True)
        record_pk = CharField(max_length=255, null=True, blank=True)
        changes_json = TextField(blank=True, default="")  # JSON-encoded changes dict
        ip_address = CharField(max_length=45, blank=True, default="")
        user_agent = TextField(blank=True, default="")
        metadata_json = TextField(blank=True, default="")  # JSON-encoded metadata dict
        success = BooleanField(default=True)
        error_message = TextField(null=True, blank=True)

        class Meta:
            ordering = ["-timestamp"]
            verbose_name = "Audit Entry"
            verbose_name_plural = "Audit Entries"
            get_latest_by = "timestamp"
            indexes = [
                Index(fields=["timestamp"], name="idx_audit_entry_timestamp"),
                Index(fields=["user_id", "timestamp"], name="idx_audit_entry_user_ts"),
                Index(fields=["action", "timestamp"], name="idx_audit_entry_action_ts"),
                Index(fields=["model_name", "timestamp"], name="idx_audit_entry_model_ts"),
            ]

        def __str__(self) -> str:
            return f"[{self.action}] {self.username} @ {self.timestamp}"

        def to_dict(self) -> Dict[str, Any]:
            """Serialize to dict compatible with existing audit templates."""
            import json as _json
            changes = None
            if self.changes_json:
                try:
                    changes = _json.loads(self.changes_json)
                except (ValueError, TypeError):
                    pass
            metadata: Dict[str, Any] = {}
            if self.metadata_json:
                try:
                    metadata = _json.loads(self.metadata_json)
                except (ValueError, TypeError):
                    pass
            ts = self.timestamp
            ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            return {
                "pk": self.pk,  # real integer primary key for admin URLs
                "id": self.entry_id,
                "timestamp": ts_str,
                "user_id": self.user_id,
                "username": self.username,
                "role": self.role,
                "action": self.action,
                "model_name": self.model_name,
                "record_pk": self.record_pk,
                "changes": changes,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "metadata": metadata,
                "success": bool(self.success),
                "error_message": self.error_message,
            }

        @classmethod
        async def create_entry(
            cls,
            user_id: str,
            username: str,
            role: str,
            action: str,
            *,
            model_name: Optional[str] = None,
            record_pk: Optional[str] = None,
            changes: Optional[Dict[str, Any]] = None,
            ip_address: Optional[str] = None,
            user_agent: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            success: bool = True,
            error_message: Optional[str] = None,
        ) -> "AdminAuditEntry":
            """Create and persist an audit entry to the database."""
            import json as _json
            import secrets as _sec
            entry_id = f"audit_{_sec.token_hex(8)}"
            return await cls.create(
                entry_id=entry_id,
                user_id=user_id or "",
                username=username or "",
                role=role or "",
                action=action if isinstance(action, str) else str(action),
                model_name=model_name,
                record_pk=str(record_pk) if record_pk is not None else None,
                changes_json=_json.dumps(changes, default=str) if changes else "",
                ip_address=ip_address or "",
                user_agent=user_agent or "",
                metadata_json=_json.dumps(metadata or {}, default=str),
                success=success,
                error_message=error_message,
            )

    # ── AdminSession ─────────────────────────────────────────────────────

    class AdminSession(Model):
        """Server-side session storage for admin authentication."""

        table = "admin_sessions"

        session_key = CharField(max_length=40, unique=True, db_index=True)
        session_data = TextField(blank=True, default="")
        expire_date = DateTimeField(db_index=True)

        class Meta:
            verbose_name = "Session"
            verbose_name_plural = "Sessions"
            indexes = [
                Index(fields=["session_key"], name="idx_admin_session_key"),
                Index(fields=["expire_date"], name="idx_admin_session_expire"),
            ]

        def __str__(self) -> str:
            return self.session_key or repr(self)

        def is_expired(self) -> bool:
            expire = getattr(self, "expire_date", None)
            if expire is None:
                return True
            if isinstance(expire, str):
                try:
                    expire = datetime.fromisoformat(expire)
                except (ValueError, TypeError):
                    return True
            return datetime.now(timezone.utc) > expire

        @classmethod
        async def clear_expired(cls) -> int:
            try:
                result = await cls.objects.filter(
                    expire_date__lt=datetime.now(timezone.utc)
                ).delete()
                return result if isinstance(result, int) else 0
            except Exception:
                return 0

else:
    # ── Fallback stubs when ORM is not available ─────────────────────────

    class ContentType:  # type: ignore[no-redef]
        """Stub ContentType when ORM is not available."""
        _HAS_ORM = False
        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def __str__(self) -> str:
            return f"{getattr(self, 'app_label', '?')}.{getattr(self, 'model', '?')}"
        @classmethod
        async def get_for_model(cls, model_cls: type) -> "ContentType":
            return cls(app_label="stub", model=model_cls.__name__.lower())

    class AdminPermission:  # type: ignore[no-redef]
        """Stub AdminPermission when ORM is not available."""
        _HAS_ORM = False
        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class AdminGroup:  # type: ignore[no-redef]
        """Stub AdminGroup when ORM is not available."""
        _HAS_ORM = False
        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class AdminUser:  # type: ignore[no-redef]
        """Stub AdminUser when ORM fields are not available."""
        _HAS_ORM = False
        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def check_password(self, raw_password: str) -> bool:
            return _verify_password(getattr(self, "password_hash", ""), raw_password)
        def set_password(self, raw_password: str) -> None:
            self.password_hash = _hash_password(raw_password)
        def get_full_name(self) -> str:
            return getattr(self, "username", "admin")
        def to_identity(self):
            from aquilia.auth.core import Identity, IdentityType, IdentityStatus
            roles: list[str] = []
            if getattr(self, "is_superuser", False):
                roles.append("superadmin")
            if getattr(self, "is_staff", False):
                roles.append("staff")
            return Identity(
                id=str(getattr(self, "pk", "stub")),
                type=IdentityType.USER,
                attributes={
                    "name": getattr(self, "username", "admin"),
                    "username": getattr(self, "username", "admin"),
                    "roles": roles,
                    "is_superuser": getattr(self, "is_superuser", False),
                    "is_staff": getattr(self, "is_staff", False),
                    "admin_role": "superadmin" if getattr(self, "is_superuser", False) else "staff",
                },
                status=IdentityStatus.ACTIVE,
            )
        @classmethod
        async def authenticate(cls, username: str, password: str) -> Optional["AdminUser"]:
            return None
        @classmethod
        async def create_superuser(cls, username: str, password: str, email: str = "", **kw: Any) -> "AdminUser":
            raise RuntimeError("ORM not available -- cannot create superuser without database models")
        @classmethod
        async def create_staff_user(cls, username: str, password: str, email: str = "", **kw: Any) -> "AdminUser":
            raise RuntimeError("ORM not available -- cannot create staff user without database models")

    class AdminLogEntry:  # type: ignore[no-redef]
        """Stub AdminLogEntry when ORM is not available."""
        ADDITION = 1
        CHANGE = 2
        DELETION = 3
        _HAS_ORM = False
        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)
        @classmethod
        async def log_action(cls, **kwargs: Any) -> "AdminLogEntry":
            return cls(**kwargs)

    class AdminAuditEntry:  # type: ignore[no-redef]
        """Stub AdminAuditEntry when ORM is not available."""
        _HAS_ORM = False
        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def to_dict(self) -> Dict[str, Any]:
            return {k: getattr(self, k, None) for k in (
                "id", "timestamp", "user_id", "username", "role", "action",
                "model_name", "record_pk", "changes", "ip_address",
                "user_agent", "metadata", "success", "error_message",
            )}
        @classmethod
        async def create_entry(cls, **kwargs: Any) -> "AdminAuditEntry":
            return cls(**kwargs)

    class AdminSession:  # type: ignore[no-redef]
        """Stub AdminSession when ORM is not available."""
        _HAS_ORM = False
        def __init__(self, **kwargs: Any):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def is_expired(self) -> bool:
            return True
        @classmethod
        async def clear_expired(cls) -> int:
            return 0


# ── Exported helpers ────────────────────────────────────────────────────────

__all__ = [
    "ContentType",
    "AdminPermission",
    "AdminGroup",
    "AdminUser",
    "AdminLogEntry",
    "AdminAuditEntry",
    "AdminSession",
    "_hash_password",
    "_verify_password",
]
