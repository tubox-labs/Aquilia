"""
Tests for the ``seal_*``/``async_seal_*`` deprecation (BP-SEC-036).

The legacy prefix convention still registers validators, and must keep doing so
until 2.0.0 — silently dropping a rule mid-1.x would be the exact failure the
deprecation exists to prevent. What changed is that declaring one now emits an
actionable ``DeprecationWarning``.
"""

from __future__ import annotations

import warnings

import pytest

from aquilia.contracts import Contract
from aquilia.contracts.facets import IntFacet
from aquilia.contracts.ward import (
    DEPRECATED_PREFIX_REMOVED_IN,
    DEPRECATED_PREFIX_SINCE,
    legacy_prefix_message,
    ward,
)


# ---------------------------------------------------------------------------
# BP-SEC-036a — the message
# ---------------------------------------------------------------------------


class TestLegacyPrefixMessage:
    def test_names_the_offending_method(self):
        message = legacy_prefix_message("OrderContract", "seal_total", is_async=False)
        assert "OrderContract.seal_total" in message

    def test_sync_method_is_told_to_use_the_bare_decorator(self):
        message = legacy_prefix_message("OrderContract", "seal_total", is_async=False)
        assert "@ward instead" in message

    def test_async_method_is_told_to_declare_the_mode(self):
        """Mode used to be inferred from ``iscoroutinefunction``; the
        replacement must declare it, so the message has to say so."""
        message = legacy_prefix_message("OrderContract", "async_seal_stock", is_async=True)
        assert '@ward(mode="async") instead' in message

    def test_states_both_the_deprecation_and_removal_release(self):
        message = legacy_prefix_message("C", "seal_x", is_async=False)
        assert DEPRECATED_PREFIX_SINCE in message
        assert DEPRECATED_PREFIX_REMOVED_IN in message

    def test_states_the_consequence_of_not_migrating(self):
        """A warning that only says "deprecated" gets filtered. Naming the
        failure — the rule silently stops running — is what makes it act on."""
        message = legacy_prefix_message("C", "seal_x", is_async=False)
        assert "silently stop validating" in message


# ---------------------------------------------------------------------------
# BP-SEC-036b — the warning
# ---------------------------------------------------------------------------


class TestLegacyPrefixWarning:
    def test_sync_prefix_method_warns(self):
        with pytest.warns(DeprecationWarning, match=r"seal_total"):

            class _Order(Contract):
                total = IntFacet()

                def seal_total(self, data): ...

    def test_async_prefix_method_warns(self):
        with pytest.warns(DeprecationWarning, match=r"async_seal_stock"):

            class _Stock(Contract):
                total = IntFacet()

                async def async_seal_stock(self, data): ...

    def test_warning_is_raised_at_class_body_evaluation(self):
        """Importing the module must be enough to surface every offender —
        that is what makes ``python -W error`` a usable audit."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            class _Order(Contract):
                total = IntFacet()

                def seal_total(self, data): ...

        assert any(issubclass(w.category, DeprecationWarning) for w in caught)

    def test_each_legacy_method_warns_separately(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            class _Order(Contract):
                total = IntFacet()

                def seal_total(self, data): ...

                def seal_currency(self, data): ...

        messages = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
        assert any("seal_total" in m for m in messages)
        assert any("seal_currency" in m for m in messages)

    def test_decorated_method_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)

            class _Order(Contract):
                total = IntFacet()

                @ward
                def total_positive(self, data): ...

    def test_decorated_method_keeping_the_legacy_name_does_not_warn(self):
        """The decorator is the registration; the name is then irrelevant. A
        migration that adds ``@ward`` without renaming must go quiet."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)

            class _Order(Contract):
                total = IntFacet()

                @ward
                def seal_total(self, data): ...

    def test_unrelated_method_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)

            class _Order(Contract):
                total = IntFacet()

                def sealed_up(self, data): ...


# ---------------------------------------------------------------------------
# BP-SEC-036c — behavior is unchanged until 2.0.0
# ---------------------------------------------------------------------------


class TestLegacyPrefixStillRuns:
    def test_legacy_sync_validator_still_rejects(self):
        """Deprecating the convention must not disarm it: a rule that stopped
        firing in a patch release would ship the exact bug the deprecation
        warns about."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            class _Order(Contract):
                total = IntFacet()

                def seal_total(self, data):
                    if data["total"] < 0:
                        self.reject("total", "Must not be negative")

        contract = _Order(data={"total": -5})
        assert contract.is_sealed() is False
        assert "total" in contract.errors

    def test_legacy_validator_registers_as_a_ward(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            class _Order(Contract):
                total = IntFacet()

                def seal_total(self, data): ...

        assert [wm.name for wm in _Order._ward_methods] == ["seal_total"]

    def test_legacy_async_validator_registers_in_async_mode(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            class _Stock(Contract):
                total = IntFacet()

                async def async_seal_stock(self, data): ...

        assert [wm.mode for wm in _Stock._ward_methods] == ["async"]

    async def test_legacy_async_validator_still_rejects(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            class _Stock(Contract):
                total = IntFacet()

                async def async_seal_stock(self, data):
                    if data["total"] > 10:
                        self.reject("total", "Out of stock")

        contract = _Stock(data={"total": 99})
        assert await contract.is_sealed_async() is False
        assert "total" in contract.errors

    def test_decorator_wins_over_the_prefix_for_the_same_method(self):
        """``@ward`` sets ``__ward_meta__``, which the prefix scan skips — so
        the decorator's ``order``/``groups`` survive rather than being
        overwritten by a default-constructed legacy entry."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            class _Order(Contract):
                total = IntFacet()

                @ward(order=-5)
                def seal_total(self, data): ...

        assert [wm.order for wm in _Order._ward_methods] == [-5]
