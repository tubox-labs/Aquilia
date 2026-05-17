# Providers API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/providers/__init__.py` | 21 | 0 | 0 | Aquilia Cloud Providers — Pluggable PaaS/IaaS Deployment Backends. |
| `aquilia/providers/render/__init__.py` | 153 | 0 | 0 | Aquilia Render Provider — Comprehensive PaaS Deployment v2. |
| `aquilia/providers/render/client.py` | 1406 | 1 | 0 | Render REST API Client — Comprehensive v2. |
| `aquilia/providers/render/deployer.py` | 661 | 2 | 0 | Render Deployment Orchestrator — Enhanced v2. |
| `aquilia/providers/render/store.py` | 752 | 1 | 0 | Render Credential Store — Military-Grade Encrypted Token Persistence. |
| `aquilia/providers/render/types.py` | 993 | 53 | 0 | Render API Type Definitions — Comprehensive v2. |
| `aquilia/providers/render_backup_phase10/__init__.py` | 53 | 0 | 0 | Aquilia Render Provider — One-command PaaS deployment. |
| `aquilia/providers/render_backup_phase10/client.py` | 571 | 1 | 0 | Render REST API Client. |
| `aquilia/providers/render_backup_phase10/deployer.py` | 544 | 2 | 0 | Render Deployment Orchestrator. |
| `aquilia/providers/render_backup_phase10/store.py` | 344 | 1 | 0 | Render Credential Store — Surp-Encrypted Token Persistence. |
| `aquilia/providers/render_backup_phase10/types.py` | 384 | 11 | 0 | Render API Type Definitions. |

## Public Exports

`DeployResult`, `ProviderAPIFault`, `ProviderAuthFault`, `ProviderRateLimitFault`, `RenderAuditLogEntry`, `RenderAutoscaling`, `RenderBlueprint`, `RenderBlueprintSync`, `RenderBlueprintSyncStatus`, `RenderClient`, `RenderCredentialStore`, `RenderCustomDomain`, `RenderDeploy`, `RenderDeployConfig`, `RenderDeployStatus`, `RenderDeployer`, `RenderDisk`, `RenderDiskSnapshot`, `RenderDomainVerificationStatus`, `RenderEnvGroup`, `RenderEnvVar`, `RenderEnvironment`, `RenderEvent`, `RenderHeaderRule`, `RenderInstance`, `RenderInstanceStatus`, `RenderJob`, `RenderJobStatus`, `RenderKeyValueConnectionInfo`, `RenderKeyValueInstance`, `RenderKeyValuePlan`, `RenderLogDirection`, `RenderLogEntry`, `RenderLogLevel`, `RenderLogStream`, `RenderLogType`, `RenderMaintenance`, `RenderMaintenanceStatus`, `RenderMetricPoint`, `RenderMetricsFilter`, `RenderNotificationSettings`, `RenderNotificationType`, `RenderOwner`, `RenderPlan`, `RenderPostgresConnectionInfo`, `RenderPostgresInstance`, `RenderPostgresPlan`, `RenderPostgresUser`, `RenderProject`, `RenderRedirectRule`, `RenderRegion`, `RenderRegistryCredential`, `RenderRouteType`, `RenderSecretFile`, `RenderService`, `RenderServiceStatus`, `RenderServiceType`, `RenderWebhook`, `RenderWebhookEventType`, `RenderWorkspaceMember`, `render`

## Public Class Summary

