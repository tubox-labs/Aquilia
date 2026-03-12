"""
Render API Type Definitions — Comprehensive v2.

Typed dataclasses for **all** Render API v1 resources, covering:
services, deploys, env vars, custom domains, disks, autoscaling,
secret files, headers, redirect/rewrite rules, jobs, instances,
events, logs, metrics, postgres databases, key-value stores,
projects, environments, env groups, registry credentials, webhooks,
maintenance windows, notifications, blueprints, log streams,
and workspace/members.

All fields use snake_case; serialization to/from camelCase JSON
is handled by the client.

Security
--------
- Secrets are never stored in memory as plain strings longer than
  needed — they are cleared after use where feasible.
- ``__repr__`` implementations redact sensitive fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ═══════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════


class RenderServiceType(str, Enum):
    """Render service type."""

    WEB_SERVICE = "web_service"
    PRIVATE_SERVICE = "private_service"
    BACKGROUND_WORKER = "background_worker"
    CRON_JOB = "cron_job"
    STATIC_SITE = "static_site"


class RenderPlan(str, Enum):
    """Render compute plans."""

    FREE = "free"
    STARTER = "starter"
    STANDARD = "standard"
    PRO = "pro"
    PRO_PLUS = "pro_plus"
    PRO_MAX = "pro_max"
    PRO_ULTRA = "pro_ultra"


class RenderDeployStatus(str, Enum):
    """Deploy lifecycle states returned by the Render API."""

    CREATED = "created"
    BUILD_IN_PROGRESS = "build_in_progress"
    UPDATE_IN_PROGRESS = "update_in_progress"
    LIVE = "live"
    DEACTIVATED = "deactivated"
    BUILD_FAILED = "build_failed"
    UPDATE_FAILED = "update_failed"
    CANCELED = "canceled"
    PRE_DEPLOY_IN_PROGRESS = "pre_deploy_in_progress"
    PRE_DEPLOY_FAILED = "pre_deploy_failed"


class RenderRegion(str, Enum):
    """Common Render deployment regions."""

    OREGON = "oregon"
    FRANKFURT = "frankfurt"
    OHIO = "ohio"
    VIRGINIA = "virginia"
    SINGAPORE = "singapore"


class RenderServiceStatus(str, Enum):
    """Service runtime statuses."""

    CREATING = "creating"
    DEPLOYING = "deploying"
    LIVE = "live"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


class RenderJobStatus(str, Enum):
    """Cron / one-off job execution states."""

    CREATED = "created"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class RenderDomainVerificationStatus(str, Enum):
    """Custom domain DNS verification statuses."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PENDING = "pending"


class RenderLogLevel(str, Enum):
    """Log severity levels for the Render logging API."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class RenderLogDirection(str, Enum):
    """Direction for paginating logs."""

    FORWARD = "forward"
    BACKWARD = "backward"


class RenderLogType(str, Enum):
    """Render log types."""

    APP = "app"
    BUILD = "build"
    DEPLOY = "deploy"
    REQUEST = "request"


class RenderRouteType(str, Enum):
    """Redirect/rewrite route types for static sites."""

    REDIRECT = "redirect"
    REWRITE = "rewrite"


class RenderMaintenanceStatus(str, Enum):
    """Maintenance window states."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class RenderWebhookEventType(str, Enum):
    """Event types for webhook subscriptions."""

    DEPLOY_STARTED = "deploy_started"
    DEPLOY_ENDED = "deploy_ended"
    SERVICE_CREATED = "service_created"
    SERVICE_DELETED = "service_deleted"
    SERVICE_SUSPENDED = "service_suspended"
    SERVICE_RESUMED = "service_resumed"
    SERVER_FAILED = "server_failed"


