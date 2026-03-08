"""
AquilAdmin -- Subsystem Integration Module.

Integrates Aquilia's core subsystems into the admin dashboard for
production-grade operation:

    Cache   → Rate limiter state persistence, query caching, fragment caching
    Effects → Typed capability declarations for admin handlers
    Tasks   → Background jobs for audit cleanup, session pruning, security alerts
    Flow    → Guard/transform/handler pipelines for admin request processing
    Lifecycle → Startup/shutdown hooks for admin initialisation and teardown

Architecture:
    AdminSubsystems (orchestrator)
    ├── AdminCacheIntegration
    │   ├── cache_model_list(model, page, filters)
    │   ├── cache_dashboard_stats()
    │   ├── invalidate_model(model)
    │   └── rate_limiter_store(key, record)
    ├── AdminEffects
    │   ├── AdminDBEffect       → DB transactions for admin CRUD
    │   ├── AdminCacheEffect    → Cache namespace for admin data
    │   └── AdminTaskEffect     → Task queue for background work
    ├── AdminTasks
    │   ├── audit_log_cleanup   → Prune old audit entries
    │   ├── session_cleanup     → Remove expired admin sessions
    │   ├── security_report     → Aggregate security events
    │   └── rate_limit_cleanup  → Clear stale rate limit records
    ├── AdminFlow
    │   ├── AdminAuthGuard      → Verify admin authentication
    │   ├── AdminPermGuard      → Check permissions for action
    │   ├── AdminCSRFGuard      → Validate CSRF token
    │   ├── AdminRateLimitGuard → Check rate limits
    │   └── AdminAuditHook      → Log action in audit trail
    └── AdminLifecycle
        ├── on_startup()        → Initialize admin, flush pending registrations
        └── on_shutdown()       → Flush audit log, cleanup rate limiter
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.admin.site import AdminSite
    from aquilia.auth.core import Identity
    from aquilia.controller.base import RequestCtx
    from aquilia.response import Response

logger = logging.getLogger("aquilia.admin.subsystems")


# ═══════════════════════════════════════════════════════════════════════════════
#  Cache Integration
# ═══════════════════════════════════════════════════════════════════════════════


class AdminCacheIntegration:
    """
    Integrates Aquilia CacheService into admin operations.

    Provides:
    - Model list query caching with automatic invalidation
    - Dashboard statistics caching
    - Rate limiter state persistence (optional cache backend)
    - Admin page fragment caching

    Uses the ``admin`` cache namespace to isolate admin data from
    application caches.
    """

    NAMESPACE = "admin"
    MODEL_LIST_TTL = 30         # 30 seconds for model list views
    DASHBOARD_TTL = 60          # 60 seconds for dashboard stats
    FRAGMENT_TTL = 120          # 2 minutes for template fragments
    RATE_LIMIT_TTL = 3600       # 1 hour for rate limiter records

    def __init__(self, cache_service: Optional[Any] = None):
        self._cache = cache_service
        self._enabled = cache_service is not None

    @property
    def enabled(self) -> bool:
        """Check if cache integration is available."""
        return self._enabled

    def set_cache_service(self, service: Any) -> None:
        """
        Set the CacheService instance (called during server startup).

        Args:
            service: CacheService instance from DI container.
        """
        self._cache = service
        self._enabled = service is not None

    async def get_model_list(
        self,
        model_name: str,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
        search: str = "",
        ordering: str = "",
    ) -> Optional[Any]:
        """
        Get cached model list result.

        Args:
            model_name: Name of the model
            page: Page number
            filters: Active filter dict
            search: Search query
            ordering: Sort ordering

        Returns:
            Cached result or None if not cached.
        """
        if not self._enabled:
            return None
        key = self._model_list_key(model_name, page, filters, search, ordering)
        try:
            return await self._cache.get(key, namespace=self.NAMESPACE)
        except Exception:
            return None

    async def set_model_list(
        self,
        model_name: str,
        page: int,
        filters: Optional[Dict[str, Any]],
        search: str,
        ordering: str,
        data: Any,
    ) -> None:
        """Cache a model list result."""
        if not self._enabled:
            return
        key = self._model_list_key(model_name, page, filters, search, ordering)
        try:
            await self._cache.set(key, data, ttl=self.MODEL_LIST_TTL, namespace=self.NAMESPACE)
        except Exception:
            pass

    async def invalidate_model(self, model_name: str) -> int:
        """
        Invalidate all cached data for a model after CUD operations.

        Args:
            model_name: Name of the model to invalidate.

        Returns:
            Number of keys invalidated.
        """
        if not self._enabled:
            return 0
        try:
            # Use tag-based invalidation if available
            if hasattr(self._cache, "invalidate_tag"):
                return await self._cache.invalidate_tag(f"model:{model_name}")
            # Fallback: delete known key patterns
            return 0
        except Exception:
            return 0

    async def get_dashboard_stats(self) -> Optional[Dict[str, Any]]:
        """Get cached dashboard statistics."""
        if not self._enabled:
            return None
        try:
            return await self._cache.get("dashboard_stats", namespace=self.NAMESPACE)
        except Exception:
            return None

    async def set_dashboard_stats(self, stats: Dict[str, Any]) -> None:
        """Cache dashboard statistics."""
        if not self._enabled:
            return
        try:
            await self._cache.set(
                "dashboard_stats", stats,
                ttl=self.DASHBOARD_TTL,
                namespace=self.NAMESPACE,
            )
        except Exception:
            pass

    async def get_fragment(self, fragment_key: str) -> Optional[str]:
        """Get a cached template fragment."""
        if not self._enabled:
            return None
        try:
            return await self._cache.get(f"fragment:{fragment_key}", namespace=self.NAMESPACE)
        except Exception:
            return None

    async def set_fragment(self, fragment_key: str, html: str, ttl: Optional[int] = None) -> None:
        """Cache a template fragment."""
        if not self._enabled:
            return
        try:
            await self._cache.set(
                f"fragment:{fragment_key}", html,
                ttl=ttl or self.FRAGMENT_TTL,
                namespace=self.NAMESPACE,
            )
        except Exception:
            pass

    def _model_list_key(
        self,
        model_name: str,
        page: int,
        filters: Optional[Dict[str, Any]],
        search: str,
        ordering: str,
    ) -> str:
        """Build a deterministic cache key for model list queries."""
        import hashlib
        filter_str = ""
        if filters:
            sorted_filters = sorted(filters.items())
            filter_str = "&".join(f"{k}={v}" for k, v in sorted_filters)
        raw = f"{model_name}:p{page}:f={filter_str}:s={search}:o={ordering}"
        # Use hash for long keys
        if len(raw) > 200:
            h = hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()
            return f"list:{model_name}:{h}"
        return f"list:{raw}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Effects Integration
# ═══════════════════════════════════════════════════════════════════════════════


class AdminDBEffect:
    """
    Typed effect token for admin database operations.

    Used to declare that an admin handler requires DB access.

    Usage::

        from aquilia.admin.subsystems import AdminDBEffect

        @requires(AdminDBEffect("write"))
        async def create_record(ctx, model, data):
            ...
    """

    def __init__(self, mode: str = "read"):
        self.name = "AdminDB"
        self.mode = mode
        self.kind = "db"

    def __repr__(self) -> str:
        return f"AdminDBEffect[{self.mode}]"


class AdminCacheEffect:
    """
    Typed effect token for admin cache operations.

    Usage::

        @requires(AdminCacheEffect("admin"))
        async def list_models(ctx, model_name):
            ...
    """

    def __init__(self, namespace: str = "admin"):
        self.name = "AdminCache"
        self.mode = namespace
        self.kind = "cache"

    def __repr__(self) -> str:
        return f"AdminCacheEffect[{self.mode}]"


class AdminTaskEffect:
    """
    Typed effect token for admin background task dispatch.

    Usage::

        @requires(AdminTaskEffect())
        async def trigger_audit_cleanup(ctx):
            ...
    """

    def __init__(self, queue: str = "admin"):
        self.name = "AdminTask"
        self.mode = queue
        self.kind = "queue"

    def __repr__(self) -> str:
        return f"AdminTaskEffect[{self.mode}]"


# ═══════════════════════════════════════════════════════════════════════════════
#  Task Integration
# ═══════════════════════════════════════════════════════════════════════════════


class AdminTasks:
    """
    Background tasks for admin housekeeping.

    Integrates with Aquilia's TaskManager to schedule periodic maintenance:
    - Audit log cleanup (prune old entries beyond max_entries)
    - Session cleanup (remove expired admin sessions)
    - Security event aggregation (summarise for monitoring dashboard)
    - Rate limiter state cleanup (remove stale IP records)

    Tasks are registered during admin startup and can be triggered
    on-demand via the admin dashboard.
    """

    def __init__(self, task_manager: Optional[Any] = None):
        self._task_manager = task_manager
        self._registered = False

    @property
    def enabled(self) -> bool:
        """Check if task integration is available."""
        return self._task_manager is not None

    def set_task_manager(self, manager: Any) -> None:
        """Set the TaskManager instance during server startup."""
        self._task_manager = manager

    async def audit_log_cleanup(self, max_entries: int = 10_000) -> Dict[str, Any]:
        """
        Prune old audit log entries beyond the configured maximum.

        Args:
            max_entries: Maximum entries to retain.

        Returns:
            Dict with ``pruned`` count and ``remaining`` count.
        """
        try:
            from .site import AdminSite
            site = AdminSite.default()
            audit_log = site.audit_log

            total = len(audit_log._entries) if hasattr(audit_log, "_entries") else 0
            pruned = 0

            if total > max_entries:
                pruned = total - max_entries
                if hasattr(audit_log, "_entries"):
                    audit_log._entries = audit_log._entries[-max_entries:]

            return {"pruned": pruned, "remaining": total - pruned}
        except Exception as exc:
            logger.error("Audit log cleanup failed: %s", exc)
            return {"pruned": 0, "remaining": 0, "error": str(exc)}

    async def session_cleanup(self) -> Dict[str, Any]:
        """
        Remove expired admin sessions.

        Returns:
            Dict with ``cleaned`` count.
        """
        cleaned = 0
        try:
            from .models import AdminSession
            if hasattr(AdminSession, "objects") and hasattr(AdminSession.objects, "filter"):
                # If ORM is available, delete expired sessions
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                expired = await AdminSession.objects.filter(
                    expires_at__lt=now
                ).delete()
                cleaned = expired if isinstance(expired, int) else 0
        except Exception:
            pass

        return {"cleaned": cleaned}

    async def security_report(self) -> Dict[str, Any]:
        """
        Generate a summary of recent security events.

        Returns:
            Dict with event counts by type and recent IPs.
        """
        try:
            from .site import AdminSite
            site = AdminSite.default()
            tracker = site.security.event_tracker

            events = tracker.get_events(limit=1000)
            by_type: Dict[str, int] = {}
            by_ip: Dict[str, int] = {}

            for event in events:
                by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
                by_ip[event.ip_address] = by_ip.get(event.ip_address, 0) + 1

            # Top 10 offending IPs
            top_ips = sorted(by_ip.items(), key=lambda x: x[1], reverse=True)[:10]

            report = {
                "total_events": len(events),
                "by_type": by_type,
                "top_ips": [{"ip": ip, "count": cnt} for ip, cnt in top_ips],
                "generated_at": time.time(),
            }
            return report
        except Exception as exc:
            logger.error("Security report generation failed: %s", exc)
            return {"error": str(exc)}

    async def rate_limit_cleanup(self) -> Dict[str, Any]:
        """
        Force cleanup of stale rate limiter records.

        Returns:
            Dict with ``cleaned_login`` and ``cleaned_sensitive`` counts.
        """
        try:
            from .site import AdminSite
            site = AdminSite.default()
            limiter = site.security.rate_limiter

            before_login = len(limiter._login_records)
            before_sensitive = len(limiter._sensitive_records)

            # Force cleanup by resetting the last_cleanup time
            limiter._last_cleanup = 0
            limiter._maybe_cleanup()

            cleaned_login = before_login - len(limiter._login_records)
            cleaned_sensitive = before_sensitive - len(limiter._sensitive_records)

            return {
                "cleaned_login": max(0, cleaned_login),
                "cleaned_sensitive": max(0, cleaned_sensitive),
            }
        except Exception as exc:
            logger.error("Rate limit cleanup failed: %s", exc)
            return {"error": str(exc)}

    async def enqueue_audit_cleanup(self, max_entries: int = 10_000) -> Optional[str]:
        """
        Enqueue audit cleanup as a background task.

        Returns:
            Job ID if task manager is available, else None.
        """
        if not self._task_manager:
            # Run inline if no task manager
            await self.audit_log_cleanup(max_entries)
            return None
        try:
            job_id = await self._task_manager.enqueue(
                self.audit_log_cleanup,
                max_entries=max_entries,
            )
            return str(job_id)
        except Exception as exc:
            logger.warning("Failed to enqueue audit cleanup: %s", exc)
            await self.audit_log_cleanup(max_entries)
            return None

    async def enqueue_session_cleanup(self) -> Optional[str]:
        """Enqueue session cleanup as a background task."""
        if not self._task_manager:
            await self.session_cleanup()
            return None
        try:
            job_id = await self._task_manager.enqueue(self.session_cleanup)
            return str(job_id)
        except Exception as exc:
            logger.warning("Failed to enqueue session cleanup: %s", exc)
            await self.session_cleanup()
            return None


# ═══════════════════════════════════════════════════════════════════════════════
#  Flow Integration (Guard/Transform/Handler Pipelines)
# ═══════════════════════════════════════════════════════════════════════════════


class AdminAuthGuard:
    """
    Flow guard that verifies admin authentication.

    Rejects requests where the identity is missing or not an admin user.
    Integrates with Aquilia's FlowPipeline as a guard node.

    Usage::

        pipeline = FlowPipeline("admin_request")
        pipeline.guard(AdminAuthGuard())
    """

    name = "admin_auth_guard"
    priority = 10  # Runs first (authentication)

    def __call__(self, ctx: Any) -> bool:
        """
        Check if request has valid admin identity.

        Args:
            ctx: FlowContext or RequestCtx

        Returns:
            True if admin authenticated, False to reject.
        """
        identity = getattr(ctx, "identity", None)
        if identity is None:
            return False

        # Check for admin-level access
        roles = []
        if hasattr(identity, "roles"):
            roles = identity.roles if isinstance(identity.roles, (list, tuple, set)) else []
        elif hasattr(identity, "claims") and isinstance(identity.claims, dict):
            roles = identity.claims.get("roles", [])

        admin_roles = {"superadmin", "admin", "staff", "editor", "viewer"}
        if isinstance(roles, (list, tuple, set)):
            return bool(set(str(r).lower() for r in roles) & admin_roles)

        return False

    def __repr__(self) -> str:
        return f"AdminAuthGuard(priority={self.priority})"


class AdminPermGuard:
    """
    Flow guard that checks model-level permissions.

    Usage::

        pipeline.guard(AdminPermGuard(model="User", action="change"))
    """

    name = "admin_perm_guard"
    priority = 20  # Runs after auth guard

    def __init__(self, model: str = "", action: str = "view"):
        self.model = model
        self.action = action

    def __call__(self, ctx: Any) -> bool:
        """Check if identity has required model permission."""
        identity = getattr(ctx, "identity", None)
        if identity is None:
            return False

        try:
            from .permissions import has_model_permission
            return has_model_permission(identity, self.model, self.action)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"AdminPermGuard(model={self.model!r}, action={self.action!r})"


class AdminCSRFGuard:
    """
    Flow guard that validates CSRF tokens for POST/PUT/DELETE requests.

    Usage::

        pipeline.guard(AdminCSRFGuard(security_policy))
    """

    name = "admin_csrf_guard"
    priority = 15  # After auth, before perm

    def __init__(self, security_policy: Optional[Any] = None):
        self._policy = security_policy

    def __call__(self, ctx: Any) -> bool:
        """
        Validate CSRF token for mutating requests.

        Safe methods (GET, HEAD, OPTIONS) always pass.
        """
        method = "GET"
        request = getattr(ctx, "request", None)
        if request:
            method = getattr(request, "method", "GET")
        elif hasattr(ctx, "method"):
            method = ctx.method

        # Safe methods don't need CSRF
        if method.upper() in ("GET", "HEAD", "OPTIONS"):
            return True

        if not self._policy:
            return True

        try:
            return self._policy.csrf.validate_request(ctx)
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"AdminCSRFGuard(priority={self.priority})"


class AdminRateLimitGuard:
    """
    Flow guard that enforces rate limits on admin requests.

    Usage::

        pipeline.guard(AdminRateLimitGuard(security_policy, operation="login"))
    """

    name = "admin_rate_limit_guard"
    priority = 5  # Runs first (before even auth)

    def __init__(self, security_policy: Optional[Any] = None, operation: str = "login"):
        self._policy = security_policy
        self._operation = operation

    def __call__(self, ctx: Any) -> bool:
        """Check if the request is within rate limits."""
        if not self._policy:
            return True

        ip = self._extract_ip(ctx)
        if self._operation == "login":
            locked, _ = self._policy.rate_limiter.is_login_locked(ip)
            return not locked
        else:
            allowed, _ = self._policy.rate_limiter.check_sensitive_op(ip, self._operation)
            return allowed

    def _extract_ip(self, ctx: Any) -> str:
        """Extract client IP from context."""
        if self._policy:
            request = getattr(ctx, "request", None)
            if request:
                return self._policy.extract_client_ip(request)
        return "unknown"

    def __repr__(self) -> str:
        return f"AdminRateLimitGuard(operation={self._operation!r})"


class AdminAuditHook:
    """
    Flow hook that logs admin actions to the audit trail.

    Runs after the handler completes (post-handler hook).

    Usage::

        pipeline.hook(AdminAuditHook())
    """

    name = "admin_audit_hook"
    priority = 90  # Runs late (after handler)

    def __init__(self, action: str = "view", model_name: str = ""):
        self.action = action
        self.model_name = model_name

    async def __call__(self, ctx: Any, result: Any = None) -> None:
        """Log the admin action to the audit trail."""
        try:
            from .site import AdminSite
            site = AdminSite.default()

            identity = getattr(ctx, "identity", None)
            username = "anonymous"
            if identity:
                username = getattr(identity, "name", None) or getattr(identity, "username", "unknown")

            ip = "unknown"
            request = getattr(ctx, "request", None)
            if request and hasattr(site.security, "extract_client_ip"):
                ip = site.security.extract_client_ip(request)

            await site.audit_log.log(
                action=self.action,
                user=username,
                model_name=self.model_name,
                ip_address=ip,
            )
        except Exception:
            pass

    def __repr__(self) -> str:
        return f"AdminAuditHook(action={self.action!r}, model={self.model_name!r})"


def build_admin_flow_pipeline(
    security_policy: Optional[Any] = None,
    model_name: str = "",
    action: str = "view",
    require_auth: bool = True,
    require_csrf: bool = False,
    rate_limit_op: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a standard admin flow pipeline configuration.

    Returns a dict describing the guards/hooks that should be applied
    to an admin request. Can be consumed by FlowPipeline.from_config()
    or used directly as a descriptor.

    Args:
        security_policy: AdminSecurityPolicy instance
        model_name: Name of the model (for perm checks and audit)
        action: Action being performed (view/add/change/delete)
        require_auth: Whether to require admin authentication
        require_csrf: Whether to validate CSRF tokens
        rate_limit_op: If set, rate limit this operation

    Returns:
        Pipeline configuration dict.
    """
    guards = []
    hooks = []

    if rate_limit_op:
        guards.append(AdminRateLimitGuard(security_policy, operation=rate_limit_op))

    if require_auth:
        guards.append(AdminAuthGuard())

    if require_csrf:
        guards.append(AdminCSRFGuard(security_policy))

    if model_name and action:
        guards.append(AdminPermGuard(model=model_name, action=action))

    # Always add audit hook
    hooks.append(AdminAuditHook(action=action, model_name=model_name))

    return {
        "name": f"admin_{action}_{model_name or 'site'}",
        "guards": guards,
        "hooks": hooks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Lifecycle Integration
# ═══════════════════════════════════════════════════════════════════════════════


class AdminLifecycle:
    """
    Admin lifecycle hooks for integration with Aquilia's LifecycleCoordinator.

    Provides startup and shutdown hooks:
    - **Startup**: Initialize admin site, flush pending registrations,
      set up cache and task integrations, register DI providers.
    - **Shutdown**: Flush audit log to persistent storage, cleanup
      rate limiter state, finalize background tasks.
    """

    def __init__(self) -> None:
        self._cache_integration = AdminCacheIntegration()
        self._tasks = AdminTasks()
        self._started = False

    @property
    def cache(self) -> AdminCacheIntegration:
        """Get the cache integration."""
        return self._cache_integration

    @property
    def tasks(self) -> AdminTasks:
        """Get the task integration."""
        return self._tasks

    async def on_startup(self, config: Optional[Dict[str, Any]] = None, container: Optional[Any] = None) -> None:
        """
        Admin startup hook.

        Called by LifecycleCoordinator during application startup.

        1. Initialize AdminSite singleton
        2. Wire cache service if available in DI container
        3. Wire task manager if available in DI container
        4. Register admin security DI providers

        Args:
            config: Application configuration dict
            container: DI container
        """
        if self._started:
            return

        try:
            # 1. Initialize admin site
            from .site import AdminSite
            site = AdminSite.default()
            site.initialize()

            # 2. Wire cache service from DI
            if container:
                try:
                    from aquilia.cache import CacheService
                    cache = container.resolve(CacheService)
                    if cache:
                        self._cache_integration.set_cache_service(cache)
                except Exception:
                    pass

                # 3. Wire task manager from DI
                try:
                    from aquilia.tasks import TaskManager
                    task_mgr = container.resolve(TaskManager)
                    if task_mgr:
                        self._tasks.set_task_manager(task_mgr)
                except Exception:
                    pass

                # 4. Register security DI providers
                try:
                    from .security import register_security_providers
                    security_config = None
                    if hasattr(site, "admin_config"):
                        security_config = site.admin_config.security_config
                    register_security_providers(container, security_config)
                except Exception:
                    pass

            self._started = True

        except Exception as exc:
            logger.error("Admin lifecycle startup error: %s", exc)

    async def on_shutdown(self, config: Optional[Dict[str, Any]] = None, container: Optional[Any] = None) -> None:
        """
        Admin shutdown hook.

        Called by LifecycleCoordinator during application shutdown.

        1. Flush audit log to persistent storage
        2. Run rate limiter cleanup
        3. Clear cache entries

        Args:
            config: Application configuration dict
            container: DI container
        """
        try:
            # 1. Flush audit log
            from .site import AdminSite
            site = AdminSite.default()
            if hasattr(site.audit_log, "flush"):
                try:
                    await site.audit_log.flush()
                except Exception as exc:
                    logger.warning("Audit log flush failed: %s", exc)

            # 2. Rate limiter cleanup
            try:
                await self._tasks.rate_limit_cleanup()
            except Exception:
                pass

            # 3. Clear security event tracker
            try:
                site.security.event_tracker.clear()
            except Exception:
                pass

            self._started = False

        except Exception as exc:
            logger.error("Admin lifecycle shutdown error: %s", exc)


# ═══════════════════════════════════════════════════════════════════════════════
#  Orchestrator
# ═══════════════════════════════════════════════════════════════════════════════


class AdminSubsystems:
    """
    Central orchestrator for all admin subsystem integrations.

    Provides a single entry point for accessing cache, tasks, flow,
    effects, and lifecycle integration from within admin controllers.

    Usage::

        subsystems = AdminSubsystems()

        # During startup
        await subsystems.lifecycle.on_startup(config, container)

        # In admin controllers
        cached_list = await subsystems.cache.get_model_list("User", page=1)

        # Build a flow pipeline for a request
        pipeline = subsystems.build_pipeline(
            model_name="User", action="change",
            require_csrf=True,
        )

        # Schedule background cleanup
        await subsystems.tasks.enqueue_audit_cleanup()

        # During shutdown
        await subsystems.lifecycle.on_shutdown()
    """

    _instance: Optional["AdminSubsystems"] = None

    def __init__(self) -> None:
        self._lifecycle = AdminLifecycle()

    @classmethod
    def default(cls) -> "AdminSubsystems":
        """Get or create the default AdminSubsystems singleton."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None

    @property
    def lifecycle(self) -> AdminLifecycle:
        """Get lifecycle integration."""
        return self._lifecycle

    @property
    def cache(self) -> AdminCacheIntegration:
        """Get cache integration."""
        return self._lifecycle.cache

    @property
    def tasks(self) -> AdminTasks:
        """Get task integration."""
        return self._lifecycle.tasks

    def build_pipeline(
        self,
        model_name: str = "",
        action: str = "view",
        require_auth: bool = True,
        require_csrf: bool = False,
        rate_limit_op: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a flow pipeline for an admin request.

        Args:
            model_name: Model being accessed
            action: Action being performed
            require_auth: Whether to require admin auth
            require_csrf: Whether to validate CSRF
            rate_limit_op: Rate limit operation name

        Returns:
            Pipeline configuration dict with guards and hooks.
        """
        security_policy = None
        try:
            from .site import AdminSite
            site = AdminSite.default()
            security_policy = site.security
        except Exception:
            pass

        return build_admin_flow_pipeline(
            security_policy=security_policy,
            model_name=model_name,
            action=action,
            require_auth=require_auth,
            require_csrf=require_csrf,
            rate_limit_op=rate_limit_op,
        )


# ── Convenience factory ──────────────────────────────────────────────────────

def get_admin_subsystems() -> AdminSubsystems:
    """Get the default AdminSubsystems instance."""
    return AdminSubsystems.default()


__all__ = [
    # Cache
    "AdminCacheIntegration",
    # Effects
    "AdminDBEffect",
    "AdminCacheEffect",
    "AdminTaskEffect",
    # Tasks
    "AdminTasks",
    # Flow guards / hooks
    "AdminAuthGuard",
    "AdminPermGuard",
    "AdminCSRFGuard",
    "AdminRateLimitGuard",
    "AdminAuditHook",
    "build_admin_flow_pipeline",
    # Lifecycle
    "AdminLifecycle",
    # Orchestrator
    "AdminSubsystems",
    "get_admin_subsystems",
]
