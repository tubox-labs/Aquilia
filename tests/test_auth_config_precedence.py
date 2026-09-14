"""Auth configuration unification — the multiple-sources-of-truth fixes.

Covers the gap-analysis findings (docs/AQUILIA_AUTH_VS_NESTJS_GAPS.md):

* **AG-13 [Critical]** — the loader's injected ``tokens.secret_key``
  default ("aquilia_insecure_dev_secret") silently outranked the operator's
  ``Auth.secret_key`` and both secret environment variables; the documented
  signing-secret resolution order was dead.
* **AG-15** — access-token TTL configured in *minutes* in the config layers
  and *seconds* on the token engine, with no linkage.
* **AG-16** — issuer/audience defaults disagreed between layers
  (``"aquilia-app"`` vs ``["api"]``).
* **AG-17** — a bcrypt-era ``hash_rounds: 12`` knob in the auth defaults
  consumed by nothing.
* **N-3** — flat pyconfig attributes (``Auth.secret_key``, ``backends``,
  ``require_auth_by_default`` …) never reached the nested keys the
  machinery read: the scaffold's own prod template + ``enabled=True``
  crashed at boot with ConfigInvalidFault in non-DEV mode.

These tests try to break the resolution from every direction: every config
mechanism (pyconfig env classes, typed integrations, nested dicts, env-var
overrides), unit aliases, retired insecure secrets, and precedence
inversions.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from aquilia.auth.config import (
    AuthSettings,
    RETIRED_INSECURE_SECRETS,
    normalize_auth_config,
    resolve_signing_secret,
)
from aquilia.config import ConfigLoader


STRONG_SECRET = "x" * 43  # >32 bytes


# ============================================================================
# normalize_auth_config — flat ↔ nested unification
# ============================================================================


class TestNormalization:
    def test_flat_pyconfig_attrs_lift_into_nested(self):
        """The scaffold's flat spelling must reach the nested machinery keys."""
        cfg = normalize_auth_config(
            {
                "enabled": True,
                "secret_key": STRONG_SECRET,
                "algorithm": "HS384",
                "issuer": "app",
                "audience": "web-client",
                "require_auth_by_default": True,
                "backends": ["token"],
                "stateless": True,
                "collapse_token_errors": True,
            }
        )
        assert cfg["tokens"]["secret_key"] == STRONG_SECRET
        assert cfg["tokens"]["algorithm"] == "HS384"
        assert cfg["tokens"]["issuer"] == "app"
        assert cfg["tokens"]["audience"] == ["web-client"]  # str → list
        assert cfg["tokens"]["stateless"] is True
        assert cfg["tokens"]["collapse_token_errors"] is True
        assert cfg["security"]["require_auth_by_default"] is True
        assert cfg["security"]["backends"] == ["token"]

    def test_nested_wins_over_flat(self):
        """The typed integration path / env overrides are more specific."""
        cfg = normalize_auth_config(
            {
                "secret_key": "flat-secret-" + "a" * 20,
                "tokens": {"secret_key": "nested-secret-" + "b" * 20},
            }
        )
        assert cfg["tokens"]["secret_key"].startswith("nested-secret")

    def test_ttl_minute_alias_converted(self):
        cfg = normalize_auth_config({"access_token_ttl_minutes": 15, "refresh_token_ttl_days": 7})
        assert cfg["tokens"]["access_token_ttl_seconds"] == 900
        assert cfg["tokens"]["refresh_token_ttl_seconds"] == 7 * 86400

    def test_ttl_seconds_wins_over_minutes(self):
        cfg = normalize_auth_config(
            {"access_token_ttl_minutes": 99, "access_token_ttl_seconds": 1800}
        )
        assert cfg["tokens"]["access_token_ttl_seconds"] == 1800

    def test_nested_legacy_ttl_aliases_converted(self):
        cfg = normalize_auth_config({"tokens": {"access_token_ttl_minutes": 15}})
        assert cfg["tokens"]["access_token_ttl_seconds"] == 900

    def test_retired_insecure_secrets_are_unset(self):
        """Copied-from-docs defaults must behave exactly like "not configured"."""
        for retired in RETIRED_INSECURE_SECRETS:
            if retired is None:
                continue
            cfg = normalize_auth_config({"tokens": {"secret_key": retired}})
            assert cfg["tokens"]["secret_key"] is None, retired

    def test_dotted_builtin_backend_names_normalized(self):
        cfg = normalize_auth_config(
            {
                "backends": [
                    "aquilia.auth.backends.TokenBackend",
                    "aquilia.auth.backends.SessionBackend",
                ]
            }
        )
        assert cfg["security"]["backends"] == ["token", "session"]

    def test_single_guard_becomes_list(self):
        cfg = normalize_auth_config({"global_guards": "app.auth.TenantGuard"})
        assert cfg["security"]["global_guards"] == ["app.auth.TenantGuard"]

    def test_store_string_override_becomes_spec(self):
        cfg = normalize_auth_config({"token_store": "redis"})
        assert cfg["token_store"] == {"type": "redis"}

    def test_input_not_mutated(self):
        original = {"secret_key": "k" * 32, "backends": ["token"]}
        snapshot = dict(original)
        normalize_auth_config(original)
        assert original == snapshot

    def test_empty_config(self):
        cfg = normalize_auth_config(None)
        assert cfg["tokens"] == {}
        assert cfg["security"] == {}
        assert cfg["store"] == {}


