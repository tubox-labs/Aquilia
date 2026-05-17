# Admin Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `AdminAuditEntry` | `aquilia/admin/audit.py` | id: str, timestamp: datetime, user_id: str, username: str, role: str, action: AdminAction, model_name: str &#124; None, record_pk: str &#124; None, changes: dict[str, Any] &#124; None, ip_address: str &#124; None, user_agent: str &#124; None, metadata: dict[str, Any], ... | Immutable audit log entry. |
| `ErrorRecord` | `aquilia/admin/error_tracker.py` | id: str, code: str, message: str, domain: str, severity: str, trace_id: str, fingerprint: str, app: str, route: str, request_id: str, exception_type: str, exception_message: str, ... | Captured error with full context. |
| `ErrorGroup` | `aquilia/admin/error_tracker.py` | fingerprint: str, code: str, message: str, domain: str, count: int, first_seen: datetime &#124; None, last_seen: datetime &#124; None, occurrences: list[str], routes: set, apps: set | Aggregated error group (same fingerprint). |
| `QueryRecord` | `aquilia/admin/query_inspector.py` | id: str, sql: str, params: Any, duration_ms: float, rows_affected: int, timestamp: datetime, explain_plan: str, source: str, model: str, operation: str, is_slow: bool, stack_summary: str, ... | Single captured query with profiling data. |
| `N1Detection` | `aquilia/admin/query_inspector.py` | pattern_sql: str, count: int, model: str, total_duration_ms: float, first_seen: str, source: str, request_id: str | Detected N+1 query pattern. |
| `PasswordStrength` | `aquilia/admin/security.py` | score: int, is_valid: bool, feedback: list[str], length: int, has_upper: bool, has_lower: bool, has_digit: bool, has_special: bool | Result of password complexity analysis. |
| `SecurityEvent` | `aquilia/admin/security.py` | timestamp: float, event_type: str, ip_address: str, details: dict[str, Any] | Immutable record of a security-relevant event. |
| `AdminSecurityPolicy` | `aquilia/admin/security.py` | See class attributes and constructor methods. | Central orchestrator for all admin security features. |
| `AdminConfig` | `aquilia/admin/site.py` | modules: dict[str, bool], audit_enabled: bool, audit_max_entries: int, audit_log_logins: bool, audit_log_views: bool, audit_log_searches: bool, audit_excluded_actions: frozenset[str], monitoring_enabled: bool, monitoring_metrics: frozenset[str], monitoring_refresh_interval: int, containers_config: dict[str, Any], pods_config: dict[str, Any], ... | Immutable admin configuration parsed from ``Integration.admin()`` config dict. |
| `AdminCacheIntegration` | `aquilia/admin/subsystems.py` | See class attributes and constructor methods. | Integrates Aquilia CacheService into admin operations. |
| `AdminWidget` | `aquilia/admin/widgets.py` | title: str, icon: str, size: WidgetSize, position: WidgetPosition, order: int, permission: str &#124; None, refresh_interval: int, css_classes: str, visible: bool | Base class for dashboard widgets. |
| `CountWidget` | `aquilia/admin/widgets.py` | model_name: str, filter_field: str &#124; None, filter_value: Any, color: str, count: int, change_percent: float &#124; None, trend: str, link: str, footer_text: str | Displays a count of records in a model. |
| `StatWidget` | `aquilia/admin/widgets.py` | value: str, value_fn: Callable &#124; None, change: str, trend: str, color: str, suffix: str, prefix: str, link: str, footer_text: str | Displays a single statistic value with trend. |
| `ChartWidget` | `aquilia/admin/widgets.py` | chart_type: str, labels: list[str], datasets: list[dict[str, Any]], data_fn: Callable &#124; None, color_scheme: str, show_legend: bool, height: int | Displays a chart (line, bar, pie, doughnut, area). |
| `RecentActivityWidget` | `aquilia/admin/widgets.py` | limit: int, actions: list[str] &#124; None, show_user: bool, show_timestamp: bool, show_model: bool | Displays recent admin activity log entries. |
| `TableWidget` | `aquilia/admin/widgets.py` | columns: list[str], rows: list[list[Any]], data_fn: Callable &#124; None, model_name: str, show_link: bool, max_rows: int | Displays a data table on the dashboard. |
| `ListWidget` | `aquilia/admin/widgets.py` | items: list[dict[str, Any]], items_fn: Callable &#124; None, show_icon: bool | Displays a simple list of items on the dashboard. |
| `ProgressWidget` | `aquilia/admin/widgets.py` | bars: list[dict[str, Any]], bars_fn: Callable &#124; None | Displays a progress bar or set of progress bars. |
| `CustomHTMLWidget` | `aquilia/admin/widgets.py` | html_content: str, html_fn: Callable &#124; None | Widget that renders custom HTML content. |

## Common Entry Points

- `AdminIntegration`
- `AdminConfig`
- `AdminSecurityPolicy`
- `ModelAdmin`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
