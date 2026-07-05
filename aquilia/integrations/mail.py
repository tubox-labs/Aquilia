"""
Mail integration -- typed mail subsystem configuration.

Provider builders below (``SmtpProvider``, ``SesProvider``, ``SendGridProvider``,
``ConsoleProvider``, ``FileProvider``) are thin wrappers around the real
``aquilia.mail.providers`` classes: field names, types, and defaults come
from those classes directly -- there is no second, independent
declaration of the same fields to keep in sync. Import the real
provider classes from ``aquilia.mail.providers`` directly if you don't
need the ``enabled=`` / ``rate_limit_per_min=`` / ``auth=`` orchestration
knobs these wrappers add.

Example::

    MailIntegration(
        default_from="noreply@myapp.com",
        auth=MailAuth.plain("user", password_env="SMTP_PASS"),
        providers=[
            SmtpProvider(host="smtp.myapp.com", port=587),
        ],
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aquilia.mail.auth import MailAuth
from aquilia.mail.providers.console import ConsoleProvider as _RealConsoleProvider
from aquilia.mail.providers.file import FileProvider as _RealFileProvider
from aquilia.mail.providers.sendgrid import SendGridProvider as _RealSendGridProvider
from aquilia.mail.providers.ses import SESProvider as _RealSESProvider
from aquilia.mail.providers.smtp import SMTPProvider as _RealSMTPProvider

__all__ = [
    "MailAuth",
    "SmtpProvider",
    "SesProvider",
    "SendGridProvider",
    "ConsoleProvider",
    "FileProvider",
    "MailIntegration",
]


def _provider_instance_to_dict(provider: Any, auth: Any, enabled: bool, rate_limit_per_min: int) -> dict[str, Any]:
    """
    Build the config dict ``MailConfig.from_dict()`` expects from a real,
    already-constructed ``aquilia.mail.providers`` instance.

    Skips unset optionals (``None``, ``""``, empty list/dict) so the shape
    matches what a hand-written "only include what's set" ``to_dict()``
    would produce, without needing one.
    """
    d: dict[str, Any] = {}
    for key, val in vars(provider).items():
        if key.startswith("_") or val is None or val == "":
            continue
        if isinstance(val, (list, dict)) and not val:
            continue
        d[key] = val.as_posix() if isinstance(val, Path) else val

    d["type"] = getattr(provider, "provider_type", "")
    d.setdefault("priority", getattr(provider, "priority", 50))
    d["enabled"] = enabled
    d["rate_limit_per_min"] = rate_limit_per_min
    if auth is not None:
        d["auth"] = auth.to_dict() if hasattr(auth, "to_dict") else auth
    return d


class _ProviderWrapper:
    """
    Base for typed provider builders.

    Wraps a real ``aquilia.mail.providers`` class -- field names and
    defaults live in exactly one place, the real provider's ``__init__``.
    Adds the orchestration-only knobs (``enabled``, ``rate_limit_per_min``,
    a top-level ``auth=`` object) that the real send-capable provider
    classes don't need to know about.
    """

    _real_cls: type

    def __init__(
        self,
        *args: Any,
        enabled: bool = True,
        rate_limit_per_min: int = 600,
        auth: Any | None = None,
        **kwargs: Any,
    ) -> None:
        self._provider = self._real_cls(*args, **kwargs)
        self._enabled = enabled
        self._rate_limit_per_min = rate_limit_per_min
        self._auth = auth

    def __getattr__(self, name: str) -> Any:
        # Delegate field access (host, port, output_dir, ...) to the
        # wrapped real provider instance.
        return getattr(self.__dict__["_provider"], name)

    def to_dict(self) -> dict[str, Any]:
        return _provider_instance_to_dict(self._provider, self._auth, self._enabled, self._rate_limit_per_min)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self._provider.name!r})"


class SmtpProvider(_ProviderWrapper):
    """SMTP / STARTTLS mail provider. Fields match ``SMTPProvider.__init__`` exactly."""

    _real_cls = _RealSMTPProvider


class SesProvider(_ProviderWrapper):
    """AWS SES mail provider. Fields match ``SESProvider.__init__`` exactly."""

    _real_cls = _RealSESProvider


class SendGridProvider(_ProviderWrapper):
    """SendGrid Web API v3 provider. Fields match ``SendGridProvider.__init__`` exactly."""

    _real_cls = _RealSendGridProvider


class ConsoleProvider(_ProviderWrapper):
    """Console / stdout provider (development only)."""

    _real_cls = _RealConsoleProvider


class FileProvider(_ProviderWrapper):
    """File / .eml provider (testing & audit)."""

    _real_cls = _RealFileProvider


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
    default_reply_to: str | None = None
    subject_prefix: str = ""
    providers: list[Any] = field(default_factory=list)
    auth: MailAuth | None = None
    console_backend: bool = False
    preview_mode: bool = False
    template_dirs: list[str] = field(default_factory=lambda: ["mail_templates"])
    retry_max_attempts: int = 5
    retry_base_delay: float = 1.0
    rate_limit_global: int = 1000
    rate_limit_per_domain: int = 100
    dkim_enabled: bool = False
    dkim_domain: str | None = None
    dkim_selector: str = "aquilia"
    require_tls: bool = True
    pii_redaction: bool = False
    metrics_enabled: bool = True
    tracing_enabled: bool = False
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        # Normalise auth
        auth_dict: dict[str, Any] | None = None
        if self.auth is not None:
            auth_dict = self.auth.to_dict() if hasattr(self.auth, "to_dict") else self.auth

        # Normalise providers
        normalised: list[dict[str, Any]] = []
        raw_providers = self.providers
        if (
            raw_providers is not None
            and hasattr(raw_providers, "to_dict")
            and not isinstance(raw_providers, (list, tuple))
        ):
            raw_providers = [raw_providers]
        for p in raw_providers or []:
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
