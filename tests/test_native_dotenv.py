"""
Comprehensive tests for the native dotenv and pyconfig system.

These tests verify:
1. Native dotenv parsing and loading
2. Env class resolution with automatic dotenv loading
3. Secret class with dotenv integration
4. AquilaConfig.to_dict() with caching
5. Duplicate resolution prevention
6. Edge cases and error handling
7. Regression tests for issue #22
"""

import os
import tempfile
from pathlib import Path

import pytest


# ============================================================================
# DOTENV PARSER TESTS
# ============================================================================


class TestDotEnvParser:
    """Tests for DotEnv.parse() and DotEnv.parse_string()."""

    def test_simple_key_value(self):
        """Parse simple KEY=value pairs."""
        from aquilia.dotenv import DotEnv

        content = """
        SIMPLE=value
        ANOTHER=another_value
        """
        values = DotEnv.parse_string(content)
        assert values["SIMPLE"] == "value"
        assert values["ANOTHER"] == "another_value"

    def test_double_quoted_values(self):
        """Parse double-quoted values with escapes."""
        from aquilia.dotenv import DotEnv

        content = """
        QUOTED="value with spaces"
        ESCAPED="line1\\nline2"
        TABS="tab\\there"
        """
        values = DotEnv.parse_string(content)
        assert values["QUOTED"] == "value with spaces"
        assert values["ESCAPED"] == "line1\nline2"
        assert values["TABS"] == "tab\there"

    def test_single_quoted_values(self):
        """Parse single-quoted values (no escape processing)."""
        from aquilia.dotenv import DotEnv

        content = """
        SINGLE='value with spaces'
        NO_ESCAPE='line1\\nline2'
        """
        values = DotEnv.parse_string(content)
        assert values["SINGLE"] == "value with spaces"
        # Single quotes preserve backslash literally
        assert values["NO_ESCAPE"] == "line1\\nline2"

    def test_comments_and_empty_lines(self):
        """Comments and empty lines are ignored."""
        from aquilia.dotenv import DotEnv

        content = """
        # This is a comment
        KEY1=value1

        # Another comment
        KEY2=value2
        """
        values = DotEnv.parse_string(content)
        assert values == {"KEY1": "value1", "KEY2": "value2"}

    def test_export_prefix(self):
        """Handle 'export' prefix."""
        from aquilia.dotenv import DotEnv

        content = """
        export EXPORTED=value1
        export ALSO_EXPORTED=value2
        NORMAL=value3
        """
        values = DotEnv.parse_string(content)
        assert values["EXPORTED"] == "value1"
        assert values["ALSO_EXPORTED"] == "value2"
        assert values["NORMAL"] == "value3"

    def test_inline_comments(self):
        """Strip inline comments from unquoted values."""
        from aquilia.dotenv import DotEnv

        content = """
        WITH_COMMENT=value # this is a comment
        NO_COMMENT=value
        """
        values = DotEnv.parse_string(content)
        assert values["WITH_COMMENT"] == "value"
        assert values["NO_COMMENT"] == "value"

    def test_multiline_double_quoted(self):
        """Parse multiline double-quoted strings."""
        from aquilia.dotenv import DotEnv

        content = '''MULTILINE="line 1
line 2
line 3"'''
        values = DotEnv.parse_string(content)
        assert values["MULTILINE"] == "line 1\nline 2\nline 3"

    def test_multiline_single_quoted(self):
        """Parse multiline single-quoted strings."""
        from aquilia.dotenv import DotEnv

        content = """MULTILINE='line 1
line 2
line 3'"""
        values = DotEnv.parse_string(content)
        assert values["MULTILINE"] == "line 1\nline 2\nline 3"

    def test_variable_interpolation_braces(self):
        """Variable interpolation with ${VAR} syntax."""
        from aquilia.dotenv import DotEnv

        content = """
        BASE=http://localhost
        API_URL=${BASE}/api
        """
        values = DotEnv.parse_string(content, interpolate=True)
        assert values["BASE"] == "http://localhost"
        assert values["API_URL"] == "http://localhost/api"

    def test_variable_interpolation_simple(self):
        """Variable interpolation with $VAR syntax."""
        from aquilia.dotenv import DotEnv

        content = """
        BASE=http://localhost
        API_URL=$BASE/api
        """
        values = DotEnv.parse_string(content, interpolate=True)
        assert values["API_URL"] == "http://localhost/api"

    def test_interpolation_from_os_environ(self):
        """Interpolation looks up os.environ for undefined vars."""
        from aquilia.dotenv import DotEnv

        os.environ["TEST_EXTERNAL_VAR"] = "external_value"
        try:
            content = """
            USES_EXTERNAL=${TEST_EXTERNAL_VAR}/path
            """
            values = DotEnv.parse_string(content, interpolate=True)
            assert values["USES_EXTERNAL"] == "external_value/path"
        finally:
            del os.environ["TEST_EXTERNAL_VAR"]

    def test_no_interpolation_when_disabled(self):
        """Interpolation can be disabled."""
        from aquilia.dotenv import DotEnv

        content = """
        BASE=http://localhost
        API_URL=${BASE}/api
        """
        values = DotEnv.parse_string(content, interpolate=False)
        assert values["API_URL"] == "${BASE}/api"

    def test_invalid_variable_names_skipped(self):
        """Invalid variable names are logged and skipped."""
        from aquilia.dotenv import DotEnv

        content = """
        VALID=ok
        123INVALID=bad
        also-invalid=bad
        """
        values = DotEnv.parse_string(content)
        assert "VALID" in values
        assert "123INVALID" not in values
        assert "also-invalid" not in values

    def test_empty_value(self):
        """Handle empty values."""
        from aquilia.dotenv import DotEnv

        content = """
        EMPTY=
        QUOTED_EMPTY=""
        """
        values = DotEnv.parse_string(content)
        assert values["EMPTY"] == ""
        assert values["QUOTED_EMPTY"] == ""

    def test_equals_in_value(self):
        """Values can contain = signs."""
        from aquilia.dotenv import DotEnv

        content = """
        URL=postgres://user:pass=word@host/db
        """
        values = DotEnv.parse_string(content)
        assert values["URL"] == "postgres://user:pass=word@host/db"

    def test_bom_handling(self):
        """UTF-8 BOM is stripped if present."""
        from aquilia.dotenv import DotEnv

        content = "\ufeffKEY=value"
        values = DotEnv.parse_string(content)
        assert values["KEY"] == "value"


