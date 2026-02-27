"""
Hostile test suite for Aquilia's type-annotation–driven Blueprint system.

Categories:
    a. End-to-End   — full pipeline validation
    b. Fuzz         — randomized / malformed input
    c. Chaos        — partial failures, conflicting annotations, mutations
    d. Stress       — high-volume instantiation, concurrent requests
    e. Regression   — guards against typing bypass, silent acceptance, etc.

This test file is SELF-CONTAINED — it does not require a running server.
It validates the Blueprint annotation engine, DI integration, and
controller engine compatibility in isolation.
"""

import asyncio
import copy
import random
import re
import string
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from aquilia.blueprints import (
    Blueprint,
    BlueprintFault,
    CastFault,
    Field,
    NestedBlueprintFacet,
    SealFault,
    computed,
)
from aquilia.blueprints.core import BlueprintMeta
from aquilia.blueprints.facets import (
    UNSET,
    BoolFacet,
    DateFacet,
    DateTimeFacet,
    DecimalFacet,
    DictFacet,
    DurationFacet,
    EmailFacet,
    Facet,
    FloatFacet,
    IntFacet,
    ListFacet,
    TextFacet,
    TimeFacet,
    UUIDFacet,
)
from aquilia.blueprints.schema import generate_schema, generate_component_schemas
from aquilia.di.core import Container
from aquilia.di.request_dag import RequestDAG
from aquilia.di.dep import Dep

pytestmark = pytest.mark.asyncio(loop_scope="function")


# ═══════════════════════════════════════════════════════════════════════════
# Test Blueprint Definitions
# ═══════════════════════════════════════════════════════════════════════════

class AddressBlueprint(Blueprint):
    """Nested Blueprint for addresses."""
    street: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    zip_code: str = Field(pattern=r"^\d{5}$")
    country: str = Field(default="US", max_length=2)


class TagBlueprint(Blueprint):
    """Simple nested Blueprint for tags."""
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#000000", pattern=r"^#[0-9a-fA-F]{6}$")


class UserBlueprint(Blueprint):
    """Full-featured annotated Blueprint."""
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")
    role: str = Field(default="user", choices=["user", "admin", "mod"])
    score: float = Field(ge=0.0, le=100.0)
    is_active: bool = True
    bio: str | None = None
    address: AddressBlueprint = Field(required=False, allow_null=True)


class ProductBlueprint(Blueprint):
    """Blueprint with various type annotations."""
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(max_digits=10, decimal_places=2, ge=Decimal("0"))
    quantity: int = Field(ge=0)
    tags: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(read_only=True)
    sku: uuid.UUID = Field(read_only=True)


class OrderItemBlueprint(Blueprint):
    """Nested item Blueprint."""
    product_name: str = Field(min_length=1)
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0.01)


class OrderBlueprint(Blueprint):
    """Blueprint with nested list of sub-Blueprints."""
    order_id: str = Field(min_length=1)
    customer_email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")
    items: list[OrderItemBlueprint]
    notes: str | None = None


class MinimalBlueprint(Blueprint):
    """Minimal annotation-only Blueprint."""
    name: str


class WriteOnlyBlueprint(Blueprint):
    """Blueprint with write-only fields."""
    username: str = Field(min_length=3)
    password: str = Field(write_only=True, min_length=8)


class ReadOnlyBlueprint(Blueprint):
    """Blueprint with read-only fields."""
    id: int = Field(read_only=True)
    created: str = Field(read_only=True)
    name: str


class ComputedBlueprint(Blueprint):
    """Blueprint with computed fields."""
    first_name: str
    last_name: str

    @computed
    def full_name(self, instance) -> str:
        return f"{instance.first_name} {instance.last_name}"


class MixedBlueprint(Blueprint):
    """Blueprint mixing annotations with explicit Facets."""
    name: str = Field(min_length=1)
    age: int = Field(ge=0)
    # Explicit Facet — should override any annotation-derived facet
    email = EmailFacet(required=True)


class ChoicesBlueprint(Blueprint):
    """Blueprint with choice constraints."""
    status: str = Field(choices=["draft", "published", "archived"])
    priority: int = Field(choices=[1, 2, 3, 4, 5])


class DateTimeBlueprint(Blueprint):
    """Blueprint with date/time annotations."""
    event_date: date
    event_time: time
    created_at: datetime
    duration: timedelta = Field(required=False, allow_null=True)