class RenderNotificationType(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class RenderPostgresPlan(str, Enum):
    """Render Postgres plans."""

    FREE = "free"
    STARTER = "starter"
    STANDARD = "standard"
    PRO = "pro"
    PRO_PLUS = "pro_plus"
    ACCELERATED = "accelerated"
    CUSTOM = "custom"


class RenderKeyValuePlan(str, Enum):
    """Render Key-Value (Redis) store plans."""

    FREE = "free"
    STARTER = "starter"
    STANDARD = "standard"
    PRO = "pro"


class RenderBlueprintSyncStatus(str, Enum):
    """Blueprint sync / IaC sync status."""

    SYNCED = "synced"
    SYNCING = "syncing"
    FAILED = "failed"
    NOT_SYNCED = "not_synced"


class RenderInstanceStatus(str, Enum):
    """Runtime instance statuses."""

    RUNNING = "running"
    STARTING = "starting"
    STOPPED = "stopped"
    CRASHED = "crashed"
    DRAINING = "draining"


# ═══════════════════════════════════════════════════════════════════════════
# Core Resource Types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RenderEnvVar:
    """Environment variable — plain value or generated secret."""

    key: str
    value: str | None = None
    generate_value: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"key": self.key}
        if self.generate_value == "yes":
            d["generateValue"] = "yes"
        else:
            d["value"] = self.value or ""
        return d


@dataclass
class RenderDisk:
    """Persistent disk attached to a Render service."""

    id: str | None = None
    name: str = "data"
    mount_path: str = "/data"
    size_gb: int = 1
    service_id: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "mountPath": self.mount_path,
            "sizeGB": self.size_gb,
        }


@dataclass
class RenderDiskSnapshot:
    """A snapshot of a persistent disk."""

    id: str | None = None
    disk_id: str | None = None
    created_at: str | None = None
    status: str | None = None


@dataclass
class RenderAutoscaling:
    """Autoscaling configuration for a Render service."""

    enabled: bool = False
    min: int = 1
    max: int = 3
    criteria: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "enabled": self.enabled,
            "min": self.min,
            "max": self.max,
        }
        if self.criteria:
            d["criteria"] = self.criteria
        return d

    @classmethod
    def disabled(cls) -> RenderAutoscaling:
        return cls(enabled=False, min=1, max=1)

    @classmethod
    def auto(
        cls,
        min_instances: int = 1,
        max_instances: int = 3,
        cpu_percent: int = 80,
        memory_percent: int | None = None,
    ) -> RenderAutoscaling:
        criteria: dict[str, Any] = {
            "cpu": {"enabled": True, "percentage": cpu_percent},
        }
        if memory_percent:
            criteria["memory"] = {"enabled": True, "percentage": memory_percent}
        return cls(
            enabled=True,
            min=min_instances,
            max=max_instances,
            criteria=criteria,
        )


@dataclass
class RenderDeploy:
    """A single deploy for a Render service."""

    id: str | None = None
    service_id: str | None = None
    status: str | None = None
    commit: dict[str, Any] | None = None
    image: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    finished_at: str | None = None
    trigger: str | None = None


@dataclass
class RenderService:
    """A Render service (top-level resource)."""

    id: str | None = None
    name: str = ""
    owner_id: str | None = None
    slug: str | None = None
    type: RenderServiceType = RenderServiceType.WEB_SERVICE
    plan: str | None = None
    region: str | None = None
    status: str | None = None
    suspended: str | None = None
    auto_deploy: str | None = None
    service_details: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    dashboard_url: str | None = None
    image_path: str | None = None
    build_filter: dict[str, Any] | None = None
    root_dir: str | None = None
    notify_on_fail: str | None = None


@dataclass
class RenderOwner:
    """A Render workspace/owner (user or team)."""

    id: str | None = None
    name: str = ""
    email: str | None = None
    type: str | None = None


# ═══════════════════════════════════════════════════════════════════════════
# Extended Resource Types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RenderSecretFile:
    """Secret file mounted into a service container."""

    name: str
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "content": self.content}

    def __repr__(self) -> str:
        return f"RenderSecretFile(name={self.name!r}, content='***')"


