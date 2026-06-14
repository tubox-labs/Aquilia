# Troubleshooting Guide

This guide covers common errors in Aquilia applications, organized by subsystem. Every error uses the structured `Fault` system — each has a stable `code`, `domain`, `severity`, and descriptive `message`.

## Error page rendering

In development (`AQUILIA_ENV=dev`, `debug=True`), browser clients receive beautiful React-style debug pages with tracebacks and source context. JSON clients receive structured error objects. In production, internal details are never leaked.

---

## Route errors

### Route not found — `ROUTE_NOT_FOUND`

**Fault**: `RouteNotFoundFault`  
**Code**: `ROUTE_NOT_FOUND`  
**Domain**: `ROUTING`  
**Severity**: `ERROR` (public)  
**HTTP**: 404

**Cause**: The requested path and method combination does not match any registered route.

**Solution**:
1. Check the controller's `prefix` and route decorator path.
2. Verify the HTTP method matches (GET vs POST vs PUT etc.).
3. Run `aq inspect routes` to list all registered routes.
4. Check that the module's `route_prefix` in `workspace.py` is correct.

```python
# Common mistake — prefix mismatch
class UsersController(Controller):
    prefix = "/users"

    @GET("/")  # Matches GET /users/
    async def list(self, ctx): ...

# But requesting GET /api/users/ — which doesn't match
```

### Ambiguous routes — `ROUTE_AMBIGUOUS`

**Fault**: `RouteAmbiguousFault`  
**Code**: `ROUTE_AMBIGUOUS`  
**Domain**: `ROUTING`  
**Severity**: `WARN` (internal)

**Cause**: Multiple route patterns match the same request path.

**Solution**:
1. Use more specific path patterns (e.g., `/users/{id:int}` vs `/users/me` — order matters).
2. Refactor overlapping prefixes into separate controllers.
3. Use path parameter constraints (`{id:int}`, `{slug:str}`).

### Invalid route pattern — `PATTERN_INVALID`

**Fault**: `PatternInvalidFault`  
**Code**: `PATTERN_INVALID`  
**Domain**: `ROUTING`  
**Severity**: `FATAL`

**Cause**: A route pattern contains syntax errors or invalid parameter types.

**Solution**: Check the route decorator path for valid syntax. Parameter types must be `int`, `str`, `float`, `uuid`, or `path`.

---

## DI (Dependency Injection) errors

### Provider not found — `PROVIDER_NOT_FOUND`

**Fault**: `ProviderNotFoundFault`  
**Code**: `PROVIDER_NOT_FOUND`  
**Domain**: `DI`  
**Severity**: `ERROR`

**Cause**: A service or dependency requested via `Inject()` cannot be resolved from any registered provider.

**Solution**:
1. Verify the service is registered in the module's `manifest.py` → `services=[...]`.
2. Check that the provider class path is correct (`"module.path:ClassName"`).
3. Ensure cross-module dependencies use `exports` (exporting module) and `imports` (importing module).
4. Use `aq inspect di` to visualise the dependency graph.

```python
# manifest.py
manifest = AppManifest(
    name="users",
    version="0.1.0",
    services=[
        "modules.users.services:UsersService",
        "modules.users.repositories:UsersRepo",
    ],
    exports=["UsersService"],  # Make visible to other modules
)

# Other module's manifest.py
manifest = AppManifest(
    name="orders",
    imports=["users"],  # Import users module's exports
)
```

### Scope violation — `SCOPE_VIOLATION`

**Fault**: `ScopeViolationFault`  
**Code**: `SCOPE_VIOLATION`  
**Domain**: `DI`  
**Severity**: `ERROR`

**Cause**: A `request`-scoped service is injected into a `singleton` or `app`-scoped provider.

**Solution**:
1. Change the dependent service scope to `request` or `transient`.
2. Use a factory/provider pattern instead of direct constructor injection.
3. Access request-scoped data through `RequestCtx` rather than constructor injection.

### DI resolution failed — `DI_RESOLUTION_FAILED`

**Fault**: `DIResolutionFault`  
**Code**: `DI_RESOLUTION_FAILED`  
**Domain**: `DI`  
**Severity**: `ERROR`

