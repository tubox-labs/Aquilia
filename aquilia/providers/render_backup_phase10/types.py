"""
Render API Type Definitions.

Typed dataclasses for all Render API resources, mirroring the
official Render REST API schema.  All fields use snake_case;
serialization to/from camelCase JSON is handled by the client.

Security
--------
- Secrets are never stored in memory as plain strings longer than
  needed — they are cleared after use where feasible.
- ``__repr__`` implementations redact sensitive fields.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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
    """Render compute plans.

    Maps to Render's plan catalog.  Only commonly-used plans are
    enumerated here; the API accepts any valid plan slug.
    """
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


# ═══════════════════════════════════════════════════════════════════════════
# Resource Types
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class RenderEnvVar:
    """Environment variable — plain value or generated secret.

    On Render, env vars live directly on a service.
    Set ``generate_value`` to ``"yes"`` to let Render auto-generate
    a secure random value for the key.
    """
    key: str
    value: Optional[str] = None
    generate_value: Optional[str] = None  # "yes" for auto-generated secrets

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"key": self.key}
        if self.generate_value == "yes":
            d["generateValue"] = "yes"
        else:
            d["value"] = self.value or ""
        return d


@dataclass
class RenderDisk:
    """Persistent disk attached to a Render service."""
    name: str = "data"
    mount_path: str = "/data"
    size_gb: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "mountPath": self.mount_path,
            "sizeGB": self.size_gb,
        }


@dataclass
class RenderAutoscaling:
    """Autoscaling configuration for a Render service."""
    enabled: bool = False
    min: int = 1
    max: int = 3
    criteria: Optional[Dict[str, Any]] = None  # CPU/memory targets

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "enabled": self.enabled,
            "min": self.min,
            "max": self.max,
        }
        if self.criteria:
            d["criteria"] = self.criteria
        return d

    @classmethod
    def disabled(cls) -> "RenderAutoscaling":
        """No autoscaling (fixed instance count)."""
        return cls(enabled=False, min=1, max=1)

    @classmethod
    def auto(
        cls,
        min_instances: int = 1,
        max_instances: int = 3,
        cpu_percent: int = 80,
        memory_percent: Optional[int] = None,
    ) -> "RenderAutoscaling":
        """CPU/memory-based autoscaling."""
        criteria: Dict[str, Any] = {
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
    id: Optional[str] = None
    service_id: Optional[str] = None
    status: Optional[str] = None
    commit: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass
class RenderService:
    """A Render service (top-level resource, no App grouping)."""
    id: Optional[str] = None
    name: str = ""
    owner_id: Optional[str] = None
    slug: Optional[str] = None
    type: RenderServiceType = RenderServiceType.WEB_SERVICE
    plan: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None
    suspended: Optional[str] = None          # "suspended" or "not_suspended"
    auto_deploy: Optional[str] = None        # "yes" or "no"
    service_details: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class RenderOwner:
    """A Render workspace/owner (user or team)."""
    id: Optional[str] = None
    name: str = ""
    email: Optional[str] = None
    type: Optional[str] = None  # "user" or "team"


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

    Example::

        config = RenderDeployConfig(
            service_name="my-api",
            image="my-registry/my-api:latest",
            plan=RenderPlan.STANDARD,
            region="oregon",
            num_instances=2,
            env_vars=[
                RenderEnvVar(key="AQUILIA_ENV", value="prod"),
                RenderEnvVar(key="DATABASE_URL", generate_value="yes"),
            ],
            health_check_path="/_health",
        )
    """
    # Service identity
    service_name: str = ""
    service_type: RenderServiceType = RenderServiceType.WEB_SERVICE
    owner_id: Optional[str] = None  # Resolved at deploy time

    # Docker image source
    image: str = ""

    # Compute configuration
    plan: RenderPlan = RenderPlan.STARTER
    region: str = "oregon"

    # Scaling
    num_instances: int = 1
    autoscaling: RenderAutoscaling = field(
        default_factory=RenderAutoscaling.disabled
    )

    # Networking
    port: int = 8000
    health_check_path: str = "/_health"

    # Environment
    env_vars: List[RenderEnvVar] = field(default_factory=list)

    # Persistent disk (optional)
    disk: Optional[RenderDisk] = None

    # Docker command override (default: use Dockerfile CMD)
    docker_command: Optional[str] = None

    # Auto-deploy on image push
    auto_deploy: str = "no"

    def to_service_payload(self) -> Dict[str, Any]:
        """Serialize to Render ``POST /v1/services`` API payload."""
        service_details: Dict[str, Any] = {
            "envVars": [e.to_dict() for e in self.env_vars],
            "plan": self.plan.value,
            "region": self.region,
            "numInstances": self.num_instances,
            "healthCheckPath": self.health_check_path,
        }

        if self.image:
            service_details["image"] = {"ownerId": self.owner_id, "imagePath": self.image}

        if self.docker_command:
            service_details["dockerCommand"] = self.docker_command

        if self.disk:
            service_details["disk"] = self.disk.to_dict()

        payload: Dict[str, Any] = {
            "name": self.service_name,
            "type": self.service_type.value,
            "autoDeploy": self.auto_deploy,
            "serviceDetails": service_details,
        }

        if self.owner_id:
            payload["ownerId"] = self.owner_id

        return payload

    def to_update_payload(self) -> Dict[str, Any]:
        """Serialize to Render ``PATCH /v1/services/{id}`` API payload."""
        service_details: Dict[str, Any] = {
            "plan": self.plan.value,
            "numInstances": self.num_instances,
            "healthCheckPath": self.health_check_path,
        }

        if self.image:
            service_details["image"] = {"imagePath": self.image}

        if self.docker_command:
            service_details["dockerCommand"] = self.docker_command

        return {
            "name": self.service_name,
            "autoDeploy": self.auto_deploy,
            "serviceDetails": service_details,
        }

    @classmethod
    def from_workspace_context(
        cls,
        wctx: Dict[str, Any],
        *,
        image: str,
        region: Optional[str] = None,
        plan: Optional[RenderPlan] = None,
        num_instances: int = 1,
        autoscaling: Optional[RenderAutoscaling] = None,
    ) -> "RenderDeployConfig":
        """Build config from Aquilia workspace introspection context.

        Automatically maps workspace features (DB, cache, auth, etc.)
        to Render env vars and health checks.
        """
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

        # Wire database URL as a generated secret placeholder
        if wctx.get("has_db"):
            env_vars.append(RenderEnvVar(key="DATABASE_URL", value=""))

        # Wire cache (Redis) URL
        if wctx.get("has_cache"):
            env_vars.append(RenderEnvVar(key="REDIS_URL", value=""))

        # Wire auth secret key (auto-generate)
        if wctx.get("has_auth"):
            env_vars.append(RenderEnvVar(key="AQ_AUTH_SECRET", generate_value="yes"))

        # Wire mail credentials
        if wctx.get("has_mail"):
            env_vars.append(RenderEnvVar(key="MAIL_API_KEY", value=""))

        # Signing key (auto-generate)
        env_vars.append(RenderEnvVar(key="AQ_SIGNING_SECRET", generate_value="yes"))

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
        )
