# Mail API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/mail/__init__.py` | 156 | 0 | 0 | AquilaMail -- Production-ready async mail subsystem for Aquilia. |
| `aquilia/mail/config.py` | 819 | 15 | 0 | AquilaMail Configuration -- Serializer-based, DI-aware mail configuration. |
| `aquilia/mail/di_providers.py` | 298 | 3 | 3 | AquilaMail -- DI Providers |
| `aquilia/mail/envelope.py` | 261 | 4 | 0 | AquilaMail Envelope -- The internal representation of a mail message. |
| `aquilia/mail/faults.py` | 179 | 7 | 0 | AquilaMail Faults -- Structured, typed fault definitions for the mail subsystem. |
| `aquilia/mail/message.py` | 368 | 3 | 0 | AquilaMail Messages -- Developer-facing message classes. |
| `aquilia/mail/providers/__init__.py` | 129 | 3 | 0 | AquilaMail Provider Interface -- Protocol + result types for mail providers. |
| `aquilia/mail/providers/console.py` | 86 | 1 | 0 | Console Provider -- prints emails to stdout/logger (development). |
| `aquilia/mail/providers/file.py` | 351 | 1 | 0 | File Provider -- Writes emails to .eml files on disk. |
| `aquilia/mail/providers/sendgrid.py` | 396 | 1 | 0 | SendGrid Provider -- Async SendGrid Web API v3 delivery via httpx. |
| `aquilia/mail/providers/ses.py` | 440 | 1 | 0 | AWS SES Provider -- Async Amazon Simple Email Service delivery. |
| `aquilia/mail/providers/smtp.py` | 536 | 1 | 0 | SMTP Provider -- Production-grade async SMTP delivery via aiosmtplib. |
| `aquilia/mail/service.py` | 433 | 1 | 3 | AquilaMail Service -- Main orchestrator for the mail subsystem. |
| `aquilia/mail/template/__init__.py` | 147 | 0 | 3 | AquilaMail ATS (Aquilia Template Syntax) -- Stub module. |

## Public Exports

`ConsoleProvider`, `EmailMessage`, `EmailMultiAlternatives`, `EnvelopeStatus`, `FileProvider`, `IMailProvider`, `MailConfig`, `MailConfigFault`, `MailConfigProvider`, `MailEnvelope`, `MailFault`, `MailProviderRegistry`, `MailRateLimitFault`, `MailSendFault`, `MailServiceProvider`, `MailSuppressedFault`, `MailTemplateFault`, `MailValidationFault`, `Priority`, `ProviderConfig`, `ProviderConfigBlueprint`, `ProviderResult`, `ProviderResultStatus`, `QueueConfig`, `QueueConfigBlueprint`, `RateLimitConfig`, `RateLimitConfigBlueprint`, `RetryConfig`, `RetryConfigBlueprint`, `SESProvider`, `SMTPProvider`, `SecurityConfig`, `SecurityConfigBlueprint`, `SendGridProvider`, `TemplateConfig`, `TemplateConfigBlueprint`, `TemplateMessage`, `asend_mail`, `register_mail_providers`, `send_mail`

## Public Class Summary

