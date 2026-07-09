import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'openapi.config',
    type: 'class',
    title: 'OpenAPIConfig',
    description: 'Configuration dataclass for OpenAPI generation. Controls titles, versions, UI paths (Swagger UI, ReDoc, openapi.json), servers, themes, security schemes, and body inference options.',
    signature: 'class OpenAPIConfig:\n    title: str = "Aquilia API"\n    version: str = "1.0.0"\n    description: str = ""\n    docs_path: str = "/docs"\n    openapi_json_path: str = "/openapi.json"\n    redoc_path: str = "/redoc"\n    enabled: bool = True',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/openapi'
  },
  {
    id: 'openapi.generator',
    type: 'class',
    title: 'OpenAPIGenerator',
    description: 'Production-grade OpenAPI 3.1.0 specification generator. Introspects compiled routes, docstrings, request schemas, status codes, and guards to build a complete spec.',
    signature: 'class OpenAPIGenerator:\n    def __init__(self, title: str = "Aquilia API", version: str = "1.0.0", config: OpenAPIConfig | None = None)',
    language: 'python',
    example: {
      code: `generator = OpenAPIGenerator(config=OpenAPIConfig(title="User API"))
spec = generator.generate(router)`,
      language: 'python'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/openapi'
  },
  {
    id: 'openapi.swagger_html',
    type: 'function',
    title: 'generate_swagger_html',
    description: 'Generates the HTML wrapper for Swagger UI, pulling the UI bundle from CDN and mounting the openapi.json spec path. Supports dark and light themes.',
    signature: 'def generate_swagger_html(config: OpenAPIConfig) -> str',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/openapi'
  },
  {
    id: 'openapi.redoc_html',
    type: 'function',
    title: 'generate_redoc_html',
    description: 'Generates the HTML wrapper for ReDoc, displaying the API documentation reference in a clean, three-column panel.',
    signature: 'def generate_redoc_html(config: OpenAPIConfig) -> str',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/openapi'
  }
])
