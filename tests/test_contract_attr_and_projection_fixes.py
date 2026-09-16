"""
Regression tests for the Contracts attribute-access and projection fixes.

Each class pins one fix from the contracts-subsystem audit (cross-review
validated): F1/F2 namespace hygiene + synthetic-None attribute access, N1
Optional unwrapping for raw Facet in Annotated, N2 empty projection include
lists, N3 ClassVar/InitVar annotations, N4 bare Field(...) without an
annotation, F-CORE-09 implicitly derived model facets, F-CO-LEAK silently
derived model columns leaking into default projections, and F-CORE-10 clean
collection child-fault messages.

The tests are written to fail loudly if the old behaviour is ever
reintroduced, so they double as executable documentation of why each fix
exists.
"""

from __future__ import annotations

import copy
import pickle
import warnings
from types import SimpleNamespace
from typing import Annotated, ClassVar, ForwardRef, Optional

import pytest

from aquilia.contracts import Contract, Field, computed
from aquilia.contracts.annotations import _is_classvar_annotation
from aquilia.contracts.facets import (
    EmailFacet,
    IntFacet,
    ListFacet,
    SetFacet,
    TextFacet,
    TupleFacet,
)
from aquilia.faults.domains import ConfigInvalidFault
from aquilia.specula.schema.contract import contract_to_schema

# ════════════════════════════════════════════════════════════════════════
# Mock ORM models (mirror the model-binding surface Spec.model reads)
# ════════════════════════════════════════════════════════════════════════


class _MF:
    """Mock ORM field descriptor."""

    def __init__(
        self,
        null: bool = False,
        blank: bool = False,
        primary_key: bool = False,
        auto_now: bool = False,
        has_default: bool = False,
    ):
        self.null = null
        self.blank = blank
        self.primary_key = primary_key
        self.auto_now = auto_now
        self.has_default = lambda: has_default


class _MockUser:
    _fields = {
        "id": _MF(primary_key=True),
        "username": _MF(null=False),
        "email": _MF(null=False),
        "bio": _MF(null=True),
        "refresh_token_hash": _MF(null=False),
    }


class _MockArticle:
    _fields = {
        "id": _MF(primary_key=True),
        "title": _MF(null=False),
        "internal_note": _MF(null=False),  # NOT NULL, not declared by contract
        "updated_at": _MF(auto_now=True),
    }


# ════════════════════════════════════════════════════════════════════════
# F1 / F2 — attribute-access matrix (namespace hygiene + synthetic None)
# ════════════════════════════════════════════════════════════════════════


class DeviceContract(Contract):
    device: str | None = None
    status: str = "draft"


class KeysContract(Contract):
    keys = ListFacet(child=TextFacet(), required=False)
    name = TextFacet()


class OmitContract(Contract):
    before: str = Field(required=False)
    after: str = Field(required=False, allow_null=True)


class ArticleContract(Contract):
    title: str

    @computed
    def word_count(self, instance) -> int:
        return len(str(getattr(instance, "title", "")).split())