| Class | Source | Bases | Summary |
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
| `RenderEnvVar` | `aquilia/providers/render/types.py` | object | Environment variable — plain value or generated secret. |
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
| `RenderEnvVar` | `aquilia/providers/render_backup_phase10/types.py` | object | Environment variable — plain value or generated secret. |
| `RenderDisk` | `aquilia/providers/render_backup_phase10/types.py` | object | Persistent disk attached to a Render service. |
| `RenderAutoscaling` | `aquilia/providers/render_backup_phase10/types.py` | object | Autoscaling configuration for a Render service. |
| `RenderDeploy` | `aquilia/providers/render_backup_phase10/types.py` | object | A single deploy for a Render service. |
| `RenderService` | `aquilia/providers/render_backup_phase10/types.py` | object | A Render service (top-level resource, no App grouping). |
| `RenderOwner` | `aquilia/providers/render_backup_phase10/types.py` | object | A Render workspace/owner (user or team). |
| `RenderDeployConfig` | `aquilia/providers/render_backup_phase10/types.py` | object | Complete deployment configuration for ``aq deploy render``. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_BASE_URL` | `aquilia/providers/render/client.py` | `'https://api.render.com/v1'` |
| `_USER_AGENT` | `aquilia/providers/render/client.py` | `'Aquilia-CLI/2.0'` |
| `_DEFAULT_TIMEOUT` | `aquilia/providers/render/client.py` | `30` |
| `_MAX_RETRIES` | `aquilia/providers/render/client.py` | `3` |
| `_RETRY_BACKOFF` | `aquilia/providers/render/client.py` | `1.5` |
| `_SSL_CTX` | `aquilia/providers/render/client.py` | `ssl.SSLContext` |
| `_SURP_MAGIC` | `aquilia/providers/render/store.py` | `b'AQCR'` |
| `_SURP_VERSION` | `aquilia/providers/render/store.py` | `2` |
| `_SURP_VERSION_LEGACY` | `aquilia/providers/render/store.py` | `1` |
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
| `_SURP_MAGIC` | `aquilia/providers/render_backup_phase10/store.py` | `b'AQCR'` |
| `_SURP_VERSION` | `aquilia/providers/render_backup_phase10/store.py` | `1` |
| `_SALT_SIZE` | `aquilia/providers/render_backup_phase10/store.py` | `32` |
| `_KEY_ITERATIONS` | `aquilia/providers/render_backup_phase10/store.py` | `200000` |
| `_HMAC_ALGO` | `aquilia/providers/render_backup_phase10/store.py` | `'sha256'` |
| `_DEFAULT_STORE_DIR` | `aquilia/providers/render_backup_phase10/store.py` | `Path.home() / '.aquilia' / 'providers' / 'render'` |

## Detailed Classes And Methods

### `RenderClient`

- Source: `aquilia/providers/render/client.py`
- Bases: `object`
- Summary: Synchronous REST client for the Render API (v1).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `list_services` | `def list_services(self, *, name: str \| None=None, type: str \| None=None, region: str \| None=None, suspended: str \| None=None, owner_id: str \| None=None, cursor: str \| None=None, limit: int=20)` | List all services, optionally filtered. |
| `get_service` | `def get_service(self, service_id: str)` | Get a specific service by ID. |
| `get_service_by_name` | `def get_service_by_name(self, name: str, owner_id: str \| None=None)` | Find a service by name. |
| `create_service` | `def create_service(self, payload: dict[str, Any])` | Create a new service. |
| `update_service` | `def update_service(self, service_id: str, payload: dict[str, Any])` | Update an existing service (PATCH). |
| `delete_service` | `def delete_service(self, service_id: str)` | Delete a service. |
| `suspend_service` | `def suspend_service(self, service_id: str)` | Suspend a running service. |
| `resume_service` | `def resume_service(self, service_id: str)` | Resume a suspended service. |
| `restart_service` | `def restart_service(self, service_id: str)` | Restart a running service (zero-downtime). |
| `purge_cache` | `def purge_cache(self, service_id: str)` | Clear the build cache for a service. |
| `create_preview` | `def create_preview(self, service_id: str, *, image_url: str \| None=None, name: str \| None=None)` | Create a preview instance of a service. |
| `list_deploys` | `def list_deploys(self, service_id: str, *, cursor: str \| None=None, limit: int=10)` | List deploys for a service. |
| `get_deploy` | `def get_deploy(self, service_id: str, deploy_id: str)` | Get a specific deploy. |
| `trigger_deploy` | `def trigger_deploy(self, service_id: str)` | Trigger a new deploy. |
| `cancel_deploy` | `def cancel_deploy(self, service_id: str, deploy_id: str)` | Cancel a running deploy. |
| `rollback_deploy` | `def rollback_deploy(self, service_id: str, deploy_id: str)` | Rollback to a previous deploy. |
| `list_env_vars` | `def list_env_vars(self, service_id: str)` | List all environment variables for a service. |
| `update_env_vars` | `def update_env_vars(self, service_id: str, env_vars: list[dict[str, Any]])` | Bulk update environment variables for a service. |
| `get_env_var` | `def get_env_var(self, service_id: str, key: str)` | Get a specific environment variable. |
| `delete_env_var` | `def delete_env_var(self, service_id: str, key: str)` | Delete a specific environment variable. |
| `list_custom_domains` | `def list_custom_domains(self, service_id: str)` | List custom domains for a service. |
| `add_custom_domain` | `def add_custom_domain(self, service_id: str, domain_name: str)` | Add a custom domain to a service. |
| `delete_custom_domain` | `def delete_custom_domain(self, service_id: str, domain_name: str)` | Remove a custom domain. |
| `verify_dns` | `def verify_dns(self, service_id: str, domain_name: str)` | Verify DNS configuration for a custom domain. |
| `list_secret_files` | `def list_secret_files(self, service_id: str)` | List secret files for a service. |
| `update_secret_files` | `def update_secret_files(self, service_id: str, files: list[dict[str, str]])` | Bulk update secret files (PUT replaces all). |
| `delete_secret_file` | `def delete_secret_file(self, service_id: str, name: str)` | Delete a specific secret file. |
| `list_headers` | `def list_headers(self, service_id: str)` | List HTTP header rules for a service. |
| `add_header` | `def add_header(self, service_id: str, header: dict[str, str])` | Add an HTTP header rule. |
| `delete_header` | `def delete_header(self, service_id: str, header_id: str)` | Delete an HTTP header rule. |
| `list_redirect_rules` | `def list_redirect_rules(self, service_id: str)` | List redirect/rewrite rules. |
| `add_redirect_rule` | `def add_redirect_rule(self, service_id: str, rule: dict[str, Any])` | Add a redirect/rewrite rule. |
| `delete_redirect_rule` | `def delete_redirect_rule(self, service_id: str, rule_id: str)` | Delete a redirect/rewrite rule. |
| `list_instances` | `def list_instances(self, service_id: str)` | List running instances of a service. |
| `list_events` | `def list_events(self, service_id: str, *, cursor: str \| None=None, limit: int=20)` | List events for a service. |
| `list_jobs` | `def list_jobs(self, service_id: str, *, cursor: str \| None=None, limit: int=20)` | List job executions for a cron service. |
| `trigger_job` | `def trigger_job(self, service_id: str)` | Manually trigger a cron job execution. |
| `cancel_job` | `def cancel_job(self, service_id: str, job_id: str)` | Cancel a running job. |
| `set_autoscaling` | `def set_autoscaling(self, service_id: str, config: dict[str, Any])` | Configure autoscaling for a service. |
| `remove_autoscaling` | `def remove_autoscaling(self, service_id: str)` | Remove autoscaling from a service. |
| `scale_service` | `def scale_service(self, service_id: str, num_instances: int)` | Manually scale a service to a specific instance count. |
| `list_disks` | `def list_disks(self, service_id: str)` | List persistent disks for a service. |
| `create_disk` | `def create_disk(self, service_id: str, payload: dict[str, Any])` | Create a persistent disk. |
| `delete_disk` | `def delete_disk(self, disk_id: str)` | Delete a persistent disk. |
| `list_disk_snapshots` | `def list_disk_snapshots(self, disk_id: str)` | List snapshots for a persistent disk. |
| `restore_disk_snapshot` | `def restore_disk_snapshot(self, disk_id: str, snapshot_id: str)` | Restore a persistent disk from a snapshot. |
| `get_logs` | `def get_logs(self, *, owner_id: str \| None=None, service_id: str \| None=None, direction: str='backward', limit: int=100, start_time: str \| None=None, end_time: str \| None=None, level: str \| None=None, log_type: str \| None=None, text: str \| None=None, instance_id: str \| None=None)` | Retrieve logs from the Render logging API. |
| `get_metrics` | `def get_metrics(self, service_id: str, *, metric: str='cpu', period: str='1h', start_time: str \| None=None, end_time: str \| None=None, instance_id: str \| None=None)` | Retrieve service metrics (CPU, memory, HTTP, bandwidth, disk). |
| `get_metrics_filtered` | `def get_metrics_filtered(self, flt: RenderMetricsFilter)` | Retrieve metrics using a RenderMetricsFilter object. |
| `list_postgres` | `def list_postgres(self, *, owner_id: str \| None=None, cursor: str \| None=None, limit: int=20)` | List Postgres database instances. |
| `create_postgres` | `def create_postgres(self, payload: dict[str, Any])` | Create a new Postgres database. |
| `get_postgres` | `def get_postgres(self, postgres_id: str)` | Get a specific Postgres instance. |
| `delete_postgres` | `def delete_postgres(self, postgres_id: str)` | Delete a Postgres database. |
| `get_postgres_connection_info` | `def get_postgres_connection_info(self, postgres_id: str)` | Get connection info for a Postgres database. |
| `list_postgres_users` | `def list_postgres_users(self, postgres_id: str)` | List users in a Postgres database. |
| `create_postgres_user` | `def create_postgres_user(self, postgres_id: str, name: str)` | Create a new Postgres user. |
| `delete_postgres_user` | `def delete_postgres_user(self, postgres_id: str, user_name: str)` | Delete a Postgres user. |
| `list_key_value` | `def list_key_value(self, *, owner_id: str \| None=None, cursor: str \| None=None, limit: int=20)` | List Key-Value (Redis) store instances. |
| `create_key_value` | `def create_key_value(self, payload: dict[str, Any])` | Create a new Key-Value store. |
| `get_key_value` | `def get_key_value(self, kv_id: str)` | Get a specific Key-Value instance. |
| `delete_key_value` | `def delete_key_value(self, kv_id: str)` | Delete a Key-Value store. |
| `get_key_value_connection_info` | `def get_key_value_connection_info(self, kv_id: str)` | Get connection info for a Key-Value store. |
| `list_projects` | `def list_projects(self, *, owner_id: str \| None=None, cursor: str \| None=None, limit: int=20)` | List projects. |
| `create_project` | `def create_project(self, payload: dict[str, Any])` | Create a new project. |
| `get_project` | `def get_project(self, project_id: str)` | Get a specific project. |
| `delete_project` | `def delete_project(self, project_id: str)` | Delete a project. |
| `list_environments` | `def list_environments(self, project_id: str)` | List environments for a project. |
| `create_environment` | `def create_environment(self, project_id: str, payload: dict[str, Any])` | Create a new environment in a project. |
| `delete_environment` | `def delete_environment(self, project_id: str, environment_id: str)` | Delete an environment. |
| `list_env_groups` | `def list_env_groups(self, *, owner_id: str \| None=None, cursor: str \| None=None, limit: int=20)` | List environment groups. |
| `create_env_group` | `def create_env_group(self, payload: dict[str, Any])` | Create a new environment group. |
| `get_env_group` | `def get_env_group(self, env_group_id: str)` | Get a specific environment group. |
| `update_env_group` | `def update_env_group(self, env_group_id: str, payload: dict[str, Any])` | Update an environment group. |
| `delete_env_group` | `def delete_env_group(self, env_group_id: str)` | Delete an environment group. |
| `link_service_to_env_group` | `def link_service_to_env_group(self, env_group_id: str, service_id: str)` | Link a service to an environment group. |
| `unlink_service_from_env_group` | `def unlink_service_from_env_group(self, env_group_id: str, service_id: str)` | Unlink a service from an environment group. |
| `list_registry_credentials` | `def list_registry_credentials(self, *, owner_id: str \| None=None)` | List private registry credentials. |
| `create_registry_credential` | `def create_registry_credential(self, payload: dict[str, Any])` | Create a private registry credential. |
| `delete_registry_credential` | `def delete_registry_credential(self, credential_id: str)` | Delete a registry credential. |
| `list_blueprints` | `def list_blueprints(self, *, owner_id: str \| None=None, cursor: str \| None=None, limit: int=20)` | List blueprints. |
| `get_blueprint` | `def get_blueprint(self, blueprint_id: str)` | Get a specific blueprint. |
| `sync_blueprint` | `def sync_blueprint(self, blueprint_id: str)` | Trigger a blueprint sync. |
| `list_webhooks` | `def list_webhooks(self, *, owner_id: str \| None=None)` | List webhooks. |
| `create_webhook` | `def create_webhook(self, payload: dict[str, Any])` | Create a webhook subscription. |
| `get_webhook` | `def get_webhook(self, webhook_id: str)` | Get a specific webhook. |
| `update_webhook` | `def update_webhook(self, webhook_id: str, payload: dict[str, Any])` | Update a webhook. |
| `delete_webhook` | `def delete_webhook(self, webhook_id: str)` | Delete a webhook. |
| `list_maintenance_windows` | `def list_maintenance_windows(self, service_id: str)` | List maintenance windows for a service. |
| `trigger_maintenance` | `def trigger_maintenance(self, service_id: str)` | Trigger maintenance for a service. |
| `get_notification_settings` | `def get_notification_settings(self, service_id: str)` | Get notification settings for a service. |
| `update_notification_settings` | `def update_notification_settings(self, service_id: str, payload: dict[str, str])` | Update notification settings for a service. |
| `list_log_streams` | `def list_log_streams(self, *, owner_id: str \| None=None)` | List log stream sinks. |
| `create_log_stream` | `def create_log_stream(self, payload: dict[str, Any])` | Create a log stream sink. |
| `delete_log_stream` | `def delete_log_stream(self, log_stream_id: str)` | Delete a log stream sink. |
| `get_user` | `def get_user(self)` | Get the authenticated user's details. |
| `list_owners` | `def list_owners(self)` | List owners (workspaces) for the authenticated user. |
| `list_workspace_members` | `def list_workspace_members(self, owner_id: str)` | List members of a workspace/team. |
| `validate_token` | `def validate_token(self)` | Validate the API token by fetching owner info. |
| `list_audit_logs` | `def list_audit_logs(self, owner_id: str, *, cursor: str \| None=None, limit: int=50)` | List audit log entries for a workspace. |

### `DeployResult`

- Source: `aquilia/providers/render/deployer.py`
- Bases: `object`
- Summary: Result of a Render deployment operation.

### `RenderDeployer`

- Source: `aquilia/providers/render/deployer.py`
- Bases: `object`
- Summary: Full-lifecycle Render deployment orchestrator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `deploy` | `def deploy(self)` | Execute the complete deployment pipeline. |
| `rollback` | `def rollback(self, deploy_id: str \| None=None)` | Rollback to a previous deployment. |
| `cancel` | `def cancel(self, service_id: str \| None=None, deploy_id: str \| None=None)` | Cancel a running deployment. |
| `create_preview` | `def create_preview(self, *, name: str \| None=None)` | Create a preview environment of the service. |
| `restart` | `def restart(self)` | Restart the service (zero-downtime). |
| `purge_cache` | `def purge_cache(self)` | Clear the build cache for the service. |
| `get_deploy_logs` | `def get_deploy_logs(self, *, limit: int=100, level: str \| None=None)` | Get recent logs for the service. |
| `get_service_metrics` | `def get_service_metrics(self, *, metric: str='cpu', period: str='1h')` | Get metrics for the service. |
| `destroy` | `def destroy(self)` | Destroy the service. |
| `status` | `def status(self)` | Get current deployment status with extended info. |

### `RenderCredentialStore`

- Source: `aquilia/providers/render/store.py`
- Bases: `object`
- Summary: Military-grade, file-based credential store for Render API tokens.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `credentials_path` | `def credentials_path(self)` |  |
| `config_path` | `def config_path(self)` |  |
| `is_configured` | `def is_configured(self)` |  |
| `save` | `def save(self, token: str, *, owner_name: str \| None=None, default_region: str='oregon', metadata: dict[str, Any] \| None=None)` | Encrypt and store the API token with military-grade security. |
| `load` | `def load(self)` | Load and decrypt the stored API token. |
| `load_config` | `def load_config(self)` | Load non-sensitive provider configuration. |
| `get_default_region` | `def get_default_region(self)` |  |
| `get_owner_name` | `def get_owner_name(self)` |  |
| `get_token_age` | `def get_token_age(self)` | Get the age of the stored token in seconds. |
| `is_expired` | `def is_expired(self)` | Check if the stored token has expired. |
| `clear` | `def clear(self)` | Securely delete stored credentials. |
| `rotate` | `def rotate(self, new_token: str \| None=None)` | Rotate credentials — re-encrypt with new key material. |
| `get_audit_log` | `def get_audit_log(self, limit: int=50)` | Read the most recent audit log entries. |
| `status` | `def status(self)` | Return credential store status (for CLI display). |

### `RenderServiceType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render service type.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `WEB_SERVICE` | `` | `'web_service'` |
| `PRIVATE_SERVICE` | `` | `'private_service'` |
| `BACKGROUND_WORKER` | `` | `'background_worker'` |
| `CRON_JOB` | `` | `'cron_job'` |
| `STATIC_SITE` | `` | `'static_site'` |

