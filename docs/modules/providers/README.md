# providers Module

## Purpose

Cloud provider deployment clients. Use this module for Render deployment configuration, clients, deployers, and persistent provider state.

## Source Coverage

- Python files: 11
- Public classes: 72
- Dataclasses: 42
- Enums: 22
- Public functions: 0

## How It Fits In Aquilia

1. Import the package from `aquilia.providers` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `RenderClient` | `aquilia/providers/render/client.py` | Synchronous REST client for the Render API (v1). |
| `DeployResult` | `aquilia/providers/render/deployer.py` | Result of a Render deployment operation. |
| `RenderDeployer` | `aquilia/providers/render/deployer.py` | Full-lifecycle Render deployment orchestrator. |
| `RenderCredentialStore` | `aquilia/providers/render/store.py` | Military-grade, file-based credential store for Render API tokens. |
| `RenderServiceType` | `aquilia/providers/render/types.py` | Render service type. |
| `RenderPlan` | `aquilia/providers/render/types.py` | Render compute plans. |
| `RenderDeployStatus` | `aquilia/providers/render/types.py` | Deploy lifecycle states returned by the Render API. |
| `RenderRegion` | `aquilia/providers/render/types.py` | Common Render deployment regions. |
| `RenderServiceStatus` | `aquilia/providers/render/types.py` | Service runtime statuses. |
| `RenderJobStatus` | `aquilia/providers/render/types.py` | Cron / one-off job execution states. |
| `RenderDomainVerificationStatus` | `aquilia/providers/render/types.py` | Custom domain DNS verification statuses. |
| `RenderLogLevel` | `aquilia/providers/render/types.py` | Log severity levels for the Render logging API. |
| `RenderLogDirection` | `aquilia/providers/render/types.py` | Direction for paginating logs. |
| `RenderLogType` | `aquilia/providers/render/types.py` | Render log types. |
| `RenderRouteType` | `aquilia/providers/render/types.py` | Redirect/rewrite route types for static sites. |
| `RenderMaintenanceStatus` | `aquilia/providers/render/types.py` | Maintenance window states. |
| `RenderWebhookEventType` | `aquilia/providers/render/types.py` | Event types for webhook subscriptions. |
| `RenderNotificationType` | `aquilia/providers/render/types.py` | Notification delivery channels. |
| `RenderPostgresPlan` | `aquilia/providers/render/types.py` | Render Postgres plans. |
| `RenderKeyValuePlan` | `aquilia/providers/render/types.py` | Render Key-Value (Redis) store plans. |
| `RenderBlueprintSyncStatus` | `aquilia/providers/render/types.py` | Blueprint sync / IaC sync status. |
| `RenderInstanceStatus` | `aquilia/providers/render/types.py` | Runtime instance statuses. |
| `RenderEnvVar` | `aquilia/providers/render/types.py` | Environment variable - plain value or generated secret. |
| `RenderDisk` | `aquilia/providers/render/types.py` | Persistent disk attached to a Render service. |
| `RenderDiskSnapshot` | `aquilia/providers/render/types.py` | A snapshot of a persistent disk. |
| `RenderAutoscaling` | `aquilia/providers/render/types.py` | Autoscaling configuration for a Render service. |
| `RenderDeploy` | `aquilia/providers/render/types.py` | A single deploy for a Render service. |
| `RenderService` | `aquilia/providers/render/types.py` | A Render service (top-level resource). |
| `RenderOwner` | `aquilia/providers/render/types.py` | A Render workspace/owner (user or team). |
| `RenderSecretFile` | `aquilia/providers/render/types.py` | Secret file mounted into a service container. |
| `RenderCustomDomain` | `aquilia/providers/render/types.py` | Custom domain attached to a Render service. |
| `RenderInstance` | `aquilia/providers/render/types.py` | A running instance of a Render service. |
| `RenderEvent` | `aquilia/providers/render/types.py` | An event from the Render event stream. |
| `RenderJob` | `aquilia/providers/render/types.py` | A cron or one-off job execution. |
| `RenderHeaderRule` | `aquilia/providers/render/types.py` | HTTP header rule for a Render service. |
| `RenderRedirectRule` | `aquilia/providers/render/types.py` | Redirect / rewrite rule for static sites. |
| `RenderLogEntry` | `aquilia/providers/render/types.py` | A single log line from the Render logging API. |
| `RenderMetricPoint` | `aquilia/providers/render/types.py` | A single metric data point. |
| `RenderWebhook` | `aquilia/providers/render/types.py` | A Render webhook subscription. |
| `RenderProject` | `aquilia/providers/render/types.py` | A Render project for organizing services. |
| `RenderEnvironment` | `aquilia/providers/render/types.py` | A Render environment within a project. |
| `RenderEnvGroup` | `aquilia/providers/render/types.py` | A shared environment group for linked services. |
| `RenderRegistryCredential` | `aquilia/providers/render/types.py` | Private container registry credential. |
| `RenderMaintenance` | `aquilia/providers/render/types.py` | Maintenance window for a Render service. |
| `RenderNotificationSettings` | `aquilia/providers/render/types.py` | Notification settings for a service. |
| `RenderAuditLogEntry` | `aquilia/providers/render/types.py` | An entry from the workspace audit log. |
| `RenderPostgresInstance` | `aquilia/providers/render/types.py` | A Render Postgres database instance. |
| `RenderPostgresConnectionInfo` | `aquilia/providers/render/types.py` | Connection info for a Render Postgres database. |
| `RenderPostgresUser` | `aquilia/providers/render/types.py` | A user in a Render Postgres database. |
| `RenderKeyValueInstance` | `aquilia/providers/render/types.py` | A Render Key-Value (Redis) store instance. |
| `RenderKeyValueConnectionInfo` | `aquilia/providers/render/types.py` | Connection info for a Render Key-Value store. |
| `RenderBlueprint` | `aquilia/providers/render/types.py` | A Render Blueprint (Infrastructure as Code). |
| `RenderBlueprintSync` | `aquilia/providers/render/types.py` | A blueprint sync run. |
| `RenderWorkspaceMember` | `aquilia/providers/render/types.py` | A member of a Render workspace/team. |
| `RenderLogStream` | `aquilia/providers/render/types.py` | A log stream/sink for forwarding logs. |
| `RenderMetricsFilter` | `aquilia/providers/render/types.py` | Filter/query parameters for the metrics API. |
| `RenderDeployConfig` | `aquilia/providers/render/types.py` | Complete deployment configuration for ``aq deploy render``. |
| `RenderClient` | `aquilia/providers/render_backup_phase10/client.py` | Synchronous REST client for the Render API (v1). |
| `DeployResult` | `aquilia/providers/render_backup_phase10/deployer.py` | Result of a Render deployment operation. |
| `RenderDeployer` | `aquilia/providers/render_backup_phase10/deployer.py` | Full-lifecycle Render deployment orchestrator. |
| `RenderCredentialStore` | `aquilia/providers/render_backup_phase10/store.py` | Secure, file-based credential store for Render API tokens. |
| `RenderServiceType` | `aquilia/providers/render_backup_phase10/types.py` | Render service type. |
| `RenderPlan` | `aquilia/providers/render_backup_phase10/types.py` | Render compute plans. |
| `RenderDeployStatus` | `aquilia/providers/render_backup_phase10/types.py` | Deploy lifecycle states returned by the Render API. |
| `RenderRegion` | `aquilia/providers/render_backup_phase10/types.py` | Common Render deployment regions. |
| `RenderEnvVar` | `aquilia/providers/render_backup_phase10/types.py` | Environment variable - plain value or generated secret. |
| `RenderDisk` | `aquilia/providers/render_backup_phase10/types.py` | Persistent disk attached to a Render service. |
| `RenderAutoscaling` | `aquilia/providers/render_backup_phase10/types.py` | Autoscaling configuration for a Render service. |
| `RenderDeploy` | `aquilia/providers/render_backup_phase10/types.py` | A single deploy for a Render service. |
| `RenderService` | `aquilia/providers/render_backup_phase10/types.py` | A Render service (top-level resource, no App grouping). |
| `RenderOwner` | `aquilia/providers/render_backup_phase10/types.py` | A Render workspace/owner (user or team). |
| `RenderDeployConfig` | `aquilia/providers/render_backup_phase10/types.py` | Complete deployment configuration for ``aq deploy render``. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| None detected |  |  |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/providers/__init__.py` | Aquilia Cloud Providers - Pluggable PaaS/IaaS Deployment Backends. |
| `aquilia/providers/render/__init__.py` | Aquilia Render Provider - Comprehensive PaaS Deployment v2. |
| `aquilia/providers/render/client.py` | Render REST API Client - Comprehensive v2. |
| `aquilia/providers/render/deployer.py` | Render Deployment Orchestrator - Enhanced v2. |
| `aquilia/providers/render/store.py` | Render Credential Store - Military-Grade Encrypted Token Persistence. |
| `aquilia/providers/render/types.py` | Render API Type Definitions - Comprehensive v2. |
| `aquilia/providers/render_backup_phase10/__init__.py` | Aquilia Render Provider - One-command PaaS deployment. |
| `aquilia/providers/render_backup_phase10/client.py` | Render REST API Client. |
| `aquilia/providers/render_backup_phase10/deployer.py` | Render Deployment Orchestrator. |
| `aquilia/providers/render_backup_phase10/store.py` | Render Credential Store - Crous-Encrypted Token Persistence. |
| `aquilia/providers/render_backup_phase10/types.py` | Render API Type Definitions. |

## Testing Pointers

Search `tests/` for `providers` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
