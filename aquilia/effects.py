"""
Aquilia Effect System -- Explicit, Typed Capability Injection with Scoped Lifecycles.

Philosophy & Architecture
=========================
The Effect System provides structured, type-safe resource injection for Aquilia
applications. Inspired by functional effect systems (specifically Effect-TS), it
separates *what* resource a handler requires from *how* that resource is constructed,
accessed, and cleaned up. This pattern decouples handlers from infrastructure,
ensuring clean boundaries, testability, and robust resource safety.

An "Effect" acts as a typed token representing a dependency (e.g. database transaction,
cache namespace, message queue, HTTP client, or blob storage bucket). Instead of
instantiating clients directly or pulling them from global state, handlers declare
their required effects using the ``@requires`` decorator. The Aquilia runtime
automatically manages the lifecycle (acquisition, verification, and releasing/committing)
of these resources around handler invocation.

Core Components
===============
1.  **Effect** (Token):
    A symbolic description of a capability, parameterized by a kind and an optional
    mode (e.g., ``DBTx["read"]`` vs. ``DBTx["write"]``).
2.  **EffectKind**:
    Categorizes effects into standard types: ``DB``, ``CACHE``, ``QUEUE``, ``HTTP``,
    ``STORAGE``, and ``CUSTOM``.
3.  **EffectProvider**:
    The abstract base class representing the implementation backend for an effect.
    It manages the lifecycle of actual resources through a set of lifecycle methods:
    *   ``initialize()``: One-time setup during application bootstrap.
    *   ``acquire(mode)``: Setup executed per-request or per-scope to create a handle.
    *   ``release(resource, success)``: Teardown executed per-request, handling commits,
        rollbacks, or connection cleanup.
    *   ``finalize()``: One-time shutdown cleanup when the server stops.
    *   ``health_check()``: Aggregates capability health statistics.
4.  **EffectRegistry**:
    A centralized registry storing mapping of effect name to provider. It integrates
    with the Dependency Injection (DI) system as an application-scoped singleton.
5.  **Resource Handles**:
    Lightweight, specialized classes that act as the interface through which handlers
    interact with the underlying capability. For example, ``DBTxHandle``, ``CacheHandle``,
    ``QueueHandle``, ``HTTPHandle``, and ``StorageHandle``.

Example Usage
=============

Declaring and Using Effects in a Controller or Handler:
-------------------------------------------------------
.. code-block:: python

    from aquilia.flow import FlowContext, requires
    from aquilia.controller import Controller, route

    class UserController(Controller):
        @route("/users", methods=["POST"])
        @requires("DBTx", "Cache")
        async def create_user(self, ctx: FlowContext, payload: dict) -> dict:
            # 1. Access the database transaction effect handle
            db = ctx.get_effect("DBTx")  # Returns a DBTxHandle

            # 2. Access the cache namespace handle
            cache = ctx.get_effect("Cache")  # Returns a CacheServiceHandle or CacheHandle

            # 3. Perform database operations safely inside the transaction
            user_id = await db.fetch_val(
                "INSERT INTO users (username) VALUES ($1) RETURNING id",
                (payload["username"],)
            )

            # 4. Perform cache write operations
            await cache.set(f"user:{user_id}", payload, ttl=300)

            return {"id": user_id, "status": "created"}

Defining a Custom Effect and Provider:
--------------------------------------
To extend the effect system with custom capability interfaces, subclass both
``Effect`` and ``EffectProvider``:

.. code-block:: python

    from typing import Any
    from aquilia.effects import Effect, EffectProvider, EffectKind

    # 1. Define the custom effect token
    class EmailEffect(Effect[str]):
        def __init__(self, provider_type: str = "smtp"):
            super().__init__("Email", mode=provider_type, kind=EffectKind.CUSTOM)

    # 2. Define the resource handle that the handler will interact with
    class EmailHandle:
        def __init__(self, provider: Any):
            self.provider = provider

        async def send(self, recipient: str, subject: str, body: str) -> None:
            await self.provider.send_email(recipient, subject, body)

    # 3. Implement the lifecycle provider
    class EmailProvider(EffectProvider):
        def __init__(self, smtp_host: str, port: int):
            self.smtp_host = smtp_host
            self.port = port
            self.client = None

        async def initialize(self) -> None:
            # Connect to SMTP server pool on startup
            self.client = SMTPClientPool(self.smtp_host, self.port)
            await self.client.connect()

        async def acquire(self, mode: str | None = None) -> EmailHandle:
            # Acquire a session connection from the pool
            session = await self.client.acquire_session()
            return EmailHandle(session)

        async def release(self, resource: EmailHandle, success: bool = True) -> None:
            # Release the session back to the pool
            await self.client.release_session(resource.provider)

        async def finalize(self) -> None:
            # Disconnect pool on shutdown
            await self.client.close()

        async def health_check(self) -> dict[str, Any]:
            return {"healthy": self.client.is_connected()}

Registering the Custom Provider with the Application:
-----------------------------------------------------
Register the provider in your application config, or manually via the registry:

.. code-block:: python

    # Manual registration (e.g., during startup/testing)
    registry = EffectRegistry()
    registry.register("Email", EmailProvider(smtp_host="localhost", port=1025))
"""

