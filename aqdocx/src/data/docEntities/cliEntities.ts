import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'cli.init_workspace',
    type: 'cli',
    title: 'aq init workspace',
    description: 'Initializes a new Aquilia workspace with a standard directory structure including workspace.py, starter.py, and a modules directory.',
    signature: 'aq init workspace [NAME] [--minimal] [--template VALUE] [--yes]',
    language: 'bash',
    parameters: [
      { name: '[NAME]', type: 'argument', description: 'Name of the workspace directory to create.' },
      { name: '--minimal', type: 'option', description: 'Skips generating example modules and extra files.' },
      { name: '--template', type: 'option', description: 'Scaffolding template: api, service, or monolith.' },
      { name: '--yes, -y', type: 'option', description: 'Skips interactive prompts and applies defaults.' }
    ],
    example: {
      code: 'aq init workspace my-project --template=api --yes',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.add_module',
    type: 'cli',
    title: 'aq add module',
    description: 'Generates a new self-contained module folder within modules/ directory, registering it with dependencies and scaffolding controllers and models.',
    signature: 'aq add module [NAME] [--depends-on VALUE] [--route-prefix VALUE] [--with-tests] [--minimal]',
    language: 'bash',
    parameters: [
      { name: '[NAME]', type: 'argument', description: 'Name of the module to create.' },
      { name: '--depends-on', type: 'option', description: 'Declare dependency on another module (repeatable).' },
      { name: '--route-prefix', type: 'option', description: 'Custom URL prefix for module controllers.' },
      { name: '--with-tests', type: 'option', description: 'Include test routes and mock files.' }
    ],
    example: {
      code: 'aq add module payments --depends-on=users --route-prefix=/v1/payments',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.generate_controller',
    type: 'cli',
    title: 'aq generate controller',
    description: 'Generates a controller class file from a template, setting up standard routes, validation contracts, or lifecycle hook methods.',
    signature: 'aq generate controller NAME [--prefix VALUE] [--resource VALUE] [--simple] [--with-lifecycle]',
    language: 'bash',
    parameters: [
      { name: 'NAME', type: 'argument', description: 'Name of the controller class.' },
      { name: '--prefix', type: 'option', description: 'Custom route prefix (defaults to /name).' },
      { name: '--resource', type: 'option', description: 'Resource model name for CRUD scaffolding.' },
      { name: '--with-lifecycle', type: 'option', description: 'Scaffolds on_startup, on_request, and on_response lifecycle hooks.' }
    ],
    example: {
      code: 'aq generate controller Users --resource=User --with-lifecycle',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/generators'
  },
  {
    id: 'cli.validate',
    type: 'cli',
    title: 'aq validate',
    description: 'Statically validates the workspace module manifests and dependency graphs, finding circular imports, route conflicts, and missing providers.',
    signature: 'aq validate [--strict] [--module VALUE] [--json]',
    language: 'bash',
    parameters: [
      { name: '--strict', type: 'option', description: 'Enforce strict production-level validation rules.' },
      { name: '--module', type: 'option', description: 'Validate only the specified module manifest.' },
      { name: '--json', type: 'option', description: 'Formats the validation output report as JSON.' }
    ],
    example: {
      code: 'aq validate --strict',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.compile',
    type: 'cli',
    title: 'aq compile',
    description: 'Compiles all modules, templates, schemas, and routes into a set of static .surp files stored in the artifacts directory.',
    signature: 'aq compile [--watch] [--output VALUE]',
    language: 'bash',
    parameters: [
      { name: '--watch', type: 'option', description: 'Watch the filesystem for changes and recompile automatically.' },
      { name: '--output', type: 'option', description: 'Custom artifacts output directory.' }
    ],
    example: {
      code: 'aq compile --output=dist/artifacts',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.run',
    type: 'cli',
    title: 'aq run',
    description: 'Launches the local ASGI development server with auto-reload, debugger, and optional pre-flight dependency validation checks.',
    signature: 'aq run [--mode dev|test] [--port VALUE] [--host VALUE] [--reload] [--skip-checks]',
    language: 'bash',
    parameters: [
      { name: '--mode', type: 'option', description: 'Select runtime mode: dev or test.' },
      { name: '--port', type: 'option', description: 'Bind to custom port (defaults to 8000).' },
      { name: '--reload', type: 'option', description: 'Enable/disable auto-reload on file edits.' }
    ],
    example: {
      code: 'aq run --port=8080 --reload',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.serve',
    type: 'cli',
    title: 'aq serve',
    description: 'Starts the production server using Uvicorn or Gunicorn, tuning workers, timeouts, and process bindings for multi-core environments.',
    signature: 'aq serve [--workers VALUE] [--bind VALUE] [--use-gunicorn] [--timeout VALUE]',
    language: 'bash',
    parameters: [
      { name: '--workers', type: 'option', description: 'Number of worker processes.' },
      { name: '--use-gunicorn', type: 'option', description: 'Wraps ASGI server in Gunicorn for supervisor controls.' },
      { name: '--timeout', type: 'option', description: 'Timeout limit in seconds for worker heartbeat.' }
    ],
    example: {
      code: 'aq serve --workers=4 --use-gunicorn --timeout=60',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.freeze',
    type: 'cli',
    title: 'aq freeze',
    description: 'Creates a snapshot of the compiled artifacts, generating cryptographic signatures to prevent tampering in production deployments.',
    signature: 'aq freeze [--output VALUE] [--sign]',
    language: 'bash',
    example: {
      code: 'aq freeze --sign',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.manifest_update',
    type: 'cli',
    title: 'aq manifest update',
    description: 'Performs auto-discovery on a module directory, finding new controllers, models, and tasks, and updating the manifest.py file accordingly.',
    signature: 'aq manifest update [--check] [--freeze] MODULE',
    language: 'bash',
    example: {
      code: 'aq manifest update payments --check',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.doctor',
    type: 'cli',
    title: 'aq doctor',
    description: 'Analyzes the environment, Python packages, sqlite backends, and config files to diagnose issues preventing startup or performance bottlenecks.',
    signature: 'aq doctor [--json]',
    language: 'bash',
    example: {
      code: 'aq doctor',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/core'
  },
  {
    id: 'cli.db_makemigrations',
    type: 'cli',
    title: 'aq db makemigrations',
    description: 'Scans models in modules and diffs them against the existing migration state, creating a serialized schema migration file.',
    signature: 'aq db makemigrations [--app VALUE] [--migrations-dir VALUE] [--no-dsl]',
    language: 'bash',
    example: {
      code: 'aq db makemigrations --app users',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/database'
  },
  {
    id: 'cli.db_migrate',
    type: 'cli',
    title: 'aq db migrate',
    description: 'Executes pending database migration files against the target connection URL, safely updating the database schema.',
    signature: 'aq db migrate [--target VALUE] [--plan] [--fake]',
    language: 'bash',
    example: {
      code: 'aq db migrate --plan',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/database'
  },
  {
    id: 'cli.ws_gen_client',
    type: 'cli',
    title: 'aq ws gen-client',
    description: 'Parses compiled WebSocket SocketControllers and generates a fully typed TypeScript client SDK for event broadcast/ack interactions.',
    signature: 'aq ws gen-client --out VALUE [--lang ts|js]',
    language: 'bash',
    example: {
      code: 'aq ws gen-client --out=frontend/src/sdk --lang=ts',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/cli/websockets'
  },
  {
    id: 'cli.test',
    type: 'cli',
    title: 'aq test',
    description: 'Executes the project test suite using pytest with pre-configured asyncio auto mode, coverage reports, and custom path discovery.',
    signature: 'aq test [PATHS] [-k PATTERN] [-m MARKERS] [--coverage] [--coverage-html] [-x] [-v]',
    language: 'bash',
    parameters: [
      { name: 'PATHS', type: 'argument', description: 'Test files or directories to run.' },
      { name: '-k, --pattern', type: 'option', description: 'Only run tests matching pattern.' },
      { name: '--coverage', type: 'option', description: 'Collect code coverage reports.' },
      { name: '-x, --failfast', type: 'option', description: 'Stop execution on first failure.' }
    ],
    example: {
      code: 'aq test --coverage --failfast',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/runner'
  }
])
