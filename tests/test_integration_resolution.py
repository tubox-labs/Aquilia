from __future__ import annotations

import os

import pytest

from aquilia import Workspace
from aquilia.faults.domains import ConfigMissingFault
from aquilia.integrations import (
    DatabaseIntegration,
    MailIntegration,
)
from aquilia.integrations import SmtpProvider as SMTPProvider
from aquilia.pyconfig import AquilaConfig, Env, Secret


def test_env_resolution(monkeypatch):
    """Verify Env resolution in integrations."""
    monkeypatch.setenv("EMAIL_HOST_USER", "test_user_from_env")

    provider = SMTPProvider(username=Env("EMAIL_HOST_USER"))
    # The provider wrapper resolves values at instantiation time and to_dict() returns them resolved
    assert provider.username == "test_user_from_env"

    d = provider.to_dict()
    assert d["username"] == "test_user_from_env"


def test_secret_resolution(monkeypatch):
    """Verify Secret resolution in integrations."""
    monkeypatch.setenv("EMAIL_HOST_PASSWORD", "secret_pass_123")

    provider = SMTPProvider(password=Secret("EMAIL_HOST_PASSWORD"))
    assert provider.password == "secret_pass_123"

    d = provider.to_dict()
    assert d["password"] == "secret_pass_123"


def test_pyconfig_resolution(monkeypatch):
    """Verify PyConfig value resolution in integrations."""
    monkeypatch.setenv("EMAIL_USER_VAR", "config_user")
    monkeypatch.setenv("EMAIL_PASS_VAR", "config_pass")

    class TestEnv(AquilaConfig):
        env = "test_env"

        class mail(AquilaConfig.Mail):
            email_user = Env("EMAIL_USER_VAR", cast=str)
            email_password = Secret(env="EMAIL_PASS_VAR")

    # SMTPProvider with PyConfig fields
    provider = SMTPProvider(
        username=TestEnv.mail.email_user,
        password=TestEnv.mail.email_password,
    )

    assert provider.username == "config_user"
    assert provider.password == "config_pass"

    d = provider.to_dict()
    assert d["username"] == "config_user"
    assert d["password"] == "config_pass"


def test_type_casting(monkeypatch):
    """Verify that Env type casting works correctly in integrations."""
    monkeypatch.setenv("EMAIL_PORT_VAR", "465")

    provider = SMTPProvider(port=Env("EMAIL_PORT_VAR", cast=int))

    assert provider.port == 465
    assert isinstance(provider.port, int)

    d = provider.to_dict()
    assert d["port"] == 465


def test_validation_errors(monkeypatch):
    """Verify that invalid values fail with meaningful errors."""
    # Env has required=True and is not set, resolving it should raise ConfigMissingFault
    if "REQUIRED_NOT_SET" in os.environ:
        monkeypatch.delenv("REQUIRED_NOT_SET", raising=False)

    with pytest.raises(ConfigMissingFault):
        SMTPProvider(username=Env("REQUIRED_NOT_SET", required=True))

    with pytest.raises(ConfigMissingFault):
        SMTPProvider(password=Secret(env="REQUIRED_NOT_SET", required=True))


def test_backwards_compatibility():
    """Verify that existing string-based and int-based configurations function unchanged."""
    provider = SMTPProvider(
        host="smtp.example.com",
        port=587,
        username="flat_string_user",
        password="flat_string_password",
    )

    assert provider.host == "smtp.example.com"
    assert provider.port == 587
    assert provider.username == "flat_string_user"
    assert provider.password == "flat_string_password"

    d = provider.to_dict()
    assert d["host"] == "smtp.example.com"
    assert d["port"] == 587
    assert d["username"] == "flat_string_user"
    assert d["password"] == "flat_string_password"


def test_integration_nested_in_workspace(monkeypatch):
    """Verify that resolving a full workspace config resolves nested Env/Secret/PyConfig wrappers."""
    monkeypatch.setenv("MAIL_FROM", "workspace_from@aquilia.io")
    monkeypatch.setenv("DB_URL", "postgresql://db.aquilia.io/prod")

    mail_integration = MailIntegration(
        default_from=Env("MAIL_FROM"), providers=[SMTPProvider(username=Env("MAIL_FROM"))]
    )

    db_integration = DatabaseIntegration(url=Env("DB_URL"))

    workspace = Workspace("test-workspace").integrate(mail_integration).integrate(db_integration)

    config = workspace.to_dict()

    assert config["integrations"]["mail"]["default_from"] == "workspace_from@aquilia.io"
    assert config["integrations"]["mail"]["providers"][0]["username"] == "workspace_from@aquilia.io"
    assert config["integrations"]["database"]["url"] == "postgresql://db.aquilia.io/prod"