### `RenderPlan`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render compute plans.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `FREE` | `` | `'free'` |
| `STARTER` | `` | `'starter'` |
| `STANDARD` | `` | `'standard'` |
| `PRO` | `` | `'pro'` |
| `PRO_PLUS` | `` | `'pro_plus'` |
| `PRO_MAX` | `` | `'pro_max'` |
| `PRO_ULTRA` | `` | `'pro_ultra'` |

### `RenderDeployStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Deploy lifecycle states returned by the Render API.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CREATED` | `` | `'created'` |
| `BUILD_IN_PROGRESS` | `` | `'build_in_progress'` |
| `UPDATE_IN_PROGRESS` | `` | `'update_in_progress'` |
| `LIVE` | `` | `'live'` |
| `DEACTIVATED` | `` | `'deactivated'` |
| `BUILD_FAILED` | `` | `'build_failed'` |
| `UPDATE_FAILED` | `` | `'update_failed'` |
| `CANCELED` | `` | `'canceled'` |
| `PRE_DEPLOY_IN_PROGRESS` | `` | `'pre_deploy_in_progress'` |
| `PRE_DEPLOY_FAILED` | `` | `'pre_deploy_failed'` |

### `RenderRegion`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Common Render deployment regions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `OREGON` | `` | `'oregon'` |
| `FRANKFURT` | `` | `'frankfurt'` |
| `OHIO` | `` | `'ohio'` |
| `VIRGINIA` | `` | `'virginia'` |
| `SINGAPORE` | `` | `'singapore'` |

