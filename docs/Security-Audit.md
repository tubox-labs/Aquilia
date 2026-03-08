# Aquilia — Security Audit

> Vulnerability assessment, severity classification, and recommended fixes.

---

## Executive Summary

Aquilia demonstrates **strong security engineering** with industry-standard practices in most areas (Argon2id hashing, HMAC-signed cookies, structured faults, OWASP headers, CSRF protection). However, several issues were identified ranging from critical to low severity.

**All Critical and High severity issues have been remediated.**

**Overall Security Posture: Strong ✅**

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 2 | ✅ **All Fixed** |
| 🟠 High | 6 | ✅ **All Fixed** |
| 🟡 Medium | 10 | Should fix in next release |
| 🟢 Low | 8 | Fix when convenient |

---

## 🔴 Critical Issues

### CRIT-001: Pickle Deserialization in Cache Serializer ✅ FIXED

**Location:** `aquilia/cache/serializers.py` — `PickleSerializer`

**Status:** ✅ **Remediated** — `PickleCacheSerializer` now requires an explicit `secret_key` and wraps all serialized data with HMAC-SHA256 signatures. Deserialization verifies the signature before calling `pickle.loads()`, preventing arbitrary code execution from tampered cache data. A deprecation warning is emitted on instantiation encouraging migration to JSON/Msgpack serializers.

---

### CRIT-002: Debug Pages Expose Sensitive Data in Production ✅ FIXED

**Location:** `aquilia/debug/pages.py` — `render_exception_page()`

**Status:** ✅ **Remediated** — Three layers of defense added:
1. **Production kill-switch:** `render_debug_exception_page()` checks `AQUILIA_ENV`; returns a generic error page if `"production"` and logs a CRITICAL warning.
2. **Local variable redaction:** Variables whose names contain sensitive patterns (password, secret, token, key, auth, cookie, session, credit, ssn, private, credential, api_key, access_token, refresh_token) are replaced with `[REDACTED]`.
3. **Header redaction:** Sensitive request headers (Authorization, Cookie, Set-Cookie, X-API-Key, X-Auth-Token, Proxy-Authorization) are redacted from debug output.

---

## 🟠 High Severity Issues

### HIGH-001: ReDoS Risk in Query Filters ✅ FIXED

**Location:** `aquilia/controller/filters.py` — `_matches_lookup()` with `regex`/`iregex` lookups

**Status:** ✅ **Remediated** — Three-layer defense:
1. **Length limit:** User-supplied regex patterns are capped at 256 characters.
2. **Dangerous pattern detection:** Common ReDoS constructs (`(a+)+`, `(a|a)+`, nested quantifiers `.+.+`) are detected and rejected before compilation.
3. **Safe compilation wrapper:** `_safe_regex_compile()` catches all errors and returns `ValueError`; callers return `False` (no match) on invalid regex instead of crashing.

---

### HIGH-002: Unsigned Cursor Pagination Tokens ✅ FIXED

**Location:** `aquilia/controller/pagination.py` — `CursorPagination`

**Status:** ✅ **Remediated** — Cursor tokens are now HMAC-SHA256 signed:
1. `_encode_cursor()` produces `<base64-payload>.<base64-signature>` format.
2. `_decode_cursor()` verifies the HMAC signature before parsing. Tampered/unsigned cursors are rejected (returns `None`, treated as first page).
3. Secret key sourced from `AQUILIA_CURSOR_SECRET` env var; falls back to a per-process ephemeral key with a logged warning.

---

### HIGH-003: Dynamic Module Import from Manifest Strings ✅ FIXED

**Location:** `aquilia/di/core.py` — `ContainerBuilder._load_manifest_services()`

**Status:** ✅ **Remediated** — Multi-layer input validation:
1. **Path format validation:** Module paths must match `^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$` — no path traversal, no special characters.
2. **Class name validation:** Must match `^[a-zA-Z_][a-zA-Z0-9_]*$` — no dunder names allowed.
3. **Blocklist enforcement:** Top-level modules `os`, `sys`, `subprocess`, `shutil`, `importlib`, `ctypes`, `pickle`, `shelve`, `code`, `builtins`, `runpy`, `pty`, `commands` are blocked.
4. **Type verification:** Resolved objects must be `isinstance(obj, type)` — prevents loading arbitrary functions or modules as services.
5. **Audit logging:** All rejections logged at WARNING level with the offending service path.
2. Add manifest integrity verification (signed manifests)
3. Sandbox manifest loading in a restricted namespace
4. Log all dynamic imports for audit

---

### HIGH-004: X-Cache-Bypass Header in Production ✅ FIXED

**Location:** `aquilia/cache/middleware.py` — `CacheMiddleware`

**Status:** ✅ **Remediated** — Cache bypass now requires a valid secret token:
1. `X-Cache-Bypass` header value must exactly match `AQUILIA_CACHE_BYPASS_SECRET` environment variable (compared via `hmac.compare_digest` to prevent timing attacks).
2. If the env var is not set, bypass is completely disabled.
3. Invalid bypass attempts are logged at WARNING level and treated as normal cached requests.
4. **Bonus fix (MED-002):** ETag generation upgraded from MD5 to SHA-256 (`hashlib.sha256` with 32-char truncation).