# ============================================================================
# AuthSettings — the canonical typed view
# ============================================================================


class TestAuthSettings:
    def test_defaults_are_coherent_with_token_config(self):
        """AG-15/AG-16: one TTL unit, one audience default, everywhere."""
        from aquilia.auth.tokens import TokenConfig

        settings = AuthSettings.from_config({})
        engine_defaults = TokenConfig()

        assert settings.access_token_ttl == engine_defaults.access_token_ttl
        assert settings.refresh_token_ttl == engine_defaults.refresh_token_ttl
        assert settings.issuer == engine_defaults.issuer
        assert settings.audience == engine_defaults.audience
        assert settings.enabled is False
        assert settings.require_auth_by_default is False

    def test_to_token_config_carries_every_setting(self):
        settings = AuthSettings.from_config(
            {
                "tokens": {
                    "issuer": "aniwave",
                    "audience": ["aniwave_client"],
                    "access_token_ttl_seconds": 1800,
                    "clock_skew_seconds": 30,
                }
            }
        )
        tc = settings.to_token_config()
        assert tc.issuer == "aniwave"
        assert tc.audience == ["aniwave_client"]
        assert tc.access_token_ttl == 1800
        assert tc.clock_skew_seconds == 30

    def test_collapse_errors_flows_to_token_config(self):
        settings = AuthSettings.from_config({"collapse_token_errors": True})
        assert settings.to_token_config().collapse_errors is True

    def test_store_shorthand_applies_to_identity_and_credential(self):
        settings = AuthSettings.from_config({"store": {"type": "database"}})
        assert settings.identity_store == {"type": "database"}
        assert settings.credential_store == {"type": "database"}
        assert settings.token_store is None  # token stores have their own registry

    def test_hash_rounds_is_not_a_default_anywhere(self):
        """AG-17: the dead bcrypt-era knob must not be injected."""
        loader = ConfigLoader(env_prefix="AQ_")
        auth = loader.get_auth_config()
        assert "hash_rounds" not in str(auth)


# ============================================================================
# AG-13 — the signing-secret precedence (the proven Critical)
# ============================================================================


class TestSigningSecretPrecedence:
    def test_operator_secret_beats_everything_without_signing_section(self):
        """The exact AG-13 scenario: user sets Auth.secret_key + env; the old
        loader default silently won. Now the operator's key must be used."""
        secret, source = resolve_signing_secret(
            signing_secret=None,
            auth_settings=AuthSettings.from_config({"secret_key": STRONG_SECRET}),
            environ={"AQ_SECRET_KEY": "env-key-" + "c" * 20, "SECRET_KEY": "older-" + "d" * 20},
        )
        assert secret == STRONG_SECRET
        assert source == "auth"

    def test_signing_section_wins_over_auth(self):
        secret, source = resolve_signing_secret(
            signing_secret="signing-key-" + "e" * 20,
            auth_settings=AuthSettings.from_config({"secret_key": STRONG_SECRET}),
            environ={},
        )
        assert secret.startswith("signing-key")
        assert source == "signing"

    def test_env_wins_when_no_config_secret(self):
        secret, source = resolve_signing_secret(
            signing_secret=None,
            auth_settings=AuthSettings.from_config({}),
            environ={"AQ_SECRET_KEY": "env-key-" + "c" * 20},
        )
        assert secret.startswith("env-key")
        assert source == "env:AQ_SECRET_KEY"

    def test_secret_key_env_beats_generic_secret_key_env(self):
        _, source = resolve_signing_secret(
            environ={"AQ_SECRET_KEY": "a" * 40, "SECRET_KEY": "b" * 40}
        )
        assert source == "env:AQ_SECRET_KEY"

    def test_retired_default_never_wins(self):
        """A copied-from-old-docs Signing.secret must not shadow a real env key."""
        secret, _ = resolve_signing_secret(
            signing_secret="aquilia_insecure_dev_secret",
            auth_settings=AuthSettings.from_config({"tokens": {"secret_key": "dev_secret"}}),
            environ={"AQ_SECRET_KEY": "real-" + "f" * 20},
        )
        assert secret.startswith("real")

    def test_none_when_nothing_configured(self):
        secret, source = resolve_signing_secret(environ={})
        assert secret is None
        assert source == "none"

    def test_loader_no_longer_injects_a_secret_default(self):
        """The root cause of AG-13: the loader must never emit a secret."""
        loader = ConfigLoader(env_prefix="AQ_")
        loader._merge_dict(loader.config_data, {"auth": {"enabled": False}})
        auth = loader.get_auth_config()
        assert auth["tokens"].get("secret_key") is None


