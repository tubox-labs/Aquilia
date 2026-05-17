# Mail API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `ProviderConfigBlueprint` | `aquilia/mail/config.py` | Blueprint | Blueprint for a single mail provider configuration. |
| `MailAuthConfigBlueprint` | `aquilia/mail/config.py` | Blueprint | Blueprint for mail provider authentication credentials. |
| `RetryConfigBlueprint` | `aquilia/mail/config.py` | Blueprint | Blueprint for retry / backoff configuration. |
| `RateLimitConfigBlueprint` | `aquilia/mail/config.py` | Blueprint | Blueprint for global and per-domain rate-limiting. |
| `SecurityConfigBlueprint` | `aquilia/mail/config.py` | Blueprint | Blueprint for security / deliverability settings. |
| `TemplateConfigBlueprint` | `aquilia/mail/config.py` | Blueprint | Blueprint for ATS template engine configuration. |
| `QueueConfigBlueprint` | `aquilia/mail/config.py` | Blueprint | Blueprint for queue / storage settings. |
| `ProviderConfig` | `aquilia/mail/config.py` | _ConfigObject | Attribute-access wrapper for a validated provider config. |
| `RetryConfig` | `aquilia/mail/config.py` | _ConfigObject | Attribute-access wrapper for a validated retry config. |
| `RateLimitConfig` | `aquilia/mail/config.py` | _ConfigObject | Attribute-access wrapper for a validated rate-limit config. |
| `SecurityConfig` | `aquilia/mail/config.py` | _ConfigObject | Attribute-access wrapper for a validated security config. |
| `TemplateConfig` | `aquilia/mail/config.py` | _ConfigObject | Attribute-access wrapper for a validated template config. |
| `QueueConfig` | `aquilia/mail/config.py` | _ConfigObject | Attribute-access wrapper for a validated queue config. |
| `MailAuthConfig` | `aquilia/mail/config.py` | _ConfigObject | Attribute-access wrapper for validated mail authentication credentials. |
| `MailConfig` | `aquilia/mail/config.py` | object | Top-level mail configuration. |
| `MailConfigProvider` | `aquilia/mail/di_providers.py` | object | DI provider that builds and validates MailConfig from workspace data. |
| `MailServiceProvider` | `aquilia/mail/di_providers.py` | object | DI provider for MailService -- the central mail orchestrator. |
| `MailProviderRegistry` | `aquilia/mail/di_providers.py` | object | Auto-discovers IMailProvider implementations using Aquilia's |
| `EnvelopeStatus` | `aquilia/mail/envelope.py` | str, Enum | Lifecycle status of an envelope. |
| `Priority` | `aquilia/mail/envelope.py` | int, Enum | Named priority levels. |
| `Attachment` | `aquilia/mail/envelope.py` | object | Attachment metadata (content stored separately in blob store). |
| `MailEnvelope` | `aquilia/mail/envelope.py` | object | Immutable mail envelope -- the unit of work in the mail pipeline. |
| `MailFault` | `aquilia/mail/faults.py` | Fault | Base class for all mail-subsystem faults. |
| `MailSendFault` | `aquilia/mail/faults.py` | MailFault | Provider-level send failure (transient or permanent). |
| `MailTemplateFault` | `aquilia/mail/faults.py` | MailFault | Template parse, compile, or render error. |
| `MailConfigFault` | `aquilia/mail/faults.py` | MailFault | Mail configuration error (missing provider, bad credentials, etc.). |
| `MailSuppressedFault` | `aquilia/mail/faults.py` | MailFault | Recipient is on the suppression list. |
| `MailRateLimitFault` | `aquilia/mail/faults.py` | MailFault | Rate limit exceeded for provider or domain. |
| `MailValidationFault` | `aquilia/mail/faults.py` | MailFault | Invalid email address, missing fields, or envelope validation error. |
| `EmailMessage` | `aquilia/mail/message.py` | object | A single email message -- the primary API for sending mail. |
| `EmailMultiAlternatives` | `aquilia/mail/message.py` | EmailMessage | Email with multiple content alternatives (e.g., plain text + HTML). |
| `TemplateMessage` | `aquilia/mail/message.py` | EmailMessage | Email rendered from an Aquilia Template Syntax (ATS) template. |
| `ProviderResultStatus` | `aquilia/mail/providers/__init__.py` | str, Enum | Granular result from a provider send attempt. |
| `ProviderResult` | `aquilia/mail/providers/__init__.py` | object | Result returned by IMailProvider.send(). |
| `IMailProvider` | `aquilia/mail/providers/__init__.py` | Protocol | Interface that all mail provider backends must implement. |
| `ConsoleProvider` | `aquilia/mail/providers/console.py` | object | Provider that logs emails to the console instead of sending them. |
| `FileProvider` | `aquilia/mail/providers/file.py` | object | Mail provider that writes emails to .eml files on disk. |
| `SendGridProvider` | `aquilia/mail/providers/sendgrid.py` | object | Async SendGrid mail provider using the v3 Web API. |
| `SESProvider` | `aquilia/mail/providers/ses.py` | object | Async AWS SES mail provider. |
| `SMTPProvider` | `aquilia/mail/providers/smtp.py` | object | Async SMTP mail provider backed by aiosmtplib. |
| `MailService` | `aquilia/mail/service.py` | object | Central mail service -- owns the pipeline from message to delivery. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `create_mail_config` | `aquilia/mail/di_providers.py` | `def create_mail_config(config_data: dict[str, Any] &#124; None = None) -> Any` | Factory that creates a validated MailConfig. |
| `create_mail_service` | `aquilia/mail/di_providers.py` | `def create_mail_service(config: Any &#124; None = None) -> Any` | Factory that creates a MailService from config. |
| `register_mail_providers` | `aquilia/mail/di_providers.py` | `def register_mail_providers(container: Container, config_data: dict[str, Any] &#124; None = None, discover_providers: bool = True, extra_scan_packages: list[str] &#124; None = None) -> Any` | Register all mail DI providers into a container. |
| `set_mail_service` | `aquilia/mail/service.py` | `def set_mail_service(svc: MailService &#124; None) -> None` | Install a MailService as the module-level singleton (or None to reset). |
| `send_mail` | `aquilia/mail/service.py` | `def send_mail(subject: str, body: str, from_email: str &#124; None = None, to: Sequence[str] &#124; str &#124; None = None, cc: Sequence[str] &#124; str &#124; None = None, bcc: Sequence[str] &#124; str &#124; None = None, reply_to: str &#124; None = None, headers: dict[str, str] &#124; None = None, attachments: Sequence[tuple[str, bytes, str]] &#124; None = None, priority: int = 50, fail_silently: bool = False, **kwargs: Any) -> str &#124; None` | Send an email synchronously. |
| `asend_mail` | `aquilia/mail/service.py` | `async def asend_mail(subject: str, body: str, from_email: str &#124; None = None, to: Sequence[str] &#124; str &#124; None = None, cc: Sequence[str] &#124; str &#124; None = None, bcc: Sequence[str] &#124; str &#124; None = None, reply_to: str &#124; None = None, headers: dict[str, str] &#124; None = None, attachments: Sequence[tuple[str, bytes, str]] &#124; None = None, priority: int = 50, fail_silently: bool = False, **kwargs: Any) -> str &#124; None` | Send an email asynchronously (Aquilia-native API). |
| `configure` | `aquilia/mail/template/__init__.py` | `def configure(template_dirs: list[str] &#124; None = None) -> None` | Set template search directories (called at MailService startup). |
| `render_string` | `aquilia/mail/template/__init__.py` | `def render_string(template_text: str, context: dict[str, Any]) -> str` | Render an ATS template string with the given context. |
| `render_template` | `aquilia/mail/template/__init__.py` | `def render_template(template_name: str, context: dict[str, Any], *, template_dirs: list[str] &#124; None = None) -> str` | Render a named ATS template file with the given context. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `PROVIDER_TYPES` | `aquilia/mail/config.py` | `('smtp', 'ses', 'sendgrid', 'console', 'file')` |
| `_EMAIL_RE` | `aquilia/mail/message.py` | `re.compile("^[a-zA-Z0-9.!#$%&'*+/=?^_`{ &#124; }~-]+@[a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)*$")` |
| `_TAG_RE` | `aquilia/mail/message.py` | `re.compile('<[^>]+>')` |
| `_MULTI_WS_RE` | `aquilia/mail/message.py` | `re.compile('\\s+')` |
| `_SENDGRID_API_BASE` | `aquilia/mail/providers/sendgrid.py` | `'https://api.sendgrid.com'` |
| `_SEND_ENDPOINT` | `aquilia/mail/providers/sendgrid.py` | `'/v3/mail/send'` |
| `_SCOPES_ENDPOINT` | `aquilia/mail/providers/sendgrid.py` | `'/v3/scopes'` |
| `_THROTTLE_CODES` | `aquilia/mail/providers/ses.py` | `frozenset({'Throttling', 'ThrottlingException', 'TooManyRequestsException', 'LimitExceededException', 'MaxSendingRateExceeded'})` |
| `_PERMANENT_CODES` | `aquilia/mail/providers/ses.py` | `frozenset({'MessageRejected', 'MailFromDomainNotVerifiedException', 'AccountSendingPausedException', 'ConfigurationSetDoesNotExistException', 'InvalidParameterV` |
| `_TRANSIENT_CODES` | `aquilia/mail/providers/smtp.py` | `frozenset({421, 450, 451, 452})` |
| `_PERMANENT_CODES` | `aquilia/mail/providers/smtp.py` | `frozenset({550, 551, 552, 553, 554, 555})` |
| `_EXPR_RE` | `aquilia/mail/template/__init__.py` | `re.compile('<<\\s*(.+?)\\s*>>')` |

## Detailed Classes And Methods

### Class: `ProviderConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for a single mail provider configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `TextFacet(max_length=100, required=True, help_text='Unique provider name')` |
| `type` |  | `ChoiceFacet(choices=PROVIDER_TYPES, required=True, help_text='Provider backend type')` |
| `priority` |  | `IntFacet(min_value=0, max_value=1000, default=50, required=False, help_text='Lower = preferred')` |
| `enabled` |  | `BoolFacet(default=True, required=False)` |
| `rate_limit_per_min` |  | `IntFacet(min_value=0, default=600, required=False, help_text='Max messages per minute for this provider')` |
| `config` |  | `DictFacet(default=dict, required=False, help_text='Extra provider-specific options')` |
| `host` |  | `TextFacet(default=None, required=False, allow_null=True)` |
| `port` |  | `IntFacet(min_value=1, max_value=65535, default=None, required=False, allow_null=True)` |
| `username` |  | `TextFacet(default=None, required=False, allow_null=True)` |
| `password` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True)` |
| `use_tls` |  | `BoolFacet(default=True, required=False)` |
| `use_ssl` |  | `BoolFacet(default=False, required=False)` |
| `timeout` |  | `FloatFacet(min_value=0.1, max_value=300.0, default=30.0, required=False)` |
| `auth` |  | `DictFacet(default=None, required=False, allow_null=True, help_text='Nested MailAuthConfig dict -- preferred over flat us` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, attrs: dict) -> dict` |  | Cross-field validation: SMTP needs host. |

### Class: `MailAuthConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for mail provider authentication credentials.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `METHOD_CHOICES` |  | `('plain', 'oauth2', 'api_key', 'ntlm', 'none')` |
| `method` |  | `ChoiceFacet(choices=METHOD_CHOICES, default='plain', required=False, help_text='Authentication mechanism')` |
| `username` |  | `TextFacet(default=None, required=False, allow_null=True, help_text='SMTP username or account identifier')` |
| `password` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True, help_text='SMTP password or app-specific passw` |
| `domain` |  | `TextFacet(default=None, required=False, allow_null=True, help_text='Windows domain for NTLM authentication')` |
| `api_key` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True, help_text='API key for API-key-authenticated p` |
| `api_key_env` |  | `TextFacet(default=None, required=False, allow_null=True, help_text='Environment variable name that holds the API key')` |
| `aws_access_key_id` |  | `TextFacet(default=None, required=False, allow_null=True, help_text='AWS access key ID for SES')` |
| `aws_secret_access_key` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True, help_text='AWS secret access key for SES (writ` |
| `aws_region` |  | `TextFacet(default=None, required=False, allow_null=True, help_text="AWS region for SES (e.g. 'us-east-1')")` |
| `aws_session_token` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True, help_text='Temporary AWS session token (STS / ` |
| `access_token` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True, help_text='OAuth2 bearer access token (write-o` |
| `refresh_token` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True, help_text='OAuth2 refresh token for auto-renew` |
| `token_url` |  | `TextFacet(default=None, required=False, allow_null=True, help_text='OAuth2 token endpoint URL')` |
| `client_id` |  | `TextFacet(default=None, required=False, allow_null=True, help_text='OAuth2 client ID')` |
| `client_secret` |  | `TextFacet(default=None, required=False, allow_null=True, write_only=True, help_text='OAuth2 client secret (write-only)')` |
| `scope` |  | `TextFacet(default=None, required=False, allow_null=True, help_text='OAuth2 scope string (space-separated)')` |
| `token_expiry` |  | `IntFacet(default=None, required=False, allow_null=True, help_text='Unix timestamp when the current access token expires'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, attrs: dict) -> dict` |  | Cross-field validation for authentication credentials. |

### Class: `RetryConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for retry / backoff configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `max_attempts` |  | `IntFacet(min_value=0, max_value=100, default=5, required=False)` |
| `base_delay` |  | `FloatFacet(min_value=0.0, max_value=60.0, default=1.0, required=False)` |
| `max_delay` |  | `FloatFacet(min_value=0.0, default=3600.0, required=False)` |
| `jitter` |  | `BoolFacet(default=True, required=False)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, attrs: dict) -> dict` |  | Ensure base_delay <= max_delay. |

### Class: `RateLimitConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for global and per-domain rate-limiting.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `global_per_minute` |  | `IntFacet(min_value=0, default=1000, required=False)` |
| `per_domain_per_minute` |  | `IntFacet(min_value=0, default=100, required=False)` |
| `per_provider_per_minute` |  | `IntFacet(min_value=0, default=None, required=False, allow_null=True)` |

### Class: `SecurityConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for security / deliverability settings.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `dkim_enabled` |  | `BoolFacet(default=False, required=False)` |
| `dkim_domain` |  | `TextFacet(default=None, required=False, allow_null=True)` |
| `dkim_selector` |  | `TextFacet(max_length=100, default='aquilia', required=False)` |
| `dkim_private_key_path` |  | `TextFacet(default=None, required=False, allow_null=True)` |
| `dkim_private_key_env` |  | `TextFacet(default='AQUILIA_DKIM_PRIVATE_KEY', required=False)` |
| `require_tls` |  | `BoolFacet(default=True, required=False)` |
| `allowed_from_domains` |  | `ListFacet(child=TextFacet(max_length=253), default=list, required=False)` |
| `pii_redaction_enabled` |  | `BoolFacet(default=False, required=False)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, attrs: dict) -> dict` |  | DKIM domain required when DKIM is enabled. |

### Class: `TemplateConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for ATS template engine configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `template_dirs` |  | `ListFacet(child=TextFacet(max_length=500), default=lambda: ['mail_templates'], required=False)` |
| `auto_escape` |  | `BoolFacet(default=True, required=False)` |
| `cache_compiled` |  | `BoolFacet(default=True, required=False)` |
| `strict_mode` |  | `BoolFacet(default=False, required=False)` |

### Class: `QueueConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for queue / storage settings.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `db_url` |  | `TextFacet(default='', required=False, help_text='Empty = use app main database')` |
| `batch_size` |  | `IntFacet(min_value=1, max_value=10000, default=50, required=False)` |
| `poll_interval` |  | `FloatFacet(min_value=0.1, max_value=60.0, default=1.0, required=False)` |
| `dedupe_window_seconds` |  | `IntFacet(min_value=0, default=3600, required=False)` |
| `retention_days` |  | `IntFacet(min_value=1, max_value=3650, default=30, required=False)` |

### Class: `ProviderConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated provider config.

### Class: `RetryConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated retry config.

### Class: `RateLimitConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated rate-limit config.

### Class: `SecurityConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated security config.

### Class: `TemplateConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated template config.

### Class: `QueueConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated queue config.

### Class: `MailAuthConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for validated mail authentication credentials.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `plain` | `def plain(cls, username: str, password: str) -> MailAuthConfig` | classmethod | Convenience constructor for plain SMTP auth. |
| `api_key` | `def api_key(cls, key: Optional[str] = None, *, env: Optional[str] = None) -> MailAuthConfig` | classmethod | Convenience constructor for API-key-based auth (SendGrid, etc.). |
| `aws_ses` | `def aws_ses(cls, access_key_id: Optional[str] = None, secret_access_key: Optional[str] = None, region: str = 'us-east-1', session_token: Optional[str] = None) -> MailAuthConfig` | classmethod | Convenience constructor for AWS SES credentials. |
| `oauth2` | `def oauth2(cls, client_id: str, client_secret: str, token_url: str, scope: Optional[str] = None, access_token: Optional[str] = None, refresh_token: Optional[str] = None) -> MailAuthConfig` | classmethod | Convenience constructor for OAuth2 auth. |
| `anonymous` | `def anonymous(cls) -> MailAuthConfig` | classmethod | Convenience constructor for unauthenticated relay. |

### Class: `MailConfig`

- Source: `aquilia/mail/config.py`
- Bases: `object`
- Summary: Top-level mail configuration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Method. |
| `from_dict` | `def from_dict(cls, data: Dict[str, Any]) -> MailConfig` | classmethod | Build MailConfig from a configuration dictionary. |
| `development` | `def development(cls) -> MailConfig` | classmethod | Pre-configured for local development (console backend). |
| `production` | `def production(cls, default_from: str, **overrides: Any) -> MailConfig` | classmethod | Pre-configured for production with sensible defaults. |

### Class: `MailConfigProvider`

- Source: `aquilia/mail/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: DI provider that builds and validates MailConfig from workspace data.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> Any` |  | Provide validated MailConfig instance. |

### Class: `MailServiceProvider`

- Source: `aquilia/mail/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: DI provider for MailService -- the central mail orchestrator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> Any` |  | Provide MailService instance. |

### Class: `MailProviderRegistry`

- Source: `aquilia/mail/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Auto-discovers IMailProvider implementations using Aquilia's

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_scan_package` | `def add_scan_package(self, package: str) -> None` |  | Add a package to scan for IMailProvider implementations. |
| `discover` | `def discover(self) -> dict[str, type]` |  | Scan configured packages for IMailProvider implementations. |
| `get_provider_class` | `def get_provider_class(self, provider_type: str) -> type &#124; None` |  | Get a discovered provider class by type name. |
| `list_types` | `def list_types(self) -> list[str]` |  | List all discovered provider type names. |

### Class: `EnvelopeStatus`

- Source: `aquilia/mail/envelope.py`
- Bases: `str, Enum`
- Summary: Lifecycle status of an envelope.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `QUEUED` |  | `'queued'` |
| `SENDING` |  | `'sending'` |
| `SENT` |  | `'sent'` |
| `FAILED` |  | `'failed'` |
| `BOUNCED` |  | `'bounced'` |
| `CANCELLED` |  | `'cancelled'` |

### Class: `Priority`

- Source: `aquilia/mail/envelope.py`
- Bases: `int, Enum`
- Summary: Named priority levels.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CRITICAL` |  | `0` |
| `HIGH` |  | `25` |
| `NORMAL` |  | `50` |
| `LOW` |  | `75` |
| `BULK` |  | `100` |

### Class: `Attachment`

- Source: `aquilia/mail/envelope.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Attachment metadata (content stored separately in blob store).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `filename` | `str` |  |
| `content_type` | `str` |  |
| `digest` | `str` |  |
| `size` | `int` |  |
| `inline` | `bool` | `False` |
| `content_id` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict` |  | Method. |
| `from_dict` | `def from_dict(cls, data: dict) -> Attachment` | classmethod | Method. |

### Class: `MailEnvelope`

- Source: `aquilia/mail/envelope.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable mail envelope -- the unit of work in the mail pipeline.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` | `field(default_factory=lambda: str(uuid.uuid4()))` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `status` | `EnvelopeStatus` | `EnvelopeStatus.QUEUED` |
| `priority` | `int` | `Priority.NORMAL.value` |
| `from_email` | `str` | `''` |
| `to` | `list[str]` | `field(default_factory=list)` |
| `cc` | `list[str]` | `field(default_factory=list)` |
| `bcc` | `list[str]` | `field(default_factory=list)` |
| `reply_to` | `str &#124; None` | `None` |
| `subject` | `str` | `''` |
| `body_text` | `str` | `''` |
| `body_html` | `str &#124; None` | `None` |
| `headers` | `dict[str, str]` | `field(default_factory=dict)` |
| `template_name` | `str &#124; None` | `None` |
| `template_context` | `dict[str, Any] &#124; None` | `None` |
| `attachments` | `list[Attachment]` | `field(default_factory=list)` |
| `attempts` | `int` | `0` |
| `max_attempts` | `int` | `5` |
| `last_attempt_at` | `datetime &#124; None` | `None` |
| `next_attempt_at` | `datetime &#124; None` | `None` |
| `provider_name` | `str &#124; None` | `None` |
| `provider_message_id` | `str &#124; None` | `None` |
| `idempotency_key` | `str &#124; None` | `None` |
| `digest` | `str` | `''` |
| `tenant_id` | `str &#124; None` | `None` |
| `trace_id` | `str &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `error_message` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compute_digest` | `def compute_digest(self) -> str` |  | Compute content-based SHA-256 digest for deduplication. |
| `all_recipients` | `def all_recipients(self) -> list[str]` |  | All unique recipient addresses (to + cc + bcc). |
| `recipient_domains` | `def recipient_domains(self) -> set[str]` |  | Unique set of recipient domains. |
| `to_dict` | `def to_dict(self) -> dict` |  | Serialize to dictionary (for DB storage / JSON). |
| `from_dict` | `def from_dict(cls, data: dict) -> MailEnvelope` | classmethod | Deserialize from dictionary. |

### Class: `MailFault`

- Source: `aquilia/mail/faults.py`
- Bases: `Fault`
- Summary: Base class for all mail-subsystem faults.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.MAIL` |
| `severity` |  | `Severity.ERROR` |

### Class: `MailSendFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Provider-level send failure (transient or permanent).

### Class: `MailTemplateFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Template parse, compile, or render error.

### Class: `MailConfigFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Mail configuration error (missing provider, bad credentials, etc.).

### Class: `MailSuppressedFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Recipient is on the suppression list.

### Class: `MailRateLimitFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Rate limit exceeded for provider or domain.

### Class: `MailValidationFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Invalid email address, missing fields, or envelope validation error.

### Class: `EmailMessage`

- Source: `aquilia/mail/message.py`
- Bases: `object`
- Summary: A single email message -- the primary API for sending mail.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `attach` | `def attach(self, filename: str, content: bytes, content_type: str = 'application/octet-stream') -> EmailMessage` |  | Attach raw bytes. |
| `attach_file` | `def attach_file(self, path: str &#124; Path, content_type: str &#124; None = None) -> EmailMessage` |  | Attach a file from disk. |
| `build_envelope` | `def build_envelope(self, default_from: str = 'noreply@localhost') -> tuple[MailEnvelope, dict[str, bytes]]` |  | Build a MailEnvelope + blob map ready for storage and dispatch. |
| `send` | `def send(self, fail_silently: bool = False) -> str &#124; None` |  | Send synchronously. |
| `asend` | `async def asend(self, fail_silently: bool = False) -> str &#124; None` |  | Send asynchronously. |

### Class: `EmailMultiAlternatives`

- Source: `aquilia/mail/message.py`
- Bases: `EmailMessage`
- Summary: Email with multiple content alternatives (e.g., plain text + HTML).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `attach_alternative` | `def attach_alternative(self, content: str, mimetype: str = 'text/html') -> EmailMultiAlternatives` |  | Add an alternative content representation. |

### Class: `TemplateMessage`

- Source: `aquilia/mail/message.py`
- Bases: `EmailMessage`
- Summary: Email rendered from an Aquilia Template Syntax (ATS) template.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `build_envelope` | `def build_envelope(self, default_from: str = 'noreply@localhost') -> tuple[MailEnvelope, dict[str, bytes]]` |  | Build envelope, rendering the template first. |

### Class: `ProviderResultStatus`

- Source: `aquilia/mail/providers/__init__.py`
- Bases: `str, Enum`
- Summary: Granular result from a provider send attempt.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SUCCESS` |  | `'success'` |
| `TRANSIENT_FAILURE` |  | `'transient_failure'` |
| `PERMANENT_FAILURE` |  | `'permanent_failure'` |
| `RATE_LIMITED` |  | `'rate_limited'` |

### Class: `ProviderResult`

- Source: `aquilia/mail/providers/__init__.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result returned by IMailProvider.send().

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `status` | `ProviderResultStatus` |  |
| `provider_message_id` | `str &#124; None` | `None` |
| `error_message` | `str &#124; None` | `None` |
| `raw_response` | `dict[str, Any] &#124; None` | `None` |
| `retry_after` | `float &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_success` | `def is_success(self) -> bool` | property | Method. |
| `should_retry` | `def should_retry(self) -> bool` | property | Method. |

### Class: `IMailProvider`

- Source: `aquilia/mail/providers/__init__.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Interface that all mail provider backends must implement.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `supports_batching` | `bool` |  |
| `max_batch_size` | `int` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `send` | `async def send(self, envelope: Any) -> ProviderResult` |  | Send a single envelope. |
| `send_batch` | `async def send_batch(self, envelopes: list[Any]) -> list[ProviderResult]` |  | Send a batch of envelopes (optional; default falls back to sequential). |
| `health_check` | `async def health_check(self) -> bool` |  | Check if the provider is reachable and healthy. |
| `initialize` | `async def initialize(self) -> None` |  | Initialize connections / sessions (called at startup). |
| `shutdown` | `async def shutdown(self) -> None` |  | Close connections / sessions (called at shutdown). |

### Class: `ConsoleProvider`

- Source: `aquilia/mail/providers/console.py`
- Bases: `object`
- Summary: Provider that logs emails to the console instead of sending them.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` | `'console'` |
| `priority` | `int` | `100` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `100` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |
| `send` | `async def send(self, envelope: MailEnvelope) -> ProviderResult` |  | Print the envelope to the console. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope]) -> list[ProviderResult]` |  | Send a batch of envelopes (sequentially via console). |
| `health_check` | `async def health_check(self) -> bool` |  | Console provider is always healthy. |

### Class: `FileProvider`

- Source: `aquilia/mail/providers/file.py`
- Bases: `object`
- Summary: Mail provider that writes emails to .eml files on disk.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `provider_type` | `str` | `'file'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `1000` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Create the output directory. |
| `shutdown` | `async def shutdown(self) -> None` |  | No cleanup needed for file provider. |
| `send` | `async def send(self, envelope: MailEnvelope) -> ProviderResult` |  | Write the envelope as an .eml file to disk. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope]) -> list[ProviderResult]` |  | Write a batch of envelopes to disk. |
| `health_check` | `async def health_check(self) -> bool` |  | Check that the output directory exists and is writable. |
| `list_files` | `def list_files(self) -> list[Path]` |  | List all .eml files in the output directory (sorted by time). |
| `read_last` | `def read_last(self) -> str &#124; None` |  | Read the most recent .eml file (useful for testing). |
| `clear` | `def clear(self) -> int` |  | Remove all .eml files and the index (useful for testing). |

