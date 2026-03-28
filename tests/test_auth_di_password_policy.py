from __future__ import annotations

import asyncio

from aquilia.auth import AuthManager
from aquilia.auth.hashing import PasswordPolicy
from aquilia.auth.integration.di_providers import create_auth_container
from aquilia.di import Container
from aquilia.di.providers import ClassProvider
from aquilia.di.providers import ValueProvider


def test_auth_container_registers_password_policy_provider():
    container = create_auth_container()

    policy = asyncio.run(container.resolve_async(PasswordPolicy))

    assert isinstance(policy, PasswordPolicy)
    assert policy.min_length >= 8


def test_auth_container_injects_optional_auth_manager_dependency():
    class Consumer:
        def __init__(self, auth: AuthManager | None = None):
            self.auth = auth

    container = Container(scope="app")
    expected_manager = object()
    container.register(ValueProvider(expected_manager, AuthManager))
    container.register(ClassProvider(Consumer, scope="app"))

    consumer = asyncio.run(container.resolve_async(Consumer))

    assert consumer.auth is expected_manager