| Class | Source | Bases | Summary |
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
| `MailProviderRegistry` | `aquilia/mail/di_providers.py` | object | Auto-discovers IMailProvider implementations using Aquilia's PackageScanner (discovery system). |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `create_mail_config` | `aquilia/mail/di_providers.py` | `def create_mail_config(config_data: dict[str, Any] \| None=None)` | Factory that creates a validated MailConfig. |
| `create_mail_service` | `aquilia/mail/di_providers.py` | `def create_mail_service(config: Any \| None=None)` | Factory that creates a MailService from config. |
| `register_mail_providers` | `aquilia/mail/di_providers.py` | `def register_mail_providers(container: Container, config_data: dict[str, Any] \| None=None, discover_providers: bool=True, extra_scan_packages: list[str] \| None=None)` | Register all mail DI providers into a container. |
| `set_mail_service` | `aquilia/mail/service.py` | `def set_mail_service(svc: MailService \| None)` | Install a MailService as the module-level singleton (or None to reset). |
| `send_mail` | `aquilia/mail/service.py` | `def send_mail(subject: str, body: str, from_email: str \| None=None, to: Sequence[str] \| str \| None=None, cc: Sequence[str] \| str \| None=None, bcc: Sequence[str] \| str \| None=None, reply_to: str \| None=None, headers: dict[str, str] \| None=None, attachments: Sequence[tuple[str, bytes, str]] \| None=None, priority: int=50, fail_silently: bool=False, **kwargs: Any)` | Send an email synchronously. |
| `asend_mail` | `aquilia/mail/service.py` | `async def asend_mail(subject: str, body: str, from_email: str \| None=None, to: Sequence[str] \| str \| None=None, cc: Sequence[str] \| str \| None=None, bcc: Sequence[str] \| str \| None=None, reply_to: str \| None=None, headers: dict[str, str] \| None=None, attachments: Sequence[tuple[str, bytes, str]] \| None=None, priority: int=50, fail_silently: bool=False, **kwargs: Any)` | Send an email asynchronously (Aquilia-native API). |
| `configure` | `aquilia/mail/template/__init__.py` | `def configure(template_dirs: list[str] \| None=None)` | Set template search directories (called at MailService startup). |
| `render_string` | `aquilia/mail/template/__init__.py` | `def render_string(template_text: str, context: dict[str, Any])` | Render an ATS template string with the given context. |
| `render_template` | `aquilia/mail/template/__init__.py` | `def render_template(template_name: str, context: dict[str, Any], *, template_dirs: list[str] \| None=None)` | Render a named ATS template file with the given context. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `PROVIDER_TYPES` | `aquilia/mail/config.py` | `('smtp', 'ses', 'sendgrid', 'console', 'file')` |
| `_EMAIL_RE` | `aquilia/mail/message.py` | `re.compile("^[a-zA-Z0-9.!#$%&'*+/=?^_`{\|}~-]+@[a-zA-Z0-9-]+(?:\\.[a-zA-Z0-9-]+)*$")` |
| `_TAG_RE` | `aquilia/mail/message.py` | `re.compile('<[^>]+>')` |
| `_MULTI_WS_RE` | `aquilia/mail/message.py` | `re.compile('\\s+')` |
| `_SENDGRID_API_BASE` | `aquilia/mail/providers/sendgrid.py` | `'https://api.sendgrid.com'` |
| `_SEND_ENDPOINT` | `aquilia/mail/providers/sendgrid.py` | `'/v3/mail/send'` |
| `_SCOPES_ENDPOINT` | `aquilia/mail/providers/sendgrid.py` | `'/v3/scopes'` |
| `_THROTTLE_CODES` | `aquilia/mail/providers/ses.py` | `frozenset({'Throttling', 'ThrottlingException', 'TooManyRequestsException', 'LimitExceededException', 'MaxSendingRateExceeded'})` |
| `_PERMANENT_CODES` | `aquilia/mail/providers/ses.py` | `frozenset({'MessageRejected', 'MailFromDomainNotVerifiedException', 'AccountSendingPausedException', 'ConfigurationSetDoesNotExistException', 'InvalidParameterValue'})` |
| `_TRANSIENT_CODES` | `aquilia/mail/providers/smtp.py` | `frozenset({421, 450, 451, 452})` |
| `_PERMANENT_CODES` | `aquilia/mail/providers/smtp.py` | `frozenset({550, 551, 552, 553, 554, 555})` |
| `_EXPR_RE` | `aquilia/mail/template/__init__.py` | `re.compile('<<\\s*(.+?)\\s*>>')` |

## Detailed Classes And Methods

### `ProviderConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for a single mail provider configuration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, attrs: dict)` | Cross-field validation: SMTP needs host. |

### `MailAuthConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for mail provider authentication credentials.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `METHOD_CHOICES` | `` | `('plain', 'oauth2', 'api_key', 'ntlm', 'none')` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, attrs: dict)` | Cross-field validation for authentication credentials. |

### `RetryConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for retry / backoff configuration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, attrs: dict)` | Ensure base_delay <= max_delay. |

### `RateLimitConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for global and per-domain rate-limiting.

### `SecurityConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for security / deliverability settings.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, attrs: dict)` | DKIM domain required when DKIM is enabled. |

### `TemplateConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for ATS template engine configuration.

### `QueueConfigBlueprint`

- Source: `aquilia/mail/config.py`
- Bases: `Blueprint`
- Summary: Blueprint for queue / storage settings.

### `ProviderConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated provider config.

### `RetryConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated retry config.

### `RateLimitConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated rate-limit config.

### `SecurityConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated security config.

### `TemplateConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated template config.

### `QueueConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for a validated queue config.

### `MailAuthConfig`

