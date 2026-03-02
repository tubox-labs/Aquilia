"""
AquilAdmin — Template Renderer.

Renders admin HTML pages using Jinja2 templates from the
``aquilia/admin/templates/`` directory.  Falls back to inline
Python string templates when Jinja2 is not installed so that
the admin module stays importable in minimal environments.

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

# ── Jinja2 environment ──────────────────────────────────────────────────────

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

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
    """Render a Jinja2 template by name.  Raises if Jinja2 is unavailable."""
    if _jinja_env is None:
        raise RuntimeError(
            "Jinja2 is required for admin templates.  "
            "Install it with: pip install Jinja2"
        )
    tpl = _jinja_env.get_template(template_name)
    return tpl.render(**ctx)


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
            app_list=app_list,
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
<title>Login — Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head><body>
<div class="login-container"><div class="card login-card">
<div style="text-align:center;margin-bottom:32px"><div style="font-size:3rem">🦅</div>
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
<meta charset="UTF-8"><title>Dashboard — Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Dashboard</h1><p>{total_models} models registered</p>
<p>Logged in as {html.escape(identity_name)}</p></div></body></html>"""


def _fallback_list(data: dict, app_list: list, identity_name: str = "Admin",
                   flash: str = "", flash_type: str = "success", **kw: Any) -> str:
    model = data.get("model_name", "Model")
    total = data.get("total", 0)
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>{html.escape(model)} — Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>{html.escape(model)}</h1><p>{total} records</p></div></body></html>"""


def _fallback_form(data: dict, app_list: list, identity_name: str = "Admin",
                   is_create: bool = False, flash: str = "", flash_type: str = "success", **kw: Any) -> str:
    model = data.get("model_name", "Model")
    title = f"{'Add' if is_create else 'Edit'} {model}"
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>{html.escape(title)} — Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>{html.escape(title)}</h1><p>Form view (install Jinja2 for full UI)</p></div></body></html>"""


def _fallback_audit(entries: list, app_list: list, identity_name: str = "Admin",
                    total: int = 0, **kw: Any) -> str:
    return f"""<!DOCTYPE html><html lang="en" data-theme="dark"><head>
<meta charset="UTF-8"><title>Audit Log — Aquilia Admin</title><style>{_FALLBACK_CSS}</style></head>
<body><div style="padding:24px"><h1>Audit Log</h1><p>{total} entries</p></div></body></html>"""