### `RenderServiceStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Service runtime statuses.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CREATING` | `` | `'creating'` |
| `DEPLOYING` | `` | `'deploying'` |
| `LIVE` | `` | `'live'` |
| `SUSPENDED` | `` | `'suspended'` |
| `DEACTIVATED` | `` | `'deactivated'` |

### `RenderJobStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Cron / one-off job execution states.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CREATED` | `` | `'created'` |
| `PENDING` | `` | `'pending'` |
| `IN_PROGRESS` | `` | `'in_progress'` |
| `SUCCEEDED` | `` | `'succeeded'` |
| `FAILED` | `` | `'failed'` |
| `CANCELED` | `` | `'canceled'` |

### `RenderDomainVerificationStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Custom domain DNS verification statuses.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `VERIFIED` | `` | `'verified'` |
| `UNVERIFIED` | `` | `'unverified'` |
| `PENDING` | `` | `'pending'` |

### `RenderLogLevel`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Log severity levels for the Render logging API.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DEBUG` | `` | `'debug'` |
| `INFO` | `` | `'info'` |
| `WARN` | `` | `'warn'` |
| `ERROR` | `` | `'error'` |
| `FATAL` | `` | `'fatal'` |

### `RenderLogDirection`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Direction for paginating logs.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `FORWARD` | `` | `'forward'` |
| `BACKWARD` | `` | `'backward'` |

