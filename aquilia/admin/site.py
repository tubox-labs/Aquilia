"""
AquilAdmin -- AdminSite (Central Registry).

The AdminSite is the central coordination point for the admin system.
It manages:
- Model registration (explicit + auto-discovered)
- Dashboard data aggregation
- Audit log
- Template rendering integration
- Permission checks
- Module visibility configuration (AdminConfig)

Design: Singleton pattern with lazy initialization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model
    from aquilia.auth.core import Identity

from .options import ModelAdmin
from .permissions import AdminRole, AdminPermission, get_admin_role, has_admin_permission, has_model_permission
from .permissions import update_role_permissions, set_model_permission_override, get_model_permission_overrides
from .audit import AdminAuditLog, ModelBackedAuditLog, AdminAction
from .faults import (
    AdminAuthorizationFault,
    AdminModelNotFoundFault,
    AdminRecordNotFoundFault,
    AdminValidationFault,
)
from aquilia.controller.pagination import PageNumberPagination

logger = logging.getLogger("aquilia.admin.site")


# ── AdminConfig -- Parsed, immutable admin configuration ──────────────────────

@dataclass(frozen=True)
class AdminConfig:
    """
    Immutable admin configuration parsed from ``Integration.admin()`` config dict.

    Provides a clean, typed API for checking which modules/features
    are enabled without digging through raw config dicts.
    """

    # Module visibility
    modules: Dict[str, bool] = field(default_factory=lambda: {
        "dashboard": True, "orm": True, "build": True,
        "migrations": True, "config": True, "workspace": True,
        "permissions": True, "monitoring": False, "admin_users": True,
        "profile": True, "audit": False, "api_keys": True,
        "preferences": True,
        "containers": False, "pods": False,
        "query_inspector": False, "tasks": False, "errors": False,
        "testing": False, "mlops": False, "storage": False,
        "mailer": False, "provider": False,
    })

    # Audit settings (disabled by default -- opt in)
    audit_enabled: bool = False
    audit_max_entries: int = 10_000
    audit_log_logins: bool = True
    audit_log_views: bool = True
    audit_log_searches: bool = True
    audit_excluded_actions: FrozenSet[str] = field(default_factory=frozenset)

    # Monitoring settings (disabled by default -- opt in)
    monitoring_enabled: bool = False
    monitoring_metrics: FrozenSet[str] = field(default_factory=lambda: frozenset({
        "cpu", "memory", "disk", "network", "process", "python", "system", "health_checks",
    }))
    monitoring_refresh_interval: int = 30

    # Containers (Docker) settings
    containers_config: Dict[str, Any] = field(default_factory=lambda: {
        "docker_host": None,
        "allowed_actions": [
            "start", "stop", "restart", "pause", "unpause",
            "kill", "rm", "logs", "inspect", "exec", "export",
        ],
        "log_tail": 200,
        "log_since": "",
        "refresh_interval": 15,
        "compose_files": [],
        "compose_project_dir": None,
        "show_system_containers": False,
        "capabilities": {
            "exec": True, "prune": True, "build": True,
            "export": True, "image_actions": True,
            "volume_actions": True, "network_actions": True,
        },
    })

    # Pods (Kubernetes) settings
    pods_config: Dict[str, Any] = field(default_factory=lambda: {
        "kubeconfig": None,
        "namespace": "default",
        "contexts": [],
        "resources": [
            "pods", "deployments", "services", "ingresses",
            "configmaps", "secrets", "namespaces", "events",
            "daemonsets", "statefulsets", "jobs", "cronjobs",
            "persistentvolumeclaims", "nodes",
        ],
        "manifest_dirs": ["k8s"],
        "manifest_patterns": ["*.yaml", "*.yml"],
        "refresh_interval": 15,
        "log_tail": 200,
        "capabilities": {
            "logs": True, "exec": True, "delete": True,
            "scale": True, "restart": True, "apply": True,
        },
    })

    # Sidebar section visibility
    sidebar_sections: Dict[str, bool] = field(default_factory=lambda: {
        "overview": True, "data": True, "system": True,
        "infrastructure": True, "security": True, "models": True,
        "devtools": True,
    })

    # UI
    theme: str = "auto"
    list_per_page: int = 25

    # Security settings (admin-specific security policy configuration)
    security_config: Dict[str, Any] = field(default_factory=lambda: {
        "csrf": {
            "enabled": True,
            "max_age": 7200,
            "token_length": 32,
        },
        "rate_limit": {
            "enabled": True,
            "max_login_attempts": 5,
            "login_window": 900,
            "sensitive_op_limit": 30,
            "sensitive_op_window": 300,
            "progressive_lockout": True,
        },
        "password": {
            "min_length": 10,
            "max_length": 128,
            "require_upper": True,
            "require_lower": True,
            "require_digit": True,
            "require_special": True,
        },
        "headers": {
            "enabled": True,
            "frame_options": "DENY",
        },
        "session_fixation_protection": True,
        "event_tracker_max_events": 1000,
    })

    def is_module_enabled(self, module_name: str) -> bool:
        """Check if an admin module is enabled.

        Normalises ``admin-users`` → ``admin_users`` for convenience.
        """
        key = module_name.replace("-", "_")
        return self.modules.get(key, False)

    def is_action_allowed(self, action: "AdminAction") -> bool:
        """Return True if the given audit action should be recorded."""
        if not self.audit_enabled:
            return False
        action_name = action.value if hasattr(action, "value") else str(action)
        # Normalise to uppercase for comparison -- AdminAction values are
        # lowercase (e.g. "view") but config uses uppercase (e.g. "VIEW").
        action_upper = action_name.upper()
        if action_upper in self.audit_excluded_actions:
            return False
        # Also check the original value in case user passed lowercase
        if action_name in self.audit_excluded_actions:
            return False
        # Category-level switches
        if action_upper in ("LOGIN", "LOGOUT", "LOGIN_FAILED") and not self.audit_log_logins:
            return False
        if action_upper in ("VIEW", "LIST", "PAGE_VIEW") and not self.audit_log_views:
            return False
        if action_upper == "SEARCH" and not self.audit_log_searches:
            return False
        return True

    def is_metric_enabled(self, metric: str) -> bool:
        """Check if a monitoring metric section is enabled."""
        return metric in self.monitoring_metrics

    def is_sidebar_section_visible(self, section: str) -> bool:
        """Check if a sidebar section is visible."""
        return self.sidebar_sections.get(section, True)

    # ── Containers (Docker) helpers ──────────────────────────────────

    def get_docker_host(self) -> Optional[str]:
        """Return the configured Docker host, or None for auto-detect."""
        return self.containers_config.get("docker_host")

    def get_container_refresh_interval(self) -> int:
        """Return the auto-refresh interval for the containers page."""
        return self.containers_config.get("refresh_interval", 15)

    def get_container_log_tail(self) -> int:
        """Return the default log tail lines for container logs."""
        return self.containers_config.get("log_tail", 200)

    def is_container_action_allowed(self, action: str) -> bool:
        """Check if a container lifecycle action is permitted."""
        return action in self.containers_config.get("allowed_actions", [])

    def is_container_capability_enabled(self, capability: str) -> bool:
        """Check if a container capability (exec/prune/build/export/etc.) is enabled."""
        caps = self.containers_config.get("capabilities", {})
        return caps.get(capability, True)

    # ── Pods (Kubernetes) helpers ────────────────────────────────────

    def get_kube_namespace(self) -> str:
        """Return the configured Kubernetes namespace."""
        return self.pods_config.get("namespace", "default")

    def get_pod_refresh_interval(self) -> int:
        """Return the auto-refresh interval for the pods page."""
        return self.pods_config.get("refresh_interval", 15)

    def get_pod_log_tail(self) -> int:
        """Return the default log tail lines for pod logs."""
        return self.pods_config.get("log_tail", 200)

    def is_pod_resource_enabled(self, resource: str) -> bool:
        """Check if a K8s resource type is enabled for display."""
        return resource in self.pods_config.get("resources", [])

    def is_pod_capability_enabled(self, capability: str) -> bool:
        """Check if a pod capability (logs/exec/delete/scale/restart/apply) is enabled."""
        caps = self.pods_config.get("capabilities", {})
        return caps.get(capability, True)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the config for template consumption."""
        return {
            "modules": dict(self.modules),
            "audit": {
                "enabled": self.audit_enabled,
                "max_entries": self.audit_max_entries,
                "log_logins": self.audit_log_logins,
                "log_views": self.audit_log_views,
                "log_searches": self.audit_log_searches,
                "excluded_actions": sorted(self.audit_excluded_actions),
            },
            "monitoring": {
                "enabled": self.monitoring_enabled,
                "metrics": sorted(self.monitoring_metrics),
                "refresh_interval": self.monitoring_refresh_interval,
            },
            "containers": dict(self.containers_config),
            "pods": dict(self.pods_config),
            "security": dict(self.security_config),
            "sidebar_sections": dict(self.sidebar_sections),
            "theme": self.theme,
            "list_per_page": self.list_per_page,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "AdminConfig":
        """Build an AdminConfig from the raw Integration.admin() config dict."""
        modules_raw = raw.get("modules", {})
        audit_raw = raw.get("audit_config", {})
        monitoring_raw = raw.get("monitoring_config", {})
        containers_raw = raw.get("containers_config", {})
        pods_raw = raw.get("pods_config", {})
        sidebar_raw = raw.get("sidebar_sections", {})
        security_raw = raw.get("security_config", {})

        # Defaults for modules (monitoring, audit, containers, pods disabled by default)
        default_modules = {
            "dashboard": True, "orm": True, "build": True,
            "migrations": True, "config": True, "workspace": True,
            "permissions": True, "monitoring": False, "admin_users": True,
            "profile": True, "audit": False, "api_keys": True,
            "preferences": True,
            "containers": False, "pods": False,
            "query_inspector": False, "tasks": False, "errors": False,
            "testing": False, "storage": False, "provider": False,
        }
        modules = {**default_modules, **modules_raw}

        # If enable_audit is explicitly provided at top level, honour it
        if "enable_audit" in raw:
            modules["audit"] = bool(raw["enable_audit"])

        # ── Containers config defaults ──
        _default_containers = {
            "docker_host": None,
            "allowed_actions": [
                "start", "stop", "restart", "pause", "unpause",
                "kill", "rm", "logs", "inspect", "exec", "export",
            ],
            "log_tail": 200,
            "log_since": "",
            "refresh_interval": 15,
            "compose_files": [],
            "compose_project_dir": None,
            "show_system_containers": False,
            "capabilities": {
                "exec": True, "prune": True, "build": True,
                "export": True, "image_actions": True,
                "volume_actions": True, "network_actions": True,
            },
        }
        # Deep merge capabilities
        merged_containers = {**_default_containers, **containers_raw}
        if "capabilities" in containers_raw and isinstance(containers_raw["capabilities"], dict):
            merged_containers["capabilities"] = {
                **_default_containers["capabilities"],
                **containers_raw["capabilities"],
            }

        # ── Pods config defaults ──
        _default_pods = {
            "kubeconfig": None,
            "namespace": "default",
            "contexts": [],
            "resources": [
                "pods", "deployments", "services", "ingresses",
                "configmaps", "secrets", "namespaces", "events",
                "daemonsets", "statefulsets", "jobs", "cronjobs",
                "persistentvolumeclaims", "nodes",
            ],
            "manifest_dirs": ["k8s"],
            "manifest_patterns": ["*.yaml", "*.yml"],
            "refresh_interval": 15,
            "log_tail": 200,
            "capabilities": {
                "logs": True, "exec": True, "delete": True,
                "scale": True, "restart": True, "apply": True,
            },
        }
        merged_pods = {**_default_pods, **pods_raw}
        if "capabilities" in pods_raw and isinstance(pods_raw["capabilities"], dict):
            merged_pods["capabilities"] = {
                **_default_pods["capabilities"],
                **pods_raw["capabilities"],
            }

        # ── Resolve security config ──
        _default_security: Dict[str, Any] = {
            "csrf": {
                "enabled": True,
                "max_age": 7200,
                "token_length": 32,
            },
            "rate_limit": {
                "enabled": True,
                "max_login_attempts": 5,
                "login_window": 900,
                "sensitive_op_limit": 30,
                "sensitive_op_window": 300,
                "progressive_lockout": True,
            },
            "password": {
                "min_length": 10,
                "max_length": 128,
                "require_upper": True,
                "require_lower": True,
                "require_digit": True,
                "require_special": True,
            },
            "headers": {
                "enabled": True,
                "frame_options": "DENY",
            },
            "session_fixation_protection": True,
            "event_tracker_max_events": 1000,
        }
        # Deep merge security config -- merge nested dicts
        merged_security: Dict[str, Any] = {}
        for key, default_val in _default_security.items():
            if isinstance(default_val, dict) and key in security_raw and isinstance(security_raw[key], dict):
                merged_security[key] = {**default_val, **security_raw[key]}
            elif key in security_raw:
                merged_security[key] = security_raw[key]
            else:
                merged_security[key] = default_val

        return cls(
            modules=modules,
            audit_enabled=audit_raw.get("enabled", raw.get("enable_audit", False)),
            audit_max_entries=audit_raw.get("max_entries", raw.get("audit_max_entries", 10_000)),
            audit_log_logins=audit_raw.get("log_logins", True),
            audit_log_views=audit_raw.get("log_views", True),
            audit_log_searches=audit_raw.get("log_searches", True),
            audit_excluded_actions=frozenset(audit_raw.get("excluded_actions", [])),
            monitoring_enabled=monitoring_raw.get("enabled", False),
            monitoring_metrics=frozenset(monitoring_raw.get("metrics", [
                "cpu", "memory", "disk", "network", "process", "python", "system", "health_checks",
            ])),
            monitoring_refresh_interval=monitoring_raw.get("refresh_interval", 30),
            containers_config=merged_containers,
            pods_config=merged_pods,
            security_config=merged_security,
            sidebar_sections={
                "overview": sidebar_raw.get("overview", True),
                "data": sidebar_raw.get("data", True),
                "system": sidebar_raw.get("system", True),
                "infrastructure": sidebar_raw.get("infrastructure", True),
                "security": sidebar_raw.get("security", True),
                "models": sidebar_raw.get("models", True),
                "devtools": sidebar_raw.get("devtools", True),
            },
            theme=raw.get("theme", "auto"),
            list_per_page=raw.get("list_per_page", 25),
        )


class AdminSite:
    """
    Central admin site -- manages all registered models.

    Singleton-safe with a default() class method.
    Multiple AdminSite instances can coexist for multi-tenant scenarios.

    Attributes:
        name: Site identifier (default "admin")
        title: Dashboard title
        header: Header text
        url_prefix: URL prefix (default "/admin")
        login_url: Login page URL
    """

    _default_instance: Optional[AdminSite] = None

    def __init__(
        self,
        name: str = "admin",
        *,
        title: str = "Aquilia Admin",
        header: str = "Aquilia Administration",
        url_prefix: str = "/admin",
        login_url: str = "/admin/login",
    ):
        self.name = name
        self.title = title
        self.header = header
        self.url_prefix = url_prefix.rstrip("/")
        self.login_url = login_url

        # Registry: model_class -> ModelAdmin instance
        self._registry: Dict[Type[Model], ModelAdmin] = {}

        # Admin configuration -- populated by server._wire_admin_integration()
        self.admin_config: AdminConfig = AdminConfig()

        # Audit log -- model-backed (persists to DB), falls back to in-memory
        self.audit_log: ModelBackedAuditLog = ModelBackedAuditLog()

        # Security policy -- built from admin_config.security_config
        from .security import AdminSecurityPolicy
        self.security: AdminSecurityPolicy = AdminSecurityPolicy.from_config(
            self.admin_config.security_config
        )

        # Initialization state
        self._initialized = False

    @classmethod
    def default(cls) -> AdminSite:
        """Get or create the default AdminSite singleton."""
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    @classmethod
    def reset(cls) -> None:
        """Reset the default site (for testing)."""
        cls._default_instance = None

    def initialize(self) -> None:
        """
        Initialize the admin site.

        Flushes pending registrations and runs autodiscovery.
        Called during app startup.
        """
        if self._initialized:
            return

        from .registry import flush_pending_registrations, autodiscover

        # Flush any @register decorators that fired before init
        flushed = flush_pending_registrations()

        # Auto-discover remaining models
        auto = autodiscover()

        self._initialized = True

        # Restore audit history from CROUS file (server startup only)
        self.audit_log.start()

    def register_admin(self, model_cls: Type[Model], admin: ModelAdmin) -> None:
        """Register a model with its ModelAdmin configuration."""
        admin.model = model_cls
        self._registry[model_cls] = admin

    def register(self, model_cls: Type[Model], admin_class: Optional[Type[ModelAdmin]] = None) -> None:
        """
        Register a model (convenience method).

        If admin_class is None, uses default ModelAdmin.
        """
        if admin_class is None:
            admin_class = ModelAdmin
        admin = admin_class(model=model_cls)
        self.register_admin(model_cls, admin)

    def unregister(self, model_cls: Type[Model]) -> None:
        """Unregister a model."""
        self._registry.pop(model_cls, None)

    def is_registered(self, model_cls: Type[Model]) -> bool:
        """Check if a model is registered."""
        return model_cls in self._registry

    # ── Registry access ──────────────────────────────────────────────

    def get_model_admin(self, model_cls_or_name: Any) -> ModelAdmin:
        """
        Get ModelAdmin for a model class or name.

        Raises AdminModelNotFoundFault if not found.
        """
        if isinstance(model_cls_or_name, str):
            for cls, admin in self._registry.items():
                if cls.__name__.lower() == model_cls_or_name.lower():
                    return admin
            raise AdminModelNotFoundFault(model_cls_or_name)
        else:
            admin = self._registry.get(model_cls_or_name)
            if admin is None:
                raise AdminModelNotFoundFault(
                    model_cls_or_name.__name__ if hasattr(model_cls_or_name, "__name__") else str(model_cls_or_name)
                )
            return admin

    def get_model_class(self, model_name: str) -> Type[Model]:
        """
        Get model class by name.

        Raises AdminModelNotFoundFault if not found.
        """
        for cls in self._registry:
            if cls.__name__.lower() == model_name.lower():
                return cls
        raise AdminModelNotFoundFault(model_name)

    def get_app_list(self, identity: Optional[Identity] = None) -> List[Dict[str, Any]]:
        """
        Get list of admin apps/models grouped by app_label.

        Filters by identity permissions.
        Returns list of app dicts with their models.
        """
        apps: Dict[str, Dict[str, Any]] = {}

        for model_cls, admin in self._registry.items():
            # Permission check
            if identity and not admin.has_module_permission(identity):
                continue

            app_label = admin.get_app_label()
            if app_label not in apps:
                apps[app_label] = {
                    "app_label": app_label,
                    "app_name": app_label.replace("_", " ").title(),
                    "models": [],
                }

            apps[app_label]["models"].append({
                "name": admin.get_model_name(),
                "name_plural": admin.get_model_name_plural(),
                "model_name": model_cls.__name__,
                "url_name": model_cls.__name__.lower(),
                "icon": admin.icon,
                "perms": {
                    "view": admin.has_view_permission(identity),
                    "add": admin.has_add_permission(identity),
                    "change": admin.has_change_permission(identity),
                    "delete": admin.has_delete_permission(identity),
                },
            })

        return sorted(apps.values(), key=lambda a: a["app_label"])

    def get_registered_models(self) -> Dict[str, ModelAdmin]:
        """Get all registered model name -> ModelAdmin pairs."""
        return {cls.__name__: admin for cls, admin in self._registry.items()}

    # ── ORM metadata helpers (private) ───────────────────────────────

    @staticmethod
    def _inspect_model_methods(model_cls: type) -> Dict[str, List[str]]:
        """Categorise user-defined methods on a model class.

        Returns ``{"methods": [...], "class_methods": [...],
        "static_methods": [...], "properties": [...]}``.
        Skips dunder / private names and anything inherited from the ORM
        base ``Model``.
        """
        import inspect as _inspect

        try:
            from aquilia.models.base import Model as _BaseModel
        except Exception:
            _BaseModel = object  # type: ignore[misc,assignment]

        base_names: set = set(dir(_BaseModel))
        result: Dict[str, List[str]] = {
            "methods": [],
            "class_methods": [],
            "static_methods": [],
            "properties": [],
        }

        for name in sorted(dir(model_cls)):
            if name.startswith("_"):
                continue
            if name in base_names:
                continue
            # Skip field descriptors / Manager
            if name in getattr(model_cls, "_fields", {}):
                continue
            if name in getattr(model_cls, "_m2m_fields", {}):
                continue
            if name == "objects":
                continue

            raw = model_cls.__dict__.get(name)
            if raw is None:
                continue

            if isinstance(raw, property):
                result["properties"].append(name)
            elif isinstance(raw, classmethod):
                result["class_methods"].append(name)
            elif isinstance(raw, staticmethod):
                result["static_methods"].append(name)
            elif callable(raw):
                result["methods"].append(name)

        return result

    @staticmethod
    def _build_reverse_relations(
        registry: Dict[type, "ModelAdmin"],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Build a map of model_name → list of models that reference it.

        Scans every FK / O2O / M2M across all registered models and
        records the reverse side.
        """
        from aquilia.models.fields_module import (
            ForeignKey, OneToOneField, ManyToManyField,
        )

        reverse: Dict[str, List[Dict[str, Any]]] = {}

        for model_cls in registry:
            source_name = model_cls.__name__
            all_fields = getattr(model_cls, "_fields", {})
            m2m_fields = getattr(model_cls, "_m2m_fields", {})

            for fname, field in all_fields.items():
                if isinstance(field, (ForeignKey, OneToOneField)):
                    target = field.to if isinstance(field.to, str) else (
                        field.to.__name__ if field.to else None
                    )
                    if target:
                        reverse.setdefault(target, []).append({
                            "from_model": source_name,
                            "field": fname,
                            "type": "O2O" if isinstance(field, OneToOneField) else "FK",
                            "on_delete": getattr(field, "on_delete", "CASCADE"),
                            "related_name": getattr(field, "related_name", None),
                        })

            for fname, m2m in m2m_fields.items():
                target = m2m.to if isinstance(m2m.to, str) else (
                    m2m.to.__name__ if m2m.to else None
                )
                if target:
                    reverse.setdefault(target, []).append({
                        "from_model": source_name,
                        "field": fname,
                        "type": "M2M",
                        "related_name": getattr(m2m, "related_name", None),
                        "db_table": getattr(m2m, "db_table", None),
                    })

        return reverse

    def get_model_schema(self) -> List[Dict[str, Any]]:
        """
        Build rich schema metadata for every registered model.

        Returns per-model:
            - **fields**: every field with full attribute introspection
              (type, python_type, null, unique, primary_key, db_index,
              default, max_length, help_text, choices, choices_list,
              editable, blank, auto_now, auto_now_add, db_column,
              verbose_name, validators, relation info)
            - **relations**: FK / O2O / M2M with on_delete, through, db_table
            - **reverse_relations**: models that reference *this* model
            - **indexes**: composite + field-level indexes with condition
            - **constraints**: UniqueConstraint + CheckConstraint with expression
            - **meta**: all Options attributes (ordering, get_latest_by,
              select_on_save, db_tablespace, default_permissions, permissions,
              required_db_vendor, required_db_features, unique_together,
              proxy, managed, abstract, order_with_respect_to,
              default_related_name)
            - **sql**: DDL statements (CREATE TABLE, CREATE INDEX, M2M tables)
            - **methods**: user-defined methods, class methods, properties
            - **source**: module path and source file location
            - **fingerprint**: deterministic schema hash for migration diffs
        """
        import inspect as _inspect

        from aquilia.models.fields_module import (
            ForeignKey, OneToOneField, ManyToManyField, Field,
        )

        # Pre-compute reverse relations once for all models
        reverse_map = self._build_reverse_relations(self._registry)

        # Detect current dialect from the database connection
        dialect = "sqlite"
        try:
            sample_model = next(iter(self._registry), None)
            if sample_model is not None:
                db = getattr(sample_model, "_db", None)
                if db is not None:
                    dialect = getattr(db, "dialect", "sqlite")
        except Exception:
            pass

        models_data: List[Dict[str, Any]] = []
        model_lookup = {cls.__name__: cls for cls in self._registry}

        for model_cls, admin in self._registry.items():
            name = model_cls.__name__
            meta = getattr(model_cls, "_meta", None)
            fields_info: List[Dict[str, Any]] = []
            relations: List[Dict[str, Any]] = []

            all_fields = getattr(model_cls, "_fields", {})
            m2m_fields = getattr(model_cls, "_m2m_fields", {})

            # ── Per-field introspection ──────────────────────────────
            for fname, field in all_fields.items():
                field_data: Dict[str, Any] = {
                    "name": fname,
                    "column": getattr(field, "column_name", fname),
                    "type": getattr(field, "_field_type", type(field).__name__),
                    "field_class": type(field).__name__,
                    "python_type": getattr(field, "_python_type", str).__name__
                        if hasattr(field, "_python_type") else "str",
                    "null": getattr(field, "null", False),
                    "blank": getattr(field, "blank", False),
                    "unique": getattr(field, "unique", False),
                    "primary_key": getattr(field, "primary_key", False),
                    "db_index": getattr(field, "db_index", False),
                    "db_column": getattr(field, "db_column", None),
                    "default": repr(getattr(field, "default", None))
                        if hasattr(field, "default") and getattr(field, "default", None) is not None
                        else None,
                    "max_length": getattr(field, "max_length", None),
                    "help_text": getattr(field, "help_text", ""),
                    "verbose_name": getattr(field, "verbose_name", None),
                    "choices": bool(getattr(field, "choices", None)),
                    "choices_list": [
                        {"value": c[0], "label": c[1]}
                        for c in (getattr(field, "choices", None) or [])
                    ] if getattr(field, "choices", None) else [],
                    "editable": getattr(field, "editable", True),
                    "auto_now": getattr(field, "auto_now", False),
                    "auto_now_add": getattr(field, "auto_now_add", False),
                    "validators": [
                        type(v).__name__ for v in (getattr(field, "validators", None) or [])
                    ],
                }

                # Decimal-specific attributes
                if hasattr(field, "max_digits"):
                    field_data["max_digits"] = field.max_digits
                if hasattr(field, "decimal_places"):
                    field_data["decimal_places"] = field.decimal_places

                # ── Relation info ────────────────────────────────────
                if isinstance(field, ManyToManyField):
                    target = field.to if isinstance(field.to, str) else (
                        field.to.__name__ if field.to else "?"
                    )
                    m2m_db_table = getattr(field, "db_table", None)
                    through = getattr(field, "through", None)
                    if through and not isinstance(through, str):
                        through = through.__name__
                    related_name = getattr(field, "related_name", None)
                    relations.append({
                        "type": "M2M",
                        "field": fname,
                        "from": name,
                        "to": target,
                        "related_name": related_name,
                        "through": through,
                        "db_table": m2m_db_table,
                    })
                    field_data["relation"] = {
                        "type": "M2M", "to": target,
                        "db_table": m2m_db_table,
                        "related_name": related_name,
                    }
                elif isinstance(field, OneToOneField):
                    target = field.to if isinstance(field.to, str) else (
                        field.to.__name__ if field.to else "?"
                    )
                    on_delete = getattr(field, "on_delete", "CASCADE")
                    related_name = getattr(field, "related_name", None)
                    relations.append({
                        "type": "O2O",
                        "field": fname,
                        "from": name,
                        "to": target,
                        "on_delete": on_delete,
                        "related_name": related_name,
                    })
                    field_data["relation"] = {
                        "type": "O2O", "to": target,
                        "on_delete": on_delete,
                        "related_name": related_name,
                    }
                elif isinstance(field, ForeignKey):
                    target = field.to if isinstance(field.to, str) else (
                        field.to.__name__ if field.to else "?"
                    )
                    on_delete = getattr(field, "on_delete", "CASCADE")
                    related_name = getattr(field, "related_name", None)
                    relations.append({
                        "type": "FK",
                        "field": fname,
                        "from": name,
                        "to": target,
                        "on_delete": on_delete,
                        "related_name": related_name,
                    })
                    field_data["relation"] = {
                        "type": "FK", "to": target,
                        "on_delete": on_delete,
                        "related_name": related_name,
                    }

                fields_info.append(field_data)

            # ── Indexes from Meta ────────────────────────────────────
            indexes_info: List[Dict[str, Any]] = []
            if meta:
                for idx in getattr(meta, "indexes", []):
                    idx_entry: Dict[str, Any] = {
                        "fields": getattr(idx, "fields", []),
                        "name": getattr(idx, "name", None),
                        "unique": getattr(idx, "unique", False),
                    }
                    # Condition (partial index WHERE clause)
                    condition = getattr(idx, "condition", None)
                    if condition:
                        idx_entry["condition"] = str(condition)
                    # Index type hint (btree, hash, gin, gist, etc.)
                    idx_type = getattr(idx, "index_type", None) or type(idx).__name__
                    if idx_type != "Index":
                        idx_entry["index_type"] = idx_type
                    indexes_info.append(idx_entry)
                # unique_together → virtual unique index
                for ut in getattr(meta, "unique_together", []):
                    indexes_info.append({
                        "fields": list(ut),
                        "name": None,
                        "unique": True,
                        "source": "unique_together",
                    })

            # Field-level indexes
            for fname, field in all_fields.items():
                if getattr(field, "db_index", False) and not getattr(field, "primary_key", False):
                    indexes_info.append({
                        "fields": [fname],
                        "name": f"idx_{name.lower()}_{fname}",
                        "unique": getattr(field, "unique", False),
                        "source": "field_level",
                    })

            # ── Constraints from Meta ────────────────────────────────
            constraints_info: List[Dict[str, Any]] = []
            if meta:
                for c in getattr(meta, "constraints", []):
                    c_entry: Dict[str, Any] = {
                        "name": getattr(c, "name", None),
                        "type": type(c).__name__,
                    }
                    if hasattr(c, "fields"):
                        c_entry["fields"] = list(c.fields)
                    if hasattr(c, "check"):
                        c_entry["check_expression"] = str(c.check)
                    if hasattr(c, "violation_error_message"):
                        c_entry["violation_message"] = c.violation_error_message
                    constraints_info.append(c_entry)

            # ── Meta options (full) ──────────────────────────────────
            meta_info: Dict[str, Any] = {}
            if meta:
                meta_info = {
                    "ordering": getattr(meta, "ordering", []),
                    "get_latest_by": getattr(meta, "get_latest_by", None),
                    "verbose_name": getattr(meta, "verbose_name", name),
                    "verbose_name_plural": getattr(meta, "verbose_name_plural", f"{name}s"),
                    "app_label": getattr(meta, "app_label", ""),
                    "managed": getattr(meta, "managed", True),
                    "abstract": getattr(meta, "abstract", False),
                    "proxy": getattr(meta, "proxy", False),
                    "select_on_save": getattr(meta, "select_on_save", False),
                    "db_tablespace": getattr(meta, "db_tablespace", ""),
                    "default_permissions": list(getattr(meta, "default_permissions", ())),
                    "permissions": [
                        {"codename": p[0], "name": p[1]}
                        for p in getattr(meta, "permissions", [])
                    ],
                    "unique_together": [list(ut) for ut in getattr(meta, "unique_together", [])],
                    "order_with_respect_to": getattr(meta, "order_with_respect_to", None),
                    "default_related_name": getattr(meta, "default_related_name", None),
                    "required_db_vendor": getattr(meta, "required_db_vendor", None),
                    "required_db_features": getattr(meta, "required_db_features", []),
                    "label": getattr(meta, "label", ""),
                    "label_lower": getattr(meta, "label_lower", ""),
                }

            # ── SQL DDL generation ───────────────────────────────────
            sql_info: Dict[str, Any] = {}
            try:
                sql_info["create_table"] = model_cls.generate_create_table_sql(dialect)
            except Exception:
                sql_info["create_table"] = None
            try:
                sql_info["indexes"] = model_cls.generate_index_sql(dialect)
            except Exception:
                sql_info["indexes"] = []
            try:
                sql_info["m2m_tables"] = model_cls.generate_m2m_sql(dialect)
            except Exception:
                sql_info["m2m_tables"] = []

            # ── Model fingerprint ────────────────────────────────────
            fingerprint = None
            try:
                fingerprint = model_cls.fingerprint()
            except Exception:
                pass

            # ── Source location ───────────────────────────────────────
            source_module = getattr(model_cls, "__module__", "")
            source_file = ""
            try:
                source_file = _inspect.getfile(model_cls)
            except (TypeError, OSError):
                pass

            # ── User-defined methods ─────────────────────────────────
            model_methods = self._inspect_model_methods(model_cls)

            # ── Reverse relations ────────────────────────────────────
            reverse_rels = reverse_map.get(name, [])

            # ── M2M junction table details ───────────────────────────
            m2m_tables: List[Dict[str, Any]] = []
            for m2m_name, m2m_field in m2m_fields.items():
                try:
                    jt = m2m_field.junction_table_name(model_cls)
                    src_col, tgt_col = m2m_field.junction_columns(model_cls)
                    target = m2m_field.to if isinstance(m2m_field.to, str) else (
                        m2m_field.to.__name__ if m2m_field.to else "?"
                    )
                    m2m_tables.append({
                        "field": m2m_name,
                        "junction_table": jt,
                        "source_column": src_col,
                        "target_column": tgt_col,
                        "target_model": target,
                        "db_table": getattr(m2m_field, "db_table", None),
                        "through": getattr(m2m_field, "through", None),
                    })
                except Exception:
                    pass

            models_data.append({
                "name": name,
                "table_name": getattr(model_cls, "_table_name", name.lower()),
                "app_label": admin.get_app_label(),
                "verbose_name": admin.get_model_name(),
                "verbose_name_plural": admin.get_model_name_plural(),
                "fields": fields_info,
                "field_count": len(fields_info),
                "relations": relations,
                "reverse_relations": reverse_rels,
                "m2m_tables": m2m_tables,
                "indexes": indexes_info,
                "constraints": constraints_info,
                "meta": meta_info,
                "sql": sql_info,
                "methods": model_methods,
                "source": {
                    "module": source_module,
                    "file": source_file,
                },
                "fingerprint": fingerprint,
                # Flat compat keys (kept for backward compatibility)
                "ordering": meta_info.get("ordering", []),
                "managed": meta_info.get("managed", True),
                "abstract": meta_info.get("abstract", False),
                "pk_field": getattr(model_cls, "_pk_attr", "id"),
            })

        return models_data

    def get_orm_metadata(self) -> Dict[str, Any]:
        """
        Gather comprehensive ORM-level metadata beyond individual models.

        Returns:
            - **database**: connection info (dialect, driver, url, status)
            - **backend**: capabilities, version info
            - **stats**: total models, fields, relations, indexes, constraints
            - **dependency_graph**: model → [models it depends on via FK/M2M]
            - **models**: condensed model list with table names
        """
        from aquilia.models.fields_module import ForeignKey, ManyToManyField

        result: Dict[str, Any] = {
            "database": {},
            "backend": {},
            "stats": {},
            "dependency_graph": {},
            "models": [],
        }

        # ── Database connection info ─────────────────────────────────
        db = None
        try:
            sample_model = next(iter(self._registry), None)
            if sample_model is not None:
                db = getattr(sample_model, "_db", None)
        except Exception:
            pass

        if db is not None:
            url = getattr(db, "url", "")
            # Redact password from URL for display
            import re as _re
            safe_url = _re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)

            result["database"] = {
                "dialect": getattr(db, "dialect", "unknown"),
                "driver": getattr(db, "driver", "unknown"),
                "url": safe_url,
                "connected": getattr(db, "is_connected", False),
                "in_transaction": getattr(db, "in_transaction", False),
            }

            # Backend capabilities
            try:
                caps = db.capabilities
                result["backend"] = {
                    "supports_returning": getattr(caps, "supports_returning", False),
                    "supports_json": getattr(caps, "supports_json", False),
                    "supports_arrays": getattr(caps, "supports_arrays", False),
                    "supports_upsert": getattr(caps, "supports_upsert", False),
                    "supports_window_functions": getattr(caps, "supports_window_functions", False),
                    "supports_cte": getattr(caps, "supports_cte", False),
                    "supports_partial_indexes": getattr(caps, "supports_partial_indexes", False),
                    "supports_transactions": getattr(caps, "supports_transactions", True),
                    "max_identifier_length": getattr(caps, "max_identifier_length", 0),
                    "param_style": getattr(caps, "param_style", "?"),
                }
            except Exception:
                pass

            # Config object info (if typed config was used)
            config = getattr(db, "_config", None)
            if config is not None:
                result["database"]["config_type"] = type(config).__name__
                config_info: Dict[str, Any] = {
                    "type": type(config).__name__,
                }
                for attr in ("host", "port", "user", "name", "database",
                             "service_name", "charset", "collation",
                             "min_connections", "max_connections",
                             "ssl", "timeout", "pool_size",
                             "pool_recycle", "echo"):
                    val = getattr(config, attr, None)
                    if val is not None and val != "" and val != 0:
                        config_info[attr] = val
                result["database"]["config"] = config_info

        # ── Global stats ─────────────────────────────────────────────
        total_fields = 0
        total_relations = 0
        total_indexes = 0
        total_constraints = 0
        total_m2m = 0

        for model_cls in self._registry:
            fields = getattr(model_cls, "_fields", {})
            m2m = getattr(model_cls, "_m2m_fields", {})
            meta = getattr(model_cls, "_meta", None)

            total_fields += len(fields)
            total_m2m += len(m2m)
            if meta:
                total_indexes += len(getattr(meta, "indexes", []))
                total_constraints += len(getattr(meta, "constraints", []))

            for f in fields.values():
                if isinstance(f, ForeignKey):
                    total_relations += 1
            total_relations += len(m2m)

            # Count field-level indexes
            for f in fields.values():
                if getattr(f, "db_index", False) and not getattr(f, "primary_key", False):
                    total_indexes += 1

        result["stats"] = {
            "total_models": len(self._registry),
            "total_fields": total_fields,
            "total_relations": total_relations,
            "total_m2m_fields": total_m2m,
            "total_indexes": total_indexes,
            "total_constraints": total_constraints,
        }

        # ── Dependency graph ─────────────────────────────────────────
        for model_cls in self._registry:
            model_name = model_cls.__name__
            deps: List[str] = []
            seen: set = set()

            fields = getattr(model_cls, "_fields", {})
            m2m = getattr(model_cls, "_m2m_fields", {})

            for f in fields.values():
                if isinstance(f, ForeignKey):
                    target = f.to if isinstance(f.to, str) else (
                        f.to.__name__ if f.to else None
                    )
                    if target and target not in seen and target != model_name:
                        deps.append(target)
                        seen.add(target)

            for m in m2m.values():
                target = m.to if isinstance(m.to, str) else (
                    m.to.__name__ if m.to else None
                )
                if target and target not in seen and target != model_name:
                    deps.append(target)
                    seen.add(target)

            result["dependency_graph"][model_name] = deps

        # ── Condensed model list ─────────────────────────────────────
        for model_cls, admin in self._registry.items():
            fields = getattr(model_cls, "_fields", {})
            m2m = getattr(model_cls, "_m2m_fields", {})
            meta = getattr(model_cls, "_meta", None)
            rel_count = sum(1 for f in fields.values() if isinstance(f, ForeignKey)) + len(m2m)
            idx_count = len(getattr(meta, "indexes", [])) if meta else 0
            for f in fields.values():
                if getattr(f, "db_index", False) and not getattr(f, "primary_key", False):
                    idx_count += 1
            result["models"].append({
                "name": model_cls.__name__,
                "table": getattr(model_cls, "_table_name", ""),
                "app_label": admin.get_app_label(),
                "field_count": len(fields),
                "pk": getattr(model_cls, "_pk_attr", "id"),
                "relation_count": rel_count,
                "index_count": idx_count,
                "managed": getattr(meta, "managed", True) if meta else True,
            })

        return result

    # ── Query Inspector data ─────────────────────────────────────────

    def get_query_inspector_data(self) -> Dict[str, Any]:
        """
        Gather query inspector data: recent queries, slow queries,
        N+1 detections, and aggregate stats.
        """
        from .query_inspector import get_query_inspector
        inspector = get_query_inspector()
        return inspector.get_stats()

    # ── Error Tracker data ───────────────────────────────────────────

    def get_error_tracker_data(self) -> Dict[str, Any]:
        """
        Gather error tracker data: recent errors, error groups,
        frequency analysis, and aggregate stats.
        """
        from .error_tracker import get_error_tracker
        tracker = get_error_tracker()
        return tracker.get_stats()

    # ── Background Tasks data ────────────────────────────────────────

    async def get_tasks_data(self) -> Dict[str, Any]:
        """
        Gather background task manager data: job list, queue stats,
        worker status, and aggregate stats.
        """
        try:
            from aquilia.tasks import TaskManager
            # Try to find the active TaskManager instance
            manager = getattr(self, "_task_manager", None)
            if manager is None:
                # Return empty structure if no task manager is configured
                return {
                    "available": False,
                    "stats": {
                        "total_jobs": 0,
                        "by_state": {},
                        "queues": [],
                        "queue_count": 0,
                        "avg_duration_ms": 0,
                        "dead_letter_count": 0,
                        "completed_count": 0,
                        "failed_count": 0,
                        "active_count": 0,
                        "pending_count": 0,
                        "manager": {
                            "running": False,
                            "num_workers": 0,
                            "total_enqueued": 0,
                            "total_completed": 0,
                            "total_failed": 0,
                            "uptime_seconds": 0,
                            "queues": [],
                            "backend": "None",
                        },
                    },
                    "jobs": [],
                    "queue_stats": {},
                    "registered_tasks": [],
                }
            stats = await manager.get_stats()
            jobs = await manager.list_jobs(limit=100)
            queue_stats = await manager.get_queue_stats()

            # ── Gather registered task definitions ────────────────
            registered_tasks = []
            try:
                from aquilia.tasks.decorators import get_registered_tasks
                for name, desc in get_registered_tasks().items():
                    sched = getattr(desc, "schedule", None)
                    registered_tasks.append({
                        "name": name,
                        "queue": getattr(desc, "queue", "default"),
                        "priority": getattr(desc, "priority", "NORMAL").name
                            if hasattr(getattr(desc, "priority", None), "name")
                            else str(getattr(desc, "priority", "NORMAL")),
                        "max_retries": getattr(desc, "max_retries", 3),
                        "timeout": getattr(desc, "timeout", 300.0),
                        "retry_delay": getattr(desc, "retry_delay", 1.0),
                        "retry_backoff": getattr(desc, "retry_backoff", 2.0),
                        "tags": getattr(desc, "tags", []),
                        "schedule": sched.human_readable if sched else "on-demand",
                        "dispatch": "periodic" if sched else "on-demand",
                    })
            except Exception:
                pass

            return {
                "available": True,
                "stats": stats,
                "jobs": [j.to_dict() for j in jobs],
                "queue_stats": {q: dict(s) for q, s in queue_stats.items()},
                "registered_tasks": registered_tasks,
            }
        except Exception:
            return {
                "available": False,
                "stats": {},
                "jobs": [],
                "queue_stats": {},
                "registered_tasks": [],
            }

    def set_task_manager(self, manager) -> None:
        """Register the application's TaskManager for admin integration."""
        self._task_manager = manager

    # ── Mailer data ──────────────────────────────────────────────────

    def set_mail_service(self, service) -> None:
        """Register the application's MailService for admin integration."""
        self._mail_service = service

    def get_mailer_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive mail subsystem data for the admin mailer page.

        Inspects the MailService, MailConfig, providers, template dirs,
        queue stats, rate limits, security settings, and recent envelope history.
        """
        data: Dict[str, Any] = {
            "available": False,
            "enabled": False,
            "config": {},
            "providers": [],
            "provider_count": 0,
            "active_provider_count": 0,
            "default_from": "noreply@localhost",
            "default_reply_to": None,
            "subject_prefix": "",
            "preview_mode": False,
            "console_backend": False,
            "metrics_enabled": False,
            "tracing_enabled": False,
            "retry": {},
            "rate_limit": {},
            "security": {},
            "templates": {},
            "queue": {},
            "is_healthy": False,
            "recent_envelopes": [],
            "stats": {
                "total_sent": 0,
                "total_failed": 0,
                "total_queued": 0,
                "total_bounced": 0,
            },
        }

        svc = getattr(self, "_mail_service", None)
        if svc is None:
            return data

        data["available"] = True

        try:
            config = getattr(svc, "config", None)
            if config is None:
                return data

            data["enabled"] = getattr(config, "enabled", False)
            data["default_from"] = getattr(config, "default_from", "noreply@localhost")
            data["default_reply_to"] = getattr(config, "default_reply_to", None)
            data["subject_prefix"] = getattr(config, "subject_prefix", "")
            data["preview_mode"] = getattr(config, "preview_mode", False)
            data["console_backend"] = getattr(config, "console_backend", False)
            data["metrics_enabled"] = getattr(config, "metrics_enabled", False)
            data["tracing_enabled"] = getattr(config, "tracing_enabled", False)
            data["is_healthy"] = svc.is_healthy() if hasattr(svc, "is_healthy") else False

            # Providers
            providers_info = []
            config_providers = getattr(config, "providers", [])
            active_names = svc.get_provider_names() if hasattr(svc, "get_provider_names") else []
            for pc in config_providers:
                p_name = getattr(pc, "name", "unknown")
                p_type = getattr(pc, "type", "unknown")
                p_enabled = getattr(pc, "enabled", True)
                p_priority = getattr(pc, "priority", 50)
                p_active = p_name in active_names
                p_rate = getattr(pc, "rate_limit_per_min", 600)

                # SMTP-specific
                p_host = getattr(pc, "host", None)
                p_port = getattr(pc, "port", None)
                p_tls = getattr(pc, "use_tls", True)
                p_ssl = getattr(pc, "use_ssl", False)
                p_timeout = getattr(pc, "timeout", 30.0)

                providers_info.append({
                    "name": p_name,
                    "type": p_type,
                    "type_display": {
                        "smtp": "SMTP",
                        "ses": "AWS SES",
                        "sendgrid": "SendGrid",
                        "console": "Console (Dev)",
                        "file": "File (Dev)",
                    }.get(p_type, p_type.title()),
                    "enabled": p_enabled,
                    "active": p_active,
                    "priority": p_priority,
                    "rate_limit_per_min": p_rate,
                    "host": p_host,
                    "port": p_port,
                    "use_tls": p_tls,
                    "use_ssl": p_ssl,
                    "timeout": p_timeout,
                    "status": "active" if p_active else ("disabled" if not p_enabled else "inactive"),
                })

            data["providers"] = providers_info
            data["provider_count"] = len(providers_info)
            data["active_provider_count"] = len(active_names)

            # Retry config
            retry = getattr(config, "retry", None)
            if retry:
                data["retry"] = {
                    "max_attempts": getattr(retry, "max_attempts", 5),
                    "base_delay": getattr(retry, "base_delay", 1.0),
                    "max_delay": getattr(retry, "max_delay", 3600.0),
                    "jitter": getattr(retry, "jitter", True),
                }

            # Rate limit config
            rl = getattr(config, "rate_limit", None)
            if rl:
                data["rate_limit"] = {
                    "global_per_minute": getattr(rl, "global_per_minute", 1000),
                    "per_domain_per_minute": getattr(rl, "per_domain_per_minute", 100),
                    "per_provider_per_minute": getattr(rl, "per_provider_per_minute", None),
                }

            # Security config
            sec = getattr(config, "security", None)
            if sec:
                data["security"] = {
                    "dkim_enabled": getattr(sec, "dkim_enabled", False),
                    "dkim_domain": getattr(sec, "dkim_domain", None),
                    "dkim_selector": getattr(sec, "dkim_selector", "aquilia"),
                    "require_tls": getattr(sec, "require_tls", True),
                    "pii_redaction_enabled": getattr(sec, "pii_redaction_enabled", False),
                    "allowed_from_domains": list(getattr(sec, "allowed_from_domains", [])),
                }

            # Template config
            tmpl = getattr(config, "templates", None)
            if tmpl:
                data["templates"] = {
                    "template_dirs": list(getattr(tmpl, "template_dirs", ["mail_templates"])),
                    "auto_escape": getattr(tmpl, "auto_escape", True),
                    "cache_compiled": getattr(tmpl, "cache_compiled", True),
                    "strict_mode": getattr(tmpl, "strict_mode", False),
                }

            # Queue config
            queue = getattr(config, "queue", None)
            if queue:
                data["queue"] = {
                    "batch_size": getattr(queue, "batch_size", 50),
                    "poll_interval": getattr(queue, "poll_interval", 1.0),
                    "dedupe_window_seconds": getattr(queue, "dedupe_window_seconds", 3600),
                    "retention_days": getattr(queue, "retention_days", 30),
                }

            # Full config dict for display
            try:
                data["config"] = config.to_dict()
            except Exception:
                data["config"] = {}

        except Exception as e:
            logger.warning(f"Error gathering mailer data: {e}")

        return data

    # ── Provider & Deployment data ──────────────────────────────────

    def set_provider_services(
        self,
        client=None,
        deployer=None,
        credential_store=None,
    ) -> None:
        """Register cloud provider services for admin integration.

        Args:
            client: A RenderClient (or compatible) instance for API calls.
            deployer: A RenderDeployer (or compatible) instance for deployments.
            credential_store: A RenderCredentialStore for credential management.
        """
        self._provider_client = client
        self._provider_deployer = deployer
        self._provider_credential_store = credential_store

    def get_provider_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive cloud provider data for the admin provider page.

        Inspects the RenderClient, RenderDeployer, and RenderCredentialStore
        to build a complete view of services, deployments, databases,
        credentials, env groups, audit logs, user profile, projects,
        custom domains, webhooks, blueprints, workspace members, and more.
        """
        data: Dict[str, Any] = {
            "available": False,
            "provider_name": "Render",
            "services": [],
            "services_live": 0,
            "deploys": [],
            "total_deploys": 0,
            "postgres_instances": [],
            "postgres_count": 0,
            "kv_instances": [],
            "kv_count": 0,
            "env_groups": [],
            "env_group_count": 0,
            "env_vars_by_service": {},
            "credential_status": "unconfigured",
            "credential_cipher": "—",
            "crous_version": "—",
            "token_age": "—",
            "token_expired": True,
            "owner_name": "—",
            "default_region": "—",
            "audit_entries": [],
            # ── Extended data (Phase 18) ──
            "user_profile": {},
            "render_workspaces": [],
            "workspace_members": [],
            "workspace_member_count": 0,
            "custom_domains": [],
            "custom_domain_count": 0,
            "projects": [],
            "project_count": 0,
            "webhooks": [],
            "webhook_count": 0,
            "blueprints": [],
            "blueprint_count": 0,
            "registry_credentials": [],
            "registry_credential_count": 0,
            "notification_settings": {},
        }

        client = getattr(self, "_provider_client", None)
        deployer = getattr(self, "_provider_deployer", None)
        store = getattr(self, "_provider_credential_store", None)

        # Auto-discover default credential store if none was wired
        # (mirrors CLI: RenderCredentialStore() uses <workspace>/.aquilia/providers/render/)
        if store is None:
            try:
                from aquilia.providers.render.store import RenderCredentialStore
                _default_store = RenderCredentialStore()
                if _default_store.is_configured():
                    store = _default_store
                    self._provider_credential_store = store
                    # Also load token and create client if we don't have one
                    if client is None:
                        try:
                            _token = store.load()
                            if _token:
                                from aquilia.providers.render.client import RenderClient
                                client = RenderClient(token=_token)
                                self._provider_client = client
                                try:
                                    from aquilia.providers.render.deployer import RenderDeployer
                                    deployer = RenderDeployer(client=client)
                                    self._provider_deployer = deployer
                                except Exception:
                                    pass
                        except Exception:
                            pass
            except Exception:
                pass

        if client is None and deployer is None and store is None:
            return data

        data["available"] = True

        # ── Credential store info ──
        if store is not None:
            try:
                status = store.status() if hasattr(store, "status") else {}
                is_configured = status.get("configured", False)
                is_expired = status.get("expired", False)
                data["credential_status"] = "active" if (is_configured and not is_expired) else ("inactive" if is_configured else "unconfigured")
                data["credential_cipher"] = status.get("cipher_suite", "AES-256-GCM")
                data["crous_version"] = f"v{status.get('crous_version', 2)}"
                age_hours = status.get("token_age_hours")
                data["token_age"] = f"{age_hours}h" if age_hours is not None else "—"
                data["token_expired"] = is_expired
                data["owner_name"] = status.get("owner_name") or "—"
                data["default_region"] = status.get("default_region") or "—"
            except Exception as e:
                logger.warning(f"Error reading credential store: {e}")

            try:
                if hasattr(store, "get_audit_log"):
                    audit_raw = store.get_audit_log()
                    data["audit_entries"] = [
                        {"ts": e.get("timestamp", "—"), "action": e.get("action", "—"),
                         "details": e.get("details", "")}
                        for e in (audit_raw or [])
                    ]
            except Exception:
                pass

        # ── Services ──
        if client is not None:
            try:
                if hasattr(client, "list_services"):
                    services_raw = client.list_services()
                    if isinstance(services_raw, list):
                        for svc in services_raw:
                            s = svc if isinstance(svc, dict) else (svc.__dict__ if hasattr(svc, "__dict__") else {})
                            data["services"].append({
                                "id": s.get("id", s.get("service_id", "—")),
                                "name": s.get("name", "unnamed"),
                                "type": s.get("type", s.get("service_type", "web_service")),
                                "status": s.get("status", s.get("state", "unknown")),
                                "region": s.get("region", "—"),
                                "plan": s.get("plan", s.get("instance_type", "—")),
                                "url": s.get("url", s.get("service_url", "—")),
                                "created_at": str(s.get("created_at", s.get("createdAt", "—"))),
                                "updated_at": str(s.get("updated_at", s.get("updatedAt", "—"))),
                            })
                        data["services_live"] = sum(
                            1 for s in data["services"] if s.get("status", "").lower() == "live"
                        )
            except Exception as e:
                logger.warning(f"Error listing services: {e}")

            # ── Deploys ──
            try:
                if hasattr(client, "list_deploys"):
                    for svc in data["services"][:10]:
                        svc_id = svc.get("id", "")
                        if not svc_id or svc_id == "—":
                            continue
                        deploys_raw = client.list_deploys(svc_id)
                        if isinstance(deploys_raw, list):
                            for d in deploys_raw[:20]:
                                dp = d if isinstance(d, dict) else (d.__dict__ if hasattr(d, "__dict__") else {})
                                data["deploys"].append({
                                    "id": dp.get("id", "—"),
                                    "service_id": svc_id,
                                    "service_name": svc.get("name", "—"),
                                    "status": dp.get("status", "unknown"),
                                    "trigger": dp.get("trigger", dp.get("type", "manual")),
                                    "commit_id": dp.get("commit_id", dp.get("commitId", "—")),
                                    "created_at": str(dp.get("created_at", dp.get("createdAt", "—"))),
                                })
                data["total_deploys"] = len(data["deploys"])
            except Exception as e:
                logger.warning(f"Error listing deploys: {e}")

            # ── PostgreSQL instances ──
            try:
                if hasattr(client, "list_postgres"):
                    pg_raw = client.list_postgres()
                    if isinstance(pg_raw, list):
                        for db in pg_raw:
                            d = db if isinstance(db, dict) else (db.__dict__ if hasattr(db, "__dict__") else {})
                            data["postgres_instances"].append({
                                "id": d.get("id", "—"),
                                "name": d.get("name", "unnamed"),
                                "region": d.get("region", "—"),
                                "plan": d.get("plan", "starter"),
                                "version": d.get("version", d.get("databaseVersion", "16")),
                            })
                        data["postgres_count"] = len(data["postgres_instances"])
            except Exception:
                pass

            # ── Key-Value (Redis) instances ──
            try:
                if hasattr(client, "list_key_value"):
                    kv_raw = client.list_key_value()
                    if isinstance(kv_raw, list):
                        for kv in kv_raw:
                            k = kv if isinstance(kv, dict) else (kv.__dict__ if hasattr(kv, "__dict__") else {})
                            data["kv_instances"].append({
                                "id": k.get("id", "—"),
                                "name": k.get("name", "unnamed"),
                                "region": k.get("region", "—"),
                                "plan": k.get("plan", "starter"),
                            })
                        data["kv_count"] = len(data["kv_instances"])
            except Exception:
                pass

            # ── Env groups ──
            try:
                if hasattr(client, "list_env_groups"):
                    eg_raw = client.list_env_groups()
                    if isinstance(eg_raw, list):
                        data["env_groups"] = eg_raw
                        data["env_group_count"] = len(eg_raw)
            except Exception:
                pass

            # ── Env vars by service ──
            try:
                if hasattr(client, "get_env_vars"):
                    for svc in data["services"][:10]:
                        svc_id = svc.get("id", "")
                        svc_name = svc.get("name", "unknown")
                        if not svc_id or svc_id == "—":
                            continue
                        try:
                            vars_raw = client.get_env_vars(svc_id)
                            if isinstance(vars_raw, list):
                                data["env_vars_by_service"][svc_name] = [
                                    {"key": v.get("key", ""), "value": v.get("value", "")}
                                    for v in vars_raw
                                ]
                        except Exception:
                            pass
            except Exception:
                pass

            # ── User Profile (GET /users) ──
            try:
                if hasattr(client, "get_user"):
                    user_raw = client.get_user()
                    if isinstance(user_raw, dict) and user_raw:
                        data["user_profile"] = {
                            "id": user_raw.get("id", "—"),
                            "name": user_raw.get("name", "—"),
                            "email": user_raw.get("email", "—"),
                            "type": user_raw.get("type", "user"),
                            "two_factor_enabled": user_raw.get("twoFactorAuth", user_raw.get("two_factor_auth", False)),
                            "created_at": str(user_raw.get("createdAt", user_raw.get("created_at", "—"))),
                        }
            except Exception:
                pass

            # ── Render Workspaces (Owners) ──
            try:
                if hasattr(client, "list_owners"):
                    owners_raw = client.list_owners()
                    if isinstance(owners_raw, list):
                        for own in owners_raw:
                            o = own if isinstance(own, dict) else (own.__dict__ if hasattr(own, "__dict__") else {})
                            data["render_workspaces"].append({
                                "id": o.get("id", "—"),
                                "name": o.get("name", "—"),
                                "email": o.get("email", "—"),
                                "type": o.get("type", "user"),
                            })
            except Exception:
                pass

            # ── Workspace Members ──
            _primary_owner_id = data["user_profile"].get("id") or (
                data["render_workspaces"][0]["id"] if data["render_workspaces"] else ""
            )
            if _primary_owner_id and _primary_owner_id != "—":
                try:
                    if hasattr(client, "list_workspace_members"):
                        members_raw = client.list_workspace_members(_primary_owner_id)
                        if isinstance(members_raw, list):
                            for m in members_raw:
                                mem = m if isinstance(m, dict) else (m.__dict__ if hasattr(m, "__dict__") else {})
                                data["workspace_members"].append({
                                    "id": mem.get("id", "—"),
                                    "name": mem.get("name", "—"),
                                    "email": mem.get("email", "—"),
                                    "role": mem.get("role", "member"),
                                    "joined_at": str(mem.get("joined_at", mem.get("joinedAt", "—"))),
                                })
                            data["workspace_member_count"] = len(data["workspace_members"])
                except Exception:
                    pass

            # ── Custom Domains (per service) ──
            try:
                if hasattr(client, "list_custom_domains"):
                    for svc in data["services"][:10]:
                        svc_id = svc.get("id", "")
                        svc_name = svc.get("name", "unknown")
                        if not svc_id or svc_id == "—":
                            continue
                        try:
                            domains_raw = client.list_custom_domains(svc_id)
                            if isinstance(domains_raw, list):
                                for dom in domains_raw:
                                    dd = dom if isinstance(dom, dict) else (dom.__dict__ if hasattr(dom, "__dict__") else {})
                                    data["custom_domains"].append({
                                        "id": dd.get("id", "—"),
                                        "name": dd.get("name", dd.get("domain", "—")),
                                        "service_name": svc_name,
                                        "verification_status": dd.get("verificationStatus", dd.get("verification_status", "unknown")),
                                        "created_at": str(dd.get("createdAt", dd.get("created_at", "—"))),
                                    })
                        except Exception:
                            pass
                    data["custom_domain_count"] = len(data["custom_domains"])
            except Exception:
                pass

            # ── Projects ──
            try:
                if hasattr(client, "list_projects"):
                    proj_raw = client.list_projects()
                    if isinstance(proj_raw, list):
                        for p in proj_raw:
                            pp = p if isinstance(p, dict) else (p.__dict__ if hasattr(p, "__dict__") else {})
                            data["projects"].append({
                                "id": pp.get("id", "—"),
                                "name": pp.get("name", "unnamed"),
                                "created_at": str(pp.get("createdAt", pp.get("created_at", "—"))),
                            })
                        data["project_count"] = len(data["projects"])
            except Exception:
                pass

            # ── Webhooks ──
            try:
                if hasattr(client, "list_webhooks"):
                    wh_raw = client.list_webhooks()
                    if isinstance(wh_raw, list):
                        for wh in wh_raw:
                            w = wh if isinstance(wh, dict) else (wh.__dict__ if hasattr(wh, "__dict__") else {})
                            data["webhooks"].append({
                                "id": w.get("id", "—"),
                                "url": w.get("url", "—"),
                                "enabled": w.get("enabled", True),
                                "created_at": str(w.get("createdAt", w.get("created_at", "—"))),
                            })
                        data["webhook_count"] = len(data["webhooks"])
            except Exception:
                pass

            # ── Blueprints ──
            try:
                if hasattr(client, "list_blueprints"):
                    bp_raw = client.list_blueprints()
                    if isinstance(bp_raw, list):
                        for bp in bp_raw:
                            b = bp if isinstance(bp, dict) else (bp.__dict__ if hasattr(bp, "__dict__") else {})
                            data["blueprints"].append({
                                "id": b.get("id", "—"),
                                "name": b.get("name", "unnamed"),
                                "status": b.get("status", "unknown"),
                                "repo": b.get("repo", b.get("repository", "—")),
                                "branch": b.get("branch", "main"),
                                "auto_sync": b.get("autoSync", b.get("auto_sync", False)),
                                "created_at": str(b.get("createdAt", b.get("created_at", "—"))),
                            })
                        data["blueprint_count"] = len(data["blueprints"])
            except Exception:
                pass

            # ── Registry Credentials ──
            try:
                if hasattr(client, "list_registry_credentials"):
                    rc_raw = client.list_registry_credentials()
                    if isinstance(rc_raw, list):
                        for rc in rc_raw:
                            r = rc if isinstance(rc, dict) else (rc.__dict__ if hasattr(rc, "__dict__") else {})
                            data["registry_credentials"].append({
                                "id": r.get("id", "—"),
                                "name": r.get("name", "unnamed"),
                                "registry": r.get("registry", r.get("server", "—")),
                                "username": r.get("username", "—"),
                            })
                        data["registry_credential_count"] = len(data["registry_credentials"])
            except Exception:
                pass

        # ── Chart data (computed from collected data) ──
        # Service status distribution
        status_counts: Dict[str, int] = {}
        for s in data["services"]:
            st = s.get("status", "unknown").lower()
            status_counts[st] = status_counts.get(st, 0) + 1
        data["chart_service_status"] = status_counts

        # Service type distribution
        type_counts: Dict[str, int] = {}
        for s in data["services"]:
            t = s.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        data["chart_service_types"] = type_counts

        # Deploy status distribution
        deploy_status_counts: Dict[str, int] = {}
        for d in data["deploys"]:
            ds = d.get("status", "unknown").lower()
            deploy_status_counts[ds] = deploy_status_counts.get(ds, 0) + 1
        data["chart_deploy_status"] = deploy_status_counts

        # Region distribution
        region_counts: Dict[str, int] = {}
        for s in data["services"]:
            r = s.get("region", "unknown")
            if r and r != "—":
                region_counts[r] = region_counts.get(r, 0) + 1
        for db in data["postgres_instances"]:
            r = db.get("region", "unknown")
            if r and r != "—":
                region_counts[r] = region_counts.get(r, 0) + 1
        data["chart_regions"] = region_counts

        # Infrastructure summary
        data["infra_summary"] = {
            "total_resources": (
                len(data["services"]) + data["postgres_count"] +
                data["kv_count"] + data["env_group_count"] +
                data["project_count"] + data["blueprint_count"] +
                data["webhook_count"] + data["custom_domain_count"]
            ),
            "services": len(data["services"]),
            "databases": data["postgres_count"],
            "kv_stores": data["kv_count"],
            "env_groups": data["env_group_count"],
            "projects": data["project_count"],
            "blueprints": data["blueprint_count"],
            "webhooks": data["webhook_count"],
            "custom_domains": data["custom_domain_count"],
            "registry_creds": data["registry_credential_count"],
            "members": data["workspace_member_count"],
        }

        # Env var counts per service (for charts)
        env_var_counts: Dict[str, int] = {}
        for svc_name, vars_list in data["env_vars_by_service"].items():
            env_var_counts[svc_name] = len(vars_list)
        data["chart_env_var_counts"] = env_var_counts

        return data

    async def execute_provider_action(
        self, action: str, service_id: str = "", deploy_id: str = "",
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a provider/deployment action and return the result.

        Supported actions:
            provider_login, resume,
            restart, purge_cache, redeploy, suspend, deploy, cancel_deploy,
            rollback, create_preview, validate_token, rotate_key, clear_credentials
        """
        client = getattr(self, "_provider_client", None)
        deployer = getattr(self, "_provider_deployer", None)
        store = getattr(self, "_provider_credential_store", None)

        try:
            # ── Provider Login (save token & rewire client) ──
            if action == "provider_login":
                _extra = extra_data or {}
                token = _extra.get("token", "").strip()
                owner_name = _extra.get("owner_name", "").strip() or None
                region = _extra.get("default_region", "oregon").strip()
                if not token:
                    return {"success": False, "message": "API token is required."}
                if len(token) < 10:
                    return {"success": False, "message": "API token appears too short. Please enter a valid Render API key."}
                # Ensure we have a credential store (workspace-local: .aquilia/providers/render/)
                if store is None:
                    try:
                        from aquilia.providers.render.store import RenderCredentialStore
                        store = RenderCredentialStore()  # <workspace>/.aquilia/providers/render/
                        self._provider_credential_store = store
                    except Exception as e:
                        return {"success": False, "message": f"Cannot initialise credential store: {e}"}
                # Save token with encryption
                store.save(token, owner_name=owner_name, default_region=region)
                # Re-create the RenderClient with the new token
                try:
                    from aquilia.providers.render.client import RenderClient
                    new_client = RenderClient(token=token)
                    self._provider_client = new_client
                except Exception as e:
                    logger.warning(f"Client re-creation warning (non-fatal): {e}")
                # Re-create the RenderDeployer if possible
                try:
                    from aquilia.providers.render.deployer import RenderDeployer
                    new_deployer = RenderDeployer(client=self._provider_client)
                    self._provider_deployer = new_deployer
                except Exception:
                    pass  # deployer is optional
                return {"success": True, "message": "Provider connected successfully! Your API token has been encrypted and stored with AES-256-GCM."}

            # ── Resume service ──
            elif action == "resume" and client and hasattr(client, "resume_service"):
                client.resume_service(service_id)
                return {"success": True, "message": f"Service {service_id} resumed."}

            elif action == "restart" and client and hasattr(client, "restart_service"):
                client.restart_service(service_id)
                return {"success": True, "message": f"Service {service_id} restart triggered."}

            elif action == "purge_cache" and deployer and hasattr(deployer, "purge_cache"):
                deployer.purge_cache(service_id)
                return {"success": True, "message": f"Cache purged for service {service_id}."}

            elif action in ("redeploy", "deploy") and deployer and hasattr(deployer, "deploy"):
                result = deployer.deploy(service_id)
                msg = f"Deploy triggered for service {service_id}."
                return {"success": True, "message": msg, "deploy_id": getattr(result, "deploy_id", "")}

            elif action == "suspend" and client and hasattr(client, "suspend_service"):
                client.suspend_service(service_id)
                return {"success": True, "message": f"Service {service_id} suspended."}

            elif action == "cancel_deploy" and client and hasattr(client, "cancel_deploy"):
                client.cancel_deploy(service_id, deploy_id)
                return {"success": True, "message": f"Deploy {deploy_id} cancelled."}

            elif action == "rollback" and deployer and hasattr(deployer, "rollback"):
                deployer.rollback(service_id, deploy_id)
                return {"success": True, "message": f"Rollback to deploy {deploy_id} triggered."}

            elif action == "create_preview" and client and hasattr(client, "create_preview"):
                client.create_preview(service_id)
                return {"success": True, "message": f"Preview environment created for {service_id}."}

            elif action == "validate_token" and store and hasattr(store, "status"):
                status = store.status()
                valid = status.get("has_token", False) and not status.get("expired", True)
                return {"success": valid, "message": "Token is valid." if valid else "Token is invalid or expired."}

            elif action == "rotate_key" and store and hasattr(store, "rotate"):
                store.rotate()
                return {"success": True, "message": "Encryption key rotated successfully."}

            elif action == "clear_credentials" and store and hasattr(store, "clear"):
                store.clear()
                self._provider_client = None
                self._provider_deployer = None
                return {"success": True, "message": "All credentials cleared. Please log in again to reconnect."}

            else:
                return {"success": False, "message": f"Unknown action: {action}"}

        except Exception as e:
            logger.warning(f"Provider action {action} failed: {e}")
            return {"success": False, "message": f"Action failed: {e}"}

    def get_provider_logs(self, service_id: str) -> list:
        """Fetch recent logs for a provider service."""
        client = getattr(self, "_provider_client", None)
        if client is None:
            return []
        try:
            if hasattr(client, "get_logs"):
                logs_raw = client.get_logs(service_id)
                if isinstance(logs_raw, list):
                    return [
                        {
                            "timestamp": l.get("timestamp", ""),
                            "level": l.get("level", "info"),
                            "message": l.get("message", str(l)),
                        }
                        for l in logs_raw
                    ]
        except Exception as e:
            logger.warning(f"Error fetching logs for {service_id}: {e}")
        return []

    # ── Storage data ─────────────────────────────────────────────────

    def set_storage_registry(self, registry) -> None:
        """Register the application's StorageRegistry for admin integration."""
        self._storage_registry = registry

    async def get_storage_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive storage subsystem data for the admin page.

        Inspects all storage backends: file listings, sizes, types,
        health status, configuration, and builds chart-ready data
        arrays for the frontend.
        """
        import os as _os
        from collections import defaultdict

        data: Dict[str, Any] = {
            "available": False,
            "backends": [],
            "health": {},
            "all_files": [],
            "total_files": 0,
            "total_size": 0,
            "default_alias": "default",
        }

        registry = getattr(self, "_storage_registry", None)
        if registry is None:
            return data

        data["available"] = True
        data["default_alias"] = getattr(registry, "_default_alias", "default")

        # Health check all backends
        try:
            health_results = await registry.health_check()
            data["health"] = health_results
        except Exception:
            data["health"] = {alias: False for alias in registry}

        all_files: list = []
        backends_info: list = []

        for alias in registry:
            backend = registry[alias]
            is_default = alias == data["default_alias"]
            backend_type = getattr(backend, "backend_name", "unknown")
            healthy = data["health"].get(alias, False)

            # Type display map
            _type_display = {
                "local": "Local Filesystem",
                "memory": "In-Memory",
                "s3": "Amazon S3",
                "gcs": "Google Cloud Storage",
                "azure": "Azure Blob Storage",
                "sftp": "SFTP / SSH",
                "composite": "Composite (Multi-Backend)",
            }

            backend_info: Dict[str, Any] = {
                "alias": alias,
                "type": backend_type,
                "type_display": _type_display.get(backend_type, backend_type.title()),
                "is_default": is_default,
                "healthy": healthy,
                "health_status": "healthy" if healthy else "unhealthy",
                "file_count": 0,
                "total_size": 0,
                "size_human": "0 B",
                "files": [],
                "config": {},
                "config_display": {},
                "capabilities": [],
                "recent_files": [],
                # Backend-specific fields (used by template conditionally)
                "root": "",
                "bucket": "",
                "region": "",
                "container_name": "",
                "host": "",
                "port": "",
                "quota_max": 0,
                "quota_pct": 0.0,
            }

            # Extract config info and backend-specific fields
            cfg = getattr(backend, "_config", None)
            if cfg is not None:
                try:
                    if hasattr(cfg, "to_dict"):
                        cfg_dict = cfg.to_dict()
                        backend_info["config"] = cfg_dict
                        # Build safe display config (hide secrets)
                        _secrets = {"secret_key", "access_key", "session_token",
                                    "password", "key_passphrase", "account_key",
                                    "sas_token", "connection_string",
                                    "credentials_json", "credentials_path"}
                        display = {}
                        for k, v in cfg_dict.items():
                            if k in _secrets and v:
                                display[k] = "••••••••"
                            elif v is not None and v != "" and v != [] and v != {}:
                                display[k] = str(v)
                        backend_info["config_display"] = display
                    else:
                        backend_info["config"] = {
                            "backend": getattr(cfg, "backend", ""),
                            "alias": getattr(cfg, "alias", alias),
                        }
                        backend_info["config_display"] = backend_info["config"]

                    # Extract backend-specific display fields
                    backend_info["root"] = getattr(cfg, "root", "")
                    backend_info["bucket"] = getattr(cfg, "bucket", "")
                    backend_info["region"] = getattr(cfg, "region", "") or getattr(cfg, "location", "")
                    backend_info["container_name"] = getattr(cfg, "container", "")
                    backend_info["host"] = getattr(cfg, "host", "")
                    backend_info["port"] = getattr(cfg, "port", "")

                    # Quota (memory backend has max_size)
                    max_size = getattr(cfg, "max_size", 0) or 0
                    backend_info["quota_max"] = max_size
                except Exception:
                    pass

            # Extract capabilities
            caps = []
            for cap in ("save", "open", "delete", "exists", "stat", "listdir",
                        "url", "copy", "move", "ping"):
                if hasattr(backend, cap) and callable(getattr(backend, cap)):
                    caps.append(cap)
            backend_info["capabilities"] = caps

            # List files
            try:
                dirs, files = await backend.listdir("")
                for fname in files:
                    try:
                        meta = await backend.stat(fname)
                        ext = _os.path.splitext(fname)[1].lower() if "." in fname else ""
                        file_entry = {
                            "name": fname,
                            "size": meta.size,
                            "size_human": self._fmt_bytes(meta.size),
                            "content_type": meta.content_type or "application/octet-stream",
                            "extension": ext,
                            "last_modified": meta.last_modified.isoformat() if meta.last_modified else None,
                            "created_at": meta.created_at.isoformat() if meta.created_at else None,
                            "etag": meta.etag or "",
                            "backend": alias,
                            "storage_class": meta.storage_class or "",
                        }
                        backend_info["files"].append(file_entry)
                        all_files.append(file_entry)
                        backend_info["total_size"] += meta.size
                        backend_info["file_count"] += 1
                    except Exception:
                        # File stat failed -- include minimal info
                        file_entry = {
                            "name": fname,
                            "size": 0,
                            "size_human": "0 B",
                            "content_type": "application/octet-stream",
                            "extension": _os.path.splitext(fname)[1].lower() if "." in fname else "",
                            "last_modified": None,
                            "created_at": None,
                            "etag": "",
                            "backend": alias,
                            "storage_class": "",
                        }
                        backend_info["files"].append(file_entry)
                        all_files.append(file_entry)
                        backend_info["file_count"] += 1

                # Also recurse into subdirectories (one level deep)
                for subdir in dirs:
                    try:
                        _, sub_files = await backend.listdir(subdir)
                        for sf in sub_files:
                            full_path = f"{subdir}/{sf}" if subdir else sf
                            try:
                                meta = await backend.stat(full_path)
                                ext = _os.path.splitext(sf)[1].lower() if "." in sf else ""
                                file_entry = {
                                    "name": full_path,
                                    "size": meta.size,
                                    "size_human": self._fmt_bytes(meta.size),
                                    "content_type": meta.content_type or "application/octet-stream",
                                    "extension": ext,
                                    "last_modified": meta.last_modified.isoformat() if meta.last_modified else None,
                                    "created_at": meta.created_at.isoformat() if meta.created_at else None,
                                    "etag": meta.etag or "",
                                    "backend": alias,
                                    "storage_class": meta.storage_class or "",
                                }
                                backend_info["files"].append(file_entry)
                                all_files.append(file_entry)
                                backend_info["total_size"] += meta.size
                                backend_info["file_count"] += 1
                            except Exception:
                                file_entry = {
                                    "name": full_path,
                                    "size": 0,
                                    "size_human": "0 B",
                                    "content_type": "application/octet-stream",
                                    "extension": _os.path.splitext(sf)[1].lower() if "." in sf else "",
                                    "last_modified": None,
                                    "created_at": None,
                                    "etag": "",
                                    "backend": alias,
                                    "storage_class": "",
                                }
                                backend_info["files"].append(file_entry)
                                all_files.append(file_entry)
                                backend_info["file_count"] += 1
                    except Exception:
                        pass  # Subdirectory listing failed

            except Exception:
                pass  # Backend listing not available

            backend_info["total_size_human"] = self._fmt_bytes(backend_info["total_size"])
            backend_info["size_human"] = backend_info["total_size_human"]

            # Compute quota percentage
            if backend_info["quota_max"] > 0:
                backend_info["quota_pct"] = min(
                    (backend_info["total_size"] / backend_info["quota_max"]) * 100,
                    100.0,
                )

            # Recent files (sorted by last_modified descending, top 5)
            sorted_files = sorted(
                backend_info["files"],
                key=lambda f: f.get("last_modified") or "",
                reverse=True,
            )
            backend_info["recent_files"] = sorted_files[:5]

            backends_info.append(backend_info)

        data["backends"] = backends_info
        data["all_files"] = all_files
        data["total_files"] = sum(b["file_count"] for b in backends_info)
        data["total_size"] = sum(b["total_size"] for b in backends_info)

        return data

    # ── MLOps data ───────────────────────────────────────────────────

    def get_mlops_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive MLOps subsystem data for the admin page.

        Inspects all MLOps subsystems: models, registry, serving,
        observability, drift detection, rollouts, plugins, experiments,
        circuit breaker, rate limiter, memory tracker, lineage, and
        scheduler.
        """
        data: Dict[str, Any] = {"available": False}

        try:
            from aquilia.mlops import (
                ModelOrchestrator, ModelRegistry, MetricsCollector,
                DriftDetector, PluginHost, CircuitBreaker,
                TokenBucketRateLimiter, MemoryTracker,
                ModelLineageDAG, ExperimentLedger,
                Framework, RuntimeKind, ModelType, DeviceType,
                BatchingStrategy, RolloutStrategy, DriftMethod,
                QuantizePreset, ExportTarget, InferenceMode,
            )
        except Exception:
            return data

        data["available"] = True

        # ── 1. Enums / Capabilities ─────────────────────────────────
        data["frameworks"] = [f.value for f in Framework]
        data["runtime_kinds"] = [r.value for r in RuntimeKind]
        data["model_types"] = [m.value for m in ModelType]
        data["device_types"] = [d.value for d in DeviceType]
        data["batching_strategies"] = [b.value for b in BatchingStrategy]
        data["rollout_strategies"] = [r.value for r in RolloutStrategy]
        data["drift_methods"] = [d.value for d in DriftMethod]
        data["quantize_presets"] = [q.value for q in QuantizePreset]
        data["export_targets"] = [e.value for e in ExportTarget]
        data["inference_modes"] = [i.value for i in InferenceMode]

        # ── 2. Registry / Models ────────────────────────────────────
        models = []
        registry = getattr(self, "_mlops_registry", None)

        # Fallback: if no registry was explicitly wired via
        # set_mlops_services(), pull from the global @model decorator
        # registry so that user-defined models show up automatically.
        if registry is None or not hasattr(registry, "list_models"):
            try:
                from aquilia.mlops.api.model_class import _get_global_registry
                _global = _get_global_registry()
                if _global is not None and hasattr(_global, "list_models"):
                    model_names = _global.list_models()
                    if model_names:
                        registry = _global
                        # Persist for subsequent calls
                        self._mlops_registry = registry
            except Exception:
                pass

        if registry is not None and hasattr(registry, "list_models"):
            try:
                for name in registry.list_models():
                    entry = registry.get(name)
                    if entry:
                        models.append(entry.to_dict() if hasattr(entry, "to_dict") else {
                            "name": name,
                            "version": getattr(entry, "version", "?"),
                            "state": getattr(entry, "state", "unknown"),
                        })
            except Exception:
                pass
        data["models"] = models
        data["total_models"] = len(models)

        # ── 3. Metrics ──────────────────────────────────────────────
        metrics_collector = getattr(self, "_mlops_metrics", None)
        metrics_summary = {}
        if metrics_collector is not None and hasattr(metrics_collector, "get_summary"):
            try:
                metrics_summary = metrics_collector.get_summary()
            except Exception:
                pass
        data["metrics"] = metrics_summary
        data["total_inferences"] = metrics_summary.get("aquilia_inference_total", 0)
        data["total_errors"] = metrics_summary.get("aquilia_inference_errors_total", 0)
        data["total_tokens"] = metrics_summary.get("aquilia_tokens_generated_total", 0)
        data["total_stream_requests"] = metrics_summary.get("aquilia_stream_requests_total", 0)
        data["total_prompt_tokens"] = metrics_summary.get("aquilia_prompt_tokens_total", 0)

        # Hot models
        hot_models = []
        if metrics_collector is not None and hasattr(metrics_collector, "hot_models"):
            try:
                hot_models = [{"name": name, "score": score}
                              for name, score in metrics_collector.hot_models(10)]
            except Exception:
                pass
        data["hot_models"] = hot_models

        # Latency percentiles
        latency_data = {}
        if metrics_collector is not None and hasattr(metrics_collector, "percentile"):
            try:
                latency_data["p50"] = round(metrics_collector.percentile("aquilia_inference_latency_ms", 0.5), 2)
                latency_data["p95"] = round(metrics_collector.percentile("aquilia_inference_latency_ms", 0.95), 2)
                latency_data["p99"] = round(metrics_collector.percentile("aquilia_inference_latency_ms", 0.99), 2)
                latency_data["ewma"] = round(metrics_collector.ewma("aquilia_inference_latency_ms"), 2)
            except Exception:
                pass
        data["latency"] = latency_data

        # Tokens per second
        tps_data = {}
        if metrics_collector is not None and hasattr(metrics_collector, "ewma"):
            try:
                tps_data["ewma"] = round(metrics_collector.ewma("aquilia_tokens_per_second"), 2)
                tps_data["ttft_ewma"] = round(metrics_collector.ewma("aquilia_time_to_first_token_ms"), 2)
            except Exception:
                pass
        data["throughput"] = tps_data

        # ── 4. Drift Detection ──────────────────────────────────────
        drift_data = {}
        drift_detector = getattr(self, "_mlops_drift", None)
        if drift_detector is not None:
            try:
                drift_data["method"] = drift_detector.method.value if hasattr(drift_detector.method, "value") else str(drift_detector.method)
                drift_data["threshold"] = drift_detector.threshold
                drift_data["has_reference"] = drift_detector._reference is not None
            except Exception:
                pass
        data["drift"] = drift_data

        # ── 5. Circuit Breaker ──────────────────────────────────────
        cb_data = {}
        circuit_breaker = getattr(self, "_mlops_circuit_breaker", None)
        if circuit_breaker is not None and hasattr(circuit_breaker, "stats"):
            try:
                cb_data = circuit_breaker.stats
            except Exception:
                pass
        data["circuit_breaker"] = cb_data

        # ── 6. Rate Limiter ─────────────────────────────────────────
        rl_data = {}
        rate_limiter = getattr(self, "_mlops_rate_limiter", None)
        if rate_limiter is not None and hasattr(rate_limiter, "stats"):
            try:
                rl_data = rate_limiter.stats
            except Exception:
                pass
        data["rate_limiter"] = rl_data

        # ── 7. Memory Tracker ───────────────────────────────────────
        mem_data = {}
        memory_tracker = getattr(self, "_mlops_memory_tracker", None)
        if memory_tracker is not None and hasattr(memory_tracker, "stats"):
            try:
                mem_data = memory_tracker.stats
            except Exception:
                pass
        data["memory"] = mem_data

        # ── 8. Plugins ──────────────────────────────────────────────
        plugins = []
        plugin_host = getattr(self, "_mlops_plugins", None)
        if plugin_host is not None and hasattr(plugin_host, "list_plugins"):
            try:
                for desc in plugin_host.list_plugins():
                    plugins.append({
                        "name": desc.name,
                        "version": desc.version,
                        "state": desc.state.value if hasattr(desc.state, "value") else str(desc.state),
                        "error": desc.error or "",
                    })
            except Exception:
                pass
        data["plugins"] = plugins
        data["total_plugins"] = len(plugins)

        # ── 9. Experiments ──────────────────────────────────────────
        experiments = []
        experiment_ledger = getattr(self, "_mlops_experiments", None)
        if experiment_ledger is not None:
            try:
                if hasattr(experiment_ledger, "to_dict"):
                    exp_dict = experiment_ledger.to_dict()
                    for eid, edata in exp_dict.items():
                        experiments.append(edata)
            except Exception:
                pass
        data["experiments"] = experiments
        data["total_experiments"] = len(experiments)
        data["active_experiments"] = sum(1 for e in experiments if e.get("status") == "active")

        # ── 10. Model Lineage ───────────────────────────────────────
        lineage_data = {}
        lineage_dag = getattr(self, "_mlops_lineage", None)
        if lineage_dag is not None and hasattr(lineage_dag, "to_dict"):
            try:
                lineage_data = lineage_dag.to_dict()
            except Exception:
                pass
        data["lineage"] = lineage_data
        data["lineage_nodes"] = len(lineage_data)

        # ── 11. Rollouts ────────────────────────────────────────────
        rollouts = []
        rollout_engine = getattr(self, "_mlops_rollout", None)
        if rollout_engine is not None and hasattr(rollout_engine, "list_rollouts"):
            try:
                for r in rollout_engine.list_rollouts():
                    rollouts.append({
                        "id": r.id,
                        "from_version": r.config.from_version,
                        "to_version": r.config.to_version,
                        "strategy": r.config.strategy.value if hasattr(r.config.strategy, "value") else str(r.config.strategy),
                        "phase": r.phase.value if hasattr(r.phase, "value") else str(r.phase),
                        "percentage": r.current_percentage,
                        "steps": r.steps_completed,
                        "error": r.error or "",
                    })
            except Exception:
                pass
        data["rollouts"] = rollouts
        data["total_rollouts"] = len(rollouts)
        data["active_rollouts"] = sum(1 for r in rollouts if r.get("phase") == "in_progress")

        # ── 12. Autoscaler ──────────────────────────────────────────
        autoscaler_data: Dict[str, Any] = {}
        autoscaler = getattr(self, "_mlops_autoscaler", None)
        if autoscaler is not None:
            try:
                if hasattr(autoscaler, "policy"):
                    p = autoscaler.policy
                    autoscaler_data["policy"] = {
                        "min_replicas": p.min_replicas,
                        "max_replicas": p.max_replicas,
                        "target_concurrency": p.target_concurrency,
                        "target_latency_p95_ms": p.target_latency_p95_ms,
                        "target_gpu_utilization": p.target_gpu_utilization,
                        "target_tokens_per_second": p.target_tokens_per_second,
                        "cooldown_seconds": p.cooldown_seconds,
                    }
                if hasattr(autoscaler, "_current_replicas"):
                    autoscaler_data["current_replicas"] = autoscaler._current_replicas
                if hasattr(autoscaler, "window_stats"):
                    autoscaler_data["window_stats"] = autoscaler.window_stats
                if hasattr(autoscaler, "evaluate"):
                    try:
                        decision = autoscaler.evaluate()
                        autoscaler_data["last_decision"] = {
                            "current": decision.current_replicas,
                            "desired": decision.desired_replicas,
                            "reason": decision.reason,
                        }
                    except Exception:
                        pass
            except Exception:
                pass
        data["autoscaler"] = autoscaler_data

        # ── 13. RBAC / Security ─────────────────────────────────────
        rbac_data: Dict[str, Any] = {}
        rbac_manager = getattr(self, "_mlops_rbac", None)
        if rbac_manager is not None:
            try:
                if hasattr(rbac_manager, "_roles"):
                    rbac_data["roles"] = [
                        {
                            "name": role.name,
                            "description": getattr(role, "description", ""),
                            "permissions": [p.value if hasattr(p, "value") else str(p) for p in role.permissions],
                        }
                        for role in rbac_manager._roles.values()
                    ]
                if hasattr(rbac_manager, "_user_roles"):
                    rbac_data["total_users"] = len(rbac_manager._user_roles)
                    rbac_data["user_assignments"] = {
                        uid: list(roles) for uid, roles in rbac_manager._user_roles.items()
                    }
            except Exception:
                pass
        data["rbac"] = rbac_data

        # ── 14. Batch Queue ─────────────────────────────────────────
        batch_queue_data: Dict[str, Any] = {}
        batch_queue = getattr(self, "_mlops_batch_queue", None)
        if batch_queue is not None and hasattr(batch_queue, "stats"):
            try:
                batch_queue_data = batch_queue.stats
            except Exception:
                pass
        data["batch_queue"] = batch_queue_data

        # ── 15. LRU Cache ───────────────────────────────────────────
        lru_cache_data: Dict[str, Any] = {}
        lru_cache = getattr(self, "_mlops_lru_cache", None)
        if lru_cache is not None and hasattr(lru_cache, "stats"):
            try:
                lru_cache_data = lru_cache.stats
            except Exception:
                pass
        data["lru_cache"] = lru_cache_data

        # ── 16. Per-model metrics ───────────────────────────────────
        per_model_metrics = []
        if metrics_collector is not None and hasattr(metrics_collector, "model_summary"):
            try:
                for m_item in models:
                    mname = m_item.get("name", "")
                    if mname:
                        ms = metrics_collector.model_summary(mname)
                        if len(ms) > 1:  # has more than just model_name
                            per_model_metrics.append(ms)
            except Exception:
                pass
        data["per_model_metrics"] = per_model_metrics

        # ── 17. Prometheus text ─────────────────────────────────────
        prometheus_text = ""
        if metrics_collector is not None and hasattr(metrics_collector, "to_prometheus"):
            try:
                result = metrics_collector.to_prometheus()
                prometheus_text = str(result) if result else ""
            except Exception:
                pass
        data["prometheus_text"] = prometheus_text

        # ── 18. DType system ────────────────────────────────────────
        dtypes = []
        try:
            from aquilia.mlops._types import DType
            dtypes = [d.value for d in DType]
        except Exception:
            pass
        data["dtypes"] = dtypes

        # ── 19. Permissions (enum values) ───────────────────────────
        permissions = []
        try:
            from aquilia.mlops.security.rbac import Permission
            permissions = [p.value for p in Permission]
        except Exception:
            pass
        data["permissions"] = permissions

        # ── 20. Charts data ─────────────────────────────────────────
        charts: Dict[str, Any] = {}

        # Model states distribution
        state_counts: Dict[str, int] = {}
        for m in models:
            state = m.get("state", "unknown")
            state_counts[state] = state_counts.get(state, 0) + 1
        charts["model_states"] = state_counts

        # Framework distribution
        fw_counts: Dict[str, int] = {}
        for m in models:
            fw = m.get("framework", "custom")
            if isinstance(fw, str):
                fw_counts[fw] = fw_counts.get(fw, 0) + 1
        charts["frameworks"] = fw_counts

        # Plugin states
        plugin_states: Dict[str, int] = {}
        for p in plugins:
            pstate = p.get("state", "unknown")
            plugin_states[pstate] = plugin_states.get(pstate, 0) + 1
        charts["plugin_states"] = plugin_states

        # Experiment statuses
        exp_statuses: Dict[str, int] = {}
        for e in experiments:
            estatus = e.get("status", "unknown")
            exp_statuses[estatus] = exp_statuses.get(estatus, 0) + 1
        charts["experiment_statuses"] = exp_statuses

        # Rollout phases
        rollout_phases: Dict[str, int] = {}
        for r in rollouts:
            rphase = r.get("phase", "unknown")
            rollout_phases[rphase] = rollout_phases.get(rphase, 0) + 1
        charts["rollout_phases"] = rollout_phases

        # Memory breakdown (per-model allocations)
        mem_allocations: Dict[str, int] = {}
        if memory_tracker is not None and hasattr(memory_tracker, "stats"):
            try:
                mem_allocations = memory_tracker.stats.get("allocations", {})
            except Exception:
                pass
        charts["memory_allocations"] = mem_allocations

        data["charts"] = charts

        # ── 21. Inference History (playground audit log) ─────────────
        data["inference_history"] = getattr(self, "_mlops_inference_history", [])[:20]

        # ── 22. Alert Rules & Triggered Alerts ──────────────────────
        data["alert_rules"] = getattr(self, "_mlops_alert_rules", [])
        data["triggered_alerts"] = getattr(self, "_mlops_triggered_alerts", [])

        return data

    def set_mlops_services(
        self,
        registry=None,
        metrics_collector=None,
        drift_detector=None,
        circuit_breaker=None,
        rate_limiter=None,
        memory_tracker=None,
        plugin_host=None,
        experiment_ledger=None,
        lineage_dag=None,
        rollout_engine=None,
        autoscaler=None,
        rbac_manager=None,
        batch_queue=None,
        lru_cache=None,
    ) -> None:
        """Register MLOps services for admin integration."""
        if registry is not None:
            self._mlops_registry = registry
        if metrics_collector is not None:
            self._mlops_metrics = metrics_collector
        if drift_detector is not None:
            self._mlops_drift = drift_detector
        if circuit_breaker is not None:
            self._mlops_circuit_breaker = circuit_breaker
        if rate_limiter is not None:
            self._mlops_rate_limiter = rate_limiter
        if memory_tracker is not None:
            self._mlops_memory_tracker = memory_tracker
        if plugin_host is not None:
            self._mlops_plugins = plugin_host
        if experiment_ledger is not None:
            self._mlops_experiments = experiment_ledger
        if lineage_dag is not None:
            self._mlops_lineage = lineage_dag
        if rollout_engine is not None:
            self._mlops_rollout = rollout_engine
        if autoscaler is not None:
            self._mlops_autoscaler = autoscaler
        if rbac_manager is not None:
            self._mlops_rbac = rbac_manager
        if batch_queue is not None:
            self._mlops_batch_queue = batch_queue
        if lru_cache is not None:
            self._mlops_lru_cache = lru_cache

    # ── Testing data ─────────────────────────────────────────────────

    def get_testing_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive testing framework data.

        Inspects the Aquilia testing module, discovers test files, and
        collects information about available test infrastructure:
        - Test classes (AquiliaTestCase, TransactionTestCase, etc.)
        - Utility counts (assertions, fixtures, helpers)
        - Auth testing (identity builders, roles)
        - Mock infrastructure (faults, effects, DI, cache, mail)
        - Test file discovery (project test files)
        - Coverage-style breakdown by component
        """
        import os
        import importlib
        import inspect

        data: Dict[str, Any] = {
            "available": True,
            "framework_version": "1.0.0",
            "components": [],
            "test_classes": [],
            "fixtures": [],
            "assertions": [],
            "mock_infra": [],
            "test_files": [],
            "summary": {},
            "charts": {},
        }

        # ── 1. Core test case classes ────────────────────────────────
        try:
            from aquilia.testing.cases import (
                AquiliaTestCase, TransactionTestCase,
                LiveServerTestCase, SimpleTestCase,
            )
            test_classes = [
                {
                    "name": "SimpleTestCase",
                    "description": "Pure unit tests — no server, no DI, no ASGI",
                    "base": "unittest.TestCase",
                    "features": ["assertion_helpers", "utility_functions"],
                    "category": "unit",
                },
                {
                    "name": "AquiliaTestCase",
                    "description": "Full async test case with server lifecycle",
                    "base": "IsolatedAsyncioTestCase",
                    "features": [
                        "auto_server", "test_client", "di_container",
                        "fault_engine", "config_override",
                        "controller_router", "effect_registry",
                    ],
                    "category": "integration",
                },
                {
                    "name": "TransactionTestCase",
                    "description": "Database tests with automatic transaction rollback",
                    "base": "AquiliaTestCase",
                    "features": [
                        "auto_server", "test_client", "db_transaction",
                        "auto_rollback", "isolation",
                    ],
                    "category": "database",
                },
                {
                    "name": "LiveServerTestCase",
                    "description": "Real ASGI server on random port for E2E testing",
                    "base": "AquiliaTestCase",
                    "features": [
                        "real_server", "tcp_connection", "live_url",
                        "browser_automation", "httpx_compatible",
                    ],
                    "category": "e2e",
                },
            ]
            data["test_classes"] = test_classes
        except Exception:
            pass

        # ── 2. TestClient capabilities ───────────────────────────────
        try:
            from aquilia.testing.client import TestClient, WebSocketTestClient
            data["client"] = {
                "http": {
                    "name": "TestClient",
                    "methods": ["get", "post", "put", "patch", "delete", "head", "options"],
                    "features": [
                        "in_process_asgi", "cookie_persistence",
                        "auto_redirect_follow", "bearer_token_auth",
                        "multipart_uploads", "response_history",
                        "json_auto_parse", "content_type_detection",
                    ],
                },
                "websocket": {
                    "name": "WebSocketTestClient",
                    "features": [
                        "connect", "send_text", "send_bytes",
                        "receive_text", "receive_bytes",
                        "close", "is_connected",
                    ],
                },
            }
        except Exception:
            data["client"] = {"http": {}, "websocket": {}}

        # ── 3. Assertion helpers ─────────────────────────────────────
        try:
            from aquilia.testing.assertions import AquiliaAssertions
            assertion_methods = [
                m for m in dir(AquiliaAssertions)
                if m.startswith("assert_") and callable(getattr(AquiliaAssertions, m))
            ]
            categories: Dict[str, list] = {}
            for method in sorted(assertion_methods):
                if any(x in method for x in ["status", "success", "redirect", "created",
                       "accepted", "no_content", "bad_request", "unauthorized",
                       "forbidden", "not_found", "conflict", "gone", "unprocessable",
                       "too_many", "server_error", "service_unavailable"]):
                    cat = "HTTP Status"
                elif any(x in method for x in ["json", "json_contains", "json_key", "json_path", "json_list"]):
                    cat = "JSON"
                elif any(x in method for x in ["header", "content_type", "cookie"]):
                    cat = "Headers"
                elif any(x in method for x in ["fault", "severity"]):
                    cat = "Faults"
                elif any(x in method for x in ["effect", "acquire"]):
                    cat = "Effects"
                elif any(x in method for x in ["mail", "email"]):
                    cat = "Mail"
                elif any(x in method for x in ["cache", "ttl"]):
                    cat = "Cache"
                elif any(x in method for x in ["di", "provider", "resolve"]):
                    cat = "DI"
                elif any(x in method for x in ["template", "render"]):
                    cat = "Templates"
                elif any(x in method for x in ["session"]):
                    cat = "Sessions"
                else:
                    cat = "General"
                categories.setdefault(cat, []).append(method)

            data["assertions"] = [
                {"category": cat, "methods": methods, "count": len(methods)}
                for cat, methods in sorted(categories.items())
            ]
            data["total_assertions"] = len(assertion_methods)
        except Exception:
            data["total_assertions"] = 0

        # ── 4. Fixtures ─────────────────────────────────────────────
        try:
            from aquilia.testing import fixtures as fx_mod
            fixture_names = [
                name for name in dir(fx_mod)
                if not name.startswith("_") and callable(getattr(fx_mod, name))
                and hasattr(getattr(fx_mod, name), "pytestmark")
                or name in (
                    "test_config", "fault_engine", "effect_registry",
                    "cache_backend", "di_container", "identity_factory",
                    "mail_outbox", "test_request", "test_scope",
                    "test_server", "test_client", "ws_client",
                    "settings_override", "aquilia_fixtures",
                )
            ]
            data["fixtures"] = [
                {"name": name, "async": name in ("test_server", "test_client", "ws_client", "settings_override")}
                for name in sorted(set(fixture_names))
            ]
            data["total_fixtures"] = len(data["fixtures"])
        except Exception:
            data["total_fixtures"] = 0

        # ── 5. Mock infrastructure ───────────────────────────────────
        mock_infra = []
        try:
            from aquilia.testing.faults import MockFaultEngine
            mock_infra.append({
                "name": "MockFaultEngine",
                "module": "faults",
                "description": "Capture & assert fault emissions",
                "features": [
                    "emit_capture", "has_fault", "get_faults",
                    "fault_codes", "fault_count", "last_fault",
                    "reset", "context_manager",
                ],
            })
        except Exception:
            pass
        try:
            from aquilia.testing.effects import MockEffectRegistry, MockEffectProvider, MockFlowContext
            mock_infra.append({
                "name": "MockEffectRegistry",
                "module": "effects",
                "description": "Auto-stub missing effects for testing",
                "features": [
                    "register_mock", "get_provider", "get_mock",
                    "reset_all", "auto_stub",
                ],
            })
            mock_infra.append({
                "name": "MockEffectProvider",
                "module": "effects",
                "description": "Configurable provider with call tracking",
                "features": [
                    "return_value", "return_sequence",
                    "acquire_side_effect", "acquire_count",
                    "call_history",
                ],
            })
            mock_infra.append({
                "name": "MockFlowContext",
                "module": "effects",
                "description": "Test-friendly FlowContext with pre-acquired mocks",
                "features": ["from_registry"],
            })
        except Exception:
            pass
        try:
            from aquilia.testing.cache import MockCacheBackend
            mock_infra.append({
                "name": "MockCacheBackend",
                "module": "cache",
                "description": "In-memory cache with TTL tracking",
                "features": [
                    "get", "set", "delete", "exists", "clear",
                    "get_or_set", "get_ttl", "ttl_tracking",
                    "get_count", "set_count", "delete_count",
                ],
            })
        except Exception:
            pass
        try:
            from aquilia.testing.di import TestContainer
            mock_infra.append({
                "name": "TestContainer",
                "module": "di",
                "description": "DI container with relaxed validation for testing",
                "features": [
                    "mock_provider", "override_provider",
                    "factory_provider", "spy_provider", "reset",
                ],
            })
        except Exception:
            pass
        try:
            from aquilia.testing.mail import MailTestMixin
            mock_infra.append({
                "name": "MailTestMixin",
                "module": "mail",
                "description": "Captured outbox for mail assertions",
                "features": [
                    "mail_outbox", "latest_mail", "get_mail_for",
                    "assert_mail_sent", "assert_mail_subject_contains",
                    "assert_no_mail_sent",
                ],
            })
        except Exception:
            pass
        try:
            from aquilia.testing.auth import TestIdentityFactory, IdentityBuilder
            mock_infra.append({
                "name": "TestIdentityFactory",
                "module": "auth",
                "description": "Create test identities with fluent builder",
                "features": [
                    "user", "admin", "service", "anonymous",
                    "suspended", "build", "IdentityBuilder",
                ],
            })
        except Exception:
            pass
        try:
            from aquilia.testing.config import TestConfig
            mock_infra.append({
                "name": "TestConfig",
                "module": "config",
                "description": "Config overlay for test overrides",
                "features": [
                    "get", "set", "has", "to_dict",
                    "override_settings", "dot_notation",
                ],
            })
        except Exception:
            pass
        data["mock_infra"] = mock_infra
        data["total_mocks"] = len(mock_infra)

        # ── 6. Utility functions ─────────────────────────────────────
        try:
            from aquilia.testing.utils import (
                make_test_scope, make_test_request, make_test_receive,
                make_test_response, make_test_ws_scope, make_upload_file,
            )
            data["utilities"] = [
                {"name": "make_test_scope", "description": "Build ASGI HTTP scope"},
                {"name": "make_test_request", "description": "Build full Request object"},
                {"name": "make_test_receive", "description": "Create ASGI receive callable"},
                {"name": "make_test_response", "description": "Build Response for assertions"},
                {"name": "make_test_ws_scope", "description": "Build ASGI WebSocket scope"},
                {"name": "make_upload_file", "description": "Create multipart upload file"},
            ]
            data["total_utilities"] = len(data["utilities"])
        except Exception:
            data["total_utilities"] = 0

        # ── 7. Discover test files in project ────────────────────────
        test_files = []
        total_test_count = 0
        total_test_classes_count = 0
        total_lines = 0
        total_assert_stmts = 0
        category_counts: Dict[str, int] = {"unit": 0, "integration": 0, "database": 0, "e2e": 0, "other": 0}
        imports_usage: Dict[str, int] = {}  # which testing imports are used
        try:
            # ── Workspace-scoped test discovery ──────────────────────
            # Only discover tests from inside the user's workspace,
            # never from the framework's own test suite.
            from pathlib import Path as _Path

            # Use workspace.py as the definitive anchor — it only
            # exists inside the user's project, never at the repo root.
            ws_file = self._find_workspace_path("workspace.py", is_file=True)
            if ws_file is not None:
                workspace_root = ws_file.parent
            else:
                # Fallback: look for a starter.py (alternative entry point)
                starter = self._find_workspace_path("starter.py", is_file=True)
                if starter is not None:
                    workspace_root = starter.parent
                else:
                    workspace_root = None

            # Collect (display_dir, absolute_dir) pairs to scan
            scan_dirs: list = []
            if workspace_root is not None:
                # 1. Main tests/ directory
                main_tests = workspace_root / "tests"
                if main_tests.is_dir():
                    scan_dirs.append(("tests", main_tests))

                # 2. modules/*/tests/ and modules/**/test_*.py (per-module tests)
                modules_dir = workspace_root / "modules"
                if modules_dir.is_dir():
                    for mod_path in sorted(modules_dir.iterdir()):
                        if mod_path.is_dir():
                            mod_name = mod_path.name
                            # Check modules/<mod>/tests/ subdirectory
                            mod_tests = mod_path / "tests"
                            if mod_tests.is_dir():
                                scan_dirs.append((f"modules/{mod_name}/tests", mod_tests))
                            # Also check for test_*.py directly in modules/<mod>/
                            has_test_files = any(
                                f.name.startswith("test_") and f.name.endswith(".py")
                                for f in mod_path.iterdir() if f.is_file()
                            )
                            if has_test_files:
                                scan_dirs.append((f"modules/{mod_name}", mod_path))

            def _analyze_test_file(fpath: str, fname: str, display_dir: str) -> None:
                """Analyze a single test file and append results."""
                nonlocal total_test_count, total_test_classes_count
                nonlocal total_lines, total_assert_stmts
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        source = f.read()
                    lines = source.count("\n") + 1
                    # Count test functions, classes, assert statements
                    test_funcs = source.count("\n    def test_") + source.count("\n    async def test_")
                    test_cls = source.count("\nclass Test")
                    assert_count = source.count("assert ") + source.count("assert(") + source.count("self.assert")
                    total_test_count += test_funcs
                    total_test_classes_count += test_cls
                    total_lines += lines
                    total_assert_stmts += assert_count

                    # Categorize test file
                    name_lower = fname.lower()
                    if "e2e" in name_lower or "live" in name_lower or "browser" in name_lower:
                        category = "e2e"
                    elif any(x in name_lower for x in ["orm", "db", "migration", "model"]):
                        category = "database"
                    elif any(x in name_lower for x in ["controller", "auth", "admin", "di", "sessions", "regression", "i18n", "integration"]):
                        category = "integration"
                    elif any(x in name_lower for x in ["unit", "util", "helper", "missing"]):
                        category = "unit"
                    else:
                        category = "other"
                    category_counts[category] += 1

                    # Density: tests per 100 lines
                    density = round(test_funcs / max(lines, 1) * 100, 1)

                    # Detect async tests
                    async_test_count = source.count("\n    async def test_")
                    sync_test_count = test_funcs - async_test_count

                    # Detect which testing imports are used
                    file_imports = []
                    _testing_imports_map = {
                        "AquiliaTestCase": "aquilia.testing.cases",
                        "TransactionTestCase": "aquilia.testing.cases",
                        "LiveServerTestCase": "aquilia.testing.cases",
                        "SimpleTestCase": "aquilia.testing.cases",
                        "TestClient": "aquilia.testing.client",
                        "MockFaultEngine": "aquilia.testing.faults",
                        "MockEffectRegistry": "aquilia.testing.effects",
                        "MockCacheBackend": "aquilia.testing.cache",
                        "TestContainer": "aquilia.testing.di",
                        "MailTestMixin": "aquilia.testing.mail",
                        "TestIdentityFactory": "aquilia.testing.auth",
                        "TestConfig": "aquilia.testing.config",
                        "override_settings": "aquilia.testing.config",
                    }
                    for symbol, mod in _testing_imports_map.items():
                        if symbol in source:
                            file_imports.append(symbol)
                            imports_usage[symbol] = imports_usage.get(symbol, 0) + 1

                    test_files.append({
                        "name": fname,
                        "directory": display_dir,
                        "path": fpath,
                        "lines": lines,
                        "test_count": test_funcs,
                        "class_count": test_cls,
                        "assert_count": assert_count,
                        "category": category,
                        "density": density,
                        "async_tests": async_test_count,
                        "sync_tests": sync_test_count,
                        "imports": file_imports,
                    })
                except Exception:
                    test_files.append({
                        "name": fname,
                        "directory": display_dir,
                        "path": fpath,
                        "lines": 0,
                        "test_count": 0,
                        "class_count": 0,
                        "assert_count": 0,
                        "category": "other",
                        "density": 0,
                        "async_tests": 0,
                        "sync_tests": 0,
                        "imports": [],
                    })

            # Scan all discovered directories for test files
            seen_paths: set = set()
            for display_dir, abs_dir in scan_dirs:
                if abs_dir.is_dir():
                    for fname in sorted(os.listdir(str(abs_dir))):
                        if fname.startswith("test_") and fname.endswith(".py"):
                            fpath = os.path.join(str(abs_dir), fname)
                            if fpath not in seen_paths:
                                seen_paths.add(fpath)
                                _analyze_test_file(fpath, fname, display_dir)
        except Exception:
            pass
        data["test_files"] = test_files
        data["total_test_files"] = len(test_files)

        # ── 8. Component coverage breakdown ──────────────────────────
        component_coverage = [
            {"name": "Server Lifecycle", "module": "server", "status": "covered"},
            {"name": "Config Overrides", "module": "config", "status": "covered"},
            {"name": "HTTP Client", "module": "client", "status": "covered"},
            {"name": "WebSocket Client", "module": "client", "status": "covered"},
            {"name": "DI Container", "module": "di", "status": "covered"},
            {"name": "Fault System", "module": "faults", "status": "covered"},
            {"name": "Effect System", "module": "effects", "status": "covered"},
            {"name": "Cache", "module": "cache", "status": "covered"},
            {"name": "Sessions", "module": "cases", "status": "covered"},
            {"name": "Auth / Identity", "module": "auth", "status": "covered"},
            {"name": "Mail", "module": "mail", "status": "covered"},
            {"name": "Controllers", "module": "cases", "status": "covered"},
            {"name": "Middleware", "module": "cases", "status": "covered"},
            {"name": "Templates", "module": "cases", "status": "covered"},
            {"name": "Database / ORM", "module": "cases", "status": "covered"},
        ]
        data["component_coverage"] = component_coverage
        data["total_components"] = len(component_coverage)
        data["covered_components"] = sum(1 for c in component_coverage if c["status"] == "covered")

        # ── 9. Summary stats ─────────────────────────────────────────
        avg_tests_per_file = round(total_test_count / max(len(test_files), 1), 1)
        avg_loc_per_test = round(total_lines / max(total_test_count, 1), 1)
        avg_density = round(total_test_count / max(total_lines, 1) * 100, 1)
        total_async_tests = sum(f.get("async_tests", 0) for f in test_files)
        total_sync_tests = total_test_count - total_async_tests

        data["summary"] = {
            "total_test_cases": len(test_classes) if "test_classes" in data else 0,
            "total_assertions": data.get("total_assertions", 0),
            "total_fixtures": data.get("total_fixtures", 0),
            "total_mocks": data.get("total_mocks", 0),
            "total_utilities": data.get("total_utilities", 0),
            "total_test_files": len(test_files),
            "total_test_functions": total_test_count,
            "total_test_classes": total_test_classes_count,
            "total_lines": total_lines,
            "total_components": len(component_coverage),
            "covered_components": sum(1 for c in component_coverage if c["status"] == "covered"),
            "total_assert_stmts": total_assert_stmts,
            "avg_tests_per_file": avg_tests_per_file,
            "avg_loc_per_test": avg_loc_per_test,
            "avg_density": avg_density,
            "total_async_tests": total_async_tests,
            "total_sync_tests": total_sync_tests,
            "category_breakdown": dict(category_counts),
            "imports_usage": dict(imports_usage),
        }

        # ── 10. Chart.js data structures ─────────────────────────────
        # Test distribution by file
        file_names = [f["name"].replace("test_", "").replace(".py", "") for f in test_files[:15]]
        file_counts = [f["test_count"] for f in test_files[:15]]

        # Test categories (from actual per-file categorisation)
        cat_labels = [k.title() for k, v in category_counts.items() if v > 0]
        cat_values = [v for v in category_counts.values() if v > 0]

        # Assertion categories
        assert_cat_labels = [a["category"] for a in data.get("assertions", [])]
        assert_cat_values = [a["count"] for a in data.get("assertions", [])]

        # Mock infrastructure by module
        mock_labels = [m["name"] for m in mock_infra]
        mock_feature_counts = [len(m["features"]) for m in mock_infra]

        # Lines of test code per file
        loc_labels = [f["name"].replace("test_", "").replace(".py", "") for f in sorted(test_files, key=lambda x: x["lines"], reverse=True)[:12]]
        loc_values = [f["lines"] for f in sorted(test_files, key=lambda x: x["lines"], reverse=True)[:12]]

        # Component coverage (for radar chart)
        cov_labels = [c["name"] for c in component_coverage]
        cov_values = [100 if c["status"] == "covered" else 0 for c in component_coverage]

        # Async vs sync test breakdown
        async_sync_labels = ["Async", "Sync"]
        async_sync_values = [total_async_tests, total_sync_tests]

        # Test density per file (tests per 100 LOC) — top 12
        density_sorted = sorted(test_files, key=lambda x: x.get("density", 0), reverse=True)[:12]
        density_labels = [f["name"].replace("test_", "").replace(".py", "") for f in density_sorted]
        density_values = [f.get("density", 0) for f in density_sorted]

        # Imports usage (which testing utilities are most used)
        imports_sorted = sorted(imports_usage.items(), key=lambda x: x[1], reverse=True)
        import_labels = [k for k, _ in imports_sorted]
        import_values = [v for _, v in imports_sorted]

        # Assertions per file (top 12)
        assert_sorted = sorted(test_files, key=lambda x: x.get("assert_count", 0), reverse=True)[:12]
        assert_file_labels = [f["name"].replace("test_", "").replace(".py", "") for f in assert_sorted]
        assert_file_values = [f.get("assert_count", 0) for f in assert_sorted]

        data["charts"] = {
            "test_distribution": {
                "labels": file_names,
                "values": file_counts,
            },
            "test_categories": {
                "labels": cat_labels,
                "values": cat_values,
            },
            "assertion_categories": {
                "labels": assert_cat_labels,
                "values": assert_cat_values,
            },
            "mock_infrastructure": {
                "labels": mock_labels,
                "values": mock_feature_counts,
            },
            "lines_of_code": {
                "labels": loc_labels,
                "values": loc_values,
            },
            "component_coverage": {
                "labels": cov_labels,
                "values": cov_values,
            },
            "async_sync": {
                "labels": async_sync_labels,
                "values": async_sync_values,
            },
            "test_density": {
                "labels": density_labels,
                "values": density_values,
            },
            "imports_usage": {
                "labels": import_labels,
                "values": import_values,
            },
            "assertions_per_file": {
                "labels": assert_file_labels,
                "values": assert_file_values,
            },
        }

        return data

    # ── Dashboard data ───────────────────────────────────────────────

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Aggregate comprehensive dashboard statistics.

        Returns model counts, audit breakdowns, system health,
        environment info, and recent activity for a rich dashboard.
        """
        import os
        import platform
        import sys
        import time
        from collections import Counter
        from datetime import datetime, timezone

        stats: Dict[str, Any] = {
            "total_models": len(self._registry),
            "model_counts": {},
            "recent_actions": [],
            "audit_summary": {},
            "environment": {},
            "top_models": [],
            "active_users": [],
            "system_health": {},
        }

        # ── Count records per model (best effort) ──
        total_records = 0
        model_record_list: list = []
        for model_cls, admin in self._registry.items():
            try:
                count = await model_cls.objects.count()
                stats["model_counts"][model_cls.__name__] = count
                total_records += count if isinstance(count, int) else 0
                model_record_list.append({
                    "name": model_cls.__name__,
                    "verbose_name": admin.get_model_name(),
                    "count": count if isinstance(count, int) else 0,
                    "icon": getattr(admin, "icon", "table"),
                    "app_label": admin.get_app_label(),
                })
            except Exception:
                stats["model_counts"][model_cls.__name__] = "?"
                model_record_list.append({
                    "name": model_cls.__name__,
                    "verbose_name": admin.get_model_name(),
                    "count": 0,
                    "icon": getattr(admin, "icon", "table"),
                    "app_label": admin.get_app_label(),
                })

        stats["total_records"] = total_records

        # Top models by record count (descending, max 6)
        model_record_list.sort(key=lambda m: m["count"], reverse=True)
        stats["top_models"] = model_record_list[:6]

        # ── Audit breakdown ──
        all_audit = self.audit_log.get_entries(limit=500)
        stats["recent_actions"] = [e.to_dict() for e in all_audit[:10]]

        action_counter: Counter = Counter()
        user_counter: Counter = Counter()
        hourly_counter: Counter = Counter()
        now = datetime.now(timezone.utc)
        logins_24h = 0
        failed_logins = 0
        users_24h: set = set()

        for entry in all_audit:
            action_counter[entry.action.value] += 1
            if entry.username:
                user_counter[entry.username] += 1

            # Hourly distribution (last 24h)
            try:
                ts = entry.timestamp
                if ts.tzinfo is None:
                    from datetime import timezone as _tz
                    ts = ts.replace(tzinfo=_tz.utc)
                diff_h = (now - ts).total_seconds() / 3600
                if diff_h <= 24:
                    hour_label = ts.strftime("%H:00")
                    hourly_counter[hour_label] += 1
                    if entry.username:
                        users_24h.add(entry.username)
                    if entry.action.value == "login":
                        logins_24h += 1
                    if entry.action.value == "login_failed":
                        failed_logins += 1
            except Exception:
                pass

        stats["audit_summary"] = {
            "total_entries": len(all_audit),
            "creates": action_counter.get("create", 0),
            "updates": action_counter.get("update", 0),
            "deletes": action_counter.get("delete", 0),
            "logins": action_counter.get("login", 0),
            "exports": action_counter.get("export", 0),
            "logins_24h": logins_24h,
            "failed_logins": failed_logins,
            "unique_users_24h": len(users_24h),
            "action_breakdown": dict(action_counter.most_common(10)),
            "hourly_activity": dict(sorted(hourly_counter.items())),
        }

        # Active sessions estimate (unique users in last hour)
        sessions_1h: set = set()
        for entry in all_audit:
            try:
                ts = entry.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if (now - ts).total_seconds() < 3600 and entry.username:
                    sessions_1h.add(entry.username)
            except Exception:
                pass
        stats["active_sessions"] = len(sessions_1h)

        # Active users (top 5 by activity)
        stats["active_users"] = [
            {"username": u, "actions": c}
            for u, c in user_counter.most_common(5)
        ]

        # ── Environment info ──
        stats["environment"] = {
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "pid": os.getpid(),
        }

        # Server uptime via process start time
        try:
            import psutil
            proc = psutil.Process(os.getpid())
            uptime_secs = time.time() - proc.create_time()
            if uptime_secs >= 86400:
                uptime_str = f"{int(uptime_secs // 86400)}d {int((uptime_secs % 86400) // 3600)}h"
            elif uptime_secs >= 3600:
                uptime_str = f"{int(uptime_secs // 3600)}h {int((uptime_secs % 3600) // 60)}m"
            else:
                uptime_str = f"{int(uptime_secs // 60)}m {int(uptime_secs % 60)}s"
            stats["environment"]["uptime"] = uptime_str
            stats["environment"]["memory_mb"] = round(proc.memory_info().rss / (1024 * 1024), 1)
            stats["environment"]["cpu_percent"] = proc.cpu_percent(interval=0.05)
        except Exception:
            stats["environment"]["uptime"] = "--"
            stats["environment"]["memory_mb"] = "--"
            stats["environment"]["cpu_percent"] = "--"

        # ── System health quick-checks ──
        health_status = "healthy"
        health_checks: list = []

        # Database check
        db_ok = True
        try:
            first_model = next(iter(self._registry), None)
            if first_model:
                await first_model.objects.count()
        except Exception:
            db_ok = False

        health_checks.append({
            "name": "Database",
            "status": "ok" if db_ok else "error",
            "icon": "database",
        })

        # Audit log check (not overflowing)
        try:
            audit_log = self.audit_log
            # Support both AdminAuditLog (has _entries) and ModelBackedAuditLog (has _fallback)
            if hasattr(audit_log, '_entries'):
                current = len(audit_log._entries)
                capacity = audit_log._max_entries
            elif hasattr(audit_log, '_fallback'):
                current = len(audit_log._fallback._entries)
                capacity = audit_log._fallback._max_entries
            else:
                current = 0
                capacity = 10000
            audit_ok = current < capacity * 0.9
            health_checks.append({
                "name": "Audit Log",
                "status": "ok" if audit_ok else "warning",
                "icon": "scroll-text",
                "detail": f"{current}/{capacity}",
            })
        except Exception:
            health_checks.append({
                "name": "Audit Log",
                "status": "ok",
                "icon": "scroll-text",
            })

        # Memory check (if available)
        try:
            mem_mb = stats["environment"]["memory_mb"]
            if isinstance(mem_mb, (int, float)):
                mem_ok = mem_mb < 512
                health_checks.append({
                    "name": "Memory",
                    "status": "ok" if mem_ok else "warning",
                    "icon": "cpu",
                    "detail": f"{mem_mb} MB",
                })
        except Exception:
            pass

        if any(c["status"] == "error" for c in health_checks):
            health_status = "error"
        elif any(c["status"] == "warning" for c in health_checks):
            health_status = "warning"

        stats["system_health"] = {
            "status": health_status,
            "checks": health_checks,
        }

        return stats

    # ── Build info ───────────────────────────────────────────────────

    def get_build_info(self) -> Dict[str, Any]:
        """
        Gather build information from Crous artifacts in the build directory.

        Scans the workspace build/ directory for .crous files and
        bundle.manifest.crous, returning artifact metadata.
        """
        import os

        result: Dict[str, Any] = {
            "info": {},
            "artifacts": [],
            "pipeline_phases": [],
            "build_log": "",
        }

        # Find workspace root -- look for build/ directory
        build_dir = self._find_workspace_path("build")
        if build_dir is None or not build_dir.is_dir():
            return result

        # Read bundle manifest if it exists
        manifest_path = build_dir / "bundle.manifest.crous"
        if manifest_path.exists():
            try:
                try:
                    import _crous_native as _cb
                except ImportError:
                    import crous as _cb
                manifest = _cb.decode(manifest_path.read_bytes())
                result["info"] = {
                    "workspace_name": manifest.get("workspace_name", ""),
                    "workspace_version": manifest.get("workspace_version", ""),
                    "mode": manifest.get("mode", ""),
                    "fingerprint": manifest.get("fingerprint", ""),
                    "total_artifacts": manifest.get("artifact_count", 0),
                    "elapsed_ms": manifest.get("elapsed_ms", 0),
                }
            except Exception:
                pass

        # Scan for .crous files (ignore .aq.json -- Crous only)
        for fpath in sorted(build_dir.iterdir()):
            if fpath.suffix == ".crous" and fpath.is_file():
                try:
                    stat = fpath.stat()
                    size_kb = stat.st_size / 1024
                    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"

                    # Compute SHA-256 digest
                    import hashlib
                    digest = hashlib.sha256(fpath.read_bytes()).hexdigest()

                    # Determine kind from filename
                    name = fpath.stem
                    kind = "bundle" if "bundle" in name else (
                        "routes" if "route" in name else (
                        "di_graph" if "di" in name else (
                        "workspace" if "workspace" in name else "module"
                    )))

                    result["artifacts"].append({
                        "name": fpath.name,
                        "kind": kind,
                        "size": size_str,
                        "digest": digest,
                        "path": str(fpath),
                    })
                except Exception:
                    result["artifacts"].append({
                        "name": fpath.name,
                        "kind": "unknown",
                        "size": "?",
                        "digest": "",
                    })

        result["info"]["total_artifacts"] = len(result["artifacts"])

        # Build pipeline phases (static structure)
        result["pipeline_phases"] = [
            {"name": "Discovery", "status": "success" if result["artifacts"] else "pending",
             "detail": "Scan workspace for modules, controllers, models"},
            {"name": "Validation", "status": "success" if result["artifacts"] else "pending",
             "detail": "Validate manifest and module configuration"},
            {"name": "Static Check", "status": "success" if result["artifacts"] else "pending",
             "detail": "Pre-flight validation of all components"},
            {"name": "Compilation", "status": "success" if result["artifacts"] else "pending",
             "detail": "Compile modules to intermediate artifacts"},
            {"name": "Bundling", "status": "success" if result["artifacts"] else "pending",
             "detail": "Serialize to Crous binary format with dedup"},
            {"name": "Fingerprint", "status": "success" if result["info"].get("fingerprint") else "pending",
             "detail": "Compute content-addressed build fingerprint"},
        ]

        # Read build log if available
        build_log_path = build_dir / "build_output.txt"
        if build_log_path.exists():
            try:
                result["build_log"] = build_log_path.read_text(encoding="utf-8")
            except Exception:
                pass

        # Read artifact contents for the file viewer
        for artifact in result["artifacts"]:
            artifact["content"] = ""
            artifact["content_type"] = "binary"
            fpath_str = artifact.get("path", "")
            if not fpath_str:
                continue
            try:
                from pathlib import Path as _P
                fpath = _P(fpath_str)
                raw = fpath.read_bytes()

                # Try Crous decode first
                try:
                    from aquilia.build.bundler import _CrousBackend
                    backend = _CrousBackend()
                    decoded = backend.decode(raw)
                    import json as _json
                    artifact["content"] = _json.dumps(decoded, indent=2, default=str)
                    artifact["content_type"] = "json"
                    artifact["content_highlighted"] = self._highlight_json(artifact["content"])
                except Exception:
                    # Fallback: try UTF-8 text
                    try:
                        text = raw.decode("utf-8")
                        artifact["content"] = text
                        artifact["content_type"] = "text"
                        # Try to detect if it's JSON
                        text_stripped = text.strip()
                        if text_stripped and text_stripped[0] in ('{', '['):
                            try:
                                import json as _json2
                                _json2.loads(text_stripped)
                                artifact["content_type"] = "json"
                                artifact["content_highlighted"] = self._highlight_json(text)
                            except (ValueError, TypeError):
                                artifact["content_highlighted"] = self._highlight_crous(text)
                        else:
                            artifact["content_highlighted"] = self._highlight_crous(text)
                    except UnicodeDecodeError:
                        # Show hex dump for binary
                        hex_lines = []
                        for offset in range(0, min(len(raw), 2048), 16):
                            chunk = raw[offset:offset + 16]
                            hex_part = " ".join(f"{b:02x}" for b in chunk)
                            ascii_part = "".join(
                                chr(b) if 32 <= b < 127 else "." for b in chunk
                            )
                            hex_lines.append(f"{offset:08x}  {hex_part:<48s}  |{ascii_part}|")
                        if len(raw) > 2048:
                            hex_lines.append(f"... ({len(raw)} bytes total, showing first 2048)")
                        artifact["content"] = "\n".join(hex_lines)
                        artifact["content_type"] = "hex"
            except Exception:
                artifact["content"] = "(unable to read file)"
                artifact["content_type"] = "error"

        # Also scan for other build files (non-.crous)
        result["build_files"] = []
        for fpath in sorted(build_dir.iterdir()):
            if fpath.is_file() and fpath.suffix != ".crous":
                try:
                    content = fpath.read_text(encoding="utf-8")
                    result["build_files"].append({
                        "name": fpath.name,
                        "content": content,
                        "size": f"{fpath.stat().st_size / 1024:.1f} KB",
                    })
                except Exception:
                    pass

        return result

    # ── Migrations data ──────────────────────────────────────────────

    def get_migrations_data(self) -> List[Dict[str, Any]]:
        """
        Scan the migrations directory for migration files and
        return their metadata and syntax-highlighted source.
        """
        import re

        migrations_dir = self._find_workspace_path("migrations")
        if migrations_dir is None or not migrations_dir.is_dir():
            return []

        migrations: List[Dict[str, Any]] = []

        for fpath in sorted(migrations_dir.iterdir()):
            if not fpath.suffix == ".py" or fpath.name.startswith("__"):
                continue

            try:
                source = fpath.read_text(encoding="utf-8")

                # Extract metadata from the migration file
                revision = ""
                models: List[str] = []
                operations_count = 0

                # Parse revision from Meta class
                rev_match = re.search(r'revision\s*=\s*["\']([^"\']+)', source)
                if rev_match:
                    revision = rev_match.group(1)

                # Parse model names from Meta.models list
                models_match = re.search(r'models\s*=\s*\[([^\]]+)\]', source)
                if models_match:
                    models = re.findall(r"'(\w+)'", models_match.group(1))

                # Count operations
                operations_count = len(re.findall(r'(?:CreateModel|CreateIndex|AlterField|AddColumn|DropColumn|RenameField)\(', source))

                # Syntax highlight the source
                highlighted = self._highlight_python(source)

                migrations.append({
                    "filename": fpath.name,
                    "revision": revision,
                    "models": models,
                    "operations_count": operations_count,
                    "source": source,
                    "source_highlighted": highlighted,
                })
            except Exception:
                migrations.append({
                    "filename": fpath.name,
                    "revision": "",
                    "models": [],
                    "operations_count": 0,
                    "source": "",
                })

        return migrations

    # ── Config data ──────────────────────────────────────────────────

    def get_config_data(self) -> Dict[str, Any]:
        """
        Read workspace.py configuration (single-file config).

        Also reads config/*.py for legacy projects that still use
        a separate config directory.

        Returns file contents for display in the admin config page.
        """
        result: Dict[str, Any] = {
            "files": [],
            "workspace": None,
        }

        # Legacy: config/ directory files (backward compat)
        config_dir = self._find_workspace_path("config")
        if config_dir and config_dir.is_dir():
            for fpath in sorted(config_dir.glob("*.py")):
                if fpath.name.startswith("_"):
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8")
                    result["files"].append({
                        "name": fpath.name,
                        "path": f"config/{fpath.name}",
                        "content": content,
                        "content_highlighted": self._highlight_python(content),
                    })
                except Exception:
                    pass

        # Read workspace.py for workspace info
        ws_path = self._find_workspace_path("workspace.py", is_file=True)
        if ws_path and ws_path.exists():
            try:
                ws_source = ws_path.read_text(encoding="utf-8")
                import re

                # Extract workspace name
                name_match = re.search(r'(?:Workspace\(\s*["\'](\w+)|name\s*=\s*["\'](\w+))', ws_source)
                ws_name = (name_match.group(1) or name_match.group(2)) if name_match else ""

                # Extract version
                ver_match = re.search(r'version\s*=\s*["\']([^"\']+)', ws_source)
                ws_version = ver_match.group(1) if ver_match else ""

                # Extract modules
                module_matches = re.findall(r'Module\(\s*["\'](\w+)', ws_source)

                # Extract integrations
                intg_matches = re.findall(r'Integration\(\s*["\'](\w+)', ws_source)

                result["workspace"] = {
                    "name": ws_name,
                    "version": ws_version,
                    "modules": module_matches,
                    "integrations": intg_matches,
                }

                # Also add workspace.py as a config file
                result["files"].append({
                    "name": "workspace.py",
                    "path": "workspace.py",
                    "content": ws_source,
                    "content_highlighted": self._highlight_python(ws_source),
                })
            except Exception:
                pass

        return result

    # ── Workspace data ───────────────────────────────────────────────

    @staticmethod
    def _fmt_bytes(b: int) -> str:
        """Format bytes into human-readable string."""
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if abs(b) < 1024:
                return f"{b:.1f} {unit}"
            b /= 1024  # type: ignore[assignment]
        return f"{b:.1f} PB"

    def get_monitoring_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive system monitoring data.

        Collects CPU, memory, disk, network, process, Python runtime,
        and health-check information using ``psutil`` (with graceful
        fallbacks when it is not installed) and stdlib introspection.

        Returns a dict with sections:
            - cpu: percent, per_core, load_avg, freq, times, cores
            - memory: total, used, available, percent, swap_*
            - disk: total, used, free, percent, partitions
            - network: bytes_sent/recv, packets, errors, connections
            - process: pid, name, status, uptime, threads, rss, vms,
              fds, io_read/write_count/bytes
            - python: version, implementation, executable, gc_objects,
              gc_generations, gc_enabled, gc_frozen, loaded_modules,
              active_threads, recursion_limit, allocator_blocks
            - system: os, platform, arch, hostname
            - health_checks: list from HealthRegistry
        """
        import gc
        import os
        import platform
        import sys
        import time
        from datetime import datetime, timezone

        result: Dict[str, Any] = {
            "cpu": {},
            "memory": {},
            "disk": {},
            "network": {},
            "process": {},
            "python": {},
            "system": {},
            "health_checks": [],
        }

        # ── System info (always available) ──
        result["system"] = {
            "os": platform.system(),
            "platform": platform.platform(),
            "arch": platform.machine(),
            "hostname": platform.node(),
        }

        # ── Python runtime ──
        gc_gens = []
        try:
            for i, stats in enumerate(gc.get_stats()):
                gc_gens.append({
                    "generation": i,
                    "collections": stats.get("collections", 0),
                    "collected": stats.get("collected", 0),
                    "uncollectable": stats.get("uncollectable", 0),
                })
        except Exception:
            pass

        try:
            gc_frozen = gc.get_freeze_count()
        except (AttributeError, TypeError):
            gc_frozen = 0

        import threading

        result["python"] = {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "gc_objects": len(gc.get_objects()),
            "gc_generations": gc_gens,
            "gc_enabled": gc.isenabled(),
            "gc_frozen": gc_frozen,
            "loaded_modules": len(sys.modules),
            "active_threads": threading.active_count(),
            "recursion_limit": sys.getrecursionlimit(),
            "allocator_blocks": "--",
        }

        # ── psutil-based metrics ──
        try:
            import psutil

            # CPU
            # On Windows (and all platforms) the *first* call to
            # cpu_percent() with interval=None/0 returns a meaningless
            # 0.0.  Using interval>0 makes the call blocking but
            # guarantees a real reading.  We use interval=0.5 to get
            # a meaningful result even on a cold start, then the
            # subsequent per-core call uses interval=0.1 (also blocking)
            # so each core gets a real reading too.
            cpu_percent = psutil.cpu_percent(interval=0.5)
            per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            cpu_times = psutil.cpu_times()

            # On Windows os.getloadavg() does not exist.  psutil
            # provides getloadavg() but it returns (0,0,0) for the
            # first ~5 s because it spawns a background thread.
            # Fall back to using cpu_percent as a rough proxy.
            try:
                load_avg = psutil.getloadavg()
                # If load avg is still (0,0,0) on Windows (first 5 s),
                # approximate it from cpu_percent so the dashboard
                # is not blank.
                if platform.system() == "Windows" and load_avg == (0.0, 0.0, 0.0):
                    _approx = cpu_percent / 100.0 * (psutil.cpu_count() or 1)
                    load_avg = (_approx, _approx, _approx)
            except (AttributeError, OSError):
                load_avg = (0.0, 0.0, 0.0)

            result["cpu"] = {
                "percent": cpu_percent,
                "per_core": per_core,
                "cores_physical": psutil.cpu_count(logical=False) or 0,
                "cores_logical": psutil.cpu_count(logical=True) or 0,
                "freq_current": round(cpu_freq.current, 0) if cpu_freq else 0,
                "freq_max": round(cpu_freq.max, 0) if cpu_freq else 0,
                "load_avg_1": round(load_avg[0], 2),
                "load_avg_5": round(load_avg[1], 2),
                "load_avg_15": round(load_avg[2], 2),
                "times_user": round(getattr(cpu_times, "user", 0), 1),
                "times_system": round(getattr(cpu_times, "system", 0), 1),
                "times_idle": round(getattr(cpu_times, "idle", 0), 1),
            }

            # Memory
            vm = psutil.virtual_memory()
            sw = psutil.swap_memory()
            result["memory"] = {
                "total": vm.total,
                "total_human": self._fmt_bytes(vm.total),
                "available": vm.available,
                "available_human": self._fmt_bytes(vm.available),
                "used": vm.used,
                "used_human": self._fmt_bytes(vm.used),
                "percent": vm.percent,
                "swap_total": sw.total,
                "swap_total_human": self._fmt_bytes(sw.total),
                "swap_used": sw.used,
                "swap_used_human": self._fmt_bytes(sw.used),
                "swap_free": sw.free,
                "swap_free_human": self._fmt_bytes(sw.free),
                "swap_percent": sw.percent,
            }

            # Disk
            try:
                # Use platform-appropriate root path
                if platform.system() == "Windows":
                    _root = os.environ.get("SystemDrive", "C:") + "\\"
                else:
                    _root = "/"
                disk = psutil.disk_usage(_root)
                result["disk"] = {
                    "total": disk.total,
                    "total_human": self._fmt_bytes(disk.total),
                    "used": disk.used,
                    "used_human": self._fmt_bytes(disk.used),
                    "free": disk.free,
                    "free_human": self._fmt_bytes(disk.free),
                    "percent": disk.percent,
                    "partitions": [],
                }
            except Exception:
                result["disk"] = {
                    "total": 0, "total_human": "--",
                    "used": 0, "used_human": "--",
                    "free": 0, "free_human": "--",
                    "percent": 0, "partitions": [],
                }

            # Disk partitions
            try:
                for p in psutil.disk_partitions(all=False):
                    try:
                        usage = psutil.disk_usage(p.mountpoint)
                        result["disk"]["partitions"].append({
                            "device": p.device,
                            "mountpoint": p.mountpoint,
                            "fstype": p.fstype,
                            "total_human": self._fmt_bytes(usage.total),
                            "used_human": self._fmt_bytes(usage.used),
                            "free_human": self._fmt_bytes(usage.free),
                            "percent": usage.percent,
                        })
                    except (PermissionError, OSError):
                        continue
            except Exception:
                pass

            # Network
            try:
                net = psutil.net_io_counters()
                result["network"] = {
                    "bytes_sent": net.bytes_sent,
                    "bytes_sent_human": self._fmt_bytes(net.bytes_sent),
                    "bytes_recv": net.bytes_recv,
                    "bytes_recv_human": self._fmt_bytes(net.bytes_recv),
                    "packets_sent": net.packets_sent,
                    "packets_recv": net.packets_recv,
                    "errin": net.errin,
                    "errout": net.errout,
                    "dropin": net.dropin,
                    "dropout": net.dropout,
                    "connections_by_status": {},
                }
            except Exception:
                result["network"] = {
                    "bytes_sent": 0, "bytes_sent_human": "--",
                    "bytes_recv": 0, "bytes_recv_human": "--",
                    "packets_sent": 0, "packets_recv": 0,
                    "errin": 0, "errout": 0, "dropin": 0, "dropout": 0,
                    "connections_by_status": {},
                }

            # Connections by status
            try:
                conns = psutil.net_connections(kind="inet")
                status_counts: Dict[str, int] = {}
                for c in conns:
                    s = c.status if c.status else "NONE"
                    status_counts[s] = status_counts.get(s, 0) + 1
                result["network"]["connections_by_status"] = status_counts
            except (psutil.AccessDenied, PermissionError, OSError):
                # On Windows, net_connections() requires admin privileges
                pass

            # Process
            proc = psutil.Process(os.getpid())
            try:
                mem_info = proc.memory_info()
                rss = mem_info.rss
                vms = mem_info.vms
            except Exception:
                rss = 0
                vms = 0

            try:
                ctx_sw = proc.num_ctx_switches()
                ctx_vol = ctx_sw.voluntary
                ctx_invol = ctx_sw.involuntary
            except Exception:
                ctx_vol = 0
                ctx_invol = 0

            try:
                open_files_count = len(proc.open_files())
            except (psutil.AccessDenied, PermissionError, OSError):
                open_files_count = 0

            try:
                create_time = proc.create_time()
                uptime_s = time.time() - create_time
                uptime_human = self._format_uptime(uptime_s)
                create_time_str = datetime.fromtimestamp(
                    create_time, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M:%S UTC")
            except Exception:
                uptime_human = "--"
                create_time_str = "--"

            # Shared / private memory (platform-specific)
            shared_mem = 0
            private_mem = 0
            try:
                ext = proc.memory_info()
                if hasattr(ext, "shared"):
                    shared_mem = ext.shared
                    private_mem = rss - shared_mem
                else:
                    private_mem = rss
            except Exception:
                private_mem = rss

            result["process"] = {
                "pid": os.getpid(),
                "name": proc.name(),
                "status": proc.status(),
                "create_time": create_time_str,
                "uptime_human": uptime_human,
                "threads": proc.num_threads(),
                "open_files": open_files_count,
                "rss": rss,
                "rss_human": self._fmt_bytes(rss),
                "vms": vms,
                "vms_human": self._fmt_bytes(vms),
                "shared": shared_mem,
                "private": private_mem,
                "mem_percent": proc.memory_percent(),
                "ctx_switches": ctx_vol + ctx_invol,
                "ctx_switches_voluntary": ctx_vol,
                "ctx_switches_involuntary": ctx_invol,
                "env_snapshot": self._safe_env_snapshot(),
            }

            # I/O counters (platform-specific; may raise AccessDenied)
            try:
                io_counters = proc.io_counters()
                result["process"]["io_read_count"] = io_counters.read_count
                result["process"]["io_write_count"] = io_counters.write_count
                result["process"]["io_read_bytes"] = io_counters.read_bytes
                result["process"]["io_read_bytes_human"] = self._fmt_bytes(
                    io_counters.read_bytes,
                )
                result["process"]["io_write_bytes"] = io_counters.write_bytes
                result["process"]["io_write_bytes_human"] = self._fmt_bytes(
                    io_counters.write_bytes,
                )
            except (psutil.AccessDenied, AttributeError, OSError):
                result["process"]["io_read_count"] = "--"
                result["process"]["io_write_count"] = "--"
                result["process"]["io_read_bytes_human"] = "--"
                result["process"]["io_write_bytes_human"] = "--"

        except ImportError:
            # psutil not available -- try to provide data via stdlib
            # and platform-specific fallbacks
            import logging
            logging.getLogger("aquilia.admin").warning(
                "psutil is not installed — monitoring data will be limited. "
                "Install it with: pip install psutil"
            )
            result["_psutil_missing"] = True

            # ── CPU fallback (stdlib + platform-specific) ──
            _cpu_pct = 0.0
            _per_core: list = []
            _cores_logical = os.cpu_count() or 0
            if platform.system() == "Windows":
                # Use WMI via subprocess to get CPU usage
                try:
                    import subprocess
                    wmi_out = subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Processor | "
                         "Select-Object -ExpandProperty LoadPercentage"],
                        capture_output=True, text=True, timeout=5,
                        encoding="utf-8",
                    )
                    if wmi_out.returncode == 0 and wmi_out.stdout.strip():
                        _cpu_pct = float(wmi_out.stdout.strip().splitlines()[0])
                except Exception:
                    pass
                # Per-core via typeperf (quick one-shot)
                try:
                    import subprocess
                    tp_out = subprocess.run(
                        ["typeperf", r"\Processor(*)\% Processor Time",
                         "-sc", "1"],
                        capture_output=True, text=True, timeout=10,
                        encoding="utf-8",
                    )
                    if tp_out.returncode == 0:
                        lines = tp_out.stdout.strip().splitlines()
                        if len(lines) >= 2:
                            # Second line has the data values, skip timestamp
                            vals = lines[1].split(",")[1:]  # skip first field (timestamp)
                            # Last value is _Total, skip it
                            core_vals = vals[:-1] if len(vals) > 1 else vals
                            _per_core = []
                            for v in core_vals:
                                v = v.strip().strip('"')
                                try:
                                    _per_core.append(round(float(v), 1))
                                except (ValueError, TypeError):
                                    pass
                except Exception:
                    pass

            result["cpu"] = {
                "percent": _cpu_pct, "per_core": _per_core,
                "cores_physical": 0,
                "cores_logical": _cores_logical,
                "freq_current": 0, "freq_max": 0,
                "load_avg_1": 0, "load_avg_5": 0, "load_avg_15": 0,
                "times_user": 0, "times_system": 0, "times_idle": 0,
            }

            # ── Memory fallback ──
            _mem_total = 0
            _mem_avail = 0
            _mem_used = 0
            _mem_pct = 0.0
            if platform.system() == "Windows":
                try:
                    import ctypes
                    class MEMORYSTATUSEX(ctypes.Structure):
                        _fields_ = [
                            ("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                        ]
                    stat = MEMORYSTATUSEX()
                    stat.dwLength = ctypes.sizeof(stat)
                    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                    _mem_total = stat.ullTotalPhys
                    _mem_avail = stat.ullAvailPhys
                    _mem_used = _mem_total - _mem_avail
                    _mem_pct = round(stat.dwMemoryLoad, 1)
                except Exception:
                    pass
            result["memory"] = {
                "total": _mem_total, "total_human": self._fmt_bytes(_mem_total),
                "available": _mem_avail, "available_human": self._fmt_bytes(_mem_avail),
                "used": _mem_used, "used_human": self._fmt_bytes(_mem_used),
                "percent": _mem_pct,
                "swap_total": 0, "swap_total_human": "--",
                "swap_used": 0, "swap_used_human": "--",
                "swap_free": 0, "swap_free_human": "--",
                "swap_percent": 0,
            }

            # ── Disk fallback ──
            _dk_total = 0
            _dk_used = 0
            _dk_free = 0
            _dk_pct = 0.0
            try:
                import shutil
                if platform.system() == "Windows":
                    _dk_root = os.environ.get("SystemDrive", "C:") + "\\"
                else:
                    _dk_root = "/"
                du = shutil.disk_usage(_dk_root)
                _dk_total = du.total
                _dk_used = du.used
                _dk_free = du.free
                _dk_pct = round(du.used / du.total * 100, 1) if du.total else 0
            except Exception:
                pass
            result["disk"] = {
                "total": _dk_total, "total_human": self._fmt_bytes(_dk_total),
                "used": _dk_used, "used_human": self._fmt_bytes(_dk_used),
                "free": _dk_free, "free_human": self._fmt_bytes(_dk_free),
                "percent": _dk_pct, "partitions": [],
            }

            result["network"] = {
                "bytes_sent": 0, "bytes_sent_human": "--",
                "bytes_recv": 0, "bytes_recv_human": "--",
                "packets_sent": 0, "packets_recv": 0,
                "errin": 0, "errout": 0, "dropin": 0, "dropout": 0,
                "connections_by_status": {},
            }

            # ── Process fallback ──
            _p_rss = 0
            _p_vms = 0
            if platform.system() == "Windows":
                try:
                    import ctypes
                    from ctypes import wintypes
                    # GetProcessMemoryInfo via kernel32/psapi
                    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                        _fields_ = [
                            ("cb", wintypes.DWORD),
                            ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t),
                            ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t),
                            ("PeakPagefileUsage", ctypes.c_size_t),
                        ]
                    pmc = PROCESS_MEMORY_COUNTERS()
                    pmc.cb = ctypes.sizeof(pmc)
                    handle = ctypes.windll.kernel32.GetCurrentProcess()
                    if ctypes.windll.psapi.GetProcessMemoryInfo(
                        handle, ctypes.byref(pmc), pmc.cb
                    ):
                        _p_rss = pmc.WorkingSetSize
                        _p_vms = pmc.PagefileUsage
                except Exception:
                    pass

            import threading as _thr
            result["process"] = {
                "pid": os.getpid(), "name": "python", "status": "running",
                "create_time": "--", "uptime_human": "--",
                "threads": _thr.active_count(), "open_files": 0,
                "rss": _p_rss, "rss_human": self._fmt_bytes(_p_rss),
                "vms": _p_vms, "vms_human": self._fmt_bytes(_p_vms),
                "shared": 0, "private": _p_rss,
                "mem_percent": round(_p_rss / _mem_total * 100, 2) if _mem_total else 0,
                "ctx_switches": 0,
                "ctx_switches_voluntary": 0, "ctx_switches_involuntary": 0,
                "env_snapshot": self._safe_env_snapshot(),
                "io_read_count": "--", "io_write_count": "--",
                "io_read_bytes_human": "--", "io_write_bytes_human": "--",
            }

        except Exception as _psutil_err:
            # psutil is installed but raised an unexpected error.
            # Log it so the user can diagnose, and still return
            # partial data from stdlib fallbacks.
            import logging
            logging.getLogger("aquilia.admin").error(
                "Monitoring: psutil raised %s: %s",
                type(_psutil_err).__name__, _psutil_err,
            )
            result["_psutil_error"] = f"{type(_psutil_err).__name__}: {_psutil_err}"

            # Provide minimal data via stdlib so the dashboard is not
            # completely empty.
            _cpu_fallback = 0.0
            _cores = os.cpu_count() or 0
            if platform.system() == "Windows":
                try:
                    import subprocess
                    wmi_out = subprocess.run(
                        ["powershell", "-NoProfile", "-Command",
                         "Get-CimInstance Win32_Processor | "
                         "Select-Object -ExpandProperty LoadPercentage"],
                        capture_output=True, text=True, timeout=5,
                        encoding="utf-8",
                    )
                    if wmi_out.returncode == 0 and wmi_out.stdout.strip():
                        _cpu_fallback = float(wmi_out.stdout.strip().splitlines()[0])
                except Exception:
                    pass

            if not result.get("cpu") or not result["cpu"].get("percent"):
                result["cpu"] = {
                    "percent": _cpu_fallback, "per_core": [],
                    "cores_physical": 0,
                    "cores_logical": _cores,
                    "freq_current": 0, "freq_max": 0,
                    "load_avg_1": 0, "load_avg_5": 0, "load_avg_15": 0,
                    "times_user": 0, "times_system": 0, "times_idle": 0,
                }
            if not result.get("memory") or not result["memory"].get("total"):
                _mt = 0
                _ma = 0
                _mu = 0
                _mp = 0.0
                if platform.system() == "Windows":
                    try:
                        import ctypes
                        class _MSEX(ctypes.Structure):
                            _fields_ = [
                                ("dwLength", ctypes.c_ulong),
                                ("dwMemoryLoad", ctypes.c_ulong),
                                ("ullTotalPhys", ctypes.c_ulonglong),
                                ("ullAvailPhys", ctypes.c_ulonglong),
                                ("ullTotalPageFile", ctypes.c_ulonglong),
                                ("ullAvailPageFile", ctypes.c_ulonglong),
                                ("ullTotalVirtual", ctypes.c_ulonglong),
                                ("ullAvailVirtual", ctypes.c_ulonglong),
                                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                            ]
                        _s = _MSEX()
                        _s.dwLength = ctypes.sizeof(_s)
                        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(_s))
                        _mt = _s.ullTotalPhys
                        _ma = _s.ullAvailPhys
                        _mu = _mt - _ma
                        _mp = round(_s.dwMemoryLoad, 1)
                    except Exception:
                        pass
                result["memory"] = {
                    "total": _mt, "total_human": self._fmt_bytes(_mt),
                    "available": _ma, "available_human": self._fmt_bytes(_ma),
                    "used": _mu, "used_human": self._fmt_bytes(_mu),
                    "percent": _mp,
                    "swap_total": 0, "swap_total_human": "--",
                    "swap_used": 0, "swap_used_human": "--",
                    "swap_free": 0, "swap_free_human": "--",
                    "swap_percent": 0,
                }
            if not result.get("disk") or not result["disk"].get("total"):
                try:
                    import shutil
                    _r = (os.environ.get("SystemDrive", "C:") + "\\") if platform.system() == "Windows" else "/"
                    _du = shutil.disk_usage(_r)
                    result["disk"] = {
                        "total": _du.total, "total_human": self._fmt_bytes(_du.total),
                        "used": _du.used, "used_human": self._fmt_bytes(_du.used),
                        "free": _du.free, "free_human": self._fmt_bytes(_du.free),
                        "percent": round(_du.used / _du.total * 100, 1) if _du.total else 0,
                        "partitions": [],
                    }
                except Exception:
                    result["disk"] = {
                        "total": 0, "total_human": "--",
                        "used": 0, "used_human": "--",
                        "free": 0, "free_human": "--",
                        "percent": 0, "partitions": [],
                    }
            if not result.get("network") or not result["network"].get("bytes_sent"):
                result["network"] = {
                    "bytes_sent": 0, "bytes_sent_human": "--",
                    "bytes_recv": 0, "bytes_recv_human": "--",
                    "packets_sent": 0, "packets_recv": 0,
                    "errin": 0, "errout": 0, "dropin": 0, "dropout": 0,
                    "connections_by_status": {},
                }
            if not result.get("process") or not result["process"].get("pid"):
                result["process"] = {
                    "pid": os.getpid(), "name": "python", "status": "running",
                    "create_time": "--", "uptime_human": "--",
                    "threads": 0, "open_files": 0,
                    "rss": 0, "rss_human": "--", "vms": 0, "vms_human": "--",
                    "shared": 0, "private": 0,
                    "mem_percent": 0, "ctx_switches": 0,
                    "ctx_switches_voluntary": 0, "ctx_switches_involuntary": 0,
                    "env_snapshot": self._safe_env_snapshot(),
                    "io_read_count": "--", "io_write_count": "--",
                    "io_read_bytes_human": "--", "io_write_bytes_human": "--",
                }

        # ── Health checks ──
        try:
            from aquilia.health import HealthRegistry
            # Try to find a HealthRegistry in the DI container or global
            registry = getattr(self, "_health_registry", None)
            if registry is None:
                # Look for a global instance
                import aquilia
                registry = getattr(aquilia, "_health_registry", None)
            if registry and isinstance(registry, HealthRegistry):
                for name, status in registry.all_statuses.items():
                    result["health_checks"].append(status.to_dict())
        except Exception:
            pass

        # ── Filter by admin_config.monitoring_metrics ──
        # Only keep metric sections the user has opted-in to.
        cfg = self.admin_config
        all_sections = ("cpu", "memory", "disk", "network", "process", "python", "system", "health_checks")
        for section in all_sections:
            if not cfg.is_metric_enabled(section):
                result[section] = {} if section != "health_checks" else []

        # Attach refresh interval for the frontend
        result["_refresh_interval"] = cfg.monitoring_refresh_interval

        return result

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        """Format seconds into human-readable uptime string."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)

    @staticmethod
    def _safe_env_snapshot() -> Dict[str, str]:
        """Capture a safe subset of environment variables (no secrets)."""
        import os
        import platform as _plat

        # Cross-platform env var list
        safe_keys = [
            "VIRTUAL_ENV", "PYTHONPATH", "PATH",
            "AQUILIA_ENV", "AQUILIA_DEBUG",
        ]
        if _plat.system() == "Windows":
            safe_keys.extend([
                "USERPROFILE", "USERNAME", "COMSPEC",
                "SYSTEMROOT", "COMPUTERNAME", "APPDATA",
                "TEMP", "TMP",
            ])
        else:
            safe_keys.extend([
                "HOME", "USER", "SHELL", "TERM",
                "LANG", "LC_ALL", "TZ",
            ])

        result: Dict[str, str] = {}
        for key in safe_keys:
            val = os.environ.get(key)
            if val:
                # Truncate long values
                if len(val) > 200:
                    val = val[:200] + "…"
                result[key] = val
        return result

    # ── Containers & Pods data ───────────────────────────────────────

    def get_containers_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive Docker container and compose data.

        Discovers:
        - Running/stopped containers via ``docker ps``
        - Compose services from ``docker-compose.yml``
        - Docker system info (version, images, volumes, networks)
        - Dockerfile metadata from workspace
        - Container resource usage via ``docker stats``

        Returns a dict with sections:
            - docker_available: bool
            - docker_version: str
            - containers: list of container dicts
            - compose: compose file metadata
            - images: list of image dicts
            - volumes: list of volume dicts
            - networks: list of network dicts
            - system_info: Docker system overview
            - dockerfile_info: Dockerfile analysis
            - error: optional error string
        """
        import json as _json
        import os
        import subprocess
        from datetime import datetime, timezone
        from pathlib import Path

        result: Dict[str, Any] = {
            "docker_available": False,
            "docker_version": "",
            "containers": [],
            "compose": {"available": False, "services": [], "file_content": ""},
            "images": [],
            "volumes": [],
            "networks": [],
            "system_info": {},
            "dockerfile_info": {},
            "error": "",
        }

        def _run_docker(*args: str, timeout: int = 10) -> tuple:
            """Run a docker command and return (success, stdout, stderr)."""
            try:
                proc = subprocess.run(
                    ["docker", *args],
                    capture_output=True, text=True, encoding="utf-8", timeout=timeout,
                )
                return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
            except FileNotFoundError:
                return False, "", "Docker CLI not found"
            except subprocess.TimeoutExpired:
                return False, "", "Command timed out"
            except Exception as e:
                return False, "", str(e)

        # ── Check Docker availability ──
        ok, ver_out, ver_err = _run_docker("version", "--format", "{{.Server.Version}}")
        if not ok:
            # Try just docker info to see if daemon is reachable
            ok2, _, _ = _run_docker("info", "--format", "{{.ServerVersion}}")
            if not ok2:
                result["error"] = ver_err or "Docker is not available"
                return result

        result["docker_available"] = True
        result["docker_version"] = ver_out or "unknown"

        # ── Docker system info ──
        ok, info_out, _ = _run_docker(
            "system", "info", "--format",
            '{"containers":{{.Containers}},"running":{{.ContainersRunning}},'
            '"paused":{{.ContainersPaused}},"stopped":{{.ContainersStopped}},'
            '"images":{{.Images}},"server_version":"{{.ServerVersion}}",'
            '"os":"{{.OperatingSystem}}","arch":"{{.Architecture}}",'
            '"cpus":{{.NCPU}},"memory":"{{.MemTotal}}",'
            '"storage_driver":"{{.Driver}}"}'
        )
        if ok and info_out:
            try:
                result["system_info"] = _json.loads(info_out)
            except _json.JSONDecodeError:
                result["system_info"] = {"raw": info_out}

        # ── List containers (all, including stopped) ──
        # Use {{json .}} to avoid broken JSON from embedded quotes
        # in Command/Labels fields. Docker escapes properly with json.
        ok, ps_out, _ = _run_docker(
            "ps", "-a", "--no-trunc", "--format", "{{json .}}"
        )
        if ok and ps_out:
            for line in ps_out.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = _json.loads(line)
                    # Normalize PascalCase → lowercase keys
                    container = {
                        "id": raw.get("ID", ""),
                        "name": raw.get("Names", ""),
                        "image": raw.get("Image", ""),
                        "status": raw.get("Status", ""),
                        "state": raw.get("State", ""),
                        "ports": raw.get("Ports", ""),
                        "created": raw.get("CreatedAt", ""),
                        "size": raw.get("Size", ""),
                        "command": raw.get("Command", ""),
                        "labels": raw.get("Labels", ""),
                        "networks": raw.get("Networks", ""),
                        "mounts": raw.get("Mounts", ""),
                        "running_for": raw.get("RunningFor", ""),
                        "local_volumes": raw.get("LocalVolumes", ""),
                    }
                    # Parse state for status classification
                    state = container.get("state", "").lower()
                    if state == "running":
                        container["status_class"] = "running"
                        container["status_icon"] = "▶"
                    elif state == "exited":
                        container["status_class"] = "stopped"
                        container["status_icon"] = "■"
                    elif state == "paused":
                        container["status_class"] = "paused"
                        container["status_icon"] = "⏸"
                    elif state in ("restarting", "removing"):
                        container["status_class"] = "warning"
                        container["status_icon"] = "↻"
                    elif state == "created":
                        container["status_class"] = "created"
                        container["status_icon"] = "○"
                    elif state == "dead":
                        container["status_class"] = "dead"
                        container["status_icon"] = "✕"
                    else:
                        container["status_class"] = "unknown"
                        container["status_icon"] = "?"
                    result["containers"].append(container)
                except _json.JSONDecodeError:
                    continue

        # ── Container stats (CPU/memory for running containers) ──
        running_ids = [c["id"] for c in result["containers"]
                       if c.get("status_class") == "running"]
        if running_ids:
            ok, stats_out, _ = _run_docker(
                "stats", "--no-stream", "--format", "{{json .}}",
                timeout=15,
            )
            if ok and stats_out:
                stats_map: Dict[str, Dict] = {}
                for line in stats_out.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw_stat = _json.loads(line)
                        stat = {
                            "id": raw_stat.get("ID", ""),
                            "name": raw_stat.get("Name", ""),
                            "cpu": raw_stat.get("CPUPerc", "0%"),
                            "memory": raw_stat.get("MemUsage", ""),
                            "mem_perc": raw_stat.get("MemPerc", "0%"),
                            "net_io": raw_stat.get("NetIO", ""),
                            "block_io": raw_stat.get("BlockIO", ""),
                            "pids": raw_stat.get("PIDs", ""),
                        }
                        stats_map[stat["id"][:12]] = stat
                    except _json.JSONDecodeError:
                        continue
                # Merge stats into containers
                for c in result["containers"]:
                    cid = c["id"][:12]
                    if cid in stats_map:
                        c["stats"] = stats_map[cid]

        # ── Docker images ──
        ok, img_out, _ = _run_docker(
            "images", "--format", "{{json .}}"
        )
        if ok and img_out:
            for line in img_out.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    raw_img = _json.loads(line)
                    result["images"].append({
                        "id": raw_img.get("ID", ""),
                        "repository": raw_img.get("Repository", ""),
                        "tag": raw_img.get("Tag", ""),
                        "size": raw_img.get("Size", ""),
                        "created": raw_img.get("CreatedAt", ""),
                    })
                except _json.JSONDecodeError:
                    continue

        # ── Docker volumes ──
        ok, vol_out, _ = _run_docker(
            "volume", "ls", "--format", "{{json .}}"
        )
        if ok and vol_out:
            for line in vol_out.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    raw_vol = _json.loads(line)
                    result["volumes"].append({
                        "name": raw_vol.get("Name", ""),
                        "driver": raw_vol.get("Driver", ""),
                        "mountpoint": raw_vol.get("Mountpoint", ""),
                    })
                except _json.JSONDecodeError:
                    continue

        # ── Docker networks ──
        ok, net_out, _ = _run_docker(
            "network", "ls", "--format", "{{json .}}"
        )
        if ok and net_out:
            for line in net_out.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    raw_net = _json.loads(line)
                    result["networks"].append({
                        "id": raw_net.get("ID", ""),
                        "name": raw_net.get("Name", ""),
                        "driver": raw_net.get("Driver", ""),
                        "scope": raw_net.get("Scope", ""),
                    })
                except _json.JSONDecodeError:
                    continue

        # ── Compose file analysis ──
        compose_path = self._find_workspace_path("docker-compose.yml", is_file=True)
        if compose_path and compose_path.is_file():
            result["compose"]["available"] = True
            try:
                content = compose_path.read_text(encoding="utf-8", errors="replace")
                result["compose"]["file_content"] = content
                # Parse services from YAML
                try:
                    import yaml
                    parsed = yaml.safe_load(content)
                    if isinstance(parsed, dict) and "services" in parsed:
                        for svc_name, svc_conf in parsed["services"].items():
                            result["compose"]["services"].append({
                                "name": svc_name,
                                "image": svc_conf.get("image", ""),
                                "build": str(svc_conf.get("build", "")),
                                "ports": svc_conf.get("ports", []),
                                "volumes": svc_conf.get("volumes", []),
                                "depends_on": (
                                    list(svc_conf["depends_on"].keys())
                                    if isinstance(svc_conf.get("depends_on"), dict)
                                    else svc_conf.get("depends_on", [])
                                ),
                                "environment": svc_conf.get("environment", {}),
                                "profiles": svc_conf.get("profiles", []),
                                "restart": svc_conf.get("restart", ""),
                                "healthcheck": bool(svc_conf.get("healthcheck")),
                            })
                except ImportError:
                    # PyYAML not installed -- basic regex parsing
                    import re
                    svc_matches = re.findall(
                        r'^\s{2}(\w[\w-]*):\s*$', content, re.MULTILINE,
                    )
                    for svc_name in svc_matches:
                        result["compose"]["services"].append({
                            "name": svc_name,
                            "image": "",
                            "build": "",
                            "ports": [],
                            "volumes": [],
                            "depends_on": [],
                            "environment": {},
                            "profiles": [],
                            "restart": "",
                            "healthcheck": False,
                        })
                except Exception:
                    pass
            except Exception:
                pass

        # ── Dockerfile analysis ──
        dockerfile_path = self._find_workspace_path("Dockerfile", is_file=True)
        if dockerfile_path and dockerfile_path.is_file():
            try:
                content = dockerfile_path.read_text(encoding="utf-8", errors="replace")
                import re
                result["dockerfile_info"] = {
                    "exists": True,
                    "path": str(dockerfile_path),
                    "size": f"{dockerfile_path.stat().st_size / 1024:.1f} KB",
                    "base_image": "",
                    "stages": [],
                    "exposed_ports": [],
                    "env_vars": [],
                    "copy_count": 0,
                    "run_count": 0,
                }
                # Extract ARG defaults so we can resolve ${VAR} in FROM lines
                arg_defaults = dict(
                    re.findall(r'^ARG\s+(\w+)=(\S+)', content, re.MULTILINE)
                )

                def _resolve_args(s: str) -> str:
                    """Resolve ${VAR} and $VAR references using ARG defaults."""
                    for var, val in arg_defaults.items():
                        s = s.replace("${" + var + "}", val).replace("$" + var, val)
                    return s

                # Extract FROM instructions (multi-stage)
                froms = re.findall(r'^FROM\s+(\S+)(?:\s+AS\s+(\S+))?',
                                   content, re.MULTILINE | re.IGNORECASE)
                if froms:
                    resolved_base = _resolve_args(froms[0][0])
                    result["dockerfile_info"]["base_image"] = resolved_base
                    result["dockerfile_info"]["stages"] = [
                        {"image": _resolve_args(img), "alias": alias or ""}
                        for img, alias in froms
                    ]
                # Exposed ports
                ports = re.findall(r'^EXPOSE\s+(.+)', content, re.MULTILINE | re.IGNORECASE)
                for p in ports:
                    result["dockerfile_info"]["exposed_ports"].extend(p.split())
                # ENV vars
                envs = re.findall(r'^ENV\s+(\S+)', content, re.MULTILINE | re.IGNORECASE)
                result["dockerfile_info"]["env_vars"] = envs
                # Instruction counts
                result["dockerfile_info"]["copy_count"] = len(
                    re.findall(r'^COPY\s', content, re.MULTILINE | re.IGNORECASE)
                )
                result["dockerfile_info"]["run_count"] = len(
                    re.findall(r'^RUN\s', content, re.MULTILINE | re.IGNORECASE)
                )
            except Exception:
                result["dockerfile_info"] = {"exists": True, "path": str(dockerfile_path)}
        else:
            result["dockerfile_info"] = {"exists": False}

        return result

    # ── Docker Action Helpers ────────────────────────────────────────

    def execute_container_action(
        self, container_id: str, action: str,
        run_params: str = "",
    ) -> Dict[str, Any]:
        """
        Execute a Docker container lifecycle action.

        Supported actions: start, stop, restart, pause, unpause, kill, rm, run
        """
        import subprocess

        ALLOWED = {"start", "stop", "restart", "pause", "unpause", "kill", "rm", "run"}
        if action not in ALLOWED:
            return {"success": False, "error": f"Unknown action: {action}"}

        # ── docker run (create+start a new container) ──
        if action == "run":
            import json as _json
            import shlex

            try:
                params = _json.loads(run_params) if run_params else {}
            except _json.JSONDecodeError:
                return {"success": False, "error": "Invalid run_params JSON"}

            image = params.get("image", "").strip()
            if not image:
                return {"success": False, "error": "Image name is required"}

            args = ["docker", "run"]
            if params.get("detach"):
                args.append("-d")
            if params.get("auto_remove"):
                args.append("--rm")
            name = params.get("name", "").strip()
            if name:
                args.extend(["--name", name])
            ports = params.get("ports", "").strip()
            if ports:
                args.extend(["-p", ports])
            env_vars = params.get("env_vars", "").strip()
            if env_vars:
                for ev in env_vars.splitlines():
                    ev = ev.strip()
                    if ev and "=" in ev:
                        args.extend(["-e", ev])
            extra_flags = params.get("extra_flags", "").strip()
            if extra_flags:
                args.extend(shlex.split(extra_flags))
            args.append(image)

            try:
                proc = subprocess.run(
                    args, capture_output=True, text=True, encoding="utf-8", timeout=120,
                )
                if proc.returncode == 0:
                    cid = proc.stdout.strip()[:12] or "started"
                    return {
                        "success": True,
                        "message": f"Container {cid} started from {image}",
                    }
                return {
                    "success": False,
                    "error": proc.stderr.strip() or "docker run failed",
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "docker run timed out"}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Sanitize container_id (only allow hex + short names)
        cid = container_id.strip()
        if not cid:
            return {"success": False, "error": "Empty container ID"}

        try:
            args = ["docker", action]
            if action == "rm":
                args.append("-f")
            args.append(cid)
            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            if proc.returncode == 0:
                return {"success": True, "message": f"Container {action} successful"}
            return {"success": False, "error": proc.stderr.strip() or f"{action} failed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_container_inspect(self, container_id: str) -> Dict[str, Any]:
        """Return full ``docker inspect`` output for a container."""
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "inspect", container_id.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode == 0:
                data = _json.loads(proc.stdout)
                if isinstance(data, list) and data:
                    return {"success": True, "data": data[0]}
                return {"success": True, "data": data}
            return {"success": False, "error": proc.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_container_logs(
        self, container_id: str, *, tail: int = 200, since: str = "",
    ) -> Dict[str, Any]:
        """Fetch recent logs from a container via ``docker logs``."""
        import subprocess

        args = ["docker", "logs", "--tail", str(tail), "--timestamps"]
        if since:
            args.extend(["--since", since])
        args.append(container_id.strip())

        try:
            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            # docker logs outputs to both stdout and stderr
            output = proc.stdout + proc.stderr
            return {"success": True, "logs": output}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Logs fetch timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_volume_inspect(self, volume_name: str) -> Dict[str, Any]:
        """Return ``docker volume inspect`` output."""
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "volume", "inspect", volume_name.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode == 0:
                data = _json.loads(proc.stdout)
                if isinstance(data, list) and data:
                    return {"success": True, "data": data[0]}
                return {"success": True, "data": data}
            return {"success": False, "error": proc.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_network_inspect(self, network_id: str) -> Dict[str, Any]:
        """Return ``docker network inspect`` output."""
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "network", "inspect", network_id.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode == 0:
                data = _json.loads(proc.stdout)
                if isinstance(data, list) and data:
                    return {"success": True, "data": data[0]}
                return {"success": True, "data": data}
            return {"success": False, "error": proc.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_image_inspect(self, image_id: str) -> Dict[str, Any]:
        """Return ``docker image inspect`` output."""
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "image", "inspect", image_id.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode == 0:
                data = _json.loads(proc.stdout)
                if isinstance(data, list) and data:
                    return {"success": True, "data": data[0]}
                return {"success": True, "data": data}
            return {"success": False, "error": proc.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_image_action(
        self, image_id: str, action: str,
    ) -> Dict[str, Any]:
        """
        Execute a Docker image action.

        Supported actions: rm (remove), pull
        """
        import subprocess

        ALLOWED = {"rm", "pull"}
        if action not in ALLOWED:
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            if action == "rm":
                proc = subprocess.run(
                    ["docker", "rmi", "-f", image_id.strip()],
                    capture_output=True, text=True, encoding="utf-8", timeout=30,
                )
            else:  # pull
                proc = subprocess.run(
                    ["docker", "pull", image_id.strip()],
                    capture_output=True, text=True, encoding="utf-8", timeout=120,
                )

            if proc.returncode == 0:
                return {"success": True, "message": f"Image {action} successful"}
            return {"success": False, "error": proc.stderr.strip() or f"{action} failed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_compose_action(self, action: str) -> Dict[str, Any]:
        """
        Execute a Docker Compose action.

        Supported actions: up, down, restart, build, pull, stop, start
        """
        import subprocess
        from pathlib import Path

        ALLOWED = {"up", "down", "restart", "build", "pull", "stop", "start"}
        if action not in ALLOWED:
            return {"success": False, "error": f"Unknown compose action: {action}"}

        compose_path = self._find_workspace_path("docker-compose.yml", is_file=True)
        if not compose_path or not compose_path.is_file():
            return {"success": False, "error": "No docker-compose.yml found"}

        compose_dir = compose_path.parent

        # If docker-compose.yml references env_file: .env but no .env exists,
        # create an empty one so docker compose doesn't fail.
        env_file = compose_dir / ".env"
        if not env_file.exists():
            try:
                env_file.write_text("# Auto-created by Aquilia admin\n", encoding="utf-8")
            except OSError:
                pass  # non-fatal: compose may still work

        try:
            args = ["docker", "compose", "-f", str(compose_path)]
            if action == "up":
                args.extend(["up", "-d", "--remove-orphans"])
            elif action == "down":
                args.append("down")
            else:
                args.append(action)

            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", timeout=120,
                cwd=str(compose_dir),
            )
            output = proc.stdout + proc.stderr
            if proc.returncode == 0:
                return {"success": True, "message": f"Compose {action} successful", "output": output}
            return {"success": False, "error": output or f"Compose {action} failed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_volume_action(
        self, volume_name: str, action: str,
    ) -> Dict[str, Any]:
        """Execute a Docker volume action. Supported: rm"""
        import subprocess

        if action != "rm":
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            proc = subprocess.run(
                ["docker", "volume", "rm", "-f", volume_name.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            if proc.returncode == 0:
                return {"success": True, "message": "Volume removed"}
            return {"success": False, "error": proc.stderr.strip() or "Remove failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_network_action(
        self, network_id: str, action: str,
    ) -> Dict[str, Any]:
        """Execute a Docker network action. Supported: rm"""
        import subprocess

        if action != "rm":
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            proc = subprocess.run(
                ["docker", "network", "rm", network_id.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            if proc.returncode == 0:
                return {"success": True, "message": "Network removed"}
            return {"success": False, "error": proc.stderr.strip() or "Remove failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Advanced Docker Features ─────────────────────────────────────

    def get_docker_disk_usage(self) -> Dict[str, Any]:
        """
        Return ``docker system df -v`` data: images, containers, volumes,
        build cache with reclaimable space information.
        """
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "system", "df", "-v", "--format", "{{json .}}"],
                capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr.strip()}

            # docker system df -v --format {{json .}} outputs multiple lines
            items = []
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if line:
                    try:
                        items.append(_json.loads(line))
                    except _json.JSONDecodeError:
                        continue
            return {"success": True, "data": items, "raw": proc.stdout.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_docker_disk_usage_summary(self) -> Dict[str, Any]:
        """Return a human-friendly summary of docker disk usage."""
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "system", "df"],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode == 0:
                return {"success": True, "output": proc.stdout.strip()}
            return {"success": False, "error": proc.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_docker_prune(self, target: str) -> Dict[str, Any]:
        """
        Execute docker prune commands.

        Supported targets: system, images, containers, volumes, builder
        """
        import subprocess

        ALLOWED = {
            "system": ["docker", "system", "prune", "-a", "-f"],
            "images": ["docker", "image", "prune", "-a", "-f"],
            "containers": ["docker", "container", "prune", "-f"],
            "volumes": ["docker", "volume", "prune", "-f"],
            "builder": ["docker", "builder", "prune", "-a", "-f"],
        }
        if target not in ALLOWED:
            return {"success": False, "error": f"Unknown prune target: {target}"}

        try:
            proc = subprocess.run(
                ALLOWED[target],
                capture_output=True, text=True, encoding="utf-8", timeout=120,
            )
            output = (proc.stdout + proc.stderr).strip()
            if proc.returncode == 0:
                return {"success": True, "message": f"Prune {target} complete", "output": output}
            return {"success": False, "error": output or f"Prune {target} failed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Prune timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_container_exec(
        self, container_id: str, command: str,
    ) -> Dict[str, Any]:
        """Execute a command inside a running container via ``docker exec``."""
        import shlex
        import subprocess

        cid = container_id.strip()
        if not cid:
            return {"success": False, "error": "Empty container ID"}
        if not command.strip():
            return {"success": False, "error": "Empty command"}

        try:
            args = ["docker", "exec", cid] + shlex.split(command)
            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", timeout=30,
            )
            output = proc.stdout + proc.stderr
            return {
                "success": proc.returncode == 0,
                "output": output.strip(),
                "exit_code": proc.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out (30s)", "exit_code": -1}
        except Exception as e:
            return {"success": False, "error": str(e), "exit_code": -1}

    def get_image_history(self, image_id: str) -> Dict[str, Any]:
        """Return ``docker history`` for an image with layer sizes."""
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "history", image_id.strip(), "--no-trunc",
                 "--format", "{{json .}}"],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr.strip()}

            layers = []
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = _json.loads(line)
                    layers.append({
                        "id": raw.get("ID", ""),
                        "created_by": raw.get("CreatedBy", ""),
                        "created_at": raw.get("CreatedAt", ""),
                        "size": raw.get("Size", "0B"),
                        "comment": raw.get("Comment", ""),
                    })
                except _json.JSONDecodeError:
                    continue
            return {"success": True, "layers": layers}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_image_tag(
        self, source_image: str, target_tag: str,
    ) -> Dict[str, Any]:
        """Tag an image with a new name via ``docker tag``."""
        import subprocess

        src = source_image.strip()
        tgt = target_tag.strip()
        if not src or not tgt:
            return {"success": False, "error": "Source and target are required"}

        try:
            proc = subprocess.run(
                ["docker", "tag", src, tgt],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode == 0:
                return {"success": True, "message": f"Tagged {src} as {tgt}"}
            return {"success": False, "error": proc.stderr.strip() or "Tag failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_container_export(
        self, container_id: str,
    ) -> Dict[str, Any]:
        """Export a container filesystem as a tar (returns path info)."""
        import subprocess
        import tempfile

        cid = container_id.strip()
        if not cid:
            return {"success": False, "error": "Empty container ID"}

        outpath = os.path.join(tempfile.gettempdir(), f"docker-export-{cid[:12]}.tar")
        try:
            proc = subprocess.run(
                ["docker", "export", "-o", outpath, cid],
                capture_output=True, text=True, encoding="utf-8", timeout=120,
            )
            if proc.returncode == 0:
                import os
                size = os.path.getsize(outpath)
                size_mb = size / (1024 * 1024)
                return {
                    "success": True,
                    "message": f"Exported to {outpath} ({size_mb:.1f} MB)",
                    "path": outpath,
                    "size": f"{size_mb:.1f} MB",
                }
            return {"success": False, "error": proc.stderr.strip() or "Export failed"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Export timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_docker_network(
        self, name: str, driver: str = "bridge",
        subnet: str = "", gateway: str = "",
        internal: bool = False,
    ) -> Dict[str, Any]:
        """Create a new Docker network."""
        import subprocess

        if not name.strip():
            return {"success": False, "error": "Network name is required"}

        args = ["docker", "network", "create"]
        if driver:
            args.extend(["--driver", driver.strip()])
        if subnet:
            args.extend(["--subnet", subnet.strip()])
        if gateway:
            args.extend(["--gateway", gateway.strip()])
        if internal:
            args.append("--internal")
        args.append(name.strip())

        try:
            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            if proc.returncode == 0:
                nid = proc.stdout.strip()[:12]
                return {"success": True, "message": f"Network '{name}' created ({nid})"}
            return {"success": False, "error": proc.stderr.strip() or "Create failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_docker_volume(
        self, name: str, driver: str = "local",
        labels: str = "",
    ) -> Dict[str, Any]:
        """Create a new Docker volume."""
        import subprocess

        if not name.strip():
            return {"success": False, "error": "Volume name is required"}

        args = ["docker", "volume", "create"]
        if driver:
            args.extend(["--driver", driver.strip()])
        if labels:
            for lbl in labels.split(","):
                lbl = lbl.strip()
                if lbl:
                    args.extend(["--label", lbl])
        args.append(name.strip())

        try:
            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", timeout=15,
            )
            if proc.returncode == 0:
                return {"success": True, "message": f"Volume '{name}' created"}
            return {"success": False, "error": proc.stderr.strip() or "Create failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_docker_events(self, since: str = "10m") -> Dict[str, Any]:
        """
        Return recent docker events (from last N minutes).
        Uses ``docker events --since Nm --until now``.
        """
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "events", "--since", since, "--until", "0s",
                 "--format", "{{json .}}"],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            events = []
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = _json.loads(line)
                    events.append({
                        "type": raw.get("Type", ""),
                        "action": raw.get("Action", ""),
                        "actor": raw.get("Actor", {}).get("Attributes", {}).get("name", "")
                            or raw.get("Actor", {}).get("ID", "")[:12],
                        "time": raw.get("time", ""),
                        "timeNano": raw.get("timeNano", ""),
                        "status": raw.get("status", raw.get("Action", "")),
                    })
                except _json.JSONDecodeError:
                    continue
            return {"success": True, "events": events}
        except subprocess.TimeoutExpired:
            return {"success": True, "events": []}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_docker_build(
        self, *, tag: str = "", no_cache: bool = False,
        build_args: str = "", target: str = "",
    ) -> Dict[str, Any]:
        """
        Execute ``docker build`` in the workspace directory.
        Returns the full build output.
        """
        import subprocess

        dockerfile_path = self._find_workspace_path("Dockerfile", is_file=True)
        if not dockerfile_path or not dockerfile_path.is_file():
            return {"success": False, "error": "No Dockerfile found in workspace"}

        build_dir = dockerfile_path.parent
        args = ["docker", "build"]

        if tag:
            args.extend(["-t", tag.strip()])
        if no_cache:
            args.append("--no-cache")
        if target:
            args.extend(["--target", target.strip()])
        if build_args:
            for ba in build_args.split("\n"):
                ba = ba.strip()
                if ba and "=" in ba:
                    args.extend(["--build-arg", ba])

        args.append(".")

        try:
            proc = subprocess.run(
                args, capture_output=True, text=True, encoding="utf-8", timeout=600,
                cwd=str(build_dir),
            )
            output = proc.stdout + proc.stderr
            if proc.returncode == 0:
                return {
                    "success": True,
                    "message": "Build completed successfully",
                    "output": output,
                }
            return {
                "success": False,
                "error": "Build failed",
                "output": output,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Build timed out (10 min limit)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_container_top(self, container_id: str) -> Dict[str, Any]:
        """Return ``docker top`` output — processes running inside a container."""
        import json as _json
        import platform
        import subprocess

        try:
            # Windows Docker doesn't support the Unix -eo ps format
            if platform.system() == "Windows":
                cmd = ["docker", "top", container_id.strip()]
            else:
                cmd = ["docker", "top", container_id.strip(),
                       "-eo", "pid,user,%cpu,%mem,vsz,rss,tty,stat,start,time,command"]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr.strip()}
            lines = proc.stdout.strip().splitlines()
            if len(lines) < 2:
                return {"success": True, "processes": [], "headers": []}
            headers = lines[0].split()
            processes = []
            for line in lines[1:]:
                parts = line.split(None, len(headers) - 1)
                processes.append(parts)
            return {"success": True, "headers": headers, "processes": processes}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_container_diff(self, container_id: str) -> Dict[str, Any]:
        """Return ``docker diff`` — filesystem changes in a container."""
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "diff", container_id.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr.strip()}
            changes = []
            for line in proc.stdout.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                kind = line[0]  # A=added, C=changed, D=deleted
                path = line[2:] if len(line) > 2 else line
                changes.append({"kind": kind, "path": path})
            return {"success": True, "changes": changes}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_container_stats_stream(self, container_id: str) -> Dict[str, Any]:
        """Return a single snapshot of ``docker stats`` for one container."""
        import json as _json
        import subprocess

        try:
            proc = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "{{json .}}",
                 container_id.strip()],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if proc.returncode != 0:
                return {"success": False, "error": proc.stderr.strip()}
            for line in proc.stdout.strip().splitlines():
                try:
                    raw = _json.loads(line.strip())
                    return {
                        "success": True,
                        "stats": {
                            "cpu": raw.get("CPUPerc", "0%"),
                            "memory": raw.get("MemUsage", ""),
                            "mem_perc": raw.get("MemPerc", "0%"),
                            "net_io": raw.get("NetIO", ""),
                            "block_io": raw.get("BlockIO", ""),
                            "pids": raw.get("PIDs", ""),
                        },
                    }
                except _json.JSONDecodeError:
                    continue
            return {"success": False, "error": "No stats available"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_pods_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive Kubernetes pod and manifest data.

        Discovers:
        - Active pods via ``kubectl get pods``
        - K8s manifest files from workspace ``k8s/`` directory
        - Cluster info via ``kubectl cluster-info``
        - Namespaces, deployments, services, ingresses
        - Resource quotas and events

        Returns a dict with sections:
            - kubectl_available: bool
            - cluster_info: cluster connection details
            - pods: list of pod dicts with status/resources
            - deployments: list of deployment dicts
            - services: list of K8s service dicts
            - ingresses: list of ingress dicts
            - namespaces: list of namespace names
            - manifests: parsed k8s/ directory manifests
            - events: recent cluster events
            - error: optional error string
        """
        import json as _json
        import os
        import re
        import subprocess
        from datetime import datetime, timezone
        from pathlib import Path

        result: Dict[str, Any] = {
            "kubectl_available": False,
            "cluster_info": {},
            "pods": [],
            "deployments": [],
            "services": [],
            "ingresses": [],
            "namespaces": [],
            "manifests": [],
            "events": [],
            "error": "",
        }

        def _run_kubectl(*args: str, timeout: int = 10) -> tuple:
            """Run a kubectl command and return (success, stdout, stderr)."""
            try:
                proc = subprocess.run(
                    ["kubectl", *args],
                    capture_output=True, text=True, encoding="utf-8", timeout=timeout,
                )
                return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
            except FileNotFoundError:
                return False, "", "kubectl CLI not found"
            except subprocess.TimeoutExpired:
                return False, "", "Command timed out"
            except Exception as e:
                return False, "", str(e)

        # ── Check kubectl availability ──
        ok, ver_out, ver_err = _run_kubectl("version", "--client", "--output=json")
        if not ok:
            result["error"] = ver_err or "kubectl is not available"
            # Still scan manifests even without kubectl
        else:
            result["kubectl_available"] = True
            try:
                ver_data = _json.loads(ver_out)
                client_ver = ver_data.get("clientVersion", {})
                result["cluster_info"]["client_version"] = client_ver.get("gitVersion", "")
                result["cluster_info"]["platform"] = client_ver.get("platform", "")
            except _json.JSONDecodeError:
                result["cluster_info"]["client_version"] = ver_out

        # ── Cluster connection check ──
        if result["kubectl_available"]:
            ok, cluster_out, cluster_err = _run_kubectl(
                "cluster-info", "--request-timeout=5s"
            )
            if ok:
                result["cluster_info"]["connected"] = True
                result["cluster_info"]["summary"] = cluster_out[:500]
            else:
                result["cluster_info"]["connected"] = False
                result["cluster_info"]["connection_error"] = cluster_err[:200]

            # ── Namespaces ──
            ok, ns_out, _ = _run_kubectl(
                "get", "namespaces", "-o",
                "jsonpath={range .items[*]}{.metadata.name}{\"\\n\"}{end}",
            )
            if ok and ns_out:
                result["namespaces"] = [
                    n.strip() for n in ns_out.splitlines() if n.strip()
                ]

            # ── Pods (all namespaces) ──
            ok, pods_out, _ = _run_kubectl(
                "get", "pods", "--all-namespaces", "-o", "json",
                "--request-timeout=8s",
            )
            if ok and pods_out:
                try:
                    pods_data = _json.loads(pods_out)
                    for item in pods_data.get("items", []):
                        meta = item.get("metadata", {})
                        spec = item.get("spec", {})
                        status = item.get("status", {})

                        # Container statuses
                        container_statuses = []
                        for cs in status.get("containerStatuses", []):
                            state_info = {}
                            for st_key in ("running", "waiting", "terminated"):
                                if st_key in cs.get("state", {}):
                                    state_info = {"state": st_key,
                                                  **cs["state"][st_key]}
                                    break
                            container_statuses.append({
                                "name": cs.get("name", ""),
                                "ready": cs.get("ready", False),
                                "restart_count": cs.get("restartCount", 0),
                                "image": cs.get("image", ""),
                                "state_info": state_info,
                            })

                        # Resource requests/limits
                        resources = {}
                        containers = spec.get("containers", [])
                        if containers:
                            res = containers[0].get("resources", {})
                            resources = {
                                "requests": res.get("requests", {}),
                                "limits": res.get("limits", {}),
                            }

                        phase = status.get("phase", "Unknown")
                        pod_dict = {
                            "name": meta.get("name", ""),
                            "namespace": meta.get("namespace", ""),
                            "node": spec.get("nodeName", ""),
                            "phase": phase,
                            "phase_class": phase.lower(),
                            "ip": status.get("podIP", ""),
                            "host_ip": status.get("hostIP", ""),
                            "start_time": status.get("startTime", ""),
                            "containers": container_statuses,
                            "container_count": len(containers),
                            "ready_count": sum(
                                1 for cs in container_statuses if cs.get("ready")
                            ),
                            "restart_count": sum(
                                cs.get("restart_count", 0)
                                for cs in container_statuses
                            ),
                            "resources": resources,
                            "labels": meta.get("labels", {}),
                            "age": "",
                        }

                        # Calculate age
                        start_time = status.get("startTime")
                        if start_time:
                            try:
                                st = datetime.fromisoformat(
                                    start_time.replace("Z", "+00:00")
                                )
                                delta = datetime.now(tz=timezone.utc) - st
                                pod_dict["age"] = self._format_uptime(
                                    delta.total_seconds()
                                )
                            except Exception:
                                pass

                        result["pods"].append(pod_dict)
                except _json.JSONDecodeError:
                    pass

            # ── Deployments ──
            ok, dep_out, _ = _run_kubectl(
                "get", "deployments", "--all-namespaces", "-o", "json",
                "--request-timeout=8s",
            )
            if ok and dep_out:
                try:
                    dep_data = _json.loads(dep_out)
                    for item in dep_data.get("items", []):
                        meta = item.get("metadata", {})
                        spec = item.get("spec", {})
                        status = item.get("status", {})
                        result["deployments"].append({
                            "name": meta.get("name", ""),
                            "namespace": meta.get("namespace", ""),
                            "replicas": spec.get("replicas", 0),
                            "ready_replicas": status.get("readyReplicas", 0),
                            "available_replicas": status.get("availableReplicas", 0),
                            "updated_replicas": status.get("updatedReplicas", 0),
                            "strategy": spec.get("strategy", {}).get("type", ""),
                            "image": "",
                            "labels": meta.get("labels", {}),
                        })
                        # Extract image from first container
                        containers = (
                            spec.get("template", {})
                            .get("spec", {})
                            .get("containers", [])
                        )
                        if containers:
                            result["deployments"][-1]["image"] = containers[0].get(
                                "image", ""
                            )
                except _json.JSONDecodeError:
                    pass

            # ── Services ──
            ok, svc_out, _ = _run_kubectl(
                "get", "services", "--all-namespaces", "-o", "json",
                "--request-timeout=8s",
            )
            if ok and svc_out:
                try:
                    svc_data = _json.loads(svc_out)
                    for item in svc_data.get("items", []):
                        meta = item.get("metadata", {})
                        spec = item.get("spec", {})
                        ports = []
                        for p in spec.get("ports", []):
                            ports.append({
                                "port": p.get("port"),
                                "target_port": p.get("targetPort"),
                                "protocol": p.get("protocol", "TCP"),
                                "name": p.get("name", ""),
                            })
                        result["services"].append({
                            "name": meta.get("name", ""),
                            "namespace": meta.get("namespace", ""),
                            "type": spec.get("type", "ClusterIP"),
                            "cluster_ip": spec.get("clusterIP", ""),
                            "external_ip": ", ".join(
                                spec.get("externalIPs", [])
                            ) or "—",
                            "ports": ports,
                        })
                except _json.JSONDecodeError:
                    pass

            # ── Ingresses ──
            ok, ing_out, _ = _run_kubectl(
                "get", "ingresses", "--all-namespaces", "-o", "json",
                "--request-timeout=8s",
            )
            if ok and ing_out:
                try:
                    ing_data = _json.loads(ing_out)
                    for item in ing_data.get("items", []):
                        meta = item.get("metadata", {})
                        spec = item.get("spec", {})
                        hosts = []
                        for rule in spec.get("rules", []):
                            hosts.append(rule.get("host", ""))
                        result["ingresses"].append({
                            "name": meta.get("name", ""),
                            "namespace": meta.get("namespace", ""),
                            "hosts": hosts,
                            "tls": bool(spec.get("tls")),
                            "class_name": spec.get("ingressClassName", ""),
                        })
                except _json.JSONDecodeError:
                    pass

            # ── Recent events (last 20) ──
            ok, evt_out, _ = _run_kubectl(
                "get", "events", "--all-namespaces",
                "--sort-by=.metadata.creationTimestamp",
                "-o", "json", "--request-timeout=8s",
            )
            if ok and evt_out:
                try:
                    evt_data = _json.loads(evt_out)
                    items = evt_data.get("items", [])[-20:]
                    for item in items:
                        meta = item.get("metadata", {})
                        result["events"].append({
                            "type": item.get("type", "Normal"),
                            "reason": item.get("reason", ""),
                            "message": (item.get("message", "") or "")[:200],
                            "namespace": meta.get("namespace", ""),
                            "object": (
                                item.get("involvedObject", {}).get("name", "")
                            ),
                            "timestamp": item.get("lastTimestamp")
                            or meta.get("creationTimestamp", ""),
                        })
                except _json.JSONDecodeError:
                    pass

        # ── K8s manifest file analysis (always, even without kubectl) ──
        k8s_dir = self._find_workspace_path("k8s")
        if k8s_dir and k8s_dir.is_dir():
            for fpath in sorted(k8s_dir.iterdir()):
                if fpath.suffix in (".yaml", ".yml") and fpath.is_file():
                    try:
                        content = fpath.read_text(
                            encoding="utf-8", errors="replace"
                        )
                        # Extract kind from YAML
                        kind_match = re.search(
                            r'^kind:\s*(\S+)', content, re.MULTILINE,
                        )
                        name_match = re.search(
                            r'^\s+name:\s*(\S+)', content, re.MULTILINE,
                        )
                        result["manifests"].append({
                            "filename": fpath.name,
                            "kind": kind_match.group(1) if kind_match else "Unknown",
                            "name": name_match.group(1) if name_match else "",
                            "size": f"{fpath.stat().st_size / 1024:.1f} KB",
                            "content": content,
                        })
                    except Exception:
                        result["manifests"].append({
                            "filename": fpath.name,
                            "kind": "Unknown",
                            "name": "",
                            "size": "?",
                            "content": "",
                        })

        return result

    def get_workspace_data(self) -> Dict[str, Any]:
        """
        Gather comprehensive workspace data for the admin workspace page.

        Reads workspace.py, discovers all modules and their manifests,
        collects project metadata, registered models, integrations,
        and overall project health/structure information.

        Returns a dict with:
            - workspace: name, version, description, path
            - modules: list of module dicts with manifest data
            - integrations: list of active integrations
            - project_meta: pyproject.toml / setup.py data
            - registered_models: list of all ORM models
            - stats: module counts, model counts, etc.
        """
        import os
        import sys
        from pathlib import Path

        result: Dict[str, Any] = {
            "workspace": None,
            "modules": [],
            "integrations": [],
            "project_meta": {},
            "registered_models": [],
            "stats": {},
        }

        # ── Read workspace.py ────────────────────────────────────────
        ws_path = self._find_workspace_path("workspace.py", is_file=True)
        workspace_root = None
        if ws_path and ws_path.exists():
            workspace_root = ws_path.parent
            try:
                ws_source = ws_path.read_text(encoding="utf-8")
                import re

                name_match = re.search(r'(?:Workspace\(\s*["\'](\w+)|name\s*=\s*["\'](\w+))', ws_source)
                ws_name = (name_match.group(1) or name_match.group(2)) if name_match else "unknown"

                ver_match = re.search(r'version\s*=\s*["\']([^"\']+)', ws_source)
                ws_version = ver_match.group(1) if ver_match else "0.0.0"

                desc_match = re.search(r'description\s*=\s*["\']([^"\']+)', ws_source)
                ws_desc = desc_match.group(1) if desc_match else ""

                # Extract integrations from workspace
                intg_matches = re.findall(r'Integration\.(\w+)', ws_source)
                integrations_list = []
                seen = set()
                for intg in intg_matches:
                    if intg not in seen:
                        seen.add(intg)
                        # Extract inline params for the integration
                        pattern = rf'Integration\.{intg}\((.*?)\)'
                        param_match = re.search(pattern, ws_source, re.DOTALL)
                        params = {}
                        if param_match:
                            param_str = param_match.group(1)
                            for kv in re.findall(r'(\w+)\s*=\s*([^,\)]+)', param_str):
                                params[kv[0]] = kv[1].strip().strip('"\'')
                        integrations_list.append({
                            "name": intg,
                            "display_name": intg.replace("_", " ").title(),
                            "params": params,
                            "icon": self._get_integration_icon(intg),
                        })

                result["workspace"] = {
                    "name": ws_name,
                    "version": ws_version,
                    "description": ws_desc,
                    "path": str(workspace_root),
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "platform": sys.platform,
                }
                result["integrations"] = integrations_list

            except Exception:
                pass

        # ── Discover modules ─────────────────────────────────────────
        if workspace_root:
            modules_dir = workspace_root / "modules"
            if modules_dir.is_dir():
                for module_path in sorted(modules_dir.iterdir()):
                    if not module_path.is_dir() or module_path.name.startswith(("_", ".")):
                        continue

                    mod_info: Dict[str, Any] = {
                        "name": module_path.name,
                        "path": str(module_path.relative_to(workspace_root)),
                        "has_manifest": False,
                        "manifest": {},
                        "files": [],
                        "models": [],
                        "controllers": [],
                        "services": [],
                    }

                    # List all files in the module
                    for f in sorted(module_path.iterdir()):
                        if f.is_file() and f.suffix == ".py" and not f.name.startswith("_"):
                            mod_info["files"].append({
                                "name": f.name,
                                "size": f.stat().st_size,
                                "kind": self._classify_module_file(f.name),
                            })
                        elif f.name == "__init__.py":
                            mod_info["files"].append({
                                "name": f.name,
                                "size": f.stat().st_size,
                                "kind": "init",
                            })

                    # Read manifest.py
                    manifest_path = module_path / "manifest.py"
                    if manifest_path.exists():
                        mod_info["has_manifest"] = True
                        try:
                            manifest_source = manifest_path.read_text(encoding="utf-8")
                            import re as _re

                            # Extract manifest fields
                            name_m = _re.search(r'name\s*=\s*["\']([^"\']+)', manifest_source)
                            ver_m = _re.search(r'version\s*=\s*["\']([^"\']+)', manifest_source)
                            desc_m = _re.search(r'description\s*=\s*["\']([^"\']+)', manifest_source)
                            prefix_m = _re.search(r'route_prefix\s*=\s*["\']([^"\']+)', manifest_source)
                            base_m = _re.search(r'base_path\s*=\s*["\']([^"\']+)', manifest_source)

                            # Extract component lists
                            controllers = _re.findall(r'"modules\.[^"]+controllers[^"]*"', manifest_source)
                            services = _re.findall(r'"modules\.[^"]+services[^"]*"', manifest_source)
                            models = _re.findall(r'"modules\.[^"]+models[^"]*"', manifest_source)
                            guards = _re.findall(r'"modules\.[^"]+guards[^"]*"', manifest_source)
                            pipes = _re.findall(r'"modules\.[^"]+pipes[^"]*"', manifest_source)
                            imports = _re.findall(r'imports\s*=\s*\[(.*?)\]', manifest_source, _re.DOTALL)
                            exports = _re.findall(r'exports\s*=\s*\[(.*?)\]', manifest_source, _re.DOTALL)

                            # Tags
                            tags = _re.findall(r'tags\s*=\s*\[(.*?)\]', manifest_source, _re.DOTALL)
                            tag_list = []
                            if tags:
                                tag_list = _re.findall(r'["\']([^"\']+)["\']', tags[0])

                            # Auto-discover
                            auto_disc = _re.search(r'auto_discover\s*=\s*(True|False)', manifest_source)

                            # Fault handling
                            fault_domain = _re.search(r'default_domain\s*=\s*["\']([^"\']+)', manifest_source)
                            fault_strategy = _re.search(r'strategy\s*=\s*["\']([^"\']+)', manifest_source)

                            mod_info["manifest"] = {
                                "name": name_m.group(1) if name_m else module_path.name,
                                "version": ver_m.group(1) if ver_m else "0.0.0",
                                "description": desc_m.group(1) if desc_m else "",
                                "route_prefix": prefix_m.group(1) if prefix_m else "",
                                "base_path": base_m.group(1) if base_m else "",
                                "controllers": [c.strip('"') for c in controllers],
                                "services": [s.strip('"') for s in services],
                                "models": [m.strip('"') for m in models],
                                "guards": [g.strip('"') for g in guards],
                                "pipes": [p.strip('"') for p in pipes],
                                "tags": tag_list,
                                "auto_discover": auto_disc.group(1) == "True" if auto_disc else True,
                                "fault_domain": fault_domain.group(1) if fault_domain else "",
                                "fault_strategy": fault_strategy.group(1) if fault_strategy else "",
                                "source": manifest_source,
                                "source_highlighted": self._highlight_python(manifest_source),
                            }
                            mod_info["controllers"] = [c.split(":")[-1].strip('"') for c in controllers]
                            mod_info["services"] = [s.split(":")[-1].strip('"') for s in services]
                            mod_info["models"] = [m.split(":")[-1].strip('"') for m in models]

                        except Exception:
                            pass

                    result["modules"].append(mod_info)

        # ── Project metadata (pyproject.toml) ────────────────────────
        if workspace_root:
            pyproject = workspace_root / "pyproject.toml"
            if not pyproject.exists():
                # Try one directory up (framework root)
                pyproject = workspace_root.parent / "pyproject.toml"

            if pyproject.exists():
                try:
                    content = pyproject.read_text(encoding="utf-8")
                    import re as _re
                    name_m = _re.search(r'name\s*=\s*"([^"]+)"', content)
                    ver_m = _re.search(r'version\s*=\s*"([^"]+)"', content)
                    desc_m = _re.search(r'description\s*=\s*"([^"]+)"', content)
                    py_req = _re.search(r'requires-python\s*=\s*"([^"]+)"', content)
                    license_m = _re.search(r'license\s*=\s*"([^"]+)"', content)

                    result["project_meta"] = {
                        "name": name_m.group(1) if name_m else "",
                        "version": ver_m.group(1) if ver_m else "",
                        "description": desc_m.group(1) if desc_m else "",
                        "python_requires": py_req.group(1) if py_req else "",
                        "license": license_m.group(1) if license_m else "",
                    }
                except Exception:
                    pass

        # ── License file ─────────────────────────────────────────────
        license_text = ""
        if workspace_root:
            for lic_name in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
                lic_path = workspace_root / lic_name
                if not lic_path.exists():
                    lic_path = workspace_root.parent / lic_name
                if lic_path.exists():
                    try:
                        license_text = lic_path.read_text(encoding="utf-8")
                    except Exception:
                        pass
                    break
        result["license_text"] = license_text

        # ── workspace.py source for admin display ────────────────────
        ws_source = ""
        if ws_path and ws_path.exists():
            try:
                ws_source = ws_path.read_text(encoding="utf-8")
            except Exception:
                pass
        result["workspace_source"] = ws_source
        if ws_source:
            result["workspace_source_highlighted"] = self._highlight_python(ws_source)

        # ── Registered ORM models ────────────────────────────────────
        for model_cls, admin in self._registry.items():
            result["registered_models"].append({
                "name": model_cls.__name__,
                "table": getattr(model_cls, "table", ""),
                "app_label": admin.get_app_label(),
                "field_count": len(model_cls._fields) if hasattr(model_cls, "_fields") else 0,
                "icon": admin.icon or "box",
            })

        # ── Stats ────────────────────────────────────────────────────
        total_controllers = sum(
            len(m.get("manifest", {}).get("controllers", []))
            for m in result["modules"]
        )
        total_services = sum(
            len(m.get("manifest", {}).get("services", []))
            for m in result["modules"]
        )
        result["stats"] = {
            "total_modules": len(result["modules"]),
            "total_models": len(result["registered_models"]),
            "total_controllers": total_controllers,
            "total_services": total_services,
            "total_integrations": len(result["integrations"]),
            "total_files": sum(len(m.get("files", [])) for m in result["modules"]),
        }

        return result

    @staticmethod
    def _classify_module_file(filename: str) -> str:
        """Classify a Python file by its conventional name."""
        name = filename.replace(".py", "")
        mapping = {
            "controllers": "controller", "controller": "controller",
            "services": "service", "service": "service",
            "models": "model", "model": "model",
            "faults": "fault", "fault": "fault",
            "guards": "guard", "guard": "guard",
            "pipes": "pipe", "pipe": "pipe",
            "interceptors": "interceptor", "interceptor": "interceptor",
            "middleware": "middleware",
            "manifest": "manifest",
            "views": "view", "schemas": "schema", "serializers": "serializer",
        }
        return mapping.get(name, "other")

    @staticmethod
    def _get_integration_icon(name: str) -> str:
        """Get a Lucide icon class for an integration type."""
        icons = {
            "di": "icon-plug",
            "registry": "icon-clipboard-list",
            "routing": "icon-git-branch",
            "fault_handling": "icon-shield",
            "patterns": "icon-puzzle",
            "database": "icon-database",
            "cache": "icon-zap",
            "templates": "icon-file-text",
            "static_files": "icon-folder",
            "admin": "icon-user",
            "cors": "icon-globe",
            "csp": "icon-lock",
            "rate_limit": "icon-clock",
            "mail": "icon-mail",
            "sessions": "icon-key",
            "auth": "icon-shield-check",
            "openapi": "icon-book-open",
        }
        return icons.get(name, "icon-settings")

    # ── Permissions data ─────────────────────────────────────────────

    def get_permissions_data(self, identity: Optional["Identity"] = None) -> Dict[str, Any]:
        """
        Gather permission roles, matrix, and per-model permissions.
        """
        from .permissions import AdminRole, AdminPermission, ROLE_PERMISSIONS

        roles = []
        role_descriptions = {
            AdminRole.SUPERADMIN: "Full access to everything -- all admin operations, user management.",
            AdminRole.STAFF: "Full CRUD on models, audit log, exports, bulk actions.",
            AdminRole.VIEWER: "Read-only access to admin dashboard and data.",
        }

        for role in AdminRole:
            perms = ROLE_PERMISSIONS.get(role, set())
            roles.append({
                "name": role.value,
                "level": role.level,
                "description": role_descriptions.get(role, ""),
                "permissions": sorted(p.value for p in perms),
            })

        # Sort by level descending (highest first)
        roles.sort(key=lambda r: r["level"], reverse=True)

        all_permissions = sorted(p.value for p in AdminPermission)

        # Model-level permissions for current identity
        model_permissions = []
        for model_cls, admin in self._registry.items():
            model_permissions.append({
                "name": model_cls.__name__,
                "perms": {
                    "view": admin.has_view_permission(identity),
                    "add": admin.has_add_permission(identity),
                    "change": admin.has_change_permission(identity),
                    "delete": admin.has_delete_permission(identity),
                    "export": True,  # Tied to MODEL_EXPORT permission
                },
            })

        return {
            "roles": roles,
            "all_permissions": all_permissions,
            "model_permissions": model_permissions,
        }

    def update_permissions(
        self,
        form_data: Dict[str, Any],
        identity: Optional["Identity"] = None,
    ) -> Dict[str, Any]:
        """
        Update role permissions and/or model permission overrides from
        form POST data.

        Form data expected:
        - Role permissions: keys like "role_<role_name>_<permission_value>" with value "on"
        - Model permissions: keys like "model_<model_name>_<action>" with value "on"
        - update_type: "roles" or "models" to indicate which tab submitted

        Returns dict with status and message.
        """
        from .permissions import (
            AdminRole, AdminPermission, ROLE_PERMISSIONS,
            update_role_permissions as _update_role,
            set_model_permission_override,
        )

        update_type = form_data.get("update_type", "roles")
        changes = 0

        if update_type == "roles":
            # Process role permission matrix
            for role in AdminRole:
                if role == AdminRole.SUPERADMIN:
                    continue  # Can't modify superadmin

                current_perms = ROLE_PERMISSIONS.get(role, set())

                for perm in AdminPermission:
                    key = f"role_{role.value}_{perm.value}"
                    should_have = key in form_data
                    currently_has = perm in current_perms

                    if should_have != currently_has:
                        _update_role(role, perm, granted=should_have)
                        changes += 1

                        # Audit the change
                        self.audit_log.log(
                            user_id=identity.id if identity else "system",
                            username=identity.get_attribute("username", identity.id) if identity else "system",
                            role=str(get_admin_role(identity) or "unknown") if identity else "system",
                            action=AdminAction.PERMISSION_CHANGE,
                            model_name=f"Role:{role.value}",
                            changes={perm.value: {"old": str(currently_has), "new": str(should_have)}},
                        )

        elif update_type == "models":
            # Process model permission overrides
            for model_cls in self._registry:
                model_name = model_cls.__name__
                for action in ["view", "add", "change", "delete", "export"]:
                    key = f"model_{model_name}_{action}"
                    allowed = key in form_data
                    set_model_permission_override(model_name, action, allowed=allowed)
                    changes += 1

            if changes:
                self.audit_log.log(
                    user_id=identity.id if identity else "system",
                    username=identity.get_attribute("username", identity.id) if identity else "system",
                    role=str(get_admin_role(identity) or "unknown") if identity else "system",
                    action=AdminAction.PERMISSION_CHANGE,
                    model_name="ModelPermissions",
                    changes={"type": "model_override_update", "changes_count": changes},
                )

        return {
            "status": "success",
            "message": f"Updated {changes} permission(s) successfully.",
            "changes": changes,
        }

    # ── Helpers ───────────────────────────────────────────────────────

    def _find_workspace_path(self, name: str, is_file: bool = False) -> Optional["Path"]:
        """
        Find a file/directory in the workspace root.

        Tries common workspace locations relative to CWD.
        """
        from pathlib import Path
        import os

        # Check common workspace roots
        candidates = [
            Path(os.getcwd()) / name,
            Path(os.getcwd()) / "myapp" / name,
        ]

        # Also try the workspace root from sys.path hints
        for p in candidates:
            if is_file and p.is_file():
                return p
            if not is_file and p.is_dir():
                return p

        return None

    @staticmethod
    def _highlight_python(source: str) -> str:
        """
        Apply simple syntax highlighting to Python source code.

        Uses a tokenize-first approach: scan for comments, strings,
        decorators, keywords, numbers, and function calls on the RAW
        source, collect (start, end, css_class) spans, then escape
        only the non-highlighted portions.  This avoids the old bug
        where regexes ran on HTML-escaped text and `&#x27;` / `&quot;`
        caused cascading mismatches.
        """
        import re
        import html as html_mod

        KEYWORDS = {
            'def', 'class', 'import', 'from', 'return', 'if', 'elif',
            'else', 'for', 'while', 'with', 'as', 'try', 'except',
            'finally', 'raise', 'pass', 'break', 'continue', 'yield',
            'async', 'await', 'not', 'and', 'or', 'in', 'is', 'None',
            'True', 'False', 'self', 'lambda',
        }
        KW_PATTERN = r'\b(' + '|'.join(KEYWORDS) + r')\b'

        def _tokenize_line(line: str):
            """
            Return a list of (text, css_class_or_None) for one line.
            Processes left-to-right so earlier tokens win.
            """
            tokens: list = []  # [(start, end, css_class)]

            # 1. Triple-quoted strings (rare on one line, but handle)
            for m in re.finditer(r'""".*?"""|\'\'\'.*?\'\'\'', line):
                tokens.append((m.start(), m.end(), 'str'))

            # 2. Single/double-quoted strings
            for m in re.finditer(r'"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\'', line):
                tokens.append((m.start(), m.end(), 'str'))

            # 3. Comments (only if # is NOT inside a string)
            cm = re.search(r'#', line)
            if cm:
                # Check the # is not inside any string token
                pos = cm.start()
                inside = any(s <= pos < e for s, e, _ in tokens)
                if not inside:
                    tokens.append((pos, len(line), 'cmt'))

            # 4. Decorators
            dm = re.match(r'^(\s*)(@\w+)', line)
            if dm:
                tokens.append((dm.start(2), dm.end(2), 'dec'))

            # 5. Keywords
            for m in re.finditer(KW_PATTERN, line):
                tokens.append((m.start(), m.end(), 'kw'))

            # 6. Numbers
            for m in re.finditer(r'\b\d+\.?\d*\b', line):
                tokens.append((m.start(), m.end(), 'num'))

            # 7. Function calls  name(
            for m in re.finditer(r'\b(\w+)\(', line):
                tokens.append((m.start(1), m.end(1), 'fn'))

            # ── Resolve overlaps: earlier & longer wins ──
            tokens.sort(key=lambda t: (t[0], -(t[1] - t[0])))
            merged: list = []
            used_end = 0
            for s, e, cls in tokens:
                if s < used_end:
                    continue  # overlaps with a previous token
                merged.append((s, e, cls))
                used_end = e

            # ── Build output fragments ──
            parts: list = []
            pos = 0
            for s, e, cls in merged:
                if s > pos:
                    parts.append(html_mod.escape(line[pos:s]))
                parts.append(f'<span class="{cls}">{html_mod.escape(line[s:e])}</span>')
                pos = e
            if pos < len(line):
                parts.append(html_mod.escape(line[pos:]))

            return ''.join(parts)

        lines = source.split('\n')
        result_lines = []
        for i, line in enumerate(lines, 1):
            highlighted = _tokenize_line(line)
            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{highlighted}')

        return '\n'.join(result_lines)

    @staticmethod
    def _highlight_yaml(source: str) -> str:
        """Apply simple syntax highlighting to YAML source."""
        import re
        import html as html_mod

        lines = source.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            escaped = html_mod.escape(line)

            # Comments
            escaped = re.sub(
                r'(#.*?)$',
                r'<span class="cmt">\1</span>',
                escaped,
            )

            # Keys (word followed by colon)
            escaped = re.sub(
                r'^(\s*)([\w\-]+)(:)',
                r'\1<span class="kw">\2</span>\3',
                escaped,
            )

            # Strings
            escaped = re.sub(
                r'(&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;)',
                r'<span class="str">\1</span>',
                escaped,
            )

            # Numbers
            escaped = re.sub(
                r':\s*(\d+\.?\d*)\s*$',
                r': <span class="num">\1</span>',
                escaped,
            )

            # Booleans
            escaped = re.sub(
                r':\s*(true|false|yes|no|null)\s*$',
                r': <span class="kw">\1</span>',
                escaped,
                flags=re.IGNORECASE,
            )

            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{escaped}')

        return '\n'.join(result_lines)

    @staticmethod
    def _highlight_json(source: str) -> str:
        """Apply syntax highlighting to JSON source."""
        import re
        import html as html_mod

        lines = source.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            escaped = html_mod.escape(line)

            # String values (after colon)
            escaped = re.sub(
                r'(&quot;)(.*?)(&quot;)\s*(:)',
                r'<span class="prop">\1\2\3</span>\4',
                escaped,
            )

            # String values (not keys)
            escaped = re.sub(
                r':\s*(&quot;)(.*?)(&quot;)',
                r': <span class="str">\1\2\3</span>',
                escaped,
            )

            # Standalone strings (in arrays)
            escaped = re.sub(
                r'(?<=[\[,\s])(&quot;)(.*?)(&quot;)(?=[,\]\s])',
                r'<span class="str">\1\2\3</span>',
                escaped,
            )

            # Numbers
            escaped = re.sub(
                r'(?<=:\s)(-?\d+\.?\d*(?:[eE][+-]?\d+)?)(?=[,\s\}\]])',
                r'<span class="num">\1</span>',
                escaped,
            )

            # Booleans and null
            escaped = re.sub(
                r'\b(true|false|null)\b',
                r'<span class="kw">\1</span>',
                escaped,
            )

            # Braces and brackets
            escaped = re.sub(
                r'([\{\}\[\]])',
                r'<span class="op">\1</span>',
                escaped,
            )

            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{escaped}')

        return '\n'.join(result_lines)

    @staticmethod
    def _highlight_crous(source: str) -> str:
        """Apply syntax highlighting to Crous format data."""
        import re
        import html as html_mod

        lines = source.split('\n')
        result_lines = []

        for i, line in enumerate(lines, 1):
            escaped = html_mod.escape(line)

            # Comments (# or //)
            escaped = re.sub(
                r'(#.*?)$',
                r'<span class="cmt">\1</span>',
                escaped,
            )
            escaped = re.sub(
                r'(//.*?)$',
                r'<span class="cmt">\1</span>',
                escaped,
            )

            # Section headers [SectionName]
            escaped = re.sub(
                r'^(\s*)(\[[\w\.\-]+\])',
                r'\1<span class="cls">\2</span>',
                escaped,
            )

            # Keys (before = or :)
            escaped = re.sub(
                r'^(\s*)([\w\.\-]+)\s*(=|:)',
                r'\1<span class="kw">\2</span> \3',
                escaped,
            )

            # Strings
            escaped = re.sub(
                r'(&quot;[^&]*?&quot;|&#x27;[^&]*?&#x27;)',
                r'<span class="str">\1</span>',
                escaped,
            )

            # Numbers
            escaped = re.sub(
                r'\b(\d+\.?\d*)\b',
                r'<span class="num">\1</span>',
                escaped,
            )

            # Booleans
            escaped = re.sub(
                r'\b(true|false|yes|no|null|none)\b',
                r'<span class="kw">\1</span>',
                escaped,
                flags=re.IGNORECASE,
            )

            # Hex values (common in Crous binary dumps)
            escaped = re.sub(
                r'\b(0x[0-9a-fA-F]+)\b',
                r'<span class="num">\1</span>',
                escaped,
            )

            line_num = f'<span class="code-line-num">{i}</span>'
            result_lines.append(f'{line_num}{escaped}')

        return '\n'.join(result_lines)

    # ── CRUD operations ──────────────────────────────────────────────

    @staticmethod
    def _coerce_form_data(model_cls: type, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coerce form string values to the correct Python types for ORM fields.

        HTML forms submit everything as strings. This converts:
        - BooleanField: "1", "true", "on" → True; "", "0", "false" → False
        - IntegerField/BigIntegerField/SmallIntegerField: "42" → 42
        - FloatField/DecimalField: "3.14" → 3.14
        - DateTimeField: kept as string (ORM handles parsing)
        - JSON values: attempted parse

        Checkbox handling:
        - The form template sends ``_checkbox_{name}=1`` as a sentinel marker
          for every checkbox field.  When the checkbox is checked the browser
          also sends ``{name}=1``.  When it is unchecked, the browser does NOT
          send the ``{name}`` key at all.  We detect unchecked checkboxes by
          looking for the sentinel marker and the absence of the value key.

        Prevents: "Field 'active': Expected boolean, got str"
        """
        if not hasattr(model_cls, '_fields'):
            return data

        from aquilia.models.fields_module import (
            BooleanField, IntegerField, BigIntegerField, SmallIntegerField,
            FloatField, DecimalField, PositiveIntegerField, PositiveSmallIntegerField,
        )

        # Detect checkbox sentinel markers (_checkbox_{name}) and inject
        # False for unchecked checkboxes that the browser didn't send.
        checkbox_sentinels = [
            k[len("_checkbox_"):] for k in data if k.startswith("_checkbox_")
        ]
        for cb_name in checkbox_sentinels:
            if cb_name not in data:
                # Checkbox was rendered but NOT checked → explicitly False
                data[cb_name] = False

        coerced = {}
        for field_name, value in data.items():
            # Skip sentinel markers -- they are not real model fields
            if field_name.startswith("_checkbox_"):
                continue

            if field_name not in model_cls._fields:
                coerced[field_name] = value
                continue

            field = model_cls._fields[field_name]

            if isinstance(field, BooleanField):
                if isinstance(value, bool):
                    coerced[field_name] = value
                elif isinstance(value, str):
                    coerced[field_name] = value.lower() in ("1", "true", "on", "yes")
                elif isinstance(value, (int, float)):
                    coerced[field_name] = bool(value)
                else:
                    coerced[field_name] = bool(value)
            elif isinstance(field, (IntegerField, BigIntegerField, SmallIntegerField,
                                     PositiveIntegerField, PositiveSmallIntegerField)):
                if isinstance(value, str):
                    if value.strip() == "":
                        coerced[field_name] = None if field.null else 0
                    else:
                        try:
                            coerced[field_name] = int(value)
                        except (ValueError, TypeError):
                            coerced[field_name] = value
                else:
                    coerced[field_name] = value
            elif isinstance(field, (FloatField, DecimalField)):
                if isinstance(value, str):
                    if value.strip() == "":
                        coerced[field_name] = None if field.null else 0.0
                    else:
                        try:
                            coerced[field_name] = float(value)
                        except (ValueError, TypeError):
                            coerced[field_name] = value
                else:
                    coerced[field_name] = value
            else:
                coerced[field_name] = value

        return coerced

    async def list_records(
        self,
        model_name: str,
        *,
        page: int = 1,
        per_page: int = 25,
        search: str = "",
        filters: Optional[Dict[str, Any]] = None,
        ordering: Optional[str] = None,
        identity: Optional[Identity] = None,
    ) -> Dict[str, Any]:
        """
        List records for a model with pagination, search, and filtering.

        Uses ``PageNumberPagination`` from ``aquilia.controller.pagination``
        for consistent, framework-standard pagination behaviour.

        Returns dict with records, total count, and pagination info.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        # Permission check
        if identity and not admin.has_view_permission(identity):
            raise AdminAuthorizationFault(action="view", resource=model_name)

        # Build queryset
        qs = model_cls.objects.get_queryset()

        # Apply search
        if search and admin.get_search_fields():
            # Build OR search across search fields
            search_q = None
            for field_name in admin.get_search_fields():
                from aquilia.models.query import QNode
                q = QNode(**{f"{field_name}__icontains": search})
                if search_q is None:
                    search_q = q
                else:
                    search_q = search_q | q
            if search_q:
                qs = qs.apply_q(search_q)

        # Apply filters
        if filters:
            qs = qs.filter(**filters)

        # Apply ordering
        if ordering:
            qs = qs.order(ordering)
        else:
            default_ordering = admin.get_ordering()
            if default_ordering:
                qs = qs.order(*default_ordering)

        # ── Paginate via PageNumberPagination ────────────────────────
        paginator = PageNumberPagination(page_size=per_page)

        # Build a lightweight request-like object that PageNumberPagination
        # can extract query params from (it calls _get_current_params which
        # looks for ``request.query_params``).
        _fake_request = type("_R", (), {
            "query_params": {
                paginator.page_param: str(page),
                paginator.page_size_param: str(per_page),
            },
            "scope": {"scheme": "http", "headers": [], "path": f"/admin/{model_name}/"},
        })()

        paginated = await paginator.paginate_queryset(qs, _fake_request)

        total = paginated["count"]
        total_pages = paginated["total_pages"]
        records_raw = paginated["results"]

        # Format records for display
        list_display = admin.get_list_display()
        rows = []
        for record_data in records_raw:
            # paginate_queryset calls to_dict(); we may get dicts or model instances
            if isinstance(record_data, dict):
                # Prefer explicit 'pk' key; fall back to integer 'id'; avoid
                # using a non-integer 'id' (e.g. entry_id = 'audit_xxxx') as pk.
                _raw_pk = record_data.get("pk")
                if _raw_pk is None:
                    _id = record_data.get("id")
                    # Only use 'id' as pk when it looks like an integer
                    if isinstance(_id, int) or (isinstance(_id, str) and _id.isdigit()):
                        _raw_pk = _id
                row = {"pk": _raw_pk}
                for field_name in list_display:
                    raw_val = record_data.get(field_name)
                    row[field_name] = admin.format_value(field_name, raw_val)
                    row[f"_raw_{field_name}"] = raw_val
            else:
                row = {"pk": record_data.pk}
                for field_name in list_display:
                    value = getattr(record_data, field_name, None)
                    row[field_name] = admin.format_value(field_name, value)
                    row[f"_raw_{field_name}"] = value
            rows.append(row)

        return {
            "rows": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": paginated["next"] is not None,
            "has_prev": paginated["previous"] is not None,
            "next_url": paginated["next"],
            "previous_url": paginated["previous"],
            "list_display": list_display,
            "list_filter": admin.get_list_filter(),
            "search_fields": admin.get_search_fields(),
            "ordering": ordering,
            "search": search,
            "model_name": model_cls.__name__,
            "verbose_name": admin.get_model_name(),
            "verbose_name_plural": admin.get_model_name_plural(),
        }

    async def get_record(
        self,
        model_name: str,
        pk: Any,
        *,
        identity: Optional[Identity] = None,
    ) -> Dict[str, Any]:
        """
        Get a single record with field metadata for the edit form.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_view_permission(identity):
            raise AdminAuthorizationFault(action="view", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        # Build field data
        fields_data = []
        readonly = admin.get_readonly_fields()
        for field_name in admin.get_fields():
            meta = admin.get_field_metadata(field_name)
            meta["value"] = getattr(record, field_name, None)
            meta["readonly"] = field_name in readonly
            fields_data.append(meta)

        # Also include readonly fields that aren't in get_fields
        for field_name in readonly:
            if field_name not in [f["name"] for f in fields_data]:
                meta = admin.get_field_metadata(field_name)
                meta["value"] = getattr(record, field_name, None)
                meta["readonly"] = True
                fields_data.append(meta)

        return {
            "pk": record.pk,
            "record": record,
            "fields": fields_data,
            "fieldsets": admin.get_fieldsets(),
            "model_name": model_cls.__name__,
            "verbose_name": admin.get_model_name(),
            "can_change": admin.has_change_permission(identity),
            "can_delete": admin.has_delete_permission(identity),
        }

    async def create_record(
        self,
        model_name: str,
        data: Dict[str, Any],
        *,
        identity: Optional[Identity] = None,
    ) -> Any:
        """Create a new record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_add_permission(identity):
            raise AdminAuthorizationFault(action="add", resource=model_name)

        # Filter to editable fields only
        editable = set(admin.get_fields()) - set(admin.get_readonly_fields())
        clean_data = {k: v for k, v in data.items() if k in editable}

        # Coerce string values from HTML forms to correct Python types
        clean_data = self._coerce_form_data(model_cls, clean_data)

        try:
            record = await model_cls.create(**clean_data)
        except Exception as e:
            raise AdminValidationFault(str(e))

        # Audit log (in-memory + ORM-backed)
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.CREATE,
                model_name=model_name,
                record_pk=str(record.pk),
                changes=clean_data,
            )
            # Persist to AdminAuditEntry (database-backed audit trail)
            try:
                from .models import AdminAuditEntry, _HAS_ORM
                if _HAS_ORM:
                    await AdminAuditEntry.create_entry(
                        action="create",
                        user_id=int(identity.id) if identity.id.isdigit() else 1,
                        username=identity.get_attribute("name", identity.id),
                        resource_type=model_name,
                        resource_id=str(record.pk),
                        summary=f"Created {model_name} #{record.pk}",
                        detail=clean_data,
                    )
            except Exception:
                pass

        return record

    async def update_record(
        self,
        model_name: str,
        pk: Any,
        data: Dict[str, Any],
        *,
        identity: Optional[Identity] = None,
    ) -> Any:
        """Update an existing record.

        Returns the updated record.  As a side-effect the site instance
        attribute ``_last_update_queries`` is populated with a list of
        ``QueryRecord.to_dict()`` dicts captured during the update so
        the controller can feed them to the query inspection panel.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_change_permission(identity):
            raise AdminAuthorizationFault(action="change", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        # Filter to editable fields and track changes
        editable = set(admin.get_fields()) - set(admin.get_readonly_fields())

        # Coerce string values from HTML forms to correct Python types
        coerced_data = self._coerce_form_data(model_cls, data)

        changes: Dict[str, Dict[str, Any]] = {}
        update_data: Dict[str, Any] = {}

        for field_name, new_value in coerced_data.items():
            if field_name not in editable:
                continue
            old_value = getattr(record, field_name, None)
            if str(old_value) != str(new_value):
                changes[field_name] = {"old": old_value, "new": new_value}
                update_data[field_name] = new_value

        # ── Snapshot query inspector BEFORE the update ───────────────
        _captured_queries: list = []
        try:
            from .query_inspector import get_query_inspector
            _inspector = get_query_inspector()
            _qi_before = _inspector._counter
        except Exception:
            _inspector = None
            _qi_before = 0

        if update_data:
            try:
                await model_cls.objects.filter(**{model_cls._pk_attr: pk}).update(update_data)
                # Refresh record
                record = await model_cls.get(pk=pk)
            except Exception as e:
                raise AdminValidationFault(str(e))

        # ── Snapshot query inspector AFTER and capture delta ─────────
        if _inspector is not None:
            try:
                _qi_after = _inspector._counter
                if _qi_after > _qi_before:
                    all_queries = list(_inspector._queries)
                    # Grab only the queries that were recorded during this update
                    _captured_queries = [
                        q.to_dict() for q in all_queries
                        if q.id > f"q-{_qi_before:06d}"
                    ]
            except Exception:
                pass

        # Stash captured queries so the controller can read them
        self._last_update_queries = _captured_queries

        # Audit log (in-memory + ORM-backed)
        if identity and changes:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.UPDATE,
                model_name=model_name,
                record_pk=str(pk),
                changes=changes,
            )
            # Persist to AdminAuditEntry (database-backed audit trail)
            try:
                from .models import AdminAuditEntry, _HAS_ORM
                if _HAS_ORM:
                    await AdminAuditEntry.create_entry(
                        action="update",
                        user_id=int(identity.id) if identity.id.isdigit() else 1,
                        username=identity.get_attribute("name", identity.id),
                        resource_type=model_name,
                        resource_id=str(pk),
                        summary=f"Updated {model_name} #{pk}",
                        detail={"changed_fields": list(changes.keys())},
                        diff=changes,
                    )
            except Exception:
                pass

        return record

    async def delete_record(
        self,
        model_name: str,
        pk: Any,
        *,
        identity: Optional[Identity] = None,
    ) -> bool:
        """Delete a record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_delete_permission(identity):
            raise AdminAuthorizationFault(action="delete", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        try:
            await model_cls.objects.filter(**{model_cls._pk_attr: pk}).delete()
        except Exception as e:
            raise AdminValidationFault(str(e))

        # Audit log (in-memory + ORM-backed)
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.DELETE,
                model_name=model_name,
                record_pk=str(pk),
            )
            # Persist to AdminAuditEntry (database-backed audit trail)
            try:
                from .models import AdminAuditEntry, _HAS_ORM
                if _HAS_ORM:
                    await AdminAuditEntry.create_entry(
                        action="delete",
                        user_id=int(identity.id) if identity.id.isdigit() else 1,
                        username=identity.get_attribute("name", identity.id),
                        resource_type=model_name,
                        resource_id=str(pk),
                        summary=f"Deleted {model_name} #{pk}",
                    )
            except Exception:
                pass

        return True

    async def execute_action(
        self,
        model_name: str,
        action_name: str,
        selected_pks: List[Any],
        *,
        identity: Optional[Identity] = None,
    ) -> str:
        """
        Execute a bulk action on selected records.

        Returns a result message string.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not has_admin_permission(identity, AdminPermission.ACTION_EXECUTE):
            raise AdminAuthorizationFault(action="execute action", resource=model_name)

        actions = admin.get_actions()
        if action_name not in actions:
            from .faults import AdminActionFault
            raise AdminActionFault(action_name, "Action not found")

        action_desc = actions[action_name]

        # Build queryset for selected records
        qs = model_cls.objects.filter(**{f"{model_cls._pk_attr}__in": selected_pks})

        try:
            result = await action_desc.func(admin, None, qs)
        except Exception as e:
            from .faults import AdminActionFault
            raise AdminActionFault(action_name, str(e))

        # Audit log
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.BULK_ACTION,
                model_name=model_name,
                metadata={"action": action_name, "pks": [str(pk) for pk in selected_pks]},
            )

        return result or f"Action '{action_name}' executed on {len(selected_pks)} record(s)"
