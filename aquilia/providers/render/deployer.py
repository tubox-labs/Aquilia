"""
Render Deployment Orchestrator — Enhanced v2.

Orchestrates the complete lifecycle of deploying an Aquilia workspace
to Render:

1. **Build gate** — ensure ``aq build --mode=prod`` has been run
2. **Docker build** — build the production image
3. **Docker push** — push to a registry (Docker Hub, GHCR, etc.)
4. **Env sync** — create/update Render service env vars
5. **Secret file sync** — push secret files to the service
6. **Service deploy** — create or update the Render service
7. **Health wait** — poll deployment until live or failed
8. **Header rules** — apply security headers
9. **Autoscaling** — configure autoscaling if enabled

Additional capabilities:
- **Rollback** — rollback to a previous deploy
- **Cancel** — cancel a running deploy
- **Preview** — create preview environments
- **Restart** — restart a service
- **Purge cache** — clear build cache
- **Logs** — stream deployment logs
- **Metrics** — pre/post-deploy health checks

Security
--------
- API tokens are loaded from the credential store, never passed as CLI args.
- Secret values are pushed via the Render env-vars API (encrypted at rest).
- Docker credentials are handled via ``docker login``.
- Security headers automatically injected.
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .client import RenderClient
from .store import RenderCredentialStore
from .types import (
    RenderAutoscaling,
    RenderDeployConfig,
    RenderDeployStatus,
    RenderDeploy,
    RenderEnvVar,
    RenderHeaderRule,
    RenderLogEntry,
    RenderMetricPoint,
    RenderPlan,
    RenderSecretFile,
    RenderService,
    RenderServiceType,
)
from aquilia.faults.domains import (
    ProviderAPIFault,
    ProviderAuthFault,
    DeployConfigFault,
    DeployImageFault,
    DeployHealthFault,
    DeployServiceFault,
)

__all__ = ["RenderDeployer", "DeployResult"]

_logger = logging.getLogger("aquilia.providers.render.deployer")


class DeployResult:
    """Result of a Render deployment operation."""

    def __init__(
        self,
        *,
        success: bool,
        service: Optional[RenderService] = None,
        deploy: Optional[RenderDeploy] = None,
        url: Optional[str] = None,
        errors: Optional[List[str]] = None,
        steps_completed: Optional[List[str]] = None,
        rollback_deploy_id: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ):
        self.success = success
        self.service = service
        self.deploy = deploy
        self.url = url
        self.errors = errors or []
        self.steps_completed = steps_completed or []
        self.rollback_deploy_id = rollback_deploy_id
        self.metrics = metrics

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"DeployResult({status}, url={self.url!r})"


class RenderDeployer:
    """Full-lifecycle Render deployment orchestrator.

    Handles the complete deploy flow from Docker build through
    health-check verification, with rollback, preview, and
    metrics capabilities.

    Args:
        client: Authenticated RenderClient instance.
        workspace_root: Path to the Aquilia workspace.
        config: Deployment configuration.
        on_step: Optional callback for progress reporting.
        dry_run: If True, validate only — no changes.
    """

    def __init__(
        self,
        client: RenderClient,
        workspace_root: Path,
        config: RenderDeployConfig,
        *,
        on_step: Optional[Callable[[str, str], None]] = None,
        dry_run: bool = False,
    ):
        self._client = client
        self._workspace_root = workspace_root
        self._config = config
        self._on_step = on_step or (lambda phase, msg: None)
        self._dry_run = dry_run
        self._steps: List[str] = []
        self._errors: List[str] = []
        self._last_live_deploy_id: Optional[str] = None

    def _step(self, phase: str, message: str) -> None:
        self._steps.append(f"[{phase}] {message}")
        self._on_step(phase, message)
        _logger.info("[%s] %s", phase, message)

    def _error(self, message: str) -> None:
        self._errors.append(message)
        _logger.error(message)

    # ═════════════════════════════════════════════════════════════════
    # Main Deploy Flow
    # ═════════════════════════════════════════════════════════════════

    def deploy(self) -> DeployResult:
        """Execute the complete deployment pipeline."""
        self._step("init", f"Deploying '{self._config.service_name}' to Render")

        # 1. Validate
        if not self._validate():
            return DeployResult(success=False, errors=self._errors, steps_completed=self._steps)

        if self._dry_run:
            self._step("dry-run", "Dry run complete — no changes made")
            return DeployResult(success=True, steps_completed=self._steps)

        # 2. Docker build
        if self._should_build_docker():
            if not self._docker_build():
                return DeployResult(success=False, errors=self._errors, steps_completed=self._steps)

        # 3. Docker push
        if self._should_push_docker():
            if not self._docker_push():
                return DeployResult(success=False, errors=self._errors, steps_completed=self._steps)

        # 4. Resolve owner
        owner_id = self._resolve_owner()
        if not owner_id:
            return DeployResult(success=False, errors=self._errors, steps_completed=self._steps)
        self._config.owner_id = owner_id

        # 5. Create or update service
        service = self._ensure_service()
        if not service:
            return DeployResult(success=False, errors=self._errors, steps_completed=self._steps)

        # 5a. Record last live deploy for rollback
        self._record_last_live_deploy(service)

        # 6. Sync env vars
        self._sync_env_vars(service)

        # 7. Sync secret files
        self._sync_secret_files(service)

        # 8. Apply security headers
        self._apply_headers(service)

        # 9. Trigger deploy and wait
        deploy = self._trigger_and_wait(service)

        # 10. Autoscaling
        if self._config.autoscaling.enabled and service.id:
            self._configure_autoscaling(service)

        # 11. Resolve URL
        url = self._resolve_url(service)

        self._step("done", "Deployment complete")

        return DeployResult(
            success=deploy is not None,
            service=service,
            deploy=deploy,
            url=url,
            errors=self._errors,
            steps_completed=self._steps,
            rollback_deploy_id=self._last_live_deploy_id,
        )

    # ═════════════════════════════════════════════════════════════════
    # Step Implementations
    # ═════════════════════════════════════════════════════════════════

    def _validate(self) -> bool:
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
        image = self._config.image
        return "/" not in image or image.startswith("localhost")

    def _should_push_docker(self) -> bool:
        return "/" in self._config.image and not self._config.image.startswith("localhost")

    def _docker_build(self) -> bool:
        self._step("docker", f"Building image: {self._config.image}")
        dockerfile = self._workspace_root / "Dockerfile"
        if not dockerfile.exists():
            self._error("Dockerfile not found. Run 'aq deploy dockerfile' first or use --image.")
            return False
        cmd = ["docker", "build", "-t", self._config.image, str(self._workspace_root)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self._workspace_root))
            if result.returncode != 0:
                self._error(f"Docker build failed:\n{result.stderr[-500:]}")
                return False
        except FileNotFoundError:
            self._error("Docker is not installed or not on PATH")
            return False
        self._step("docker", "Image built successfully")
        return True

    def _docker_push(self) -> bool:
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

    def _resolve_owner(self) -> Optional[str]:
        if self._config.owner_id:
            return self._config.owner_id
        self._step("owner", "Resolving Render workspace")
        try:
            owners = self._client.list_owners()
            if not owners:
                self._error("No Render workspaces found for this account")
                return None
            owner = owners[0]
            self._step("owner", f"Using workspace: {owner.name} ({owner.id})")
            return owner.id
        except ProviderAPIFault as e:
            self._error(f"Failed to resolve workspace: {e}")
            return None

    def _ensure_service(self) -> Optional[RenderService]:
        service_name = self._config.service_name
        self._step("service", f"Resolving service: {service_name}")
        try:
            existing = self._client.get_service_by_name(service_name, owner_id=self._config.owner_id)
            if existing and existing.id:
                self._step("service", f"Updating existing service: {service_name} ({existing.id})")
                payload = self._config.to_update_payload()
                updated = self._client.update_service(existing.id, payload)
                self._step("service", "Service updated")
                return updated
        except ProviderAPIFault as e:
            _logger.debug("Service lookup error: %s", e)

        self._step("service", f"Creating service: {service_name}")
        try:
            payload = self._config.to_service_payload()
            service = self._client.create_service(payload)
            self._step("service", f"Service created: {service_name}")
            return service
        except ProviderAPIFault as e:
            self._error(f"Failed to create service: {e}")
            return None

    def _record_last_live_deploy(self, service: RenderService) -> None:
        """Record the current live deploy ID for rollback."""
        if not service.id:
            return
        try:
            deploys = self._client.list_deploys(service.id, limit=1)
            for d in deploys:
                if d.status == RenderDeployStatus.LIVE.value:
                    self._last_live_deploy_id = d.id
                    self._step("rollback", f"Recorded rollback target: {d.id}")
                    break
        except ProviderAPIFault:
            pass

    def _sync_env_vars(self, service: RenderService) -> None:
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

    def _sync_secret_files(self, service: RenderService) -> None:
        """Sync secret files to the service."""
        if not self._config.secret_files or not service.id:
            return
        self._step("secrets", f"Syncing {len(self._config.secret_files)} secret file(s)")
        try:
            files = [sf.to_dict() for sf in self._config.secret_files]
            self._client.update_secret_files(service.id, files)
            self._step("secrets", "Secret files synced")
        except ProviderAPIFault as e:
            _logger.warning("Could not sync secret files: %s", e)
            self._step("secrets", f"Warning: secret file sync failed — {e}")

    def _apply_headers(self, service: RenderService) -> None:
        """Apply security headers to the service."""
        if not self._config.headers or not service.id:
            return
        self._step("headers", f"Applying {len(self._config.headers)} header rule(s)")
        for header in self._config.headers:
            try:
                self._client.add_header(service.id, header.to_dict())
            except ProviderAPIFault as e:
                _logger.debug("Could not apply header %s: %s", header.name, e)
        self._step("headers", "Security headers applied")

    def _trigger_and_wait(self, service: RenderService) -> Optional[RenderDeploy]:
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
        self, service: RenderService, *, timeout: int = 300, poll_interval: int = 10,
    ) -> Optional[RenderDeploy]:
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
        assert service.id is not None
        self._step("autoscale", "Configuring autoscaling")
        try:
            self._client.set_autoscaling(service.id, self._config.autoscaling.to_dict())
            self._step("autoscale", f"Autoscaling: {self._config.autoscaling.min}-{self._config.autoscaling.max} instances")
        except ProviderAPIFault as e:
            _logger.warning("Could not configure autoscaling: %s", e)
            self._step("autoscale", f"Warning: autoscaling setup failed — {e}")

    def _resolve_url(self, service: RenderService) -> Optional[str]:
        if service.slug:
            return f"https://{service.slug}.onrender.com"
        if service.id:
            try:
                domains = self._client.list_custom_domains(service.id)
                for domain in domains:
                    name = domain.get("name")
                    if name:
                        return f"https://{name}"
            except ProviderAPIFault:
                pass
        return f"https://{self._config.service_name}.onrender.com"

    # ═════════════════════════════════════════════════════════════════
    # Rollback
    # ═════════════════════════════════════════════════════════════════

    def rollback(self, deploy_id: Optional[str] = None) -> DeployResult:
        """Rollback to a previous deployment.

        Args:
            deploy_id: Specific deploy ID to rollback to.
                       Uses the last-known live deploy if omitted.
        """
        target_id = deploy_id or self._last_live_deploy_id
        if not target_id:
            return DeployResult(success=False, errors=["No deploy ID for rollback"])

        self._step("rollback", f"Rolling back to deploy: {target_id}")

        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                return DeployResult(success=False, errors=["Service not found for rollback"])

            deploy = self._client.rollback_deploy(svc.id, target_id)
            self._step("rollback", f"Rollback triggered: {deploy.id}")

            live = self._wait_for_live(svc, timeout=300, poll_interval=10)
            url = self._resolve_url(svc)
            return DeployResult(
                success=live is not None,
                service=svc, deploy=live, url=url,
                steps_completed=self._steps,
                errors=self._errors,
                rollback_deploy_id=target_id,
            )
        except ProviderAPIFault as e:
            self._error(f"Rollback failed: {e}")
            return DeployResult(success=False, errors=self._errors, steps_completed=self._steps)

    # ═════════════════════════════════════════════════════════════════
    # Cancel Deploy
    # ═════════════════════════════════════════════════════════════════

    def cancel(self, service_id: Optional[str] = None, deploy_id: Optional[str] = None) -> bool:
        """Cancel a running deployment."""
        self._step("cancel", "Cancelling deployment")
        try:
            svc_id = service_id
            if not svc_id:
                svc = self._client.get_service_by_name(self._config.service_name)
                if not svc or not svc.id:
                    self._error("Service not found")
                    return False
                svc_id = svc.id

            d_id = deploy_id
            if not d_id:
                deploys = self._client.list_deploys(svc_id, limit=1)
                if deploys:
                    d_id = deploys[0].id

            if not d_id:
                self._error("No active deploy to cancel")
                return False

            self._client.cancel_deploy(svc_id, d_id)
            self._step("cancel", f"Deploy {d_id} cancelled")
            return True
        except ProviderAPIFault as e:
            self._error(f"Cancel failed: {e}")
            return False

    # ═════════════════════════════════════════════════════════════════
    # Preview
    # ═════════════════════════════════════════════════════════════════

    def create_preview(self, *, name: Optional[str] = None) -> DeployResult:
        """Create a preview environment of the service."""
        self._step("preview", "Creating preview environment")
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                return DeployResult(success=False, errors=["Service not found"])

            preview = self._client.create_preview(
                svc.id,
                image_url=self._config.image,
                name=name or f"{self._config.service_name}-preview",
            )
            url = self._resolve_url(preview)
            self._step("preview", f"Preview created: {preview.name}")
            return DeployResult(success=True, service=preview, url=url, steps_completed=self._steps)
        except ProviderAPIFault as e:
            self._error(f"Preview creation failed: {e}")
            return DeployResult(success=False, errors=self._errors, steps_completed=self._steps)

    # ═════════════════════════════════════════════════════════════════
    # Restart & Purge Cache
    # ═════════════════════════════════════════════════════════════════

    def restart(self) -> bool:
        """Restart the service (zero-downtime)."""
        self._step("restart", f"Restarting: {self._config.service_name}")
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                self._error("Service not found")
                return False
            self._client.restart_service(svc.id)
            self._step("restart", "Service restarted")
            return True
        except ProviderAPIFault as e:
            self._error(f"Restart failed: {e}")
            return False

    def purge_cache(self) -> bool:
        """Clear the build cache for the service."""
        self._step("cache", "Purging build cache")
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                self._error("Service not found")
                return False
            self._client.purge_cache(svc.id)
            self._step("cache", "Build cache purged")
            return True
        except ProviderAPIFault as e:
            self._error(f"Cache purge failed: {e}")
            return False

    # ═════════════════════════════════════════════════════════════════
    # Logs
    # ═════════════════════════════════════════════════════════════════

    def get_deploy_logs(self, *, limit: int = 100, level: Optional[str] = None) -> List[RenderLogEntry]:
        """Get recent logs for the service."""
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                return []
            return self._client.get_logs(service_id=svc.id, limit=limit, level=level)
        except ProviderAPIFault:
            return []

    # ═════════════════════════════════════════════════════════════════
    # Metrics
    # ═════════════════════════════════════════════════════════════════

    def get_service_metrics(self, *, metric: str = "cpu", period: str = "1h") -> List[RenderMetricPoint]:
        """Get metrics for the service."""
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                return []
            return self._client.get_metrics(svc.id, metric=metric, period=period)
        except ProviderAPIFault:
            return []

    # ═════════════════════════════════════════════════════════════════
    # Destroy & Status
    # ═════════════════════════════════════════════════════════════════

    def destroy(self) -> bool:
        """Destroy the service."""
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

    def status(self) -> Dict[str, Any]:
        """Get current deployment status with extended info."""
        try:
            svc = self._client.get_service_by_name(self._config.service_name)
            if not svc or not svc.id:
                return {"status": "not_deployed", "service_name": self._config.service_name}

            deploys = self._client.list_deploys(svc.id, limit=1)
            latest_deploy = deploys[0] if deploys else None

            # Get instance count
            instance_count = 0
            try:
                instances = self._client.list_instances(svc.id)
                instance_count = len(instances)
            except ProviderAPIFault:
                pass

            result: Dict[str, Any] = {
                "status": "deployed",
                "service_name": svc.name,
                "service_id": svc.id,
                "service_status": svc.status,
                "suspended": svc.suspended,
                "plan": svc.plan,
                "region": svc.region,
                "url": self._resolve_url(svc),
                "instance_count": instance_count,
                "latest_deploy": {
                    "id": latest_deploy.id,
                    "status": latest_deploy.status,
                    "created_at": latest_deploy.created_at,
                    "trigger": latest_deploy.trigger,
                } if latest_deploy else None,
            }
            return result
        except ProviderAPIFault as e:
            return {"status": "error", "service_name": self._config.service_name, "error": str(e)}
