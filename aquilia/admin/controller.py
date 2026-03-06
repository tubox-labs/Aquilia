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
from .faults import AdminAuthorizationFault
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
    render_admin_users_page,
    render_profile_page,
    render_error_page,
    render_disabled_page,
    render_query_inspector_page,
    render_tasks_page,
    render_errors_page,
    render_testing_page,
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

    # ── Dashboard ────────────────────────────────────────────────────

    @GET("/")
    async def dashboard(self, request, ctx: RequestCtx) -> Response:
        """Admin dashboard -- model overview with stats."""
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
        try:
            error_stats = self.site.get_error_tracker_data()
        except Exception:
            pass
        try:
            tasks_data = await self.site.get_tasks_data()
            tasks_stats = tasks_data.get("stats", {})
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
        )
        return _html_response(html)

    # ── Login / Logout ───────────────────────────────────────────────

    @GET("/login")
    async def login_page(self, request, ctx: RequestCtx) -> Response:
        """Render admin login page."""
        # Already logged in?
        identity = _get_identity(ctx)
        if identity and get_admin_role(identity) is not None:
            return _redirect("/admin/")

        return _html_response(render_login_page())

    @POST("/login")
    async def login_submit(self, request, ctx: RequestCtx) -> Response:
        """
        Process admin login.

        Validates credentials against auth system and creates
        an admin session.
        """
        form_data = await _parse_form(ctx)

        username = form_data.get("username", "")
        password = form_data.get("password", "")

        if not username or not password:
            return _html_response(render_login_page(error="Username and password required"), 400)

        # Authenticate via built-in admin auth
        # In production, this integrates with AuthManager
        identity = await self._authenticate_admin(username, password)

        if identity is None:
            # Log failed attempt -- persisted to DB via alog
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
            return _html_response(render_login_page(error="Invalid credentials"), 401)

        # Store identity in session
        if ctx.session and hasattr(ctx.session, "data"):
            ctx.session.data["_admin_identity"] = identity.to_dict()

        # Log successful login -- persisted to DB
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

    @GET("/logout")
    async def logout(self, request, ctx: RequestCtx) -> Response:
        """Logout and clear admin session."""
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

        return _redirect("/admin/login")

    # Reserved names -- system pages that must not be treated as model names
    _SYSTEM_PAGES = frozenset({
        "login", "logout", "orm", "build", "migrations",
        "config", "workspace", "permissions", "audit", "monitoring",
        "admin-users", "profile", "containers", "pods",
    })

    # ── List View ────────────────────────────────────────────────────

    @GET("/{model}/")
    async def list_view(self, request, ctx: RequestCtx) -> Response:
        """List records for a model with search and pagination."""
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

        try:
            data = await self.site.list_records(
                model,
                page=page,
                search=search,
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

        # Get actions for the model
        try:
            admin_obj = self.site.get_model_admin(model)
            data["actions"] = admin_obj.get_actions()
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

        try:
            record = await self.site.create_record(model, form_data, identity=identity)
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

        try:
            await self.site.update_record(model, pk, form_data, identity=identity)

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
        """Export model data as CSV or JSON."""
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

        try:
            data = await self.site.list_records(
                model, page=page, search=search, identity=identity,
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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("orm"):
            return self._module_disabled_response("ORM Models", identity)

        self._ensure_initialized()

        app_list = self.site.get_app_list(identity)
        stats = await self.site.get_dashboard_stats()
        model_schema = self.site.get_model_schema()
        orm_metadata = self.site.get_orm_metadata()

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("build"):
            return self._module_disabled_response("Build", identity)

        self._ensure_initialized()

        build_data = self.site.get_build_info()
        app_list = self.site.get_app_list(identity)

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("migrations"):
            return self._module_disabled_response("Migrations", identity)

        self._ensure_initialized()

        migrations = self.site.get_migrations_data()
        app_list = self.site.get_app_list(identity)

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("config"):
            return self._module_disabled_response("Configuration", identity)

        self._ensure_initialized()

        config_data = self.site.get_config_data()
        app_list = self.site.get_app_list(identity)

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("workspace"):
            return self._module_disabled_response("Workspace", identity)

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("permissions"):
            return self._module_disabled_response("Permissions", identity)

        self._ensure_initialized()

        # Check for flash message from permissions update
        flash = ""
        flash_type = "success"
        if ctx.session and hasattr(ctx.session, "data"):
            flash = ctx.session.data.pop("_admin_flash", "")
            flash_type = ctx.session.data.pop("_admin_flash_type", "success")

        perms_data = self.site.get_permissions_data(identity)
        app_list = self.site.get_app_list(identity)

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

        result = self.site.update_permissions(form_data, identity)

        # Flash the result message
        if ctx.session and hasattr(ctx.session, "data"):
            ctx.session.data["_admin_flash"] = result.get("message", "Permissions updated.")
            ctx.session.data["_admin_flash_type"] = result.get("status", "success")

        return _redirect("/admin/permissions/")

    # ── Audit Log ────────────────────────────────────────────────────

    @GET("/audit/")
    async def audit_view(self, request, ctx: RequestCtx) -> Response:
        """View the admin audit log -- reads from DB if available."""
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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("monitoring"):
            return self._module_disabled_response("Monitoring", identity)

        self._ensure_initialized()

        monitoring_data = self.site.get_monitoring_data()
        app_list = self.site.get_app_list(identity)

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("containers"):
            return self._module_disabled_response("Containers", identity)

        self._ensure_initialized()

        containers_data = self.site.get_containers_data()
        app_list = self.site.get_app_list(identity)

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
        container_id = form_data.get("container_id", "")
        action = form_data.get("action", "")
        run_params = form_data.get("run_params", "")

        if not container_id or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_container_action(container_id, action, run_params=run_params)
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
        image_id = form_data.get("image_id", "")
        action = form_data.get("action", "")

        if not image_id or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing image_id or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_image_action(image_id, action)
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
        action = form_data.get("action", "")

        if not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_compose_action(action)
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
        name = form_data.get("name", "")
        action = form_data.get("action", "")

        if not name or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing name or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_volume_action(name, action)
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
        network_id = form_data.get("network_id", "")
        action = form_data.get("action", "")

        if not network_id or not action:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing network_id or action"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )

        result = self.site.execute_network_action(network_id, action)
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
        target = form_data.get("target", "")
        if not target:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing target"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_docker_prune(target)
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
        container_id = form_data.get("container_id", "")
        command = form_data.get("command", "")
        if not container_id or not command:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id or command"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_container_exec(container_id, command)
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
        source = form_data.get("source", "")
        target = form_data.get("target", "")
        if not source or not target:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing source or target"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_image_tag(source, target)
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
        container_id = form_data.get("container_id", "")
        if not container_id:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing container_id"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.execute_container_export(container_id)
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
        name = form_data.get("name", "")
        driver = form_data.get("driver", "local")
        labels = form_data.get("labels", "")
        if not name:
            return Response(
                content=_json.dumps({"success": False, "error": "Missing volume name"}).encode(),
                status=400, headers={"content-type": "application/json"},
            )
        result = self.site.create_docker_volume(name, driver, labels)
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
        tag = form_data.get("tag", "")
        no_cache = form_data.get("no_cache", "") in ("1", "true", "on")
        build_args = form_data.get("build_args", "")
        target = form_data.get("target", "")
        result = self.site.execute_docker_build(
            tag=tag, no_cache=no_cache, build_args=build_args, target=target,
        )
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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("pods"):
            return self._module_disabled_response("Pods", identity)

        self._ensure_initialized()

        pods_data = self.site.get_pods_data()
        app_list = self.site.get_app_list(identity)

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

    # ── Query Inspector Page ─────────────────────────────────────────

    @GET("/query-inspector/")
    async def query_inspector_view(self, request, ctx: RequestCtx) -> Response:
        """Live query inspector -- ORM→SQL, timing, EXPLAIN, N+1 detection."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("query_inspector"):
            return self._module_disabled_response("Query Inspector", identity)

        self._ensure_initialized()

        query_data = self.site.get_query_inspector_data()
        app_list = self.site.get_app_list(identity)

        html = render_query_inspector_page(
            query_data=query_data,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            identity_avatar=_get_identity_avatar(identity),
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

    # ── Background Tasks Page ────────────────────────────────────────

    @GET("/tasks/")
    async def tasks_view(self, request, ctx: RequestCtx) -> Response:
        """Background task monitor -- job queue, workers, retries."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("tasks"):
            return self._module_disabled_response("Background Tasks", identity)

        self._ensure_initialized()

        tasks_data = await self.site.get_tasks_data()
        app_list = self.site.get_app_list(identity)

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("errors"):
            return self._module_disabled_response("Error Monitoring", identity)

        self._ensure_initialized()

        errors_data = self.site.get_error_tracker_data()
        app_list = self.site.get_app_list(identity)

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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("testing"):
            return self._module_disabled_response("Testing Framework", identity)

        self._ensure_initialized()

        testing_data = self.site.get_testing_data()
        app_list = self.site.get_app_list(identity)

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

    # ── Admin Users Management ───────────────────────────────────────

    @GET("/admin-users/")
    async def admin_users_view(self, request, ctx: RequestCtx) -> Response:
        """List and manage admin users with hierarchy."""
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
        """Create a new admin user."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not has_admin_permission(identity, AdminPermission.USER_MANAGE):
            return _redirect("/admin/")

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

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

        if len(password) < 8:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "Password must be at least 8 characters."
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
                self.site.audit_log.log(
                    AdminAction.CREATE,
                    identity=identity,
                    model="AdminUser",
                    object_repr=username,
                    **_extract_request_meta(request),
                )
            except Exception:
                pass

            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Admin '{username}' created successfully as {role}."
                ctx.session.data["_admin_flash_type"] = "success"
        except Exception as e:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = f"Failed to create admin: {e}"
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
        user_id = form_data.get("user_id", "")

        try:
            from aquilia.admin.models import AdminUser
            user = await AdminUser.objects.get(pk=user_id)
            user.is_active = not user.is_active
            await user.save()

            action = "activated" if user.is_active else "deactivated"
            try:
                self.site.audit_log.log(
                    AdminAction.UPDATE,
                    identity=identity,
                    model="AdminUser",
                    object_repr=f"{user.username} {action}",
                    **_extract_request_meta(request),
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
        """Reset password for an admin user."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not has_admin_permission(identity, AdminPermission.USER_MANAGE):
            return _redirect("/admin/")

        self._ensure_initialized()
        form_data = await _parse_form(ctx)
        user_id = form_data.get("user_id", "")
        new_password = form_data.get("new_password", "")

        if not new_password or len(new_password) < 8:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "Password must be at least 8 characters."
                ctx.session.data["_admin_flash_type"] = "error"
            return _redirect("/admin/admin-users/")

        try:
            from aquilia.admin.models import AdminUser
            user = await AdminUser.objects.get(pk=user_id)
            user.set_password(new_password)
            await user.save()

            try:
                self.site.audit_log.log(
                    AdminAction.UPDATE,
                    identity=identity,
                    model="AdminUser",
                    object_repr=f"Password reset: {user.username}",
                    **_extract_request_meta(request),
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
                self.site.audit_log.log(
                    AdminAction.DELETE,
                    identity=identity,
                    model="AdminUser",
                    object_repr=f"Deleted: {username}",
                    **_extract_request_meta(request),
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
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not self.site.admin_config.is_module_enabled("profile"):
            return self._module_disabled_response("Profile", identity)

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
        """Change password for the currently logged-in admin."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()
        form_data = await _parse_form(ctx)

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

        if len(new_password) < 8:
            if ctx.session and hasattr(ctx.session, "data"):
                ctx.session.data["_admin_flash"] = "Password must be at least 8 characters."
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
                # Log to AdminLogEntry (ORM-backed audit trail)
                try:
                    from aquilia.admin.models import AdminLogEntry, ContentType
                    await AdminLogEntry.log_action(
                        user_id=user.pk,
                        content_type_id=None,
                        object_id=None,
                        object_repr=f"Login: {username}",
                        action_flag=AdminLogEntry.ADDITION,
                        change_message='[{"action": "login"}]',
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
