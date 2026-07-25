# Migration Guide — Aquilia v1.3.4

Aquilia v1.3.4 is a **backwards-compatible** bug-fix and feature-expansion release. No existing APIs have been removed or broken. All manifests and configurations from 1.3.3 continue to work without modification.

This guide outlines recommended migrations to take advantage of new features, explicit API patterns, and security enhancements.

---

## Upgrading

Upgrade your environment using pip:

```bash
pip install aquilia==1.3.4
```

---

## Secret API Changes

The `Secret` class now enforces strict separation between literal values and environment variable lookups.

**1.3.3 Behavior:** 
`Secret("API_KEY")` ambiguously tried to look up the `API_KEY` environment variable because the string was all caps.

**1.3.4 Behavior:**
Positional arguments are strictly treated as literal values. If you want to pull a secret from the environment, you must use the `env` keyword argument.

**Migration Steps:**
If you see a `DeprecationWarning: ALL_CAPS positional argument treated as literal`, update your code:

```python
# Change this:
my_key = Secret("STRIPE_KEY")

# To this:
my_key = Secret(env="STRIPE_KEY")
```

---

## `imports` vs `depends_on`

The `depends_on` field in `AppManifest` is officially deprecated in favor of `imports`. 

**Migration Steps:**
Both fields work identically in 1.3.4 due to internal bidirectional synchronization. However, you should update your manifests to the v2 API pattern:

```python
# Change this:
manifest = AppManifest(name="app", depends_on=["other"])

# To this:
manifest = AppManifest(name="app", imports=["other"])
```
Use `aq validate --deprecated` to find all instances of `depends_on` in your codebase.

---

## AQUILIA_FAIL_FAST Environment Variable

By default, Aquilia catches startup exceptions to allow local development servers to boot and serve 500-error stubs. If you prefer your server to immediately crash and exit on a bad boot (highly recommended for CI/CD and Production), opt-in using the new environment variable.

**Migration Steps:**
No action is required to maintain 1.3.3 behavior. To enable fail-fast, add the following to your environment:

```bash
export AQUILIA_FAIL_FAST=1
```

---

## Authentication Provisioning (`issue_tokens`)

**Status:** Recommended Migration (Security Hardening)

If you are using `AuthManager.authenticate_password()` in a flow that only relies on session cookies and does not require JWTs, you should explicitly disable token generation. Previously, JWTs were minted unconditionally.

```python
# Before
identity = await auth_manager.authenticate_password(username, password)

# After (if you only need session auth)
identity = await auth_manager.authenticate_password(username, password, issue_tokens=False)
```

---

## Distributed Throttle Backend Migration

**Status:** Optional Migration

If your application runs across multiple workers or processes and you are using the legacy `Throttle` object, rate limits were previously tracked independently per worker in memory. You can upgrade to a distributed Redis backend with a single line change.

```python
# Before (Single-process memory only)
from aquilia.controller.throttle import Throttle
throttle = Throttle(limit=100, window=60)

# After (Distributed via Redis)
throttle = Throttle.with_redis(
    url="redis://localhost:6379/0",
    limit=100,
    window=60
)
```
Existing instances of `Throttle(limit, window)` will continue to operate exactly as they did before, using the memory tracker.

---

## Strict Discovery Mode

**Status:** Optional Migration

If your `AutoDiscoveryEngine` or Aquilia CLI fails to detect controllers or models because they are imported via aliases, re-exported through `__all__`, or rely on deep transitive inheritance across multiple files, switch to strict mode.

```bash
# In your terminal
aq discover --strict
```

Or programmatically:
```python
engine.discover(strict=True)
```
*Note: Strict mode physically imports your application modules. Ensure your module-level code is side-effect free.*

---

## Resource / ViewSet Adoption

**Status:** Optional Adoption

For standard CRUD endpoints, you can significantly reduce boilerplate by swapping plain `Controller` instances for `Resource` subclasses.

```python
# Before
class PostController(Controller):
    @route(["GET"], "/")
    async def list_posts(self, ctx): ...
    
    @route(["GET"], "/{id:int}")
    async def get_post(self, ctx, id: int): ...

# After
from aquilia.controller.resource import ReadOnlyResource

class PostResource(ReadOnlyResource):
    async def list(self, ctx): ...
    async def retrieve(self, ctx, id: int): ...
```
All existing Aquilia decorators and pipeline definitions apply seamlessly to `Resource` classes.