from __future__ import annotations

import contextlib
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

if TYPE_CHECKING:
    from .db.engine import AquiliaDatabase
    from .sqlite._cursor import AsyncCursor
else:
    AsyncCursor = Any
    AquiliaDatabase = Any

from .typing.effects import EffectMap, EffectName

T = TypeVar("T")

logger = logging.getLogger("aquilia.effects")


# ---------------------------------------------------------------------------
# DBTxHandle — typed alias for the dict returned by DBTxProvider.acquire()
# ---------------------------------------------------------------------------


class DBTxHandle(dict):
    """
    Typed handle representing an acquired database transaction resource.

    Subclasses ``dict`` so existing code that inspects ``resource["connection"]``
    or ``resource["mode"]`` continues to work, while type checkers now infer
    ``DBTxHandle`` instead of ``Any`` for ``ctx.get_effect("DBTx")``.

    Exposes async query methods: ``execute()``, ``execute_many()``,
    ``fetch_all()``, ``fetch_one()``, and ``fetch_val()`` that run queries
    within the active transaction scope.
    """

    def __init__(self, data: dict, db: Any | None = None) -> None:
        """
        Initialize the database transaction handle.

        Args:
            data: Raw dictionary backing containing connection metadata.
            db: Optional associated database connection or engine instance.
        """
        super().__init__(data)
        self._db = db

    def _get_db(self) -> AquiliaDatabase:
        """
        Retrieve the active database instance.

        Returns:
            The AquiliaDatabase instance.
        """
        if self._db is not None:
            return self._db
        from .db.engine import get_database

        return get_database()

    async def execute(self, sql: str, params: Sequence[Any] | None = None) -> AsyncCursor:
        """
        Execute a SQL query statement within the transaction context.

        Args:
            sql: The SQL query statement to run.
            params: Parameters to bind to the statement.

        Returns:
            An AsyncCursor object pointing to the executed query result.
        """
        return await self._get_db().execute(sql, params)

    async def execute_many(self, sql: str, params_list: Sequence[Sequence[Any]] | None = None) -> None:
        """
        Execute a SQL query statement multiple times with different parameter lists.

        Args:
            sql: The SQL query statement to run.
            params_list: A sequence of parameter sets to execute the query with.
        """
        await self._get_db().execute_many(sql, params_list)

    async def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        """
        Fetch all rows returned by a query within the transaction.

        Args:
            sql: The SELECT SQL statement to run.
            params: Parameters to bind to the statement.

        Returns:
            A list of dictionary objects representing database rows.
        """
        return await self._get_db().fetch_all(sql, params)

    async def fetch_one(self, sql: str, params: Sequence[Any] | None = None) -> dict[str, Any] | None:
        """
        Fetch a single row returned by a query within the transaction.

        Args:
            sql: The SELECT SQL statement to run.
            params: Parameters to bind to the statement.

        Returns:
            A dictionary representing the row, or None if no row is returned.
        """
        return await self._get_db().fetch_one(sql, params)

    async def fetch_val(self, sql: str, params: Sequence[Any] | None = None) -> Any:
        """
        Fetch a single scalar value from the first row and column of the query results.

        Args:
            sql: The SELECT SQL statement to run.
            params: Parameters to bind to the statement.

        Returns:
            The scalar value returned, or None.
        """
        return await self._get_db().fetch_val(sql, params)

    @property
    def connection(self) -> Any:
        """
        Get the underlying database connection or pool handle.

        Returns:
            The active connection/pool instance.
        """
        return self.get("connection")

    @property
    def mode(self) -> str:
        """
        Get the transaction mode ("read" or "write").

        Returns:
            The transaction mode string.
        """
        return str(self.get("mode", "read"))

    @property
    def transaction(self) -> Any:
        """
        Get the active transaction object context.

        Returns:
            The transaction context manager/object, or None if not started.
        """
        return self.get("transaction")

    @property
    def acquired_at(self) -> float:
        """
        Get the monotonic timestamp at which this handle was acquired.

        Returns:
            Monotonic timestamp float.
        """
        return float(self.get("acquired_at", 0.0))

    def __repr__(self) -> str:
        return f"DBTxHandle(mode={self.mode!r}, connection={self.connection!r})"


