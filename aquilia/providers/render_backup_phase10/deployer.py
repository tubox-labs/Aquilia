"""
Render Deployment Orchestrator.

Orchestrates the complete lifecycle of deploying an Aquilia workspace
to Render:

1. **Build gate** — ensure ``aq build --mode=prod`` has been run
2. **Docker build** — build the production image
3. **Docker push** — push to a registry (Docker Hub, GHCR, etc.)
4. **Env sync** — create/update Render service env vars
5. **Service deploy** — create or update the Render service
6. **Health wait** — poll deployment until live or failed

Render has **no App grouping** — services are top-level resources
owned by a workspace (``ownerId``).

Security
--------
- API tokens are loaded from the credential store, never passed as CLI args.
- Secret values are pushed via the Render env-vars API (encrypted at rest).
- Docker credentials are handled via ``docker login``.
"""

from __future__ import annotations

import logging
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aquilia.faults.domains import (
    ProviderAPIFault,
    ProviderAuthFault,
)

from .client import RenderClient
from .types import (
    RenderDeploy,
    RenderDeployConfig,
    RenderDeployStatus,
    RenderService,
)

__all__ = ["RenderDeployer", "DeployResult"]

_logger = logging.getLogger("aquilia.providers.render.deployer")


class DeployResult:
    """Result of a Render deployment operation."""

    def __init__(
        self,
        *,
        success: bool,
        service: RenderService | None = None,
        deploy: RenderDeploy | None = None,
        url: str | None = None,
        errors: list[str] | None = None,
        steps_completed: list[str] | None = None,
    ):
        self.success = success
        self.service = service
        self.deploy = deploy
        self.url = url
        self.errors = errors or []
        self.steps_completed = steps_completed or []

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"DeployResult({status}, url={self.url!r})"