### Class: `SendGridProvider`

- Source: `aquilia/mail/providers/sendgrid.py`
- Bases: `object`
- Summary: Async SendGrid mail provider using the v3 Web API.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `provider_type` | `str` | `'sendgrid'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `1000` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Initialize the httpx async client. |
| `shutdown` | `async def shutdown(self) -> None` |  | Close the httpx client. |
| `send` | `async def send(self, envelope: MailEnvelope) -> ProviderResult` |  | Send a single envelope via SendGrid v3 API. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope]) -> list[ProviderResult]` |  | Send batch of envelopes. |
| `health_check` | `async def health_check(self) -> bool` |  | Check SendGrid API access via scopes endpoint. |

### Class: `SESProvider`

- Source: `aquilia/mail/providers/ses.py`
- Bases: `object`
- Summary: Async AWS SES mail provider.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `provider_type` | `str` | `'ses'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `50` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Initialize the SES client (aiobotocore or boto3 fallback). |
| `shutdown` | `async def shutdown(self) -> None` |  | Close the SES client. |
| `send` | `async def send(self, envelope: MailEnvelope) -> ProviderResult` |  | Send a single envelope via SES. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope]) -> list[ProviderResult]` |  | Send batch via SES (falls back to sequential for raw mode). |
| `health_check` | `async def health_check(self) -> bool` |  | Check SES account status via GetAccount. |