class EffectKind(Enum):
    """Categories of effects."""

    DB = "db"
    CACHE = "cache"
    QUEUE = "queue"
    HTTP = "http"
    STORAGE = "storage"
    CUSTOM = "custom"


class Effect(Generic[T]):
    """
    Effect token representing a capability.

    Example:
        DBTx['read']  - Read-only database transaction
        DBTx['write'] - Read-write database transaction
        Cache['user'] - User cache namespace
    """

    def __init__(self, name: str, mode: T | None = None, kind: EffectKind = EffectKind.CUSTOM):
        self.name: EffectName = EffectName(name)
        self.mode = mode
        self.kind = kind

    def __class_getitem__(cls, mode):
        """Support DBTx['read'] syntax."""
        instance = cls.__new__(cls)
        instance.mode = mode
        return instance

    def __repr__(self):
        if self.mode:
            return f"Effect({self.name}[{self.mode}])"
        return f"Effect({self.name})"


class EffectProvider(ABC):
    """
    Base class for effect providers.

    Providers implement the actual capability (e.g., database connection).
    Lifecycle:
        1. initialize()  -- called once at startup
        2. acquire(mode)  -- called per-request to get a resource
        3. release(resource, success) -- called at end of request
        4. finalize()    -- called once at shutdown
    """

    @abstractmethod
    async def initialize(self):
        """Initialize the provider (called once at startup)."""
        pass

    @abstractmethod
    async def acquire(self, mode: str | None = None) -> Any:
        """
        Acquire a resource for this effect (called per-request).

        Args:
            mode: Optional mode specifier (e.g., 'read', 'write')

        Returns:
            Resource handle
        """
        pass

    @abstractmethod
    async def release(self, resource: Any, success: bool = True):
        """
        Release the resource (called at end of request).

        Args:
            resource: Resource handle from acquire()
            success: Whether request completed successfully
        """
        pass

    async def finalize(self):
        """Finalize provider (called at shutdown)."""
        pass

    async def health_check(self) -> dict[str, Any]:
        """
        Check provider health. Override for custom health reporting.

        Returns:
            Dict with 'healthy' bool and optional metadata.
        """
        return {"healthy": True}


class DBTx(Effect):
    """Database transaction effect."""

    def __init__(self, mode: str = "read"):
        super().__init__("DBTx", mode=mode, kind=EffectKind.DB)


class CacheEffect(Effect):
    """Cache effect."""

    def __init__(self, namespace: str = "default"):
        super().__init__("Cache", mode=namespace, kind=EffectKind.CACHE)


class QueueEffect(Effect):
    """Queue/message publish effect."""

    def __init__(self, topic: str | None = None):
        super().__init__("Queue", mode=topic, kind=EffectKind.QUEUE)


class HTTPEffect(Effect):
    """HTTP client effect for outbound requests."""

    def __init__(self, service: str | None = None):
        super().__init__("HTTP", mode=service, kind=EffectKind.HTTP)


class StorageEffect(Effect):
    """File/blob storage effect."""

    def __init__(self, bucket: str | None = None):
        super().__init__("Storage", mode=bucket, kind=EffectKind.STORAGE)


# ============================================================================
# Providers
# ============================================================================


