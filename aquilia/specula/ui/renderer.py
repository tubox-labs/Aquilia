"""
SpeculaRenderer — renders the complete Observatory UI as one HTML string.
"""

from __future__ import annotations

import json

from ..._version import __version__ as framework_version
from ..config import SpeculaConfig
from .assets import SPECULA_CSS, SPECULA_JS


class SpeculaRenderer:
    """
    Renders the complete Specula Observatory UI as a self-contained HTML string.

    Zero external dependencies at runtime — all CSS and JS are inlined. The
    spec is fetched client-side from ``config.json_path``. Fonts load from
    Google Fonts asynchronously with system fallbacks active immediately.
    """

    def __init__(self, config: SpeculaConfig):
        self.config = config

    def render(self) -> str:
        """Produce the complete HTML page string."""
        cfg = self.config
        primary = cfg.ui_primary_color or "#22c55e"
        custom_css = cfg.ui_custom_css or ""

        boot = {
            "specUrl": cfg.json_path,
            "yamlUrl": cfg.yaml_path,
            "streamUrl": cfg.stream_path,
            "versionsUrl": cfg.versions_path,
            "schemasUrl": cfg.schemas_path,
            "routesUrl": cfg.routes_path,
            "mockUrl": cfg.mock_path,
            "exportUrl": cfg.export_path,
            "mockEnabled": bool(cfg.mock_server_enabled),
            "theme": cfg.ui_theme,
            "primaryColor": primary,
            "title": cfg.title,
            "apiVersion": cfg.version,
        }

        return f"""<!DOCTYPE html>
<html lang="en" data-theme="{cfg.ui_theme}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <meta name="color-scheme" content="light dark">
    <title>{cfg.title} — Specular API Observatory</title>
    {self._favicon_tag()}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" media="print" onload="this.media='all'">
    <style>:root{{--aq-primary:{primary};}}{SPECULA_CSS}{custom_css}</style>
</head>
<body>

<div id="aq-app">
    <header id="aq-header">
        <div class="aq-header-left">
            <div class="aq-logo" onclick="Specula.scrollTop()" title="Specular API Observatory">
                <img src="https://raw.githubusercontent.com/tubox-labs/Aquilia/master/assets/logo.png" alt="Specular Logo" width="30" height="30" style="object-fit: contain; margin-right: 8px; background: transparent; border: none; box-shadow: none;">
                <span class="aq-logo-text">Specular</span>
            </div>
        </div>
        <div class="aq-header-center">
            <button class="aq-search-trigger" id="aq-search-btn" onclick="Specula.openSearch()">
                <svg class="aq-icon" viewBox="0 0 16 16" fill="none">
                    <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" stroke-width="1.4"/>
                    <line x1="10" y1="10" x2="14" y2="14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
                </svg>
                <span>Search operations &amp; schemas</span>
                <kbd>&#8984;K</kbd>
            </button>
        </div>
        <div class="aq-header-right">
            <div id="aq-version-selector-container" style="display:none"></div>
            <button class="aq-icon-btn" onclick="Specula.toggleTheme()" title="Toggle theme">
                <svg class="aq-sun" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="3" stroke="currentColor" stroke-width="1.4"/><line x1="8" y1="1" x2="8" y2="2.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><line x1="8" y1="13.5" x2="8" y2="15" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><line x1="1" y1="8" x2="2.5" y2="8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/><line x1="13.5" y1="8" x2="15" y2="8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
                <svg class="aq-moon" viewBox="0 0 16 16" fill="none"><path d="M13 8.5A5.5 5.5 0 0 1 7.5 3a5.5 5.5 0 1 0 5.5 5.5z" stroke="currentColor" stroke-width="1.4"/></svg>
            </button>
            <a class="aq-spec-btn" href="{cfg.json_path}" target="_blank" title="View raw JSON spec">JSON</a>
            <a class="aq-spec-btn" href="{cfg.yaml_path}" target="_blank" title="Download YAML spec">YAML</a>
            <a class="aq-spec-btn" href="{cfg.export_path}/postman" download title="Export Postman collection">Postman</a>
        </div>
    </header>
 
    <div id="aq-body">
        <nav id="aq-sidebar">
            <div id="aq-sidebar-content">
                <div class="aq-sidebar-loading">Loading&#8230;</div>
            </div>
        </nav>
        <main id="aq-main">
            <div id="aq-loading" class="aq-spinner-container">
                <div class="aq-spinner"></div>
                <span>Loading API Observatory&#8230;</span>
            </div>
            <div id="aq-operations" hidden></div>
            <div id="aq-error-banner" hidden></div>
        </main>
    </div>
</div>
 
<div id="aq-search-modal" class="aq-modal" hidden>
    <div class="aq-modal-backdrop" onclick="Specula.closeSearch()"></div>
    <div class="aq-search-dialog">
        <div class="aq-search-input-wrap">
            <svg class="aq-icon aq-search-icon" viewBox="0 0 16 16" fill="none"><circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" stroke-width="1.4"/><line x1="10" y1="10" x2="14" y2="14" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>
            <input id="aq-search-input" type="text" placeholder="Search operations, schemas, tags&#8230;" autocomplete="off" spellcheck="false">
            <kbd>Esc</kbd>
        </div>
        <div id="aq-search-results"></div>
    </div>
</div>

<div id="aq-tryit" class="aq-panel" hidden>
    <div class="aq-panel-header">
        <span id="aq-tryit-label">Details</span>
        <button class="aq-icon-btn" onclick="Specula.closeTryIt()" title="Close (Esc)">
            <svg viewBox="0 0 14 14" fill="none"><line x1="1" y1="1" x2="13" y2="13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><line x1="13" y1="1" x2="1" y2="13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
        </button>
    </div>
    <div id="aq-tryit-body" class="aq-panel-body"></div>
</div>
 
<div id="aq-toasts"></div>

<script>
window.__SPECULA__ = {json.dumps(boot)};
{SPECULA_JS}
</script>
</body>
</html>"""

    def _favicon_tag(self) -> str:
        """Favicon: user-supplied URL, else an inline SVG crosshair."""
        if self.config.ui_favicon_url:
            return f'<link rel="icon" href="{self.config.ui_favicon_url}">'
        return (
            '<link rel="icon" href="data:image/svg+xml,'
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
            "<circle cx='16' cy='16' r='15' fill='%2322c55e' opacity='.15'/>"
            "<circle cx='16' cy='16' r='6' fill='%2322c55e'/>"
            "<line x1='16' y1='1' x2='16' y2='7' stroke='%2322c55e' stroke-width='2' stroke-linecap='round'/>"
            "<line x1='16' y1='25' x2='16' y2='31' stroke='%2322c55e' stroke-width='2' stroke-linecap='round'/>"
            "<line x1='1' y1='16' x2='7' y2='16' stroke='%2322c55e' stroke-width='2' stroke-linecap='round'/>"
            "<line x1='25' y1='16' x2='31' y2='16' stroke='%2322c55e' stroke-width='2' stroke-linecap='round'/>"
            '</svg>">'
        )
