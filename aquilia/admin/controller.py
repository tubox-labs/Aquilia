"""
AquilAdmin -- Admin Controller.

Full-featured admin controller mounted at /admin with:
- Dashboard with model stats
- Session-based authentication (login/logout)
- CRUD views for all registered models
- Search, filtering, pagination
- Bulk actions
- Audit log viewer
- Permission-checked at every endpoint

Integrates with Aquilia's Controller system, Sessions,
Auth, and TemplateEngine.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from aquilia.controller.base import Controller, RequestCtx
from aquilia.controller.decorators import GET, POST
from aquilia.response import Response

from .site import AdminSite
from .permissions import (
    AdminPermission,
    get_admin_role,
    has_admin_permission,
    require_admin_access,
)
from .audit import AdminAction
from .faults import AdminAuthorizationFault, AdminAuthenticationFault, AdminCSRFViolationFault
from .security import AdminSecurityPolicy
from .templates import (
    render_login_page,
    render_dashboard,
    render_list_view,
    render_form_view,
    render_audit_page,
    render_orm_page,
    render_build_page,
    render_migrations_page,
    render_config_page,
    render_permissions_page,
    render_workspace_page,
    render_monitoring_page,
    render_containers_page,
    render_pods_page,
    render_storage_page,
    render_admin_users_page,
    render_profile_page,
    render_error_page,
    render_disabled_page,
    render_forbidden_page,
    render_query_inspector_page,
    render_tasks_page,
    render_errors_page,
    render_testing_page,
    render_mlops_page,
    render_mailer_page,
)

if TYPE_CHECKING:
    from aquilia.auth.core import Identity

logger = logging.getLogger("aquilia.admin.controller")


# ── Shared helpers ───────────────────────────────────────────────────


def _extract_request_meta(request) -> dict:
    """Extract IP address and user agent from request for audit logging."""
    ip_address = None
    user_agent = None
    try:
        # Try X-Forwarded-For first, then X-Real-IP, then peer info
        if hasattr(request, 'headers'):
            hdrs = request.headers
            if hasattr(hdrs, 'get'):
                forwarded = hdrs.get('x-forwarded-for')
                if forwarded:
                    # Take the first IP (client IP) from comma-separated list
                    ip_address = forwarded.split(',')[0].strip()
                else:
                    ip_address = hdrs.get('x-real-ip')
                user_agent = hdrs.get('user-agent')
        if not ip_address and hasattr(request, 'scope'):
            client = request.scope.get('client')
            if client and isinstance(client, (list, tuple)) and len(client) >= 1:
                ip_address = str(client[0])
    except Exception:
        pass
    return {"ip_address": ip_address or "", "user_agent": user_agent or ""}


def _html_response(html_content: str, status: int = 200) -> Response:
    """Create an HTML response."""
    return Response(
        content=html_content.encode("utf-8"),
        status=status,
        headers={"content-type": "text/html; charset=utf-8"},
    )


# Placeholder used in templates for the per-request CSP nonce.
# _secure_html_response replaces every occurrence before sending.
_CSP_NONCE_PLACEHOLDER = "__CSP_NONCE__"


def _secure_html_response(
    html_content: str,
    site: "AdminSite",
    status: int = 200,
    *,
    is_asset: bool = False,
) -> Response:
    """Create an HTML response with security headers applied.

    Generates a per-request CSP nonce, substitutes the ``__CSP_NONCE__``
    placeholder that appears in every inline ``<script nonce=...>`` tag,
    then passes the same nonce to the security-headers layer so the
    Content-Security-Policy header matches.
    """
    nonce = site.security.headers.generate_nonce()
    # Replace placeholder in rendered HTML so every inline <script> carries
    # the correct nonce attribute before the bytes are written to the wire.
    if _CSP_NONCE_PLACEHOLDER in html_content:
        html_content = html_content.replace(_CSP_NONCE_PLACEHOLDER, nonce)
    resp = Response(
        content=html_content.encode("utf-8"),
        status=status,
        headers={"content-type": "text/html; charset=utf-8"},
    )
    return site.security.protect_response(resp, nonce=nonce, is_asset=is_asset)


def _redirect(url: str) -> Response:
    """Create a redirect response."""
    return Response(
        content=b"",
        status=302,
        headers={"location": url},
    )


def _get_identity(ctx: RequestCtx) -> Optional[Identity]:
    """
    Extract admin identity from session or request context.

    Resolution order:
    1. Session-stored admin identity (``_admin_identity`` key)
    2. ``ctx.identity`` (populated by auth middleware / guards)
    """
    if ctx.session and hasattr(ctx.session, "data"):
        admin_data = ctx.session.data.get("_admin_identity")
        if admin_data:
            try:
                from aquilia.auth.core import Identity
                return Identity.from_dict(admin_data)
            except Exception:
                pass
    # Also check ctx.identity
    if ctx.identity:
        return ctx.identity
    return None


def _get_identity_name(identity: Optional[Identity]) -> str:
    """Get display name from identity."""
    if identity is None:
        return "Anonymous"
    return identity.get_attribute("name", identity.get_attribute("username", identity.id))


def _get_identity_avatar(identity: Optional[Identity]) -> str:
    """Get avatar URL from identity (empty string if none set).

    Normalises legacy ``avatar_path`` values that were stored before the
    ``/profile/avatar/<filename>`` sub-path was introduced:

    * Bare filename          ``abc123.jpg``          → ``/admin/profile/avatar/abc123.jpg``
    * Old prefix (no /avatar) ``/admin/profile/abc123.jpg`` → ``/admin/profile/avatar/abc123.jpg``
    * Already-correct URL   ``/admin/profile/avatar/abc123.jpg`` → unchanged
    """
    if identity is None:
        return ""
    raw = identity.get_attribute("avatar_path", "") or ""
    if not raw:
        return ""
    # Already correct form: contains /profile/avatar/
    if "/profile/avatar/" in raw:
        return raw
    import re as _re
    # Legacy: stored as /admin/profile/<filename> (missing /avatar/ segment)
    legacy = _re.match(r"^(/[^/]+)/profile/([^/]+\.[a-zA-Z0-9]+)$", raw)
    if legacy:
        prefix, fname = legacy.group(1), legacy.group(2)
        return f"{prefix}/profile/avatar/{fname}"
    # Bare filename with no path component
    if "/" not in raw and "." in raw:
        return f"/admin/profile/avatar/{raw}"
    # Unknown format — return as-is and let the browser deal with it
    return raw


def _require_identity(ctx: RequestCtx) -> tuple:
    """
    Extract and verify admin identity from request context.

    Combines the recurring pattern of:
    1. ``_get_identity(ctx)``
    2. ``require_admin_access(identity)``
    3. Redirect to ``/admin/login`` on failure

    Returns:
        ``(identity, None)`` on success -- caller uses ``identity``.
        ``(None, redirect_response)`` on failure -- caller returns the response.
    """
    identity = _get_identity(ctx)
    if identity is None:
        return None, _redirect("/admin/login")
    try:
        require_admin_access(identity)
    except AdminAuthorizationFault:
        return None, _redirect("/admin/login")
    return identity, None


async def _parse_form(ctx: RequestCtx, *, multi: bool = False) -> Dict[str, Any]:
    """
    Parse form data from request context into a plain dict.

    Handles the ``FormData.fields.to_dict()`` pattern that repeats
    across all POST handlers.

    Args:
        ctx: Request context
        multi: If True, keep multi-value lists (for bulk actions)

    Returns:
        Plain dict of field name → value
    """
    try:
        raw_form = await ctx.form()
        if hasattr(raw_form, 'fields'):
            return raw_form.fields.to_dict(multi=multi)
        if isinstance(raw_form, dict):
            return dict(raw_form)
        return {}
    except Exception:
        return {}


def _get_avatar_dir() -> Path:
    """
    Resolve .aquilia/admin/profile/ under the current workspace root (cwd).

    Creates the directory tree if it does not exist.
    Returns the absolute Path to the profile avatars directory.
    """
    avatar_dir = Path(os.getcwd()) / ".aquilia" / "admin" / "profile"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    return avatar_dir


_ALLOWED_IMAGE_TYPES: Dict[bytes, tuple] = {
    b"\xff\xd8\xff":       ("jpg",  "image/jpeg"),
    b"\x89PNG\r\n\x1a\n": ("png",  "image/png"),
    b"GIF87a":            ("gif",  "image/gif"),
    b"GIF89a":            ("gif",  "image/gif"),
    b"RIFF":              ("webp", "image/webp"),  # RIFF....WEBP
}
_MAX_AVATAR_BYTES = 4 * 1024 * 1024  # 4 MB


def _sniff_image_ext(data: bytes) -> Optional[str]:
    """Return file extension for known image magic bytes, or None."""
    for magic, (ext, _) in _ALLOWED_IMAGE_TYPES.items():
        if data[:len(magic)] == magic:
            # Extra check for WebP: bytes 8-12 must be b'WEBP'
            if ext == "webp" and data[8:12] != b"WEBP":
                continue
            return ext
    return None


class AdminController(Controller):
    """
    Aquilia Admin Controller.

    Provides the complete admin web interface at /admin/*.
    All endpoints are session-authenticated and permission-checked.

    Routes:
        GET  /admin/             → Dashboard
        GET  /admin/login        → Login page
        POST /admin/login        → Authenticate
        GET  /admin/logout       → Logout
        GET  /admin/{model}/     → List view
        GET  /admin/{model}/add  → Add form
        POST /admin/{model}/add  → Create record
        GET  /admin/{model}/{pk} → Edit form
        POST /admin/{model}/{pk} → Update record
        POST /admin/{model}/{pk}/delete → Delete record
        GET  /admin/audit/       → Audit log
    """

    prefix = "/admin"
    tags = ["admin"]

    def __init__(self, site: Optional[AdminSite] = None):
        self.site = site or AdminSite.default()

    def _ensure_initialized(self) -> None:
        """Ensure the admin site has been initialized (lazy init)."""
        if not self.site._initialized:
            self.site.initialize()

    def _module_disabled_response(self, module: str, identity) -> Response:
        """Return a styled page with blur overlay when a module is disabled.

        Instead of a flat 404, the actual page layout is rendered with a
        beautiful blurred glass overlay prompting the developer to enable
        the feature in their workspace config.  This gives context about
        *what* the page would show and *how* to activate it.
        """
        app_list = self.site.get_app_list(identity) if identity else []
        identity_name = _get_identity_name(identity)

        # Map module names to their config param hint
        _config_hints = {
            "Monitoring": (
                "Integration.AdminMonitoring().enable()",
                "enable_monitoring=True",
                "monitoring",
                "System metrics, CPU, memory, disk, and network monitoring with live charts.",
            ),
            "Audit Log": (
                "Integration.AdminAudit().enable()",
                "enable_audit=True",
                "audit",
                "Complete activity trail -- every action, login, and data change recorded.",
            ),
            "ORM Models": (
                "Integration.AdminModules().enable_orm()",
                "enable_orm=True",
                "orm",
                "Explore registered models, schema, relations, and indexes.",
            ),
            "Build": (
                "Integration.AdminModules().enable_build()",
                "enable_build=True",
                "build",
                "Build artifacts, pipeline status, and Crous output.",
            ),
            "Migrations": (
                "Integration.AdminModules().enable_migrations()",
                "enable_migrations=True",
                "migrations",
                "Database migration history with syntax-highlighted source.",
            ),
            "Configuration": (
                "Integration.AdminModules().enable_config()",
                "enable_config=True",
                "config",
                "Workspace configuration files and settings overview.",
            ),
            "Workspace": (
                "Integration.AdminModules().enable_workspace()",
                "enable_workspace=True",
                "workspace",
                "Modules, manifests, and project metadata inspector.",
            ),
            "Permissions": (
                "Integration.AdminModules().enable_permissions()",
                "enable_permissions=True",
                "permissions",
                "Role matrix and per-model access control management.",
            ),
            "Admin Users": (
                "Integration.AdminModules().enable_admin_users()",
                "enable_admin_users=True",
                "admin_users",
                "Admin user accounts, roles, and hierarchy management.",
            ),
            "Profile": (
                "Integration.AdminModules().enable_profile()",
                "enable_profile=True",
                "profile",
                "Your admin profile, avatar, and password management.",
            ),
            "Containers": (
                "Integration.AdminModules().enable_containers()",
                "enable_containers=True",
                "container",
                "Docker containers, images, volumes, networks, and Compose services.",
            ),
            "Pods": (
                "Integration.AdminModules().enable_pods()",
                "enable_pods=True",
                "cloud",
                "Kubernetes pods, deployments, services, and cluster management.",
            ),
            "Query Inspector": (
                "Integration.AdminModules().enable_query_inspector()",
                "enable_query_inspector=True",
                "terminal",
                "Live SQL profiling, ORM→SQL translation, EXPLAIN plans, and N+1 detection.",
            ),
            "Background Tasks": (
                "Integration.AdminModules().enable_tasks()",
                "enable_tasks=True",
                "clock",
                "Background task queue, job lifecycle, retries, and worker monitoring.",
            ),
            "Error Monitoring": (
                "Integration.AdminModules().enable_errors()",
                "enable_errors=True",
                "alert-triangle",
                "Error tracking with stack traces, grouping, frequency analysis, and trends.",
            ),
            "Testing Framework": (
                "Integration.AdminModules().enable_testing()",
                "enable_testing=True",
                "check-circle",
                "Test infrastructure, assertions, fixtures, mock systems, coverage analysis, and file discovery.",
            ),
            "MLOps": (
                "Integration.AdminModules().enable_mlops()",
                "enable_mlops=True",
                "cpu",
                "ML model registry, inference serving, drift detection, rollouts, experiments, and observability.",
            ),
            "Storage": (
                "Integration.AdminModules().enable_storage()",
                "enable_storage=True",
                "hard-drive",
                "Storage backend management, file browser, quota analytics, health monitoring, and Chart.js dashboards.",
            ),
        }

        hint = _config_hints.get(module, (
            f"enable_{module.lower().replace(' ', '_')}=True",
            f"enable_{module.lower().replace(' ', '_')}=True",
            module.lower(),
            f"The {module} module.",
        ))

        builder_hint, flat_hint, icon_key, description = hint

        html = render_disabled_page(
            module_name=module,
            builder_hint=builder_hint,
            flat_hint=flat_hint,
            icon_key=icon_key,
            description=description,
            app_list=app_list,
            identity_name=identity_name,
        )
        return _html_response(html, 200)

    def _permission_denied_response(
        self, module: str, identity, permission: "AdminPermission"
    ) -> Response:
        """Return a styled 403 page when a user lacks the required permission."""
        app_list = self.site.get_app_list(identity) if identity else []
        identity_name = _get_identity_name(identity)
        current_role = str(get_admin_role(identity) or "none")
        html = render_forbidden_page(
            module_name=module,
            required_permission=permission.value if permission else "",
            current_role=current_role,
            app_list=app_list,
            identity_name=identity_name,
            identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html, 403)

    # ── CSRF Helpers ─────────────────────────────────────────────────

    def _ensure_csrf(self, ctx: RequestCtx) -> str:
        """
        Ensure the CSRF token is populated in both the session and the
        template contextvar.

        Admin routes are registered as monkeypatched handlers on the
        controller router, so the normal ``on_request`` lifecycle hook
        is **not** invoked by the engine fast-path.  This method must
        therefore be called explicitly at the start of every admin
        handler (or indirectly through the CSRF-reject helpers).

        Returns:
            The current CSRF token string (for use in templates).
        """
        from .templates import _csrf_token_var

        token = self.site.security.csrf.get_or_create_token(ctx)
        _csrf_token_var.set(token)
        return token

    def _csrf_reject_redirect(
        self,
        request,
        ctx: RequestCtx,
        form_data: Dict[str, Any],
        redirect_url: str,
    ) -> Optional[Response]:
        """
        Validate CSRF token from form_data; return redirect on failure, None on success.

        Usage in POST handlers that redirect::

            denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/model/")
            if denied:
                return denied
        """
        # Ensure session token exists (on_request may not have run)
        self._ensure_csrf(ctx)

        if not self.site.security.csrf.validate_request(ctx, form_data):
            client_ip = self.site.security.extract_client_ip(request)
            self.site.security.event_tracker.record(
                "csrf_violation", client_ip, endpoint=redirect_url,
            )
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "Invalid or expired security token. Please try again."
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect(redirect_url)
        return None

    def _csrf_reject_json(
        self,
        request,
        ctx: RequestCtx,
        form_data: Dict[str, Any],
    ) -> Optional[Response]:
        """
        Validate CSRF token from form_data; raise AdminCSRFViolationFault on failure.

        Usage in POST handlers that return JSON::

            denied = self._csrf_reject_json(request, ctx, form_data)
            if denied:
                return denied
        """
        # Ensure session token exists (on_request may not have run)
        self._ensure_csrf(ctx)

        if not self.site.security.csrf.validate_request(ctx, form_data):
            client_ip = self.site.security.extract_client_ip(request)
            self.site.security.event_tracker.record(
                "csrf_violation", client_ip, endpoint="json-api",
            )
            import json as _json
            return Response(
                content=_json.dumps({
                    "error": "csrf_failed",
                    "message": "Invalid or expired security token. Please reload the page and try again.",
                }).encode("utf-8"),
                status=403,
                headers={"content-type": "application/json"},
            )
        return None

    # ── Lifecycle ────────────────────────────────────────────────────

    async def on_request(self, ctx: RequestCtx) -> None:
        """Populate the CSRF contextvar so every template gets the token."""
        self._ensure_csrf(ctx)

    # ── Dashboard ────────────────────────────────────────────────────

    @GET("/")
    async def dashboard(self, request, ctx: RequestCtx) -> Response:
        """Admin dashboard -- model overview with stats."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        # print(identity)
        if denied:
            return denied

        self._ensure_initialized()

        app_list = self.site.get_app_list(identity)
        stats = await self.site.get_dashboard_stats()

        # Gather infrastructure summaries for dashboard widgets
        containers_summary = {}
        pods_summary = {}
        if self.site.admin_config.is_module_enabled("containers"):
            try:
                cd = self.site.get_containers_data()
                containers_summary = {
                    "available": cd.get("docker_available", False),
                    "total": len(cd.get("containers", [])),
                    "running": sum(1 for c in cd.get("containers", []) if c.get("state", "").lower() == "running"),
                    "stopped": sum(1 for c in cd.get("containers", []) if c.get("state", "").lower() != "running"),
                    "images": len(cd.get("images", [])),
                    "volumes": len(cd.get("volumes", [])),
                    "networks": len(cd.get("networks", [])),
                    "version": cd.get("docker_version", ""),
                    "error": cd.get("error", ""),
                }
            except Exception:
                containers_summary = {"available": False, "error": "Failed to fetch"}

        if self.site.admin_config.is_module_enabled("pods"):
            try:
                pd = self.site.get_pods_data()
                pods_summary = {
                    "available": pd.get("kubectl_available", False),
                    "total_pods": len(pd.get("pods", [])),
                    "running_pods": sum(1 for p in pd.get("pods", []) if p.get("status", "").lower() == "running"),
                    "deployments": len(pd.get("deployments", [])),
                    "services": len(pd.get("services", [])),
                    "namespaces": len(pd.get("namespaces", [])),
                    "error": pd.get("error", ""),
                }
            except Exception:
                pods_summary = {"available": False, "error": "Failed to fetch"}

        # Gather ORM metadata for dashboard widgets
        orm_metadata = self.site.get_orm_metadata()

        # Gather error and task stats for dashboard live stats row
        error_stats = {}
        tasks_stats = {}
        mlops_summary = {}
        try:
            error_stats = self.site.get_error_tracker_data()
        except Exception:
            pass
        try:
            tasks_data = await self.site.get_tasks_data()
            tasks_stats = tasks_data.get("stats", {})
        except Exception:
            pass

        # Gather MLOps summary for dashboard widget
        if self.site.admin_config.is_module_enabled("mlops"):
            try:
                md = self.site.get_mlops_data()
                mlops_summary = {
                    "available": md.get("available", False),
                    "total_models": md.get("total_models", 0),
                    "total_inferences": md.get("total_inferences", 0),
                    "total_errors": md.get("total_errors", 0),
                    "avg_latency": md.get("avg_latency_ms", 0),
                    "models": [],
                    "inference_history_count": len(getattr(self.site, "_mlops_inference_history", [])),
                    "alert_rules_count": len(getattr(self.site, "_mlops_alert_rules", [])),
                    "triggered_alerts_count": len(getattr(self.site, "_mlops_triggered_alerts", [])),
                }
                for m in md.get("models", [])[:6]:
                    mlops_summary["models"].append({
                        "name": m.get("name", ""),
                        "version": m.get("version", ""),
                        "state": m.get("state", "unknown"),
                        "framework": m.get("framework", ""),
                    })
            except Exception:
                mlops_summary = {"available": False}

        # Gather Storage summary for dashboard widget
        storage_summary = {"available": False}
        if self.site.admin_config.is_module_enabled("storage"):
            try:
                sd = await self.site.get_storage_data()
                if sd.get("available"):
                    storage_summary = {
                        "available": True,
                        "total_backends": len(sd.get("backends", [])),
                        "total_files": sd.get("total_files", 0),
                        "total_size": sd.get("total_size", 0),
                        "total_size_human": self.site._fmt_bytes(sd.get("total_size", 0)),
                        "healthy_count": sum(1 for v in sd.get("health", {}).values() if v),
                        "unhealthy_count": sum(1 for v in sd.get("health", {}).values() if not v),
                        "default_alias": sd.get("default_alias", "default"),
                        "backends": [
                            {
                                "alias": b.get("alias", ""),
                                "type": b.get("type", "unknown"),
                                "healthy": b.get("healthy", False),
                                "file_count": b.get("file_count", 0),
                                "size_human": b.get("size_human", "0 B"),
                            }
                            for b in sd.get("backends", [])[:6]
                        ],
                    }
            except Exception:
                storage_summary = {"available": False}

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Dashboard",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_dashboard(
            app_list=app_list,
            stats=stats,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
            containers_summary=containers_summary,
            pods_summary=pods_summary,
            orm_metadata=orm_metadata,
            error_stats=error_stats,
            tasks_stats=tasks_stats,
            mlops_summary=mlops_summary,
            storage_summary=storage_summary,
        )
        return _html_response(html)

    # ── Offline Detection Page ───────────────────────────────────────

    @GET("/offline")
    async def offline_page(self, request, ctx: RequestCtx) -> Response:
        """Render the offline detection page.

        This is a standalone page (no auth required) that checks whether
        the user has an active internet connection.  The admin panel
        relies on external CDN assets (Google Fonts, Lucide icons) so
        it redirects here when the browser detects ``navigator.onLine``
        is ``false``.  The page auto-redirects back once connectivity
        is restored.
        """
        from .templates import _render_offline_page
        html = _render_offline_page()
        return _secure_html_response(html, self.site)

    # ── Login / Logout ───────────────────────────────────────────────

    @GET("/login")
    async def login_page(self, request, ctx: RequestCtx) -> Response:
        """Render admin login page with CSRF token."""
        # Already logged in?
        identity = _get_identity(ctx)
        if identity and get_admin_role(identity) is not None:
            return _redirect("/admin/")

        # Generate CSRF token for the login form
        csrf_token = self.site.security.csrf.get_or_create_token(ctx)

        resp = _secure_html_response(
            render_login_page(csrf_token=csrf_token), self.site,
        )
        # Attach CSRF cookie for pre-session double-submit pattern
        self.site.security.csrf.apply_cookie(resp, secure=False)
        return resp

    @POST("/login")
    async def login_submit(self, request, ctx: RequestCtx) -> Response:
        """
        Process admin login.

        Security layers:
        1. Rate limiting — brute-force protection with progressive lockout
        2. CSRF validation — double-submit token pattern
        3. Credential verification — timing-safe password check
        4. Session fixation protection — regenerate session on login
        5. Audit logging — both success and failure
        """
        client_ip = self.site.security.extract_client_ip(request)

        # ── Rate limit check ─────────────────────────────────────
        is_locked, retry_after = self.site.security.rate_limiter.is_login_locked(client_ip)
        if is_locked:
            self.site.security.event_tracker.record(
                "rate_limited", client_ip, endpoint="login",
                retry_after=retry_after,
            )
            csrf_token = self.site.security.csrf.get_or_create_token(ctx)
            return _secure_html_response(
                render_login_page(
                    error=f"Too many login attempts. Please try again in {retry_after // 60} minutes.",
                    csrf_token=csrf_token,
                ),
                self.site,
                429,
            )

        form_data = await _parse_form(ctx)

        # ── CSRF validation ──────────────────────────────────────
        if not self.site.security.csrf.validate_request(ctx, form_data):
            self.site.security.event_tracker.record(
                "csrf_violation", client_ip, endpoint="login",
            )
            csrf_token = self.site.security.csrf.get_or_create_token(ctx)
            resp = _secure_html_response(
                render_login_page(
                    error="Security validation failed. Please try again.",
                    csrf_token=csrf_token,
                ),
                self.site,
                403,
            )
            self.site.security.csrf.apply_cookie(resp, secure=False)
            return resp

        username = form_data.get("username", "")
        password = form_data.get("password", "")

        if not username or not password:
            csrf_token = self.site.security.csrf.get_or_create_token(ctx)
            return _secure_html_response(
                render_login_page(
                    error="Username and password required",
                    csrf_token=csrf_token,
                ),
                self.site,
                400,
            )

        # Authenticate via built-in admin auth
        identity = await self._authenticate_admin(username, password)

        if identity is None:
            # ── Record failure + progressive lockout ──────────────
            now_locked, lockout_duration = self.site.security.rate_limiter.record_login_failure(client_ip)
            remaining = self.site.security.rate_limiter.get_remaining_login_attempts(client_ip)

            self.site.security.event_tracker.record(
                "login_failed", client_ip,
                username=username, remaining_attempts=remaining,
            )

            # Log failed attempt
            meta = _extract_request_meta(request)
            audit = self.site.audit_log
            if hasattr(audit, "alog"):
                await audit.alog(
                    user_id="unknown",
                    username=username,
                    role="none",
                    action=AdminAction.LOGIN_FAILED,
                    success=False,
                    error_message="Invalid credentials",
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            else:
                audit.log(
                    user_id="unknown",
                    username=username,
                    role="none",
                    action=AdminAction.LOGIN_FAILED,
                    success=False,
                    error_message="Invalid credentials",
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )

            error_msg = "Invalid credentials"
            if now_locked:
                error_msg = f"Account locked for {lockout_duration // 60} minutes due to too many failed attempts."
            elif remaining <= 2:
                error_msg = f"Invalid credentials. {remaining} attempt(s) remaining before lockout."

            csrf_token = self.site.security.csrf.get_or_create_token(ctx)
            return _secure_html_response(
                render_login_page(error=error_msg, csrf_token=csrf_token),
                self.site,
                401,
            )

        # ── Success: clear rate limiter ──────────────────────────
        self.site.security.rate_limiter.record_login_success(client_ip)

        # ── Session fixation protection: regenerate session ──────
        if ctx.session and hasattr(ctx.session, "regenerate"):
            try:
                await ctx.session.regenerate()
            except Exception:
                pass  # Best effort — session may not support regeneration

        # Store identity in session
        if ctx.session and hasattr(ctx.session, "data"):
            ctx.session.data["_admin_identity"] = identity.to_dict()

        # Log successful login
        meta = _extract_request_meta(request)
        audit = self.site.audit_log
        if hasattr(audit, "alog"):
            await audit.alog(
                user_id=identity.id,
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.LOGIN,
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        else:
            audit.log(
                user_id=identity.id,
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.LOGIN,
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )

        return _redirect("/admin/")

    @POST("/logout")
    async def logout(self, request, ctx: RequestCtx) -> Response:
        """Logout and clear admin session (POST to prevent CSRF via GET)."""
        identity = _get_identity(ctx)

        if identity:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=identity.id,
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.LOGOUT,
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )

        # Clear admin session data
        if ctx.session and hasattr(ctx.session, "data"):
            ctx.session.data.pop("_admin_identity", None)
            ctx.session.data.pop("_admin_csrf_token", None)

        return _redirect("/admin/login")

    @GET("/logout")
    async def logout_get(self, request, ctx: RequestCtx) -> Response:
        """GET /logout kept for backward compat — performs same action."""
        identity = _get_identity(ctx)

        if identity:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=identity.id,
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.LOGOUT,
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )

        # Clear all admin session data including CSRF token
        if ctx.session and hasattr(ctx.session, "data"):
            ctx.session.data.pop("_admin_identity", None)
            ctx.session.data.pop("_admin_csrf_token", None)

        return _redirect("/admin/login")

    # Reserved names -- system pages that must not be treated as model names
    _SYSTEM_PAGES = frozenset({
        "login", "logout", "orm", "build", "migrations",
        "config", "workspace", "permissions", "audit", "monitoring",
        "admin-users", "profile", "containers", "pods", "storage",
    })

    # ── List View ────────────────────────────────────────────────────

    @GET("/{model}/")
    async def list_view(self, request, ctx: RequestCtx) -> Response:
        """List records for a model with search and pagination."""
        self._ensure_csrf(ctx)
        model = request.state.get("path_params", {}).get("model", "")

        # Delegate to the correct system page handler
        if model in self._SYSTEM_PAGES:
            handler = getattr(self, f"{model}_view", None)
            if handler:
                return await handler(request, ctx)

        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        # Check for flash message
        flash = ""
        flash_type = "success"
        if ctx.session and hasattr(ctx.session, "data"):
            flash = ctx.session.data.pop("_admin_flash", "")
            flash_type = ctx.session.data.pop("_admin_flash_type", "success")

        # Parse query params
        search = ctx.query_param("q", "")
        page_str = ctx.query_param("page", "1")
        try:
            page = max(1, int(page_str))
        except ValueError:
            page = 1

        # Parse per_page (allow user to change rows per page)
        per_page_str = ctx.query_param("per_page", "")
        per_page = 25  # default
        if per_page_str:
            try:
                per_page = max(5, min(200, int(per_page_str)))
            except ValueError:
                per_page = 25

        # Parse ordering from query param
        ordering = ctx.query_param("ordering", "")

        # Parse filter params (filter__<field>=<value>)
        filters = {}
        active_filters = {}
        try:
            admin_obj = self.site.get_model_admin(model)
            filter_fields = admin_obj.get_list_filter()
            for f_field in filter_fields:
                f_val = ctx.query_param(f"filter__{f_field}", "")
                if f_val:
                    # Detect date range filters
                    f_val_from = ctx.query_param(f"filter__{f_field}__gte", "")
                    f_val_to = ctx.query_param(f"filter__{f_field}__lte", "")
                    if f_val_from or f_val_to:
                        continue  # handled below
                    # Exact match filter
                    active_filters[f_field] = f_val
                    if f_val.lower() in ("true", "1", "yes"):
                        filters[f_field] = True
                    elif f_val.lower() in ("false", "0", "no"):
                        filters[f_field] = False
                    else:
                        filters[f_field] = f_val
                # Date range filters
                f_val_from = ctx.query_param(f"filter__{f_field}__gte", "")
                f_val_to = ctx.query_param(f"filter__{f_field}__lte", "")
                if f_val_from:
                    filters[f"{f_field}__gte"] = f_val_from
                    active_filters[f"{f_field}__gte"] = f_val_from
                if f_val_to:
                    filters[f"{f_field}__lte"] = f_val_to
                    active_filters[f"{f_field}__lte"] = f_val_to
        except Exception:
            pass

        try:
            data = await self.site.list_records(
                model,
                page=page,
                per_page=per_page,
                search=search,
                filters=filters if filters else None,
                ordering=ordering if ordering else None,
                identity=identity,
            )
        except Exception as e:
            app_list = self.site.get_app_list(identity)
            return _html_response(
                render_error_page(
                    status=404,
                    title="Not Found",
                    message=str(e),
                    app_list=app_list,
                    identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                ),
                404,
            )

        # Audit: log list/search access
        if identity and self.site.audit_log:
            meta = _extract_request_meta(request)
            if search:
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.SEARCH,
                    model_name=model,
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                    metadata={"query": search, "page": page},
                )
            else:
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.LIST,
                    model_name=model,
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                    metadata={"page": page},
                )

        # Get actions and enrich data with field metadata
        try:
            admin_obj = self.site.get_model_admin(model)
            data["actions"] = admin_obj.get_actions()
            data["list_editable"] = list(admin_obj.list_editable) if admin_obj.list_editable else []
            data["date_hierarchy"] = admin_obj.date_hierarchy or ""

            # Build field type metadata for each list_display column
            field_types = {}
            filter_metadata = {}
            for col in data.get("list_display", []):
                meta = admin_obj.get_field_metadata(col)
                field_types[col] = meta.get("type", "text")
            # Build filter metadata (type + choices for each filter field)
            for f_field in data.get("list_filter", []):
                meta = admin_obj.get_field_metadata(f_field)
                filter_metadata[f_field] = {
                    "type": meta.get("type", "text"),
                    "label": meta.get("label", f_field.replace("_", " ").title()),
                    "choices": meta.get("choices") or [],
                }
            data["field_types"] = field_types
            data["filter_metadata"] = filter_metadata
            data["active_filters"] = active_filters
        except Exception:
            data["actions"] = {}

        app_list = self.site.get_app_list(identity)

        html = render_list_view(
            data=data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
            flash=flash,
            flash_type=flash_type,
        )
        return _html_response(html)

    # ── Add (Create) ─────────────────────────────────────────────────

    @GET("/{model}/add")
    async def add_form(self, request, ctx: RequestCtx) -> Response:
        """Render the add/create form for a model."""
        self._ensure_csrf(ctx)
        model = request.state.get("path_params", {}).get("model", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        try:
            model_cls = self.site.get_model_class(model)
            admin = self.site.get_model_admin(model_cls)
        except Exception as e:
            app_list = self.site.get_app_list(identity)
            return _html_response(
                render_error_page(
                    status=404,
                    title="Not Found",
                    message=str(e),
                    app_list=app_list,
                    identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                ),
                404,
            )

        # Build empty field data for form
        fields_data = []
        readonly = admin.get_readonly_fields()
        for field_name in admin.get_fields():
            meta = admin.get_field_metadata(field_name)
            meta["value"] = ""
            meta["readonly"] = field_name in readonly
            fields_data.append(meta)

        form_data = {
            "pk": "",
            "fields": fields_data,
            "fieldsets": admin.get_fieldsets(),
            "model_name": model_cls.__name__,
            "verbose_name": admin.get_model_name(),
            "can_delete": False,
        }

        app_list = self.site.get_app_list(identity)
        html = render_form_view(
            data=form_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
            is_create=True,
        )
        return _html_response(html)

    @POST("/{model}/add")
    async def add_submit(self, request, ctx: RequestCtx) -> Response:
        """Process create form submission."""
        model = request.state.get("path_params", {}).get("model", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, f"/admin/{model.lower()}/add/")
        if csrf_denied:
            return csrf_denied

        try:
            record = await self.site.create_record(model, form_data, identity=identity)

            # ── Audit: log create ────────────────────────────────
            if identity and self.site.audit_log:
                meta = _extract_request_meta(request)
                # Try to get the PK of the newly created record
                new_pk = ""
                if record is not None:
                    if isinstance(record, dict):
                        new_pk = str(record.get("pk", record.get("id", "")))
                    elif hasattr(record, "pk"):
                        new_pk = str(record.pk)
                    elif hasattr(record, "id"):
                        new_pk = str(record.id)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.CREATE,
                    model_name=model,
                    record_pk=new_pk,
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )

            return _redirect(f"/admin/{model.lower()}/")
        except Exception as e:
            # Re-render form with error
            try:
                model_cls = self.site.get_model_class(model)
                admin = self.site.get_model_admin(model_cls)
            except Exception:
                app_list = self.site.get_app_list(identity)
                return _html_response(
                    render_error_page(
                        status=400,
                        title="Error",
                        message=str(e),
                        app_list=app_list,
                        identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                    ),
                    400,
                )

            fields_data = []
            for field_name in admin.get_fields():
                meta = admin.get_field_metadata(field_name)
                meta["value"] = form_data.get(field_name, "")
                fields_data.append(meta)

            data = {
                "pk": "",
                "fields": fields_data,
                "fieldsets": admin.get_fieldsets(),
                "model_name": model_cls.__name__,
                "verbose_name": admin.get_model_name(),
                "can_delete": False,
            }

            app_list = self.site.get_app_list(identity)
            html = render_form_view(
                data=data,
                app_list=app_list,
                identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                is_create=True,
                flash=str(e),
                flash_type="error",
            )
            return _html_response(html, 400)

    # ── Edit (Update) ────────────────────────────────────────────────

    @GET("/{model}/{pk}")
    async def edit_form(self, request, ctx: RequestCtx) -> Response:
        """Render the edit form for a record."""
        self._ensure_csrf(ctx)
        _pp = request.state.get("path_params", {})
        model = _pp.get("model", "")
        pk = _pp.get("pk", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        try:
            data = await self.site.get_record(model, pk, identity=identity)
        except Exception as e:
            app_list = self.site.get_app_list(identity)
            return _html_response(
                render_error_page(
                    status=404,
                    title="Not Found",
                    message=str(e),
                    app_list=app_list,
                    identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                ),
                404,
            )

        # Audit: log record view
        if identity and self.site.audit_log:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.VIEW,
                model_name=model,
                record_pk=str(pk),
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )

        app_list = self.site.get_app_list(identity)
        html = render_form_view(
            data=data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @POST("/{model}/{pk}")
    async def edit_submit(self, request, ctx: RequestCtx) -> Response:
        """Process edit form submission."""
        _pp = request.state.get("path_params", {})
        model = _pp.get("model", "")
        pk = _pp.get("pk", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, f"/admin/{model.lower()}/{pk}/")
        if csrf_denied:
            return csrf_denied

        try:
            # Capture old data for change tracking
            old_data = {}
            try:
                old_record = await self.site.get_record(model, pk, identity=identity)
                if old_record and isinstance(old_record, dict):
                    for f in old_record.get("fields", []):
                        fname = f.get("name", "")
                        if fname:
                            old_data[fname] = f.get("value", "")
            except Exception:
                pass

            await self.site.update_record(model, pk, form_data, identity=identity)

            # ── Audit: log update ────────────────────────────────
            if identity and self.site.audit_log:
                meta = _extract_request_meta(request)
                # Build changes dict: old vs new
                changes = {}
                for fk, fv in form_data.items():
                    if fk.startswith("_"):
                        continue
                    old_val = old_data.get(fk)
                    if old_val is not None and str(old_val) != str(fv):
                        changes[fk] = {"old": str(old_val), "new": str(fv)}
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.UPDATE,
                    model_name=model,
                    record_pk=str(pk),
                    changes=changes if changes else None,
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )

            # ── Capture query inspection data from the update ────────
            qi_queries = getattr(self.site, "_last_update_queries", [])
            self.site._last_update_queries = []  # Reset

            qi_enabled = self.site.admin_config.is_module_enabled("query_inspector")

            # Re-render the form with success flash + query inspector panel
            try:
                data = await self.site.get_record(model, pk, identity=identity)
            except Exception:
                return _redirect(f"/admin/{model.lower()}/")

            app_list = self.site.get_app_list(identity)
            html = render_form_view(
                data=data,
                app_list=app_list,
                identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                flash="Record updated successfully.",
                flash_type="success",
                query_inspection=qi_queries if qi_enabled else None,
            )
            return _html_response(html)
        except Exception as e:
            # Re-render form with error
            try:
                data = await self.site.get_record(model, pk, identity=identity)
            except Exception:
                app_list = self.site.get_app_list(identity)
                return _html_response(
                    render_error_page(
                        status=400,
                        title="Error",
                        message=str(e),
                        app_list=app_list,
                        identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                    ),
                    400,
                )

            app_list = self.site.get_app_list(identity)
            html = render_form_view(
                data=data,
                app_list=app_list,
                identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                flash=str(e),
                flash_type="error",
            )
            return _html_response(html, 400)

    # ── Delete ───────────────────────────────────────────────────────

    @POST("/{model}/{pk}/delete")
    async def delete_record(self, request, ctx: RequestCtx) -> Response:
        """Delete a record."""
        _pp = request.state.get("path_params", {})
        model = _pp.get("model", "")
        pk = _pp.get("pk", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        # CSRF validation (delete uses body or header token)
        form_data = await _parse_form(ctx)
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, f"/admin/{model.lower()}/")
        if csrf_denied:
            return csrf_denied

        try:
            await self.site.delete_record(model, pk, identity=identity)
            # Audit: log delete
            if identity and self.site.audit_log:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.DELETE,
                    model_name=model,
                    record_pk=str(pk),
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
        except Exception as e:
            logger.warning("Admin delete failed: %s", e)
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = str(e)
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect(f"/admin/{model.lower()}/")

    # ── Bulk Actions ─────────────────────────────────────────────────

    @POST("/{model}/action")
    async def bulk_action(self, request, ctx: RequestCtx) -> Response:
        """Execute a bulk action on selected records."""
        model = request.state.get("path_params", {}).get("model", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        form_data = await _parse_form(ctx, multi=True)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, f"/admin/{model.lower()}/")
        if csrf_denied:
            return csrf_denied

        action_name = form_data.get("action", "") if isinstance(form_data.get("action"), str) else (form_data.get("action", [""])[0] if isinstance(form_data.get("action"), list) else "")
        selected_raw = form_data.get("selected", [])
        if isinstance(selected_raw, str):
            selected_raw = [selected_raw]
        selected_pks = [pk for pk in selected_raw if pk]

        if not action_name or not selected_pks:
            return _redirect(f"/admin/{model.lower()}/")

        try:
            result = await self.site.execute_action(
                model, action_name, selected_pks, identity=identity,
            )
            # Audit: log bulk action
            if identity and self.site.audit_log:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.BULK_ACTION,
                    model_name=model,
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                    metadata={"action": action_name, "pks": selected_pks, "count": len(selected_pks)},
                )
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = result
                ctx.session.data["_admin_flash_type"] = "success"
        except Exception as e:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = str(e)
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect(f"/admin/{model.lower()}/")

    # ── Export ────────────────────────────────────────────────────────

    @GET("/{model}/export")
    async def export_view(self, request, ctx: RequestCtx) -> Response:
        """Export model data as CSV, JSON, or XML using the export system."""
        self._ensure_csrf(ctx)
        model = request.state.get("path_params", {}).get("model", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        fmt = ctx.query_param("format", "csv")

        try:
            data = await self.site.list_records(
                model, page=1, per_page=10000, identity=identity,
            )
        except Exception as e:
            app_list = self.site.get_app_list(identity)
            return _html_response(
                render_error_page(
                    status=404,
                    title="Not Found",
                    message=str(e),
                    app_list=app_list,
                    identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
                ),
                404,
            )

        rows = data.get("rows", [])
        columns = data.get("list_display", [])
        model_name = data.get("model_name", model)

        # Audit log
        if identity:
            self.site.audit_log.log(
                user_id=identity.id,
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.EXPORT,
                model_name=model_name,
                metadata={"format": fmt, "count": len(rows)},
            )

        # Use the export system
        from aquilia.admin.export import ExportRegistry
        raw_headers = {c: c for c in columns}  # Keep field names as-is
        exporter = ExportRegistry.create(fmt, fields=columns, headers=raw_headers)
        if exporter:
            content = exporter.export(rows)
            filename = exporter.get_filename(model_name)
            return Response(
                content=content.encode("utf-8"),
                status=200,
                headers={
                    "content-type": exporter.content_type,
                    "content-disposition": f'attachment; filename="{filename}"',
                },
            )

        # Fallback for unrecognized formats
        if fmt == "json":
            import json
            export_rows = []
            for row in rows:
                export_rows.append({col: row.get(col, "") for col in columns})
            content = json.dumps(export_rows, indent=2, default=str)
            return Response(
                content=content.encode("utf-8"),
                status=200,
                headers={
                    "content-type": "application/json; charset=utf-8",
                    "content-disposition": f'attachment; filename="{model_name}.json"',
                },
            )
        else:
            # CSV export
            import csv
            import io
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(columns)
            for row in rows:
                writer.writerow([row.get(col, "") for col in columns])
            content = buf.getvalue()
            return Response(
                content=content.encode("utf-8"),
                status=200,
                headers={
                    "content-type": "text/csv; charset=utf-8",
                    "content-disposition": f'attachment; filename="{model_name}.csv"',
                },
            )

    # ── History View ─────────────────────────────────────────────────

    @GET("/{model}/{pk}/history")
    async def history_view(self, request, ctx: RequestCtx) -> Response:
        """View change history for a specific record."""
        self._ensure_csrf(ctx)
        _pp = request.state.get("path_params", {})
        model = _pp.get("model", "")
        pk = _pp.get("pk", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        # Get audit entries for this specific record
        import json as _json
        history_entries = []
        if self.site.audit_log:
            # Use dedicated method that searches both memory and CROUS file
            if hasattr(self.site.audit_log, "get_history_for_record"):
                raw_entries = self.site.audit_log.get_history_for_record(model, str(pk))
            else:
                raw_entries = [
                    e for e in self.site.audit_log.get_entries(limit=10_000)
                    if (getattr(e, "model_name", None) or "").lower() == model.lower()
                    and str(getattr(e, "record_pk", "") or "") == str(pk)
                ]

            for entry in raw_entries:
                if hasattr(entry, "to_dict"):
                    entry_data = entry.to_dict()
                elif isinstance(entry, dict):
                    entry_data = entry
                else:
                    entry_data = entry.__dict__ if hasattr(entry, "__dict__") else {}

                entry_meta = entry_data.get("metadata") or {}
                if isinstance(entry_meta, str):
                    try:
                        entry_meta = _json.loads(entry_meta)
                    except Exception:
                        entry_meta = {}

                entry_changes = entry_data.get("changes") or {}
                if isinstance(entry_changes, str):
                    try:
                        entry_changes = _json.loads(entry_changes)
                    except Exception:
                        entry_changes = {}

                action_val = entry_data.get("action", "")
                if hasattr(action_val, "value"):
                    action_val = action_val.value

                ts = entry_data.get("timestamp", "")
                if hasattr(ts, "isoformat"):
                    ts = ts.isoformat()

                history_entries.append({
                    "id": entry_data.get("id", ""),
                    "timestamp": ts,
                    "user_id": entry_data.get("user_id", ""),
                    "username": entry_data.get("username") or "Unknown",
                    "role": entry_data.get("role", ""),
                    "action": str(action_val),
                    "metadata": entry_meta,
                    "changes": entry_changes or {},
                    "ip_address": entry_data.get("ip_address") or "",
                    "user_agent": entry_data.get("user_agent") or "",
                    "success": entry_data.get("success", True),
                    "error_message": entry_data.get("error_message") or "",
                    "fields_changed": len(entry_changes) if entry_changes else 0,
                })

        # Compute summary stats for the history overview
        _action_counts: Dict[str, int] = {}
        _users_seen: set = set()
        for _he in history_entries:
            act = _he.get("action", "")
            _action_counts[act] = _action_counts.get(act, 0) + 1
            _users_seen.add(_he.get("username", "Unknown"))
        total_changes = sum(
            _he.get("fields_changed", 0) for _he in history_entries
        )
        history_stats = {
            "total_entries": len(history_entries),
            "action_counts": _action_counts,
            "unique_users": len(_users_seen),
            "total_field_changes": total_changes,
            "first_entry": history_entries[-1]["timestamp"] if history_entries else "",
            "last_entry": history_entries[0]["timestamp"] if history_entries else "",
        }

        # Get model verbose name
        verbose_name = model
        try:
            model_cls = self.site.get_model_class(model)
            admin = self.site.get_model_admin(model_cls)
            verbose_name = admin.get_model_name()
        except Exception:
            pass

        app_list = self.site.get_app_list(identity)

        # Render using the history template
        try:
            from .templates import _render_template, _HAS_JINJA2
            if _HAS_JINJA2:
                html = _render_template(
                    "history.html",
                    model_name=model,
                    verbose_name=verbose_name,
                    pk=pk,
                    entries=history_entries,
                    total=len(history_entries),
                    stats=history_stats,
                    app_list=app_list,
                    active_page="",
                    active_model=model.lower(),
                    identity_name=_get_identity_name(identity),
                    identity_avatar=_get_identity_avatar(identity),
                    site_title="Aquilia Admin",
                    url_prefix="/admin",
                    page_title=f"History: {verbose_name} #{pk}",
                )
                return _html_response(html)
        except Exception:
            pass

        # Fallback: JSON response
        return Response(
            content=_json.dumps({"model": model, "pk": pk, "entries": history_entries}, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json"},
        )

    # ── Batch Update API ─────────────────────────────────────────────

    @POST("/{model}/batch-update")
    async def batch_update(self, request, ctx: RequestCtx) -> Response:
        """Update a specific field on multiple records at once."""
        import json as _json

        model = request.state.get("path_params", {}).get("model", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()

        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        field_name = form_data.get("field", "")
        new_value = form_data.get("value", "")
        selected_raw = form_data.get("selected", "")
        if isinstance(selected_raw, str):
            try:
                selected_pks = _json.loads(selected_raw)
            except Exception:
                selected_pks = [pk.strip() for pk in selected_raw.split(",") if pk.strip()]
        else:
            selected_pks = list(selected_raw)

        if not field_name or not selected_pks:
            return Response(
                content=_json.dumps({"error": "Missing field or selected records"}).encode("utf-8"),
                status=400,
                headers={"content-type": "application/json"},
            )

        try:
            count = 0
            for pk in selected_pks:
                try:
                    await self.site.update_record(model, pk, {field_name: new_value}, identity=identity)
                    count += 1
                except Exception:
                    pass

            # Audit
            if identity and self.site.audit_log:
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.BULK_ACTION,
                    model_name=model,
                    metadata={
                        "action": "batch_update",
                        "field": field_name,
                        "value": new_value,
                        "pks": selected_pks,
                        "count": count,
                    },
                )

            return Response(
                content=_json.dumps({"success": True, "updated": count}).encode("utf-8"),
                status=200,
                headers={"content-type": "application/json"},
            )
        except Exception as e:
            return Response(
                content=_json.dumps({"error": str(e)}).encode("utf-8"),
                status=500,
                headers={"content-type": "application/json"},
            )

    # ── Filter Metadata API ──────────────────────────────────────────

    @GET("/{model}/filter-meta")
    async def filter_metadata_api(self, request, ctx: RequestCtx) -> Response:
        """Return filter metadata as JSON for dynamic filter UI."""
        import json as _json

        model = request.state.get("path_params", {}).get("model", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()

        try:
            from aquilia.admin.filters import resolve_filter
            admin_obj = self.site.get_model_admin(model)
            model_cls = self.site.get_model_class(model)
            filter_specs = admin_obj.get_list_filter()
            filters = []
            for spec in filter_specs:
                f = resolve_filter(spec, model_cls)
                filters.append(f.to_metadata())
            return Response(
                content=_json.dumps({"filters": filters}).encode("utf-8"),
                status=200,
                headers={"content-type": "application/json"},
            )
        except Exception as e:
            return Response(
                content=_json.dumps({"error": str(e)}).encode("utf-8"),
                status=500,
                headers={"content-type": "application/json"},
            )

    # ── JSON Search API (no page refresh) ──────────────────────────

    @GET("/{model}/search")
    async def search_api(self, request, ctx: RequestCtx) -> Response:
        """Return JSON search results for live AJAX search."""
        import json as _json

        model = request.state.get("path_params", {}).get("model", "")
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()

        search = ctx.query_param("q", "")
        page_str = ctx.query_param("page", "1")
        try:
            page = max(1, int(page_str))
        except ValueError:
            page = 1

        per_page_str = ctx.query_param("per_page", "")
        per_page = 25
        if per_page_str:
            try:
                per_page = max(5, min(200, int(per_page_str)))
            except ValueError:
                per_page = 25

        ordering = ctx.query_param("ordering", "")

        # Parse filter params
        filters = {}
        try:
            admin_obj = self.site.get_model_admin(model)
            for f_field in admin_obj.get_list_filter():
                f_val = ctx.query_param(f"filter__{f_field}", "")
                if f_val:
                    if f_val.lower() in ("true", "1", "yes"):
                        filters[f_field] = True
                    elif f_val.lower() in ("false", "0", "no"):
                        filters[f_field] = False
                    else:
                        filters[f_field] = f_val
                f_from = ctx.query_param(f"filter__{f_field}__gte", "")
                f_to = ctx.query_param(f"filter__{f_field}__lte", "")
                if f_from:
                    filters[f"{f_field}__gte"] = f_from
                if f_to:
                    filters[f"{f_field}__lte"] = f_to
        except Exception:
            pass

        try:
            data = await self.site.list_records(
                model,
                page=page,
                per_page=per_page,
                search=search,
                filters=filters if filters else None,
                ordering=ordering if ordering else None,
                identity=identity,
            )
        except Exception as e:
            return Response(
                content=_json.dumps({"error": str(e)}).encode("utf-8"),
                status=404,
                headers={"content-type": "application/json"},
            )

        result = {
            "rows": data.get("rows", []),
            "total": data.get("total", 0),
            "page": data.get("page", 1),
            "total_pages": data.get("total_pages", 1),
            "has_next": data.get("has_next", False),
            "has_prev": data.get("has_prev", False),
            "list_display": data.get("list_display", []),
        }
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── ORM Models Page ──────────────────────────────────────────────

    @GET("/orm/")
    async def orm_view(self, request, ctx: RequestCtx) -> Response:
        """ORM models overview -- all registered models with counts."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("orm"):
            return self._module_disabled_response("ORM Models", identity)

        if not has_admin_permission(identity, AdminPermission.ORM_VIEW):
            return self._permission_denied_response("ORM Models", identity, AdminPermission.ORM_VIEW)

        self._ensure_initialized()

        app_list = self.site.get_app_list(identity)
        stats = await self.site.get_dashboard_stats()
        model_schema = self.site.get_model_schema()
        orm_metadata = self.site.get_orm_metadata()

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="ORM",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_orm_page(
            app_list=app_list,
            model_counts=stats.get("model_counts", {}),
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
            model_schema=model_schema,
            orm_metadata=orm_metadata,
        )
        return _html_response(html)

    # ── Build Page ───────────────────────────────────────────────────

    @GET("/build/")
    async def build_view(self, request, ctx: RequestCtx) -> Response:
        """Build page -- Crous artifacts and pipeline status."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("build"):
            return self._module_disabled_response("Build", identity)

        if not has_admin_permission(identity, AdminPermission.BUILD_VIEW):
            return self._permission_denied_response("Build", identity, AdminPermission.BUILD_VIEW)

        self._ensure_initialized()

        build_data = self.site.get_build_info()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Build",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_build_page(
            build_info=build_data.get("info", {}),
            artifacts=build_data.get("artifacts", []),
            pipeline_phases=build_data.get("pipeline_phases", []),
            build_log=build_data.get("build_log", ""),
            build_files=build_data.get("build_files", []),
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    # ── Migrations Page ──────────────────────────────────────────────

    @GET("/migrations/")
    async def migrations_view(self, request, ctx: RequestCtx) -> Response:
        """Migrations page -- list all migrations with syntax-highlighted source."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("migrations"):
            return self._module_disabled_response("Migrations", identity)

        if not has_admin_permission(identity, AdminPermission.MIGRATIONS_VIEW):
            return self._permission_denied_response("Migrations", identity, AdminPermission.MIGRATIONS_VIEW)

        self._ensure_initialized()

        migrations = self.site.get_migrations_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Migrations",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_migrations_page(
            migrations=migrations,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    # ── Config Page ──────────────────────────────────────────────────

    @GET("/config/")
    async def config_view(self, request, ctx: RequestCtx) -> Response:
        """Configuration page -- show workspace YAML configuration."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("config"):
            return self._module_disabled_response("Configuration", identity)

        if not has_admin_permission(identity, AdminPermission.CONFIG_VIEW):
            return self._permission_denied_response("Configuration", identity, AdminPermission.CONFIG_VIEW)

        self._ensure_initialized()

        config_data = self.site.get_config_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Configuration",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_config_page(
            config_files=config_data.get("files", []),
            workspace_info=config_data.get("workspace", None),
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    # ── Workspace Page ───────────────────────────────────────────────

    @GET("/workspace/")
    async def workspace_view(self, request, ctx: RequestCtx) -> Response:
        """Workspace page -- monitor modules, manifests & project metadata."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("workspace"):
            return self._module_disabled_response("Workspace", identity)

        if not has_admin_permission(identity, AdminPermission.WORKSPACE_VIEW):
            return self._permission_denied_response("Workspace", identity, AdminPermission.WORKSPACE_VIEW)

        self._ensure_initialized()

        workspace_data = self.site.get_workspace_data()
        app_list = self.site.get_app_list(identity)

        # Flatten: merge workspace sub-dict into top level for template
        ws_info = workspace_data.pop("workspace", {})
        workspace_data.update(ws_info)

        # Ensure stats has all keys the template expects
        stats = workspace_data.get("stats", {})
        stats.setdefault("total_modules", 0)
        stats.setdefault("total_models", 0)
        stats.setdefault("total_controllers", 0)
        stats.setdefault("total_services", 0)
        stats.setdefault("total_integrations", 0)
        workspace_data["stats"] = stats

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Workspace",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_workspace_page(
            workspace=workspace_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    # ── Permissions Page ─────────────────────────────────────────────

    @GET("/permissions/")
    async def permissions_view(self, request, ctx: RequestCtx) -> Response:
        """Permissions page -- role matrix and per-model access."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("permissions"):
            return self._module_disabled_response("Permissions", identity)

        if not has_admin_permission(identity, AdminPermission.PERMISSIONS_VIEW):
            return self._permission_denied_response("Permissions", identity, AdminPermission.PERMISSIONS_VIEW)

        self._ensure_initialized()

        # Check for flash message from permissions update
        flash = ""
        flash_type = "success"
        if ctx.session and hasattr(ctx.session, "data"):
            flash = ctx.session.data.pop("_admin_flash", "")
            flash_type = ctx.session.data.pop("_admin_flash_type", "success")

        perms_data = self.site.get_permissions_data(identity)
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Permissions",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_permissions_page(
            roles=perms_data.get("roles", []),
            all_permissions=perms_data.get("all_permissions", []),
            model_permissions=perms_data.get("model_permissions", []),
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
            flash=flash,
            flash_type=flash_type,
        )
        return _html_response(html)

    @POST("/permissions/update")
    async def permissions_update(self, request, ctx: RequestCtx) -> Response:
        """Handle permission updates from the permissions page form."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        # Only superadmins can modify permissions
        role = get_admin_role(identity)
        from .permissions import AdminRole as _AR
        if role is None or role != _AR.SUPERADMIN:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "Only superadmins can modify permissions."
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/permissions/")

        self._ensure_initialized()

        # Parse form data
        try:
            body = await request.body()
            form_data = {}
            for pair in body.decode("utf-8").split("&"):
                if "=" in pair:
                    from urllib.parse import unquote_plus
                    key, val = pair.split("=", 1)
                    form_data[unquote_plus(key)] = unquote_plus(val)
        except Exception:
            form_data = {}

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/permissions/")
        if csrf_denied:
            return csrf_denied

        result = self.site.update_permissions(form_data, identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PERMISSION_CHANGE,
                model_name="Permissions",
                metadata={"result": result.get("status", "unknown")},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        # Flash the result message
        if ctx.session and hasattr(ctx.session, "data"):
            ctx.session.data["_admin_flash"] = result.get("message", "Permissions updated.")
            ctx.session.data["_admin_flash_type"] = result.get("status", "success")

        return _redirect("/admin/permissions/")

    # ── Audit Log ────────────────────────────────────────────────────

    @GET("/audit/")
    async def audit_view(self, request, ctx: RequestCtx) -> Response:
        """View the admin audit log -- reads from DB if available."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("audit"):
            return self._module_disabled_response("Audit Log", identity)

        if not has_admin_permission(identity, AdminPermission.AUDIT_VIEW):
            return _redirect("/admin/")

        self._ensure_initialized()

        # Pagination params
        try:
            qs = request.query_params
            page = max(1, int(qs.get("page", 1)))
        except (ValueError, TypeError, AttributeError):
            page = 1
        per_page = 50
        offset = (page - 1) * per_page

        # Use async DB-backed query so persisted entries survive restarts
        audit = self.site.audit_log
        if hasattr(audit, "get_entries_async"):
            entries = await audit.get_entries_async(limit=per_page, offset=offset)
            total = await audit.count_async()
        else:
            entries = audit.get_entries(limit=per_page, offset=offset)
            total = audit.count()

        total_pages = max(1, (total + per_page - 1) // per_page)

        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Audit",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_audit_page(
            entries=[e.to_dict() for e in entries],
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )
        return _html_response(html)

    # ── Monitoring Page ──────────────────────────────────────────────

    @GET("/monitoring/")
    async def monitoring_view(self, request, ctx: RequestCtx) -> Response:
        """Application monitoring -- CPU, memory, disk, network & process metrics."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("monitoring"):
            return self._module_disabled_response("Monitoring", identity)

        if not has_admin_permission(identity, AdminPermission.MONITORING_VIEW):
            return self._permission_denied_response("Monitoring", identity, AdminPermission.MONITORING_VIEW)

        self._ensure_initialized()

        monitoring_data = self.site.get_monitoring_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Monitoring",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_monitoring_page(
            monitoring=monitoring_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/monitoring/api/")
    async def monitoring_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling monitoring metrics."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("monitoring"):
            return Response(
                content=b'{"error":"monitoring disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        monitoring_data = self.site.get_monitoring_data()
        return Response(
            content=_json.dumps(monitoring_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Containers Page ──────────────────────────────────────────────

    @GET("/containers/")
    async def containers_view(self, request, ctx: RequestCtx) -> Response:
        """Docker containers -- images, volumes, networks & compose services."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("containers"):
            return self._module_disabled_response("Containers", identity)

        if not has_admin_permission(identity, AdminPermission.CONTAINER_VIEW):
            return self._permission_denied_response("Containers", identity, AdminPermission.CONTAINER_VIEW)

        self._ensure_initialized()

        containers_data = self.site.get_containers_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Containers",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_containers_page(
            containers_data=containers_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/containers/api/")
    async def containers_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling container metrics."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("containers"):
            return Response(
                content=b'{"error":"containers disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        containers_data = self.site.get_containers_data()
        return Response(
            content=_json.dumps(containers_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/action/")
    async def containers_action(self, request, ctx: RequestCtx) -> Response:
        """Execute a container lifecycle action (start/stop/restart/pause/unpause/kill/rm)."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("containers"):
            return Response(content=b'{"error":"containers disabled"}', status=404,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()

        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")
        action = form_data.get("action", "")
        run_params = form_data.get("run_params", "")

        if not container_id or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_container_action(container_id, action, run_params=run_params)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.CONTAINER_ACTION,
                model_name="Docker",
                metadata={"container_id": container_id, "action": action},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/inspect/")
    async def containers_inspect(self, request, ctx: RequestCtx) -> Response:
        """Return full docker inspect for a container."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("containers"):
            return Response(content=b'{"error":"containers disabled"}', status=404,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")

        if not container_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.get_container_inspect(container_id)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/logs/")
    async def containers_logs(self, request, ctx: RequestCtx) -> Response:
        """Fetch real docker logs for a container."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("containers"):
            return Response(content=b'{"error":"containers disabled"}', status=404,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")
        tail = form_data.get("tail", "200")
        since = form_data.get("since", "")

        if not container_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        try:
            tail = int(tail)
        except (ValueError, TypeError):
            tail = 200

        result = self.site.get_container_logs(container_id, tail=tail, since=since)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/volume-inspect/")
    async def volume_inspect(self, request, ctx: RequestCtx) -> Response:
        """Return docker volume inspect output."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        name = form_data.get("name", "")

        if not name:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing volume name"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.get_volume_inspect(name)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/network-inspect/")
    async def network_inspect(self, request, ctx: RequestCtx) -> Response:
        """Return docker network inspect output."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        network_id = form_data.get("network_id", "")

        if not network_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing network_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.get_network_inspect(network_id)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/image-inspect/")
    async def image_inspect(self, request, ctx: RequestCtx) -> Response:
        """Return docker image inspect output."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        image_id = form_data.get("image_id", "")

        if not image_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing image_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.get_image_inspect(image_id)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/image-action/")
    async def image_action(self, request, ctx: RequestCtx) -> Response:
        """Execute image action (rm/pull)."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        image_id = form_data.get("image_id", "")
        action = form_data.get("action", "")

        if not image_id or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing image_id or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_image_action(image_id, action)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.IMAGE_ACTION,
                model_name="Docker",
                metadata={"image_id": image_id, "action": action},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/compose-action/")
    async def compose_action(self, request, ctx: RequestCtx) -> Response:
        """Execute compose action (up/down/restart/build/pull/stop/start)."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        action = form_data.get("action", "")

        if not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_compose_action(action)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.COMPOSE_ACTION,
                model_name="Docker",
                metadata={"action": action},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/volume-action/")
    async def volume_action(self, request, ctx: RequestCtx) -> Response:
        """Execute volume action (rm)."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        name = form_data.get("name", "")
        action = form_data.get("action", "")

        if not name or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing name or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_volume_action(name, action)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.VOLUME_ACTION,
                model_name="Docker",
                metadata={"volume": name, "action": action},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/network-action/")
    async def network_action(self, request, ctx: RequestCtx) -> Response:
        """Execute network action (rm)."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        network_id = form_data.get("network_id", "")
        action = form_data.get("action", "")

        if not network_id or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing network_id or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_network_action(network_id, action)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.NETWORK_ACTION,
                model_name="Docker",
                metadata={"network_id": network_id, "action": action},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Advanced Docker Endpoints ────────────────────────────────────

    @POST("/containers/disk-usage/")
    async def docker_disk_usage(self, request, ctx: RequestCtx) -> Response:
        """Return docker system df output."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()

        # CSRF validation (JSON API - check headers)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        result = self.site.get_docker_disk_usage_summary()
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/prune/")
    async def docker_prune(self, request, ctx: RequestCtx) -> Response:
        """Execute docker prune (system/images/containers/volumes/builder)."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        target = form_data.get("target", "")
        if not target:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing target"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_docker_prune(target)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.DOCKER_PRUNE,
                model_name="Docker",
                metadata={"target": target},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/exec/")
    async def container_exec(self, request, ctx: RequestCtx) -> Response:
        """Execute a command inside a running container."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")
        command = form_data.get("command", "")
        if not container_id or not command:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id or command"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_container_exec(container_id, command)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.CONTAINER_EXEC,
                model_name="Docker",
                metadata={"container_id": container_id, "command": command},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/image-history/")
    async def image_history(self, request, ctx: RequestCtx) -> Response:
        """Return docker history for an image."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        image_id = form_data.get("image_id", "")
        if not image_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing image_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.get_image_history(image_id)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/image-tag/")
    async def image_tag(self, request, ctx: RequestCtx) -> Response:
        """Tag an image with a new name."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        source = form_data.get("source", "")
        target = form_data.get("target", "")
        if not source or not target:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing source or target"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_image_tag(source, target)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.IMAGE_TAG,
                model_name="Docker",
                metadata={"source": source, "target": target},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/export/")
    async def container_export(self, request, ctx: RequestCtx) -> Response:
        """Export a container filesystem as tar."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")
        if not container_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_container_export(container_id)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.CONTAINER_EXPORT,
                model_name="Docker",
                metadata={"container_id": container_id},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/create-network/")
    async def create_network(self, request, ctx: RequestCtx) -> Response:
        """Create a new Docker network."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        name = form_data.get("name", "")
        driver = form_data.get("driver", "bridge")
        subnet = form_data.get("subnet", "")
        gateway = form_data.get("gateway", "")
        internal = form_data.get("internal", "") in ("1", "true", "on")
        if not name:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing network name"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.create_docker_network(name, driver, subnet, gateway, internal)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.NETWORK_CREATE,
                model_name="Docker",
                metadata={"name": name, "driver": driver},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/create-volume/")
    async def create_volume(self, request, ctx: RequestCtx) -> Response:
        """Create a new Docker volume."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        name = form_data.get("name", "")
        driver = form_data.get("driver", "local")
        labels = form_data.get("labels", "")
        if not name:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing volume name"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.create_docker_volume(name, driver, labels)
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.VOLUME_CREATE,
                model_name="Docker",
                metadata={"name": name, "driver": driver},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/events/")
    async def docker_events(self, request, ctx: RequestCtx) -> Response:
        """Return recent docker events."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        since = form_data.get("since", "10m")
        result = self.site.get_docker_events(since)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/build/")
    async def docker_build(self, request, ctx: RequestCtx) -> Response:
        """Execute docker build in the workspace."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        tag = form_data.get("tag", "")
        no_cache = form_data.get("no_cache", "") in ("1", "true", "on")
        build_args = form_data.get("build_args", "")
        target = form_data.get("target", "")
        result = self.site.execute_docker_build(
            tag=tag, no_cache=no_cache, build_args=build_args, target=target,
        )
        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.DOCKER_BUILD,
                model_name="Docker",
                metadata={"tag": tag, "no_cache": no_cache},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/top/")
    async def container_top(self, request, ctx: RequestCtx) -> Response:
        """Return processes running inside a container."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")
        if not container_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.get_container_top(container_id)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/diff/")
    async def container_diff(self, request, ctx: RequestCtx) -> Response:
        """Return filesystem changes in a container."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")
        if not container_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.get_container_diff(container_id)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/containers/container-stats/")
    async def container_stats_single(self, request, ctx: RequestCtx) -> Response:
        """Return single-shot stats for one container."""
        import json as _json
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})
        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, form_data)
        if csrf_denied:
            return csrf_denied

        container_id = form_data.get("container_id", "")
        if not container_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.get_container_stats_stream(container_id)
        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200, headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Pods Page ────────────────────────────────────────────────────

    @GET("/pods/")
    async def pods_view(self, request, ctx: RequestCtx) -> Response:
        """Kubernetes pods -- deployments, services, ingresses & manifests."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("pods"):
            return self._module_disabled_response("Pods", identity)

        if not has_admin_permission(identity, AdminPermission.POD_VIEW):
            return self._permission_denied_response("Pods", identity, AdminPermission.POD_VIEW)

        self._ensure_initialized()

        pods_data = self.site.get_pods_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Pods",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_pods_page(
            pods_data=pods_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/pods/api/")
    async def pods_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling pod metrics."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("pods"):
            return Response(
                content=b'{"error":"pods disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        pods_data = self.site.get_pods_data()
        return Response(
            content=_json.dumps(pods_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Storage Page ─────────────────────────────────────────────────

    @GET("/storage/")
    async def storage_view(self, request, ctx: RequestCtx) -> Response:
        """Storage backends -- file browser, analytics, health & configuration."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("storage"):
            return self._module_disabled_response("Storage", identity)

        if not has_admin_permission(identity, AdminPermission.STORAGE_VIEW):
            return self._permission_denied_response("Storage", identity, AdminPermission.STORAGE_VIEW)

        self._ensure_initialized()

        storage_data = await self.site.get_storage_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Storage",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_storage_page(
            storage_data=storage_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/storage/api/")
    async def storage_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling storage metrics."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("storage"):
            return Response(
                content=b'{"error":"storage disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        storage_data = await self.site.get_storage_data()

        # ── Compute derived fields the frontend expects ──
        backends = storage_data.get("backends", [])
        health = storage_data.get("health", {})
        all_files = storage_data.get("all_files", [])
        total_size = storage_data.get("total_size", 0)

        def _fmt_bytes(b: int) -> str:
            for u in ("B", "KB", "MB", "GB", "TB"):
                if abs(b) < 1024:
                    return f"{b:.1f} {u}"
                b /= 1024
            return f"{b:.1f} PB"

        file_type_count: dict = {}
        largest = 0
        for f in all_files:
            ct = f.get("content_type", "application/octet-stream")
            major = ct.split("/")[0] if "/" in ct else ct
            file_type_count[major] = file_type_count.get(major, 0) + 1
            sz = f.get("size", 0)
            if sz > largest:
                largest = sz

        storage_data["total_backends"] = len(backends)
        storage_data["total_size_human"] = _fmt_bytes(total_size)
        storage_data["healthy_count"] = sum(1 for v in health.values() if v)
        storage_data["file_type_count"] = len(file_type_count)
        storage_data["largest_file_size"] = _fmt_bytes(largest)
        storage_data["health_labels"] = list(health.keys()) if health else []
        storage_data["health_values"] = [1 if health.get(a, False) else 0 for a in storage_data["health_labels"]]

        return Response(
            content=_json.dumps(storage_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Storage File Operations ──────────────────────────────────────

    @GET("/storage/api/download")
    async def storage_download(self, request, ctx: RequestCtx) -> Response:
        """Download a file from a storage backend."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401, headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("storage"):
            return Response(content=b'{"error":"storage disabled"}', status=404, headers={"content-type": "application/json"})

        self._ensure_initialized()

        backend_alias = ctx.query_param("backend", "default")
        file_path = ctx.query_param("path", "")
        if not file_path:
            return Response(content=b'{"error":"path is required"}', status=400, headers={"content-type": "application/json"})

        try:
            registry = self.site._storage_registry
            if not registry:
                return Response(content=b'{"error":"storage not available"}', status=503, headers={"content-type": "application/json"})

            backend = registry.get(backend_alias)
            if not backend:
                return Response(content=b'{"error":"backend not found"}', status=404, headers={"content-type": "application/json"})
            storage_file = await backend.open(file_path)
            # StorageFile.read() returns bytes
            content = await storage_file.read()
            await storage_file.close()

            # Use content-type from metadata if available, else guess
            import mimetypes as _mt
            ct = (storage_file.meta.content_type if storage_file.meta and storage_file.meta.content_type else None)
            if not ct:
                ct, _ = _mt.guess_type(file_path)
            ct = ct or "application/octet-stream"
            fname = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path

            try:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.FILE_DOWNLOAD,
                    model_name="Storage",
                    metadata={"backend": backend_alias, "path": file_path, "size": len(content)},
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            except Exception:
                pass

            return Response(
                content=content,
                status=200,
                headers={
                    "content-type": ct,
                    "content-disposition": f'attachment; filename="{fname}"',
                    "content-length": str(len(content)),
                },
            )
        except FileNotFoundError:
            return Response(
                content=b'{"error":"file not found"}',
                status=404,
                headers={"content-type": "application/json"},
            )
        except Exception as exc:
            import json as _json
            return Response(
                content=_json.dumps({"error": str(exc)}).encode("utf-8"),
                status=500,
                headers={"content-type": "application/json"},
            )

    @POST("/storage/api/upload")
    async def storage_upload(self, request, ctx: RequestCtx) -> Response:
        """Upload a file to a storage backend from the admin panel."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401, headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("storage"):
            return Response(content=b'{"error":"storage disabled"}', status=404, headers={"content-type": "application/json"})

        self._ensure_initialized()

        import json as _json

        # CSRF validation (check headers for multipart uploads)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        try:
            form = await ctx.multipart()
            file_obj = form.get_file("file")
            if not file_obj:
                return Response(content=b'{"error":"no file provided"}', status=400, headers={"content-type": "application/json"})

            backend_alias = form.get_field("backend", "default") if hasattr(form, "get_field") else form.get("backend", "default")
            file_path = (form.get_field("path", "") if hasattr(form, "get_field") else form.get("path", "")) or getattr(file_obj, "filename", "uploaded_file")
            file_data = await file_obj.read() if hasattr(file_obj, "read") else file_obj.data if hasattr(file_obj, "data") else bytes(file_obj)

            registry = self.site._storage_registry
            if not registry:
                return Response(content=b'{"error":"storage not available"}', status=503, headers={"content-type": "application/json"})

            backend = registry.get(backend_alias)
            if not backend:
                return Response(content=b'{"error":"backend not found"}', status=404, headers={"content-type": "application/json"})
            await backend.save(file_path, file_data)

            try:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.FILE_UPLOAD,
                    model_name="Storage",
                    metadata={"backend": backend_alias, "path": file_path, "size": len(file_data)},
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            except Exception:
                pass

            return Response(
                content=_json.dumps({"success": True, "path": file_path, "backend": backend_alias}).encode("utf-8"),
                status=200,
                headers={"content-type": "application/json; charset=utf-8"},
            )
        except Exception as exc:
            return Response(
                content=_json.dumps({"error": str(exc)}).encode("utf-8"),
                status=500,
                headers={"content-type": "application/json"},
            )

    @POST("/storage/api/delete")
    async def storage_delete(self, request, ctx: RequestCtx) -> Response:
        """Delete a file from a storage backend."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401, headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("storage"):
            return Response(content=b'{"error":"storage disabled"}', status=404, headers={"content-type": "application/json"})

        self._ensure_initialized()

        import json as _json

        # CSRF validation (JSON API - check headers)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        try:
            body = await ctx.json()
            backend_alias = body.get("backend", "default")
            file_path = body.get("path", "")
            if not file_path:
                return Response(content=b'{"error":"path is required"}', status=400, headers={"content-type": "application/json"})

            registry = self.site._storage_registry
            if not registry:
                return Response(content=b'{"error":"storage not available"}', status=503, headers={"content-type": "application/json"})

            backend = registry.get(backend_alias)
            if not backend:
                return Response(content=b'{"error":"backend not found"}', status=404, headers={"content-type": "application/json"})
            await backend.delete(file_path)

            try:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.FILE_DELETE,
                    model_name="Storage",
                    metadata={"backend": backend_alias, "path": file_path},
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            except Exception:
                pass

            return Response(
                content=_json.dumps({"success": True, "path": file_path, "backend": backend_alias}).encode("utf-8"),
                status=200,
                headers={"content-type": "application/json; charset=utf-8"},
            )
        except Exception as exc:
            return Response(
                content=_json.dumps({"error": str(exc)}).encode("utf-8"),
                status=500,
                headers={"content-type": "application/json"},
            )

    # ── Query Inspector Page ─────────────────────────────────────────

    @GET("/query-inspector/")
    async def query_inspector_view(self, request, ctx: RequestCtx) -> Response:
        """Live query inspector -- ORM→SQL, timing, EXPLAIN, N+1 detection."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("query_inspector"):
            return self._module_disabled_response("Query Inspector", identity)

        if not has_admin_permission(identity, AdminPermission.QUERY_INSPECTOR_VIEW):
            return self._permission_denied_response("Query Inspector", identity, AdminPermission.QUERY_INSPECTOR_VIEW)

        self._ensure_initialized()

        query_data = self.site.get_query_inspector_data()
        app_list = self.site.get_app_list(identity)

        # Pagination for recent queries
        try:
            qs = request.query_params
            qi_page = max(1, int(qs.get("page", 1)))
        except (ValueError, TypeError, AttributeError):
            qi_page = 1
        qi_per_page = 30
        all_recent = query_data.get("recent_queries", [])
        qi_total = len(all_recent)
        qi_total_pages = max(1, (qi_total + qi_per_page - 1) // qi_per_page)
        qi_page = min(qi_page, qi_total_pages)
        qi_offset = (qi_page - 1) * qi_per_page
        # Show most recent first: reverse, then paginate
        reversed_queries = list(reversed(all_recent))
        paginated_queries = reversed_queries[qi_offset:qi_offset + qi_per_page]
        query_data["recent_queries"] = paginated_queries

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="QueryInspector",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_query_inspector_page(
            query_data=query_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
            qi_page=qi_page,
            qi_per_page=qi_per_page,
            qi_total=qi_total,
            qi_total_pages=qi_total_pages,
        )
        return _html_response(html)

    @GET("/query-inspector/api/")
    async def query_inspector_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling query inspector data."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("query_inspector"):
            return Response(
                content=b'{"error":"query_inspector disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        query_data = self.site.get_query_inspector_data()
        return Response(
            content=_json.dumps(query_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Mailer Page ────────────────────────────────────────────────

    @GET("/mailer/")
    async def mailer_view(self, request, ctx: RequestCtx) -> Response:
        """Mail administration -- providers, config, templates, send test email."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("mailer"):
            return self._module_disabled_response("Mailer", identity)

        if not has_admin_permission(identity, AdminPermission.MAILER_VIEW):
            return self._permission_denied_response("Mailer", identity, AdminPermission.MAILER_VIEW)

        self._ensure_initialized()

        mailer_data = self.site.get_mailer_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Mailer",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_mailer_page(
            mailer_data=mailer_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/mailer/api/")
    async def mailer_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling mailer data."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("mailer"):
            return Response(
                content=b'{"error":"mailer disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        mailer_data = self.site.get_mailer_data()
        return Response(
            content=_json.dumps(mailer_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/mailer/send-test/")
    async def mailer_send_test(self, request, ctx: RequestCtx) -> Response:
        """Send a test email via the configured mail subsystem."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("mailer"):
            return Response(
                content=b'{"error":"mailer disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        if not has_admin_permission(identity, AdminPermission.MAILER_MANAGE):
            return Response(
                content=b'{"error":"permission denied"}',
                status=403,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json

        # CSRF validation (JSON API - check headers for JSON body requests)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        try:
            body = await request.body()
            payload = _json.loads(body) if body else {}
        except Exception:
            payload = {}

        to_email = payload.get("to", "").strip()
        subject = payload.get("subject", "Aquilia Test Email").strip()
        body_text = payload.get("body", "").strip()
        body_html = payload.get("body_html", "").strip()
        from_email = payload.get("from_email", "").strip() or None
        reply_to = payload.get("reply_to", "").strip() or None
        priority = payload.get("priority", "normal")

        if not to_email:
            return Response(
                content=_json.dumps({"success": False, "error": "Recipient email is required"}).encode(),
                status=400,
                headers={"content-type": "application/json"},
            )

        # Validate email format
        import re
        email_re = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$")
        if not email_re.match(to_email):
            return Response(
                content=_json.dumps({"success": False, "error": f"Invalid email address: {to_email}"}).encode(),
                status=400,
                headers={"content-type": "application/json"},
            )

        priority_map = {"critical": 0, "high": 25, "normal": 50, "low": 75, "bulk": 100}
        priority_val = priority_map.get(priority, 50)

        # Default body
        if not body_text and not body_html:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            body_text = (
                f"This is a test email sent from Aquilia Admin at {now}.\n\n"
                f"Sent by: {_get_identity_name(identity)}\n"
                f"Priority: {priority}\n\n"
                f"If you received this email, your mail configuration is working correctly."
            )
            body_html = (
                f'<div style="font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;'
                f'max-width:600px;margin:0 auto;padding:40px 20px;">'
                f'<div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:12px;'
                f'padding:32px;color:white;text-align:center;margin-bottom:24px;">'
                f'<h1 style="margin:0 0 8px;font-size:24px;">✉️ Aquilia Test Email</h1>'
                f'<p style="margin:0;opacity:0.9;font-size:14px;">Mail subsystem verification</p>'
                f'</div>'
                f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:24px;">'
                f'<p style="margin:0 0 12px;color:#334155;">This is a <strong>test email</strong> '
                f'sent from the Aquilia Admin panel.</p>'
                f'<table style="width:100%;font-size:13px;color:#64748b;">'
                f'<tr><td style="padding:4px 0;font-weight:600;">Sent at:</td>'
                f'<td style="padding:4px 0;">{now}</td></tr>'
                f'<tr><td style="padding:4px 0;font-weight:600;">Sent by:</td>'
                f'<td style="padding:4px 0;">{_get_identity_name(identity)}</td></tr>'
                f'<tr><td style="padding:4px 0;font-weight:600;">Priority:</td>'
                f'<td style="padding:4px 0;">{priority.title()}</td></tr>'
                f'</table>'
                f'</div>'
                f'<p style="text-align:center;color:#94a3b8;font-size:12px;margin-top:16px;">'
                f'Powered by AquilaMail — Production-ready async mail for Aquilia</p>'
                f'</div>'
            )

        if not subject:
            subject = "Aquilia Test Email"

        result = {"success": False, "error": None, "envelope_id": None, "provider": None}

        try:
            svc = getattr(self.site, "_mail_service", None)
            if svc is None:
                result["error"] = "MailService not available. Ensure mail integration is enabled."
            else:
                from aquilia.mail.message import EmailMessage, EmailMultiAlternatives

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=body_text,
                    from_email=from_email,
                    to=[to_email],
                    reply_to=reply_to,
                    priority=priority_val,
                    metadata={"source": "admin_test", "sent_by": _get_identity_name(identity)},
                )
                if body_html:
                    msg.attach_alternative(body_html, "text/html")

                envelope_id = await svc.send_message(msg)
                result["success"] = True
                result["envelope_id"] = envelope_id
                result["provider"] = "auto"

                # Audit log
                try:
                    meta = _extract_request_meta(request)
                    self.site.audit_log.log(
                        user_id=getattr(identity, "id", ""),
                        username=_get_identity_name(identity),
                        role=str(get_admin_role(identity) or "unknown"),
                        action=AdminAction.SETTINGS_CHANGE,
                        model_name="Mailer",
                        object_repr=f"Test email to {to_email}",
                        ip_address=meta.get("ip_address"),
                        user_agent=meta.get("user_agent"),
                    )
                except Exception:
                    pass

        except Exception as e:
            result["error"] = str(e)

        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200 if result["success"] else 500,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/mailer/health-check/")
    async def mailer_health_check(self, request, ctx: RequestCtx) -> Response:
        """Run health checks on all mail providers."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not has_admin_permission(identity, AdminPermission.MAILER_VIEW):
            return Response(
                content=b'{"error":"permission denied"}',
                status=403,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()
        import json as _json

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        svc = getattr(self.site, "_mail_service", None)
        if svc is None:
            return Response(
                content=_json.dumps({"error": "MailService not available"}).encode(),
                status=404,
                headers={"content-type": "application/json"},
            )

        results = {}
        providers = getattr(svc, "_providers", {})
        for name, provider in providers.items():
            try:
                healthy = await provider.health_check()
                results[name] = {"healthy": healthy, "error": None}
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)}

        overall = all(r["healthy"] for r in results.values()) if results else False

        return Response(
            content=_json.dumps({
                "overall_healthy": overall,
                "providers": results,
                "checked_count": len(results),
            }, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Background Tasks Page ────────────────────────────────────────

    @GET("/tasks/")
    async def tasks_view(self, request, ctx: RequestCtx) -> Response:
        """Background task monitor -- job queue, workers, retries."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("tasks"):
            return self._module_disabled_response("Background Tasks", identity)

        if not has_admin_permission(identity, AdminPermission.TASKS_VIEW):
            return self._permission_denied_response("Background Tasks", identity, AdminPermission.TASKS_VIEW)

        self._ensure_initialized()

        tasks_data = await self.site.get_tasks_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Tasks",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_tasks_page(
            tasks_data=tasks_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/tasks/api/")
    async def tasks_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling task data."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("tasks"):
            return Response(
                content=b'{"error":"tasks disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        tasks_data = await self.site.get_tasks_data()
        return Response(
            content=_json.dumps(tasks_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Error Monitoring Page ────────────────────────────────────────

    @GET("/errors/")
    async def errors_view(self, request, ctx: RequestCtx) -> Response:
        """Error monitoring -- stack traces, grouping, trends."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("errors"):
            return self._module_disabled_response("Error Monitoring", identity)

        if not has_admin_permission(identity, AdminPermission.ERRORS_VIEW):
            return self._permission_denied_response("Error Monitoring", identity, AdminPermission.ERRORS_VIEW)

        self._ensure_initialized()

        errors_data = self.site.get_error_tracker_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Errors",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_errors_page(
            errors_data=errors_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/errors/api/")
    async def errors_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling error data."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("errors"):
            return Response(
                content=b'{"error":"errors disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        errors_data = self.site.get_error_tracker_data()
        return Response(
            content=_json.dumps(errors_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── Testing Framework Page ───────────────────────────────────────

    @GET("/testing/")
    async def testing_view(self, request, ctx: RequestCtx) -> Response:
        """Testing framework -- test infrastructure, coverage, assertions."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("testing"):
            return self._module_disabled_response("Testing Framework", identity)

        if not has_admin_permission(identity, AdminPermission.TESTING_VIEW):
            return self._permission_denied_response("Testing", identity, AdminPermission.TESTING_VIEW)

        self._ensure_initialized()

        testing_data = self.site.get_testing_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Testing",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_testing_page(
            testing_data=testing_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/testing/api/")
    async def testing_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling testing data."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("testing"):
            return Response(
                content=b'{"error":"testing disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        testing_data = self.site.get_testing_data()
        return Response(
            content=_json.dumps(testing_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── MLOps Page ─────────────────────────────────────────────────

    @GET("/mlops/")
    async def mlops_view(self, request, ctx: RequestCtx) -> Response:
        """MLOps dashboard -- model registry, serving, drift, rollouts."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("mlops"):
            return self._module_disabled_response("MLOps", identity)

        if not has_admin_permission(identity, AdminPermission.MLOPS_VIEW):
            return self._permission_denied_response("MLOps", identity, AdminPermission.MLOPS_VIEW)

        self._ensure_initialized()

        mlops_data = self.site.get_mlops_data()
        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="MLOps",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_mlops_page(
            mlops_data=mlops_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
        )
        return _html_response(html)

    @GET("/mlops/api/")
    async def mlops_api(self, request, ctx: RequestCtx) -> Response:
        """JSON API endpoint for live-polling MLOps data."""
        identity, denied = _require_identity(ctx)
        if denied:
            return Response(
                content=b'{"error":"unauthorized"}',
                status=401,
                headers={"content-type": "application/json"},
            )

        if not self.site.admin_config.is_module_enabled("mlops"):
            return Response(
                content=b'{"error":"mlops disabled"}',
                status=404,
                headers={"content-type": "application/json"},
            )

        self._ensure_initialized()

        import json as _json
        mlops_data = self.site.get_mlops_data()
        return Response(
            content=_json.dumps(mlops_data, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    # ── MLOps Live Inference Playground ──────────────────────────────

    @POST("/mlops/api/predict/")
    async def mlops_predict(self, request, ctx: RequestCtx) -> Response:
        """
        Live inference playground -- send JSON input to a registered model.

        Expects JSON body:
            {"model": "model_name", "input": {...}, "version": "v1"}
        Returns:
            {"output": {...}, "latency_ms": float, "model": str, "version": str, "status": "ok"|"error"}
        """
        import json as _json
        import time as _time

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("mlops"):
            return Response(content=b'{"error":"mlops disabled"}', status=404,
                            headers={"content-type": "application/json"})

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        try:
            raw_body = await request.body()
            body = _json.loads(raw_body) if raw_body else {}
        except Exception:
            return Response(content=b'{"error":"invalid JSON body"}', status=400,
                            headers={"content-type": "application/json"})

        model_name = body.get("model", "")
        model_input = body.get("input", {})
        version = body.get("version", "")

        if not model_name:
            return Response(content=b'{"error":"model name required"}', status=400,
                            headers={"content-type": "application/json"})

        result: dict = {"model": model_name, "version": version, "status": "error"}

        try:
            # Try orchestrator-based predict
            registry = getattr(self.site, "_mlops_registry", None)
            entry = None
            if registry and hasattr(registry, "get"):
                entry = registry.get(model_name)

            if entry is None:
                result["error"] = f"Model '{model_name}' not found in registry"
                return Response(
                    content=_json.dumps(result, default=str).encode("utf-8"),
                    status=404,
                    headers={"content-type": "application/json; charset=utf-8"},
                )

            # Attempt to run inference
            model_instance = None
            if hasattr(entry, "instance") and entry.instance is not None:
                model_instance = entry.instance
            elif hasattr(entry, "model_class"):
                # Lazily instantiate for playground
                try:
                    model_instance = entry.model_class()
                    if hasattr(model_instance, "load"):
                        import asyncio
                        coro = model_instance.load("", "cpu")
                        if asyncio.iscoroutine(coro):
                            await coro
                    entry.instance = model_instance
                except Exception as load_err:
                    result["error"] = f"Failed to load model: {str(load_err)}"
                    return Response(
                        content=_json.dumps(result, default=str).encode("utf-8"),
                        status=500,
                        headers={"content-type": "application/json; charset=utf-8"},
                    )

            if model_instance is None:
                result["error"] = "Model instance not available"
                return Response(
                    content=_json.dumps(result, default=str).encode("utf-8"),
                    status=500,
                    headers={"content-type": "application/json; charset=utf-8"},
                )

            # Pre-process → Predict → Post-process
            import asyncio
            start = _time.perf_counter()

            processed_input = model_input
            if hasattr(model_instance, "preprocess"):
                pre = model_instance.preprocess(processed_input)
                if asyncio.iscoroutine(pre):
                    processed_input = await pre
                else:
                    processed_input = pre

            pred = model_instance.predict(processed_input)
            if asyncio.iscoroutine(pred):
                output = await pred
            else:
                output = pred

            if hasattr(model_instance, "postprocess"):
                post = model_instance.postprocess(output)
                if asyncio.iscoroutine(post):
                    output = await post
                else:
                    output = post

            elapsed = (_time.perf_counter() - start) * 1000.0

            # Record in metrics collector
            metrics_collector = getattr(self.site, "_mlops_metrics", None)
            if metrics_collector and hasattr(metrics_collector, "record_inference"):
                metrics_collector.record_inference(latency_ms=elapsed, model_name=model_name)

            # Store in inference history
            history = getattr(self.site, "_mlops_inference_history", None)
            if history is None:
                self.site._mlops_inference_history = []
                history = self.site._mlops_inference_history
            import datetime
            history.insert(0, {
                "model": model_name,
                "version": version or getattr(entry, "version", "?"),
                "input": model_input,
                "output": output,
                "latency_ms": round(elapsed, 2),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "status": "ok",
                "user": _get_identity_name(identity),
            })
            # Keep only last 100 entries
            if len(history) > 100:
                self.site._mlops_inference_history = history[:100]

            result["output"] = output
            result["latency_ms"] = round(elapsed, 2)
            result["version"] = version or getattr(entry, "version", "?")
            result["status"] = "ok"

        except Exception as e:
            result["error"] = str(e)
            result["status"] = "error"
            # Store failed inference
            history = getattr(self.site, "_mlops_inference_history", None)
            if history is None:
                self.site._mlops_inference_history = []
                history = self.site._mlops_inference_history
            import datetime
            history.insert(0, {
                "model": model_name,
                "version": version,
                "input": model_input,
                "output": None,
                "error": str(e),
                "latency_ms": 0,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "status": "error",
                "user": _get_identity_name(identity),
            })
            if len(history) > 100:
                self.site._mlops_inference_history = history[:100]

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.ML_INFERENCE,
                model_name="MLOps",
                metadata={"model": model_name, "version": version, "status": result.get("status", "unknown")},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        return Response(
            content=_json.dumps(result, default=str).encode("utf-8"),
            status=200 if result["status"] == "ok" else 500,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/mlops/api/compare/")
    async def mlops_compare(self, request, ctx: RequestCtx) -> Response:
        """
        Model comparison -- run same input through multiple models.

        Expects JSON body:
            {"models": ["model_a", "model_b"], "input": {...}}
        Returns:
            {"results": [{"model": str, "output": {...}, "latency_ms": float}, ...]}
        """
        import json as _json
        import time as _time

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("mlops"):
            return Response(content=b'{"error":"mlops disabled"}', status=404,
                            headers={"content-type": "application/json"})

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        try:
            raw_body = await request.body()
            body = _json.loads(raw_body) if raw_body else {}
        except Exception:
            return Response(content=b'{"error":"invalid JSON body"}', status=400,
                            headers={"content-type": "application/json"})

        model_names = body.get("models", [])
        model_input = body.get("input", {})

        if not model_names or len(model_names) < 2:
            return Response(content=b'{"error":"at least 2 model names required"}', status=400,
                            headers={"content-type": "application/json"})

        registry = getattr(self.site, "_mlops_registry", None)
        results = []

        for mname in model_names[:5]:  # Cap at 5 models
            entry_result: dict = {"model": mname, "status": "error"}
            try:
                entry = None
                if registry and hasattr(registry, "get"):
                    entry = registry.get(mname)

                if entry is None:
                    entry_result["error"] = f"Model '{mname}' not found"
                    results.append(entry_result)
                    continue

                model_instance = None
                if hasattr(entry, "instance") and entry.instance is not None:
                    model_instance = entry.instance
                elif hasattr(entry, "model_class"):
                    try:
                        import asyncio
                        model_instance = entry.model_class()
                        if hasattr(model_instance, "load"):
                            coro = model_instance.load("", "cpu")
                            if asyncio.iscoroutine(coro):
                                await coro
                        entry.instance = model_instance
                    except Exception as load_err:
                        entry_result["error"] = f"Load failed: {str(load_err)}"
                        results.append(entry_result)
                        continue

                if model_instance is None:
                    entry_result["error"] = "Instance not available"
                    results.append(entry_result)
                    continue

                import asyncio
                start = _time.perf_counter()

                processed = model_input
                if hasattr(model_instance, "preprocess"):
                    pre = model_instance.preprocess(processed)
                    if asyncio.iscoroutine(pre):
                        processed = await pre
                    else:
                        processed = pre

                pred = model_instance.predict(processed)
                if asyncio.iscoroutine(pred):
                    output = await pred
                else:
                    output = pred

                if hasattr(model_instance, "postprocess"):
                    post = model_instance.postprocess(output)
                    if asyncio.iscoroutine(post):
                        output = await post
                    else:
                        output = post

                elapsed = (_time.perf_counter() - start) * 1000.0

                entry_result["output"] = output
                entry_result["latency_ms"] = round(elapsed, 2)
                entry_result["version"] = getattr(entry, "version", "?")
                entry_result["status"] = "ok"

            except Exception as e:
                entry_result["error"] = str(e)

            results.append(entry_result)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.ML_COMPARE,
                model_name="MLOps",
                metadata={"models": model_names[:5], "result_count": len(results)},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        return Response(
            content=_json.dumps({"results": results}, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/mlops/api/health-check/")
    async def mlops_health_check(self, request, ctx: RequestCtx) -> Response:
        """
        Run health checks on all registered models.

        Returns:
            {"models": [{"name": str, "status": str, "details": {...}, "latency_ms": float}, ...]}
        """
        import json as _json
        import time as _time

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("mlops"):
            return Response(content=b'{"error":"mlops disabled"}', status=404,
                            headers={"content-type": "application/json"})

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        registry = getattr(self.site, "_mlops_registry", None)
        results = []

        if registry and hasattr(registry, "list_models"):
            try:
                for name in registry.list_models():
                    entry = registry.get(name)
                    check: dict = {"name": name, "status": "unknown", "details": {}, "latency_ms": 0}

                    try:
                        model_instance = None
                        if hasattr(entry, "instance") and entry.instance is not None:
                            model_instance = entry.instance

                        if model_instance is not None and hasattr(model_instance, "health"):
                            import asyncio
                            start = _time.perf_counter()
                            h = model_instance.health()
                            if asyncio.iscoroutine(h):
                                details = await h
                            else:
                                details = h
                            elapsed = (_time.perf_counter() - start) * 1000.0
                            check["details"] = details if isinstance(details, dict) else {"result": str(details)}
                            check["latency_ms"] = round(elapsed, 2)
                            check["status"] = details.get("status", "ok") if isinstance(details, dict) else "ok"
                        else:
                            state = getattr(entry, "state", "unknown")
                            check["status"] = state if isinstance(state, str) else (state.value if hasattr(state, "value") else str(state))
                            check["details"] = {"state": check["status"]}
                    except Exception as e:
                        check["status"] = "error"
                        check["details"] = {"error": str(e)}

                    results.append(check)
            except Exception:
                pass

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.ML_HEALTH_CHECK,
                model_name="MLOps",
                metadata={"models_checked": len(results)},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        return Response(
            content=_json.dumps({"models": results}, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/mlops/api/batch-predict/")
    async def mlops_batch_predict(self, request, ctx: RequestCtx) -> Response:
        """
        Batch inference -- run multiple inputs through a model.

        Expects JSON body:
            {"model": "model_name", "inputs": [{...}, {...}, ...]}
        Returns:
            {"results": [{"input": {...}, "output": {...}, "latency_ms": float}, ...],
             "total_latency_ms": float, "count": int, "errors": int}
        """
        import json as _json
        import time as _time

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        if not self.site.admin_config.is_module_enabled("mlops"):
            return Response(content=b'{"error":"mlops disabled"}', status=404,
                            headers={"content-type": "application/json"})

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        try:
            raw_body = await request.body()
            body = _json.loads(raw_body) if raw_body else {}
        except Exception:
            return Response(content=b'{"error":"invalid JSON body"}', status=400,
                            headers={"content-type": "application/json"})

        model_name = body.get("model", "")
        inputs = body.get("inputs", [])

        if not model_name:
            return Response(content=b'{"error":"model name required"}', status=400,
                            headers={"content-type": "application/json"})

        if not inputs or not isinstance(inputs, list):
            return Response(content=b'{"error":"inputs must be a non-empty array"}', status=400,
                            headers={"content-type": "application/json"})

        # Cap batch size at 50
        inputs = inputs[:50]

        registry = getattr(self.site, "_mlops_registry", None)
        entry = None
        if registry and hasattr(registry, "get"):
            entry = registry.get(model_name)

        if entry is None:
            return Response(
                content=_json.dumps({"error": f"Model '{model_name}' not found"}).encode("utf-8"),
                status=404, headers={"content-type": "application/json; charset=utf-8"},
            )

        model_instance = None
        if hasattr(entry, "instance") and entry.instance is not None:
            model_instance = entry.instance
        elif hasattr(entry, "model_class"):
            try:
                import asyncio
                model_instance = entry.model_class()
                if hasattr(model_instance, "load"):
                    coro = model_instance.load("", "cpu")
                    if asyncio.iscoroutine(coro):
                        await coro
                entry.instance = model_instance
            except Exception as e:
                return Response(
                    content=_json.dumps({"error": f"Load failed: {str(e)}"}).encode("utf-8"),
                    status=500, headers={"content-type": "application/json; charset=utf-8"},
                )

        if model_instance is None:
            return Response(
                content=_json.dumps({"error": "Instance not available"}).encode("utf-8"),
                status=500, headers={"content-type": "application/json; charset=utf-8"},
            )

        results = []
        errors = 0
        batch_start = _time.perf_counter()

        for item in inputs:
            row: dict = {"input": item, "status": "ok"}
            try:
                import asyncio
                start = _time.perf_counter()

                processed = item
                if hasattr(model_instance, "preprocess"):
                    pre = model_instance.preprocess(processed)
                    if asyncio.iscoroutine(pre):
                        processed = await pre
                    else:
                        processed = pre

                pred = model_instance.predict(processed)
                if asyncio.iscoroutine(pred):
                    output = await pred
                else:
                    output = pred

                if hasattr(model_instance, "postprocess"):
                    post = model_instance.postprocess(output)
                    if asyncio.iscoroutine(post):
                        output = await post
                    else:
                        output = post

                elapsed = (_time.perf_counter() - start) * 1000.0
                row["output"] = output
                row["latency_ms"] = round(elapsed, 2)
            except Exception as e:
                row["status"] = "error"
                row["error"] = str(e)
                errors += 1
            results.append(row)

        total_elapsed = (_time.perf_counter() - batch_start) * 1000.0

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.ML_BATCH_INFERENCE,
                model_name="MLOps",
                metadata={"model": model_name, "batch_size": len(inputs), "errors": errors, "total_ms": round(total_elapsed, 2)},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        return Response(
            content=_json.dumps({
                "results": results,
                "total_latency_ms": round(total_elapsed, 2),
                "count": len(results),
                "errors": errors,
                "model": model_name,
                "avg_latency_ms": round(total_elapsed / len(results), 2) if results else 0,
            }, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @GET("/mlops/api/inference-history/")
    async def mlops_inference_history(self, request, ctx: RequestCtx) -> Response:
        """Return recent inference history for the audit log."""
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        history = getattr(self.site, "_mlops_inference_history", [])
        return Response(
            content=_json.dumps({"history": history[:50]}, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/mlops/api/alerts/")
    async def mlops_update_alerts(self, request, ctx: RequestCtx) -> Response:
        """
        Update alert rules for MLOps monitoring.

        Expects JSON body:
            {"rules": [{"metric": str, "operator": str, "threshold": float, "enabled": bool}, ...]}
        """
        import json as _json

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        try:
            raw_body = await request.body()
            body = _json.loads(raw_body) if raw_body else {}
        except Exception:
            return Response(content=b'{"error":"invalid JSON body"}', status=400,
                            headers={"content-type": "application/json"})

        rules = body.get("rules", [])
        self.site._mlops_alert_rules = rules

        # Evaluate alerts against current data
        triggered = []
        mlops_data = self.site.get_mlops_data()
        metrics = mlops_data.get("metrics", {})
        latency = mlops_data.get("latency", {})

        metric_map = {
            "error_rate": mlops_data.get("total_errors", 0) / max(mlops_data.get("total_inferences", 1), 1),
            "p50_latency": latency.get("p50", 0),
            "p95_latency": latency.get("p95", 0),
            "p99_latency": latency.get("p99", 0),
            "total_errors": mlops_data.get("total_errors", 0),
            "drift_score": 0,
            "memory_usage_pct": 0,
        }

        # Get drift score
        drift = mlops_data.get("drift", {})
        if drift.get("has_reference"):
            drift_detector = getattr(self.site, "_mlops_drift", None)
            if drift_detector and hasattr(drift_detector, "_reference") and drift_detector._reference:
                metric_map["drift_score"] = drift.get("threshold", 0)

        # Get memory usage
        mem = mlops_data.get("memory", {})
        if mem.get("hard_limit", 0) > 0:
            metric_map["memory_usage_pct"] = (mem.get("current_bytes", 0) / mem["hard_limit"]) * 100

        for rule in rules:
            if not rule.get("enabled", True):
                continue
            metric_val = metric_map.get(rule.get("metric", ""), 0)
            op = rule.get("operator", ">")
            threshold = rule.get("threshold", 0)
            fired = False
            if op == ">" and metric_val > threshold:
                fired = True
            elif op == ">=" and metric_val >= threshold:
                fired = True
            elif op == "<" and metric_val < threshold:
                fired = True
            elif op == "==" and metric_val == threshold:
                fired = True
            if fired:
                triggered.append({
                    "metric": rule.get("metric"),
                    "current_value": round(metric_val, 4),
                    "threshold": threshold,
                    "operator": op,
                    "severity": rule.get("severity", "warning"),
                })

        self.site._mlops_triggered_alerts = triggered

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.ALERT_CONFIG,
                model_name="MLOps",
                metadata={"rules_count": len(rules), "triggered_count": len(triggered)},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        return Response(
            content=_json.dumps({"rules": rules, "triggered": triggered}, default=str).encode("utf-8"),
            status=200,
            headers={"content-type": "application/json; charset=utf-8"},
        )

    @POST("/mlops/api/export-snapshot/")
    async def mlops_export_snapshot(self, request, ctx: RequestCtx) -> Response:
        """Export a full MLOps state snapshot as JSON."""
        import json as _json
        import datetime

        identity, denied = _require_identity(ctx)
        if denied:
            return Response(content=b'{"error":"unauthorized"}', status=401,
                            headers={"content-type": "application/json"})

        # CSRF validation (JSON API)
        csrf_denied = self._csrf_reject_json(request, ctx, {})
        if csrf_denied:
            return csrf_denied

        mlops_data = self.site.get_mlops_data()
        snapshot = {
            "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "exported_by": _get_identity_name(identity),
            "data": mlops_data,
            "inference_history": getattr(self.site, "_mlops_inference_history", []),
            "alert_rules": getattr(self.site, "_mlops_alert_rules", []),
            "triggered_alerts": getattr(self.site, "_mlops_triggered_alerts", []),
        }

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.SNAPSHOT_EXPORT,
                model_name="MLOps",
                metadata={"exported_by": _get_identity_name(identity)},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        return Response(
            content=_json.dumps(snapshot, default=str, indent=2).encode("utf-8"),
            status=200,
            headers={
                "content-type": "application/json; charset=utf-8",
                "content-disposition": f'attachment; filename="aquilia-mlops-snapshot-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}.json"',
            },
        )

    # ── Admin Users Management ───────────────────────────────────────

    @GET("/admin-users/")
    async def admin_users_view(self, request, ctx: RequestCtx) -> Response:
        """List and manage admin users with hierarchy."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("admin_users"):
            return self._module_disabled_response("Admin Users", identity)

        if not has_admin_permission(identity, AdminPermission.USER_MANAGE):
            return _redirect("/admin/")

        self._ensure_initialized()

        # Fetch all admin users via ORM
        users = []
        try:
            from aquilia.admin.models import AdminUser
            all_users = await AdminUser.objects.all()
            users = [
                {
                    "pk": str(u.pk),
                    "username": u.username,
                    "email": getattr(u, "email", ""),
                    "first_name": getattr(u, "first_name", ""),
                    "last_name": getattr(u, "last_name", ""),
                    "is_superuser": getattr(u, "is_superuser", False),
                    "is_staff": getattr(u, "is_staff", False),
                    "is_active": getattr(u, "is_active", True),
                    "last_login": str(getattr(u, "last_login", "") or ""),
                    "date_joined": str(getattr(u, "date_joined", "") or ""),
                    "avatar_path": getattr(u, "avatar_path", "") or "",
                }
                for u in all_users
            ]
        except Exception:
            pass

        # Flash
        flash = ""
        flash_type = "success"
        if ctx.session and hasattr(ctx.session, "data"):
            flash = ctx.session.data.pop("_admin_flash", "")
            flash_type = ctx.session.data.pop("_admin_flash_type", "success")

        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="AdminUsers",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_admin_users_page(
            users=users,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
            flash=flash,
            flash_type=flash_type,
        )
        return _html_response(html)

    @POST("/admin-users/create")
    async def admin_users_create(self, request, ctx: RequestCtx) -> Response:
        """Create a new admin user with CSRF, rate limiting, and password validation."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not has_admin_permission(identity, AdminPermission.USER_MANAGE):
            return _redirect("/admin/")

        self._ensure_initialized()

        client_ip = self.site.security.extract_client_ip(request)

        # Rate limit sensitive operation
        allowed, retry_after = self.site.security.rate_limiter.check_sensitive_op(
            client_ip, "admin_user_create"
        )
        if not allowed:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Rate limited. Try again in {retry_after} seconds."
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/admin-users/")

        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/admin-users/")
        if csrf_denied:
            return csrf_denied

        username = (form_data.get("username") or "").strip()
        email = (form_data.get("email") or "").strip()
        password = form_data.get("password") or ""
        first_name = (form_data.get("first_name") or "").strip()
        last_name = (form_data.get("last_name") or "").strip()
        role = (form_data.get("role") or "staff").strip()

        if not username or not password:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "Username and password are required."
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/admin-users/")

        # Password complexity validation
        pw_result = self.site.security.password_validator.validate(password, username=username)
        if not pw_result.is_valid:
            feedback = " ".join(pw_result.feedback)
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Weak password: {feedback}"
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/admin-users/")

        try:
            from aquilia.admin.models import AdminUser

            # Three roles: superadmin, staff, viewer
            is_superuser = role == "superadmin"
            is_staff = role in ("superadmin", "staff")

            if is_superuser:
                user = await AdminUser.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                )
            else:
                user = await AdminUser.create_staff_user(
                    username=username,
                    email=email,
                    password=password,
                )

            # Update extra fields
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            # Viewer: is_staff=False so they get read-only access
            if role == "viewer":
                user.is_staff = False
            user.is_active = True
            await user.save()

            # Audit
            try:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.ADMIN_USER_CREATE,
                    model_name="AdminUser",
                    record_pk=str(getattr(user, "pk", "")),
                    changes={"username": username, "email": email, "role": role},
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            except Exception:
                pass

            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Admin '{username}' created successfully as {role}."
                ctx.session.data["_admin_flash_type"] = "success"
        except Exception as e:
            err_msg = str(e).lower()
            if "unique constraint" in err_msg and "username" in err_msg:
                flash_msg = f"Username '{username}' already exists. Choose a different username."
            elif "unique constraint" in err_msg and "email" in err_msg:
                flash_msg = f"Email '{email}' is already registered to another admin."
            elif "unique constraint" in err_msg:
                flash_msg = f"A user with that username or email already exists."
            else:
                flash_msg = f"Failed to create admin: {e}"
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = flash_msg
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect("/admin/admin-users/")

    @POST("/admin-users/toggle-status")
    async def admin_users_toggle_status(self, request, ctx: RequestCtx) -> Response:
        """Toggle active status of an admin user."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not has_admin_permission(identity, AdminPermission.USER_MANAGE):
            return _redirect("/admin/")

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/admin-users/")
        if csrf_denied:
            return csrf_denied

        user_id = form_data.get("user_id", "")

        try:
            from aquilia.admin.models import AdminUser
            user = await AdminUser.objects.get(pk=user_id)
            user.is_active = not user.is_active
            await user.save()

            action = "activated" if user.is_active else "deactivated"
            try:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.ADMIN_USER_UPDATE,
                    model_name="AdminUser",
                    record_pk=str(user_id),
                    changes={"is_active": user.is_active, "action": action},
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            except Exception:
                pass

            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Admin '{user.username}' {action}."
                ctx.session.data["_admin_flash_type"] = "success"
        except Exception as e:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Failed: {e}"
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect("/admin/admin-users/")

    @POST("/admin-users/reset-password")
    async def admin_users_reset_password(self, request, ctx: RequestCtx) -> Response:
        """Reset password for an admin user (with CSRF and password validation)."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not has_admin_permission(identity, AdminPermission.USER_MANAGE):
            return _redirect("/admin/")

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/admin-users/")
        if csrf_denied:
            return csrf_denied

        user_id = form_data.get("user_id", "")
        new_password = form_data.get("new_password", "")

        # Password complexity validation
        pw_result = self.site.security.password_validator.validate(new_password)
        if not pw_result.is_valid:
            feedback = " ".join(pw_result.feedback)
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Weak password: {feedback}"
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/admin-users/")

        try:
            from aquilia.admin.models import AdminUser
            user = await AdminUser.objects.get(pk=user_id)
            user.set_password(new_password)
            await user.save()

            try:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.PASSWORD_CHANGE,
                    model_name="AdminUser",
                    record_pk=str(user_id),
                    metadata={"target_user": user.username, "action": "password_reset"},
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            except Exception:
                pass

            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Password for '{user.username}' has been reset."
                ctx.session.data["_admin_flash_type"] = "success"
        except Exception as e:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Failed: {e}"
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect("/admin/admin-users/")

    @POST("/admin-users/delete")
    async def admin_users_delete(self, request, ctx: RequestCtx) -> Response:
        """Delete an admin user (cannot delete superadmins)."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not has_admin_permission(identity, AdminPermission.USER_MANAGE):
            return _redirect("/admin/")

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/admin-users/")
        if csrf_denied:
            return csrf_denied

        user_id = form_data.get("user_id", "")

        try:
            from aquilia.admin.models import AdminUser
            user = await AdminUser.objects.get(pk=user_id)

            if user.is_superuser:
                if ctx.session and hasattr(ctx.session, "data"):
                    ctx.session.data["_admin_flash"] = "Cannot delete a superadmin account."
                    ctx.session.data["_admin_flash_type"] = "error"
                return _redirect("/admin/admin-users/")

            username = user.username
            await user.delete()

            try:
                meta = _extract_request_meta(request)
                self.site.audit_log.log(
                    user_id=getattr(identity, "id", ""),
                    username=_get_identity_name(identity),
                    role=str(get_admin_role(identity) or "unknown"),
                    action=AdminAction.ADMIN_USER_DELETE,
                    model_name="AdminUser",
                    record_pk=str(user_id),
                    metadata={"deleted_user": username},
                    ip_address=meta.get("ip_address"),
                    user_agent=meta.get("user_agent"),
                )
            except Exception:
                pass

            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Admin '{username}' deleted."
                ctx.session.data["_admin_flash_type"] = "success"
        except Exception as e:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Failed: {e}"
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect("/admin/admin-users/")

    # ── Profile ──────────────────────────────────────────────────────

    @GET("/profile/")
    async def profile_view(self, request, ctx: RequestCtx) -> Response:
        """View the admin profile management page."""
        self._ensure_csrf(ctx)
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("profile"):
            return self._module_disabled_response("Profile", identity)

        if not has_admin_permission(identity, AdminPermission.PROFILE_VIEW):
            return self._permission_denied_response("Profile", identity, AdminPermission.PROFILE_VIEW)

        self._ensure_initialized()

        # Build user dict from identity attributes
        user = {
            "username": identity.get_attribute("username", identity.id),
            "email": identity.get_attribute("email", ""),
            "first_name": identity.get_attribute("first_name", ""),
            "last_name": identity.get_attribute("last_name", ""),
            "is_superuser": identity.get_attribute("is_superuser", False),
            "is_staff": identity.get_attribute("is_staff", False),
            "admin_role": identity.get_attribute("admin_role", "staff"),
            "avatar_path": identity.get_attribute("avatar_path", ""),
            "bio": identity.get_attribute("bio", ""),
            "phone": identity.get_attribute("phone", ""),
            "timezone": identity.get_attribute("timezone", "UTC"),
            "locale": identity.get_attribute("locale", "en"),
        }

        # Try to get full user from DB
        try:
            from aquilia.admin.models import AdminUser
            db_user = await AdminUser.objects.filter(
                username=user["username"]
            ).first()
            if db_user:
                user.update({
                    "pk": str(db_user.pk),
                    "email": getattr(db_user, "email", "") or "",
                    "first_name": getattr(db_user, "first_name", "") or "",
                    "last_name": getattr(db_user, "last_name", "") or "",
                    "is_superuser": getattr(db_user, "is_superuser", False),
                    "is_staff": getattr(db_user, "is_staff", False),
                    "last_login": str(getattr(db_user, "last_login", "") or ""),
                    "date_joined": str(getattr(db_user, "date_joined", "") or ""),
                    "avatar_path": getattr(db_user, "avatar_path", "") or "",
                    "bio": getattr(db_user, "bio", "") or "",
                    "phone": getattr(db_user, "phone", "") or "",
                    "timezone": getattr(db_user, "timezone", "UTC") or "UTC",
                    "locale": getattr(db_user, "locale", "en") or "en",
                })
        except Exception:
            pass

        flash = ""
        flash_type = "success"
        if ctx.session and hasattr(ctx.session, "data"):
            flash = ctx.session.data.pop("_admin_flash", "")
            flash_type = ctx.session.data.pop("_admin_flash_type", "success")

        app_list = self.site.get_app_list(identity)

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.PAGE_VIEW,
                model_name="Profile",
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        html = render_profile_page(
            user=user,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
                identity_avatar=_get_identity_avatar(identity),
            flash=flash,
            flash_type=flash_type,
        )
        return _html_response(html)

    @GET("/profile/<filename>")
    async def profile_avatar_legacy_redirect(self, request, ctx: RequestCtx, filename: str) -> Response:
        """Redirect legacy avatar URLs (/admin/profile/<file>) to the canonical path.

        Old code stored ``avatar_path`` without the ``/avatar/`` sub-segment,
        so browsers may still have the wrong URL cached.  A permanent (301)
        redirect keeps images working without breaking bookmarks.

        Only activates for filenames that look like image files
        (``<name>.<ext>``).  Pure path segments like ``avatar`` or ``upload``
        are left for their own routes and fall through to a 404.
        """
        import re
        # Must look like a filename with an extension; "avatar" itself is not
        # an image filename, so sub-routes are unaffected.
        if not re.fullmatch(r"[A-Za-z0-9_\-]+\.[a-zA-Z0-9]{2,5}", filename):
            return Response(content=b"Not Found", status=404,
                            headers={"content-type": "text/plain"})
        prefix = self.site.url_prefix if hasattr(self, "site") and self.site else "/admin"
        return Response(
            content=b"",
            status=301,
            headers={"location": f"{prefix}/profile/avatar/{filename}"},
        )

    @GET("/profile/avatar/<filename>")
    async def profile_avatar_serve(self, request, ctx: RequestCtx, filename: str) -> Response:
        """Serve a stored profile avatar from .aquilia/admin/profile/."""
        import re
        # Sanitise: only alphanumeric, dash, underscore, dot
        if not re.fullmatch(r"[A-Za-z0-9_\-\.]+", filename):
            return Response(content=b"Not Found", status=404,
                            headers={"content-type": "text/plain"})
        avatar_dir = _get_avatar_dir()
        file_path = avatar_dir / filename
        if not file_path.is_file():
            return Response(content=b"Not Found", status=404,
                            headers={"content-type": "text/plain"})
        # Determine content-type from extension
        ext = file_path.suffix.lower().lstrip(".")
        ct_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                  "png": "image/png", "gif": "image/gif",
                  "webp": "image/webp"}
        ct = ct_map.get(ext, "application/octet-stream")
        try:
            data = file_path.read_bytes()
        except OSError:
            return Response(content=b"Not Found", status=404,
                            headers={"content-type": "text/plain"})
        return Response(
            content=data,
            status=200,
            headers={
                "content-type": ct,
                "cache-control": "private, max-age=86400",
                "content-length": str(len(data)),
            },
        )

    @POST("/profile/upload-avatar")
    async def profile_upload_avatar(self, request, ctx: RequestCtx) -> Response:
        """Upload a new profile photo and persist it in .aquilia/admin/profile/."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        def _flash(msg: str, kind: str = "error") -> Response:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = msg
                ctx.session.data["_admin_flash_type"] = kind
            return _redirect("/admin/profile/")

        # Parse multipart
        try:
            form_data = await ctx.multipart()
        except Exception as e:
            return _flash(f"Upload failed: {e}")

        # CSRF validation (check multipart fields and headers)
        multipart_fields = {}
        try:
            if hasattr(form_data, "fields") and hasattr(form_data.fields, "to_dict"):
                multipart_fields = form_data.fields.to_dict()
            elif hasattr(form_data, "fields") and isinstance(form_data.fields, dict):
                multipart_fields = dict(form_data.fields)
        except Exception:
            pass
        csrf_denied = self._csrf_reject_json(request, ctx, multipart_fields)
        if csrf_denied:
            return csrf_denied

        # Retrieve file from the 'avatar' field
        upload_file = None
        try:
            files = form_data.files  # Dict[str, List[UploadFile]]
            candidates = files.get("avatar") or []
            if candidates:
                upload_file = candidates[0]
        except Exception:
            pass

        if upload_file is None:
            return _flash("No file received. Please choose an image.")

        # Read content (cap at max size + 1 byte to detect over-limit)
        try:
            raw = await upload_file.read(_MAX_AVATAR_BYTES + 1)
        except Exception as e:
            return _flash(f"Could not read file: {e}")

        if len(raw) > _MAX_AVATAR_BYTES:
            return _flash("Image is too large. Maximum size is 4 MB.")

        ext = _sniff_image_ext(raw)
        if ext is None:
            # Fallback: trust Content-Type only if it maps cleanly
            ct = getattr(upload_file, "content_type", "") or ""
            fallback = {
                "image/jpeg": "jpg", "image/png": "png",
                "image/gif": "gif", "image/webp": "webp",
            }.get(ct.split(";")[0].strip())
            if fallback is None:
                return _flash("Unsupported file type. Please upload a JPEG, PNG, GIF or WebP image.")
            ext = fallback

        # Derive a stable UUID from the username so each user has one file
        import uuid as _uuid
        username = identity.get_attribute("username", identity.id)
        file_uuid = str(_uuid.uuid5(_uuid.NAMESPACE_URL, f"aquilia-admin-avatar:{username}"))
        filename = f"{file_uuid}.{ext}"

        # Write to .aquilia/admin/profile/
        avatar_dir = _get_avatar_dir()
        dest = avatar_dir / filename
        try:
            dest.write_bytes(raw)
        except OSError as e:
            return _flash(f"Could not save image: {e}")

        # Build the full serving URL path so templates/JS can use it directly
        prefix = self.site.url_prefix if hasattr(self, "site") and self.site else "/admin"
        avatar_url = f"{prefix}/profile/avatar/{filename}"

        try:
            meta = _extract_request_meta(request)
            self.site.audit_log.log(
                user_id=getattr(identity, "id", ""),
                username=_get_identity_name(identity),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.AVATAR_UPLOAD,
                model_name="Profile",
                metadata={"filename": filename, "size": len(raw), "ext": ext},
                ip_address=meta.get("ip_address"),
                user_agent=meta.get("user_agent"),
            )
        except Exception:
            pass

        # Persist path in AdminUser table
        try:
            from aquilia.admin.models import AdminUser
            db_user = await AdminUser.objects.filter(username=username).first()
            if db_user:
                db_user.avatar_path = avatar_url
                await db_user.save()
        except Exception:
            pass  # DB may not have the column yet (migration pending)

        # Update session identity so the change is reflected immediately
        if ctx.session and hasattr(ctx.session, "data"):
            admin_data = ctx.session.data.get("_admin_identity")
            if admin_data and isinstance(admin_data, dict):
                admin_data.setdefault("attributes", {})["avatar_path"] = avatar_url
                ctx.session.data["_admin_identity"] = admin_data

        return _flash("Profile photo updated.", "success")

    @POST("/profile/update")
    async def profile_update(self, request, ctx: RequestCtx) -> Response:
        """Update admin profile data."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/profile/")
        if csrf_denied:
            return csrf_denied

        first_name = (form_data.get("first_name") or "").strip()
        last_name  = (form_data.get("last_name")  or "").strip()
        email      = (form_data.get("email")      or "").strip()
        bio        = (form_data.get("bio")        or "").strip()
        phone      = (form_data.get("phone")      or "").strip()
        timezone   = (form_data.get("timezone")   or "UTC").strip()
        locale     = (form_data.get("locale")     or "en").strip()

        try:
            from aquilia.admin.models import AdminUser
            username = identity.get_attribute("username", identity.id)
            user = await AdminUser.objects.filter(username=username).first()
            if user:
                user.first_name = first_name
                user.last_name  = last_name
                user.email      = email
                user.bio        = bio
                user.phone      = phone
                user.timezone   = timezone
                user.locale     = locale
                await user.save()

                # Update session identity so the header reflects changes immediately
                if ctx.session and hasattr(ctx.session, "data"):
                    admin_data = ctx.session.data.get("_admin_identity")
                    if admin_data and isinstance(admin_data, dict):
                        attrs = admin_data.setdefault("attributes", {})
                        attrs["first_name"] = first_name
                        attrs["last_name"]  = last_name
                        attrs["email"]      = email
                        attrs["bio"]        = bio
                        attrs["phone"]      = phone
                        attrs["timezone"]   = timezone
                        attrs["locale"]     = locale
                        attrs["name"]       = f"{first_name} {last_name}".strip() or username
                        ctx.session.data["_admin_identity"] = admin_data

                try:
                    meta = _extract_request_meta(request)
                    self.site.audit_log.log(
                        user_id=getattr(identity, "id", ""),
                        username=_get_identity_name(identity),
                        role=str(get_admin_role(identity) or "unknown"),
                        action=AdminAction.PROFILE_UPDATE,
                        model_name="Profile",
                        changes={"first_name": first_name, "last_name": last_name, "email": email, "timezone": timezone, "locale": locale},
                        ip_address=meta.get("ip_address"),
                        user_agent=meta.get("user_agent"),
                    )
                except Exception:
                    pass

                if ctx.session and hasattr(ctx.session, "data"):
                    ctx.session.data["_admin_flash"]      = "Profile updated successfully."
                    ctx.session.data["_admin_flash_type"] = "success"
            else:
                if ctx.session and hasattr(ctx.session, "data"):
                    ctx.session.data["_admin_flash"]      = "User not found in database."
                    ctx.session.data["_admin_flash_type"] = "error"
        except Exception as e:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"]      = f"Failed: {e}"
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect("/admin/profile/")

    @POST("/profile/change-password")
    async def profile_change_password(self, request, ctx: RequestCtx) -> Response:
        """Change password for the currently logged-in admin (with validation)."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

        # CSRF validation
        csrf_denied = self._csrf_reject_redirect(request, ctx, form_data, "/admin/profile/")
        if csrf_denied:
            return csrf_denied

        current_password = form_data.get("current_password", "")
        new_password = form_data.get("new_password", "")
        confirm_password = form_data.get("confirm_password", "")

        if not current_password or not new_password:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "All password fields are required."
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/profile/")

        if new_password != confirm_password:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "New passwords do not match."
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/profile/")

        # Password complexity validation
        username = identity.get_attribute("username", identity.id)
        pw_result = self.site.security.password_validator.validate(new_password, username=username)
        if not pw_result.is_valid:
            feedback = " ".join(pw_result.feedback)
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Weak password: {feedback}"
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/profile/")

        try:
            from aquilia.admin.models import AdminUser
            username = identity.get_attribute("username", identity.id)
            user = await AdminUser.objects.filter(username=username).first()
            if user:
                if not user.check_password(current_password):
                    if ctx.session and hasattr(ctx.session, "data"):
                        ctx.session.data["_admin_flash"] = "Current password is incorrect."
                        ctx.session.data["_admin_flash_type"] = "error"
                    return _redirect("/admin/profile/")

                user.set_password(new_password)
                await user.save()

                try:
                    meta = _extract_request_meta(request)
                    self.site.audit_log.log(
                        user_id=getattr(identity, "id", ""),
                        username=_get_identity_name(identity),
                        role=str(get_admin_role(identity) or "unknown"),
                        action=AdminAction.PASSWORD_CHANGE,
                        model_name="Profile",
                        metadata={"action": "self_password_change"},
                        ip_address=meta.get("ip_address"),
                        user_agent=meta.get("user_agent"),
                    )
                except Exception:
                    pass

                if ctx.session and hasattr(ctx.session, "data"):
                    ctx.session.data["_admin_flash"] = "Password changed successfully."
                    ctx.session.data["_admin_flash_type"] = "success"
            else:
                if ctx.session and hasattr(ctx.session, "data"):
                    ctx.session.data["_admin_flash"] = "User not found in database."
                    ctx.session.data["_admin_flash_type"] = "error"
        except Exception as e:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Failed: {e}"
                ctx.session.data["_admin_flash_type"] = "error"

        return _redirect("/admin/profile/")

    # ── Admin authentication ─────────────────────────────────────────

    async def _authenticate_admin(self, username: str, password: str) -> Optional[Identity]:
        """
        Authenticate an admin user.

        Tries ORM-based AdminUser first (production), then falls back to
        environment-based superuser (development).
        """
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        # Try ORM-based AdminUser (preferred)
        try:
            from aquilia.admin.models import AdminUser
            user = await AdminUser.authenticate(username, password)
            if user is not None:
                # Log to AdminAuditEntry (ORM-backed audit trail)
                try:
                    from aquilia.admin.models import AdminAuditEntry
                    await AdminAuditEntry.create_entry(
                        action="login",
                        user=user,
                        resource_type="AdminUser",
                        resource_id=str(user.pk),
                        summary=f"Login: {username}",
                        category="auth",
                    )
                except Exception:
                    pass
                return user.to_identity()
        except Exception:
            pass

        # Development fallback: AQUILIA_ADMIN_USER / AQUILIA_ADMIN_PASSWORD
        import os
        admin_user = os.environ.get("AQUILIA_ADMIN_USER")
        admin_pass = os.environ.get("AQUILIA_ADMIN_PASSWORD")

        # Only use env fallback if explicitly configured
        if admin_user and admin_pass and username == admin_user and password == admin_pass:
            return Identity(
                id="admin-1",
                type=IdentityType.USER,
                attributes={
                    "name": "Admin",
                    "username": username,
                    "roles": ["superadmin"],
                    "is_superuser": True,
                    "is_staff": True,
                    "admin_role": "superadmin",
                },
                status=IdentityStatus.ACTIVE,
            )

        return None
