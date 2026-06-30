from __future__ import annotations

import json
import time

from aquilia.controller.base import RequestCtx
from aquilia.middleware import Middleware
from aquilia.request import Request
from aquilia.response import Response
from aquilia.typing.middleware import RequestHandler

from .config import InspectorConfig
from .trace import current_trace


class ToolbarInjectionMiddleware(Middleware):
    """
    Middleware that injects the Aquilia Inspector toolbar into HTML responses.

    Acts as a lightweight, in-browser companion showing real-time query metrics,
    execution times, headers, and request details.
    """

    def __init__(self, config: InspectorConfig):
        self._config = config

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: RequestHandler) -> Response:
        # 1. Eligibility pre-checks
        toolbar_enabled = self._config.toolbar_enabled
        if toolbar_enabled is None:
            toolbar_enabled = self._config.enabled

        if not toolbar_enabled:
            return await next_handler(request, ctx)

        # Avoid injecting into the inspector's own mounted paths
        mount_path = self._config.mount_path
        if request.path.startswith(mount_path) or request.path.startswith("/__aquilia__/"):
            return await next_handler(request, ctx)

        # Proceed with request pipeline
        response = await next_handler(request, ctx)

        # Verify response eligibility
        content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type != "text/html":
            return response

        from .middleware import _is_stream_content

        if _is_stream_content(response._content):
            return response

        # Do not inject on redirects (handled by History panel/redirect-folding in Phase 4)
        if 300 <= response.status < 400:
            return response

        trace = current_trace()
        if trace is None:
            return response

        # Measure injection overhead
        t0 = time.perf_counter()

        # Decode body
        try:
            body_bytes = response._encode_body(response._content)
            body_str = body_bytes.decode("utf-8", errors="replace")
        except Exception:
            return response

        # Find closing body tag
        idx = body_str.rfind("</body>")
        if idx == -1:
            idx = body_str.lower().rfind("</body>")
        if idx == -1:
            return response

        overhead_ms = (time.perf_counter() - t0) * 1000.0

        # Build injection payload
        sql_spans = [s for s in trace.spans if s.lane == "database"]
        sql_count = len(sql_spans)
        duration_ms = trace.duration_ms
        status_code = trace.status_code or response.status

        status_class = "aq-status-success"
        if status_code >= 400:
            status_class = "aq-status-error"
        elif status_code >= 300:
            status_class = "aq-status-warning"

        trace_data = json.dumps(trace.to_dict())

        # Splice HTML
        toolbar_html = _TOOLBAR_TEMPLATE.replace("__TRACE_JSON__", trace_data)
        toolbar_html = toolbar_html.replace("__SQL_COUNT__", str(sql_count))
        toolbar_html = toolbar_html.replace("__DURATION_MS__", f"{duration_ms:.1f}")
        toolbar_html = toolbar_html.replace("__OVERHEAD_MS__", f"{overhead_ms:.2f}")
        toolbar_html = toolbar_html.replace("__STATUS_CODE__", str(status_code))
        toolbar_html = toolbar_html.replace("__STATUS_CLASS__", status_class)

        new_body_str = body_str[:idx] + toolbar_html + body_str[idx:]
        new_body_bytes = new_body_str.encode("utf-8", errors="replace")

        # Update response body and content length
        response._content = new_body_bytes
        response.headers["content-length"] = str(len(new_body_bytes))

        return response


# ── HTML/CSS/JS Shell Template ──────────────────────────────────────────────

