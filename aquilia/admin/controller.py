"""
AquilAdmin — Admin Controller.

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


def _require_identity(ctx: RequestCtx) -> tuple:
    """
    Extract and verify admin identity from request context.

    Combines the recurring pattern of:
    1. ``_get_identity(ctx)``
    2. ``require_admin_access(identity)``
    3. Redirect to ``/admin/login`` on failure

    Returns:
        ``(identity, None)`` on success — caller uses ``identity``.
        ``(None, redirect_response)`` on failure — caller returns the response.
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

    # ── Dashboard ────────────────────────────────────────────────────

    @GET("/")
    async def dashboard(self, request, ctx: RequestCtx) -> Response:
        """Admin dashboard — model overview with stats."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        app_list = self.site.get_app_list(identity)
        stats = await self.site.get_dashboard_stats()

        html = render_dashboard(
            app_list=app_list,
            stats=stats,
            identity_name=_get_identity_name(identity),
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
            # Log failed attempt — persisted to DB via alog
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

        # Log successful login — persisted to DB
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

    # Reserved names — system pages that must not be treated as model names
    _SYSTEM_PAGES = frozenset({
        "login", "logout", "orm", "build", "migrations",
        "config", "workspace", "permissions", "audit",
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
            return _html_response(
                render_login_page(error=f"Error: {e}"),
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
            return _html_response(str(e), 404)

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
                return _html_response(str(e), 400)

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
            return _html_response(str(e), 404)

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
            # Redirect back to edit page with success message
            return _redirect(f"/admin/{model.lower()}/")
        except Exception as e:
            # Re-render form with error
            try:
                data = await self.site.get_record(model, pk, identity=identity)
            except Exception:
                return _html_response(str(e), 400)

            app_list = self.site.get_app_list(identity)
            html = render_form_view(
                data=data,
                app_list=app_list,
                identity_name=_get_identity_name(identity),
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
            return _html_response(str(e), 404)

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
        """ORM models overview — all registered models with counts."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        app_list = self.site.get_app_list(identity)
        stats = await self.site.get_dashboard_stats()
        model_schema = self.site.get_model_schema()

        html = render_orm_page(
            app_list=app_list,
            model_counts=stats.get("model_counts", {}),
            identity_name=_get_identity_name(identity),
            model_schema=model_schema,
        )
        return _html_response(html)

    # ── Build Page ───────────────────────────────────────────────────

    @GET("/build/")
    async def build_view(self, request, ctx: RequestCtx) -> Response:
        """Build page — Crous artifacts and pipeline status."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

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
        )
        return _html_response(html)

    # ── Migrations Page ──────────────────────────────────────────────

    @GET("/migrations/")
    async def migrations_view(self, request, ctx: RequestCtx) -> Response:
        """Migrations page — list all migrations with syntax-highlighted source."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        migrations = self.site.get_migrations_data()
        app_list = self.site.get_app_list(identity)

        html = render_migrations_page(
            migrations=migrations,
            app_list=app_list,
            identity_name=_get_identity_name(identity),
        )
        return _html_response(html)

    # ── Config Page ──────────────────────────────────────────────────

    @GET("/config/")
    async def config_view(self, request, ctx: RequestCtx) -> Response:
        """Configuration page — show workspace YAML configuration."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        self._ensure_initialized()

        config_data = self.site.get_config_data()
        app_list = self.site.get_app_list(identity)

        html = render_config_page(
            config_files=config_data.get("files", []),
            workspace_info=config_data.get("workspace", None),
            app_list=app_list,
            identity_name=_get_identity_name(identity),
        )
        return _html_response(html)

    # ── Workspace Page ───────────────────────────────────────────────

    @GET("/workspace/")
    async def workspace_view(self, request, ctx: RequestCtx) -> Response:
        """Workspace page — monitor modules, manifests & project metadata."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

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
        )
        return _html_response(html)

    # ── Permissions Page ─────────────────────────────────────────────

    @GET("/permissions/")
    async def permissions_view(self, request, ctx: RequestCtx) -> Response:
        """Permissions page — role matrix and per-model access."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

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
        """View the admin audit log — reads from DB if available."""
        identity, denied = _require_identity(ctx)
        if denied:
            return denied

        if not has_admin_permission(identity, AdminPermission.AUDIT_VIEW):
            return _redirect("/admin/")

        self._ensure_initialized()

        # Use async DB-backed query so persisted entries survive restarts
        audit = self.site.audit_log
        if hasattr(audit, "get_entries_async"):
            entries = await audit.get_entries_async(limit=200)
            total = await audit.count_async()
        else:
            entries = audit.get_entries(limit=200)
            total = audit.count()

        app_list = self.site.get_app_list(identity)
        html = render_audit_page(
            entries=[e.to_dict() for e in entries],
            app_list=app_list,
            identity_name=_get_identity_name(identity),
            total=total,
        )
        return _html_response(html)

    # ── Admin authentication ─────────────────────────────────────────

    async def _authenticate_admin(self, username: str, password: str) -> Optional[Identity]:
        """
        Authenticate an admin user.

        Tries ORM-based AdminUser first (production), then falls back to
        environment-based superuser (development).
        """
        from aquilia.auth.core import Identity, IdentityType, IdentityStatus

        # Try ORM-based AdminUser (preferred — Django-like)
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