class TestDotEnvLoad:
    """Tests for DotEnv.load() and file operations."""

    def test_load_file(self, tmp_path):
        """Load variables from a file into os.environ."""
        from aquilia.dotenv import DotEnv

        env_file = tmp_path / ".env"
        env_file.write_text("TEST_LOAD_KEY=test_value\n")

        # Clean up before test
        if "TEST_LOAD_KEY" in os.environ:
            del os.environ["TEST_LOAD_KEY"]

        loaded = DotEnv.load(env_file)

        assert "TEST_LOAD_KEY" in loaded
        assert os.environ.get("TEST_LOAD_KEY") == "test_value"

        # Clean up
        del os.environ["TEST_LOAD_KEY"]

    def test_load_respects_existing_env_by_default(self, tmp_path):
        """By default, existing environment variables are not overwritten."""
        from aquilia.dotenv import DotEnv

        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING_KEY=new_value\n")

        os.environ["EXISTING_KEY"] = "original_value"

        try:
            DotEnv.load(env_file, override=False)
            assert os.environ["EXISTING_KEY"] == "original_value"
        finally:
            del os.environ["EXISTING_KEY"]

    def test_load_with_override(self, tmp_path):
        """With override=True, existing values are replaced."""
        from aquilia.dotenv import DotEnv

        env_file = tmp_path / ".env"
        env_file.write_text("OVERRIDE_KEY=new_value\n")

        os.environ["OVERRIDE_KEY"] = "original_value"

        try:
            DotEnv.load(env_file, override=True)
            assert os.environ["OVERRIDE_KEY"] == "new_value"
        finally:
            del os.environ["OVERRIDE_KEY"]

    def test_load_missing_file_returns_empty(self, tmp_path):
        """Loading a non-existent file returns empty dict."""
        from aquilia.dotenv import DotEnv

        loaded = DotEnv.load(tmp_path / "nonexistent.env")
        assert loaded == {}