class TestAttributeAccessMatrix:
    """
    Facets and plain defaults left in the class ``__dict__`` used to shadow
    ``Contract.__getattr__``, so ``bp.field`` returned the facet object or a
    stale class-body default instead of the validated value. After a
    successful seal, absent optionals / read-only fields now read as ``None``
    instead of raising AttributeError.
    """

    def test_plain_default_none_returns_validated(self):
        bp = DeviceContract(data={"device": "ios", "status": "published"})
        assert bp.is_sealed(), bp.errors
        assert bp.device == "ios"
        assert bp.status == "published"

    def test_plain_defaults_not_left_in_class_dict(self):
        assert "device" not in vars(DeviceContract)
        assert "status" not in vars(DeviceContract)

    def test_declared_facet_field_returns_data_not_facet(self):
        bp = KeysContract(data={"keys": ["a", "b"], "name": "x"})
        assert bp.is_sealed(), bp.errors
        assert bp.keys == ["a", "b"]
        assert not isinstance(bp.keys, ListFacet)
        assert bp.name == "x"
        assert not isinstance(bp.name, TextFacet)

    def test_class_level_access_returns_facet(self):
        # Class-level introspection keeps receiving the facet via
        # ContractMeta.__getattr__ even though the name was removed from
        # the class __dict__.
        assert isinstance(KeysContract.keys, ListFacet)
        assert isinstance(KeysContract.name, TextFacet)

    def test_absent_optional_returns_none(self):
        bp = OmitContract(data={"after": None})
        assert bp.is_sealed(), bp.errors
        assert bp.before is None
        assert bp.after is None

    def test_read_only_absent_returns_none(self):
        class ReadOnlyContract(Contract):
            id: Annotated[str | None, Field(read_only=True, required=False)] = None
            title: str

        bp = ReadOnlyContract(data={"title": "hello"})
        assert bp.is_sealed(), bp.errors
        assert bp.id is None

    def test_computed_absent_still_raises(self):
        # Computed facets never enter validated_data and carry no input
        # meaning; they must keep raising rather than degrade to None.
        bp = ArticleContract(data={"title": "hello there"})
        assert bp.is_sealed(), bp.errors
        with pytest.raises(AttributeError):
            bp.word_count

    def test_many_true_raises(self):
        class ManyContract(Contract):
            name = TextFacet()

        bp = ManyContract(data=[{"name": "a"}, {"name": "b"}], many=True)
        assert bp.is_sealed(), bp.errors
        with pytest.raises(AttributeError):
            bp.name

    def test_partial_required_absent_returns_none(self):
        class PatchContract(Contract):
            title: str
            body: str = Field(required=False)

        bp = PatchContract(data={"body": "x"}, partial=True)
        assert bp.is_sealed(), bp.errors
        assert bp.title is None
        assert bp.body == "x"

    def test_field_named_data_no_longer_shadows_data_property(self):
        class WeirdContract(Contract):
            data = TextFacet()

        bp = WeirdContract(data={"data": "v"})
        assert bp.is_sealed(), bp.errors
        # The class-body TextFacet no longer shadows Contract.data: the
        # property returns the bound request data, and the field value is
        # reachable through validated_data / __getattr__.
        assert not isinstance(bp.data, TextFacet)
        assert bp.validated_data["data"] == "v"


# ════════════════════════════════════════════════════════════════════════
# N1 — Optional unwrapping for raw Facet in Annotated
# ════════════════════════════════════════════════════════════════════════


class OptFacetContract(Contract):
    email: Annotated[str | None, EmailFacet()]


class OptFacetRequired(Contract):
    email: Annotated[str | None, Field(required=True)]


class PlainOptionalContract(Contract):
    a: str | None = None
    b: Optional[str]  # noqa: UP045 — deliberate: covers the typing.Optional path


SHARED_EMAIL_FACET = EmailFacet()


class SharedOptionalContract(Contract):
    maybe: Annotated[str | None, SHARED_EMAIL_FACET]
    surely: Annotated[str, SHARED_EMAIL_FACET]


class TestOptionalRawFacet:
    """
    ``Annotated[str | None, SomeFacet()]`` previously returned the facet
    untouched: the Optional half was silently ignored and the field stayed
    required / non-nullable.
    """

    def test_optional_raw_facet_honors_allow_null(self):
        facet = OptFacetContract._all_facets["email"]
        assert facet.required is False
        assert facet.allow_null is True

        bp = OptFacetContract(data={"email": None})
        assert bp.is_sealed(), bp.errors
        assert bp.email is None

    def test_explicit_field_required_wins_over_optional(self):
        # Precedence: Field kwargs > annotation Optional > facet constructor
        # kwargs.
        assert OptFacetRequired._all_facets["email"].required is True

    def test_facet_constructor_kwargs_still_honored(self):
        class ConstructorKwargsContract(Contract):
            email: Annotated[str | None, EmailFacet(required=False)]

        facet = ConstructorKwargsContract._all_facets["email"]
        assert facet.required is False
        assert facet.allow_null is True

    def test_plain_optional_paths_still_honored(self):
        assert PlainOptionalContract._all_facets["a"].allow_null is True
        assert PlainOptionalContract._all_facets["b"].allow_null is True
        assert PlainOptionalContract._all_facets["b"].required is False

    def test_shared_facet_instance_not_polluted(self):
        # A module-level facet shared between Optional and non-Optional
        # annotations must be cloned before mutation, never polluted.
        maybe = SharedOptionalContract._all_facets["maybe"]
        surely = SharedOptionalContract._all_facets["surely"]
        assert maybe.allow_null is True
        assert surely.allow_null is False
        assert SHARED_EMAIL_FACET.allow_null is False
        assert maybe is not surely


# ════════════════════════════════════════════════════════════════════════
# N2 — empty projection include list
# ════════════════════════════════════════════════════════════════════════