- Source: `aquilia/mail/config.py`
- Bases: `_ConfigObject`
- Summary: Attribute-access wrapper for validated mail authentication credentials.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `plain` | `def plain(cls, username: str, password: str)` | Convenience constructor for plain SMTP auth. |
| `api_key` | `def api_key(cls, key: Optional[str]=None, *, env: Optional[str]=None)` | Convenience constructor for API-key-based auth (SendGrid, etc.). |
| `aws_ses` | `def aws_ses(cls, access_key_id: Optional[str]=None, secret_access_key: Optional[str]=None, region: str='us-east-1', session_token: Optional[str]=None)` | Convenience constructor for AWS SES credentials. |
| `oauth2` | `def oauth2(cls, client_id: str, client_secret: str, token_url: str, scope: Optional[str]=None, access_token: Optional[str]=None, refresh_token: Optional[str]=None)` | Convenience constructor for OAuth2 auth. |
| `anonymous` | `def anonymous(cls)` | Convenience constructor for unauthenticated relay. |

### `MailConfig`

- Source: `aquilia/mail/config.py`
- Bases: `object`
- Summary: Top-level mail configuration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, data: Dict[str, Any])` | Build MailConfig from a configuration dictionary. |
| `development` | `def development(cls)` | Pre-configured for local development (console backend). |
| `production` | `def production(cls, default_from: str, **overrides: Any)` | Pre-configured for production with sensible defaults. |

### `MailConfigProvider`

- Source: `aquilia/mail/di_providers.py`
- Bases: `object`
- Summary: DI provider that builds and validates MailConfig from workspace data.
- Decorators: `service(scope='app', name='MailConfigProvider')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide validated MailConfig instance. |

### `MailServiceProvider`

- Source: `aquilia/mail/di_providers.py`
- Bases: `object`
- Summary: DI provider for MailService -- the central mail orchestrator.
- Decorators: `service(scope='app', name='MailServiceProvider')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide MailService instance. |

### `MailProviderRegistry`

- Source: `aquilia/mail/di_providers.py`
- Bases: `object`
- Summary: Auto-discovers IMailProvider implementations using Aquilia's PackageScanner (discovery system).
- Decorators: `service(scope='app', name='MailProviderRegistry')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_scan_package` | `def add_scan_package(self, package: str)` | Add a package to scan for IMailProvider implementations. |
| `discover` | `def discover(self)` | Scan configured packages for IMailProvider implementations. |
| `get_provider_class` | `def get_provider_class(self, provider_type: str)` | Get a discovered provider class by type name. |
| `list_types` | `def list_types(self)` | List all discovered provider type names. |

### `EnvelopeStatus`

- Source: `aquilia/mail/envelope.py`
- Bases: `str, Enum`
- Summary: Lifecycle status of an envelope.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `QUEUED` | `` | `'queued'` |
| `SENDING` | `` | `'sending'` |
| `SENT` | `` | `'sent'` |
| `FAILED` | `` | `'failed'` |
| `BOUNCED` | `` | `'bounced'` |
| `CANCELLED` | `` | `'cancelled'` |

### `Priority`

- Source: `aquilia/mail/envelope.py`
- Bases: `int, Enum`
- Summary: Named priority levels.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CRITICAL` | `` | `0` |
| `HIGH` | `` | `25` |
| `NORMAL` | `` | `50` |
| `LOW` | `` | `75` |
| `BULK` | `` | `100` |

### `Attachment`