class DBTxProvider(EffectProvider):
    """Database transaction provider backed by AquiliaDatabase."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db: Any = None
        self._acquire_count = 0
        self._release_count = 0

    async def initialize(self):
        """Initialize database connection."""
        from .db.engine import AquiliaDatabase

        self.db = AquiliaDatabase(self.connection_string)
        await self.db.connect()

    async def acquire(self, mode: str | None = None) -> DBTxHandle:
        """Acquire database connection and start transaction."""
        self._acquire_count += 1
        if self.db is None:
            from .db.engine import get_database

            try:
                self.db = get_database()
            except Exception as exc:
                from .faults.domains import DatabaseConnectionFault

                raise DatabaseConnectionFault(
                    backend="dbtx_effect",
                    reason=f"Database connection not initialized in DBTxProvider: {exc}",
                )

        readonly = mode == "read"
        from .models.transactions import Atomic

        txn = Atomic(db=self.db, readonly=readonly)
        await txn.__aenter__()

        return DBTxHandle(
            {
                "connection": self.db,
                "mode": mode or "read",
                "transaction": txn,
                "acquired_at": time.monotonic(),
            },
            db=self.db,
        )

    async def release(self, resource: DBTxHandle, success: bool = True) -> None:
        """Release database connection and commit/rollback transaction."""
        self._release_count += 1
        if isinstance(resource, dict) and "transaction" in resource:
            txn = resource["transaction"]
            if txn is not None:
                if success:
                    await txn.__aexit__(None, None, None)
                else:
                    await txn.__aexit__(Exception, Exception("Effect release rollback"), None)

    async def finalize(self):
        """Disconnect database pool."""
        if self.db is not None:
            await self.db.disconnect()

    async def health_check(self) -> dict[str, Any]:
        healthy = self.db is not None and self.db.is_connected()
        return {
            "healthy": healthy,
            "acquire_count": self._acquire_count,
            "release_count": self._release_count,
        }


class CacheProvider(EffectProvider):
    """
    Cache effect provider backed by the real CacheService.

    If a :class:`~aquilia.cache.service.CacheService` is provided it is used
    for all acquire/release operations; otherwise falls back to a simple
    in-memory dict (useful in tests or when the cache subsystem is disabled).
    """

    def __init__(self, backend: str = "memory", *, cache_service: Any = None):
        self.backend = backend
        self._svc = cache_service  # Optional CacheService
        self._fallback: dict = {}

    async def initialize(self):
        """Initialize cache backend."""
        if self._svc is not None:
            try:
                await self._svc.initialize()
            except Exception:
                pass  # CacheService.initialize is idempotent

    async def acquire(self, mode: str | None = None) -> CacheServiceHandle | CacheHandle:
        """Get cache handle for namespace."""
        namespace = mode or "default"
        if self._svc is not None:
            return CacheServiceHandle(self._svc, namespace)
        return CacheHandle(self._fallback, namespace)

    async def release(self, resource: CacheServiceHandle | CacheHandle, success: bool = True) -> None:
        """Nothing to release for cache."""
        pass

    async def finalize(self):
        """Shutdown underlying cache service."""
        if self._svc is not None:
            with contextlib.suppress(Exception):
                await self._svc.shutdown()

    async def health_check(self) -> dict[str, Any]:
        return {
            "healthy": True,
            "backend": self.backend,
            "has_service": self._svc is not None,
        }


class QueueProvider(EffectProvider):
    """
    Queue/message publish effect provider.

    Wraps a message broker connection (RabbitMQ, Redis Streams, etc.).
    """

    def __init__(self, broker_url: str | None = None):
        self.broker_url = broker_url
        self._connected = False
        self._messages: list[dict[str, Any]] = []  # In-memory fallback

    async def initialize(self):
        self._connected = True

    async def acquire(self, mode: str | None = None) -> QueueHandle:
        """Return a queue handle for a topic/channel."""
        topic = mode or "default"
        return QueueHandle(self._messages, topic)

    async def release(self, resource: QueueHandle, success: bool = True) -> None:
        pass

    async def finalize(self):
        self._connected = False

    async def health_check(self) -> dict[str, Any]:
        return {"healthy": self._connected, "broker_url": self.broker_url}


class TaskQueueProvider(EffectProvider):
    """
    Task queue effect provider backed by AquilaTasks TaskManager.

    Bridges the effect system with the background task subsystem,
    allowing controllers/services to enqueue tasks via ``@requires(Queue)``.

    When a TaskManager is available, ``acquire()`` returns a
    ``TaskQueueHandle`` that wraps ``manager.enqueue()``. Otherwise
    falls back to the in-memory message list.
    """

    def __init__(self, *, task_manager: Any = None):
        self._manager = task_manager
        self._fallback_messages: list[dict[str, Any]] = []

    async def initialize(self):
        pass  # Manager lifecycle is managed by the server

    async def acquire(self, mode: str | None = None) -> TaskQueueHandle | QueueHandle:
        queue = mode or "default"
        if self._manager is not None:
            return TaskQueueHandle(self._manager, queue)
        return QueueHandle(self._fallback_messages, queue)

    async def release(self, resource: TaskQueueHandle | QueueHandle, success: bool = True) -> None:
        pass

    async def finalize(self):
        pass

    async def health_check(self) -> dict[str, Any]:
        if self._manager is not None:
            return {
                "healthy": self._manager.is_running,
                "backend": self._manager.backend.__class__.__name__,
                "workers": self._manager.num_workers,
            }
        return {"healthy": True, "backend": "fallback"}


class HTTPProvider(EffectProvider):
    """
    HTTP client effect provider backed by Aquilia's native AsyncHTTPClient.
    """

    def __init__(self, base_url: str | None = None, *, timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
        self.client: Any = None

    async def initialize(self):
        """Create AsyncHTTPClient session."""
        from .http.client import AsyncHTTPClient
        from .http.config import HTTPClientConfig, TimeoutConfig

        config = HTTPClientConfig(timeout=TimeoutConfig(total=self.timeout))
        self.client = AsyncHTTPClient(base_url=self.base_url, config=config)

    async def acquire(self, mode: str | None = None) -> HTTPHandle:
        """Return HTTP client handle."""
        if self.client is None:
            from .http.client import AsyncHTTPClient

            self.client = AsyncHTTPClient(base_url=self.base_url)
        return HTTPHandle(self.client, self.base_url)

    async def release(self, resource: HTTPHandle, success: bool = True) -> None:
        pass

    async def finalize(self):
        if self.client is not None:
            await self.client.close()


class StorageProvider(EffectProvider):
    """
    File/blob storage effect provider.

    Wraps local filesystem or cloud storage (S3, GCS, etc.).
    """

    def __init__(self, root_path: str = "./storage", *, storage_registry: Any = None) -> None:
        self.root_path = root_path
        self._registry = storage_registry

    async def initialize(self) -> None:
        import os

        os.makedirs(self.root_path, exist_ok=True)

    async def acquire(self, mode: str | None = None) -> StorageHandle:
        bucket = mode or "default"
        return StorageHandle(self.root_path, bucket, registry=self._registry)

    async def release(self, resource: StorageHandle, success: bool = True) -> None:
        pass

    async def health_check(self) -> dict[str, Any]:
        import os

        healthy = os.path.isdir(self.root_path)
        if self._registry is not None:
            try:
                # check registry health
                healthy = all((await self._registry.health_check()).values())
            except Exception:
                healthy = False
        return {"healthy": healthy, "root": self.root_path}


# ============================================================================
# Resource Handles
# ============================================================================


class CacheServiceHandle:
    """Handle wrapping real CacheService for a given namespace."""

    __slots__ = ("_svc", "_ns")

    def __init__(self, svc: Any, namespace: str):
        """
        Initialize the cache service handle.

        Args:
            svc: The underlying CacheService instance.
            namespace: The specific namespace to scope operations.
        """
        self._svc = svc
        self._ns = namespace

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the cache namespace.

        Args:
            key: The cache key string.

        Returns:
            The cached value, or None if the key does not exist.
        """
        return await self._svc.get(key, namespace=self._ns)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set a value in the cache namespace with an optional time-to-live.

        Args:
            key: The cache key string.
            value: The data/value to store.
            ttl: Optional time-to-live in seconds.
        """
        await self._svc.set(key, value, ttl=ttl, namespace=self._ns)

    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache namespace.

        Args:
            key: The cache key string to delete.

        Returns:
            True if the deletion succeeded, False otherwise.
        """
        return await self._svc.delete(key, namespace=self._ns)