### `RenderLogType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render log types.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `APP` | `` | `'app'` |
| `BUILD` | `` | `'build'` |
| `DEPLOY` | `` | `'deploy'` |
| `REQUEST` | `` | `'request'` |

### `RenderRouteType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Redirect/rewrite route types for static sites.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `REDIRECT` | `` | `'redirect'` |
| `REWRITE` | `` | `'rewrite'` |

### `RenderMaintenanceStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Maintenance window states.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SCHEDULED` | `` | `'scheduled'` |
| `IN_PROGRESS` | `` | `'in_progress'` |
| `COMPLETED` | `` | `'completed'` |
| `SKIPPED` | `` | `'skipped'` |

### `RenderWebhookEventType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Event types for webhook subscriptions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DEPLOY_STARTED` | `` | `'deploy_started'` |
| `DEPLOY_ENDED` | `` | `'deploy_ended'` |
| `SERVICE_CREATED` | `` | `'service_created'` |
| `SERVICE_DELETED` | `` | `'service_deleted'` |
| `SERVICE_SUSPENDED` | `` | `'service_suspended'` |
| `SERVICE_RESUMED` | `` | `'service_resumed'` |
| `SERVER_FAILED` | `` | `'server_failed'` |

### `RenderNotificationType`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Notification delivery channels.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `EMAIL` | `` | `'email'` |
| `SLACK` | `` | `'slack'` |
| `WEBHOOK` | `` | `'webhook'` |

### `RenderPostgresPlan`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render Postgres plans.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `FREE` | `` | `'free'` |
| `STARTER` | `` | `'starter'` |
| `STANDARD` | `` | `'standard'` |
| `PRO` | `` | `'pro'` |
| `PRO_PLUS` | `` | `'pro_plus'` |
| `ACCELERATED` | `` | `'accelerated'` |
| `CUSTOM` | `` | `'custom'` |

### `RenderKeyValuePlan`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Render Key-Value (Redis) store plans.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `FREE` | `` | `'free'` |
| `STARTER` | `` | `'starter'` |
| `STANDARD` | `` | `'standard'` |
| `PRO` | `` | `'pro'` |

### `RenderBlueprintSyncStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Blueprint sync / IaC sync status.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SYNCED` | `` | `'synced'` |
| `SYNCING` | `` | `'syncing'` |
| `FAILED` | `` | `'failed'` |
| `NOT_SYNCED` | `` | `'not_synced'` |

### `RenderInstanceStatus`

- Source: `aquilia/providers/render/types.py`
- Bases: `str, Enum`
- Summary: Runtime instance statuses.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `RUNNING` | `` | `'running'` |
| `STARTING` | `` | `'starting'` |
| `STOPPED` | `` | `'stopped'` |
| `CRASHED` | `` | `'crashed'` |
| `DRAINING` | `` | `'draining'` |

### `RenderEnvVar`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Environment variable — plain value or generated secret.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `key` | `str` | `` |
| `value` | `str \| None` | `None` |
| `generate_value` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderDisk`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Persistent disk attached to a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `'data'` |
| `mount_path` | `str` | `'/data'` |
| `size_gb` | `int` | `1` |
| `service_id` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderDiskSnapshot`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A snapshot of a persistent disk.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `disk_id` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |

### `RenderAutoscaling`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Autoscaling configuration for a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `min` | `int` | `1` |
| `max` | `int` | `3` |
| `criteria` | `dict[str, Any] \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `disabled` | `def disabled(cls)` |  |
| `auto` | `def auto(cls, min_instances: int=1, max_instances: int=3, cpu_percent: int=80, memory_percent: int \| None=None)` |  |

### `RenderDeploy`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A single deploy for a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `service_id` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `commit` | `dict[str, Any] \| None` | `None` |
| `image` | `dict[str, Any] \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |
| `finished_at` | `str \| None` | `None` |
| `trigger` | `str \| None` | `None` |

### `RenderService`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render service (top-level resource).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str \| None` | `None` |
| `slug` | `str \| None` | `None` |
| `type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `plan` | `str \| None` | `None` |
| `region` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `suspended` | `str \| None` | `None` |
| `auto_deploy` | `str \| None` | `None` |
| `service_details` | `dict[str, Any] \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |
| `dashboard_url` | `str \| None` | `None` |
| `image_path` | `str \| None` | `None` |
| `build_filter` | `dict[str, Any] \| None` | `None` |
| `root_dir` | `str \| None` | `None` |
| `notify_on_fail` | `str \| None` | `None` |

### `RenderOwner`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render workspace/owner (user or team).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `email` | `str \| None` | `None` |
| `type` | `str \| None` | `None` |

### `RenderSecretFile`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Secret file mounted into a service container.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `content` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderCustomDomain`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Custom domain attached to a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `domain_type` | `str \| None` | `None` |
| `verification_status` | `str \| None` | `None` |
| `redirect_for_name` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `server` | `dict[str, Any] \| None` | `None` |

### `RenderInstance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A running instance of a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `service_id` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |
| `region` | `str \| None` | `None` |
| `image_hash` | `str \| None` | `None` |

### `RenderEvent`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: An event from the Render event stream.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `service_id` | `str \| None` | `None` |
| `type` | `str \| None` | `None` |
| `timestamp` | `str \| None` | `None` |
| `details` | `dict[str, Any] \| None` | `None` |
| `status_code` | `int \| None` | `None` |