class EmptyProjectionContract(Contract):
    a = TextFacet()
    b = IntFacet()

    class Spec:
        projections = {"none": [], "excl": ["-b"]}


class TestEmptyProjection:
    """An empty field list is a valid projection: empty output, not everything."""

    def test_empty_include_list_resolves_empty(self):
        assert set(EmptyProjectionContract._projections.resolve("none")) == set()

    def test_empty_projection_molds_empty(self):
        inst = SimpleNamespace(a="x", b=1)
        assert EmptyProjectionContract(instance=inst, projection="none").data == {}

    def test_exclusion_projection_still_works(self):
        assert set(EmptyProjectionContract._projections.resolve("excl")) == {"a"}
        inst = SimpleNamespace(a="x", b=1)
        assert EmptyProjectionContract(instance=inst, projection="excl").data == {"a": "x"}


# ════════════════════════════════════════════════════════════════════════
# N3 — ClassVar / InitVar annotations are not wire fields
# ════════════════════════════════════════════════════════════════════════


class ClassVarContract(Contract):
    version: ClassVar[str] = "1.0"
    name: str


class TestClassVarAnnotations:
    """ClassVar/InitVar annotations are class-level configuration, not wire fields."""

    def test_classvar_is_not_a_facet(self):
        assert "version" not in ClassVarContract._all_facets
        assert "name" in ClassVarContract._all_facets

    def test_classvar_not_accepted_from_wire(self):
        bp = ClassVarContract(data={"name": "n"})
        assert bp.is_sealed(), bp.errors
        assert "version" not in bp.validated_data

    def test_classvar_not_in_schema(self):
        assert "version" not in ClassVarContract.to_schema()["properties"]
        for mode in ("input", "output"):
            schema = contract_to_schema(ClassVarContract, mode=mode)
            assert "version" not in schema["properties"]
            assert "name" in schema["properties"]

    def test_is_classvar_annotation_string_and_ref_forms(self):
        # Resolved forms
        assert _is_classvar_annotation(ClassVar[str]) is True
        assert _is_classvar_annotation(int) is False
        assert _is_classvar_annotation("str") is False
        # String / ForwardRef fallbacks for unresolvable annotations
        assert _is_classvar_annotation("ClassVar[str]") is True
        assert _is_classvar_annotation("typing.ClassVar[str]") is True
        assert _is_classvar_annotation("InitVar[int]") is True
        assert _is_classvar_annotation(ForwardRef("ClassVar[int]")) is True
        assert _is_classvar_annotation(ForwardRef("list[str]")) is False


# ════════════════════════════════════════════════════════════════════════
# N4 — bare Field(...) without a type annotation
# ════════════════════════════════════════════════════════════════════════


class TestBareField:
    """
    A Field(...) assigned without a type annotation never reached
    annotation introspection, so its constraints silently vanished -- a
    validation bypass. It now fails loudly at class creation.
    """

    def test_bare_field_raises_config_invalid(self):
        with pytest.raises(ConfigInvalidFault, match="no type annotation"):

            class BareFieldContract(Contract):
                name = Field(min_length=2)

    def test_annotated_field_still_works(self):
        class AnnotatedFieldContract(Contract):
            name: str = Field(min_length=2)

        assert set(AnnotatedFieldContract._all_facets) == {"name"}
        bp = AnnotatedFieldContract(data={"name": "ab"})
        assert bp.is_sealed(), bp.errors
        bad = AnnotatedFieldContract(data={"name": "a"})
        assert not bad.is_sealed()


# ════════════════════════════════════════════════════════════════════════
# F-CORE-09 — implicitly derived model facets must not auto-require columns
# ════════════════════════════════════════════════════════════════════════


class PutUserContract(Contract):
    username: str

    class Spec:
        model = _MockUser


class ExplicitFieldsContract(Contract):
    class Spec:
        model = _MockUser
        fields = ["username", "email"]


class UpdateArticleContract(Contract):
    title: Annotated[str | None, Field(min_length=5, required=False)] = None

    class Spec:
        model = _MockArticle


class TestImplicitModelDerivation:
    """
    With ``Spec.fields`` unset, model NOT NULL constraints used to mark every
    derived column required, so an inbound PUT/PATCH contract 400'd on every
    column its author never named. Explicit ``Spec.fields`` is the opt-in
    that keeps model-constraint-derived requiredness.
    """

    def test_implicit_derivation_seals_without_undeclared_columns(self):
        bp = PutUserContract(data={"username": "alice"})
        assert bp.is_sealed(), bp.errors

    def test_explicit_spec_fields_still_require_listed_columns(self):
        bp = ExplicitFieldsContract(data={"username": "a"})
        assert not bp.is_sealed()
        assert bp.errors["email"] == ["This field is required"]

    def test_update_contract_pattern_seals(self):
        bp = UpdateArticleContract(data={"title": "hello world"})
        assert bp.is_sealed(), bp.errors