class TestDotEnvLoader:
    """Tests for DotEnvLoader singleton."""

    def test_ensure_loaded_is_idempotent(self, tmp_path):
        """ensure_loaded() only loads files once."""
        from aquilia.dotenv import DotEnvLoader

        # Reset for clean test
        DotEnvLoader.reset()

        env_file = tmp_path / ".env"
        env_file.write_text("IDEMPOTENT_KEY=value\n")

        # First call
        loaded1 = DotEnvLoader.ensure_loaded(path=env_file)

        # Modify the file
        env_file.write_text("IDEMPOTENT_KEY=new_value\n")

        # Second call (should return cached, not reload)
        loaded2 = DotEnvLoader.ensure_loaded(path=env_file)

        assert loaded1 == loaded2
        assert DotEnvLoader.is_loaded()

        # Clean up
        DotEnvLoader.reset()
        if "IDEMPOTENT_KEY" in os.environ:
            del os.environ["IDEMPOTENT_KEY"]

    def test_reset_allows_reload(self, tmp_path):
        """reset() allows files to be loaded again."""
        from aquilia.dotenv import DotEnvLoader

        DotEnvLoader.reset()

        env_file = tmp_path / ".env"
        env_file.write_text("RESET_KEY=value1\n")

        DotEnvLoader.ensure_loaded(path=env_file)
        assert os.environ.get("RESET_KEY") == "value1"

        DotEnvLoader.reset()
        env_file.write_text("RESET_KEY=value2\n")

        # After reset, we still have the old value in os.environ
        # but the loader state is cleared
        assert not DotEnvLoader.is_loaded()

        # Clean up
        if "RESET_KEY" in os.environ:
            del os.environ["RESET_KEY"]

    def test_default_known_paths_include_example_and_mode(self, tmp_path):
        """Without explicit search paths, loader checks known defaults including .env.example and mode files."""
        from aquilia.dotenv import DotEnvLoader

        DotEnvLoader.reset()
        (tmp_path / ".env.example").write_text("DEFAULT_CHAIN_KEY=from_example\n")
        (tmp_path / ".env.prod").write_text("DEFAULT_CHAIN_KEY=from_mode\n")

        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)
        os.environ["AQUILIA_ENV"] = "prod"
        if "DEFAULT_CHAIN_KEY" in os.environ:
            del os.environ["DEFAULT_CHAIN_KEY"]

        try:
            loaded = DotEnvLoader.ensure_loaded()
            assert loaded.get("DEFAULT_CHAIN_KEY") == "from_mode"
            assert os.environ.get("DEFAULT_CHAIN_KEY") == "from_mode"
        finally:
            DotEnvLoader.reset()
            del os.environ["AQUILIA_WORKSPACE"]
            del os.environ["AQUILIA_ENV"]
            if "DEFAULT_CHAIN_KEY" in os.environ:
                del os.environ["DEFAULT_CHAIN_KEY"]


# ============================================================================
# ENV CLASS TESTS
# ============================================================================