### `RenderJob`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A cron or one-off job execution.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `service_id` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `plan_id` | `str \| None` | `None` |
| `started_at` | `str \| None` | `None` |
| `finished_at` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |

### `RenderHeaderRule`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: HTTP header rule for a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `path` | `str` | `'/*'` |
| `name` | `str` | `''` |
| `value` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderRedirectRule`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Redirect / rewrite rule for static sites.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `source` | `str` | `''` |
| `destination` | `str` | `''` |
| `type` | `str` | `'redirect'` |
| `status_code` | `int` | `301` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderLogEntry`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A single log line from the Render logging API.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `timestamp` | `str \| None` | `None` |
| `message` | `str` | `''` |
| `level` | `str \| None` | `None` |
| `service_id` | `str \| None` | `None` |
| `instance_id` | `str \| None` | `None` |
| `deploy_id` | `str \| None` | `None` |
| `type` | `str \| None` | `None` |

### `RenderMetricPoint`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A single metric data point.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `timestamp` | `str \| None` | `None` |
| `value` | `float` | `0.0` |
| `unit` | `str \| None` | `None` |
| `label` | `str \| None` | `None` |

### `RenderWebhook`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render webhook subscription.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `url` | `str` | `''` |
| `secret` | `str \| None` | `None` |
| `events` | `list[str]` | `field(default_factory=list)` |
| `enabled` | `bool` | `True` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderProject`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render project for organizing services.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |
| `environment_ids` | `list[str]` | `field(default_factory=list)` |

### `RenderEnvironment`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render environment within a project.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `project_id` | `str \| None` | `None` |
| `protected_status` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |

### `RenderEnvGroup`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A shared environment group for linked services.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str \| None` | `None` |
| `env_vars` | `list[RenderEnvVar]` | `field(default_factory=list)` |
| `secret_files` | `list[RenderSecretFile]` | `field(default_factory=list)` |
| `service_links` | `list[str]` | `field(default_factory=list)` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderRegistryCredential`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Private container registry credential.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `registry` | `str` | `''` |
| `username` | `str` | `''` |
| `created_at` | `str \| None` | `None` |

### `RenderMaintenance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Maintenance window for a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `service_id` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `scheduled_at` | `str \| None` | `None` |
| `started_at` | `str \| None` | `None` |
| `completed_at` | `str \| None` | `None` |
| `description` | `str \| None` | `None` |

### `RenderNotificationSettings`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Notification settings for a service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `notify_on_fail` | `str \| None` | `None` |
| `preview_notify_on_fail` | `str \| None` | `None` |

### `RenderAuditLogEntry`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: An entry from the workspace audit log.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `action` | `str \| None` | `None` |
| `actor` | `dict[str, Any] \| None` | `None` |
| `resource` | `dict[str, Any] \| None` | `None` |
| `timestamp` | `str \| None` | `None` |
| `details` | `dict[str, Any] \| None` | `None` |

### `RenderPostgresInstance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render Postgres database instance.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str \| None` | `None` |
| `plan` | `str \| None` | `None` |
| `region` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `version` | `str \| None` | `None` |
| `disk_size_gb` | `int \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |
| `dashboard_url` | `str \| None` | `None` |
| `primary_postgres_id` | `str \| None` | `None` |
| `high_availability_enabled` | `bool` | `False` |
| `read_replicas` | `list[str]` | `field(default_factory=list)` |

### `RenderPostgresConnectionInfo`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Connection info for a Render Postgres database.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `internal_connection_string` | `str \| None` | `None` |
| `external_connection_string` | `str \| None` | `None` |
| `psql_command` | `str \| None` | `None` |
| `host` | `str \| None` | `None` |
| `port` | `int \| None` | `None` |
| `database` | `str \| None` | `None` |
| `user` | `str \| None` | `None` |
| `password` | `str \| None` | `None` |

### `RenderPostgresUser`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A user in a Render Postgres database.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `''` |
| `password` | `str \| None` | `None` |
| `grants` | `list[str]` | `field(default_factory=list)` |

### `RenderKeyValueInstance`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render Key-Value (Redis) store instance.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str \| None` | `None` |
| `plan` | `str \| None` | `None` |
| `region` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `max_memory_policy` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |

### `RenderKeyValueConnectionInfo`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Connection info for a Render Key-Value store.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `internal_connection_string` | `str \| None` | `None` |
| `external_connection_string` | `str \| None` | `None` |
| `host` | `str \| None` | `None` |
| `port` | `int \| None` | `None` |
| `password` | `str \| None` | `None` |

### `RenderBlueprint`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A Render Blueprint (Infrastructure as Code).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `status` | `str \| None` | `None` |
| `auto_sync` | `bool` | `False` |
| `repo` | `str \| None` | `None` |
| `branch` | `str \| None` | `None` |
| `owner_id` | `str \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |
| `last_sync` | `dict[str, Any] \| None` | `None` |

### `RenderBlueprintSync`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A blueprint sync run.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `blueprint_id` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `started_at` | `str \| None` | `None` |
| `completed_at` | `str \| None` | `None` |
| `error` | `str \| None` | `None` |

### `RenderWorkspaceMember`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A member of a Render workspace/team.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `email` | `str \| None` | `None` |
| `name` | `str \| None` | `None` |
| `role` | `str \| None` | `None` |
| `joined_at` | `str \| None` | `None` |

### `RenderLogStream`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: A log stream/sink for forwarding logs.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `endpoint` | `str` | `''` |
| `token` | `str \| None` | `None` |
| `enabled` | `bool` | `True` |
| `created_at` | `str \| None` | `None` |

### `RenderMetricsFilter`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Filter/query parameters for the metrics API.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `resource_id` | `str \| None` | `None` |
| `metric` | `str` | `'cpu'` |
| `period` | `str` | `'1h'` |
| `start_time` | `str \| None` | `None` |
| `end_time` | `str \| None` | `None` |
| `instance_id` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_params` | `def to_params(self)` |  |

### `RenderDeployConfig`