class CacheHandle:
    """Handle for cache operations in a namespace (in-memory dict fallback)."""

    def __init__(self, cache: dict, namespace: str):
        """
        Initialize the fallback in-memory cache handle.

        Args:
            cache: The dictionary acting as the in-memory cache store.
            namespace: The namespace to isolate keys.
        """
        self._cache = cache
        self._namespace = namespace

    def _key(self, key: str) -> str:
        """
        Construct a namespace-prefixed cache key.

        Args:
            key: Raw cache key.

        Returns:
            Namespaced cache key.
        """
        return f"{self._namespace}:{key}"

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from the in-memory cache.

        Args:
            key: The cache key string.

        Returns:
            The cached value, or None if not found.
        """
        return self._cache.get(self._key(key))

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set a value in the in-memory cache.

        Args:
            key: The cache key string.
            value: The data/value to store.
            ttl: Ignored for the in-memory fallback.
        """
        self._cache[self._key(key)] = value

    async def delete(self, key: str) -> bool:
        """
        Delete a value from the in-memory cache.

        Args:
            key: The cache key string to delete.

        Returns:
            True if the key was deleted, False otherwise.
        """
        return bool(self._cache.pop(self._key(key), None) is not None)


class QueueHandle:
    """Handle for queue operations on a topic."""

    def __init__(self, messages: list[dict[str, Any]], topic: str):
        """
        Initialize the queue handle.

        Args:
            messages: Underlyling message list backing the queue.
            topic: The message queue topic or channel name.
        """
        self._messages = messages
        self._topic = topic

    async def publish(self, payload: Any, *, headers: dict[str, str] | None = None) -> None:
        """
        Publish a single message payload to the configured topic.

        Args:
            payload: The message body to publish.
            headers: Optional dictionary of metadata headers.
        """
        self._messages.append(
            {
                "topic": self._topic,
                "payload": payload,
                "headers": headers or {},
                "timestamp": time.monotonic(),
            }
        )

    async def publish_batch(self, payloads: Sequence[Any]) -> None:
        """
        Publish a sequence of message payloads to the configured topic.

        Args:
            payloads: A sequence of message bodies to publish.
        """
        for payload in payloads:
            await self.publish(payload)