- Source: `aquilia/mail/envelope.py`
- Bases: `object`
- Summary: Attachment metadata (content stored separately in blob store).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `filename` | `str` | `` |
| `content_type` | `str` | `` |
| `digest` | `str` | `` |
| `size` | `int` | `` |
| `inline` | `bool` | `False` |
| `content_id` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, data: dict)` |  |

### `MailEnvelope`

- Source: `aquilia/mail/envelope.py`
- Bases: `object`
- Summary: Immutable mail envelope -- the unit of work in the mail pipeline.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str` | `field(default_factory=lambda: str(uuid.uuid4()))` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `status` | `EnvelopeStatus` | `EnvelopeStatus.QUEUED` |
| `priority` | `int` | `Priority.NORMAL.value` |
| `from_email` | `str` | `''` |
| `to` | `list[str]` | `field(default_factory=list)` |
| `cc` | `list[str]` | `field(default_factory=list)` |
| `bcc` | `list[str]` | `field(default_factory=list)` |
| `reply_to` | `str \| None` | `None` |
| `subject` | `str` | `''` |
| `body_text` | `str` | `''` |
| `body_html` | `str \| None` | `None` |
| `headers` | `dict[str, str]` | `field(default_factory=dict)` |
| `template_name` | `str \| None` | `None` |
| `template_context` | `dict[str, Any] \| None` | `None` |
| `attachments` | `list[Attachment]` | `field(default_factory=list)` |
| `attempts` | `int` | `0` |
| `max_attempts` | `int` | `5` |
| `last_attempt_at` | `datetime \| None` | `None` |
| `next_attempt_at` | `datetime \| None` | `None` |
| `provider_name` | `str \| None` | `None` |
| `provider_message_id` | `str \| None` | `None` |
| `idempotency_key` | `str \| None` | `None` |
| `digest` | `str` | `''` |
| `tenant_id` | `str \| None` | `None` |
| `trace_id` | `str \| None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `error_message` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compute_digest` | `def compute_digest(self)` | Compute content-based SHA-256 digest for deduplication. |
| `all_recipients` | `def all_recipients(self)` | All unique recipient addresses (to + cc + bcc). |
| `recipient_domains` | `def recipient_domains(self)` | Unique set of recipient domains. |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary (for DB storage / JSON). |
| `from_dict` | `def from_dict(cls, data: dict)` | Deserialize from dictionary. |

### `MailFault`

- Source: `aquilia/mail/faults.py`
- Bases: `Fault`
- Summary: Base class for all mail-subsystem faults.

### `MailSendFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Provider-level send failure (transient or permanent).

### `MailTemplateFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Template parse, compile, or render error.

### `MailConfigFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Mail configuration error (missing provider, bad credentials, etc.).

### `MailSuppressedFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Recipient is on the suppression list.

### `MailRateLimitFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Rate limit exceeded for provider or domain.

### `MailValidationFault`

- Source: `aquilia/mail/faults.py`
- Bases: `MailFault`
- Summary: Invalid email address, missing fields, or envelope validation error.

### `EmailMessage`

- Source: `aquilia/mail/message.py`
- Bases: `object`
- Summary: A single email message -- the primary API for sending mail.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `attach` | `def attach(self, filename: str, content: bytes, content_type: str='application/octet-stream')` | Attach raw bytes. |
| `attach_file` | `def attach_file(self, path: str \| Path, content_type: str \| None=None)` | Attach a file from disk. |
| `build_envelope` | `def build_envelope(self, default_from: str='noreply@localhost')` | Build a MailEnvelope + blob map ready for storage and dispatch. |
| `send` | `def send(self, fail_silently: bool=False)` | Send synchronously. |
| `asend` | `async def asend(self, fail_silently: bool=False)` | Send asynchronously. |

### `EmailMultiAlternatives`

- Source: `aquilia/mail/message.py`
- Bases: `EmailMessage`
- Summary: Email with multiple content alternatives (e.g., plain text + HTML).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `attach_alternative` | `def attach_alternative(self, content: str, mimetype: str='text/html')` | Add an alternative content representation. |

### `TemplateMessage`

- Source: `aquilia/mail/message.py`
- Bases: `EmailMessage`
- Summary: Email rendered from an Aquilia Template Syntax (ATS) template.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build_envelope` | `def build_envelope(self, default_from: str='noreply@localhost')` | Build envelope, rendering the template first. |

### `ProviderResultStatus`

- Source: `aquilia/mail/providers/__init__.py`
- Bases: `str, Enum`
- Summary: Granular result from a provider send attempt.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SUCCESS` | `` | `'success'` |
| `TRANSIENT_FAILURE` | `` | `'transient_failure'` |
| `PERMANENT_FAILURE` | `` | `'permanent_failure'` |
| `RATE_LIMITED` | `` | `'rate_limited'` |

### `ProviderResult`

- Source: `aquilia/mail/providers/__init__.py`
- Bases: `object`
- Summary: Result returned by IMailProvider.send().
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `status` | `ProviderResultStatus` | `` |
| `provider_message_id` | `str \| None` | `None` |
| `error_message` | `str \| None` | `None` |
| `raw_response` | `dict[str, Any] \| None` | `None` |
| `retry_after` | `float \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_success` | `def is_success(self)` |  |
| `should_retry` | `def should_retry(self)` |  |

### `IMailProvider`