class RenderDeployer:
    """Full-lifecycle Render deployment orchestrator.

    Handles the complete deploy flow from Docker build through
    health-check verification.

    Args:
        client: Authenticated RenderClient instance.
        workspace_root: Path to the Aquilia workspace.
        config: Deployment configuration.
        on_step: Optional callback for progress reporting.

    Example::

        store = RenderCredentialStore()
        token = store.load()
        client = RenderClient(token=token)

        config = RenderDeployConfig.from_workspace_context(
            wctx, image="registry/myapp:latest"
        )

        deployer = RenderDeployer(client, Path.cwd(), config)
        result = deployer.deploy()

        if result.success:
            print(f"Deployed: {result.url}")
    """

    def __init__(
        self,
        client: RenderClient,
        workspace_root: Path,
        config: RenderDeployConfig,
        *,
        on_step: Callable[[str, str], None] | None = None,
        dry_run: bool = False,
    ):
        self._client = client
        self._workspace_root = workspace_root
        self._config = config
        self._on_step = on_step or (lambda phase, msg: None)
        self._dry_run = dry_run
        self._steps: list[str] = []
        self._errors: list[str] = []

    def _step(self, phase: str, message: str) -> None:
        """Record and report a deployment step."""
        self._steps.append(f"[{phase}] {message}")
        self._on_step(phase, message)
        _logger.info("[%s] %s", phase, message)

    def _error(self, message: str) -> None:
        """Record an error."""
        self._errors.append(message)
        _logger.error(message)

    # ─── Main deploy flow ────────────────────────────────────────────

    def deploy(self) -> DeployResult:
        """Execute the complete deployment pipeline.

        Steps:
          1. Validate configuration
          2. Docker build (if image is local)
          3. Docker push (if registry configured)
          4. Resolve owner (workspace)
          5. Create or update Render service
          6. Sync environment variables
          7. Trigger deploy and wait for live
          8. Configure autoscaling (if enabled)

        Returns:
            DeployResult with success/failure status, URL, and details.
        """
        self._step("init", f"Deploying '{self._config.service_name}' to Render")

        # ── 1. Validate ──────────────────────────────────────────────
        if not self._validate():
            return DeployResult(
                success=False,
                errors=self._errors,
                steps_completed=self._steps,
            )

        if self._dry_run:
            self._step("dry-run", "Dry run complete — no changes made")
            return DeployResult(
                success=True,
                steps_completed=self._steps,
            )

        # ── 2. Docker build ──────────────────────────────────────────
        if self._should_build_docker() and not self._docker_build():
            return DeployResult(
                success=False,
                errors=self._errors,
                steps_completed=self._steps,
            )

        # ── 3. Docker push ───────────────────────────────────────────
        if self._should_push_docker() and not self._docker_push():
            return DeployResult(
                success=False,
                errors=self._errors,
                steps_completed=self._steps,
            )

        # ── 4. Resolve owner ─────────────────────────────────────────
        owner_id = self._resolve_owner()
        if not owner_id:
            return DeployResult(
                success=False,
                errors=self._errors,
                steps_completed=self._steps,
            )
        self._config.owner_id = owner_id

        # ── 5. Create or update service ──────────────────────────────
        service = self._ensure_service()
        if not service:
            return DeployResult(
                success=False,
                errors=self._errors,
                steps_completed=self._steps,
            )

        # ── 6. Sync env vars ─────────────────────────────────────────
        self._sync_env_vars(service)

        # ── 7. Trigger deploy and wait ───────────────────────────────
        deploy = self._trigger_and_wait(service)

        # ── 8. Autoscaling ───────────────────────────────────────────
        if self._config.autoscaling.enabled and service.id:
            self._configure_autoscaling(service)

        # ── 9. Resolve URL ───────────────────────────────────────────
        url = self._resolve_url(service)

        self._step("done", "Deployment complete")

        return DeployResult(
            success=deploy is not None,
            service=service,
            deploy=deploy,
            url=url,
            errors=self._errors,
            steps_completed=self._steps,
        )

    # ─── Step implementations ────────────────────────────────────────

    def _validate(self) -> bool:
        """Validate deployment configuration."""
        self._step("validate", "Checking configuration")

        if not self._config.service_name:
            self._error("Service name is required")
            return False

        if not self._config.image:
            self._error("Docker image is required")
            return False

        if not self._config.region:
            self._error("A deployment region is required")
            return False

        # Validate client auth
        self._step("validate", "Verifying API token")
        try:
            if not self._client.validate_token():
                self._error("Render API token is invalid or expired")
                return False
        except ProviderAuthFault as e:
            self._error(f"Authentication failed: {e}")
            return False
        except ProviderAPIFault as e:
            self._error(f"Cannot validate token: {e}")
            return False

        self._step("validate", "Configuration valid")
        return True

    def _should_build_docker(self) -> bool:
        """Determine if Docker build is needed."""
        image = self._config.image
        return "/" not in image or image.startswith("localhost")

    def _should_push_docker(self) -> bool:
        """Determine if Docker push is needed."""
        return "/" in self._config.image and not self._config.image.startswith("localhost")

    def _docker_build(self) -> bool:
        """Build the Docker image."""
        self._step("docker", f"Building image: {self._config.image}")

        dockerfile = self._workspace_root / "Dockerfile"
        if not dockerfile.exists():
            self._error("Dockerfile not found. Run 'aq deploy dockerfile' first or use a pre-built image with --image.")
            return False

        cmd = [
            "docker",
            "build",
            "-t",
            self._config.image,
            str(self._workspace_root),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self._workspace_root),
            )
            if result.returncode != 0:
                self._error(f"Docker build failed:\n{result.stderr[-500:]}")
                return False
        except FileNotFoundError:
            self._error("Docker is not installed or not on PATH")
            return False

        self._step("docker", "Image built successfully")
        return True

    def _docker_push(self) -> bool:
        """Push Docker image to registry."""
        self._step("docker", f"Pushing image: {self._config.image}")

        cmd = ["docker", "push", self._config.image]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self._error(f"Docker push failed:\n{result.stderr[-500:]}")
                return False
        except FileNotFoundError:
            self._error("Docker is not installed or not on PATH")
            return False

        self._step("docker", "Image pushed successfully")
        return True

    def _resolve_owner(self) -> str | None:
        """Resolve the Render owner (workspace) ID."""
        if self._config.owner_id:
            return self._config.owner_id

        self._step("owner", "Resolving Render workspace")
        try:
            owners = self._client.list_owners()
            if not owners:
                self._error("No Render workspaces found for this account")
                return None

            # Use the first owner (typically the personal workspace)
            owner = owners[0]
            self._step("owner", f"Using workspace: {owner.name} ({owner.id})")
            return owner.id
        except ProviderAPIFault as e:
            self._error(f"Failed to resolve workspace: {e}")
            return None

    def _ensure_service(self) -> RenderService | None:
        """Create or update the Render service."""
        service_name = self._config.service_name
        self._step("service", f"Resolving service: {service_name}")

        # Check for existing service
        try:
            existing = self._client.get_service_by_name(service_name, owner_id=self._config.owner_id)
            if existing and existing.id:
                self._step(
                    "service",
                    f"Updating existing service: {service_name} ({existing.id})",
                )
                payload = self._config.to_update_payload()
                updated = self._client.update_service(existing.id, payload)
                self._step("service", "Service updated")
                return updated
        except ProviderAPIFault as e:
            _logger.debug("Service lookup error: %s", e)

        # Create new service
        self._step("service", f"Creating service: {service_name}")
        try:
            payload = self._config.to_service_payload()
            service = self._client.create_service(payload)
            self._step("service", f"Service created: {service_name}")
            return service
        except ProviderAPIFault as e:
            self._error(f"Failed to create service: {e}")
            return None

    def _sync_env_vars(self, service: RenderService) -> None:
        """Sync environment variables to the Render service."""
        if not self._config.env_vars or not service.id:
            return

        self._step("env", f"Syncing {len(self._config.env_vars)} env var(s)")

        try:
            env_payload = [ev.to_dict() for ev in self._config.env_vars]
            self._client.update_env_vars(service.id, env_payload)
            self._step("env", "Environment variables synced")
        except ProviderAPIFault as e:
            _logger.warning("Could not sync env vars: %s", e)
            self._step("env", f"Warning: env var sync failed — {e}")

    def _trigger_and_wait(self, service: RenderService) -> RenderDeploy | None:
        """Trigger a deploy and wait for it to become live."""
        if not service.id:
            self._error("Cannot trigger deploy — service has no ID")
            return None

        self._step("deploy", "Triggering deployment...")

        try:
            deploy = self._client.trigger_deploy(service.id)
            self._step("deploy", f"Deploy triggered: {deploy.id}")
        except ProviderAPIFault as e:
            self._error(f"Failed to trigger deploy: {e}")
            return None

        return self._wait_for_live(service, timeout=300, poll_interval=10)

    def _wait_for_live(
        self,
        service: RenderService,
        *,
        timeout: int = 300,
        poll_interval: int = 10,
    ) -> RenderDeploy | None:
        """Poll the latest deploy until live or failed."""
        assert service.id is not None
        self._step("health", "Waiting for deployment to go live...")

        deadline = time.time() + timeout
        last_status = ""

        while time.time() < deadline:
            try:
                deploys = self._client.list_deploys(service.id, limit=1)
                if not deploys:
                    time.sleep(poll_interval)
                    continue

                latest = deploys[0]
                status = latest.status or ""

                if status != last_status:
                    self._step("health", f"Deploy status: {status}")
                    last_status = status

                if status == RenderDeployStatus.LIVE.value:
                    self._step("health", "Deployment is live!")
                    return latest

                if status in (
                    RenderDeployStatus.BUILD_FAILED.value,
                    RenderDeployStatus.UPDATE_FAILED.value,
                    RenderDeployStatus.CANCELED.value,
                    RenderDeployStatus.DEACTIVATED.value,
                    RenderDeployStatus.PRE_DEPLOY_FAILED.value,
                ):
                    self._error(f"Deployment failed with status: {status}")
                    return None

            except ProviderAPIFault as e:
                _logger.warning("Health poll error: %s", e)

            time.sleep(poll_interval)

        self._error(f"Deployment did not go live within {timeout}s. Last status: {last_status}")
        return None

    def _configure_autoscaling(self, service: RenderService) -> None:
        """Configure autoscaling if enabled."""
        assert service.id is not None
        self._step("autoscale", "Configuring autoscaling")

        try:
            self._client.set_autoscaling(service.id, self._config.autoscaling.to_dict())
            self._step(
                "autoscale",
                f"Autoscaling configured: {self._config.autoscaling.min}-{self._config.autoscaling.max} instances",
            )
        except ProviderAPIFault as e:
            _logger.warning("Could not configure autoscaling: %s", e)
            self._step("autoscale", f"Warning: autoscaling setup failed — {e}")

    def _resolve_url(self, service: RenderService) -> str | None:
        """Resolve the public URL for the deployed service."""
        # Render assigns URLs as {slug}.onrender.com
        if service.slug:
            return f"https://{service.slug}.onrender.com"

        # Try to get custom domains
        if service.id:
            try:
                domains = self._client.list_custom_domains(service.id)
                for domain in domains:
                    name = domain.get("name")
                    if name:
                        return f"https://{name}"
            except ProviderAPIFault:
                pass

        # Fallback
        return f"https://{self._config.service_name}.onrender.com"

    # ─── Utility methods ─────────────────────────────────────────────

    def destroy(self) -> bool:
        """Destroy the service.

        Returns True if destroyed successfully.
        """
        self._step("destroy", f"Destroying service: {self._config.service_name}")
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                self._step("destroy", "Service not found — nothing to destroy")
                return True
            self._client.delete_service(svc.id)
            self._step("destroy", "Service destroyed successfully")
            return True
        except ProviderAPIFault as e:
            self._error(f"Failed to destroy service: {e}")
            return False

    def status(self) -> dict[str, Any]:
        """Get current deployment status."""
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                return {
                    "status": "not_deployed",
                    "service_name": self._config.service_name,
                }

            # Get latest deploy
            deploys = self._client.list_deploys(svc.id, limit=1)
            latest_deploy = deploys[0] if deploys else None

            return {
                "status": "deployed",
                "service_name": svc.name,
                "service_id": svc.id,
                "service_status": svc.status,
                "suspended": svc.suspended,
                "plan": svc.plan,
                "region": svc.region,
                "url": self._resolve_url(svc),
                "latest_deploy": {
                    "id": latest_deploy.id,
                    "status": latest_deploy.status,
                    "created_at": latest_deploy.created_at,
                }
                if latest_deploy
                else None,
            }
        except ProviderAPIFault as e:
            return {
                "status": "error",
                "service_name": self._config.service_name,
                "error": str(e),
            }
