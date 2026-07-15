const fs = require('fs');
const path = require('path');

const DOMAIN = 'https://tubox.cloud';
const LASTMOD = new Date().toISOString().split('T')[0];

const rootRoutes = [
  { path: '/', priority: '1.0', changefreq: 'weekly' },
  { path: '/benchmark', priority: '0.8', changefreq: 'weekly' },
  { path: '/changelogs', priority: '0.7', changefreq: 'weekly' },
  { path: '/releases', priority: '0.7', changefreq: 'weekly' },
  { path: '/help', priority: '0.8', changefreq: 'weekly' },
  { path: '/community', priority: '0.8', changefreq: 'weekly' },
  { path: '/privacy', priority: '0.5', changefreq: 'monthly' },
  { path: '/terms', priority: '0.5', changefreq: 'monthly' },
];

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
      {
        label: 'Dependency Injection', path: '/docs/di',
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
        label: 'Contracts', path: '/docs/contracts',
        children: [
          { label: 'Overview', path: '/docs/contracts/overview' },
          { label: 'Facets', path: '/docs/contracts/facets' },
          { label: 'Projections', path: '/docs/contracts/projections' },
          { label: 'Lenses', path: '/docs/contracts/lenses' },
          { label: 'Seals (Validation)', path: '/docs/contracts/seals' },
          { label: 'Annotations', path: '/docs/contracts/annotations' },
          { label: 'Integration', path: '/docs/contracts/integration' },
          { label: 'Schemas', path: '/docs/contracts/schemas' },
          { label: 'Faults', path: '/docs/contracts/faults' },
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

const urls = [];

// Add root routes
rootRoutes.forEach(r => {
  urls.push({
    loc: `${DOMAIN}${r.path}`,
    priority: r.priority,
    changefreq: r.changefreq
  });
});

// Helper to recursively parse sidebar items
function crawl(items) {
  items.forEach(item => {
    urls.push({
      loc: `${DOMAIN}${item.path}`,
      priority: item.children ? '0.8' : '0.7',
      changefreq: 'monthly'
    });
    if (item.children) {
      crawl(item.children);
    }
  });
}

docSections.forEach(section => {
  crawl(section.items);
});

// Remove duplicates
const uniqueUrlsMap = new Map();
urls.forEach(u => {
  let loc = u.loc;
  if (loc !== `${DOMAIN}/` && loc.endsWith('/')) {
    loc = loc.slice(0, -1);
  }
  uniqueUrlsMap.set(loc, u);
});

const uniqueUrls = Array.from(uniqueUrlsMap.values());

const xmlEntries = uniqueUrls.map(u => `  <url>
    <loc>${u.loc}</loc>
    <lastmod>${LASTMOD}</lastmod>
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`).join('\n');

const sitemapXml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${xmlEntries}
</urlset>
`;

fs.writeFileSync(path.join(__dirname, '../public/sitemap.xml'), sitemapXml, 'utf-8');
console.log(`Successfully generated sitemap.xml with ${uniqueUrls.length} routes.`);