- Source: `aquilia/mail/providers/__init__.py`
- Bases: `Protocol`
- Summary: Interface that all mail provider backends must implement.
- Decorators: `runtime_checkable`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `supports_batching` | `bool` | `` |
| `max_batch_size` | `int` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `send` | `async def send(self, envelope: Any)` | Send a single envelope. |
| `send_batch` | `async def send_batch(self, envelopes: list[Any])` | Send a batch of envelopes (optional; default falls back to sequential). |
| `health_check` | `async def health_check(self)` | Check if the provider is reachable and healthy. |
| `initialize` | `async def initialize(self)` | Initialize connections / sessions (called at startup). |
| `shutdown` | `async def shutdown(self)` | Close connections / sessions (called at shutdown). |

### `ConsoleProvider`

- Source: `aquilia/mail/providers/console.py`
- Bases: `object`
- Summary: Provider that logs emails to the console instead of sending them.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `'console'` |
| `priority` | `int` | `100` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `100` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` |  |
| `shutdown` | `async def shutdown(self)` |  |
| `send` | `async def send(self, envelope: MailEnvelope)` | Print the envelope to the console. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope])` | Send a batch of envelopes (sequentially via console). |
| `health_check` | `async def health_check(self)` | Console provider is always healthy. |

### `FileProvider`

- Source: `aquilia/mail/providers/file.py`
- Bases: `object`
- Summary: Mail provider that writes emails to .eml files on disk.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `provider_type` | `str` | `'file'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `1000` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Create the output directory. |
| `shutdown` | `async def shutdown(self)` | No cleanup needed for file provider. |
| `send` | `async def send(self, envelope: MailEnvelope)` | Write the envelope as an .eml file to disk. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope])` | Write a batch of envelopes to disk. |
| `health_check` | `async def health_check(self)` | Check that the output directory exists and is writable. |
| `list_files` | `def list_files(self)` | List all .eml files in the output directory (sorted by time). |
| `read_last` | `def read_last(self)` | Read the most recent .eml file (useful for testing). |
| `clear` | `def clear(self)` | Remove all .eml files and the index (useful for testing). |

### `SendGridProvider`

- Source: `aquilia/mail/providers/sendgrid.py`
- Bases: `object`
- Summary: Async SendGrid mail provider using the v3 Web API.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `provider_type` | `str` | `'sendgrid'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `1000` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize the httpx async client. |
| `shutdown` | `async def shutdown(self)` | Close the httpx client. |
| `send` | `async def send(self, envelope: MailEnvelope)` | Send a single envelope via SendGrid v3 API. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope])` | Send batch of envelopes. |
| `health_check` | `async def health_check(self)` | Check SendGrid API access via scopes endpoint. |

### `SESProvider`

- Source: `aquilia/mail/providers/ses.py`
- Bases: `object`
- Summary: Async AWS SES mail provider.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `provider_type` | `str` | `'ses'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `50` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize the SES client (aiobotocore or boto3 fallback). |
| `shutdown` | `async def shutdown(self)` | Close the SES client. |
| `send` | `async def send(self, envelope: MailEnvelope)` | Send a single envelope via SES. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope])` | Send batch via SES (falls back to sequential for raw mode). |
| `health_check` | `async def health_check(self)` | Check SES account status via GetAccount. |

### `SMTPProvider`

- Source: `aquilia/mail/providers/smtp.py`
- Bases: `object`
- Summary: Async SMTP mail provider backed by aiosmtplib.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `provider_type` | `str` | `'smtp'` |
| `supports_batching` | `bool` | `True` |
| `max_batch_size` | `int` | `100` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Pre-warm the connection pool. |
| `shutdown` | `async def shutdown(self)` | Drain and close all pooled connections. |
| `send` | `async def send(self, envelope: MailEnvelope)` | Send a single envelope via SMTP. |
| `send_batch` | `async def send_batch(self, envelopes: Sequence[MailEnvelope])` | Send a batch of envelopes, reusing a single connection. |
| `health_check` | `async def health_check(self)` | Check SMTP connectivity via NOOP. |

### `MailService`

- Source: `aquilia/mail/service.py`
- Bases: `object`
- Summary: Central mail service -- owns the pipeline from message to delivery.
- Decorators: `service(scope='app', name='MailService')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_startup` | `async def on_startup(self)` | Initialize providers, store, dispatcher. |
| `on_shutdown` | `async def on_shutdown(self)` | Shutdown providers and flush queue. |
| `send_message` | `async def send_message(self, message: Any)` | Accept an EmailMessage, build envelope, dispatch. |
| `get_provider_names` | `def get_provider_names(self)` | Return names of registered providers. |
| `is_healthy` | `def is_healthy(self)` | Quick health check. |