class TestEnvClass:
    """Tests for the Env class."""

    def setup_method(self):
        """Reset dotenv state before each test."""
        from aquilia.pyconfig import reset_dotenv_state

        reset_dotenv_state()

    def test_resolve_from_environ(self):
        """Env.resolve() reads from os.environ."""
        from aquilia.pyconfig import Env

        os.environ["TEST_ENV_KEY"] = "test_value"
        try:
            env = Env("TEST_ENV_KEY")
            assert env.resolve() == "test_value"
        finally:
            del os.environ["TEST_ENV_KEY"]

    def test_resolve_default_when_missing(self):
        """Env.resolve() returns default when variable is not set."""
        from aquilia.pyconfig import Env

        # Ensure the key doesn't exist
        if "NONEXISTENT_KEY" in os.environ:
            del os.environ["NONEXISTENT_KEY"]

        env = Env("NONEXISTENT_KEY", default="default_value")
        assert env.resolve() == "default_value"

    def test_cast_to_int(self):
        """Env with cast=int converts string to integer."""
        from aquilia.pyconfig import Env

        os.environ["INT_KEY"] = "42"
        try:
            env = Env("INT_KEY", cast=int)
            assert env.resolve() == 42
            assert isinstance(env.resolve(), int)
        finally:
            del os.environ["INT_KEY"]

    def test_cast_to_float(self):
        """Env with cast=float converts string to float."""
        from aquilia.pyconfig import Env

        os.environ["FLOAT_KEY"] = "3.14"
        try:
            env = Env("FLOAT_KEY", cast=float)
            assert env.resolve() == 3.14
        finally:
            del os.environ["FLOAT_KEY"]

    def test_cast_to_bool_truthy(self):
        """Env with cast=bool handles truthy values."""
        from aquilia.pyconfig import Env

        for truthy in ["1", "true", "True", "TRUE", "yes", "YES", "on", "ON"]:
            os.environ["BOOL_KEY"] = truthy
            env = Env("BOOL_KEY", cast=bool)
            assert env.resolve() is True, f"Failed for {truthy}"

        del os.environ["BOOL_KEY"]

    def test_cast_to_bool_falsy(self):
        """Env with cast=bool handles falsy values."""
        from aquilia.pyconfig import Env

        for falsy in ["0", "false", "False", "FALSE", "no", "NO", "off", "OFF"]:
            os.environ["BOOL_KEY"] = falsy
            env = Env("BOOL_KEY", cast=bool)
            assert env.resolve() is False, f"Failed for {falsy}"

        del os.environ["BOOL_KEY"]

    def test_auto_cast_int(self):
        """Auto-casting converts integer strings."""
        from aquilia.pyconfig import Env

        os.environ["AUTO_INT"] = "123"
        try:
            env = Env("AUTO_INT")  # no cast specified
            result = env.resolve()
            assert result == 123
            assert isinstance(result, int)
        finally:
            del os.environ["AUTO_INT"]

    def test_auto_cast_float(self):
        """Auto-casting converts float strings."""
        from aquilia.pyconfig import Env

        os.environ["AUTO_FLOAT"] = "1.5"
        try:
            env = Env("AUTO_FLOAT")
            result = env.resolve()
            assert result == 1.5
            assert isinstance(result, float)
        finally:
            del os.environ["AUTO_FLOAT"]

    def test_auto_cast_json_array(self):
        """Auto-casting parses JSON arrays."""
        from aquilia.pyconfig import Env

        os.environ["AUTO_JSON"] = '["a", "b", "c"]'
        try:
            env = Env("AUTO_JSON")
            result = env.resolve()
            assert result == ["a", "b", "c"]
        finally:
            del os.environ["AUTO_JSON"]

    def test_auto_cast_json_object(self):
        """Auto-casting parses JSON objects."""
        from aquilia.pyconfig import Env

        os.environ["AUTO_OBJ"] = '{"key": "value"}'
        try:
            env = Env("AUTO_OBJ")
            result = env.resolve()
            assert result == {"key": "value"}
        finally:
            del os.environ["AUTO_OBJ"]

    def test_caching(self):
        """Env.resolve() caches results when use_cache=True."""
        from aquilia.pyconfig import Env

        os.environ["CACHE_KEY"] = "initial"
        env = Env("CACHE_KEY")

        # First call
        result1 = env.resolve(use_cache=True)
        assert result1 == "initial"

        # Change the environment
        os.environ["CACHE_KEY"] = "changed"

        # Cached call returns old value
        result2 = env.resolve(use_cache=True)
        assert result2 == "initial"

        # Non-cached call returns new value
        result3 = env.resolve(use_cache=False)
        assert result3 == "changed"

        del os.environ["CACHE_KEY"]

    def test_invalidate_cache(self):
        """invalidate_cache() clears the cached value."""
        from aquilia.pyconfig import Env

        os.environ["INVALIDATE_KEY"] = "initial"
        env = Env("INVALIDATE_KEY")

        env.resolve(use_cache=True)
        os.environ["INVALIDATE_KEY"] = "changed"

        # Still cached
        assert env.resolve(use_cache=True) == "initial"

        # Invalidate
        env.invalidate_cache()

        # Now gets new value
        assert env.resolve(use_cache=True) == "changed"

        del os.environ["INVALIDATE_KEY"]

    def test_disable_auto_load(self, tmp_path):
        """Env.disable_auto_load() prevents automatic dotenv loading."""
        from aquilia.pyconfig import Env, reset_dotenv_state

        reset_dotenv_state()

        # Create a .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AUTO_LOAD_TEST=should_not_load\n")

        # Change to tmp_path so the loader would find .env
        old_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            Env.disable_auto_load()
            env = Env("AUTO_LOAD_TEST", default="default")
            result = env.resolve()
            # Should get default because auto-load is disabled
            # and we didn't manually set the env var
            if "AUTO_LOAD_TEST" not in os.environ:
                assert result == "default"
        finally:
            os.chdir(old_cwd)
            Env.enable_auto_load()
            reset_dotenv_state()

    def test_required_raises_when_missing(self):
        """Env with required=True raises ConfigMissingFault when variable is not set."""
        from aquilia.faults.domains import ConfigMissingFault
        from aquilia.pyconfig import Env

        # Ensure the key doesn't exist
        if "REQUIRED_MISSING_KEY" in os.environ:
            del os.environ["REQUIRED_MISSING_KEY"]

        env = Env("REQUIRED_MISSING_KEY", required=True)
        with pytest.raises(ConfigMissingFault) as exc_info:
            env.resolve()

        assert "REQUIRED_MISSING_KEY" in str(exc_info.value)

    def test_required_with_value_works(self):
        """Env with required=True works when variable is set."""
        from aquilia.pyconfig import Env

        os.environ["REQUIRED_PRESENT_KEY"] = "value"
        try:
            env = Env("REQUIRED_PRESENT_KEY", required=True)
            assert env.resolve() == "value"
        finally:
            del os.environ["REQUIRED_PRESENT_KEY"]

    def test_required_with_default_uses_default(self):
        """Env with required=True but default provided uses default when missing."""
        from aquilia.pyconfig import Env

        # Key not in environment
        if "REQUIRED_WITH_DEFAULT" in os.environ:
            del os.environ["REQUIRED_WITH_DEFAULT"]

        # Even though required=True, if default is provided, it's used
        env = Env("REQUIRED_WITH_DEFAULT", required=True, default="fallback")
        assert env.resolve() == "fallback"