@dataclass
class RenderCustomDomain:
    """Custom domain attached to a Render service."""

    id: str | None = None
    name: str = ""
    domain_type: str | None = None
    verification_status: str | None = None
    redirect_for_name: str | None = None
    created_at: str | None = None
    server: dict[str, Any] | None = None


@dataclass
class RenderInstance:
    """A running instance of a Render service."""

    id: str | None = None
    service_id: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    region: str | None = None
    image_hash: str | None = None


@dataclass
class RenderEvent:
    """An event from the Render event stream."""

    id: str | None = None
    service_id: str | None = None
    type: str | None = None
    timestamp: str | None = None
    details: dict[str, Any] | None = None
    status_code: int | None = None


@dataclass
class RenderJob:
    """A cron or one-off job execution."""

    id: str | None = None
    service_id: str | None = None
    status: str | None = None
    plan_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None


@dataclass
class RenderHeaderRule:
    """HTTP header rule for a Render service."""

    id: str | None = None
    path: str = "/*"
    name: str = ""
    value: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "name": self.name, "value": self.value}


@dataclass
class RenderRedirectRule:
    """Redirect / rewrite rule for static sites."""

    id: str | None = None
    source: str = ""
    destination: str = ""
    type: str = "redirect"
    status_code: int = 301

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "destination": self.destination,
            "type": self.type,
            "statusCode": self.status_code,
        }


@dataclass
class RenderLogEntry:
    """A single log line from the Render logging API."""

    timestamp: str | None = None
    message: str = ""
    level: str | None = None
    service_id: str | None = None
    instance_id: str | None = None
    deploy_id: str | None = None
    type: str | None = None


@dataclass
class RenderMetricPoint:
    """A single metric data point."""

    timestamp: str | None = None
    value: float = 0.0
    unit: str | None = None
    label: str | None = None


@dataclass
class RenderWebhook:
    """A Render webhook subscription."""

    id: str | None = None
    url: str = ""
    secret: str | None = None
    events: list[str] = field(default_factory=list)
    enabled: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"url": self.url, "events": self.events, "enabled": self.enabled}
        if self.secret:
            d["secret"] = self.secret
        return d

    def __repr__(self) -> str:
        return f"RenderWebhook(id={self.id!r}, url={self.url!r}, events={self.events!r}, secret='***')"


@dataclass
class RenderProject:
    """A Render project for organizing services."""

    id: str | None = None
    name: str = ""
    owner_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    environment_ids: list[str] = field(default_factory=list)


@dataclass
class RenderEnvironment:
    """A Render environment within a project."""

    id: str | None = None
    name: str = ""
    project_id: str | None = None
    protected_status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class RenderEnvGroup:
    """A shared environment group for linked services."""

    id: str | None = None
    name: str = ""
    owner_id: str | None = None
    env_vars: list[RenderEnvVar] = field(default_factory=list)
    secret_files: list[RenderSecretFile] = field(default_factory=list)
    service_links: list[str] = field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "envVars": [e.to_dict() for e in self.env_vars],
            "secretFiles": [s.to_dict() for s in self.secret_files],
        }


@dataclass
class RenderRegistryCredential:
    """Private container registry credential."""

    id: str | None = None
    name: str = ""
    registry: str = ""  # e.g. "DOCKER", "GITHUB", "GITLAB"
    username: str = ""
    created_at: str | None = None

    def __repr__(self) -> str:
        return (
            f"RenderRegistryCredential(id={self.id!r}, name={self.name!r}, "
            f"registry={self.registry!r}, username={self.username!r})"
        )


@dataclass
class RenderMaintenance:
    """Maintenance window for a Render service."""

    id: str | None = None
    service_id: str | None = None
    status: str | None = None
    scheduled_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    description: str | None = None


@dataclass
class RenderNotificationSettings:
    """Notification settings for a service."""

    notify_on_fail: str | None = None  # "default", "notify", "ignore"
    preview_notify_on_fail: str | None = None


