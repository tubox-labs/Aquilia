"""
Regression tests for the mail config builder system.

Covers:
  - Integration.MailAuth   (all methods + to_dict)
  - Integration.MailProvider.*   (SMTP, SES, SendGrid, Console, File)
  - Integration.mail()  (flat params, auth=, providers=, single vs list)
  - aquilia.mail.config.MailAuthConfig  (blueprint, wrappers, factories)
  - aquilia.mail.config.MailConfig  (auth slot, from_dict, to_dict round-trip)
  - Backward compatibility: plain dict providers still work
"""

import pytest
from typing import Any, Dict


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _mail_integration():
    from aquilia.config_builders import Integration
    return Integration


def _mail_config_mod():
    from aquilia.mail import config as mc
    return mc


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthImport
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthImport:
    def test_integration_mailauth_exists(self):
        I = _mail_integration()
        assert hasattr(I, "MailAuth")

    def test_mailauth_is_nested_class(self):
        I = _mail_integration()
        assert isinstance(I.MailAuth, type)

    def test_mailauth_has_plain_classmethod(self):
        I = _mail_integration()
        assert callable(I.MailAuth.plain)

    def test_mailauth_has_api_key_classmethod(self):
        I = _mail_integration()
        assert callable(I.MailAuth.api_key)

    def test_mailauth_has_aws_ses_classmethod(self):
        I = _mail_integration()
        assert callable(I.MailAuth.aws_ses)

    def test_mailauth_has_oauth2_classmethod(self):
        I = _mail_integration()
        assert callable(I.MailAuth.oauth2)

    def test_mailauth_has_ntlm_classmethod(self):
        I = _mail_integration()
        assert callable(I.MailAuth.ntlm)

    def test_mailauth_has_anonymous_classmethod(self):
        I = _mail_integration()
        assert callable(I.MailAuth.anonymous)

    def test_mailauth_has_to_dict(self):
        I = _mail_integration()
        a = I.MailAuth.plain("u", "p")
        assert hasattr(a, "to_dict")
        assert callable(a.to_dict)


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthPlain
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthPlain:
    def _plain(self, **kw):
        from aquilia.config_builders import Integration
        return Integration.MailAuth.plain(**kw)

    def test_method_is_plain(self):
        a = self._plain(username="u", password="p")
        assert a.to_dict()["method"] == "plain"

    def test_username_in_dict(self):
        a = self._plain(username="bob@example.com", password="s3cr3t")
        assert a.to_dict()["username"] == "bob@example.com"

    def test_password_in_dict(self):
        a = self._plain(username="u", password="pw123")
        assert a.to_dict()["password"] == "pw123"

    def test_password_env_in_dict(self):
        a = self._plain(username="u", password_env="MY_SMTP_PASS")
        d = a.to_dict()
        assert d.get("password_env") == "MY_SMTP_PASS"
        assert "password" not in d

    def test_no_extra_keys_without_optionals(self):
        a = self._plain(username="u", password="p")
        d = a.to_dict()
        assert set(d.keys()) == {"method", "username", "password"}

    def test_direct_init_method(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth(method="plain", username="x", password="y")
        d = a.to_dict()
        assert d["method"] == "plain"
        assert d["username"] == "x"


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthApiKey
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthApiKey:
    def test_method_is_api_key(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.api_key(env="SG_KEY")
        assert a.to_dict()["method"] == "api_key"

    def test_api_key_env_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.api_key(env="SG_KEY")
        assert a.to_dict()["api_key_env"] == "SG_KEY"

    def test_literal_api_key_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.api_key(key="SG.abc123")
        assert a.to_dict()["api_key"] == "SG.abc123"

    def test_both_key_and_env(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.api_key(key="SG.x", env="SG_KEY")
        d = a.to_dict()
        assert d["api_key"] == "SG.x"
        assert d["api_key_env"] == "SG_KEY"


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthAwsSes
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthAwsSes:
    def test_method_is_aws_ses(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.aws_ses(region="us-east-1")
        assert a.to_dict()["method"] == "aws_ses"

    def test_region_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.aws_ses(region="eu-west-1")
        assert a.to_dict()["aws_region"] == "eu-west-1"

    def test_access_key_id_env(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.aws_ses(access_key_id_env="AWS_KEY")
        assert a.to_dict()["aws_access_key_id_env"] == "AWS_KEY"

    def test_secret_env(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.aws_ses(secret_access_key_env="AWS_SECRET")
        assert a.to_dict()["aws_secret_access_key_env"] == "AWS_SECRET"

    def test_literal_credentials(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.aws_ses(
            access_key_id="AKIA123",
            secret_access_key="s3cr3t",
            region="us-west-2",
        )
        d = a.to_dict()
        assert d["aws_access_key_id"] == "AKIA123"
        assert d["aws_secret_access_key"] == "s3cr3t"
        assert d["aws_region"] == "us-west-2"

    def test_session_token(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.aws_ses(session_token="tok123")
        assert a.to_dict()["aws_session_token"] == "tok123"


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthOAuth2
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthOAuth2:
    def test_method_is_oauth2(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.oauth2(
            "cid", "csec", token_url="https://tok.url"
        )
        assert a.to_dict()["method"] == "oauth2"

    def test_client_id_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.oauth2("mycid", token_url="https://t.url")
        assert a.to_dict()["client_id"] == "mycid"

    def test_token_url_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.oauth2("c", token_url="https://my.token.url")
        assert a.to_dict()["token_url"] == "https://my.token.url"

    def test_scope_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.oauth2(
            "c", token_url="https://t.url", scope="mail.send"
        )
        assert a.to_dict()["scope"] == "mail.send"

    def test_client_secret_env(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.oauth2(
            "c", client_secret_env="OAUTH_SEC", token_url="https://t.url"
        )
        assert a.to_dict()["client_secret_env"] == "OAUTH_SEC"

    def test_refresh_token_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.oauth2(
            "c", token_url="https://t.url", refresh_token="rtok"
        )
        assert a.to_dict()["refresh_token"] == "rtok"


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthNtlm
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthNtlm:
    def test_method_is_ntlm(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.ntlm("DOMAIN\\user", "pass", domain="DOMAIN")
        assert a.to_dict()["method"] == "ntlm"

    def test_domain_in_dict(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.ntlm("u", domain="CORP")
        assert a.to_dict()["domain"] == "CORP"


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthAnonymous
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthAnonymous:
    def test_method_is_none(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.anonymous()
        assert a.to_dict()["method"] == "none"

    def test_no_credential_keys(self):
        from aquilia.config_builders import Integration
        a = Integration.MailAuth.anonymous()
        d = a.to_dict()
        assert "username" not in d
        assert "password" not in d
        assert "api_key" not in d


# ═══════════════════════════════════════════════════════════════════
# TestMailProviderImport
# ═══════════════════════════════════════════════════════════════════

class TestMailProviderImport:
    def test_integration_mailprovider_exists(self):
        I = _mail_integration()
        assert hasattr(I, "MailProvider")

    def test_smtp_class_exists(self):
        I = _mail_integration()
        assert hasattr(I.MailProvider, "SMTP")

    def test_ses_class_exists(self):
        I = _mail_integration()
        assert hasattr(I.MailProvider, "SES")

    def test_sendgrid_class_exists(self):
        I = _mail_integration()
        assert hasattr(I.MailProvider, "SendGrid")

    def test_console_class_exists(self):
        I = _mail_integration()
        assert hasattr(I.MailProvider, "Console")

    def test_file_class_exists(self):
        I = _mail_integration()
        assert hasattr(I.MailProvider, "File")

    def test_all_have_to_dict(self):
        I = _mail_integration()
        for cls in (I.MailProvider.SMTP, I.MailProvider.SES,
                    I.MailProvider.SendGrid, I.MailProvider.Console,
                    I.MailProvider.File):
            instance = cls(name="test")
            assert callable(instance.to_dict)


# ═══════════════════════════════════════════════════════════════════
# TestMailProviderSMTP
# ═══════════════════════════════════════════════════════════════════

class TestMailProviderSMTP:
    def _smtp(self, **kw):
        from aquilia.config_builders import Integration
        return Integration.MailProvider.SMTP(**kw)

    def test_type_is_smtp(self):
        assert self._smtp(name="s").to_dict()["type"] == "smtp"

    def test_name_in_dict(self):
        assert self._smtp(name="primary").to_dict()["name"] == "primary"

    def test_host_in_dict(self):
        d = self._smtp(name="s", host="smtp.myapp.com").to_dict()
        assert d["host"] == "smtp.myapp.com"

    def test_port_in_dict(self):
        d = self._smtp(name="s", port=465).to_dict()
        assert d["port"] == 465

    def test_use_tls_default_true(self):
        assert self._smtp(name="s").to_dict()["use_tls"] is True

    def test_use_ssl_default_false(self):
        assert self._smtp(name="s").to_dict()["use_ssl"] is False

    def test_timeout_default(self):
        assert self._smtp(name="s").to_dict()["timeout"] == 30.0

    def test_pool_size_in_dict(self):
        d = self._smtp(name="s", pool_size=5).to_dict()
        assert d["pool_size"] == 5

    def test_validate_certs_in_dict(self):
        d = self._smtp(name="s", validate_certs=False).to_dict()
        assert d["validate_certs"] is False

    def test_priority_default(self):
        assert self._smtp(name="s").to_dict()["priority"] == 10

    def test_enabled_default_true(self):
        assert self._smtp(name="s").to_dict()["enabled"] is True

    def test_enabled_false(self):
        assert self._smtp(name="s", enabled=False).to_dict()["enabled"] is False

    def test_rate_limit_per_min(self):
        d = self._smtp(name="s", rate_limit_per_min=300).to_dict()
        assert d["rate_limit_per_min"] == 300

    def test_client_cert_optional(self):
        d = self._smtp(name="s", client_cert="/path/to/cert.pem").to_dict()
        assert d["client_cert"] == "/path/to/cert.pem"

    def test_client_cert_absent_by_default(self):
        assert "client_cert" not in self._smtp(name="s").to_dict()

    def test_source_address_optional(self):
        d = self._smtp(name="s", source_address="1.2.3.4").to_dict()
        assert d["source_address"] == "1.2.3.4"

    def test_auth_serialised(self):
        from aquilia.config_builders import Integration
        auth = Integration.MailAuth.plain("u", "p")
        d = self._smtp(name="s", auth=auth).to_dict()
        assert d["auth"]["method"] == "plain"
        assert d["auth"]["username"] == "u"

    def test_auth_dict_passthrough(self):
        d = self._smtp(name="s", auth={"method": "plain", "username": "x"}).to_dict()
        assert d["auth"]["username"] == "x"

    def test_default_name(self):
        from aquilia.config_builders import Integration
        d = Integration.MailProvider.SMTP().to_dict()
        assert d["name"] == "smtp"
        assert d["host"] == "localhost"

    def test_single_provider_not_iterable_bug(self):
        """Regression: passing a single SMTP instance to Integration.mail()
        should NOT raise TypeError: 'SMTP' object is not iterable."""
        from aquilia.config_builders import Integration
        provider = Integration.MailProvider.SMTP(
            name="gmail", host="smtp.gmail.com", port=587
        )
        # Must not raise
        result = Integration.mail(
            default_from="test@example.com",
            providers=provider,   # intentionally NOT wrapped in a list
        )
        assert len(result["providers"]) == 1
        assert result["providers"][0]["name"] == "gmail"


# ═══════════════════════════════════════════════════════════════════
# TestMailProviderSES
# ═══════════════════════════════════════════════════════════════════

class TestMailProviderSES:
    def _ses(self, **kw):
        from aquilia.config_builders import Integration
        return Integration.MailProvider.SES(**kw)

    def test_type_is_ses(self):
        assert self._ses(name="s").to_dict()["type"] == "ses"

    def test_region_default(self):
        assert self._ses(name="s").to_dict()["region"] == "us-east-1"

    def test_region_override(self):
        assert self._ses(name="s", region="eu-west-1").to_dict()["region"] == "eu-west-1"

    def test_use_raw_default(self):
        assert self._ses(name="s").to_dict()["use_raw"] is True

    def test_configuration_set_optional(self):
        d = self._ses(name="s", configuration_set="cfg").to_dict()
        assert d["configuration_set"] == "cfg"

    def test_configuration_set_absent_by_default(self):
        assert "configuration_set" not in self._ses(name="s").to_dict()

    def test_source_arn_optional(self):
        d = self._ses(name="s", source_arn="arn:aws:ses:...").to_dict()
        assert d["source_arn"] == "arn:aws:ses:..."

    def test_tags_optional(self):
        d = self._ses(name="s", tags={"env": "prod"}).to_dict()
        assert d["tags"] == {"env": "prod"}

    def test_tags_absent_by_default(self):
        assert "tags" not in self._ses(name="s").to_dict()

    def test_endpoint_url_optional(self):
        d = self._ses(name="s", endpoint_url="http://localhost:4566").to_dict()
        assert d["endpoint_url"] == "http://localhost:4566"

    def test_auth_ses_credentials(self):
        from aquilia.config_builders import Integration
        auth = Integration.MailAuth.aws_ses(
            access_key_id="AKIA", secret_access_key="sec", region="us-east-1"
        )
        d = self._ses(name="s", auth=auth).to_dict()
        assert d["auth"]["aws_access_key_id"] == "AKIA"


# ═══════════════════════════════════════════════════════════════════
# TestMailProviderSendGrid
# ═══════════════════════════════════════════════════════════════════

class TestMailProviderSendGrid:
    def _sg(self, **kw):
        from aquilia.config_builders import Integration
        return Integration.MailProvider.SendGrid(**kw)

    def test_type_is_sendgrid(self):
        assert self._sg(name="sg").to_dict()["type"] == "sendgrid"

    def test_sandbox_mode_default_false(self):
        assert self._sg(name="sg").to_dict()["sandbox_mode"] is False

    def test_sandbox_mode_true(self):
        assert self._sg(name="sg", sandbox_mode=True).to_dict()["sandbox_mode"] is True

    def test_click_tracking_default_true(self):
        assert self._sg(name="sg").to_dict()["click_tracking"] is True

    def test_open_tracking_default_true(self):
        assert self._sg(name="sg").to_dict()["open_tracking"] is True

    def test_categories_optional(self):
        d = self._sg(name="sg", categories=["transactional"]).to_dict()
        assert d["categories"] == ["transactional"]

    def test_categories_absent_by_default(self):
        assert "categories" not in self._sg(name="sg").to_dict()

    def test_template_id_optional(self):
        d = self._sg(name="sg", template_id="d-abc123").to_dict()
        assert d["template_id"] == "d-abc123"

    def test_api_base_url_default(self):
        assert "sendgrid.com" in self._sg(name="sg").to_dict()["api_base_url"]

    def test_timeout_default(self):
        assert self._sg(name="sg").to_dict()["timeout"] == 30.0

    def test_auth_api_key(self):
        from aquilia.config_builders import Integration
        auth = Integration.MailAuth.api_key(env="SG_KEY")
        d = self._sg(name="sg", auth=auth).to_dict()
        assert d["auth"]["api_key_env"] == "SG_KEY"

    def test_asm_group_id(self):
        d = self._sg(name="sg", asm_group_id=42).to_dict()
        assert d["asm_group_id"] == 42


# ═══════════════════════════════════════════════════════════════════
# TestMailProviderConsole
# ═══════════════════════════════════════════════════════════════════

class TestMailProviderConsole:
    def _con(self, **kw):
        from aquilia.config_builders import Integration
        return Integration.MailProvider.Console(**kw)

    def test_type_is_console(self):
        assert self._con().to_dict()["type"] == "console"

    def test_default_name(self):
        assert self._con().to_dict()["name"] == "console"

    def test_custom_name(self):
        assert self._con(name="dev").to_dict()["name"] == "dev"

    def test_priority_default_100(self):
        assert self._con().to_dict()["priority"] == 100

    def test_rate_limit_large(self):
        assert self._con().to_dict()["rate_limit_per_min"] == 10000

    def test_enabled_default(self):
        assert self._con().to_dict()["enabled"] is True


# ═══════════════════════════════════════════════════════════════════
# TestMailProviderFile
# ═══════════════════════════════════════════════════════════════════

class TestMailProviderFile:
    def _file(self, **kw):
        from aquilia.config_builders import Integration
        return Integration.MailProvider.File(**kw)

    def test_type_is_file(self):
        assert self._file().to_dict()["type"] == "file"

    def test_default_name(self):
        assert self._file().to_dict()["name"] == "file"

    def test_output_dir_default(self):
        assert "/tmp" in self._file().to_dict()["output_dir"]

    def test_output_dir_custom(self):
        d = self._file(output_dir="/data/mail").to_dict()
        assert d["output_dir"] == "/data/mail"

    def test_max_files_default(self):
        assert self._file().to_dict()["max_files"] == 10000

    def test_max_files_custom(self):
        assert self._file(max_files=500).to_dict()["max_files"] == 500

    def test_write_index_default_true(self):
        assert self._file().to_dict()["write_index"] is True

    def test_include_metadata_default_true(self):
        assert self._file().to_dict()["include_metadata"] is True

    def test_file_extension_default(self):
        assert self._file().to_dict()["file_extension"] == ".eml"

    def test_priority_default_90(self):
        assert self._file().to_dict()["priority"] == 90


# ═══════════════════════════════════════════════════════════════════
# TestIntegrationMailFunction
# ═══════════════════════════════════════════════════════════════════

class TestIntegrationMailFunction:
    def _mail(self, **kw):
        from aquilia.config_builders import Integration
        return Integration.mail(**kw)

    def test_integration_type_key(self):
        d = self._mail()
        assert d["_integration_type"] == "mail"

    def test_enabled_default_true(self):
        assert self._mail()["enabled"] is True

    def test_default_from_default(self):
        assert self._mail()["default_from"] == "noreply@localhost"

    def test_default_from_custom(self):
        d = self._mail(default_from="hi@example.com")
        assert d["default_from"] == "hi@example.com"

    def test_providers_empty_by_default(self):
        assert self._mail()["providers"] == []

    def test_auth_none_by_default(self):
        assert self._mail()["auth"] is None

    def test_auth_plain_serialised(self):
        from aquilia.config_builders import Integration
        d = self._mail(auth=Integration.MailAuth.plain("u", "p"))
        assert d["auth"]["method"] == "plain"
        assert d["auth"]["username"] == "u"

    def test_auth_dict_passthrough(self):
        d = self._mail(auth={"method": "api_key", "api_key": "x"})
        assert d["auth"]["api_key"] == "x"

    # ── providers as list of MailProvider instances ──────────────────

    def test_providers_list_smtp(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=[Integration.MailProvider.SMTP(name="s", host="h")])
        assert d["providers"][0]["type"] == "smtp"
        assert d["providers"][0]["host"] == "h"

    def test_providers_list_ses(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=[Integration.MailProvider.SES(name="s", region="eu-west-1")])
        assert d["providers"][0]["type"] == "ses"
        assert d["providers"][0]["region"] == "eu-west-1"

    def test_providers_list_sendgrid(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=[Integration.MailProvider.SendGrid(name="sg")])
        assert d["providers"][0]["type"] == "sendgrid"

    def test_providers_list_console(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=[Integration.MailProvider.Console()])
        assert d["providers"][0]["type"] == "console"

    def test_providers_list_file(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=[Integration.MailProvider.File()])
        assert d["providers"][0]["type"] == "file"

    def test_providers_mixed_dict_and_instance(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=[
            Integration.MailProvider.SMTP(name="s1"),
            {"name": "s2", "type": "smtp", "host": "h2"},
        ])
        assert len(d["providers"]) == 2
        assert d["providers"][1]["host"] == "h2"

    # ── REGRESSION: single provider instance (not in a list) ─────────

    def test_single_smtp_instance_not_list_no_error(self):
        """Regression for TypeError: 'SMTP' object is not iterable."""
        from aquilia.config_builders import Integration
        provider = Integration.MailProvider.SMTP(name="gmail", host="smtp.gmail.com", port=587)
        d = self._mail(default_from="me@example.com", providers=provider)
        assert len(d["providers"]) == 1
        assert d["providers"][0]["host"] == "smtp.gmail.com"

    def test_single_ses_instance_not_list_no_error(self):
        from aquilia.config_builders import Integration
        provider = Integration.MailProvider.SES(name="ses")
        d = self._mail(providers=provider)
        assert d["providers"][0]["type"] == "ses"

    def test_single_console_instance_not_list_no_error(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=Integration.MailProvider.Console())
        assert d["providers"][0]["type"] == "console"

    def test_single_file_instance_not_list_no_error(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=Integration.MailProvider.File())
        assert d["providers"][0]["type"] == "file"

    def test_single_sendgrid_instance_not_list_no_error(self):
        from aquilia.config_builders import Integration
        d = self._mail(providers=Integration.MailProvider.SendGrid(name="sg"))
        assert d["providers"][0]["type"] == "sendgrid"

    # ── per-provider auth normalisation ──────────────────────────────

    def test_per_provider_auth_in_dict_normalised(self):
        from aquilia.config_builders import Integration
        auth = Integration.MailAuth.api_key(env="KEY")
        d = self._mail(providers=[{"name": "sg", "type": "sendgrid", "auth": auth}])
        assert d["providers"][0]["auth"]["api_key_env"] == "KEY"

    def test_provider_instance_with_auth_serialised(self):
        from aquilia.config_builders import Integration
        provider = Integration.MailProvider.SMTP(
            name="s",
            auth=Integration.MailAuth.plain("u", password_env="PW_ENV"),
        )
        d = self._mail(providers=[provider])
        assert d["providers"][0]["auth"]["password_env"] == "PW_ENV"

    # ── flat scalar params ────────────────────────────────────────────

    def test_console_backend_false_default(self):
        assert self._mail()["console_backend"] is False

    def test_console_backend_true(self):
        assert self._mail(console_backend=True)["console_backend"] is True

    def test_preview_mode_false_default(self):
        assert self._mail()["preview_mode"] is False

    def test_subject_prefix(self):
        d = self._mail(subject_prefix="[TEST] ")
        assert d["subject_prefix"] == "[TEST] "

    def test_metrics_enabled_default(self):
        assert self._mail()["metrics_enabled"] is True

    def test_tracing_enabled_default(self):
        assert self._mail()["tracing_enabled"] is False

    def test_retry_block(self):
        d = self._mail(retry_max_attempts=3, retry_base_delay=2.0)
        assert d["retry"]["max_attempts"] == 3
        assert d["retry"]["base_delay"] == 2.0

    def test_rate_limit_block(self):
        d = self._mail(rate_limit_global=500, rate_limit_per_domain=50)
        assert d["rate_limit"]["global_per_minute"] == 500
        assert d["rate_limit"]["per_domain_per_minute"] == 50

    def test_security_block(self):
        d = self._mail(
            dkim_enabled=True,
            dkim_domain="myapp.com",
            dkim_selector="mail",
            require_tls=True,
            pii_redaction=True,
        )
        s = d["security"]
        assert s["dkim_enabled"] is True
        assert s["dkim_domain"] == "myapp.com"
        assert s["dkim_selector"] == "mail"
        assert s["require_tls"] is True
        assert s["pii_redaction_enabled"] is True

    def test_template_dirs(self):
        d = self._mail(template_dirs=["templates/mail"])
        assert d["templates"]["template_dirs"] == ["templates/mail"]

    def test_template_dirs_default(self):
        d = self._mail()
        assert d["templates"]["template_dirs"] == ["mail_templates"]

    def test_kwargs_passthrough(self):
        d = self._mail(custom_key="custom_val")
        assert d["custom_key"] == "custom_val"


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthConfigBlueprint  (aquilia.mail.config)
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthConfigBlueprint:
    def test_blueprint_exists(self):
        mc = _mail_config_mod()
        assert hasattr(mc, "MailAuthConfigBlueprint")

    def test_method_choices_include_plain(self):
        mc = _mail_config_mod()
        assert "plain" in mc.MailAuthConfigBlueprint.METHOD_CHOICES

    def test_method_choices_include_oauth2(self):
        mc = _mail_config_mod()
        assert "oauth2" in mc.MailAuthConfigBlueprint.METHOD_CHOICES

    def test_method_choices_include_api_key(self):
        mc = _mail_config_mod()
        assert "api_key" in mc.MailAuthConfigBlueprint.METHOD_CHOICES

    def test_method_choices_include_ntlm(self):
        mc = _mail_config_mod()
        assert "ntlm" in mc.MailAuthConfigBlueprint.METHOD_CHOICES

    def test_method_choices_include_none(self):
        mc = _mail_config_mod()
        assert "none" in mc.MailAuthConfigBlueprint.METHOD_CHOICES


# ═══════════════════════════════════════════════════════════════════
# TestMailAuthConfig  (aquilia.mail.config)
# ═══════════════════════════════════════════════════════════════════

class TestMailAuthConfig:
    def test_class_exists(self):
        mc = _mail_config_mod()
        assert hasattr(mc, "MailAuthConfig")

    def test_plain_factory(self):
        mc = _mail_config_mod()
        a = mc.MailAuthConfig.plain("user@x.com", "hunter2")
        assert a.method == "plain"
        assert a.username == "user@x.com"

    def test_api_key_factory(self):
        mc = _mail_config_mod()
        a = mc.MailAuthConfig.api_key(env="SG_KEY")
        assert a.to_dict()["api_key_env"] == "SG_KEY"

    def test_oauth2_factory(self):
        mc = _mail_config_mod()
        a = mc.MailAuthConfig.oauth2("cid", "csec", token_url="https://t.url")
        assert a.to_dict()["client_id"] == "cid"
        assert a.to_dict()["token_url"] == "https://t.url"

    def test_anonymous_factory(self):
        mc = _mail_config_mod()
        a = mc.MailAuthConfig.anonymous()
        assert a.method == "none"

    def test_aws_ses_factory(self):
        mc = _mail_config_mod()
        a = mc.MailAuthConfig.aws_ses(
            access_key_id="AKIA",
            secret_access_key="sec",
            region="ap-southeast-1",
        )
        d = a.to_dict()
        assert d["aws_access_key_id"] == "AKIA"
        assert d["aws_region"] == "ap-southeast-1"

    def test_to_dict_roundtrip(self):
        mc = _mail_config_mod()
        a = mc.MailAuthConfig.plain("u", "p")
        d = a.to_dict()
        assert d["method"] == "plain"
        assert d["username"] == "u"
        assert d["password"] == "p"


# ═══════════════════════════════════════════════════════════════════
# TestMailConfigAuthSlot  (aquilia.mail.config.MailConfig)
# ═══════════════════════════════════════════════════════════════════

class TestMailConfigAuthSlot:
    def test_mailconfig_has_auth_slot(self):
        mc = _mail_config_mod()
        assert "auth" in mc.MailConfig.__slots__

    def test_auth_none_by_default(self):
        mc = _mail_config_mod()
        cfg = mc.MailConfig()
        assert cfg.auth is None

    def test_auth_set_via_init(self):
        mc = _mail_config_mod()
        auth = mc.MailAuthConfig.plain("u", "p")
        cfg = mc.MailConfig(auth=auth)
        assert cfg.auth is not None
        assert cfg.auth.method == "plain"

    def test_auth_set_via_dict(self):
        mc = _mail_config_mod()
        cfg = mc.MailConfig(auth={"method": "plain", "username": "x", "password": "y"})
        assert cfg.auth.username == "x"

    def test_auth_in_to_dict_when_set(self):
        mc = _mail_config_mod()
        cfg = mc.MailConfig(auth=mc.MailAuthConfig.plain("u", "p"))
        d = cfg.to_dict()
        assert d["auth"] is not None
        assert d["auth"]["method"] == "plain"

    def test_auth_none_in_to_dict_when_not_set(self):
        mc = _mail_config_mod()
        cfg = mc.MailConfig()
        assert cfg.to_dict()["auth"] is None

    def test_from_dict_round_trip_with_auth(self):
        mc = _mail_config_mod()
        data = {
            "default_from": "noreply@x.com",
            "auth": {"method": "plain", "username": "u", "password": "p"},
            "providers": [],
        }
        cfg = mc.MailConfig.from_dict(data)
        assert cfg.auth is not None
        assert cfg.auth.username == "u"

    def test_from_dict_no_auth_key(self):
        mc = _mail_config_mod()
        cfg = mc.MailConfig.from_dict({"default_from": "x@x.com"})
        assert cfg.auth is None

    def test_from_dict_auth_none_explicit(self):
        mc = _mail_config_mod()
        cfg = mc.MailConfig.from_dict({"auth": None})
        assert cfg.auth is None

    def test_roundtrip_auth_preserved(self):
        mc = _mail_config_mod()
        original = mc.MailConfig(auth=mc.MailAuthConfig.plain("u", "p"))
        restored = mc.MailConfig.from_dict(original.to_dict())
        assert restored.auth.method == "plain"
        assert restored.auth.username == "u"


# ═══════════════════════════════════════════════════════════════════
# TestValidateAuth  (aquilia.mail.config._validate_auth)
# ═══════════════════════════════════════════════════════════════════

class TestValidateAuth:
    def test_none_returns_none(self):
        mc = _mail_config_mod()
        assert mc._validate_auth(None) is None

    def test_dict_returns_mailauth_config(self):
        mc = _mail_config_mod()
        result = mc._validate_auth({"method": "plain", "username": "u", "password": "p"})
        assert isinstance(result, mc.MailAuthConfig)

    def test_mailauth_instance_returned_as_is(self):
        mc = _mail_config_mod()
        a = mc.MailAuthConfig.plain("u", "p")
        result = mc._validate_auth(a)
        assert result is a

    def test_unknown_type_returns_none(self):
        mc = _mail_config_mod()
        result = mc._validate_auth(42)
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# TestProviderConfigBlueprintAuthField
# ═══════════════════════════════════════════════════════════════════

class TestProviderConfigBlueprintAuthField:
    def test_blueprint_has_auth_field(self):
        mc = _mail_config_mod()
        assert hasattr(mc.ProviderConfigBlueprint, "auth")

    def test_validate_provider_with_auth_dict(self):
        mc = _mail_config_mod()
        p = mc._validate_provider({
            "name": "s",
            "type": "smtp",
            "host": "localhost",
            "auth": {"method": "plain", "username": "u", "password": "p"},
        })
        assert p is not None
        assert p.name == "s"


# ═══════════════════════════════════════════════════════════════════
# TestMailConfigFullRoundTrip
# ═══════════════════════════════════════════════════════════════════

class TestMailConfigFullRoundTrip:
    def test_integration_mail_to_mailconfig(self):
        """Full pipeline: Integration.mail() → MailConfig.from_dict()."""
        from aquilia.config_builders import Integration
        from aquilia.mail.config import MailConfig

        d = Integration.mail(
            default_from="noreply@myapp.com",
            auth=Integration.MailAuth.plain("u", password_env="SMTP_PW"),
            providers=[
                Integration.MailProvider.SMTP(
                    name="primary",
                    host="smtp.myapp.com",
                    port=587,
                    use_tls=True,
                ),
            ],
            dkim_enabled=True,
            dkim_domain="myapp.com",
            retry_max_attempts=3,
        )
        cfg = MailConfig.from_dict(d)

        assert cfg.default_from == "noreply@myapp.com"
        assert cfg.auth is not None
        assert cfg.auth.method == "plain"
        assert cfg.auth.username == "u"
        assert len(cfg.providers) == 1
        assert cfg.providers[0].name == "primary"
        assert cfg.security.dkim_enabled is True
        assert cfg.retry.max_attempts == 3

    def test_integration_mail_ses_to_mailconfig(self):
        from aquilia.config_builders import Integration
        from aquilia.mail.config import MailConfig

        d = Integration.mail(
            default_from="noreply@myapp.com",
            providers=[
                Integration.MailProvider.SES(
                    name="ses",
                    region="eu-west-1",
                    configuration_set="cfg",
                    auth=Integration.MailAuth.aws_ses(
                        access_key_id="AKIA",
                        secret_access_key="sec",
                    ),
                ),
            ],
        )
        cfg = MailConfig.from_dict(d)
        assert cfg.providers[0].name == "ses"

    def test_integration_mail_multiple_providers(self):
        from aquilia.config_builders import Integration
        from aquilia.mail.config import MailConfig

        d = Integration.mail(
            default_from="x@x.com",
            providers=[
                Integration.MailProvider.SMTP(name="primary", host="smtp.x.com"),
                Integration.MailProvider.Console(),
                Integration.MailProvider.File(output_dir="/tmp/m"),
            ],
        )
        cfg = MailConfig.from_dict(d)
        assert len(cfg.providers) == 3

    def test_single_provider_no_list_full_pipeline(self):
        """Regression: single provider object without list wrapping."""
        from aquilia.config_builders import Integration
        from aquilia.mail.config import MailConfig

        d = Integration.mail(
            default_from="x@x.com",
            providers=Integration.MailProvider.Console(),
        )
        cfg = MailConfig.from_dict(d)
        assert len(cfg.providers) == 1
        assert cfg.providers[0].type == "console"

    def test_workspace_like_gmail_smtp_config(self):
        """Mirrors the myapp/workspace.py Gmail config that triggered the bug."""
        from aquilia.config_builders import Integration
        from aquilia.mail.config import MailConfig

        d = Integration.mail(
            default_from="Aquilia Team <noreply@example.com>",
            auth=Integration.MailAuth.plain(
                username="noreply@example.com",
                password="app_password_here",
            ),
            providers=[
                Integration.MailProvider.SMTP(
                    name="gmail",
                    host="smtp.gmail.com",
                    port=587,
                    use_tls=True,
                )
            ],
        )
        assert d["_integration_type"] == "mail"
        assert d["providers"][0]["host"] == "smtp.gmail.com"
        cfg = MailConfig.from_dict(d)
        assert cfg.auth.username == "noreply@example.com"


# ═══════════════════════════════════════════════════════════════════
# TestMailProviderBaseDefaults
# ═══════════════════════════════════════════════════════════════════

class TestMailProviderBaseDefaults:
    def test_base_has_name(self):
        from aquilia.config_builders import Integration
        d = Integration.MailProvider.SMTP(name="x").to_dict()
        assert "name" in d

    def test_base_has_type(self):
        from aquilia.config_builders import Integration
        d = Integration.MailProvider.SMTP(name="x").to_dict()
        assert "type" in d

    def test_base_has_priority(self):
        from aquilia.config_builders import Integration
        d = Integration.MailProvider.SMTP(name="x").to_dict()
        assert "priority" in d

    def test_base_has_enabled(self):
        from aquilia.config_builders import Integration
        d = Integration.MailProvider.SMTP(name="x").to_dict()
        assert "enabled" in d

    def test_base_has_rate_limit_per_min(self):
        from aquilia.config_builders import Integration
        d = Integration.MailProvider.SMTP(name="x").to_dict()
        assert "rate_limit_per_min" in d

    def test_no_auth_key_when_none(self):
        from aquilia.config_builders import Integration
        d = Integration.MailProvider.SMTP(name="x").to_dict()
        assert "auth" not in d