# ============================================================================
# get_auth_config — loader-level behavior
# ============================================================================


class TestLoaderAuthConfig:
    def test_flat_pyconfig_section_flows_to_machinery_keys(self):
        """N-3: the scaffold's pyconfig shape must actually reach tokens.*."""
        loader = ConfigLoader(env_prefix="AQ_")
        loader._merge_dict(
            loader.config_data,
            {
                "auth": {
                    "enabled": True,
                    "secret_key": STRONG_SECRET,
                    "access_token_ttl_minutes": 30,
                    "backends": ["token"],
                    "require_auth_by_default": True,
                }
            },
        )
        auth = loader.get_auth_config()
        assert auth["enabled"] is True
        assert auth["tokens"]["secret_key"] == STRONG_SECRET
        assert auth["tokens"]["access_token_ttl_seconds"] == 1800
        assert auth["security"]["backends"] == ["token"]
        assert auth["security"]["require_auth_by_default"] is True

    def test_auth_section_presence_does_not_enable(self):
        """AG-01 residual: a raw auth section without ``enabled`` must not
        flip enforcement on (the old get_subsystem_config defaulted it True)."""
        loader = ConfigLoader(env_prefix="AQ_")
        loader._merge_dict(
            loader.config_data,
            {"auth": {"secret_key": STRONG_SECRET}},  # no "enabled" key
        )
        assert loader.get_auth_config()["enabled"] is False

    def test_explicit_enabled_true_is_honored(self):
        loader = ConfigLoader(env_prefix="AQ_")
        loader._merge_dict(loader.config_data, {"auth": {"enabled": True}})
        assert loader.get_auth_config()["enabled"] is True

    def test_integration_shaped_section_preserved(self):
        loader = ConfigLoader(env_prefix="AQ_")
        loader._merge_dict(
            loader.config_data,
            {
                "integrations": {
                    "auth": {
                        "enabled": True,
                        "tokens": {"secret_key": "nested-" + "g" * 20, "access_token_ttl_seconds": 600},
                    }
                }
            },
        )
        auth = loader.get_auth_config()
        assert auth["enabled"] is True
        assert auth["tokens"]["secret_key"].startswith("nested")
        assert auth["tokens"]["access_token_ttl_seconds"] == 600

    def test_env_var_override_lands_in_nested_shape(self, monkeypatch):
        monkeypatch.setenv("AQ_AUTH__TOKENS__SECRET_KEY", "env-nested-" + "h" * 20)
        monkeypatch.setenv("AQ_AUTH__TOKENS__ACCESS_TOKEN_TTL_SECONDS", "120")
        loader = ConfigLoader.load(paths=[])
        auth = loader.get_auth_config()
        assert auth["tokens"]["secret_key"].startswith("env-nested")
        assert auth["tokens"]["access_token_ttl_seconds"] == 120

    def test_minutes_vs_seconds_misconfiguration_is_impossible(self):
        """AG-15's footgun: an operator setting minutes cannot accidentally
        get a 60-second token or a 3600-minute token."""
        settings = AuthSettings.from_config({"access_token_ttl_minutes": 30})
        assert settings.access_token_ttl == 1800  # 30 minutes → seconds

        settings = AuthSettings.from_config({"tokens": {"access_token_ttl_minutes": 30}})
        assert settings.access_token_ttl == 1800


