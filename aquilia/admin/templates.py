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


class _AttrDict(dict):
    """A dict subclass that also supports attribute access.

    This lets Jinja2 templates use both ``obj.key`` and ``obj['key']``
    interchangeably, and preserves dict methods like ``.items()``,
    ``.keys()``, and ``.values()`` so loops such as
    ``{% for k, v in obj.items() %}`` continue to work.
    """

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name) from None


def _dict_to_ns(obj: Any) -> Any:
    """Recursively convert plain dicts to ``_AttrDict`` so that Jinja2
    attribute access (``monitoring.network.connections_by_status``) works
    correctly on nested data structures while preserving dict methods
    like ``.items()`` needed for ``{% for k, v in d.items() %}``."""
    if isinstance(obj, dict):
        return _AttrDict({k: _dict_to_ns(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_dict_to_ns(i) for i in obj]
    return obj

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

    # Provide a default so base.html / sidebar can always reference it
    ctx.setdefault("identity_avatar", "")

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
    identity_avatar: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
    containers_summary: Optional[Dict[str, Any]] = None,
    pods_summary: Optional[Dict[str, Any]] = None,
    orm_metadata: Optional[Dict[str, Any]] = None,
    error_stats: Optional[Dict[str, Any]] = None,
    tasks_stats: Optional[Dict[str, Any]] = None,
) -> str:
    """Render the admin dashboard."""
    model_counts = stats.get("model_counts", {})
    total_models = stats.get("total_models", 0)
    total_records = stats.get("total_records", sum(v for v in model_counts.values() if isinstance(v, int)))
    recent_actions = stats.get("recent_actions", [])
    audit_summary = stats.get("audit_summary", {})
    environment = stats.get("environment", {})
    top_models = stats.get("top_models", [])
    active_users = stats.get("active_users", [])
    system_health = stats.get("system_health", {})

    # Live stats for the new dashboard row
    _error_stats = error_stats or {}
    _tasks_stats = tasks_stats or {}
    _tasks_manager = _tasks_stats.get("manager", {})

    if _HAS_JINJA2:
        return _render_template(
            "dashboard.html",
            app_list=app_list,
            model_counts=model_counts,
            total_models=total_models,
            total_records=total_records,
            recent_actions=recent_actions,
            audit_summary=audit_summary,
            environment=environment,
            top_models=top_models,
            active_users=active_users,
            system_health=system_health,
            identity_name=identity_name,
            identity_avatar=identity_avatar,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Dashboard",
            active_page="dashboard",
            containers_summary=containers_summary or {},
            pods_summary=pods_summary or {},
            orm_metadata=orm_metadata or {},
            # New live stats
            users_today=audit_summary.get("unique_users_24h", 0),
            active_sessions=stats.get("active_sessions", 0),
            error_count=_error_stats.get("errors_last_24h", 0),
            errors_last_hour=_error_stats.get("errors_last_hour", 0),
            tasks_active=_tasks_stats.get("active_count", 0),
            tasks_pending=_tasks_stats.get("pending_count", 0),
        )
    return _fallback_dashboard(
        app_list, stats, identity_name,
        site_title=site_title, url_prefix=url_prefix,
    )


def render_list_view(
    data: Dict[str, Any],
    app_list: List[Dict[str, Any]],
    identity_name: str = "Admin",
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
    is_create: bool = False,
    flash: str = "",
    flash_type: str = "success",
    query_inspection: Optional[List[Dict[str, Any]]] = None,
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the add/edit form view.

    Args:
        query_inspection: Optional list of query dicts captured during
            the update operation (shown in a collapsible Query Inspector
            panel when the module is enabled).
    """
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
            identity_avatar=identity_avatar,
            flash=flash,
            flash_type=flash_type,
            site_title=site_title,
            url_prefix=url_prefix,
            query_inspection=query_inspection or [],
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
    model_schema: Optional[List[Dict[str, Any]]] = None,
    orm_metadata: Optional[Dict[str, Any]] = None,
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the ORM models page with schema inspector and relation graph."""
    total_models = sum(len(a.get("models", [])) for a in app_list)
    total_records = sum(v for v in model_counts.values() if isinstance(v, int))

    # Build relation edges and index stats from schema
    schema = model_schema or []
    metadata = orm_metadata or {}
    all_relations: List[Dict[str, Any]] = []
    total_indexes = 0
    total_fk = 0
    total_m2m = 0
    total_constraints = 0
    for m in schema:
        total_indexes += len(m.get("indexes", []))
        total_constraints += len(m.get("constraints", []))
        for r in m.get("relations", []):
            all_relations.append(r)
            if r["type"] == "FK":
                total_fk += 1
            elif r["type"] == "O2O":
                pass
            elif r["type"] == "M2M":
                total_m2m += 1
        # Also count M2M from m2m_tables (not in relations list)
        for jt in m.get("m2m_tables", []):
            # Avoid double-counting if already in relations
            already = any(
                r.get("type") == "M2M" and r.get("field") == jt.get("field")
                for r in m.get("relations", [])
            )
            if not already:
                total_m2m += 1
                all_relations.append({
                    "type": "M2M",
                    "field": jt.get("field", ""),
                    "from": m["name"],
                    "to": jt.get("target_model", "?"),
                    "related_name": "",
                    "db_table": jt.get("db_table", ""),
                })

    if _HAS_JINJA2:
        return _render_template(
            "orm.html",
            app_list=app_list,
            model_counts=model_counts,
            total_models=total_models,
            total_records=total_records,
            model_schema=schema,
            orm_metadata=metadata,
            all_relations=all_relations,
            total_indexes=total_indexes,
            total_fk=total_fk,
            total_m2m=total_m2m,
            total_constraints=total_constraints,
            active_page="orm",
            identity_name=identity_name,
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the application monitoring page with system metrics and charts."""
    if _HAS_JINJA2:
        return _render_template(
            "monitoring.html",
            monitoring=_dict_to_ns(monitoring),
            app_list=app_list or [],
            active_page="monitoring",
            identity_name=identity_name,
            identity_avatar=identity_avatar,
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


def render_containers_page(
    containers_data: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    identity_avatar: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the containers page with Docker Desktop-like container management."""
    if _HAS_JINJA2:
        return _render_template(
            "containers.html",
            data=containers_data,
            containers=containers_data.get("containers", []),
            compose=containers_data.get("compose", {}),
            images=containers_data.get("images", []),
            volumes=containers_data.get("volumes", []),
            networks=containers_data.get("networks", []),
            system_info=containers_data.get("system_info", {}),
            dockerfile_info=containers_data.get("dockerfile_info", {}),
            docker_available=containers_data.get("docker_available", False),
            docker_version=containers_data.get("docker_version", ""),
            error=containers_data.get("error", ""),
            app_list=app_list or [],
            active_page="containers",
            identity_name=identity_name,
            identity_avatar=identity_avatar,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Containers",
        )
    total = len(containers_data.get("containers", []))
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Containers -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Containers</h1><p>{total} containers</p></div></body></html>"""


def render_pods_page(
    pods_data: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    identity_avatar: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the pods page with Kubernetes pod tracking and manifest viewer."""
    if _HAS_JINJA2:
        return _render_template(
            "pods.html",
            data=pods_data,
            pods=pods_data.get("pods", []),
            deployments=pods_data.get("deployments", []),
            services=pods_data.get("services", []),
            ingresses=pods_data.get("ingresses", []),
            namespaces=pods_data.get("namespaces", []),
            manifests=pods_data.get("manifests", []),
            events=pods_data.get("events", []),
            cluster_info=pods_data.get("cluster_info", {}),
            kubectl_available=pods_data.get("kubectl_available", False),
            error=pods_data.get("error", ""),
            app_list=app_list or [],
            active_page="pods",
            identity_name=identity_name,
            identity_avatar=identity_avatar,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Pods",
        )
    total = len(pods_data.get("pods", []))
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Pods -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Kubernetes Pods</h1><p>{total} pods</p></div></body></html>"""


def render_admin_users_page(
    users: List[Dict[str, Any]],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
            identity_avatar=identity_avatar,
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
    identity_avatar: str = "",
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
        "containers": "icon-container",
        "pods": "icon-cloud",
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
            identity_avatar=identity_avatar,
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
# Query Inspector, Tasks, Errors pages
# ═══════════════════════════════════════════════════════════════════════════

def render_query_inspector_page(
    query_data: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    identity_avatar: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the live query inspector page with SQL profiling and N+1 detection."""
    if _HAS_JINJA2:
        return _render_template(
            "query_inspector.html",
            data=_dict_to_ns(query_data),
            total_queries=query_data.get("total_queries", 0),
            avg_duration=query_data.get("avg_duration_ms", 0),
            slow_queries=query_data.get("slow_queries", 0),
            n1_detections=query_data.get("n1_detections", 0),
            by_operation=query_data.get("by_operation", {}),
            by_model=query_data.get("by_model", {}),
            recent_queries=query_data.get("recent_queries", []),
            slow_query_list=query_data.get("slow_query_list", []),
            n1_list=query_data.get("n1_list", []),
            queries_per_second=query_data.get("queries_per_second", 0),
            slow_threshold_ms=query_data.get("slow_threshold_ms", 100),
            app_list=app_list or [],
            active_page="query_inspector",
            identity_name=identity_name,
            identity_avatar=identity_avatar,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Query Inspector",
        )
    total = query_data.get("total_queries", 0)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Query Inspector -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Query Inspector</h1><p>{total} queries captured</p></div></body></html>"""


def render_tasks_page(
    tasks_data: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    identity_avatar: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the background tasks monitor page with Chart.js analytics."""
    stats = tasks_data.get("stats", {})
    manager_info = stats.get("manager", {})
    charts = stats.get("charts", {})
    registered_tasks = tasks_data.get("registered_tasks", [])
    if _HAS_JINJA2:
        return _render_template(
            "tasks.html",
            data=_dict_to_ns(tasks_data),
            available=tasks_data.get("available", False),
            stats=_dict_to_ns(stats),
            manager=_dict_to_ns(manager_info),
            jobs=tasks_data.get("jobs", []),
            queue_stats=tasks_data.get("queue_stats", {}),
            registered_tasks=registered_tasks,
            total_jobs=stats.get("total_jobs", 0),
            active_count=stats.get("active_count", 0),
            pending_count=stats.get("pending_count", 0),
            completed_count=stats.get("completed_count", 0),
            failed_count=stats.get("failed_count", 0),
            dead_letter_count=stats.get("dead_letter_count", 0),
            success_rate=stats.get("success_rate", 100),
            p50_ms=stats.get("p50_ms", 0),
            p95_ms=stats.get("p95_ms", 0),
            p99_ms=stats.get("p99_ms", 0),
            charts=charts,
            app_list=app_list or [],
            active_page="tasks",
            identity_name=identity_name,
            identity_avatar=identity_avatar,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Background Tasks",
        )
    total = stats.get("total_jobs", 0)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Background Tasks -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Background Tasks</h1><p>{total} jobs</p></div></body></html>"""


def render_errors_page(
    errors_data: Dict[str, Any],
    app_list: Optional[List[Dict[str, Any]]] = None,
    identity_name: str = "Admin",
    identity_avatar: str = "",
    *,
    site_title: str = "Aquilia Admin",
    url_prefix: str = "/admin",
) -> str:
    """Render the error monitoring page with Chart.js analytics."""
    charts = errors_data.get("charts", {})
    if _HAS_JINJA2:
        return _render_template(
            "errors.html",
            data=_dict_to_ns(errors_data),
            total_errors=errors_data.get("total_errors", 0),
            errors_last_hour=errors_data.get("errors_last_hour", 0),
            errors_last_24h=errors_data.get("errors_last_24h", 0),
            error_rate=errors_data.get("error_rate_per_min", 0),
            unique_errors=errors_data.get("unique_errors", 0),
            unresolved_count=errors_data.get("unresolved_count", 0),
            resolved_count=errors_data.get("resolved_count", 0),
            mttr_seconds=errors_data.get("mttr_seconds", 0),
            by_domain=errors_data.get("by_domain", {}),
            by_severity=errors_data.get("by_severity", {}),
            top_routes=errors_data.get("top_routes", []),
            top_codes=errors_data.get("top_codes", []),
            recent_errors=errors_data.get("recent_errors", []),
            error_groups=errors_data.get("error_groups", []),
            hourly_trend=errors_data.get("hourly_trend", []),
            charts=charts,
            app_list=app_list or [],
            active_page="errors",
            identity_name=identity_name,
            identity_avatar=identity_avatar,
            site_title=site_title,
            url_prefix=url_prefix,
            page_title="Error Monitoring",
        )
    total = errors_data.get("total_errors", 0)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Error Monitoring -- Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Error Monitoring</h1><p>{total} errors tracked</p></div></body></html>"""


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
<link rel="icon" type="image/x-icon" href="https://raw.githubusercontent.com/tubox-labs/Aquilia/master/assets/favicon.ico">
<style>{_FALLBACK_CSS}</style></head><body>
<div class="login-container"><div class="card login-card">
<div style="text-align:center;margin-bottom:32px">
<div style="margin-bottom:12px"><img src="https://raw.githubusercontent.com/tubox-labs/Aquilia/master/assets/logo.png" alt="Aquilia" style="width:64px;height:64px;object-fit:contain"></div>
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
