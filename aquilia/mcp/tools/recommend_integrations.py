"""recommend_integrations tool."""

from __future__ import annotations

from ..context.search import search_index
from ..models import KnowledgeIndex

_RECOMMENDATIONS = {
    "auth": ["Integration.auth(...)", "Workspace.sessions(...)"],
    "session": ["Workspace.sessions(...)", "Integration.sessions(...)"],
    "database": ["Workspace.database(...)", "Integration.database(config=SqliteConfig/PostgresConfig/...)"],
    "db": ["Workspace.database(...)", "Integration.database(...)"],
    "cache": ["Integration.cache(...)"],
    "storage": ["Workspace.storage(...)", "Integration.storage(...)"],
    "tasks": ["Workspace.tasks(...)", "Integration.tasks(...)"],
    "mail": ["Integration.mail(...)", "Integration.MailProvider.*", "Integration.MailAuth.*"],
    "template": ["Integration.templates(...)", "TemplatesIntegration(...)"],
    "i18n": ["Workspace.i18n(...)", "Integration.i18n(...)"],
    "admin": ["Integration.admin(...)", "AdminModules(...)"],
    "versioning": ["Integration.versioning(...)", "version-aware controller decorators"],
    "http": [
        "Use aquilia.http.AsyncHTTPClient and MockTransport in tests; configure cache/retry through service code."
    ],
    "provider": [
        "RenderIntegration(...) for Render deployments; keep provider credentials in provider credential stores/env."
    ],
    "render": ["RenderIntegration(...)", "aq deploy-gen render for deployment planning"],
    "openapi": [
        "OpenAPIIntegration(...) or Integration.openapi(...)",
        "Controller metadata and decorators drive schema generation",
    ],
    "security": [
        "Workspace.security(...)",
        "CorsIntegration/CspIntegration/RateLimitIntegration or Integration.cors/csp/rate_limit",
    ],
    "filesystem": ["aquilia.filesystem service/helpers", "StorageIntegration for app-level file storage"],
}


def recommend_integrations(index: KnowledgeIndex, arguments: dict) -> dict:
    goal = arguments["goal"].lower()
    recommendations = []
    for key, values in _RECOMMENDATIONS.items():
        if key in goal:
            recommendations.extend(values)
    if not recommendations:
        recommendations = [
            "Use Workspace.module(...) for module orchestration; add Integration.* only for enabled subsystems."
        ]
    anchors = [result.to_dict() for result in search_index(index, goal, limit=6)]
    return {"goal": arguments["goal"], "recommendations": list(dict.fromkeys(recommendations)), "anchors": anchors}