**Cause**: A provider's factory or constructor raised an exception during instantiation.

**Solution**:
1. Check the service's `__init__` for errors.
2. Verify all injected dependencies are themselves resolvable.
3. Check for circular dependencies — use `aq inspect di` to identify cycles.

### Dependency cycle — `DEPENDENCY_CYCLE`

**Fault**: `DependencyCycleFault`  
**Code**: `DEPENDENCY_CYCLE`  
**Domain**: `REGISTRY`  
**Severity**: `FATAL`

**Cause**: Circular dependency detected in the module dependency graph (e.g., Module A depends on Module B, which depends on Module A).

**Solution**:
1. Extract shared interfaces into a third module (Dependency Inversion).
2. Use `exports`/`imports` instead of `depends_on` with lazy imports.
3. Redesign service boundaries to break the cycle.

---

## Session errors

### Session expired — `SessionExpiredFault`

**Fault**: `SessionExpiredFault`  
**Code**: (session-specific)  
**Domain**: `SECURITY`  
**Severity**: `WARN` (public)  
**HTTP**: 401

**Cause**: The session TTL or idle timeout has been exceeded.

**Solution**:
1. Adjust session TTL configuration:
```python
class sessions(AquilaConfig.Sessions):
    ttl_days = 30
    idle_timeout_minutes = 60
```
2. Implement token refresh for long-lived sessions.
3. Redirect users to re-authenticate.

### Session required — `SESSION_REQUIRED`

**Fault**: `SessionRequiredFault`  
**Code**: `SESSION_REQUIRED`  
**Domain**: `SECURITY`  
**Severity**: `ERROR` (public)  
**HTTP**: 401

**Cause**: A route decorated with `@authenticated` or `@session()` was accessed without a valid session.

**Solution**:
1. Ensure the auth middleware is in the middleware chain.
2. Check that sessions integration is enabled.
3. Verify the client is sending session cookies or auth headers.

---

## Authentication errors

### Authentication failed — `AUTHENTICATION_FAILED`

**Fault**: `AuthenticationFault`  
**Code**: `AUTHENTICATION_FAILED`  
**Domain**: `SECURITY`  
**Severity**: `ERROR` (public)  
**HTTP**: 401

**Cause**: Invalid credentials, expired token, or revoked token.

**Solution**:
1. Check username/password or token validity.
2. Verify the token's `exp` claim has not passed.
3. Check the `iss` and `aud` claims match configuration.
4. For API keys, verify the key has not been revoked or expired.

### Account locked — `AUTH_ACCOUNT_LOCKED`

**Fault**: `AUTH_ACCOUNT_LOCKED`  
**Code**: `AUTH_ACCOUNT_LOCKED`  
**Domain**: `SECURITY`  
**Severity**: `ERROR` (public)  
**HTTP**: 429

**Cause**: Too many failed login attempts (default: 5 in 15 minutes).

**Solution**:
1. Wait for the lockout duration (default: 1 hour).
2. Reset attempts via the admin dashboard.
3. Configure rate limiter parameters:
```python
limiter = RateLimiter(
    max_attempts=5,
    window_seconds=900,
    lockout_duration=3600,
)
```

### Account suspended — `AUTH_ACCOUNT_SUSPENDED`

**Fault**: `AUTH_ACCOUNT_SUSPENDED`  
**Code**: `AUTH_ACCOUNT_SUSPENDED`  
**Domain**: `SECURITY`

**Cause**: The identity's status is `SUSPENDED`.

**Solution**: Change the identity status to `ACTIVE` via the identity store.

---

## Database errors

### Connection failed — `DB_CONNECTION_FAILED`

**Fault**: `DatabaseConnectionFault`  
**Code**: `DB_CONNECTION_FAILED`  
**Domain**: `MODEL`  
**Severity**: `FATAL` (retryable)

**Cause**: The database is unreachable or the connection URL is incorrect.

**Solution**:
1. Verify the database server is running.
2. Check the connection URL in `DatabaseIntegration` or `AquilaConfig.Database`.
3. Verify network connectivity (firewall, port) between app and database.
4. Check credentials.

