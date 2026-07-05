"""
MailAuth -- canonical mail provider authentication credentials.

Single source of truth for auth field names/classmethods, used by both
``aquilia.integrations.mail.MailIntegration`` and the legacy
``aquilia.integrations.Integration.mail()`` builder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MailAuth:
    """
    Mail authentication credentials.

    Use the factory classmethods for type-safe construction::

        MailAuth.plain("user", password_env="SMTP_PASS")
        MailAuth.api_key(env="SENDGRID_API_KEY")
        MailAuth.aws_ses(region="eu-west-1")
        MailAuth.oauth2(client_id="...", token_url="...")
        MailAuth.ntlm("user", domain="CORP")
        MailAuth.anonymous()
    """

    method: str = "none"
    username: str | None = None
    password: str | None = None
    password_env: str | None = None
    domain: str | None = None
    # Note: stored as api_key_value, not api_key -- a dataclass field can't
    # share a name with the api_key() classmethod defined below (the
    # classmethod's class-body definition clobbers the field's default,
    # making every instance's "api_key" attribute a bound method instead
    # of the intended None/str value). The public dict key stays "api_key"
    # (see to_dict()); only the Python attribute name differs.
    api_key_value: str | None = None
    api_key_env: str | None = None
    aws_access_key_id: str | None = None
    aws_access_key_id_env: str | None = None
    aws_secret_access_key: str | None = None
    aws_secret_access_key_env: str | None = None
    aws_region: str | None = None
    aws_session_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    client_secret_env: str | None = None
    scope: str | None = None

    # ── Factory classmethods ─────────────────────────────────────────

    @classmethod
    def plain(
        cls,
        username: str,
        password: str | None = None,
        *,
        password_env: str | None = None,
    ) -> MailAuth:
        """SMTP AUTH PLAIN / LOGIN."""
        return cls(
            method="plain",
            username=username,
            password=password,
            password_env=password_env,
        )

    @classmethod
    def api_key(
        cls,
        key: str | None = None,
        *,
        env: str | None = None,
    ) -> MailAuth:
        """API-key auth for SendGrid, Mailgun, Postmark, etc."""
        return cls(method="api_key", api_key_value=key, api_key_env=env)

    @classmethod
    def aws_ses(
        cls,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str = "us-east-1",
        session_token: str | None = None,
        *,
        access_key_id_env: str | None = None,
        secret_access_key_env: str | None = None,
    ) -> MailAuth:
        """AWS SES credentials."""
        return cls(
            method="aws_ses",
            aws_access_key_id=access_key_id,
            aws_access_key_id_env=access_key_id_env,
            aws_secret_access_key=secret_access_key,
            aws_secret_access_key_env=secret_access_key_env,
            aws_region=region,
            aws_session_token=session_token,
        )

    @classmethod
    def oauth2(
        cls,
        client_id: str,
        client_secret: str | None = None,
        *,
        client_secret_env: str | None = None,
        token_url: str,
        scope: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
    ) -> MailAuth:
        """OAuth2 bearer-token auth (Gmail, Microsoft 365, etc.)."""
        return cls(
            method="oauth2",
            client_id=client_id,
            client_secret=client_secret,
            client_secret_env=client_secret_env,
            token_url=token_url,
            scope=scope,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    @classmethod
    def ntlm(
        cls,
        username: str,
        password: str | None = None,
        domain: str | None = None,
        *,
        password_env: str | None = None,
    ) -> MailAuth:
        """Windows NTLM authentication."""
        return cls(
            method="ntlm",
            username=username,
            password=password,
            password_env=password_env,
            domain=domain,
        )

    @classmethod
    def anonymous(cls) -> MailAuth:
        """No authentication — open relay."""
        return cls(method="none")

    # ── Serialisation ────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"method": self.method}
        _optionals = [
            "username",
            "password",
            "password_env",
            "domain",
            ("api_key_value", "api_key"),  # (attribute name, dict key)
            "api_key_env",
            "aws_access_key_id",
            "aws_access_key_id_env",
            "aws_secret_access_key",
            "aws_secret_access_key_env",
            "aws_region",
            "aws_session_token",
            "access_token",
            "refresh_token",
            "token_url",
            "client_id",
            "client_secret",
            "client_secret_env",
            "scope",
        ]
        for entry in _optionals:
            attr, key = entry if isinstance(entry, tuple) else (entry, entry)
            val = getattr(self, attr)
            if val is not None:
                d[key] = val
        return d
