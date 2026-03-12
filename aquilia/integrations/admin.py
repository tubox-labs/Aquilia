"""
Admin integration — typed admin dashboard configuration.

Replaces the bloated ``Integration.AdminModules`` (44 methods for 22
booleans) with a clean dataclass + ``with_()`` method for fluent
partial overrides.

Before (old)::

    modules = (
        Integration.AdminModules()
        .enable_orm()
        .enable_monitoring()
        .disable_build()
    )

After (new)::

    modules = AdminModules(orm=True, monitoring=True, build=False)
    # or fluent:
    modules = AdminModules.default().with_(monitoring=True, build=False)
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from dataclasses import fields as dc_fields
from typing import Any

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminModules
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class AdminModules:
    """
    Controls which admin pages are visible.

    All modules default to ``True`` except monitoring, audit, containers,
    pods, query_inspector, tasks, errors, testing, mlops, storage, mailer,
    and provider which default to ``False`` (opt-in).

    Example::

        AdminModules(monitoring=True, audit=True, build=False)
    """

    dashboard: bool = True
    orm: bool = True
    build: bool = True
    migrations: bool = True
    config: bool = True
    workspace: bool = True
    permissions: bool = True
    monitoring: bool = False
    admin_users: bool = True
    profile: bool = True
    audit: bool = False
    containers: bool = False
    pods: bool = False
    query_inspector: bool = False
    tasks: bool = False
    errors: bool = False
    testing: bool = False
    mlops: bool = False
    storage: bool = False
    mailer: bool = False
    api_keys: bool = True
    preferences: bool = True
    provider: bool = False

    @classmethod
    def default(cls) -> AdminModules:
        """Create with default visibility."""
        return cls()

    @classmethod
    def all_enabled(cls) -> AdminModules:
        """Every module enabled."""
        return cls(**{f.name: True for f in dc_fields(cls)})

    @classmethod
    def all_disabled(cls) -> AdminModules:
        """Every module disabled."""
        return cls(**{f.name: False for f in dc_fields(cls)})

    def with_(self, **overrides: bool) -> AdminModules:
        """Return a copy with specific modules overridden."""
        return replace(self, **overrides)

    # ── Legacy fluent API (backward compat) ──────────────────────────

    def enable_dashboard(self) -> AdminModules:
        self.dashboard = True
        return self

    def disable_dashboard(self) -> AdminModules:
        self.dashboard = False
        return self

    def enable_orm(self) -> AdminModules:
        self.orm = True
        return self

    def disable_orm(self) -> AdminModules:
        self.orm = False
        return self

    def enable_build(self) -> AdminModules:
        self.build = True
        return self

    def disable_build(self) -> AdminModules:
        self.build = False
        return self

    def enable_migrations(self) -> AdminModules:
        self.migrations = True
        return self

    def disable_migrations(self) -> AdminModules:
        self.migrations = False
        return self

    def enable_config(self) -> AdminModules:
        self.config = True
        return self

    def disable_config(self) -> AdminModules:
        self.config = False
        return self

    def enable_workspace(self) -> AdminModules:
        self.workspace = True
        return self

    def disable_workspace(self) -> AdminModules:
        self.workspace = False
        return self

    def enable_permissions(self) -> AdminModules:
        self.permissions = True
        return self

    def disable_permissions(self) -> AdminModules:
        self.permissions = False
        return self

    def enable_monitoring(self) -> AdminModules:
        self.monitoring = True
        return self

    def disable_monitoring(self) -> AdminModules:
        self.monitoring = False
        return self

    def enable_admin_users(self) -> AdminModules:
        self.admin_users = True
        return self

    def disable_admin_users(self) -> AdminModules:
        self.admin_users = False
        return self

    def enable_profile(self) -> AdminModules:
        self.profile = True
        return self

    def disable_profile(self) -> AdminModules:
        self.profile = False
        return self

    def enable_containers(self) -> AdminModules:
        self.containers = True
        return self

    def disable_containers(self) -> AdminModules:
        self.containers = False
        return self

    def enable_pods(self) -> AdminModules:
        self.pods = True
        return self

    def disable_pods(self) -> AdminModules:
        self.pods = False
        return self

    def enable_audit(self) -> AdminModules:
        self.audit = True
        return self

    def disable_audit(self) -> AdminModules:
        self.audit = False
        return self

    def enable_query_inspector(self) -> AdminModules:
        self.query_inspector = True
        return self

    def disable_query_inspector(self) -> AdminModules:
        self.query_inspector = False
        return self

    def enable_tasks(self) -> AdminModules:
        self.tasks = True
        return self

    def disable_tasks(self) -> AdminModules:
        self.tasks = False
        return self

    def enable_errors(self) -> AdminModules:
        self.errors = True
        return self

    def disable_errors(self) -> AdminModules:
        self.errors = False
        return self

    def enable_testing(self) -> AdminModules:
        self.testing = True
        return self

    def disable_testing(self) -> AdminModules:
        self.testing = False
        return self

    def enable_mlops(self) -> AdminModules:
        self.mlops = True
        return self

    def disable_mlops(self) -> AdminModules:
        self.mlops = False
        return self

    def enable_storage(self) -> AdminModules:
        self.storage = True
        return self

    def disable_storage(self) -> AdminModules:
        self.storage = False
        return self

    def enable_mailer(self) -> AdminModules:
        self.mailer = True
        return self

    def disable_mailer(self) -> AdminModules:
        self.mailer = False
        return self

    def enable_provider(self) -> AdminModules:
        self.provider = True
        return self

    def disable_provider(self) -> AdminModules:
        self.provider = False
        return self

    def enable_api_keys(self) -> AdminModules:
        self.api_keys = True
        return self

    def disable_api_keys(self) -> AdminModules:
        self.api_keys = False
        return self

    def enable_preferences(self) -> AdminModules:
        self.preferences = True
        return self

    def disable_preferences(self) -> AdminModules:
        self.preferences = False
        return self

    def enable_all(self) -> AdminModules:
        for f in dc_fields(self):
            setattr(self, f.name, True)
        return self

    def disable_all(self) -> AdminModules:
        for f in dc_fields(self):
            setattr(self, f.name, False)
        return self

    def to_dict(self) -> dict[str, bool]:
        return {f.name: getattr(self, f.name) for f in dc_fields(self)}

    def __repr__(self) -> str:
        enabled = [k for k, v in self.to_dict().items() if v]
        return f"AdminModules(enabled={enabled})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminAudit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class AdminAudit:
    """
    Audit log configuration.

    Example::

        AdminAudit(enabled=True, max_entries=50_000, log_views=False)
    """

    enabled: bool = False
    max_entries: int = 10_000
    log_logins: bool = True
    log_views: bool = True
    log_searches: bool = True
    excluded_actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.max_entries = max(100, self.max_entries)

    # ── Legacy fluent API ────────────────────────────────────────────

    def enable(self) -> AdminAudit:
        self.enabled = True
        return self

    def disable(self) -> AdminAudit:
        self.enabled = False
        return self

    def max_entries_set(self, n: int) -> AdminAudit:
        self.max_entries = max(100, int(n))
        return self

    # Keep old name for backward compat
    def set_max_entries(self, n: int) -> AdminAudit:  # type: ignore[override]
        """Set the maximum number of audit entries (FIFO eviction)."""
        self._max_entries_val = max(100, int(n))
        # Since max_entries is also a field, we need a workaround:
        object.__setattr__(self, "max_entries", self._max_entries_val)
        return self

    def log_logins_set(self, enabled: bool = True) -> AdminAudit:
        self.log_logins = enabled
        return self

    def no_log_logins(self) -> AdminAudit:
        self.log_logins = False
        return self

    def log_views_set(self, enabled: bool = True) -> AdminAudit:
        self.log_views = enabled
        return self

    def no_log_views(self) -> AdminAudit:
        self.log_views = False
        return self

    def log_searches_set(self, enabled: bool = True) -> AdminAudit:
        self.log_searches = enabled
        return self

    def no_log_searches(self) -> AdminAudit:
        self.log_searches = False
        return self

    def exclude_actions(self, *actions: str) -> AdminAudit:
        self.excluded_actions = list(actions)
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_entries": self.max_entries if isinstance(self.max_entries, int) else 10_000,
            "log_logins": self.log_logins,
            "log_views": self.log_views,
            "log_searches": self.log_searches,
            "excluded_actions": list(self.excluded_actions),
        }

    def __repr__(self) -> str:
        state = "enabled" if self.enabled else "disabled"
        return f"AdminAudit({state})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminMonitoring
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


_ALL_METRICS = [
    "cpu",
    "memory",
    "disk",
    "network",
    "process",
    "python",
    "system",
    "health_checks",
]


@dataclass
class AdminMonitoring:
    """
    Monitoring dashboard configuration.

    Example::

        AdminMonitoring(enabled=True, metrics=["cpu", "memory"], refresh_interval=15)
    """

    enabled: bool = False
    metrics: list[str] = field(default_factory=lambda: list(_ALL_METRICS))
    refresh_interval: int = 30

    def __post_init__(self) -> None:
        self.refresh_interval = max(5, self.refresh_interval)

    # ── Legacy fluent API ────────────────────────────────────────────

    def enable(self) -> AdminMonitoring:
        self.enabled = True
        return self

    def disable(self) -> AdminMonitoring:
        self.enabled = False
        return self

    def metrics_set(self, *names: str) -> AdminMonitoring:
        self.metrics = list(names) if names else list(_ALL_METRICS)
        return self

    def all_metrics(self) -> AdminMonitoring:
        self.metrics = list(_ALL_METRICS)
        return self

    def refresh_interval_set(self, seconds: int) -> AdminMonitoring:
        self.refresh_interval = max(5, int(seconds))
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "metrics": list(self.metrics),
            "refresh_interval": self.refresh_interval,
        }

    def __repr__(self) -> str:
        state = "enabled" if self.enabled else "disabled"
        return f"AdminMonitoring({state}, metrics={self.metrics})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminSidebar
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class AdminSidebar:
    """
    Admin sidebar section visibility.

    Example::

        AdminSidebar(security=False, devtools=True)
    """

    overview: bool = True
    data: bool = True
    system: bool = True
    infrastructure: bool = True
    security: bool = True
    models: bool = True
    devtools: bool = True

    # ── Legacy fluent API ────────────────────────────────────────────

    def show_overview(self) -> AdminSidebar:
        self.overview = True
        return self

    def hide_overview(self) -> AdminSidebar:
        self.overview = False
        return self

    def show_data(self) -> AdminSidebar:
        self.data = True
        return self

    def hide_data(self) -> AdminSidebar:
        self.data = False
        return self

    def show_system(self) -> AdminSidebar:
        self.system = True
        return self

    def hide_system(self) -> AdminSidebar:
        self.system = False
        return self

    def show_infrastructure(self) -> AdminSidebar:
        self.infrastructure = True
        return self

    def hide_infrastructure(self) -> AdminSidebar:
        self.infrastructure = False
        return self

    def show_security(self) -> AdminSidebar:
        self.security = True
        return self

    def hide_security(self) -> AdminSidebar:
        self.security = False
        return self

    def show_models(self) -> AdminSidebar:
        self.models = True
        return self

    def hide_models(self) -> AdminSidebar:
        self.models = False
        return self

    def show_devtools(self) -> AdminSidebar:
        self.devtools = True
        return self

    def hide_devtools(self) -> AdminSidebar:
        self.devtools = False
        return self

    def show_all(self) -> AdminSidebar:
        for f in dc_fields(self):
            setattr(self, f.name, True)
        return self

    def hide_all(self) -> AdminSidebar:
        for f in dc_fields(self):
            setattr(self, f.name, False)
        return self

    def to_dict(self) -> dict[str, bool]:
        return {f.name: getattr(self, f.name) for f in dc_fields(self)}

    def __repr__(self) -> str:
        visible = [k for k, v in self.to_dict().items() if v]
        return f"AdminSidebar(visible={visible})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminContainers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_ALL_CONTAINER_ACTIONS = [
    "start",
    "stop",
    "restart",
    "pause",
    "unpause",
    "kill",
    "rm",
    "logs",
    "inspect",
    "exec",
    "export",
]


@dataclass
class AdminContainers:
    """
    Docker containers admin page configuration.

    Example::

        AdminContainers(
            docker_host="unix:///var/run/docker.sock",
            log_tail=500,
            refresh_interval=10,
        )
    """

    docker_host: str | None = None
    allowed_actions: list[str] = field(default_factory=lambda: list(_ALL_CONTAINER_ACTIONS))
    denied_actions: list[str] = field(default_factory=list)
    log_tail: int = 200
    log_since: str = ""
    refresh_interval: int = 15
    compose_files: list[str] = field(default_factory=list)
    compose_project_dir: str | None = None
    show_system_containers: bool = False
    enable_exec: bool = True
    enable_prune: bool = True
    enable_build: bool = True
    enable_export: bool = True
    enable_image_actions: bool = True
    enable_volume_actions: bool = True
    enable_network_actions: bool = True

    # ── Legacy fluent API ────────────────────────────────────────────

    def docker_socket(self, path: str) -> AdminContainers:
        self.docker_host = f"unix://{path}"
        return self

    def read_only(self) -> AdminContainers:
        self.allowed_actions = ["logs", "inspect"]
        self.enable_exec = False
        self.enable_prune = False
        self.enable_build = False
        self.enable_export = False
        self.enable_image_actions = False
        self.enable_volume_actions = False
        self.enable_network_actions = False
        return self

    def to_dict(self) -> dict[str, Any]:
        effective = [a for a in self.allowed_actions if a not in self.denied_actions]
        return {
            "docker_host": self.docker_host,
            "allowed_actions": effective,
            "log_tail": self.log_tail,
            "log_since": self.log_since,
            "refresh_interval": self.refresh_interval,
            "compose_files": self.compose_files,
            "compose_project_dir": self.compose_project_dir,
            "show_system_containers": self.show_system_containers,
            "capabilities": {
                "exec": self.enable_exec,
                "prune": self.enable_prune,
                "build": self.enable_build,
                "export": self.enable_export,
                "image_actions": self.enable_image_actions,
                "volume_actions": self.enable_volume_actions,
                "network_actions": self.enable_network_actions,
            },
        }

    def __repr__(self) -> str:
        return f"AdminContainers(host={self.docker_host!r}, refresh={self.refresh_interval}s)"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminPods
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_ALL_K8S_RESOURCES = [
    "pods",
    "deployments",
    "services",
    "ingresses",
    "configmaps",
    "secrets",
    "namespaces",
    "events",
    "daemonsets",
    "statefulsets",
    "jobs",
    "cronjobs",
    "persistentvolumeclaims",
    "nodes",
]


@dataclass
class AdminPods:
    """
    Kubernetes pods admin page configuration.

    Example::

        AdminPods(namespace="production", refresh_interval=15)
    """

    kubeconfig: str | None = None
    namespace: str = "default"
    contexts: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=lambda: list(_ALL_K8S_RESOURCES))
    manifest_dirs: list[str] = field(default_factory=lambda: ["k8s"])
    manifest_patterns: list[str] = field(default_factory=lambda: ["*.yaml", "*.yml"])
    refresh_interval: int = 15
    log_tail: int = 200
    enable_logs: bool = True
    enable_exec: bool = True
    enable_delete: bool = True
    enable_scale: bool = True
    enable_restart: bool = True
    enable_apply: bool = True

    # ── Legacy fluent API ────────────────────────────────────────────

    def all_namespaces(self) -> AdminPods:
        self.namespace = "*"
        return self

    def read_only(self) -> AdminPods:
        self.enable_exec = False
        self.enable_delete = False
        self.enable_scale = False
        self.enable_restart = False
        self.enable_apply = False
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "kubeconfig": self.kubeconfig,
            "namespace": self.namespace,
            "contexts": self.contexts,
            "resources": self.resources,
            "manifest_dirs": self.manifest_dirs,
            "manifest_patterns": self.manifest_patterns,
            "refresh_interval": self.refresh_interval,
            "log_tail": self.log_tail,
            "capabilities": {
                "logs": self.enable_logs,
                "exec": self.enable_exec,
                "delete": self.enable_delete,
                "scale": self.enable_scale,
                "restart": self.enable_restart,
                "apply": self.enable_apply,
            },
        }

    def __repr__(self) -> str:
        return f"AdminPods(ns={self.namespace!r}, refresh={self.refresh_interval}s)"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminSecurity
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class AdminSecurity:
    """
    Admin dashboard security configuration (CSRF, rate-limit, passwords, headers).

    Example::

        AdminSecurity(
            csrf_enabled=True,
            rate_limit_max_attempts=5,
            password_min_length=12,
        )
    """

    # CSRF
    csrf_enabled: bool = True
    csrf_max_age: int = 7200
    csrf_token_length: int = 32
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_max_attempts: int = 5
    rate_limit_window: int = 900
    sensitive_op_limit: int = 30
    sensitive_op_window: int = 300
    # Progressive lockout
    progressive_lockout: bool = True
    lockout_tiers: list[list[int]] | None = None
    # Password policy
    password_min_length: int = 10
    password_max_length: int = 128
    password_require_upper: bool = True
    password_require_lower: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    # Security headers
    security_headers_enabled: bool = True
    csp_template: str | None = None
    frame_options: str = "DENY"
    permissions_policy: str | None = None
    # Session
    session_fixation_protection: bool = True
    # Event tracking
    event_tracker_max_events: int = 1000

    # ── Legacy fluent API ────────────────────────────────────────────

    def csrf_enabled_set(self, enabled: bool = True) -> AdminSecurity:
        self.csrf_enabled = enabled
        return self

    def no_csrf(self) -> AdminSecurity:
        self.csrf_enabled = False
        return self

    def no_rate_limit(self) -> AdminSecurity:
        self.rate_limit_enabled = False
        return self

    def relaxed_password_policy(self) -> AdminSecurity:
        self.password_min_length = 8
        self.password_require_upper = False
        self.password_require_lower = False
        self.password_require_digit = False
        self.password_require_special = False
        return self

    def strict_password_policy(self) -> AdminSecurity:
        self.password_min_length = 12
        self.password_require_upper = True
        self.password_require_lower = True
        self.password_require_digit = True
        self.password_require_special = True
        return self

    def no_security_headers(self) -> AdminSecurity:
        self.security_headers_enabled = False
        return self

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "csrf": {
                "enabled": self.csrf_enabled,
                "max_age": self.csrf_max_age,
                "token_length": self.csrf_token_length,
            },
            "rate_limit": {
                "enabled": self.rate_limit_enabled,
                "max_login_attempts": self.rate_limit_max_attempts,
                "login_window": self.rate_limit_window,
                "sensitive_op_limit": self.sensitive_op_limit,
                "sensitive_op_window": self.sensitive_op_window,
                "progressive_lockout": self.progressive_lockout,
            },
            "password": {
                "min_length": self.password_min_length,
                "max_length": self.password_max_length,
                "require_upper": self.password_require_upper,
                "require_lower": self.password_require_lower,
                "require_digit": self.password_require_digit,
                "require_special": self.password_require_special,
            },
            "headers": {
                "enabled": self.security_headers_enabled,
                "frame_options": self.frame_options,
            },
            "session_fixation_protection": self.session_fixation_protection,
            "event_tracker_max_events": self.event_tracker_max_events,
        }
        if self.lockout_tiers is not None:
            result["rate_limit"]["lockout_tiers"] = self.lockout_tiers
        if self.csp_template is not None:
            result["headers"]["csp_template"] = self.csp_template
        if self.permissions_policy is not None:
            result["headers"]["permissions_policy"] = self.permissions_policy
        return result

    def __repr__(self) -> str:
        parts = []
        if self.csrf_enabled:
            parts.append("csrf")
        if self.rate_limit_enabled:
            parts.append("rate_limit")
        if self.security_headers_enabled:
            parts.append("headers")
        return f"AdminSecurity({', '.join(parts) or 'minimal'})"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AdminIntegration  (top-level)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class AdminIntegration:
    """
    Typed admin dashboard integration config.

    Example::

        AdminIntegration(
            site_title="My Admin",
            modules=AdminModules(monitoring=True, audit=True),
            security=AdminSecurity(password_min_length=12),
        )
    """

    _integration_type: str = field(default="admin", init=False, repr=False)

    url_prefix: str = "/admin"
    site_title: str = "Aquilia Admin"
    site_header: str = "Aquilia Administration"
    auto_discover: bool = True
    login_url: str | None = None
    list_per_page: int = 25
    theme: str = "auto"
    modules: AdminModules | None = None
    audit: AdminAudit | None = None
    monitoring: AdminMonitoring | None = None
    sidebar: AdminSidebar | None = None
    containers: AdminContainers | None = None
    pods: AdminPods | None = None
    security: AdminSecurity | None = None

    def to_dict(self) -> dict[str, Any]:
        mod_dict = (self.modules or AdminModules()).to_dict()
        audit_dict = (self.audit or AdminAudit()).to_dict()
        mon_dict = (self.monitoring or AdminMonitoring()).to_dict()
        sidebar_dict = (self.sidebar or AdminSidebar()).to_dict()
        containers_dict = (self.containers or AdminContainers()).to_dict()
        pods_dict = (self.pods or AdminPods()).to_dict()
        security_dict = (self.security or AdminSecurity()).to_dict()

        # Sync module flags with sub-config enabled states
        if self.audit is not None:
            mod_dict["audit"] = audit_dict.get("enabled", False)
        if self.monitoring is not None:
            mod_dict["monitoring"] = mon_dict.get("enabled", False)

        prefix = self.url_prefix.rstrip("/")
        return {
            "_integration_type": "admin",
            "enabled": True,
            "url_prefix": prefix,
            "site_title": self.site_title,
            "site_header": self.site_header,
            "auto_discover": self.auto_discover,
            "login_url": self.login_url or f"{prefix}/login",
            "enable_audit": audit_dict.get("enabled", False),
            "audit_max_entries": audit_dict.get("max_entries", 10_000),
            "list_per_page": self.list_per_page,
            "theme": self.theme,
            "modules": mod_dict,
            "audit_config": audit_dict,
            "monitoring_config": mon_dict,
            "containers_config": containers_dict,
            "pods_config": pods_dict,
            "security_config": security_dict,
            "sidebar_sections": sidebar_dict,
        }
