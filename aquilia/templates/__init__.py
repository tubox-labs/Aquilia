"""
AquilaTemplates - First-class Jinja2-based template rendering for Aquilia.

Production-ready, async-capable template system with:
- Manifest-driven compilation and crous artifacts
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

from .auth_integration import (
    IdentityTemplateProxy,
    TemplateAuthMixin,
)
from .bytecode_cache import (
    BytecodeCache,
    CrousBytecodeCache,
    InMemoryBytecodeCache,
)
from .context import TemplateContext, create_template_context
from .di_providers import (
    create_development_engine,
    create_production_engine,
    create_testing_engine,
    register_template_providers,
)
from .engine import TemplateEngine
from .extensions import StaticTagExtension
from .faults import (
    TEMPLATE_DOMAIN,
    TemplateCacheIntegrityFault,
    TemplateEngineUnavailableFault,
    TemplateFault,
    TemplateSanitizationWarning,
)
from .loader import PackageLoader, TemplateLoader
from .manager import TemplateLintIssue, TemplateManager
from .manifest_integration import (
    ModuleTemplateRegistry,
    create_manifest_aware_loader,
    discover_template_directories,
)
from .middleware import TemplateMiddleware
from .security import SandboxPolicy, TemplateSandbox
from .sessions_integration import (
    FlashMessages,
    SessionTemplateProxy,
    TemplateFlashMixin,
)

__all__ = [
    # Core
    "TemplateEngine",
    "StaticTagExtension",
    "TemplateLoader",
    "PackageLoader",
    # Cache
    "BytecodeCache",
    "InMemoryBytecodeCache",
    "CrousBytecodeCache",
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
