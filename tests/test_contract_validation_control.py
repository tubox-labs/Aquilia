"""
Tests for Contract validation control and alternate data sources
(BP-SEC-032 … BP-SEC-034).

Covers ward ordering/conditions/groups, fail-fast validation, localized
validation messages, and the environment/CLI data sources.
"""

from __future__ import annotations

import pytest

from aquilia.contracts import Contract, ward
from aquilia.contracts.exceptions import SealFault
from aquilia.contracts.facets import BoolFacet, IntFacet, ListFacet, TextFacet
from aquilia.contracts.messages import DEFAULT_MESSAGES, contract_message

# ════════════════════════════════════════════════════════════════════════
# BP-SEC-032 — ward ordering, conditions, and groups
# ════════════════════════════════════════════════════════════════════════


class TestWardOrdering:
    def test_order_controls_sequence(self):
        calls: list[str] = []

        class OrderedContract(Contract):
            name = TextFacet()

            @ward(order=10)
            def last(self, data):
                calls.append("last")

            @ward(order=-10)
            def first(self, data):
                calls.append("first")

            @ward
            def middle(self, data):
                calls.append("middle")

        OrderedContract(data={"name": "x"}).is_sealed()
        assert calls == ["first", "middle", "last"]

    def test_definition_order_preserved_without_explicit_order(self):
        calls: list[str] = []

        class UnorderedContract(Contract):
            name = TextFacet()

            @ward
            def alpha(self, data):
                calls.append("alpha")

            @ward
            def beta(self, data):
                calls.append("beta")

        UnorderedContract(data={"name": "x"}).is_sealed()
        # Unchanged behaviour for wards that do not opt into ordering.
        assert calls == ["alpha", "beta"]


class TestWardConditions:
    def test_when_gates_execution(self):
        calls: list[str] = []

        class ConditionalContract(Contract):
            kind = TextFacet()

            @ward(when=lambda data: data.get("kind") == "physical")
            def needs_shipping(self, data):
                calls.append("shipping")
                self.reject("kind", "shipping address required")

        assert ConditionalContract(data={"kind": "digital"}).is_sealed() is True
        assert calls == []

        assert ConditionalContract(data={"kind": "physical"}).is_sealed() is False
        assert calls == ["shipping"]

    def test_raising_predicate_skips_ward(self):
        class BrokenPredicateContract(Contract):
            name = TextFacet()

            @ward(when=lambda data: data["missing_key"] == 1)
            def never_runs(self, data):
                self.reject("name", "should not happen")

        # A broken gate must not manufacture a validation error.
        assert BrokenPredicateContract(data={"name": "x"}).is_sealed() is True

    def test_rejects_non_callable_when(self):
        with pytest.raises(TypeError, match="expects a callable"):

            @ward(when="not callable")
            def bad(self, data): ...


class TestWardGroups:
    def test_grouped_ward_runs_only_when_requested(self):
        calls: list[str] = []

        class GroupedContract(Contract):
            name = TextFacet()

            @ward(groups=("checkout",))
            def checkout_rule(self, data):
                calls.append("checkout")

            @ward
            def always(self, data):
                calls.append("always")

        GroupedContract(data={"name": "x"}).is_sealed()
        assert calls == ["always"]

        calls.clear()
        GroupedContract(data={"name": "x"}).is_sealed(groups="checkout")
        # Definition order: checkout_rule is declared before always.
        assert calls == ["checkout", "always"]

    def test_group_accepts_sequence(self):
        calls: list[str] = []

        class MultiGroupContract(Contract):
            name = TextFacet()

            @ward(groups=("a", "b"))
            def rule(self, data):
                calls.append("rule")

        MultiGroupContract(data={"name": "x"}).is_sealed(groups=["b"])
        assert calls == ["rule"]

    async def test_groups_apply_to_async_wards(self):
        calls: list[str] = []

        class AsyncGroupContract(Contract):
            name = TextFacet()

            @ward(mode="async", groups=("slow",))
            async def slow_check(self, data):
                calls.append("slow")

        contract = AsyncGroupContract(data={"name": "x"})
        await contract.is_sealed_async()
        assert calls == []

        await AsyncGroupContract(data={"name": "x"}).is_sealed_async(groups="slow")
        assert calls == ["slow"]

    def test_groups_propagate_to_many_children(self):
        calls: list[str] = []

        class RowContract(Contract):
            name = TextFacet()

            @ward(groups=("strict",))
            def strict_rule(self, data):
                calls.append(data["name"])

        contract = RowContract(data=[{"name": "a"}, {"name": "b"}], many=True)
        contract.is_sealed(groups="strict")
        # Groups describe the validation pass, so every row observes them.
        assert calls == ["a", "b"]


class TestFailFast:
    def test_fail_fast_stops_at_first_error(self):
        calls: list[str] = []

        class FailFastContract(Contract):
            name = TextFacet()

            class Spec:
                fail_fast = True

            @ward
            def first(self, data):
                calls.append("first")
                self.reject("name", "first error")

            @ward
            def second(self, data):
                calls.append("second")
                self.reject("name", "second error")

        contract = FailFastContract(data={"name": "x"})
        assert contract.is_sealed() is False
        assert calls == ["first"]
        assert contract.errors == {"name": ["first error"]}

    def test_accumulates_by_default(self):
        class AccumulatingContract(Contract):
            name = TextFacet()

            @ward
            def first(self, data):
                self.reject("name", "first error")

            @ward
            def second(self, data):
                self.reject("name", "second error")

        contract = AccumulatingContract(data={"name": "x"})
        assert contract.is_sealed() is False
        assert contract.errors == {"name": ["first error", "second error"]}


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-033 — localized validation messages
# ════════════════════════════════════════════════════════════════════════


