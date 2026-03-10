"""
Aquilia Render Provider — Comprehensive PaaS Deployment v2.

Provides everything needed to deploy an Aquilia workspace to Render:

- ``RenderClient`` — typed REST client for the FULL Render API v1
  (services, deploys, env vars, postgres, key-value, projects,
  blueprints, webhooks, log streams, metrics, and more)
- ``RenderDeployer`` — orchestrator with rollback, preview, and metrics
- ``RenderCredentialStore`` — military-grade AES-256-GCM credential storage
- ``RenderDeployConfig`` — typed deployment configuration
- CLI commands via ``aq deploy render`` and ``aq provider login render``

Usage::

    from aquilia.providers.render import RenderClient, RenderDeployer

    client = RenderClient(token="rnd_xxxxxxxxxxxx")
    deployer = RenderDeployer(client, workspace_root="/app")
    deployer.deploy()
"""

from .client import RenderClient
from .deployer import RenderDeployer, DeployResult
from .store import RenderCredentialStore
from .types import (
    # Core resources
    RenderService,
    RenderDeploy,
    RenderOwner,
    RenderEnvVar,
    RenderDisk,
    RenderDiskSnapshot,
    RenderAutoscaling,
    RenderDeployConfig,
    # Enums
    RenderServiceType,
    RenderPlan,
    RenderDeployStatus,
    RenderRegion,
    RenderServiceStatus,
    RenderJobStatus,
    RenderDomainVerificationStatus,
    RenderLogLevel,
    RenderLogDirection,
    RenderLogType,
    RenderRouteType,
    RenderMaintenanceStatus,
    RenderWebhookEventType,
    RenderNotificationType,
    RenderPostgresPlan,
    RenderKeyValuePlan,
    RenderBlueprintSyncStatus,
    RenderInstanceStatus,
    # Extended resources
    RenderSecretFile,
    RenderCustomDomain,
    RenderInstance,
    RenderEvent,
    RenderJob,
    RenderHeaderRule,
    RenderRedirectRule,
    RenderLogEntry,
    RenderMetricPoint,
    RenderMetricsFilter,
    RenderWebhook,
    RenderProject,
    RenderEnvironment,
    RenderEnvGroup,
    RenderRegistryCredential,
    RenderMaintenance,
    RenderNotificationSettings,
    RenderAuditLogEntry,
    # Postgres & Key-Value
    RenderPostgresInstance,
    RenderPostgresConnectionInfo,
    RenderPostgresUser,
    RenderKeyValueInstance,
    RenderKeyValueConnectionInfo,
    # Blueprint / IaC
    RenderBlueprint,
    RenderBlueprintSync,
    # Workspace
    RenderWorkspaceMember,
    RenderLogStream,
)

__all__ = [
    # Client & Deployer
    "RenderClient",
    "RenderDeployer",
    "DeployResult",
    "RenderCredentialStore",
    # Core resources
    "RenderService",
    "RenderDeploy",
    "RenderOwner",
    "RenderEnvVar",
    "RenderDisk",
    "RenderDiskSnapshot",
    "RenderAutoscaling",
    "RenderDeployConfig",
    # Enums
    "RenderServiceType",
    "RenderPlan",
    "RenderDeployStatus",
    "RenderRegion",
    "RenderServiceStatus",
    "RenderJobStatus",
    "RenderDomainVerificationStatus",
    "RenderLogLevel",
    "RenderLogDirection",
    "RenderLogType",
    "RenderRouteType",
    "RenderMaintenanceStatus",
    "RenderWebhookEventType",
    "RenderNotificationType",
    "RenderPostgresPlan",
    "RenderKeyValuePlan",
    "RenderBlueprintSyncStatus",
    "RenderInstanceStatus",
    # Extended resources
    "RenderSecretFile",
    "RenderCustomDomain",
    "RenderInstance",
    "RenderEvent",
    "RenderJob",
    "RenderHeaderRule",
    "RenderRedirectRule",
    "RenderLogEntry",
    "RenderMetricPoint",
    "RenderMetricsFilter",
    "RenderWebhook",
    "RenderProject",
    "RenderEnvironment",
    "RenderEnvGroup",
    "RenderRegistryCredential",
    "RenderMaintenance",
    "RenderNotificationSettings",
    "RenderAuditLogEntry",
    # Postgres & Key-Value
    "RenderPostgresInstance",
    "RenderPostgresConnectionInfo",
    "RenderPostgresUser",
    "RenderKeyValueInstance",
    "RenderKeyValueConnectionInfo",
    # Blueprint / IaC
    "RenderBlueprint",
    "RenderBlueprintSync",
    # Workspace
    "RenderWorkspaceMember",
    "RenderLogStream",
]
