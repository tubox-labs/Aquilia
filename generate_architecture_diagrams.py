#!/usr/bin/env python3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets" / "architecture"

# Ensure output directory exists
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Helper function to generate SVG wrapper
def get_svg_wrapper(width, height, title, content):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">
  <defs>
    <!-- Drop Shadow Filter -->
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
      <feDropShadow dx="0" dy="4" stdDeviation="5" flood-color="#020617" flood-opacity="0.5"/>
    </filter>
    
    <!-- Accent Gradients -->
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0ea5e9" />
      <stop offset="100%" stop-color="#38bdf8" />
    </linearGradient>
    <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#059669" />
      <stop offset="100%" stop-color="#34d399" />
    </linearGradient>
    <linearGradient id="violetGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#7c3aed" />
      <stop offset="100%" stop-color="#a78bfa" />
    </linearGradient>
    <linearGradient id="roseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e11d48" />
      <stop offset="100%" stop-color="#fb7185" />
    </linearGradient>
    <linearGradient id="slateGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#475569" />
      <stop offset="100%" stop-color="#64748b" />
    </linearGradient>
    <linearGradient id="amberGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#d97706" />
      <stop offset="100%" stop-color="#f59e0b" />
    </linearGradient>

    <!-- Arrow Markers -->
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#38bdf8"/>
    </marker>
    <marker id="arrowMuted" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569"/>
    </marker>
    <marker id="arrowRose" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#fb7185"/>
    </marker>
  </defs>

  <style>
    .bg {{ fill: #070a13; rx: 12px; }}
    .border-stroke {{ stroke: #1e293b; stroke-width: 1.5; fill: none; }}
    .title {{ font-family: system-ui, -apple-system, sans-serif; font-size: 20px; font-weight: 800; fill: #f8fafc; letter-spacing: -0.02em; }}
    
    /* Card Styles */
    .card-bg {{ fill: #0f172a; stroke: #1e293b; stroke-width: 1.5; rx: 8px; filter: url(#shadow); transition: stroke 0.2s ease; }}
    .card-bg:hover {{ stroke: #38bdf8; }}
    .node-text-title {{ font-family: system-ui, -apple-system, sans-serif; font-size: 13px; font-weight: 700; fill: #f1f5f9; }}
    .node-text-desc {{ font-family: system-ui, -apple-system, sans-serif; font-size: 11px; fill: #94a3b8; }}
    
    /* Group Styles */
    .group-rect {{ rx: 12px; fill: #090d16; stroke: #1e293b; stroke-dasharray: 6 6; stroke-width: 1.5; }}
    .group-label {{ font-family: system-ui, -apple-system, sans-serif; font-size: 11px; font-weight: 700; fill: #475569; letter-spacing: 0.08em; }}
    
    /* Connection lines */
    .connection-line {{ fill: none; stroke: #38bdf8; stroke-width: 1.8; marker-end: url(#arrow); }}
    .connection-dashed {{ fill: none; stroke: #475569; stroke-width: 1.5; stroke-dasharray: 4 4; marker-end: url(#arrowMuted); }}
    .connection-error {{ fill: none; stroke: #fb7185; stroke-width: 1.8; stroke-dasharray: 3 3; marker-end: url(#arrowRose); }}
    
    /* Badges */
    .badge-rect {{ rx: 4px; }}
    .badge-text {{ font-family: system-ui, -apple-system, sans-serif; font-size: 9px; font-weight: 800; fill: #ffffff; }}
  </style>

  <rect width="{width}" height="{height}" class="bg" />
  <rect width="{width - 2}" height="{height - 2}" x="1" y="1" class="border-stroke" />
  
  <!-- Title and Subtitle Block -->
  <g transform="translate(30, 40)">
    <text x="0" y="0" class="title">{title}</text>
  </g>
  
  {content}
</svg>"""

def create_node(x, y, w, h, title, desc, gradient="slateGrad", meta=""):
    badge_html = ""
    if meta:
        badge_w = len(meta) * 6 + 10
        badge_html = f"""
    <rect class="badge-rect" x="{x + 16}" y="{y + h - 22}" width="{badge_w}" height="14" fill="url(#{gradient})" />
    <text class="badge-text" x="{x + 16 + badge_w/2}" y="{y + h - 12}" text-anchor="middle">{meta}</text>
        """
    desc_y_start = y + 42
    desc_lines = desc.split("\n")
    desc_html = ""
    for idx, line in enumerate(desc_lines):
        desc_html += f'<text x="{x + 16}" y="{desc_y_start + idx*15}" class="node-text-desc">{line}</text>'

    return f"""
  <g>
    <!-- Card Body -->
    <rect x="{x}" y="{y}" width="{w}" height="{h}" class="card-bg" />
    
    <!-- Accent Left Line -->
    <rect x="{x}" y="{y}" width="4" height="{h}" rx="2" fill="url(#{gradient})" />
    
    <!-- Title -->
    <text x="{x + 16}" y="{y + 24}" class="node-text-title">{title}</text>
    
    <!-- Description -->
    {desc_html}
    
    <!-- Badge -->
    {badge_html}
  </g>"""

def create_group(x, y, w, h, label):
    return f"""
  <g>
    <rect x="{x}" y="{y}" width="{w}" height="{h}" class="group-rect" />
    <text x="{x + 15}" y="{y - 8}" class="group-label">{label.upper()}</text>
  </g>"""

def draw_arrow(x1, y1, x2, y2, label="", style="connection-line"):
    label_html = ""
    if label:
        lx = (x1 + x2) / 2
        ly = (y1 + y2) / 2 - 8
        label_html = f'<text x="{lx}" y="{ly}" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10px" font-weight="600" fill="#94a3b8">{label}</text>'
    
    if abs(x1 - x2) > 40 and abs(y1 - y2) > 40:
        return f'<path d="M {x1} {y1} L {(x1+x2)/2} {y1} L {(x1+x2)/2} {y2} L {x2} {y2}" class="{style}" />{label_html}'
    
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{style}" />{label_html}'


# 1. High-Level Architecture
high_level_content = "\n".join([
    create_group(20, 90, 260, 480, "Development and CLI Source"),
    create_node(40, 120, 220, 90, "Developer Code", "Writes Controllers, Services,\nworkspace.py, manifest.py", "slateGrad", "INPUT"),
    create_node(40, 250, 220, 90, "Aquilia CLI (aq)", "aq init, aq add, aq serve,\naq compile, aq deploy", "blueGrad", "CLI"),
    create_node(40, 380, 220, 95, "Package Scanner", "Auto-discovers manifests\nand registers workspace\nmodules dynamically", "slateGrad", "DISCOVERY"),

    create_group(310, 90, 500, 480, "Aquilia Engine (ASGI Runtime)"),
    create_node(330, 120, 220, 95, "AquiliaRuntime", "Linear Boot Phase Manager\nCreated -> Discovering ->\nBootstrapping -> Ready", "violetGrad", "LIFECYCLE"),
    create_node(570, 120, 220, 95, "AquiliaServer", "Main ASGI callable\nInitializes AppRegistry,\nRouter and middleware", "violetGrad", "CORE SERVER"),
    create_node(330, 270, 220, 95, "DI Container", "Manages dependencies,\ninstantiates providers,\nhandles scoped DAGs", "emeraldGrad", "DI CONTAINER"),
    create_node(570, 270, 220, 95, "Flow Pipeline", "Executes composed route\nsteps: Guards -> Transforms\n-> Handler -> Hooks", "amberGrad", "PIPELINE"),
    create_node(330, 410, 460, 135, "Subsystem Integrations", "Database ORM (SQLite / PG)  |  Cache Services (Redis / Memory)\nStorage Engines (S3 / SFTP) |  Template Mailer and I18n Engine\nOpenTelemetry Tracer        |  Sockets (WS Realtime)", "slateGrad", "SERVICES"),

    create_group(840, 90, 240, 480, "Production Infrastructure"),
    create_node(850, 120, 220, 85, "Docker Integration", "Automated production\nDockerfile scaffolding", "slateGrad", "INFRA"),
    create_node(850, 240, 220, 85, "Compose Config", "Database, Cache, and\nAPI services configuration", "slateGrad", "COMPOSE"),
    create_node(850, 360, 220, 95, "Render Provider", "Auto-deploys codebase to\nRender cloud workspace\nvia credentials store", "blueGrad", "DEPLOYMENT"),

    draw_arrow(260, 165, 330, 165, "Config and Code"),
    draw_arrow(150, 210, 150, 250),
    draw_arrow(260, 295, 330, 165),
    draw_arrow(150, 340, 150, 380),
    draw_arrow(260, 425, 330, 455, "Register modules", "connection-dashed"),
    draw_arrow(550, 165, 570, 165),
    draw_arrow(440, 215, 440, 270),
    draw_arrow(680, 215, 680, 270),
    draw_arrow(550, 315, 570, 315, "Injects"),
    draw_arrow(440, 365, 440, 410),
    draw_arrow(680, 365, 680, 410),
    draw_arrow(790, 475, 850, 410),
    draw_arrow(790, 165, 850, 165),
    draw_arrow(790, 280, 850, 280)
])
with open(ASSETS_DIR / "high_level.svg", "w") as f:
    f.write(get_svg_wrapper(1100, 600, "Aquilia High-Level System Architecture", high_level_content))


# 2. Manifest Architecture
manifest_content = "\n".join([
    create_node(30, 110, 240, 95, "workspace.py", "Defines the workspace name,\nintegrations, global\nmiddleware, and modules list", "slateGrad", "WORKSPACE"),
    create_node(30, 240, 240, 95, "modules/*/manifest.py", "Declares local controllers,\nservices, task configurations,\nand autowire directives", "slateGrad", "APP MANIFEST"),
    create_node(330, 170, 250, 105, "PackageScanner", "Traverses filesystem modules\nfolder, parses AST metadata,\nregisters manifest objects\nand imports target packages", "blueGrad", "DISCOVERY"),
    create_node(640, 170, 250, 105, "RuntimeRegistry", "Compiles manifests into an\nin-memory route dictionary,\ndependency graph structure,\nand server environment", "violetGrad", "REGISTRY"),
    create_node(950, 170, 250, 105, "Aquilary.from_manifests", "Resolves manifest parameters\nat boot, validates schemas,\ninstantiates controllers and\nwires ASGI path mappings", "emeraldGrad", "BOOTSTRAP"),

    draw_arrow(270, 155, 330, 220),
    draw_arrow(270, 285, 330, 220),
    draw_arrow(580, 220, 640, 220, "Register"),
    draw_arrow(890, 220, 950, 220, "Initialize")
])
with open(ASSETS_DIR / "manifest.svg", "w") as f:
    f.write(get_svg_wrapper(1240, 320, "Aquilia Manifest and Component Wiring Architecture", manifest_content))


# 3. Runtime Architecture
runtime_content = "\n".join([
    create_node(30, 140, 190, 90, "1. CONFIGURING", "Injects workspace root\nto sys.path; loads\nworkspace.py config", "slateGrad", "START"),
    create_node(250, 140, 190, 90, "2. DISCOVERING", "PackageScanner scans\nmodules; imports all\nmodule manifests", "slateGrad"),
    create_node(470, 140, 190, 90, "3. BOOTSTRAPPING", "Initializes server,\nDI container graph,\nand registers routes", "slateGrad"),
    create_node(690, 140, 190, 90, "4. READY / ASGI L.", "Triggers startup hooks;\nDI constructs\nsingleton services", "blueGrad"),
    create_node(910, 140, 190, 90, "5. RUNNING", "ASGI server starts;\nhandles connection\nevents and routes", "emeraldGrad", "UPTIME"),
    create_node(1130, 140, 190, 90, "6. SHUTTING DOWN", "Triggers shutdown hooks;\ntears down DI resources,\nflushes tasks", "roseGrad", "STOP"),

    draw_arrow(220, 185, 250, 185),
    draw_arrow(440, 185, 470, 185),
    draw_arrow(660, 185, 690, 185),
    draw_arrow(900, 185, 910, 185),
    draw_arrow(1100, 185, 1130, 185)
])
with open(ASSETS_DIR / "runtime.svg", "w") as f:
    f.write(get_svg_wrapper(1350, 270, "Aquilia Runtime Boot Phase Lifecycle", runtime_content))


# 4. Dependency Injection Architecture
di_content = "\n".join([
    create_group(20, 100, 240, 360, "1. Discovery and Decl."),
    create_node(35, 130, 210, 85, "@service Decorator", "Marks class as a DI\ninjectable service", "slateGrad", "ANNOTATION"),
    create_node(35, 230, 210, 85, "@factory Decorator", "Marks method returning\ncustom value/provider", "slateGrad"),
    create_node(35, 330, 210, 85, "Manifest Decl.", "Manual list in AppManifest\nservices array", "slateGrad"),

    create_group(290, 100, 240, 360, "2. Provider Registry"),
    create_node(305, 130, 210, 85, "ClassProvider", "Instantiates target\nclass when resolved", "blueGrad", "PROVIDER"),
    create_node(305, 230, 210, 85, "FactoryProvider", "Invokes factory function\nwith dynamic params", "blueGrad"),
    create_node(305, 330, 210, 85, "ValueProvider", "Wraps raw configured\nobjects / secrets", "blueGrad"),

    create_group(560, 100, 240, 360, "3. Container and Scopes"),
    create_node(575, 130, 210, 85, "Singleton Scope", "Shared across the entire\nruntime lifetime", "violetGrad", "GLOBAL"),
    create_node(575, 230, 210, 85, "App Scope", "Bound to the server\nbootstrap instance", "violetGrad"),
    create_node(575, 330, 210, 85, "Request Scope", "Instantiated and destroyed\nper HTTP/WS connection", "violetGrad", "TRANSIENT"),

    create_group(830, 100, 240, 360, "4. Resolution Engine"),
    create_node(845, 130, 210, 105, "Topological Sorting", "Calculates compilation\norder; resolves service\ndependencies first", "emeraldGrad", "AST ENGINE"),
    create_node(845, 260, 210, 95, "DI Diagnostics", "Performs dry-run checks;\ndetects cyclical dependencies\nand raises errors", "roseGrad", "VALIDATION"),

    draw_arrow(245, 170, 305, 170),
    draw_arrow(245, 270, 305, 270),
    draw_arrow(245, 370, 305, 370),
    draw_arrow(515, 170, 575, 170),
    draw_arrow(515, 270, 575, 270),
    draw_arrow(515, 370, 575, 370),
    draw_arrow(785, 170, 845, 170),
    draw_arrow(785, 370, 845, 305)
])
with open(ASSETS_DIR / "di.svg", "w") as f:
    f.write(get_svg_wrapper(1050, 480, "Aquilia Dependency Injection Engine Architecture", di_content))


# 5. Middleware Architecture
middleware_content = "\n".join([
    create_node(20, 160, 150, 90, "ASGI Request", "Client initiates\nHTTP connection", "blueGrad", "INCOMING"),
    create_group(190, 100, 900, 200, "Middleware Execution Pipeline"),
    create_node(205, 140, 160, 90, "CORS / CSP Guard", "Security policy\nheaders check", "slateGrad", "PRIO 10"),
    create_node(380, 140, 160, 90, "Request ID", "Assigns unique\ntrace ID to ctx", "slateGrad", "PRIO 20"),
    create_node(555, 140, 160, 90, "Session Manager", "Loads session\ncryptographic state", "slateGrad", "PRIO 30"),
    create_node(730, 140, 160, 90, "Auth Guard", "Verifies token;\nbinds Identity", "slateGrad", "PRIO 40"),
    create_node(905, 140, 160, 90, "Telemetry Tracer", "Starts distributed\ntracing span", "slateGrad", "PRIO 50"),
    create_node(1110, 160, 160, 90, "Controller Router", "Matches route;\nruns FlowPipeline", "emeraldGrad", "CONTROLLER"),
    create_node(1290, 160, 150, 90, "ASGI Response", "Returns response\nto target client", "blueGrad", "OUTGOING"),

    draw_arrow(170, 185, 205, 185),
    draw_arrow(365, 185, 380, 185),
    draw_arrow(540, 185, 555, 185),
    draw_arrow(715, 185, 730, 185),
    draw_arrow(890, 185, 905, 185),
    draw_arrow(1065, 185, 1110, 185),
    draw_arrow(1270, 185, 1290, 185),
    draw_arrow(1110, 225, 1065, 225, "", "connection-dashed"),
    draw_arrow(905, 225, 890, 225, "", "connection-dashed"),
    draw_arrow(730, 225, 715, 225, "", "connection-dashed"),
    draw_arrow(555, 225, 540, 225, "", "connection-dashed"),
    draw_arrow(380, 225, 365, 225, "", "connection-dashed"),
    draw_arrow(205, 225, 170, 225, "", "connection-dashed")
])
with open(ASSETS_DIR / "middleware.svg", "w") as f:
    f.write(get_svg_wrapper(1460, 330, "Aquilia Middleware Chain Execution Flow", middleware_content))


# 6. Fault Architecture
fault_content = "\n".join([
    create_node(30, 140, 220, 95, "Exception Raised", "Uncaught runtime or\ncustom exception inside\ncontroller handler", "roseGrad", "ERROR STATE"),
    create_node(280, 140, 220, 95, "ExceptionMiddleware", "Catches all failures;\ninitiates mapping\nto structured Fault", "slateGrad", "INTERCEPTOR"),
    create_node(530, 140, 220, 95, "FaultEngine Mapping", "Resolves Exception\ndomain (Security, DB,\nCache) and maps handler", "violetGrad", "FAULT DOMAIN"),
    create_node(780, 140, 220, 95, "Fault Severity", "Checks recovery path;\nlogs critical alerts;\ndetermines public disclosure", "amberGrad", "ANALYZER"),
    create_node(1030, 140, 220, 95, "DebugPageRenderer", "Generates public JSON\nor visual rich HTML\ndebug template page", "blueGrad", "RESPONSE"),

    draw_arrow(250, 185, 280, 185, "", "connection-error"),
    draw_arrow(500, 185, 530, 185, "", "connection-error"),
    draw_arrow(750, 185, 780, 185, "", "connection-error"),
    draw_arrow(1000, 185, 1030, 185, "", "connection-error")
])
with open(ASSETS_DIR / "fault.svg", "w") as f:
    f.write(get_svg_wrapper(1280, 270, "Aquilia Structured Fault and Exception Lifecycle", fault_content))


# 7. Blueprint Architecture
blueprint_content = "\n".join([
    create_node(30, 140, 200, 95, "Raw Request Payload", "Incoming JSON, Form,\nor Query parameters\nfrom ASGI adapter", "blueGrad", "1. INPUT"),
    create_node(260, 140, 220, 95, "validate_body Decorator", "Intercepts route call;\nbinds Blueprint schema\nto request context", "slateGrad", "2. BINDING"),
    create_node(510, 140, 220, 95, "Facet Parsing and Casting", "Evaluates facet types\n(IntFacet, EmailFacet,\netc.); applies constraints", "slateGrad", "3. VALIDATION"),
    create_node(760, 140, 220, 95, "Molded Blueprint Instance", "Typed object initialized;\npassed as parameter\nto controller method", "emeraldGrad", "4. RESOLUTION"),
    create_node(1010, 140, 220, 95, "Lens / Projection", "Response filtering;\nexcludes WriteOnly fields;\ncomputes custom properties", "violetGrad", "5. OUTPUT"),

    draw_arrow(230, 185, 260, 185),
    draw_arrow(480, 185, 510, 185),
    draw_arrow(720, 185, 760, 185),
    draw_arrow(980, 185, 1010, 185)
])
with open(ASSETS_DIR / "blueprint.svg", "w") as f:
    f.write(get_svg_wrapper(1260, 270, "Aquilia Blueprint Validation and Data Molding Engine", blueprint_content))


# 8. Flow and Effect Architecture
flow_effect_content = "\n".join([
    create_group(20, 100, 520, 360, "FlowPipeline Execution Nodes"),
    create_node(40, 140, 220, 95, "1. Guard Nodes", "ClearanceGuard / RequireAuth\nverifies request permissions\nand short-circuits if forbidden", "slateGrad", "SECURITY"),
    create_node(40, 255, 220, 85, "2. Transform Nodes", "Transforms input body;\nmolds typed blueprints", "slateGrad"),
    create_node(40, 355, 220, 90, "3. Handler Node", "Controller action execution;\nbusiness logic execution", "blueGrad", "ACTION"),
    create_group(580, 100, 380, 360, "EffectScope Management"),
    create_node(600, 140, 340, 105, "4. Effect Requirements (@requires)", "Handler declares: @requires(DBTx['write'], Cache['user'])\nAcquires matching database transaction and cache\nnamespace resources from registry", "amberGrad", "ACQUIRE"),
    create_node(600, 260, 340, 85, "5. Provider Allocation", "EffectProvider resolves connection pool / client;\nbinds resource reference to FlowContext.effects", "amberGrad"),
    create_node(600, 360, 340, 85, "6. Resource Release and Commit", "Concludes flow; commits DB changes;\nreleases resource handles back to pool", "emeraldGrad", "RELEASE"),

    draw_arrow(260, 185, 280, 295),
    draw_arrow(260, 295, 280, 395),
    draw_arrow(260, 395, 600, 190, "Declares"),
    draw_arrow(770, 245, 770, 260),
    draw_arrow(770, 345, 770, 360)
])
with open(ASSETS_DIR / "flow_effect.svg", "w") as f:
    f.write(get_svg_wrapper(980, 480, "Aquilia Flow Pipeline and Effect Orchestration", flow_effect_content))



# 9. ORM Architecture
orm_content = "\n".join([
    create_node(30, 140, 220, 95, "Declarative Model", "Model fields (CharField,\nForeignKey, UUIDField)\ndefine database schema", "blueGrad", "MODEL LAYER"),
    create_node(280, 140, 220, 95, "QueryBuilder (Q)", "Chainable filter criteria\nsupports logical expressions\nand custom managers", "slateGrad", "QUERY BUILDER"),
    create_node(530, 140, 220, 95, "Transaction Manager", "Wraps queries with DBTx\ntransaction context;\nhandles commit / rollback", "violetGrad", "TRANSACTIONS"),
    create_node(780, 140, 220, 95, "Database Driver Adapter", "Compiles query to SQL;\nexecutes via native SQLite\nor asyncpg PostgreSQL", "emeraldGrad", "ADAPTER"),
    create_node(1030, 140, 220, 95, "Migration Engine", "Scans model schema snapshot;\ngenerates and executes\nmigration SQL scripts", "amberGrad", "MIGRATIONS"),

    draw_arrow(250, 185, 280, 185),
    draw_arrow(500, 185, 530, 185),
    draw_arrow(750, 185, 780, 185),
    draw_arrow(1000, 185, 1030, 185)
])
with open(ASSETS_DIR / "orm.svg", "w") as f:
    f.write(get_svg_wrapper(1280, 270, "Aquilia Pure Python ORM and Persistence Engine", orm_content))


# 10. Versioning Architecture
versioning_content = "\n".join([
    create_node(30, 140, 220, 95, "Route Request", "Request targets versioned\nAPI path: e.g. /users\nwith version parameter", "blueGrad", "API INPUT"),
    create_node(280, 140, 220, 95, "VersionResolver", "Extracts version using\nStrategy (URL, Header,\nQuery, or Media Type)", "slateGrad", "RESOLVER"),
    create_node(530, 140, 220, 95, "VersionGraph Router", "Matches request version to\ntarget Controller (V1.0,\nV2.0) using promotion", "violetGrad", "ROUTING MATCH"),
    create_node(780, 140, 220, 95, "SunsetPolicy Evaluator", "Inspects deprecation schedule;\nadds warning headers or\nraises SunsetFault if past", "amberGrad", "DEPRECATION"),
    create_node(1030, 140, 220, 95, "Response Delivery", "Appends Version and\nSunset warning headers;\nreturns response to client", "emeraldGrad", "RESPONSE"),

    draw_arrow(250, 185, 280, 185),
    draw_arrow(500, 185, 530, 185),
    draw_arrow(750, 185, 780, 185),
    draw_arrow(1000, 185, 1030, 185)
])
with open(ASSETS_DIR / "versioning.svg", "w") as f:
    f.write(get_svg_wrapper(1280, 270, "Aquilia API Versioning and Sunset Lifecycle", versioning_content))


# 11. Lifecycle Architecture
lifecycle_content = "\n".join([
    create_node(30, 140, 240, 95, "ASGI Startup (Lifespan)", "Invoked by ASGI server;\nloads AppManifest;\nstarts boot orchestration", "blueGrad", "STARTUP"),
    create_node(310, 140, 240, 95, "Subsystem Init (Lifecycle)", "Initializes DB connections,\nCache backends, Storage,\nOTel tracer, Task workers", "slateGrad", "INITIALIZATION"),
    create_node(590, 140, 240, 95, "Request Context Hooks", "Executes pre-request hooks;\nbinds context; resolves\nrequest-scoped DI graphs", "slateGrad", "RUNTIME WORK"),
    create_node(870, 140, 240, 95, "ASGI Shutdown (Lifespan)", "Invoked on server stop;\ntriggers cleanup hooks;\nfinalizes service pools", "roseGrad", "SHUTDOWN"),

    draw_arrow(270, 185, 310, 185),
    draw_arrow(550, 185, 590, 185),
    draw_arrow(830, 185, 870, 185)
])
with open(ASSETS_DIR / "lifecycle.svg", "w") as f:
    f.write(get_svg_wrapper(1140, 270, "Aquilia Lifespan and Hook Orchestration", lifecycle_content))


# 12. Complete System Architecture
complete_system_content = "\n".join([
    create_group(20, 100, 270, 480, "1. Source Scaffolding"),
    create_node(35, 130, 240, 85, "workspace.py", "Global settings,\nintegrations list", "slateGrad", "CONFIG"),
    create_node(35, 230, 240, 95, "modules/*/manifest.py", "AppManifest defines\ncontrollers, services\nand dependency rules", "slateGrad", "MANIFEST"),
    create_node(35, 340, 240, 85, "Controllers and Services", "Writes controller\nclasses and services", "blueGrad", "CODE"),
    create_node(35, 440, 240, 100, "PackageScanner", "CLI / runtime scans\nmodules tree to\nfind manifest objects", "slateGrad", "SCANNER"),

    create_group(310, 100, 480, 480, "2. Aquilia Runtime Boot and DI"),
    create_node(325, 130, 450, 95, "AquiliaRuntime Lifecycle", "Linear bootstrap orchestrator: CREATED -> CONFIGURING ->\nDISCOVERING -> BOOTSTRAPPING -> READY", "violetGrad", "BOOT PHASE"),
    create_node(325, 240, 215, 95, "DI Container Scope", "Resolves providers:\n- Singleton (Global)\n- App (Server instance)\n- Request (Connection)", "emeraldGrad", "DI REGISTRY"),
    create_node(560, 240, 215, 95, "DI Diagnostics Graph", "Dry-runs container;\ntest dependency cycle;\ncompiles request DAG", "emeraldGrad", "DI CHECK"),
    create_node(325, 350, 450, 105, "AquiliaServer (ASGI Adapter)", "Translates ASGI lifespan/HTTP connection scopes to Request/Response;\npasses request context into Middleware chain and Router", "violetGrad", "ASGI ENTRY"),
    create_node(325, 470, 450, 85, "RuntimeRegistry", "Binds dynamic and compiled routes; compiles versions mapping", "slateGrad", "REGISTRY"),

    create_group(810, 100, 600, 480, "3. Request Pipeline Execution"),
    create_node(825, 130, 570, 95, "Middleware Chain", "Runs sequentially by Priority Band:\nSecurity (10) -> RequestId (20) -> Session (30) -> Auth (40) -> OTel (50)", "slateGrad", "MIDDLEWARE"),
    create_node(825, 240, 275, 95, "FlowPipeline Context", "Binds Request state,\nscoped DI container,\nidentity, session", "amberGrad", "CONTEXT"),
    create_node(1115, 240, 280, 95, "FlowPipeline Nodes", "Guards (Clearance) ->\nTransforms (Validation) ->\nHandler -> Hooks", "amberGrad", "NODES"),
    create_node(825, 350, 570, 105, "EffectScope and Providers", "Acquires/releases declared resources around handler execution:\n- DB Transactions (DBTx['write']) | - Cache (Cache['user'])\n- File storage (Storage['s3'])     | - Outbound HTTP client", "amberGrad", "EFFECTS"),
    create_node(825, 470, 275, 85, "Structured Faults", "Catches exceptions;\nmaps to fault domain;\ngenerates public JSON/HTML", "roseGrad", "FAULTS"),
    create_node(1120, 470, 275, 85, "Response Delivery", "Appends version and\nsecurity headers;\nreturns output to ASGI", "blueGrad", "RESPONSE"),

    draw_arrow(275, 170, 325, 170),
    draw_arrow(275, 490, 325, 510),
    draw_arrow(432, 225, 432, 240),
    draw_arrow(432, 335, 432, 350),
    draw_arrow(775, 400, 825, 175),
    draw_arrow(775, 400, 825, 285),
    draw_arrow(1100, 175, 1115, 285),
    draw_arrow(962, 335, 962, 350),
    draw_arrow(1110, 395, 962, 510),
    draw_arrow(962, 455, 962, 470),
    draw_arrow(1100, 510, 1120, 510)
])
with open(ASSETS_DIR / "complete_system.svg", "w") as f:
    f.write(get_svg_wrapper(1430, 600, "Aquilia Complete System Architecture Diagram", complete_system_content))

print("All architecture diagrams generated successfully.")