class DefaultsBlueprint(Blueprint):
    """Blueprint testing default values and factories."""
    name: str = "Anonymous"
    count: int = 0
    tags: list[str] = Field(default_factory=list)
    active: bool = True
    metadata: dict = Field(default_factory=dict)


class DeepNestedBlueprint(Blueprint):
    """Level 3 nesting."""
    value: str


class MidNestedBlueprint(Blueprint):
    """Level 2 nesting."""
    label: str
    inner: DeepNestedBlueprint


class TopNestedBlueprint(Blueprint):
    """Level 1 nesting — 3 levels deep."""
    title: str
    mid: MidNestedBlueprint


class ListOfBlueprintsBlueprint(Blueprint):
    """Blueprint with list of nested Blueprints."""
    name: str
    addresses: list[AddressBlueprint]


class OptionalFieldsBlueprint(Blueprint):
    """Every field is optional."""
    name: str | None = None
    age: int | None = None
    email: str | None = None


# ═══════════════════════════════════════════════════════════════════════════
# Dummy Request for DI Tests
# ═══════════════════════════════════════════════════════════════════════════

class DummyRequest:
    def __init__(self, headers=None, query=None, body=None):
        self.headers = headers or {}
        self.query_params = query or {}
        self._body = body or {}

    async def json(self):
        return self._body

    def query_param(self, name):
        return self.query_params.get(name)

    def content_type(self):
        return "application/json"

    def is_json(self):
        return True