_TOOLBAR_TEMPLATE = """
<!-- Aquilia Inspector Toolbar -->
<style>
    .aq-toolbar {
        --aq-accent: #22c55e;
        --aq-accent-hover: #16a34a;
        --aq-bg: #09090b;
        --aq-bg-surface: #18181b;
        --aq-bg-hover: rgba(255, 255, 255, 0.05);
        --aq-border: rgba(255, 255, 255, 0.08);
        --aq-text-primary: #e4e4e7;
        --aq-text-secondary: #a1a1aa;
        --aq-text-muted: #71717a;
        --aq-font-sans: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        --aq-font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        --aq-success: #22c55e;
        --aq-warning: #f59e0b;
        --aq-danger: #ef4444;

        font-family: var(--aq-font-sans);
        color: var(--aq-text-primary);
        font-size: 13px;
        box-sizing: border-box;
    }

    .aq-toolbar * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }

    /* Collapsed Floating Tab */
    #aq-tab {
        position: fixed;
        bottom: 12px;
        right: 12px;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(9, 9, 11, 0.85);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid var(--aq-border);
        padding: 8px 12px;
        border-radius: 9999px;
        cursor: pointer;
        user-select: none;
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    #aq-tab:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 12px var(--aq-accent);
        border-color: var(--aq-accent);
    }

    .aq-logo {
        width: 8px;
        height: 8px;
        background: var(--aq-accent);
        border-radius: 50%;
        box-shadow: 0 0 8px var(--aq-accent);
    }

    .aq-stat {
        font-weight: 500;
        font-size: 12px;
        color: var(--aq-text-primary);
    }

    .aq-stat-sep {
        color: var(--aq-text-muted);
    }

    .aq-tab-badge {
        font-size: 11px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
    }

    .aq-status-success { background: rgba(34, 197, 94, 0.15); color: var(--aq-success); }
    .aq-status-warning { background: rgba(245, 158, 11, 0.15); color: var(--aq-warning); }
    .aq-status-error { background: rgba(239, 68, 68, 0.15); color: var(--aq-danger); }

    /* Panel Drawer */
    #aq-panel {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 380px;
        background: var(--aq-bg);
        border-top: 1px solid var(--aq-border);
        z-index: 999998;
        transform: translateY(100%);
        transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.4);
    }

    #aq-panel.open {
        transform: translateY(0);
    }

    /* Header Bar */
    .aq-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--aq-bg-surface);
        border-bottom: 1px solid var(--aq-border);
        padding: 0 16px;
        height: 44px;
        flex-shrink: 0;
    }

    .aq-brand {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
        font-size: 14px;
        color: var(--aq-text-primary);
    }

    .aq-tabs {
        display: flex;
        gap: 4px;
        height: 100%;
        align-items: center;
    }

    .aq-tab-btn {
        background: transparent;
        border: none;
        color: var(--aq-text-secondary);
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s;
    }

    .aq-tab-btn:hover {
        background: var(--aq-bg-hover);
        color: var(--aq-text-primary);
    }

    .aq-tab-btn.active {
        background: var(--aq-accent);
        color: #000;
        font-weight: 600;
    }

    .aq-close-btn {
        background: transparent;
        border: none;
        color: var(--aq-text-secondary);
        font-size: 20px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 4px;
    }

    .aq-close-btn:hover {
        background: var(--aq-bg-hover);
        color: var(--aq-text-primary);
    }

    /* Content Area */
    .aq-content {
        flex-grow: 1;
        overflow-y: auto;
        padding: 16px;
        background: var(--aq-bg);
    }

    /* Data tables & UI components */
    .aq-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 16px;
        font-size: 12px;
    }

    .aq-table th {
        text-align: left;
        padding: 8px 12px;
        background: var(--aq-bg-surface);
        border-bottom: 1px solid var(--aq-border);
        color: var(--aq-text-secondary);
        font-weight: 600;
    }

    .aq-table td {
        padding: 8px 12px;
        border-bottom: 1px solid var(--aq-border);
        color: var(--aq-text-primary);
        word-break: break-all;
    }

    .aq-table tr:hover td {
        background: var(--aq-bg-hover);
    }

    .aq-mono {
        font-family: var(--aq-font-mono);
        font-size: 11px;
    }

    .aq-code-block {
        background: rgba(0, 0, 0, 0.4);
        border: 1px solid var(--aq-border);
        border-radius: 6px;
        padding: 12px;
        overflow-x: auto;
        font-family: var(--aq-font-mono);
        font-size: 11px;
        white-space: pre;
    }

    /* Highlight styles */
    .sql-keyword { color: #f472b6; font-weight: bold; }
    .sql-string { color: #34d399; }
    .sql-number { color: #60a5fa; }
    .json-key { color: #f472b6; font-weight: bold; }
    .json-string { color: #34d399; }
    .json-number { color: #60a5fa; }
    .json-boolean { color: #fbbf24; }
    .json-null { color: #9ca3af; }

    /* Waterfall visualization */
    .aq-waterfall-container {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .aq-waterfall-row {
        display: flex;
        align-items: center;
        font-size: 12px;
    }
    .aq-waterfall-label {
        width: 250px;
        flex-shrink: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        padding-right: 12px;
    }
    .aq-waterfall-bar-container {
        flex-grow: 1;
        background: var(--aq-bg-hover);
        height: 16px;
        position: relative;
        border-radius: 3px;
    }
    .aq-waterfall-bar {
        position: absolute;
        height: 100%;
        background: var(--aq-accent);
        border-radius: 3px;
        opacity: 0.85;
    }
    .aq-waterfall-time {
        margin-left: 12px;
        font-size: 11px;
        color: var(--aq-text-secondary);
        width: 80px;
        flex-shrink: 0;
    }
</style>

<div class="aq-toolbar">
    <!-- Floating Tab -->
    <div id="aq-tab" title="Open Aquilia Inspector">
        <span class="aq-logo"></span>
        <span class="aq-stat">__DURATION_MS__ms</span>
        <span class="aq-stat-sep">|</span>
        <span class="aq-stat">__SQL_COUNT__ sql</span>
        <span class="aq-stat-sep">|</span>
        <span class="aq-tab-badge __STATUS_CLASS__">__STATUS_CODE__</span>
        <span class="aq-stat-sep">|</span>
        <span class="aq-stat" style="color: var(--aq-text-muted); font-size: 10px;">Inspector: __OVERHEAD_MS__ms</span>
    </div>

    <!-- Drawer Panel -->
    <div id="aq-panel">
        <div class="aq-header">
            <div class="aq-brand">
                <span class="aq-logo"></span>
                <span>Aquilia Inspector</span>
            </div>
            <div class="aq-tabs">
                <button class="aq-tab-btn active" data-tab="timer">Timer</button>
                <button class="aq-tab-btn" data-tab="sql">SQL (__SQL_COUNT__)</button>
                <button class="aq-tab-btn" data-tab="request">Request</button>
                <button class="aq-tab-btn" data-tab="response">Response</button>
                <button class="aq-tab-btn" data-tab="headers">Headers</button>
            </div>
            <button class="aq-close-btn" id="aq-close-btn">&times;</button>
        </div>
        <div class="aq-content" id="aq-content">
            <!-- Hydrated dynamically -->
        </div>
    </div>
</div>

<script type="application/json" id="aq-toolbar-data">__TRACE_JSON__</script>

<script>
(function() {
    const tab = document.getElementById("aq-tab");
    const panel = document.getElementById("aq-panel");
    const closeBtn = document.getElementById("aq-close-btn");
    const content = document.getElementById("aq-content");
    const tabButtons = document.querySelectorAll(".aq-tab-btn");

    let traceData = {};
    try {
        traceData = JSON.parse(document.getElementById("aq-toolbar-data").textContent);
    } catch(e) {
        console.error("Aquilia Inspector failed to parse trace JSON data:", e);
    }

    // Toggle visibility
    tab.addEventListener("click", () => {
        panel.classList.add("open");
        tab.style.display = "none";
        renderActiveTab();
    });

    closeBtn.addEventListener("click", () => {
        panel.classList.remove("open");
        tab.style.display = "flex";
    });

    // Tabs switching
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            renderActiveTab();
        });
    });

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function highlightSql(sqlStr) {
        if (!sqlStr) return "";
        let escaped = escapeHtml(sqlStr);
        const keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE", "JOIN",
            "INNER", "LEFT", "RIGHT", "OUTER", "ON", "AND", "OR", "LIMIT",
            "OFFSET", "GROUP BY", "ORDER BY", "HAVING", "CREATE", "DROP", "ALTER",
            "TABLE", "INTO", "VALUES", "SET", "AS", "IN", "IS", "NULL", "NOT"
        ];
        const regex = new RegExp('\\\\b(' + keywords.join('|') + ')\\\\b', 'gi');
        return escaped.replace(regex, '<span class="sql-keyword">$1</span>')
                      .replace(/'([^']*)'/g, '<span class="sql-string">\\'$1\\'</span>')
                      .replace(/\\\\b(\\\\d+)\\\\b/g, '<span class="sql-number">$1</span>');
    }

    function highlightJson(jsonStr) {
        if (!jsonStr) return "";
        try {
            const obj = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr;
            jsonStr = JSON.stringify(obj, null, 2);
        } catch (e) {}

        let escaped = escapeHtml(jsonStr);
        return escaped.replace(/("(\\\\u[a-zA-Z0-9]{4}|\\\\[^u]|[^\\\\"])*"(\\\\s*:)?|\\\\b(true|false|null)\\\\b|-?\\\\d+(?:\\\\.\\\\d*)?(?:[eE][+\\\\-]?\\\\d+)?)/g, function (match) {
            let cls = 'number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'key';
                } else {
                    cls = 'string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'boolean';
            } else if (/null/.test(match)) {
                cls = 'null';
            }
            return '<span class="json-' + cls + '">' + match + '</span>';
        });
    }

    function renderActiveTab() {
        const activeTabBtn = document.querySelector(".aq-tab-btn.active");
        if (!activeTabBtn) return;
        const tabName = activeTabBtn.getAttribute("data-tab");

        if (tabName === "timer") {
            renderTimer();
        } else if (tabName === "sql") {
            renderSql();
        } else if (tabName === "request") {
            renderRequest();
        } else if (tabName === "response") {
            renderResponse();
        } else if (tabName === "headers") {
            renderHeaders();
        }
    }

    function renderTimer() {
        if (!traceData.spans || traceData.spans.length === 0) {
            content.innerHTML = `<div style="color: var(--aq-text-muted);">No spans recorded.</div>`;
            return;
        }

        let html = '<div class="aq-waterfall-container">';
        const totalDuration = traceData.duration_ms || 1.0;

        // Sort spans by start offset
        const sortedSpans = [...traceData.spans].sort((a, b) => a.start_offset_ms - b.start_offset_ms);

        sortedSpans.forEach(s => {
            const startPct = Math.min(100, Math.max(0, (s.start_offset_ms / totalDuration) * 100));
            const durationPct = Math.min(100 - startPct, Math.max(0.5, (s.duration_ms / totalDuration) * 100));

            html += `
                <div class="aq-waterfall-row">
                    <div class="aq-waterfall-label" title="${escapeHtml(s.label)}">
                        <span style="color: var(--aq-text-muted); font-size: 10px;">[${escapeHtml(s.lane)}]</span>
                        ${escapeHtml(s.label)}
                    </div>
                    <div class="aq-waterfall-bar-container">
                        <div class="aq-waterfall-bar" style="left: ${startPct}%; width: ${durationPct}%;"></div>
                    </div>
                    <div class="aq-waterfall-time">${s.duration_ms.toFixed(2)} ms</div>
                </div>
            `;
        });

        html += '</div>';
        content.innerHTML = html;
    }

    function renderSql() {
        const sqlSpans = (traceData.spans || []).filter(s => s.lane === "database");
        if (sqlSpans.length === 0) {
            content.innerHTML = `<div style="color: var(--aq-text-muted);">No SQL queries executed for this request.</div>`;
            return;
        }

        let html = `
            <table class="aq-table">
                <thead>
                    <tr>
                        <th style="width: 80px;">Time</th>
                        <th style="width: 100px;">Model</th>
                        <th>Query</th>
                        <th style="width: 80px;">Rows</th>
                    </tr>
                </thead>
                <tbody>
        `;

        sqlSpans.forEach(s => {
            const detail = s.detail || {};
            html += `
                <tr>
                    <td class="aq-mono">${s.duration_ms.toFixed(2)} ms</td>
                    <td class="aq-mono">${escapeHtml(detail.model || '-')}</td>
                    <td>
                        <div class="aq-code-block">${highlightSql(s.label)}</div>
                        ${s.source ? `<div style="font-size: 10px; color: var(--aq-text-muted); margin-top: 4px;">Source: ${escapeHtml(s.source)}</div>` : ''}
                    </td>
                    <td class="aq-mono">${detail.rows !== undefined ? detail.rows : '-'}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        content.innerHTML = html;
    }

    function renderRequest() {
        let html = `
            <table class="aq-table" style="max-width: 800px;">
                <tbody>
                    <tr>
                        <td style="font-weight: 600; width: 120px;">Method</td>
                        <td class="aq-mono">${escapeHtml(traceData.method)}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Path</td>
                        <td class="aq-mono">${escapeHtml(traceData.path)}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Route Pattern</td>
                        <td class="aq-mono">${escapeHtml(traceData.route_pattern || '-')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Client Address</td>
                        <td class="aq-mono">${escapeHtml(traceData.client_addr || '-')}</td>
                    </tr>
                </tbody>
            </table>
        `;

        if (traceData.query_params && Object.keys(traceData.query_params).length > 0) {
            html += `
                <h4 style="margin-bottom: 8px; font-size: 12px; color: var(--aq-text-secondary);">Query Parameters</h4>
                <table class="aq-table" style="max-width: 800px; margin-bottom: 20px;">
                    <thead>
                        <tr>
                            <th style="width: 200px;">Key</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            for (const [k, v] of Object.entries(traceData.query_params)) {
                html += `
                    <tr>
                        <td class="aq-mono">${escapeHtml(k)}</td>
                        <td class="aq-mono">${escapeHtml(Array.isArray(v) ? v.join(', ') : v)}</td>
                    </tr>
                `;
            }
            html += '</tbody></table>';
        }

        if (traceData.request_body_preview) {
            html += `
                <h4 style="margin-bottom: 8px; font-size: 12px; color: var(--aq-text-secondary);">Request Body</h4>
                <div class="aq-code-block">${highlightJson(traceData.request_body_preview)}</div>
            `;
        }

        content.innerHTML = html;
    }

    function renderResponse() {
        const resp = traceData.response || {};
        let html = `
            <table class="aq-table" style="max-width: 800px;">
                <tbody>
                    <tr>
                        <td style="font-weight: 600; width: 120px;">Status Code</td>
                        <td class="aq-mono"><span class="aq-tab-badge aq-status-success">${resp.status || traceData.status_code || '-'}</span></td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Content-Type</td>
                        <td class="aq-mono">${escapeHtml(resp.content_type || '-')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: 600;">Size</td>
                        <td class="aq-mono">${resp.size_bytes !== undefined ? (resp.size_bytes / 1024).toFixed(2) + ' KB' : '-'}</td>
                    </tr>
                </tbody>
            </table>
        `;

        if (resp.preview) {
            html += `
                <h4 style="margin-bottom: 8px; font-size: 12px; color: var(--aq-text-secondary);">Response Body Preview</h4>
                <div class="aq-code-block">${highlightJson(resp.preview)}</div>
            `;
        }

        content.innerHTML = html;
    }

    function renderHeaders() {
        let html = `
            <div style="display: flex; gap: 20px;">
                <div style="flex: 1;">
                    <h4 style="margin-bottom: 8px; font-size: 12px; color: var(--aq-text-secondary);">Request Headers</h4>
                    <table class="aq-table">
                        <thead>
                            <tr>
                                <th style="width: 150px;">Header</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        for (const [k, v] of Object.entries(traceData.request_headers || {})) {
            html += `
                <tr>
                    <td class="aq-mono" style="font-weight: 500;">${escapeHtml(k)}</td>
                    <td class="aq-mono">${escapeHtml(v)}</td>
                </tr>
            `;
        }

        html += `
                        </tbody>
                    </table>
                </div>
            </div>
        `;

        content.innerHTML = html;
    }
})();
</script>
"""
