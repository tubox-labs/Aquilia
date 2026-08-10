"""
Regression tests for @computed facet inheritance and annotation-overlap bugs.

Each class below pins the behaviour of one confirmed defect found during the
@computed decorator audit (v1.4.0b4). Tests are written to fail loudly if the
old behaviour is ever re-introduced, and double as executable documentation of
why each fix exists.

Bug report:   @computed decorator incorrectly demoted to TextFacet in three
              scenarios — subclass annotation re-declaration, ORM model binding,
              and same-class annotation + @computed co-declaration.

Fixed in:     v1.4.0b4 ("Resolved Fields")
Root causes:  (1) Dead code in introspect_annotations() — isinstance check on
              _ComputedMarker was always False because the metaclass had already
              converted the marker to a Computed instance before calling
              introspect_annotations, and with include_explicit_facets=True the
              Facet guard was bypassed.
              (2) ContractMeta.__new__ merge blindly ran
              all_facets.update(annotated_facets) and all_facets.update(model_facets)
              after parent_facets, so a bare type annotation or model column
              overwrote an inherited Computed facet.
"""

from __future__ import annotations

from aquilia.contracts import Contract
from aquilia.contracts.annotations import computed
from aquilia.contracts.facets import Computed, TextFacet

# ════════════════════════════════════════════════════════════════════════
# Scenario 1 — Basic @computed on a single Contract class (Baseline)
# ════════════════════════════════════════════════════════════════════════


class _PersonInstance:
    def __init__(self, first_name: str, last_name: str) -> None:
        self.first_name = first_name
        self.last_name = last_name


class SingleClassComputedContract(Contract):
    first_name: str
    last_name: str

    @computed
    def full_name(self, instance) -> str:
        return f"{instance.first_name} {instance.last_name}"


class TestScenario1_BaselineComputed:
    """
    Scenario 1 (working baseline):
    A single contract class with @computed defines a Computed facet.
    Validation with only the non-computed fields should succeed.
    The computed field must not appear in the input schema's required list.
    """

    def test_full_name_facet_is_computed(self):
        assert isinstance(SingleClassComputedContract._all_facets["full_name"], Computed), (
            "Expected 'full_name' to be a Computed facet on a single contract class."
        )

    def test_full_name_is_not_text_facet(self):
        assert not isinstance(SingleClassComputedContract._all_facets["full_name"], TextFacet), (
            "'full_name' must not be a TextFacet — it was declared with @computed."
        )

    def test_is_sealed_without_full_name_passes(self):
        bp = SingleClassComputedContract(data={"first_name": "Ada", "last_name": "Lovelace"})
        assert bp.is_sealed() is True, (
            f"is_sealed() must return True when computed fields are absent from input. Errors: {bp.errors}"
        )

    def test_errors_is_empty(self):
        bp = SingleClassComputedContract(data={"first_name": "Ada", "last_name": "Lovelace"})
        bp.is_sealed()
        assert bp.errors == {}, f"Expected no errors, got: {bp.errors}"

    def test_full_name_not_required_in_input_schema(self):
        schema = SingleClassComputedContract.to_schema(mode="input")
        required = schema.get("required", [])
        assert "full_name" not in required, (
            f"'full_name' must not be in input schema required fields. Required: {required}"
        )

    def test_full_name_present_in_output(self):
        bp = SingleClassComputedContract(instance=_PersonInstance("Ada", "Lovelace"))
        assert bp.data.get("full_name") == "Ada Lovelace", f"Expected computed full_name='Ada Lovelace', got: {bp.data}"


# ════════════════════════════════════════════════════════════════════════
# Scenario 2 — Subclass re-declaring a type annotation (PREVIOUSLY BROKEN)
# ════════════════════════════════════════════════════════════════════════


class _BaseUserContractForAnnotation(Contract):
    first_name: str
    last_name: str

    @computed
    def full_name(self, instance) -> str:
        return f"{instance.first_name} {instance.last_name}"


class _ChildWithAnnotation(_BaseUserContractForAnnotation):
    """Child re-declares full_name as a type annotation for IDE autocompletion."""

    full_name: str  # Type hint declared on subclass — must NOT demote @computed


