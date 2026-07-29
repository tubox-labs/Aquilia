"""
Tests for the Contract typing and ergonomics additions (BP-SEC-028 … BP-SEC-031).

Covers the facets added for strongly-typed primitives that previously fell
through to a permissive ``TextFacet`` or no facet at all, and the Contract-level
helpers (equality, copy-with-update, frozen Contracts).
"""

from __future__ import annotations

import ipaddress
import pathlib

import pytest

from aquilia.contracts import Contract
from aquilia.contracts.exceptions import SealFault
from aquilia.contracts.facets import (
    IntFacet,
    MACAddressFacet,
    PathFacet,
    Secret,
    SecretFacet,
    TextFacet,
)

# ════════════════════════════════════════════════════════════════════════
# BP-SEC-028 — PathFacet refuses to hand a traversal string to the caller
# ════════════════════════════════════════════════════════════════════════


class _PathContract(Contract):
    destination = PathFacet()


class TestPathFacet:
    def test_accepts_relative_path(self):
        contract = _PathContract(data={"destination": "reports/q3.pdf"})
        assert contract.is_sealed() is True
        assert contract.validated_data["destination"] == pathlib.PurePosixPath("reports/q3.pdf")

    @pytest.mark.parametrize(
        ("payload", "reason"),
        [
            ("../../etc/passwd", "'..' segments"),
            ("/etc/passwd", "must be relative"),
            ("nested/../../escape", "'..' segments"),
            ("a\x00b.txt", "null bytes"),
            ("   ", "may not be empty"),
        ],
    )
    def test_rejects_unsafe_paths(self, payload, reason):
        contract = _PathContract(data={"destination": payload})
        assert contract.is_sealed() is False
        assert reason.lower() in str(contract.errors["destination"]).lower()

    def test_rejects_backslash_traversal(self):
        # A Windows-style separator must not smuggle '..' past the check on a
        # POSIX server.
        contract = _PathContract(data={"destination": r"a\..\..\etc"})
        assert contract.is_sealed() is False

    def test_absolute_allowed_when_configured(self):
        class ServerPathContract(Contract):
            root = PathFacet(must_be_relative=False)

        contract = ServerPathContract(data={"root": "/srv/data"})
        assert contract.is_sealed() is True

    def test_traversal_allowed_when_configured(self):
        class RelaxedContract(Contract):
            rel = PathFacet(allow_traversal=True)

        assert RelaxedContract(data={"rel": "../sibling"}).is_sealed() is True

    def test_strict_mode_still_validates(self):
        class StrictPathContract(Contract):
            destination = PathFacet()

            class Spec:
                strict = True

        # seal() re-validates because strict mode skips cast().
        contract = StrictPathContract(data={"destination": "../escape"})
        assert contract.is_sealed() is False

    def test_molds_back_to_string(self):
        class Row:
            destination = pathlib.PurePosixPath("a/b.txt")

        assert _PathContract(instance=Row()).to_dict() == {"destination": "a/b.txt"}

    def test_path_annotation_routes_to_path_facet(self):
        class AnnotatedContract(Contract):
            location: pathlib.Path

        assert isinstance(AnnotatedContract._all_facets["location"], PathFacet)


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-029 — SecretFacet keeps sensitive values out of output and logs
# ════════════════════════════════════════════════════════════════════════


class _LoginContract(Contract):
    username = TextFacet()
    password = SecretFacet(min_length=8)


class TestSecretFacet:
    def test_masks_repr_and_str(self):
        contract = _LoginContract(data={"username": "kai", "password": "hunter2hunter2"})
        assert contract.is_sealed() is True
        secret = contract.validated_data["password"]
        assert "hunter2hunter2" not in repr(secret)
        assert "hunter2hunter2" not in str(secret)
        assert "hunter2hunter2" not in f"{secret}"

    def test_reveal_returns_value(self):
        contract = _LoginContract(data={"username": "kai", "password": "hunter2hunter2"})
        contract.is_sealed()
        assert contract.validated_data["password"].reveal() == "hunter2hunter2"

    def test_constraints_apply_to_underlying_value(self):
        contract = _LoginContract(data={"username": "kai", "password": "short"})
        assert contract.is_sealed() is False
        assert "password" in contract.errors

    def test_write_only_by_default(self):
        class Row:
            username = "kai"
            password = Secret("hunter2hunter2")

        # Omitted from output entirely — a secret cannot leak through the API.
        assert _LoginContract(instance=Row()).to_dict() == {"username": "kai"}

    def test_equality_against_plain_string(self):
        assert Secret("abc") == "abc"
        assert Secret("abc") == Secret("abc")
        assert Secret("abc") != "abd"

    def test_secret_annotation_routes_to_secret_facet(self):
        class AnnotatedContract(Contract):
            token: Secret

        assert isinstance(AnnotatedContract._all_facets["token"], SecretFacet)


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-030 — MACAddressFacet normalizes every accepted notation
# ════════════════════════════════════════════════════════════════════════


class _DeviceContract(Contract):
    mac = MACAddressFacet()


