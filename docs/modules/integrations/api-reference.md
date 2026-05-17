# Integrations API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `IntegrationConfig` | `aquilia/integrations/_protocol.py` | Protocol | Protocol that all typed integration configs implement. |
| `AdminModules` | `aquilia/integrations/admin.py` | object | Controls which admin pages are visible. |
| `AdminAudit` | `aquilia/integrations/admin.py` | object | Audit log configuration. |
| `AdminMonitoring` | `aquilia/integrations/admin.py` | object | Monitoring dashboard configuration. |
| `AdminSidebar` | `aquilia/integrations/admin.py` | object | Admin sidebar section visibility. |
| `AdminContainers` | `aquilia/integrations/admin.py` | object | Docker containers admin page configuration. |
| `AdminPods` | `aquilia/integrations/admin.py` | object | Kubernetes pods admin page configuration. |
| `AdminSecurity` | `aquilia/integrations/admin.py` | object | Admin dashboard security configuration (CSRF, rate-limit, passwords, headers). |
| `AdminIntegration` | `aquilia/integrations/admin.py` | object | Typed admin dashboard integration config. |
| `AuthIntegration` | `aquilia/integrations/auth.py` | object | Typed authentication integration config. |
| `CacheIntegration` | `aquilia/integrations/cache.py` | object | Typed cache subsystem configuration. |
| `DatabaseIntegration` | `aquilia/integrations/database.py` | object | Typed database integration config. |
| `I18nIntegration` | `aquilia/integrations/i18n.py` | object | Typed i18n (internationalization) configuration. |
| `LoggingIntegration` | `aquilia/integrations/logging_cfg.py` | object | Typed request logging configuration. |
| `MailAuth` | `aquilia/integrations/mail.py` | object | Mail authentication credentials. |
| `SmtpProvider` | `aquilia/integrations/mail.py` | _ProviderBase | SMTP / STARTTLS mail provider. |
| `SesProvider` | `aquilia/integrations/mail.py` | _ProviderBase | AWS Simple Email Service provider. |
| `SendGridProvider` | `aquilia/integrations/mail.py` | _ProviderBase | SendGrid Web API v3 provider. |
| `ConsoleProvider` | `aquilia/integrations/mail.py` | _ProviderBase | Console / stdout provider (development only). |
| `FileProvider` | `aquilia/integrations/mail.py` | _ProviderBase | File / .eml provider (testing & audit). |
| `MailIntegration` | `aquilia/integrations/mail.py` | object | Typed mail subsystem configuration. |
| `MLOpsIntegration` | `aquilia/integrations/mlops.py` | object | Typed MLOps platform configuration. |
| `MiddlewareEntry` | `aquilia/integrations/mw.py` | object | A single middleware entry in the chain. |
| `MiddlewareChain` | `aquilia/integrations/mw.py` | list | Fluent middleware chain builder. |
| `OpenAPIIntegration` | `aquilia/integrations/openapi.py` | object | Typed OpenAPI spec / Swagger UI configuration. |
| `RenderIntegration` | `aquilia/integrations/render.py` | object | Typed Render deployment configuration. |
| `CorsIntegration` | `aquilia/integrations/security.py` | object | Typed CORS middleware configuration. |
| `CspIntegration` | `aquilia/integrations/security.py` | object | Typed Content-Security-Policy configuration. |
| `RateLimitIntegration` | `aquilia/integrations/security.py` | object | Typed rate limiting configuration. |
| `CsrfIntegration` | `aquilia/integrations/security.py` | object | Typed CSRF protection configuration. |
| `SessionIntegration` | `aquilia/integrations/sessions.py` | object | Typed session integration config. |
| `DiIntegration` | `aquilia/integrations/simple.py` | object | Dependency injection configuration. |
| `RoutingIntegration` | `aquilia/integrations/simple.py` | object | Routing configuration. |
| `FaultHandlingIntegration` | `aquilia/integrations/simple.py` | object | Fault handling configuration. |
| `PatternsIntegration` | `aquilia/integrations/simple.py` | object | Patterns configuration. |
| `RegistryIntegration` | `aquilia/integrations/simple.py` | object | Registry configuration. |
| `SerializersIntegration` | `aquilia/integrations/simple.py` | object | Global serializer settings. |
| `StaticFilesIntegration` | `aquilia/integrations/static.py` | object | Typed static file serving configuration. |
| `StorageIntegration` | `aquilia/integrations/storage.py` | object | Typed file storage configuration. |
| `TasksIntegration` | `aquilia/integrations/tasks.py` | object | Typed background tasks configuration. |
| `TemplatesIntegration` | `aquilia/integrations/templates.py` | object | Typed template engine configuration. |
| `VersioningIntegration` | `aquilia/integrations/versioning_cfg.py` | object | Typed API versioning configuration. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| None detected |  |  |  |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_ALL_METRICS` | `aquilia/integrations/admin.py` | `['cpu', 'memory', 'disk', 'network', 'process', 'python', 'system', 'health_checks']` |
| `_ALL_CONTAINER_ACTIONS` | `aquilia/integrations/admin.py` | `['start', 'stop', 'restart', 'pause', 'unpause', 'kill', 'rm', 'logs', 'inspect', 'exec', 'export']` |
| `_ALL_K8S_RESOURCES` | `aquilia/integrations/admin.py` | `['pods', 'deployments', 'services', 'ingresses', 'configmaps', 'secrets', 'namespaces', 'events', 'daemonsets', 'statefulsets', 'jobs', 'cronjobs', 'persistentv` |

## Detailed Classes And Methods

### Class: `IntegrationConfig`

- Source: `aquilia/integrations/_protocol.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol that all typed integration configs implement.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to the flat dict consumed by ``ConfigLoader``. |

### Class: `AdminModules`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Controls which admin pages are visible.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `dashboard` | `bool` | `True` |
| `orm` | `bool` | `True` |
| `migrations` | `bool` | `True` |
| `config` | `bool` | `True` |
| `workspace` | `bool` | `True` |
| `permissions` | `bool` | `True` |
| `monitoring` | `bool` | `False` |
| `admin_users` | `bool` | `True` |
| `profile` | `bool` | `True` |
| `audit` | `bool` | `False` |
| `containers` | `bool` | `False` |
| `pods` | `bool` | `False` |
| `query_inspector` | `bool` | `False` |
| `tasks` | `bool` | `False` |
| `errors` | `bool` | `False` |
| `testing` | `bool` | `False` |
| `mlops` | `bool` | `False` |
| `storage` | `bool` | `False` |
| `mailer` | `bool` | `False` |
| `api_keys` | `bool` | `True` |
| `preferences` | `bool` | `True` |
| `provider` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `default` | `def default(cls) -> AdminModules` | classmethod | Create with default visibility. |
| `all_enabled` | `def all_enabled(cls) -> AdminModules` | classmethod | Every module enabled. |
| `all_disabled` | `def all_disabled(cls) -> AdminModules` | classmethod | Every module disabled. |
| `with_` | `def with_(self, **overrides: bool) -> AdminModules` |  | Return a copy with specific modules overridden. |
| `enable_dashboard` | `def enable_dashboard(self) -> AdminModules` |  | Method. |
| `disable_dashboard` | `def disable_dashboard(self) -> AdminModules` |  | Method. |
| `enable_orm` | `def enable_orm(self) -> AdminModules` |  | Method. |
| `disable_orm` | `def disable_orm(self) -> AdminModules` |  | Method. |
| `enable_migrations` | `def enable_migrations(self) -> AdminModules` |  | Method. |
| `disable_migrations` | `def disable_migrations(self) -> AdminModules` |  | Method. |
| `enable_config` | `def enable_config(self) -> AdminModules` |  | Method. |
| `disable_config` | `def disable_config(self) -> AdminModules` |  | Method. |
| `enable_workspace` | `def enable_workspace(self) -> AdminModules` |  | Method. |
| `disable_workspace` | `def disable_workspace(self) -> AdminModules` |  | Method. |
| `enable_permissions` | `def enable_permissions(self) -> AdminModules` |  | Method. |
| `disable_permissions` | `def disable_permissions(self) -> AdminModules` |  | Method. |
| `enable_monitoring` | `def enable_monitoring(self) -> AdminModules` |  | Method. |
| `disable_monitoring` | `def disable_monitoring(self) -> AdminModules` |  | Method. |
| `enable_admin_users` | `def enable_admin_users(self) -> AdminModules` |  | Method. |
| `disable_admin_users` | `def disable_admin_users(self) -> AdminModules` |  | Method. |
| `enable_profile` | `def enable_profile(self) -> AdminModules` |  | Method. |
| `disable_profile` | `def disable_profile(self) -> AdminModules` |  | Method. |
| `enable_containers` | `def enable_containers(self) -> AdminModules` |  | Method. |
| `disable_containers` | `def disable_containers(self) -> AdminModules` |  | Method. |
| `enable_pods` | `def enable_pods(self) -> AdminModules` |  | Method. |
| `disable_pods` | `def disable_pods(self) -> AdminModules` |  | Method. |
| `enable_audit` | `def enable_audit(self) -> AdminModules` |  | Method. |
| `disable_audit` | `def disable_audit(self) -> AdminModules` |  | Method. |
| `enable_query_inspector` | `def enable_query_inspector(self) -> AdminModules` |  | Method. |
| `disable_query_inspector` | `def disable_query_inspector(self) -> AdminModules` |  | Method. |
| `enable_tasks` | `def enable_tasks(self) -> AdminModules` |  | Method. |
| `disable_tasks` | `def disable_tasks(self) -> AdminModules` |  | Method. |
| `enable_errors` | `def enable_errors(self) -> AdminModules` |  | Method. |
| `disable_errors` | `def disable_errors(self) -> AdminModules` |  | Method. |
| `enable_testing` | `def enable_testing(self) -> AdminModules` |  | Method. |
| `disable_testing` | `def disable_testing(self) -> AdminModules` |  | Method. |
| `enable_mlops` | `def enable_mlops(self) -> AdminModules` |  | Method. |
| `disable_mlops` | `def disable_mlops(self) -> AdminModules` |  | Method. |
| `enable_storage` | `def enable_storage(self) -> AdminModules` |  | Method. |
| `disable_storage` | `def disable_storage(self) -> AdminModules` |  | Method. |
| `enable_mailer` | `def enable_mailer(self) -> AdminModules` |  | Method. |
| `disable_mailer` | `def disable_mailer(self) -> AdminModules` |  | Method. |
| `enable_provider` | `def enable_provider(self) -> AdminModules` |  | Method. |
| `disable_provider` | `def disable_provider(self) -> AdminModules` |  | Method. |
| `enable_api_keys` | `def enable_api_keys(self) -> AdminModules` |  | Method. |
| `disable_api_keys` | `def disable_api_keys(self) -> AdminModules` |  | Method. |
| `enable_preferences` | `def enable_preferences(self) -> AdminModules` |  | Method. |
| `disable_preferences` | `def disable_preferences(self) -> AdminModules` |  | Method. |
| `enable_all` | `def enable_all(self) -> AdminModules` |  | Method. |
| `disable_all` | `def disable_all(self) -> AdminModules` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, bool]` |  | Method. |

### Class: `AdminAudit`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Audit log configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `max_entries` | `int` | `10000` |
| `log_logins` | `bool` | `True` |
| `log_views` | `bool` | `True` |
| `log_searches` | `bool` | `True` |
| `excluded_actions` | `list[str]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `enable` | `def enable(self) -> AdminAudit` |  | Method. |
| `disable` | `def disable(self) -> AdminAudit` |  | Method. |
| `max_entries_set` | `def max_entries_set(self, n: int) -> AdminAudit` |  | Method. |
| `set_max_entries` | `def set_max_entries(self, n: int) -> AdminAudit` |  | Set the maximum number of audit entries (FIFO eviction). |
| `log_logins_set` | `def log_logins_set(self, enabled: bool = True) -> AdminAudit` |  | Method. |
| `no_log_logins` | `def no_log_logins(self) -> AdminAudit` |  | Method. |
| `log_views_set` | `def log_views_set(self, enabled: bool = True) -> AdminAudit` |  | Method. |
| `no_log_views` | `def no_log_views(self) -> AdminAudit` |  | Method. |
| `log_searches_set` | `def log_searches_set(self, enabled: bool = True) -> AdminAudit` |  | Method. |
| `no_log_searches` | `def no_log_searches(self) -> AdminAudit` |  | Method. |
| `exclude_actions` | `def exclude_actions(self, *actions: str) -> AdminAudit` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AdminMonitoring`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Monitoring dashboard configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `metrics` | `list[str]` | `field(default_factory=lambda: list(_ALL_METRICS))` |
| `refresh_interval` | `int` | `30` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `enable` | `def enable(self) -> AdminMonitoring` |  | Method. |
| `disable` | `def disable(self) -> AdminMonitoring` |  | Method. |
| `metrics_set` | `def metrics_set(self, *names: str) -> AdminMonitoring` |  | Method. |
| `all_metrics` | `def all_metrics(self) -> AdminMonitoring` |  | Method. |
| `refresh_interval_set` | `def refresh_interval_set(self, seconds: int) -> AdminMonitoring` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AdminSidebar`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Admin sidebar section visibility.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `overview` | `bool` | `True` |
| `data` | `bool` | `True` |
| `system` | `bool` | `True` |
| `infrastructure` | `bool` | `True` |
| `security` | `bool` | `True` |
| `models` | `bool` | `True` |
| `devtools` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `show_overview` | `def show_overview(self) -> AdminSidebar` |  | Method. |
| `hide_overview` | `def hide_overview(self) -> AdminSidebar` |  | Method. |
| `show_data` | `def show_data(self) -> AdminSidebar` |  | Method. |
| `hide_data` | `def hide_data(self) -> AdminSidebar` |  | Method. |
| `show_system` | `def show_system(self) -> AdminSidebar` |  | Method. |
| `hide_system` | `def hide_system(self) -> AdminSidebar` |  | Method. |
| `show_infrastructure` | `def show_infrastructure(self) -> AdminSidebar` |  | Method. |
| `hide_infrastructure` | `def hide_infrastructure(self) -> AdminSidebar` |  | Method. |
| `show_security` | `def show_security(self) -> AdminSidebar` |  | Method. |
| `hide_security` | `def hide_security(self) -> AdminSidebar` |  | Method. |
| `show_models` | `def show_models(self) -> AdminSidebar` |  | Method. |
| `hide_models` | `def hide_models(self) -> AdminSidebar` |  | Method. |
| `show_devtools` | `def show_devtools(self) -> AdminSidebar` |  | Method. |
| `hide_devtools` | `def hide_devtools(self) -> AdminSidebar` |  | Method. |
| `show_all` | `def show_all(self) -> AdminSidebar` |  | Method. |
| `hide_all` | `def hide_all(self) -> AdminSidebar` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, bool]` |  | Method. |

### Class: `AdminContainers`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Docker containers admin page configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `docker_host` | `str &#124; None` | `None` |
| `allowed_actions` | `list[str]` | `field(default_factory=lambda: list(_ALL_CONTAINER_ACTIONS))` |
| `denied_actions` | `list[str]` | `field(default_factory=list)` |
| `log_tail` | `int` | `200` |
| `log_since` | `str` | `''` |
| `refresh_interval` | `int` | `15` |
| `compose_files` | `list[str]` | `field(default_factory=list)` |
| `compose_project_dir` | `str &#124; None` | `None` |
| `show_system_containers` | `bool` | `False` |
| `enable_exec` | `bool` | `True` |
| `enable_prune` | `bool` | `True` |
| `enable_build` | `bool` | `True` |
| `enable_export` | `bool` | `True` |
| `enable_image_actions` | `bool` | `True` |
| `enable_volume_actions` | `bool` | `True` |
| `enable_network_actions` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `docker_socket` | `def docker_socket(self, path: str) -> AdminContainers` |  | Method. |
| `read_only` | `def read_only(self) -> AdminContainers` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AdminPods`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Kubernetes pods admin page configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `kubeconfig` | `str &#124; None` | `None` |
| `namespace` | `str` | `'default'` |
| `contexts` | `list[str]` | `field(default_factory=list)` |
| `resources` | `list[str]` | `field(default_factory=lambda: list(_ALL_K8S_RESOURCES))` |
| `manifest_dirs` | `list[str]` | `field(default_factory=lambda: ['k8s'])` |
| `manifest_patterns` | `list[str]` | `field(default_factory=lambda: ['*.yaml', '*.yml'])` |
| `refresh_interval` | `int` | `15` |
| `log_tail` | `int` | `200` |
| `enable_logs` | `bool` | `True` |
| `enable_exec` | `bool` | `True` |
| `enable_delete` | `bool` | `True` |
| `enable_scale` | `bool` | `True` |
| `enable_restart` | `bool` | `True` |
| `enable_apply` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `all_namespaces` | `def all_namespaces(self) -> AdminPods` |  | Method. |
| `read_only` | `def read_only(self) -> AdminPods` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AdminSecurity`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Admin dashboard security configuration (CSRF, rate-limit, passwords, headers).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `csrf_enabled` | `bool` | `True` |
| `csrf_max_age` | `int` | `7200` |
| `csrf_token_length` | `int` | `32` |
| `rate_limit_enabled` | `bool` | `True` |
| `rate_limit_max_attempts` | `int` | `5` |
| `rate_limit_window` | `int` | `900` |
| `sensitive_op_limit` | `int` | `30` |
| `sensitive_op_window` | `int` | `300` |
| `progressive_lockout` | `bool` | `True` |
| `lockout_tiers` | `list[list[int]] &#124; None` | `None` |
| `password_min_length` | `int` | `10` |
| `password_max_length` | `int` | `128` |
| `password_require_upper` | `bool` | `True` |
| `password_require_lower` | `bool` | `True` |
| `password_require_digit` | `bool` | `True` |
| `password_require_special` | `bool` | `True` |
| `security_headers_enabled` | `bool` | `True` |
| `csp_template` | `str &#124; None` | `None` |
| `frame_options` | `str` | `'DENY'` |
| `permissions_policy` | `str &#124; None` | `None` |
| `session_fixation_protection` | `bool` | `True` |
| `event_tracker_max_events` | `int` | `1000` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `csrf_enabled_set` | `def csrf_enabled_set(self, enabled: bool = True) -> AdminSecurity` |  | Method. |
| `no_csrf` | `def no_csrf(self) -> AdminSecurity` |  | Method. |
| `no_rate_limit` | `def no_rate_limit(self) -> AdminSecurity` |  | Method. |
| `relaxed_password_policy` | `def relaxed_password_policy(self) -> AdminSecurity` |  | Method. |
| `strict_password_policy` | `def strict_password_policy(self) -> AdminSecurity` |  | Method. |
| `no_security_headers` | `def no_security_headers(self) -> AdminSecurity` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AdminIntegration`

- Source: `aquilia/integrations/admin.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed admin dashboard integration config.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `url_prefix` | `str` | `'/admin'` |
| `site_title` | `str` | `'Aquilia Admin'` |
| `site_header` | `str` | `'Aquilia Administration'` |
| `auto_discover` | `bool` | `True` |
| `login_url` | `str &#124; None` | `None` |
| `list_per_page` | `int` | `25` |
| `theme` | `str` | `'auto'` |
| `modules` | `AdminModules &#124; None` | `None` |
| `audit` | `AdminAudit &#124; None` | `None` |
| `monitoring` | `AdminMonitoring &#124; None` | `None` |
| `sidebar` | `AdminSidebar &#124; None` | `None` |
| `containers` | `AdminContainers &#124; None` | `None` |
| `pods` | `AdminPods &#124; None` | `None` |
| `security` | `AdminSecurity &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AuthIntegration`

- Source: `aquilia/integrations/auth.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed authentication integration config.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `store_type` | `str` | `'memory'` |
| `secret_key` | `str &#124; None` | `None` |
| `algorithm` | `str` | `'HS256'` |
| `issuer` | `str` | `'aquilia'` |
| `audience` | `str` | `'aquilia-app'` |
| `access_token_ttl_minutes` | `int` | `60` |
| `refresh_token_ttl_days` | `int` | `30` |
| `require_auth_by_default` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `CacheIntegration`

- Source: `aquilia/integrations/cache.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed cache subsystem configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'memory'` |
| `default_ttl` | `int` | `300` |
| `max_size` | `int` | `10000` |
| `eviction_policy` | `str` | `'lru'` |
| `namespace` | `str` | `'default'` |
| `key_prefix` | `str` | `'aq:'` |
| `serializer` | `str` | `'json'` |
| `redis_url` | `str` | `'redis://localhost:6379/0'` |
| `redis_max_connections` | `int` | `10` |
| `l1_max_size` | `int` | `1000` |
| `l1_ttl` | `int` | `60` |
| `l2_backend` | `str` | `'redis'` |
| `middleware_enabled` | `bool` | `False` |
| `middleware_default_ttl` | `int` | `60` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `DatabaseIntegration`

- Source: `aquilia/integrations/database.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed database integration config.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `url` | `str &#124; None` | `None` |
| `config` | `Any &#124; None` | `field(default=None, repr=False)` |
| `auto_connect` | `bool` | `True` |
| `auto_create` | `bool` | `True` |
| `auto_migrate` | `bool` | `False` |
| `migrations_dir` | `str` | `'migrations'` |
| `pool_size` | `int` | `5` |
| `echo` | `bool` | `False` |
| `model_paths` | `list[str]` | `field(default_factory=list)` |
| `scan_dirs` | `list[str]` | `field(default_factory=lambda: ['models'])` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `I18nIntegration`

- Source: `aquilia/integrations/i18n.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed i18n (internationalization) configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `default_locale` | `str` | `'en'` |
| `available_locales` | `list[str]` | `field(default_factory=lambda: ['en'])` |
| `fallback_locale` | `str` | `'en'` |
| `catalog_dirs` | `list[str]` | `field(default_factory=lambda: ['locales'])` |
| `catalog_format` | `str` | `'json'` |
| `missing_key_strategy` | `str` | `'log_and_key'` |
| `auto_reload` | `bool` | `False` |
| `auto_detect` | `bool` | `True` |
| `cookie_name` | `str` | `'aq_locale'` |
| `query_param` | `str` | `'lang'` |
| `path_prefix` | `bool` | `False` |
| `resolver_order` | `list[str]` | `field(default_factory=lambda: ['query', 'cookie', 'header'])` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `LoggingIntegration`

- Source: `aquilia/integrations/logging_cfg.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed request logging configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `format` | `str` | `'%(method)s %(path)s %(status)s %(duration_ms).1fms'` |
| `level` | `str` | `'INFO'` |
| `slow_threshold_ms` | `float` | `1000.0` |
| `skip_paths` | `list[str]` | `field(default_factory=lambda: ['/health', '/healthz', '/ready', '/metrics'])` |
| `include_headers` | `bool` | `False` |
| `include_query` | `bool` | `True` |
| `include_user_agent` | `bool` | `False` |
| `log_request_body` | `bool` | `False` |
| `log_response_body` | `bool` | `False` |
| `colorize` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `MailAuth`

- Source: `aquilia/integrations/mail.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Mail authentication credentials.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `method` | `str` | `'none'` |
| `username` | `str &#124; None` | `None` |
| `password` | `str &#124; None` | `None` |
| `password_env` | `str &#124; None` | `None` |
| `domain` | `str &#124; None` | `None` |
| `api_key` | `str &#124; None` | `None` |
| `api_key_env` | `str &#124; None` | `None` |
| `aws_access_key_id` | `str &#124; None` | `None` |
| `aws_access_key_id_env` | `str &#124; None` | `None` |
| `aws_secret_access_key` | `str &#124; None` | `None` |
| `aws_secret_access_key_env` | `str &#124; None` | `None` |
| `aws_region` | `str &#124; None` | `None` |
| `aws_session_token` | `str &#124; None` | `None` |
| `access_token` | `str &#124; None` | `None` |
| `refresh_token` | `str &#124; None` | `None` |
| `token_url` | `str &#124; None` | `None` |
| `client_id` | `str &#124; None` | `None` |
| `client_secret` | `str &#124; None` | `None` |
| `client_secret_env` | `str &#124; None` | `None` |
| `scope` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `plain` | `def plain(cls, username: str, password: str &#124; None = None, *, password_env: str &#124; None = None) -> MailAuth` | classmethod | SMTP AUTH PLAIN / LOGIN. |
| `api_key` | `def api_key(cls, key: str &#124; None = None, *, env: str &#124; None = None) -> MailAuth` | classmethod | API-key auth for SendGrid, Mailgun, Postmark, etc. |
| `aws_ses` | `def aws_ses(cls, access_key_id: str &#124; None = None, secret_access_key: str &#124; None = None, region: str = 'us-east-1', session_token: str &#124; None = None, *, access_key_id_env: str &#124; None = None, secret_access_key_env: str &#124; None = None) -> MailAuth` | classmethod | AWS SES credentials. |
| `oauth2` | `def oauth2(cls, client_id: str, client_secret: str &#124; None = None, *, client_secret_env: str &#124; None = None, token_url: str, scope: str &#124; None = None, access_token: str &#124; None = None, refresh_token: str &#124; None = None) -> MailAuth` | classmethod | OAuth2 bearer-token auth (Gmail, Microsoft 365, etc.). |
| `ntlm` | `def ntlm(cls, username: str, password: str &#124; None = None, domain: str &#124; None = None, *, password_env: str &#124; None = None) -> MailAuth` | classmethod | Windows NTLM authentication. |
| `anonymous` | `def anonymous(cls) -> MailAuth` | classmethod | No authentication - open relay. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SmtpProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Decorators: `dataclass`
- Summary: SMTP / STARTTLS mail provider.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `host` | `str` | `'localhost'` |
| `port` | `int` | `587` |
| `use_tls` | `bool` | `True` |
| `use_ssl` | `bool` | `False` |
| `timeout` | `float` | `30.0` |
| `pool_size` | `int` | `3` |
| `pool_recycle` | `float` | `300.0` |
| `validate_certs` | `bool` | `True` |
| `client_cert` | `str &#124; None` | `None` |
| `client_key` | `str &#124; None` | `None` |
| `source_address` | `str &#124; None` | `None` |
| `local_hostname` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SesProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Decorators: `dataclass`
- Summary: AWS Simple Email Service provider.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `region` | `str` | `'us-east-1'` |
| `configuration_set` | `str &#124; None` | `None` |
| `source_arn` | `str &#124; None` | `None` |
| `return_path` | `str &#124; None` | `None` |
| `tags` | `dict[str, str]` | `field(default_factory=dict)` |
| `use_raw` | `bool` | `True` |
| `endpoint_url` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SendGridProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Decorators: `dataclass`
- Summary: SendGrid Web API v3 provider.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `sandbox_mode` | `bool` | `False` |
| `click_tracking` | `bool` | `True` |
| `open_tracking` | `bool` | `True` |
| `categories` | `list[str]` | `field(default_factory=list)` |
| `asm_group_id` | `int &#124; None` | `None` |
| `ip_pool_name` | `str &#124; None` | `None` |
| `template_id` | `str &#124; None` | `None` |
| `api_base_url` | `str` | `'https://api.sendgrid.com'` |
| `timeout` | `float` | `30.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `ConsoleProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Decorators: `dataclass`
- Summary: Console / stdout provider (development only).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `FileProvider`

- Source: `aquilia/integrations/mail.py`
- Bases: `_ProviderBase`
- Decorators: `dataclass`
- Summary: File / .eml provider (testing & audit).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `output_dir` | `str` | `'/tmp/aquilia_mail'` |
| `max_files` | `int` | `10000` |
| `write_index` | `bool` | `True` |
| `include_metadata` | `bool` | `True` |
| `file_extension` | `str` | `'.eml'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `MailIntegration`

- Source: `aquilia/integrations/mail.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed mail subsystem configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `default_from` | `str` | `'noreply@localhost'` |
| `default_reply_to` | `str &#124; None` | `None` |
| `subject_prefix` | `str` | `''` |
| `providers` | `list[Any]` | `field(default_factory=list)` |
| `auth` | `MailAuth &#124; None` | `None` |
| `console_backend` | `bool` | `False` |
| `preview_mode` | `bool` | `False` |
| `template_dirs` | `list[str]` | `field(default_factory=lambda: ['mail_templates'])` |
| `retry_max_attempts` | `int` | `5` |
| `retry_base_delay` | `float` | `1.0` |
| `rate_limit_global` | `int` | `1000` |
| `rate_limit_per_domain` | `int` | `100` |
| `dkim_enabled` | `bool` | `False` |
| `dkim_domain` | `str &#124; None` | `None` |
| `dkim_selector` | `str` | `'aquilia'` |
| `require_tls` | `bool` | `True` |
| `pii_redaction` | `bool` | `False` |
| `metrics_enabled` | `bool` | `True` |
| `tracing_enabled` | `bool` | `False` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `MLOpsIntegration`

- Source: `aquilia/integrations/mlops.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed MLOps platform configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `registry_db` | `str` | `'registry.db'` |
| `blob_root` | `str` | `'.aquilia-store'` |
| `storage_backend` | `str` | `'filesystem'` |
| `drift_method` | `str` | `'psi'` |
| `drift_threshold` | `float` | `0.2` |
| `drift_num_bins` | `int` | `10` |
| `max_batch_size` | `int` | `16` |
| `max_latency_ms` | `float` | `50.0` |
| `batching_strategy` | `str` | `'hybrid'` |
| `sample_rate` | `float` | `0.01` |
| `log_dir` | `str` | `'prediction_logs'` |
| `hmac_secret` | `str &#124; None` | `None` |
| `signing_private_key` | `str &#124; None` | `None` |
| `signing_public_key` | `str &#124; None` | `None` |
| `encryption_key` | `Any &#124; None` | `None` |
| `plugin_auto_discover` | `bool` | `True` |
| `scaling_policy` | `dict[str, Any] &#124; None` | `None` |
| `rollout_default_strategy` | `str` | `'canary'` |
| `auto_rollback` | `bool` | `True` |
| `metrics_model_name` | `str` | `''` |
| `metrics_model_version` | `str` | `''` |
| `cache_enabled` | `bool` | `True` |
| `cache_ttl` | `int` | `60` |
| `cache_namespace` | `str` | `'mlops'` |
| `artifact_store_dir` | `str` | `'artifacts'` |
| `fault_engine_debug` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `MiddlewareEntry`

- Source: `aquilia/integrations/mw.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single middleware entry in the chain.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `path` | `str` |  |
| `priority` | `int` | `50` |
| `scope` | `str` | `'global'` |
| `name` | `str &#124; None` | `None` |
| `kwargs` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `MiddlewareChain`

- Source: `aquilia/integrations/mw.py`
- Bases: `list`
- Summary: Fluent middleware chain builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `use` | `def use(self, path: str, *, priority: int = 50, scope: str = 'global', name: str &#124; None = None, **kwargs: Any) -> MiddlewareChain` |  | Method. |
| `to_list` | `def to_list(self) -> list[dict[str, Any]]` |  | Method. |
| `chain` | `def chain(cls) -> MiddlewareChain` | classmethod | Create an empty chain. |
| `defaults` | `def defaults(cls) -> MiddlewareChain` | classmethod | Standard development middleware chain. |
| `production` | `def production(cls) -> MiddlewareChain` | classmethod | Production-grade middleware chain. |
| `minimal` | `def minimal(cls) -> MiddlewareChain` | classmethod | Minimal middleware chain. |

### Class: `OpenAPIIntegration`

- Source: `aquilia/integrations/openapi.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed OpenAPI spec / Swagger UI configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `title` | `str` | `'Aquilia API'` |
| `version` | `str` | `'1.0.0'` |
| `description` | `str` | `''` |
| `terms_of_service` | `str` | `''` |
| `contact_name` | `str` | `''` |
| `contact_email` | `str` | `''` |
| `contact_url` | `str` | `''` |
| `license_name` | `str` | `''` |
| `license_url` | `str` | `''` |
| `servers` | `list[dict[str, str]]` | `field(default_factory=list)` |
| `docs_path` | `str` | `'/docs'` |
| `openapi_json_path` | `str` | `'/openapi.json'` |
| `redoc_path` | `str` | `'/redoc'` |
| `include_internal` | `bool` | `False` |
| `group_by_module` | `bool` | `True` |
| `infer_request_body` | `bool` | `True` |
| `infer_responses` | `bool` | `True` |
| `detect_security` | `bool` | `True` |
| `external_docs_url` | `str` | `''` |
| `external_docs_description` | `str` | `''` |
| `swagger_ui_theme` | `str` | `''` |
| `swagger_ui_config` | `dict[str, Any]` | `field(default_factory=dict)` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderIntegration`

- Source: `aquilia/integrations/render.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed Render deployment configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `service_name` | `str &#124; None` | `None` |
| `region` | `str` | `'oregon'` |
| `plan` | `str` | `'starter'` |
| `num_instances` | `int` | `1` |
| `image` | `str &#124; None` | `None` |
| `health_path` | `str` | `'/_health'` |
| `auto_deploy` | `str` | `'no'` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `CorsIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed CORS middleware configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `allow_origins` | `list[str]` | `field(default_factory=lambda: ['*'])` |
| `allow_methods` | `list[str]` | `field(default_factory=lambda: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'])` |
| `allow_headers` | `list[str]` | `field(default_factory=lambda: ['accept', 'accept-language', 'content-language', 'content-type', 'authorization', 'x-requested-with'])` |
| `expose_headers` | `list[str]` | `field(default_factory=list)` |
| `allow_credentials` | `bool` | `False` |
| `max_age` | `int` | `600` |
| `allow_origin_regex` | `str &#124; None` | `None` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `CspIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed Content-Security-Policy configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `policy` | `dict[str, list[str]] &#124; None` | `None` |
| `report_only` | `bool` | `False` |
| `nonce` | `bool` | `True` |
| `preset` | `str` | `'strict'` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RateLimitIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed rate limiting configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `limit` | `int` | `100` |
| `window` | `int` | `60` |
| `algorithm` | `str` | `'sliding_window'` |
| `per_user` | `bool` | `False` |
| `burst` | `int &#124; None` | `None` |
| `exempt_paths` | `list[str]` | `field(default_factory=lambda: ['/health', '/healthz', '/ready'])` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `CsrfIntegration`

- Source: `aquilia/integrations/security.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed CSRF protection configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `secret_key` | `str` | `''` |
| `token_length` | `int` | `32` |
| `header_name` | `str` | `'X-CSRF-Token'` |
| `field_name` | `str` | `'_csrf_token'` |
| `cookie_name` | `str` | `'_csrf_cookie'` |
| `cookie_path` | `str` | `'/'` |
| `cookie_domain` | `str &#124; None` | `None` |
| `cookie_secure` | `bool` | `True` |
| `cookie_samesite` | `str` | `'Lax'` |
| `cookie_httponly` | `bool` | `False` |
| `cookie_max_age` | `int` | `3600` |
| `safe_methods` | `list[str]` | `field(default_factory=lambda: ['GET', 'HEAD', 'OPTIONS', 'TRACE'])` |
| `exempt_paths` | `list[str]` | `field(default_factory=list)` |
| `exempt_content_types` | `list[str]` | `field(default_factory=list)` |
| `trust_ajax` | `bool` | `True` |
| `rotate_token` | `bool` | `False` |
| `failure_status` | `int` | `403` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SessionIntegration`

- Source: `aquilia/integrations/sessions.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed session integration config.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `policy` | `Any &#124; None` | `None` |
| `store` | `Any &#124; None` | `None` |
| `transport` | `Any &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `DiIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Dependency injection configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `auto_wire` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RoutingIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Routing configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `strict_matching` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `FaultHandlingIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fault handling configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `default_strategy` | `str` | `'propagate'` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `PatternsIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Patterns configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RegistryIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Registry configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SerializersIntegration`

- Source: `aquilia/integrations/simple.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Global serializer settings.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `auto_discover` | `bool` | `True` |
| `strict_validation` | `bool` | `True` |
| `raise_on_error` | `bool` | `False` |
| `date_format` | `str` | `'iso-8601'` |
| `datetime_format` | `str` | `'iso-8601'` |
| `coerce_decimal_to_string` | `bool` | `True` |
| `compact_json` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `StaticFilesIntegration`

- Source: `aquilia/integrations/static.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed static file serving configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `directories` | `dict[str, str]` | `field(default_factory=lambda: {'/static': 'static'})` |
| `cache_max_age` | `int` | `86400` |
| `immutable` | `bool` | `False` |
| `etag` | `bool` | `True` |
| `gzip` | `bool` | `True` |
| `brotli` | `bool` | `True` |
| `memory_cache` | `bool` | `True` |
| `html5_history` | `bool` | `False` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `StorageIntegration`

- Source: `aquilia/integrations/storage.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed file storage configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `default` | `str` | `'default'` |
| `backends` | `dict[str, Any] &#124; None` | `None` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `TasksIntegration`

- Source: `aquilia/integrations/tasks.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed background tasks configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `backend` | `str` | `'memory'` |
| `num_workers` | `int` | `4` |
| `default_queue` | `str` | `'default'` |
| `cleanup_interval` | `float` | `300.0` |
| `cleanup_max_age` | `float` | `3600.0` |
| `max_retries` | `int` | `3` |
| `retry_delay` | `float` | `1.0` |
| `retry_backoff` | `float` | `2.0` |
| `retry_max_delay` | `float` | `300.0` |
| `default_timeout` | `float` | `300.0` |
| `auto_start` | `bool` | `True` |
| `dead_letter_max` | `int` | `1000` |
| `scheduler_tick` | `float` | `15.0` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `TemplatesIntegration`

- Source: `aquilia/integrations/templates.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed template engine configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `search_paths` | `list[str]` | `field(default_factory=lambda: ['templates'])` |
| `cache` | `str` | `'memory'` |
| `sandbox` | `bool` | `True` |
| `sandbox_policy` | `str` | `'strict'` |
| `precompile` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `builder` | `def builder(cls) -> _Builder` | classmethod | Start a fluent builder. |
| `source` | `def source(cls, *paths: str) -> _Builder` | classmethod | Start builder with source paths. |
| `defaults` | `def defaults(cls) -> _Builder` | classmethod | Start with default configuration. |

### Class: `VersioningIntegration`

- Source: `aquilia/integrations/versioning_cfg.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed API versioning configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `strategy` | `str` | `'header'` |
| `versions` | `list[str]` | `field(default_factory=list)` |
| `default_version` | `str &#124; None` | `None` |
| `require_version` | `bool` | `False` |
| `header_name` | `str` | `'X-API-Version'` |
| `query_param` | `str` | `'api_version'` |
| `url_prefix` | `str` | `'v'` |
| `url_segment_index` | `int` | `0` |
| `strip_version_from_path` | `bool` | `True` |
| `media_type_param` | `str` | `'version'` |
| `channels` | `dict[str, str]` | `field(default_factory=dict)` |
| `channel_header` | `str` | `'X-API-Channel'` |
| `channel_query_param` | `str` | `'api_channel'` |
| `negotiation_mode` | `str` | `'exact'` |
| `sunset_policy` | `Any &#124; None` | `None` |
| `sunset_schedules` | `dict[str, dict[str, Any]] &#124; None` | `None` |
| `include_version_header` | `bool` | `True` |
| `response_header_name` | `str` | `'X-API-Version'` |
| `include_supported_versions_header` | `bool` | `True` |
| `neutral_paths` | `list[str]` | `field(default_factory=lambda: ['/_health', '/openapi.json', '/docs', '/redoc'])` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |


## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_ALL_METRICS` | `aquilia/integrations/admin.py` | `['cpu', 'memory', 'disk', 'network', 'process', 'python', 'system', 'health_checks']` |
| `_ALL_CONTAINER_ACTIONS` | `aquilia/integrations/admin.py` | `['start', 'stop', 'restart', 'pause', 'unpause', 'kill', 'rm', 'logs', 'inspect', 'exec', 'export']` |
| `_ALL_K8S_RESOURCES` | `aquilia/integrations/admin.py` | `['pods', 'deployments', 'services', 'ingresses', 'configmaps', 'secrets', 'namespaces', 'events', 'daemonsets', 'statefulsets', 'jobs', 'cronjobs', 'persistentv` |
