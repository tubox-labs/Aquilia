"""
Aquilia Contract Core -- the Contract metaclass and base class.

A Contract is a contract between a Model and the outside world.
It declares what the world sees (Facets), what it can send (Casts),
how integrity is enforced (Seals), and how data is written back (Imprints).

This is NOT a serializer. It is a *first-class framework primitive*.
"""

from __future__ import annotations

import contextlib
import warnings
from collections.abc import Mapping, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
    cast,
    overload,
)

from aquilia.contracts._native_plan import field_plan_for
from aquilia.contracts.annotations import (
    Field,
    LazyContractFacet,
    NestedContractFacet,
    _ComputedMarker,
    introspect_annotations,
)
from aquilia.contracts.exceptions import CastFault, ContractAsyncMismatchFault, ImprintFault, SealFault
from aquilia.contracts.facets import UNSET, Computed, Constant, Facet, Inject, derive_facet
from aquilia.contracts.lenses import Lens, _ProjectedRef
from aquilia.contracts.messages import contract_message
from aquilia.contracts.projections import ProjectionRegistry
from aquilia.faults.domains import ConfigInvalidFault
from aquilia.models.fields_module import ForeignKey, ManyToManyField, OneToOneField
from aquilia.utils.data import DataObject

if TYPE_CHECKING:
    pass


__all__ = ["Contract", "ContractMeta", "_contract_registry"]

ModelT = TypeVar("ModelT")

# Global registry for resolving forward/lazy Contract references by string name
_contract_registry: dict[str, type[Contract]] = {}


def resolve_sync_safe(container: Any, key: Any) -> Any:
    """Safe resolution from container cache or sync resolve without raising loop errors."""
    import asyncio

    # Guard against Mock objects to avoid infinite recursion
    if hasattr(container, "_mock_new_parent") or type(container).__name__ in (
        "Mock",
        "MagicMock",
        "NonCallableMagicMock",
        "AsyncMock",
    ):
        return None

    # 1. Convert to key
    if hasattr(container, "_token_to_key"):
        token_key = container._token_to_key(key)
    else:
        token_key = str(key)

    if hasattr(container, "_make_cache_key"):
        cache_key = container._make_cache_key(token_key, None)
    else:
        cache_key = token_key

    # Check current container cache
    if hasattr(container, "_cache") and cache_key in container._cache:
        return container._cache[cache_key]

    # Check parent container cache recursively
    parent = getattr(container, "_parent", None)
    if parent is not None:
        val = resolve_sync_safe(parent, key)
        if val is not None:
            return val

    # 2. If not cached, check if loop is running. If not, resolve synchronously
    try:
        asyncio.get_running_loop()
        has_loop = True
    except RuntimeError:
        has_loop = False

    if not has_loop and hasattr(container, "resolve"):
        try:
            return container.resolve(key, optional=True)
        except Exception:
            pass

    # 3. If loop is running, check if the provider is a ValueProvider
    # We look up the provider recursively
    if hasattr(container, "_lookup_provider"):
        try:
            provider = container._lookup_provider(token_key, None)
            if provider is not None:
                # ValueProvider.instantiate is technically async, but it returns self._value.
                # We can get it directly!
                if hasattr(provider, "_value"):
                    return provider._value
        except Exception:
            pass

    return None


class ContractContext(dict):
    """
    Context dictionary for Contracts.

    Acts as a standard dict, but falls back to resolving string keys or type keys
    from the DI container (if present under the key 'container').
    """

    def __getitem__(self, key: Any) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            container = super().get("container")
            if container is not None:
                res = resolve_sync_safe(container, key)
                if res is not None:
                    return res
            raise

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: Any) -> bool:
        if super().__contains__(key):
            return True
        container = super().get("container")
        if container is not None:
            try:
                # Check if registered in container
                if hasattr(container, "is_registered") and container.is_registered(key):
                    return True
            except Exception:
                pass
        return False


# ── Spec Descriptor ──────────────────────────────────────────────────────


