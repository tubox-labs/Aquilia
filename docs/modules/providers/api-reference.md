# Providers API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `RenderClient` | `aquilia/providers/render/client.py` | object | Synchronous REST client for the Render API (v1). |
| `DeployResult` | `aquilia/providers/render/deployer.py` | object | Result of a Render deployment operation. |
| `RenderDeployer` | `aquilia/providers/render/deployer.py` | object | Full-lifecycle Render deployment orchestrator. |
| `RenderCredentialStore` | `aquilia/providers/render/store.py` | object | Military-grade, file-based credential store for Render API tokens. |
| `RenderServiceType` | `aquilia/providers/render/types.py` | str, Enum | Render service type. |
| `RenderPlan` | `aquilia/providers/render/types.py` | str, Enum | Render compute plans. |
| `RenderDeployStatus` | `aquilia/providers/render/types.py` | str, Enum | Deploy lifecycle states returned by the Render API. |
| `RenderRegion` | `aquilia/providers/render/types.py` | str, Enum | Common Render deployment regions. |
| `RenderServiceStatus` | `aquilia/providers/render/types.py` | str, Enum | Service runtime statuses. |
| `RenderJobStatus` | `aquilia/providers/render/types.py` | str, Enum | Cron / one-off job execution states. |
| `RenderDomainVerificationStatus` | `aquilia/providers/render/types.py` | str, Enum | Custom domain DNS verification statuses. |
| `RenderLogLevel` | `aquilia/providers/render/types.py` | str, Enum | Log severity levels for the Render logging API. |
| `RenderLogDirection` | `aquilia/providers/render/types.py` | str, Enum | Direction for paginating logs. |
| `RenderLogType` | `aquilia/providers/render/types.py` | str, Enum | Render log types. |
| `RenderRouteType` | `aquilia/providers/render/types.py` | str, Enum | Redirect/rewrite route types for static sites. |
| `RenderMaintenanceStatus` | `aquilia/providers/render/types.py` | str, Enum | Maintenance window states. |
| `RenderWebhookEventType` | `aquilia/providers/render/types.py` | str, Enum | Event types for webhook subscriptions. |
| `RenderNotificationType` | `aquilia/providers/render/types.py` | str, Enum | Notification delivery channels. |
| `RenderPostgresPlan` | `aquilia/providers/render/types.py` | str, Enum | Render Postgres plans. |
| `RenderKeyValuePlan` | `aquilia/providers/render/types.py` | str, Enum | Render Key-Value (Redis) store plans. |
| `RenderBlueprintSyncStatus` | `aquilia/providers/render/types.py` | str, Enum | Blueprint sync / IaC sync status. |
| `RenderInstanceStatus` | `aquilia/providers/render/types.py` | str, Enum | Runtime instance statuses. |
| `RenderEnvVar` | `aquilia/providers/render/types.py` | object | Environment variable - plain value or generated secret. |
| `RenderDisk` | `aquilia/providers/render/types.py` | object | Persistent disk attached to a Render service. |
| `RenderDiskSnapshot` | `aquilia/providers/render/types.py` | object | A snapshot of a persistent disk. |
| `RenderAutoscaling` | `aquilia/providers/render/types.py` | object | Autoscaling configuration for a Render service. |
| `RenderDeploy` | `aquilia/providers/render/types.py` | object | A single deploy for a Render service. |
| `RenderService` | `aquilia/providers/render/types.py` | object | A Render service (top-level resource). |
| `RenderOwner` | `aquilia/providers/render/types.py` | object | A Render workspace/owner (user or team). |
| `RenderSecretFile` | `aquilia/providers/render/types.py` | object | Secret file mounted into a service container. |
| `RenderCustomDomain` | `aquilia/providers/render/types.py` | object | Custom domain attached to a Render service. |
| `RenderInstance` | `aquilia/providers/render/types.py` | object | A running instance of a Render service. |
| `RenderEvent` | `aquilia/providers/render/types.py` | object | An event from the Render event stream. |
| `RenderJob` | `aquilia/providers/render/types.py` | object | A cron or one-off job execution. |
| `RenderHeaderRule` | `aquilia/providers/render/types.py` | object | HTTP header rule for a Render service. |
| `RenderRedirectRule` | `aquilia/providers/render/types.py` | object | Redirect / rewrite rule for static sites. |
| `RenderLogEntry` | `aquilia/providers/render/types.py` | object | A single log line from the Render logging API. |
| `RenderMetricPoint` | `aquilia/providers/render/types.py` | object | A single metric data point. |
| `RenderWebhook` | `aquilia/providers/render/types.py` | object | A Render webhook subscription. |
| `RenderProject` | `aquilia/providers/render/types.py` | object | A Render project for organizing services. |
| `RenderEnvironment` | `aquilia/providers/render/types.py` | object | A Render environment within a project. |
| `RenderEnvGroup` | `aquilia/providers/render/types.py` | object | A shared environment group for linked services. |
| `RenderRegistryCredential` | `aquilia/providers/render/types.py` | object | Private container registry credential. |
| `RenderMaintenance` | `aquilia/providers/render/types.py` | object | Maintenance window for a Render service. |
| `RenderNotificationSettings` | `aquilia/providers/render/types.py` | object | Notification settings for a service. |
| `RenderAuditLogEntry` | `aquilia/providers/render/types.py` | object | An entry from the workspace audit log. |
| `RenderPostgresInstance` | `aquilia/providers/render/types.py` | object | A Render Postgres database instance. |
| `RenderPostgresConnectionInfo` | `aquilia/providers/render/types.py` | object | Connection info for a Render Postgres database. |
| `RenderPostgresUser` | `aquilia/providers/render/types.py` | object | A user in a Render Postgres database. |
| `RenderKeyValueInstance` | `aquilia/providers/render/types.py` | object | A Render Key-Value (Redis) store instance. |
| `RenderKeyValueConnectionInfo` | `aquilia/providers/render/types.py` | object | Connection info for a Render Key-Value store. |
| `RenderBlueprint` | `aquilia/providers/render/types.py` | object | A Render Blueprint (Infrastructure as Code). |
| `RenderBlueprintSync` | `aquilia/providers/render/types.py` | object | A blueprint sync run. |
| `RenderWorkspaceMember` | `aquilia/providers/render/types.py` | object | A member of a Render workspace/team. |
| `RenderLogStream` | `aquilia/providers/render/types.py` | object | A log stream/sink for forwarding logs. |
| `RenderMetricsFilter` | `aquilia/providers/render/types.py` | object | Filter/query parameters for the metrics API. |
| `RenderDeployConfig` | `aquilia/providers/render/types.py` | object | Complete deployment configuration for ``aq deploy render``. |
| `RenderClient` | `aquilia/providers/render_backup_phase10/client.py` | object | Synchronous REST client for the Render API (v1). |
| `DeployResult` | `aquilia/providers/render_backup_phase10/deployer.py` | object | Result of a Render deployment operation. |
| `RenderDeployer` | `aquilia/providers/render_backup_phase10/deployer.py` | object | Full-lifecycle Render deployment orchestrator. |
| `RenderCredentialStore` | `aquilia/providers/render_backup_phase10/store.py` | object | Secure, file-based credential store for Render API tokens. |
| `RenderServiceType` | `aquilia/providers/render_backup_phase10/types.py` | str, Enum | Render service type. |
| `RenderPlan` | `aquilia/providers/render_backup_phase10/types.py` | str, Enum | Render compute plans. |
| `RenderDeployStatus` | `aquilia/providers/render_backup_phase10/types.py` | str, Enum | Deploy lifecycle states returned by the Render API. |
| `RenderRegion` | `aquilia/providers/render_backup_phase10/types.py` | str, Enum | Common Render deployment regions. |
| `RenderEnvVar` | `aquilia/providers/render_backup_phase10/types.py` | object | Environment variable - plain value or generated secret. |
| `RenderDisk` | `aquilia/providers/render_backup_phase10/types.py` | object | Persistent disk attached to a Render service. |
| `RenderAutoscaling` | `aquilia/providers/render_backup_phase10/types.py` | object | Autoscaling configuration for a Render service. |
| `RenderDeploy` | `aquilia/providers/render_backup_phase10/types.py` | object | A single deploy for a Render service. |
| `RenderService` | `aquilia/providers/render_backup_phase10/types.py` | object | A Render service (top-level resource, no App grouping). |
| `RenderOwner` | `aquilia/providers/render_backup_phase10/types.py` | object | A Render workspace/owner (user or team). |
| `RenderDeployConfig` | `aquilia/providers/render_backup_phase10/types.py` | object | Complete deployment configuration for ``aq deploy render``. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| None detected |  |  |  |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_BASE_URL` | `aquilia/providers/render/client.py` | `'https://api.render.com/v1'` |
| `_USER_AGENT` | `aquilia/providers/render/client.py` | `'Aquilia-CLI/2.0'` |
| `_DEFAULT_TIMEOUT` | `aquilia/providers/render/client.py` | `30` |
| `_MAX_RETRIES` | `aquilia/providers/render/client.py` | `3` |
| `_RETRY_BACKOFF` | `aquilia/providers/render/client.py` | `1.5` |
| `_SSL_CTX` | `aquilia/providers/render/client.py` | `ssl.SSLContext` |
| `_CROUS_MAGIC` | `aquilia/providers/render/store.py` | `b'AQCR'` |
| `_CROUS_VERSION` | `aquilia/providers/render/store.py` | `2` |
| `_CROUS_VERSION_LEGACY` | `aquilia/providers/render/store.py` | `1` |
| `_SALT_SIZE` | `aquilia/providers/render/store.py` | `32` |
| `_NONCE_SIZE` | `aquilia/providers/render/store.py` | `12` |
| `_KEY_ITERATIONS` | `aquilia/providers/render/store.py` | `600000` |
| `_HMAC_ALGO` | `aquilia/providers/render/store.py` | `'sha512'` |
| `_TAG_SIZE` | `aquilia/providers/render/store.py` | `16` |
| `_CANARY_PLAINTEXT` | `aquilia/providers/render/store.py` | `b'AQUILIA_CANARY_OK'` |
| `_CANARY_SIZE` | `aquilia/providers/render/store.py` | `32` |
| `_DEFAULT_TTL` | `aquilia/providers/render/store.py` | `0` |
| `_MAX_TOKEN_SIZE` | `aquilia/providers/render/store.py` | `8192` |
| `_CIPHER_AES_GCM` | `aquilia/providers/render/store.py` | `1` |
| `_CIPHER_XOR_HMAC` | `aquilia/providers/render/store.py` | `3` |
| `_AUDIT_MAX_BYTES` | `aquilia/providers/render/store.py` | `1048576` |
| `_BASE_URL` | `aquilia/providers/render_backup_phase10/client.py` | `'https://api.render.com/v1'` |
| `_USER_AGENT` | `aquilia/providers/render_backup_phase10/client.py` | `'Aquilia-CLI/1.0'` |
| `_DEFAULT_TIMEOUT` | `aquilia/providers/render_backup_phase10/client.py` | `30` |
| `_MAX_RETRIES` | `aquilia/providers/render_backup_phase10/client.py` | `3` |
| `_RETRY_BACKOFF` | `aquilia/providers/render_backup_phase10/client.py` | `1.5` |
| `_SSL_CTX` | `aquilia/providers/render_backup_phase10/client.py` | `ssl.SSLContext` |
| `_CROUS_MAGIC` | `aquilia/providers/render_backup_phase10/store.py` | `b'AQCR'` |
| `_CROUS_VERSION` | `aquilia/providers/render_backup_phase10/store.py` | `1` |
| `_SALT_SIZE` | `aquilia/providers/render_backup_phase10/store.py` | `32` |
| `_KEY_ITERATIONS` | `aquilia/providers/render_backup_phase10/store.py` | `200000` |
| `_HMAC_ALGO` | `aquilia/providers/render_backup_phase10/store.py` | `'sha256'` |
| `_DEFAULT_STORE_DIR` | `aquilia/providers/render_backup_phase10/store.py` | `Path.home() / '.aquilia' / 'providers' / 'render'` |

## Detailed Classes And Methods

### Class: `RenderClient`

- Source: `aquilia/providers/render/client.py`
- Bases: `object`
- Summary: Synchronous REST client for the Render API (v1).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `list_services` | `def list_services(self, *, name: str &#124; None = None, type: str &#124; None = None, region: str &#124; None = None, suspended: str &#124; None = None, owner_id: str &#124; None = None, cursor: str &#124; None = None, limit: int = 20) -> list[RenderService]` |  | List all services, optionally filtered. |
| `get_service` | `def get_service(self, service_id: str) -> RenderService` |  | Get a specific service by ID. |
| `get_service_by_name` | `def get_service_by_name(self, name: str, owner_id: str &#124; None = None) -> RenderService &#124; None` |  | Find a service by name. |
| `create_service` | `def create_service(self, payload: dict[str, Any]) -> RenderService` |  | Create a new service. |
| `update_service` | `def update_service(self, service_id: str, payload: dict[str, Any]) -> RenderService` |  | Update an existing service (PATCH). |
| `delete_service` | `def delete_service(self, service_id: str) -> None` |  | Delete a service. |
| `suspend_service` | `def suspend_service(self, service_id: str) -> None` |  | Suspend a running service. |
| `resume_service` | `def resume_service(self, service_id: str) -> None` |  | Resume a suspended service. |
| `restart_service` | `def restart_service(self, service_id: str) -> None` |  | Restart a running service (zero-downtime). |
| `purge_cache` | `def purge_cache(self, service_id: str) -> None` |  | Clear the build cache for a service. |
| `create_preview` | `def create_preview(self, service_id: str, *, image_url: str &#124; None = None, name: str &#124; None = None) -> RenderService` |  | Create a preview instance of a service. |
| `list_deploys` | `def list_deploys(self, service_id: str, *, cursor: str &#124; None = None, limit: int = 10) -> list[RenderDeploy]` |  | List deploys for a service. |
| `get_deploy` | `def get_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy` |  | Get a specific deploy. |
| `trigger_deploy` | `def trigger_deploy(self, service_id: str) -> RenderDeploy` |  | Trigger a new deploy. |
| `cancel_deploy` | `def cancel_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy` |  | Cancel a running deploy. |
| `rollback_deploy` | `def rollback_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy` |  | Rollback to a previous deploy. |
| `list_env_vars` | `def list_env_vars(self, service_id: str) -> list[dict[str, Any]]` |  | List all environment variables for a service. |
| `update_env_vars` | `def update_env_vars(self, service_id: str, env_vars: list[dict[str, Any]]) -> list[dict[str, Any]]` |  | Bulk update environment variables for a service. |
| `get_env_var` | `def get_env_var(self, service_id: str, key: str) -> dict[str, Any] &#124; None` |  | Get a specific environment variable. |
| `delete_env_var` | `def delete_env_var(self, service_id: str, key: str) -> None` |  | Delete a specific environment variable. |
| `list_custom_domains` | `def list_custom_domains(self, service_id: str) -> list[dict[str, Any]]` |  | List custom domains for a service. |
| `add_custom_domain` | `def add_custom_domain(self, service_id: str, domain_name: str) -> dict[str, Any]` |  | Add a custom domain to a service. |
| `delete_custom_domain` | `def delete_custom_domain(self, service_id: str, domain_name: str) -> None` |  | Remove a custom domain. |
| `verify_dns` | `def verify_dns(self, service_id: str, domain_name: str) -> dict[str, Any]` |  | Verify DNS configuration for a custom domain. |
| `list_secret_files` | `def list_secret_files(self, service_id: str) -> list[RenderSecretFile]` |  | List secret files for a service. |
| `update_secret_files` | `def update_secret_files(self, service_id: str, files: list[dict[str, str]]) -> list[RenderSecretFile]` |  | Bulk update secret files (PUT replaces all). |
| `delete_secret_file` | `def delete_secret_file(self, service_id: str, name: str) -> None` |  | Delete a specific secret file. |
| `list_headers` | `def list_headers(self, service_id: str) -> list[RenderHeaderRule]` |  | List HTTP header rules for a service. |
| `add_header` | `def add_header(self, service_id: str, header: dict[str, str]) -> RenderHeaderRule` |  | Add an HTTP header rule. |
| `delete_header` | `def delete_header(self, service_id: str, header_id: str) -> None` |  | Delete an HTTP header rule. |
| `list_redirect_rules` | `def list_redirect_rules(self, service_id: str) -> list[RenderRedirectRule]` |  | List redirect/rewrite rules. |
| `add_redirect_rule` | `def add_redirect_rule(self, service_id: str, rule: dict[str, Any]) -> RenderRedirectRule` |  | Add a redirect/rewrite rule. |
| `delete_redirect_rule` | `def delete_redirect_rule(self, service_id: str, rule_id: str) -> None` |  | Delete a redirect/rewrite rule. |
| `list_instances` | `def list_instances(self, service_id: str) -> list[RenderInstance]` |  | List running instances of a service. |
| `list_events` | `def list_events(self, service_id: str, *, cursor: str &#124; None = None, limit: int = 20) -> list[RenderEvent]` |  | List events for a service. |
| `list_jobs` | `def list_jobs(self, service_id: str, *, cursor: str &#124; None = None, limit: int = 20) -> list[RenderJob]` |  | List job executions for a cron service. |
| `trigger_job` | `def trigger_job(self, service_id: str) -> RenderJob` |  | Manually trigger a cron job execution. |
| `cancel_job` | `def cancel_job(self, service_id: str, job_id: str) -> RenderJob` |  | Cancel a running job. |
| `set_autoscaling` | `def set_autoscaling(self, service_id: str, config: dict[str, Any]) -> dict[str, Any]` |  | Configure autoscaling for a service. |
| `remove_autoscaling` | `def remove_autoscaling(self, service_id: str) -> None` |  | Remove autoscaling from a service. |
| `scale_service` | `def scale_service(self, service_id: str, num_instances: int) -> None` |  | Manually scale a service to a specific instance count. |
| `list_disks` | `def list_disks(self, service_id: str) -> list[dict[str, Any]]` |  | List persistent disks for a service. |
| `create_disk` | `def create_disk(self, service_id: str, payload: dict[str, Any]) -> dict[str, Any]` |  | Create a persistent disk. |
| `delete_disk` | `def delete_disk(self, disk_id: str) -> None` |  | Delete a persistent disk. |
| `list_disk_snapshots` | `def list_disk_snapshots(self, disk_id: str) -> list[RenderDiskSnapshot]` |  | List snapshots for a persistent disk. |
| `restore_disk_snapshot` | `def restore_disk_snapshot(self, disk_id: str, snapshot_id: str) -> dict[str, Any]` |  | Restore a persistent disk from a snapshot. |
| `get_logs` | `def get_logs(self, *, owner_id: str &#124; None = None, service_id: str &#124; None = None, direction: str = 'backward', limit: int = 100, start_time: str &#124; None = None, end_time: str &#124; None = None, level: str &#124; None = None, log_type: str &#124; None = None, text: str &#124; None = None, instance_id: str &#124; None = None) -> list[RenderLogEntry]` |  | Retrieve logs from the Render logging API. |
| `get_metrics` | `def get_metrics(self, service_id: str, *, metric: str = 'cpu', period: str = '1h', start_time: str &#124; None = None, end_time: str &#124; None = None, instance_id: str &#124; None = None) -> list[RenderMetricPoint]` |  | Retrieve service metrics (CPU, memory, HTTP, bandwidth, disk). |
| `get_metrics_filtered` | `def get_metrics_filtered(self, flt: RenderMetricsFilter) -> list[RenderMetricPoint]` |  | Retrieve metrics using a RenderMetricsFilter object. |
| `list_postgres` | `def list_postgres(self, *, owner_id: str &#124; None = None, cursor: str &#124; None = None, limit: int = 20) -> list[RenderPostgresInstance]` |  | List Postgres database instances. |
| `create_postgres` | `def create_postgres(self, payload: dict[str, Any]) -> RenderPostgresInstance` |  | Create a new Postgres database. |
| `get_postgres` | `def get_postgres(self, postgres_id: str) -> RenderPostgresInstance` |  | Get a specific Postgres instance. |
| `delete_postgres` | `def delete_postgres(self, postgres_id: str) -> None` |  | Delete a Postgres database. |
| `get_postgres_connection_info` | `def get_postgres_connection_info(self, postgres_id: str) -> RenderPostgresConnectionInfo` |  | Get connection info for a Postgres database. |
| `list_postgres_users` | `def list_postgres_users(self, postgres_id: str) -> list[RenderPostgresUser]` |  | List users in a Postgres database. |
| `create_postgres_user` | `def create_postgres_user(self, postgres_id: str, name: str) -> RenderPostgresUser` |  | Create a new Postgres user. |
| `delete_postgres_user` | `def delete_postgres_user(self, postgres_id: str, user_name: str) -> None` |  | Delete a Postgres user. |
| `list_key_value` | `def list_key_value(self, *, owner_id: str &#124; None = None, cursor: str &#124; None = None, limit: int = 20) -> list[RenderKeyValueInstance]` |  | List Key-Value (Redis) store instances. |
| `create_key_value` | `def create_key_value(self, payload: dict[str, Any]) -> RenderKeyValueInstance` |  | Create a new Key-Value store. |
| `get_key_value` | `def get_key_value(self, kv_id: str) -> RenderKeyValueInstance` |  | Get a specific Key-Value instance. |
| `delete_key_value` | `def delete_key_value(self, kv_id: str) -> None` |  | Delete a Key-Value store. |
| `get_key_value_connection_info` | `def get_key_value_connection_info(self, kv_id: str) -> RenderKeyValueConnectionInfo` |  | Get connection info for a Key-Value store. |
| `list_projects` | `def list_projects(self, *, owner_id: str &#124; None = None, cursor: str &#124; None = None, limit: int = 20) -> list[RenderProject]` |  | List projects. |
| `create_project` | `def create_project(self, payload: dict[str, Any]) -> RenderProject` |  | Create a new project. |
| `get_project` | `def get_project(self, project_id: str) -> RenderProject` |  | Get a specific project. |
| `delete_project` | `def delete_project(self, project_id: str) -> None` |  | Delete a project. |
| `list_environments` | `def list_environments(self, project_id: str) -> list[RenderEnvironment]` |  | List environments for a project. |
| `create_environment` | `def create_environment(self, project_id: str, payload: dict[str, Any]) -> RenderEnvironment` |  | Create a new environment in a project. |
| `delete_environment` | `def delete_environment(self, project_id: str, environment_id: str) -> None` |  | Delete an environment. |
| `list_env_groups` | `def list_env_groups(self, *, owner_id: str &#124; None = None, cursor: str &#124; None = None, limit: int = 20) -> list[RenderEnvGroup]` |  | List environment groups. |
| `create_env_group` | `def create_env_group(self, payload: dict[str, Any]) -> RenderEnvGroup` |  | Create a new environment group. |
| `get_env_group` | `def get_env_group(self, env_group_id: str) -> RenderEnvGroup` |  | Get a specific environment group. |
| `update_env_group` | `def update_env_group(self, env_group_id: str, payload: dict[str, Any]) -> RenderEnvGroup` |  | Update an environment group. |
| `delete_env_group` | `def delete_env_group(self, env_group_id: str) -> None` |  | Delete an environment group. |
| `link_service_to_env_group` | `def link_service_to_env_group(self, env_group_id: str, service_id: str) -> None` |  | Link a service to an environment group. |
| `unlink_service_from_env_group` | `def unlink_service_from_env_group(self, env_group_id: str, service_id: str) -> None` |  | Unlink a service from an environment group. |
| `list_registry_credentials` | `def list_registry_credentials(self, *, owner_id: str &#124; None = None) -> list[RenderRegistryCredential]` |  | List private registry credentials. |
| `create_registry_credential` | `def create_registry_credential(self, payload: dict[str, Any]) -> RenderRegistryCredential` |  | Create a private registry credential. |
| `delete_registry_credential` | `def delete_registry_credential(self, credential_id: str) -> None` |  | Delete a registry credential. |
| `list_blueprints` | `def list_blueprints(self, *, owner_id: str &#124; None = None, cursor: str &#124; None = None, limit: int = 20) -> list[RenderBlueprint]` |  | List blueprints. |
| `get_blueprint` | `def get_blueprint(self, blueprint_id: str) -> RenderBlueprint` |  | Get a specific blueprint. |
| `sync_blueprint` | `def sync_blueprint(self, blueprint_id: str) -> RenderBlueprintSync` |  | Trigger a blueprint sync. |
| `list_webhooks` | `def list_webhooks(self, *, owner_id: str &#124; None = None) -> list[RenderWebhook]` |  | List webhooks. |
| `create_webhook` | `def create_webhook(self, payload: dict[str, Any]) -> RenderWebhook` |  | Create a webhook subscription. |
| `get_webhook` | `def get_webhook(self, webhook_id: str) -> RenderWebhook` |  | Get a specific webhook. |
| `update_webhook` | `def update_webhook(self, webhook_id: str, payload: dict[str, Any]) -> RenderWebhook` |  | Update a webhook. |
| `delete_webhook` | `def delete_webhook(self, webhook_id: str) -> None` |  | Delete a webhook. |
| `list_maintenance_windows` | `def list_maintenance_windows(self, service_id: str) -> list[RenderMaintenance]` |  | List maintenance windows for a service. |
| `trigger_maintenance` | `def trigger_maintenance(self, service_id: str) -> RenderMaintenance` |  | Trigger maintenance for a service. |
| `get_notification_settings` | `def get_notification_settings(self, service_id: str) -> RenderNotificationSettings` |  | Get notification settings for a service. |
| `update_notification_settings` | `def update_notification_settings(self, service_id: str, payload: dict[str, str]) -> RenderNotificationSettings` |  | Update notification settings for a service. |
| `list_log_streams` | `def list_log_streams(self, *, owner_id: str &#124; None = None) -> list[RenderLogStream]` |  | List log stream sinks. |
| `create_log_stream` | `def create_log_stream(self, payload: dict[str, Any]) -> RenderLogStream` |  | Create a log stream sink. |
| `delete_log_stream` | `def delete_log_stream(self, log_stream_id: str) -> None` |  | Delete a log stream sink. |
| `get_user` | `def get_user(self) -> dict[str, Any]` |  | Get the authenticated user's details. |
| `list_owners` | `def list_owners(self) -> list[RenderOwner]` |  | List owners (workspaces) for the authenticated user. |
| `list_workspace_members` | `def list_workspace_members(self, owner_id: str) -> list[RenderWorkspaceMember]` |  | List members of a workspace/team. |
| `validate_token` | `def validate_token(self) -> bool` |  | Validate the API token by fetching owner info. |
| `list_audit_logs` | `def list_audit_logs(self, owner_id: str, *, cursor: str &#124; None = None, limit: int = 50) -> list[RenderAuditLogEntry]` |  | List audit log entries for a workspace. |

### Class: `DeployResult`

- Source: `aquilia/providers/render/deployer.py`
- Bases: `object`
- Summary: Result of a Render deployment operation.

### Class: `RenderDeployer`

- Source: `aquilia/providers/render/deployer.py`
- Bases: `object`
- Summary: Full-lifecycle Render deployment orchestrator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `deploy` | `def deploy(self) -> DeployResult` |  | Execute the complete deployment pipeline. |
| `rollback` | `def rollback(self, deploy_id: str &#124; None = None) -> DeployResult` |  | Rollback to a previous deployment. |
| `cancel` | `def cancel(self, service_id: str &#124; None = None, deploy_id: str &#124; None = None) -> bool` |  | Cancel a running deployment. |
| `create_preview` | `def create_preview(self, *, name: str &#124; None = None) -> DeployResult` |  | Create a preview environment of the service. |
| `restart` | `def restart(self) -> bool` |  | Restart the service (zero-downtime). |
| `purge_cache` | `def purge_cache(self) -> bool` |  | Clear the build cache for the service. |
| `get_deploy_logs` | `def get_deploy_logs(self, *, limit: int = 100, level: str &#124; None = None) -> list[RenderLogEntry]` |  | Get recent logs for the service. |
| `get_service_metrics` | `def get_service_metrics(self, *, metric: str = 'cpu', period: str = '1h') -> list[RenderMetricPoint]` |  | Get metrics for the service. |
| `destroy` | `def destroy(self) -> bool` |  | Destroy the service. |
| `status` | `def status(self) -> dict[str, Any]` |  | Get current deployment status with extended info. |

### Class: `RenderCredentialStore`

- Source: `aquilia/providers/render/store.py`
- Bases: `object`
- Summary: Military-grade, file-based credential store for Render API tokens.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `credentials_path` | `def credentials_path(self) -> Path` | property | Method. |
| `config_path` | `def config_path(self) -> Path` | property | Method. |
| `is_configured` | `def is_configured(self) -> bool` |  | Method. |
| `save` | `def save(self, token: str, *, owner_name: str &#124; None = None, default_region: str = 'oregon', metadata: dict[str, Any] &#124; None = None) -> None` |  | Encrypt and store the API token with military-grade security. |
| `load` | `def load(self) -> str &#124; None` |  | Load and decrypt the stored API token. |
| `load_config` | `def load_config(self) -> dict[str, Any]` |  | Load non-sensitive provider configuration. |
| `get_default_region` | `def get_default_region(self) -> str` |  | Method. |
| `get_owner_name` | `def get_owner_name(self) -> str &#124; None` |  | Method. |
| `get_token_age` | `def get_token_age(self) -> float &#124; None` |  | Get the age of the stored token in seconds. |
| `is_expired` | `def is_expired(self) -> bool` |  | Check if the stored token has expired. |
| `clear` | `def clear(self) -> None` |  | Securely delete stored credentials. |
| `rotate` | `def rotate(self, new_token: str &#124; None = None) -> None` |  | Rotate credentials - re-encrypt with new key material. |
| `get_audit_log` | `def get_audit_log(self, limit: int = 50) -> list[dict[str, Any]]` |  | Read the most recent audit log entries. |
| `status` | `def status(self) -> dict[str, Any]` |  | Return credential store status (for CLI display). |

### Class: `RenderServiceType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render service type.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `WEB_SERVICE` |  | `'web_service'` |
| `PRIVATE_SERVICE` |  | `'private_service'` |
| `BACKGROUND_WORKER` |  | `'background_worker'` |
| `CRON_JOB` |  | `'cron_job'` |
| `STATIC_SITE` |  | `'static_site'` |

### Class: `RenderPlan`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render compute plans.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FREE` |  | `'free'` |
| `STARTER` |  | `'starter'` |
| `STANDARD` |  | `'standard'` |
| `PRO` |  | `'pro'` |
| `PRO_PLUS` |  | `'pro_plus'` |
| `PRO_MAX` |  | `'pro_max'` |
| `PRO_ULTRA` |  | `'pro_ultra'` |

### Class: `RenderDeployStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Deploy lifecycle states returned by the Render API.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CREATED` |  | `'created'` |
| `BUILD_IN_PROGRESS` |  | `'build_in_progress'` |
| `UPDATE_IN_PROGRESS` |  | `'update_in_progress'` |
| `LIVE` |  | `'live'` |
| `DEACTIVATED` |  | `'deactivated'` |
| `BUILD_FAILED` |  | `'build_failed'` |
| `UPDATE_FAILED` |  | `'update_failed'` |
| `CANCELED` |  | `'canceled'` |
| `PRE_DEPLOY_IN_PROGRESS` |  | `'pre_deploy_in_progress'` |
| `PRE_DEPLOY_FAILED` |  | `'pre_deploy_failed'` |

### Class: `RenderRegion`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Common Render deployment regions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `OREGON` |  | `'oregon'` |
| `FRANKFURT` |  | `'frankfurt'` |
| `OHIO` |  | `'ohio'` |
| `VIRGINIA` |  | `'virginia'` |
| `SINGAPORE` |  | `'singapore'` |

### Class: `RenderServiceStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Service runtime statuses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CREATING` |  | `'creating'` |
| `DEPLOYING` |  | `'deploying'` |
| `LIVE` |  | `'live'` |
| `SUSPENDED` |  | `'suspended'` |
| `DEACTIVATED` |  | `'deactivated'` |

### Class: `RenderJobStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Cron / one-off job execution states.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CREATED` |  | `'created'` |
| `PENDING` |  | `'pending'` |
| `IN_PROGRESS` |  | `'in_progress'` |
| `SUCCEEDED` |  | `'succeeded'` |
| `FAILED` |  | `'failed'` |
| `CANCELED` |  | `'canceled'` |

### Class: `RenderDomainVerificationStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Custom domain DNS verification statuses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `VERIFIED` |  | `'verified'` |
| `UNVERIFIED` |  | `'unverified'` |
| `PENDING` |  | `'pending'` |

### Class: `RenderLogLevel`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Log severity levels for the Render logging API.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DEBUG` |  | `'debug'` |
| `INFO` |  | `'info'` |
| `WARN` |  | `'warn'` |
| `ERROR` |  | `'error'` |
| `FATAL` |  | `'fatal'` |

### Class: `RenderLogDirection`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Direction for paginating logs.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FORWARD` |  | `'forward'` |
| `BACKWARD` |  | `'backward'` |

### Class: `RenderLogType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render log types.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `APP` |  | `'app'` |
| `BUILD` |  | `'build'` |
| `DEPLOY` |  | `'deploy'` |
| `REQUEST` |  | `'request'` |

### Class: `RenderRouteType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Redirect/rewrite route types for static sites.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `REDIRECT` |  | `'redirect'` |
| `REWRITE` |  | `'rewrite'` |

### Class: `RenderMaintenanceStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Maintenance window states.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SCHEDULED` |  | `'scheduled'` |
| `IN_PROGRESS` |  | `'in_progress'` |
| `COMPLETED` |  | `'completed'` |
| `SKIPPED` |  | `'skipped'` |

### Class: `RenderWebhookEventType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Event types for webhook subscriptions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DEPLOY_STARTED` |  | `'deploy_started'` |
| `DEPLOY_ENDED` |  | `'deploy_ended'` |
| `SERVICE_CREATED` |  | `'service_created'` |
| `SERVICE_DELETED` |  | `'service_deleted'` |
| `SERVICE_SUSPENDED` |  | `'service_suspended'` |
| `SERVICE_RESUMED` |  | `'service_resumed'` |
| `SERVER_FAILED` |  | `'server_failed'` |

### Class: `RenderNotificationType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Notification delivery channels.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `EMAIL` |  | `'email'` |
| `SLACK` |  | `'slack'` |
| `WEBHOOK` |  | `'webhook'` |

### Class: `RenderPostgresPlan`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render Postgres plans.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FREE` |  | `'free'` |
| `STARTER` |  | `'starter'` |
| `STANDARD` |  | `'standard'` |
| `PRO` |  | `'pro'` |
| `PRO_PLUS` |  | `'pro_plus'` |
| `ACCELERATED` |  | `'accelerated'` |
| `CUSTOM` |  | `'custom'` |

### Class: `RenderKeyValuePlan`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render Key-Value (Redis) store plans.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FREE` |  | `'free'` |
| `STARTER` |  | `'starter'` |
| `STANDARD` |  | `'standard'` |
| `PRO` |  | `'pro'` |

### Class: `RenderBlueprintSyncStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Blueprint sync / IaC sync status.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SYNCED` |  | `'synced'` |
| `SYNCING` |  | `'syncing'` |
| `FAILED` |  | `'failed'` |
| `NOT_SYNCED` |  | `'not_synced'` |

### Class: `RenderInstanceStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Runtime instance statuses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `RUNNING` |  | `'running'` |
| `STARTING` |  | `'starting'` |
| `STOPPED` |  | `'stopped'` |
| `CRASHED` |  | `'crashed'` |
| `DRAINING` |  | `'draining'` |

### Class: `RenderEnvVar`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Environment variable - plain value or generated secret.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `key` | `str` |  |
| `value` | `str &#124; None` | `None` |
| `generate_value` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderDisk`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Persistent disk attached to a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `'data'` |
| `mount_path` | `str` | `'/data'` |
| `size_gb` | `int` | `1` |
| `service_id` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderDiskSnapshot`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A snapshot of a persistent disk.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `disk_id` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |

### Class: `RenderAutoscaling`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Autoscaling configuration for a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `min` | `int` | `1` |
| `max` | `int` | `3` |
| `criteria` | `dict[str, Any] &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `disabled` | `def disabled(cls) -> RenderAutoscaling` | classmethod | Method. |
| `auto` | `def auto(cls, min_instances: int = 1, max_instances: int = 3, cpu_percent: int = 80, memory_percent: int &#124; None = None) -> RenderAutoscaling` | classmethod | Method. |

### Class: `RenderDeploy`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single deploy for a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `service_id` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `commit` | `dict[str, Any] &#124; None` | `None` |
| `image` | `dict[str, Any] &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |
| `finished_at` | `str &#124; None` | `None` |
| `trigger` | `str &#124; None` | `None` |

### Class: `RenderService`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render service (top-level resource).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str &#124; None` | `None` |
| `slug` | `str &#124; None` | `None` |
| `type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `plan` | `str &#124; None` | `None` |
| `region` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `suspended` | `str &#124; None` | `None` |
| `auto_deploy` | `str &#124; None` | `None` |
| `service_details` | `dict[str, Any] &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |
| `dashboard_url` | `str &#124; None` | `None` |
| `image_path` | `str &#124; None` | `None` |
| `build_filter` | `dict[str, Any] &#124; None` | `None` |
| `root_dir` | `str &#124; None` | `None` |
| `notify_on_fail` | `str &#124; None` | `None` |

### Class: `RenderOwner`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render workspace/owner (user or team).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `email` | `str &#124; None` | `None` |
| `type` | `str &#124; None` | `None` |

### Class: `RenderSecretFile`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Secret file mounted into a service container.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `content` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderCustomDomain`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Custom domain attached to a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `domain_type` | `str &#124; None` | `None` |
| `verification_status` | `str &#124; None` | `None` |
| `redirect_for_name` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `server` | `dict[str, Any] &#124; None` | `None` |

### Class: `RenderInstance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A running instance of a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `service_id` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |
| `region` | `str &#124; None` | `None` |
| `image_hash` | `str &#124; None` | `None` |

### Class: `RenderEvent`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: An event from the Render event stream.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `service_id` | `str &#124; None` | `None` |
| `type` | `str &#124; None` | `None` |
| `timestamp` | `str &#124; None` | `None` |
| `details` | `dict[str, Any] &#124; None` | `None` |
| `status_code` | `int &#124; None` | `None` |

### Class: `RenderJob`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A cron or one-off job execution.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `service_id` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `plan_id` | `str &#124; None` | `None` |
| `started_at` | `str &#124; None` | `None` |
| `finished_at` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |

### Class: `RenderHeaderRule`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: HTTP header rule for a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `path` | `str` | `'/*'` |
| `name` | `str` | `''` |
| `value` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderRedirectRule`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Redirect / rewrite rule for static sites.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `source` | `str` | `''` |
| `destination` | `str` | `''` |
| `type` | `str` | `'redirect'` |
| `status_code` | `int` | `301` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderLogEntry`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single log line from the Render logging API.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `timestamp` | `str &#124; None` | `None` |
| `message` | `str` | `''` |
| `level` | `str &#124; None` | `None` |
| `service_id` | `str &#124; None` | `None` |
| `instance_id` | `str &#124; None` | `None` |
| `deploy_id` | `str &#124; None` | `None` |
| `type` | `str &#124; None` | `None` |

### Class: `RenderMetricPoint`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single metric data point.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `timestamp` | `str &#124; None` | `None` |
| `value` | `float` | `0.0` |
| `unit` | `str &#124; None` | `None` |
| `label` | `str &#124; None` | `None` |

### Class: `RenderWebhook`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render webhook subscription.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `url` | `str` | `''` |
| `secret` | `str &#124; None` | `None` |
| `events` | `list[str]` | `field(default_factory=list)` |
| `enabled` | `bool` | `True` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderProject`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render project for organizing services.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |
| `environment_ids` | `list[str]` | `field(default_factory=list)` |

### Class: `RenderEnvironment`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render environment within a project.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `project_id` | `str &#124; None` | `None` |
| `protected_status` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |

### Class: `RenderEnvGroup`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A shared environment group for linked services.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str &#124; None` | `None` |
| `env_vars` | `list[RenderEnvVar]` | `field(default_factory=list)` |
| `secret_files` | `list[RenderSecretFile]` | `field(default_factory=list)` |
| `service_links` | `list[str]` | `field(default_factory=list)` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderRegistryCredential`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Private container registry credential.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `registry` | `str` | `''` |
| `username` | `str` | `''` |
| `created_at` | `str &#124; None` | `None` |

### Class: `RenderMaintenance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Maintenance window for a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `service_id` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `scheduled_at` | `str &#124; None` | `None` |
| `started_at` | `str &#124; None` | `None` |
| `completed_at` | `str &#124; None` | `None` |
| `description` | `str &#124; None` | `None` |

### Class: `RenderNotificationSettings`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Notification settings for a service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `notify_on_fail` | `str &#124; None` | `None` |
| `preview_notify_on_fail` | `str &#124; None` | `None` |

### Class: `RenderAuditLogEntry`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: An entry from the workspace audit log.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `action` | `str &#124; None` | `None` |
| `actor` | `dict[str, Any] &#124; None` | `None` |
| `resource` | `dict[str, Any] &#124; None` | `None` |
| `timestamp` | `str &#124; None` | `None` |
| `details` | `dict[str, Any] &#124; None` | `None` |

### Class: `RenderPostgresInstance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render Postgres database instance.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str &#124; None` | `None` |
| `plan` | `str &#124; None` | `None` |
| `region` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `version` | `str &#124; None` | `None` |
| `disk_size_gb` | `int &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |
| `dashboard_url` | `str &#124; None` | `None` |
| `primary_postgres_id` | `str &#124; None` | `None` |
| `high_availability_enabled` | `bool` | `False` |
| `read_replicas` | `list[str]` | `field(default_factory=list)` |

### Class: `RenderPostgresConnectionInfo`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Connection info for a Render Postgres database.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `internal_connection_string` | `str &#124; None` | `None` |
| `external_connection_string` | `str &#124; None` | `None` |
| `psql_command` | `str &#124; None` | `None` |
| `host` | `str &#124; None` | `None` |
| `port` | `int &#124; None` | `None` |
| `database` | `str &#124; None` | `None` |
| `user` | `str &#124; None` | `None` |
| `password` | `str &#124; None` | `None` |

### Class: `RenderPostgresUser`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A user in a Render Postgres database.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` | `''` |
| `password` | `str &#124; None` | `None` |
| `grants` | `list[str]` | `field(default_factory=list)` |

### Class: `RenderKeyValueInstance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render Key-Value (Redis) store instance.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str &#124; None` | `None` |
| `plan` | `str &#124; None` | `None` |
| `region` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `max_memory_policy` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |

### Class: `RenderKeyValueConnectionInfo`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Connection info for a Render Key-Value store.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `internal_connection_string` | `str &#124; None` | `None` |
| `external_connection_string` | `str &#124; None` | `None` |
| `host` | `str &#124; None` | `None` |
| `port` | `int &#124; None` | `None` |
| `password` | `str &#124; None` | `None` |

### Class: `RenderBlueprint`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render Blueprint (Infrastructure as Code).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `status` | `str &#124; None` | `None` |
| `auto_sync` | `bool` | `False` |
| `repo` | `str &#124; None` | `None` |
| `branch` | `str &#124; None` | `None` |
| `owner_id` | `str &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |
| `last_sync` | `dict[str, Any] &#124; None` | `None` |

### Class: `RenderBlueprintSync`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A blueprint sync run.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `blueprint_id` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `started_at` | `str &#124; None` | `None` |
| `completed_at` | `str &#124; None` | `None` |
| `error` | `str &#124; None` | `None` |

### Class: `RenderWorkspaceMember`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A member of a Render workspace/team.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `email` | `str &#124; None` | `None` |
| `name` | `str &#124; None` | `None` |
| `role` | `str &#124; None` | `None` |
| `joined_at` | `str &#124; None` | `None` |

### Class: `RenderLogStream`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A log stream/sink for forwarding logs.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `endpoint` | `str` | `''` |
| `token` | `str &#124; None` | `None` |
| `enabled` | `bool` | `True` |
| `created_at` | `str &#124; None` | `None` |

### Class: `RenderMetricsFilter`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Filter/query parameters for the metrics API.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `resource_id` | `str &#124; None` | `None` |
| `metric` | `str` | `'cpu'` |
| `period` | `str` | `'1h'` |
| `start_time` | `str &#124; None` | `None` |
| `end_time` | `str &#124; None` | `None` |
| `instance_id` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_params` | `def to_params(self) -> dict[str, str]` |  | Method. |

### Class: `RenderDeployConfig`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete deployment configuration for ``aq deploy render``.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `service_name` | `str` | `''` |
| `service_type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `owner_id` | `str &#124; None` | `None` |
| `image` | `str` | `''` |
| `plan` | `RenderPlan` | `RenderPlan.STARTER` |
| `region` | `str` | `'oregon'` |
| `num_instances` | `int` | `1` |
| `autoscaling` | `RenderAutoscaling` | `field(default_factory=RenderAutoscaling.disabled)` |
| `port` | `int` | `8000` |
| `health_check_path` | `str` | `'/_health'` |
| `env_vars` | `list[RenderEnvVar]` | `field(default_factory=list)` |
| `disk` | `RenderDisk &#124; None` | `None` |
| `docker_command` | `str &#124; None` | `None` |
| `auto_deploy` | `str` | `'no'` |
| `secret_files` | `list[RenderSecretFile]` | `field(default_factory=list)` |
| `headers` | `list[RenderHeaderRule]` | `field(default_factory=list)` |
| `redirect_rules` | `list[RenderRedirectRule]` | `field(default_factory=list)` |
| `registry_credential_id` | `str &#124; None` | `None` |
| `notify_on_fail` | `str &#124; None` | `None` |
| `pre_deploy_command` | `str &#124; None` | `None` |
| `build_command` | `str &#124; None` | `None` |
| `root_dir` | `str &#124; None` | `None` |
| `env_group_ids` | `list[str]` | `field(default_factory=list)` |
| `project_id` | `str &#124; None` | `None` |
| `environment_id` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_service_payload` | `def to_service_payload(self) -> dict[str, Any]` |  | Serialize to Render ``POST /v1/services`` API payload. |
| `to_update_payload` | `def to_update_payload(self) -> dict[str, Any]` |  | Serialize to Render ``PATCH /v1/services/{id}`` API payload. |
| `from_workspace_context` | `def from_workspace_context(cls, wctx: dict[str, Any], *, image: str, region: str &#124; None = None, plan: RenderPlan &#124; None = None, num_instances: int = 1, autoscaling: RenderAutoscaling &#124; None = None) -> RenderDeployConfig` | classmethod | Build config from Aquilia workspace introspection context. |

### Class: `RenderClient`

- Source: `aquilia/providers/render_backup_phase10/client.py`
- Bases: `object`
- Summary: Synchronous REST client for the Render API (v1).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `list_services` | `def list_services(self, *, name: str &#124; None = None, type: str &#124; None = None, region: str &#124; None = None, suspended: str &#124; None = None, owner_id: str &#124; None = None, cursor: str &#124; None = None, limit: int = 20) -> list[RenderService]` |  | List all services, optionally filtered. |
| `get_service` | `def get_service(self, service_id: str) -> RenderService` |  | Get a specific service by ID. |
| `get_service_by_name` | `def get_service_by_name(self, name: str, owner_id: str &#124; None = None) -> RenderService &#124; None` |  | Find a service by name. Returns None if not found. |
| `create_service` | `def create_service(self, payload: dict[str, Any]) -> RenderService` |  | Create a new service. |
| `update_service` | `def update_service(self, service_id: str, payload: dict[str, Any]) -> RenderService` |  | Update an existing service (PATCH). |
| `delete_service` | `def delete_service(self, service_id: str) -> None` |  | Delete a service. |
| `suspend_service` | `def suspend_service(self, service_id: str) -> None` |  | Suspend a running service. |
| `resume_service` | `def resume_service(self, service_id: str) -> None` |  | Resume a suspended service. |
| `list_deploys` | `def list_deploys(self, service_id: str, *, cursor: str &#124; None = None, limit: int = 10) -> list[RenderDeploy]` |  | List deploys for a service. |
| `get_deploy` | `def get_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy` |  | Get a specific deploy. |
| `trigger_deploy` | `def trigger_deploy(self, service_id: str) -> RenderDeploy` |  | Trigger a new deploy for the service. |
| `list_env_vars` | `def list_env_vars(self, service_id: str) -> list[dict[str, Any]]` |  | List all environment variables for a service. |
| `update_env_vars` | `def update_env_vars(self, service_id: str, env_vars: list[dict[str, Any]]) -> list[dict[str, Any]]` |  | Bulk update environment variables for a service. |
| `get_env_var` | `def get_env_var(self, service_id: str, key: str) -> dict[str, Any] &#124; None` |  | Get a specific environment variable. |
| `delete_env_var` | `def delete_env_var(self, service_id: str, key: str) -> None` |  | Delete a specific environment variable. |
| `list_custom_domains` | `def list_custom_domains(self, service_id: str) -> list[dict[str, Any]]` |  | List custom domains for a service. |
| `add_custom_domain` | `def add_custom_domain(self, service_id: str, domain_name: str) -> dict[str, Any]` |  | Add a custom domain to a service. |
| `delete_custom_domain` | `def delete_custom_domain(self, service_id: str, domain_name: str) -> None` |  | Remove a custom domain from a service. |
| `set_autoscaling` | `def set_autoscaling(self, service_id: str, config: dict[str, Any]) -> dict[str, Any]` |  | Configure autoscaling for a service. |
| `remove_autoscaling` | `def remove_autoscaling(self, service_id: str) -> None` |  | Remove autoscaling from a service. |
| `scale_service` | `def scale_service(self, service_id: str, num_instances: int) -> None` |  | Manually scale a service to a specific instance count. |
| `get_user` | `def get_user(self) -> dict[str, Any]` |  | Get the authenticated user's details. |
| `list_owners` | `def list_owners(self) -> list[RenderOwner]` |  | List owners (workspaces) for the authenticated user. |
| `validate_token` | `def validate_token(self) -> bool` |  | Validate the API token by fetching owner info. |

### Class: `DeployResult`

- Source: `aquilia/providers/render_backup_phase10/deployer.py`
- Bases: `object`
- Summary: Result of a Render deployment operation.

### Class: `RenderDeployer`

- Source: `aquilia/providers/render_backup_phase10/deployer.py`
- Bases: `object`
- Summary: Full-lifecycle Render deployment orchestrator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `deploy` | `def deploy(self) -> DeployResult` |  | Execute the complete deployment pipeline. |
| `destroy` | `def destroy(self) -> bool` |  | Destroy the service. |
| `status` | `def status(self) -> dict[str, Any]` |  | Get current deployment status. |

### Class: `RenderCredentialStore`

- Source: `aquilia/providers/render_backup_phase10/store.py`
- Bases: `object`
- Summary: Secure, file-based credential store for Render API tokens.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `credentials_path` | `def credentials_path(self) -> Path` | property | Path to the encrypted credentials file. |
| `config_path` | `def config_path(self) -> Path` | property | Path to the non-sensitive config file. |
| `is_configured` | `def is_configured(self) -> bool` |  | Return True if credentials are stored. |
| `save` | `def save(self, token: str, *, owner_name: str &#124; None = None, default_region: str = 'oregon', metadata: dict[str, Any] &#124; None = None) -> None` |  | Encrypt and store the API token. |
| `load` | `def load(self) -> str &#124; None` |  | Load and decrypt the stored API token. |
| `load_config` | `def load_config(self) -> dict[str, Any]` |  | Load non-sensitive provider configuration. |
| `get_default_region` | `def get_default_region(self) -> str` |  | Get the default deployment region. |
| `get_owner_name` | `def get_owner_name(self) -> str &#124; None` |  | Get the stored workspace/owner name. |
| `clear` | `def clear(self) -> None` |  | Securely delete stored credentials. |
| `status` | `def status(self) -> dict[str, Any]` |  | Return credential store status (for CLI display). |

### Class: `RenderServiceType`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Render service type.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `WEB_SERVICE` |  | `'web_service'` |
| `PRIVATE_SERVICE` |  | `'private_service'` |
| `BACKGROUND_WORKER` |  | `'background_worker'` |
| `CRON_JOB` |  | `'cron_job'` |
| `STATIC_SITE` |  | `'static_site'` |

### Class: `RenderPlan`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Render compute plans.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FREE` |  | `'free'` |
| `STARTER` |  | `'starter'` |
| `STANDARD` |  | `'standard'` |
| `PRO` |  | `'pro'` |
| `PRO_PLUS` |  | `'pro_plus'` |
| `PRO_MAX` |  | `'pro_max'` |
| `PRO_ULTRA` |  | `'pro_ultra'` |

### Class: `RenderDeployStatus`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Deploy lifecycle states returned by the Render API.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CREATED` |  | `'created'` |
| `BUILD_IN_PROGRESS` |  | `'build_in_progress'` |
| `UPDATE_IN_PROGRESS` |  | `'update_in_progress'` |
| `LIVE` |  | `'live'` |
| `DEACTIVATED` |  | `'deactivated'` |
| `BUILD_FAILED` |  | `'build_failed'` |
| `UPDATE_FAILED` |  | `'update_failed'` |
| `CANCELED` |  | `'canceled'` |
| `PRE_DEPLOY_IN_PROGRESS` |  | `'pre_deploy_in_progress'` |
| `PRE_DEPLOY_FAILED` |  | `'pre_deploy_failed'` |

### Class: `RenderRegion`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Common Render deployment regions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `OREGON` |  | `'oregon'` |
| `FRANKFURT` |  | `'frankfurt'` |
| `OHIO` |  | `'ohio'` |
| `VIRGINIA` |  | `'virginia'` |
| `SINGAPORE` |  | `'singapore'` |

### Class: `RenderEnvVar`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Environment variable - plain value or generated secret.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `key` | `str` |  |
| `value` | `str &#124; None` | `None` |
| `generate_value` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderDisk`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Persistent disk attached to a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` | `'data'` |
| `mount_path` | `str` | `'/data'` |
| `size_gb` | `int` | `1` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `RenderAutoscaling`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Autoscaling configuration for a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `min` | `int` | `1` |
| `max` | `int` | `3` |
| `criteria` | `dict[str, Any] &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `disabled` | `def disabled(cls) -> RenderAutoscaling` | classmethod | No autoscaling (fixed instance count). |
| `auto` | `def auto(cls, min_instances: int = 1, max_instances: int = 3, cpu_percent: int = 80, memory_percent: int &#124; None = None) -> RenderAutoscaling` | classmethod | CPU/memory-based autoscaling. |

### Class: `RenderDeploy`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single deploy for a Render service.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `service_id` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `commit` | `dict[str, Any] &#124; None` | `None` |
| `image` | `dict[str, Any] &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |
| `finished_at` | `str &#124; None` | `None` |

### Class: `RenderService`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render service (top-level resource, no App grouping).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str &#124; None` | `None` |
| `slug` | `str &#124; None` | `None` |
| `type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `plan` | `str &#124; None` | `None` |
| `region` | `str &#124; None` | `None` |
| `status` | `str &#124; None` | `None` |
| `suspended` | `str &#124; None` | `None` |
| `auto_deploy` | `str &#124; None` | `None` |
| `service_details` | `dict[str, Any] &#124; None` | `None` |
| `created_at` | `str &#124; None` | `None` |
| `updated_at` | `str &#124; None` | `None` |

### Class: `RenderOwner`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A Render workspace/owner (user or team).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str &#124; None` | `None` |
| `name` | `str` | `''` |
| `email` | `str &#124; None` | `None` |
| `type` | `str &#124; None` | `None` |

### Class: `RenderDeployConfig`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete deployment configuration for ``aq deploy render``.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `service_name` | `str` | `''` |
| `service_type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `owner_id` | `str &#124; None` | `None` |
| `image` | `str` | `''` |
| `plan` | `RenderPlan` | `RenderPlan.STARTER` |
| `region` | `str` | `'oregon'` |
| `num_instances` | `int` | `1` |
| `autoscaling` | `RenderAutoscaling` | `field(default_factory=RenderAutoscaling.disabled)` |
| `port` | `int` | `8000` |
| `health_check_path` | `str` | `'/_health'` |
| `env_vars` | `list[RenderEnvVar]` | `field(default_factory=list)` |
| `disk` | `RenderDisk &#124; None` | `None` |
| `docker_command` | `str &#124; None` | `None` |
| `auto_deploy` | `str` | `'no'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_service_payload` | `def to_service_payload(self) -> dict[str, Any]` |  | Serialize to Render ``POST /v1/services`` API payload. |
| `to_update_payload` | `def to_update_payload(self) -> dict[str, Any]` |  | Serialize to Render ``PATCH /v1/services/{id}`` API payload. |
| `from_workspace_context` | `def from_workspace_context(cls, wctx: dict[str, Any], *, image: str, region: str &#124; None = None, plan: RenderPlan &#124; None = None, num_instances: int = 1, autoscaling: RenderAutoscaling &#124; None = None) -> RenderDeployConfig` | classmethod | Build config from Aquilia workspace introspection context. |


## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_BASE_URL` | `aquilia/providers/render/client.py` | `'https://api.render.com/v1'` |
| `_USER_AGENT` | `aquilia/providers/render/client.py` | `'Aquilia-CLI/2.0'` |
| `_DEFAULT_TIMEOUT` | `aquilia/providers/render/client.py` | `30` |
| `_MAX_RETRIES` | `aquilia/providers/render/client.py` | `3` |
| `_RETRY_BACKOFF` | `aquilia/providers/render/client.py` | `1.5` |
| `_SSL_CTX` | `aquilia/providers/render/client.py` | `ssl.SSLContext` |
| `_CROUS_MAGIC` | `aquilia/providers/render/store.py` | `b'AQCR'` |
| `_CROUS_VERSION` | `aquilia/providers/render/store.py` | `2` |
| `_CROUS_VERSION_LEGACY` | `aquilia/providers/render/store.py` | `1` |
| `_SALT_SIZE` | `aquilia/providers/render/store.py` | `32` |
| `_NONCE_SIZE` | `aquilia/providers/render/store.py` | `12` |
| `_KEY_ITERATIONS` | `aquilia/providers/render/store.py` | `600000` |
| `_HMAC_ALGO` | `aquilia/providers/render/store.py` | `'sha512'` |
| `_TAG_SIZE` | `aquilia/providers/render/store.py` | `16` |
| `_CANARY_PLAINTEXT` | `aquilia/providers/render/store.py` | `b'AQUILIA_CANARY_OK'` |
| `_CANARY_SIZE` | `aquilia/providers/render/store.py` | `32` |
| `_DEFAULT_TTL` | `aquilia/providers/render/store.py` | `0` |
| `_MAX_TOKEN_SIZE` | `aquilia/providers/render/store.py` | `8192` |
| `_CIPHER_AES_GCM` | `aquilia/providers/render/store.py` | `1` |
| `_CIPHER_XOR_HMAC` | `aquilia/providers/render/store.py` | `3` |
| `_AUDIT_MAX_BYTES` | `aquilia/providers/render/store.py` | `1048576` |
| `_BASE_URL` | `aquilia/providers/render_backup_phase10/client.py` | `'https://api.render.com/v1'` |
| `_USER_AGENT` | `aquilia/providers/render_backup_phase10/client.py` | `'Aquilia-CLI/1.0'` |
| `_DEFAULT_TIMEOUT` | `aquilia/providers/render_backup_phase10/client.py` | `30` |
| `_MAX_RETRIES` | `aquilia/providers/render_backup_phase10/client.py` | `3` |
| `_RETRY_BACKOFF` | `aquilia/providers/render_backup_phase10/client.py` | `1.5` |
| `_SSL_CTX` | `aquilia/providers/render_backup_phase10/client.py` | `ssl.SSLContext` |
| `_CROUS_MAGIC` | `aquilia/providers/render_backup_phase10/store.py` | `b'AQCR'` |
| `_CROUS_VERSION` | `aquilia/providers/render_backup_phase10/store.py` | `1` |
| `_SALT_SIZE` | `aquilia/providers/render_backup_phase10/store.py` | `32` |
| `_KEY_ITERATIONS` | `aquilia/providers/render_backup_phase10/store.py` | `200000` |
| `_HMAC_ALGO` | `aquilia/providers/render_backup_phase10/store.py` | `'sha256'` |
| `_DEFAULT_STORE_DIR` | `aquilia/providers/render_backup_phase10/store.py` | `Path.home() / '.aquilia' / 'providers' / 'render'` |