@dataclass
class RenderAuditLogEntry:
    """An entry from the workspace audit log."""

    id: str | None = None
    action: str | None = None
    actor: dict[str, Any] | None = None
    resource: dict[str, Any] | None = None
    timestamp: str | None = None
    details: dict[str, Any] | None = None


# ═══════════════════════════════════════════════════════════════════════════
# Postgres & Key-Value Types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RenderPostgresInstance:
    """A Render Postgres database instance."""

    id: str | None = None
    name: str = ""
    owner_id: str | None = None
    plan: str | None = None
    region: str | None = None
    status: str | None = None
    version: str | None = None
    disk_size_gb: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    dashboard_url: str | None = None
    primary_postgres_id: str | None = None
    high_availability_enabled: bool = False
    read_replicas: list[str] = field(default_factory=list)


@dataclass
class RenderPostgresConnectionInfo:
    """Connection info for a Render Postgres database."""

    internal_connection_string: str | None = None
    external_connection_string: str | None = None
    psql_command: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None
    user: str | None = None
    password: str | None = None

    def __repr__(self) -> str:
        return "RenderPostgresConnectionInfo(***redacted***)"


@dataclass
class RenderPostgresUser:
    """A user in a Render Postgres database."""

    name: str = ""
    password: str | None = None
    grants: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"RenderPostgresUser(name={self.name!r}, password='***')"


@dataclass
class RenderKeyValueInstance:
    """A Render Key-Value (Redis) store instance."""

    id: str | None = None
    name: str = ""
    owner_id: str | None = None
    plan: str | None = None
    region: str | None = None
    status: str | None = None
    max_memory_policy: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class RenderKeyValueConnectionInfo:
    """Connection info for a Render Key-Value store."""

    internal_connection_string: str | None = None
    external_connection_string: str | None = None
    host: str | None = None
    port: int | None = None
    password: str | None = None

    def __repr__(self) -> str:
        return "RenderKeyValueConnectionInfo(***redacted***)"


# ═══════════════════════════════════════════════════════════════════════════
# Blueprint / IaC Types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RenderBlueprint:
    """A Render Blueprint (Infrastructure as Code)."""

    id: str | None = None
    name: str = ""
    status: str | None = None
    auto_sync: bool = False
    repo: str | None = None
    branch: str | None = None
    owner_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    last_sync: dict[str, Any] | None = None


@dataclass
class RenderBlueprintSync:
    """A blueprint sync run."""

    id: str | None = None
    blueprint_id: str | None = None
    status: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None


# ═══════════════════════════════════════════════════════════════════════════
# Workspace / Team Types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RenderWorkspaceMember:
    """A member of a Render workspace/team."""

    id: str | None = None
    email: str | None = None
    name: str | None = None
    role: str | None = None  # "owner", "admin", "member", "viewer"
    joined_at: str | None = None


@dataclass
class RenderLogStream:
    """A log stream/sink for forwarding logs."""

    id: str | None = None
    name: str = ""
    endpoint: str = ""
    token: str | None = None
    enabled: bool = True
    created_at: str | None = None

    def __repr__(self) -> str:
        return f"RenderLogStream(id={self.id!r}, name={self.name!r}, endpoint={self.endpoint!r}, token='***')"


@dataclass
class RenderMetricsFilter:
    """Filter/query parameters for the metrics API."""

    resource_id: str | None = None
    metric: str = "cpu"  # cpu, memory, http_request_count, bandwidth, disk
    period: str = "1h"  # 1h, 6h, 24h, 7d, 30d
    start_time: str | None = None
    end_time: str | None = None
    instance_id: str | None = None

    def to_params(self) -> dict[str, str]:
        params: dict[str, str] = {"metric": self.metric, "period": self.period}
        if self.resource_id:
            params["resourceId"] = self.resource_id
        if self.start_time:
            params["startTime"] = self.start_time
        if self.end_time:
            params["endTime"] = self.end_time
        if self.instance_id:
            params["instanceId"] = self.instance_id
        return params


