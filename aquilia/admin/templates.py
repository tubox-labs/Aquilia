"""
AquilAdmin -- Template Renderer.

Renders admin HTML pages using the Aquilia TemplateEngine from
``aquilia/templates/``.  Templates live in ``aquilia/admin/templates/``.
Falls back to a plain Jinja2 environment when the full TemplateEngine
cannot be initialised, and to inline Python string templates when Jinja2
is not installed at all -- ensuring the admin module stays importable in
minimal environments.

Design system: matches aqdocx exactly.
- Dark/light mode with Aquilia green accent (#22c55e / #16a34a)
- Outfit font family
- Glass morphism cards
- Responsive layout
"""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Template engine setup ────────────────────────────────────────────────────

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Try to use Aquilia's own TemplateEngine first, then fall back to raw Jinja2.
_admin_engine = None
_HAS_JINJA2 = False
_jinja_env = None  # type: ignore[assignment]

try:
    from aquilia.templates import TemplateEngine, TemplateLoader

    _admin_loader = TemplateLoader(search_paths=[str(_TEMPLATES_DIR)])
    _admin_engine = TemplateEngine(
        _admin_loader,
        sandbox=False,          # Admin templates are trusted first-party code
        autoescape=True,
        enable_async=False,     # Admin renders synchronously within event loop
    )
    # Enable trim_blocks / lstrip_blocks on the underlying Jinja2 env so
    # that admin templates render cleanly without extra whitespace.
    _admin_engine.env.trim_blocks = True
    _admin_engine.env.lstrip_blocks = True
    _HAS_JINJA2 = True
except Exception:
    # Fallback: create a plain Jinja2 Environment (no TemplateEngine)
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        _jinja_env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        _HAS_JINJA2 = True
    except ImportError:
        _jinja_env = None  # type: ignore[assignment]
        _HAS_JINJA2 = False


def _render_template(template_name: str, **ctx: Any) -> str:
    """Render a Jinja2 template by name.

    Uses Aquilia TemplateEngine when available, plain Jinja2 otherwise.
    Raises RuntimeError when neither is installed.

    Automatically injects ``admin_config`` from the AdminSite singleton
    if not already present in the context, so sidebar and templates can
    conditionally render modules.
    """
    if "admin_config" not in ctx:
        try:
            from .site import AdminSite
            site = AdminSite.default()
            ctx["admin_config"] = site.admin_config.to_dict()
        except Exception:
            ctx["admin_config"] = {}

    if _admin_engine is not None:
        # Synchronous render via the framework engine
        return _admin_engine.render_sync(template_name, ctx)
    if _jinja_env is not None:
        tpl = _jinja_env.get_template(template_name)
        return tpl.render(**ctx)
    raise RuntimeError(
        "Jinja2 is required for admin templates.  "
        "Install it with: pip install Jinja2"
    )


def _get_jinja_env():
    """Return the active Jinja2 Environment.

    Prefers the TemplateEngine's underlying env; falls back to the raw
    _jinja_env.  Used by tests that need direct template access.
    """
    if _admin_engine is not None:
        return _admin_engine.env
    return _jinja_env


# ── CSS Design System (kept in Python for backward compat imports) ───────

ADMIN_CSS = ""
try:
    _css_path = _TEMPLATES_DIR / "partials" / "css.html"
    if _css_path.exists():
        ADMIN_CSS = _css_path.read_text(encoding="utf-8")
except Exception:
    pass


# ── Page Renderers ───────────────────────────────────────────────────────────
#
# These public functions are the stable API consumed by controller.py and
# tests.  When Jinja2 is available they delegate to the .html templates;
# otherwise they fall back to simple inline HTML.
# ─────────────────────────────────────────────────────────────────────────────


