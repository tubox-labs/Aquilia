# Providers Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `RenderEnvVar` | `aquilia/providers/render/types.py` | key: str, value: str &#124; None, generate_value: str &#124; None | Environment variable - plain value or generated secret. |
| `RenderDisk` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, mount_path: str, size_gb: int, service_id: str &#124; None, created_at: str &#124; None | Persistent disk attached to a Render service. |
| `RenderDiskSnapshot` | `aquilia/providers/render/types.py` | id: str &#124; None, disk_id: str &#124; None, created_at: str &#124; None, status: str &#124; None | A snapshot of a persistent disk. |
| `RenderAutoscaling` | `aquilia/providers/render/types.py` | enabled: bool, min: int, max: int, criteria: dict[str, Any] &#124; None | Autoscaling configuration for a Render service. |
| `RenderDeploy` | `aquilia/providers/render/types.py` | id: str &#124; None, service_id: str &#124; None, status: str &#124; None, commit: dict[str, Any] &#124; None, image: dict[str, Any] &#124; None, created_at: str &#124; None, updated_at: str &#124; None, finished_at: str &#124; None, trigger: str &#124; None | A single deploy for a Render service. |
| `RenderService` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, owner_id: str &#124; None, slug: str &#124; None, type: RenderServiceType, plan: str &#124; None, region: str &#124; None, status: str &#124; None, suspended: str &#124; None, auto_deploy: str &#124; None, service_details: dict[str, Any] &#124; None, created_at: str &#124; None, ... | A Render service (top-level resource). |
| `RenderOwner` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, email: str &#124; None, type: str &#124; None | A Render workspace/owner (user or team). |
| `RenderSecretFile` | `aquilia/providers/render/types.py` | name: str, content: str | Secret file mounted into a service container. |
| `RenderCustomDomain` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, domain_type: str &#124; None, verification_status: str &#124; None, redirect_for_name: str &#124; None, created_at: str &#124; None, server: dict[str, Any] &#124; None | Custom domain attached to a Render service. |
| `RenderInstance` | `aquilia/providers/render/types.py` | id: str &#124; None, service_id: str &#124; None, status: str &#124; None, created_at: str &#124; None, updated_at: str &#124; None, region: str &#124; None, image_hash: str &#124; None | A running instance of a Render service. |
| `RenderEvent` | `aquilia/providers/render/types.py` | id: str &#124; None, service_id: str &#124; None, type: str &#124; None, timestamp: str &#124; None, details: dict[str, Any] &#124; None, status_code: int &#124; None | An event from the Render event stream. |
| `RenderJob` | `aquilia/providers/render/types.py` | id: str &#124; None, service_id: str &#124; None, status: str &#124; None, plan_id: str &#124; None, started_at: str &#124; None, finished_at: str &#124; None, created_at: str &#124; None | A cron or one-off job execution. |
| `RenderHeaderRule` | `aquilia/providers/render/types.py` | id: str &#124; None, path: str, name: str, value: str | HTTP header rule for a Render service. |
| `RenderRedirectRule` | `aquilia/providers/render/types.py` | id: str &#124; None, source: str, destination: str, type: str, status_code: int | Redirect / rewrite rule for static sites. |
| `RenderLogEntry` | `aquilia/providers/render/types.py` | timestamp: str &#124; None, message: str, level: str &#124; None, service_id: str &#124; None, instance_id: str &#124; None, deploy_id: str &#124; None, type: str &#124; None | A single log line from the Render logging API. |
| `RenderMetricPoint` | `aquilia/providers/render/types.py` | timestamp: str &#124; None, value: float, unit: str &#124; None, label: str &#124; None | A single metric data point. |
| `RenderWebhook` | `aquilia/providers/render/types.py` | id: str &#124; None, url: str, secret: str &#124; None, events: list[str], enabled: bool, created_at: str &#124; None, updated_at: str &#124; None | A Render webhook subscription. |
| `RenderProject` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, owner_id: str &#124; None, created_at: str &#124; None, updated_at: str &#124; None, environment_ids: list[str] | A Render project for organizing services. |
| `RenderEnvironment` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, project_id: str &#124; None, protected_status: str &#124; None, created_at: str &#124; None, updated_at: str &#124; None | A Render environment within a project. |
| `RenderEnvGroup` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, owner_id: str &#124; None, env_vars: list[RenderEnvVar], secret_files: list[RenderSecretFile], service_links: list[str], created_at: str &#124; None, updated_at: str &#124; None | A shared environment group for linked services. |
| `RenderRegistryCredential` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, registry: str, username: str, created_at: str &#124; None | Private container registry credential. |
| `RenderMaintenance` | `aquilia/providers/render/types.py` | id: str &#124; None, service_id: str &#124; None, status: str &#124; None, scheduled_at: str &#124; None, started_at: str &#124; None, completed_at: str &#124; None, description: str &#124; None | Maintenance window for a Render service. |
| `RenderNotificationSettings` | `aquilia/providers/render/types.py` | notify_on_fail: str &#124; None, preview_notify_on_fail: str &#124; None | Notification settings for a service. |
| `RenderAuditLogEntry` | `aquilia/providers/render/types.py` | id: str &#124; None, action: str &#124; None, actor: dict[str, Any] &#124; None, resource: dict[str, Any] &#124; None, timestamp: str &#124; None, details: dict[str, Any] &#124; None | An entry from the workspace audit log. |
| `RenderPostgresInstance` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, owner_id: str &#124; None, plan: str &#124; None, region: str &#124; None, status: str &#124; None, version: str &#124; None, disk_size_gb: int &#124; None, created_at: str &#124; None, updated_at: str &#124; None, dashboard_url: str &#124; None, primary_postgres_id: str &#124; None, ... | A Render Postgres database instance. |
| `RenderPostgresConnectionInfo` | `aquilia/providers/render/types.py` | internal_connection_string: str &#124; None, external_connection_string: str &#124; None, psql_command: str &#124; None, host: str &#124; None, port: int &#124; None, database: str &#124; None, user: str &#124; None, password: str &#124; None | Connection info for a Render Postgres database. |
| `RenderPostgresUser` | `aquilia/providers/render/types.py` | name: str, password: str &#124; None, grants: list[str] | A user in a Render Postgres database. |
| `RenderKeyValueInstance` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, owner_id: str &#124; None, plan: str &#124; None, region: str &#124; None, status: str &#124; None, max_memory_policy: str &#124; None, created_at: str &#124; None, updated_at: str &#124; None | A Render Key-Value (Redis) store instance. |
| `RenderKeyValueConnectionInfo` | `aquilia/providers/render/types.py` | internal_connection_string: str &#124; None, external_connection_string: str &#124; None, host: str &#124; None, port: int &#124; None, password: str &#124; None | Connection info for a Render Key-Value store. |
| `RenderBlueprint` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, status: str &#124; None, auto_sync: bool, repo: str &#124; None, branch: str &#124; None, owner_id: str &#124; None, created_at: str &#124; None, updated_at: str &#124; None, last_sync: dict[str, Any] &#124; None | A Render Blueprint (Infrastructure as Code). |
| `RenderBlueprintSync` | `aquilia/providers/render/types.py` | id: str &#124; None, blueprint_id: str &#124; None, status: str &#124; None, started_at: str &#124; None, completed_at: str &#124; None, error: str &#124; None | A blueprint sync run. |
| `RenderWorkspaceMember` | `aquilia/providers/render/types.py` | id: str &#124; None, email: str &#124; None, name: str &#124; None, role: str &#124; None, joined_at: str &#124; None | A member of a Render workspace/team. |
| `RenderLogStream` | `aquilia/providers/render/types.py` | id: str &#124; None, name: str, endpoint: str, token: str &#124; None, enabled: bool, created_at: str &#124; None | A log stream/sink for forwarding logs. |
| `RenderMetricsFilter` | `aquilia/providers/render/types.py` | resource_id: str &#124; None, metric: str, period: str, start_time: str &#124; None, end_time: str &#124; None, instance_id: str &#124; None | Filter/query parameters for the metrics API. |
| `RenderDeployConfig` | `aquilia/providers/render/types.py` | service_name: str, service_type: RenderServiceType, owner_id: str &#124; None, image: str, plan: RenderPlan, region: str, num_instances: int, autoscaling: RenderAutoscaling, port: int, health_check_path: str, env_vars: list[RenderEnvVar], disk: RenderDisk &#124; None, ... | Complete deployment configuration for ``aq deploy render``. |
| `RenderEnvVar` | `aquilia/providers/render_backup_phase10/types.py` | key: str, value: str &#124; None, generate_value: str &#124; None | Environment variable - plain value or generated secret. |
| `RenderDisk` | `aquilia/providers/render_backup_phase10/types.py` | name: str, mount_path: str, size_gb: int | Persistent disk attached to a Render service. |
| `RenderAutoscaling` | `aquilia/providers/render_backup_phase10/types.py` | enabled: bool, min: int, max: int, criteria: dict[str, Any] &#124; None | Autoscaling configuration for a Render service. |
| `RenderDeploy` | `aquilia/providers/render_backup_phase10/types.py` | id: str &#124; None, service_id: str &#124; None, status: str &#124; None, commit: dict[str, Any] &#124; None, image: dict[str, Any] &#124; None, created_at: str &#124; None, updated_at: str &#124; None, finished_at: str &#124; None | A single deploy for a Render service. |
| `RenderService` | `aquilia/providers/render_backup_phase10/types.py` | id: str &#124; None, name: str, owner_id: str &#124; None, slug: str &#124; None, type: RenderServiceType, plan: str &#124; None, region: str &#124; None, status: str &#124; None, suspended: str &#124; None, auto_deploy: str &#124; None, service_details: dict[str, Any] &#124; None, created_at: str &#124; None, ... | A Render service (top-level resource, no App grouping). |
| `RenderOwner` | `aquilia/providers/render_backup_phase10/types.py` | id: str &#124; None, name: str, email: str &#124; None, type: str &#124; None | A Render workspace/owner (user or team). |
| `RenderDeployConfig` | `aquilia/providers/render_backup_phase10/types.py` | service_name: str, service_type: RenderServiceType, owner_id: str &#124; None, image: str, plan: RenderPlan, region: str, num_instances: int, autoscaling: RenderAutoscaling, port: int, health_check_path: str, env_vars: list[RenderEnvVar], disk: RenderDisk &#124; None, ... | Complete deployment configuration for ``aq deploy render``. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

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