# ============================================================================
# Full pyconfig-class flow — the scaffold path end-to-end
# ============================================================================


class TestPyconfigClassFlow:
    def test_env_class_serializes_into_canonical_shape(self, tmp_path, monkeypatch):
        """The exact scaffold pattern (BaseEnv + class auth) — via to_loader."""
        from aquilia.pyconfig import AquilaConfig
        from aquilia.pyconfig import Secret as PSecret

        class BaseEnv(AquilaConfig):
            class auth(AquilaConfig.Auth):
                secret_key = PSecret(env="AQ_TEST_SECRET", default=STRONG_SECRET)
                access_token_ttl_seconds = 1800
                stateless = True
                backends = ["jwt-stateless"]

        loader = BaseEnv.to_loader()
        auth = loader.get_auth_config()
        settings = AuthSettings.from_config(auth)

        assert settings.enabled is False  # opt-in preserved
        assert settings.secret_key == STRONG_SECRET
        assert settings.access_token_ttl == 1800
        assert settings.stateless is True
        assert settings.backends == ["jwt-stateless"]

    def test_workspace_env_config_merges_flat_and_reaches_machinery(self):
        """Workspace.to_dict() merges env-class data flat into config['auth'];
        get_auth_config must lift it into tokens.*/security.* (the N-3 fix)."""
        from aquilia.pyconfig import AquilaConfig

        class DevEnv(AquilaConfig):
            class auth(AquilaConfig.Auth):
                secret_key = STRONG_SECRET
                require_auth_by_default = True
                global_guards = ["tests.test_auth_config_precedence:_DummyGuard"]

        data = DevEnv.to_dict()
        assert data["auth"]["secret_key"] == STRONG_SECRET  # flat, as the workspace writes it

        loader = ConfigLoader(env_prefix="AQ_")
        loader._merge_dict(loader.config_data, {"auth": data["auth"]})
        settings = AuthSettings.from_config(loader.get_auth_config())

        assert settings.secret_key == STRONG_SECRET
        assert settings.require_auth_by_default is True
        assert settings.global_guards == ["tests.test_auth_config_precedence:_DummyGuard"]


class _DummyGuard:
    def check(self, ctx) -> None:
        return None


# ============================================================================
# Adversarial: malformed configuration
# ============================================================================


class TestMalformedConfig:
    def test_garbage_ttl_values_are_ignored_not_crashing(self):
        settings = AuthSettings.from_config({"access_token_ttl_minutes": "not-a-number"})
        assert settings.access_token_ttl == 3600  # falls back to canonical default

    def test_bogus_audience_types_do_not_crash(self):
        settings = AuthSettings.from_config({"audience": 12345})
        assert settings.audience == ["api"]

    def test_backends_string_accepted(self):
        settings = AuthSettings.from_config({"backends": "token"})
        assert settings.backends == ["token"]

    def test_partial_nested_and_flat_mix(self):
        settings = AuthSettings.from_config(
            {
                "secret_key": "flat-" + "i" * 20,
                "tokens": {"issuer": "nested-issuer"},
            }
        )
        assert settings.secret_key.startswith("flat-")
        assert settings.issuer == "nested-issuer"


# ============================================================================
# Server bootstrap — the signing engine actually uses the resolved secret
# ============================================================================


class TestBootstrapSigningUsesResolvedSecret:
    def test_configured_secret_reaches_signing_engine(self, monkeypatch):
        """The AG-13 proof scenario, end-to-end at the engine level: with the
        user's secret configured AND env vars set, the signing engine must be
        keyed by the user's secret (the old code picked the 27-byte default)."""
        import aquilia.signing as signing

        monkeypatch.setenv("AQ_SECRET_KEY", "env-" + "j" * 40)
        monkeypatch.setenv("SECRET_KEY", "legacy-" + "k" * 40)

        from aquilia.auth.config import AuthSettings, resolve_signing_secret

        secret, source = resolve_signing_secret(
            auth_settings=AuthSettings.from_config({"secret_key": "user-set-" + "l" * 24})
        )
        assert secret.startswith("user-set")
        assert source == "auth"

        # And the engine configured with it round-trips a signed value.
        signer = signing.Signer(secret=secret, salt="test.precedence")
        token = signer.sign("payload")
        assert signer.unsign(token) == "payload"
