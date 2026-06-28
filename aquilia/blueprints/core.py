"""
Aquilia Blueprint Core -- the Blueprint metaclass and base class.

A Blueprint is a contract between a Model and the outside world.
It declares what the world sees (Facets), what it can send (Casts),
how integrity is enforced (Seals), and how data is written back (Imprints).

This is NOT a serializer. It is a *first-class framework primitive*.
"""

from __future__ import annotations

import contextlib
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
    cast,
    overload,
)

from ..utils.data import DataObject
from .annotations import (
    Field,
    LazyBlueprintFacet,
    NestedBlueprintFacet,
    _ComputedMarker,
    introspect_annotations,
)
from .exceptions import (
    CastFault,
    ImprintFault,
    SealFault,
)
from .facets import UNSET, Computed, Constant, Facet, Inject, derive_facet
from .lenses import Lens, _ProjectedRef
from .projections import ProjectionRegistry

if TYPE_CHECKING:
    pass


__all__ = ["Blueprint", "BlueprintMeta", "_blueprint_registry"]

ModelT = TypeVar("ModelT")

# Global registry for resolving forward/lazy Blueprint references by string name
_blueprint_registry: dict[str, type[Blueprint]] = {}

# ── Spec Descriptor ──────────────────────────────────────────────────────


class _SpecData:
    """
    Parsed Spec (inner class) data for a Blueprint.

    This replaces the DRF-style ``Meta`` class -- we call it ``Spec``
    to avoid collision with the Model's ``Meta``.
    """

    __slots__ = (
        "model",
        "fields",
        "exclude",
        "read_only_fields",
        "write_only_fields",
        "extra_facets",
        "projections",
        "default_projection",
        "depth",
        "validators",
        "extra_fields",
        "max_many_items",
        "strict",
        "revision",
        "migrate_from",
        "discriminator",
    )

    def __init__(self, spec_cls: type | None = None):
        if spec_cls is None:
            self.model = None
            self.fields = None
            self.exclude = None
            self.read_only_fields = ()
            self.write_only_fields = ()
            self.extra_facets = {}
            self.projections = None
            self.default_projection = None
            self.depth = 3
            self.validators = []
            self.extra_fields = "ignore"
            self.max_many_items = 10000
            self.strict = False
            self.revision = None
            self.migrate_from = {}
            self.discriminator = None
            return

        self.model = getattr(spec_cls, "model", None)
        self.fields = getattr(spec_cls, "fields", None)
        self.exclude = getattr(spec_cls, "exclude", None)
        self.read_only_fields = tuple(getattr(spec_cls, "read_only_fields", ()))
        self.write_only_fields = tuple(getattr(spec_cls, "write_only_fields", ()))
        self.extra_facets = dict(getattr(spec_cls, "extra_facets", {}))
        self.projections = getattr(spec_cls, "projections", None)
        self.default_projection = getattr(spec_cls, "default_projection", None)
        self.depth = getattr(spec_cls, "depth", 3)
        self.validators = list(getattr(spec_cls, "validators", []))
        self.extra_fields = getattr(spec_cls, "extra_fields", "ignore")
        self.max_many_items = getattr(spec_cls, "max_many_items", 10000)
        self.strict = getattr(spec_cls, "strict", False)
        self.revision = getattr(spec_cls, "revision", None)
        migrate_val = getattr(spec_cls, "migrate_from", None)
        if isinstance(migrate_val, dict):
            self.migrate_from = dict(migrate_val)
        elif isinstance(migrate_val, type):
            rev = getattr(getattr(migrate_val, "_spec", None), "revision", 1) or 1
            self.migrate_from = {rev: migrate_val}
        elif isinstance(migrate_val, (list, tuple)):
            self.migrate_from = {}
            for item in migrate_val:
                rev = getattr(getattr(item, "_spec", None), "revision", 1) or 1
                self.migrate_from[rev] = item
        else:
            self.migrate_from = {}
        self.discriminator = getattr(spec_cls, "discriminator", None)


# ── Metaclass ────────────────────────────────────────────────────────────


