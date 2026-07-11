const fs = require('fs');
const path = require('path');

// 1. Load compiled docsContent
const { docsContent } = require(path.join(__dirname, 'temp/docsContent.cjs'));

// 2. Load the sitemap sections config to find labels dynamically
const docSections = [
  {
    title: 'Getting Started',
    items: [
      { label: 'Introduction', path: '/docs' },
      { label: 'Installation', path: '/docs/installation' },
      { label: 'Quick Start', path: '/docs/quickstart' },
      { label: 'Developer Guide', path: '/docs/developer-guide' },
      { label: 'Architecture', path: '/docs/architecture' },
      { label: 'Project Structure', path: '/docs/project-structure' },
      { label: 'Admin Panel Setup', path: '/docs/admin-panel' },
    ]
  },
  {
    title: 'Tutorials',
    items: [
      { label: 'Overview', path: '/docs/tutorials/overview' },
      { label: 'Todo Application', path: '/docs/tutorials/todo-app' },
      { label: 'Authentication App', path: '/docs/tutorials/auth-app' },
    ]
  },
  {
    title: 'Core',
    items: [
      {
        label: 'Server', path: '/docs/server',
        children: [
          { label: 'AquiliaServer', path: '/docs/server/aquilia-server' },
          { label: 'ASGI Adapter', path: '/docs/server/asgi' },
          { label: 'Lifecycle', path: '/docs/server/lifecycle' },
        ]
      },
      {
        label: 'Configuration', path: '/docs/config',
        children: [
          { label: 'Overview', path: '/docs/config/loader' },
          { label: 'AquilaConfig & Env', path: '/docs/config/pyconfig' },
          { label: '.env Files', path: '/docs/config/dotenv' },
          { label: 'Workspace Builder', path: '/docs/config/workspace' },
          { label: 'Module Builder', path: '/docs/config/module' },
          { label: 'AppManifest', path: '/docs/config/manifest' },
          { label: 'Integrations', path: '/docs/config/integrations' },
        ]
      },
      {
        label: 'Request & Response', path: '/docs/request-response',
        children: [
          { label: 'Request', path: '/docs/request-response/request' },
          { label: 'Response', path: '/docs/request-response/response' },
          { label: 'Data Structures', path: '/docs/request-response/data-structures' },
          { label: 'File Uploads', path: '/docs/request-response/uploads' },
        ]
      },
      {
        label: 'Controllers', path: '/docs/controllers',
        children: [
          { label: 'Overview', path: '/docs/controllers/overview' },
          { label: 'RequestCtx', path: '/docs/controllers/request-ctx' },
          { label: 'Controller Factory', path: '/docs/controllers/factory' },
          { label: 'Controller Engine', path: '/docs/controllers/engine' },
          { label: 'Controller Compiler', path: '/docs/controllers/compiler' },
          { label: 'Controller Router', path: '/docs/controllers/router' },
          { label: 'OpenAPI Generation', path: '/docs/controllers/openapi' },
          { label: 'Body Validation', path: '/docs/controllers/validation' },
          { label: 'Pagination', path: '/docs/controllers/pagination' },
          { label: 'Filtering & Search', path: '/docs/controllers/filters' },
          { label: 'Content Negotiation', path: '/docs/controllers/renderers' },
          {
            label: 'Route Decorators', path: '/docs/controllers/decorators',
            children: [
              { label: 'Overview', path: '/docs/controllers/decorators' },
              { label: '@GET', path: '/docs/controllers/decorators/get' },
              { label: '@POST', path: '/docs/controllers/decorators/post' },
              { label: '@PUT', path: '/docs/controllers/decorators/put' },
              { label: '@PATCH', path: '/docs/controllers/decorators/patch' },
              { label: '@DELETE', path: '/docs/controllers/decorators/delete' },
              { label: '@HEAD', path: '/docs/controllers/decorators/head' },
              { label: '@OPTIONS', path: '/docs/controllers/decorators/options' },
              { label: '@WS', path: '/docs/controllers/decorators/ws' },
              { label: '@route', path: '/docs/controllers/decorators/route' },
            ]
          },
        ]
      },
      {
        label: 'Routing', path: '/docs/routing',
        children: [
          { label: 'Pattern Matching', path: '/docs/routing/patterns' },
          { label: 'Controller Router', path: '/docs/routing/router' },
          { label: 'URL Generation', path: '/docs/routing/urls' },
        ]
      },
    ]
  },
  {
    title: 'Dependency Injection',
    items: [
      {
        label: 'DI System', path: '/docs/di',
        children: [
          { label: 'Overview', path: '/docs/di' },
          { label: 'Container', path: '/docs/di/container' },
          { label: 'Providers', path: '/docs/di/providers' },
          { label: 'Scopes', path: '/docs/di/scopes' },
          { label: 'Decorators', path: '/docs/di/decorators' },
          { label: 'RequestDAG', path: '/docs/di/request-dag' },
          { label: 'HTTP Extractors', path: '/docs/di/extractors' },
          { label: 'Lifecycle', path: '/docs/di/lifecycle' },
          { label: 'Diagnostics', path: '/docs/di/diagnostics' },
          { label: 'Advanced', path: '/docs/di/advanced' },
        ]
      },
    ]
  },
  {
    title: 'Data Layer',
    items: [
      {
        label: 'Models (ORM)', path: '/docs/models',
        children: [
          { label: 'Overview', path: '/docs/models/overview' },
          {
            label: 'Fields', path: '/docs/models/fields',
            children: [
              { label: 'Overview & Core', path: '/docs/models/fields/overview' },
              { label: 'Numeric Fields', path: '/docs/models/fields/numeric' },
              { label: 'Text & String Fields', path: '/docs/models/fields/text' },
              { label: 'Date & Time Fields', path: '/docs/models/fields/datetime' },
              { label: 'Structured & JSON Fields', path: '/docs/models/fields/structured' },
            ]
          },
          { label: 'QuerySet API', path: '/docs/models/queryset' },
          {
            label: 'Relationships', path: '/docs/models/relationships',
            children: [
              { label: 'Defining Relations', path: '/docs/models/relationships/defining' },
              { label: 'Hydration Primitives', path: '/docs/models/relationships/hydration' },
              { label: 'Many-to-Many Operations', path: '/docs/models/relationships/m2m' },
            ]
          },
          {
            label: 'Transactions', path: '/docs/models/transactions',
            children: [
              { label: 'Atomic & Contexts', path: '/docs/models/transactions/atomic' },
              { label: 'Savepoints & Nesting', path: '/docs/models/transactions/savepoints' },
              { label: 'Lifecycle Hooks', path: '/docs/models/transactions/hooks' },
            ]
          },
          { label: 'Signals', path: '/docs/models/signals' },
          { label: 'Aggregation', path: '/docs/models/aggregation' },
          { label: 'Migrations', path: '/docs/models/migrations' },
          { label: 'Advanced Usage', path: '/docs/models/advanced' },
        ]
      },
      {
        label: 'Database Engine', path: '/docs/database',
        children: [
          { label: 'Overview', path: '/docs/database' },
          { label: 'AquiliaDatabase', path: '/docs/database/engine' },
          { label: 'Config Classes', path: '/docs/database/configs' },
          { label: 'SQLite Backend', path: '/docs/database/sqlite' },
          { label: 'PostgreSQL Backend', path: '/docs/database/postgresql' },
          { label: 'MySQL Backend', path: '/docs/database/mysql' },
        ]
      },
      {
        label: 'SQLite', path: '/docs/sqlite',
        children: [
          { label: 'Overview', path: '/docs/sqlite/overview' },
          { label: 'API Reference', path: '/docs/sqlite/api' },
          { label: 'Pool Configuration', path: '/docs/sqlite/pool' },
          { label: 'Transactions', path: '/docs/sqlite/transactions' },
          { label: 'Controller Guide', path: '/docs/sqlite/controller' },
        ]
      },
      {
        label: 'Blueprints', path: '/docs/blueprints',
        children: [
          { label: 'Overview', path: '/docs/blueprints/overview' },
          { label: 'Facets', path: '/docs/blueprints/facets' },
          { label: 'Projections', path: '/docs/blueprints/projections' },
          { label: 'Lenses', path: '/docs/blueprints/lenses' },
          { label: 'Seals (Validation)', path: '/docs/blueprints/seals' },
          { label: 'Annotations', path: '/docs/blueprints/annotations' },
          { label: 'Integration', path: '/docs/blueprints/integration' },
          { label: 'Schemas', path: '/docs/blueprints/schemas' },
          { label: 'Faults', path: '/docs/blueprints/faults' },
        ]
      },
    ]
  },
  {
    title: 'Security & Auth',
    items: [
      {
        label: 'Authentication', path: '/docs/auth',
        children: [
          { label: 'Identity Model', path: '/docs/auth/identity' },
          { label: 'Credentials', path: '/docs/auth/credentials' },
          { label: 'Auth Manager', path: '/docs/auth/manager' },
          { label: 'OAuth2 / OIDC', path: '/docs/auth/oauth' },
          { label: 'MFA', path: '/docs/auth/mfa' },
          { label: 'Tokens & Keys', path: '/docs/auth/tokens' },
          { label: 'Stores', path: '/docs/auth/stores' },
          { label: 'Guards', path: '/docs/auth/guards' },
          { label: 'Faults', path: '/docs/auth/faults' },
          { label: 'Integration', path: '/docs/auth/integration' },
          { label: 'Advanced', path: '/docs/auth/advanced' },
        ]
      },
      {
        label: 'Authorization', path: '/docs/authz',
        children: [
          { label: 'Overview', path: '/docs/authz' },
          { label: 'RBAC', path: '/docs/authz/rbac' },
          { label: 'ABAC', path: '/docs/authz/abac' },
          { label: 'Policies', path: '/docs/authz/policies' },
        ]
      },
      {
        label: 'Sessions', path: '/docs/sessions',
        children: [
          { label: 'Overview', path: '/docs/sessions/overview' },
          { label: 'Workspace Integration', path: '/docs/sessions/integration' },
          { label: 'Engine', path: '/docs/sessions/engine' },
          { label: 'Policies', path: '/docs/sessions/policies' },
          { label: 'Stores', path: '/docs/sessions/stores' },
          { label: 'Transport', path: '/docs/sessions/transport' },
          { label: 'Decorators', path: '/docs/sessions/decorators' },
          { label: 'Typed State', path: '/docs/sessions/state' },
          { label: 'Guards & Context', path: '/docs/sessions/guards' },
          { label: 'Faults', path: '/docs/sessions/faults' },
        ]
      },
      {
        label: 'Signing', path: '/docs/signing',
        children: [
          { label: 'Overview', path: '/docs/signing/overview' },
          { label: 'Core Signers', path: '/docs/signing/signers' },
          { label: 'Specialized Signers', path: '/docs/signing/specialized' },
          { label: 'Advanced Signing', path: '/docs/signing/advanced' },
        ]
      },
    ]
  },
  {
    title: 'Middleware',
    items: [
      {
        label: 'Middleware System', path: '/docs/middleware',
        children: [
          { label: 'Overview', path: '/docs/middleware/overview' },
          { label: 'MiddlewareStack', path: '/docs/middleware/stack' },
          { label: 'Built-in Middleware', path: '/docs/middleware/built-in' },
          { label: 'Static Files', path: '/docs/middleware/static' },
          { label: 'CORS', path: '/docs/middleware/cors' },
          { label: 'Rate Limiting', path: '/docs/middleware/rate-limit' },
          { label: 'Security Headers', path: '/docs/middleware/security' },
          { label: 'Request Scope', path: '/docs/middleware/request-scope' },
          { label: 'Sessions', path: '/docs/middleware/session' },
          { label: 'Access Logging', path: '/docs/middleware/logging' },
          { label: 'CSP', path: '/docs/middleware/csp' },
          { label: 'CSRF', path: '/docs/middleware/csrf' },
          { label: 'HSTS', path: '/docs/middleware/hsts' },
          { label: 'HTTPS Redirect', path: '/docs/middleware/https-redirect' },
          { label: 'Proxy Fix', path: '/docs/middleware/proxy-fix' },
          { label: 'Effects Acquisition', path: '/docs/middleware/effect' },
        ]
      },
    ]
  },
  {
    title: 'Realtime & Network',
    items: [
      {
        label: 'HTTP Client', path: '/docs/http',
        children: [
          { label: 'Overview', path: '/docs/http' },
          { label: 'HTTPClient', path: '/docs/http/client' },
          { label: 'Sessions', path: '/docs/http/sessions' },
          { label: 'Transport Layer', path: '/docs/http/transport' },
          { label: 'Advanced Usage', path: '/docs/http/advanced' },
          { label: 'Error Handling', path: '/docs/http/faults' },
          { label: 'DI Integration', path: '/docs/http/integration' },
          {
            label: 'Core API Reference', path: '/docs/http/api',
            children: [
              { label: 'Request API', path: '/docs/http/api/request' },
              { label: 'Response API', path: '/docs/http/api/response' },
              { label: 'Auth API', path: '/docs/http/api/auth' },
              { label: 'Cookies API', path: '/docs/http/api/cookies' },
              { label: 'Middleware API', path: '/docs/http/api/middleware' },
              { label: 'Multipart API', path: '/docs/http/api/multipart' },
              { label: 'Streaming API', path: '/docs/http/api/streaming' },
            ]
          },
        ]
      },
      {
        label: 'WebSockets', path: '/docs/websockets',
        children: [
          { label: 'Overview', path: '/docs/websockets' },
          { label: 'Socket Controllers', path: '/docs/websockets/controllers' },
          { label: 'Runtime', path: '/docs/websockets/runtime' },
          { label: 'Adapters', path: '/docs/websockets/adapters' },
        ]
      },
      {
        label: 'Server-Sent Events', path: '/docs/sse',
        children: [
          { label: 'Overview', path: '/docs/sse/overview' },
          { label: 'Standard Events', path: '/docs/sse/standard' },
          { label: 'Text & JSON Streams', path: '/docs/sse/streams' },
          { label: 'OpenAI Streaming', path: '/docs/sse/openai' },
          { label: 'Resource Management', path: '/docs/sse/resources' },
        ]
      },
    ]
  },
  {
    title: 'Caching',
    items: [
      {
        label: 'Cache', path: '/docs/cache',
        children: [
          { label: 'Overview', path: '/docs/cache' },
          { label: 'Configuration', path: '/docs/cache/configuration' },
          { label: 'CLI', path: '/docs/cache/cli' },
          { label: 'CacheService', path: '/docs/cache/service' },
          { label: 'Backends', path: '/docs/cache/backends' },
          { label: 'Decorators', path: '/docs/cache/decorators' },
          { label: 'API Reference', path: '/docs/cache/api-reference' },
        ]
      },
    ]
  },
  {
    title: 'Storage & Filesystem',
    items: [
      {
        label: 'Storage', path: '/docs/storage',
        children: [
          { label: 'Overview', path: '/docs/storage/overview' },
          { label: 'API Reference', path: '/docs/storage/api' },
          { label: 'Configuration', path: '/docs/storage/configuration' },
          { label: 'Backends', path: '/docs/storage/backends' },
          { label: 'Controller Guide', path: '/docs/storage/controller' },
        ]
      },
      {
        label: 'Filesystem', path: '/docs/filesystem',
        children: [
          { label: 'Overview', path: '/docs/filesystem/overview' },
          { label: 'API Reference', path: '/docs/filesystem/api' },
          { label: 'Operations', path: '/docs/filesystem/operations' },
          { label: 'Controller Guide', path: '/docs/filesystem/controller' },
        ]
      },
    ]
  },
  {
    title: 'Localization & i18n',
    items: [
      {
        label: 'i18n', path: '/docs/i18n',
        children: [
          { label: 'Overview', path: '/docs/i18n' },
          { label: 'Architecture', path: '/docs/i18n/architecture' },
          { label: 'Configuration', path: '/docs/i18n/configuration' },
          { label: 'Integration', path: '/docs/i18n/integration' },
          { label: 'API Reference', path: '/docs/i18n/api-reference' },
          { label: 'CLI', path: '/docs/i18n/cli' },
          { label: 'Edge Cases', path: '/docs/i18n/edge-cases' },
          { label: 'Troubleshooting', path: '/docs/i18n/troubleshooting' },
        ]
      },
    ]
  },
  {
    title: 'Templates & Mail',
    items: [
      {
        label: 'Templates', path: '/docs/templates',
        children: [
          { label: 'Overview', path: '/docs/templates' },
          { label: 'TemplateEngine', path: '/docs/templates/engine' },
          { label: 'Loaders', path: '/docs/templates/loaders' },
          { label: 'Security', path: '/docs/templates/security' },
        ]
      },
      {
        label: 'Mail', path: '/docs/mail',
        children: [
          { label: 'Overview', path: '/docs/mail' },
          { label: 'MailService', path: '/docs/mail/service' },
          { label: 'Providers', path: '/docs/mail/providers' },
          { label: 'Templates', path: '/docs/mail/templates' },
        ]
      },
    ]
  },
  {
    title: 'Background Jobs',
    items: [
      {
        label: 'Tasks', path: '/docs/tasks',
        children: [
          { label: 'Overview', path: '/docs/tasks/overview' },
          { label: 'API Reference', path: '/docs/tasks/api' },
          { label: 'Configuration', path: '/docs/tasks/configuration' },
          { label: 'Retry Logic', path: '/docs/tasks/retry' },
          { label: 'Scheduling', path: '/docs/tasks/scheduling' },
          { label: 'Controller Guide', path: '/docs/tasks/controller' },
        ]
      },
    ]
  },
  {
    title: 'Tooling',
    items: [
      {
        label: 'CLI', path: '/docs/cli',
        children: [
          { label: 'Overview', path: '/docs/cli' },
          { label: 'Core Commands', path: '/docs/cli/core' },
          { label: 'Database', path: '/docs/cli/database' },
          { label: 'Inspection', path: '/docs/cli/inspection' },
          { label: 'Generators', path: '/docs/cli/generators' },
          { label: 'WebSocket', path: '/docs/cli/websockets' },
          { label: 'Deploy', path: '/docs/cli/deploy' },
          { label: 'Artifacts', path: '/docs/cli/artifacts' },
          { label: 'Subsystems', path: '/docs/cli/subsystems' },
        ]
      },
      {
        label: 'Testing', path: '/docs/testing',
        children: [
          { label: 'Overview', path: '/docs/testing' },
          { label: 'TestClient', path: '/docs/testing/client' },
          { label: 'Test Cases', path: '/docs/testing/cases' },
          { label: 'Mocks & Fixtures', path: '/docs/testing/mocks' },
          { label: 'Test Runner (aq test)', path: '/docs/testing/runner' },
        ]
      },
      {
        label: 'OpenAPI', path: '/docs/openapi',
      },
    ]
  },
  {
    title: 'Advanced',
    items: [
      {
        label: 'Aquilary Registry', path: '/docs/aquilary',
        children: [
          { label: 'Overview', path: '/docs/aquilary/overview' },
          { label: 'Manifest System', path: '/docs/aquilary/manifest' },
          { label: 'RuntimeRegistry', path: '/docs/aquilary/runtime' },
          { label: 'Fingerprinting', path: '/docs/aquilary/fingerprint' },
        ]
      },
      {
        label: 'Subsystem', path: '/docs/subsystem',
        children: [
          { label: 'Overview', path: '/docs/subsystem/overview' },
          { label: 'Flow Pipelines', path: '/docs/subsystem/pipelines' },
          { label: 'Flow Context & Nodes', path: '/docs/subsystem/context-nodes' },
          { label: 'Layers & Compositions', path: '/docs/subsystem/layers' },
          { label: 'Built-in Effects', path: '/docs/subsystem/built-in' },
          { label: 'DBTx Effect', path: '/docs/subsystem/dbtx' },
          { label: 'Cache Effect', path: '/docs/subsystem/cache' },
          { label: 'Queue & Task Effects', path: '/docs/subsystem/queue' },
          { label: 'HTTP Client Effect', path: '/docs/subsystem/http' },
          { label: 'Storage Effect', path: '/docs/subsystem/storage' },
          { label: 'Custom Effects', path: '/docs/subsystem/custom' },
        ]
      },
      {
        label: 'Fault System', path: '/docs/faults',
        children: [
          { label: 'Overview', path: '/docs/faults' },
          { label: 'Fault Taxonomy', path: '/docs/faults/taxonomy' },
          { label: 'FaultEngine', path: '/docs/faults/engine' },
          { label: 'Fault Handlers', path: '/docs/faults/handlers' },
          { label: 'Fault Domains', path: '/docs/faults/domains' },
          { label: 'Advanced Handlers', path: '/docs/faults/advanced' },
        ]
      },
    ]
  },
];