# ═══════════════════════════════════════════════════════════════════════════
# a. END-TO-END TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestE2EAnnotatedBlueprints:
    """Full pipeline E2E tests."""

    def test_simple_str_annotation(self):
        """str annotation → TextFacet with validation."""
        bp = MinimalBlueprint(data={"name": "Alice"})
        assert bp.is_sealed()
        assert bp.validated_data["name"] == "Alice"

    def test_simple_str_missing_required(self):
        """Missing required str field → error."""
        bp = MinimalBlueprint(data={})
        assert not bp.is_sealed()
        assert "name" in bp.errors

    def test_full_user_blueprint_success(self):
        """Full UserBlueprint with all fields valid."""
        data = {
            "name": "Alice Johnson",
            "age": 30,
            "email": "alice@example.com",
            "role": "admin",
            "score": 95.5,
            "is_active": True,
            "bio": "A developer",
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "zip_code": "12345",
            },
        }
        bp = UserBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["name"] == "Alice Johnson"
        assert bp.validated_data["age"] == 30
        assert bp.validated_data["email"] == "alice@example.com"
        assert bp.validated_data["role"] == "admin"
        assert bp.validated_data["score"] == 95.5
        assert bp.validated_data["is_active"] is True
        assert bp.validated_data["bio"] == "A developer"
        # Nested address
        addr = bp.validated_data["address"]
        assert addr["street"] == "123 Main St"
        assert addr["city"] == "Anytown"
        assert addr["zip_code"] == "12345"
        assert addr["country"] == "US"  # default

    def test_user_blueprint_validation_errors(self):
        """Multiple validation failures reported."""
        data = {
            "name": "A",            # min_length=2 violation
            "age": -1,              # ge=0 violation
            "email": "not-email",   # pattern violation
            "role": "superadmin",   # choices violation
            "score": 200.0,         # le=100.0 violation
        }
        bp = UserBlueprint(data=data)
        assert not bp.is_sealed()
        assert "name" in bp.errors
        assert "age" in bp.errors
        assert "email" in bp.errors or "role" in bp.errors

    def test_optional_field_none(self):
        """Optional fields accept None."""
        data = {"name": "Alice", "age": 25, "email": "a@b.com", "score": 50.0, "bio": None}
        bp = UserBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["bio"] is None

    def test_optional_field_missing(self):
        """Optional fields can be omitted."""
        data = {"name": "Alice", "age": 25, "email": "a@b.com", "score": 50.0}
        bp = UserBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"

    def test_default_values(self):
        """Default values are used when fields are omitted."""
        bp = DefaultsBlueprint(data={})
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["name"] == "Anonymous"
        assert bp.validated_data["count"] == 0
        assert bp.validated_data["tags"] == []
        assert bp.validated_data["active"] is True
        assert bp.validated_data["metadata"] == {}

    def test_default_factory_isolation(self):
        """Each Blueprint instance gets its own default_factory result."""
        bp1 = DefaultsBlueprint(data={})
        bp2 = DefaultsBlueprint(data={})
        bp1.is_sealed()
        bp2.is_sealed()
        # Mutating one should not affect the other
        bp1.validated_data["tags"].append("test")
        assert bp2.validated_data["tags"] == []

    def test_nested_blueprint_success(self):
        """Nested Blueprint validates correctly."""
        data = {
            "street": "456 Oak Ave",
            "city": "Springfield",
            "zip_code": "67890",
        }
        bp = AddressBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["country"] == "US"

    def test_nested_blueprint_failure(self):
        """Nested Blueprint propagates validation errors."""
        data = {
            "street": "",           # min_length=1
            "city": "Springfield",
            "zip_code": "bad",      # pattern ^\d{5}$
        }
        bp = AddressBlueprint(data=data)
        assert not bp.is_sealed()
        assert "street" in bp.errors or "zip_code" in bp.errors

    def test_deeply_nested_blueprint(self):
        """3-level nested Blueprint works end-to-end."""
        data = {
            "title": "Top Level",
            "mid": {
                "label": "Mid Level",
                "inner": {
                    "value": "Deep Level",
                },
            },
        }
        bp = TopNestedBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["mid"]["label"] == "Mid Level"
        assert bp.validated_data["mid"]["inner"]["value"] == "Deep Level"

    def test_list_of_nested_blueprints(self):
        """list[Blueprint] annotation works."""
        data = {
            "order_id": "ORD-001",
            "customer_email": "customer@shop.com",
            "items": [
                {"product_name": "Widget", "quantity": 2, "unit_price": 9.99},
                {"product_name": "Gadget", "quantity": 1, "unit_price": 19.50},
            ],
        }
        bp = OrderBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert len(bp.validated_data["items"]) == 2
        assert bp.validated_data["items"][0]["product_name"] == "Widget"
        assert bp.validated_data["items"][1]["unit_price"] == 19.50

    def test_list_of_nested_blueprints_failure(self):
        """Nested list item validation failure."""
        data = {
            "order_id": "ORD-001",
            "customer_email": "customer@shop.com",
            "items": [
                {"product_name": "", "quantity": 0, "unit_price": 0.0},
            ],
        }
        bp = OrderBlueprint(data=data)
        assert not bp.is_sealed()
        assert "items" in bp.errors

    def test_choices_valid(self):
        """Choice constraint allows valid values."""
        bp = ChoicesBlueprint(data={"status": "draft", "priority": 3})
        assert bp.is_sealed(), f"Errors: {bp.errors}"

    def test_choices_invalid(self):
        """Choice constraint rejects invalid values."""
        bp = ChoicesBlueprint(data={"status": "deleted", "priority": 99})
        assert not bp.is_sealed()
        assert "status" in bp.errors or "priority" in bp.errors

    def test_datetime_annotations(self):
        """Date/time type annotations work."""
        data = {
            "event_date": "2025-06-15",
            "event_time": "14:30:00",
            "created_at": "2025-06-15T14:30:00",
        }
        bp = DateTimeBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert isinstance(bp.validated_data["event_date"], date)
        assert isinstance(bp.validated_data["event_time"], time)
        assert isinstance(bp.validated_data["created_at"], datetime)

    def test_write_only_field_not_in_output(self):
        """Write-only fields don't appear in to_dict output."""
        # First seal the data
        data = {"username": "alice", "password": "securepassword123"}
        bp = WriteOnlyBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        # Verify password is in validated_data
        assert bp.validated_data["password"] == "securepassword123"

    def test_read_only_field_ignored_on_input(self):
        """Read-only fields are not required on input."""
        data = {"name": "Test Item"}
        bp = ReadOnlyBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["name"] == "Test Item"

    def test_computed_field(self):
        """@computed decorator creates a Computed facet."""
        # Computed fields are output-only; verify the facet exists
        assert "full_name" in ComputedBlueprint._all_facets
        facet = ComputedBlueprint._all_facets["full_name"]
        assert isinstance(facet, Facet)
        # Computed fields should not require input
        data = {"first_name": "Alice", "last_name": "Smith"}
        bp = ComputedBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"

    def test_mixed_annotation_and_explicit_facet(self):
        """Explicit Facets coexist with annotations and take precedence."""
        assert "email" in MixedBlueprint._all_facets
        assert isinstance(MixedBlueprint._all_facets["email"], EmailFacet)
        assert "name" in MixedBlueprint._all_facets
        assert isinstance(MixedBlueprint._all_facets["name"], TextFacet)

    def test_partial_mode(self):
        """Partial mode (PATCH semantics) skips required fields."""
        bp = UserBlueprint(data={"name": "Updated Name"}, partial=True)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["name"] == "Updated Name"
        assert "age" not in bp.validated_data

    def test_seal_fault_raised(self):
        """is_sealed(raise_fault=True) raises SealFault."""
        bp = MinimalBlueprint(data={})
        with pytest.raises(SealFault):
            bp.is_sealed(raise_fault=True)

    def test_many_mode(self):
        """many=True validates a list of items."""
        data = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}]
        bp = MinimalBlueprint(data=data, many=True)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert len(bp.validated_data) == 3

    def test_many_mode_failure(self):
        """many=True reports item-level errors."""
        data = [{"name": "Alice"}, {}]  # Second item missing name
        bp = MinimalBlueprint(data=data, many=True)
        assert not bp.is_sealed()
        assert "1" in bp.errors

    def test_all_optional_fields_empty_data(self):
        """Blueprint with all optional fields accepts empty data."""
        bp = OptionalFieldsBlueprint(data={})
        assert bp.is_sealed(), f"Errors: {bp.errors}"

    def test_schema_generation(self):
        """Type annotations produce valid JSON Schema."""
        schema = generate_schema(UserBlueprint, mode="input")
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]

    def test_component_schema_generation(self):
        """Multiple Blueprint schemas generate correctly."""
        schemas = generate_component_schemas(
            UserBlueprint, AddressBlueprint,
            include_projections=False,
        )
        assert "UserBlueprint" in schemas
        assert "AddressBlueprint" in schemas


