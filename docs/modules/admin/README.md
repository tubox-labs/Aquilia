# admin Module

## Purpose

Auto-detecting administration interface. Use this module for model administration, audit views, API keys, task and storage panels, security controls, and operational dashboards.

## Source Coverage

- Python files: 21
- Public classes: 92
- Dataclasses: 17
- Enums: 6
- Public functions: 53

## How It Fits In Aquilia

1. Import the package from `aquilia.admin` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `AdminAction` | `aquilia/admin/audit.py` | Admin action types for audit logging. |
| `AdminAuditEntry` | `aquilia/admin/audit.py` | Immutable audit log entry. |
| `CrousAuditStore` | `aquilia/admin/audit.py` | Thin persistence layer that stores/loads audit entries using the CROUS |
| `AdminAuditLog` | `aquilia/admin/audit.py` | Admin audit log -- records all admin operations. |
| `ModelBackedAuditLog` | `aquilia/admin/audit.py` | Model-backed audit log -- persists entries to the AdminAuditEntry ORM table. |
| `AdminController` | `aquilia/admin/controller.py` | Aquilia Admin Controller. |
| `ErrorRecord` | `aquilia/admin/error_tracker.py` | Captured error with full context. |
| `ErrorGroup` | `aquilia/admin/error_tracker.py` | Aggregated error group (same fingerprint). |
| `ErrorTracker` | `aquilia/admin/error_tracker.py` | Central error tracking system. |
| `ExportFormat` | `aquilia/admin/export.py` | Supported export formats. |
| `Exporter` | `aquilia/admin/export.py` | Base exporter class. |
| `CSVExporter` | `aquilia/admin/export.py` | Export data as CSV. |
| `JSONExporter` | `aquilia/admin/export.py` | Export data as JSON array. |
| `XMLExporter` | `aquilia/admin/export.py` | Export data as XML. |
| `ExportRegistry` | `aquilia/admin/export.py` | Registry of available export formats. |
| `AdminFault` | `aquilia/admin/faults.py` | Base fault for all admin operations. |
| `AdminAuthenticationFault` | `aquilia/admin/faults.py` | Admin authentication failed. |
| `AdminAuthorizationFault` | `aquilia/admin/faults.py` | Admin authorization failed -- insufficient permissions. |
| `AdminSecurityFault` | `aquilia/admin/faults.py` | Base fault for admin security violations. |
| `AdminCSRFViolationFault` | `aquilia/admin/faults.py` | CSRF token validation failed. |
| `AdminRateLimitFault` | `aquilia/admin/faults.py` | Rate limit exceeded for admin operation. |
| `AdminModelNotFoundFault` | `aquilia/admin/faults.py` | Requested model is not registered with admin. |
| `AdminRecordNotFoundFault` | `aquilia/admin/faults.py` | Record not found in database. |
| `AdminValidationFault` | `aquilia/admin/faults.py` | Validation error when creating/updating records. |
| `AdminActionFault` | `aquilia/admin/faults.py` | Bulk action execution failed. |
| `AdminConfigurationFault` | `aquilia/admin/faults.py` | Admin system misconfiguration or missing dependency. |
| `AdminRegistrationFault` | `aquilia/admin/faults.py` | Model registration error. |
| `AdminInlineFault` | `aquilia/admin/faults.py` | Inline model configuration error. |
| `AdminTemplateFault` | `aquilia/admin/faults.py` | Template rendering error. |
| `AdminExportFault` | `aquilia/admin/faults.py` | Export generation error. |
| `ListFilter` | `aquilia/admin/filters.py` | Base class for admin list view filters. |
| `SimpleFilter` | `aquilia/admin/filters.py` | Filter by exact field value. |
| `BooleanFilter` | `aquilia/admin/filters.py` | Filter for boolean fields with Yes/No/All choices. |
| `ChoiceFilter` | `aquilia/admin/filters.py` | Filter with explicitly defined choices. |
| `DateRangeFilter` | `aquilia/admin/filters.py` | Date range filter with preset periods and custom range support. |
| `NumericRangeFilter` | `aquilia/admin/filters.py` | Numeric range filter with min/max inputs. |
| `AllValuesFilter` | `aquilia/admin/filters.py` | Filter showing all distinct values found in the database. |
| `RelatedModelFilter` | `aquilia/admin/filters.py` | Filter for ForeignKey fields using related model's __str__. |
| `EmptyFieldFilter` | `aquilia/admin/filters.py` | Filter to find records where a field is empty/null or not. |
| `AdminHooksMixin` | `aquilia/admin/hooks.py` | Mixin providing lifecycle hook methods for ModelAdmin. |
| `SoftDeleteMixin` | `aquilia/admin/hooks.py` | Mixin for soft-delete support in ModelAdmin. |
| `VersioningMixin` | `aquilia/admin/hooks.py` | Mixin for automatic version tracking on save. |
| `TimestampMixin` | `aquilia/admin/hooks.py` | Mixin for automatic timestamp management. |
| `InlineModelAdmin` | `aquilia/admin/inlines.py` | Base class for inline model editing within a parent form. |
| `TabularInline` | `aquilia/admin/inlines.py` | Inline rendered as a compact table with one row per record. |
| `StackedInline` | `aquilia/admin/inlines.py` | Inline rendered as a full form stacked vertically. |
| `ContentType` | `aquilia/admin/models.py` | Stub - Aquilia does not use a ContentType indirection table. |
| `AdminPermission` | `aquilia/admin/models.py` | Stub - permissions live in ``permissions.py`` as an in-memory enum. |
| `AdminGroup` | `aquilia/admin/models.py` | Stub - roles are defined in ``permissions.AdminRole``. |
| `AdminLogEntry` | `aquilia/admin/models.py` | Stub - use :class:`AdminAuditEntry` instead. |
| `AdminSession` | `aquilia/admin/models.py` | Stub - sessions are managed by ``aquilia.sessions`` at the framework level. |
| `AdminActionDescriptor` | `aquilia/admin/options.py` | Describes a bulk action available in the admin list view. |
| `ModelAdmin` | `aquilia/admin/options.py` | Declarative admin configuration for a model. |
| `AdminRole` | `aquilia/admin/permissions.py` | Built-in admin roles with hierarchical permissions. |
| `AdminPermission` | `aquilia/admin/permissions.py` | Fine-grained admin permissions. |
| `QueryRecord` | `aquilia/admin/query_inspector.py` | Single captured query with profiling data. |
| `N1Detection` | `aquilia/admin/query_inspector.py` | Detected N+1 query pattern. |
| `QueryInspector` | `aquilia/admin/query_inspector.py` | Central query profiler and inspector. |
| `AdminCSRFProtection` | `aquilia/admin/security.py` | CSRF protection specifically for the admin panel. |
| `AdminRateLimiter` | `aquilia/admin/security.py` | Rate limiter for admin authentication and sensitive operations. |
| `AdminSecurityHeaders` | `aquilia/admin/security.py` | Applies security headers to all admin responses. |
| `PasswordStrength` | `aquilia/admin/security.py` | Result of password complexity analysis. |
| `PasswordValidator` | `aquilia/admin/security.py` | Password complexity validator for admin accounts. |
| `SecurityEvent` | `aquilia/admin/security.py` | Immutable record of a security-relevant event. |
| `SecurityEventTracker` | `aquilia/admin/security.py` | Tracks security events for monitoring and alerting. |
| `AdminSecurityPolicy` | `aquilia/admin/security.py` | Central orchestrator for all admin security features. |
| `AdminConfig` | `aquilia/admin/site.py` | Immutable admin configuration parsed from ``Integration.admin()`` config dict. |
| `AdminSite` | `aquilia/admin/site.py` | Central admin site -- manages all registered models. |
| `AdminCacheIntegration` | `aquilia/admin/subsystems.py` | Integrates Aquilia CacheService into admin operations. |
| `AdminDBEffect` | `aquilia/admin/subsystems.py` | Typed effect token for admin database operations. |
| `AdminCacheEffect` | `aquilia/admin/subsystems.py` | Typed effect token for admin cache operations. |
| `AdminTaskEffect` | `aquilia/admin/subsystems.py` | Typed effect token for admin background task dispatch. |
| `AdminTasks` | `aquilia/admin/subsystems.py` | Background tasks for admin housekeeping. |
| `AdminAuthGuard` | `aquilia/admin/subsystems.py` | Flow guard that verifies admin authentication. |
| `AdminPermGuard` | `aquilia/admin/subsystems.py` | Flow guard that checks model-level permissions. |
| `AdminCSRFGuard` | `aquilia/admin/subsystems.py` | Flow guard that validates CSRF tokens for POST/PUT/DELETE requests. |
| `AdminRateLimitGuard` | `aquilia/admin/subsystems.py` | Flow guard that enforces rate limits on admin requests. |
| `AdminAuditHook` | `aquilia/admin/subsystems.py` | Flow hook that logs admin actions to the audit trail. |
| `AdminLifecycle` | `aquilia/admin/subsystems.py` | Admin lifecycle hooks for integration with Aquilia's LifecycleCoordinator. |
| `AdminSubsystems` | `aquilia/admin/subsystems.py` | Central orchestrator for all admin subsystem integrations. |