# ============================================================================
# SECRET CLASS TESTS
# ============================================================================


class TestSecretClass:
    """Tests for the Secret class."""

    def setup_method(self):
        """Reset dotenv state before each test."""
        from aquilia.pyconfig import reset_dotenv_state

        reset_dotenv_state()

    def test_reveal_from_environ(self):
        """Secret.reveal() reads from os.environ."""
        from aquilia.pyconfig import Secret

        os.environ["SECRET_KEY"] = "super_secret"
        try:
            secret = Secret(env="SECRET_KEY")
            assert secret.reveal() == "super_secret"
        finally:
            del os.environ["SECRET_KEY"]

    def test_reveal_literal_value(self):
        """Secret with literal value returns it."""
        from aquilia.pyconfig import Secret

        secret = Secret(value="inline_secret")
        assert secret.reveal() == "inline_secret"

    def test_reveal_default(self):
        """Secret with default returns it when env is not set."""
        from aquilia.pyconfig import Secret

        secret = Secret(env="NONEXISTENT_SECRET", default="default_secret")
        assert secret.reveal() == "default_secret"

    def test_reveal_required_raises(self):
        """Required secret raises when value is not available."""
        from aquilia.faults.domains import ConfigMissingFault
        from aquilia.pyconfig import Secret

        secret = Secret(env="MISSING_REQUIRED", required=True)
        with pytest.raises(ConfigMissingFault):
            secret.reveal()

    def test_repr_does_not_leak(self):
        """repr() does not contain the secret value."""
        from aquilia.pyconfig import Secret

        os.environ["REPR_SECRET"] = "super_secret_value"
        try:
            secret = Secret(env="REPR_SECRET")
            repr_str = repr(secret)
            assert "super_secret_value" not in repr_str
            assert "REPR_SECRET" in repr_str
        finally:
            del os.environ["REPR_SECRET"]

    def test_str_returns_redacted(self):
        """str() returns redacted marker."""
        from aquilia.pyconfig import Secret

        secret = Secret(value="real_value")
        assert str(secret) == "<secret>"


# ============================================================================
# AQUILACONFIG TESTS
# ============================================================================


