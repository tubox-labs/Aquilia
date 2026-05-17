# Admin API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `AdminAction` | `aquilia/admin/audit.py` | str, Enum | Admin action types for audit logging. |
| `AdminAuditEntry` | `aquilia/admin/audit.py` | object | Immutable audit log entry. |
| `CrousAuditStore` | `aquilia/admin/audit.py` | object | Thin persistence layer that stores/loads audit entries using the CROUS |
| `AdminAuditLog` | `aquilia/admin/audit.py` | object | Admin audit log -- records all admin operations. |
| `ModelBackedAuditLog` | `aquilia/admin/audit.py` | object | Model-backed audit log -- persists entries to the AdminAuditEntry ORM table. |
| `AdminController` | `aquilia/admin/controller.py` | Controller | Aquilia Admin Controller. |
| `ErrorRecord` | `aquilia/admin/error_tracker.py` | object | Captured error with full context. |
| `ErrorGroup` | `aquilia/admin/error_tracker.py` | object | Aggregated error group (same fingerprint). |
| `ErrorTracker` | `aquilia/admin/error_tracker.py` | object | Central error tracking system. |
| `ExportFormat` | `aquilia/admin/export.py` | Enum | Supported export formats. |
| `Exporter` | `aquilia/admin/export.py` | object | Base exporter class. |
| `CSVExporter` | `aquilia/admin/export.py` | Exporter | Export data as CSV. |
| `JSONExporter` | `aquilia/admin/export.py` | Exporter | Export data as JSON array. |
| `XMLExporter` | `aquilia/admin/export.py` | Exporter | Export data as XML. |
| `ExportRegistry` | `aquilia/admin/export.py` | object | Registry of available export formats. |
| `AdminFault` | `aquilia/admin/faults.py` | Fault | Base fault for all admin operations. |
| `AdminAuthenticationFault` | `aquilia/admin/faults.py` | AdminFault | Admin authentication failed. |
| `AdminAuthorizationFault` | `aquilia/admin/faults.py` | AdminFault | Admin authorization failed -- insufficient permissions. |
| `AdminSecurityFault` | `aquilia/admin/faults.py` | AdminFault | Base fault for admin security violations. |
| `AdminCSRFViolationFault` | `aquilia/admin/faults.py` | AdminSecurityFault | CSRF token validation failed. |
| `AdminRateLimitFault` | `aquilia/admin/faults.py` | AdminSecurityFault | Rate limit exceeded for admin operation. |
| `AdminModelNotFoundFault` | `aquilia/admin/faults.py` | AdminFault | Requested model is not registered with admin. |
| `AdminRecordNotFoundFault` | `aquilia/admin/faults.py` | AdminFault | Record not found in database. |
| `AdminValidationFault` | `aquilia/admin/faults.py` | AdminFault | Validation error when creating/updating records. |
| `AdminActionFault` | `aquilia/admin/faults.py` | AdminFault | Bulk action execution failed. |
| `AdminConfigurationFault` | `aquilia/admin/faults.py` | AdminFault | Admin system misconfiguration or missing dependency. |
| `AdminRegistrationFault` | `aquilia/admin/faults.py` | AdminFault | Model registration error. |
| `AdminInlineFault` | `aquilia/admin/faults.py` | AdminFault | Inline model configuration error. |
| `AdminTemplateFault` | `aquilia/admin/faults.py` | AdminFault | Template rendering error. |
| `AdminExportFault` | `aquilia/admin/faults.py` | AdminFault | Export generation error. |
| `ListFilter` | `aquilia/admin/filters.py` | object | Base class for admin list view filters. |
| `SimpleFilter` | `aquilia/admin/filters.py` | ListFilter | Filter by exact field value. |
| `BooleanFilter` | `aquilia/admin/filters.py` | ListFilter | Filter for boolean fields with Yes/No/All choices. |
| `ChoiceFilter` | `aquilia/admin/filters.py` | ListFilter | Filter with explicitly defined choices. |
| `DateRangeFilter` | `aquilia/admin/filters.py` | ListFilter | Date range filter with preset periods and custom range support. |
| `NumericRangeFilter` | `aquilia/admin/filters.py` | ListFilter | Numeric range filter with min/max inputs. |
| `AllValuesFilter` | `aquilia/admin/filters.py` | ListFilter | Filter showing all distinct values found in the database. |
| `RelatedModelFilter` | `aquilia/admin/filters.py` | ListFilter | Filter for ForeignKey fields using related model's __str__. |
| `EmptyFieldFilter` | `aquilia/admin/filters.py` | ListFilter | Filter to find records where a field is empty/null or not. |
| `AdminHooksMixin` | `aquilia/admin/hooks.py` | object | Mixin providing lifecycle hook methods for ModelAdmin. |
| `SoftDeleteMixin` | `aquilia/admin/hooks.py` | object | Mixin for soft-delete support in ModelAdmin. |
| `VersioningMixin` | `aquilia/admin/hooks.py` | object | Mixin for automatic version tracking on save. |
| `TimestampMixin` | `aquilia/admin/hooks.py` | object | Mixin for automatic timestamp management. |
| `InlineModelAdmin` | `aquilia/admin/inlines.py` | object | Base class for inline model editing within a parent form. |
| `TabularInline` | `aquilia/admin/inlines.py` | InlineModelAdmin | Inline rendered as a compact table with one row per record. |
| `StackedInline` | `aquilia/admin/inlines.py` | InlineModelAdmin | Inline rendered as a full form stacked vertically. |
| `ContentType` | `aquilia/admin/models.py` | object | Stub - Aquilia does not use a ContentType indirection table. |
| `AdminPermission` | `aquilia/admin/models.py` | object | Stub - permissions live in ``permissions.py`` as an in-memory enum. |
| `AdminGroup` | `aquilia/admin/models.py` | object | Stub - roles are defined in ``permissions.AdminRole``. |
| `AdminLogEntry` | `aquilia/admin/models.py` | object | Stub - use :class:`AdminAuditEntry` instead. |
| `AdminSession` | `aquilia/admin/models.py` | object | Stub - sessions are managed by ``aquilia.sessions`` at the framework level. |
| `AdminActionDescriptor` | `aquilia/admin/options.py` | object | Describes a bulk action available in the admin list view. |
| `ModelAdmin` | `aquilia/admin/options.py` | object | Declarative admin configuration for a model. |
| `AdminRole` | `aquilia/admin/permissions.py` | str, Enum | Built-in admin roles with hierarchical permissions. |
| `AdminPermission` | `aquilia/admin/permissions.py` | str, Enum | Fine-grained admin permissions. |
| `QueryRecord` | `aquilia/admin/query_inspector.py` | object | Single captured query with profiling data. |
| `N1Detection` | `aquilia/admin/query_inspector.py` | object | Detected N+1 query pattern. |
| `QueryInspector` | `aquilia/admin/query_inspector.py` | object | Central query profiler and inspector. |
| `AdminCSRFProtection` | `aquilia/admin/security.py` | object | CSRF protection specifically for the admin panel. |
| `AdminRateLimiter` | `aquilia/admin/security.py` | object | Rate limiter for admin authentication and sensitive operations. |
| `AdminSecurityHeaders` | `aquilia/admin/security.py` | object | Applies security headers to all admin responses. |
| `PasswordStrength` | `aquilia/admin/security.py` | object | Result of password complexity analysis. |
| `PasswordValidator` | `aquilia/admin/security.py` | object | Password complexity validator for admin accounts. |
| `SecurityEvent` | `aquilia/admin/security.py` | object | Immutable record of a security-relevant event. |
| `SecurityEventTracker` | `aquilia/admin/security.py` | object | Tracks security events for monitoring and alerting. |
| `AdminSecurityPolicy` | `aquilia/admin/security.py` | object | Central orchestrator for all admin security features. |
| `AdminConfig` | `aquilia/admin/site.py` | object | Immutable admin configuration parsed from ``Integration.admin()`` config dict. |
| `AdminSite` | `aquilia/admin/site.py` | object | Central admin site -- manages all registered models. |
| `AdminCacheIntegration` | `aquilia/admin/subsystems.py` | object | Integrates Aquilia CacheService into admin operations. |
| `AdminDBEffect` | `aquilia/admin/subsystems.py` | object | Typed effect token for admin database operations. |
| `AdminCacheEffect` | `aquilia/admin/subsystems.py` | object | Typed effect token for admin cache operations. |
| `AdminTaskEffect` | `aquilia/admin/subsystems.py` | object | Typed effect token for admin background task dispatch. |
| `AdminTasks` | `aquilia/admin/subsystems.py` | object | Background tasks for admin housekeeping. |
| `AdminAuthGuard` | `aquilia/admin/subsystems.py` | object | Flow guard that verifies admin authentication. |
| `AdminPermGuard` | `aquilia/admin/subsystems.py` | object | Flow guard that checks model-level permissions. |
| `AdminCSRFGuard` | `aquilia/admin/subsystems.py` | object | Flow guard that validates CSRF tokens for POST/PUT/DELETE requests. |
| `AdminRateLimitGuard` | `aquilia/admin/subsystems.py` | object | Flow guard that enforces rate limits on admin requests. |
| `AdminAuditHook` | `aquilia/admin/subsystems.py` | object | Flow hook that logs admin actions to the audit trail. |
| `AdminLifecycle` | `aquilia/admin/subsystems.py` | object | Admin lifecycle hooks for integration with Aquilia's LifecycleCoordinator. |
| `AdminSubsystems` | `aquilia/admin/subsystems.py` | object | Central orchestrator for all admin subsystem integrations. |
| `WidgetSize` | `aquilia/admin/widgets.py` | Enum | Widget size on the dashboard grid. |
| `WidgetPosition` | `aquilia/admin/widgets.py` | Enum | Widget placement section. |
| `AdminWidget` | `aquilia/admin/widgets.py` | object | Base class for dashboard widgets. |
| `CountWidget` | `aquilia/admin/widgets.py` | AdminWidget | Displays a count of records in a model. |
| `StatWidget` | `aquilia/admin/widgets.py` | AdminWidget | Displays a single statistic value with trend. |
| `ChartWidget` | `aquilia/admin/widgets.py` | AdminWidget | Displays a chart (line, bar, pie, doughnut, area). |
| `RecentActivityWidget` | `aquilia/admin/widgets.py` | AdminWidget | Displays recent admin activity log entries. |
| `TableWidget` | `aquilia/admin/widgets.py` | AdminWidget | Displays a data table on the dashboard. |
| `ListWidget` | `aquilia/admin/widgets.py` | AdminWidget | Displays a simple list of items on the dashboard. |
| `ProgressWidget` | `aquilia/admin/widgets.py` | AdminWidget | Displays a progress bar or set of progress bars. |
| `CustomHTMLWidget` | `aquilia/admin/widgets.py` | AdminWidget | Widget that renders custom HTML content. |
| `WidgetRegistry` | `aquilia/admin/widgets.py` | object | Registry for dashboard widgets. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `provide_admin_site` | `aquilia/admin/di_providers.py` | `def provide_admin_site() -> AdminSite` | Provide the default AdminSite singleton. |
| `provide_admin_controller` | `aquilia/admin/di_providers.py` | `def provide_admin_controller(site: AdminSite &#124; None = None) -> AdminController` | Provide an AdminController bound to the given or default site. |
| `provide_audit_log` | `aquilia/admin/di_providers.py` | `def provide_audit_log(site: AdminSite &#124; None = None) -> AdminAuditLog` | Provide the audit log from the current AdminSite. |
| `provide_model_backed_audit_log` | `aquilia/admin/di_providers.py` | `def provide_model_backed_audit_log() -> ModelBackedAuditLog` | Provide a ModelBackedAuditLog instance. |
| `register_admin_providers` | `aquilia/admin/di_providers.py` | `def register_admin_providers(container: Container) -> None` | Register all admin DI providers with the given container. |
| `get_error_tracker` | `aquilia/admin/error_tracker.py` | `def get_error_tracker() -> ErrorTracker` | Get or create the global ErrorTracker instance. |
| `resolve_filter` | `aquilia/admin/filters.py` | `def resolve_filter(filter_spec: Any, model: type[Model] &#124; None = None) -> ListFilter` | Resolve a filter specification into a ListFilter instance. |
| `action` | `aquilia/admin/options.py` | `def action(short_description: str = '', confirmation: str = '', permission: str = '')` | Decorator to mark a method as an admin action. |
| `get_admin_role` | `aquilia/admin/permissions.py` | `def get_admin_role(identity: Identity &#124; None) -> AdminRole &#124; None` | Determine the admin role for an identity. |
| `has_admin_permission` | `aquilia/admin/permissions.py` | `def has_admin_permission(identity: Identity &#124; None, permission: AdminPermission) -> bool` | Check if an identity has a specific admin permission. |
| `has_model_permission` | `aquilia/admin/permissions.py` | `def has_model_permission(identity: Identity &#124; None, model_name: str, action: str) -> bool` | Check if an identity can perform an action on a model. |
| `require_admin_access` | `aquilia/admin/permissions.py` | `def require_admin_access(identity: Identity &#124; None) -> None` | Raise AdminAuthorizationFault if identity has no admin access. |
| `update_role_permissions` | `aquilia/admin/permissions.py` | `def update_role_permissions(role: AdminRole, permission: AdminPermission, *, granted: bool) -> None` | Grant or revoke a specific permission for a role at runtime. |
| `set_model_permission_override` | `aquilia/admin/permissions.py` | `def set_model_permission_override(model_name: str, action: str, *, allowed: bool) -> None` | Set a per-model permission override. |
| `get_model_permission_overrides` | `aquilia/admin/permissions.py` | `def get_model_permission_overrides() -> dict[str, dict[str, bool]]` | Return the current model permission overrides. |
| `clear_model_permission_overrides` | `aquilia/admin/permissions.py` | `def clear_model_permission_overrides(model_name: str &#124; None = None) -> None` | Clear model permission overrides. |
| `get_query_inspector` | `aquilia/admin/query_inspector.py` | `def get_query_inspector() -> QueryInspector` | Get or create the global QueryInspector instance. |
| `register` | `aquilia/admin/registry.py` | `def register(model_or_admin: Any = None, *, site: AdminSite &#124; None = None) -> Callable` | Register a model or ModelAdmin with the admin site. |
| `autodiscover` | `aquilia/admin/registry.py` | `def autodiscover() -> dict[str, type[Model]]` | Auto-discover and register all models from ModelRegistry. |
| `flush_pending_registrations` | `aquilia/admin/registry.py` | `def flush_pending_registrations() -> int` | Flush any pending registrations to the default AdminSite. |
| `register_security_providers` | `aquilia/admin/security.py` | `def register_security_providers(container: Any, config: dict[str, Any] &#124; None = None) -> None` | Register admin security components with the DI container. |
| `build_admin_flow_pipeline` | `aquilia/admin/subsystems.py` | `def build_admin_flow_pipeline(security_policy: Any &#124; None = None, model_name: str = '', action: str = 'view', require_auth: bool = True, require_csrf: bool = False, rate_limit_op: str &#124; None = None) -> dict[str, Any]` | Build a standard admin flow pipeline configuration. |
| `get_admin_subsystems` | `aquilia/admin/subsystems.py` | `def get_admin_subsystems() -> AdminSubsystems` | Get the default AdminSubsystems instance. |
| `render_login_page` | `aquilia/admin/templates.py` | `def render_login_page(error: str = '', *, csrf_token: str = '', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the admin login page. |
| `render_dashboard` | `aquilia/admin/templates.py` | `def render_dashboard(app_list: list[dict[str, Any]], stats: dict[str, Any], identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin', containers_summary: dict[str, Any] &#124; None = None, pods_summary: dict[str, Any] &#124; None = None, orm_metadata: dict[str, Any] &#124; None = None, error_stats: dict[str, Any] &#124; None = None, tasks_stats: dict[str, Any] &#124; None = None, mlops_summary: dict[str, Any] &#124; None = None, storage_summary: dict[str, Any] &#124; None = None) -> str` | Render the admin dashboard. |
| `render_list_view` | `aquilia/admin/templates.py` | `def render_list_view(data: dict[str, Any], app_list: list[dict[str, Any]], identity_name: str = 'Admin', identity_avatar: str = '', flash: str = '', flash_type: str = 'success', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the model list view with table, search, pagination. |
| `render_form_view` | `aquilia/admin/templates.py` | `def render_form_view(data: dict[str, Any], app_list: list[dict[str, Any]], identity_name: str = 'Admin', identity_avatar: str = '', is_create: bool = False, flash: str = '', flash_type: str = 'success', query_inspection: list[dict[str, Any]] &#124; None = None, *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the add/edit form view. |
| `render_audit_page` | `aquilia/admin/templates.py` | `def render_audit_page(entries: list[dict[str, Any]], app_list: list[dict[str, Any]], identity_name: str = 'Admin', identity_avatar: str = '', total: int = 0, page: int = 1, per_page: int = 50, total_pages: int = 1, *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the audit log page. |
| `render_orm_page` | `aquilia/admin/templates.py` | `def render_orm_page(app_list: list[dict[str, Any]], model_counts: dict[str, Any], identity_name: str = 'Admin', identity_avatar: str = '', model_schema: list[dict[str, Any]] &#124; None = None, orm_metadata: dict[str, Any] &#124; None = None, *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the ORM models page with schema inspector and relation graph. |
| `render_migrations_page` | `aquilia/admin/templates.py` | `def render_migrations_page(migrations: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the migrations page with syntax highlighted source. |
| `render_config_page` | `aquilia/admin/templates.py` | `def render_config_page(config_files: list[dict[str, Any]], workspace_info: dict[str, Any] &#124; None = None, app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the configuration page with YAML file contents. |
| `render_workspace_page` | `aquilia/admin/templates.py` | `def render_workspace_page(workspace: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the workspace monitoring page. |
| `render_permissions_page` | `aquilia/admin/templates.py` | `def render_permissions_page(roles: list[dict[str, Any]], all_permissions: list[str], model_permissions: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', flash: str = '', flash_type: str = 'success', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the permissions page with role matrix. |
| `render_monitoring_page` | `aquilia/admin/templates.py` | `def render_monitoring_page(monitoring: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the application monitoring page with system metrics and charts. |
| `render_containers_page` | `aquilia/admin/templates.py` | `def render_containers_page(containers_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the containers page with Docker Desktop-like container management. |
| `render_pods_page` | `aquilia/admin/templates.py` | `def render_pods_page(pods_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the pods page with Kubernetes pod tracking and manifest viewer. |
| `render_storage_page` | `aquilia/admin/templates.py` | `def render_storage_page(storage_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the storage admin page with backend analytics and file browser. |
| `render_admin_users_page` | `aquilia/admin/templates.py` | `def render_admin_users_page(users: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the admin-users management page with hierarchy, roles, and creation form. |
| `render_profile_page` | `aquilia/admin/templates.py` | `def render_profile_page(user: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the admin profile management page. |
| `render_api_keys_page` | `aquilia/admin/templates.py` | `def render_api_keys_page(keys: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the API keys management page. |
| `render_preferences_page` | `aquilia/admin/templates.py` | `def render_preferences_page(preferences: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the user preferences management page. |
| `render_forbidden_page` | `aquilia/admin/templates.py` | `def render_forbidden_page(module_name: str = 'this page', required_permission: str = '', current_role: str = '', app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render a styled 403 Forbidden page when a user lacks permissions. |
| `render_error_page` | `aquilia/admin/templates.py` | `def render_error_page(status: int = 404, title: str = 'Not Found', message: str = '', app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render a styled admin error page (404, 403, 400, etc.). |
| `render_disabled_page` | `aquilia/admin/templates.py` | `def render_disabled_page(module_name: str, builder_hint: str = '', flat_hint: str = '', icon_key: str = '', description: str = '', app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render a beautiful blurred overlay page for disabled admin modules. |
| `render_query_inspector_page` | `aquilia/admin/templates.py` | `def render_query_inspector_page(query_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin', qi_page: int = 1, qi_per_page: int = 30, qi_total: int = 0, qi_total_pages: int = 1) -> str` | Render the live query inspector page with SQL profiling and N+1 detection. |
| `render_provider_page` | `aquilia/admin/templates.py` | `def render_provider_page(provider_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the comprehensive provider & deployment administration page. |
| `render_mailer_page` | `aquilia/admin/templates.py` | `def render_mailer_page(mailer_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the comprehensive mail administration page. |
| `render_tasks_page` | `aquilia/admin/templates.py` | `def render_tasks_page(tasks_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the background tasks monitor page with Chart.js analytics. |
| `render_errors_page` | `aquilia/admin/templates.py` | `def render_errors_page(errors_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the error monitoring page with Chart.js analytics. |
| `render_mlops_page` | `aquilia/admin/templates.py` | `def render_mlops_page(mlops_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the MLOps admin page with comprehensive analytics. |
| `render_testing_page` | `aquilia/admin/templates.py` | `def render_testing_page(testing_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the testing framework admin page with Chart.js analytics. |
| `get_widget_registry` | `aquilia/admin/widgets.py` | `def get_widget_registry() -> WidgetRegistry` | Get the default widget registry. |
| `register_widget` | `aquilia/admin/widgets.py` | `def register_widget(widget: AdminWidget) -> AdminWidget` | Register a widget to the default registry. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CSP_NONCE_PLACEHOLDER` | `aquilia/admin/controller.py` | `'__CSP_NONCE__'` |
| `_ALLOWED_IMAGE_TYPES` | `aquilia/admin/controller.py` | `dict[bytes, tuple]` |
| `_MAX_AVATAR_BYTES` | `aquilia/admin/controller.py` | `4 * 1024 * 1024` |
| `ADMIN_DOMAIN` | `aquilia/admin/faults.py` | `FaultDomain.custom('ADMIN', 'Admin dashboard faults')` |
| `API_KEY_PREFIX` | `aquilia/admin/models.py` | `'aq_'` |
| `API_KEY_ENTROPY` | `aquilia/admin/models.py` | `32` |
| `DEFAULT_ROLE` | `aquilia/admin/models.py` | `'staff'` |
| `VALID_ROLES` | `aquilia/admin/models.py` | `('superadmin', 'staff', 'viewer')` |
| `_ROLE_CHECK_SQL` | `aquilia/admin/models.py` | `"role IN ('superadmin', 'staff', 'viewer')"` |
| `_HAS_ORM` | `aquilia/admin/models.py` | `_ORM_AVAILABLE` |
| `ROLE_PERMISSIONS` | `aquilia/admin/permissions.py` | `dict[AdminRole, set[AdminPermission]]` |
| `_MODEL_PERMISSION_OVERRIDES` | `aquilia/admin/permissions.py` | `dict[str, dict[str, bool]]` |
| `_TEMPLATES_DIR` | `aquilia/admin/templates.py` | `Path(__file__).resolve().parent / 'templates'` |
| `_HAS_JINJA2` | `aquilia/admin/templates.py` | `False` |
| `ADMIN_CSS` | `aquilia/admin/templates.py` | `''` |
| `_FALLBACK_CSS` | `aquilia/admin/templates.py` | `'\n:root{--bg-primary:#02040a;--bg-card:#09090b;--bg-input:#18181b;--border-color:#27272a;\n--accent:#22c55e;--accent-hover:#16a34a;--accent-glow:rgba(34,197,94` |

## Detailed Classes And Methods

### Class: `AdminAction`

- Source: `aquilia/admin/audit.py`
- Bases: `str, Enum`
- Summary: Admin action types for audit logging.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `LOGIN` |  | `'login'` |
| `LOGOUT` |  | `'logout'` |
| `LOGIN_FAILED` |  | `'login_failed'` |
| `VIEW` |  | `'view'` |
| `LIST` |  | `'list'` |
| `CREATE` |  | `'create'` |
| `UPDATE` |  | `'update'` |
| `DELETE` |  | `'delete'` |
| `BULK_ACTION` |  | `'bulk_action'` |
| `EXPORT` |  | `'export'` |
| `SEARCH` |  | `'search'` |
| `SETTINGS_CHANGE` |  | `'settings_change'` |
| `PERMISSION_CHANGE` |  | `'permission_change'` |
| `PAGE_VIEW` |  | `'page_view'` |
| `ADMIN_USER_CREATE` |  | `'admin_user_create'` |
| `ADMIN_USER_UPDATE` |  | `'admin_user_update'` |
| `ADMIN_USER_DELETE` |  | `'admin_user_delete'` |
| `CONTAINER_ACTION` |  | `'container_action'` |
| `CONTAINER_EXEC` |  | `'container_exec'` |
| `CONTAINER_EXPORT` |  | `'container_export'` |
| `DOCKER_PRUNE` |  | `'docker_prune'` |
| `DOCKER_BUILD` |  | `'docker_build'` |
| `IMAGE_ACTION` |  | `'image_action'` |
| `IMAGE_TAG` |  | `'image_tag'` |
| `COMPOSE_ACTION` |  | `'compose_action'` |
| `VOLUME_ACTION` |  | `'volume_action'` |
| `VOLUME_CREATE` |  | `'volume_create'` |
| `NETWORK_ACTION` |  | `'network_action'` |
| `NETWORK_CREATE` |  | `'network_create'` |
| `FILE_UPLOAD` |  | `'file_upload'` |
| `FILE_DELETE` |  | `'file_delete'` |
| `FILE_DOWNLOAD` |  | `'file_download'` |
| `PROFILE_UPDATE` |  | `'profile_update'` |
| `AVATAR_UPLOAD` |  | `'avatar_upload'` |
| `PASSWORD_CHANGE` |  | `'password_change'` |
| `ML_INFERENCE` |  | `'ml_inference'` |
| `ML_BATCH_INFERENCE` |  | `'ml_batch_inference'` |
| `ML_COMPARE` |  | `'ml_compare'` |
| `ML_HEALTH_CHECK` |  | `'ml_health_check'` |
| `ALERT_CONFIG` |  | `'alert_config'` |
| `SNAPSHOT_EXPORT` |  | `'snapshot_export'` |
| `API_KEY_CREATE` |  | `'api_key_create'` |
| `API_KEY_REVOKE` |  | `'api_key_revoke'` |
| `API_KEY_DELETE` |  | `'api_key_delete'` |
| `PREFERENCE_UPDATE` |  | `'preference_update'` |
| `PREFERENCE_DELETE` |  | `'preference_delete'` |

### Class: `AdminAuditEntry`

- Source: `aquilia/admin/audit.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable audit log entry.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` |  |
| `timestamp` | `datetime` |  |
| `user_id` | `str` |  |
| `username` | `str` |  |
| `role` | `str` |  |
| `action` | `AdminAction` |  |
| `model_name` | `str &#124; None` | `None` |
| `record_pk` | `str &#124; None` | `None` |
| `changes` | `dict[str, Any] &#124; None` | `None` |
| `ip_address` | `str &#124; None` | `None` |
| `user_agent` | `str &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `success` | `bool` | `True` |
| `error_message` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |
| `from_dict` | `def from_dict(data: dict[str, Any]) -> AdminAuditEntry` | staticmethod | Reconstruct an entry from a serialized dictionary. |

### Class: `CrousAuditStore`

- Source: `aquilia/admin/audit.py`
- Bases: `object`
- Summary: Thin persistence layer that stores/loads audit entries using the CROUS

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `persist` | `def persist(self, entry: AdminAuditEntry) -> None` |  | Append a single audit entry to the .crous file. |
| `load_all` | `def load_all(self) -> list[AdminAuditEntry]` |  | Load all persisted entries from the .crous file. |
| `load_for_record` | `def load_for_record(self, model_name: str, record_pk: str) -> list[AdminAuditEntry]` |  | Load only entries matching a specific model + pk (case-insensitive). |
| `clear` | `def clear(self) -> None` |  | Remove the .crous audit file. |
| `truncate` | `def truncate(self, keep: int = 10000) -> None` |  | Keep only the *keep* most recent entries. |

### Class: `AdminAuditLog`

- Source: `aquilia/admin/audit.py`
- Bases: `object`
- Summary: Admin audit log -- records all admin operations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `log` | `def log(self, user_id: str, username: str, role: str, action: AdminAction, *, model_name: str &#124; None = None, record_pk: str &#124; None = None, changes: dict[str, Any] &#124; None = None, ip_address: str &#124; None = None, user_agent: str &#124; None = None, metadata: dict[str, Any] &#124; None = None, success: bool = True, error_message: str &#124; None = None) -> AdminAuditEntry` |  | Record an admin action. |
| `get_entries` | `def get_entries(self, *, action: AdminAction &#124; None = None, user_id: str &#124; None = None, model_name: str &#124; None = None, limit: int = 50, offset: int = 0) -> list[AdminAuditEntry]` |  | Query audit entries with optional filtering. |
| `count` | `def count(self, *, action: AdminAction &#124; None = None, model_name: str &#124; None = None) -> int` |  | Count audit entries with optional filtering. |
| `clear` | `def clear(self) -> int` |  | Clear all audit entries. Returns count cleared. |
| `get_history_for_record` | `def get_history_for_record(self, model_name: str, record_pk: str) -> list[AdminAuditEntry]` |  | Return all audit entries for a specific model + pk, newest-first. |

### Class: `ModelBackedAuditLog`

- Source: `aquilia/admin/audit.py`
- Bases: `object`
- Summary: Model-backed audit log -- persists entries to the AdminAuditEntry ORM table.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `admin_config` | `def admin_config(self)` | property | Method. |
| `admin_config` | `def admin_config(self, value)` | admin_config.setter | Method. |
| `start` | `def start(self) -> None` |  | Enable CROUS hydration and load persisted entries. |
| `log` | `def log(self, user_id: str, username: str, role: str, action: AdminAction, *, model_name: str &#124; None = None, record_pk: str &#124; None = None, changes: dict[str, Any] &#124; None = None, ip_address: str &#124; None = None, user_agent: str &#124; None = None, metadata: dict[str, Any] &#124; None = None, success: bool = True, error_message: str &#124; None = None) -> AdminAuditEntry` |  | Record an audit entry. |
| `alog` | `async def alog(self, user_id: str, username: str, role: str, action: AdminAction, **kwargs: Any) -> AdminAuditEntry` |  | Async version of log() -- awaits the DB write directly. |
| `get_entries_async` | `async def get_entries_async(self, *, action: AdminAction &#124; None = None, user_id: str &#124; None = None, model_name: str &#124; None = None, limit: int = 100, offset: int = 0) -> list[AdminAuditEntry]` |  | Fetch entries from the DB (preferred) or in-memory fallback. |
| `get_entries` | `def get_entries(self, *, action: AdminAction &#124; None = None, user_id: str &#124; None = None, model_name: str &#124; None = None, limit: int = 100, offset: int = 0) -> list[AdminAuditEntry]` |  | Synchronous get_entries -- returns in-memory entries only. |
| `count_async` | `async def count_async(self, *, action: AdminAction &#124; None = None, model_name: str &#124; None = None) -> int` |  | Count entries from DB if available, else in-memory. |
| `count` | `def count(self, *, action: AdminAction &#124; None = None, model_name: str &#124; None = None) -> int` |  | Synchronous count -- returns in-memory count only. |
| `clear` | `def clear(self) -> int` |  | Clear in-memory fallback entries and CROUS file. DB entries are retained. |
| `get_history_for_record` | `def get_history_for_record(self, model_name: str, record_pk: str) -> list[AdminAuditEntry]` |  | Return all audit entries for a specific model + pk. |

### Class: `AdminController`

- Source: `aquilia/admin/controller.py`
- Bases: `Controller`
- Summary: Aquilia Admin Controller.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `prefix` |  | `'/admin'` |
| `tags` |  | `['admin']` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_request` | `async def on_request(self, ctx: RequestCtx) -> None` |  | Populate the CSRF contextvar so every template gets the token. |
| `dashboard` | `async def dashboard(self, request, ctx: RequestCtx) -> Response` | GET | Admin dashboard -- model overview with stats. |
| `offline_page` | `async def offline_page(self, request, ctx: RequestCtx) -> Response` | GET | Render the offline detection page. |
| `login_page` | `async def login_page(self, request, ctx: RequestCtx) -> Response` | GET | Render admin login page with CSRF token. |
| `login_submit` | `async def login_submit(self, request, ctx: RequestCtx) -> Response` | POST | Process admin login. |
| `logout` | `async def logout(self, request, ctx: RequestCtx) -> Response` | POST | Logout and clear admin session (POST to prevent CSRF via GET). |
| `logout_get` | `async def logout_get(self, request, ctx: RequestCtx) -> Response` | GET | GET /logout kept for backward compat - performs same action. |
| `list_view` | `async def list_view(self, request, ctx: RequestCtx) -> Response` | GET | List records for a model with search and pagination. |
| `add_form` | `async def add_form(self, request, ctx: RequestCtx) -> Response` | GET | Render the add/create form for a model. |
| `add_submit` | `async def add_submit(self, request, ctx: RequestCtx) -> Response` | POST | Process create form submission. |
| `edit_form` | `async def edit_form(self, request, ctx: RequestCtx) -> Response` | GET | Render the edit form for a record. |
| `edit_submit` | `async def edit_submit(self, request, ctx: RequestCtx) -> Response` | POST | Process edit form submission. |
| `delete_record` | `async def delete_record(self, request, ctx: RequestCtx) -> Response` | POST | Delete a record. |
| `bulk_action` | `async def bulk_action(self, request, ctx: RequestCtx) -> Response` | POST | Execute a bulk action on selected records. |
| `export_view` | `async def export_view(self, request, ctx: RequestCtx) -> Response` | GET | Export model data as CSV, JSON, or XML using the export system. |
| `history_view` | `async def history_view(self, request, ctx: RequestCtx) -> Response` | GET | View change history for a specific record. |
| `batch_update` | `async def batch_update(self, request, ctx: RequestCtx) -> Response` | POST | Update a specific field on multiple records at once. |
| `filter_metadata_api` | `async def filter_metadata_api(self, request, ctx: RequestCtx) -> Response` | GET | Return filter metadata as JSON for dynamic filter UI. |
| `search_api` | `async def search_api(self, request, ctx: RequestCtx) -> Response` | GET | Return JSON search results for live AJAX search. |
| `orm_view` | `async def orm_view(self, request, ctx: RequestCtx) -> Response` | GET | ORM models overview -- all registered models with counts. |
| `migrations_view` | `async def migrations_view(self, request, ctx: RequestCtx) -> Response` | GET | Migrations page -- list all migrations with syntax-highlighted source. |
| `config_view` | `async def config_view(self, request, ctx: RequestCtx) -> Response` | GET | Configuration page -- show workspace YAML configuration. |
| `workspace_view` | `async def workspace_view(self, request, ctx: RequestCtx) -> Response` | GET | Workspace page -- monitor modules, manifests & project metadata. |
| `permissions_view` | `async def permissions_view(self, request, ctx: RequestCtx) -> Response` | GET | Permissions page -- role matrix and per-model access. |
| `permissions_update` | `async def permissions_update(self, request, ctx: RequestCtx) -> Response` | POST | Handle permission updates from the permissions page form. |
| `audit_view` | `async def audit_view(self, request, ctx: RequestCtx) -> Response` | GET | View the admin audit log -- reads from DB if available. |
| `monitoring_view` | `async def monitoring_view(self, request, ctx: RequestCtx) -> Response` | GET | Application monitoring -- CPU, memory, disk, network & process metrics. |
| `monitoring_api` | `async def monitoring_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling monitoring metrics. |
| `containers_view` | `async def containers_view(self, request, ctx: RequestCtx) -> Response` | GET | Docker containers -- images, volumes, networks & compose services. |
| `containers_api` | `async def containers_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling container metrics. |
| `containers_action` | `async def containers_action(self, request, ctx: RequestCtx) -> Response` | POST | Execute a container lifecycle action (start/stop/restart/pause/unpause/kill/rm). |
| `containers_inspect` | `async def containers_inspect(self, request, ctx: RequestCtx) -> Response` | POST | Return full docker inspect for a container. |
| `containers_logs` | `async def containers_logs(self, request, ctx: RequestCtx) -> Response` | POST | Fetch real docker logs for a container. |
| `volume_inspect` | `async def volume_inspect(self, request, ctx: RequestCtx) -> Response` | POST | Return docker volume inspect output. |
| `network_inspect` | `async def network_inspect(self, request, ctx: RequestCtx) -> Response` | POST | Return docker network inspect output. |
| `image_inspect` | `async def image_inspect(self, request, ctx: RequestCtx) -> Response` | POST | Return docker image inspect output. |
| `image_action` | `async def image_action(self, request, ctx: RequestCtx) -> Response` | POST | Execute image action (rm/pull). |
| `compose_action` | `async def compose_action(self, request, ctx: RequestCtx) -> Response` | POST | Execute compose action (up/down/restart/build/pull/stop/start). |
| `volume_action` | `async def volume_action(self, request, ctx: RequestCtx) -> Response` | POST | Execute volume action (rm). |
| `network_action` | `async def network_action(self, request, ctx: RequestCtx) -> Response` | POST | Execute network action (rm). |
| `docker_disk_usage` | `async def docker_disk_usage(self, request, ctx: RequestCtx) -> Response` | POST | Return docker system df output. |
| `docker_prune` | `async def docker_prune(self, request, ctx: RequestCtx) -> Response` | POST | Execute docker prune (system/images/containers/volumes/builder). |
| `container_exec` | `async def container_exec(self, request, ctx: RequestCtx) -> Response` | POST | Execute a command inside a running container. |
| `image_history` | `async def image_history(self, request, ctx: RequestCtx) -> Response` | POST | Return docker history for an image. |
| `image_tag` | `async def image_tag(self, request, ctx: RequestCtx) -> Response` | POST | Tag an image with a new name. |
| `container_export` | `async def container_export(self, request, ctx: RequestCtx) -> Response` | POST | Export a container filesystem as tar. |
| `create_network` | `async def create_network(self, request, ctx: RequestCtx) -> Response` | POST | Create a new Docker network. |
| `create_volume` | `async def create_volume(self, request, ctx: RequestCtx) -> Response` | POST | Create a new Docker volume. |
| `docker_events` | `async def docker_events(self, request, ctx: RequestCtx) -> Response` | POST | Return recent docker events. |
| `docker_build` | `async def docker_build(self, request, ctx: RequestCtx) -> Response` | POST | Execute docker build in the workspace. |
| `container_top` | `async def container_top(self, request, ctx: RequestCtx) -> Response` | POST | Return processes running inside a container. |
| `container_diff` | `async def container_diff(self, request, ctx: RequestCtx) -> Response` | POST | Return filesystem changes in a container. |
| `container_stats_single` | `async def container_stats_single(self, request, ctx: RequestCtx) -> Response` | POST | Return single-shot stats for one container. |
| `pods_view` | `async def pods_view(self, request, ctx: RequestCtx) -> Response` | GET | Kubernetes pods -- deployments, services, ingresses & manifests. |
| `pods_api` | `async def pods_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling pod metrics. |
| `storage_view` | `async def storage_view(self, request, ctx: RequestCtx) -> Response` | GET | Storage backends -- file browser, analytics, health & configuration. |
| `storage_api` | `async def storage_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling storage metrics. |
| `storage_download` | `async def storage_download(self, request, ctx: RequestCtx) -> Response` | GET | Download a file from a storage backend. |
| `storage_upload` | `async def storage_upload(self, request, ctx: RequestCtx) -> Response` | POST | Upload a file to a storage backend from the admin panel. |
| `storage_delete` | `async def storage_delete(self, request, ctx: RequestCtx) -> Response` | POST | Delete a file from a storage backend. |
| `query_inspector_view` | `async def query_inspector_view(self, request, ctx: RequestCtx) -> Response` | GET | Live query inspector -- ORM->SQL, timing, EXPLAIN, N+1 detection. |
| `query_inspector_api` | `async def query_inspector_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling query inspector data. |
| `mailer_view` | `async def mailer_view(self, request, ctx: RequestCtx) -> Response` | GET | Mail administration -- providers, config, templates, send test email. |
| `mailer_api` | `async def mailer_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling mailer data. |
| `mailer_send_test` | `async def mailer_send_test(self, request, ctx: RequestCtx) -> Response` | POST | Send a test email via the configured mail subsystem. |
| `mailer_health_check` | `async def mailer_health_check(self, request, ctx: RequestCtx) -> Response` | POST | Run health checks on all mail providers. |
| `provider_view` | `async def provider_view(self, request, ctx: RequestCtx) -> Response` | GET | Cloud provider & deployment dashboard -- services, deploys, credentials, databases. |
| `provider_api` | `async def provider_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling provider data. |
| `provider_logs_api` | `async def provider_logs_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint to fetch service logs. |
| `provider_action` | `async def provider_action(self, request, ctx: RequestCtx) -> Response` | POST | Execute a provider/deployment action (deploy, restart, rollback, etc.). |
| `tasks_view` | `async def tasks_view(self, request, ctx: RequestCtx) -> Response` | GET | Background task monitor -- job queue, workers, retries. |
| `tasks_api` | `async def tasks_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling task data. |
| `errors_view` | `async def errors_view(self, request, ctx: RequestCtx) -> Response` | GET | Error monitoring -- stack traces, grouping, trends. |
| `errors_api` | `async def errors_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling error data. |
| `testing_view` | `async def testing_view(self, request, ctx: RequestCtx) -> Response` | GET | Testing framework -- test infrastructure, coverage, assertions. |
| `testing_api` | `async def testing_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling testing data. |
| `mlops_view` | `async def mlops_view(self, request, ctx: RequestCtx) -> Response` | GET | MLOps dashboard -- model registry, serving, drift, rollouts. |
| `mlops_api` | `async def mlops_api(self, request, ctx: RequestCtx) -> Response` | GET | JSON API endpoint for live-polling MLOps data. |
| `mlops_predict` | `async def mlops_predict(self, request, ctx: RequestCtx) -> Response` | POST | Live inference playground -- send JSON input to a registered model. |
| `mlops_compare` | `async def mlops_compare(self, request, ctx: RequestCtx) -> Response` | POST | Model comparison -- run same input through multiple models. |
| `mlops_health_check` | `async def mlops_health_check(self, request, ctx: RequestCtx) -> Response` | POST | Run health checks on all registered models. |
| `mlops_batch_predict` | `async def mlops_batch_predict(self, request, ctx: RequestCtx) -> Response` | POST | Batch inference -- run multiple inputs through a model. |
| `mlops_inference_history` | `async def mlops_inference_history(self, request, ctx: RequestCtx) -> Response` | GET | Return recent inference history for the audit log. |
| `mlops_update_alerts` | `async def mlops_update_alerts(self, request, ctx: RequestCtx) -> Response` | POST | Update alert rules for MLOps monitoring. |
| `mlops_export_snapshot` | `async def mlops_export_snapshot(self, request, ctx: RequestCtx) -> Response` | POST | Export a full MLOps state snapshot as JSON. |
| `admin_users_view` | `async def admin_users_view(self, request, ctx: RequestCtx) -> Response` | GET | List and manage admin users with hierarchy. |
| `admin_users_create` | `async def admin_users_create(self, request, ctx: RequestCtx) -> Response` | POST | Create a new admin user with CSRF, rate limiting, and password validation. |
| `admin_users_toggle_status` | `async def admin_users_toggle_status(self, request, ctx: RequestCtx) -> Response` | POST | Toggle active status of an admin user. |
| `admin_users_reset_password` | `async def admin_users_reset_password(self, request, ctx: RequestCtx) -> Response` | POST | Reset password for an admin user (with CSRF and password validation). |
| `admin_users_delete` | `async def admin_users_delete(self, request, ctx: RequestCtx) -> Response` | POST | Delete an admin user (cannot delete superadmins). |
| `api_keys_view` | `async def api_keys_view(self, request, ctx: RequestCtx) -> Response` | GET | API keys management page. |
| `api_keys_create` | `async def api_keys_create(self, request, ctx: RequestCtx) -> Response` | POST | Create a new API key for the current user. |
| `api_keys_revoke` | `async def api_keys_revoke(self, request, ctx: RequestCtx) -> Response` | POST | Revoke (deactivate) an API key without deleting the record. |
| `api_keys_delete` | `async def api_keys_delete(self, request, ctx: RequestCtx) -> Response` | POST | Permanently delete an API key record. |
| `preferences_view` | `async def preferences_view(self, request, ctx: RequestCtx) -> Response` | GET | Preferences management page. |
| `preferences_get` | `async def preferences_get(self, request, ctx: RequestCtx, namespace: str = 'ui') -> Response` | GET | Get preferences for a specific namespace (JSON API). |
| `preferences_update` | `async def preferences_update(self, request, ctx: RequestCtx) -> Response` | POST | Create or update preferences for a namespace. |
| `preferences_delete` | `async def preferences_delete(self, request, ctx: RequestCtx) -> Response` | POST | Delete a preference namespace for the current user. |
| `profile_view` | `async def profile_view(self, request, ctx: RequestCtx) -> Response` | GET | View the admin profile management page. |
| `profile_avatar_legacy_redirect` | `async def profile_avatar_legacy_redirect(self, request, ctx: RequestCtx, filename: str) -> Response` | GET | Redirect legacy avatar URLs (/admin/profile/<file>) to the canonical path. |
| `profile_avatar_serve` | `async def profile_avatar_serve(self, request, ctx: RequestCtx, filename: str) -> Response` | GET | Serve a stored profile avatar from .aquilia/admin/profile/. |
| `profile_upload_avatar` | `async def profile_upload_avatar(self, request, ctx: RequestCtx) -> Response` | POST | Upload a new profile photo and persist it in .aquilia/admin/profile/. |
| `profile_update` | `async def profile_update(self, request, ctx: RequestCtx) -> Response` | POST | Update admin profile data. |
| `profile_change_password` | `async def profile_change_password(self, request, ctx: RequestCtx) -> Response` | POST | Change password for the currently logged-in admin (with validation). |

### Class: `ErrorRecord`

- Source: `aquilia/admin/error_tracker.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Captured error with full context.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` | `''` |
| `code` | `str` | `''` |
| `message` | `str` | `''` |
| `domain` | `str` | `''` |
| `severity` | `str` | `'ERROR'` |
| `trace_id` | `str` | `''` |
| `fingerprint` | `str` | `''` |
| `app` | `str` | `''` |
| `route` | `str` | `''` |
| `request_id` | `str` | `''` |
| `exception_type` | `str` | `''` |
| `exception_message` | `str` | `''` |
| `stack_trace` | `str` | `''` |
| `stack_frames` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `timestamp` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `ErrorGroup`

- Source: `aquilia/admin/error_tracker.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Aggregated error group (same fingerprint).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `fingerprint` | `str` | `''` |
| `code` | `str` | `''` |
| `message` | `str` | `''` |
| `domain` | `str` | `''` |
| `count` | `int` | `0` |
| `first_seen` | `datetime &#124; None` | `None` |
| `last_seen` | `datetime &#124; None` | `None` |
| `occurrences` | `list[str]` | `field(default_factory=list)` |
| `routes` | `set` | `field(default_factory=set)` |
| `apps` | `set` | `field(default_factory=set)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `ErrorTracker`

- Source: `aquilia/admin/error_tracker.py`
- Bases: `object`
- Summary: Central error tracking system.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `capture` | `def capture(self, fault_context) -> None` |  | FaultEngine listener callback. |
| `record_error` | `def record_error(self, *, code: str = 'UNKNOWN', message: str = '', domain: str = 'SYSTEM', severity: str = 'ERROR', app: str = '', route: str = '', request_id: str = '', exception_type: str = '', exception_message: str = '', stack_trace: str = '', metadata: dict[str, Any] &#124; None = None) -> ErrorRecord` |  | Manually record an error. |
| `get_recent_errors` | `def get_recent_errors(self, limit: int = 50) -> list[ErrorRecord]` |  | Get most recent errors. |
| `get_error` | `def get_error(self, error_id: str) -> ErrorRecord &#124; None` |  | Get a specific error by ID. |
| `get_groups` | `def get_groups(self, limit: int = 50) -> list[ErrorGroup]` |  | Get error groups sorted by count descending. |
| `get_errors_by_route` | `def get_errors_by_route(self, route: str, limit: int = 50) -> list[ErrorRecord]` |  | Get errors for a specific route. |
| `get_errors_by_domain` | `def get_errors_by_domain(self, domain: str, limit: int = 50) -> list[ErrorRecord]` |  | Get errors for a specific domain. |
| `get_stats` | `def get_stats(self) -> dict[str, Any]` |  | Get comprehensive error statistics with chart-ready data. |
| `resolve_error` | `def resolve_error(self, fingerprint: str) -> bool` |  | Mark an error group as resolved. |
| `clear` | `def clear(self) -> None` |  | Clear all tracked errors. |

### Class: `ExportFormat`

- Source: `aquilia/admin/export.py`
- Bases: `Enum`
- Summary: Supported export formats.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CSV` |  | `'csv'` |
| `JSON` |  | `'json'` |
| `XLSX` |  | `'xlsx'` |
| `XML` |  | `'xml'` |
| `YAML` |  | `'yaml'` |

### Class: `Exporter`

- Source: `aquilia/admin/export.py`
- Bases: `object`
- Summary: Base exporter class.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `format` | `ExportFormat` | `ExportFormat.CSV` |
| `content_type` | `str` | `'text/plain'` |
| `file_extension` | `str` | `'txt'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_fields` | `def get_fields(self, sample_row: dict[str, Any] &#124; None = None) -> list[str]` |  | Determine which fields to export. |
| `get_header` | `def get_header(self, field_name: str) -> str` |  | Get the display header for a field. |
| `get_value` | `def get_value(self, row: Any, field_name: str) -> Any` |  | Extract and format a field value from a row. |
| `get_filename` | `def get_filename(self, model_name: str = '') -> str` |  | Generate the export filename. |
| `export` | `def export(self, rows: Sequence[Any]) -> str` |  | Export rows to the target format. |
| `render` | `def render(self, rows: Sequence[Any]) -> str` |  | Render rows to string. Override in subclasses. |

### Class: `CSVExporter`

- Source: `aquilia/admin/export.py`
- Bases: `Exporter`
- Summary: Export data as CSV.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `format` |  | `ExportFormat.CSV` |
| `content_type` |  | `'text/csv; charset=utf-8'` |
| `file_extension` |  | `'csv'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, rows: Sequence[Any]) -> str` |  | Method. |

### Class: `JSONExporter`

- Source: `aquilia/admin/export.py`
- Bases: `Exporter`
- Summary: Export data as JSON array.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `format` |  | `ExportFormat.JSON` |
| `content_type` |  | `'application/json; charset=utf-8'` |
| `file_extension` |  | `'json'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, rows: Sequence[Any]) -> str` |  | Method. |

### Class: `XMLExporter`

- Source: `aquilia/admin/export.py`
- Bases: `Exporter`
- Summary: Export data as XML.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `format` |  | `ExportFormat.XML` |
| `content_type` |  | `'application/xml; charset=utf-8'` |
| `file_extension` |  | `'xml'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, rows: Sequence[Any]) -> str` |  | Method. |

### Class: `ExportRegistry`

- Source: `aquilia/admin/export.py`
- Bases: `object`
- Summary: Registry of available export formats.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(cls, format_name: str, exporter_cls: type[Exporter]) -> None` | classmethod | Register an exporter class for a format. |
| `get` | `def get(cls, format_name: str) -> type[Exporter] &#124; None` | classmethod | Get an exporter class by format name. |
| `create` | `def create(cls, format_name: str, **kwargs) -> Exporter &#124; None` | classmethod | Create an exporter instance by format name. |
| `available_formats` | `def available_formats(cls) -> list[str]` | classmethod | List all registered export format names. |

### Class: `AdminFault`

- Source: `aquilia/admin/faults.py`
- Bases: `Fault`
- Summary: Base fault for all admin operations.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `ADMIN_DOMAIN` |

### Class: `AdminAuthenticationFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Admin authentication failed.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_AUTH_FAILED'` |
| `status` |  | `401` |

### Class: `AdminAuthorizationFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Admin authorization failed -- insufficient permissions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_AUTHZ_DENIED'` |
| `status` |  | `403` |

### Class: `AdminSecurityFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Base fault for admin security violations.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_SECURITY_ERROR'` |
| `status` |  | `403` |

### Class: `AdminCSRFViolationFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminSecurityFault`
- Summary: CSRF token validation failed.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_CSRF_VIOLATION'` |
| `status` |  | `403` |

### Class: `AdminRateLimitFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminSecurityFault`
- Summary: Rate limit exceeded for admin operation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_RATE_LIMIT'` |
| `status` |  | `429` |

### Class: `AdminModelNotFoundFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Requested model is not registered with admin.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_MODEL_NOT_FOUND'` |
| `status` |  | `404` |

### Class: `AdminRecordNotFoundFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Record not found in database.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_RECORD_NOT_FOUND'` |
| `status` |  | `404` |

### Class: `AdminValidationFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Validation error when creating/updating records.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_VALIDATION_ERROR'` |
| `status` |  | `422` |

### Class: `AdminActionFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Bulk action execution failed.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_ACTION_FAILED'` |
| `status` |  | `400` |

### Class: `AdminConfigurationFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Admin system misconfiguration or missing dependency.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_CONFIG_ERROR'` |
| `status` |  | `500` |

### Class: `AdminRegistrationFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Model registration error.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_REGISTRATION_ERROR'` |
| `status` |  | `500` |

### Class: `AdminInlineFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Inline model configuration error.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_INLINE_ERROR'` |
| `status` |  | `400` |

### Class: `AdminTemplateFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Template rendering error.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_TEMPLATE_ERROR'` |
| `status` |  | `500` |

### Class: `AdminExportFault`

- Source: `aquilia/admin/faults.py`
- Bases: `AdminFault`
- Summary: Export generation error.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `code` |  | `'ADMIN_EXPORT_ERROR'` |
| `status` |  | `500` |

### Class: `ListFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `object`
- Summary: Base class for admin list view filters.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `title` | `str` | `''` |
| `parameter_name` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_choices` | `def get_choices(self) -> list[dict[str, Any]]` |  | Return list of filter choices. |
| `get_queryset` | `def get_queryset(self, queryset: Any, value: Any) -> Any` |  | Apply this filter to the queryset. |
| `to_metadata` | `def to_metadata(self) -> dict[str, Any]` |  | Serialize filter for template rendering. |

### Class: `SimpleFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Filter by exact field value.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_choices` | `def get_choices(self) -> list[dict[str, Any]]` |  | Method. |

### Class: `BooleanFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Filter for boolean fields with Yes/No/All choices.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_choices` | `def get_choices(self) -> list[dict[str, Any]]` |  | Method. |
| `to_metadata` | `def to_metadata(self) -> dict[str, Any]` |  | Method. |

### Class: `ChoiceFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Filter with explicitly defined choices.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `choices_list` | `list[tuple[str, str]]` | `[]` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_choices` | `def get_choices(self) -> list[dict[str, Any]]` |  | Method. |

### Class: `DateRangeFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Date range filter with preset periods and custom range support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_choices` | `def get_choices(self) -> list[dict[str, Any]]` |  | Method. |
| `get_date_range` | `def get_date_range(self, value: str) -> tuple[datetime, datetime] &#124; None` |  | Convert a preset value to a (start, end) datetime pair. |
| `to_metadata` | `def to_metadata(self) -> dict[str, Any]` |  | Method. |

### Class: `NumericRangeFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Numeric range filter with min/max inputs.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `step` | `float` | `1` |
| `min_value` | `float &#124; None` | `None` |
| `max_value` | `float &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_choices` | `def get_choices(self) -> list[dict[str, Any]]` |  | Method. |
| `to_metadata` | `def to_metadata(self) -> dict[str, Any]` |  | Method. |

### Class: `AllValuesFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Filter showing all distinct values found in the database.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_metadata` | `def to_metadata(self) -> dict[str, Any]` |  | Method. |

### Class: `RelatedModelFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Filter for ForeignKey fields using related model's __str__.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_metadata` | `def to_metadata(self) -> dict[str, Any]` |  | Method. |

### Class: `EmptyFieldFilter`

- Source: `aquilia/admin/filters.py`
- Bases: `ListFilter`
- Summary: Filter to find records where a field is empty/null or not.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_choices` | `def get_choices(self) -> list[dict[str, Any]]` |  | Method. |
| `to_metadata` | `def to_metadata(self) -> dict[str, Any]` |  | Method. |

### Class: `AdminHooksMixin`

- Source: `aquilia/admin/hooks.py`
- Bases: `object`
- Summary: Mixin providing lifecycle hook methods for ModelAdmin.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_queryset` | `def get_queryset(self, request: Any = None) -> Any` |  | Return the base queryset for list views. |
| `get_object` | `def get_object(self, request: Any = None, pk: Any = None) -> Any` |  | Retrieve a single object by primary key. |
| `get_form_fields` | `def get_form_fields(self, request: Any = None, obj: Any = None) -> list[dict[str, Any]]` |  | Return the field definitions for the add/edit form. |
| `clean_form` | `def clean_form(self, request: Any, form_data: dict[str, Any], obj: Any = None, change: bool = False) -> dict[str, Any]` |  | Validate and clean form data before saving. |
| `get_readonly_fields_for_request` | `def get_readonly_fields_for_request(self, request: Any = None, obj: Any = None) -> list[str]` |  | Return readonly fields, possibly varying by request/object. |
| `get_fieldsets_for_request` | `def get_fieldsets_for_request(self, request: Any = None, obj: Any = None) -> list &#124; None` |  | Return fieldsets, possibly varying by request/object. |
| `before_save` | `def before_save(self, request: Any, obj: Any, form_data: dict[str, Any], change: bool = False) -> None` |  | Called before save_model(). |
| `save_model` | `def save_model(self, request: Any, obj: Any, form_data: dict[str, Any], change: bool = False) -> None` |  | Persist the model instance to the database. |
| `save_related` | `def save_related(self, request: Any, obj: Any, form_data: dict[str, Any], change: bool = False) -> None` |  | Save related/inline objects after the main object is saved. |
| `after_save` | `def after_save(self, request: Any, obj: Any, form_data: dict[str, Any], change: bool = False) -> None` |  | Called after save_model() and save_related(). |
| `before_delete` | `def before_delete(self, request: Any, obj: Any) -> None` |  | Called before delete_model(). |
| `delete_model` | `def delete_model(self, request: Any, obj: Any) -> None` |  | Delete the model instance. |
| `after_delete` | `def after_delete(self, request: Any, obj: Any) -> None` |  | Called after delete_model(). |
| `before_bulk_action` | `def before_bulk_action(self, request: Any, action_name: str, queryset: Any) -> Any` |  | Called before executing a bulk action. |
| `after_bulk_action` | `def after_bulk_action(self, request: Any, action_name: str, queryset: Any, result: Any = None) -> None` |  | Called after a bulk action completes. |
| `log_addition` | `def log_addition(self, request: Any, obj: Any, message: str = '') -> None` |  | Log the creation of a new object. |
| `log_change` | `def log_change(self, request: Any, obj: Any, message: str = '') -> None` |  | Log a change to an existing object. |
| `log_deletion` | `def log_deletion(self, request: Any, obj: Any) -> None` |  | Log the deletion of an object. |
| `get_list_display_for_request` | `def get_list_display_for_request(self, request: Any = None) -> list[str] &#124; None` |  | Return list_display columns, possibly varying by request. |
| `get_search_fields_for_request` | `def get_search_fields_for_request(self, request: Any = None) -> list[str] &#124; None` |  | Return search fields, possibly varying by request. |
| `get_actions_for_request` | `def get_actions_for_request(self, request: Any = None) -> list &#124; None` |  | Return available actions, possibly varying by request. |
| `get_ordering_for_request` | `def get_ordering_for_request(self, request: Any = None) -> list[str] &#124; None` |  | Return ordering, possibly varying by request. |
| `response_add` | `def response_add(self, request: Any, obj: Any) -> Any &#124; None` |  | Determine the response after a successful add. |
| `response_change` | `def response_change(self, request: Any, obj: Any) -> Any &#124; None` |  | Determine the response after a successful edit. |
| `response_delete` | `def response_delete(self, request: Any, obj: Any) -> Any &#124; None` |  | Determine the response after a successful delete. |
| `get_inlines` | `def get_inlines(self, request: Any = None, obj: Any = None) -> list` |  | Return inline classes, possibly varying by request/object. |
| `get_inline_instances` | `def get_inline_instances(self, request: Any = None, obj: Any = None) -> list` |  | Instantiate inline classes. |

### Class: `SoftDeleteMixin`

- Source: `aquilia/admin/hooks.py`
- Bases: `object`
- Summary: Mixin for soft-delete support in ModelAdmin.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `soft_delete_field` | `str` | `'is_deleted'` |
| `soft_delete_timestamp_field` | `str &#124; None` | `'deleted_at'` |
| `show_deleted` | `bool` | `False` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_queryset` | `def get_queryset(self, request: Any = None) -> Any` |  | Filter out soft-deleted records by default. |
| `delete_model` | `def delete_model(self, request: Any, obj: Any) -> None` |  | Soft delete: set the flag instead of actually deleting. |
| `restore_model` | `def restore_model(self, request: Any, obj: Any) -> None` |  | Restore a soft-deleted record. |

### Class: `VersioningMixin`

- Source: `aquilia/admin/hooks.py`
- Bases: `object`
- Summary: Mixin for automatic version tracking on save.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `version_field` | `str` | `'version'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `before_save` | `def before_save(self, request: Any, obj: Any, form_data: dict[str, Any], change: bool = False) -> None` |  | Increment version number on save. |

### Class: `TimestampMixin`

- Source: `aquilia/admin/hooks.py`
- Bases: `object`
- Summary: Mixin for automatic timestamp management.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `created_at_field` | `str` | `'created_at'` |
| `updated_at_field` | `str` | `'updated_at'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `before_save` | `def before_save(self, request: Any, obj: Any, form_data: dict[str, Any], change: bool = False) -> None` |  | Set timestamps automatically. |

### Class: `InlineModelAdmin`

- Source: `aquilia/admin/inlines.py`
- Bases: `object`
- Summary: Base class for inline model editing within a parent form.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model` | `type[Model] &#124; None` | `None` |
| `fk_name` | `str &#124; None` | `None` |
| `fields` | `list[str] &#124; None` | `None` |
| `readonly_fields` | `list[str]` | `[]` |
| `exclude` | `list[str]` | `[]` |
| `extra` | `int` | `3` |
| `max_num` | `int &#124; None` | `None` |
| `min_num` | `int &#124; None` | `None` |
| `can_delete` | `bool` | `True` |
| `verbose_name` | `str &#124; None` | `None` |
| `verbose_name_plural` | `str &#124; None` | `None` |
| `ordering` | `list[str] &#124; None` | `None` |
| `show_change_link` | `bool` | `False` |
| `classes` | `list[str]` | `[]` |
| `template` | `str` | `'tabular'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_fk_name` | `def get_fk_name(self) -> str` |  | Get or auto-detect the FK field name linking to the parent model. |
| `get_fields` | `def get_fields(self) -> list[str]` |  | Get fields to display in the inline form. |
| `get_readonly_fields` | `def get_readonly_fields(self) -> list[str]` |  | Get read-only fields for the inline. |
| `get_verbose_name` | `def get_verbose_name(self) -> str` |  | Get display name for this inline. |
| `get_verbose_name_plural` | `def get_verbose_name_plural(self) -> str` |  | Get plural display name. |
| `get_ordering` | `def get_ordering(self) -> list[str]` |  | Get ordering for inline records. |
| `has_add_permission` | `def has_add_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can add inline records. |
| `has_change_permission` | `def has_change_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can change inline records. |
| `has_delete_permission` | `def has_delete_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can delete inline records. |
| `get_field_metadata` | `def get_field_metadata(self, field_name: str) -> dict[str, Any]` |  | Get metadata about a field for template rendering. |
| `to_template_data` | `def to_template_data(self, records: list[Any] = None, parent_pk: Any = None) -> dict[str, Any]` |  | Serialize inline configuration and data for template rendering. |

### Class: `TabularInline`

- Source: `aquilia/admin/inlines.py`
- Bases: `InlineModelAdmin`
- Summary: Inline rendered as a compact table with one row per record.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `template` |  | `'tabular'` |

### Class: `StackedInline`

- Source: `aquilia/admin/inlines.py`
- Bases: `InlineModelAdmin`
- Summary: Inline rendered as a full form stacked vertically.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `template` |  | `'stacked'` |

### Class: `ContentType`

- Source: `aquilia/admin/models.py`
- Bases: `object`
- Summary: Stub - Aquilia does not use a ContentType indirection table.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_for_model` | `def get_for_model(cls, model: Any) -> ContentType` | classmethod | Method. |

### Class: `AdminPermission`

- Source: `aquilia/admin/models.py`
- Bases: `object`
- Summary: Stub - permissions live in ``permissions.py`` as an in-memory enum.

### Class: `AdminGroup`

- Source: `aquilia/admin/models.py`
- Bases: `object`
- Summary: Stub - roles are defined in ``permissions.AdminRole``.

### Class: `AdminLogEntry`

- Source: `aquilia/admin/models.py`
- Bases: `object`
- Summary: Stub - use :class:`AdminAuditEntry` instead.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `log_action` | `async def log_action(cls, **kw: Any) -> AdminAuditEntry` | classmethod | Proxy to :meth:`AdminAuditEntry.log_action`. |

### Class: `AdminSession`

- Source: `aquilia/admin/models.py`
- Bases: `object`
- Summary: Stub - sessions are managed by ``aquilia.sessions`` at the framework level.

### Class: `AdminActionDescriptor`

- Source: `aquilia/admin/options.py`
- Bases: `object`
- Summary: Describes a bulk action available in the admin list view.

### Class: `ModelAdmin`

- Source: `aquilia/admin/options.py`
- Bases: `object`
- Summary: Declarative admin configuration for a model.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model` | `type[Model] &#124; None` | `None` |
| `list_display` | `list[str]` | `[]` |
| `list_display_links` | `list[str] &#124; None` | `None` |
| `list_filter` | `list[str]` | `[]` |
| `list_editable` | `list[str]` | `[]` |
| `search_fields` | `list[str]` | `[]` |
| `ordering` | `list[str]` | `[]` |
| `list_per_page` | `int` | `25` |
| `list_max_show_all` | `int` | `200` |
| `date_hierarchy` | `str &#124; None` | `None` |
| `show_full_result_count` | `bool` | `True` |
| `preserve_filters` | `bool` | `True` |
| `fieldsets` | `list[tuple[str, dict[str, Any]]] &#124; None` | `None` |
| `fields` | `list[str] &#124; None` | `None` |
| `readonly_fields` | `list[str]` | `[]` |
| `exclude` | `list[str]` | `[]` |
| `prepopulated_fields` | `dict[str, list[str]]` | `{}` |
| `raw_id_fields` | `list[str]` | `[]` |
| `save_on_top` | `bool` | `False` |
| `save_as` | `bool` | `False` |
| `save_as_continue` | `bool` | `True` |
| `inlines` | `list[Any]` | `[]` |
| `actions` | `list[Any]` | `[]` |
| `export_formats` | `list[str]` | `['csv', 'json', 'xml']` |
| `export_fields` | `list[str] &#124; None` | `None` |
| `empty_value_display` | `str` | `'--'` |
| `verbose_name` | `str &#124; None` | `None` |
| `verbose_name_plural` | `str &#124; None` | `None` |
| `icon` | `str` | `'list'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_list_display` | `def get_list_display(self) -> list[str]` |  | Get fields to display in list view. |
| `get_list_filter` | `def get_list_filter(self) -> list[str]` |  | Get filter fields. Auto-detects boolean and choice fields. |
| `get_search_fields` | `def get_search_fields(self) -> list[str]` |  | Get search fields. Auto-detects CharField and TextField. |
| `get_fields` | `def get_fields(self) -> list[str]` |  | Get editable fields for the form view. |
| `get_readonly_fields` | `def get_readonly_fields(self) -> list[str]` |  | Get read-only fields. |
| `get_fieldsets` | `def get_fieldsets(self) -> list[tuple[str, dict[str, Any]]]` |  | Get fieldsets for the form view. |
| `get_ordering` | `def get_ordering(self) -> list[str]` |  | Get default ordering. |
| `get_model_name` | `def get_model_name(self) -> str` |  | Get human-readable model name. |
| `get_model_name_plural` | `def get_model_name_plural(self) -> str` |  | Get plural model name. |
| `get_app_label` | `def get_app_label(self) -> str` |  | Get app label for grouping. |
| `get_actions` | `def get_actions(self) -> dict[str, AdminActionDescriptor]` |  | Get available actions. |
| `get_field_metadata` | `def get_field_metadata(self, field_name: str) -> dict[str, Any]` |  | Get metadata about a field for template rendering. |
| `has_view_permission` | `def has_view_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can view records. |
| `has_add_permission` | `def has_add_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can add records. |
| `has_change_permission` | `def has_change_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can change records. |
| `has_delete_permission` | `def has_delete_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can delete records. |
| `has_module_permission` | `def has_module_permission(self, identity: Identity &#124; None = None) -> bool` |  | Check if user can access this model's admin section. |
| `format_value` | `def format_value(self, field_name: str, value: Any) -> str` |  | Format a field value for display. |
| `get_inlines` | `def get_inlines(self) -> list` |  | Return inline classes for this admin. |
| `get_inline_instances` | `def get_inline_instances(self) -> list` |  | Instantiate InlineModelAdmin subclasses and resolve FK relationships. |
| `get_inline_template_data` | `def get_inline_template_data(self) -> list[dict[str, Any]]` |  | Get inline data serialized for template rendering. |
| `get_export_formats` | `def get_export_formats(self) -> list[str]` |  | Return available export format names. |
| `get_export_fields` | `def get_export_fields(self) -> list[str] &#124; None` |  | Return fields to include in exports (None = all). |

### Class: `AdminRole`

- Source: `aquilia/admin/permissions.py`
- Bases: `str, Enum`
- Summary: Built-in admin roles with hierarchical permissions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SUPERADMIN` |  | `'superadmin'` |
| `STAFF` |  | `'staff'` |
| `VIEWER` |  | `'viewer'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `level` | `def level(self) -> int` | property | Numeric hierarchy level (higher = more permissions). |

### Class: `AdminPermission`

- Source: `aquilia/admin/permissions.py`
- Bases: `str, Enum`
- Summary: Fine-grained admin permissions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DASHBOARD_VIEW` |  | `'admin.dashboard.view'` |
| `MODEL_VIEW` |  | `'admin.model.view'` |
| `MODEL_ADD` |  | `'admin.model.add'` |
| `MODEL_CHANGE` |  | `'admin.model.change'` |
| `MODEL_DELETE` |  | `'admin.model.delete'` |
| `MODEL_EXPORT` |  | `'admin.model.export'` |
| `ACTION_EXECUTE` |  | `'admin.action.execute'` |
| `AUDIT_VIEW` |  | `'admin.audit.view'` |
| `USER_MANAGE` |  | `'admin.user.manage'` |
| `ROLE_MANAGE` |  | `'admin.role.manage'` |
| `MONITORING_VIEW` |  | `'admin.monitoring.view'` |
| `CONTAINER_VIEW` |  | `'admin.container.view'` |
| `CONTAINER_MANAGE` |  | `'admin.container.manage'` |
| `POD_VIEW` |  | `'admin.pod.view'` |
| `POD_MANAGE` |  | `'admin.pod.manage'` |
| `STORAGE_VIEW` |  | `'admin.storage.view'` |
| `STORAGE_MANAGE` |  | `'admin.storage.manage'` |
| `MLOPS_VIEW` |  | `'admin.mlops.view'` |
| `MLOPS_MANAGE` |  | `'admin.mlops.manage'` |
| `QUERY_INSPECTOR_VIEW` |  | `'admin.query_inspector.view'` |
| `TASKS_VIEW` |  | `'admin.tasks.view'` |
| `TASKS_MANAGE` |  | `'admin.tasks.manage'` |
| `ERRORS_VIEW` |  | `'admin.errors.view'` |
| `TESTING_VIEW` |  | `'admin.testing.view'` |
| `TESTING_MANAGE` |  | `'admin.testing.manage'` |
| `ORM_VIEW` |  | `'admin.orm.view'` |
| `MIGRATIONS_VIEW` |  | `'admin.migrations.view'` |
| `CONFIG_VIEW` |  | `'admin.config.view'` |
| `WORKSPACE_VIEW` |  | `'admin.workspace.view'` |
| `PERMISSIONS_VIEW` |  | `'admin.permissions.view'` |
| `PERMISSIONS_MANAGE` |  | `'admin.permissions.manage'` |
| `MAILER_VIEW` |  | `'admin.mailer.view'` |
| `MAILER_MANAGE` |  | `'admin.mailer.manage'` |
| `PROVIDER_VIEW` |  | `'admin.provider.view'` |
| `PROVIDER_MANAGE` |  | `'admin.provider.manage'` |
| `API_KEY_VIEW` |  | `'admin.api_key.view'` |
| `API_KEY_MANAGE` |  | `'admin.api_key.manage'` |
| `PREFERENCE_VIEW` |  | `'admin.preference.view'` |
| `PREFERENCE_MANAGE` |  | `'admin.preference.manage'` |
| `PROFILE_VIEW` |  | `'admin.profile.view'` |
| `PROFILE_MANAGE` |  | `'admin.profile.manage'` |

### Class: `QueryRecord`

- Source: `aquilia/admin/query_inspector.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Single captured query with profiling data.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` | `''` |
| `sql` | `str` | `''` |
| `params` | `Any` | `None` |
| `duration_ms` | `float` | `0.0` |
| `rows_affected` | `int` | `0` |
| `timestamp` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `explain_plan` | `str` | `''` |
| `source` | `str` | `''` |
| `model` | `str` | `''` |
| `operation` | `str` | `''` |
| `is_slow` | `bool` | `False` |
| `stack_summary` | `str` | `''` |
| `request_id` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `fingerprint` | `def fingerprint(self) -> str` | property | Stable fingerprint for query grouping (ignores param values). |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `N1Detection`

- Source: `aquilia/admin/query_inspector.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Detected N+1 query pattern.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `pattern_sql` | `str` | `''` |
| `count` | `int` | `0` |
| `model` | `str` | `''` |
| `total_duration_ms` | `float` | `0.0` |
| `first_seen` | `str` | `''` |
| `source` | `str` | `''` |
| `request_id` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `QueryInspector`

- Source: `aquilia/admin/query_inspector.py`
- Bases: `object`
- Summary: Central query profiler and inspector.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `record` | `def record(self, sql: str, params: Any = None, duration_ms: float = 0.0, rows_affected: int = 0, model: str = '', request_id: str = '') -> QueryRecord` |  | Record a query execution. |
| `detect_n_plus_one` | `def detect_n_plus_one(self, request_id: str &#124; None = None) -> list[N1Detection]` |  | Detect N+1 query patterns. |
| `get_slow_queries` | `def get_slow_queries(self, limit: int = 50) -> list[QueryRecord]` |  | Get recent slow queries, sorted by duration descending. |
| `get_recent_queries` | `def get_recent_queries(self, limit: int = 100) -> list[QueryRecord]` |  | Get most recent queries. |
| `get_stats` | `def get_stats(self) -> dict[str, Any]` |  | Get aggregate query statistics. |
| `clear` | `def clear(self) -> None` |  | Clear all recorded queries. |

### Class: `AdminCSRFProtection`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Summary: CSRF protection specifically for the admin panel.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FORM_FIELD` |  | `'_csrf_token'` |
| `HEADER_NAME` |  | `'x-csrf-token'` |
| `SESSION_KEY` |  | `'_admin_csrf_token'` |
| `COOKIE_NAME` |  | `'_admin_csrf'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_token` | `def generate_token(self) -> str` |  | Generate a new HMAC-signed CSRF token with timestamp. |
| `validate_token` | `def validate_token(self, token: str) -> bool` |  | Validate a CSRF token (signature + expiry). |
| `get_or_create_token` | `def get_or_create_token(self, ctx: RequestCtx) -> str` |  | Get existing CSRF token from session, or create a new one. |
| `apply_cookie` | `def apply_cookie(self, response: Response, *, secure: bool = False) -> None` |  | Attach the pending CSRF cookie to a response. |
| `validate_request` | `def validate_request(self, ctx: RequestCtx, form_data: dict &#124; None = None) -> bool` |  | Validate CSRF token from request. |

### Class: `AdminRateLimiter`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Summary: Rate limiter for admin authentication and sensitive operations.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `LOCKOUT_TIERS` |  | `[(5, 300), (10, 900), (20, 3600), (50, 86400)]` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_login_locked` | `def is_login_locked(self, ip: str) -> tuple[bool, int]` |  | Check if an IP is locked out from login attempts. |
| `record_login_failure` | `def record_login_failure(self, ip: str) -> tuple[bool, int]` |  | Record a failed login attempt. |
| `record_login_success` | `def record_login_success(self, ip: str) -> None` |  | Clear login failure tracking on successful authentication. |
| `get_remaining_login_attempts` | `def get_remaining_login_attempts(self, ip: str) -> int` |  | Get remaining login attempts before lockout. |
| `check_sensitive_op` | `def check_sensitive_op(self, ip: str, operation: str = 'default') -> tuple[bool, int]` |  | Check if a sensitive operation is rate-limited. |

### Class: `AdminSecurityHeaders`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Summary: Applies security headers to all admin responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DEFAULT_CSP` |  | `"default-src 'self'; script-src 'self' {nonce} https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inli` |
| `DEFAULT_PERMISSIONS_POLICY` |  | `'camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_nonce` | `def generate_nonce(self) -> str` |  | Generate a cryptographically random nonce for CSP. |
| `apply` | `def apply(self, response: Response, *, nonce: str &#124; None = None, cache_control: str = 'no-store, no-cache, must-revalidate, max-age=0') -> Response` |  | Apply security headers to a response. |
| `apply_for_asset` | `def apply_for_asset(self, response: Response) -> Response` |  | Apply lighter security headers for static assets (avatars, downloads). |

### Class: `PasswordStrength`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of password complexity analysis.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `score` | `int` |  |
| `is_valid` | `bool` |  |
| `feedback` | `list[str]` |  |
| `length` | `int` |  |
| `has_upper` | `bool` |  |
| `has_lower` | `bool` |  |
| `has_digit` | `bool` |  |
| `has_special` | `bool` |  |

### Class: `PasswordValidator`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Summary: Password complexity validator for admin accounts.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `COMMON_PASSWORDS` | `frozenset[str]` | `frozenset({'password', '123456', '12345678', '1234567890', 'qwerty', 'abc123', 'password1', 'admin', 'letmein', 'welcome', 'monkey', 'dragon', 'master', 'login', 'princess', 'starwars', 'passw0rd', 'shadow', 'sunshine', 'trustno1', 'iloveyou', 'batman', 'access', 'hello', 'charlie', 'password123', 'admin123', 'root', 'toor', 'changeme', '123456789', '12345', '1234', 'qwerty123', '1q2w3e4r', 'qwertyuiop', '654321', '555555', 'lovely', 'password1!'})` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, password: str, *, username: str &#124; None = None) -> PasswordStrength` |  | Validate password complexity. |

### Class: `SecurityEvent`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable record of a security-relevant event.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `timestamp` | `float` |  |
| `event_type` | `str` |  |
| `ip_address` | `str` |  |
| `details` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `SecurityEventTracker`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Summary: Tracks security events for monitoring and alerting.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `record` | `def record(self, event_type: str, ip_address: str, **details: Any) -> SecurityEvent` |  | Record a security event. |
| `get_events` | `def get_events(self, *, event_type: str &#124; None = None, ip_address: str &#124; None = None, since: float &#124; None = None, limit: int = 100) -> list[SecurityEvent]` |  | Query recent security events with optional filters. |
| `count_events` | `def count_events(self, event_type: str, *, ip_address: str &#124; None = None, since: float &#124; None = None) -> int` |  | Count events matching criteria. |
| `clear` | `def clear(self) -> None` |  | Clear all tracked events. |

### Class: `AdminSecurityPolicy`

- Source: `aquilia/admin/security.py`
- Bases: `object`
- Summary: Central orchestrator for all admin security features.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_config` | `def from_config(cls, config: dict[str, Any]) -> AdminSecurityPolicy` | classmethod | Build an AdminSecurityPolicy from a security config dict. |
| `protect_response` | `def protect_response(self, response: Response, *, nonce: str &#124; None = None, is_asset: bool = False) -> Response` |  | Apply all security policies to a response. |
| `extract_client_ip` | `def extract_client_ip(self, request: Any) -> str` |  | Extract the client IP address from a request. |

### Class: `AdminConfig`

- Source: `aquilia/admin/site.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable admin configuration parsed from ``Integration.admin()`` config dict.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `modules` | `dict[str, bool]` | `field(default_factory=lambda: {'dashboard': True, 'orm': True, 'migrations': True, 'config': True, 'workspace': True, 'permissions': True, 'monitoring': False, 'admin_users': True, 'profile': True, 'audit': False, 'api_keys': True, 'preferences': True, 'containers': False, 'pods': False, 'query_inspector': False, 'tasks': False, 'errors': False, 'testing': False, 'mlops': False, 'storage': False, 'mailer': False, 'provider': False})` |
| `audit_enabled` | `bool` | `False` |
| `audit_max_entries` | `int` | `10000` |
| `audit_log_logins` | `bool` | `True` |
| `audit_log_views` | `bool` | `True` |
| `audit_log_searches` | `bool` | `True` |
| `audit_excluded_actions` | `frozenset[str]` | `field(default_factory=frozenset)` |
| `monitoring_enabled` | `bool` | `False` |
| `monitoring_metrics` | `frozenset[str]` | `field(default_factory=lambda: frozenset({'cpu', 'memory', 'disk', 'network', 'process', 'python', 'system', 'health_checks'}))` |
| `monitoring_refresh_interval` | `int` | `30` |
| `containers_config` | `dict[str, Any]` | `field(default_factory=lambda: {'docker_host': None, 'allowed_actions': ['start', 'stop', 'restart', 'pause', 'unpause', 'kill', 'rm', 'logs', 'inspect', 'exec', 'export'], 'log_tail': 200, 'log_since': '', 'refresh_interval': 15, 'compose_files': [], 'compose_project_dir': None, 'show_system_containers': False, 'capabilities': {'exec': True, 'prune': True, 'build': True, 'export': True, 'image_actions': True, 'volume_actions': True, 'network_actions': True}})` |
| `pods_config` | `dict[str, Any]` | `field(default_factory=lambda: {'kubeconfig': None, 'namespace': 'default', 'contexts': [], 'resources': ['pods', 'deployments', 'services', 'ingresses', 'configmaps', 'secrets', 'namespaces', 'events', 'daemonsets', 'statefulsets', 'jobs', 'cronjobs', 'persistentvolumeclaims', 'nodes'], 'manifest_dirs': ['k8s'], 'manifest_patterns': ['*.yaml', '*.yml'], 'refresh_interval': 15, 'log_tail': 200, 'capabilities': {'logs': True, 'exec': True, 'delete': True, 'scale': True, 'restart': True, 'apply': True}})` |
| `sidebar_sections` | `dict[str, bool]` | `field(default_factory=lambda: {'overview': True, 'data': True, 'system': True, 'infrastructure': True, 'security': True, 'models': True, 'devtools': True})` |
| `theme` | `str` | `'auto'` |
| `list_per_page` | `int` | `25` |
| `security_config` | `dict[str, Any]` | `field(default_factory=lambda: {'csrf': {'enabled': True, 'max_age': 7200, 'token_length': 32}, 'rate_limit': {'enabled': True, 'max_login_attempts': 5, 'login_window': 900, 'sensitive_op_limit': 30, 'sensitive_op_window': 300, 'progressive_lockout': True}, 'password': {'min_length': 10, 'max_length': 128, 'require_upper': True, 'require_lower': True, 'require_digit': True, 'require_special': True}, 'headers': {'enabled': True, 'frame_options': 'DENY'}, 'session_fixation_protection': True, 'event_tracker_max_events': 1000})` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_module_enabled` | `def is_module_enabled(self, module_name: str) -> bool` |  | Check if an admin module is enabled. |
| `is_action_allowed` | `def is_action_allowed(self, action: AdminAction) -> bool` |  | Return True if the given audit action should be recorded. |
| `is_metric_enabled` | `def is_metric_enabled(self, metric: str) -> bool` |  | Check if a monitoring metric section is enabled. |
| `is_sidebar_section_visible` | `def is_sidebar_section_visible(self, section: str) -> bool` |  | Check if a sidebar section is visible. |
| `get_docker_host` | `def get_docker_host(self) -> str &#124; None` |  | Return the configured Docker host, or None for auto-detect. |
| `get_container_refresh_interval` | `def get_container_refresh_interval(self) -> int` |  | Return the auto-refresh interval for the containers page. |
| `get_container_log_tail` | `def get_container_log_tail(self) -> int` |  | Return the default log tail lines for container logs. |
| `is_container_action_allowed` | `def is_container_action_allowed(self, action: str) -> bool` |  | Check if a container lifecycle action is permitted. |
| `is_container_capability_enabled` | `def is_container_capability_enabled(self, capability: str) -> bool` |  | Check if a container capability (exec/prune/build/export/etc.) is enabled. |
| `get_kube_namespace` | `def get_kube_namespace(self) -> str` |  | Return the configured Kubernetes namespace. |
| `get_pod_refresh_interval` | `def get_pod_refresh_interval(self) -> int` |  | Return the auto-refresh interval for the pods page. |
| `get_pod_log_tail` | `def get_pod_log_tail(self) -> int` |  | Return the default log tail lines for pod logs. |
| `is_pod_resource_enabled` | `def is_pod_resource_enabled(self, resource: str) -> bool` |  | Check if a K8s resource type is enabled for display. |
| `is_pod_capability_enabled` | `def is_pod_capability_enabled(self, capability: str) -> bool` |  | Check if a pod capability (logs/exec/delete/scale/restart/apply) is enabled. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialise the config for template consumption. |
| `from_dict` | `def from_dict(cls, raw: dict[str, Any]) -> AdminConfig` | classmethod | Build an AdminConfig from the raw Integration.admin() config dict. |

### Class: `AdminSite`

- Source: `aquilia/admin/site.py`
- Bases: `object`
- Summary: Central admin site -- manages all registered models.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `default` | `def default(cls) -> AdminSite` | classmethod | Get or create the default AdminSite singleton. |
| `reset` | `def reset(cls) -> None` | classmethod | Reset the default site (for testing). |
| `initialize` | `def initialize(self) -> None` |  | Initialize the admin site. |
| `register_admin` | `def register_admin(self, model_cls: type[Model], admin: ModelAdmin) -> None` |  | Register a model with its ModelAdmin configuration. |
| `register` | `def register(self, model_cls: type[Model], admin_class: type[ModelAdmin] &#124; None = None) -> None` |  | Register a model (convenience method). |
| `unregister` | `def unregister(self, model_cls: type[Model]) -> None` |  | Unregister a model. |
| `is_registered` | `def is_registered(self, model_cls: type[Model]) -> bool` |  | Check if a model is registered. |
| `get_model_admin` | `def get_model_admin(self, model_cls_or_name: Any) -> ModelAdmin` |  | Get ModelAdmin for a model class or name. |
| `get_model_class` | `def get_model_class(self, model_name: str) -> type[Model]` |  | Get model class by name. |
| `get_app_list` | `def get_app_list(self, identity: Identity &#124; None = None) -> list[dict[str, Any]]` |  | Get list of admin apps/models grouped by app_label. |
| `get_registered_models` | `def get_registered_models(self) -> dict[str, ModelAdmin]` |  | Get all registered model name -> ModelAdmin pairs. |
| `get_model_schema` | `def get_model_schema(self) -> list[dict[str, Any]]` |  | Build rich schema metadata for every registered model. |
| `get_orm_metadata` | `def get_orm_metadata(self) -> dict[str, Any]` |  | Gather comprehensive ORM-level metadata beyond individual models. |
| `get_query_inspector_data` | `def get_query_inspector_data(self) -> dict[str, Any]` |  | Gather query inspector data: recent queries, slow queries, |
| `get_error_tracker_data` | `def get_error_tracker_data(self) -> dict[str, Any]` |  | Gather error tracker data: recent errors, error groups, |
| `get_tasks_data` | `async def get_tasks_data(self) -> dict[str, Any]` |  | Gather background task manager data: job list, queue stats, |
| `set_task_manager` | `def set_task_manager(self, manager) -> None` |  | Register the application's TaskManager for admin integration. |
| `set_mail_service` | `def set_mail_service(self, service) -> None` |  | Register the application's MailService for admin integration. |
| `get_mailer_data` | `def get_mailer_data(self) -> dict[str, Any]` |  | Gather comprehensive mail subsystem data for the admin mailer page. |
| `set_provider_services` | `def set_provider_services(self, client = None, deployer = None, credential_store = None) -> None` |  | Register cloud provider services for admin integration. |
| `get_provider_data` | `def get_provider_data(self) -> dict[str, Any]` |  | Gather comprehensive cloud provider data for the admin provider page. |
| `execute_provider_action` | `async def execute_provider_action(self, action: str, service_id: str = '', deploy_id: str = '', extra_data: dict[str, Any] &#124; None = None) -> dict[str, Any]` |  | Execute a provider/deployment action and return the result. |
| `get_provider_logs` | `def get_provider_logs(self, service_id: str) -> list` |  | Fetch recent logs for a provider service. |
| `set_storage_registry` | `def set_storage_registry(self, registry) -> None` |  | Register the application's StorageRegistry for admin integration. |
| `get_storage_data` | `async def get_storage_data(self) -> dict[str, Any]` |  | Gather comprehensive storage subsystem data for the admin page. |
| `get_mlops_data` | `def get_mlops_data(self) -> dict[str, Any]` |  | Gather comprehensive MLOps subsystem data for the admin page. |
| `set_mlops_services` | `def set_mlops_services(self, registry = None, metrics_collector = None, drift_detector = None, circuit_breaker = None, rate_limiter = None, memory_tracker = None, plugin_host = None, experiment_ledger = None, lineage_dag = None, rollout_engine = None, autoscaler = None, rbac_manager = None, batch_queue = None, lru_cache = None) -> None` |  | Register MLOps services for admin integration. |
| `get_testing_data` | `def get_testing_data(self) -> dict[str, Any]` |  | Gather comprehensive testing framework data. |
| `get_dashboard_stats` | `async def get_dashboard_stats(self) -> dict[str, Any]` |  | Aggregate comprehensive dashboard statistics. |
| `get_migrations_data` | `def get_migrations_data(self) -> list[dict[str, Any]]` |  | Scan the migrations directory for migration files and |
| `get_config_data` | `def get_config_data(self) -> dict[str, Any]` |  | Read workspace.py configuration (single-file config). |
| `get_monitoring_data` | `def get_monitoring_data(self) -> dict[str, Any]` |  | Gather comprehensive system monitoring data. |
| `get_containers_data` | `def get_containers_data(self) -> dict[str, Any]` |  | Gather comprehensive Docker container and compose data. |
| `execute_container_action` | `def execute_container_action(self, container_id: str, action: str, run_params: str = '') -> dict[str, Any]` |  | Execute a Docker container lifecycle action. |
| `get_container_inspect` | `def get_container_inspect(self, container_id: str) -> dict[str, Any]` |  | Return full ``docker inspect`` output for a container. |
| `get_container_logs` | `def get_container_logs(self, container_id: str, *, tail: int = 200, since: str = '') -> dict[str, Any]` |  | Fetch recent logs from a container via ``docker logs``. |
| `get_volume_inspect` | `def get_volume_inspect(self, volume_name: str) -> dict[str, Any]` |  | Return ``docker volume inspect`` output. |
| `get_network_inspect` | `def get_network_inspect(self, network_id: str) -> dict[str, Any]` |  | Return ``docker network inspect`` output. |
| `get_image_inspect` | `def get_image_inspect(self, image_id: str) -> dict[str, Any]` |  | Return ``docker image inspect`` output. |
| `execute_image_action` | `def execute_image_action(self, image_id: str, action: str) -> dict[str, Any]` |  | Execute a Docker image action. |
| `execute_compose_action` | `def execute_compose_action(self, action: str) -> dict[str, Any]` |  | Execute a Docker Compose action. |
| `execute_volume_action` | `def execute_volume_action(self, volume_name: str, action: str) -> dict[str, Any]` |  | Execute a Docker volume action. Supported: rm |
| `execute_network_action` | `def execute_network_action(self, network_id: str, action: str) -> dict[str, Any]` |  | Execute a Docker network action. Supported: rm |
| `get_docker_disk_usage` | `def get_docker_disk_usage(self) -> dict[str, Any]` |  | Return ``docker system df -v`` data: images, containers, volumes, |
| `get_docker_disk_usage_summary` | `def get_docker_disk_usage_summary(self) -> dict[str, Any]` |  | Return a human-friendly summary of docker disk usage. |
| `execute_docker_prune` | `def execute_docker_prune(self, target: str) -> dict[str, Any]` |  | Execute docker prune commands. |
| `execute_container_exec` | `def execute_container_exec(self, container_id: str, command: str) -> dict[str, Any]` |  | Execute a command inside a running container via ``docker exec``. |
| `get_image_history` | `def get_image_history(self, image_id: str) -> dict[str, Any]` |  | Return ``docker history`` for an image with layer sizes. |
| `execute_image_tag` | `def execute_image_tag(self, source_image: str, target_tag: str) -> dict[str, Any]` |  | Tag an image with a new name via ``docker tag``. |
| `execute_container_export` | `def execute_container_export(self, container_id: str) -> dict[str, Any]` |  | Export a container filesystem as a tar (returns path info). |
| `create_docker_network` | `def create_docker_network(self, name: str, driver: str = 'bridge', subnet: str = '', gateway: str = '', internal: bool = False) -> dict[str, Any]` |  | Create a new Docker network. |
| `create_docker_volume` | `def create_docker_volume(self, name: str, driver: str = 'local', labels: str = '') -> dict[str, Any]` |  | Create a new Docker volume. |
| `get_docker_events` | `def get_docker_events(self, since: str = '10m') -> dict[str, Any]` |  | Return recent docker events (from last N minutes). |
| `execute_docker_build` | `def execute_docker_build(self, *, tag: str = '', no_cache: bool = False, build_args: str = '', target: str = '') -> dict[str, Any]` |  | Execute ``docker build`` in the workspace directory. |
| `get_container_top` | `def get_container_top(self, container_id: str) -> dict[str, Any]` |  | Return ``docker top`` output - processes running inside a container. |
| `get_container_diff` | `def get_container_diff(self, container_id: str) -> dict[str, Any]` |  | Return ``docker diff`` - filesystem changes in a container. |
| `get_container_stats_stream` | `def get_container_stats_stream(self, container_id: str) -> dict[str, Any]` |  | Return a single snapshot of ``docker stats`` for one container. |
| `get_pods_data` | `def get_pods_data(self) -> dict[str, Any]` |  | Gather comprehensive Kubernetes pod and manifest data. |
| `get_workspace_data` | `def get_workspace_data(self) -> dict[str, Any]` |  | Gather comprehensive workspace data for the admin workspace page. |
| `get_permissions_data` | `def get_permissions_data(self, identity: Identity &#124; None = None) -> dict[str, Any]` |  | Gather permission roles, matrix, and per-model permissions. |
| `update_permissions` | `def update_permissions(self, form_data: dict[str, Any], identity: Identity &#124; None = None) -> dict[str, Any]` |  | Update role permissions and/or model permission overrides from |
| `list_records` | `async def list_records(self, model_name: str, *, page: int = 1, per_page: int = 25, search: str = '', filters: dict[str, Any] &#124; None = None, ordering: str &#124; None = None, identity: Identity &#124; None = None) -> dict[str, Any]` |  | List records for a model with pagination, search, and filtering. |
| `get_record` | `async def get_record(self, model_name: str, pk: Any, *, identity: Identity &#124; None = None) -> dict[str, Any]` |  | Get a single record with field metadata for the edit form. |
| `create_record` | `async def create_record(self, model_name: str, data: dict[str, Any], *, identity: Identity &#124; None = None) -> Any` |  | Create a new record. |
| `update_record` | `async def update_record(self, model_name: str, pk: Any, data: dict[str, Any], *, identity: Identity &#124; None = None) -> Any` |  | Update an existing record. |
| `delete_record` | `async def delete_record(self, model_name: str, pk: Any, *, identity: Identity &#124; None = None) -> bool` |  | Delete a record. |
| `execute_action` | `async def execute_action(self, model_name: str, action_name: str, selected_pks: list[Any], *, identity: Identity &#124; None = None) -> str` |  | Execute a bulk action on selected records. |

### Class: `AdminCacheIntegration`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Integrates Aquilia CacheService into admin operations.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `NAMESPACE` |  | `'admin'` |
| `MODEL_LIST_TTL` |  | `30` |
| `DASHBOARD_TTL` |  | `60` |
| `FRAGMENT_TTL` |  | `120` |
| `RATE_LIMIT_TTL` |  | `3600` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `enabled` | `def enabled(self) -> bool` | property | Check if cache integration is available. |
| `set_cache_service` | `def set_cache_service(self, service: Any) -> None` |  | Set the CacheService instance (called during server startup). |
| `get_model_list` | `async def get_model_list(self, model_name: str, page: int = 1, filters: dict[str, Any] &#124; None = None, search: str = '', ordering: str = '') -> Any &#124; None` |  | Get cached model list result. |
| `set_model_list` | `async def set_model_list(self, model_name: str, page: int, filters: dict[str, Any] &#124; None, search: str, ordering: str, data: Any) -> None` |  | Cache a model list result. |
| `invalidate_model` | `async def invalidate_model(self, model_name: str) -> int` |  | Invalidate all cached data for a model after CUD operations. |
| `get_dashboard_stats` | `async def get_dashboard_stats(self) -> dict[str, Any] &#124; None` |  | Get cached dashboard statistics. |
| `set_dashboard_stats` | `async def set_dashboard_stats(self, stats: dict[str, Any]) -> None` |  | Cache dashboard statistics. |
| `get_fragment` | `async def get_fragment(self, fragment_key: str) -> str &#124; None` |  | Get a cached template fragment. |
| `set_fragment` | `async def set_fragment(self, fragment_key: str, html: str, ttl: int &#124; None = None) -> None` |  | Cache a template fragment. |

### Class: `AdminDBEffect`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Typed effect token for admin database operations.

### Class: `AdminCacheEffect`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Typed effect token for admin cache operations.

### Class: `AdminTaskEffect`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Typed effect token for admin background task dispatch.

### Class: `AdminTasks`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Background tasks for admin housekeeping.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `enabled` | `def enabled(self) -> bool` | property | Check if task integration is available. |
| `set_task_manager` | `def set_task_manager(self, manager: Any) -> None` |  | Set the TaskManager instance during server startup. |
| `audit_log_cleanup` | `async def audit_log_cleanup(self, max_entries: int = 10000) -> dict[str, Any]` |  | Prune old audit log entries beyond the configured maximum. |
| `session_cleanup` | `async def session_cleanup(self) -> dict[str, Any]` |  | Remove expired admin sessions. |
| `security_report` | `async def security_report(self) -> dict[str, Any]` |  | Generate a summary of recent security events. |
| `rate_limit_cleanup` | `async def rate_limit_cleanup(self) -> dict[str, Any]` |  | Force cleanup of stale rate limiter records. |
| `enqueue_audit_cleanup` | `async def enqueue_audit_cleanup(self, max_entries: int = 10000) -> str &#124; None` |  | Enqueue audit cleanup as a background task. |
| `enqueue_session_cleanup` | `async def enqueue_session_cleanup(self) -> str &#124; None` |  | Enqueue session cleanup as a background task. |

### Class: `AdminAuthGuard`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Flow guard that verifies admin authentication.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `'admin_auth_guard'` |
| `priority` |  | `10` |

### Class: `AdminPermGuard`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Flow guard that checks model-level permissions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `'admin_perm_guard'` |
| `priority` |  | `20` |

### Class: `AdminCSRFGuard`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Flow guard that validates CSRF tokens for POST/PUT/DELETE requests.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `'admin_csrf_guard'` |
| `priority` |  | `15` |

### Class: `AdminRateLimitGuard`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Flow guard that enforces rate limits on admin requests.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `'admin_rate_limit_guard'` |
| `priority` |  | `5` |

### Class: `AdminAuditHook`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Flow hook that logs admin actions to the audit trail.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `'admin_audit_hook'` |
| `priority` |  | `90` |

### Class: `AdminLifecycle`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Admin lifecycle hooks for integration with Aquilia's LifecycleCoordinator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `cache` | `def cache(self) -> AdminCacheIntegration` | property | Get the cache integration. |
| `tasks` | `def tasks(self) -> AdminTasks` | property | Get the task integration. |
| `on_startup` | `async def on_startup(self, config: dict[str, Any] &#124; None = None, container: Any &#124; None = None) -> None` |  | Admin startup hook. |
| `on_shutdown` | `async def on_shutdown(self, config: dict[str, Any] &#124; None = None, container: Any &#124; None = None) -> None` |  | Admin shutdown hook. |

### Class: `AdminSubsystems`

- Source: `aquilia/admin/subsystems.py`
- Bases: `object`
- Summary: Central orchestrator for all admin subsystem integrations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `default` | `def default(cls) -> AdminSubsystems` | classmethod | Get or create the default AdminSubsystems singleton. |
| `reset` | `def reset(cls) -> None` | classmethod | Reset the singleton (for testing). |
| `lifecycle` | `def lifecycle(self) -> AdminLifecycle` | property | Get lifecycle integration. |
| `cache` | `def cache(self) -> AdminCacheIntegration` | property | Get cache integration. |
| `tasks` | `def tasks(self) -> AdminTasks` | property | Get task integration. |
| `build_pipeline` | `def build_pipeline(self, model_name: str = '', action: str = 'view', require_auth: bool = True, require_csrf: bool = False, rate_limit_op: str &#124; None = None) -> dict[str, Any]` |  | Build a flow pipeline for an admin request. |

### Class: `WidgetSize`

- Source: `aquilia/admin/widgets.py`
- Bases: `Enum`
- Summary: Widget size on the dashboard grid.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SMALL` |  | `'sm'` |
| `MEDIUM` |  | `'md'` |
| `LARGE` |  | `'lg'` |
| `FULL` |  | `'full'` |

### Class: `WidgetPosition`

- Source: `aquilia/admin/widgets.py`
- Bases: `Enum`
- Summary: Widget placement section.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `TOP` |  | `'top'` |
| `MAIN` |  | `'main'` |
| `SIDEBAR` |  | `'sidebar'` |
| `BOTTOM` |  | `'bottom'` |

### Class: `AdminWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Base class for dashboard widgets.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `title` | `str` | `''` |
| `icon` | `str` | `''` |
| `size` | `WidgetSize` | `WidgetSize.SMALL` |
| `position` | `WidgetPosition` | `WidgetPosition.TOP` |
| `order` | `int` | `0` |
| `permission` | `str &#124; None` | `None` |
| `refresh_interval` | `int` | `0` |
| `css_classes` | `str` | `''` |
| `visible` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Return data for rendering this widget. |
| `to_template_data` | `def to_template_data(self) -> dict[str, Any]` |  | Serialize widget for template rendering. |

### Class: `CountWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Displays a count of records in a model.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` | `str` | `''` |
| `filter_field` | `str &#124; None` | `None` |
| `filter_value` | `Any` | `None` |
| `color` | `str` | `'blue'` |
| `count` | `int` | `0` |
| `change_percent` | `float &#124; None` | `None` |
| `trend` | `str` | `''` |
| `link` | `str` | `''` |
| `footer_text` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `StatWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Displays a single statistic value with trend.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `value` | `str` | `''` |
| `value_fn` | `Callable &#124; None` | `None` |
| `change` | `str` | `''` |
| `trend` | `str` | `''` |
| `color` | `str` | `'blue'` |
| `suffix` | `str` | `''` |
| `prefix` | `str` | `''` |
| `link` | `str` | `''` |
| `footer_text` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `ChartWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Displays a chart (line, bar, pie, doughnut, area).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `chart_type` | `str` | `'line'` |
| `labels` | `list[str]` | `field(default_factory=list)` |
| `datasets` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `data_fn` | `Callable &#124; None` | `None` |
| `color_scheme` | `str` | `'default'` |
| `show_legend` | `bool` | `True` |
| `height` | `int` | `300` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `RecentActivityWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Displays recent admin activity log entries.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `limit` | `int` | `10` |
| `actions` | `list[str] &#124; None` | `None` |
| `show_user` | `bool` | `True` |
| `show_timestamp` | `bool` | `True` |
| `show_model` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `TableWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Displays a data table on the dashboard.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `columns` | `list[str]` | `field(default_factory=list)` |
| `rows` | `list[list[Any]]` | `field(default_factory=list)` |
| `data_fn` | `Callable &#124; None` | `None` |
| `model_name` | `str` | `''` |
| `show_link` | `bool` | `True` |
| `max_rows` | `int` | `10` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `ListWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Displays a simple list of items on the dashboard.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `items` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `items_fn` | `Callable &#124; None` | `None` |
| `show_icon` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `ProgressWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Displays a progress bar or set of progress bars.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `bars` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `bars_fn` | `Callable &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `CustomHTMLWidget`

- Source: `aquilia/admin/widgets.py`
- Bases: `AdminWidget`
- Decorators: `dataclass`
- Summary: Widget that renders custom HTML content.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `html_content` | `str` | `''` |
| `html_fn` | `Callable &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_data` | `def get_data(self) -> dict[str, Any]` |  | Method. |

### Class: `WidgetRegistry`

- Source: `aquilia/admin/widgets.py`
- Bases: `object`
- Summary: Registry for dashboard widgets.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, widget: AdminWidget) -> None` |  | Register a widget. |
| `unregister` | `def unregister(self, widget: AdminWidget) -> None` |  | Unregister a widget. |
| `clear` | `def clear(self) -> None` |  | Remove all widgets. |
| `get_widgets` | `def get_widgets(self, position: WidgetPosition &#124; None = None) -> list[AdminWidget]` |  | Get widgets, optionally filtered by position. |
| `get_widgets_by_size` | `def get_widgets_by_size(self, size: WidgetSize) -> list[AdminWidget]` |  | Get widgets of a specific size. |
| `to_template_data` | `def to_template_data(self, position: WidgetPosition &#124; None = None) -> list[dict[str, Any]]` |  | Serialize all matching widgets for template rendering. |
| `count` | `def count(self) -> int` | property | Return total number of registered widgets. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `provide_admin_site` | `aquilia/admin/di_providers.py` | `def provide_admin_site() -> AdminSite` | Provide the default AdminSite singleton. |
| `provide_admin_controller` | `aquilia/admin/di_providers.py` | `def provide_admin_controller(site: AdminSite &#124; None = None) -> AdminController` | Provide an AdminController bound to the given or default site. |
| `provide_audit_log` | `aquilia/admin/di_providers.py` | `def provide_audit_log(site: AdminSite &#124; None = None) -> AdminAuditLog` | Provide the audit log from the current AdminSite. |
| `provide_model_backed_audit_log` | `aquilia/admin/di_providers.py` | `def provide_model_backed_audit_log() -> ModelBackedAuditLog` | Provide a ModelBackedAuditLog instance. |
| `register_admin_providers` | `aquilia/admin/di_providers.py` | `def register_admin_providers(container: Container) -> None` | Register all admin DI providers with the given container. |
| `get_error_tracker` | `aquilia/admin/error_tracker.py` | `def get_error_tracker() -> ErrorTracker` | Get or create the global ErrorTracker instance. |
| `resolve_filter` | `aquilia/admin/filters.py` | `def resolve_filter(filter_spec: Any, model: type[Model] &#124; None = None) -> ListFilter` | Resolve a filter specification into a ListFilter instance. |
| `action` | `aquilia/admin/options.py` | `def action(short_description: str = '', confirmation: str = '', permission: str = '')` | Decorator to mark a method as an admin action. |
| `get_admin_role` | `aquilia/admin/permissions.py` | `def get_admin_role(identity: Identity &#124; None) -> AdminRole &#124; None` | Determine the admin role for an identity. |
| `has_admin_permission` | `aquilia/admin/permissions.py` | `def has_admin_permission(identity: Identity &#124; None, permission: AdminPermission) -> bool` | Check if an identity has a specific admin permission. |
| `has_model_permission` | `aquilia/admin/permissions.py` | `def has_model_permission(identity: Identity &#124; None, model_name: str, action: str) -> bool` | Check if an identity can perform an action on a model. |
| `require_admin_access` | `aquilia/admin/permissions.py` | `def require_admin_access(identity: Identity &#124; None) -> None` | Raise AdminAuthorizationFault if identity has no admin access. |
| `update_role_permissions` | `aquilia/admin/permissions.py` | `def update_role_permissions(role: AdminRole, permission: AdminPermission, *, granted: bool) -> None` | Grant or revoke a specific permission for a role at runtime. |
| `set_model_permission_override` | `aquilia/admin/permissions.py` | `def set_model_permission_override(model_name: str, action: str, *, allowed: bool) -> None` | Set a per-model permission override. |
| `get_model_permission_overrides` | `aquilia/admin/permissions.py` | `def get_model_permission_overrides() -> dict[str, dict[str, bool]]` | Return the current model permission overrides. |
| `clear_model_permission_overrides` | `aquilia/admin/permissions.py` | `def clear_model_permission_overrides(model_name: str &#124; None = None) -> None` | Clear model permission overrides. |
| `get_query_inspector` | `aquilia/admin/query_inspector.py` | `def get_query_inspector() -> QueryInspector` | Get or create the global QueryInspector instance. |
| `register` | `aquilia/admin/registry.py` | `def register(model_or_admin: Any = None, *, site: AdminSite &#124; None = None) -> Callable` | Register a model or ModelAdmin with the admin site. |
| `autodiscover` | `aquilia/admin/registry.py` | `def autodiscover() -> dict[str, type[Model]]` | Auto-discover and register all models from ModelRegistry. |
| `flush_pending_registrations` | `aquilia/admin/registry.py` | `def flush_pending_registrations() -> int` | Flush any pending registrations to the default AdminSite. |
| `register_security_providers` | `aquilia/admin/security.py` | `def register_security_providers(container: Any, config: dict[str, Any] &#124; None = None) -> None` | Register admin security components with the DI container. |
| `build_admin_flow_pipeline` | `aquilia/admin/subsystems.py` | `def build_admin_flow_pipeline(security_policy: Any &#124; None = None, model_name: str = '', action: str = 'view', require_auth: bool = True, require_csrf: bool = False, rate_limit_op: str &#124; None = None) -> dict[str, Any]` | Build a standard admin flow pipeline configuration. |
| `get_admin_subsystems` | `aquilia/admin/subsystems.py` | `def get_admin_subsystems() -> AdminSubsystems` | Get the default AdminSubsystems instance. |
| `render_login_page` | `aquilia/admin/templates.py` | `def render_login_page(error: str = '', *, csrf_token: str = '', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the admin login page. |
| `render_dashboard` | `aquilia/admin/templates.py` | `def render_dashboard(app_list: list[dict[str, Any]], stats: dict[str, Any], identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin', containers_summary: dict[str, Any] &#124; None = None, pods_summary: dict[str, Any] &#124; None = None, orm_metadata: dict[str, Any] &#124; None = None, error_stats: dict[str, Any] &#124; None = None, tasks_stats: dict[str, Any] &#124; None = None, mlops_summary: dict[str, Any] &#124; None = None, storage_summary: dict[str, Any] &#124; None = None) -> str` | Render the admin dashboard. |
| `render_list_view` | `aquilia/admin/templates.py` | `def render_list_view(data: dict[str, Any], app_list: list[dict[str, Any]], identity_name: str = 'Admin', identity_avatar: str = '', flash: str = '', flash_type: str = 'success', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the model list view with table, search, pagination. |
| `render_form_view` | `aquilia/admin/templates.py` | `def render_form_view(data: dict[str, Any], app_list: list[dict[str, Any]], identity_name: str = 'Admin', identity_avatar: str = '', is_create: bool = False, flash: str = '', flash_type: str = 'success', query_inspection: list[dict[str, Any]] &#124; None = None, *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the add/edit form view. |
| `render_audit_page` | `aquilia/admin/templates.py` | `def render_audit_page(entries: list[dict[str, Any]], app_list: list[dict[str, Any]], identity_name: str = 'Admin', identity_avatar: str = '', total: int = 0, page: int = 1, per_page: int = 50, total_pages: int = 1, *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the audit log page. |
| `render_orm_page` | `aquilia/admin/templates.py` | `def render_orm_page(app_list: list[dict[str, Any]], model_counts: dict[str, Any], identity_name: str = 'Admin', identity_avatar: str = '', model_schema: list[dict[str, Any]] &#124; None = None, orm_metadata: dict[str, Any] &#124; None = None, *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the ORM models page with schema inspector and relation graph. |
| `render_migrations_page` | `aquilia/admin/templates.py` | `def render_migrations_page(migrations: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the migrations page with syntax highlighted source. |
| `render_config_page` | `aquilia/admin/templates.py` | `def render_config_page(config_files: list[dict[str, Any]], workspace_info: dict[str, Any] &#124; None = None, app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the configuration page with YAML file contents. |
| `render_workspace_page` | `aquilia/admin/templates.py` | `def render_workspace_page(workspace: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the workspace monitoring page. |
| `render_permissions_page` | `aquilia/admin/templates.py` | `def render_permissions_page(roles: list[dict[str, Any]], all_permissions: list[str], model_permissions: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', flash: str = '', flash_type: str = 'success', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the permissions page with role matrix. |
| `render_monitoring_page` | `aquilia/admin/templates.py` | `def render_monitoring_page(monitoring: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the application monitoring page with system metrics and charts. |
| `render_containers_page` | `aquilia/admin/templates.py` | `def render_containers_page(containers_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the containers page with Docker Desktop-like container management. |
| `render_pods_page` | `aquilia/admin/templates.py` | `def render_pods_page(pods_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the pods page with Kubernetes pod tracking and manifest viewer. |
| `render_storage_page` | `aquilia/admin/templates.py` | `def render_storage_page(storage_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the storage admin page with backend analytics and file browser. |
| `render_admin_users_page` | `aquilia/admin/templates.py` | `def render_admin_users_page(users: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the admin-users management page with hierarchy, roles, and creation form. |
| `render_profile_page` | `aquilia/admin/templates.py` | `def render_profile_page(user: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the admin profile management page. |
| `render_api_keys_page` | `aquilia/admin/templates.py` | `def render_api_keys_page(keys: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the API keys management page. |
| `render_preferences_page` | `aquilia/admin/templates.py` | `def render_preferences_page(preferences: list[dict[str, Any]], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, flash: str = '', flash_type: str = 'success', site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the user preferences management page. |
| `render_forbidden_page` | `aquilia/admin/templates.py` | `def render_forbidden_page(module_name: str = 'this page', required_permission: str = '', current_role: str = '', app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render a styled 403 Forbidden page when a user lacks permissions. |
| `render_error_page` | `aquilia/admin/templates.py` | `def render_error_page(status: int = 404, title: str = 'Not Found', message: str = '', app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render a styled admin error page (404, 403, 400, etc.). |
| `render_disabled_page` | `aquilia/admin/templates.py` | `def render_disabled_page(module_name: str, builder_hint: str = '', flat_hint: str = '', icon_key: str = '', description: str = '', app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render a beautiful blurred overlay page for disabled admin modules. |
| `render_query_inspector_page` | `aquilia/admin/templates.py` | `def render_query_inspector_page(query_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin', qi_page: int = 1, qi_per_page: int = 30, qi_total: int = 0, qi_total_pages: int = 1) -> str` | Render the live query inspector page with SQL profiling and N+1 detection. |
| `render_provider_page` | `aquilia/admin/templates.py` | `def render_provider_page(provider_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the comprehensive provider & deployment administration page. |
| `render_mailer_page` | `aquilia/admin/templates.py` | `def render_mailer_page(mailer_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the comprehensive mail administration page. |
| `render_tasks_page` | `aquilia/admin/templates.py` | `def render_tasks_page(tasks_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the background tasks monitor page with Chart.js analytics. |
| `render_errors_page` | `aquilia/admin/templates.py` | `def render_errors_page(errors_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the error monitoring page with Chart.js analytics. |
| `render_mlops_page` | `aquilia/admin/templates.py` | `def render_mlops_page(mlops_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the MLOps admin page with comprehensive analytics. |
| `render_testing_page` | `aquilia/admin/templates.py` | `def render_testing_page(testing_data: dict[str, Any], app_list: list[dict[str, Any]] &#124; None = None, identity_name: str = 'Admin', identity_avatar: str = '', *, site_title: str = 'Aquilia Admin', url_prefix: str = '/admin') -> str` | Render the testing framework admin page with Chart.js analytics. |
| `get_widget_registry` | `aquilia/admin/widgets.py` | `def get_widget_registry() -> WidgetRegistry` | Get the default widget registry. |
| `register_widget` | `aquilia/admin/widgets.py` | `def register_widget(widget: AdminWidget) -> AdminWidget` | Register a widget to the default registry. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CSP_NONCE_PLACEHOLDER` | `aquilia/admin/controller.py` | `'__CSP_NONCE__'` |
| `_ALLOWED_IMAGE_TYPES` | `aquilia/admin/controller.py` | `dict[bytes, tuple]` |
| `_MAX_AVATAR_BYTES` | `aquilia/admin/controller.py` | `4 * 1024 * 1024` |
| `ADMIN_DOMAIN` | `aquilia/admin/faults.py` | `FaultDomain.custom('ADMIN', 'Admin dashboard faults')` |
| `API_KEY_PREFIX` | `aquilia/admin/models.py` | `'aq_'` |
| `API_KEY_ENTROPY` | `aquilia/admin/models.py` | `32` |
| `DEFAULT_ROLE` | `aquilia/admin/models.py` | `'staff'` |
| `VALID_ROLES` | `aquilia/admin/models.py` | `('superadmin', 'staff', 'viewer')` |
| `_ROLE_CHECK_SQL` | `aquilia/admin/models.py` | `"role IN ('superadmin', 'staff', 'viewer')"` |
| `_HAS_ORM` | `aquilia/admin/models.py` | `_ORM_AVAILABLE` |
| `ROLE_PERMISSIONS` | `aquilia/admin/permissions.py` | `dict[AdminRole, set[AdminPermission]]` |
| `_MODEL_PERMISSION_OVERRIDES` | `aquilia/admin/permissions.py` | `dict[str, dict[str, bool]]` |
| `_TEMPLATES_DIR` | `aquilia/admin/templates.py` | `Path(__file__).resolve().parent / 'templates'` |
| `_HAS_JINJA2` | `aquilia/admin/templates.py` | `False` |
| `ADMIN_CSS` | `aquilia/admin/templates.py` | `''` |
| `_FALLBACK_CSS` | `aquilia/admin/templates.py` | `'\n:root{--bg-primary:#02040a;--bg-card:#09090b;--bg-input:#18181b;--border-color:#27272a;\n--accent:#22c55e;--accent-hover:#16a34a;--accent-glow:rgba(34,197,94` |