// Helper to recursively find labels
function findItemLabel(items, pathVal) {
  for (const item of items) {
    if (item.path.toLowerCase() === pathVal.toLowerCase()) {
      return item.label;
    }
    if (item.children) {
      const found = findItemLabel(item.children, pathVal);
      if (found) return found;
    }
  }
  return null;
}

// 3. Static metadata configuration for root-level pages
const staticPages = {
  '/': {
    title: 'Aquilia — High-Performance Async Python Web Framework',
    description: 'Aquilia is a Manifest-First, async-native Python web framework with zero boilerplate. Built-in ORM, DI, auth, sessions, caching, WebSockets, Docker/K8s manifests, and admin dashboard. Production-ready from day one.',
    keywords: 'Python web framework, async Python, Python API framework, Python REST API, manifest-first, dependency injection Python, Python ORM, background tasks, Python microservices, Docker Kubernetes deployment, Python admin dashboard, Aquilia framework, high-performance Python',
    plainText: 'Aquilia is a Manifest-First, async-native Python framework with zero boilerplate. Built-in ORM, dependency injection, authentication, sessions, caching, WebSockets, background tasks, admin dashboard, and manifest-first tooling.'
  },
  '/benchmark': {
    title: 'Framework Benchmarks — Aquilia vs FastAPI vs Django',
    description: 'Compare Aquilia performance against FastAPI, Starlette, Django, and Flask. Review throughput, latency, concurrency, and memory consumption metrics under high load.',
    keywords: 'Python benchmarks, FastAPI vs Aquilia, web framework performance, async performance, python web framework, async Python',
    plainText: 'Compare Aquilia performance metrics (throughput, latency, concurrency, memory consumption) against FastAPI, Starlette, Django, and Flask under high load.'
  },
  '/changelogs': {
    title: 'Changelogs & Developer Logs — Aquilia',
    description: 'Detailed changelogs, API deprecations, migration guides, and release logs for Aquilia framework developers.',
    keywords: 'Aquilia changelogs, API deprecations, migration guides, release notes',
    plainText: 'Read the latest changelogs, API deprecations, and upgrade migration guides for the Aquilia Python framework.'
  },
  '/releases': {
    title: 'Releases & Version History — Aquilia',
    description: 'Stay up to date with the latest releases, features, performance improvements, bug fixes, and upgrade notes of the Aquilia Python framework.',
    keywords: 'Aquilia releases, Python web framework releases, async Python version history, Aquilia framework changelogs',
    plainText: 'Explore version history, GitHub releases, performance improvements, and bug fixes for the Aquilia Python framework.'
  },
  '/help': {
    title: 'Help Center & Support — Aquilia',
    description: 'Find resources, FAQs, troubleshooting guides, and community channels to resolve issues with the Aquilia Python framework.',
    keywords: 'Aquilia support, help center, ScopeViolationError, PatternSyntaxError, Python framework support',
    plainText: 'Get help and technical support. View frequently asked questions, resolve common exceptions like ScopeViolationError and PatternSyntaxError, and connect with our team.'
  },
  '/community': {
    title: 'Developer Community & Ecosystem — Aquilia',
    description: 'Join the Aquilia framework community. Connect on GitHub, Discussions, and contribute to the async Python ecosystem.',
    keywords: 'Aquilia community, Python open source community, async Python framework community, contribute to Aquilia',
    plainText: 'Join the Aquilia ecosystem. Learn how to contribute to the open-source Python framework and connect on Discord, Discussions, and GitHub.'
  },
  '/privacy': {
    title: 'Privacy Policy — Aquilia',
    description: 'Read the privacy policy for Aquilia documentation and services. Learn how we handle your data.',
    keywords: 'privacy policy, compliance, cookies, Aquilia framework',
    plainText: 'Privacy Policy and data practices description for the Aquilia documentation and related services.'
  },
  '/terms': {
    title: 'Terms & Conditions — Aquilia',
    description: 'Terms and conditions describing guidelines for using the Aquilia documentation, assets, and licensing policies.',
    keywords: 'terms of service, user agreement, Aquilia framework documentation',
    plainText: 'Terms of Service and terms of use for the Aquilia documentation, assets, and branding guidelines.'
  }
};