class TestMACAddressFacet:
    @pytest.mark.parametrize(
        "payload",
        ["aa:bb:cc:dd:ee:ff", "AA-BB-CC-DD-EE-FF", "aabb.ccdd.eeff", "AABBCCDDEEFF"],
    )
    def test_normalizes_notations(self, payload):
        contract = _DeviceContract(data={"mac": payload})
        assert contract.is_sealed() is True
        # One canonical form regardless of input notation, so lookups match.
        assert contract.validated_data["mac"] == "aa:bb:cc:dd:ee:ff"

    @pytest.mark.parametrize("payload", ["zz:bb:cc:dd:ee:ff", "aa:bb:cc:dd:ee", "", "aa:bb:cc:dd:ee:ff:00"])
    def test_rejects_invalid(self, payload):
        assert _DeviceContract(data={"mac": payload}).is_sealed() is False

    def test_rejects_non_string(self):
        assert _DeviceContract(data={"mac": 12345}).is_sealed() is False


class TestIPAnnotation:
    def test_ip_annotation_routes_to_ip_facet(self):
        from aquilia.contracts.facets import IPFacet

        class HostContract(Contract):
            address: ipaddress.IPv4Address

        assert isinstance(HostContract._all_facets["address"], IPFacet)


# ════════════════════════════════════════════════════════════════════════
# BP-SEC-031 — Contract equality, copy, and frozen semantics
# ════════════════════════════════════════════════════════════════════════


class _PointContract(Contract):
    name = TextFacet()
    value = IntFacet(min_value=0)


class TestContractEquality:
    def test_equal_by_validated_data(self):
        first = _PointContract(data={"name": "a", "value": 1})
        second = _PointContract(data={"name": "a", "value": 1})
        first.is_sealed()
        second.is_sealed()
        assert first == second

    def test_unequal_by_data(self):
        first = _PointContract(data={"name": "a", "value": 1})
        second = _PointContract(data={"name": "a", "value": 2})
        first.is_sealed()
        second.is_sealed()
        assert first != second

    def test_unequal_across_classes(self):
        class OtherContract(Contract):
            name = TextFacet()
            value = IntFacet()

        first = _PointContract(data={"name": "a", "value": 1})
        second = OtherContract(data={"name": "a", "value": 1})
        first.is_sealed()
        second.is_sealed()
        assert first != second

    def test_non_contract_comparison_is_false(self):
        assert _PointContract(data={"name": "a", "value": 1}) != "not a contract"

    def test_unhashable(self):
        # Defining __eq__ without __hash__ would silently make Contracts
        # unhashable; this makes the reason explicit.
        with pytest.raises(TypeError, match="unhashable"):
            hash(_PointContract(data={"name": "a", "value": 1}))


class TestContractCopy:
    def test_copy_with_update(self):
        original = _PointContract(data={"name": "a", "value": 1})
        original.is_sealed()
        updated = original.copy(update={"value": 2})
        assert dict(updated.validated_data) == {"name": "a", "value": 2}
        # The original is untouched.
        assert dict(original.validated_data) == {"name": "a", "value": 1}

    def test_copy_validates_by_default(self):
        original = _PointContract(data={"name": "a", "value": 1})
        original.is_sealed()
        with pytest.raises(SealFault):
            original.copy(update={"value": -1})

    def test_copy_can_defer_validation(self):
        original = _PointContract(data={"name": "a", "value": 1})
        original.is_sealed()
        draft = original.copy(update={"value": -1}, validate=False)
        assert draft.is_sealed() is False

    def test_copy_from_unsealed_contract(self):
        original = _PointContract(data={"name": "a", "value": 1})
        assert dict(original.copy(update={"value": 3}).validated_data) == {"name": "a", "value": 3}

    async def test_copy_async(self):
        from aquilia.contracts import ward

        class AsyncPointContract(Contract):
            name = TextFacet()
            value = IntFacet(min_value=0)

            @ward(mode="async")
            async def check(self, data):
                if data["value"] == 99:
                    self.reject("value", "reserved")

        original = AsyncPointContract(data={"name": "a", "value": 1})
        await original.is_sealed_async()
        updated = await original.copy_async(update={"value": 2})
        assert dict(updated.validated_data) == {"name": "a", "value": 2}

        with pytest.raises(SealFault):
            await original.copy_async(update={"value": 99})


class TestFrozenContract:
    def test_frozen_rejects_mutation(self):
        class FrozenContract(Contract):
            name = TextFacet()

            class Spec:
                frozen = True

        contract = FrozenContract(data={"name": "a"})
        contract.is_sealed()
        assert contract.validated_data.is_frozen() is True
        with pytest.raises(TypeError):
            contract.validated_data["name"] = "b"

    def test_not_frozen_by_default(self):
        contract = _PointContract(data={"name": "a", "value": 1})
        contract.is_sealed()
        contract.validated_data["name"] = "b"
        assert contract.validated_data["name"] == "b"

    def test_copy_is_the_supported_update_path(self):
        class FrozenContract(Contract):
            name = TextFacet()

            class Spec:
                frozen = True

        contract = FrozenContract(data={"name": "a"})
        contract.is_sealed()
        assert dict(contract.copy(update={"name": "b"}).validated_data) == {"name": "b"}
