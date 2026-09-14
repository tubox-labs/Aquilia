"""
AquilAuth — Unified Configuration Model

Single source of truth for authentication configuration.

Historically, auth settings were spread across three config systems with
different key shapes, different defaults, and different units:

* the Python-native ``AquilaConfig.Auth`` env classes — **flat** attributes
  (``secret_key``, ``access_token_ttl_minutes``, ``backends`` …);
* the ``ConfigLoader`` subsystem dicts — **nested** shape
  (``tokens.secret_key``, ``security.backends`` …);
* constructor defaults on ``TokenManager`` / ``PasswordHasher`` (seconds vs
  minutes, ``"aquilia-app"`` vs ``["api"]``).

Worse, the loader *injected* value defaults (a well-known secret, a backends
list) that could silently outrank operator configuration, and the flat
pyconfig attributes never reached the nested keys the machinery read at all.

This module removes the ambiguity:

* :func:`normalize_auth_config` maps *every* supported spelling — flat
  pyconfig attributes, the nested loader shape, minute/day aliases — onto one
  canonical nested shape. Explicit nested values win over flat values (the
  typed ``Integration.auth(...)`` path and ``AQ_AUTH__TOKENS__*`` env
  overrides are the most specific sources).
* :class:`AuthSettings` is the frozen, typed view of that shape consumed by
  the server bootstrap, the auth middleware, and the token engine. All TTLs
  are **seconds**; the audience is always a **list**. Defaults live *only*
  here — the loader injects no values.
* :func:`resolve_signing_secret` implements the documented secret precedence
  and never injects a fallback.

Canonical shape (after normalization)::

    auth:
      enabled: false                      # opt-in HTTP enforcement
      store: {type: memory}               # shorthand for identity/credential stores
      identity_store: null                # per-store override (dict | object)
      credential_store: null
      token_store: null                   # e.g. {type: redis, url: ...}
      tokens:
        secret_key: null                  # never defaulted
        algorithm: HS256
        issuer: aquilia
        audience: [api]                   # list[str]; str accepted
        access_token_ttl_seconds: 3600    # seconds canonical
        refresh_token_ttl_seconds: 2592000
        clock_skew_seconds: 0
        stateless: false                  # verify claims without identity lookup
        collapse_token_errors: false      # one generic 401 (anti-enumeration)
      security:
        require_auth_by_default: false
        backends: [token, session]        # registry names or dotted paths
        global_guards: []                 # APP_GUARD-equivalent registration
        principal_factory: null           # dotted path: (identity, claims) -> principal
        rate_limit_max_attempts: 5
        rate_limit_window_seconds: 900
        rate_limit_lockout_seconds: 3600
        mfa_enabled: false
        mfa_required: false
        audit_enabled: true
      hashing: {algorithm: argon2id, ...} # -> HasherConfig
      initial_users: [...]

Minute/day spellings (``access_token_ttl_minutes``,
``refresh_token_ttl_days``) remain accepted everywhere and are converted;
``*_seconds`` wins when both are present.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("aquilia.auth.config")

# Well-known insecure values that older scaffolds/docs copied verbatim.
# Seeing one of these in a config is treated the same as "unset": an
# injected default must never silently win over an operator-provided secret.
RETIRED_INSECURE_SECRETS: frozenset[str | None] = frozenset(
    {
        None,
        "",
        "aquilia_insecure_dev_secret",
        "dev_secret",
        "change-me-in-prod",
        "aquilia-dev-secret-key-CHANGEME",
    }
)

# Legacy fully-qualified builtin backend paths → registry names.
BUILTIN_BACKEND_NAMES: dict[str, str] = {
    "aquilia.auth.backends.TokenBackend": "token",
    "aquilia.auth.backends.SessionBackend": "session",
    "aquilia.auth.backends.PasswordBackend": "password",
    "aquilia.auth.backends.ApiKeyBackend": "api_key",
    "aquilia.auth.backends.token.TokenBackend": "token",
    "aquilia.auth.backends.base.SessionBackend": "session",
    "aquilia.auth.backends.password.PasswordBackend": "password",
    "aquilia.auth.backends.api_key.ApiKeyBackend": "api_key",
    "jwt": "token",
    "bearer": "token",
    "api-key": "api_key",
}

# Flat pyconfig attribute → (nested section, canonical key).
_FLAT_TO_NESTED: dict[str, tuple[str, str]] = {
    "secret_key": ("tokens", "secret_key"),
    "algorithm": ("tokens", "algorithm"),
    "issuer": ("tokens", "issuer"),
    "audience": ("tokens", "audience"),
    "clock_skew_seconds": ("tokens", "clock_skew_seconds"),
    "stateless": ("tokens", "stateless"),
    "collapse_token_errors": ("tokens", "collapse_token_errors"),
    "access_token_ttl_seconds": ("tokens", "access_token_ttl_seconds"),
    "refresh_token_ttl_seconds": ("tokens", "refresh_token_ttl_seconds"),
    "require_auth_by_default": ("security", "require_auth_by_default"),
    "backends": ("security", "backends"),
    "global_guards": ("security", "global_guards"),
    "principal_factory": ("security", "principal_factory"),
    "mfa_enabled": ("security", "mfa_enabled"),
    "mfa_required": ("security", "mfa_required"),
    "audit_enabled": ("security", "audit_enabled"),
    "rate_limit_max_attempts": ("security", "rate_limit_max_attempts"),
    "rate_limit_window_seconds": ("security", "rate_limit_window_seconds"),
    "rate_limit_lockout_seconds": ("security", "rate_limit_lockout_seconds"),
    "store_type": ("store", "type"),
}

# Flat alias → canonical nested key (with unit multiplier).
_FLAT_TTL_ALIASES: dict[str, tuple[str, str, int]] = {
    "access_token_ttl_minutes": ("access_token_ttl_seconds", 60),
    "access_token_ttl": ("access_token_ttl_seconds", 1),
    "refresh_token_ttl_days": ("refresh_token_ttl_seconds", 86400),
    "refresh_token_ttl": ("refresh_token_ttl_seconds", 1),
}

# Nested legacy alias → canonical nested key (with unit multiplier).
_NESTED_TTL_ALIASES: dict[str, tuple[str, str, int]] = {
    "access_token_ttl_minutes": ("access_token_ttl_seconds", 60),
    "refresh_token_ttl_days": ("refresh_token_ttl_seconds", 86400),
}


def _as_audience_list(value: Any) -> list[str] | None:
    """Normalize an audience to ``list[str]``."""
    if value is None:
        return None
    if isinstance(value, str):
        return [value] if value else None
    if isinstance(value, (list, tuple)):
        items = [str(v) for v in value if v]
        return items or None
    return None


def _is_unset(value: Any) -> bool:
    """True when a config slot carries no user intent.

    ``None`` and empty containers are "unset" (defaults apply); explicit
    ``False`` / ``0`` / ``""`` are *set* — an operator disabling something
    must not be overridden by a default.
    """
    return value is None or (isinstance(value, (list, tuple, dict)) and len(value) == 0)


def _as_dict(value: Any, section: str) -> dict:
    """Coerce a config section to a dict; malformed values are dropped with
    a warning instead of crashing the boot with a raw ValueError."""
    if isinstance(value, dict):
        return dict(value)
    if value is not None:
        logger.warning("auth config: section %r is not a dict (%r) — ignoring it", section, value)
    return {}


def _as_bool(value: Any) -> bool:
    """Bool coercion that does not treat the string ``"false"`` as True."""
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _as_int(value: Any, default: int) -> int:
    """Int coercion honoring explicit zero/negative values, with fallback."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        logger.warning("auth config: %r is not an integer — using %s", value, default)
        return default


