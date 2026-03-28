from __future__ import annotations

import asyncio

from aquilia.auth.hashing import PasswordPolicy
from aquilia.auth.integration.di_providers import create_auth_container


def test_auth_container_registers_password_policy_provider():
    container = create_auth_container()

    policy = asyncio.run(container.resolve_async(PasswordPolicy))

    assert isinstance(policy, PasswordPolicy)
    assert policy.min_length >= 8
