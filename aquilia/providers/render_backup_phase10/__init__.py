"""
Aquilia Render Provider — One-command PaaS deployment.

Provides everything needed to deploy an Aquilia workspace to Render:

- ``RenderClient`` — typed REST client for the Render API (v1)
- ``RenderDeployer`` — orchestrator (Docker build → push → deploy)
- ``RenderCredentialStore`` — Crous-encrypted credential storage
- ``RenderDeployConfig`` — typed deployment configuration
- CLI commands via ``aq deploy render`` and ``aq provider login render``

Usage::

    from aquilia.providers.render import RenderClient, RenderDeployer

    client = RenderClient(token="rnd_xxxxxxxxxxxx")
    deployer = RenderDeployer(client, workspace_root="/app")
    deployer.deploy()
"""

from .client import RenderClient
from .deployer import RenderDeployer
from .store import RenderCredentialStore
from .types import (
    RenderAutoscaling,
    RenderDeploy,
    RenderDeployConfig,
    RenderDeployStatus,
    RenderDisk,
    RenderEnvVar,
    RenderOwner,
    RenderPlan,
    RenderRegion,
    RenderService,
    RenderServiceType,
)

__all__ = [
    "RenderClient",
    "RenderDeployer",
    "RenderCredentialStore",
    "RenderService",
    "RenderDeploy",
    "RenderOwner",
    "RenderServiceType",
    "RenderPlan",
    "RenderDeployStatus",
    "RenderDeployConfig",
    "RenderAutoscaling",
    "RenderRegion",
    "RenderEnvVar",
    "RenderDisk",
]