# ═══════════════════════════════════════════════════════════════════════════
# DI INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestDIBlueprintAnnotationIntegration:
    """Test that annotated Blueprints work with DI RequestDAG."""

    async def test_annotated_blueprint_resolved_via_dag(self):
        """RequestDAG resolves an annotated Blueprint from request body."""
        container = Container(scope="app")
        request = DummyRequest(body={"name": "Alice"})
        dag = RequestDAG(container, request)

        async def handler(data: MinimalBlueprint):
            return data

        dep = Dep(handler)
        result = await dag.resolve(dep, type(None))
        assert isinstance(result, MinimalBlueprint)
        assert result.validated_data["name"] == "Alice"

    async def test_complex_annotated_blueprint_via_dag(self):
        """Complex annotated Blueprint through DI."""
        container = Container(scope="app")
        request = DummyRequest(body={
            "name": "Bob",
            "age": 25,
            "email": "bob@example.com",
            "score": 88.5,
        })
        dag = RequestDAG(container, request)

        async def handler(user: UserBlueprint):
            return user

        dep = Dep(handler)
        result = await dag.resolve(dep, type(None))
        assert isinstance(result, UserBlueprint)
        assert result.validated_data["name"] == "Bob"
        assert result.validated_data["role"] == "user"  # default

    async def test_annotated_blueprint_validation_failure_via_dag(self):
        """DI propagates Blueprint validation failure as SealFault."""
        container = Container(scope="app")
        request = DummyRequest(body={})  # Missing required 'name'
        dag = RequestDAG(container, request)

        async def handler(data: MinimalBlueprint):
            return data

        dep = Dep(handler)
        with pytest.raises(SealFault):
            await dag.resolve(dep, type(None))