def render_login_page(
    error: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the admin login page."""
    if _HAS_JINJA2:
        return _render_template(
            "login.html",
            error=error,
            site_title=site_title,
            url_prefix=url_prefix,
        )
    # Inline fallback
    return _fallback_login(error, site_title=site_title, url_prefix=url_prefix)


def render_dashboard(
    app_list: List[Dict[str, Any]],
    stats: Dict[str, Any],
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the admin dashboard."""
    model_counts = stats.get("model_counts", {})
    total_models = stats.get("total_models", 0)
    total_records = sum(v for v in model_counts.values() if isinstance(v, int))
    recent_actions = stats.get("recent_actions", [])

    if _HAS_JINJA2:
        return _render_template(
            "dashboard.html",
            app_list=app_list,
            model_counts=model_counts,
            total_models=total_models,
            total_records=total_records,
            recent_actions=recent_actions,
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Dashboard",
            active_page="dashboard",
        )
    return _fallback_dashboard(
        app_list, stats, identity_name,
        site_title=site_title, url_prefix=url_prefix,
    )


def render_list_view(
    data: Dict[str, Any],
    app_list: List[Dict[str, Any]],
    identity_name: str = "Admin",
    flash: str = "",
    flash_type: str = "success",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the model list view with table, search, pagination."""
    model_name = data.get("model_name", "")
    verbose_name = data.get("verbose_name", model_name)
    verbose_name_plural = data.get("verbose_name_plural", model_name)

    if _HAS_JINJA2:
        return _render_template(
            "list.html",
            model_name=model_name,
            verbose_name=verbose_name,
            verbose_name_plural=verbose_name_plural,
            rows=data.get("rows", []),
            list_display=data.get("list_display", []),
            total=data.get("total", 0),
            page=data.get("page", 1),
            total_pages=data.get("total_pages", 1),
            search=data.get("search", ""),
            actions=data.get("actions", {}),
            app_list=app_list,
            active_page="",
            active_model=model_name.lower() if model_name else "",
            identity_name=identity_name,
            flash=flash,
            flash_type=flash_type,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title=verbose_name_plural,
        )
    return _fallback_list(
        data, app_list, identity_name, flash, flash_type,
        site_title=site_title, url_prefix=url_prefix,
    )


def render_form_view(
    data: Dict[str, Any],
    app_list: List[Dict[str, Any]],
    identity_name: str = "Admin",
    is_create: bool = False,
    flash: str = "",
    flash_type: str = "success",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the add/edit form view."""
    model_name = data.get("model_name", "")
    verbose_name = data.get("verbose_name", model_name)
    pk = data.get("pk", "")

    if _HAS_JINJA2:
        return _render_template(
            "form.html",
            model_name=model_name,
            verbose_name=verbose_name,
            pk=pk,
            fields=data.get("fields", []),
            fieldsets=data.get("fieldsets", []),
            can_delete=data.get("can_delete", False) and not is_create,
            is_create=is_create,
            app_list=app_list,
            active_page="",
            active_model=model_name.lower() if model_name else "",
            identity_name=identity_name,
            flash=flash,
            flash_type=flash_type,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title=f"{'Add' if is_create else 'Edit'} {verbose_name}" + (f" #{pk}" if not is_create else ""),
        )
    return _fallback_form(
        data, app_list, identity_name, is_create, flash, flash_type,
        site_title=site_title, url_prefix=url_prefix,
    )


def render_audit_page(
    entries: List[Dict[str, Any]],
    app_list: List[Dict[str, Any]],
    identity_name: str = "Admin",
    total: int = 0,
    page: int = 1,
    per_page: int = 50,
    total_pages: int = 1,
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the audit log page."""
    if _HAS_JINJA2:
        return _render_template(
            "audit.html",
            entries=entries,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            app_list=app_list,
            active_page="audit",
            active_model="_audit",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Audit Log",
        )
    return _fallback_audit(
        entries, app_list, identity_name, total,
        site_title=site_title, url_prefix=url_prefix,
    )


def render_orm_page(
    app_list: List[Dict[str, Any]],
    model_counts: Dict[str, Any],
    identity_name: str = "Admin",
    model_schema: Optional[List[Dict[str, Any]]] = None,
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the ORM models page with schema inspector and relation graph."""
    total_models = sum(len(a.get("models", [])) for a in app_list)
    total_records = sum(v for v in model_counts.values() if isinstance(v, int))

    # Build relation edges and index stats from schema
    schema = model_schema or []
    all_relations: List[Dict[str, Any]] = []
    total_indexes = 0
    total_fk = 0
    total_m2m = 0
    for m in schema:
        total_indexes += len(m.get("indexes", []))
        for r in m.get("relations", []):
            all_relations.append(r)
            if r["type"] == "FK":
                total_fk += 1
            elif r["type"] == "M2M":
                total_m2m += 1

    if _HAS_JINJA2:
        return _render_template(
            "orm.html",
            app_list=app_list,
            model_counts=model_counts,
            total_models=total_models,
            total_records=total_records,
            model_schema=schema,
            all_relations=all_relations,
            total_indexes=total_indexes,
            total_fk=total_fk,
            total_m2m=total_m2m,
            active_page="orm",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="ORM Models",
        )
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>ORM Models -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>ORM Models</h1><p>{total_models} models registered</p></div></body></html>"""


def render_build_page(
    build_info: Dict[str, Any],
    artifacts: List[Dict[str, Any]],
    pipeline_phases: List[Dict[str, Any]],
    build_log: str = "",
    build_files: Optional[List[Dict[str, Any]]] = None,
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the build page with Crous artifacts and pipeline status."""
    if _HAS_JINJA2:
        return _render_template(
            "build.html",
            build_info=build_info,
            artifacts=artifacts,
            pipeline_phases=pipeline_phases,
            build_log=build_log,
            build_files=build_files or [],
            app_list=app_list or [],
            active_page="build",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Build",
        )
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Build -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Build</h1><p>{len(artifacts)} artifacts</p></div></body></html>"""


def render_migrations_page(
    migrations: List[Dict[str, Any]],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the migrations page with syntax highlighted source."""
    total_operations = sum(m.get("operations_count", 0) for m in migrations)
    total_models_affected = len(set(
        model for m in migrations for model in m.get("models", [])
    ))

    if _HAS_JINJA2:
        return _render_template(
            "migrations.html",
            migrations=migrations,
            total_operations=total_operations,
            total_models_affected=total_models_affected,
            app_list=app_list or [],
            active_page="migrations",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Migrations",
        )
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Migrations -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Migrations</h1><p>{len(migrations)} migrations</p></div></body></html>"""


def render_config_page(
    config_files: List[Dict[str, Any]],
    workspace_info: Optional[Dict[str, Any]] = None,
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the configuration page with YAML file contents."""
    if _HAS_JINJA2:
        return _render_template(
            "config.html",
            config_files=config_files,
            workspace_info=workspace_info or {},
            app_list=app_list or [],
            active_page="config",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Configuration",
        )
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Configuration -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Configuration</h1><p>{len(config_files)} config files</p></div></body></html>"""


def render_workspace_page(
    workspace: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the workspace monitoring page."""
    if _HAS_JINJA2:
        return _render_template(
            "workspace.html",
            workspace=workspace,
            app_list=app_list or [],
            active_page="workspace",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Workspace",
        )
    mods = workspace.get("modules", [])
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Workspace -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Workspace</h1><p>{len(mods)} modules</p></div></body></html>"""


def render_permissions_page(
    roles: List[Dict[str, Any]],
    all_permissions: List[str],
    model_permissions: List[Dict[str, Any]],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    flash: str = "",
    flash_type: str = "success",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the permissions page with role matrix."""
    if _HAS_JINJA2:
        return _render_template(
            "permissions.html",
            roles=roles,
            all_permissions=all_permissions,
            model_permissions=model_permissions,
            app_list=app_list or [],
            active_page="permissions",
            identity_name=identity_name,
            flash=flash,
            flash_type=flash_type,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Permissions",
        )
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Permissions -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Permissions</h1><p>{len(roles)} roles</p></div></body></html>"""


def render_monitoring_page(
    monitoring: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the application monitoring page with system metrics and charts."""
    if _HAS_JINJA2:
        return _render_template(
            "monitoring.html",
            monitoring=monitoring,
            app_list=app_list or [],
            active_page="monitoring",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Monitoring",
        )
    cpu_pct = monitoring.get("cpu", {}).get("percent", 0)
    mem_pct = monitoring.get("memory", {}).get("percent", 0)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Monitoring -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Monitoring</h1>
<p>CPU: {cpu_pct}% · Memory: {mem_pct}%</p></div></body></html>"""


def render_admin_users_page(
    users: List[Dict[str, Any]],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    flash: str = "",
    flash_type: str = "success",
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the admin-users management page with hierarchy, roles, and creation form."""
    if _HAS_JINJA2:
        return _render_template(
            "admin_users.html",
            users=users,
            app_list=app_list or [],
            active_page="admin-users",
            identity_name=identity_name,
            flash=flash,
            flash_type=flash_type,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Admin Users",
        )
    total = len(users)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Admin Users -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Admin Users</h1><p>{total} admin accounts</p></div></body></html>"""


def render_profile_page(
    user: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    flash: str = "",
    flash_type: str = "success",
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the admin profile management page."""
    if _HAS_JINJA2:
        return _render_template(
            "profile.html",
            user=user,
            app_list=app_list or [],
            active_page="profile",
            identity_name=identity_name,
            flash=flash,
            flash_type=flash_type,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Profile",
        )
    uname = html.escape(user.get("username", "Admin"))
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Profile -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Profile</h1><p>{uname}</p></div></body></html>"""


def render_error_page(
    status: int = 404,
    title: str = "Not Found",
    message: str = "",
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render a styled admin error page (404, 403, 400, etc.).

    Instead of returning raw text for errors, this renders the error
    inside the full admin layout with sidebar, header, and navigation
    so the user stays in-context and can easily navigate back.
    """
    if _HAS_JINJA2:
        return _render_template(
            "error.html",
            status=status,
            title=title,
            message=message,
            app_list=app_list or [],
            active_page="",
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title=title,
        )
    esc_title = html.escape(title)
    esc_msg = html.escape(message) if message else ""
    msg_block = f'<p style="margin-top:12px;color:#a1a1aa;font-size:.9rem">{esc_msg}</p>' if esc_msg else ""
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>{status} {esc_title} -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:48px;text-align:center">
<div style="font-size:6rem;font-weight:800;opacity:.15;color:#22c55e">{status}</div>
<h1>{esc_title}</h1>{msg_block}
<p style="margin-top:24px"><a href="{url_prefix}/" style="color:#22c55e">← Back to Dashboard</a></p>
</div></body></html>"""


def render_disabled_page(
    module_name: str,
    builder_hint: str = "",
    flat_hint: str = "",
    icon_key: str = "",
    description: str = "",
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render a beautiful blurred overlay page for disabled admin modules.

    Shows the page layout with a frosted-glass overlay explaining that
    the module is disabled and providing the exact config snippet needed
    to enable it.  Much more helpful than a flat 404.
    """
    # Map icon_key to Lucide icon classes
    _icon_map = {
        "monitoring": "icon-activity",
        "audit": "icon-scroll-text",
        "orm": "icon-database",
        "build": "icon-package",
        "migrations": "icon-git-branch",
        "config": "icon-settings",
        "workspace": "icon-layout-template",
        "permissions": "icon-shield",
        "admin_users": "icon-users",
        "profile": "icon-user",
    }
    icon_class = _icon_map.get(icon_key, "icon-lock")

    if _HAS_JINJA2:
        return _render_template(
            "disabled.html",
            module_name=module_name,
            builder_hint=builder_hint,
            flat_hint=flat_hint,
            icon_key=icon_key,
            icon_class=icon_class,
            description=description,
            app_list=app_list or [],
            active_page=icon_key,
            identity_name=identity_name,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title=f"{module_name} (Disabled)",
        )
    # Inline fallback
    esc_name = html.escape(module_name)
    esc_builder = html.escape(builder_hint)
    esc_flat = html.escape(flat_hint)
    esc_desc = html.escape(description)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>{esc_name} (Disabled) -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:48px;text-align:center">
<div style="font-size:4rem;opacity:.15;margin-bottom:16px;">⏸</div>
<h1>{esc_name} -- Disabled</h1>
<p style="color:#a1a1aa;margin:12px 0;">{esc_desc}</p>
<div style="background:#18181b;border:1px solid #27272a;border-radius:8px;padding:16px;margin:24px auto;max-width:500px;text-align:left;">
<code style="color:#22c55e;font-size:.85rem;">{esc_builder}</code><br>
<span style="color:#71717a;font-size:.75rem;">or: {esc_flat}</span>
</div>
<a href="{url_prefix}/" style="color:#22c55e">← Back to Dashboard</a>
</div></body></html>"""


# ═══════════════════════════════════════════════════════════════════════════
# Inline fallbacks (when Jinja2 is not installed)
# ═══════════════════════════════════════════════════════════════════════════

_FALLBACK_CSS = """
:root{--bg-primary:#02040a;--bg-card:#09090b;--bg-input:#18181b;--border-color:#27272a;
--accent:#22c55e;--accent-hover:#16a34a;--accent-glow:rgba(34,197,94,.3);
--text-primary:#e4e4e7;--text-secondary:#a1a1aa;--text-muted:#71717a;--danger:#ef4444;
--font-sans:"Outfit",system-ui,sans-serif}
[data-theme="light"]{--bg-primary:#fafafa;--bg-card:#fff;--bg-input:#fff;--border-color:#e4e4e7;
--accent:#16a34a;--text-primary:#18181b;--text-secondary:#52525b}
*{margin:0;padding:0;box-sizing:border-box}body{font-family:var(--font-sans);background:var(--bg-primary);
color:var(--text-primary);min-height:100vh}a{color:var(--accent);text-decoration:none}
.card{background:var(--bg-card);border:1px solid var(--border-color);border-radius:12px;padding:20px}
.btn{padding:8px 16px;border-radius:8px;font-size:.875rem;cursor:pointer;border:none;font-family:var(--font-sans)}
.btn-primary{background:var(--accent);color:#fff}.form-input{width:100%;padding:10px 14px;border-radius:8px;
background:var(--bg-input);color:var(--text-primary);border:1px solid var(--border-color);font-family:var(--font-sans)}
.flash{padding:12px;border-radius:8px;margin-bottom:16px;font-size:.875rem}
.flash-error{background:rgba(239,68,68,.15);color:var(--danger)}
.login-container{min-height:100vh;display:flex;align-items:center;justify-content:center}
.login-card{width:100%;max-width:400px}.form-group{margin-bottom:16px}
.form-label{display:block;font-size:.8rem;margin-bottom:6px;color:var(--text-secondary)}
"""


def _fallback_login(error: str = "", **kw: Any) -> str:
    e = f'<div class="flash flash-error">{html.escape(error)}</div>' if error else ""
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Sign in to the Aquilia Admin dashboard.">
<meta name="robots" content="noindex, nofollow"><meta name="theme-color" content="#22c55e">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>Login -- Aquilia Admin</title>
<link rel="icon" type="image/x-icon" href="/static/favicon.ico">
<style>{_FALLBACK_CSS}</style></head><body>
<div class="login-container"><div class="card login-card">
<div style="text-align:center;margin-bottom:32px">
<div style="margin-bottom:12px"><img src="/static/logo.png" alt="Aquilia" style="width:64px;height:64px;object-fit:contain"></div>
<h1 style="font-size:2rem;font-weight:800">Aquilia Admin</h1>
<p style="color:var(--text-muted);font-size:.85rem;margin-top:8px">Sign in to access the admin dashboard</p></div>
{e}<form method="POST" action="/admin/login">
<div class="form-group"><label class="form-label">Username</label>
<input type="text" name="username" class="form-input" required autofocus></div>
<div class="form-group"><label class="form-label">Password</label>
<input type="password" name="password" class="form-input" required></div>
<button type="submit" class="btn btn-primary" style="width:100%">Sign In</button>
</form></div></div><script>var s=localStorage.getItem('aquilia-admin-theme');
if(s)document.documentElement.setAttribute('data-theme',s);</script></body></html>"""


def _fallback_dashboard(app_list: list, stats: dict, identity_name: str = "Admin", **kw: Any) -> str:
    total_models = stats.get("total_models", 0)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Dashboard -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Dashboard</h1><p>{total_models} models registered</p>
<p>Logged in as {html.escape(identity_name)}</p></div></body></html>"""


def _fallback_list(data: dict, app_list: list, identity_name: str = "Admin",
                   flash: str = "", flash_type: str = "success", **kw: Any) -> str:
    model = data.get("model_name", "Model")
    total = data.get("total", 0)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>{html.escape(model)} -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>{html.escape(model)}</h1><p>{total} records</p></div></body></html>"""


def _fallback_form(data: dict, app_list: list, identity_name: str = "Admin",
                   is_create: bool = False, flash: str = "", flash_type: str = "success", **kw: Any) -> str:
    model = data.get("model_name", "Model")
    title = f"{'Add' if is_create else 'Edit'} {model}"
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>{html.escape(title)} -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>{html.escape(title)}</h1><p>Form view (install Jinja2 for full UI)</p></div></body></html>"""


def _fallback_audit(entries: list, app_list: list, identity_name: str = "Admin",
                    total: int = 0, **kw: Any) -> str:
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Audit Log -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Audit Log</h1><p>{total} entries</p></div></body></html>"""
