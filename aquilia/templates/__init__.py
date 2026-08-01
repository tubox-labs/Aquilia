"""
AquilaTemplates - First-class Jinja2-based template rendering for Aquilia.

Production-ready, async-capable template system with:
- Manifest-driven compilation and json artifacts
- DI-friendly Controller integration
- Sandboxed execution with security by default
- Fast precompilation, bytecode cache, streaming
- Hot-reload support in dev mode
- Observable with metrics and tracing

Example:
    from aquilia.templates import TemplateEngine, TemplateLoader
    from aquilia import Controller, GET

    class ProfileController(Controller):
        prefix = "/profile"

        def __init__(self, templates: TemplateEngine):
            self.templates = templates

        @GET("/")
        async def view(self, ctx):
            return await self.templates.render_to_response(
                "users/profile.html",
                {"user": ctx.identity}
            )
"""

from aquilia._version import __version__  # noqa: F401 — re-exported
from aquilia.templates.auth_integration import IdentityTemplateProxy, TemplateAuthMixin
from aquilia.templates.bytecode_cache import BytecodeCache, InMemoryBytecodeCache, JSONBytecodeCache
from aquilia.templates.context import TemplateContext, create_template_context
from aquilia.templates.di_providers import (
    create_development_engine,
    create_production_engine,
    create_testing_engine,
    register_template_providers,
)
from aquilia.templates.engine import TemplateEngine
from aquilia.templates.extensions import StaticTagExtension
from aquilia.templates.faults import (
    TEMPLATE_DOMAIN,
    TemplateCacheIntegrityFault,
    TemplateEngineUnavailableFault,
    TemplateFault,
    TemplateSanitizationWarning,
)
from aquilia.templates.loader import PackageLoader, TemplateLoader
from aquilia.templates.manager import TemplateLintIssue, TemplateManager
from aquilia.templates.manifest_integration import (
    ModuleTemplateRegistry,
    create_manifest_aware_loader,
    discover_template_directories,
)
from aquilia.templates.middleware import TemplateMiddleware
from aquilia.templates.security import SandboxPolicy, TemplateSandbox
from aquilia.templates.sessions_integration import FlashMessages, SessionTemplateProxy, TemplateFlashMixin

__all__ = [
    # Core
    "TemplateEngine",
    "StaticTagExtension",
    "TemplateLoader",
    "PackageLoader",
    # Cache
    "BytecodeCache",
    "InMemoryBytecodeCache",
    "JSONBytecodeCache",
    # Manager
    "TemplateManager",
    "TemplateLintIssue",
    # Middleware
    "TemplateMiddleware",
    # Context
    "TemplateContext",
    "create_template_context",
    # Security
    "TemplateSandbox",
    "SandboxPolicy",
    # DI Integration
    "register_template_providers",
    "create_development_engine",
    "create_production_engine",
    "create_testing_engine",
    # Session Integration
    "SessionTemplateProxy",
    "FlashMessages",
    "TemplateFlashMixin",
    # Auth Integration
    "IdentityTemplateProxy",
    "TemplateAuthMixin",
    # Manifest Integration
    "discover_template_directories",
    "create_manifest_aware_loader",
    "ModuleTemplateRegistry",
    # Faults
    "TEMPLATE_DOMAIN",
    "TemplateFault",
    "TemplateEngineUnavailableFault",
    "TemplateCacheIntegrityFault",
    "TemplateSanitizationWarning",
]