class TaskQueueHandle:
    """Handle for enqueuing background tasks via the TaskManager."""

    def __init__(self, manager: Any, queue: str):
        """
        Initialize the task queue handle.

        Args:
            manager: The underlying TaskManager instance.
            queue: The name of the target queue to submit tasks.
        """
        self._manager = manager
        self._queue = queue

    async def enqueue(self, func: Any, *args: Any, **kwargs: Any) -> str:
        """
        Enqueue a callable task for background execution.

        Args:
            func: The asynchronous callable or `@task`-decorated function.
            *args: Positional arguments to forward to the task function.
            **kwargs: Keyword arguments to forward to the task function.

        Returns:
            The job ID string for the enqueued task.
        """
        job_id = await self._manager.enqueue(func, *args, queue=self._queue, **kwargs)
        return cast(str, job_id)

    async def publish(self, payload: Any, *, headers: dict[str, str] | None = None) -> None:
        """
        Compatibility method to enqueue payload. Currently a no-op.

        Args:
            payload: Message payload.
            headers: Message headers.
        """
        # For generic publish, store as a no-op message
        # Real usage should call enqueue() with a @task function
        pass

    async def publish_batch(self, payloads: Sequence[Any]) -> None:
        """
        Compatibility method to enqueue multiple payloads. Currently a no-op.

        Args:
            payloads: Sequence of payloads.
        """
        pass


class HTTPHandle:
    """Handle for outbound HTTP requests wrapping AsyncHTTPClient."""

    def __init__(self, client: Any, base_url: str | None = None):
        """
        Initialize the HTTP effect handle.

        Args:
            client: The AsyncHTTPClient instance.
            base_url: Optional base URL prefix for requests.
        """
        self._client = client
        self._session = client  # backward compatibility
        self._base_url = base_url

    async def get(self, url: str, **kwargs) -> Any:
        """
        Perform an HTTP GET request.

        Args:
            url: Target URL path or absolute URL.
            **kwargs: Additional parameters forwarded to client.get().

        Returns:
            JSON decoded response, or None if client is not initialized.
        """
        if self._client:
            resp = await self._client.get(url, **kwargs)
            return await resp.json()
        return None

    async def post(self, url: str, *, json: Any = None, **kwargs) -> Any:
        """
        Perform an HTTP POST request.

        Args:
            url: Target URL path or absolute URL.
            json: JSON serializable object to send in body.
            **kwargs: Additional parameters forwarded to client.post().

        Returns:
            JSON decoded response, or None if client is not initialized.
        """
        if self._client:
            resp = await self._client.post(url, json=json, **kwargs)
            return await resp.json()
        return None

    async def put(self, url: str, *, json: Any = None, **kwargs) -> Any:
        """
        Perform an HTTP PUT request.

        Args:
            url: Target URL path or absolute URL.
            json: JSON serializable object to send in body.
            **kwargs: Additional parameters forwarded to client.put().

        Returns:
            JSON decoded response, or None if client is not initialized.
        """
        if self._client:
            resp = await self._client.put(url, json=json, **kwargs)
            return await resp.json()
        return None

    async def delete(self, url: str, **kwargs) -> Any:
        """
        Perform an HTTP DELETE request.

        Args:
            url: Target URL path or absolute URL.
            **kwargs: Additional parameters forwarded to client.delete().

        Returns:
            JSON decoded response, or None if client is not initialized.
        """
        if self._client:
            resp = await self._client.delete(url, **kwargs)
            return await resp.json()
        return None


