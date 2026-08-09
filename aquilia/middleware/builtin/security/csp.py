"""Content-Security-Policy — header builder with per-request nonce support."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class CSPPolicy:
    """
    Builder for Content-Security-Policy directives.

    Ecosystem Integration:
    - Uses fluent builder pattern (like Aquilia Serializers)
    - Validated at build time, not at creation time
    - Integrates with CSPMiddleware for per-request nonce injection
    - Configurable via Integration.csp() config builder

    Example::

        policy = (
            CSPPolicy()
            .default_src("'self'")
            .script_src("'self'", "'nonce-{nonce}'")
            .style_src("'self'", "'unsafe-inline'")
            .img_src("'self'", "data:", "https:")
            .connect_src("'self'", "wss:")
            .report_uri("/csp-report")
        )
    """

    __slots__ = ("directives", "report_only")

    def __init__(
        self,
        directives: dict[str, list[str]] | None = None,
        report_only: bool = False,
    ):
        self.directives: dict[str, list[str]] = directives if directives is not None else {}
        self.report_only = report_only

    def default_src(self, *sources: str) -> CSPPolicy:
        self.directives["default-src"] = list(sources)
        return self

    def script_src(self, *sources: str) -> CSPPolicy:
        self.directives["script-src"] = list(sources)
        return self

    def style_src(self, *sources: str) -> CSPPolicy:
        self.directives["style-src"] = list(sources)
        return self

    def img_src(self, *sources: str) -> CSPPolicy:
        self.directives["img-src"] = list(sources)
        return self

    def font_src(self, *sources: str) -> CSPPolicy:
        self.directives["font-src"] = list(sources)
        return self

    def connect_src(self, *sources: str) -> CSPPolicy:
        self.directives["connect-src"] = list(sources)
        return self

    def media_src(self, *sources: str) -> CSPPolicy:
        self.directives["media-src"] = list(sources)
        return self

    def object_src(self, *sources: str) -> CSPPolicy:
        self.directives["object-src"] = list(sources)
        return self

    def frame_src(self, *sources: str) -> CSPPolicy:
        self.directives["frame-src"] = list(sources)
        return self

    def frame_ancestors(self, *sources: str) -> CSPPolicy:
        self.directives["frame-ancestors"] = list(sources)
        return self

    def base_uri(self, *sources: str) -> CSPPolicy:
        self.directives["base-uri"] = list(sources)
        return self

    def form_action(self, *sources: str) -> CSPPolicy:
        self.directives["form-action"] = list(sources)
        return self

    def worker_src(self, *sources: str) -> CSPPolicy:
        self.directives["worker-src"] = list(sources)
        return self

    def child_src(self, *sources: str) -> CSPPolicy:
        self.directives["child-src"] = list(sources)
        return self

    def manifest_src(self, *sources: str) -> CSPPolicy:
        self.directives["manifest-src"] = list(sources)
        return self

    def upgrade_insecure_requests(self) -> CSPPolicy:
        self.directives["upgrade-insecure-requests"] = []
        return self

    def block_all_mixed_content(self) -> CSPPolicy:
        self.directives["block-all-mixed-content"] = []
        return self

    def report_uri(self, uri: str) -> CSPPolicy:
        self.directives["report-uri"] = [uri]
        return self

    def report_to(self, group: str) -> CSPPolicy:
        self.directives["report-to"] = [group]
        return self

    def directive(self, name: str, *sources: str) -> CSPPolicy:
        """Add an arbitrary directive."""
        self.directives[name] = list(sources)
        return self

    def build(self, nonce: str | None = None) -> str:
        """Compile directives into a CSP header value string."""
        parts: list[str] = []
        for directive, sources in self.directives.items():
            if not sources:
                parts.append(directive)
            else:
                rendered = []
                for src in sources:
                    if nonce and "{nonce}" in src:
                        rendered.append(src.replace("{nonce}", nonce))
                    else:
                        rendered.append(src)
                parts.append(f"{directive} {' '.join(rendered)}")
        return "; ".join(parts)

    @classmethod
    def strict(cls) -> CSPPolicy:
        """Strict CSP suitable for most web applications."""
        return (
            cls()
            .default_src("'self'")
            .script_src("'self'")
            .style_src("'self'", "'unsafe-inline'")
            .img_src("'self'", "data:", "https:")
            .font_src("'self'", "https:", "data:")
            .object_src("'none'")
            .frame_ancestors("'none'")
            .base_uri("'self'")
            .form_action("'self'")
            .upgrade_insecure_requests()
        )

    @classmethod
    def relaxed(cls) -> CSPPolicy:
        """Relaxed CSP for rapid development."""
        return (
            cls()
            .default_src("'self'", "https:", "data:")
            .script_src("'self'", "'unsafe-inline'", "'unsafe-eval'", "https:")
            .style_src("'self'", "'unsafe-inline'", "https:")
            .img_src("*", "data:", "blob:")
        )


class CSPMiddleware(Middleware):
    """
    Content-Security-Policy middleware.

    Features:
    - Fluent CSPPolicy builder
    - Per-request nonce generation (cryptographically secure)
    - Report-only mode
    - Nonce injection into request.state for template use

    Args:
        policy: CSPPolicy instance (or will use strict defaults).
        report_only: Send as Content-Security-Policy-Report-Only.
        nonce: Enable per-request nonce generation.
    """

    def __init__(
        self,
        policy: CSPPolicy | None = None,
        report_only: bool = False,
        nonce: bool = True,
    ):
        self._policy = policy or CSPPolicy.strict()
        self._report_only = report_only or self._policy.report_only
        self._nonce_enabled = nonce

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        nonce: str | None = None
        if self._nonce_enabled:
            nonce = secrets.token_urlsafe(16)
            request.state["csp_nonce"] = nonce

        response = await next_handler(request, ctx)

        header_name = "content-security-policy-report-only" if self._report_only else "content-security-policy"
        response.headers[header_name] = self._policy.build(nonce=nonce)

        return response


__all__ = ["CSPMiddleware", "CSPPolicy"]
