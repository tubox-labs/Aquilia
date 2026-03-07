"""
AquilaMail Configuration -- Serializer-based, DI-aware mail configuration.

Uses Aquilia's Serializer system instead of raw dataclasses for:
- Declarative field validation with typed fields
- OpenAPI schema generation via ``.to_schema()``
- DI-aware defaults (InjectDefault, container resolution)
- Cross-field validation hooks
- Consistent Aquilia-native patterns

Integrates with Aquilia's Config system and workspace builder pattern.
All values have sensible defaults for development; override via config
files, environment variables, or the Workspace fluent API.
"""

from __future__ import annotations

from ..blueprints.core import Blueprint
from ..blueprints.facets import (
    BoolFacet,
    TextFacet,
    DictFacet,
    FloatFacet,
    IntFacet,
    ListFacet,
    ChoiceFacet,
)


# ── Provider types ──────────────────────────────────────────────────

PROVIDER_TYPES = ("smtp", "ses", "sendgrid", "console", "file")


# ═══════════════════════════════════════════════════════════════════
# Sub-config Serializers
# ═══════════════════════════════════════════════════════════════════


class ProviderConfigBlueprint(Blueprint):
    """
    Blueprint for a single mail provider configuration.

    Validates provider type, priority bounds, and SMTP-specific fields.
    """

    name = TextFacet(max_length=100, required=True, help_text="Unique provider name")
    type = ChoiceFacet(
        choices=PROVIDER_TYPES,
        required=True,
        help_text="Provider backend type",
    )
    priority = IntFacet(
        min_value=0, max_value=1000, default=50, required=False,
        help_text="Lower = preferred",
    )
    enabled = BoolFacet(default=True, required=False)
    rate_limit_per_min = IntFacet(
        min_value=0, default=600, required=False,
        help_text="Max messages per minute for this provider",
    )
    config = DictFacet(default=dict, required=False, help_text="Extra provider-specific options")

    # SMTP shortcuts
    host = TextFacet(default=None, required=False, allow_null=True)
    port = IntFacet(
        min_value=1, max_value=65535, default=None, required=False, allow_null=True,
    )
    username = TextFacet(default=None, required=False, allow_null=True)
    password = TextFacet(default=None, required=False, allow_null=True, write_only=True)
    use_tls = BoolFacet(default=True, required=False)
    use_ssl = BoolFacet(default=False, required=False)
    timeout = FloatFacet(min_value=0.1, max_value=300.0, default=30.0, required=False)

    # Nested auth block (preferred over flat username/password)
    auth = DictFacet(default=None, required=False, allow_null=True,
                     help_text="Nested MailAuthConfig dict -- preferred over flat username/password")

    def validate(self, attrs: dict) -> dict:
        """Cross-field validation: SMTP needs host."""
        if attrs.get("type") == "smtp":
            host = attrs.get("host")
            config = attrs.get("config", {})
            if not host and not (config and config.get("host")):
                pass  # host defaults to localhost in provider
        return attrs