Only the first 80 classes are shown here. See the file inventory for the rest of the package.

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `provide_admin_site` | `aquilia/admin/di_providers.py` | Provide the default AdminSite singleton. |
| `provide_admin_controller` | `aquilia/admin/di_providers.py` | Provide an AdminController bound to the given or default site. |
| `provide_audit_log` | `aquilia/admin/di_providers.py` | Provide the audit log from the current AdminSite. |
| `provide_model_backed_audit_log` | `aquilia/admin/di_providers.py` | Provide a ModelBackedAuditLog instance. |
| `register_admin_providers` | `aquilia/admin/di_providers.py` | Register all admin DI providers with the given container. |
| `get_error_tracker` | `aquilia/admin/error_tracker.py` | Get or create the global ErrorTracker instance. |
| `resolve_filter` | `aquilia/admin/filters.py` | Resolve a filter specification into a ListFilter instance. |
| `action` | `aquilia/admin/options.py` | Decorator to mark a method as an admin action. |
| `get_admin_role` | `aquilia/admin/permissions.py` | Determine the admin role for an identity. |
| `has_admin_permission` | `aquilia/admin/permissions.py` | Check if an identity has a specific admin permission. |
| `has_model_permission` | `aquilia/admin/permissions.py` | Check if an identity can perform an action on a model. |
| `require_admin_access` | `aquilia/admin/permissions.py` | Raise AdminAuthorizationFault if identity has no admin access. |
| `update_role_permissions` | `aquilia/admin/permissions.py` | Grant or revoke a specific permission for a role at runtime. |
| `set_model_permission_override` | `aquilia/admin/permissions.py` | Set a per-model permission override. |
| `get_model_permission_overrides` | `aquilia/admin/permissions.py` | Return the current model permission overrides. |
| `clear_model_permission_overrides` | `aquilia/admin/permissions.py` | Clear model permission overrides. |
| `get_query_inspector` | `aquilia/admin/query_inspector.py` | Get or create the global QueryInspector instance. |
| `register` | `aquilia/admin/registry.py` | Register a model or ModelAdmin with the admin site. |
| `autodiscover` | `aquilia/admin/registry.py` | Auto-discover and register all models from ModelRegistry. |
| `flush_pending_registrations` | `aquilia/admin/registry.py` | Flush any pending registrations to the default AdminSite. |
| `register_security_providers` | `aquilia/admin/security.py` | Register admin security components with the DI container. |
| `build_admin_flow_pipeline` | `aquilia/admin/subsystems.py` | Build a standard admin flow pipeline configuration. |
| `get_admin_subsystems` | `aquilia/admin/subsystems.py` | Get the default AdminSubsystems instance. |
| `render_login_page` | `aquilia/admin/templates.py` | Render the admin login page. |
| `render_dashboard` | `aquilia/admin/templates.py` | Render the admin dashboard. |
| `render_list_view` | `aquilia/admin/templates.py` | Render the model list view with table, search, pagination. |
| `render_form_view` | `aquilia/admin/templates.py` | Render the add/edit form view. |
| `render_audit_page` | `aquilia/admin/templates.py` | Render the audit log page. |
| `render_orm_page` | `aquilia/admin/templates.py` | Render the ORM models page with schema inspector and relation graph. |
| `render_migrations_page` | `aquilia/admin/templates.py` | Render the migrations page with syntax highlighted source. |
| `render_config_page` | `aquilia/admin/templates.py` | Render the configuration page with YAML file contents. |
| `render_workspace_page` | `aquilia/admin/templates.py` | Render the workspace monitoring page. |
| `render_permissions_page` | `aquilia/admin/templates.py` | Render the permissions page with role matrix. |
| `render_monitoring_page` | `aquilia/admin/templates.py` | Render the application monitoring page with system metrics and charts. |
| `render_containers_page` | `aquilia/admin/templates.py` | Render the containers page with Docker Desktop-like container management. |
| `render_pods_page` | `aquilia/admin/templates.py` | Render the pods page with Kubernetes pod tracking and manifest viewer. |
| `render_storage_page` | `aquilia/admin/templates.py` | Render the storage admin page with backend analytics and file browser. |
| `render_admin_users_page` | `aquilia/admin/templates.py` | Render the admin-users management page with hierarchy, roles, and creation form. |
| `render_profile_page` | `aquilia/admin/templates.py` | Render the admin profile management page. |
| `render_api_keys_page` | `aquilia/admin/templates.py` | Render the API keys management page. |
| `render_preferences_page` | `aquilia/admin/templates.py` | Render the user preferences management page. |
| `render_forbidden_page` | `aquilia/admin/templates.py` | Render a styled 403 Forbidden page when a user lacks permissions. |
| `render_error_page` | `aquilia/admin/templates.py` | Render a styled admin error page (404, 403, 400, etc.). |
| `render_disabled_page` | `aquilia/admin/templates.py` | Render a beautiful blurred overlay page for disabled admin modules. |
| `render_query_inspector_page` | `aquilia/admin/templates.py` | Render the live query inspector page with SQL profiling and N+1 detection. |
| `render_provider_page` | `aquilia/admin/templates.py` | Render the comprehensive provider & deployment administration page. |
| `render_mailer_page` | `aquilia/admin/templates.py` | Render the comprehensive mail administration page. |
| `render_tasks_page` | `aquilia/admin/templates.py` | Render the background tasks monitor page with Chart.js analytics. |
| `render_errors_page` | `aquilia/admin/templates.py` | Render the error monitoring page with Chart.js analytics. |
| `render_mlops_page` | `aquilia/admin/templates.py` | Render the MLOps admin page with comprehensive analytics. |
| `render_testing_page` | `aquilia/admin/templates.py` | Render the testing framework admin page with Chart.js analytics. |
| `get_widget_registry` | `aquilia/admin/widgets.py` | Get the default widget registry. |
| `register_widget` | `aquilia/admin/widgets.py` | Register a widget to the default registry. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/admin/__init__.py` | AquilAdmin -- Modern, Auto-Detecting Admin System for Aquilia. |
| `aquilia/admin/audit.py` | AquilAdmin -- Audit Trail. |
| `aquilia/admin/blueprints.py` | AquilAdmin -- Blueprints for Admin Models. |
| `aquilia/admin/controller.py` | AquilAdmin -- Admin Controller. |
| `aquilia/admin/di_providers.py` | AquilAdmin -- DI Providers. |
| `aquilia/admin/error_tracker.py` | AquilAdmin - Error Tracker. |
| `aquilia/admin/export.py` | AquilAdmin -- Export System. |
| `aquilia/admin/faults.py` | AquilAdmin -- Structured Faults for Admin System. |
| `aquilia/admin/filters.py` | AquilAdmin -- Advanced Filter System. |
| `aquilia/admin/hooks.py` | AquilAdmin -- Lifecycle Hooks System. |
| `aquilia/admin/inlines.py` | AquilAdmin -- Inline Model Admin. |
| `aquilia/admin/models.py` | Aquilia Admin - Data Models |
| `aquilia/admin/options.py` | AquilAdmin -- ModelAdmin Options. |
| `aquilia/admin/permissions.py` | AquilAdmin -- Admin Permission & Role System. |
| `aquilia/admin/query_inspector.py` | AquilAdmin - Live Query Inspector. |
| `aquilia/admin/registry.py` | AquilAdmin -- Model Registration & Auto-Discovery. |
| `aquilia/admin/security.py` | AquilAdmin -- Security Hardening Module. |
| `aquilia/admin/site.py` | AquilAdmin -- AdminSite (Central Registry). |
| `aquilia/admin/subsystems.py` | AquilAdmin -- Subsystem Integration Module. |
| `aquilia/admin/templates.py` | AquilAdmin -- Template Renderer. |
| `aquilia/admin/widgets.py` | AquilAdmin -- Dashboard Widget System. |

## Testing Pointers

Search `tests/` for `admin` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
