# Native HTTP Client & Third-Party HTTP Removal — Aquilia v1.3.5

In Aquilia v1.3.5, all remaining traces of third-party HTTP clients (specifically `httpx`) have been completely removed from the framework codebase, dependencies, test suite, and documentation in favor of Aquilia's native zero-dependency `aquilia.http` client.

---

## 1. Overview & Motivation

Aquilia features a production-grade, fully asynchronous HTTP client implementation in `aquilia.http` built directly on Python standard library primitives (`asyncio`, `ssl`, `gzip`, `zlib`).

Previously, optional subsystems like `SendGridProvider` and test helpers like `LiveServerTestCase` relied on `httpx` as a third-party dependency. In v1.3.5:

1. **SendGrid Mail Provider** (`aquilia.mail.providers.sendgrid.SendGridProvider`) uses native `aquilia.http.AsyncHTTPClient`.
2. **`LiveServerTestCase`** (`aquilia.testing.cases.LiveServerTestCase`) documentation and usage examples use native `aquilia.http.AsyncHTTPClient`.
3. **Dependency Clean-Up**: `httpx` has been removed from `pyproject.toml`, `setup.py`, `aquilia.egg-info`, and all extra dependency bundles (`mail-sendgrid`, `testing`, `dev`).

---

## 2. Changes in SendGrid Provider

The `SendGridProvider` now initializes `AsyncHTTPClient` directly from `aquilia.http`:

```python
from aquilia.http import AsyncHTTPClient

class SendGridProvider:
    async def initialize(self) -> None:
        self._client = AsyncHTTPClient(
            base_url=self.api_base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "aquilia-mail/1.0",
            },
            timeout=self.timeout,
        )
```

Error handling consumes the async `HTTPClientResponse` API:

```python
body = await response.json()
```

---

## 3. Backward Compatibility & `aclose` Alias

To ensure smooth transition for any external callers expecting `aclose()`, `aquilia.http.AsyncHTTPClient` now provides an alias:

```python
class AsyncHTTPClient:
    async def close(self) -> None: ...

    aclose = close
```

Both `await client.close()` and `await client.aclose()` work seamlessly.

---

## 4. Dependencies Updated

- `mail-sendgrid` extra: no longer installs `httpx`.
- `testing` extra: no longer installs `httpx`.
- `dev` extra: no longer installs `httpx`.