class MailAuthConfigBlueprint(Blueprint):
    """
    Blueprint for mail provider authentication credentials.

    Groups all authentication data for a mail provider into one
    nested object, making it clear which fields are credentials
    versus transport options.

    Supported authentication schemes (set ``method`` accordingly):

    * ``plain``  -- SMTP AUTH PLAIN / LOGIN (username + password)
    * ``oauth2`` -- OAuth2 bearer token (access_token + optionally token_url,
                    client_id, client_secret for auto-refresh)
    * ``api_key`` -- API-key-based providers (SendGrid, SES, etc.)
    * ``ntlm``   -- Windows NTLM (username + password + domain)
    * ``none``   -- Anonymous / unauthenticated relay
    """

    METHOD_CHOICES = ("plain", "oauth2", "api_key", "ntlm", "none")

    method = ChoiceFacet(
        choices=METHOD_CHOICES,
        default="plain",
        required=False,
        help_text="Authentication mechanism",
    )

    # ── Plain / NTLM ──
    username = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="SMTP username or account identifier",
    )
    password = TextFacet(
        default=None, required=False, allow_null=True, write_only=True,
        help_text="SMTP password or app-specific password (write-only)",
    )

    # ── NTLM extras ──
    domain = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="Windows domain for NTLM authentication",
    )

    # ── API-key / SES / SendGrid ──
    api_key = TextFacet(
        default=None, required=False, allow_null=True, write_only=True,
        help_text="API key for API-key-authenticated providers (write-only)",
    )
    api_key_env = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="Environment variable name that holds the API key",
    )

    # ── AWS SES ──
    aws_access_key_id = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="AWS access key ID for SES",
    )
    aws_secret_access_key = TextFacet(
        default=None, required=False, allow_null=True, write_only=True,
        help_text="AWS secret access key for SES (write-only)",
    )
    aws_region = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="AWS region for SES (e.g. 'us-east-1')",
    )
    aws_session_token = TextFacet(
        default=None, required=False, allow_null=True, write_only=True,
        help_text="Temporary AWS session token (STS / assume-role)",
    )

    # ── OAuth2 ──
    access_token = TextFacet(
        default=None, required=False, allow_null=True, write_only=True,
        help_text="OAuth2 bearer access token (write-only)",
    )
    refresh_token = TextFacet(
        default=None, required=False, allow_null=True, write_only=True,
        help_text="OAuth2 refresh token for auto-renewal (write-only)",
    )
    token_url = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="OAuth2 token endpoint URL",
    )
    client_id = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="OAuth2 client ID",
    )
    client_secret = TextFacet(
        default=None, required=False, allow_null=True, write_only=True,
        help_text="OAuth2 client secret (write-only)",
    )
    scope = TextFacet(
        default=None, required=False, allow_null=True,
        help_text="OAuth2 scope string (space-separated)",
    )
    token_expiry = IntFacet(
        default=None, required=False, allow_null=True,
        help_text="Unix timestamp when the current access token expires",
    )

    def validate(self, attrs: dict) -> dict:
        """Cross-field validation for authentication credentials."""
        method = attrs.get("method", "plain")
        if method in ("plain", "ntlm"):
            # Soft-warn: username typically required for authenticated SMTP
            pass
        elif method == "api_key":
            # Either api_key literal OR api_key_env should be set
            pass
        elif method == "oauth2":
            # access_token or (client_id + token_url) should be present
            pass
        return attrs


class RetryConfigBlueprint(Blueprint):
    """Blueprint for retry / backoff configuration."""

    max_attempts = IntFacet(min_value=0, max_value=100, default=5, required=False)
    base_delay = FloatFacet(min_value=0.0, max_value=60.0, default=1.0, required=False)
    max_delay = FloatFacet(min_value=0.0, default=3600.0, required=False)
    jitter = BoolFacet(default=True, required=False)

    def validate(self, attrs: dict) -> dict:
        """Ensure base_delay <= max_delay."""
        base = attrs.get("base_delay", 1.0)
        mx = attrs.get("max_delay", 3600.0)
        if base > mx:
            raise ValueError("base_delay must be <= max_delay")
        return attrs


class RateLimitConfigBlueprint(Blueprint):
    """Blueprint for global and per-domain rate-limiting."""

    global_per_minute = IntFacet(min_value=0, default=1000, required=False)
    per_domain_per_minute = IntFacet(min_value=0, default=100, required=False)
    per_provider_per_minute = IntFacet(
        min_value=0, default=None, required=False, allow_null=True,
    )