### Class: `SMTPProvider`

- Source: `aquilia/mail/providers/smtp.py`
- Bases: `object`
- Summary: Async SMTP mail provider backed by aiosmtplib.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `provider_type` | `str` | `'smtp'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `100` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Pre-warm the connection pool. |
| `shutdown` | `async def shutdown(self) -> None` |  | Drain and close all pooled connections. |
| `send` | `async def send(self, envelope: MailEnvelope) -> ProviderResult` |  | Send a single envelope via SMTP. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope]) -> list[ProviderResult]` |  | Send a batch of envelopes, reusing a single connection. |
| `health_check` | `async def health_check(self) -> bool` |  | Check SMTP connectivity via NOOP. |

### Class: `MailService`

- Source: `aquilia/mail/service.py`
- Bases: `object`
- Decorators: `service`
- Summary: Central mail service -- owns the pipeline from message to delivery.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_startup` | `async def on_startup(self) -> None` |  | Initialize providers, store, dispatcher. |
| `on_shutdown` | `async def on_shutdown(self) -> None` |  | Shutdown providers and flush queue. |
| `send_message` | `async def send_message(self, message: Any) -> str` |  | Accept an EmailMessage, build envelope, dispatch. |
| `get_provider_names` | `def get_provider_names(self) -> list[str]` |  | Return names of registered providers. |
| `is_healthy` | `def is_healthy(self) -> bool` |  | Quick health check. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `create_mail_config` | `aquilia/mail/di_providers.py` | `def create_mail_config(config_data: dict[str, Any] &#124; None = None) -> Any` | Factory that creates a validated MailConfig. |
| `create_mail_service` | `aquilia/mail/di_providers.py` | `def create_mail_service(config: Any &#124; None = None) -> Any` | Factory that creates a MailService from config. |
| `register_mail_providers` | `aquilia/mail/di_providers.py` | `def register_mail_providers(container: Container, config_data: dict[str, Any] &#124; None = None, discover_providers: bool = True, extra_scan_packages: list[str] &#124; None = None) -> Any` | Register all mail DI providers into a container. |
| `set_mail_service` | `aquilia/mail/service.py` | `def set_mail_service(svc: MailService &#124; None) -> None` | Install a MailService as the module-level singleton (or None to reset). |
| `send_mail` | `aquilia/mail/service.py` | `def send_mail(subject: str, body: str, from_email: str &#124; None = None, to: Sequence[str] &#124; str &#124; None = None, cc: Sequence[str] &#124; str &#124; None = None, bcc: Sequence[str] &#124; str &#124; None = None, reply_to: str &#124; None = None, headers: dict[str, str] &#124; None = None, attachments: Sequence[tuple[str, bytes, str]] &#124; None = None, priority: int = 50, fail_silently: bool = False, **kwargs: Any) -> str &#124; None` | Send an email synchronously. |
| `asend_mail` | `aquilia/mail/service.py` | `async def asend_mail(subject: str, body: str, from_email: str &#124; None = None, to: Sequence[str] &#124; str &#124; None = None, cc: Sequence[str] &#124; str &#124; None = None, bcc: Sequence[str] &#124; str &#124; None = None, reply_to: str &#124; None = None, headers: dict[str, str] &#124; None = None, attachments: Sequence[tuple[str, bytes, str]] &#124; None = None, priority: int = 50, fail_silently: bool = False, **kwargs: Any) -> str &#124; None` | Send an email asynchronously (Aquilia-native API). |
| `configure` | `aquilia/mail/template/__init__.py` | `def configure(template_dirs: list[str] &#124; None = None) -> None` | Set template search directories (called at MailService startup). |
| `render_string` | `aquilia/mail/template/__init__.py` | `def render_string(template_text: str, context: dict[str, Any]) -> str` | Render an ATS template string with the given context. |
| `render_template` | `aquilia/mail/template/__init__.py` | `def render_template(template_name: str, context: dict[str, Any], *, template_dirs: list[str] &#124; None = None) -> str` | Render a named ATS template file with the given context. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `PROVIDER_TYPES` | `aquilia/mail/config.py` | `('smtp', 'ses', 'sendgrid', 'console', 'file')` |
| `_EMAIL_RE` | `aquilia/mail/message.py` | `re.compile("^[a-zA-Z0-9.!#$%&'*+/=?^_`{ &#124; }~-]+@[a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)*$")` |
| `_TAG_RE` | `aquilia/mail/message.py` | `re.compile('<[^>]+>')` |
| `_MULTI_WS_RE` | `aquilia/mail/message.py` | `re.compile('\\s+')` |
| `_SENDGRID_API_BASE` | `aquilia/mail/providers/sendgrid.py` | `'https://api.sendgrid.com'` |
| `_SEND_ENDPOINT` | `aquilia/mail/providers/sendgrid.py` | `'/v3/mail/send'` |
| `_SCOPES_ENDPOINT` | `aquilia/mail/providers/sendgrid.py` | `'/v3/scopes'` |
| `_THROTTLE_CODES` | `aquilia/mail/providers/ses.py` | `frozenset({'Throttling', 'ThrottlingException', 'TooManyRequestsException', 'LimitExceededException', 'MaxSendingRateExceeded'})` |
| `_PERMANENT_CODES` | `aquilia/mail/providers/ses.py` | `frozenset({'MessageRejected', 'MailFromDomainNotVerifiedException', 'AccountSendingPausedException', 'ConfigurationSetDoesNotExistException', 'InvalidParameterV` |
| `_TRANSIENT_CODES` | `aquilia/mail/providers/smtp.py` | `frozenset({421, 450, 451, 452})` |
| `_PERMANENT_CODES` | `aquilia/mail/providers/smtp.py` | `frozenset({550, 551, 552, 553, 554, 555})` |
| `_EXPR_RE` | `aquilia/mail/template/__init__.py` | `re.compile('<<\\s*(.+?)\\s*>>')` |
