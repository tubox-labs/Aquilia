import { registerDocEntities } from '../../lib/docPreview/registry'

/**
 * Doc-entity data for `/docs/server/lifecycle`. Imported once (side-effect) from
 * `src/data/docEntities/index.ts`, which is loaded eagerly in `App.tsx` so every
 * `<DocTerm>` across the site can resolve these ids regardless of which page mounts
 * first.
 */
registerDocEntities([
  {
    id: 'lifecycle.on_startup',
    type: 'hook',
    title: 'on_startup(ctx)',
    description: 'Runs once during application startup, after dependency-ordered wiring completes but before the server accepts requests.',
    signature: 'async def on_startup(self, ctx: RequestCtx) -> None',
    language: 'python',
    parameters: [
      { name: 'ctx', type: 'RequestCtx', description: 'The lifecycle-scoped request context, useful for reading app config and DI-resolved services.' },
    ],
    returns: { type: 'None', description: 'Raising inside this hook aborts startup and triggers rollback of already-started apps.' },
    example: {
      code: `class DatabaseController(Controller):
    instantiation_mode = "singleton"

    async def on_startup(self, ctx: RequestCtx) -> None:
        self.pool = await self.db.create_pool(min_size=5, max_size=20)`,
      language: 'python',
    },
    related: [
      { id: 'lifecycle.on_shutdown', label: 'on_shutdown(ctx)' },
      { id: 'lifecycle.coordinator', label: 'LifecycleCoordinator' },
    ],
    status: 'stable',
    version: 'v1.0+',
    notes: [{ kind: 'note', text: 'Only called on controllers with instantiation_mode = "singleton".' }],
    docsHref: '/docs/server/lifecycle',
    source: { file: 'aquilia/lifecycle.py', line: 115 },
  },
  {
    id: 'lifecycle.on_shutdown',
    type: 'hook',
    title: 'on_shutdown(ctx)',
    description: 'Runs once during application shutdown, in reverse dependency order relative to startup.',
    signature: 'async def on_shutdown(self, ctx: RequestCtx) -> None',
    language: 'python',
    parameters: [{ name: 'ctx', type: 'RequestCtx', description: 'The lifecycle-scoped request context.' }],
    returns: { type: 'None', description: 'Errors are logged but do not stop other apps from shutting down.' },
    related: [
      { id: 'lifecycle.on_startup', label: 'on_startup(ctx)' },
      { id: 'lifecycle.coordinator', label: 'LifecycleCoordinator' },
    ],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/server/lifecycle',
    source: { file: 'aquilia/lifecycle.py', line: 151 },
  },
  {
    id: 'lifecycle.coordinator',
    type: 'class',
    title: 'LifecycleCoordinator',
    description: 'Manages dependency-ordered startup and shutdown of app components using the RuntimeRegistry dependency graph.',
    signature: 'class LifecycleCoordinator:\n    def __init__(self, runtime: RuntimeRegistry, config: ConfigLoader): ...',
    language: 'python',
    related: [
      { id: 'lifecycle.on_startup', label: 'on_startup(ctx)' },
      { id: 'lifecycle.on_shutdown', label: 'on_shutdown(ctx)' },
      { label: 'RuntimeRegistry', href: '/docs/aquilary/runtime' },
    ],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/server/lifecycle',
    source: { file: 'aquilia/lifecycle.py', line: 96 },
  },
  {
    id: 'lifecycle.on_request',
    type: 'hook',
    title: 'on_request(ctx)',
    description: 'Runs before every request on this controller — both singleton and per_request instantiation modes.',
    signature: 'async def on_request(self, ctx: RequestCtx) -> None',
    language: 'python',
    parameters: [{ name: 'ctx', type: 'RequestCtx', description: 'The current request context. Mutate ctx.state to pass data downstream.' }],
    related: [{ id: 'lifecycle.on_response', label: 'on_response(ctx, response)' }],
    status: 'stable',
    docsHref: '/docs/server/lifecycle',
  },
  {
    id: 'lifecycle.on_response',
    type: 'hook',
    title: 'on_response(ctx, response)',
    description: 'Runs after every request. Can inspect or replace the outgoing Response.',
    signature: 'async def on_response(self, ctx: RequestCtx, response: Response) -> Response',
    language: 'python',
    parameters: [
      { name: 'ctx', type: 'RequestCtx', description: 'The current request context.' },
      { name: 'response', type: 'Response', description: 'The response produced by the route handler.' },
    ],
    returns: { type: 'Response', description: 'Return the (optionally modified) response to send to the client.' },
    related: [{ id: 'lifecycle.on_request', label: 'on_request(ctx)' }],
    status: 'stable',
    docsHref: '/docs/server/lifecycle',
  },
])