class _MessageContract(Contract):
    name = TextFacet(min_length=8)
    age = IntFacet(min_value=18)


class TestValidationMessages:
    def test_english_default_without_i18n(self):
        contract = _MessageContract(data={"name": "ab", "age": 5})
        contract.is_sealed()
        assert "Must be at least 8 characters" in str(contract.errors["name"])
        assert "Must be at least 18" in str(contract.errors["age"])

    def test_required_message_unchanged(self):
        contract = _MessageContract(data={})
        contract.is_sealed()
        assert contract.errors["name"] == ["This field is required"]

    def test_contract_message_interpolates(self):
        assert contract_message("min_length", min=8) == "Must be at least 8 characters"

    def test_unknown_key_returns_key(self):
        # Never raises: a missing message must not turn a 422 into a 500.
        assert contract_message("no_such_message_key") == "no_such_message_key"

    def test_missing_params_fall_back_to_pattern(self):
        assert contract_message("min_length") == DEFAULT_MESSAGES["min_length"]

    def test_localized_when_service_active(self):
        from aquilia.i18n import I18nConfig, I18nService, MemoryCatalog
        from aquilia.i18n.lazy import clear_lazy_context, set_lazy_context

        catalog = MemoryCatalog(
            {
                "es": {
                    "contracts": {
                        "min_length": "Debe tener al menos {min} caracteres",
                        "required": "Este campo es obligatorio",
                    }
                }
            }
        )
        service = I18nService(
            config=I18nConfig(default_locale="es", available_locales=["es", "en"]),
            catalog=catalog,
        )
        set_lazy_context(service, "es")
        try:
            contract = _MessageContract(data={"name": "ab", "age": 5})
            contract.is_sealed()
            assert "Debe tener al menos 8 caracteres" in str(contract.errors["name"])

            missing = _MessageContract(data={})
            missing.is_sealed()
            assert missing.errors["name"] == ["Este campo es obligatorio"]

            # A key absent from the catalog falls back to English rather than
            # rendering the raw key to an end user.
            assert "Must be at least 18" in str(contract.errors["age"])
        finally:
            clear_lazy_context()

        # Context cleared — back to the built-in text.
        after = _MessageContract(data={})
        after.is_sealed()
        assert after.errors["name"] == ["This field is required"]


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-034 — environment and CLI data sources
# ════════════════════════════════════════════════════════════════════════


class _SettingsContract(Contract):
    port = IntFacet(default=8000)
    database_url = TextFacet()
    debug = BoolFacet(default=False)


class TestFromEnv:
    def test_reads_prefixed_variables(self):
        settings = _SettingsContract.from_env(
            {"APP_PORT": "9000", "APP_DATABASE_URL": "postgres://x", "APP_DEBUG": "true"},
            prefix="APP_",
        )
        assert dict(settings.validated_data) == {
            "port": 9000,
            "database_url": "postgres://x",
            "debug": True,
        }

    def test_absent_variables_use_defaults(self):
        settings = _SettingsContract.from_env({"DATABASE_URL": "sqlite://"})
        assert settings.validated_data["port"] == 8000
        assert settings.validated_data["debug"] is False

    def test_missing_required_raises(self):
        with pytest.raises(SealFault):
            _SettingsContract.from_env({})

    def test_can_defer_validation(self):
        contract = _SettingsContract.from_env({}, seal=False)
        assert contract.is_sealed() is False

    def test_ignores_unrelated_variables(self):
        settings = _SettingsContract.from_env({"DATABASE_URL": "x", "UNRELATED": "y"})
        assert "UNRELATED" not in dict(settings.validated_data)


class _ImportContract(Contract):
    source = TextFacet()
    dry_run = BoolFacet(default=False)
    tags = ListFacet(required=False)


class TestFromCli:
    def test_space_separated_flag(self):
        options = _ImportContract.from_cli(["--source", "data.csv"])
        assert options.validated_data["source"] == "data.csv"

    def test_equals_form(self):
        options = _ImportContract.from_cli(["--source=data.csv"])
        assert options.validated_data["source"] == "data.csv"

    def test_bare_flag_is_boolean(self):
        options = _ImportContract.from_cli(["--source", "x", "--dry-run"])
        assert options.validated_data["dry_run"] is True

    def test_dashes_map_to_underscores(self):
        options = _ImportContract.from_cli(["--source", "x", "--dry-run"])
        assert "dry_run" in dict(options.validated_data)

    def test_repeated_flag_collects_into_list(self):
        options = _ImportContract.from_cli(["--source", "x", "--tags", "a", "--tags", "b"])
        assert options.validated_data["tags"] == ["a", "b"]

    def test_unknown_flags_ignored(self):
        options = _ImportContract.from_cli(["--source", "x", "--not-a-field", "y"])
        assert options.validated_data["source"] == "x"

    def test_missing_required_raises(self):
        with pytest.raises(SealFault):
            _ImportContract.from_cli([])
