"""
Testing utilities for DI system.
"""

from contextlib import asynccontextmanager
from typing import Any

from .core import Container, Provider, Registry
from .providers import ValueProvider


class MockProvider(ValueProvider):
    """
    Mock provider for testing.

    Tracks access for assertions.
    """

    def __init__(
        self,
        value: Any,
        token: type | str,
        name: str = "mock",
        tags: tuple[str, ...] = (),
    ):
        super().__init__(value, token, name, tags)
        self.access_count = 0
        self.instantiate_calls = []

    async def instantiate(self, ctx):
        """Track instantiation calls."""
        self.access_count += 1
        self.instantiate_calls.append(ctx.get_trace())
        return await super().instantiate(ctx)

    def reset(self) -> None:
        """Reset tracking."""
        self.access_count = 0
        self.instantiate_calls.clear()


class TestRegistry(Registry):
    """
    Registry with testing support.

    Allows easy provider overrides for testing.
    """

    def __init__(self, config: Any | None = None):
        super().__init__(config)
        self._overrides: dict[str, Provider] = {}

    @classmethod
    def from_manifests(
        cls,
        manifests: list[Any],
        config: Any | None = None,
        *,
        overrides: dict[str, Provider] | None = None,
        enforce_cross_app: bool = False,  # Relaxed for tests
    ) -> "TestRegistry":
        """
        Build test registry with overrides.

        Args:
            manifests: List of manifests
            config: Optional config
            overrides: Dict of {token: mock_provider}
            enforce_cross_app: If False, skip cross-app validation

        Returns:
            Test registry
        """
        registry = cls(config=config)

        # Load manifests normally
        for manifest in manifests:
            registry._load_manifest_services(manifest)

        # Apply overrides
        if overrides:
            for token, provider in overrides.items():
                registry._overrides[token] = provider

        # Build graph (skip validation in tests)
        registry._build_dependency_graph()

        # Cycle detection still useful in tests
        try:
            registry._detect_cycles()
        except Exception:
            # Allow cycles in tests with lazy proxies
            pass

        return registry

    def build_container(self) -> Container:
        """Build container with overrides applied."""
        container = super().build_container()

        # Apply overrides
        for _token, provider in self._overrides.items():
            tag = provider.meta.tags[0] if provider.meta.tags else None
            container.register(provider, tag=tag)

        return container


@asynccontextmanager
async def override_container(
    container: Container,
    token: type | str,
    mock_value: Any,
    *,
    tag: str | None = None,
):
    """
    Context manager to temporarily override a provider.

    Args:
        container: Container to override
        token: Token to override
        mock_value: Mock value to inject
        tag: Optional tag

    Example:
        async with override_container(container, UserRepo, MockRepo()):
            # Tests run with MockRepo
            result = await handler()
    """
    # Create mock provider
    mock = MockProvider(mock_value, token, tags=(tag,) if tag else ())

    # Save original provider and cache
    token_key = container._token_to_key(token)
    cache_key = container._make_cache_key(token_key, tag)
    original_provider = container._providers.get(cache_key)
    original_cached = container._cache.get(cache_key)

    # SEC-DI-07: Ensure COW ownership before mutating _providers
    if not container._providers_owned:
        container._providers = container._providers.copy()
        container._providers_owned = True

    # Force-replace provider (bypass duplicate check)
    container._providers[cache_key] = mock

    # Clear cache so the mock is resolved on next access
    container._cache.pop(cache_key, None)

    try:
        yield mock
    finally:
        # Restore original provider
        if original_provider is not None:
            container._providers[cache_key] = original_provider
        else:
            container._providers.pop(cache_key, None)

        # Restore original cache
        container._cache.pop(cache_key, None)
        if original_cached is not None:
            container._cache[cache_key] = original_cached


# Pytest fixtures (if pytest is available)
try:
    import pytest

    @pytest.fixture
    def di_container():
        """Provide a clean DI container for tests."""
        container = Container(scope="app")
        yield container
        # Cleanup handled by pytest

    @pytest.fixture
    async def request_container(di_container):
        """Provide a request-scoped container."""
        container = di_container.create_request_scope()
        yield container
        await container.shutdown()

    @pytest.fixture
    def mock_provider():
        """Factory fixture for creating mock providers."""

        def _create_mock(value: Any, token: type | str, **kwargs):
            return MockProvider(value, token, **kwargs)

        return _create_mock

except ImportError:
    # pytest not available - skip fixtures
    pass