def normalize_auth_config(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """
    Map every supported auth-config spelling onto the canonical nested shape.

    The input may contain:

    * the canonical nested shape itself (``tokens.*`` / ``security.*``);
    * flat pyconfig attributes (``secret_key``, ``backends`` …) — lifted
      into their nested positions;
    * minute/day TTL aliases — converted to seconds.

    Rules:

    * Explicit nested values win over flat values (the typed integration
      path and ``AQ_AUTH__TOKENS__*`` env overrides are most specific).
    * ``*_seconds`` TTL spellings win over minute/day aliases.
    * ``audience`` accepts ``str`` or ``list[str]`` and always becomes a list.
    * A secret equal to one of the retired insecure defaults is dropped
      (treated as unset) — before any lifting, so a retired nested value
      can never shadow a real flat secret.
    * Malformed sections (``tokens: "string"``, ``store: "memory"``) are
      tolerated: non-dict sections warn and are ignored; a string ``store``
      becomes ``{"type": "memory"}``-style spec.

    Args:
        cfg: The merged ``auth`` config section (already default-merged by
            :meth:`~aquilia.config.ConfigLoader.get_auth_config` or built
            by hand).

    Returns:
        A new dict in the canonical shape. The input is not mutated.
    """
    cfg = dict(cfg or {})
    tokens = _as_dict(cfg.get("tokens"), "tokens")
    security = _as_dict(cfg.get("security"), "security")
    store = _as_dict(cfg.get("store"), "store")
    # A bare string store ("store": "memory") is the sibling-session spelling.
    if isinstance(cfg.get("store"), str) and cfg["store"]:
        store = {"type": cfg["store"]}
    sections = {"tokens": tokens, "security": security, "store": store}

    # ── 0. Retire insecure secrets FIRST (flat and nested) so a retired
    #       default can never shadow a real secret via the lift below. ──
    flat_secret = cfg.get("secret_key")
    if flat_secret is not None and flat_secret in RETIRED_INSECURE_SECRETS:
        cfg["secret_key"] = None
    if "secret_key" in tokens and tokens["secret_key"] in RETIRED_INSECURE_SECRETS:
        tokens["secret_key"] = None

    # ── 1. Lift flat pyconfig attributes (nested wins when both are set) ──
    for flat_key, (section, canonical_key) in _FLAT_TO_NESTED.items():
        if flat_key not in cfg:
            continue
        value = cfg[flat_key]
        target = sections[section]
        if _is_unset(target.get(canonical_key)):
            target[canonical_key] = value

    # TTL aliases: flat spellings → seconds.
    for flat_key, (canonical_key, multiplier) in _FLAT_TTL_ALIASES.items():
        if flat_key not in cfg or cfg[flat_key] is None:
            continue
        try:
            seconds = int(cfg[flat_key]) * multiplier
        except (TypeError, ValueError):
            logger.warning("auth config: %r is not an integer — ignoring TTL alias", cfg[flat_key])
            continue
        if _is_unset(tokens.get(canonical_key)):
            tokens[canonical_key] = seconds

    # TTL aliases: nested legacy spellings (``tokens.access_token_ttl_minutes``).
    for legacy_key, (canonical_key, multiplier) in _NESTED_TTL_ALIASES.items():
        if legacy_key not in tokens or tokens[legacy_key] is None:
            continue
        try:
            seconds = int(tokens[legacy_key]) * multiplier
        except (TypeError, ValueError):
            continue
        if _is_unset(tokens.get(canonical_key)):
            tokens[canonical_key] = seconds

    # ── 2. Audience is always a list of strings ──
    audience = _as_audience_list(tokens.get("audience"))
    if audience is not None:
        tokens["audience"] = audience
    else:
        tokens.pop("audience", None)

    # ── 3. Backends: accept str or list; normalize builtin dotted paths to
    #       registry names so comparisons and logs are stable. ──
    backends = security.get("backends")
    if isinstance(backends, str):
        backends = [backends]
    if isinstance(backends, (list, tuple)) and len(backends) > 0:
        security["backends"] = [BUILTIN_BACKEND_NAMES.get(b, b) if isinstance(b, str) else b for b in backends]
    else:
        security.pop("backends", None)

    # ── 4. global_guards: a single value or tuple becomes a list ──
    guards = security.get("global_guards")
    if guards is not None:
        if isinstance(guards, (list, tuple)):
            security["global_guards"] = list(guards)
        else:
            security["global_guards"] = [guards]

    # ── 5. Per-store overrides: a plain string means {"type": ...} ──
    out_extra: dict[str, Any] = {}
    for key in ("identity_store", "credential_store", "token_store"):
        value = cfg.get(key)
        if isinstance(value, str):
            if value:
                out_extra[key] = {"type": value}
        elif value is not None:
            out_extra[key] = value

    out = {
        k: v
        for k, v in cfg.items()
        if k not in _FLAT_TO_NESTED and k not in _FLAT_TTL_ALIASES and k not in out_extra
    }
    out["tokens"] = tokens
    out["security"] = security
    out["store"] = store
    out.update(out_extra)
    return out


# ============================================================================
# Canonical typed settings
# ============================================================================


@dataclass(frozen=True)
class AuthSettings:
    """
    Frozen, typed view of the canonical auth configuration.

    Build via :meth:`from_config` (accepts any supported spelling — the input
    is normalized first). Every consumer — server bootstrap, auth middleware,
    token engine — reads these values; nobody re-derives defaults.
    """

    enabled: bool = False
    require_auth_by_default: bool = False

    # Token engine
    secret_key: str | None = None
    algorithm: str = "HS256"
    issuer: str = "aquilia"
    audience: list[str] = field(default_factory=lambda: ["api"])
    access_token_ttl: int = 3600  # seconds — the ONLY unit
    refresh_token_ttl: int = 2_592_000  # seconds
    clock_skew_seconds: int = 0
    stateless: bool = False
    collapse_token_errors: bool = False

    # HTTP pipeline
    backends: list[str] = field(default_factory=lambda: ["token", "session"])
    global_guards: list[Any] = field(default_factory=list)
    principal_factory: str | None = None

    # Stores (dict specs resolved by the bootstrap, or ready-made objects)
    store_type: str = "memory"
    identity_store: Any = None
    credential_store: Any = None
    token_store: Any = None

    # Security posture
    rate_limit_max_attempts: int = 5
    rate_limit_window_seconds: int = 900
    rate_limit_lockout_seconds: int = 3600
    mfa_enabled: bool = False
    mfa_required: bool = False
    audit_enabled: bool = True

    # Hashing (HasherConfig-shaped dict/object, or a PasswordHasher instance)
    password_hasher: Any = None

    #: Bootstrap users seeded into the memory stores at boot
    #: (``[{id, email, password, roles, ...}, ...]``).
    initial_users: list[Any] = field(default_factory=list)

    @classmethod
    def from_config(cls, cfg: dict[str, Any] | None) -> AuthSettings:
        """Build from any supported config spelling (normalized first)."""
        cfg = normalize_auth_config(cfg)
        tokens = cfg.get("tokens") or {}
        security = cfg.get("security") or {}
        store = cfg.get("store") or {}

        identity_store = cfg.get("identity_store")
        credential_store = cfg.get("credential_store")
        token_store = cfg.get("token_store")
        # Legacy shorthand: ``store: {type: ...}`` applies to the identity +
        # credential stores (token stores have their own registry).
        if store.get("type"):
            if identity_store is None:
                identity_store = {"type": store["type"]}
            if credential_store is None:
                credential_store = {"type": store["type"]}

        hasher_cfg = cfg.get("password_hasher")
        if hasher_cfg is None:
            hasher_cfg = cfg.get("hashing")

        access_ttl = _as_int(tokens.get("access_token_ttl_seconds"), 3600)
        refresh_ttl = _as_int(tokens.get("refresh_token_ttl_seconds"), 2_592_000)
        if access_ttl <= 0:
            logger.warning("auth config: access_token_ttl_seconds must be positive (got %s) — using 3600", access_ttl)
            access_ttl = 3600
        if refresh_ttl <= 0:
            logger.warning("auth config: refresh_token_ttl_seconds must be positive (got %s) — using default", refresh_ttl)
            refresh_ttl = 2_592_000

        return cls(
            enabled=_as_bool(cfg.get("enabled", False)),
            require_auth_by_default=_as_bool(security.get("require_auth_by_default", False)),
            secret_key=tokens.get("secret_key"),
            algorithm=tokens.get("algorithm", "HS256"),
            issuer=tokens.get("issuer", "aquilia"),
            audience=_as_audience_list(tokens.get("audience")) or ["api"],
            access_token_ttl=access_ttl,
            refresh_token_ttl=refresh_ttl,
            clock_skew_seconds=_as_int(tokens.get("clock_skew_seconds"), 0),
            stateless=_as_bool(tokens.get("stateless", False)),
            collapse_token_errors=_as_bool(tokens.get("collapse_token_errors", False)),
            backends=list(security.get("backends") or ["token", "session"]),
            global_guards=list(security.get("global_guards") or []),
            principal_factory=security.get("principal_factory"),
            store_type=store.get("type", "memory"),
            identity_store=identity_store,
            credential_store=credential_store,
            token_store=token_store,
            rate_limit_max_attempts=_as_int(security.get("rate_limit_max_attempts"), 5),
            rate_limit_window_seconds=_as_int(security.get("rate_limit_window_seconds"), 900),
            rate_limit_lockout_seconds=_as_int(security.get("rate_limit_lockout_seconds"), 3600),
            mfa_enabled=_as_bool(security.get("mfa_enabled", False)),
            mfa_required=_as_bool(security.get("mfa_required", False)),
            audit_enabled=_as_bool(security.get("audit_enabled", True)),
            password_hasher=hasher_cfg,
            initial_users=list(cfg.get("initial_users") or []),
        )

    def to_token_config(self, **overrides: Any) -> Any:
        """
        Build a :class:`~aquilia.auth.tokens.TokenConfig` from these settings.

        This is the bridge that ends the minutes-vs-seconds and
        issuer/audience divergence between config layers: the token engine is
        always constructed from the same values the config layer resolved.
        """
        from aquilia.auth.tokens import TokenConfig

        kwargs: dict[str, Any] = {
            "issuer": self.issuer,
            "audience": list(self.audience),
            "access_token_ttl": self.access_token_ttl,
            "refresh_token_ttl": self.refresh_token_ttl,
            "clock_skew_seconds": self.clock_skew_seconds,
        }
        if self.collapse_token_errors:
            kwargs["collapse_errors"] = True
        kwargs.update(overrides)
        return TokenConfig(**kwargs)


def resolve_signing_secret(
    signing_secret: str | None = None,
    auth_settings: AuthSettings | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[str | None, str]:
    """
    Resolve the ``aquilia.signing`` secret with a *fixed, tested* precedence.

    Order (highest first):

    1. ``AquilaConfig.Signing.secret`` (signing owns signing)
    2. user-set ``auth.tokens.secret_key`` / ``auth.secret_key``
    3. ``AQ_SECRET_KEY`` environment variable
    4. ``SECRET_KEY`` environment variable

    Returns ``(secret, source)`` where *source* names the winning layer
    (``"signing"``, ``"auth"``, ``"env:AQ_SECRET_KEY"``, ``"env:SECRET_KEY"``,
    or ``(None, "none")``). Callers decide their own fallback policy — this
    function never injects a secret, so an injected default can never outrank
    operator configuration.
    """
    environ = environ if environ is not None else os.environ

    if signing_secret and signing_secret not in RETIRED_INSECURE_SECRETS:
        return signing_secret, "signing"

    if auth_settings is not None and auth_settings.secret_key:
        if auth_settings.secret_key not in RETIRED_INSECURE_SECRETS:
            return auth_settings.secret_key, "auth"

    for var in ("AQ_SECRET_KEY", "SECRET_KEY"):
        value = environ.get(var)
        if value and value not in RETIRED_INSECURE_SECRETS:
            return value, f"env:{var}"

    return None, "none"


__all__ = [
    "AuthSettings",
    "normalize_auth_config",
    "resolve_signing_secret",
    "RETIRED_INSECURE_SECRETS",
    "BUILTIN_BACKEND_NAMES",
]