// 4. Crawl sitemap sections to gather all paths
const pathsToPrerender = Object.keys(staticPages);

function crawl(items) {
  items.forEach(item => {
    // Add child page path
    pathsToPrerender.push(item.path);
    if (item.children) {
      crawl(item.children);
    }
  });
}

docSections.forEach(section => {
  crawl(section.items);
});

// Remove duplicates and normalize paths
const uniquePaths = Array.from(new Set(pathsToPrerender.map(p => p.toLowerCase().replace(/\/$/, ''))));

// 5. Read index.html template from dist folder
const distPath = path.join(__dirname, '../dist');
const templateHtml = fs.readFileSync(path.join(distPath, 'index.html'), 'utf-8');

console.log(`Prerendering ${uniquePaths.length} pages...`);

uniquePaths.forEach(p => {
  let title, description, keywords, plainText;

  // Determine metadata
  const originalPath = Object.keys(staticPages).find(k => k.toLowerCase() === p);
  if (originalPath) {
    // Static page
    const metadata = staticPages[originalPath];
    title = metadata.title;
    description = metadata.description;
    keywords = metadata.keywords;
    plainText = metadata.plainText;
  } else {
    // Doc page
    // 1. Find matching item label
    let pageLabel = 'Documentation';
    for (const sec of docSections) {
      const found = findItemLabel(sec.items, p);
      if (found) {
        pageLabel = found;
        break;
      }
    }
    
    title = `${pageLabel} — Aquilia Documentation`;
    description = `Comprehensive guide and documentation for ${pageLabel} in the Aquilia framework. View API reference, examples, and implementation patterns.`;
    keywords = `Aquilia, ${pageLabel}, Python framework, async, dependency injection, ORM, WebSockets, background tasks`;

    // 2. Find matching content in docsContent.ts
    // Let's normalize lookups (e.g. /docs/server/aquilia-server -> /docs/server)
    let searchPath = p;
    if (p === '/docs/server/aquilia-server') searchPath = '/docs/server';
    else if (p === '/docs/config/loader') searchPath = '/docs/config';
    else if (p === '/docs/request-response/request') searchPath = '/docs/request-response';
    else if (p === '/docs/controllers/overview') searchPath = '/docs/controllers';
    else if (p === '/docs/authz/overview') searchPath = '/docs/authz';
    else if (p === '/docs/sessions/overview') searchPath = '/docs/sessions';
    else if (p === '/docs/signing/overview') searchPath = '/docs/signing';
    else if (p === '/docs/middleware/overview') searchPath = '/docs/middleware';
    else if (p === '/docs/http/overview') searchPath = '/docs/http';
    else if (p === '/docs/sse/overview') searchPath = '/docs/sse';
    else if (p === '/docs/cache/overview') searchPath = '/docs/cache';
    else if (p === '/docs/storage/overview') searchPath = '/docs/storage';
    else if (p === '/docs/filesystem/overview') searchPath = '/docs/filesystem';
    else if (p === '/docs/i18n/overview') searchPath = '/docs/i18n';
    else if (p === '/docs/templates/overview') searchPath = '/docs/templates';
    else if (p === '/docs/mail/overview') searchPath = '/docs/mail';
    else if (p === '/docs/tasks/overview') searchPath = '/docs/tasks';
    else if (p === '/docs/cli/overview') searchPath = '/docs/cli';
    else if (p === '/docs/testing/overview') searchPath = '/docs/testing';
    else if (p === '/docs/aquilary/overview') searchPath = '/docs/aquilary';
    else if (p === '/docs/subsystem/overview') searchPath = '/docs/subsystem';
    else if (p === '/docs/faults/overview') searchPath = '/docs/faults';
    
    // Exact lookups or partial matching fallback
    let docItem = docsContent.find(d => d.path.toLowerCase() === searchPath);
    if (!docItem) {
      // Suffix search
      docItem = docsContent.find(d => searchPath.endsWith(d.path.toLowerCase()));
    }
    
    plainText = docItem ? docItem.plainText : `${pageLabel} documentation page in the Aquilia async Python web framework.`;
  }

  const canonicalUrl = `https://aquilia.tubox.cloud${p === '' ? '/' : p}`;

  // 6. Generate the prerendered HTML content
  let outputHtml = templateHtml;

  // Replace standard titles and tags
  outputHtml = outputHtml.replace(/<title>[^<]*<\/title>/g, `<title>${title}</title>`);
  outputHtml = outputHtml.replace(/<meta\s+name="title"\s+content="[^"]*"\s*\/>/g, `<meta name="title" content="${title}" />`);
  outputHtml = outputHtml.replace(/<meta\s+name="description"\s+content="[^"]*"\s*\/>/g, `<meta name="description" content="${description}" />`);
  outputHtml = outputHtml.replace(/<meta\s+name="keywords"\s+content="[^"]*"\s*\/>/g, `<meta name="keywords" content="${keywords}" />`);
  outputHtml = outputHtml.replace(/<link\s+rel="canonical"\s+href="[^"]*"\s*\/>/g, `<link rel="canonical" href="${canonicalUrl}" />`);

  // Replace Open Graph / Facebook tags
  outputHtml = outputHtml.replace(/<meta\s+property="og:title"\s+content="[^"]*"\s*\/>/g, `<meta property="og:title" content="${title}" />`);
  outputHtml = outputHtml.replace(/<meta\s+property="og:description"\s+content="[^"]*"\s*\/>/g, `<meta property="og:description" content="${description}" />`);
  outputHtml = outputHtml.replace(/<meta\s+property="og:url"\s+content="[^"]*"\s*\/>/g, `<meta property="og:url" content="${canonicalUrl}" />`);

  // Replace Twitter tags
  outputHtml = outputHtml.replace(/<meta\s+name="twitter:title"\s+content="[^"]*"\s*\/>/g, `<meta name="twitter:title" content="${title}" />`);
  outputHtml = outputHtml.replace(/<meta\s+name="twitter:description"\s+content="[^"]*"\s*\/>/g, `<meta name="twitter:description" content="${description}" />`);
  outputHtml = outputHtml.replace(/<meta\s+name="twitter:url"\s+content="[^"]*"\s*\/>/g, `<meta name="twitter:url" content="${canonicalUrl}" />`);

  // Replace the generic <noscript> tag with page-specific contents
  const pageNoscript = `<noscript>
    <div style="padding:2rem;max-width:800px;margin:0 auto;font-family:system-ui,sans-serif;">
      <h1>${title}</h1>
      <p>${description}</p>
      <hr style="margin:2rem 0;opacity:0.2;" />
      <div style="line-height:1.6;font-size:1.1rem;color:#333;">
        ${plainText}
      </div>
      <p style="margin-top:3rem;"><a href="https://aquilia.tubox.cloud">Go to Homepage</a></p>
    </div>
  </noscript>`;
  
  outputHtml = outputHtml.replace(/<noscript>[\s\S]*?<\/noscript>/g, pageNoscript);

  // 7. Write files to target directories
  if (p === '' || p === '/') {
    // Root index.html
    fs.writeFileSync(path.join(distPath, 'index.html'), outputHtml, 'utf-8');
  } else {
    // Sub-route directory (e.g. dist/docs/installation/index.html)
    const pageDir = path.join(distPath, p);
    fs.mkdirSync(pageDir, { recursive: true });
    fs.writeFileSync(pageDir + '/index.html', outputHtml, 'utf-8');
  }
});

console.log(`Pre-rendering completed successfully for ${uniquePaths.length} routes.`);