```python
# Check database config
workspace.database(
    url="postgresql://user:pass@localhost:5432/mydb",
    auto_connect=True,
)
```

### Query failed — `QUERY_FAILED`

**Fault**: `QueryFault`  
**Code**: `QUERY_FAILED`  
**Domain**: `MODEL`  
**Severity**: `ERROR` (retryable)

**Cause**: Invalid query, constraint violation, or schema mismatch.

**Solution**:
1. Check the SQL or ORM query for errors.
2. Run `aq db sqlmigrate` to inspect pending migration SQL.
3. Run `aq db migrate` to apply pending migrations.
4. Check for unique constraint violations or foreign key errors.

### Model not found — `MODEL_NOT_FOUND`

**Fault**: `ModelNotFoundFault`  
**Code**: `MODEL_NOT_FOUND`  
**Domain**: `MODEL`  
**Severity**: `ERROR`

**Cause**: A model referenced in code has not been registered in the `ModelRegistry`.

**Solution**:
1. Register the model in the module's `manifest.py`:
```python
manifest = AppManifest(
    name="users",
    models=["modules.users.models:User", "modules.users.models:Profile"],
)
```
2. Ensure the model file is in the scan directory (`models/` by default).
3. Check that `auto_discover=True` can find the model file.

---

## Cache errors

### Cache connection error — `CacheConnectionFault`

**Fault**: `CacheConnectionFault`  
**Code**: (cache-specific)  
**Domain**: `CACHE`

**Cause**: Cannot connect to the cache backend (e.g., Redis is down).

**Solution**:
1. Verify Redis is running: `redis-cli ping`.
2. Check the `redis_url` in `CacheIntegration`.
3. Switch to `memory` backend for development.
4. Check `redis_max_connections` if pool exhausted.

### Cache miss — `CacheMissFault`

**Fault**: `CacheMissFault`  
**Domain**: `CACHE`  
**Severity**: `WARN`

**Cause**: Requested cache key not found (not an error, diagnostic only).

### Cache stampede — `CacheStampedeFault`

**Fault**: `CacheStampedeFault`  
**Domain**: `CACHE`

**Cause**: Many concurrent requests for an expired cache key, overwhelming the backend.

**Solution**:
1. Use the `CompositeCache` with L1 (memory) + L2 (Redis) configuration.
2. Implement probabilistic early recomputation.
3. Use `cache_aside` decorator with locking.

### Cache capacity exceeded — `CacheCapacityFault`

**Fault**: `CacheCapacityFault`  
**Domain**: `CACHE`

**Cause**: Memory cache has reached `max_size`.

**Solution**:
1. Increase `max_size` in `CacheIntegration`.
2. Use a more aggressive eviction policy (`lfu` instead of `lru`).
3. Switch to Redis backend for larger capacity.

---

## Storage errors

### Storage error — `StorageError`

**Fault**: `StorageError`  
**Code**: (storage-specific)  
**Domain**: `STORAGE`

**Cause**: File read/write/delete operation failed on a storage backend.

**Solution**:
1. Check backend connectivity (S3, GCS, SFTP, local filesystem).
2. Verify permissions on the storage path/bucket.
3. Check that the backend alias in `StorageIntegration.backends` matches usage.
4. For S3, verify IAM permissions and bucket policy.

---

## Configuration errors

### Config missing — `CONFIG_MISSING`

**Fault**: `ConfigMissingFault`  
**Code**: `CONFIG_MISSING`  
**Domain**: `CONFIG`  
**Severity**: `FATAL`

**Cause**: Required configuration key is not set.

**Solution**:
1. Set the environment variable referenced by `Env()` or `Secret()`.
2. Provide a `default` value in the `Env()` or `Secret()` binding.
3. Verify `.env` file is in the correct location.

### Config invalid — `CONFIG_INVALID`

**Fault**: `ConfigInvalidFault`  
**Code**: `CONFIG_INVALID`  
**Domain**: `CONFIG`  
**Severity**: `FATAL`

**Cause**: A configuration value fails validation.

**Solution**:
1. Check the value type (e.g., `port` must be an integer).
2. For `cast=int` or `cast=bool` bindings, ensure the env var value is parseable.
3. Check that algorithm names are valid (`HS256`, not `HS-256`).