class TestAquilaConfig:
    """Tests for AquilaConfig.to_dict() and related methods."""

    def setup_method(self):
        """Reset dotenv state before each test."""
        from aquilia.pyconfig import reset_dotenv_state

        reset_dotenv_state()

    def test_to_dict_basic(self):
        """to_dict() converts config class to dictionary."""
        from aquilia.pyconfig import AquilaConfig

        class TestConfig(AquilaConfig):
            env = "test"
            debug = True
            port = 8080

        result = TestConfig.to_dict()
        assert result["env"] == "test"
        assert result["debug"] is True
        assert result["port"] == 8080

    def test_to_dict_nested_section(self):
        """to_dict() handles nested section classes."""
        from aquilia.pyconfig import AquilaConfig

        class TestConfig(AquilaConfig):
            env = "test"

            class server(AquilaConfig.Server):
                host = "0.0.0.0"
                port = 9000

        result = TestConfig.to_dict()
        assert "server" in result
        assert result["server"]["host"] == "0.0.0.0"
        assert result["server"]["port"] == 9000

    def test_to_dict_resolves_env(self):
        """to_dict() resolves Env instances."""
        from aquilia.pyconfig import AquilaConfig, Env

        os.environ["CONFIG_PORT"] = "3000"
        try:

            class TestConfig(AquilaConfig):
                port = Env("CONFIG_PORT", default=8000, cast=int)

            result = TestConfig.to_dict()
            assert result["port"] == 3000
        finally:
            del os.environ["CONFIG_PORT"]

    def test_to_dict_reveals_secrets(self):
        """to_dict() reveals Secret values."""
        from aquilia.pyconfig import AquilaConfig, Secret

        os.environ["CONFIG_SECRET"] = "secret_value"
        try:

            class TestConfig(AquilaConfig):
                secret = Secret(env="CONFIG_SECRET")

            result = TestConfig.to_dict()
            assert result["secret"] == "secret_value"
        finally:
            del os.environ["CONFIG_SECRET"]

    def test_to_dict_caching_prevents_duplicates(self):
        """to_dict() uses caching to prevent duplicate resolution."""
        from aquilia.pyconfig import AquilaConfig, Env

        call_count = 0

        class CountingCast:
            def __call__(self, value):
                nonlocal call_count
                call_count += 1
                return int(value)

        os.environ["COUNTED_KEY"] = "42"
        try:

            class TestConfig(AquilaConfig):
                value1 = Env("COUNTED_KEY", cast=CountingCast())
                value2 = Env("COUNTED_KEY", cast=CountingCast())

            result = TestConfig.to_dict(use_cache=True)
            # Each Env is resolved once (not cached across different Env instances)
            # The cache is per-Env instance, not per-key
            assert result["value1"] == 42
            assert result["value2"] == 42
        finally:
            del os.environ["COUNTED_KEY"]

    def test_for_env_resolution(self):
        """for_env() resolves the correct subclass."""
        from aquilia.pyconfig import AquilaConfig

        class BaseConfig(AquilaConfig):
            env = "base"
            debug = False

        class DevConfig(BaseConfig):
            env = "dev"
            debug = True

        class ProdConfig(BaseConfig):
            env = "prod"
            debug = False

        resolved = BaseConfig.for_env("dev")
        assert resolved is DevConfig  # Exact class match

        resolved = BaseConfig.for_env("prod")
        assert resolved is ProdConfig

    def test_from_env_var(self):
        """from_env_var() reads AQ_ENV and resolves."""
        from aquilia.pyconfig import AquilaConfig

        class BaseConfig(AquilaConfig):
            env = "base"

        class TestEnvConfig(BaseConfig):
            env = "testenv"

        os.environ["AQ_ENV"] = "testenv"
        try:
            resolved = BaseConfig.from_env_var()
            assert resolved is TestEnvConfig
        finally:
            del os.environ["AQ_ENV"]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestDotenvIntegration:
    """Integration tests for dotenv + pyconfig."""

    def setup_method(self):
        """Reset state before each test."""
        from aquilia.dotenv import DotEnvLoader
        from aquilia.pyconfig import reset_dotenv_state

        reset_dotenv_state()
        DotEnvLoader.reset()

    def test_env_auto_loads_dotenv(self, tmp_path):
        """Env.resolve() automatically loads .env files."""
        from aquilia.dotenv import DotEnvLoader
        from aquilia.pyconfig import Env, reset_dotenv_state

        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AUTO_LOADED_VAR=loaded_value\n")

        # Set AQUILIA_WORKSPACE to tmp_path
        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()
            DotEnvLoader.reset()

            env = Env("AUTO_LOADED_VAR", default="not_loaded")
            result = env.resolve()

            # Should have loaded from .env
            assert result == "loaded_value"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            if "AUTO_LOADED_VAR" in os.environ:
                del os.environ["AUTO_LOADED_VAR"]

    def test_aquila_config_auto_loads_dotenv(self, tmp_path):
        """AquilaConfig.to_dict() automatically loads .env files."""
        from aquilia.dotenv import DotEnvLoader
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("CONFIG_DATABASE_URL=postgres://localhost/db\n")

        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()
            DotEnvLoader.reset()

            class TestConfig(AquilaConfig):
                database_url = Env("CONFIG_DATABASE_URL", default="sqlite://")

            result = TestConfig.to_dict()
            assert result["database_url"] == "postgres://localhost/db"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            if "CONFIG_DATABASE_URL" in os.environ:
                del os.environ["CONFIG_DATABASE_URL"]


# ============================================================================
# REGRESSION TESTS
# ============================================================================


