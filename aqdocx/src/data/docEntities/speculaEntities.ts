import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'specula.config',
    type: 'class',
    title: 'SpeculaConfig',
    description: 'Configuration dataclass for Specula — the Aquilia API Observatory. Controls title, version, UI paths, feature flags, cache TTL, authentication requirements, and mock server options.',
    signature: 'class SpeculaConfig:\n    title: str = "Aquilia API"\n    version: str = "1.0.0"\n    ui_path: str = "/specula"\n    json_path: str = "/specula/spec.json"\n    yaml_path: str = "/specula/spec.yaml"\n    mock_server_enabled: bool = False\n    spec_cache_ttl: int = 60\n    enabled: bool = True',
    language: 'python',
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/controllers/openapi'
  },
  {
    id: 'specula.integration',
    type: 'class',
    title: 'SpeculaIntegration',
    description: 'Typed integration wrapper for Specula in workspace.py. Fields mirror SpeculaConfig and can be registered via Integration.specula(...) or instantiated directly.',
    signature: 'class SpeculaIntegration:\n    title: str = "Aquilia API"\n    version: str = "1.0.0"\n    ui_path: str = "/specula"\n    enabled: bool = True',
    language: 'python',
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/controllers/openapi'
  },
  {
    id: 'specula.builder',
    type: 'class',
    title: 'SpeculaBuilder',
    description: 'API Observatory specification engine. Extracts OpenAPI 3.1.0 specifications, tags, custom vendor extensions (x-specula-*), and security schemas.',
    signature: 'class SpeculaBuilder:\n    def __init__(self, config: SpeculaConfig):\n    def build(self, router: ControllerRouter, routes: list[CompiledRoute] | None = None) -> dict[str, Any]',
    language: 'python',
    example: {
      code: `builder = SpeculaBuilder(config=SpeculaConfig(title="Store API"))
spec = builder.build(router)`,
      language: 'python'
    },
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/controllers/openapi'
  },
  {
    id: 'specula.service',
    type: 'class',
    title: 'SpeculaService',
    description: 'Observatory service that manages spec generation, caching, hot reload SSE streams, Postman/Insomnia exports, and mock endpoint resolution.',
    signature: 'class SpeculaService:\n    def __init__(self, router: ControllerRouter, config: SpeculaConfig)',
    language: 'python',
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/controllers/openapi'
  }
])