class BlueprintMeta(type):
    """
    Metaclass for Blueprint classes.

    Responsibilities:
        1. Collect declared Facets from namespace + parent classes
        2. Parse the Spec inner class
        3. Auto-derive Facets from Model fields (if Spec.model is set)
        4. Build the ProjectionRegistry
        5. Set up seal/async_seal method discovery
        6. Support ``Blueprint["projection"]`` subscript syntax
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs,
    ) -> BlueprintMeta:
        # Collect declared facets from namespace
        declared_facets: dict[str, Facet] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Facet):
                declared_facets[key] = value

        # Clean up Field/ComputedMarker descriptors from namespace
        # so they don't pollute the class dict.
        # Collect Field descriptors separately so we can pass them
        # to annotation introspection later.
        field_descriptors: dict[str, Field] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                field_descriptors[key] = value
                namespace.pop(key, None)
            elif isinstance(value, _ComputedMarker):
                # Convert to Computed facet immediately
                facet = value.to_facet()
                declared_facets[key] = facet
                namespace[key] = facet

        # Inherit facets from parent Blueprints
        parent_facets: dict[str, Facet] = {}
        for base in bases:
            if hasattr(base, "_declared_facets"):
                for fname, facet in base._declared_facets.items():
                    if fname not in declared_facets:
                        parent_facets[fname] = facet.clone()
            # Also inherit annotation-derived facets from parent
            if hasattr(base, "_annotated_facets"):
                for fname, facet in base._annotated_facets.items():
                    if fname not in declared_facets and fname not in parent_facets:
                        parent_facets[fname] = facet.clone()

        # Parse Spec inner class
        spec_cls = namespace.pop("Spec", None)

        # Also check bases for Spec
        if spec_cls is None:
            for base in bases:
                if hasattr(base, "_spec") and base._spec is not None:
                    spec_cls = type(
                        "Spec",
                        (),
                        {attr: getattr(base._spec, attr) for attr in _SpecData.__slots__ if hasattr(base._spec, attr)},
                    )
                    break

        spec = _SpecData(spec_cls)

        # Build the class -- AFTER this, cls.__annotations__ is available
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)
        cls._spec = spec
        cls._declared_facets = declared_facets
        cls._parent_facets = parent_facets
        cls._all_facets: dict[str, Facet] = {}

        # ── Type-annotation introspection ────────────────────────────
        # Now that the class is created, we can read cls.__annotations__
        # which is properly populated even with PEP 649 (Python 3.14).
        annotated_facets: dict[str, Facet] = {}
        try:
            # Build a namespace dict with annotations and field descriptors
            ann_namespace: dict[str, Any] = {}
            # Get resolved annotations from the class
            cls_annotations = {}
            with contextlib.suppress(Exception):
                cls_annotations = cls.__annotations__
            ann_namespace["__annotations__"] = cls_annotations
            # Re-inject field descriptors for introspection
            ann_namespace.update(field_descriptors)
            # Inject any other class attributes that are defaults (not Facets)
            for fname in cls_annotations:
                if fname not in ann_namespace and fname not in declared_facets:
                    val = namespace.get(fname, UNSET)
                    if val is not UNSET:
                        ann_namespace[fname] = val
            annotated_facets = introspect_annotations(
                cls,
                ann_namespace,
                bases,
                include_explicit_facets=True,
            )
        except Exception as exc:
            warnings.warn(
                f"Blueprint '{name}': annotation introspection failed: {exc}. "
                f"Annotation-derived facets will be unavailable.",
                RuntimeWarning,
                stacklevel=2,
            )

        cls._annotated_facets = annotated_facets

        # Deterministic merge for nested Blueprint fields declared via both
        # annotation and explicit NestedBlueprintFacet.
        declared_facets = mcs._merge_nested_annotation_facets(
            name=name,
            annotated_facets=annotated_facets,
            declared_facets=declared_facets,
        )
        cls._declared_facets = declared_facets

        # If this is the base Blueprint class itself, skip model derivation
        if spec.model is None and not declared_facets and not annotated_facets:
            cls._seal_methods = []
            cls._async_seal_methods = []
            return cls

        # Auto-derive facets from model
        model_facets: dict[str, Facet] = {}
        if spec.model is not None:
            model_facets = mcs._derive_model_facets(spec)

        # Merge: parent < annotated < model < declared (declared wins)
        all_facets = {}
        all_facets.update(parent_facets)
        all_facets.update(annotated_facets)
        all_facets.update(model_facets)
        all_facets.update(declared_facets)

        # Add extra facets from Spec
        for fname, facet in spec.extra_facets.items():
            if fname not in all_facets:
                all_facets[fname] = facet

        # Apply read_only/write_only overrides from Spec
        for fname in spec.read_only_fields:
            if fname in all_facets:
                all_facets[fname].read_only = True
        for fname in spec.write_only_fields:
            if fname in all_facets:
                all_facets[fname].write_only = True

        # Sort by creation order
        cls._all_facets = dict(sorted(all_facets.items(), key=lambda item: item[1]._order))

        # Bind class-level facets name and source properties
        for fname, facet in cls._all_facets.items():
            facet.name = fname
            if facet.source is None:
                facet.source = fname

        # Build projection registry
        cls._projections = ProjectionRegistry()
        write_only_names = {fname for fname, f in cls._all_facets.items() if f.write_only}
        cls._projections.configure(
            projections=spec.projections,
            default=spec.default_projection,
            all_facet_names=set(cls._all_facets.keys()),
            write_only_names=write_only_names,
        )

        # Discover seal methods
        cls._seal_methods: list[str] = []
        cls._async_seal_methods: list[str] = []
        for attr_name in dir(cls):
            if attr_name.startswith("seal_") and not attr_name.startswith("__"):
                method = getattr(cls, attr_name, None)
                if callable(method):
                    cls._seal_methods.append(attr_name)
            elif attr_name.startswith("async_seal_") and not attr_name.startswith("__"):
                method = getattr(cls, attr_name, None)
                if callable(method):
                    cls._async_seal_methods.append(attr_name)

        # Collect ward methods
        from .ward import collect_ward_methods
        cls._ward_methods = collect_ward_methods(name, bases, namespace)

        # Build sigil
        from .sigil import build_sigil
        cls._sigil = build_sigil(cls)

        # Register the Blueprint in the global registry for forward references
        # Only register if it's an actual defined Blueprint, not a base
        if name != "Blueprint":
            _blueprint_registry[name] = cls

        return cls

    @staticmethod
    def _facet_target_tokens(facet: Facet) -> set[str]:
        """Return normalized target identifiers for nested-blueprint facets."""
        tokens: set[str] = set()

        if isinstance(facet, NestedBlueprintFacet):
            target = facet.target
            tokens.add(target.__name__)
            tokens.add(target.__qualname__)
            tokens.add(f"{target.__module__}.{target.__qualname__}")
            return tokens

        if isinstance(facet, LazyBlueprintFacet):
            ref = facet.ref
            tokens.add(ref)
            if "." in ref:
                tokens.add(ref.split(".")[-1])
            return tokens

        return tokens

    @staticmethod
    def _merge_nested_annotation_facets(
        *,
        name: str,
        annotated_facets: dict[str, Facet],
        declared_facets: dict[str, Facet],
    ) -> dict[str, Facet]:
        """Merge annotation+explicit nested facets with explicit validation."""
        from aquilia.faults.domains import ConfigInvalidFault

        merged = dict(declared_facets)

        for field_name, declared in declared_facets.items():
            annotated = annotated_facets.get(field_name)
            if annotated is None:
                continue

            declared_is_nested = isinstance(declared, (NestedBlueprintFacet, LazyBlueprintFacet))
            annotated_is_nested = isinstance(annotated, (NestedBlueprintFacet, LazyBlueprintFacet))

            if not declared_is_nested and not annotated_is_nested:
                # Backward-compatible behavior for non-nested overlaps:
                # explicit facet remains authoritative.
                continue

            if declared_is_nested != annotated_is_nested:
                raise ConfigInvalidFault(
                    key=f"blueprints.{name}.{field_name}",
                    reason=(
                        f"Conflicting field '{field_name}' definitions: annotation and explicit facet "
                        "must both define a nested Blueprint field when combined."
                    ),
                )

            # Both sides are nested facets. Annotation defines structure.
            if declared.many != annotated.many:
                raise ConfigInvalidFault(
                    key=f"blueprints.{name}.{field_name}",
                    reason=(
                        f"Nested field '{field_name}' has conflicting cardinality: annotation implies "
                        f"many={annotated.many}, explicit facet sets many={declared.many}."
                    ),
                )

            declared_tokens = BlueprintMeta._facet_target_tokens(declared)
            annotated_tokens = BlueprintMeta._facet_target_tokens(annotated)
            if not (declared_tokens & annotated_tokens):
                raise ConfigInvalidFault(
                    key=f"blueprints.{name}.{field_name}",
                    reason=(
                        f"Nested field '{field_name}' annotation/facet type mismatch: "
                        f"annotation={sorted(annotated_tokens)} facet={sorted(declared_tokens)}"
                    ),
                )

            resolved = annotated.clone()

            # Apply explicit-facet behavior/configuration over annotated structure.
            if declared.source is not None and declared.source != field_name:
                resolved.source = declared.source
            if declared._required is not None:
                resolved._required = declared._required
            if declared.read_only:
                resolved.read_only = True
            if declared.write_only:
                resolved.write_only = True
            if declared.default is not UNSET:
                resolved.default = declared.default
            if declared.allow_null:
                resolved.allow_null = True
            if declared.allow_blank:
                resolved.allow_blank = True
            if declared.label is not None:
                resolved.label = declared.label
            if declared.help_text is not None:
                resolved.help_text = declared.help_text
            if declared.validators:
                resolved.validators.extend(declared.validators)

            if hasattr(declared, "_max_depth") and hasattr(resolved, "_max_depth"):
                resolved._max_depth = declared._max_depth

            merged[field_name] = resolved

        return merged

    @staticmethod
    def _derive_model_facets(spec: _SpecData) -> dict[str, Facet]:
        """Derive Facets from Model._fields."""
        model = spec.model
        facets: dict[str, Facet] = {}

        # Get model fields
        model_fields = getattr(model, "_fields", {})
        if not model_fields:
            # Fallback: scan class for Field instances
            try:
                from ..models.fields_module import Field

                for attr_name in dir(model):
                    val = getattr(model, attr_name, None)
                    if isinstance(val, Field):
                        model_fields[attr_name] = val
            except ImportError:
                pass

        # Determine which fields to include
        if spec.fields == "__all__":
            include = set(model_fields.keys())
        elif spec.fields is not None:
            include = set(spec.fields)
        else:
            include = set(model_fields.keys())

        if spec.exclude:
            include -= set(spec.exclude)

        # Derive facets
        for fname in include:
            mf = model_fields.get(fname)
            if mf is None:
                continue

            # Check if it's a relation field
            if hasattr(mf, "to"):
                # ForeignKey / OneToOneField / ManyToManyField
                facets[fname] = _derive_relation_facet(mf, fname, spec)
            else:
                facets[fname] = derive_facet(mf)

        return facets

    def __getitem__(cls, projection: Any) -> Any:
        """
        Enable projection refs for concrete Blueprints while preserving typing subscripts.

        Returns a _ProjectedRef that can be passed to Lens or used
        as a response_blueprint in route decorators.
        """
        if isinstance(projection, str) and cls.__name__ != "Blueprint":
            return _ProjectedRef(cls, projection)

        # Defer non-projection subscripts (e.g., Blueprint[UserModel]) to typing.
        class_getitem = getattr(cls, "__class_getitem__", None)
        if callable(class_getitem):
            return class_getitem(projection)

        raise TypeError(f"Unsupported Blueprint subscript: {projection!r}")

    def __repr__(cls) -> str:
        model_name = cls._spec.model.__name__ if cls._spec and cls._spec.model else "None"
        return f"<Blueprint '{cls.__name__}' model={model_name}>"

    def __or__(cls, other: Any) -> Any:
        from .core import BlueprintUnion, Blueprint
        if isinstance(other, type) and issubclass(other, Blueprint):
            return BlueprintUnion((cls, other))
        if isinstance(other, BlueprintUnion):
            return BlueprintUnion((cls, *other.members))
        return NotImplemented

    def __ror__(cls, other: Any) -> Any:
        from .core import BlueprintUnion, Blueprint
        if isinstance(other, type) and issubclass(other, Blueprint):
            return BlueprintUnion((other, cls))
        return NotImplemented


def _derive_relation_facet(model_field: Any, name: str, spec: _SpecData) -> Facet:
    """
    Derive a Lens or IntFacet for a relation field.

    - ForeignKey → IntFacet (PK reference) by default
    - If the FK field name matches a declared Lens, that takes precedence
    """
    from ..models.fields_module import ForeignKey, ManyToManyField, OneToOneField

    is_many = isinstance(model_field, ManyToManyField)

    # Default: expose as PK reference (IntFacet for FK ID)
    kwargs: dict[str, Any] = {}
    if getattr(model_field, "null", False):
        kwargs["allow_null"] = True
    if is_many:
        # M2M → list of PKs
        return Facet(read_only=True, **kwargs)

    # FK/OneToOne → ID field
    # The actual column is usually `{name}_id`
    facet = Facet(**kwargs)
    facet.source = f"{name}_id" if isinstance(model_field, (ForeignKey, OneToOneField)) else name
    return facet


# ── BlueprintUnion ────────────────────────────────────────────────────────


class BlueprintUnion:
    """Compiled discriminated union wrapper constructed via | operator on Blueprints."""

    __slots__ = ("members", "discriminator_field", "_dispatch")

    def __init__(self, members: tuple):
        self.members = members
        self.discriminator_field, self._dispatch = self._build_dispatch()

    def _build_dispatch(self):
        discriminator_field = None
        # Check if any member has Spec.discriminator set explicitly
        for member in self.members:
            spec = getattr(member, "_spec", None)
            if spec and getattr(spec, "discriminator", None):
                discriminator_field = spec.discriminator
                break

        # If not explicitly set, auto-detect it
        if discriminator_field is None:
            candidate_fields = {}
            for member in self.members:
                member_fields = getattr(member, "_all_facets", {})
                for fname, facet in member_fields.items():
                    from .facets import ChoiceFacet
                    if isinstance(facet, ChoiceFacet):
                        candidate_fields.setdefault(fname, []).append(member)

            # Filter to those present in all members
            common_candidates = [
                fname for fname, members_list in candidate_fields.items()
                if len(members_list) == len(self.members)
            ]

            # Check if their Literal values are disjoint
            for fname in common_candidates:
                values_to_member = {}
                disjoint = True
                for member in self.members:
                    facet = member._all_facets[fname]
                    allowed = getattr(facet, "allowed_values", ())
                    for val in allowed:
                        if val in values_to_member:
                            disjoint = False
                            break
                        values_to_member[val] = member
                    if not disjoint:
                        break
                if disjoint:
                    discriminator_field = fname
                    break

        if discriminator_field is not None:
            dispatch = {}
            for member in self.members:
                facet = member._all_facets.get(discriminator_field)
                if facet is not None:
                    from .facets import ChoiceFacet
                    if isinstance(facet, ChoiceFacet):
                        allowed = getattr(facet, "allowed_values", ())
                        for val in allowed:
                            dispatch[val] = member
            return discriminator_field, dispatch

        return None, None

    def validate(self, data: Any) -> tuple[dict, dict]:
        if self._dispatch:
            from .sigil import is_mapping_like, get_field_value
            from .facets import UNSET, TextFacet
            tag = None
            if self.discriminator_field and is_mapping_like(data):
                tag = get_field_value(data, self.discriminator_field, TextFacet())
                if tag is UNSET:
                    tag = None
            cls = self._dispatch.get(tag)
            if cls is None:
                return {self.discriminator_field or "tag": [f"Unknown discriminator value: {tag!r}"]}, {}
            return cls._sigil.validate(data)
        else:
            import warnings
            warnings.warn(
                "No discriminator found; falling back to try-each validation. "
                "Add a Literal-typed field or set Spec.discriminator.",
                RuntimeWarning,
                stacklevel=2,
            )
            for cls in self.members:
                errors, validated = cls._sigil.validate(data)
                if not errors:
                    return {}, validated
            return {"__union__": ["No member matched"]}, {}

    def __or__(self, other):
        if isinstance(other, BlueprintUnion):
            return BlueprintUnion((*self.members, *other.members))
        return BlueprintUnion((*self.members, other))

    def __ror__(self, other):
        return BlueprintUnion((other, *self.members))

    def to_json_schema(self) -> dict:
        choices_schemas = []
        for member in self.members:
            choices_schemas.append(member._sigil.to_json_schema())
        sch = {"oneOf": choices_schemas}
        if self.discriminator_field:
            sch["discriminator"] = {"propertyName": self.discriminator_field}
        return sch


# ── Blueprint Base Class ─────────────────────────────────────────────────


class BlueprintSerializationDescriptor:
    """Descriptor to support calling to_dict/to_dict_many as class methods or instance methods."""

    def __init__(self, name: str):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            # Accessed on the class, e.g., ComplexUserBlueprint.to_dict
            if self.name == "to_dict":
                def class_to_dict(obj, *, _depth: int = 0, _seen: set | None = None):
                    return owner(instance=obj).to_dict(_depth=_depth, _seen=_seen)
                return class_to_dict
            elif self.name == "to_dict_many":
                def class_to_dict_many(objs, *, _depth: int = 0, _seen: set | None = None):
                    return owner(many=True).to_dict_many(objs, _depth=_depth, _seen=_seen)
                return class_to_dict_many
        # Accessed on the instance, e.g., bp.to_dict
        return getattr(instance, f"_{self.name}_instance")


class Blueprint(Generic[ModelT], metaclass=BlueprintMeta):
    to_dict = BlueprintSerializationDescriptor("to_dict")
    to_dict_many = BlueprintSerializationDescriptor("to_dict_many")
    """
    The Blueprint -- a contract between a Model and the outside world.

    A Blueprint declares:
        - **Facets**: what data points are visible/writable
        - **Projections**: named subsets of facets
        - **Seals**: validation rules (field, cross-field, async)
        - **Imprints**: how validated data writes back to the model

    Usage::

        class ProductBlueprint(Blueprint):
            class Spec:
                model = Product
                projections = {
                    "summary": ["id", "name", "price"],
                    "detail": "__all__",
                }

        # Outbound: Model → dict
        bp = ProductBlueprint(instance=product)
        data = bp.to_dict()

        # Inbound: dict → validated data
        bp = ProductBlueprint(data={"name": "Widget", "price": 9.99})
        if bp.is_sealed():
            product = await bp.imprint()

    Args:
        instance: Model instance for outbound (mold) operations.
        data: Raw input data for inbound (cast + seal) operations.
        many: If True, expect a list of instances/data.
        partial: If True, don't require all required fields (PATCH semantics).
        projection: Named projection to use.
        context: Extra context dict (request, container, etc.).
    """

    _spec: _SpecData
    _all_facets: dict[str, Facet]
    _projections: ProjectionRegistry
    _seal_methods: list[str]
    _async_seal_methods: list[str]

    def __init__(
        self,
        instance: ModelT | list[ModelT] | None = None,
        *,
        data: Any = UNSET,
        many: bool = False,
        partial: bool = False,
        projection: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        self.instance = instance
        self._input_data = data
        self.many = many
        self.partial = partial
        self._projection_name = projection
        self.context: dict[str, Any] = context or {}

        # State
        self._validated_data: dict[str, Any] | None = None
        self._errors: dict[str, list[str]] = {}
        self._is_sealed: bool | None = None  # None = not yet validated

        # Reference to compiled schema
        self._sigil = getattr(self.__class__, "_sigil", None)
        # Store context
        self._context = self.context

    @property
    def _bound_facets(self) -> dict[str, Facet]:
        # TODO(deprecation): remove in next major
        return self.__class__._all_facets

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to validated_data."""
        if name.startswith("_"):
            raise AttributeError(name)
        if self._validated_data is not None and name in self._validated_data:
            return self._validated_data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getitem__(self, key: str) -> Any:
        """Proxy dictionary-style access to validated_data."""
        return self.validated_data[key]

    # ── Outbound: Mold ───────────────────────────────────────────────

    @property
    def data(self) -> dict[str, Any] | list[dict[str, Any]]:
        """
        The output representation -- molded from the instance.

        For inbound usage, returns validated_data after sealing.
        """
        if self.instance is not None:
            if self.many:
                return self.to_dict_many(self.instance)
            return self.to_dict()
        if self._validated_data is not None:
            return self._validated_data
        return {}

    def _to_dict_instance(
        self,
        instance: Any = None,
        *,
        _depth: int = 0,
        _seen: set | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Mold a model instance into a dict, respecting projections.

        Args:
            instance: Override instance (default: self.instance)
            _depth: Internal depth counter for Lens traversal
            _seen: Internal cycle detection set
        """
        if instance is None and self.many:
            if self.instance is not None:
                return self.to_dict_many(self.instance, _depth=_depth, _seen=_seen)
            if self._validated_data is not None:
                return self._validated_data
            return []

        obj = instance or self.instance
        if obj is None:
            if self._validated_data is not None:
                return self._validated_data
            return {}

        # Resolve projection
        projection_fields = self._projections.resolve(self._projection_name)

        result: dict[str, Any] = {}
        for fname, facet in self._bound_facets.items():
            # Skip write-only facets in output
            if facet.write_only:
                continue
            # Apply projection filter
            if projection_fields and fname not in projection_fields:
                continue

            # Extract value from instance
            value = facet.extract(obj)

            # Mold through Lens (with depth/cycle tracking)
            if isinstance(facet, Lens):
                value = facet.mold(value, _depth=_depth, _seen=_seen)
            elif value is not None:
                value = facet.mold(value)
            elif facet.allow_null:
                value = None
            else:
                continue  # Skip None values for non-nullable facets

            result[fname] = value

        return result

    def _to_dict_many_instance(
        self,
        instances: Any,
        *,
        _depth: int = 0,
        _seen: set | None = None,
    ) -> list[dict[str, Any]]:
        """Mold multiple instances."""
        return [self.to_dict(instance=obj, _depth=_depth, _seen=_seen) for obj in instances]

    # ── Inbound: Cast + Seal ─────────────────────────────────────────

    def is_sealed(self, *, raise_fault: bool = False) -> bool:
        """
        Validate the input data through the full pipeline.

        Pipeline:
            1. Cast: type coercion per facet
            2. Field seals: per-facet validators
            3. Cross-field seals: ``seal_*()`` methods
            4. Object-level validate: ``validate()``

        Args:
            raise_fault: If True, raise BlueprintFault on failure.

        Returns:
            True if data passes all seals.
        """
        if self._is_sealed is not None:
            if raise_fault and not self._is_sealed:
                raise SealFault(
                    message="Blueprint validation failed",
                    errors=self._errors,
                )
            return self._is_sealed

        if self._input_data is UNSET:
            self._errors = {"__all__": ["No input data provided"]}
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="No input data provided", errors=self._errors)
            return False

        if self.many:
            return self._seal_many(raise_fault=raise_fault)

        self._errors = {}
        validated: dict[str, Any] = {}

        from .sigil import is_mapping_like
        data = self._input_data if is_mapping_like(self._input_data) else {}

        # ── Unknown field rejection ──────────────────────────────────
        extra_fields_mode = self._spec.extra_fields if self._spec else "ignore"
        if self.context.get("extra_fields"):
            extra_fields_mode = self.context["extra_fields"]

        if extra_fields_mode == "reject" and is_mapping_like(data):
            from .sigil import get_keys
            known_fields = set(self._bound_facets.keys())
            unknown = get_keys(data) - known_fields
            if unknown:
                for field_name in sorted(unknown):
                    self._errors.setdefault(field_name, []).append(f"Unknown field '{field_name}' is not allowed")
                self._is_sealed = False
                if raise_fault:
                    raise SealFault(
                        message="Unknown fields in input data",
                        errors=self._errors,
                    )
                return False

        # Phase 1 + 2: Structural validation via Sigil
        strict_override = self.context.get("strict", None)
        errors, validated_dict = self._sigil.validate(
            data,
            strict=strict_override,
            partial=self.partial,
            context=self.context,
        )
        self._errors.update(errors)
        validated.update(validated_dict)

        if self._errors:
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Blueprint validation failed", errors=self._errors)
            return False

        # Phase 3: Cross-field seals (ward methods)
        validated = DataObject(validated)
        data_obj = validated
        for wm in self.__class__._ward_methods:
            if wm.mode == "sync":
                try:
                    wm.fn(self, data_obj)
                except CastFault as exc:
                    msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                    if exc.field not in self._errors or msg not in self._errors[exc.field]:
                        self._errors.setdefault(exc.field, []).append(msg)
                except Exception as exc:
                    self._errors.setdefault("__all__", []).append(str(exc))

        if self._errors:
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Blueprint validation failed", errors=self._errors)
            return False

        # Phase 4: Object-level validate
        try:
            validated = self.validate(validated)
        except CastFault as exc:
            msg = exc.field_errors.get(exc.field, [str(exc)])[0]
            if exc.field not in self._errors or msg not in self._errors[exc.field]:
                self._errors.setdefault(exc.field, []).append(msg)
        except SealFault as exc:
            if hasattr(exc, "field_errors") and exc.field_errors:
                for field, msgs in exc.field_errors.items():
                    self._errors.setdefault(field, []).extend(msgs)
            else:
                self._errors.setdefault("__all__", []).append(str(exc))
        except Exception as exc:
            self._errors.setdefault("__all__", []).append(str(exc))

        if self._errors:
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Blueprint validation failed", errors=self._errors)
            return False

        self._validated_data = validated
        self._is_sealed = True
        return True

    async def is_sealed_async(self, *, raise_fault: bool = False) -> bool:
        """
        Async variant of is_sealed -- also runs async_seal_* and async ward methods.
        """
        # Run sync pipeline (which skips async wards)
        if not self.is_sealed(raise_fault=False):
            if raise_fault:
                raise SealFault(message="Blueprint validation failed", errors=self._errors)
            return False

        # Phase 5: Async seals and coroutine ward methods
        data_obj = self._validated_data
        for wm in self.__class__._ward_methods:
            if wm.mode == "async":
                try:
                    import inspect
                    if inspect.iscoroutinefunction(wm.fn):
                        await wm.fn(self, data_obj)
                    else:
                        wm.fn(self, data_obj)
                except CastFault as exc:
                    msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                    if exc.field not in self._errors or msg not in self._errors[exc.field]:
                        self._errors.setdefault(exc.field, []).append(msg)
                except Exception as exc:
                    self._errors.setdefault("__all__", []).append(str(exc))

        if self._errors:
            self._is_sealed = False
            self._validated_data = None
            if raise_fault:
                raise SealFault(message="Blueprint validation failed", errors=self._errors)
            return False

        return True

    def _seal_many(self, *, raise_fault: bool) -> bool:
        """Validate a list of input items."""
        from .sigil import is_mapping_like, extract_flat_list_mapping
        input_data = self._input_data
        if is_mapping_like(input_data):
            extracted = extract_flat_list_mapping(input_data)
            if extracted is not None:
                input_data = extracted

        if not isinstance(input_data, (list, tuple)):
            self._errors = {"__all__": ["Expected a list"]}
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Expected a list", errors=self._errors)
            return False

        # Enforce maximum list size to prevent resource exhaustion
        max_items = self._spec.max_many_items if self._spec else 10000
        # Allow runtime override via context
        if self.context.get("max_many_items"):
            max_items = self.context["max_many_items"]

        if len(input_data) > max_items:
            self._errors = {
                "__all__": [f"List contains {len(input_data)} items, exceeding the maximum of {max_items}"]
            }
            self._is_sealed = False
            if raise_fault:
                raise SealFault(
                    message=f"Too many items ({len(input_data)} > {max_items})",
                    errors=self._errors,
                )
            return False

        all_validated = []
        all_errors = {}
        for i, item in enumerate(input_data):
            child = self.__class__(
                data=item,
                partial=self.partial,
                projection=self._projection_name,
                context=self.context,
            )
            if child.is_sealed():
                all_validated.append(child.validated_data)
            else:
                all_errors[str(i)] = child.errors

        if all_errors:
            self._errors = all_errors
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="List validation failed", errors=self._errors)
            return False

        self._validated_data = all_validated
        self._is_sealed = True
        return True

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Object-level validation hook.

        Override this to add cross-field logic. Return the (possibly
        modified) data dict, or raise an exception.

        This is the final gate before data is considered sealed.
        """
        return data

    def reject(self, field: str, message: str) -> None:
        """
        Convenience method for seal methods to register a field error.

        Usage in seal_* methods::

            def seal_date_range(self, data):
                if data["end_date"] < data["start_date"]:
                    self.reject("end_date", "Must be after start date")
        """
        raise CastFault(field, message)

    @property
    def validated_data(self) -> dict[str, Any] | list[dict[str, Any]] | None:
        """The validated data -- only available after successful sealing."""
        if self._is_sealed is None:
            self.is_sealed()
        return self._validated_data

    @property
    def errors(self) -> dict[str, list[str]]:
        """Validation errors -- available after sealing attempt."""
        if self._is_sealed is None:
            self.is_sealed()
        return self._errors

    # ── Write: Imprint ───────────────────────────────────────────────

    @overload
    async def imprint(
        self,
        instance: None = None,
        *,
        partial: bool | None = None,
    ) -> ModelT | list[ModelT]: ...

    @overload
    async def imprint(
        self,
        instance: ModelT,
        *,
        partial: bool | None = None,
    ) -> ModelT: ...

    @overload
    async def imprint(
        self,
        instance: list[ModelT],
        *,
        partial: bool | None = None,
    ) -> list[ModelT]: ...

    async def imprint(
        self,
        instance: ModelT | list[ModelT] | None = None,
        *,
        partial: bool | None = None,
    ) -> ModelT | list[ModelT]:
        """
        Write validated data back to a model instance.

        - If ``instance`` is None: creates a new model instance
        - If ``instance`` is provided: updates the existing instance
        - If ``partial`` is True: only update provided fields (PATCH)

        Returns the saved model instance.

        Raises:
            ImprintFault: If sealing hasn't been done or failed.
        """
        if self._validated_data is None:
            raise ImprintFault(
                message="Cannot imprint -- data has not been sealed. Call is_sealed() first.",
            )

        is_partial = partial if partial is not None else self.partial
        target = instance or self.instance

        if self.many:
            return await self._imprint_many(target)

        if target is not None:
            return await self._imprint_update(target, is_partial)
        return await self._imprint_create()

    async def _imprint_create(self) -> ModelT:
        """Create a new model instance from validated data."""
        model_cls = self._spec.model
        if model_cls is None:
            raise ImprintFault(message="Cannot imprint without a model class in Spec")

        # Filter to only model-writable fields
        create_data = self._filter_imprint_data(self._validated_data)

        try:
            instance = model_cls(**create_data)
            await instance.save()
            return cast(ModelT, instance)
        except Exception as exc:
            raise ImprintFault(
                message=f"Failed to create {model_cls.__name__}: {exc}",
                metadata={"model": model_cls.__name__, "error": str(exc)},
            ) from exc

    async def _imprint_update(self, instance: ModelT, partial: bool) -> ModelT:
        """Update an existing model instance."""
        update_data = self._filter_imprint_data(self._validated_data)
        update_fields = []

        for attr, value in update_data.items():
            setattr(instance, attr, value)
            update_fields.append(attr)

        try:
            if update_fields:
                await instance.save(update_fields=update_fields)
            return instance
        except Exception as exc:
            model_name = type(instance).__name__
            raise ImprintFault(
                message=f"Failed to update {model_name}: {exc}",
                metadata={"model": model_name, "error": str(exc)},
            ) from exc

    async def _imprint_many(self, instances: list[ModelT] | None = None) -> list[ModelT]:
        """Create or update multiple instances."""
        results = []
        for i, item_data in enumerate(self._validated_data):
            child = self.__class__(
                instance=instances[i] if instances and i < len(instances) else None,
                data=item_data,
                partial=self.partial,
                context=self.context,
            )
            child._validated_data = item_data
            child._is_sealed = True
            result = await child.imprint()
            results.append(result)
        return cast(list[ModelT], results)

    def _filter_imprint_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Filter validated data to only include model-writable attributes.

        Removes computed facets, constants, and fields not on the model.
        """
        if self._spec.model is None:
            return dict(data)

        model_fields = getattr(self._spec.model, "_fields", {})
        model_attrs = set(model_fields.keys())

        # Also include FK _id columns
        for fname, mf in model_fields.items():
            if hasattr(mf, "to"):
                model_attrs.add(f"{fname}_id")

        result = {}
        for key, value in data.items():
            # Check if the facet is writable
            facet = self._bound_facets.get(key)
            if facet is not None and isinstance(facet, (Computed, Constant, Inject)):
                continue
            # Check if it maps to a model attribute
            source = facet.source if facet else key
            if source in model_attrs or key in model_attrs:
                result[source] = value
            else:
                # Allow through if no model (pure Blueprint)
                result[key] = value

        return result

    # ── Schema ───────────────────────────────────────────────────────

    @classmethod
    def to_schema(
        cls,
        *,
        projection: str | None = None,
        mode: str = "output",
    ) -> dict[str, Any]:
        """
        Generate JSON Schema for this Blueprint.

        Args:
            projection: Named projection (None = default)
            mode: "output" (mold schema) or "input" (cast schema)

        Returns:
            JSON Schema dict
        """
        base_schema = cls._sigil.to_json_schema()
        projection_fields = cls._projections.resolve(projection)

        properties: dict[str, Any] = {}
        required: list[str] = []

        import copy

        for fname, facet in cls._all_facets.items():
            if mode == "output" and facet.write_only:
                continue
            if mode == "input" and facet.read_only:
                continue
            if projection_fields and fname not in projection_fields:
                continue

            if fname in base_schema["properties"]:
                properties[fname] = copy.deepcopy(base_schema["properties"][fname])

            if mode == "input" and facet.required and not facet.read_only:
                required.append(fname)

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required

        if "$defs" in base_schema:
            schema["$defs"] = copy.deepcopy(base_schema["$defs"])

        title = cls.__name__
        if projection:
            title = f"{title}_{projection}"
        schema["title"] = title

        return schema

    # ── Utilities ────────────────────────────────────────────────────

    @classmethod
    def facet_names(cls, *, projection: str | None = None) -> list[str]:
        """List facet names, optionally filtered by projection."""
        if projection:
            return sorted(cls._projections.resolve(projection))
        return list(cls._all_facets.keys())

    @classmethod
    def get_facet(cls, name: str) -> Facet | None:
        """Get a facet by name."""
        return cls._all_facets.get(name)

    @classmethod
    def seal_many(cls, rows: list[dict], *, parallel: bool = False, raise_on_any: bool = False) -> list[SealOutcome]:
        """Validate multiple rows of input data, returning outcomes."""
        outcomes = []
        if not parallel or len(rows) <= 1:
            for idx, row in enumerate(rows):
                errors, validated = cls._sigil.validate(row)
                if not errors:
                    inst = cls(data=row)
                    inst._errors = {}
                    validated = DataObject(validated)
                    data_obj = validated
                    for wm in cls._ward_methods:
                        if wm.mode == "sync":
                            try:
                                wm.fn(inst, data_obj)
                            except CastFault as exc:
                                msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                                if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                                    inst._errors.setdefault(exc.field, []).append(msg)
                            except Exception as exc:
                                inst.reject("__all__", str(exc))
                    errors = inst.errors

                if not errors:
                    try:
                        inst = cls(data=row)
                        inst._errors = {}
                        validated = inst.validate(validated)
                        errors = inst.errors
                    except CastFault as exc:
                        msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                        if exc.field not in errors or msg not in errors[exc.field]:
                            errors.setdefault(exc.field, []).append(msg)
                    except SealFault as exc:
                        if hasattr(exc, "field_errors") and exc.field_errors:
                            for field, msgs in exc.field_errors.items():
                                errors.setdefault(field, []).extend(msgs)
                        else:
                            errors.setdefault("__all__", []).append(str(exc))
                    except Exception as exc:
                        errors.setdefault("__all__", []).append(str(exc))

                ok = not errors
                outcome = SealOutcome(
                    index=idx,
                    ok=ok,
                    value=validated if ok else None,
                    errors=errors if not ok else None
                )
                if not ok and raise_on_any:
                    raise SealFault(message="Seal validation failed", errors=errors)
                outcomes.append(outcome)
        else:
            from concurrent.futures import ThreadPoolExecutor

            def validate_single(args):
                idx, row = args
                errors, validated = cls._sigil.validate(row)
                if not errors:
                    inst = cls(data=row)
                    inst._errors = {}
                    validated = DataObject(validated)
                    data_obj = validated
                    for wm in cls._ward_methods:
                        if wm.mode == "sync":
                            try:
                                wm.fn(inst, data_obj)
                            except CastFault as exc:
                                msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                                if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                                    inst._errors.setdefault(exc.field, []).append(msg)
                            except Exception as exc:
                                inst.reject("__all__", str(exc))
                    errors = inst.errors

                if not errors:
                    try:
                        inst = cls(data=row)
                        inst._errors = {}
                        validated = inst.validate(validated)
                        errors = inst.errors
                    except CastFault as exc:
                        msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                        if exc.field not in errors or msg not in errors[exc.field]:
                            errors.setdefault(exc.field, []).append(msg)
                    except SealFault as exc:
                        if hasattr(exc, "field_errors") and exc.field_errors:
                            for field, msgs in exc.field_errors.items():
                                errors.setdefault(field, []).extend(msgs)
                        else:
                            errors.setdefault("__all__", []).append(str(exc))
                    except Exception as exc:
                        errors.setdefault("__all__", []).append(str(exc))

                ok = not errors
                return SealOutcome(
                    index=idx,
                    ok=ok,
                    value=validated if ok else None,
                    errors=errors if not ok else None
                )

            with ThreadPoolExecutor(max_workers=min(32, len(rows))) as executor:
                futures = executor.map(validate_single, enumerate(rows))
                for outcome in futures:
                    if not outcome.ok and raise_on_any:
                        raise SealFault(message="Seal validation failed", errors=outcome.errors)
                    outcomes.append(outcome)

        return outcomes

    @classmethod
    async def seal_stream(cls, byte_or_dict_iterator: Any, *, chunk_size: int | None = None) -> Any:
        """Validate stream NDJSON data or dicts asynchronously."""
        idx = 0
        buffer = ""
        async for chunk in byte_or_dict_iterator:
            if isinstance(chunk, dict):
                errors, validated = cls._sigil.validate(chunk)
                if not errors:
                    inst = cls(data=chunk)
                    inst._errors = {}
                    validated = DataObject(validated)
                    data_obj = validated
                    for wm in cls._ward_methods:
                        try:
                            import inspect
                            if wm.mode == "async" and inspect.iscoroutinefunction(wm.fn):
                                await wm.fn(inst, data_obj)
                            else:
                                wm.fn(inst, data_obj)
                        except CastFault as exc:
                            msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                            if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                                inst._errors.setdefault(exc.field, []).append(msg)
                        except Exception as exc:
                            inst.reject("__all__", str(exc))
                    errors = inst.errors

                if not errors:
                    try:
                        inst = cls(data=chunk)
                        inst._errors = {}
                        validated = inst.validate(validated)
                        errors = inst.errors
                    except CastFault as exc:
                        msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                        if exc.field not in errors or msg not in errors[exc.field]:
                            errors.setdefault(exc.field, []).append(msg)
                    except SealFault as exc:
                        if hasattr(exc, "field_errors") and exc.field_errors:
                            for field, msgs in exc.field_errors.items():
                                errors.setdefault(field, []).extend(msgs)
                        else:
                            errors.setdefault("__all__", []).append(str(exc))
                    except Exception as exc:
                        errors.setdefault("__all__", []).append(str(exc))

                ok = not errors
                yield SealOutcome(
                    index=idx,
                    ok=ok,
                    value=validated if ok else None,
                    errors=errors if not ok else None
                )
                idx += 1
            else:
                if isinstance(chunk, bytes):
                    buffer += chunk.decode("utf-8")
                else:
                    buffer += str(chunk)

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    import json
                    try:
                        item = json.loads(line)
                        errors, validated = cls._sigil.validate(item)
                        if not errors:
                            inst = cls(data=item)
                            inst._errors = {}
                            validated = DataObject(validated)
                            data_obj = validated
                            for wm in cls._ward_methods:
                                try:
                                    import inspect
                                    if wm.mode == "async" and inspect.iscoroutinefunction(wm.fn):
                                        await wm.fn(inst, data_obj)
                                    else:
                                        wm.fn(inst, data_obj)
                                except CastFault as exc:
                                    msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                                    if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                                        inst._errors.setdefault(exc.field, []).append(msg)
                                except Exception as exc:
                                    inst.reject("__all__", str(exc))
                            errors = inst.errors

                        if not errors:
                            try:
                                inst = cls(data=item)
                                inst._errors = {}
                                validated = inst.validate(validated)
                                errors = inst.errors
                            except CastFault as exc:
                                msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                                if exc.field not in errors or msg not in errors[exc.field]:
                                    errors.setdefault(exc.field, []).append(msg)
                            except SealFault as exc:
                                if hasattr(exc, "field_errors") and exc.field_errors:
                                    for field, msgs in exc.field_errors.items():
                                        errors.setdefault(field, []).extend(msgs)
                                else:
                                    errors.setdefault("__all__", []).append(str(exc))
                            except Exception as exc:
                                errors.setdefault("__all__", []).append(str(exc))

                        ok = not errors
                        yield SealOutcome(
                            index=idx,
                            ok=ok,
                            value=validated if ok else None,
                            errors=errors if not ok else None
                        )
                    except Exception as e:
                        yield SealOutcome(
                            index=idx,
                            ok=False,
                            value=None,
                            errors={"__all__": [f"JSON parse error: {e}"]}
                        )
                    idx += 1

        if buffer.strip():
            try:
                import json
                item = json.loads(buffer.strip())
                errors, validated = cls._sigil.validate(item)
                if not errors:
                    inst = cls(data=item)
                    inst._errors = {}
                    validated = DataObject(validated)
                    data_obj = validated
                    for wm in cls._ward_methods:
                        try:
                            import inspect
                            if wm.mode == "async" and inspect.iscoroutinefunction(wm.fn):
                                await wm.fn(inst, data_obj)
                            else:
                                wm.fn(inst, data_obj)
                        except CastFault as exc:
                            msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                            if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                                inst._errors.setdefault(exc.field, []).append(msg)
                        except Exception as exc:
                            inst.reject("__all__", str(exc))
                    errors = inst.errors

                if not errors:
                    try:
                        inst = cls(data=item)
                        inst._errors = {}
                        validated = inst.validate(validated)
                        errors = inst.errors
                    except CastFault as exc:
                        msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                        if exc.field not in errors or msg not in errors[exc.field]:
                            errors.setdefault(exc.field, []).append(msg)
                    except SealFault as exc:
                        if hasattr(exc, "field_errors") and exc.field_errors:
                            for field, msgs in exc.field_errors.items():
                                errors.setdefault(field, []).extend(msgs)
                        else:
                            errors.setdefault("__all__", []).append(str(exc))
                    except Exception as exc:
                        errors.setdefault("__all__", []).append(str(exc))

                ok = not errors
                yield SealOutcome(
                    index=idx,
                    ok=ok,
                    value=validated if ok else None,
                    errors=errors if not ok else None
                )
            except Exception as e:
                yield SealOutcome(
                    index=idx,
                    ok=False,
                    value=None,
                    errors={"__all__": [f"JSON parse error: {e}"]}
                )

    @classmethod
    def seal_columnar(cls, rows_as_dicts_iterable: Any) -> ColumnarReport:
        """Perform column-oriented validation over bulk records."""
        rows = list(rows_as_dicts_iterable)
        num_rows = len(rows)
        valid_mask = [True] * num_rows
        errors_by_column = {fname: [None] * num_rows for fname in cls._sigil.fields}

        for fname, spec in cls._sigil.fields.items():
            facet = spec.facet
            from .facets import Computed, Constant
            if isinstance(facet, (Computed, Constant)) or facet.read_only:
                continue

            column_values = [row.get(fname, UNSET) for row in rows]
            failed_count = 0
            for idx, val in enumerate(column_values):
                if val is UNSET:
                    if facet.default is not UNSET:
                        continue
                    if facet.required:
                        errors_by_column[fname][idx] = "This field is required"
                        valid_mask[idx] = False
                        failed_count += 1
                        continue
                    if facet.allow_null:
                        continue
                    continue
                if val is None:
                    if facet.allow_null:
                        continue
                    errors_by_column[fname][idx] = "This field may not be null"
                    valid_mask[idx] = False
                    failed_count += 1
                    continue

                try:
                    cast_val = facet.cast(val)
                    facet.seal(cast_val)
                except Exception as exc:
                    errors_by_column[fname][idx] = str(exc)
                    valid_mask[idx] = False
                    failed_count += 1

        return ColumnarReport(valid_mask=valid_mask, errors_by_column=errors_by_column)

    @classmethod
    def example(cls) -> dict[str, Any]:
        """Generate schema-valid random test data dict."""
        import random
        import string
        from .facets import (
            BoolFacet,
            ChoiceFacet,
            DictFacet,
            FloatFacet,
            IntFacet,
            ListFacet,
            TextFacet,
        )
        from .sigil import get_nested_blueprint_cls

        result = {}
        for fname, spec in cls._sigil.fields.items():
            facet = spec.facet
            if facet.read_only:
                continue

            nested_cls = get_nested_blueprint_cls(facet)
            if nested_cls is not None:
                is_many = getattr(facet, "many", False)
                if is_many:
                    result[fname] = [nested_cls.example() for _ in range(random.randint(1, 3))]
                else:
                    result[fname] = nested_cls.example()
                continue

            if isinstance(facet, ChoiceFacet):
                allowed = getattr(facet, "_valid_values", ())
                if allowed:
                    result[fname] = random.choice(list(allowed))
                else:
                    result[fname] = None
                continue

            if isinstance(facet, TextFacet):
                min_len = facet.min_length or 0
                max_len = facet.max_length or (min_len + 10)
                length = random.randint(min_len, max_len)

                pattern = getattr(facet, "pattern", None)
                if pattern is not None:
                    p_str = pattern.pattern
                    if p_str == r"^[-a-zA-Z0-9_]+$":
                        chars = string.ascii_letters + string.digits + "-_"
                        result[fname] = "".join(random.choice(chars) for _ in range(max(1, length)))
                    elif p_str == r"^[a-z0-9-]+$":
                        chars = string.ascii_lowercase + string.digits + "-"
                        result[fname] = "".join(random.choice(chars) for _ in range(max(1, length)))
                    else:
                        chars = string.ascii_letters + string.digits
                        result[fname] = "".join(random.choice(chars) for _ in range(max(1, length)))
                else:
                    result[fname] = "".join(random.choice(string.ascii_lowercase) for _ in range(length))
                continue

            if isinstance(facet, IntFacet):
                min_val = facet.min_value if facet.min_value is not None else 0
                max_val = facet.max_value if facet.max_value is not None else (min_val + 100)

                mult = getattr(facet, "multiple_of", None)
                if mult is not None:
                    start_mult = (min_val + mult - 1) // mult
                    end_mult = max_val // mult
                    if start_mult <= end_mult:
                        result[fname] = random.randint(start_mult, end_mult) * mult
                    else:
                        result[fname] = min_val
                else:
                    result[fname] = random.randint(min_val, max_val)
                continue

            if isinstance(facet, FloatFacet):
                min_val = facet.min_value if facet.min_value is not None else 0.0
                max_val = facet.max_value if facet.max_value is not None else (min_val + 100.0)

                mult = getattr(facet, "multiple_of", None)
                if mult is not None:
                    start_mult = int((min_val + mult - 1e-9) / mult)
                    end_mult = int(max_val / mult)
                    if start_mult <= end_mult:
                        result[fname] = float(random.randint(start_mult, end_mult) * mult)
                    else:
                        result[fname] = float(min_val)
                else:
                    result[fname] = random.uniform(min_val, max_val)
                continue

            if isinstance(facet, BoolFacet):
                result[fname] = random.choice([True, False])
                continue

            if isinstance(facet, ListFacet):
                min_items = getattr(facet, "min_items", 0) or 0
                max_items = getattr(facet, "max_items", 5) or (min_items + 3)
                num_items = random.randint(min_items, max_items)
                child = getattr(facet, "child", None)
                if child is not None:
                    if isinstance(child, TextFacet):
                        result[fname] = ["".join(random.choice(string.ascii_lowercase) for _ in range(5)) for _ in range(num_items)]
                    elif isinstance(child, IntFacet):
                        result[fname] = [random.randint(0, 100) for _ in range(num_items)]
                    else:
                        result[fname] = []
                else:
                    result[fname] = []
                continue

            if isinstance(facet, DictFacet):
                result[fname] = {}
                continue

            from datetime import date, datetime
            import uuid
            facet_cls_name = type(facet).__name__
            if facet_cls_name == "DateFacet":
                result[fname] = date.today().isoformat()
            elif facet_cls_name == "DateTimeFacet":
                result[fname] = datetime.now().isoformat()
            elif facet_cls_name == "UUIDFacet":
                result[fname] = str(uuid.uuid4())
            else:
                result[fname] = None

        return result

    @classmethod
    def strategy(cls) -> Any:
        """Construct hypothesis FixedDictionary SearchStrategy matching this schema."""
        try:
            from hypothesis import strategies as st
        except ImportError:
            raise ImportError("hypothesis is not installed. pip install hypothesis to use Blueprint.strategy().")

        import string
        from .facets import (
            BoolFacet,
            ChoiceFacet,
            DictFacet,
            FloatFacet,
            IntFacet,
            ListFacet,
            TextFacet,
        )
        from .sigil import get_nested_blueprint_cls

        fields_strategies = {}
        for fname, spec in cls._sigil.fields.items():
            facet = spec.facet
            if facet.read_only:
                continue

            nested_cls = get_nested_blueprint_cls(facet)
            if nested_cls is not None:
                is_many = getattr(facet, "many", False)
                if is_many:
                    fields_strategies[fname] = st.lists(nested_cls.strategy(), min_size=1, max_size=3)
                else:
                    fields_strategies[fname] = nested_cls.strategy()
                continue

            if isinstance(facet, ChoiceFacet):
                allowed = getattr(facet, "_valid_values", ())
                if allowed:
                    fields_strategies[fname] = st.sampled_from(list(allowed))
                else:
                    fields_strategies[fname] = st.none()
                continue

            if isinstance(facet, TextFacet):
                min_len = facet.min_length if facet.min_length is not None else 0
                max_len = facet.max_length if facet.max_length is not None else (min_len + 16)

                pattern = getattr(facet, "pattern", None)
                if pattern is not None:
                    fields_strategies[fname] = st.from_regex(pattern, fullmatch=True)
                else:
                    fields_strategies[fname] = st.text(alphabet=string.ascii_lowercase, min_size=min_len, max_size=max_len)
                continue

            if isinstance(facet, IntFacet):
                min_val = facet.min_value if facet.min_value is not None else -1000
                max_val = facet.max_value if facet.max_value is not None else 1000

                mult = getattr(facet, "multiple_of", None)
                if mult is not None:
                    fields_strategies[fname] = st.integers(
                        min_value=(min_val + mult - 1) // mult if min_val is not None else -100,
                        max_value=max_val // mult if max_val is not None else 100
                    ).map(lambda x, m=mult: x * m)
                else:
                    fields_strategies[fname] = st.integers(min_value=min_val, max_value=max_val)
                continue

            if isinstance(facet, FloatFacet):
                min_val = facet.min_value if facet.min_value is not None else -1000.0
                max_val = facet.max_value if facet.max_value is not None else 1000.0

                mult = getattr(facet, "multiple_of", None)
                if mult is not None:
                    fields_strategies[fname] = st.integers(
                        min_value=int(min_val / mult) if min_val is not None else -100,
                        max_value=int(max_val / mult) if max_val is not None else 100
                    ).map(lambda x, m=mult: float(x * m))
                else:
                    fields_strategies[fname] = st.floats(min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False)
                continue

            if isinstance(facet, BoolFacet):
                fields_strategies[fname] = st.booleans()
                continue

            if isinstance(facet, ListFacet):
                min_items = getattr(facet, "min_items", 0) or 0
                max_items = getattr(facet, "max_items", 5) or 5
                child = getattr(facet, "child", None)
                if child is not None:
                    if isinstance(child, TextFacet):
                        el_strat = st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=5)
                    elif isinstance(child, IntFacet):
                        el_strat = st.integers(min_value=0, max_value=100)
                    else:
                        el_strat = st.none()
                else:
                    el_strat = st.none()
                fields_strategies[fname] = st.lists(el_strat, min_size=min_items, max_size=max_items)
                continue

            if isinstance(facet, DictFacet):
                fields_strategies[fname] = st.dictionaries(st.text(), st.text())
                continue

            fields_strategies[fname] = st.none()

        return st.fixed_dictionaries(fields_strategies)

    def __repr__(self) -> str:
        model_name = self._spec.model.__name__ if self._spec.model else "None"
        state = "sealed" if self._is_sealed else ("failed" if self._is_sealed is False else "pending")
        return f"<{type(self).__name__} model={model_name} state={state}>"


# ---------------------------------------------------------------------------
# Outbound reports and outcomes
# ---------------------------------------------------------------------------

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class SealOutcome:
    index: int
    ok: bool
    value: dict | None
    errors: dict | None


@dataclass(frozen=True, slots=True)
class ColumnarReport:
    valid_mask: list[bool]
    errors_by_column: dict[str, list[str | None]]