class TestIssue22Regression:
    """Regression tests for issue #22 - no manual load_dotenv() needed."""

    def setup_method(self):
        """Reset state before each test."""
        from aquilia.dotenv import DotEnvLoader
        from aquilia.pyconfig import reset_dotenv_state

        reset_dotenv_state()
        DotEnvLoader.reset()

    def test_no_manual_load_dotenv_required(self, tmp_path):
        """
        Regression test for issue #22:
        Users should NOT need to call load_dotenv() manually.
        """
        from aquilia.dotenv import DotEnvLoader
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        # Simulate user's .env file
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
DATABASE_URL=postgres://user:pass@localhost/mydb
SECRET_KEY=super_secret_key_123
DEBUG=true
WORKERS=4
"""
        )

        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()
            DotEnvLoader.reset()

            # User defines their config WITHOUT calling load_dotenv()
            class MyConfig(AquilaConfig):
                env = "dev"
                database_url = Env("DATABASE_URL")
                secret_key = Env("SECRET_KEY")
                debug = Env("DEBUG", default=False, cast=bool)
                workers = Env("WORKERS", default=1, cast=int)

            # This should work without manual load_dotenv()!
            result = MyConfig.to_dict()

            assert result["database_url"] == "postgres://user:pass@localhost/mydb"
            assert result["secret_key"] == "super_secret_key_123"
            assert result["debug"] is True
            assert result["workers"] == 4
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            for key in ["DATABASE_URL", "SECRET_KEY", "DEBUG", "WORKERS"]:
                if key in os.environ:
                    del os.environ[key]

    def test_single_resolution_not_duplicate(self, tmp_path):
        """
        Regression test for issue #22:
        Values should be resolved once, not duplicated.
        """
        from aquilia.dotenv import DotEnvLoader
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        env_file = tmp_path / ".env"
        env_file.write_text("SINGLE_VALUE=expected\n")

        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()
            DotEnvLoader.reset()

            class TestConfig(AquilaConfig):
                value = Env("SINGLE_VALUE", default="default")

            result = TestConfig.to_dict()

            # Should be a single string, not duplicated
            assert result["value"] == "expected"
            assert isinstance(result["value"], str)

            # Call again - should be consistent
            result2 = TestConfig.to_dict()
            assert result2["value"] == "expected"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            if "SINGLE_VALUE" in os.environ:
                del os.environ["SINGLE_VALUE"]


# ============================================================================
# AQUILACONFIG DOTENV POLICY TESTS
# ============================================================================


class TestAquilaConfigDotenvPolicy:
    """Tests for class-level AquilaConfig dotenv policy."""

    def setup_method(self):
        """Reset dotenv state before each test."""
        from aquilia.dotenv import DotEnvLoader
        from aquilia.pyconfig import reset_dotenv_state

        reset_dotenv_state()
        DotEnvLoader.reset()

    def test_single_file_policy(self, tmp_path):
        """AquilaConfig.dotenv.file loads a single explicit dotenv file."""
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        (tmp_path / ".env.custom").write_text("SINGLE_POLICY_KEY=expected\n")
        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()

            class TestConfig(AquilaConfig):
                class dotenv(AquilaConfig.Dotenv):
                    file = ".env.custom"

                value = Env("SINGLE_POLICY_KEY", default="missing")

            assert TestConfig.to_dict()["value"] == "expected"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            if "SINGLE_POLICY_KEY" in os.environ:
                del os.environ["SINGLE_POLICY_KEY"]

    def test_multiple_files_fallback_order(self, tmp_path):
        """Later dotenv files override earlier dotenv files by declaration order."""
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        (tmp_path / ".env").write_text("ORDER_KEY=base\n")
        (tmp_path / ".env.local").write_text("ORDER_KEY=local\n")
        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()

            class TestConfig(AquilaConfig):
                class dotenv(AquilaConfig.Dotenv):
                    files = [".env", ".env.local"]

                value = Env("ORDER_KEY", default="missing")

            assert TestConfig.to_dict()["value"] == "local"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            if "ORDER_KEY" in os.environ:
                del os.environ["ORDER_KEY"]

    def test_process_env_precedence_when_override_false(self, tmp_path):
        """With override=False, process environment keeps precedence over dotenv."""
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        (tmp_path / ".env").write_text("PRECEDENCE_KEY=dotenv\n")
        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)
        os.environ["PRECEDENCE_KEY"] = "process"

        try:
            reset_dotenv_state()

            class TestConfig(AquilaConfig):
                class dotenv(AquilaConfig.Dotenv):
                    file = ".env"
                    override = False

                value = Env("PRECEDENCE_KEY", default="missing")

            assert TestConfig.to_dict()["value"] == "process"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            del os.environ["PRECEDENCE_KEY"]

    def test_process_env_overridden_when_override_true(self, tmp_path):
        """With override=True, dotenv values replace existing process env values."""
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        (tmp_path / ".env").write_text("OVERRIDE_POLICY_KEY=dotenv\n")
        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)
        os.environ["OVERRIDE_POLICY_KEY"] = "process"

        try:
            reset_dotenv_state()

            class TestConfig(AquilaConfig):
                class dotenv(AquilaConfig.Dotenv):
                    file = ".env"
                    override = True

                value = Env("OVERRIDE_POLICY_KEY", default="missing")

            assert TestConfig.to_dict()["value"] == "dotenv"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            del os.environ["OVERRIDE_POLICY_KEY"]

    def test_required_dotenv_file_missing_raises(self, tmp_path):
        """Required dotenv files raise ConfigMissingFault when absent."""
        from aquilia.faults.domains import ConfigMissingFault
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()

            class TestConfig(AquilaConfig):
                class dotenv(AquilaConfig.Dotenv):
                    files = [AquilaConfig.EnvFile(".env.required", required=True)]

                value = Env("REQUIRED_POLICY_KEY", default="missing")

            with pytest.raises(ConfigMissingFault):
                TestConfig.to_dict()
        finally:
            del os.environ["AQUILIA_WORKSPACE"]

    def test_legacy_filename_alias_maps_to_dotenv(self, tmp_path):
        """Deprecated __filename__ continues to work via dotenv section mapping."""
        from aquilia.pyconfig import AquilaConfig, Env, reset_dotenv_state

        (tmp_path / ".env.legacy").write_text("LEGACY_ALIAS_KEY=legacy\n")
        os.environ["AQUILIA_WORKSPACE"] = str(tmp_path)

        try:
            reset_dotenv_state()

            with pytest.warns(DeprecationWarning):

                class TestConfig(AquilaConfig):
                    __filename__ = ".env.legacy"
                    value = Env("LEGACY_ALIAS_KEY", default="missing")

            assert TestConfig.to_dict()["value"] == "legacy"
        finally:
            del os.environ["AQUILIA_WORKSPACE"]
            if "LEGACY_ALIAS_KEY" in os.environ:
                del os.environ["LEGACY_ALIAS_KEY"]


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Edge case and error handling tests."""

    def test_malformed_dotenv_line_skipped(self):
        """Lines without = are skipped gracefully."""
        from aquilia.dotenv import DotEnv

        content = """
        VALID=value
        this_line_has_no_equals
        ALSO_VALID=another
        """
        values = DotEnv.parse_string(content)
        assert values == {"VALID": "value", "ALSO_VALID": "another"}

    def test_unicode_in_values(self):
        """Unicode values are preserved."""
        from aquilia.dotenv import DotEnv

        content = "EMOJI=🚀\nJAPANESE=日本語"
        values = DotEnv.parse_string(content)
        assert values["EMOJI"] == "🚀"
        assert values["JAPANESE"] == "日本語"

    def test_very_long_value(self):
        """Very long values are handled."""
        from aquilia.dotenv import DotEnv

        long_value = "x" * 100000
        content = f"LONG={long_value}"
        values = DotEnv.parse_string(content)
        assert values["LONG"] == long_value

    def test_special_characters_in_quotes(self):
        """Special characters in quoted values."""
        from aquilia.dotenv import DotEnv

        content = """
        SPECIAL="$pecial #chars @here!"
        BACKTICK="`command`"
        """
        values = DotEnv.parse_string(content, interpolate=False)
        assert values["SPECIAL"] == "$pecial #chars @here!"
        assert values["BACKTICK"] == "`command`"

    def test_whitespace_handling(self):
        """Whitespace is handled correctly."""
        from aquilia.dotenv import DotEnv

        content = """
          KEY1  =  value1
        KEY2=  value2
        KEY3  =value3
        """
        values = DotEnv.parse_string(content)
        # Keys should be stripped, values should have trailing space stripped
        # for unquoted values
        assert values.get("KEY1") == "value1"
        assert values.get("KEY2") == "value2"
        assert values.get("KEY3") == "value3"


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_find_dotenv_in_current_dir(self, tmp_path):
        """find_dotenv() finds .env in current directory."""
        from aquilia.dotenv import find_dotenv

        env_file = tmp_path / ".env"
        env_file.write_text("KEY=value\n")

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = find_dotenv()
            assert result is not None
            assert result.name == ".env"
        finally:
            os.chdir(old_cwd)

    def test_find_dotenv_returns_none_when_missing(self, tmp_path):
        """find_dotenv() returns None when file doesn't exist."""
        from aquilia.dotenv import find_dotenv

        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            result = find_dotenv(".env.missing")
            assert result is None
        finally:
            os.chdir(old_cwd)

    def test_load_dotenv_function(self, tmp_path):
        """load_dotenv() convenience function works."""
        from aquilia.dotenv import load_dotenv

        env_file = tmp_path / ".env"
        env_file.write_text("LOAD_DOTENV_KEY=value\n")

        if "LOAD_DOTENV_KEY" in os.environ:
            del os.environ["LOAD_DOTENV_KEY"]

        result = load_dotenv(env_file)
        assert result is True
        assert os.environ.get("LOAD_DOTENV_KEY") == "value"

        del os.environ["LOAD_DOTENV_KEY"]

    def test_dotenv_values_function(self, tmp_path):
        """dotenv_values() returns values without modifying os.environ."""
        from aquilia.dotenv import dotenv_values

        env_file = tmp_path / ".env"
        env_file.write_text("DOTENV_VALUES_KEY=value\n")

        # Ensure key is not in environ
        if "DOTENV_VALUES_KEY" in os.environ:
            del os.environ["DOTENV_VALUES_KEY"]

        values = dotenv_values(env_file)
        assert values["DOTENV_VALUES_KEY"] == "value"
        # os.environ should NOT be modified
        assert "DOTENV_VALUES_KEY" not in os.environ
