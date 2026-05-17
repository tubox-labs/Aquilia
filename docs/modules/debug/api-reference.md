# Debug Pages API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `DebugPageRenderer` | `aquilia/debug/pages.py` | object | Public class. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `render_debug_exception_page` | `aquilia/debug/pages.py` | `def render_debug_exception_page(exc: BaseException, request: Any = None, *, aquilia_version: str = '') -> str` | Public function. |
| `render_http_error_page` | `aquilia/debug/pages.py` | `def render_http_error_page(status_code: int, message: str = '', detail: str = '', request: Any = None, *, aquilia_version: str = '') -> str` | Public function. |
| `render_version_error_page` | `aquilia/debug/pages.py` | `def render_version_error_page(status_code: int, error_code: str, message: str = '', detail: str = '', request: Any = None, metadata: dict[str, Any] &#124; None = None, *, aquilia_version: str = '') -> str` | Render a themed HTML page for API versioning errors. |
| `render_welcome_page` | `aquilia/debug/pages.py` | `def render_welcome_page(*, aquilia_version: str = '', system_info: dict[str, Any] &#124; None = None) -> str` | Public function. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_REDACTED` | `aquilia/debug/pages.py` | `'[REDACTED]'` |
| `_SENSITIVE_HEADERS` | `aquilia/debug/pages.py` | `frozenset[str]` |
| `_SENSITIVE_VAR_PATTERNS` | `aquilia/debug/pages.py` | `tuple[str, ...]` |
| `_BASE_CSS` | `aquilia/debug/pages.py` | `"\n:root {\n  /* Dark Theme (Default) */\n  --tx-bg: #000000;\n  --tx-bg-alt: #0a0a0a;\n  --tx-surface: rgba(10, 10, 10, 0.8);\n  --tx-border: #222;\n  --tx-bor` |
| `_BASE_JS` | `aquilia/debug/pages.py` | `'\n(function() {\n  // Theme Toggle\n  const themeBtn = document.getElementById(\'theme-toggle\');\n  const iconMoon = document.getElementById(\'icon-moon\');\n` |

## Detailed Classes And Methods

### Class: `DebugPageRenderer`

- Source: `aquilia/debug/pages.py`
- Bases: `object`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render_exception` | `def render_exception(exc: BaseException, request: Any = None, *, aquilia_version: str = '') -> str` | staticmethod | Method. |
| `render_http_error` | `def render_http_error(status_code: int, message: str = '', detail: str = '', request: Any = None, *, aquilia_version: str = '') -> str` | staticmethod | Method. |
| `render_welcome` | `def render_welcome(*, aquilia_version: str = '', system_info: dict[str, Any] &#124; None = None) -> str` | staticmethod | Method. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `render_debug_exception_page` | `aquilia/debug/pages.py` | `def render_debug_exception_page(exc: BaseException, request: Any = None, *, aquilia_version: str = '') -> str` | Public function. |
| `render_http_error_page` | `aquilia/debug/pages.py` | `def render_http_error_page(status_code: int, message: str = '', detail: str = '', request: Any = None, *, aquilia_version: str = '') -> str` | Public function. |
| `render_version_error_page` | `aquilia/debug/pages.py` | `def render_version_error_page(status_code: int, error_code: str, message: str = '', detail: str = '', request: Any = None, metadata: dict[str, Any] &#124; None = None, *, aquilia_version: str = '') -> str` | Render a themed HTML page for API versioning errors. |
| `render_welcome_page` | `aquilia/debug/pages.py` | `def render_welcome_page(*, aquilia_version: str = '', system_info: dict[str, Any] &#124; None = None) -> str` | Public function. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_REDACTED` | `aquilia/debug/pages.py` | `'[REDACTED]'` |
| `_SENSITIVE_HEADERS` | `aquilia/debug/pages.py` | `frozenset[str]` |
| `_SENSITIVE_VAR_PATTERNS` | `aquilia/debug/pages.py` | `tuple[str, ...]` |
| `_BASE_CSS` | `aquilia/debug/pages.py` | `"\n:root {\n  /* Dark Theme (Default) */\n  --tx-bg: #000000;\n  --tx-bg-alt: #0a0a0a;\n  --tx-surface: rgba(10, 10, 10, 0.8);\n  --tx-border: #222;\n  --tx-bor` |
| `_BASE_JS` | `aquilia/debug/pages.py` | `'\n(function() {\n  // Theme Toggle\n  const themeBtn = document.getElementById(\'theme-toggle\');\n  const iconMoon = document.getElementById(\'icon-moon\');\n` |
