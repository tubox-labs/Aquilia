import { registerDocEntities } from '../../lib/docPreview/registry'

/**
 * A small cross-domain sample proving the preview system is a site-wide primitive,
 * not something specific to one page — one entry per category called out in the
 * design brief (class, decorator, model, CLI command, type).
 */
registerDocEntities([
  {
    id: 'controllers.router',
    type: 'class',
    title: 'Router',
    description: 'Compiles controller route declarations into a matchable route table, resolving prefixes, path params, and method dispatch ahead of time.',
    signature: 'class Router:\n    def __init__(self, controllers: list[Controller]): ...',
    language: 'python',
    parameters: [{ name: 'controllers', type: 'list[Controller]', description: 'Discovered controller instances to compile routes for.' }],
    related: [{ label: '@GET / @POST', href: '/docs/controllers/decorators' }, { label: 'ControllerRouter', href: '/docs/controllers/router' }],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/router',
    source: { file: 'aquilia/controller/router.py' },
  },
  {
    id: 'di.inject',
    type: 'decorator',
    title: '@inject',
    description: 'Marks a constructor or function parameter for dependency resolution from the active DI container at the appropriate scope.',
    signature: '@inject\ndef __init__(self, db: Database, cache: Cache): ...',
    language: 'python',
    example: {
      code: `class ReportsController(Controller):
    @inject
    def __init__(self, db: Database, cache: Cache):
        self.db = db
        self.cache = cache`,
      language: 'python',
    },
    related: [{ label: 'DI Scopes', href: '/docs/di/scopes' }, { label: 'Providers', href: '/docs/di/providers' }],
    status: 'stable',
    docsHref: '/docs/di/decorators',
  },
  {
    id: 'models.user_model',
    type: 'model',
    title: 'UserModel',
    description: 'Example async ORM model — declares typed fields and generates a query set, migrations, and validation automatically.',
    signature: 'class UserModel(Model):\n    id: int = Field(primary_key=True)\n    email: str = Field(unique=True)',
    language: 'python',
    related: [{ label: 'Fields', href: '/docs/models/fields' }, { label: 'QuerySet', href: '/docs/models/queryset' }],
    status: 'stable',
    docsHref: '/docs/models/overview',
  },
  {
    id: 'cli.aquilia_run',
    type: 'cli',
    title: 'aquilia run',
    description: 'Starts the dev server with hot reload, using the workspace at AQUILIA_WORKSPACE (defaults to the current directory).',
    signature: 'aquilia run [--host HOST] [--port PORT] [--reload]',
    language: 'bash',
    parameters: [
      { name: '--host', type: 'string', optional: true, default: '127.0.0.1', description: 'Bind address.' },
      { name: '--port', type: 'int', optional: true, default: '8000', description: 'Bind port.' },
      { name: '--reload', optional: true, description: 'Enable file-watch hot reload (default in dev mode).' },
    ],
    example: { code: 'aquilia run --port 3000 --reload', language: 'bash' },
    status: 'stable',
    docsHref: '/docs/cli/core',
  },
  {
    id: 'http.request_type',
    type: 'type',
    title: 'Request',
    description: 'Immutable, typed representation of an inbound HTTP request — headers, query params, path params, and a lazily-parsed body.',
    signature: 'class Request:\n    method: str\n    path: str\n    headers: Headers\n    query: QueryParams',
    language: 'python',
    related: [{ label: 'Response', href: '/docs/request-response/response' }, { label: 'RequestCtx', href: '/docs/controllers/request-ctx' }],
    status: 'stable',
    docsHref: '/docs/request-response/request',
  },
])