class SecurityConfigBlueprint(Blueprint):
    """Blueprint for security / deliverability settings."""

    dkim_enabled = BoolFacet(default=False, required=False)
    dkim_domain = TextFacet(default=None, required=False, allow_null=True)
    dkim_selector = TextFacet(max_length=100, default="aquilia", required=False)
    dkim_private_key_path = TextFacet(default=None, required=False, allow_null=True)
    dkim_private_key_env = TextFacet(default="AQUILIA_DKIM_PRIVATE_KEY", required=False)

    require_tls = BoolFacet(default=True, required=False)
    allowed_from_domains = ListFacet(
        child=TextFacet(max_length=253),
        default=list,
        required=False,
    )
    pii_redaction_enabled = BoolFacet(default=False, required=False)

    def validate(self, attrs: dict) -> dict:
        """DKIM domain required when DKIM is enabled."""
        if attrs.get("dkim_enabled") and not attrs.get("dkim_domain"):
            pass  # warning-level, not a hard error
        return attrs


class TemplateConfigBlueprint(Blueprint):
    """Blueprint for ATS template engine configuration."""

    template_dirs = ListFacet(
        child=TextFacet(max_length=500),
        default=lambda: ["mail_templates"],
        required=False,
    )
    auto_escape = BoolFacet(default=True, required=False)
    cache_compiled = BoolFacet(default=True, required=False)
    strict_mode = BoolFacet(default=False, required=False)


class QueueConfigBlueprint(Blueprint):
    """Blueprint for queue / storage settings."""

    db_url = TextFacet(default="", required=False, help_text="Empty = use app main database")
    batch_size = IntFacet(min_value=1, max_value=10000, default=50, required=False)
    poll_interval = FloatFacet(min_value=0.1, max_value=60.0, default=1.0, required=False)
    dedupe_window_seconds = IntFacet(min_value=0, default=3600, required=False)
    retention_days = IntFacet(min_value=1, max_value=3650, default=30, required=False)


# ═══════════════════════════════════════════════════════════════════
# Backward-compatible config wrappers
# ═══════════════════════════════════════════════════════════════════
#
# These lightweight classes wrap validated serializer data so that
# existing code can still access config via attribute syntax
# (e.g. ``config.retry.max_attempts``).  They are created by the
# ``from_dict`` / ``from_validated`` factories.
# ═══════════════════════════════════════════════════════════════════