- Source: `aquilia/providers/render/types.py`
- Bases: `object`
- Summary: Complete deployment configuration for ``aq deploy render``.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `service_name` | `str` | `''` |
| `service_type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `owner_id` | `str \| None` | `None` |
| `image` | `str` | `''` |
| `plan` | `RenderPlan` | `RenderPlan.STARTER` |
| `region` | `str` | `'oregon'` |
| `num_instances` | `int` | `1` |
| `autoscaling` | `RenderAutoscaling` | `field(default_factory=RenderAutoscaling.disabled)` |
| `port` | `int` | `8000` |
| `health_check_path` | `str` | `'/_health'` |
| `env_vars` | `list[RenderEnvVar]` | `field(default_factory=list)` |
| `disk` | `RenderDisk \| None` | `None` |
| `docker_command` | `str \| None` | `None` |
| `auto_deploy` | `str` | `'no'` |
| `secret_files` | `list[RenderSecretFile]` | `field(default_factory=list)` |
| `headers` | `list[RenderHeaderRule]` | `field(default_factory=list)` |
| `redirect_rules` | `list[RenderRedirectRule]` | `field(default_factory=list)` |
| `registry_credential_id` | `str \| None` | `None` |
| `notify_on_fail` | `str \| None` | `None` |
| `pre_deploy_command` | `str \| None` | `None` |
| `build_command` | `str \| None` | `None` |
| `root_dir` | `str \| None` | `None` |
| `env_group_ids` | `list[str]` | `field(default_factory=list)` |
| `project_id` | `str \| None` | `None` |
| `environment_id` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_service_payload` | `def to_service_payload(self)` | Serialize to Render ``POST /v1/services`` API payload. |
| `to_update_payload` | `def to_update_payload(self)` | Serialize to Render ``PATCH /v1/services/{id}`` API payload. |
| `from_workspace_context` | `def from_workspace_context(cls, wctx: dict[str, Any], *, image: str, region: str \| None=None, plan: RenderPlan \| None=None, num_instances: int=1, autoscaling: RenderAutoscaling \| None=None)` | Build config from Aquilia workspace introspection context. |

### `RenderClient`

- Source: `aquilia/providers/render_backup_phase10/client.py`
- Bases: `object`
- Summary: Synchronous REST client for the Render API (v1).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `list_services` | `def list_services(self, *, name: str \| None=None, type: str \| None=None, region: str \| None=None, suspended: str \| None=None, owner_id: str \| None=None, cursor: str \| None=None, limit: int=20)` | List all services, optionally filtered. |
| `get_service` | `def get_service(self, service_id: str)` | Get a specific service by ID. |
| `get_service_by_name` | `def get_service_by_name(self, name: str, owner_id: str \| None=None)` | Find a service by name. Returns None if not found. |
| `create_service` | `def create_service(self, payload: dict[str, Any])` | Create a new service. |
| `update_service` | `def update_service(self, service_id: str, payload: dict[str, Any])` | Update an existing service (PATCH). |
| `delete_service` | `def delete_service(self, service_id: str)` | Delete a service. |
| `suspend_service` | `def suspend_service(self, service_id: str)` | Suspend a running service. |
| `resume_service` | `def resume_service(self, service_id: str)` | Resume a suspended service. |
| `list_deploys` | `def list_deploys(self, service_id: str, *, cursor: str \| None=None, limit: int=10)` | List deploys for a service. |
| `get_deploy` | `def get_deploy(self, service_id: str, deploy_id: str)` | Get a specific deploy. |
| `trigger_deploy` | `def trigger_deploy(self, service_id: str)` | Trigger a new deploy for the service. |
| `list_env_vars` | `def list_env_vars(self, service_id: str)` | List all environment variables for a service. |
| `update_env_vars` | `def update_env_vars(self, service_id: str, env_vars: list[dict[str, Any]])` | Bulk update environment variables for a service. |
| `get_env_var` | `def get_env_var(self, service_id: str, key: str)` | Get a specific environment variable. |
| `delete_env_var` | `def delete_env_var(self, service_id: str, key: str)` | Delete a specific environment variable. |
| `list_custom_domains` | `def list_custom_domains(self, service_id: str)` | List custom domains for a service. |
| `add_custom_domain` | `def add_custom_domain(self, service_id: str, domain_name: str)` | Add a custom domain to a service. |
| `delete_custom_domain` | `def delete_custom_domain(self, service_id: str, domain_name: str)` | Remove a custom domain from a service. |
| `set_autoscaling` | `def set_autoscaling(self, service_id: str, config: dict[str, Any])` | Configure autoscaling for a service. |
| `remove_autoscaling` | `def remove_autoscaling(self, service_id: str)` | Remove autoscaling from a service. |
| `scale_service` | `def scale_service(self, service_id: str, num_instances: int)` | Manually scale a service to a specific instance count. |
| `get_user` | `def get_user(self)` | Get the authenticated user's details. |
| `list_owners` | `def list_owners(self)` | List owners (workspaces) for the authenticated user. |
| `validate_token` | `def validate_token(self)` | Validate the API token by fetching owner info. |

### `DeployResult`

- Source: `aquilia/providers/render_backup_phase10/deployer.py`
- Bases: `object`
- Summary: Result of a Render deployment operation.

### `RenderDeployer`

- Source: `aquilia/providers/render_backup_phase10/deployer.py`
- Bases: `object`
- Summary: Full-lifecycle Render deployment orchestrator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `deploy` | `def deploy(self)` | Execute the complete deployment pipeline. |
| `destroy` | `def destroy(self)` | Destroy the service. |
| `status` | `def status(self)` | Get current deployment status. |

### `RenderCredentialStore`