class TestScenario2_SubclassAnnotationOverwrite:
    """
    Scenario 2 (previously broken):
    A child contract re-declares the same field as a bare type annotation
    (e.g., 'full_name: str') to satisfy IDE type checkers or mypy.

    Before the fix, introspect_annotations() generated a new TextFacet for
    'full_name' in annotated_facets, which was then merged over parent_facets
    (containing the Computed facet), silently replacing it. The child contract
    then demanded 'full_name' as a required input field, causing HTTP 422
    errors on well-formed requests.

    After the fix:
    - The merge in ContractMeta.__new__ skips annotated_facets entries that
      would overwrite an inherited Computed unless the subclass explicitly
      re-declared a new Facet/method.
    - is_sealed() succeeds without 'full_name' in the input data.
    """

    def test_child_full_name_facet_is_computed(self):
        assert isinstance(_ChildWithAnnotation._all_facets["full_name"], Computed), (
            "Expected 'full_name' to remain a Computed facet on the child contract. "
            "A bare type annotation must not overwrite an inherited @computed field."
        )

    def test_child_is_not_text_facet(self):
        assert not isinstance(_ChildWithAnnotation._all_facets["full_name"], TextFacet), (
            "Child contract's 'full_name' must NOT be a TextFacet. "
            "Bare 'full_name: str' annotation in the child silently broke this before v1.4.0b4."
        )

    def test_child_is_sealed_without_full_name(self):
        bp = _ChildWithAnnotation(data={"first_name": "Grace", "last_name": "Hopper"})
        assert bp.is_sealed() is True, (
            "is_sealed() must return True when a re-annotated @computed field is "
            f"absent from input. This was broken before v1.4.0b4. Errors: {bp.errors}"
        )

    def test_child_errors_is_empty(self):
        bp = _ChildWithAnnotation(data={"first_name": "Grace", "last_name": "Hopper"})
        bp.is_sealed()
        assert bp.errors == {}, (
            f"Expected no errors on child contract, got: {bp.errors}. "
            "This was the regression: 'full_name': ['This field is required']"
        )

    def test_child_full_name_not_required_in_input_schema(self):
        schema = _ChildWithAnnotation.to_schema(mode="input")
        required = schema.get("required", [])
        assert "full_name" not in required, (
            f"'full_name' must not be in child contract input schema required fields. Required: {required}"
        )

    def test_child_outputs_computed_value(self):
        bp = _ChildWithAnnotation(instance=_PersonInstance("Grace", "Hopper"))
        assert bp.data.get("full_name") == "Grace Hopper", (
            f"Child contract must still output computed full_name. Got: {bp.data}"
        )


# ════════════════════════════════════════════════════════════════════════
# Scenario 3 — ORM model binding overwrites inherited Computed (PREVIOUSLY BROKEN)
# ════════════════════════════════════════════════════════════════════════


class _MockField:
    """Minimal mock of an ORM field descriptor."""


class _MockUserModel:
    """
    Mock ORM model with _fields including a 'full_name' column.
    Simulates a real DB model where the full_name is stored as a DB column
    but the contract wants to compute it dynamically from first/last name.
    """

    _fields = {
        "first_name": _MockField(),
        "last_name": _MockField(),
        "full_name": _MockField(),  # Exists in DB schema — must NOT overwrite @computed
    }


class _BaseContractWithComputed(Contract):
    first_name: str
    last_name: str

    @computed
    def full_name(self, instance) -> str:
        return f"{instance.first_name} {instance.last_name}"


class _ModelBoundContract(_BaseContractWithComputed):
    """
    Subclass that binds MockUserModel. The model has a 'full_name' column which
    _derive_model_facets would generate a facet for — that facet must NOT
    overwrite the inherited @computed facet.
    """

    class Spec:
        model = _MockUserModel


class TestScenario3_OrmModelBindingOverwrite:
    """
    Scenario 3 (previously broken):
    A base contract defines @computed def full_name(...). A concrete subclass
    binds an ORM Model that also has a 'full_name' column.

    Before the fix, _derive_model_facets generated a model-derived facet for
    'full_name', which was then unconditionally merged over parent_facets,
    replacing the inherited Computed with a plain model-derived facet.
    Validation then demanded 'full_name' as a required field.

    After the fix:
    - The merge loop for model_facets skips entries that would overwrite an
      inherited Computed unless the subclass explicitly re-declared the field.
    """

    def test_model_bound_full_name_is_computed(self):
        assert isinstance(_ModelBoundContract._all_facets["full_name"], Computed), (
            "Expected 'full_name' to remain a Computed facet even after binding "
            "a model with a 'full_name' column. The model column must not win."
        )

    def test_model_bound_is_not_text_facet(self):
        assert not isinstance(_ModelBoundContract._all_facets["full_name"], TextFacet), (
            "_ModelBoundContract's 'full_name' must NOT be a model-derived TextFacet."
        )

    def test_model_bound_is_sealed_without_full_name(self):
        bp = _ModelBoundContract(data={"first_name": "Alan", "last_name": "Turing"})
        assert bp.is_sealed() is True, (
            "is_sealed() must return True when the inherited @computed field is "
            f"absent from input (ORM binding scenario). Errors: {bp.errors}"
        )

    def test_model_bound_errors_is_empty(self):
        bp = _ModelBoundContract(data={"first_name": "Alan", "last_name": "Turing"})
        bp.is_sealed()
        assert bp.errors == {}, (
            f"Expected no errors in ORM-bound contract, got: {bp.errors}. "
            "This was the regression: 'full_name': ['This field is required']"
        )