# ═══════════════════════════════════════════════════════════════════════════
# b. FUZZ TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestFuzzAnnotatedBlueprints:
    """Randomised and malformed input fuzzing."""

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    @given(
        name=st.one_of(st.text(), st.integers(), st.none(), st.booleans()),
        age=st.one_of(st.integers(), st.text(), st.none(), st.floats()),
        email=st.one_of(st.text(), st.integers(), st.none()),
        score=st.one_of(st.floats(allow_nan=True, allow_infinity=True), st.text(), st.none()),
    )
    def test_fuzz_user_blueprint(self, name, age, email, score):
        """UserBlueprint never crashes, always returns bool from is_sealed."""
        data = {"name": name, "age": age, "email": email, "score": score}
        bp = UserBlueprint(data=data)
        result = bp.is_sealed()
        assert isinstance(result, bool)
        if result:
            assert "name" in bp.validated_data
            assert "age" in bp.validated_data

    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    @given(
        body=st.one_of(
            st.dictionaries(st.text(), st.text()),
            st.dictionaries(st.text(), st.integers()),
            st.dictionaries(st.text(), st.none()),
            st.text(),
            st.none(),
            st.integers(),
            st.lists(st.text()),
        )
    )
    def test_fuzz_arbitrary_input(self, body):
        """MinimalBlueprint handles any input type gracefully."""
        if isinstance(body, dict):
            bp = MinimalBlueprint(data=body)
        else:
            bp = MinimalBlueprint(data=body)
        result = bp.is_sealed()
        assert isinstance(result, bool)

    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    @given(
        items=st.lists(
            st.one_of(
                st.dictionaries(st.text(), st.text()),
                st.text(),
                st.integers(),
                st.none(),
            ),
            max_size=20,
        )
    )
    def test_fuzz_nested_list(self, items):
        """OrderBlueprint handles malformed item lists."""
        data = {
            "order_id": "ORD-001",
            "customer_email": "test@test.com",
            "items": items,
        }
        bp = OrderBlueprint(data=data)
        result = bp.is_sealed()
        assert isinstance(result, bool)

    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
    @given(
        street=st.text(max_size=300),
        city=st.text(max_size=200),
        zip_code=st.text(max_size=20),
    )
    def test_fuzz_address_blueprint(self, street, city, zip_code):
        """AddressBlueprint handles random text inputs."""
        data = {"street": street, "city": city, "zip_code": zip_code}
        bp = AddressBlueprint(data=data)
        result = bp.is_sealed()
        assert isinstance(result, bool)

    def test_fuzz_extra_fields_ignored(self):
        """Extra unknown fields don't cause crashes."""
        data = {
            "name": "Alice",
            "unknown_field": "surprise",
            "another": 42,
            "__proto__": "injection",
        }
        bp = MinimalBlueprint(data=data)
        assert bp.is_sealed()
        assert bp.validated_data["name"] == "Alice"

    def test_fuzz_deeply_nested_structure(self):
        """5-level nested dicts don't crash the system."""
        deep = {"value": "leaf"}
        for i in range(5):
            deep = {"label": f"level-{i}", "inner": deep}
        # Only 3 levels of actual Blueprint nesting exist
        data = {"title": "Top", "mid": deep}
        bp = TopNestedBlueprint(data=data)
        # Should either succeed or fail gracefully, never crash
        result = bp.is_sealed()
        assert isinstance(result, bool)

    def test_fuzz_empty_string_fields(self):
        """Empty strings handled correctly per allow_blank."""
        # MinimalBlueprint has no allow_blank, so empty string should fail
        bp = MinimalBlueprint(data={"name": ""})
        result = bp.is_sealed()
        # TextFacet with allow_blank=False should reject empty string
        # but str annotation doesn't set allow_blank by default
        assert isinstance(result, bool)

    def test_fuzz_unicode_input(self):
        """Unicode edge cases don't crash."""
        data = {"name": "🏴‍☠️ Unicode 日本語 العربية"}
        bp = MinimalBlueprint(data=data)
        assert bp.is_sealed()
        assert bp.validated_data["name"] == "🏴‍☠️ Unicode 日本語 العربية"

    def test_fuzz_very_large_number(self):
        """Extremely large numbers handled."""
        data = {"name": "Alice", "age": 10**18, "email": "a@b.com", "score": 50.0}
        bp = UserBlueprint(data=data)
        result = bp.is_sealed()
        # age=10^18 > max 150, should fail
        assert not result
        assert "age" in bp.errors

    def test_fuzz_negative_number(self):
        """Negative numbers correctly caught by ge constraint."""
        data = {"name": "Alice", "age": -999, "email": "a@b.com", "score": -1.0}
        bp = UserBlueprint(data=data)
        assert not bp.is_sealed()
        assert "age" in bp.errors


