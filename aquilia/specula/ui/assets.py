"""
Specula Observatory UI assets — inlined CSS and JS.

Zero external runtime dependencies: everything ships in the HTML page.
Fonts load asynchronously from Google Fonts with system fallbacks active
immediately (progressive enhancement, not a runtime dependency).
"""

# ruff: noqa: E501

SPECULA_CSS = """
/* ── Design tokens ─────────────────────────────────────────────────── */
:root[data-theme="dark"] {
    --aq-bg-base: #02040a;
    --aq-bg-base-rgb: 2, 4, 10;
    --aq-bg-surface: #09090b;
    --aq-bg-elevated: #0f0f13;
    --aq-bg-overlay: #141417;
    --aq-border: #27272a;
    --aq-border-subtle: #1f1f23;
    --aq-text-primary: #e4e4e7;
    --aq-text-secondary: #a1a1aa;
    --aq-text-muted: #71717a;
    --aq-accent: var(--aq-primary, #22c55e);
    --aq-accent-hover: #4ade80;
    --aq-accent-dim: rgba(34, 197, 94, 0.1);
    --aq-accent-glow: 0 0 16px rgba(34, 197, 94, 0.2);
    --aq-get: #22c55e;
    --aq-post: #3b82f6;
    --aq-put: #f97316;
    --aq-patch: #eab308;
    --aq-delete: #ef4444;
    --aq-ws: #06b6d4;
    --aq-head: #71717a;
    --aq-options: #71717a;
    --aq-2xx: #22c55e;
    --aq-3xx: #eab308;
    --aq-4xx: #f97316;
    --aq-5xx: #ef4444;
    --aq-shadow-card: 0 1px 3px rgba(0,0,0,0.5), 0 0 0 1px var(--aq-border);
    --aq-shadow-elevated: 0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px var(--aq-border);
}
:root[data-theme="light"] {
    --aq-bg-base: #fafafa;
    --aq-bg-base-rgb: 250, 250, 250;
    --aq-bg-surface: #ffffff;
    --aq-bg-elevated: #f4f4f5;
    --aq-bg-overlay: #ffffff;
    --aq-border: #e4e4e7;
    --aq-border-subtle: #f4f4f5;
    --aq-text-primary: #18181b;
    --aq-text-secondary: #52525b;
    --aq-text-muted: #71717a;
    --aq-accent: var(--aq-primary, #16a34a);
    --aq-accent-hover: #15803d;
    --aq-accent-dim: rgba(22, 163, 74, 0.08);
    --aq-accent-glow: 0 0 16px rgba(22, 163, 74, 0.15);
    --aq-get: #16a34a;
    --aq-post: #2563eb;
    --aq-put: #ea580c;
    --aq-patch: #d97706;
    --aq-delete: #dc2626;
    --aq-ws: #0891b2;
    --aq-head: #71717a;
    --aq-options: #71717a;
    --aq-2xx: #16a34a;
    --aq-3xx: #d97706;
    --aq-4xx: #ea580c;
    --aq-5xx: #dc2626;
    --aq-shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px var(--aq-border);
    --aq-shadow-elevated: 0 4px 12px rgba(0,0,0,0.08), 0 0 0 1px var(--aq-border);
}
:root {
    --aq-radius-sm: 4px;
    --aq-radius-md: 8px;
    --aq-radius-lg: 12px;
    --aq-radius-xl: 16px;
    --aq-font-sans: "Inter", system-ui, -apple-system, sans-serif;
    --aq-font-mono: "JetBrains Mono", "Cascadia Code", ui-monospace, monospace;
}

/* ── Base ──────────────────────────────────────────────────────────── */
* { box-sizing: border-box; }
[hidden] { display: none !important; }
html { scroll-behavior: smooth; }
body {
    margin: 0;
    font-family: var(--aq-font-sans);
    background: var(--aq-bg-base);
    color: var(--aq-text-primary);
    font-size: 14px;
    line-height: 1.55;
    transition: background-color 0.15s ease, color 0.15s ease;
}
a { color: var(--aq-accent); text-decoration: none; }
a:hover { color: var(--aq-accent-hover); }
button { font-family: inherit; cursor: pointer; }
kbd {
    font-family: var(--aq-font-mono);
    font-size: 10px;
    padding: 2px 5px;
    border-radius: var(--aq-radius-sm);
    border: 1px solid var(--aq-border);
    background: var(--aq-bg-elevated);
    color: var(--aq-text-secondary);
}
:focus-visible { outline: 2px solid var(--aq-accent); outline-offset: 2px; }
.aq-icon { width: 16px; height: 16px; }

/* ── Header ────────────────────────────────────────────────────────── */
#aq-header {
    position: fixed; top: 0; left: 0; right: 0; height: 56px; z-index: 100;
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 16px; gap: 16px;
    background: rgba(var(--aq-bg-base-rgb), 0.9);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--aq-border-subtle);
}
.aq-header-left { display: flex; align-items: center; gap: 14px; min-width: 0; }
.aq-logo {
    display: flex; align-items: center; gap: 8px; color: var(--aq-accent);
    cursor: pointer; user-select: none;
}
.aq-logo-text { font-weight: 700; font-size: 15px; letter-spacing: 0.02em; }
.aq-title-block { display: flex; align-items: center; gap: 8px; min-width: 0; }
.aq-api-title {
    font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.aq-version-pill {
    font-family: var(--aq-font-mono); font-size: 11px; padding: 2px 8px;
    border-radius: 999px; background: var(--aq-accent-dim); color: var(--aq-accent);
}
.aq-header-center { flex: 1; display: flex; justify-content: center; max-width: 480px; }
.aq-search-trigger {
    display: flex; align-items: center; gap: 8px; width: 100%;
    padding: 7px 12px; border-radius: var(--aq-radius-md);
    border: 1px solid var(--aq-border); background: var(--aq-bg-surface);
    color: var(--aq-text-muted); font-size: 13px;
}
.aq-search-trigger:hover { border-color: var(--aq-accent); }
.aq-search-trigger span { flex: 1; text-align: left; }
.aq-header-right { display: flex; align-items: center; gap: 8px; }
.aq-icon-btn {
    display: flex; align-items: center; justify-content: center;
    width: 32px; height: 32px; border-radius: var(--aq-radius-md);
    border: 1px solid var(--aq-border); background: var(--aq-bg-surface);
    color: var(--aq-text-secondary);
}
.aq-icon-btn:hover { color: var(--aq-text-primary); border-color: var(--aq-accent); }
.aq-icon-btn svg { width: 16px; height: 16px; }
:root[data-theme="dark"] .aq-sun { display: none; }
:root[data-theme="light"] .aq-moon { display: none; }
.aq-spec-btn {
    font-size: 12px; font-weight: 500; padding: 6px 10px;
    border-radius: var(--aq-radius-md); border: 1px solid var(--aq-border);
    background: var(--aq-bg-surface); color: var(--aq-text-secondary);
}
.aq-spec-btn:hover { color: var(--aq-accent); border-color: var(--aq-accent); }
.aq-version-selector {
    font-family: var(--aq-font-mono); font-size: 12px; padding: 6px 8px;
    border-radius: var(--aq-radius-md); border: 1px solid var(--aq-border);
    background: var(--aq-bg-surface); color: var(--aq-text-primary);
}
.aq-version-selector:empty, .aq-version-selector:not(:has(option)) { display: none; }

/* ── Layout ────────────────────────────────────────────────────────── */
#aq-body { display: flex; padding-top: 56px; }
#aq-sidebar {
    position: fixed; top: 56px; left: 0; width: 260px;
    height: calc(100vh - 56px); overflow-y: auto;
    border-right: 1px solid var(--aq-border-subtle);
    background: var(--aq-bg-base); padding: 12px 8px 40px;
}
#aq-main {
    margin-left: 260px; padding: 24px 40px 80px; max-width: 940px; width: 100%;
    min-height: calc(100vh - 56px);
}

/* ── Sidebar ───────────────────────────────────────────────────────── */
.aq-side-group { margin-bottom: 4px; }
.aq-side-group > summary {
    list-style: none; cursor: pointer; padding: 6px 10px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--aq-text-secondary);
    border-radius: var(--aq-radius-md); user-select: none;
}
.aq-side-group > summary::-webkit-details-marker { display: none; }
.aq-side-group > summary:hover { background: var(--aq-bg-elevated); }
.aq-side-item {
    display: flex; align-items: center; gap: 8px; padding: 5px 10px;
    border-radius: var(--aq-radius-md); cursor: pointer;
    color: var(--aq-text-secondary); font-size: 12.5px;
    white-space: nowrap; overflow: hidden;
}
.aq-side-item:hover { background: var(--aq-bg-elevated); color: var(--aq-text-primary); }
.aq-side-item .aq-method { flex-shrink: 0; min-width: 38px; text-align: center; }
.aq-side-path { overflow: hidden; text-overflow: ellipsis; font-family: var(--aq-font-mono); font-size: 11.5px; }
.aq-side-divider { border-top: 1px solid var(--aq-border-subtle); margin: 12px 8px; }
.aq-sidebar-loading { color: var(--aq-text-muted); padding: 12px; font-size: 12px; }

/* ── Method badges ─────────────────────────────────────────────────── */
.aq-method {
    font-family: var(--aq-font-mono); text-transform: uppercase;
    font-weight: 600; font-size: 11px; padding: 3px 8px;
    border-radius: var(--aq-radius-sm);
    color: var(--aq-method-color, var(--aq-text-secondary));
    background: color-mix(in srgb, var(--aq-method-color, #888) 14%, transparent);
}
.aq-method-get { --aq-method-color: var(--aq-get); }
.aq-method-post { --aq-method-color: var(--aq-post); }
.aq-method-put { --aq-method-color: var(--aq-put); }
.aq-method-patch { --aq-method-color: var(--aq-patch); }
.aq-method-delete { --aq-method-color: var(--aq-delete); }
.aq-method-ws { --aq-method-color: var(--aq-ws); }
.aq-method-head { --aq-method-color: var(--aq-head); }
.aq-method-options { --aq-method-color: var(--aq-options); }

/* ── Tag sections & operation cards ────────────────────────────────── */
.aq-tag-section { margin-bottom: 32px; }
.aq-tag-header {
    position: sticky; top: 56px; z-index: 10;
    display: flex; align-items: baseline; justify-content: space-between;
    padding: 12px 0 8px; background: var(--aq-bg-base);
    border-bottom: 1px solid var(--aq-border-subtle); margin-bottom: 12px;
}
.aq-tag-header h2 { margin: 0; font-size: 18px; font-weight: 700; }
.aq-tag-count { font-size: 12px; color: var(--aq-text-muted); }

.aq-operation {
    border-radius: var(--aq-radius-lg); box-shadow: var(--aq-shadow-card);
    background: var(--aq-bg-surface); margin-bottom: 12px;
    border-left: 3px solid var(--aq-border);
    transition: box-shadow 0.15s ease;
}
.aq-operation:hover {
    box-shadow: var(--aq-shadow-elevated);
}
.aq-op-row {
    display: flex; align-items: center; gap: 12px; padding: 12px 16px;
    cursor: pointer; user-select: none;
}
.aq-op-path { font-family: var(--aq-font-mono); font-size: 13px; font-weight: 500; }
.aq-op-summary {
    flex: 1; color: var(--aq-text-secondary); font-size: 13px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.aq-op-expand { color: var(--aq-text-muted); transition: transform 0.15s ease; }
.aq-operation.expanded .aq-op-expand { transform: rotate(90deg); }
.aq-deprecated-badge {
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    color: var(--aq-4xx); border: 1px solid var(--aq-4xx);
    padding: 1px 6px; border-radius: var(--aq-radius-sm);
}
.aq-op-body { border-top: 1px solid var(--aq-border-subtle); padding: 0 16px 16px; }
.aq-op-desc { color: var(--aq-text-secondary); margin: 12px 0; }

/* ── Tabs ──────────────────────────────────────────────────────────── */
.aq-tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--aq-border-subtle); margin: 12px 0; }
.aq-tab {
    padding: 8px 12px; font-size: 13px; font-weight: 500;
    color: var(--aq-text-secondary); background: none; border: none;
    border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.aq-tab:hover { color: var(--aq-text-primary); }
.aq-tab.active { color: var(--aq-accent); border-bottom-color: var(--aq-accent); }
.aq-tab-panel { padding: 8px 0; }

/* ── Parameters ────────────────────────────────────────────────────── */
.aq-param { display: flex; align-items: baseline; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--aq-border-subtle); flex-wrap: wrap; }
.aq-param:last-child { border-bottom: none; }
.aq-param-name { font-family: var(--aq-font-mono); font-size: 13px; color: var(--aq-accent); font-weight: 500; }
.aq-param-name.required::before { content: "*"; color: var(--aq-delete); margin-right: 2px; }
.aq-in-pill {
    font-size: 10px; text-transform: uppercase; font-weight: 600;
    padding: 1px 6px; border-radius: var(--aq-radius-sm);
    background: var(--aq-bg-elevated); color: var(--aq-text-secondary);
}
.aq-param-desc { color: var(--aq-text-secondary); font-size: 12.5px; flex-basis: 100%; }

/* ── Type pills ────────────────────────────────────────────────────── */
.aq-type-pill {
    font-family: var(--aq-font-mono); font-size: 11px; padding: 1px 7px;
    border-radius: var(--aq-radius-sm); background: var(--aq-bg-elevated);
    color: var(--aq-text-secondary);
}
.aq-type-string { background: var(--aq-accent-dim); color: var(--aq-accent); }
.aq-type-integer, .aq-type-number { background: color-mix(in srgb, var(--aq-post) 12%, transparent); color: var(--aq-post); }
.aq-type-boolean { background: color-mix(in srgb, var(--aq-get) 12%, transparent); color: var(--aq-get); }
.aq-type-array { background: color-mix(in srgb, var(--aq-put) 12%, transparent); color: var(--aq-put); }
.aq-type-object { background: var(--aq-bg-elevated); color: var(--aq-text-secondary); }

/* ── Responses ─────────────────────────────────────────────────────── */
.aq-response { margin-bottom: 8px; }
.aq-response summary {
    display: flex; align-items: center; gap: 10px; cursor: pointer;
    padding: 8px 10px; border-radius: var(--aq-radius-md); list-style: none;
}
.aq-response summary::-webkit-details-marker { display: none; }
.aq-response summary:hover { background: var(--aq-bg-elevated); }
.aq-status {
    font-family: var(--aq-font-mono); font-weight: 600; font-size: 12px;
    padding: 2px 8px; border-radius: var(--aq-radius-sm);
}
.aq-status-2xx { color: var(--aq-2xx); background: color-mix(in srgb, var(--aq-2xx) 12%, transparent); }
.aq-status-3xx { color: var(--aq-3xx); background: color-mix(in srgb, var(--aq-3xx) 12%, transparent); }
.aq-status-4xx { color: var(--aq-4xx); background: color-mix(in srgb, var(--aq-4xx) 12%, transparent); }
.aq-status-5xx { color: var(--aq-5xx); background: color-mix(in srgb, var(--aq-5xx) 12%, transparent); }
.aq-response-desc { color: var(--aq-text-secondary); font-size: 13px; }

/* ── Schema tree ───────────────────────────────────────────────────── */
.aq-schema-tree { font-family: var(--aq-font-mono); font-size: 12.5px; padding: 8px 12px; }
.aq-schema-node { padding: 2px 0 2px 0; }
.aq-schema-children { margin-left: 18px; border-left: 1px solid var(--aq-border-subtle); padding-left: 10px; }
.aq-schema-prop { color: var(--aq-text-primary); }
.aq-schema-req { color: var(--aq-delete); }
.aq-schema-desc { color: var(--aq-text-muted); font-family: var(--aq-font-sans); font-size: 12px; }
.aq-ref-link { cursor: pointer; text-decoration: underline dotted; }
.aq-schema-ref-header { margin: 2px 0; display: inline-block; }

/* ── Code blocks ───────────────────────────────────────────────────── */
.aq-codeblock {
    position: relative; background: var(--aq-bg-base);
    border: 1px solid var(--aq-border-subtle);
    border-radius: var(--aq-radius-md); margin: 8px 0;
}
.aq-codeblock pre {
    margin: 0; padding: 12px 14px; overflow-x: auto;
    font-family: var(--aq-font-mono); font-size: 12.5px; line-height: 1.6;
}
.aq-copy-btn {
    position: absolute; top: 8px; right: 8px;
    font-size: 11px; padding: 3px 8px; border-radius: var(--aq-radius-sm);
    border: 1px solid var(--aq-border); background: var(--aq-bg-surface);
    color: var(--aq-text-secondary); opacity: 0; transition: opacity 0.15s ease;
}
.aq-codeblock:hover .aq-copy-btn { opacity: 1; }
.aq-copy-btn:hover { color: var(--aq-accent); border-color: var(--aq-accent); }
.aq-tok-keyword { color: var(--aq-ws); }
.aq-tok-string { color: var(--aq-get); }
.aq-tok-number { color: var(--aq-put); }
.aq-tok-comment { color: var(--aq-text-muted); font-style: italic; }
.aq-tok-punctuation { color: var(--aq-text-secondary); }
.aq-tok-builtin { color: var(--aq-post); }

/* ── Aquilia tab (chips) ───────────────────────────────────────────── */
.aq-meta-row { display: flex; gap: 10px; align-items: baseline; padding: 6px 0; }
.aq-meta-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--aq-text-muted); min-width: 80px; }
.aq-chip {
    display: inline-block; font-family: var(--aq-font-mono); font-size: 11.5px;
    padding: 2px 9px; border-radius: 999px; margin: 0 4px 4px 0;
    background: var(--aq-accent-dim); color: var(--aq-accent); cursor: default;
}
.aq-pipeline-stage {
    display: inline-flex; align-items: center; font-family: var(--aq-font-mono);
    font-size: 11.5px; padding: 2px 9px; border-radius: var(--aq-radius-sm);
    background: var(--aq-bg-elevated); color: var(--aq-text-secondary); margin: 0 4px 4px 0;
}

/* ── Try It Out panel ──────────────────────────────────────────────── */
.aq-tryit-btn {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 13px; font-weight: 600; padding: 8px 14px;
    border-radius: var(--aq-radius-md); border: 1px solid var(--aq-accent);
    background: var(--aq-accent-dim); color: var(--aq-accent); margin-top: 8px;
}
.aq-tryit-btn:hover { background: var(--aq-accent); color: #fff; }
.aq-panel {
    position: fixed; right: 0; top: 56px; width: 480px; max-width: 100vw;
    height: calc(100vh - 56px); z-index: 200;
    background: var(--aq-bg-surface); border-left: 1px solid var(--aq-border);
    box-shadow: var(--aq-shadow-elevated);
    transform: translateX(100%); transition: transform 0.2s ease;
    display: flex; flex-direction: column;
}
.aq-panel.open { transform: translateX(0); }
.aq-panel[hidden] { display: flex; }
.aq-panel-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 16px; border-bottom: 1px solid var(--aq-border-subtle);
    font-weight: 600;
}
.aq-panel-body { flex: 1; overflow-y: auto; padding: 16px; }
.aq-field { margin-bottom: 12px; }
.aq-field label { display: block; font-size: 12px; font-weight: 500; color: var(--aq-text-secondary); margin-bottom: 4px; }
.aq-field input, .aq-field select, .aq-field textarea {
    width: 100%; padding: 7px 10px; font-size: 13px;
    font-family: var(--aq-font-mono); border-radius: var(--aq-radius-md);
    border: 1px solid var(--aq-border); background: var(--aq-bg-base);
    color: var(--aq-text-primary);
}
.aq-field textarea { min-height: 120px; resize: vertical; }
.aq-field input:focus, .aq-field textarea:focus, .aq-field select:focus { border-color: var(--aq-accent); outline: none; }
.aq-send-btn {
    width: 100%; padding: 10px; font-size: 14px; font-weight: 600;
    border-radius: var(--aq-radius-md); border: none;
    background: var(--aq-accent); color: #fff; margin: 8px 0;
}
.aq-send-btn:hover { background: var(--aq-accent-hover); }
.aq-send-btn:disabled { opacity: 0.6; cursor: wait; }
.aq-resp-meta { display: flex; align-items: center; gap: 12px; margin: 12px 0 8px; }
.aq-latency { font-family: var(--aq-font-mono); font-size: 12px; color: var(--aq-text-secondary); }
.aq-section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--aq-text-muted); margin: 16px 0 8px; }

/* ── Search modal ──────────────────────────────────────────────────── */
.aq-modal { position: fixed; inset: 0; z-index: 300; }
.aq-modal-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,0.5); }
.aq-search-dialog {
    position: relative; margin: 80px auto 0; width: 560px; max-width: calc(100vw - 32px);
    background: var(--aq-bg-overlay); border: 1px solid var(--aq-border);
    border-radius: var(--aq-radius-lg); box-shadow: var(--aq-shadow-elevated);
    overflow: hidden;
}
.aq-search-input-wrap {
    display: flex; align-items: center; gap: 10px; padding: 12px 14px;
    border-bottom: 1px solid var(--aq-border-subtle);
}
#aq-search-input {
    flex: 1; border: none; background: none; color: var(--aq-text-primary);
    font-size: 15px; font-family: inherit; outline: none;
}
#aq-search-results { max-height: 400px; overflow-y: auto; }
.aq-search-result {
    display: flex; align-items: center; gap: 10px; padding: 10px 14px;
    cursor: pointer; border-bottom: 1px solid var(--aq-border-subtle);
}
.aq-search-result:hover, .aq-search-result.selected { background: var(--aq-bg-elevated); }
.aq-search-result .aq-op-summary { font-size: 12px; }
.aq-search-empty { padding: 20px; text-align: center; color: var(--aq-text-muted); font-size: 13px; }
.aq-search-kind { font-size: 10px; text-transform: uppercase; color: var(--aq-text-muted); }

/* ── Toasts ────────────────────────────────────────────────────────── */
#aq-toasts { position: fixed; bottom: 20px; right: 20px; z-index: 400; display: flex; flex-direction: column; gap: 8px; }
.aq-toast {
    padding: 10px 16px; border-radius: var(--aq-radius-md);
    background: var(--aq-bg-overlay); border: 1px solid var(--aq-border);
    box-shadow: var(--aq-shadow-elevated); font-size: 13px;
    animation: aq-toast-in 0.2s ease;
}
.aq-toast-success { border-left: 3px solid var(--aq-get); }
.aq-toast-info { border-left: 3px solid var(--aq-post); }
.aq-toast-error { border-left: 3px solid var(--aq-delete); }
@keyframes aq-toast-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

/* ── Loading / error ───────────────────────────────────────────────── */
.aq-spinner-container {
    display: flex; flex-direction: column; align-items: center; gap: 14px;
    padding: 80px 0; color: var(--aq-text-secondary);
}
.aq-spinner {
    width: 28px; height: 28px; border-radius: 50%;
    border: 3px solid var(--aq-border); border-top-color: var(--aq-accent);
    animation: aq-spin 0.8s linear infinite;
}
@keyframes aq-spin { to { transform: rotate(360deg); } }
#aq-error-banner {
    padding: 16px; border-radius: var(--aq-radius-md);
    background: color-mix(in srgb, var(--aq-delete) 10%, transparent);
    border: 1px solid var(--aq-delete); color: var(--aq-text-primary);
}

/* ── Footer badge ──────────────────────────────────────────────────── */
.aq-footer {
    margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--aq-border-subtle);
    font-size: 12px; color: var(--aq-text-muted); text-align: center;
}

/* ── Responsive ────────────────────────────────────────────────────── */
@media (max-width: 768px) {
    #aq-sidebar { transform: translateX(-100%); transition: transform 0.2s ease; z-index: 150; background: var(--aq-bg-surface); }
    #aq-sidebar.open { transform: none; }
    #aq-main { margin-left: 0; padding: 16px; }
    .aq-header-center { display: none; }
    .aq-api-title { display: none; }
    .aq-panel { width: 100vw; }
}

/* ── Reduced motion ────────────────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; transition: none !important; }
    html { scroll-behavior: auto; }
}

/* ── Custom Dropdown Menu ─────────────────────────────────────────── */
.aq-custom-select {
    position: relative;
    display: inline-block;
    width: 100%;
}
.aq-select-trigger {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 6px 12px;
    font-size: 13px;
    font-family: var(--aq-font-sans);
    border: 1px solid var(--aq-border);
    border-radius: var(--aq-radius-md);
    background: var(--aq-bg-surface);
    color: var(--aq-text-primary);
    cursor: pointer;
    user-select: none;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.aq-select-trigger:hover {
    border-color: var(--aq-accent);
}
.aq-select-trigger::after {
    content: "▼";
    font-size: 9px;
    color: var(--aq-text-muted);
    margin-left: 8px;
    transition: transform 0.15s ease;
}
.aq-custom-select.open .aq-select-trigger::after {
    transform: rotate(180deg);
}
.aq-select-options {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    width: 100%;
    max-height: 200px;
    overflow-y: auto;
    background: var(--aq-bg-surface);
    border: 1px solid var(--aq-border);
    border-radius: var(--aq-radius-md);
    box-shadow: var(--aq-shadow-elevated);
    z-index: 300;
    display: none;
    padding: 4px 0;
}
.aq-custom-select.open .aq-select-options {
    display: block;
}
.aq-select-option {
    padding: 8px 12px;
    font-size: 13px;
    color: var(--aq-text-secondary);
    cursor: pointer;
    transition: background 0.1s ease, color 0.1s ease;
}
.aq-select-option:hover, .aq-select-option.selected {
    background: var(--aq-accent-dim);
    color: var(--aq-accent);
}

/* ── Code Editor ── */
.aq-editor-container {
    position: relative;
    height: 150px;
    width: 100%;
    border: 1px solid var(--aq-border);
    border-radius: var(--aq-radius-md);
    background: var(--aq-bg-base);
    overflow: hidden;
}
.aq-editor-textarea, .aq-editor-highlight-pre {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    margin: 0 !important;
    padding: 10px !important;
    font-family: var(--aq-font-mono) !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
    white-space: pre-wrap !important;
    word-wrap: break-word !important;
    border: none !important;
    background: transparent !important;
    overflow-y: auto !important;
    box-sizing: border-box !important;
}
.aq-editor-textarea {
    color: transparent !important;
    caret-color: var(--aq-text-primary) !important;
    resize: none !important;
    z-index: 2;
}
.aq-editor-textarea:focus {
    outline: none !important;
}
.aq-editor-highlight-pre {
    z-index: 1;
    pointer-events: none;
}
.aq-editor-highlight-code {
    font-family: var(--aq-font-mono) !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
}
.aq-kv-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
}
.aq-kv-table th {
    text-align: left;
    padding: 6px 8px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--aq-text-muted);
    border-bottom: 1px solid var(--aq-border-subtle);
}
.aq-kv-table td {
    padding: 6px 4px;
    vertical-align: middle;
}
.aq-kv-table input[type="text"], .aq-kv-table select {
    width: 100%;
    padding: 6px 10px;
    font-size: 13px;
    border-radius: var(--aq-radius-sm);
    border: 1px solid var(--aq-border);
    background: var(--aq-bg-base);
    color: var(--aq-text-primary);
}
.aq-kv-table input[type="file"] {
    width: 100%;
    font-size: 12px;
}
.aq-lock-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: var(--aq-radius-sm);
    padding: 2px 6px;
    font-size: 10px;
    font-weight: 600;
    margin-right: 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    gap: 4px;
    line-height: 1;
}
.aq-lock-badge svg {
    width: 10px;
    height: 10px;
}
.aq-security-card {
    background: var(--aq-bg-surface);
    border: 1px solid var(--aq-border-subtle);
    border-radius: var(--aq-radius-md);
    padding: 16px;
    margin-top: 12px;
}
.aq-security-title {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 12px;
    color: var(--aq-text-primary);
    display: flex;
    align-items: center;
    gap: 6px;
}
.aq-security-title svg {
    width: 14px;
    height: 14px;
    color: #ef4444;
}
.aq-security-item {
    margin-bottom: 8px;
    font-size: 13px;
    color: var(--aq-text-secondary);
}
.aq-security-item-label {
    font-weight: 500;
    color: var(--aq-text-primary);
    margin-right: 6px;
}
.aq-guard-stage {
    background: var(--aq-bg-base);
    border: 1px solid var(--aq-border);
    border-radius: var(--aq-radius-sm);
    padding: 4px 8px;
    margin-top: 6px;
    display: inline-block;
    font-family: var(--aq-font-mono);
    font-size: 11px;
}
.aq-clearance-badge {
    color: #ffffff;
    border-radius: var(--aq-radius-sm);
    padding: 1px 6px;
    font-weight: 600;
    font-size: 10px;
    text-transform: uppercase;
    display: inline-block;
}
.aq-clearance-badge.level-restricted {
    background: #ef4444;
}
.aq-clearance-badge.level-confidential {
    background: #f59e0b;
}
.aq-clearance-badge.level-internal {
    background: #10b981;
}
.aq-clearance-badge.level-authenticated {
    background: #3b82f6;
}
.aq-clearance-badge.level-public {
    background: var(--aq-text-muted);
}
"""