### Dotenv parse error — `DOTENV_PARSE_ERROR`

**Fault**: `DotenvParseFault`  
**Code**: `DOTENV_PARSE_ERROR`  
**Domain**: `CONFIG`  
**Severity**: `ERROR`

**Cause**: Syntax error in a `.env` file.

**Solution**: Fix the syntax on the reported line number. Valid syntax is `KEY=value`, `KEY="value"`, or `KEY='value'`.

---

## Security errors

### CSRF validation failed — `CSRF_VIOLATION`

**Fault**: `CSRFViolationFault`  
**Code**: `CSRF_VIOLATION`  
**Domain**: `SECURITY`  
**Severity**: `WARN` (public)  
**HTTP**: 403

**Cause**: CSRF token is missing, expired, or does not match.

**Solution**:
1. Ensure forms include the CSRF token (`{% csrf_token %}` or `_csrf_token` field).
2. Include the `X-CSRF-Token` header in AJAX requests.
3. Add webhook endpoints to `exempt_paths` if they use external POST:
```python
CsrfIntegration(exempt_paths=["/api/webhooks/stripe"])
```

### CORS violation — `CORS_VIOLATION`

**Fault**: `CORSViolationFault`  
**Code**: `CORS_VIOLATION`  
**Domain**: `SECURITY`  
**Severity**: `WARN` (public)

**Cause**: Origin not in the allowed CORS origins list.

**Solution**:
1. Add the origin to `CorsIntegration.allow_origins`.
2. Set `allow_origins=["*"]` for public APIs.
3. Check that `allow_credentials` is `True` if the client sends cookies.

### Rate limit exceeded — `RATE_LIMIT_EXCEEDED`

**Fault**: `RateLimitExceededFault`  
**Code**: `RATE_LIMIT_EXCEEDED`  
**Domain**: `SECURITY`  
**Severity**: `WARN` (public)  
**HTTP**: 429

**Cause**: Client exceeded the configured rate limit.

**Solution**:
1. Wait for the `Retry-After` period.
2. Increase limits in `RateLimitIntegration`.
3. Add the path to `exempt_paths` if it's a health check.

---

## Manifest errors

### Manifest validation failed — `MANIFEST_INVALID`

**Fault**: `ManifestInvalidFault`  
**Code**: `MANIFEST_INVALID`  
**Domain**: `REGISTRY`  
**Severity**: `FATAL`

**Cause**: Module manifest (`manifest.py`) has validation errors.

**Solution**:
1. Ensure `name` is set and is alphanumeric with underscores.
2. Ensure `version` is set (semantic version string).
3. Check that class paths use the correct `"module.path:ClassName"` format.

### Controller not found

**Fault**: `RegistryError`  
**Domain**: `REGISTRY`

**Cause**: A controller referenced in `manifest.py` cannot be imported.

**Solution**:
1. Verify the dotted path is correct.
2. Check that the class exists in the specified module.
3. Ensure the module is installed/accessible in the Python path.

---

## Mail errors

### Mail send failed — `MailSendFault`

**Fault**: `MailSendFault`  
**Domain**: (mail-specific)

**Cause**: The mail provider returned an error or is unreachable.

**Solution**:
1. Verify SMTP host and port in `SmtpProvider`.
2. Check mail authentication credentials.
3. Enable `console_backend=True` for development.
4. Check `require_tls` and `use_tls`/`use_ssl` settings.

---

## General debugging tips

1. **Run `aq validate`** to check workspace and manifest integrity.
2. **Run `aq inspect routes`** to verify all routes are registered.
3. **Run `aq inspect di`** to check dependency injection wiring.
4. **Run `aq inspect manifest`** to see effective configuration.
5. **Enable debug mode** (`AQUILIA_ENV=dev`, `debug=True`) for verbose error pages.
6. **Check logs** — the `aquilia.exceptions`, `aquilia.requests`, and `aquilia.health` loggers capture detailed diagnostics.
7. **Use `TestClient`** to isolate and reproduce issues in unit tests:

```python
from aquilia.testing import TestClient

client = TestClient(app)
response = await client.get("/api/users/")
assert response.status == 200
```