# ════════════════════════════════════════════════════════════════════════
# Scenario 4 — Type annotation + @computed on the same class (Latent Bug)
# ════════════════════════════════════════════════════════════════════════


class _SameClassAnnotationAndComputed(Contract):
    first_name: str
    last_name: str
    full_name: str  # Bare annotation at class level — co-declared with @computed below

    @computed
    def full_name(self, instance) -> str:  # type: ignore[override]
        return f"{instance.first_name} {instance.last_name}"


class _SubclassOfSameClassAnnotationAndComputed(_SameClassAnnotationAndComputed):
    """Plain subclass that inherits the annotation+computed class."""


class TestScenario4_SameClassAnnotationAndComputed:
    """
    Scenario 4 (latent bug — previously caused pollution of _annotated_facets):
    A single contract declares both 'full_name: str' (bare annotation at class
    top) AND '@computed def full_name(...)'. Before the fix:
    - introspect_annotations() generated a TextFacet for 'full_name' in
      _annotated_facets (because the isinstance(_ComputedMarker) check was
      dead code — the metaclass had already converted it to Computed).
    - cls._annotated_facets['full_name'] was polluted with TextFacet.
    - Any subclass inheriting from this class would see TextFacet inherited
      from _annotated_facets instead of Computed from _declared_facets.

    After the fix (introspect_annotations skips Facet instances):
    - The @computed wins on the declaring class.
    - Subclasses correctly inherit Computed.
    """

    def test_same_class_full_name_is_computed(self):
        assert isinstance(_SameClassAnnotationAndComputed._all_facets["full_name"], Computed), (
            "In a class with both 'full_name: str' annotation and '@computed def full_name', "
            "the @computed must win — the field must be Computed, not TextFacet."
        )

    def test_same_class_full_name_not_text_facet(self):
        assert not isinstance(_SameClassAnnotationAndComputed._all_facets["full_name"], TextFacet), (
            "'full_name' in _SameClassAnnotationAndComputed must not be a TextFacet."
        )

    def test_annotated_facets_not_polluted(self):
        """
        The latent part: _annotated_facets must NOT contain a TextFacet for
        'full_name', because that would propagate incorrectly to subclasses.
        """
        annotated = _SameClassAnnotationAndComputed._annotated_facets
        if "full_name" in annotated:
            # If it exists in annotated_facets, it must still be Computed (not TextFacet)
            assert isinstance(annotated["full_name"], Computed), (
                "_annotated_facets['full_name'] must be Computed (or absent), not TextFacet. "
                "A TextFacet here is the latent-bug pollution that breaks subclasses."
            )

    def test_subclass_full_name_is_computed(self):
        assert isinstance(_SubclassOfSameClassAnnotationAndComputed._all_facets["full_name"], Computed), (
            "A subclass of a class with annotation+@computed must still have a Computed facet. "
            "This is the latent-bug scenario: subclass inherits TextFacet from polluted "
            "_annotated_facets instead of Computed from _declared_facets."
        )

    def test_subclass_is_sealed_without_full_name(self):
        bp = _SubclassOfSameClassAnnotationAndComputed(data={"first_name": "Linus", "last_name": "Torvalds"})
        assert bp.is_sealed() is True, (
            f"Subclass of annotation+@computed contract must seal without full_name in input. Errors: {bp.errors}"
        )

    def test_subclass_errors_is_empty(self):
        bp = _SubclassOfSameClassAnnotationAndComputed(data={"first_name": "Linus", "last_name": "Torvalds"})
        bp.is_sealed()
        assert bp.errors == {}, f"Expected no errors, got: {bp.errors}"