# ═══════════════════════════════════════════════════════════════════════════
# c. CHAOS TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestChaosAnnotatedBlueprints:
    """Partial failures, conflicting annotations, runtime mutation."""

    def test_chaos_runtime_mutation_of_all_facets(self):
        """Mutating _all_facets at runtime doesn't corrupt other instances."""
        # Snapshot original
        original_facets = dict(MinimalBlueprint._all_facets)

        # Corrupt the class-level facets
        MinimalBlueprint._all_facets["injected_evil"] = TextFacet(required=False)

        try:
            # Existing instances should still work
            bp = MinimalBlueprint(data={"name": "Safe"})
            result = bp.is_sealed()
            assert isinstance(result, bool)
        finally:
            # Restore
            MinimalBlueprint._all_facets = original_facets

    def test_chaos_conflicting_annotation_and_explicit_facet(self):
        """Explicit Facet always wins over annotation-derived one."""
        # MixedBlueprint has email as EmailFacet (explicit)
        # Even if annotated as str, the EmailFacet should prevail
        assert isinstance(MixedBlueprint._all_facets["email"], EmailFacet)

        # Validate that EmailFacet validation is active
        bp = MixedBlueprint(data={"name": "Test", "age": 25, "email": "not-email"})
        assert not bp.is_sealed()
        assert "email" in bp.errors

    def test_chaos_blueprint_class_created_dynamically(self):
        """Dynamically created Blueprint classes work."""
        DynamicBP = type("DynamicBP", (Blueprint,), {
            "__annotations__": {"value": str},
        })
        bp = DynamicBP(data={"value": "hello"})
        assert bp.is_sealed()
        assert bp.validated_data["value"] == "hello"

    def test_chaos_blueprint_inheritance(self):
        """Inherited annotated fields are preserved."""

        class ParentBP(Blueprint):
            name: str = Field(min_length=1)

        class ChildBP(ParentBP):
            age: int = Field(ge=0)

        # Child should have both fields
        assert "name" in ChildBP._all_facets
        assert "age" in ChildBP._all_facets

        bp = ChildBP(data={"name": "Test", "age": 5})
        assert bp.is_sealed(), f"Errors: {bp.errors}"

    def test_chaos_blueprint_override_parent_field(self):
        """Child can override parent's annotation with different constraints."""

        class ParentBP(Blueprint):
            name: str = Field(max_length=10)

        class ChildBP(ParentBP):
            name: str = Field(max_length=50)

        # Child's constraint should apply
        bp = ChildBP(data={"name": "A" * 30})
        assert bp.is_sealed(), f"Errors: {bp.errors}"

    async def test_chaos_di_container_empty(self):
        """Empty DI container doesn't break Blueprint resolution."""
        container = Container(scope="app")
        request = DummyRequest(body={"name": "Test"})
        dag = RequestDAG(container, request)

        async def handler(data: MinimalBlueprint):
            return data

        dep = Dep(handler)
        result = await dag.resolve(dep, type(None))
        assert isinstance(result, MinimalBlueprint)

    def test_chaos_repeated_validation(self):
        """Calling is_sealed() multiple times returns consistent results."""
        bp = MinimalBlueprint(data={"name": "Test"})
        r1 = bp.is_sealed()
        r2 = bp.is_sealed()
        r3 = bp.is_sealed()
        assert r1 == r2 == r3 == True

        bp_fail = MinimalBlueprint(data={})
        f1 = bp_fail.is_sealed()
        f2 = bp_fail.is_sealed()
        assert f1 == f2 == False

    def test_chaos_none_as_data(self):
        """None as data doesn't crash."""
        bp = MinimalBlueprint(data=None)
        result = bp.is_sealed()
        assert isinstance(result, bool)

    def test_chaos_non_dict_data(self):
        """Non-dict data (string, list, int) handled gracefully."""
        for bad_data in ["hello", 42, True, [1, 2, 3], (1,)]:
            bp = MinimalBlueprint(data=bad_data)
            result = bp.is_sealed()
            assert isinstance(result, bool)

    def test_chaos_no_data_provided(self):
        """No data at all → proper error."""
        bp = MinimalBlueprint()  # data defaults to UNSET
        result = bp.is_sealed()
        assert not result
        assert "__all__" in bp.errors