- Source: `aquilia/providers/render_backup_phase10/store.py`
- Bases: `object`
- Summary: Secure, file-based credential store for Render API tokens.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `credentials_path` | `def credentials_path(self)` | Path to the encrypted credentials file. |
| `config_path` | `def config_path(self)` | Path to the non-sensitive config file. |
| `is_configured` | `def is_configured(self)` | Return True if credentials are stored. |
| `save` | `def save(self, token: str, *, owner_name: str \| None=None, default_region: str='oregon', metadata: dict[str, Any] \| None=None)` | Encrypt and store the API token. |
| `load` | `def load(self)` | Load and decrypt the stored API token. |
| `load_config` | `def load_config(self)` | Load non-sensitive provider configuration. |
| `get_default_region` | `def get_default_region(self)` | Get the default deployment region. |
| `get_owner_name` | `def get_owner_name(self)` | Get the stored workspace/owner name. |
| `clear` | `def clear(self)` | Securely delete stored credentials. |
| `status` | `def status(self)` | Return credential store status (for CLI display). |

### `RenderServiceType`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Render service type.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `WEB_SERVICE` | `` | `'web_service'` |
| `PRIVATE_SERVICE` | `` | `'private_service'` |
| `BACKGROUND_WORKER` | `` | `'background_worker'` |
| `CRON_JOB` | `` | `'cron_job'` |
| `STATIC_SITE` | `` | `'static_site'` |

### `RenderPlan`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Render compute plans.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `FREE` | `` | `'free'` |
| `STARTER` | `` | `'starter'` |
| `STANDARD` | `` | `'standard'` |
| `PRO` | `` | `'pro'` |
| `PRO_PLUS` | `` | `'pro_plus'` |
| `PRO_MAX` | `` | `'pro_max'` |
| `PRO_ULTRA` | `` | `'pro_ultra'` |

### `RenderDeployStatus`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Deploy lifecycle states returned by the Render API.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CREATED` | `` | `'created'` |
| `BUILD_IN_PROGRESS` | `` | `'build_in_progress'` |
| `UPDATE_IN_PROGRESS` | `` | `'update_in_progress'` |
| `LIVE` | `` | `'live'` |
| `DEACTIVATED` | `` | `'deactivated'` |
| `BUILD_FAILED` | `` | `'build_failed'` |
| `UPDATE_FAILED` | `` | `'update_failed'` |
| `CANCELED` | `` | `'canceled'` |
| `PRE_DEPLOY_IN_PROGRESS` | `` | `'pre_deploy_in_progress'` |
| `PRE_DEPLOY_FAILED` | `` | `'pre_deploy_failed'` |

### `RenderRegion`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `str, Enum`
- Summary: Common Render deployment regions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `OREGON` | `` | `'oregon'` |
| `FRANKFURT` | `` | `'frankfurt'` |
| `OHIO` | `` | `'ohio'` |
| `VIRGINIA` | `` | `'virginia'` |
| `SINGAPORE` | `` | `'singapore'` |

### `RenderEnvVar`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Summary: Environment variable — plain value or generated secret.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `key` | `str` | `` |
| `value` | `str \| None` | `None` |
| `generate_value` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderDisk`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Summary: Persistent disk attached to a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `'data'` |
| `mount_path` | `str` | `'/data'` |
| `size_gb` | `int` | `1` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `RenderAutoscaling`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Summary: Autoscaling configuration for a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `False` |
| `min` | `int` | `1` |
| `max` | `int` | `3` |
| `criteria` | `dict[str, Any] \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `disabled` | `def disabled(cls)` | No autoscaling (fixed instance count). |
| `auto` | `def auto(cls, min_instances: int=1, max_instances: int=3, cpu_percent: int=80, memory_percent: int \| None=None)` | CPU/memory-based autoscaling. |

### `RenderDeploy`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Summary: A single deploy for a Render service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `service_id` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `commit` | `dict[str, Any] \| None` | `None` |
| `image` | `dict[str, Any] \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |
| `finished_at` | `str \| None` | `None` |

### `RenderService`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Summary: A Render service (top-level resource, no App grouping).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `owner_id` | `str \| None` | `None` |
| `slug` | `str \| None` | `None` |
| `type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `plan` | `str \| None` | `None` |
| `region` | `str \| None` | `None` |
| `status` | `str \| None` | `None` |
| `suspended` | `str \| None` | `None` |
| `auto_deploy` | `str \| None` | `None` |
| `service_details` | `dict[str, Any] \| None` | `None` |
| `created_at` | `str \| None` | `None` |
| `updated_at` | `str \| None` | `None` |

### `RenderOwner`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Summary: A Render workspace/owner (user or team).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str \| None` | `None` |
| `name` | `str` | `''` |
| `email` | `str \| None` | `None` |
| `type` | `str \| None` | `None` |

### `RenderDeployConfig`

- Source: `aquilia/providers/render_backup_phase10/types.py`
- Bases: `object`
- Summary: Complete deployment configuration for ``aq deploy render``.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `service_name` | `str` | `''` |
| `service_type` | `RenderServiceType` | `RenderServiceType.WEB_SERVICE` |
| `owner_id` | `str \| None` | `None` |
| `image` | `str` | `''` |
| `plan` | `RenderPlan` | `RenderPlan.STARTER` |
| `region` | `str` | `'oregon'` |
| `num_instances` | `int` | `1` |
| `autoscaling` | `RenderAutoscaling` | `field(default_factory=RenderAutoscaling.disabled)` |
| `port` | `int` | `8000` |
| `health_check_path` | `str` | `'/_health'` |
| `env_vars` | `list[RenderEnvVar]` | `field(default_factory=list)` |
| `disk` | `RenderDisk \| None` | `None` |
| `docker_command` | `str \| None` | `None` |
| `auto_deploy` | `str` | `'no'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_service_payload` | `def to_service_payload(self)` | Serialize to Render ``POST /v1/services`` API payload. |
| `to_update_payload` | `def to_update_payload(self)` | Serialize to Render ``PATCH /v1/services/{id}`` API payload. |
| `from_workspace_context` | `def from_workspace_context(cls, wctx: dict[str, Any], *, image: str, region: str \| None=None, plan: RenderPlan \| None=None, num_instances: int=1, autoscaling: RenderAutoscaling \| None=None)` | Build config from Aquilia workspace introspection context. |