class _SpecData:
    """
    Parsed Spec (inner class) data for a Contract.

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
        "frozen",
        "fail_fast",
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
            self.frozen = False
            self.fail_fast = False
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
        self.frozen = getattr(spec_cls, "frozen", False)
        self.fail_fast = getattr(spec_cls, "fail_fast", False)


# ── Metaclass ────────────────────────────────────────────────────────────


class ContractMeta(type):
    """
    Metaclass for Contract classes.

    Responsibilities:
        1. Collect declared Facets from namespace + parent classes
        2. Parse the Spec inner class
        3. Auto-derive Facets from Model fields (if Spec.model is set)
        4. Build the ProjectionRegistry
        5. Set up seal/async_seal method discovery
        6. Support ``Contract["projection"]`` subscript syntax
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs,
    ) -> ContractMeta:
        # Collect declared facets from namespace
        declared_facets: dict[str, Facet] = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Facet):
                declared_facets[key] = value
            elif isinstance(value, mcs):
                # Auto-wrap Contract subclass assignments in a NestedContractFacet

                facet = NestedContractFacet(value)
                declared_facets[key] = facet
                namespace[key] = facet

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

        # Inherit facets from parent Contracts
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
        if "Meta" in namespace:
            from aquilia.contracts.exceptions import ContractFault

            raise ContractFault(
                f"Contract '{name}' defined 'class Meta'. Aquilia Contracts "
                f"use 'class Spec' instead of 'class Meta' to avoid collision with Model Meta. "
                f"Please rename your configuration class to 'Spec'."
            )

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
                f"Contract '{name}': annotation introspection failed: {exc}. "
                f"Annotation-derived facets will be unavailable.",
                RuntimeWarning,
                stacklevel=2,
            )

        cls._annotated_facets = annotated_facets

        # Deterministic merge for nested Contract fields declared via both
        # annotation and explicit NestedContractFacet.
        declared_facets = mcs._merge_nested_annotation_facets(
            name=name,
            annotated_facets=annotated_facets,
            declared_facets=declared_facets,
        )
        cls._declared_facets = declared_facets

        # If this is the base Contract class itself, skip model derivation and basic setup
        if name == "Contract":
            return cls

        # Auto-derive facets from model
        model_facets: dict[str, Facet] = {}
        if spec.model is not None:
            model_facets = mcs._derive_model_facets(spec)

        # Merge: parent < model < annotated < declared (annotated & declared win over auto-derived model fields)
        all_facets = {}
        all_facets.update(parent_facets)
        all_facets.update(model_facets)
        all_facets.update(annotated_facets)
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

        # The declared field names as a set, for the extra_fields="reject" check
        # in is_sealed(). Static per class, so rebuilding it per call was 80 ns
        # of pure waste. Assigned here rather than memoised on first use so a
        # subclass cannot inherit its parent's set.
        cls._known_field_names = frozenset(cls._all_facets)

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
            minimal_names=mcs._minimal_facet_names(cls._all_facets, spec),
        )

        # Collect ward methods
        from aquilia.contracts.ward import collect_ward_methods

        cls._ward_methods = collect_ward_methods(name, bases, namespace)

        # Build sigil
        from aquilia.contracts.sigil import build_sigil

        cls._sigil = build_sigil(cls)

        # Register the Contract in the global registry for forward references
        # Only register if it's an actual defined Contract, not a base
        if name != "Contract":
            _contract_registry[name] = cls

        return cls

    @staticmethod
    def _minimal_facet_names(all_facets: dict[str, Facet], spec: _SpecData) -> set[str]:
        """
        Resolve the facet names that make up the ``"__minimal__"`` projection.

        A minimal projection is the smallest identifying view of a record:
        the model's primary key plus every facet the Contract marks
        ``read_only`` (server-owned fields such as ``created_at``, which are
        safe to expose because a client can never set them).

        Primary keys are discovered from ``Spec.model._fields`` when a model is
        bound; otherwise the conventional ``id``/``pk`` facet names are used so
        that model-less DTO Contracts still get a meaningful minimal view.

        Args:
            all_facets: The Contract's fully merged facet mapping.
            spec: The Contract's parsed ``Spec`` configuration.

        Returns:
            Facet names to include. May be empty — an empty minimal
            projection renders ``{}`` rather than leaking every field.

        See Also:
            :meth:`ProjectionRegistry.configure` — consumes this set.
        """
        names: set[str] = set()

        model = spec.model if spec else None
        model_fields = getattr(model, "_fields", {}) if model is not None else {}
        for fname, mf in model_fields.items():
            if getattr(mf, "primary_key", False) and fname in all_facets:
                names.add(fname)

        if not names:
            names.update(n for n in ("id", "pk") if n in all_facets)

        names.update(fname for fname, facet in all_facets.items() if facet.read_only)
        return names

    @staticmethod
    def _facet_target_tokens(facet: Facet) -> set[str]:
        """Return normalized target identifiers for nested-contract facets."""
        tokens: set[str] = set()

        if isinstance(facet, NestedContractFacet):
            target = facet.target
            tokens.add(target.__name__)
            tokens.add(target.__qualname__)
            tokens.add(f"{target.__module__}.{target.__qualname__}")
            return tokens

        if isinstance(facet, LazyContractFacet):
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

        merged = dict(declared_facets)

        for field_name, declared in declared_facets.items():
            annotated = annotated_facets.get(field_name)
            if annotated is None:
                continue

            declared_is_nested = isinstance(declared, (NestedContractFacet, LazyContractFacet))
            annotated_is_nested = isinstance(annotated, (NestedContractFacet, LazyContractFacet))

            if not declared_is_nested and not annotated_is_nested:
                # Backward-compatible behavior for non-nested overlaps:
                # explicit facet remains authoritative.
                continue

            if declared_is_nested != annotated_is_nested:
                raise ConfigInvalidFault(
                    key=f"contracts.{name}.{field_name}",
                    reason=(
                        f"Conflicting field '{field_name}' definitions: annotation and explicit facet "
                        "must both define a nested Contract field when combined."
                    ),
                )

            # Both sides are nested facets. Annotation defines structure.
            if declared.many != annotated.many:
                raise ConfigInvalidFault(
                    key=f"contracts.{name}.{field_name}",
                    reason=(
                        f"Nested field '{field_name}' has conflicting cardinality: annotation implies "
                        f"many={annotated.many}, explicit facet sets many={declared.many}."
                    ),
                )

            declared_tokens = ContractMeta._facet_target_tokens(declared)
            annotated_tokens = ContractMeta._facet_target_tokens(annotated)
            if not (declared_tokens & annotated_tokens):
                raise ConfigInvalidFault(
                    key=f"contracts.{name}.{field_name}",
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
                from aquilia.models.fields_module import Field

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
        Enable projection refs for concrete Contracts while preserving typing subscripts.

        Returns a _ProjectedRef that can be passed to Lens or used
        as a response_contract in route decorators.
        """
        if isinstance(projection, str) and cls.__name__ != "Contract":
            return _ProjectedRef(cls, projection)

        # Defer non-projection subscripts (e.g., Contract[UserModel]) to typing.
        class_getitem = getattr(cls, "__class_getitem__", None)
        if callable(class_getitem):
            return class_getitem(projection)

        raise TypeError(f"Unsupported Contract subscript: {projection!r}")

    def __repr__(cls) -> str:
        model_name = cls._spec.model.__name__ if cls._spec and cls._spec.model else "None"
        return f"<Contract '{cls.__name__}' model={model_name}>"

    def __or__(cls, other: Any) -> Any:
        from aquilia.contracts.core import Contract, ContractUnion

        if isinstance(other, type) and issubclass(other, Contract):
            return ContractUnion((cls, other))
        if isinstance(other, ContractUnion):
            return ContractUnion((cls, *other.members))
        return NotImplemented

    def __ror__(cls, other: Any) -> Any:
        from aquilia.contracts.core import Contract, ContractUnion

        if isinstance(other, type) and issubclass(other, Contract):
            return ContractUnion((other, cls))
        return NotImplemented


def _derive_relation_facet(model_field: Any, name: str, spec: _SpecData) -> Facet:
    """
    Derive a Lens or IntFacet for a relation field.

    - ForeignKey → IntFacet (PK reference) by default
    - If the FK field name matches a declared Lens, that takes precedence
    """

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


# ── ContractUnion ────────────────────────────────────────────────────────


class ContractUnion:
    """Compiled discriminated union wrapper constructed via | operator on Contracts."""

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
                    from aquilia.contracts.facets import ChoiceFacet

                    if isinstance(facet, ChoiceFacet):
                        candidate_fields.setdefault(fname, []).append(member)

            # Filter to those present in all members
            common_candidates = [
                fname for fname, members_list in candidate_fields.items() if len(members_list) == len(self.members)
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
                    from aquilia.contracts.facets import ChoiceFacet

                    if isinstance(facet, ChoiceFacet):
                        allowed = getattr(facet, "allowed_values", ())
                        for val in allowed:
                            dispatch[val] = member
            return discriminator_field, dispatch

        return None, None

    def validate(self, data: Any) -> tuple[dict, dict]:
        if self._dispatch:
            from aquilia.contracts.facets import UNSET, TextFacet
            from aquilia.contracts.sigil import get_field_value, is_mapping_like

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
        if isinstance(other, ContractUnion):
            return ContractUnion((*self.members, *other.members))
        return ContractUnion((*self.members, other))

    def __ror__(self, other):
        return ContractUnion((other, *self.members))

    def to_json_schema(self) -> dict:
        choices_schemas = []
        for member in self.members:
            choices_schemas.append(member._sigil.to_json_schema())
        sch = {"oneOf": choices_schemas}
        if self.discriminator_field:
            sch["discriminator"] = {"propertyName": self.discriminator_field}
        return sch


# ── Contract Base Class ─────────────────────────────────────────────────


class ContractSerializationDescriptor:
    """
    Expose ``to_dict``/``to_dict_many`` (and their async variants) as both
    class methods and instance methods.

    On an instance, ``bp.to_dict`` binds to ``bp._to_dict_instance``. On the
    class, ``UserContract.to_dict(obj)`` wraps ``obj`` in a throwaway Contract
    first, so a model instance can be molded without constructing one by hand.

    Args:
        name: Public method name — one of ``to_dict``, ``to_dict_many``,
            ``to_dict_async``, ``to_dict_many_async``.
    """

    __slots__ = ("name", "is_many", "is_async")

    def __init__(self, name: str):
        self.name = name
        self.is_many = name.startswith("to_dict_many")
        self.is_async = name.endswith("_async")

    def __get__(self, instance, owner):
        if instance is not None:
            # Accessed on the instance, e.g., bp.to_dict
            return getattr(instance, f"_{self.name}_instance")

        # Accessed on the class, e.g., ComplexUserContract.to_dict
        name = self.name
        if self.is_many:

            def class_many(objs, *, _depth: int = 0, _seen: set | None = None):
                if isinstance(objs, Contract):
                    return getattr(objs, name)(_depth=_depth, _seen=_seen)
                return getattr(owner(many=True), name)(objs, _depth=_depth, _seen=_seen)

            return class_many

        def class_single(obj, *, _depth: int = 0, _seen: set | None = None):
            if isinstance(obj, Contract):
                return getattr(obj, name)(_depth=_depth, _seen=_seen)
            return getattr(owner(instance=obj), name)(_depth=_depth, _seen=_seen)

        return class_single


class Contract(Generic[ModelT], metaclass=ContractMeta):
    """
    The core Contract base class -- defining first-class data contracts between Model instances and the external world.

    Purpose:
        Declaratively manages outbound model serialization (molding), inbound payload validation (casting & sealing),
        field projection filtering, and ORM persistence (imprinting).

    Lifecycle:
        1. **Class Creation**: Metaclass ``ContractMeta.__new__`` parses ``Spec``, gathers Facets, sets up Sigil schemas, and compiles Projections.
        2. **Instantiation**: Bound to outbound ``instance`` or inbound ``data`` (payload dictionary).
        3. **Sealing Phase**: Executes type casting, facet constraints, and cross-field ``@ward`` validators via ``is_sealed()`` or ``is_sealed_async()``.
        4. **Imprint Phase**: Writes back validated data to ORM model instances via ``imprint()``.

    Execution Order:
        - **Inbound Pipeline** (``Contract(data=...)``):
          1. Cast input values via Facet pipelines.
          2. Execute facet-level validators.
          3. Execute ``@ward`` cross-field validator methods.
          4. Store cleaned validated dictionary in ``_validated_data``.
        - **Outbound Pipeline** (``Contract(instance=...)``):
          1. Extract values from model fields/properties via Facet ``source`` mappings.
          2. Filter attributes against active ``projection``.
          3. Transform nested relations through Lens facets or nested contracts.
          4. Output JSON-serializable dictionary payload.

    Parameters:
        instance (ModelT | list[ModelT] | None, optional):
            Model instance or list of model instances for outbound serialization. Defaults to ``None``.
        data (Any, optional):
            Raw dictionary or form payload for inbound validation. Defaults to ``UNSET``.
        many (bool, optional):
            If ``True``, processes a collection of instances/payloads. Defaults to ``False``.
        partial (bool, optional):
            If ``True``, disables required field checks for partial updates (PATCH semantics). Defaults to ``False``.
        projection (str | None, optional):
            Name of specific projection to apply for field filtering. Defaults to ``None``.
        context (dict[str, Any] | None, optional):
            Execution context dictionary (injecting HTTP request, DI container, etc.). Defaults to ``None``.

    Returns:
        Contract: An instantiated Contract instance.

    Exceptions:
        ImprintFault: Raised during ``imprint()`` if data is unsealed or model creation fails.
        SealFault: Raised during validation if ``raise_fault=True`` and validation seals break.
        ContractAsyncMismatchFault: Raised if a contract containing async wards is validated via sync ``is_sealed()``.

    Notes:
        - Thread and Async Safe: Uses context variables for depth tracking and isolated validation state per instance.
        - Subscript syntax support: ``Contract["projection_name"]`` returns a projected reference.

    Examples:
        >>> class UserRegistrationContract(Contract[UserModel]):
        ...     name: str = Field(min_length=1, max_length=100)
        ...     email: typing.Annotated[str, Facet.email() >> strip >> lower]
        ...
        ...     class Spec:
        ...         model = UserModel
        ...         projections = {"summary": ["id", "name", "email"]}
        >>> contract = UserRegistrationContract(data=payload)
        >>> if await contract.is_sealed_async():
        ...     user = await contract.imprint()
    """

    # Class-level default: some paths build instances without running
    # __init__ (Computed.extract), and __getattr__ would otherwise mask the
    # missing attribute as "no such field".
    _active_groups: frozenset[str] | None = None

    to_dict = ContractSerializationDescriptor("to_dict")
    to_dict_many = ContractSerializationDescriptor("to_dict_many")
    to_dict_async = ContractSerializationDescriptor("to_dict_async")
    to_dict_many_async = ContractSerializationDescriptor("to_dict_many_async")

    _spec: _SpecData
    _all_facets: dict[str, Facet]
    _known_field_names: frozenset[str]
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
        if context is not None and (hasattr(context, "container") or type(context).__name__ == "ContractContext"):
            self.context = context
        else:
            self.context = ContractContext(context) if context is not None else ContractContext()

        # State
        self._validated_data: DataObject | list[DataObject] | None = None
        self._errors: dict[str, list[str]] = {}
        self._is_sealed: bool | None = None  # None = not yet validated

        # Reference to compiled schema
        self._sigil = getattr(self.__class__, "_sigil", None)
        # Store context
        self._context = self.context
        # Validation groups requested for the current pass; None = unrestricted.
        self._active_groups: frozenset[str] | None = None

    @property
    def has_async_wards(self) -> bool:
        """
        True if this Contract, or any Contract nested beneath it, declares an
        ``@ward(mode="async")`` method.

        Nested Contracts are included because their wards run as part of this
        Contract's validation. If only the top level were consulted, a Contract
        whose nested child declares an async ward would pass :meth:`is_sealed`
        while that ward never ran — silently skipping validation instead of
        directing the caller to :meth:`is_sealed_async`.
        """
        return self.__class__._has_async_wards_deep()

    @classmethod
    def _has_async_wards_deep(cls, _seen: frozenset[int] = frozenset()) -> bool:
        """
        Walk this Contract's facet tree looking for async wards.

        Args:
            _seen: Contract class ids already visited, so a self-referential
                Contract terminates instead of recursing forever.

        Returns:
            True if this Contract or any nested Contract declares an async ward.

        Performance:
            Memoized per class once the walk is complete; it runs once, not per
            request. Self-referential Contracts are cut by ``_seen``.
        """
        cached = cls.__dict__.get("_async_wards_deep_cache")
        if cached is not None:
            return cached

        if any(wm.mode == "async" for wm in cls._ward_methods):
            cls._async_wards_deep_cache = True
            return True

        from aquilia.contracts.sigil import get_nested_contract_cls

        seen = _seen | {id(cls)}
        result = False
        complete = True
        sigil = getattr(cls, "_sigil", None)
        if sigil is not None:
            for spec in sigil.fields.values():
                if not spec.is_nested_contract:
                    continue
                nested_cls = get_nested_contract_cls(spec.facet)
                if not isinstance(nested_cls, type) or not issubclass(nested_cls, Contract):
                    # An unresolved forward reference (still a string): the
                    # answer for this class is not yet knowable, so it must
                    # not be cached.
                    complete = False
                    continue
                if id(nested_cls) in seen:
                    # Cycle: this branch adds nothing, but the truncation is
                    # specific to the path that reached it.
                    complete = False
                    continue
                if nested_cls._has_async_wards_deep(seen):
                    result = True
                    break

        if result or complete:
            cls._async_wards_deep_cache = result
        return result

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
    def data(self) -> DataObject | list[DataObject] | dict[str, Any] | list[dict[str, Any]]:
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

    def _mold_steps(
        self,
        obj: Any,
        *,
        _depth: int,
        _seen: set | None,
    ) -> Any:
        """
        Mold one instance, yielding each Lens field for the driver to resolve.

        This is the single implementation of the field-molding loop, shared by
        the sync and async serializers. Every step except Lens resolution is
        identical in both modes; a Lens is the only field type that may need to
        await the ORM. Rather than duplicating the loop, this generator yields
        ``(facet, value)`` for each Lens and receives the molded result back via
        ``send()`` — so the driver decides whether resolution is sync or async.

        Args:
            obj: Model instance to mold.
            _depth: Lens traversal depth.
            _seen: Cycle-detection set for Lens traversal.

        Yields:
            ``(lens_facet, raw_value)`` pairs awaiting resolution.

        Returns:
            The completed output mapping (via ``StopIteration.value``).

        See Also:
            :meth:`_to_dict_instance`, :meth:`_to_dict_async_instance`
        """
        projection_fields = self._projections.resolve(self._projection_name)

        result: dict[str, Any] = {}
        for fname, facet in self._bound_facets.items():
            # Skip write-only facets in output
            if facet.write_only:
                continue
            # Apply projection filter. Compared against None, not truthiness:
            # an empty projection means "expose nothing", not "expose all".
            if projection_fields is not None and fname not in projection_fields:
                continue

            # Extract value from instance
            if isinstance(facet, Computed):
                value = facet.extract(obj, _owner=self)
            else:
                value = facet.extract(obj)

            # Mold through Lens (with depth/cycle tracking)
            if isinstance(facet, Lens):
                value = yield (facet, value)
            elif value is not None:
                value = facet.mold(value)
            elif facet.allow_null:
                value = None
            else:
                continue  # Skip None values for non-nullable facets

            result[fname] = value

        return result

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

        Raises:
            LensUnresolvedFault: If a ``many=True`` Lens receives an un-awaited
                related manager. Prefetch the relation, or use
                :meth:`to_dict_async`, which awaits it.
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

        gen = self._mold_steps(obj, _depth=_depth, _seen=_seen)
        try:
            facet, value = next(gen)
            while True:
                molded = facet.mold(value, _depth=_depth, _seen=_seen)
                facet, value = gen.send(molded)
        except StopIteration as stop:
            return stop.value

    async def _to_dict_async_instance(
        self,
        instance: Any = None,
        *,
        _depth: int = 0,
        _seen: set | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Async counterpart of :meth:`_to_dict_instance` — awaits ORM relations.

        Args:
            instance: Override instance (default: self.instance)
            _depth: Internal depth counter for Lens traversal
            _seen: Internal cycle detection set

        Returns:
            The molded mapping, or a list of them for ``many=True``.
        """
        if instance is None and self.many:
            if self.instance is not None:
                return await self.to_dict_many_async(self.instance, _depth=_depth, _seen=_seen)
            if self._validated_data is not None:
                return self._validated_data
            return []

        obj = instance or self.instance
        if obj is None:
            if self._validated_data is not None:
                return self._validated_data
            return {}

        gen = self._mold_steps(obj, _depth=_depth, _seen=_seen)
        try:
            facet, value = next(gen)
            while True:
                molded = await facet.mold_async(value, _depth=_depth, _seen=_seen)
                facet, value = gen.send(molded)
        except StopIteration as stop:
            return stop.value

    def _to_dict_many_instance(
        self,
        instances: Any,
        *,
        _depth: int = 0,
        _seen: set | None = None,
    ) -> list[dict[str, Any]]:
        """Mold multiple instances."""
        if isinstance(instances, Contract):
            return instances.to_dict_many(_depth=_depth, _seen=_seen)
        return [self.to_dict(instance=obj, _depth=_depth, _seen=_seen) for obj in instances]

    async def _to_dict_many_async_instance(
        self,
        instances: Any,
        *,
        _depth: int = 0,
        _seen: set | None = None,
    ) -> list[dict[str, Any]]:
        """
        Async counterpart of :meth:`_to_dict_many_instance`.

        Args:
            instances: An iterable of model instances, an un-awaited related
                manager, or a Contract wrapping them.
            _depth: Lens traversal depth.
            _seen: Cycle-detection set.

        Returns:
            One molded mapping per instance, in input order.

        Performance:
            Instances are molded sequentially. Gathering them concurrently
            would issue one lazy-relation query per row simultaneously and
            exhaust the connection pool on a large result set.
        """
        if isinstance(instances, Contract):
            return await instances.to_dict_many_async(_depth=_depth, _seen=_seen)
        instances = await Lens._resolve_manager(instances)
        return [await self.to_dict_async(instance=obj, _depth=_depth, _seen=_seen) for obj in instances]

    # ── Inbound: Cast + Seal ─────────────────────────────────────────

    def is_sealed(
        self,
        *,
        raise_fault: bool = False,
        groups: str | Sequence[str] | None = None,
        _bypass_async_check: bool = False,
        _async_pending: list[Any] | None = None,
    ) -> bool:
        """
        Validate the input data through the full pipeline.

        Pipeline:
            1. Cast: type coercion per facet
            2. Field seals: per-facet validators
            3. Cross-field seals: ``seal_*()`` methods
            4. Object-level validate: ``validate()``

        Args:
            raise_fault: If True, raise ContractFault on failure.
            groups: Restrict ward execution to these validation groups. Wards
                declared without groups always run; a grouped ward runs only
                when one of its groups is named here. ``None`` (default) runs
                every ungrouped ward and no grouped ones.
            _bypass_async_check: Internal. Skip the async-ward guard because an
                async driver is running this as its synchronous phase.
            _async_pending: Internal. Accumulator for nested Contracts with
                async wards, drained by :meth:`is_sealed_async`.

        Returns:
            True if data passes all seals.
        """
        if groups is not None:
            self._active_groups = frozenset((groups,) if isinstance(groups, str) else groups)

        if not _bypass_async_check and self.has_async_wards:
            raise ContractAsyncMismatchFault(
                "Contract contains async wards (is async but called from sync context) and must be validated using is_sealed_async()."
            )

        if self._is_sealed is not None:
            if raise_fault and not self._is_sealed:
                raise SealFault(
                    message="Contract validation failed",
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

        from aquilia.contracts.sigil import adapt_input, is_mapping_like

        data = adapt_input(self._input_data)
        if not is_mapping_like(data):
            # Previously coerced to {}, which reported every field as missing —
            # a misleading diagnosis of a payload that was never an object.
            self._errors = {"__all__": [contract_message("expected_object", type=type(self._input_data).__name__)]}
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Contract validation failed", errors=self._errors)
            return False

        # ── Unknown field rejection ──────────────────────────────────
        extra_fields_mode = self._spec.extra_fields if self._spec else "ignore"
        if self.context.get("extra_fields"):
            extra_fields_mode = self.context["extra_fields"]

        if extra_fields_mode == "reject" and is_mapping_like(data):
            from aquilia.contracts.sigil import get_keys

            known_fields = self.__class__._known_field_names
            unknown = get_keys(data) - known_fields
            if unknown:
                for field_name in sorted(unknown):
                    self._errors.setdefault(field_name, []).append(contract_message("unknown_field", field=field_name))
                self._is_sealed = False
                if raise_fault:
                    raise SealFault(
                        message="Unknown fields in input data",
                        errors=self._errors,
                    )
                return False

        # Phase 1 + 2: Structural validation via Sigil
        strict_override = self.context.get("strict", None)

        # Native fast path. Only for the plain, common shape: an exact dict,
        # full (non-partial) validation, no strict override. Everything else --
        # and any payload the plan cannot decide with certainty -- returns None
        # and falls through to the Python path below, which stays the reference
        # implementation and the source of every error message.
        validated_dict = None
        if type(data) is dict and not self.partial and strict_override is None and _async_pending is None:
            plan = field_plan_for(self.__class__)
            if plan is not None:
                validated_dict = plan.execute(data)

        if validated_dict is None:
            errors, validated_dict = self._sigil.validate(
                data,
                strict=strict_override,
                partial=self.partial,
                context=self.context,
                _async_pending=_async_pending,
            )
            self._errors.update(errors)
        validated.update(validated_dict)

        if self._errors:
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Contract validation failed", errors=self._errors)
            return False

        # Phase 3: Cross-field seals (ward methods)
        validated = DataObject(validated)
        self.__class__._run_ward_phase(self, validated)

        if self._errors:
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Contract validation failed", errors=self._errors)
            return False

        # Phase 4: Object-level validate
        validated = self.__class__._run_validate_hook(self, validated)

        if self._errors:
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="Contract validation failed", errors=self._errors)
            return False

        self._validated_data = self._freeze_if_needed(validated)
        self._is_sealed = True
        return True

    async def is_sealed_async(
        self,
        *,
        raise_fault: bool = False,
        groups: str | Sequence[str] | None = None,
    ) -> bool:
        """
        Validate the input data, including ``@ward(mode="async")`` methods.

        Required whenever the Contract declares any async ward — the sync
        :meth:`is_sealed` raises :class:`ContractAsyncMismatchFault` in that
        case rather than silently skipping the async validation.

        Args:
            raise_fault: If True, raise :class:`SealFault` on failure instead of
                returning False.

        Returns:
            True if the data passes every phase.

        Raises:
            SealFault: If validation fails and ``raise_fault`` is set.

        Async Behavior:
            The synchronous phases run first (structural validation, sync
            wards, the ``validate()`` hook), then async wards. For
            ``many=True`` Contracts, async wards run **per item** — each row is
            validated independently, matching the per-item semantics of the
            single-item path.

        Examples:
        ```
            Async uniqueness check against the database::

                class UserContract(Contract):
                    email: str

                    @ward(mode="async")
                    async def unique_email(self, data):
                        if await User.objects.filter(email=data["email"]).exists():
                            self.reject("email", "Already registered")

                bp = UserContract(data=payload)
                if not await bp.is_sealed_async():
                    return Response.json(bp.errors, status=422)

            Bulk bodies work the same way::

                bp = UserContract(data=rows, many=True)
                await bp.is_sealed_async()  # async wards run once per row
        ```
        See Also:
            :meth:`is_sealed`, :meth:`seal_stream`
        """
        if groups is not None:
            self._active_groups = frozenset((groups,) if isinstance(groups, str) else groups)

        if self.many:
            return await self._seal_many_async(raise_fault=raise_fault)

        # Run sync pipeline (which skips async wards), collecting any nested
        # Contracts whose async wards still need to be awaited.
        nested_pending: list[Any] = []
        if not self.is_sealed(
            raise_fault=False,
            groups=groups,
            _bypass_async_check=True,
            _async_pending=nested_pending,
        ):
            if raise_fault:
                raise SealFault(message="Contract validation failed", errors=self._errors)
            return False

        # Phase 4b: nested Contracts' async wards
        if nested_pending:
            from aquilia.contracts.sigil import merge_nested_errors

            for path, nested_cls, inst, data_obj in nested_pending:
                await nested_cls._run_ward_phase_async(inst, data_obj, _sync_already_run=True)
                if inst._errors:
                    merge_nested_errors(self._errors, path, inst._errors)

            if self._errors:
                self._is_sealed = False
                self._validated_data = None
                if raise_fault:
                    raise SealFault(message="Contract validation failed", errors=self._errors)
                return False

        # Phase 5: async ward methods. Delegated to the shared helper so group,
        # condition, ordering, and fail-fast semantics cannot drift between the
        # single-item path and the bulk paths.
        await self.__class__._run_ward_phase_async(self, self._validated_data, _sync_already_run=True)

        if self._errors:
            self._is_sealed = False
            self._validated_data = None
            if raise_fault:
                raise SealFault(message="Contract validation failed", errors=self._errors)
            return False

        return True

    def _seal_many(self, *, raise_fault: bool) -> bool:
        """
        Validate a list of input items synchronously.

        Args:
            raise_fault: If True, raise :class:`SealFault` on failure.

        Returns:
            True if every item validates.

        Raises:
            SealFault: If validation fails and ``raise_fault`` is set.
            ContractAsyncMismatchFault: If the Contract declares async wards —
                use :meth:`is_sealed_async` instead, which dispatches per item.

        Security:
            The batch size is capped by ``Spec.max_many_items`` (10,000 by
            default) *before* iteration, so an oversized list is rejected
            without allocating per-item Contract instances.
        """
        items, failure = self._prepare_many_items(raise_fault=raise_fault)
        if items is None:
            return failure

        all_validated = []
        all_errors: dict[str, Any] = {}
        for i, item in enumerate(items):
            child = self._make_child(item)
            if child.is_sealed():
                all_validated.append(child.validated_data)
            else:
                all_errors[str(i)] = child.errors

        return self._finish_many(all_validated, all_errors, raise_fault=raise_fault)

    async def _seal_many_async(self, *, raise_fault: bool) -> bool:
        """
        Async counterpart of :meth:`_seal_many` — validates each item via
        :meth:`is_sealed_async` so async wards run once per item.

        Args:
            raise_fault: If True, raise :class:`SealFault` on failure.

        Returns:
            True if every item validates.

        Raises:
            SealFault: If validation fails and ``raise_fault`` is set.

        Async Behavior:
            Items are validated sequentially rather than concurrently: async
            wards commonly hit a database, and unbounded concurrency over a
            10,000-item batch would exhaust the connection pool.
        """
        items, failure = self._prepare_many_items(raise_fault=raise_fault)
        if items is None:
            return failure

        all_validated = []
        all_errors: dict[str, Any] = {}
        for i, item in enumerate(items):
            child = self._make_child(item)
            if await child.is_sealed_async():
                all_validated.append(child.validated_data)
            else:
                all_errors[str(i)] = child.errors

        return self._finish_many(all_validated, all_errors, raise_fault=raise_fault)

    def _make_child(self, item: Any) -> Contract:
        """Build the per-item child Contract used by the ``many=True`` paths."""
        child = self.__class__(
            data=item,
            partial=self.partial,
            projection=self._projection_name,
            context=self.context,
        )
        # Groups are a property of the validation pass, not of one row.
        child._active_groups = self._active_groups
        return child

    def _prepare_many_items(self, *, raise_fault: bool) -> tuple[list[Any] | None, bool]:
        """
        Normalize and size-check ``many=True`` input.

        Returns:
            ``(items, unused)`` on success, or ``(None, False)`` when the input
            is not a list or exceeds ``Spec.max_many_items`` — in which case
            ``self._errors``/``self._is_sealed`` are already set.

        Raises:
            SealFault: If the input is rejected and ``raise_fault`` is set.
        """
        from aquilia.contracts.sigil import extract_flat_list_mapping, is_mapping_like

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
            return None, False

        # Enforce maximum list size to prevent resource exhaustion
        max_items = self._spec.max_many_items if self._spec else 10000
        # Allow runtime override via context (trusted, server-side data only)
        if self.context.get("max_many_items"):
            max_items = self.context["max_many_items"]

        if len(input_data) > max_items:
            self._errors = {"__all__": [f"List contains {len(input_data)} items, exceeding the maximum of {max_items}"]}
            self._is_sealed = False
            if raise_fault:
                raise SealFault(
                    message=f"Too many items ({len(input_data)} > {max_items})",
                    errors=self._errors,
                )
            return None, False

        return list(input_data), False

    def _finish_many(self, validated: list[Any], errors: dict[str, Any], *, raise_fault: bool) -> bool:
        """Record the aggregated outcome of a ``many=True`` validation pass."""
        if errors:
            self._errors = errors
            self._is_sealed = False
            if raise_fault:
                raise SealFault(message="List validation failed", errors=self._errors)
            return False

        self._validated_data = self._freeze_if_needed(validated)
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
    def validated_data(self) -> DataObject | list[DataObject] | None:
        """The validated data -- only available after successful sealing."""
        if self._is_sealed is None:
            if self.has_async_wards:
                raise ContractAsyncMismatchFault(
                    "Contract contains async wards (is async but called from sync context) and must be validated using await is_sealed_async() before accessing properties."
                )
            self.is_sealed()
        return self._validated_data

    @property
    def errors(self) -> dict[str, list[str]]:
        """Validation errors -- available after sealing attempt."""
        if self._is_sealed is None:
            if self.has_async_wards:
                raise ContractAsyncMismatchFault(
                    "Contract contains async wards (is async but called from sync context) and must be validated using await is_sealed_async() before accessing properties."
                )
            self.is_sealed()
        return self._errors

    # ── Write: Imprint ───────────────────────────────────────────────

    @overload
    async def imprint(
        self,
        instance: None = None,
        *,
        partial: bool | None = None,
    ) -> ModelT: ...

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
                # Allow through if no model (pure Contract)
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
        Generate JSON Schema for this Contract.

        Args:
            projection: Named projection (None = default)
            mode: "output" (mold schema) or "input" (cast schema)

        Returns:
            JSON Schema dict
        """
        base_schema = cls._sigil.to_json_schema()
        if mode == "input" and (projection is None or projection == "__all__"):
            projection_fields = frozenset(cls._all_facets.keys())
        else:
            projection_fields = cls._projections.resolve(projection)

        properties: dict[str, Any] = {}
        required: list[str] = []

        import copy

        for fname, facet in cls._all_facets.items():
            if mode == "output" and facet.write_only:
                continue
            if mode == "input" and facet.read_only:
                continue
            if projection_fields is not None and fname not in projection_fields:
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
    def _run_ward_phase(
        cls,
        inst: Contract,
        data_obj: DataObject,
        *,
        include_async: bool = False,
    ) -> None:
        """
        Run cross-field ward methods against already-structurally-validated data.

        Shared by :meth:`is_sealed`, :meth:`seal_many`, and :meth:`seal_stream`
        so all four entry points apply identical ward semantics. Errors are
        accumulated onto ``inst._errors`` rather than raised — a ward that
        rejects a field is an expected outcome, not an exceptional one.

        Args:
            inst: Contract instance the wards are bound to; receives errors.
            data_obj: The validated data passed as the ward's ``data`` argument.
            include_async: If False, ``mode="async"`` wards are skipped (they
                belong to the ``is_sealed_async`` phase). If True, async wards
                are invoked but *not* awaited — only use from
                :meth:`_run_ward_phase_async`.

        Side Effects:
            Mutates ``inst._errors``.
        """
        groups = inst._active_groups
        fail_fast = inst._spec is not None and inst._spec.fail_fast
        for wm in cls._ward_methods:
            if wm.mode != "sync" and not include_async:
                continue
            if not wm.should_run(data_obj, groups):
                continue
            try:
                wm.fn(inst, data_obj)
            except CastFault as exc:
                msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                    inst._errors.setdefault(exc.field, []).append(msg)
            except Exception as exc:
                inst._errors.setdefault("__all__", []).append(str(exc))

            if inst._errors and fail_fast:
                return

    @classmethod
    async def _run_ward_phase_async(
        cls,
        inst: Contract,
        data_obj: DataObject,
        *,
        _sync_already_run: bool = False,
    ) -> None:
        """
        Async counterpart of :meth:`_run_ward_phase` — runs *all* wards.

        Sync wards run inline; ``mode="async"`` wards are awaited when they are
        coroutine functions and called directly otherwise (defensive: a ward
        may be declared ``mode="async"`` while remaining a plain function).

        Args:
            inst: Contract instance the wards are bound to; receives errors.
            data_obj: The validated data passed as the ward's ``data`` argument.
            _sync_already_run: Skip ``mode="sync"`` wards because the caller
                already ran them. Used by the nested-Contract async drain,
                where the sync phase completed during structural validation —
                without this, a ward with side effects would fire twice.

        Side Effects:
            Mutates ``inst._errors``.
        """
        import inspect

        groups = inst._active_groups
        fail_fast = inst._spec is not None and inst._spec.fail_fast
        for wm in cls._ward_methods:
            if _sync_already_run and wm.mode != "async":
                continue
            if not wm.should_run(data_obj, groups):
                continue
            try:
                if wm.mode == "async" and inspect.iscoroutinefunction(wm.fn):
                    await wm.fn(inst, data_obj)
                else:
                    wm.fn(inst, data_obj)
            except CastFault as exc:
                msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                    inst._errors.setdefault(exc.field, []).append(msg)
            except Exception as exc:
                inst._errors.setdefault("__all__", []).append(str(exc))

            if inst._errors and fail_fast:
                return

    @staticmethod
    def _run_validate_hook(inst: Contract, validated: DataObject) -> DataObject:
        """
        Run the overridable object-level :meth:`validate` hook exactly once.

        Args:
            inst: Contract instance whose ``validate()`` override to invoke.
            validated: Data to pass to the hook.

        Returns:
            The hook's return value, or ``validated`` unchanged if the hook
            raised (in which case the reason is recorded on ``inst._errors``).

        Side Effects:
            Mutates ``inst._errors`` on failure.

        Notes:
            Exactly-once invocation matters: a ``validate()`` override may have
            side effects (metrics, audit logs, external calls). Earlier
            revisions of the bulk paths invoked it up to three times per row.
        """
        try:
            return inst.validate(validated)
        except CastFault as exc:
            msg = exc.field_errors.get(exc.field, [str(exc)])[0]
            if exc.field not in inst._errors or msg not in inst._errors[exc.field]:
                inst._errors.setdefault(exc.field, []).append(msg)
        except SealFault as exc:
            if getattr(exc, "field_errors", None):
                for field, msgs in exc.field_errors.items():
                    inst._errors.setdefault(field, []).extend(msgs)
            else:
                inst._errors.setdefault("__all__", []).append(str(exc))
        except Exception as exc:
            inst._errors.setdefault("__all__", []).append(str(exc))
        return validated

    @classmethod
    def _seal_row(cls, row: Any, index: int, *, context: dict[str, Any] | None = None) -> SealOutcome:
        """
        Validate one row through the full pipeline and report the outcome.

        The single implementation behind :meth:`seal_many` and
        :meth:`seal_stream`. Runs, in order: Sigil structural validation, sync
        ward methods, then the object-level ``validate()`` hook — each stage
        gated on the previous one producing no errors, and each stage run
        exactly once.

        Args:
            row: One inbound record (mapping-like).
            index: Position of the row in the batch; echoed into the outcome.
            context: Optional contextual data forwarded to the Contract.

        Returns:
            A :class:`SealOutcome` carrying either the validated value or the
            accumulated per-field errors.

        Performance:
            One Contract instantiation and one Sigil pass per row.

        See Also:
            :meth:`_seal_row_async` — variant that also runs async wards.
        """
        from aquilia.contracts.sigil import adapt_input, is_mapping_like

        row = adapt_input(row)
        if not is_mapping_like(row):
            return SealOutcome(
                index=index,
                ok=False,
                value=None,
                errors={"__all__": [contract_message("expected_object", type=type(row).__name__)]},
            )

        errors, validated_dict = cls._sigil.validate(row, context=context)
        if errors:
            return SealOutcome(index=index, ok=False, value=None, errors=errors)

        inst = cls(data=row, context=context)
        inst._errors = {}
        validated = DataObject(validated_dict)

        cls._run_ward_phase(inst, validated)
        if not inst._errors:
            validated = cls._run_validate_hook(inst, validated)

        if inst._errors:
            return SealOutcome(index=index, ok=False, value=None, errors=inst._errors)
        return SealOutcome(index=index, ok=True, value=validated, errors=None)

    @classmethod
    async def _seal_row_async(cls, row: Any, index: int, *, context: dict[str, Any] | None = None) -> SealOutcome:
        """
        Async variant of :meth:`_seal_row` — also awaits ``mode="async"`` wards.

        Args:
            row: One inbound record (mapping-like).
            index: Position of the row in the batch; echoed into the outcome.
            context: Optional contextual data forwarded to the Contract.

        Returns:
            A :class:`SealOutcome`.

        See Also:
            :meth:`_seal_row`
        """
        from aquilia.contracts.sigil import adapt_input, is_mapping_like

        row = adapt_input(row)
        if not is_mapping_like(row):
            return SealOutcome(
                index=index,
                ok=False,
                value=None,
                errors={"__all__": [contract_message("expected_object", type=type(row).__name__)]},
            )

        errors, validated_dict = cls._sigil.validate(row, context=context)
        if errors:
            return SealOutcome(index=index, ok=False, value=None, errors=errors)

        inst = cls(data=row, context=context)
        inst._errors = {}
        validated = DataObject(validated_dict)

        await cls._run_ward_phase_async(inst, validated)
        if not inst._errors:
            validated = cls._run_validate_hook(inst, validated)

        if inst._errors:
            return SealOutcome(index=index, ok=False, value=None, errors=inst._errors)
        return SealOutcome(index=index, ok=True, value=validated, errors=None)

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        prefix: str = "",
        seal: bool = True,
    ) -> Contract:
        """
        Build a Contract from environment variables.

        Field names map to upper-case variable names, so a field ``database_url``
        reads ``DATABASE_URL`` (or ``<PREFIX>DATABASE_URL``). Absent variables
        are omitted rather than set empty, so each field's ``default`` and
        ``required`` rules decide the outcome exactly as they would for a JSON
        body.

        Args:
            env: Mapping to read. Defaults to :data:`os.environ`.
            prefix: Prefix stripped from variable names, e.g. ``"APP_"``.
            seal: Validate before returning. Default ``True`` — configuration
                errors should surface at startup, not at first use.

        Returns:
            A Contract populated from the environment.

        Raises:
            SealFault: If ``seal`` is set and validation fails.

        Examples:
            >>> class SettingsContract(Contract):
            ...     port = IntFacet(default=8000)
            ...     database_url = TextFacet()
            >>> settings = SettingsContract.from_env(prefix="APP_")

        Notes:
            Every value arrives as a string; the facets' normal casting turns
            ``"8000"`` into an ``int``. Configuration therefore gets the same
            validation as request data instead of a parallel parsing path.
        """
        import os

        source = os.environ if env is None else env
        data: dict[str, Any] = {}
        for fname in cls._all_facets:
            key = f"{prefix}{fname.upper()}"
            if key in source:
                data[fname] = source[key]

        contract = cls(data=data)
        if seal:
            contract.is_sealed(raise_fault=True)
        return contract

    @classmethod
    def from_cli(
        cls,
        argv: Sequence[str] | None = None,
        *,
        seal: bool = True,
    ) -> Contract:
        """
        Build a Contract from command-line arguments.

        Parses the common ``--flag value``, ``--flag=value``, and bare
        ``--flag`` (boolean) forms. Dashes in flag names map to underscores, so
        ``--database-url`` fills a ``database_url`` field. A flag repeated more
        than once collects into a list for a ``ListFacet`` to validate.

        Args:
            argv: Arguments to parse. Defaults to ``sys.argv[1:]``.
            seal: Validate before returning. Default ``True``.

        Returns:
            A Contract populated from the parsed arguments.

        Raises:
            SealFault: If ``seal`` is set and validation fails.

        Examples:
            >>> class ImportContract(Contract):
            ...     source = TextFacet()
            ...     dry_run = BoolFacet(default=False)
            >>> options = ImportContract.from_cli(["--source", "data.csv", "--dry-run"])

        Notes:
            A deliberately small parser for feeding a Contract, not a
            replacement for the ``aq`` CLI's Click layer. Unknown flags are
            ignored so a Contract can read the subset of arguments it cares
            about from a larger command line.
        """
        import sys

        args = list(sys.argv[1:] if argv is None else argv)
        raw: dict[str, Any] = {}

        index = 0
        while index < len(args):
            token = args[index]
            if not token.startswith("--"):
                index += 1
                continue

            token = token[2:]
            if "=" in token:
                name, value = token.split("=", 1)
            else:
                name = token
                nxt = args[index + 1] if index + 1 < len(args) else None
                if nxt is not None and not nxt.startswith("--"):
                    value = nxt
                    index += 1
                else:
                    value = "true"  # bare flag
            index += 1

            name = name.replace("-", "_")
            if name in raw:
                existing = raw[name]
                raw[name] = [*existing, value] if isinstance(existing, list) else [existing, value]
            else:
                raw[name] = value

        data = {k: v for k, v in raw.items() if k in cls._all_facets}

        contract = cls(data=data)
        if seal:
            contract.is_sealed(raise_fault=True)
        return contract

    @classmethod
    def seal_many(cls, rows: list[dict], *, parallel: bool = False, raise_on_any: bool = False) -> list[SealOutcome]:
        """
        Validate multiple rows of input data, returning one outcome per row.

        Args:
            rows: Inbound records.
            parallel: Spread rows across a :class:`~concurrent.futures.ThreadPoolExecutor`.
                See the Performance note before enabling this.
            raise_on_any: Raise :class:`SealFault` on the first failing row
                instead of returning its outcome.

        Returns:
            One :class:`SealOutcome` per input row, in input order.

        Raises:
            SealFault: If ``raise_on_any`` is set and any row fails.

        Performance:
            ``parallel=True`` is only useful when ward methods block on I/O.
            Structural validation and ward dispatch are pure-Python CPU work,
            which CPython's GIL serializes — on a standard build this flag adds
            thread-scheduling overhead without adding throughput. It becomes
            genuinely parallel on a free-threaded interpreter build.

        Examples:
            >>> outcomes = OrderContract.seal_many([{"total": 10}, {"total": -1}])
            >>> [o.ok for o in outcomes]
            [True, False]

            Collect the valid rows and report the rest::

                good = [o.value for o in outcomes if o.ok]
                bad = {o.index: o.errors for o in outcomes if not o.ok}

        Notes:
            Async wards are not run by this method; use :meth:`seal_stream` or
            per-row :meth:`is_sealed_async` when async validation is required.

        See Also:
            :meth:`seal_stream`, :meth:`seal_columnar`
        """
        if not parallel or len(rows) <= 1:
            outcomes = [cls._seal_row(row, idx) for idx, row in enumerate(rows)]
        else:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=min(32, len(rows))) as executor:
                outcomes = list(executor.map(lambda args: cls._seal_row(args[1], args[0]), enumerate(rows)))

        if raise_on_any:
            for outcome in outcomes:
                if not outcome.ok:
                    raise SealFault(message="Seal validation failed", errors=outcome.errors)
        return outcomes

    @classmethod
    async def seal_stream(cls, byte_or_dict_iterator: Any, *, chunk_size: int | None = None) -> Any:
        """
        Validate a stream of NDJSON bytes or pre-parsed dicts, lazily.

        Yields one outcome per record as it is decoded, so memory stays flat
        regardless of stream length — the intended entry point for bulk
        ingestion of untrusted payloads.

        Args:
            byte_or_dict_iterator: Async iterable yielding ``dict`` records, or
                ``bytes``/``str`` chunks of newline-delimited JSON. Chunks need
                not align to record boundaries; partial lines are buffered.
            chunk_size: Accepted for call-site symmetry; the caller controls
                chunking by what it yields.

        Yields:
            :class:`SealOutcome` per record, including malformed-JSON lines
            (reported as an ``__all__`` error rather than raising).

        Async Behavior:
            Both sync and ``mode="async"`` ward methods run for every record.

        Examples:
            >>> async for outcome in EventContract.seal_stream(request.iter_bytes()):
            ...     if outcome.ok:
            ...         await sink.write(outcome.value)

        See Also:
            :meth:`seal_many`, :meth:`_seal_row_async`
        """
        import json

        idx = 0
        buffer = ""

        async for chunk in byte_or_dict_iterator:
            if isinstance(chunk, dict):
                yield await cls._seal_row_async(chunk, idx)
                idx += 1
                continue

            buffer += chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk)

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except Exception as exc:
                    yield SealOutcome(index=idx, ok=False, value=None, errors={"__all__": [f"JSON parse error: {exc}"]})
                else:
                    yield await cls._seal_row_async(item, idx)
                idx += 1

        if buffer.strip():
            try:
                item = json.loads(buffer.strip())
            except Exception as exc:
                yield SealOutcome(index=idx, ok=False, value=None, errors={"__all__": [f"JSON parse error: {exc}"]})
            else:
                yield await cls._seal_row_async(item, idx)

    @classmethod
    def seal_columnar(cls, rows_as_dicts_iterable: Any) -> ColumnarReport:
        """Perform column-oriented validation over bulk records."""
        rows = list(rows_as_dicts_iterable)
        num_rows = len(rows)
        valid_mask = [True] * num_rows
        errors_by_column = {fname: [None] * num_rows for fname in cls._sigil.fields}

        for fname, spec in cls._sigil.fields.items():
            facet = spec.facet

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

        from aquilia.contracts.facets import (
            BoolFacet,
            ChoiceFacet,
            DictFacet,
            FloatFacet,
            IntFacet,
            ListFacet,
            TextFacet,
        )
        from aquilia.contracts.sigil import get_nested_contract_cls

        result = {}
        for fname, spec in cls._sigil.fields.items():
            facet = spec.facet
            if facet.read_only:
                continue

            nested_cls = get_nested_contract_cls(facet)
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
                        result[fname] = [
                            "".join(random.choice(string.ascii_lowercase) for _ in range(5)) for _ in range(num_items)
                        ]
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

            import uuid
            from datetime import date, datetime

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
            raise ImportError("hypothesis is not installed. pip install hypothesis to use Contract.strategy().")

        import string

        from aquilia.contracts.facets import (
            BoolFacet,
            ChoiceFacet,
            DictFacet,
            FloatFacet,
            IntFacet,
            ListFacet,
            TextFacet,
        )
        from aquilia.contracts.sigil import get_nested_contract_cls

        fields_strategies = {}
        for fname, spec in cls._sigil.fields.items():
            facet = spec.facet
            if facet.read_only:
                continue

            nested_cls = get_nested_contract_cls(facet)
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
                    fields_strategies[fname] = st.text(
                        alphabet=string.ascii_lowercase, min_size=min_len, max_size=max_len
                    )
                continue

            if isinstance(facet, IntFacet):
                min_val = facet.min_value if facet.min_value is not None else -1000
                max_val = facet.max_value if facet.max_value is not None else 1000

                mult = getattr(facet, "multiple_of", None)
                if mult is not None:
                    fields_strategies[fname] = st.integers(
                        min_value=(min_val + mult - 1) // mult if min_val is not None else -100,
                        max_value=max_val // mult if max_val is not None else 100,
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
                        max_value=int(max_val / mult) if max_val is not None else 100,
                    ).map(lambda x, m=mult: float(x * m))
                else:
                    fields_strategies[fname] = st.floats(
                        min_value=min_val, max_value=max_val, allow_nan=False, allow_infinity=False
                    )
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

    def _freeze_if_needed(self, validated: Any) -> Any:
        """
        Freeze validated data when the Contract declares ``Spec.frozen``.

        A frozen Contract's validated data rejects mutation, so a value that
        passed validation cannot be edited afterwards — the guarantee
        ``is_sealed()`` gives would otherwise expire the moment a caller
        assigned to a field.

        Args:
            validated: The freshly validated data (a ``DataObject``, or a list
                of them for ``many=True``).

        Returns:
            The same object, frozen in place when ``Spec.frozen`` is set.

        See Also:
            :meth:`copy` — the supported way to derive an updated Contract from
            a frozen one.
        """
        if self._spec is None or not self._spec.frozen:
            return validated
        if isinstance(validated, list):
            for item in validated:
                if isinstance(item, DataObject):
                    item.freeze()
        elif isinstance(validated, DataObject):
            validated.freeze()
        return validated

    def __eq__(self, other: object) -> bool:
        """
        Compare two Contracts by class and validated data.

        Two Contracts are equal when they are the same class and carry the same
        validated data. Unvalidated Contracts compare on their raw input
        instead, so a comparison before sealing is still meaningful rather than
        falling back to identity.

        Returns:
            ``NotImplemented`` for non-Contract operands, so Python falls back
            to the reflected operation.
        """
        if not isinstance(other, Contract):
            return NotImplemented
        if type(self) is not type(other):
            return False
        if self._validated_data is not None and other._validated_data is not None:
            return self._validated_data == other._validated_data
        if self._validated_data is not None or other._validated_data is not None:
            return False
        return self._input_data == other._input_data

    def __hash__(self) -> int:
        # Contracts hold mutable validated data, so they are unhashable by
        # design — defining __eq__ without this would silently make them so.
        raise TypeError(f"{type(self).__name__} is unhashable (its validated data is mutable)")

    def copy(
        self,
        *,
        update: dict[str, Any] | None = None,
        validate: bool = True,
    ) -> Contract:
        """
        Return a new Contract with some fields replaced.

        Args:
            update: Field values to override. Merged over this Contract's
                current data; keys absent from ``update`` are carried over.
            validate: Seal the copy before returning it. Default ``True`` —
                an override can violate a constraint the original satisfied, so
                skipping validation would produce a Contract whose
                ``validated_data`` never passed the rules it claims to enforce.

        Returns:
            A new Contract of the same class, projection, and context.

        Raises:
            SealFault: If ``validate`` is set and the updated data fails.
            ContractAsyncMismatchFault: If ``validate`` is set on a Contract
                with async wards. Use :meth:`copy_async` instead.

        Examples:
            >>> updated = contract.copy(update={"name": "New"})

            Defer validation when building up a payload in stages::

                draft = contract.copy(update={"name": "New"}, validate=False)

        See Also:
            :meth:`copy_async` — the variant that awaits async wards.
        """
        clone = self._copy_unsealed(update)
        if validate:
            clone.is_sealed(raise_fault=True)
        return clone

    async def copy_async(
        self,
        *,
        update: dict[str, Any] | None = None,
    ) -> Contract:
        """
        Async counterpart of :meth:`copy` — awaits async wards on the copy.

        Args:
            update: Field values to override.

        Returns:
            A new, sealed Contract of the same class.

        Raises:
            SealFault: If the updated data fails validation.
        """
        clone = self._copy_unsealed(update)
        await clone.is_sealed_async(raise_fault=True)
        return clone

    def _copy_unsealed(self, update: dict[str, Any] | None) -> Contract:
        """Build an unsealed copy of this Contract with ``update`` merged in."""
        from aquilia.contracts.sigil import adapt_input, is_mapping_like

        base: dict[str, Any]
        if self._validated_data is not None and not self.many:
            base = dict(self._validated_data)
        else:
            adapted = adapt_input(self._input_data)
            base = dict(adapted) if is_mapping_like(adapted) else {}

        if update:
            base.update(update)

        return type(self)(
            data=base,
            partial=self.partial,
            projection=self._projection_name,
            context=self.context,
            many=self.many,
        )

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