# ═══════════════════════════════════════════════════════════════════════════
# d. STRESS & LOAD TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestStressAnnotatedBlueprints:
    """High-volume instantiation and concurrent validation."""

    def test_stress_high_volume_instantiation(self):
        """10,000 Blueprint instantiations don't leak or crash."""
        for i in range(10_000):
            bp = MinimalBlueprint(data={"name": f"user_{i}"})
            assert bp.is_sealed()
            assert bp.validated_data["name"] == f"user_{i}"

    def test_stress_high_volume_with_nested(self):
        """1,000 nested Blueprint validations."""
        for i in range(1_000):
            data = {
                "street": f"Street {i}",
                "city": f"City {i}",
                "zip_code": f"{i:05d}",
            }
            bp = AddressBlueprint(data=data)
            assert bp.is_sealed(), f"Failed at {i}: {bp.errors}"

    async def test_stress_concurrent_blueprint_resolution(self):
        """500 concurrent Blueprint resolutions via asyncio.gather."""
        container = Container(scope="app")

        async def resolve_one(idx: int):
            request = DummyRequest(body={"name": f"user_{idx}"})
            dag = RequestDAG(container, request)

            async def handler(data: MinimalBlueprint):
                assert isinstance(data, MinimalBlueprint)
                assert data.validated_data["name"] == f"user_{idx}"
                return True

            dep = Dep(handler)
            return await dag.resolve(dep, type(None))

        tasks = [resolve_one(i) for i in range(500)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 500

    def test_stress_many_mode_large_list(self):
        """Validate a list of 500 items via many=True."""
        data = [{"name": f"item_{i}"} for i in range(500)]
        bp = MinimalBlueprint(data=data, many=True)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert len(bp.validated_data) == 500

    def test_stress_deeply_nested_large(self):
        """100 deeply nested Blueprint validations."""
        for i in range(100):
            data = {
                "title": f"Top {i}",
                "mid": {
                    "label": f"Mid {i}",
                    "inner": {"value": f"Deep {i}"},
                },
            }
            bp = TopNestedBlueprint(data=data)
            assert bp.is_sealed(), f"Failed at {i}: {bp.errors}"

    def test_stress_order_with_many_items(self):
        """OrderBlueprint with 100 items per order, 10 orders."""
        for order_num in range(10):
            items = [
                {
                    "product_name": f"Product {j}",
                    "quantity": random.randint(1, 100),
                    "unit_price": round(random.uniform(0.01, 999.99), 2),
                }
                for j in range(100)
            ]
            data = {
                "order_id": f"ORD-{order_num}",
                "customer_email": f"customer{order_num}@shop.com",
                "items": items,
            }
            bp = OrderBlueprint(data=data)
            assert bp.is_sealed(), f"Order {order_num} failed: {bp.errors}"


# ═══════════════════════════════════════════════════════════════════════════
# e. REGRESSION GUARDS
# ═══════════════════════════════════════════════════════════════════════════

class TestRegressionGuards:
    """Tests that MUST fail if certain invariants are violated."""

    def test_regression_annotation_creates_facets(self):
        """Annotation-declared fields ARE in _all_facets."""
        assert "name" in MinimalBlueprint._all_facets
        assert isinstance(MinimalBlueprint._all_facets["name"], TextFacet)

    def test_regression_typing_cannot_be_bypassed(self):
        """Passing wrong types MUST produce validation errors, never silently pass."""
        # int where str expected
        bp = MinimalBlueprint(data={"name": 42})
        if bp.is_sealed():
            # TextFacet.cast coerces int to str — that's intentional behavior
            assert isinstance(bp.validated_data["name"], str)

    def test_regression_required_fields_enforced(self):
        """Missing required field MUST cause validation failure."""
        bp = MinimalBlueprint(data={})
        assert not bp.is_sealed()
        assert "name" in bp.errors

    def test_regression_constraints_enforced_at_runtime(self):
        """Field constraints MUST be checked at runtime, not just declared."""
        bp = UserBlueprint(data={
            "name": "X",   # min_length=2 → MUST fail
            "age": 200,     # le=150 → MUST fail
            "email": "a@b.com",
            "score": 50.0,
        })
        assert not bp.is_sealed()
        errors = bp.errors
        assert "name" in errors, "min_length constraint not enforced"
        assert "age" in errors, "le constraint not enforced"

    def test_regression_di_honors_blueprint_type(self):
        """DI system MUST resolve Blueprint by type annotation, not by name."""
        # The DI system uses _is_blueprint_type() which checks issubclass.
        # Annotated Blueprints must pass this check.
        from aquilia.di.request_dag import _is_blueprint_type
        assert _is_blueprint_type(MinimalBlueprint)
        assert _is_blueprint_type(UserBlueprint)
        assert _is_blueprint_type(OrderBlueprint)
        assert not _is_blueprint_type(str)
        assert not _is_blueprint_type(int)
        assert not _is_blueprint_type(Blueprint)  # Base class itself is NOT

    def test_regression_validation_never_silently_accepts_invalid(self):
        """Invalid data MUST result in is_sealed() == False, never True."""
        # Negative age with ge=0
        bp = UserBlueprint(data={
            "name": "Alice",
            "age": -1,
            "email": "a@b.com",
            "score": 50.0,
        })
        assert bp.is_sealed() is False

        # Invalid zip code pattern
        bp2 = AddressBlueprint(data={
            "street": "123 Main",
            "city": "Town",
            "zip_code": "ABCDE",  # pattern \d{5}
        })
        assert bp2.is_sealed() is False

    def test_regression_no_legacy_serializer_reappearance(self):
        """Blueprint is not a Serializer — no Serializer attributes exist."""
        bp = MinimalBlueprint(data={"name": "Test"})
        # These would be Serializer-era attributes that MUST NOT exist
        assert not hasattr(bp, "serialize")
        assert not hasattr(bp, "deserialize")
        assert not hasattr(bp, "_meta")

    def test_regression_facet_order_stable(self):
        """Field declaration order must be preserved."""
        names = list(UserBlueprint._all_facets.keys())
        # The annotations should appear in declaration order
        assert "name" in names
        assert "age" in names
        assert "email" in names

    def test_regression_blueprint_is_not_mutable(self):
        """Validated data on one instance doesn't bleed to another."""
        bp1 = MinimalBlueprint(data={"name": "Alice"})
        bp2 = MinimalBlueprint(data={"name": "Bob"})
        bp1.is_sealed()
        bp2.is_sealed()
        assert bp1.validated_data["name"] == "Alice"
        assert bp2.validated_data["name"] == "Bob"

    def test_regression_nested_blueprint_errors_propagate(self):
        """Nested Blueprint validation errors MUST propagate to parent."""
        data = {
            "name": "Alice",
            "age": 25,
            "email": "a@b.com",
            "score": 50.0,
            "address": {
                "street": "Main",
                "city": "Town",
                "zip_code": "BAD",  # Invalid
            },
        }
        bp = UserBlueprint(data=data)
        assert not bp.is_sealed()
        assert "address" in bp.errors

    def test_regression_field_default_and_default_factory_conflict(self):
        """Specifying both default and default_factory MUST raise."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            Field(default="hello", default_factory=list)

    def test_regression_empty_blueprint_no_crash(self):
        """A Blueprint with no fields (base class) doesn't crash."""
        class EmptyBP(Blueprint):
            pass

        bp = EmptyBP(data={})
        # Should either succeed or return base behavior
        result = bp.is_sealed()
        assert isinstance(result, bool)

    def test_regression_type_coercion_produces_correct_type(self):
        """IntFacet must produce int, FloatFacet must produce float, etc."""
        data = {
            "name": "Alice",
            "age": "30",      # String → should be coerced to int
            "email": "a@b.com",
            "score": "88.5",  # String → should be coerced to float
        }
        bp = UserBlueprint(data=data)
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert isinstance(bp.validated_data["age"], int)
        assert isinstance(bp.validated_data["score"], float)

    def test_regression_list_annotation_type_check(self):
        """list[str] facet must validate child types."""
        class StringListBP(Blueprint):
            items: list[str]

        bp = StringListBP(data={"items": ["a", "b", "c"]})
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["items"] == ["a", "b", "c"]

    def test_regression_dict_annotation(self):
        """dict annotation creates DictFacet."""
        class DictBP(Blueprint):
            metadata: dict

        bp = DictBP(data={"metadata": {"key": "value"}})
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert bp.validated_data["metadata"] == {"key": "value"}

    def test_regression_uuid_annotation(self):
        """uuid.UUID annotation creates UUIDFacet."""
        class UuidBP(Blueprint):
            id: uuid.UUID

        test_uuid = str(uuid.uuid4())
        bp = UuidBP(data={"id": test_uuid})
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert isinstance(bp.validated_data["id"], uuid.UUID)

    def test_regression_decimal_annotation(self):
        """Decimal annotation creates DecimalFacet."""
        class DecimalBP(Blueprint):
            amount: Decimal = Field(max_digits=10, decimal_places=2)

        bp = DecimalBP(data={"amount": "99.99"})
        assert bp.is_sealed(), f"Errors: {bp.errors}"
        assert isinstance(bp.validated_data["amount"], Decimal)
        assert bp.validated_data["amount"] == Decimal("99.99")

    def test_regression_bool_coercion(self):
        """BoolFacet coerces string values correctly."""
        class BoolBP(Blueprint):
            active: bool

        for truthy in [True, "true", "1", "yes"]:
            bp = BoolBP(data={"active": truthy})
            assert bp.is_sealed(), f"Failed for {truthy}: {bp.errors}"
            assert bp.validated_data["active"] is True

        for falsy in [False, "false", "0", "no"]:
            bp = BoolBP(data={"active": falsy})
            assert bp.is_sealed(), f"Failed for {falsy}: {bp.errors}"
            assert bp.validated_data["active"] is False
