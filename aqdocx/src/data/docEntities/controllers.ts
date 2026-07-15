import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'controller.controller',
    type: 'class',
    title: 'Controller',
    description: 'Base class for class-based HTTP handlers. Supports constructor-based DI, lifecycle hooks, versioning, throttling, interceptors, and exception filters.',
    signature: 'class Controller:\n    prefix: str = ""\n    pipeline: list[Any] = []\n    tags: list[str] = []\n    instantiation_mode: str = "per_request"\n    version: str | None = None\n    throttle: Throttle | None = None\n    interceptors: list[Any] = []\n    exception_filters: list[Any] = []\n    timeout: float = 0\n    max_body_size: int = 0',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/overview',
    source: { file: 'aquilia/controller/base.py', line: 497 }
  },
  {
    id: 'controller.requestctx',
    type: 'class',
    title: 'RequestCtx',
    description: 'Context object passed to controller methods. Optimized with __slots__ and pooled via RequestCtxPool to eliminate per-request allocation overhead.',
    signature: 'class RequestCtx:\n    request: Request\n    identity: Identity | None\n    session: Session | None\n    auth: Any | None\n    container: Any | None\n    state: dict[str, Any]\n    request_id: str',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/request-ctx',
    source: { file: 'aquilia/controller/base.py', line: 55 }
  },
  {
    id: 'controller.exceptionfilter',
    type: 'class',
    title: 'ExceptionFilter',
    description: 'Catches unhandled exceptions raised in controller methods and converts them to HTTP responses.',
    signature: 'class ExceptionFilter:\n    catches: list[type] = []\n    async def catch(self, exception: Exception, ctx: RequestCtx) -> Response | None: ...',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/controllers/overview',
    source: { file: 'aquilia/controller/base.py', line: 260 }
  },
  {
    id: 'controller.interceptor',
    type: 'class',
    title: 'Interceptor',
    description: 'Controller hooks executed before and after handlers. Good for logging, metrics, response decoration, or caching.',
    signature: 'class Interceptor:\n    async def before(self, ctx: RequestCtx) -> Response | None: ...\n    async def after(self, ctx: RequestCtx, result: Any) -> Any: ...',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/controllers/overview',
    source: { file: 'aquilia/controller/base.py', line: 303 }
  },
  {
    id: 'controller.throttle',
    type: 'class',
    title: 'Throttle',
    description: 'Sliding window in-memory rate limiter with LRU eviction and memory bounds to protect against DoS attacks.',
    signature: 'class Throttle:\n    def __init__(self, limit: int = 100, window: int = 60, max_clients: int = 10000)',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/controllers/overview',
    source: { file: 'aquilia/controller/base.py', line: 355 }
  },
  {
    id: 'controller.validate_body',
    type: 'decorator',
    title: '@validate_body(contract_class)',
    description: 'Decorator that parses and validates request bodies using an Aquilia Contract. Passes validated_data downstream as "body".',
    signature: 'def validate_body(contract_class: type, *, projection: str = "__all__") -> Callable',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/validation',
    source: { file: 'aquilia/controller/validation.py', line: 50 }
  },
  {
    id: 'controller.get',
    type: 'decorator',
    title: '@GET(path)',
    description: 'HTTP GET route decorator. Binds an endpoint route template to a controller method.',
    signature: '@GET(path: str | None = None, *, pipeline: list[Any] = None, request_contract: type = None, response_contract: type = None, filterset_class: type = None, pagination_class: type = None, version: str | list[str] = None)',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/controllers/decorators/get',
    source: { file: 'aquilia/controller/decorators.py', line: 180 }
  },
  {
    id: 'controller.post',
    type: 'decorator',
    title: '@POST(path)',
    description: 'HTTP POST route decorator. Typically used for resource creation.',
    signature: '@POST(path: str | None = None, *, pipeline: list[Any] = None, request_contract: type = None, response_contract: type = None, status_code: int = 201)',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/controllers/decorators/post',
    source: { file: 'aquilia/controller/decorators.py', line: 230 }
  },
  {
    id: 'controller.attributes',
    type: 'class',
    title: 'Attributes',
    description: 'Fluent builder for Controller class-level configuration. Configures prefix, pipeline, tags, instantiation_mode, version, throttle, interceptors, exception_filters, timeout, and max_body_size at class-definition time via the __set_name__ descriptor protocol with zero request-time overhead.',
    signature: 'class Attributes:\n    def prefix(self, value: str) -> Attributes\n    def pipeline(self, *nodes: Any) -> Attributes\n    def tags(self, *tag_values: str) -> Attributes\n    def instantiation_mode(self, mode: Literal["per_request", "singleton"]) -> Attributes\n    def version(self, v: str | list[str]) -> Attributes\n    def throttle(self, t: Throttle) -> Attributes\n    def interceptors(self, *items: Interceptor) -> Attributes\n    def exception_filters(self, *items: ExceptionFilter) -> Attributes\n    def timeout(self, seconds: float) -> Attributes\n    def max_body_size(self, bytes_size: int) -> Attributes',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/controllers/attributes',
    source: { file: 'aquilia/controller/attrs.py', line: 49 }
  }
])