---

### HIGH-005: Build Resolver Integrity Bypass ✅ FIXED

**Location:** `aquilia/build/resolver.py`

**Status:** ✅ **Remediated** — The `except Exception` fallback in `_resolve_from_bundle()` now sets `verified = False` instead of `verified = True`. Artifacts that fail SHA-256 digest re-verification are marked as unverified, preventing deployment of tampered bundles.

---

### HIGH-006: X-Forwarded-For Spoofing Without Trusted Proxy ✅ FIXED

**Location:** `aquilia/controller/base.py` — `Throttle` class; `aquilia/request.py` — `client_ip`

**Status:** ✅ **Remediated** — Two complementary fixes:
1. **`Request.client_ip()` rewritten:** When `trust_proxy` is a list of CIDR strings, the X-Forwarded-For chain is walked **right-to-left**, skipping entries that fall within trusted proxy networks. The first non-trusted IP is returned as the real client. This prevents attackers from prepending fake IPs. When `trust_proxy=True` (blanket), legacy left-most behaviour is preserved with a clear upgrade path.
2. **`Throttle._client_key()` secured:** No longer reads `X-Forwarded-For` directly. Delegates to `request.client_ip()` so that trusted-proxy validation is always honoured. Falls back to the ASGI scope's direct client tuple.

---

## 🟡 Medium Severity Issues

### MED-001: `sys.path` Manipulation During Build/Compile

**Location:** `aquilia/build/pipeline.py`, `aquilia/cli/compiler.py`

**Description:** The build pipeline inserts the workspace root into `sys.path` to load workspace.py. If the workspace root is attacker-controlled (e.g., malicious Git clone), this enables arbitrary code loading.

**Impact:** Code execution during build

**Recommendation:** Use isolated subprocess or restricted `importlib` for workspace loading.

---

### MED-002: MD5 for ETag Generation ✅ FIXED

**Location:** `aquilia/cache/middleware.py`

**Status:** ✅ **Remediated** (fixed alongside HIGH-004) — `_generate_etag()` now uses `hashlib.sha256` with 32-character truncation instead of `hashlib.md5`.

---

### MED-003: Redis URL Credential Exposure

**Location:** `aquilia/cache/base.py`, `aquilia/cache/backends/redis.py`

**Description:** Redis URLs containing passwords are stored in `CacheConfig.url` and passed directly to connection constructors. They may appear in logs, error messages, or debug output.

**Recommendation:** Mask passwords in Redis URLs before logging (similar to `_mask_dsn` in the PostgreSQL adapter).

---

### MED-004: Global Mutable State in Cache Decorators

**Location:** `aquilia/cache/decorators.py` — `_default_cache`

**Description:** The cache decorator uses a module-level `_default_cache` variable. In async environments, this is safe due to GIL, but it's fragile and could break under alternative Python implementations.

**Recommendation:** Use `ContextVar` for async-safe cache resolution.

---

### MED-005: SQLite PRAGMA with Table Names

**Location:** `aquilia/db/adapters/sqlite.py`

**Description:** Introspection methods use f-string formatting for table names in PRAGMA calls. While table names come from internal code, this is a defense-in-depth violation.

**Recommendation:** Validate table names against `^[a-zA-Z_][a-zA-Z0-9_]*$` before use in PRAGMA statements.

---

### MED-006: ContextVar Cross-Request Leakage

**Location:** `aquilia/di/request_context.py`

**Description:** The DI request container uses a `ContextVar`. If not properly cleared between requests (e.g., in certain middleware error paths), a request could access another request's DI container.

**Recommendation:** Ensure `clear_request_container()` is called in a `finally` block in the ASGI adapter.

---

### MED-007: Provider Override Without Authorization

**Location:** `aquilia/di/container.py` — `Container.override()`

**Description:** The `override()` method silently replaces existing providers. If called from untrusted code, it could replace security-critical services (e.g., auth manager, identity store).

**Recommendation:** Add an `allow_override` flag to sensitive providers. Log all overrides at WARNING level.

---

### MED-008: Requirements File Version Drift

**Location:** `requirements-dev.txt` vs `pyproject.toml`

**Description:** Version ranges in `requirements-dev.txt` are lower than those in `pyproject.toml` (e.g., pytest >=7.4 vs >=8.0, aiosqlite >=0.19 vs >=0.20). This can lead to inconsistent test environments.

**Recommendation:** Remove `requirements-dev.txt` and `requirements-cli.txt`. Use `pip install -e ".[dev]"` only.

---

### MED-009: Missing Dependencies in pyproject.toml

**Location:** `pyproject.toml`, `requirements-cli.txt`

**Description:** `rich`, `watchdog`, and `hypothesis` are used by CLI and tests but not declared in any `pyproject.toml` extras.