# ═══════════════════════════════════════════════════════════════════════════
# Deployment Configuration
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RenderDeployConfig:
    """Complete deployment configuration for ``aq deploy render``.

    This is the high-level configuration object that the deployer
    consumes.  It can be built programmatically or from workspace
    introspection.

    Unlike Koyeb, Render has **no App grouping** — services are
    top-level resources owned by a workspace (``owner_id``).
    """

    # Service identity
    service_name: str = ""
    service_type: RenderServiceType = RenderServiceType.WEB_SERVICE
    owner_id: str | None = None

    # Docker image source
    image: str = ""

    # Compute configuration
    plan: RenderPlan = RenderPlan.STARTER
    region: str = "oregon"

    # Scaling
    num_instances: int = 1
    autoscaling: RenderAutoscaling = field(default_factory=RenderAutoscaling.disabled)

    # Networking
    port: int = 8000
    health_check_path: str = "/_health"

    # Environment
    env_vars: list[RenderEnvVar] = field(default_factory=list)

    # Persistent disk (optional)
    disk: RenderDisk | None = None

    # Docker command override
    docker_command: str | None = None

    # Auto-deploy on image push
    auto_deploy: str = "no"

    # Extended fields (v2)
    secret_files: list[RenderSecretFile] = field(default_factory=list)
    headers: list[RenderHeaderRule] = field(default_factory=list)
    redirect_rules: list[RenderRedirectRule] = field(default_factory=list)
    registry_credential_id: str | None = None
    notify_on_fail: str | None = None  # "default", "notify", "ignore"
    pre_deploy_command: str | None = None
    build_command: str | None = None
    root_dir: str | None = None
    env_group_ids: list[str] = field(default_factory=list)
    project_id: str | None = None
    environment_id: str | None = None

    def to_service_payload(self) -> dict[str, Any]:
        """Serialize to Render ``POST /v1/services`` API payload."""
        service_details: dict[str, Any] = {
            "envVars": [e.to_dict() for e in self.env_vars],
            "plan": self.plan.value,
            "region": self.region,
            "numInstances": self.num_instances,
            "healthCheckPath": self.health_check_path,
        }

        if self.image:
            img_payload: dict[str, Any] = {"imagePath": self.image}
            if self.owner_id:
                img_payload["ownerId"] = self.owner_id
            if self.registry_credential_id:
                img_payload["registryCredentialId"] = self.registry_credential_id
            service_details["image"] = img_payload

        if self.docker_command:
            service_details["dockerCommand"] = self.docker_command

        if self.disk:
            service_details["disk"] = self.disk.to_dict()

        if self.secret_files:
            service_details["secretFiles"] = [sf.to_dict() for sf in self.secret_files]

        if self.headers:
            service_details["headers"] = [h.to_dict() for h in self.headers]

        if self.redirect_rules:
            service_details["routes"] = [r.to_dict() for r in self.redirect_rules]

        if self.pre_deploy_command:
            service_details["preDeployCommand"] = self.pre_deploy_command

        if self.build_command:
            service_details["buildCommand"] = self.build_command

        payload: dict[str, Any] = {
            "name": self.service_name,
            "type": self.service_type.value,
            "autoDeploy": self.auto_deploy,
            "serviceDetails": service_details,
        }

        if self.owner_id:
            payload["ownerId"] = self.owner_id
        if self.root_dir:
            payload["rootDir"] = self.root_dir
        if self.notify_on_fail:
            payload["notifyOnFail"] = self.notify_on_fail
        if self.env_group_ids:
            payload["envSpecificDetails"] = {"envGroupIds": self.env_group_ids}
        if self.project_id:
            payload["projectId"] = self.project_id
        if self.environment_id:
            payload["environmentId"] = self.environment_id

        return payload

    def to_update_payload(self) -> dict[str, Any]:
        """Serialize to Render ``PATCH /v1/services/{id}`` API payload."""
        service_details: dict[str, Any] = {
            "plan": self.plan.value,
            "numInstances": self.num_instances,
            "healthCheckPath": self.health_check_path,
        }

        if self.image:
            img_payload: dict[str, Any] = {"imagePath": self.image}
            if self.registry_credential_id:
                img_payload["registryCredentialId"] = self.registry_credential_id
            service_details["image"] = img_payload

        if self.docker_command:
            service_details["dockerCommand"] = self.docker_command

        if self.pre_deploy_command:
            service_details["preDeployCommand"] = self.pre_deploy_command

        if self.build_command:
            service_details["buildCommand"] = self.build_command

        payload: dict[str, Any] = {
            "name": self.service_name,
            "autoDeploy": self.auto_deploy,
            "serviceDetails": service_details,
        }
        if self.root_dir:
            payload["rootDir"] = self.root_dir
        if self.notify_on_fail:
            payload["notifyOnFail"] = self.notify_on_fail

        return payload

    @classmethod
    def from_workspace_context(
        cls,
        wctx: dict[str, Any],
        *,
        image: str,
        region: str | None = None,
        plan: RenderPlan | None = None,
        num_instances: int = 1,
        autoscaling: RenderAutoscaling | None = None,
    ) -> RenderDeployConfig:
        """Build config from Aquilia workspace introspection context."""
        name = wctx.get("name", "aquilia-app")
        port = wctx.get("port", 8000)
        workers = wctx.get("workers", 4)

        env_vars = [
            RenderEnvVar(key="AQUILIA_ENV", value="prod"),
            RenderEnvVar(key="AQUILIA_WORKSPACE", value="/app"),
            RenderEnvVar(key="AQ_SERVER_HOST", value="0.0.0.0"),
            RenderEnvVar(key="AQ_SERVER_PORT", value=str(port)),
            RenderEnvVar(key="AQ_SERVER_WORKERS", value=str(workers)),
            RenderEnvVar(key="PYTHONUNBUFFERED", value="1"),
            RenderEnvVar(key="PYTHONDONTWRITEBYTECODE", value="1"),
        ]

        if wctx.get("has_db"):
            env_vars.append(RenderEnvVar(key="DATABASE_URL", value=""))
        if wctx.get("has_cache"):
            env_vars.append(RenderEnvVar(key="REDIS_URL", value=""))
        if wctx.get("has_auth"):
            env_vars.append(RenderEnvVar(key="AQ_AUTH_SECRET", generate_value="yes"))
        if wctx.get("has_mail"):
            env_vars.append(RenderEnvVar(key="MAIL_API_KEY", value=""))

        env_vars.append(RenderEnvVar(key="AQ_SIGNING_SECRET", generate_value="yes"))

        # Security headers by default
        security_headers = [
            RenderHeaderRule(path="/*", name="X-Content-Type-Options", value="nosniff"),
            RenderHeaderRule(path="/*", name="X-Frame-Options", value="DENY"),
            RenderHeaderRule(path="/*", name="Referrer-Policy", value="strict-origin-when-cross-origin"),
            RenderHeaderRule(path="/*", name="X-XSS-Protection", value="1; mode=block"),
            RenderHeaderRule(
                path="/*",
                name="Strict-Transport-Security",
                value="max-age=63072000; includeSubDomains; preload",
            ),
            RenderHeaderRule(
                path="/*",
                name="Permissions-Policy",
                value="camera=(), microphone=(), geolocation=()",
            ),
        ]

        return cls(
            service_name=name,
            service_type=RenderServiceType.WEB_SERVICE,
            image=image,
            plan=plan or RenderPlan.STARTER,
            region=region or "oregon",
            num_instances=num_instances,
            autoscaling=autoscaling or RenderAutoscaling.disabled(),
            port=port,
            health_check_path="/_health",
            env_vars=env_vars,
            headers=security_headers,
        )
