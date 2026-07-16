"""
aquilia.specula — Specula API Observatory for Aquilia.

The Aquilia-native API documentation, exploration, and testing platform.
Named after the Roman watchtower (*specula*) from which Eagle standard-bearers
surveyed their entire domain. From Specula, you see everything your API is.

Features:
  - Full OpenAPI 3.1.0 spec generation with Contract/Model/Fault schema bridges
  - Aquilia vendor extensions: x-specula-effects, x-specula-pipeline,
    x-specula-module, x-specula-version
  - Premium custom Observatory UI (no Swagger UI / ReDoc dependency)
  - Live spec updates via SSE (dev-mode hot-reload)
  - Multi-version spec support (integrates with aquilia.versioning)
  - Try It Out: real HTTP requests from the browser
  - Code generation: curl, Python (httpx), JavaScript (fetch), TypeScript (axios)
  - Fuzzy search across operations and schemas
  - Mock server: plausible example responses
  - Postman Collection v2.1 + Insomnia v4 export
  - In-process spec caching + CacheService integration
  - Typed fault hierarchy under SPECULA_DOMAIN
  - Singleton DI-injectable SpeculaService
  - Native Aquilia SpeculaController

Configure::

    Integration.specula(title="My API", version="2.0.0", ui_theme="dark")

Then visit http://localhost:8000/specula.
"""

from .config import SpeculaConfig
from .controller import SpeculaController
from .faults import (
    SPECULA_DOMAIN,
    MockServerFault,
    ObservatoryForbiddenFault,
    SchemaResolutionFault,
    SpecBuildFault,
    SpecCacheFault,
    SpeculaFault,
    VersionNotFoundFault,
)
from .manifest import bind_specula_routes, create_specula_manifest, specula_route_table
from .schema.builder import SpeculaBuilder
from .schema.contract import contract_components, contract_to_schema
from .schema.fault import aquilia_error_schema, aquilia_validation_error_schema, fault_to_response
from .schema.model import model_components, model_to_schema
from .schema.standard import STANDARD_SCHEMAS
from .schema.types import python_type_to_schema
from .service import SpeculaService
from .ui.renderer import SpeculaRenderer

__all__ = [
    # Config
    "SpeculaConfig",
    # Faults
    "SPECULA_DOMAIN",
    "SpeculaFault",
    "SpecBuildFault",
    "SchemaResolutionFault",
    "SpecCacheFault",
    "VersionNotFoundFault",
    "MockServerFault",
    "ObservatoryForbiddenFault",
    # Schema engine
    "SpeculaBuilder",
    # Schema bridges
    "contract_to_schema",
    "contract_components",
    "model_to_schema",
    "model_components",
    "python_type_to_schema",
    "aquilia_error_schema",
    "aquilia_validation_error_schema",
    "fault_to_response",
    "STANDARD_SCHEMAS",
    # Service & Controller
    "SpeculaService",
    "SpeculaController",
    # Manifest
    "create_specula_manifest",
    "bind_specula_routes",
    "specula_route_table",
    # UI
    "SpeculaRenderer",
]