# ════════════════════════════════════════════════════════════════════════
# F-CO-LEAK — silently derived model columns in the default projection
# ════════════════════════════════════════════════════════════════════════


_USER_INST = SimpleNamespace(
    id=7, username="alice", email="a@b.c", bio=None, refresh_token_hash="SECRET"
)


class TestSilentlyDerivedProjection:
    """
    A contract that binds ``Spec.model`` without ``Spec.fields`` or
    ``Spec.projections`` used to mold every model column -- secrets
    included. The implicit default projection now excludes facets that
    exist only through silent model derivation, with a RuntimeWarning.
    """

    def test_runtime_warning_fires(self):
        with pytest.warns(RuntimeWarning, match="model-derived"):

            class WarnContract(Contract):
                username = TextFacet()

                class Spec:
                    model = _MockUser

    def test_default_projection_excludes_silently_derived(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)

            class LeakContract(Contract):
                username = TextFacet()

                class Spec:
                    model = _MockUser

        data = LeakContract(instance=_USER_INST).data
        assert data == {"username": "alice"}
        assert "refresh_token_hash" not in data

    def test_explicit_all_projection_restores_full_output(self):
        class FullContract(Contract):
            username = TextFacet()

            class Spec:
                model = _MockUser
                projections = {"full": "__all__"}
                default_projection = "full"

        data = FullContract(instance=_USER_INST).data
        assert data == {
            "username": "alice",
            "id": 7,
            "email": "a@b.c",
            "bio": None,
            "refresh_token_hash": "SECRET",
        }

    def test_admin_pattern_with_explicit_fields_molds_identically(self):
        class AdminPatternContract(Contract):
            class Spec:
                model = _MockUser
                fields = ["id", "username", "email"]
                read_only_fields = ["id"]

        assert AdminPatternContract(instance=_USER_INST).data == {
            "id": 7,
            "username": "alice",
            "email": "a@b.c",
        }

    def test_output_schema_excludes_silently_derived(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)

            class SchemaLeakContract(Contract):
                username = TextFacet()

                class Spec:
                    model = _MockUser

        output = sorted(SchemaLeakContract.to_schema(mode="output")["properties"])
        assert output == ["username"]
        # Input schemas keep every facet: sealing still validates what the
        # model binding accepts.
        schema_input = sorted(SchemaLeakContract.to_schema(mode="input")["properties"])
        assert "refresh_token_hash" in schema_input


# ════════════════════════════════════════════════════════════════════════
# F-CORE-10 — clean collection child-fault messages
# ════════════════════════════════════════════════════════════════════════


class TagsContract(Contract):
    tags = ListFacet(child=IntFacet())


class NamesContract(Contract):
    names = ListFacet(child=TextFacet())


class MatrixContract(Contract):
    matrix = ListFacet(child=ListFacet(child=IntFacet()))


class SetTagsContract(Contract):
    tags = SetFacet(child=IntFacet())


class PairContract(Contract):
    pair = TupleFacet(child=IntFacet())


class QuantityContract(Contract):
    quantity = IntFacet(min_value=0)


class TestCollectionFaultMessages:
    """
    ``CastFault`` prepends ``Cast failed for '<field>': `` to its message;
    collection facets re-wrapped child faults, so the per-field error list
    showed one accumulated prefix per nesting layer plus ``<unbound>``.
    ``fault_message`` now strips the prefixes, and the collection wrap sites
    carry the item index the prefix used to encode.
    """

    def test_list_child_error_single_prefix(self):
        bp = NamesContract(data={"names": ["ok", ""]})
        bp.is_sealed()
        assert bp.errors == {"names": ["item 1: This field may not be blank"]}

    def test_list_child_error_has_no_cast_decoration(self):
        bp = TagsContract(data={"tags": [1, "x"]})
        bp.is_sealed()
        (message,) = bp.errors["tags"]
        assert "Cast failed for" not in message
        assert "<unbound>" not in message

    def test_nested_list_errors(self):
        bp = MatrixContract(data={"matrix": [[1, "x"], ["y"]]})
        bp.is_sealed()
        assert bp.errors == {"matrix": ["item 0: item 1: Expected integer, got str"]}

    def test_set_child_error_uses_item_label(self):
        bp = SetTagsContract(data={"tags": ["x", 1]})
        bp.is_sealed()
        assert bp.errors == {"tags": ["item: Expected integer, got str"]}

    def test_tuple_child_error_uses_index(self):
        bp = PairContract(data={"pair": [1, "z"]})
        bp.is_sealed()
        assert bp.errors == {"pair": ["item 1: Expected integer, got str"]}

    def test_plain_field_error_strips_cast_prefix(self):
        bp = QuantityContract(data={"quantity": -3})
        bp.is_sealed()
        assert bp.errors == {"quantity": ["Must be at least 0"]}