class StorageHandle:
    """Handle for file/blob storage operations."""

    def __init__(self, root_path: str, bucket: str, registry: Any | None = None) -> None:
        """
        Initialize the storage handle.

        Args:
            root_path: Root filesystem path directory fallback.
            bucket: The scoped storage bucket name.
            registry: Optional StorageRegistry to resolve cloud storage backends.
        """
        self._root = root_path
        self._bucket = bucket
        self._registry = registry

    def _path(self, key: str) -> str:
        """
        Get the absolute local path for a storage key.

        Args:
            key: Storage object key.

        Returns:
            Local file path string.
        """
        import os

        return os.path.join(self._root, self._bucket, key)

    async def read(self, key: str) -> bytes | None:
        """
        Read file contents as bytes.

        Args:
            key: The unique storage path/key.

        Returns:
            Raw file bytes if successful, None if not found or errored.
        """
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            try:
                storage_file = await backend.open(key, "rb")
                return await storage_file.read()
            except Exception:
                return None

        import os

        path = self._path(key)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return f.read()

    async def write(self, key: str, data: bytes) -> None:
        """
        Write/save file bytes.

        Args:
            key: The unique storage path/key.
            data: Raw file bytes to save.
        """
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            await backend.save(key, data, overwrite=True)
            return

        import os

        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    async def delete(self, key: str) -> bool:
        """
        Delete a file from storage.

        Args:
            key: The unique storage path/key.

        Returns:
            True if deletion was successful, False otherwise.
        """
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            try:
                await backend.delete(key)
                return True
            except Exception:
                return False

        import os

        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    async def exists(self, key: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            key: The unique storage path/key.

        Returns:
            True if the file exists, False otherwise.
        """
        if self._registry is not None:
            backend = self._registry.get(self._bucket) or self._registry.default
            try:
                return await backend.exists(key)
            except Exception:
                return False

        import os

        return os.path.exists(self._path(key))


# ============================================================================
# EffectRegistry -- Central registry with lifecycle and DI integration
# ============================================================================


class EffectRegistry:
    """
    Registry for effect providers.

    Validates effect availability, manages provider lifecycles,
    and integrates with the DI system.

    Lifecycle:
        1. register() -- register providers at setup time
        2. initialize_all() -- called at startup (initializes all providers)
        3. acquire/release -- per-request via FlowPipeline or EffectScope
        4. finalize_all() -- called at shutdown

    DI Integration:
        - Registered as app-scoped singleton via register_with_container()
        - Individual providers accessible via ``effect:{name}`` tokens
        - Supports ``startup()`` / ``shutdown()`` DI lifecycle hooks

    Health:
        - ``health_check()`` aggregates health from all providers
    """

    def __init__(self):
        self.providers: dict[str, EffectProvider] = {}
        self._initialized = False
        self._metrics: dict[str, dict[str, int]] = {}  # per-effect acquire/release counts
        self._acquired_resources: EffectMap = {}

    def register(self, effect_name: str, provider: EffectProvider):
        """Register an effect provider."""
        self.providers[effect_name] = provider
        self._metrics[effect_name] = {"acquires": 0, "releases": 0, "errors": 0}

    def unregister(self, effect_name: str) -> EffectProvider | None:
        """Unregister and return an effect provider."""
        self._metrics.pop(effect_name, None)
        return self.providers.pop(effect_name, None)

    async def initialize_all(self):
        """Initialize all registered providers (lifecycle startup hook)."""
        if self._initialized:
            return
        for name, provider in self.providers.items():
            try:
                await provider.initialize()
            except Exception as exc:
                logger.error("Failed to initialize effect '%s': %s", name, exc)
                raise
        self._initialized = True

    async def finalize_all(self):
        """Finalize all providers (lifecycle shutdown hook)."""
        for name, provider in self.providers.items():
            try:
                await provider.finalize()
            except Exception as exc:
                logger.warning("Error finalizing effect '%s': %s", name, exc)
        self._initialized = False

    # -- Per-request acquire/release --------------------------------------

    async def acquire(self, effect_name: str, mode: str | None = None) -> Any:
        """
        Acquire a resource for the named effect.

        Args:
            effect_name: Registered effect name.
            mode: Optional mode specifier.

        Returns:
            Resource handle.

        Raises:
            KeyError: If effect is not registered.
        """
        provider = self.get_provider(effect_name)
        try:
            resource = await provider.acquire(mode)
            self._acquired_resources[effect_name] = resource
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["acquires"] += 1
            return resource
        except Exception:
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["errors"] += 1
            raise

    async def release(
        self,
        effect_name: str,
        resource: Any,
        *,
        success: bool = True,
    ) -> None:
        """
        Release a resource for the named effect.

        Args:
            effect_name: Registered effect name.
            resource: Resource handle from acquire().
            success: Whether the operation succeeded.
        """
        provider = self.get_provider(effect_name)
        try:
            await provider.release(resource, success=success)
            self._acquired_resources.pop(effect_name, None)
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["releases"] += 1
        except Exception as exc:
            metrics = self._metrics.get(effect_name)
            if metrics:
                metrics["errors"] += 1
            logger.warning("Error releasing effect '%s': %s", effect_name, exc)

    # DI lifecycle aliases
    async def startup(self):
        """DI lifecycle startup hook."""
        await self.initialize_all()

    async def shutdown(self):
        """DI lifecycle shutdown hook."""
        await self.finalize_all()

    def has_effect(self, effect_name: str) -> bool:
        """Check if effect is available."""
        return effect_name in self.providers

    def get_provider(self, effect_name: str) -> EffectProvider:
        """Get provider for effect."""
        if effect_name not in self.providers:
            from .faults.domains import EffectNotAcquiredFault

            raise EffectNotAcquiredFault(
                effect_name=effect_name,
                reason="No provider is registered for this effect name.",
                registered_effects=list(self.providers.keys()),
                middleware_active=False,
            )
        return self.providers[effect_name]

    # -- Health -----------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        """Aggregate health from all providers."""
        results: dict[str, Any] = {}
        all_healthy = True
        for name, provider in self.providers.items():
            try:
                health = await provider.health_check()
                results[name] = health
                if not health.get("healthy", True):
                    all_healthy = False
            except Exception as exc:
                results[name] = {"healthy": False, "error": str(exc)}
                all_healthy = False
        return {
            "healthy": all_healthy,
            "initialized": self._initialized,
            "provider_count": len(self.providers),
            "providers": results,
            "metrics": dict(self._metrics),
        }

    # -- DI Integration ---------------------------------------------------

    def register_with_container(self, container: Any):
        """
        Register this EffectRegistry and all effect providers with a DI container.

        Args:
            container: DI Container instance
        """
        from aquilia.di.providers import ValueProvider

        # Register the registry itself
        container.register(
            ValueProvider(
                value=self,
                token=EffectRegistry,
                scope="app",
            )
        )

        # Register individual providers by effect name
        for effect_name, provider in self.providers.items():
            try:
                container.register(
                    ValueProvider(
                        value=provider,
                        token=f"effect:{effect_name}",
                        scope="app",
                    )
                )
            except ValueError:
                pass  # Already registered

    # -- Introspection ----------------------------------------------------

    def list_effects(self) -> list[str]:
        """Return all registered effect names."""
        return list(self.providers.keys())

    def get_metrics(self) -> dict[str, dict[str, int]]:
        """Return per-effect metrics."""
        return dict(self._metrics)

    def __repr__(self) -> str:
        effects = list(self.providers.keys())
        return f"<EffectRegistry effects={effects} initialized={self._initialized}>"
