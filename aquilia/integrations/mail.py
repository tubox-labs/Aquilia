"""
Mail integration — typed, flat-namespace mail configuration.

Before (old, 3-level nesting)::

    Integration.MailAuth.plain("user", password_env="SMTP_PASS")
    Integration.MailProvider.SMTP(name="primary", host="smtp.app.com")
    Integration.mail(default_from="noreply@app.com", ...)

After (new, flat)::

    MailAuth.plain("user", password_env="SMTP_PASS")
    SmtpProvider(name="primary", host="smtp.app.com")
    MailIntegration(default_from="noreply@app.com", ...)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MailAuth
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


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
    username: Optional[str] = None
    password: Optional[str] = None
    password_env: Optional[str] = None
    domain: Optional[str] = None
    api_key: Optional[str] = None
    api_key_env: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_access_key_id_env: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_secret_access_key_env: Optional[str] = None
    aws_region: Optional[str] = None
    aws_session_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    client_secret_env: Optional[str] = None
    scope: Optional[str] = None

    # ── Factory classmethods ─────────────────────────────────────────

    @classmethod
    def plain(
        cls,
        username: str,
        password: Optional[str] = None,
        *,
        password_env: Optional[str] = None,
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
        key: Optional[str] = None,
        *,
        env: Optional[str] = None,
    ) -> MailAuth:
        """API-key auth for SendGrid, Mailgun, Postmark, etc."""
        return cls(method="api_key", api_key=key, api_key_env=env)

    @classmethod
    def aws_ses(
        cls,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        session_token: Optional[str] = None,
        *,
        access_key_id_env: Optional[str] = None,
        secret_access_key_env: Optional[str] = None,
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
        client_secret: Optional[str] = None,
        *,
        client_secret_env: Optional[str] = None,
        token_url: str,
        scope: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
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
        password: Optional[str] = None,
        domain: Optional[str] = None,
        *,
        password_env: Optional[str] = None,
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

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"method": self.method}
        _optionals = [
            "username", "password", "password_env", "domain",
            "api_key", "api_key_env",
            "aws_access_key_id", "aws_access_key_id_env",
            "aws_secret_access_key", "aws_secret_access_key_env",
            "aws_region", "aws_session_token",
            "access_token", "refresh_token", "token_url",
            "client_id", "client_secret", "client_secret_env", "scope",
        ]
        for attr in _optionals:
            val = getattr(self, attr)
            if val is not None:
                d[attr] = val
        return d


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Mail Provider base + concrete providers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class _ProviderBase:
    """Shared fields for all mail provider configs."""

    name: str = ""
    priority: int = 10
    enabled: bool = True
    rate_limit_per_min: int = 600
    auth: Optional[MailAuth] = None

    def _base_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "name": self.name,
            "type": getattr(self, "_provider_type", ""),
            "priority": self.priority,
            "enabled": self.enabled,
            "rate_limit_per_min": self.rate_limit_per_min,
        }
        if self.auth is not None:
            d["auth"] = self.auth.to_dict() if hasattr(self.auth, "to_dict") else self.auth
        return d


@dataclass
class SmtpProvider(_ProviderBase):
    """
    SMTP / STARTTLS mail provider.

    Example::

        SmtpProvider(
            name="primary",
            host="smtp.myapp.com",
            port=587,
            auth=MailAuth.plain("user", password_env="SMTP_PASS"),
        )
    """

    _provider_type: str = field(default="smtp", init=False, repr=False)

    host: str = "localhost"
    port: int = 587
    use_tls: bool = True
    use_ssl: bool = False
    timeout: float = 30.0
    pool_size: int = 3
    pool_recycle: float = 300.0
    validate_certs: bool = True
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    source_address: Optional[str] = None
    local_hostname: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name:
            self.name = "smtp"

    def to_dict(self) -> Dict[str, Any]:
        d = self._base_dict()
        d.update({
            "host": self.host,
            "port": self.port,
            "use_tls": self.use_tls,
            "use_ssl": self.use_ssl,
            "timeout": self.timeout,
            "pool_size": self.pool_size,
            "pool_recycle": self.pool_recycle,
            "validate_certs": self.validate_certs,
        })
        if self.client_cert is not None:
            d["client_cert"] = self.client_cert
        if self.client_key is not None:
            d["client_key"] = self.client_key
        if self.source_address is not None:
            d["source_address"] = self.source_address
        if self.local_hostname is not None:
            d["local_hostname"] = self.local_hostname
        return d


@dataclass
class SesProvider(_ProviderBase):
    """
    AWS Simple Email Service provider.

    Example::

        SesProvider(
            name="ses-prod",
            region="eu-west-1",
            auth=MailAuth.aws_ses(access_key_id_env="AWS_KEY"),
        )
    """

    _provider_type: str = field(default="ses", init=False, repr=False)

    region: str = "us-east-1"
    configuration_set: Optional[str] = None
    source_arn: Optional[str] = None
    return_path: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    use_raw: bool = True
    endpoint_url: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.name:
            self.name = "ses"

    def to_dict(self) -> Dict[str, Any]:
        d = self._base_dict()
        d["region"] = self.region
        d["use_raw"] = self.use_raw
        if self.configuration_set is not None:
            d["configuration_set"] = self.configuration_set
        if self.source_arn is not None:
            d["source_arn"] = self.source_arn
        if self.return_path is not None:
            d["return_path"] = self.return_path
        if self.tags:
            d["tags"] = self.tags
        if self.endpoint_url is not None:
            d["endpoint_url"] = self.endpoint_url
        return d


@dataclass
class SendGridProvider(_ProviderBase):
    """
    SendGrid Web API v3 provider.

    Example::

        SendGridProvider(
            auth=MailAuth.api_key(env="SENDGRID_API_KEY"),
            click_tracking=True,
        )
    """

    _provider_type: str = field(default="sendgrid", init=False, repr=False)

    sandbox_mode: bool = False
    click_tracking: bool = True
    open_tracking: bool = True
    categories: List[str] = field(default_factory=list)
    asm_group_id: Optional[int] = None
    ip_pool_name: Optional[str] = None
    template_id: Optional[str] = None
    api_base_url: str = "https://api.sendgrid.com"
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.name:
            self.name = "sendgrid"

    def to_dict(self) -> Dict[str, Any]:
        d = self._base_dict()
        d.update({
            "sandbox_mode": self.sandbox_mode,
            "click_tracking": self.click_tracking,
            "open_tracking": self.open_tracking,
            "api_base_url": self.api_base_url,
            "timeout": self.timeout,
        })
        if self.categories:
            d["categories"] = self.categories
        if self.asm_group_id is not None:
            d["asm_group_id"] = self.asm_group_id
        if self.ip_pool_name is not None:
            d["ip_pool_name"] = self.ip_pool_name
        if self.template_id is not None:
            d["template_id"] = self.template_id
        return d


@dataclass
class ConsoleProvider(_ProviderBase):
    """Console / stdout provider (development only)."""

    _provider_type: str = field(default="console", init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.name:
            self.name = "console"
        if self.priority == 10:
            self.priority = 100

    def to_dict(self) -> Dict[str, Any]:
        return self._base_dict()


@dataclass
class FileProvider(_ProviderBase):
    """File / .eml provider (testing & audit)."""

    _provider_type: str = field(default="file", init=False, repr=False)

    output_dir: str = "/tmp/aquilia_mail"
    max_files: int = 10000
    write_index: bool = True
    include_metadata: bool = True
    file_extension: str = ".eml"

    def __post_init__(self) -> None:
        if not self.name:
            self.name = "file"
        if self.priority == 10:
            self.priority = 90

    def to_dict(self) -> Dict[str, Any]:
        d = self._base_dict()
        d.update({
            "output_dir": self.output_dir,
            "max_files": self.max_files,
            "write_index": self.write_index,
            "include_metadata": self.include_metadata,
            "file_extension": self.file_extension,
        })
        return d


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MailIntegration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@dataclass
class MailIntegration:
    """
    Typed mail subsystem configuration.

    Example::

        MailIntegration(
            default_from="noreply@myapp.com",
            auth=MailAuth.plain("user", password_env="SMTP_PASS"),
            providers=[
                SmtpProvider(host="smtp.myapp.com", port=587),
            ],
        )
    """

    _integration_type: str = field(default="mail", init=False, repr=False)

    default_from: str = "noreply@localhost"
    default_reply_to: Optional[str] = None
    subject_prefix: str = ""
    providers: List[Any] = field(default_factory=list)
    auth: Optional[MailAuth] = None
    console_backend: bool = False
    preview_mode: bool = False
    template_dirs: List[str] = field(default_factory=lambda: ["mail_templates"])
    retry_max_attempts: int = 5
    retry_base_delay: float = 1.0
    rate_limit_global: int = 1000
    rate_limit_per_domain: int = 100
    dkim_enabled: bool = False
    dkim_domain: Optional[str] = None
    dkim_selector: str = "aquilia"
    require_tls: bool = True
    pii_redaction: bool = False
    metrics_enabled: bool = True
    tracing_enabled: bool = False
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        # Normalise auth
        auth_dict: Optional[Dict[str, Any]] = None
        if self.auth is not None:
            auth_dict = self.auth.to_dict() if hasattr(self.auth, "to_dict") else self.auth

        # Normalise providers
        normalised: List[Dict[str, Any]] = []
        raw_providers = self.providers
        if raw_providers is not None and hasattr(raw_providers, "to_dict") and not isinstance(raw_providers, (list, tuple)):
            raw_providers = [raw_providers]
        for p in (raw_providers or []):
            if hasattr(p, "to_dict"):
                p = p.to_dict()
            elif isinstance(p, dict) and hasattr(p.get("auth"), "to_dict"):
                p = {**p, "auth": p["auth"].to_dict()}
            normalised.append(p)

        return {
            "_integration_type": "mail",
            "enabled": self.enabled,
            "default_from": self.default_from,
            "default_reply_to": self.default_reply_to,
            "subject_prefix": self.subject_prefix,
            "providers": normalised,
            "auth": auth_dict,
            "console_backend": self.console_backend,
            "preview_mode": self.preview_mode,
            "templates": {
                "template_dirs": list(self.template_dirs),
            },
            "retry": {
                "max_attempts": self.retry_max_attempts,
                "base_delay": self.retry_base_delay,
            },
            "rate_limit": {
                "global_per_minute": self.rate_limit_global,
                "per_domain_per_minute": self.rate_limit_per_domain,
            },
            "security": {
                "dkim_enabled": self.dkim_enabled,
                "dkim_domain": self.dkim_domain,
                "dkim_selector": self.dkim_selector,
                "require_tls": self.require_tls,
                "pii_redaction_enabled": self.pii_redaction,
            },
            "metrics_enabled": self.metrics_enabled,
            "tracing_enabled": self.tracing_enabled,
        }