SPECULA_JS = r"""
const Specula = (() => {
    'use strict';

    // ── State ──────────────────────────────────────────────────────────
    let spec = null;
    let cfg = {};
    let theme = 'auto';
    let searchIndex = [];
    let activeVersion = null;
    let sse = null;
    let sseRetry = 1000;
    let searchSelection = 0;

    const EFFECT_DOCS = {
        'DBTx': 'Database transaction — acquired/released per-request by EffectMiddleware',
        'Cache': 'Cache read/write — uses CacheService (Redis or Memory backend)',
        'Queue': 'Message queue — enqueues background tasks',
        'HTTP': 'Outbound HTTP client — rate-limited, with retry and circuit-breaker',
        'Storage': 'File storage — local, S3, GCS, Azure, or SFTP backend',
    };

    const LOCK_ICON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>';

    // ── Helpers ────────────────────────────────────────────────────────
    function esc(str) {
        return String(str).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#x27;'}[m]));
    }
    function el(tag, cls, text) {
        const node = document.createElement(tag);
        if (cls) node.className = cls;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function createCustomDropdown(container, options, defaultValue, onChange) {
        container.textContent = '';
        const wrapper = el('div', 'aq-custom-select');
        
        const trigger = el('div', 'aq-select-trigger');
        const selectedText = el('span', '', defaultValue ? (options.find(o => o.value === defaultValue)?.label || defaultValue) : (options[0]?.label || ''));
        trigger.appendChild(selectedText);
        wrapper.appendChild(trigger);
        
        const optionsContainer = el('div', 'aq-select-options');
        
        let activeValue = defaultValue || (options[0]?.value);
        
        options.forEach(opt => {
            const optionEl = el('div', 'aq-select-option', opt.label);
            if (opt.value === activeValue) optionEl.classList.add('selected');
            optionEl.addEventListener('click', (e) => {
                e.stopPropagation();
                optionsContainer.querySelectorAll('.aq-select-option').forEach(o => o.classList.remove('selected'));
                optionEl.classList.add('selected');
                selectedText.textContent = opt.label;
                activeValue = opt.value;
                wrapper.classList.remove('open');
                if (onChange) onChange(opt.value);
            });
            optionsContainer.appendChild(optionEl);
        });
        
        wrapper.appendChild(optionsContainer);
        
        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            document.querySelectorAll('.aq-custom-select').forEach(sel => {
                if (sel !== wrapper) sel.classList.remove('open');
            });
            wrapper.classList.toggle('open');
        });
        
        container.appendChild(wrapper);
        
        return {
            getValue: () => activeValue,
            setValue: (val) => {
                const opt = options.find(o => o.value === val);
                if (opt) {
                    optionsContainer.querySelectorAll('.aq-select-option').forEach(o => {
                        o.classList.toggle('selected', o.textContent === opt.label);
                    });
                    selectedText.textContent = opt.label;
                    activeValue = val;
                }
            }
        };
    }

    function renderCodeEditor(container, type, op, state) {
        const field = el('div', 'aq-field');
        
        const editorContainer = el('div', 'aq-editor-container');
        const textarea = el('textarea', 'aq-editor-textarea');
        textarea.placeholder = type === 'application/json' ? '{\n  "key": "value"\n}' : 'Enter request body...';
        
        if (type === 'application/json') {
            textarea.value = bodyExample(op) || '{}';
        } else if (type === 'application/xml') {
            textarea.value = '<?xml version="1.0" encoding="UTF-8"?>\n<request>\n  \n</request>';
        } else {
            textarea.value = '';
        }
        state.body = textarea.value;
        
        const pre = el('pre', 'aq-editor-highlight-pre');
        const code = el('code', 'aq-editor-highlight-code');
        pre.appendChild(code);
        
        editorContainer.appendChild(pre);
        editorContainer.appendChild(textarea);
        field.appendChild(editorContainer);
        container.appendChild(field);
        
        const updatePreview = () => {
            let lang = 'plain';
            if (type === 'application/json') lang = 'json';
            else if (type === 'application/xml') lang = 'xml';
            
            code.innerHTML = highlight(textarea.value, lang) + '\n';
            pre.scrollTop = textarea.scrollTop;
            pre.scrollLeft = textarea.scrollLeft;
        };
        
        textarea.addEventListener('scroll', () => {
            pre.scrollTop = textarea.scrollTop;
            pre.scrollLeft = textarea.scrollLeft;
        });
        
        let formatTimeout = null;
        textarea.addEventListener('input', () => {
            state.body = textarea.value;
            updatePreview();
            
            clearTimeout(formatTimeout);
            if (type === 'application/json') {
                formatTimeout = setTimeout(() => {
                    try {
                        const val = textarea.value;
                        if (!val.trim()) return;
                        const parsed = JSON.parse(val);
                        const start = textarea.selectionStart;
                        const end = textarea.selectionEnd;
                        const formatted = JSON.stringify(parsed, null, 2);
                        if (formatted !== val) {
                            textarea.value = formatted;
                            textarea.selectionStart = Math.min(start, formatted.length);
                            textarea.selectionEnd = Math.min(end, formatted.length);
                            updatePreview();
                        }
                    } catch (e) {}
                }, 1200);
            }
        });
        
        textarea.addEventListener('blur', () => {
            if (type === 'application/json') {
                try {
                    const val = textarea.value;
                    if (val.trim()) {
                        textarea.value = JSON.stringify(JSON.parse(val), null, 2);
                        textarea.dispatchEvent(new Event('input'));
                    }
                } catch (e) {}
            }
        });
        
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const val = textarea.value;
                textarea.value = val.substring(0, start) + '  ' + val.substring(end);
                textarea.selectionStart = textarea.selectionEnd = start + 2;
                textarea.dispatchEvent(new Event('input'));
                return;
            }
            
            const pairs = { '{': '}', '[': ']', '(': ')', '"': '"', "'": "'" };
            if (pairs[e.key] !== undefined) {
                e.preventDefault();
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const text = textarea.value;
                const closing = pairs[e.key];
                
                textarea.value = text.substring(0, start) + e.key + closing + text.substring(end);
                textarea.selectionStart = start + 1;
                textarea.selectionEnd = start + 1;
                textarea.dispatchEvent(new Event('input'));
            } else if (['}', ']', ')', '"', "'"].includes(e.key)) {
                const start = textarea.selectionStart;
                if (textarea.value[start] === e.key) {
                    e.preventDefault();
                    textarea.selectionStart = start + 1;
                    textarea.selectionEnd = start + 1;
                }
            } else if (e.key === 'Backspace') {
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                if (start === end && start > 0) {
                    const charBefore = textarea.value[start - 1];
                    const charAfter = textarea.value[start];
                    if (pairs[charBefore] === charAfter) {
                        e.preventDefault();
                        textarea.value = textarea.value.substring(0, start - 1) + textarea.value.substring(start + 1);
                        textarea.selectionStart = start - 1;
                        textarea.selectionEnd = start - 1;
                        textarea.dispatchEvent(new Event('input'));
                    }
                }
            }
        });
        
        updatePreview();
    }

    function renderKeyValueEditor(container, type, op, state) {
        const wrapper = el('div', 'aq-kv-editor');
        const table = el('table', 'aq-kv-table');
        const thead = el('thead');
        const headerRow = el('tr');
        headerRow.appendChild(el('th', '', 'Key'));
        headerRow.appendChild(el('th', '', 'Value'));
        if (type === 'multipart/form-data') {
            headerRow.appendChild(el('th', '', 'Type'));
        }
        headerRow.appendChild(el('th', '', ''));
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        const tbody = el('tbody');
        table.appendChild(tbody);
        wrapper.appendChild(table);
        
        state.formParams = [];
        
        const addRow = (key = '', val = '', paramType = 'text') => {
            const row = el('tr');
            
            const tdKey = el('td');
            const inputKey = el('input');
            inputKey.type = 'text';
            inputKey.placeholder = 'Key';
            inputKey.value = key;
            tdKey.appendChild(inputKey);
            row.appendChild(tdKey);
            
            let inputType = 'text';
            let tdType = null;
            if (type === 'multipart/form-data') {
                tdType = el('td');
                const selectType = el('select');
                const optText = el('option', '', 'Text');
                optText.value = 'text';
                const optFile = el('option', '', 'File');
                optFile.value = 'file';
                selectType.appendChild(optText);
                selectType.appendChild(optFile);
                selectType.value = paramType;
                tdType.appendChild(selectType);
                row.appendChild(tdType);
                
                inputType = paramType;
            }
            
            const tdValue = el('td');
            let inputValue = el('input');
            
            const setupValueInput = (pType) => {
                tdValue.textContent = '';
                inputValue = el('input');
                if (pType === 'file') {
                    inputValue.type = 'file';
                } else {
                    inputValue.type = 'text';
                    inputValue.placeholder = 'Value';
                    inputValue.value = val;
                }
                tdValue.appendChild(inputValue);
                
                inputValue.addEventListener('input', syncParams);
                if (pType === 'file') {
                    inputValue.addEventListener('change', syncParams);
                }
            };
            
            setupValueInput(inputType);
            row.appendChild(tdValue);
            
            if (type === 'multipart/form-data') {
                const selectType = tdType.firstChild;
                selectType.addEventListener('change', () => {
                    setupValueInput(selectType.value);
                    syncParams();
                });
            }
            
            const tdAction = el('td');
            const delBtn = el('button', 'aq-icon-btn', '×');
            delBtn.style.color = 'var(--aq-delete)';
            delBtn.style.fontSize = '18px';
            delBtn.addEventListener('click', (e) => {
                e.preventDefault();
                row.remove();
                syncParams();
            });
            tdAction.appendChild(delBtn);
            row.appendChild(tdAction);
            
            tbody.appendChild(row);
            
            function syncParams() {
                state.formParams = [];
                tbody.querySelectorAll('tr').forEach(r => {
                    const k = r.cells[0].firstChild.value.trim();
                    if (!k) return;
                    
                    let t = 'text';
                    let v = '';
                    
                    if (type === 'multipart/form-data') {
                        const sel = r.cells[1].firstChild;
                        t = sel.value;
                        const valInput = r.cells[2].firstChild;
                        v = t === 'file' ? valInput.files[0] : valInput.value;
                    } else {
                        const valInput = r.cells[1].firstChild;
                        v = valInput.value;
                    }
                    
                    state.formParams.push({ key: k, value: v, type: t });
                });
            }
            
            inputKey.addEventListener('input', syncParams);
            syncParams();
        };
        
        let hasPrepopulated = false;
        const media = op.requestBody && op.requestBody.content && op.requestBody.content[type];
        if (media && media.schema) {
            const resolvedSchema = media.schema.$ref ? resolveRef(media.schema.$ref) : media.schema;
            if (resolvedSchema && resolvedSchema.properties) {
                for (const [k, v] of Object.entries(resolvedSchema.properties)) {
                    const schemaType = v.type || 'string';
                    const isBinary = (v.format === 'binary') || (schemaType === 'string' && v.format === 'binary');
                    addRow(k, '', isBinary ? 'file' : 'text');
                    hasPrepopulated = true;
                }
            }
        }
        
        if (!hasPrepopulated) {
            addRow();
        }
        
        const addParamBtn = el('button', 'aq-spec-btn', '+ Add Parameter');
        addParamBtn.style.marginTop = '8px';
        addParamBtn.addEventListener('click', (e) => {
            e.preventDefault();
            addRow();
        });
        
        wrapper.appendChild(addParamBtn);
        container.appendChild(wrapper);
    }

    function opDomId(opId) { return 'aq-op-' + opId.replace(/[^\w-]/g, '_'); }
    function resolveRef(ref) {
        if (typeof ref !== 'string' || !ref.startsWith('#/components/schemas/')) return null;
        const name = ref.split('/').pop();
        return (spec.components && spec.components.schemas && spec.components.schemas[name]) || null;
    }
    function schemaTypeName(schema) {
        if (!schema) return 'any';
        if (schema.$ref) return schema.$ref.split('/').pop();
        if (schema.oneOf) return schema.oneOf.map(schemaTypeName).join(' | ');
        if (schema.enum) return 'enum';
        let t = schema.type || 'object';
        if (t === 'array') t = 'array<' + schemaTypeName(schema.items) + '>';
        if (schema.format) t += '(' + schema.format + ')';
        return t;
    }
    function baseType(schema) {
        if (!schema) return 'object';
        if (schema.$ref) return 'object';
        if (schema.oneOf) { const first = schema.oneOf.find(s => s.type !== 'null'); return baseType(first || schema.oneOf[0]); }
        return schema.type || 'object';
    }
    function typePill(schema) {
        const pill = el('span', 'aq-type-pill aq-type-' + baseType(schema), schemaTypeName(schema));
        return pill;
    }
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => showToast('Copied!'));
    }
    function showToast(msg, type = 'success') {
        const toast = el('div', 'aq-toast aq-toast-' + type, msg);
        document.getElementById('aq-toasts').appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
    function showError(msg) {
        const banner = document.getElementById('aq-error-banner');
        banner.hidden = false;
        banner.textContent = msg;
        document.getElementById('aq-loading').hidden = true;
    }
    function scrollTop() { window.scrollTo({top: 0, behavior: 'smooth'}); }
    function setURLHash(opId) { history.replaceState(null, '', '#' + opId); }

    // ── Syntax highlighter (regex, 6 token classes) ────────────────────
    const HIGHLIGHT_RULES = {
        json: [
            [/"(?:[^"\\]|\\.)*"(?=\s*:)/g, 'builtin'],
            [/"(?:[^"\\]|\\.)*"/g, 'string'],
            [/\b(true|false|null)\b/g, 'keyword'],
            [/-?\b\d+\.?\d*([eE][+-]?\d+)?\b/g, 'number'],
        ],
        bash: [
            [/#.*$/gm, 'comment'],
            [/'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"/g, 'string'],
            [/\b(curl|http|https)\b/g, 'keyword'],
            [/\s(-{1,2}[\w-]+)/g, 'builtin'],
        ],
        python: [
            [/#.*$/gm, 'comment'],
            [/'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"/g, 'string'],
            [/\b(import|from|as|def|async|await|with|return|print|None|True|False)\b/g, 'keyword'],
            [/\b\d+\.?\d*\b/g, 'number'],
            [/\b(AsyncHTTPClient|json|response)\b/g, 'builtin'],
        ],
        javascript: [
            [/\/\/.*$/gm, 'comment'],
            [/'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`/g, 'string'],
            [/\b(const|let|var|await|async|function|return|fetch|import|from|new|true|false|null)\b/g, 'keyword'],
            [/\b\d+\.?\d*\b/g, 'number'],
            [/\b(console|JSON|response)\b/g, 'builtin'],
        ],
        xml: [
            [/<!--[\s\S]*?-->/g, 'comment'],
            [/<\/([^> \t\r\n]+)>/g, 'keyword'],
            [/<([^> \t\r\n\/]+)/g, 'keyword'],
            [/\b([a-zA-Z0-9_:-]+)=/g, 'builtin'],
            [/"(?:[^"\\]|\\.)*"/g, 'string'],
            [/'(?:[^'\\]|\\.)*'/g, 'string'],
        ],
    };
    HIGHLIGHT_RULES.typescript = HIGHLIGHT_RULES.javascript;

    function highlight(code, lang) {
        const rules = HIGHLIGHT_RULES[lang] || [];
        // Tokenize by collecting matches, then emit escaped HTML.
        const marks = [];
        for (const [regex, cls] of rules) {
            regex.lastIndex = 0;
            let m;
            while ((m = regex.exec(code)) !== null) {
                const start = m.index + (m[0].length - (m[1] || m[0]).length);
                const text = m[1] || m[0];
                if (!marks.some(x => start < x.end && start + text.length > x.start)) {
                    marks.push({start, end: start + text.length, cls});
                }
                if (m.index === regex.lastIndex) regex.lastIndex++;
            }
        }
        marks.sort((a, b) => a.start - b.start);
        let out = '', pos = 0;
        for (const mark of marks) {
            if (mark.start < pos) continue;
            out += esc(code.slice(pos, mark.start));
            out += '<span class="aq-tok-' + mark.cls + '">' + esc(code.slice(mark.start, mark.end)) + '</span>';
            pos = mark.end;
        }
        out += esc(code.slice(pos));
        return out;
    }

    function codeBlock(code, lang) {
        const wrap = el('div', 'aq-codeblock');
        const pre = el('pre');
        pre.innerHTML = highlight(code, lang);
        const btn = el('button', 'aq-copy-btn', 'Copy');
        btn.addEventListener('click', e => { e.stopPropagation(); copyToClipboard(code); });
        wrap.appendChild(pre);
        wrap.appendChild(btn);
        return wrap;
    }

    // ── Init ───────────────────────────────────────────────────────────
    async function init() {
        cfg = window.__SPECULA__ || {};
        theme = localStorage.getItem('specula-theme') || cfg.theme || 'auto';
        applyTheme(theme);
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (theme === 'auto') applyTheme('auto');
        });

        try {
            await loadSpec(cfg.specUrl);
        } catch (e) {
            showError('Failed to load spec from ' + cfg.specUrl + ': ' + e.message);
            return;
        }

        renderVersionSelector();
        connectSSE();
        setupKeyboard();
        restoreFromURL();
        document.addEventListener('click', () => {
            document.querySelectorAll('.aq-custom-select').forEach(sel => {
                sel.classList.remove('open');
            });
        });
    }

    async function loadSpec(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        spec = await res.json();
        buildSearchIndex();
        populateObservatoryStats();
        renderSidebar();
        renderOperations();
        document.getElementById('aq-loading').hidden = true;
        document.getElementById('aq-operations').hidden = false;
    }

    // ── Operations grouped by tag ──────────────────────────────────────
    function groupOperations() {
        const groups = new Map();
        for (const [path, item] of Object.entries(spec.paths || {})) {
            if (!item || typeof item !== 'object') continue;
            for (const [method, op] of Object.entries(item)) {
                if (method.startsWith('x-') || !op || typeof op !== 'object') continue;
                const tag = (op.tags && op.tags[0]) || 'General';
                if (!groups.has(tag)) groups.set(tag, []);
                groups.get(tag).push({path, method, op});
            }
        }
        // Honour x-tagGroups ordering when present
        const ordered = new Map();
        for (const tg of spec['x-tagGroups'] || []) {
            for (const tag of tg.tags || []) {
                if (groups.has(tag)) { ordered.set(tag, groups.get(tag)); groups.delete(tag); }
            }
        }
        for (const [tag, ops] of groups) ordered.set(tag, ops);
        return ordered;
    }

    // ── Sidebar ────────────────────────────────────────────────────────
    function renderSidebar() {
        const container = document.getElementById('aq-sidebar-content');
        container.textContent = '';

        for (const [tag, ops] of groupOperations()) {
            const details = el('details', 'aq-side-group');
            details.open = true;
            const summary = el('summary', '', tag);
            details.appendChild(summary);
            for (const {path, method, op} of ops) {
                const item = el('div', 'aq-side-item');
                const isWS = op['x-specula-websocket'];
                const badge = el('span', 'aq-method aq-method-' + (isWS ? 'ws' : method), isWS ? 'WS' : method.slice(0, 3).toUpperCase());
                item.appendChild(badge);
                item.appendChild(el('span', 'aq-side-path', path));
                item.addEventListener('click', () => jumpToOperation(op.operationId));
                details.appendChild(item);
            }
            container.appendChild(details);
        }

        // Schemas section
        const schemas = (spec.components && spec.components.schemas) || {};
        if (Object.keys(schemas).length) {
            container.appendChild(el('div', 'aq-side-divider'));
            const details = el('details', 'aq-side-group');
            const summary = el('summary', '', 'Schemas');
            details.appendChild(summary);
            for (const name of Object.keys(schemas)) {
                const item = el('div', 'aq-side-item');
                item.appendChild(el('span', 'aq-side-path', name));
                item.addEventListener('click', () => showSchemaModal(name));
                details.appendChild(item);
            }
            container.appendChild(details);
        }
    }

    function showSchemaModal(name) {
        const schema = spec.components.schemas[name];
        if (!schema) return;
        openPanel('Schema: ' + name, body => {
            body.appendChild(renderSchemaTree(schema, 0));
            body.appendChild(codeBlock(JSON.stringify(schema, null, 2), 'json'));
        });
    }

    // ── Operations list ────────────────────────────────────────────────
    function renderOperations() {
        const container = document.getElementById('aq-operations');
        container.textContent = '';

        for (const [tag, ops] of groupOperations()) {
            const section = el('section', 'aq-tag-section');
            const header = el('div', 'aq-tag-header');
            header.appendChild(el('h2', '', tag));
            header.appendChild(el('span', 'aq-tag-count', ops.length + ' operation' + (ops.length === 1 ? '' : 's')));
            section.appendChild(header);
            for (const {path, method, op} of ops) {
                section.appendChild(renderOperationCard(path, method, op));
            }
            container.appendChild(section);
        }

        const footer = el('div', 'aq-footer', 'Powered by Specula · Aquilia API Observatory');
        container.appendChild(footer);
    }

    function renderOperationCard(path, method, op) {
        const isWS = op['x-specula-websocket'];
        const methodCls = isWS ? 'ws' : method;
        const card = el('div', 'aq-operation aq-method-' + methodCls);
        card.id = opDomId(op.operationId || (method + path));

        const row = el('div', 'aq-op-row');
        row.appendChild(el('span', 'aq-method aq-method-' + methodCls, isWS ? 'WS' : method.toUpperCase()));
        row.appendChild(el('span', 'aq-op-path', path));
        
        const hasSecurity = (op.security && op.security.length > 0) || (op['x-specula-security'] && op['x-specula-security'].authenticated);
        if (hasSecurity) {
            const badge = el('span', 'aq-lock-badge');
            badge.innerHTML = LOCK_ICON_SVG + ' Protected';
            row.appendChild(badge);
        }
        
        row.appendChild(el('span', 'aq-op-summary', op.summary || ''));
        if (op.deprecated) row.appendChild(el('span', 'aq-deprecated-badge', 'Deprecated'));
        row.appendChild(el('span', 'aq-op-expand', '›'));
        card.appendChild(row);

        let body = null;
        row.addEventListener('click', () => {
            if (body) {
                const expanded = card.classList.toggle('expanded');
                body.hidden = !expanded;
                if (expanded) setURLHash(op.operationId);
                return;
            }
            body = buildOperationBody(path, method, op);
            card.appendChild(body);
            card.classList.add('expanded');
            setURLHash(op.operationId);
        });

        return card;
    }

    function buildOperationBody(path, method, op) {
        const body = el('div', 'aq-op-body');
        if (op.description) body.appendChild(el('p', 'aq-op-desc', op.description));

        const tabs = el('div', 'aq-tabs');
        const panel = el('div', 'aq-tab-panel');
        const tabDefs = [
            ['Parameters', () => renderParameters(op.parameters || [], op.requestBody)],
            ['Responses', () => renderResponses(op.responses || {})],
            ['Code', () => renderCodeSnippets(path, method, op)],
            ['◈ Aquilia', () => renderAquiliaTab(op)],
        ];
        const rendered = new Map();
        let activeBtn = null;

        for (const [label, renderFn] of tabDefs) {
            const btn = el('button', 'aq-tab', label);
            btn.addEventListener('click', () => {
                if (activeBtn) activeBtn.classList.remove('active');
                btn.classList.add('active');
                activeBtn = btn;
                panel.textContent = '';
                if (!rendered.has(label)) rendered.set(label, renderFn());
                panel.appendChild(rendered.get(label));
            });
            tabs.appendChild(btn);
            if (!activeBtn) { activeBtn = btn; }
        }
        body.appendChild(tabs);
        body.appendChild(panel);
        // Activate first tab
        tabs.firstChild.classList.add('active');
        rendered.set(tabDefs[0][0], tabDefs[0][1]());
        panel.appendChild(rendered.get(tabDefs[0][0]));

        if (!op['x-specula-websocket']) {
            const tryBtn = el('button', 'aq-tryit-btn', '▶ Try it out');
            tryBtn.addEventListener('click', () => openTryItInline(path, method, op, body, tryBtn));
            body.appendChild(tryBtn);
        }
        return body;
    }

    // ── Parameters tab ─────────────────────────────────────────────────
    function renderParameters(params, requestBody) {
        const container = el('div');
        if (!params.length && !requestBody) {
            container.appendChild(el('p', 'aq-response-desc', 'No parameters.'));
            return container;
        }
        for (const p of params) {
            const row = el('div', 'aq-param');
            row.appendChild(el('span', 'aq-param-name' + (p.required ? ' required' : ''), p.name));
            row.appendChild(el('span', 'aq-in-pill', p.in));
            row.appendChild(typePill(p.schema));
            if (p.description) row.appendChild(el('div', 'aq-param-desc', p.description));
            container.appendChild(row);
        }
        if (requestBody) {
            container.appendChild(el('div', 'aq-section-title', 'Request body'));
            const content = requestBody.content || {};
            for (const [mime, media] of Object.entries(content)) {
                container.appendChild(el('span', 'aq-in-pill', mime));
                container.appendChild(renderSchemaTree(media.schema || {}, 0));
            }
        }
        return container;
    }

    // ── Responses tab ──────────────────────────────────────────────────
    function statusClass(code) {
        const c = code[0];
        return c === '2' ? '2xx' : c === '3' ? '3xx' : c === '4' ? '4xx' : '5xx';
    }

    function renderResponses(responses) {
        const container = el('div');
        for (const [code, resp] of Object.entries(responses)) {
            const details = el('details', 'aq-response');
            const summary = el('summary');
            summary.appendChild(el('span', 'aq-status aq-status-' + statusClass(code), code));
            summary.appendChild(el('span', 'aq-response-desc', resp.description || ''));
            details.appendChild(summary);
            const content = resp.content || {};
            for (const [mime, media] of Object.entries(content)) {
                details.appendChild(el('span', 'aq-in-pill', mime));
                if (media.schema) details.appendChild(renderSchemaTree(media.schema, 0));
            }
            container.appendChild(details);
        }
        return container;
    }

    // ── Schema tree ────────────────────────────────────────────────────
    function renderSchemaTree(schema, depth) {
        const container = el('div', depth === 0 ? 'aq-schema-tree' : 'aq-schema-node');
        if (depth > 6 || !schema) {
            container.appendChild(el('span', 'aq-schema-desc', '…'));
            return container;
        }
        if (schema.$ref) {
            const name = schema.$ref.split('/').pop();
            const resolved = resolveRef(schema.$ref);
            if (resolved && (resolved.properties || resolved.items || resolved.$ref)) {
                const header = el('div', 'aq-schema-ref-header');
                const link = el('span', 'aq-ref-link aq-type-pill aq-type-object', name);
                link.addEventListener('click', () => showSchemaModal(name));
                header.appendChild(link);
                container.appendChild(header);

                const children = el('div', 'aq-schema-children');
                children.appendChild(renderSchemaTree(resolved, depth + 1));
                container.appendChild(children);
                return container;
            } else {
                const link = el('span', 'aq-ref-link aq-type-pill aq-type-object', name);
                link.addEventListener('click', () => showSchemaModal(name));
                container.appendChild(link);
                return container;
            }
        }
        const required = new Set(schema.required || []);
        if (schema.properties) {
            for (const [prop, sub] of Object.entries(schema.properties)) {
                const node = el('div', 'aq-schema-node');
                node.appendChild(el('span', 'aq-schema-prop', prop));
                if (required.has(prop)) node.appendChild(el('span', 'aq-schema-req', ' *'));
                node.appendChild(document.createTextNode(' '));
                node.appendChild(typePill(sub));
                if (sub && sub.description) node.appendChild(el('span', 'aq-schema-desc', ' ' + sub.description));
                const inner = sub && (sub.properties || (sub.items && (sub.items.properties || sub.items.$ref)) || sub.$ref);
                if (inner) {
                    const children = el('div', 'aq-schema-children');
                    children.appendChild(renderSchemaTree(sub.items || sub, depth + 1));
                    node.appendChild(children);
                }
                container.appendChild(node);
            }
        } else if (schema.items) {
            container.appendChild(typePill(schema));
            const children = el('div', 'aq-schema-children');
            children.appendChild(renderSchemaTree(schema.items, depth + 1));
            container.appendChild(children);
        } else {
            container.appendChild(typePill(schema));
            if (schema.enum) container.appendChild(el('span', 'aq-schema-desc', ' one of: ' + schema.enum.join(', ')));
        }
        return container;
    }

    // ── Code snippets ──────────────────────────────────────────────────
    function exampleUrl(path) {
        const server = (spec.servers && spec.servers[0] && spec.servers[0].url) || '/';
        const base = server === '/' ? window.location.origin : server.replace(/\/$/, '');
        return base + path;
    }
    function bodyExample(op) {
        const media = op.requestBody && op.requestBody.content && op.requestBody.content['application/json'];
        if (!media) return null;
        return JSON.stringify(synthesize(media.schema || {}, 3), null, 2);
    }
    function synthesize(schema, depth) {
        if (!schema || depth < 0) return null;
        if (schema.$ref) return synthesize(resolveRef(schema.$ref), depth - 1);
        if (schema.example !== undefined) return schema.example;
        if (schema.enum) return schema.enum[0];
        if (schema.oneOf) { const nn = schema.oneOf.find(s => s.type !== 'null'); return synthesize(nn || schema.oneOf[0], depth - 1); }
        switch (schema.type) {
            case 'string': return schema.format === 'email' ? 'user@example.com' : schema.format === 'uuid' ? '550e8400-e29b-41d4-a716-446655440000' : 'string';
            case 'integer': return 42;
            case 'number': return 3.14;
            case 'boolean': return true;
            case 'null': return null;
            case 'array': return [synthesize(schema.items, depth - 1)];
            default: {
                const out = {};
                for (const [k, v] of Object.entries(schema.properties || {})) out[k] = synthesize(v, depth - 1);
                return out;
            }
        }
    }

    function buildCurlSnippet(path, method, op) {
        const url = exampleUrl(path);
        let cmd = 'curl -X ' + method.toUpperCase() + " '" + url + "'";
        const hasAuth = op.security || (op['x-specula-security'] && op['x-specula-security'].authenticated);
        if (hasAuth) cmd += " \\\n  -H 'Authorization: Bearer $TOKEN'";
        const body = bodyExample(op);
        if (body) cmd += " \\\n  -H 'Content-Type: application/json' \\\n  -d '" + body.replace(/\n\s*/g, ' ') + "'";
        return cmd;
    }
    function buildPythonSnippet(path, method, op) {
        const url = exampleUrl(path);
        let lines = ['from aquilia.http import AsyncHTTPClient', ''];
        const args = ["'" + url + "'"];
        const hasAuth = op.security || (op['x-specula-security'] && op['x-specula-security'].authenticated);
        if (hasAuth) { lines.push("headers = {'Authorization': f'Bearer {token}'}"); args.push('headers=headers'); }
        const body = bodyExample(op);
        if (body) { lines.push('payload = ' + body.replace(/"([^"]+)":/g, "'$1':").replace(/"/g, "'")); args.push('json=payload'); }
        lines.push('', 'async with AsyncHTTPClient() as client:');
        lines.push('    response = await client.' + method.toLowerCase() + '(' + args.join(', ') + ')');
        lines.push('    print(await response.json())');
        return lines.join('\n');
    }
    function buildJSSnippet(path, method, op) {
        const url = exampleUrl(path);
        const body = bodyExample(op);
        let opts = ["method: '" + method.toUpperCase() + "'"];
        const headers = [];
        const hasAuth = op.security || (op['x-specula-security'] && op['x-specula-security'].authenticated);
        if (hasAuth) headers.push("'Authorization': `Bearer ${token}`");
        if (body) headers.push("'Content-Type': 'application/json'");
        if (headers.length) opts.push('headers: { ' + headers.join(', ') + ' }');
        if (body) opts.push('body: JSON.stringify(' + body + ')');
        return "const response = await fetch('" + url + "', {\n  " + opts.join(',\n  ') + '\n});\nconst data = await response.json();';
    }
    function buildTSSnippet(path, method, op) {
        const url = exampleUrl(path);
        const body = bodyExample(op);
        let lines = ["import axios from 'axios';", ''];
        const args = ["'" + url + "'"];
        if (body) args.push(body.replace(/\n/g, '\n  '));
        let config = [];
        const hasAuth = op.security || (op['x-specula-security'] && op['x-specula-security'].authenticated);
        if (hasAuth) config.push("headers: { Authorization: `Bearer ${token}` }");
        if (config.length) args.push('{ ' + config.join(', ') + ' }');
        lines.push('const { data } = await axios.' + method.toLowerCase() + '<unknown>(' + args.join(', ') + ');');
        return lines.join('\n');
    }

    function renderCodeSnippets(path, method, op) {
        const container = el('div');
        const langs = [
            ['curl', 'bash', buildCurlSnippet],
            ['Python', 'python', buildPythonSnippet],
            ['JavaScript', 'javascript', buildJSSnippet],
            ['TypeScript', 'typescript', buildTSSnippet],
        ];
        const tabs = el('div', 'aq-tabs');
        const panel = el('div');
        let activeBtn = null;
        for (const [label, lang, buildFn] of langs) {
            const btn = el('button', 'aq-tab', label);
            btn.addEventListener('click', () => {
                if (activeBtn) activeBtn.classList.remove('active');
                btn.classList.add('active');
                activeBtn = btn;
                panel.textContent = '';
                panel.appendChild(codeBlock(buildFn(path, method, op), lang));
            });
            tabs.appendChild(btn);
        }
        container.appendChild(tabs);
        container.appendChild(panel);
        tabs.firstChild.click();
        return container;
    }

    // ── Aquilia info tab ───────────────────────────────────────────────
    function renderAquiliaTab(op) {
        const container = el('div');
        const rows = [
            ['Module', op['x-specula-module']],
            ['Version', op['x-specula-version']],
        ];
        for (const [label, value] of rows) {
            if (!value) continue;
            const row = el('div', 'aq-meta-row');
            row.appendChild(el('span', 'aq-meta-label', label));
            row.appendChild(el('span', '', Array.isArray(value) ? value.join(', ') : String(value)));
            container.appendChild(row);
        }
        
        const sec = op['x-specula-security'];
        if (sec) {
            const secCard = el('div', 'aq-security-card');
            
            const title = el('div', 'aq-security-title');
            title.innerHTML = LOCK_ICON_SVG + ' Security & Access Control';
            secCard.appendChild(title);
            
            if (sec.authenticated) {
                const item = el('div', 'aq-security-item');
                item.appendChild(el('span', 'aq-security-item-label', 'Requires Authentication:'));
                item.appendChild(el('span', '', 'Yes'));
                secCard.appendChild(item);
            }
            
            if (sec.guards && sec.guards.length) {
                const item = el('div', 'aq-security-item');
                item.appendChild(el('span', 'aq-security-item-label', 'Guards Pipeline:'));
                const wrap = el('div');
                wrap.style.marginTop = '4px';
                sec.guards.forEach(g => {
                    let desc = g.name;
                    if (g.optional) desc += ' (optional)';
                    if (g.roles && g.roles.length) {
                        desc += ` [roles: ${g.roles.join(', ')}${g.require_all ? ' (all)' : ' (any)'}]`;
                    }
                    if (g.scopes && g.scopes.length) {
                        desc += ` [scopes: ${g.scopes.join(', ')}${g.require_all ? ' (all)' : ' (any)'}]`;
                    }
                    if (g.key) desc += ` [policy: ${g.key}]`;
                    
                    const gEl = el('div', 'aq-guard-stage', desc);
                    wrap.appendChild(gEl);
                });
                item.appendChild(wrap);
                secCard.appendChild(item);
            }
            
            if (sec.clearance) {
                const c = sec.clearance;
                const clearanceSection = el('div');
                clearanceSection.style.marginTop = '12px';
                clearanceSection.style.paddingTop = '12px';
                clearanceSection.style.borderTop = '1px solid var(--aq-border-subtle)';
                
                const cTitle = el('div', 'aq-security-item-label');
                cTitle.style.marginBottom = '8px';
                cTitle.textContent = 'Clearance Requirements:';
                clearanceSection.appendChild(cTitle);
                
                const lvlItem = el('div', 'aq-security-item');
                lvlItem.appendChild(el('span', 'aq-security-item-label', 'Access Level:'));
                const badge = el('span', 'aq-clearance-badge level-' + String(c.level).toLowerCase(), c.level);
                lvlItem.appendChild(badge);
                clearanceSection.appendChild(lvlItem);
                
                if (c.entitlements && c.entitlements.length) {
                    const entItem = el('div', 'aq-security-item');
                    entItem.appendChild(el('span', 'aq-security-item-label', 'Entitlements:'));
                    entItem.appendChild(el('span', '', c.entitlements.join(', ')));
                    clearanceSection.appendChild(entItem);
                }
                
                if (c.conditions && c.conditions.length) {
                    const condItem = el('div', 'aq-security-item');
                    condItem.appendChild(el('span', 'aq-security-item-label', 'Conditions:'));
                    condItem.appendChild(el('span', '', c.conditions.join(', ')));
                    clearanceSection.appendChild(condItem);
                }
                
                if (c.compartment) {
                    const compItem = el('div', 'aq-security-item');
                    compItem.appendChild(el('span', 'aq-security-item-label', 'Compartment:'));
                    compItem.appendChild(el('span', 'aq-pipeline-stage', c.compartment));
                    clearanceSection.appendChild(compItem);
                }
                
                secCard.appendChild(clearanceSection);
            }
            container.appendChild(secCard);
        }

        const effects = op['x-specula-effects'] || [];
        if (effects.length) {
            const row = el('div', 'aq-meta-row');
            row.appendChild(el('span', 'aq-meta-label', 'Effects'));
            const wrap = el('span');
            for (const eff of effects) {
                const chip = el('span', 'aq-chip', eff);
                chip.title = EFFECT_DOCS[eff] || 'Aquilia effect: ' + eff;
                wrap.appendChild(chip);
            }
            row.appendChild(wrap);
            container.appendChild(row);
        }
        const pipeline = op['x-specula-pipeline'] || [];
        if (pipeline.length) {
            const row = el('div', 'aq-meta-row');
            row.appendChild(el('span', 'aq-meta-label', 'Pipeline'));
            const wrap = el('span');
            pipeline.forEach((stage, i) => {
                wrap.appendChild(el('span', 'aq-pipeline-stage', (i + 1) + '. ' + stage));
            });
            row.appendChild(wrap);
            container.appendChild(row);
        }
        if (op['x-specula-throttle']) {
            const row = el('div', 'aq-meta-row');
            row.appendChild(el('span', 'aq-meta-label', 'Throttle'));
            row.appendChild(el('span', '', JSON.stringify(op['x-specula-throttle'])));
            container.appendChild(row);
        }
        if (!container.children.length) {
            container.appendChild(el('p', 'aq-response-desc', 'No Aquilia metadata for this operation.'));
        }
        return container;
    }

    // ── Panel plumbing ─────────────────────────────────────────────────
    function openPanel(title, buildBody) {
        const panel = document.getElementById('aq-tryit');
        document.getElementById('aq-tryit-label').textContent = title;
        const body = document.getElementById('aq-tryit-body');
        body.textContent = '';
        buildBody(body);
        panel.hidden = false;
        requestAnimationFrame(() => panel.classList.add('open'));
    }
    function closeTryIt() {
        const panel = document.getElementById('aq-tryit');
        panel.classList.remove('open');
        setTimeout(() => { panel.hidden = true; }, 200);
    }

    // ── Try It Out ─────────────────────────────────────────────────────
    function openTryItInline(path, method, op, parentContainer, tryBtn) {
        tryBtn.style.display = 'none';
        
        const tryItDiv = el('div', 'aq-inline-tryit');
        tryItDiv.style.marginTop = '24px';
        tryItDiv.style.padding = '20px 0 0 0';
        tryItDiv.style.border = 'none';
        tryItDiv.style.borderTop = '1px solid var(--aq-border)';
        tryItDiv.style.background = 'transparent';
        
        const header = el('div');
        header.style.display = 'flex';
        header.style.justifyContent = 'space-between';
        header.style.alignItems = 'center';
        header.style.marginBottom = '20px';
        
        const titleSpan = el('span', '', 'Try It Out');
        titleSpan.style.fontSize = '12px';
        titleSpan.style.letterSpacing = '0.08em';
        titleSpan.style.textTransform = 'uppercase';
        titleSpan.style.fontWeight = '700';
        titleSpan.style.color = 'var(--aq-accent)';
        header.appendChild(titleSpan);
        
        const closeBtn = el('button', 'aq-spec-btn');
        closeBtn.textContent = 'Cancel';
        closeBtn.style.padding = '4px 10px';
        closeBtn.style.fontSize = '11px';
        closeBtn.style.height = '24px';
        closeBtn.style.display = 'inline-flex';
        closeBtn.style.alignItems = 'center';
        closeBtn.style.justifyContent = 'center';
        closeBtn.style.borderRadius = 'var(--aq-radius-sm)';
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            tryItDiv.remove();
            tryBtn.style.display = 'inline-flex';
        });
        header.appendChild(closeBtn);
        tryItDiv.appendChild(header);

        const state = {pathParams: {}, queryParams: {}, headers: {}, token: '', body: '', bodyType: ''};

        // Server selector
        const serverField = el('div', 'aq-field');
        serverField.appendChild(el('label', '', 'Server'));
        const serverSelectContainer = el('div');
        serverField.appendChild(serverSelectContainer);
        tryItDiv.appendChild(serverField);

        const serverOptions = (spec.servers || [{url: '/'}]).map(s => ({
            label: s.url + (s.description ? ' — ' + s.description : ''),
            value: s.url
        }));
        const customServerDropdown = createCustomDropdown(serverSelectContainer, serverOptions, serverOptions[0]?.value);

        // Auth
        const hasAuth = op.security || (op['x-specula-security'] && op['x-specula-security'].authenticated);
        if (hasAuth) {
            const authField = el('div', 'aq-field');
            authField.appendChild(el('label', '', 'Bearer token'));
            const tokenInput = el('input');
            tokenInput.type = 'password';
            tokenInput.placeholder = 'eyJhbGciOi...';
            tokenInput.addEventListener('input', () => { state.token = tokenInput.value; });
            authField.appendChild(tokenInput);
            tryItDiv.appendChild(authField);
        }

        // Path params
        const pathParams = (op.parameters || []).filter(p => p.in === 'path');
        if (pathParams.length) tryItDiv.appendChild(el('div', 'aq-section-title', 'Path parameters'));
        for (const p of pathParams) {
            const field = el('div', 'aq-field');
            field.appendChild(el('label', '', p.name + (p.required ? ' *' : '')));
            const input = el('input');
            input.placeholder = schemaTypeName(p.schema);
            input.addEventListener('input', () => { state.pathParams[p.name] = input.value; });
            field.appendChild(input);
            tryItDiv.appendChild(field);
        }

        // Query params
        const queryParams = (op.parameters || []).filter(p => p.in === 'query');
        if (queryParams.length) tryItDiv.appendChild(el('div', 'aq-section-title', 'Query parameters'));
        for (const p of queryParams) {
            const field = el('div', 'aq-field');
            field.appendChild(el('label', '', p.name));
            const input = el('input');
            input.placeholder = schemaTypeName(p.schema);
            input.addEventListener('input', () => {
                if (input.value) state.queryParams[p.name] = input.value;
                else delete state.queryParams[p.name];
            });
            field.appendChild(input);
            tryItDiv.appendChild(field);
        }

        // Request body
        if (op.requestBody) {
            tryItDiv.appendChild(el('div', 'aq-section-title', 'Request body'));
            
            const bodyTypeField = el('div', 'aq-field');
            bodyTypeField.appendChild(el('label', '', 'Content-Type'));
            const bodyTypeSelectContainer = el('div');
            bodyTypeField.appendChild(bodyTypeSelectContainer);
            tryItDiv.appendChild(bodyTypeField);
            
            const bodyOptions = [
                { label: 'JSON (application/json)', value: 'application/json' },
                { label: 'Multipart Form (multipart/form-data)', value: 'multipart/form-data' },
                { label: 'Form URL Encoded (application/x-www-form-urlencoded)', value: 'application/x-www-form-urlencoded' },
                { label: 'XML (application/xml)', value: 'application/xml' },
                { label: 'Plain Text (text/plain)', value: 'text/plain' }
            ];
            
            const specContentTypes = Object.keys(op.requestBody.content || {});
            let defaultBodyType = 'application/json';
            if (specContentTypes.length > 0) {
                const match = bodyOptions.find(o => specContentTypes.includes(o.value));
                if (match) defaultBodyType = match.value;
                else defaultBodyType = specContentTypes[0];
            }
            
            specContentTypes.forEach(t => {
                if (!bodyOptions.find(o => o.value === t)) {
                    bodyOptions.push({ label: t, value: t });
                }
            });
            
            const editorArea = el('div', 'aq-body-editor-area');
            tryItDiv.appendChild(editorArea);
            
            let activeBodyType = defaultBodyType;
            state.bodyType = activeBodyType;
            
            const renderEditor = (type) => {
                editorArea.textContent = '';
                activeBodyType = type;
                state.bodyType = type;
                
                if (type === 'multipart/form-data' || type === 'application/x-www-form-urlencoded') {
                    renderKeyValueEditor(editorArea, type, op, state);
                } else {
                    renderCodeEditor(editorArea, type, op, state);
                }
            };
            
            createCustomDropdown(bodyTypeSelectContainer, bodyOptions, defaultBodyType, (val) => {
                renderEditor(val);
            });
            
            renderEditor(defaultBodyType);
        }

        // Send button + response area
        const sendBtn = el('button', 'aq-send-btn', '▶ Send Request');
        const respArea = el('div');
        sendBtn.addEventListener('click', async () => {
            sendBtn.disabled = true;
            sendBtn.textContent = 'Sending…';
            try {
                await sendRequest(customServerDropdown.getValue(), path, method, op, state, respArea);
            } finally {
                sendBtn.disabled = false;
                sendBtn.textContent = '▶ Send Request';
            }
        });
        tryItDiv.appendChild(sendBtn);

        // Copy as cURL
        const curlBtn = el('button', 'aq-spec-btn', 'Copy as cURL');
        curlBtn.style.marginLeft = '8px';
        curlBtn.addEventListener('click', () => {
            copyToClipboard(buildCurlFromState(customServerDropdown.getValue(), path, method, state));
        });
        tryItDiv.appendChild(curlBtn);
        tryItDiv.appendChild(respArea);

        parentContainer.appendChild(tryItDiv);
    }

    function buildUrlFromState(server, path, state) {
        let url = path;
        for (const [k, v] of Object.entries(state.pathParams)) {
            url = url.replace('{' + k + '}', encodeURIComponent(v));
        }
        const base = server === '/' ? '' : server.replace(/\/$/, '');
        const query = new URLSearchParams(state.queryParams).toString();
        return base + url + (query ? '?' + query : '');
    }
    function buildCurlFromState(server, path, method, state) {
        let cmd = 'curl -X ' + method.toUpperCase() + " '" + buildUrlFromState(server, path, state) + "'";
        if (state.token) cmd += " \\\n  -H 'Authorization: Bearer " + state.token + "'";
        
        if (method.toUpperCase() !== 'GET' && method.toUpperCase() !== 'HEAD') {
            if (state.bodyType === 'multipart/form-data') {
                (state.formParams || []).forEach(p => {
                    if (p.key) {
                        if (p.type === 'file') {
                            const fileName = p.value instanceof File ? p.value.name : 'file';
                            cmd += " \\\n  -F '" + p.key + "=@" + fileName + "'";
                        } else {
                            cmd += " \\\n  -F '" + p.key + "=" + p.value + "'";
                        }
                    }
                });
            } else if (state.bodyType === 'application/x-www-form-urlencoded') {
                cmd += " \\\n  -H 'Content-Type: application/x-www-form-urlencoded'";
                const params = (state.formParams || []).map(p => {
                    return p.key ? encodeURIComponent(p.key) + '=' + encodeURIComponent(p.value) : '';
                }).filter(Boolean).join('&');
                if (params) {
                    cmd += " \\\n  -d '" + params + "'";
                }
            } else if (state.bodyType) {
                cmd += " \\\n  -H 'Content-Type: " + state.bodyType + "'";
                if (state.body) {
                    cmd += " \\\n  -d '" + state.body.replace(/\n\s*/g, ' ') + "'";
                }
            } else if (state.body) {
                cmd += " \\\n  -H 'Content-Type: application/json' \\\n  -d '" + state.body.replace(/\n\s*/g, ' ') + "'";
            }
        }
        return cmd;
    }

    async function sendRequest(server, path, method, op, state, respArea) {
        const url = buildUrlFromState(server, path, state);
        const headers = {};
        if (state.token) headers['Authorization'] = 'Bearer ' + state.token;
        const init = {method: method.toUpperCase(), headers};
        
        if (!['GET', 'HEAD'].includes(init.method)) {
            if (state.bodyType === 'multipart/form-data') {
                const formData = new FormData();
                (state.formParams || []).forEach(p => {
                    if (p.key) {
                        formData.append(p.key, p.value);
                    }
                });
                init.body = formData;
            } else if (state.bodyType === 'application/x-www-form-urlencoded') {
                headers['Content-Type'] = 'application/x-www-form-urlencoded';
                const urlParams = new URLSearchParams();
                (state.formParams || []).forEach(p => {
                    if (p.key) {
                        urlParams.append(p.key, p.value);
                    }
                });
                init.body = urlParams.toString();
            } else if (state.bodyType) {
                headers['Content-Type'] = state.bodyType;
                init.body = state.body;
            } else if (state.body) {
                headers['Content-Type'] = 'application/json';
                init.body = state.body;
            }
        }
        const start = performance.now();
        respArea.textContent = '';
        try {
            const res = await fetch(url, init);
            const latency = Math.round(performance.now() - start);
            const text = await res.text();
            addHistoryEntry(method, path, res.status, latency);

            const meta = el('div', 'aq-resp-meta');
            meta.appendChild(el('span', 'aq-status aq-status-' + statusClass(String(res.status)), String(res.status)));
            meta.appendChild(el('span', 'aq-latency', latency + ' ms'));
            respArea.appendChild(meta);

            // Response headers accordion
            const headersDetails = el('details', 'aq-response');
            headersDetails.appendChild(el('summary', 'aq-response-desc', 'Response headers'));
            const headerLines = [];
            res.headers.forEach((v, k) => headerLines.push(k + ': ' + v));
            headersDetails.appendChild(codeBlock(headerLines.join('\n'), 'bash'));
            respArea.appendChild(headersDetails);

            // Inspector trace link (dev mode)
            const requestId = res.headers.get('x-request-id');
            if (requestId) {
                const trace = el('a', 'aq-spec-btn', 'Trace ↗');
                trace.href = '/__aquilia__/inspector/#' + requestId;
                trace.target = '_blank';
                respArea.appendChild(trace);
            }

            const contentType = res.headers.get('content-type') || '';
            if (contentType.includes('json')) {
                try {
                    respArea.appendChild(codeBlock(JSON.stringify(JSON.parse(text), null, 2), 'json'));
                } catch { respArea.appendChild(codeBlock(text, 'json')); }
            } else {
                respArea.appendChild(codeBlock(text.slice(0, 20000), 'bash'));
            }
        } catch (e) {
            respArea.appendChild(el('p', '', 'Request failed: ' + e.message));
            addHistoryEntry(method, path, 'ERR', 0);
        }
    }

    // ── Search ─────────────────────────────────────────────────────────
    function buildSearchIndex() {
        searchIndex = [];
        for (const [path, item] of Object.entries(spec.paths || {})) {
            if (!item || typeof item !== 'object') continue;
            for (const [method, op] of Object.entries(item)) {
                if (method.startsWith('x-') || typeof op !== 'object') continue;
                searchIndex.push({
                    type: 'operation', method, path,
                    opId: op.operationId || '',
                    summary: op.summary || '',
                    description: op.description || '',
                    tags: op.tags || [],
                    module: op['x-specula-module'] || '',
                });
            }
        }
        for (const name of Object.keys((spec.components && spec.components.schemas) || {})) {
            searchIndex.push({type: 'schema', name});
        }
    }

    function search(query) {
        const q = query.toLowerCase();
        const scored = [];
        for (const entry of searchIndex) {
            let score = 0;
            if (entry.type === 'operation') {
                if (entry.opId.toLowerCase() === q) score = 100;
                else if (entry.path.toLowerCase() === q) score = 80;
                else if (entry.summary.toLowerCase() === q) score = 60;
                else if (entry.opId.toLowerCase().includes(q) || entry.path.toLowerCase().includes(q)) score = 50;
                else if (entry.summary.toLowerCase().includes(q) || entry.description.toLowerCase().includes(q)) score = 40;
                else if (entry.tags.some(t => t.toLowerCase().includes(q)) || entry.module.toLowerCase().includes(q)) score = 20;
            } else if (entry.name.toLowerCase().includes(q)) {
                score = entry.name.toLowerCase() === q ? 30 : 10;
            }
            if (score > 0) scored.push({entry, score});
        }
        scored.sort((a, b) => b.score - a.score);
        return scored.slice(0, 20).map(s => s.entry);
    }

    function openSearch() {
        document.getElementById('aq-search-modal').hidden = false;
        document.getElementById('aq-search-input').focus();
        searchSelection = 0;
    }
    function closeSearch() {
        document.getElementById('aq-search-modal').hidden = true;
        document.getElementById('aq-search-input').value = '';
        document.getElementById('aq-search-results').textContent = '';
    }

    function renderSearchResults(results) {
        const container = document.getElementById('aq-search-results');
        container.textContent = '';
        if (!results.length) {
            container.appendChild(el('div', 'aq-search-empty', 'No results.'));
            return;
        }
        results.forEach((entry, i) => {
            const row = el('div', 'aq-search-result' + (i === searchSelection ? ' selected' : ''));
            if (entry.type === 'operation') {
                row.appendChild(el('span', 'aq-method aq-method-' + entry.method, entry.method.slice(0, 3).toUpperCase()));
                row.appendChild(el('span', 'aq-op-path', entry.path));
                row.appendChild(el('span', 'aq-op-summary', entry.summary));
                row.addEventListener('click', () => { closeSearch(); jumpToOperation(entry.opId); });
            } else {
                row.appendChild(el('span', 'aq-search-kind', 'schema'));
                row.appendChild(el('span', 'aq-op-path', entry.name));
                row.addEventListener('click', () => { closeSearch(); showSchemaModal(entry.name); });
            }
            container.appendChild(row);
        });
    }

    function jumpToOperation(opId) {
        if (!opId) return;
        const card = document.getElementById(opDomId(opId));
        if (!card) return;
        card.scrollIntoView({behavior: 'smooth', block: 'start'});
        if (!card.classList.contains('expanded')) card.querySelector('.aq-op-row').click();
        setURLHash(opId);
        document.getElementById('aq-sidebar').classList.remove('open');
    }

    // ── Version selector ───────────────────────────────────────────────
    async function renderVersionSelector() {
        const container = document.getElementById('aq-version-selector-container');
        try {
            const res = await fetch(cfg.versionsUrl);
            if (!res.ok) return;
            const data = await res.json();
            const versions = data.versions || [];
            if (versions.length <= 1) return;
            const options = versions.map(v => ({ label: v, value: v }));
            createCustomDropdown(container, options, 'latest', (val) => {
                selectVersion(val);
            });
            container.style.display = '';
        } catch { /* versioning inactive */ }
    }

    async function selectVersion(v) {
        activeVersion = v;
        const url = v && v !== 'latest' ? cfg.specUrl + '?version=' + encodeURIComponent(v) : cfg.specUrl;
        document.getElementById('aq-loading').hidden = false;
        document.getElementById('aq-operations').hidden = true;
        try {
            await loadSpec(url);
            showToast('Switched to version ' + v, 'info');
            populateObservatoryStats();
        } catch (e) {
            showError('Failed to load version ' + v + ': ' + e.message);
        }
    }

    // ── SSE live reload ────────────────────────────────────────────────
    function connectSSE() {
        if (!cfg.streamUrl || !window.EventSource) return;
        try { sse = new EventSource(cfg.streamUrl); } catch { return; }
        sse.addEventListener('spec:invalidated', async () => {
            await loadSpec(activeVersion && activeVersion !== 'latest'
                ? cfg.specUrl + '?version=' + encodeURIComponent(activeVersion)
                : cfg.specUrl);
            showToast('Spec updated', 'info');
        });
        sse.onopen = () => { sseRetry = 1000; };
        sse.onerror = () => {
            sse.close();
            setTimeout(connectSSE, sseRetry);
            sseRetry = Math.min(sseRetry * 2, 30000);
        };
    }

    // ── Theme ──────────────────────────────────────────────────────────
    function toggleTheme() {
        const cycle = {auto: 'dark', dark: 'light', light: 'auto'};
        theme = cycle[theme] || 'dark';
        localStorage.setItem('specula-theme', theme);
        applyTheme(theme);
        showToast('Theme: ' + theme, 'info');
    }
    function applyTheme(t) {
        const resolved = t === 'auto'
            ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
            : t;
        document.documentElement.setAttribute('data-theme', resolved);
        document.documentElement.setAttribute('data-theme-pref', t);
    }

    // ── Expand all ─────────────────────────────────────────────────────
    let allExpanded = false;
    function toggleExpandAll() {
        allExpanded = !allExpanded;
        document.querySelectorAll('.aq-operation').forEach(card => {
            const expanded = card.classList.contains('expanded');
            if (expanded !== allExpanded) card.querySelector('.aq-op-row').click();
        });
    }

    // ── Keyboard ───────────────────────────────────────────────────────
    function setupKeyboard() {
        document.addEventListener('keydown', e => {
            const mod = e.metaKey || e.ctrlKey;
            if (mod && e.key === 'k') { e.preventDefault(); openSearch(); }
            if (mod && e.shiftKey && (e.key === 'L' || e.key === 'l')) { e.preventDefault(); toggleTheme(); }
            if (mod && e.key === 'e') { e.preventDefault(); toggleExpandAll(); }
            if (e.key === 'Escape') {
                if (!document.getElementById('aq-search-modal').hidden) closeSearch();
                else if (document.getElementById('aq-tryit').classList.contains('open')) closeTryIt();
            }
        });

        const input = document.getElementById('aq-search-input');
        input.addEventListener('input', e => {
            const q = e.target.value.trim();
            searchSelection = 0;
            if (q.length < 2) {
                document.getElementById('aq-search-results').textContent = '';
                return;
            }
            renderSearchResults(search(q));
        });
        input.addEventListener('keydown', e => {
            const results = document.querySelectorAll('.aq-search-result');
            if (e.key === 'ArrowDown') { e.preventDefault(); searchSelection = Math.min(searchSelection + 1, results.length - 1); }
            else if (e.key === 'ArrowUp') { e.preventDefault(); searchSelection = Math.max(searchSelection - 1, 0); }
            else if (e.key === 'Enter' && results[searchSelection]) { results[searchSelection].click(); return; }
            else return;
            results.forEach((r, i) => r.classList.toggle('selected', i === searchSelection));
        });
    }

    // ── Observatory Live panel logic ──
    function populateObservatoryStats() {
        const paths = spec.paths || {};
        let endpointsCount = 0;
        const modulesSet = new Set();
        
        for (const [path, item] of Object.entries(paths)) {
            if (!item || typeof item !== 'object') continue;
            for (const [method, op] of Object.entries(item)) {
                if (method.startsWith('x-') || typeof op !== 'object') continue;
                endpointsCount++;
                if (op['x-specula-module']) {
                    modulesSet.add(op['x-specula-module']);
                }
            }
        }
        
        const schemasCount = Object.keys(spec.components?.schemas || {}).length;
        const modulesCount = modulesSet.size || 1;
        
        const modEl = document.getElementById('aq-stat-modules');
        if (modEl) modEl.textContent = String(modulesCount);
        const endEl = document.getElementById('aq-stat-endpoints');
        if (endEl) endEl.textContent = String(endpointsCount);
        const schEl = document.getElementById('aq-stat-schemas');
        if (schEl) schEl.textContent = String(schemasCount);
    }

    const requestHistory = [];
    function addHistoryEntry(method, path, status, latency) {
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const entry = { method, path, status, latency, timestamp };
        requestHistory.unshift(entry);
        if (requestHistory.length > 20) requestHistory.pop();
        renderHistory();
        updateAverageLatency();
    }
    
    function renderHistory() {
        const list = document.getElementById('aq-history-list');
        if (!list) return;
        list.textContent = '';
        if (requestHistory.length === 0) {
            list.appendChild(el('div', 'aq-sidebar-loading', 'No requests recorded yet.'));
            return;
        }
        
        requestHistory.forEach(item => {
            const row = el('div', 'aq-history-item');
            row.addEventListener('click', () => {
                const opId = findOperationIdByPath(item.path, item.method);
                if (opId) jumpToOperation(opId);
            });
            
            const top = el('div', 'aq-history-meta');
            const methodSpan = el('span', 'aq-history-method aq-method aq-method-' + item.method.toLowerCase(), item.method);
            methodSpan.style.fontSize = '9px';
            methodSpan.style.padding = '2px 4px';
            methodSpan.style.borderRadius = 'var(--aq-radius-sm)';
            top.appendChild(methodSpan);
            
            const statusSpan = el('span', 'aq-history-status aq-status aq-status-' + statusClass(String(item.status)), String(item.status));
            top.appendChild(statusSpan);
            row.appendChild(top);
            
            const middle = el('div', 'aq-history-path', item.path);
            row.appendChild(middle);
            
            const bottom = el('div', 'aq-history-meta');
            bottom.appendChild(el('span', 'aq-history-time', item.timestamp));
            bottom.appendChild(el('span', 'aq-history-time', item.latency ? item.latency + ' ms' : '--'));
            row.appendChild(bottom);
            
            list.appendChild(row);
        });
    }
    
    function updateAverageLatency() {
        const validLatencies = requestHistory.filter(h => h.latency > 0).map(h => h.latency);
        if (validLatencies.length === 0) return;
        const avg = Math.round(validLatencies.reduce((a, b) => a + b, 0) / validLatencies.length);
        const latEl = document.getElementById('aq-stat-latency');
        if (latEl) latEl.textContent = avg + 'ms';
    }

    function findOperationIdByPath(path, method) {
        const match = searchIndex.find(idx => idx.path === path && idx.method.toLowerCase() === method.toLowerCase());
        return match ? match.opId : null;
    }

    // ── URL state ──────────────────────────────────────────────────────
    function restoreFromURL() {
        const hash = location.hash.slice(1);
        if (hash) setTimeout(() => jumpToOperation(hash), 100);
    }

    // ── Public ─────────────────────────────────────────────────────────
    return {
        init, openSearch, closeSearch, closeTryIt,
        toggleTheme, selectVersion, scrollTop,
    };
})();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', Specula.init);
} else {
    Specula.init();
}
"""
