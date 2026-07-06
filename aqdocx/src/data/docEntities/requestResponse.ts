import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'reqres.request',
    type: 'class',
    title: 'Request',
    description: 'Production-grade ASGI request wrapper with async body streaming, lazy parsing, and ReDoS/security protections.',
    signature: 'class Request:\n    def __init__(self, scope: ASGIScope, receive: ASGIReceive, send: Callable | None = None, *, max_body_size: int = 10_485_760, max_field_count: int = 1000, max_file_size: int = 2_147_483_648, upload_tempdir: PathLike | None = None, trust_proxy: bool | list[str] = False, chunk_size: int = 65536, json_max_size: int = 10_485_760, json_max_depth: int = 64, form_memory_threshold: int = 1048576)',
    language: 'python',
    parameters: [
      { name: 'scope', type: 'ASGIScope', description: 'Raw ASGI scope dictionary containing request metadata.' },
      { name: 'receive', type: 'ASGIReceive', description: 'ASGI receive channel callback.' },
      { name: 'send', type: 'Callable', optional: true, description: 'ASGI send channel callback.' },
      { name: 'max_body_size', type: 'int', optional: true, default: '10_485_760', description: 'Maximum allowed request body size in bytes.' },
      { name: 'max_field_count', type: 'int', optional: true, default: '1000', description: 'Maximum number of fields in forms/multipart requests.' },
      { name: 'max_file_size', type: 'int', optional: true, default: '2_147_483_648', description: 'Maximum single file size allowed in uploads.' },
      { name: 'trust_proxy', type: 'bool | list[str]', optional: true, default: 'False', description: 'Trust proxy headers for client IP detection. Can be list of trusted CIDRs.' }
    ],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/request-response/request',
    source: { file: 'aquilia/request.py', line: 215 }
  },
  {
    id: 'reqres.response',
    type: 'class',
    title: 'Response',
    description: 'ASGI 3 compliant response builder. Handles serialization, streaming, Range headers, SSE, content negotiation, and background tasks.',
    signature: 'class Response:\n    def __init__(self, content: bytes | str | Mapping | Sequence | AsyncIterator[bytes] | Iterator[bytes] | Awaitable[Any] = b"", status: int = 200, headers: Mapping[str, str | Sequence[str]] | None = None, media_type: str | None = None, *, background: BackgroundTask | list[BackgroundTask] | None = None, encoding: str = "utf-8", validate_headers: bool = True)',
    language: 'python',
    parameters: [
      { name: 'content', type: 'Any', description: 'Response payload: bytes, string, JSON dict/list, or async/sync iterator.' },
      { name: 'status', type: 'int', optional: true, default: '200', description: 'HTTP status code.' },
      { name: 'headers', type: 'Mapping', optional: true, description: 'HTTP headers dictionary.' },
      { name: 'media_type', type: 'str', optional: true, description: 'Explicit Content-Type header override.' }
    ],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/request-response/response',
    source: { file: 'aquilia/response.py', line: 358 }
  },
  {
    id: 'reqres.multidict',
    type: 'class',
    title: 'MultiDict',
    description: 'A dictionary supporting multiple values per key. Used for query parameters and URL-encoded form parsing.',
    signature: 'class MultiDict(MutableMapping[str, list[str]]):\n    def __init__(self, items: list[tuple[str, str]] | Mapping[str, str | list[str]] | None = None)',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/request-response/data-structures',
    source: { file: 'aquilia/_datastructures.py', line: 27 }
  },
  {
    id: 'reqres.headers',
    type: 'class',
    title: 'Headers',
    description: 'Case-insensitive header collection preserving original casing and supporting multiple values per header.',
    signature: 'class Headers:\n    def __init__(self, raw: list[tuple[bytes, bytes]] = None)',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/request-response/data-structures',
    source: { file: 'aquilia/_datastructures.py', line: 120 }
  },
  {
    id: 'reqres.cookiesigner',
    type: 'class',
    title: 'CookieSigner',
    description: 'HMAC-based cookie signer utilizing SHA-256 (default) and urlsafe-base64 formatting to sign and verify cookie values.',
    signature: 'class CookieSigner:\n    def __init__(self, secret_key: str | bytes, algorithm: str = "sha256")',
    language: 'python',
    parameters: [
      { name: 'secret_key', type: 'str | bytes', description: 'Secret key for signing.' },
      { name: 'algorithm', type: 'str', optional: true, default: '"sha256"', description: 'Hash algorithm: sha256, sha384, sha512.' }
    ],
    status: 'stable',
    docsHref: '/docs/request-response/response',
    source: { file: 'aquilia/response.py', line: 231 }
  },
  {
    id: 'reqres.uploadfile',
    type: 'class',
    title: 'UploadFile',
    description: 'Uploaded file representation. Keeps small files in memory and streams large files from disk to prevent unbounded RAM usage.',
    signature: 'class UploadFile:\n    async def read(self, size: int = -1) -> bytes\n    async def stream(self, chunk_size: int | None = None) -> AsyncIterator[bytes]\n    async def save(self, path: str | Path, overwrite: bool = False) -> Path\n    async def close(self) -> None',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/request-response/uploads',
    source: { file: 'aquilia/_uploads.py', line: 47 }
  },
  {
    id: 'reqres.formdata',
    type: 'class',
    title: 'FormData',
    description: 'Container for parsed form values containing both text fields and files.',
    signature: 'class FormData:\n    fields: MultiDict\n    files: dict[str, list[UploadFile]]',
    language: 'python',
    status: 'stable',
    docsHref: '/docs/request-response/uploads',
    source: { file: 'aquilia/_uploads.py', line: 184 }
  }
])