# ════════════════════════════════════════════════════════════════════════
# Copy / pickle of contract instances
# ════════════════════════════════════════════════════════════════════════


class TestCopyPickle:
    """Copies and pickled round-trips must carry data, not facet objects."""

    def _sealed(self):
        bp = KeysContract(data={"keys": ["k"], "name": "n"})
        assert bp.is_sealed(), bp.errors
        return bp

    def test_copy(self):
        original = self._sealed()
        duplicate = copy.copy(original)
        assert duplicate.keys == ["k"]
        assert not isinstance(duplicate.keys, ListFacet)
        assert duplicate.name == "n"

    def test_pickle_round_trip(self):
        original = self._sealed()
        restored = pickle.loads(pickle.dumps(original))
        assert restored.keys == ["k"]
        assert not isinstance(restored.keys, ListFacet)
        assert restored.name == "n"
        assert restored.validated_data == {"keys": ["k"], "name": "n"}


# ════════════════════════════════════════════════════════════════════════
# ContractMeta.__getattr__ guard battery
# ════════════════════════════════════════════════════════════════════════


class TestMetaclassGuardBattery:
    """Class-level access must keep normal attribute semantics."""

    def test_hasattr_unknown_is_false(self):
        assert hasattr(KeysContract, "definitely_not_here") is False

    def test_hasattr_declared_field_is_true(self):
        assert hasattr(KeysContract, "name") is True

    def test_getattr_with_default(self):
        assert getattr(KeysContract, "definitely_not_here", "DEFAULT") == "DEFAULT"

    def test_getattr_unknown_raises_attribute_error(self):
        with pytest.raises(AttributeError, match="no field 'nope'"):
            KeysContract.nope

    def test_getattr_facet(self):
        assert isinstance(KeysContract.keys, ListFacet)

    def test_dunder_lookup_still_resolves(self):
        assert hasattr(KeysContract, "__reduce_ex__") is True
        assert hasattr(KeysContract, "__deepcopy__") is False

    def test_dir_works_and_fields_are_served_by_getattr(self):
        listing = dir(KeysContract)
        assert isinstance(listing, list)
        assert "__init__" in listing
        # Facet names were removed from the class __dict__, so they no
        # longer appear in dir(); they remain reachable via getattr.
        assert "keys" not in listing
        assert KeysContract.keys is KeysContract.get_facet("keys")

    def test_copy_of_class_is_identity(self):
        assert copy.copy(KeysContract) is KeysContract

    def test_base_contract_usable(self):
        assert hasattr(Contract, "definitely_not_here") is False
        assert isinstance(Contract._synthetic_none_fields, frozenset)
        assert isinstance(Contract._input_field_names, frozenset)


# ════════════════════════════════════════════════════════════════════════
# Subclass inheritance of popped defaults
# ════════════════════════════════════════════════════════════════════════


class ParentContract(Contract):
    device: str | None = None


class ChildContract(ParentContract):
    extra: str = Field(required=False)


class TestSubclassInheritance:
    """Popped class-body defaults must not break subclasses."""

    def test_child_instance_returns_validated_parent_field(self):
        bp = ChildContract(data={"device": "tv"})
        assert bp.is_sealed(), bp.errors
        assert bp.device == "tv"

    def test_child_class_dict_has_no_inherited_shadow(self):
        assert "device" not in vars(ChildContract)
        assert "device" not in vars(ParentContract)

    def test_child_class_level_access_returns_facet(self):
        assert isinstance(ChildContract.device, type(ChildContract.get_facet("device")))

    def test_child_absent_optional_returns_none(self):
        bp = ChildContract(data={})
        assert bp.is_sealed(), bp.errors
        assert bp.device is None
        assert bp.extra is None