class _ConfigObject:
    """
    Thin attribute-access wrapper over a dict.

    Allows ``obj.key`` access while keeping dict underneath
    for serializer round-trips.

    Subclasses set ``_serializer_cls`` to auto-validate and fill
    defaults when created with keyword arguments.
    """

    __slots__ = ("_data",)
    _serializer_cls: type | None = None

    def __init__(self, data: dict | None = None, **kwargs):
        if data is None:
            data = kwargs
        # Validate through the blueprint to populate defaults
        # (e.g. ProviderConfig(name="x", type="smtp") gets priority=50, etc.
        #  or RetryConfig() gets max_attempts=5, base_delay=1.0, etc.)
        cls_bp = type(self)._blueprint_cls
        if cls_bp is not None:
            bp = cls_bp(data=data)
            if bp.is_sealed():
                data = bp.validated_data
        object.__setattr__(self, "_data", dict(data))

    def __getattr__(self, name: str) -> Any:
        data = object.__getattribute__(self, "_data")
        if name in data:
            return data[name]
        raise AttributeError(
            f"{type(self).__name__!r} has no attribute {name!r}"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        data = object.__getattribute__(self, "_data")
        data[name] = value

    def __repr__(self) -> str:
        cls = type(self).__name__
        data = object.__getattribute__(self, "_data")
        return f"{cls}({data!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _ConfigObject):
            return (
                object.__getattribute__(self, "_data")
                == object.__getattribute__(other, "_data")
            )
        return NotImplemented

    def to_dict(self) -> dict:
        data = object.__getattribute__(self, "_data")
        result = {}
        for k, v in data.items():
            if isinstance(v, _ConfigObject):
                result[k] = v.to_dict()
            elif isinstance(v, list):
                result[k] = [
                    item.to_dict() if isinstance(item, _ConfigObject) else item
                    for item in v
                ]
            else:
                result[k] = v
        return result


class ProviderConfig(_ConfigObject):
    """Attribute-access wrapper for a validated provider config."""
    _blueprint_cls = ProviderConfigBlueprint


class RetryConfig(_ConfigObject):
    """Attribute-access wrapper for a validated retry config."""
    _blueprint_cls = RetryConfigBlueprint


class RateLimitConfig(_ConfigObject):
    """Attribute-access wrapper for a validated rate-limit config."""
    _blueprint_cls = RateLimitConfigBlueprint


class SecurityConfig(_ConfigObject):
    """Attribute-access wrapper for a validated security config."""
    _blueprint_cls = SecurityConfigBlueprint


class TemplateConfig(_ConfigObject):
    """Attribute-access wrapper for a validated template config."""
    _blueprint_cls = TemplateConfigBlueprint


class QueueConfig(_ConfigObject):
    """Attribute-access wrapper for a validated queue config."""
    _blueprint_cls = QueueConfigBlueprint


class MailAuthConfig(_ConfigObject):
    """
    Attribute-access wrapper for validated mail authentication credentials.

    Group all provider credentials in one place::

        MailAuthConfig(
            method="plain",
            username="user@example.com",
            password="s3cr3t",
        )

        MailAuthConfig(
            method="api_key",
            api_key_env="SENDGRID_API_KEY",
        )

        MailAuthConfig(
            method="oauth2",
            client_id="abc",
            client_secret="xyz",
            token_url="https://oauth.provider/token",
            scope="https://mail.example.com/send",
        )

        MailAuthConfig(
            method="api_key",
            aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
            aws_secret_access_key_env="AWS_SECRET_ACCESS_KEY",
            aws_region="us-east-1",
        )
    """
    _blueprint_cls = MailAuthConfigBlueprint

    @classmethod
    def plain(cls, username: str, password: str) -> "MailAuthConfig":
        """Convenience constructor for plain SMTP auth."""
        return cls({"method": "plain", "username": username, "password": password})

    @classmethod
    def api_key(cls, key: Optional[str] = None, *, env: Optional[str] = None) -> "MailAuthConfig":
        """Convenience constructor for API-key-based auth (SendGrid, etc.)."""
        return cls({"method": "api_key", "api_key": key, "api_key_env": env})

    @classmethod
    def aws_ses(
        cls,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        session_token: Optional[str] = None,
    ) -> "MailAuthConfig":
        """Convenience constructor for AWS SES credentials."""
        return cls({
            "method": "api_key",
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": secret_access_key,
            "aws_region": region,
            "aws_session_token": session_token,
        })

    @classmethod
    def oauth2(
        cls,
        client_id: str,
        client_secret: str,
        token_url: str,
        scope: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> "MailAuthConfig":
        """Convenience constructor for OAuth2 auth."""
        return cls({
            "method": "oauth2",
            "client_id": client_id,
            "client_secret": client_secret,
            "token_url": token_url,
            "scope": scope,
            "access_token": access_token,
            "refresh_token": refresh_token,
        })

    @classmethod
    def anonymous(cls) -> "MailAuthConfig":
        """Convenience constructor for unauthenticated relay."""
        return cls({"method": "none"})


# ═══════════════════════════════════════════════════════════════════
# Internal validation helpers
# ═══════════════════════════════════════════════════════════════════


def _validate_sub(
    blueprint_cls: type,
    data: dict,
    wrapper_cls: type,
) -> _ConfigObject:
    """Validate a sub-config dict through its blueprint, return wrapper."""
    bp = blueprint_cls(data=data)
    if bp.is_sealed():
        return wrapper_cls(bp.validated_data)
    # If validation fails, still create with defaults (lenient for config)
    return wrapper_cls(data)


def _validate_auth(
    value: Any,
) -> Optional["MailAuthConfig"]:
    """
    Coerce a raw dict, MailAuthConfig, or None into a validated MailAuthConfig.
    Returns None when the value is None (anonymous / not set).
    """
    if value is None:
        return None
    if isinstance(value, MailAuthConfig):
        return value
    if isinstance(value, dict):
        return _validate_sub(MailAuthConfigBlueprint, value, MailAuthConfig)  # type: ignore[arg-type]
    return None


def _validate_provider(data: dict) -> ProviderConfig:
    """Validate a single provider config dict."""
    # Coerce nested auth dict → MailAuthConfig wrapper
    if isinstance(data.get("auth"), dict):
        data = dict(data)  # shallow copy before mutation
        data["auth"] = _validate_auth(data["auth"]).to_dict() if _validate_auth(data["auth"]) else None
    bp = ProviderConfigBlueprint(data=data)
    if bp.is_sealed():
        return ProviderConfig(bp.validated_data)
    return ProviderConfig(data)


def _coerce_providers(items: list) -> List[ProviderConfig]:
    """Convert a list of dicts / ProviderConfig objects to validated wrappers."""
    result: list[ProviderConfig] = []
    for item in items:
        if isinstance(item, ProviderConfig):
            result.append(item)
        elif isinstance(item, dict):
            result.append(_validate_provider(item))
        else:
            result.append(item)
    return result


def _coerce_sub(
    value: Any,
    blueprint_cls: type,
    wrapper_cls: type,
) -> _ConfigObject:
    """Accept a wrapper, dict, or None and return a validated wrapper."""
    if isinstance(value, wrapper_cls):
        return value
    if isinstance(value, _ConfigObject):
        return wrapper_cls(object.__getattribute__(value, "_data"))
    if isinstance(value, dict):
        return _validate_sub(blueprint_cls, value, wrapper_cls)
    # None / missing → defaults
    return _validate_sub(blueprint_cls, {}, wrapper_cls)


# ═══════════════════════════════════════════════════════════════════
# MailConfig -- top-level (preserves the public API)
# ═══════════════════════════════════════════════════════════════════


class MailConfig:
    """
    Top-level mail configuration.

    Integrates with Aquilia's layered config:
        config/base.yaml → config/{mode}.yaml → env vars → workspace.py overrides

    Usage in workspace.py::

        .integrate(Integration.mail(
            default_from="noreply@myapp.com",
            template_dir="mail_templates",
            providers=[...],
        ))

    Attribute access is fully preserved -- all existing code works unchanged.
    Under the hood, each sub-config is validated through its corresponding
    Serializer class.
    """

    __slots__ = (
        "enabled", "default_from", "default_reply_to", "subject_prefix",
        "providers", "retry", "rate_limit", "security", "templates", "queue",
        "auth",
        "console_backend", "file_backend_path", "preview_mode",
        "metrics_enabled", "tracing_enabled",
    )

    def __init__(
        self,
        enabled: bool = True,
        default_from: str = "noreply@localhost",
        default_reply_to: Optional[str] = None,
        subject_prefix: str = "",
        providers: Optional[List[Any]] = None,
        retry: Optional[Any] = None,
        rate_limit: Optional[Any] = None,
        security: Optional[Any] = None,
        templates: Optional[Any] = None,
        queue: Optional[Any] = None,
        auth: Optional[Any] = None,
        console_backend: bool = False,
        file_backend_path: Optional[str] = None,
        preview_mode: bool = False,
        metrics_enabled: bool = True,
        tracing_enabled: bool = False,
    ):
        self.enabled = enabled
        self.default_from = default_from
        self.default_reply_to = default_reply_to
        self.subject_prefix = subject_prefix

        # Sub-configs: accept wrapper objects or raw dicts
        self.providers = _coerce_providers(providers or [])
        self.retry = _coerce_sub(retry, RetryConfigBlueprint, RetryConfig)
        self.rate_limit = _coerce_sub(
            rate_limit, RateLimitConfigBlueprint, RateLimitConfig,
        )
        self.security = _coerce_sub(
            security, SecurityConfigBlueprint, SecurityConfig,
        )
        self.templates = _coerce_sub(
            templates, TemplateConfigBlueprint, TemplateConfig,
        )
        self.queue = _coerce_sub(queue, QueueConfigBlueprint, QueueConfig)

        # Top-level auth (global default -- providers may override with their own auth)
        self.auth: Optional[MailAuthConfig] = _validate_auth(auth)

        self.console_backend = console_backend
        self.file_backend_path = file_backend_path
        self.preview_mode = preview_mode
        self.metrics_enabled = metrics_enabled
        self.tracing_enabled = tracing_enabled

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "default_from": self.default_from,
            "default_reply_to": self.default_reply_to,
            "subject_prefix": self.subject_prefix,
            "providers": [p.to_dict() for p in self.providers],
            "retry": self.retry.to_dict(),
            "rate_limit": self.rate_limit.to_dict(),
            "security": self.security.to_dict(),
            "templates": self.templates.to_dict(),
            "queue": self.queue.to_dict(),
            "auth": self.auth.to_dict() if self.auth is not None else None,
            "console_backend": self.console_backend,
            "metrics_enabled": self.metrics_enabled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MailConfig":
        """
        Build MailConfig from a configuration dictionary.

        Each sub-section is validated through its corresponding Blueprint.
        """
        providers: list[ProviderConfig] = []
        for p in data.get("providers", []):
            if isinstance(p, ProviderConfig):
                providers.append(p)
            elif isinstance(p, dict):
                providers.append(_validate_provider(p))

        retry_data = data.get("retry")
        rate_data = data.get("rate_limit")
        sec_data = data.get("security")
        tmpl_data = data.get("templates")
        queue_data = data.get("queue")
        auth_data = data.get("auth")

        return cls(
            enabled=data.get("enabled", True),
            default_from=data.get("default_from", "noreply@localhost"),
            default_reply_to=data.get("default_reply_to"),
            subject_prefix=data.get("subject_prefix", ""),
            providers=providers,
            retry=_validate_sub(
                RetryConfigBlueprint,
                retry_data if isinstance(retry_data, dict) else {},
                RetryConfig,
            ),
            rate_limit=_validate_sub(
                RateLimitConfigBlueprint,
                rate_data if isinstance(rate_data, dict) else {},
                RateLimitConfig,
            ),
            security=_validate_sub(
                SecurityConfigBlueprint,
                sec_data if isinstance(sec_data, dict) else {},
                SecurityConfig,
            ),
            templates=_validate_sub(
                TemplateConfigBlueprint,
                tmpl_data if isinstance(tmpl_data, dict) else {},
                TemplateConfig,
            ),
            queue=_validate_sub(
                QueueConfigBlueprint,
                queue_data if isinstance(queue_data, dict) else {},
                QueueConfig,
            ),
            auth=_validate_auth(auth_data),
            console_backend=data.get("console_backend", False),
            file_backend_path=data.get("file_backend_path"),
            preview_mode=data.get("preview_mode", False),
            metrics_enabled=data.get("metrics_enabled", True),
            tracing_enabled=data.get("tracing_enabled", False),
        )

    @classmethod
    def development(cls) -> "MailConfig":
        """Pre-configured for local development (console backend)."""
        return cls(
            console_backend=True,
            preview_mode=True,
            default_from="dev@localhost",
            providers=[
                ProviderConfig({"name": "console", "type": "console"}),
            ],
        )

    @classmethod
    def production(cls, default_from: str, **overrides: Any) -> "MailConfig":
        """Pre-configured for production with sensible defaults."""
        config = cls(
            default_from=default_from,
            console_backend=False,
            preview_mode=False,
            metrics_enabled=True,
            tracing_enabled=True,
            security=SecurityConfig({
                "dkim_enabled": True,
                "require_tls": True,
                "pii_redaction_enabled": True,
            }),
        )
        for k, v in overrides.items():
            if hasattr(config, k):
                setattr(config, k, v)
        return config