**Recommendation:** Add `rich` and `watchdog` to a `cli` extra. Add `hypothesis` to the `testing` extra.

---

### MED-010: Dockerfile Uses Default Credentials

**Location:** `Dockerfile`

**Description:** The PostgreSQL Dockerfile uses `admin` / `admin123` as default credentials.

**Recommendation:** Use environment variable substitution without defaults, or document clearly that this is dev-only.

---

## 🟢 Low Severity Issues

### LOW-001: `MANIFEST.in` References Missing `requirements.txt`

**Location:** `MANIFEST.in`

**Description:** References `requirements.txt` which doesn't exist at the repo root.

**Recommendation:** Remove the line or create the file.

---

### LOW-002: DI Error Messages Expose Internal Paths

**Location:** `aquilia/di/errors.py`

**Description:** DI errors include module paths and line numbers in error messages. These are helpful for development but could leak internal architecture in production error responses.

**Recommendation:** Sanitize error details for non-debug responses.

---

### LOW-003: Swagger UI Loads from CDN

**Location:** `aquilia/controller/openapi.py` — `_swagger_ui_html()`

**Description:** Swagger UI HTML includes scripts from `cdn.jsdelivr.net`. This creates an external dependency and potential supply-chain risk.

**Recommendation:** Bundle Swagger UI assets or make CDN URLs configurable.

---

### LOW-004: Missing `__all__` in Some Modules

**Location:** Various subpackages

**Description:** Some modules don't define `__all__`, allowing unintended exports via `from module import *`.

**Recommendation:** Add `__all__` to all public modules.

---

### LOW-005: No Rate Limiting on Admin Login

**Location:** `aquilia/admin/controller.py`

**Description:** The admin login endpoint doesn't have dedicated rate limiting beyond the global rate limiter. An attacker could attempt brute-force against admin credentials.

**Recommendation:** Add per-IP rate limiting specifically for `/admin/login` (e.g., 5 attempts per 15 minutes).

---

### LOW-006: Avatar Upload Magic Byte Sniffing

**Location:** `aquilia/admin/controller.py`

**Description:** Avatar uploads check magic bytes for image type detection, but the implementation only checks a few formats. Malicious files with valid magic bytes but embedded exploits could pass.

**Recommendation:** Use a proper image validation library (e.g., Pillow) to verify the image is parseable.

---

### LOW-007: Console Mail Provider Logs Content

**Location:** `aquilia/mail/providers/console.py`

**Description:** The console mail provider logs full email content including potentially sensitive data.

**Recommendation:** Add a `redact_body` option for non-development environments.

---

### LOW-008: Deprecated Config Fields Not Removed

**Location:** `aquilia/manifest.py`

**Description:** Deprecated manifest fields (`controllers`, `services`, `models` as plain lists) are auto-migrated with deprecation warnings but not yet removed.

**Recommendation:** Set a deprecation timeline and remove in the next major version.

---

## ✅ Security Strengths

| Area | Implementation | Assessment |
|------|---------------|------------|
| **Password Hashing** | Argon2id (64MB, 2 passes, 4 threads) + PBKDF2-SHA256 (600k iter) fallback | ✅ Industry best practice |
| **API Key Storage** | SHA-256 hash before storage | ✅ Proper |
| **Token Signing** | RSA-2048/ECDSA-P256/Ed25519 with key rotation | ✅ Excellent |
| **CSRF Protection** | Double-submit cookie with HMAC-SHA256 + timestamp + nonce | ✅ OWASP compliant |
| **Session Security** | Rotation on privilege change, fingerprinting, HTTPOnly+Secure+SameSite | ✅ Strong |
| **Rate Limiting** | Sliding window + token bucket, per-credential lockout | ✅ Good |
| **OAuth 2.0** | PKCE mandatory for public clients, authorization code expiry | ✅ Standards compliant |
| **MFA** | TOTP (RFC 6238) + WebAuthn + hashed backup codes | ✅ Excellent |
| **Authorization** | RBAC + ABAC + Clearance + Policy DSL, default-deny | ✅ Defense-in-depth |
| **SQL Injection** | Parameterized queries on all 4 backends, savepoint name validation | ✅ Safe |
| **XSS Prevention** | `html.escape()` in debug pages, XML tag sanitization in renderers | ✅ Good |
| **Security Headers** | Full OWASP set (CSP, HSTS, X-Frame-Options, COOP/COEP/CORP, etc.) | ✅ Comprehensive |
| **Timing Attacks** | `hmac.compare_digest()` / `secrets.compare_digest()` throughout | ✅ Proper |
| **Audit Logging** | OWASP-compliant, multi-store, immutable entries | ✅ Excellent |
| **Build Integrity** | SHA-256 content-addressed artifacts | ✅ Good (see HIGH-005) |
| **Fault Isolation** | Structured faults prevent exception leakage | ✅ Strong pattern |
| **Trusted Proxies** | CIDR-based proxy validation | ✅ Proper |
| **Directory Traversal** | Static file serving with path sanitization | ✅ Protected |
