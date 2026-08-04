"""
Aquilia Contract Sigil -- compiled schema IR.

A Sigil is built once per Contract class and stored as ``cls._sigil``.
It is the compiled, immutable representation of the schema.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from aquilia.contracts.exceptions import MAX_NESTING_DEPTH, CastFault
from aquilia.contracts.facets import (
    UNSET,
    BoolFacet,
    Computed,
    Constant,
    DateFacet,
    DateTimeFacet,
    DecimalFacet,
    DictFacet,
    DurationFacet,
    FileFacet,
    FloatFacet,
    Inject,
    IntFacet,
    ListFacet,
    TextFacet,
    TimeFacet,
    UUIDFacet,
)
from aquilia.contracts.messages import contract_message
from aquilia.contracts.pipeline import Pipeline
from aquilia.faults.domains import RegistryFault
from aquilia.utils.data import DataObject

__all__ = ["Sigil", "FieldSpec", "SigilDiff", "FieldDiff", "build_sigil"]

# Module-level caches for validation helpers
_MAPPING_LIKE_TYPES = None
_MULTIDICT_CLS = None
_FORMDATA_CLS = None
_FIELD_REGEX_CACHE = {}
_EXTRACT_FLAT_P1 = re.compile(r"^\[(\d+)\]")
_EXTRACT_FLAT_P2 = re.compile(r"^(\d+)\b")


def _init_validation_types():
    global _MAPPING_LIKE_TYPES, _MULTIDICT_CLS, _FORMDATA_CLS
    if _MAPPING_LIKE_TYPES is not None:
        return
    from collections.abc import Mapping

    types = [dict, Mapping]
    try:
        from aquilia._datastructures import MultiDict

        _MULTIDICT_CLS = MultiDict
        types.append(MultiDict)
    except ImportError:
        pass
    try:
        from aquilia._uploads import FormData

        _FORMDATA_CLS = FormData
        types.append(FormData)
    except ImportError:
        pass
    _MAPPING_LIKE_TYPES = tuple(types)


# ---------------------------------------------------------------------------
# Sigil / FieldSpec
# ---------------------------------------------------------------------------


class FieldSpec:
    """Compiled field specification in a Sigil schema."""

    __slots__ = (
        "name",
        "facet",
        "required",
        "default",
        "default_factory",
        "pipeline",
        "is_nested_contract",
        "is_lens",
    )

    def __init__(
        self,
        name: str,
        facet: Any,
        required: bool,
        default: Any,
        default_factory: Any,
        pipeline: Pipeline | None = None,
        is_nested_contract: bool = False,
        is_lens: bool = False,
    ):
        self.name = name
        self.facet = facet
        self.required = required
        self.default = default
        self.default_factory = default_factory
        self.pipeline = pipeline
        self.is_nested_contract = is_nested_contract
        self.is_lens = is_lens

    def __repr__(self) -> str:
        return f"<FieldSpec '{self.name}' type={type(self.facet).__name__}>"


class Sigil:
    """Immutable compiled representation of a Contract validation schema."""

    __slots__ = (
        "fields",
        "ward_methods",
        "strict",
        "revision",
        "migrate_from",
        "migrate_step",
        "discriminator",
        "content_hash",
        "_json_schema_cache",
    )

    def __init__(
        self,
        fields: dict[str, FieldSpec],
        ward_methods: tuple[Any, ...],
        strict: bool = False,
        revision: int | None = None,
        migrate_from: dict[int, Callable[[dict], dict]] | None = None,
        migrate_step: Callable[[dict, int], dict] | None = None,
        discriminator: str | None = None,
    ):
        self.fields = fields
        self.ward_methods = ward_methods
        self.strict = strict
        self.revision = revision
        self.migrate_from = migrate_from or {}
        self.migrate_step = migrate_step
        self.discriminator = discriminator
        self._json_schema_cache = None
        self.content_hash = self._compute_content_hash()

    def _compute_content_hash(self) -> str:
        """Compute stable deterministic sha256 hash of the schema shape."""
        hasher = hashlib.sha256()
        structure = []
        for name, spec in sorted(self.fields.items()):
            facet_shape = serialize_facet_shape(spec.facet)
            structure.append((name, type(spec.facet).__name__, facet_shape))

        repr_str = repr(structure)
        hasher.update(repr_str.encode("utf-8"))
        return hasher.hexdigest()

    def validate(
        self,
        data: Any,
        *,
        strict: bool | None = None,
        partial: bool = False,
        context: dict[str, Any] | None = None,
        _depth: int = 0,
        _async_pending: list[Any] | None = None,
        _path: tuple[str, ...] = (),
    ) -> tuple[dict[str, list[str]], dict[str, Any]]:
        """
        Validate input data against this schema. Never raises.

        Args:
            data: Mapping-like inbound payload.
            strict: Override the Contract's ``Spec.strict`` setting. In strict
                mode a field's declared type must already match — ``cast()`` is
                skipped, so any normalization a Facet performs during casting
                (trimming, case folding) does **not** run.
            partial: Skip "this field is required" errors for absent keys
                (PATCH semantics).
            context: Contextual data; also the resolution source for
                ``Inject`` facets.
            _depth: Internal nested-Contract recursion counter. Recursion is
                capped at :data:`~aquilia.contracts.exceptions.MAX_NESTING_DEPTH`
                so a deeply nested payload yields a structured error rather
                than an uncaught ``RecursionError``.
            _async_pending: Internal. When supplied, nested Contracts declaring
                ``@ward(mode="async")`` are not rejected — instead a
                ``(path, contract_cls, data, validated)`` record is appended for
                the async driver to await. When ``None`` (the synchronous entry
                point), such a nested Contract raises
                :class:`ContractAsyncMismatchFault`, matching the top-level
                behavior of :meth:`~aquilia.contracts.core.Contract.is_sealed`.
            _path: Internal. Dotted field path of this Sigil within the outer
                Contract, used to report nested async ward errors at the right
                location.

        Returns:
            ``(errors, validated)``. ``errors`` maps field name to a list of
            reasons (or, for nested collections, to a nested error mapping).

        See Also:
            :meth:`aquilia.contracts.core.Contract.is_sealed` — the caller that
            layers ward methods and the object-level hook on top of this.
        """
        errors: dict[str, list[str]] = {}
        validated: dict[str, Any] = {}
        context = context or {}
        is_strict = self.strict if strict is None else strict

        # Run migrations sequentially if revision context matches
        if self.revision is not None and self.migrate_from and is_mapping_like(data):
            data_rev = None
            if isinstance(data, dict) or hasattr(data, "get"):
                data_rev = data.get("__revision__")

            if data_rev is None and self.migrate_from:
                # If __revision__ is not specified, start migrating from the lowest available migration revision
                data_rev = min(self.migrate_from.keys())

            if data_rev is not None and isinstance(data_rev, int) and data_rev < self.revision:
                data = dict(data)
                current_rev = data_rev
                while current_rev < self.revision:
                    next_rev = current_rev + 1
                    if self.migrate_step is not None:
                        try:
                            data = self.migrate_step(data, current_rev)
                            current_rev = next_rev
                        except Exception as e:
                            return {"__revision__": [f"Migration failed: {e}"]}, {}
                    else:
                        migration_fn = self.migrate_from.get(current_rev)
                        if migration_fn is not None:
                            try:
                                data = migration_fn(data)
                                current_rev = next_rev
                            except Exception as e:
                                return {"__revision__": [f"Migration failed: {e}"]}, {}
                        else:
                            return {
                                "__revision__": [f"Missing migration path from revision {current_rev} to {next_rev}"]
                            }, {}

        for fname, spec in self.fields.items():
            facet = spec.facet
            if isinstance(facet, (Computed, Constant)):
                continue

            if isinstance(facet, Inject):
                resolved = facet.resolve_from_context(context)
                if resolved is not UNSET:
                    validated[fname] = resolved
                continue

            if facet.read_only:
                continue

            raw = get_field_value(data, fname, facet)

            # Handle missing values
            if raw is UNSET:
                if partial:
                    continue
                if facet.default is not UNSET:
                    default = facet.default() if callable(facet.default) else facet.default
                    validated[fname] = default
                    continue
                if facet.required:
                    errors.setdefault(fname, []).append(contract_message("required"))
                    continue
                if facet.allow_null:
                    validated[fname] = None
                    continue
                continue

            # Handle null
            if raw is None:
                if facet.allow_null:
                    validated[fname] = None
                    continue
                errors.setdefault(fname, []).append(contract_message("not_null"))
                continue

            # Recursive nested contracts check
            nested_cls, is_many = resolve_nested(facet) if spec.is_nested_contract else (None, False)
            if nested_cls is not None:
                # Depth guard: a self-referential Contract fed deeply nested
                # input would otherwise recurse until the interpreter's stack
                # limit, surfacing as an uncaught RecursionError.
                if _depth >= MAX_NESTING_DEPTH:
                    errors.setdefault(fname, []).append(contract_message("nesting_depth", max=MAX_NESTING_DEPTH))
                    continue

                if is_many:
                    if not isinstance(raw, (list, tuple)):
                        errors.setdefault(fname, []).append(contract_message("expected_list"))
                        continue
                    list_errors = {}
                    list_validated = []
                    for idx, item in enumerate(raw):
                        item = adapt_input(item)
                        if not is_mapping_like(item):
                            list_errors[str(idx)] = {"__all__": [contract_message("expected_dict")]}
                            continue
                        sub_errors, sub_validated = run_nested_contract(
                            nested_cls,
                            item,
                            strict=strict,
                            partial=partial,
                            context=context,
                            _depth=_depth + 1,
                            _async_pending=_async_pending,
                            _path=(*_path, fname, str(idx)),
                        )
                        if sub_errors:
                            list_errors[str(idx)] = sub_errors
                        else:
                            list_validated.append(sub_validated)
                    if list_errors:
                        errors[fname] = list_errors  # type: ignore[assignment]
                    else:
                        try:
                            validated[fname] = facet.seal(list_validated)
                        except CastFault as exc:
                            msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                            errors.setdefault(fname, []).append(msg)
                        except Exception as exc:
                            errors.setdefault(fname, []).append(str(exc))
                else:
                    raw = adapt_input(raw)
                    if not is_mapping_like(raw):
                        errors.setdefault(fname, []).append(contract_message("expected_dict"))
                        continue
                    sub_errors, sub_validated = run_nested_contract(
                        nested_cls,
                        raw,
                        strict=strict,
                        partial=partial,
                        context=context,
                        _depth=_depth + 1,
                        _async_pending=_async_pending,
                        _path=(*_path, fname),
                    )
                    if sub_errors:
                        errors[fname] = sub_errors  # type: ignore[assignment]
                    else:
                        try:
                            validated[fname] = facet.seal(sub_validated)
                        except CastFault as exc:
                            msg = exc.field_errors.get(exc.field, [str(exc)])[0]
                            errors.setdefault(fname, []).append(msg)
                        except Exception as exc:
                            errors.setdefault(fname, []).append(str(exc))
                continue

            # Strict mode vs Normal mode
            if is_strict:
                if not check_strict_type(facet, raw):
                    errors.setdefault(fname, []).append(
                        contract_message("invalid_type", expected=type(facet).__name__.replace("Facet", "").lower())
                    )
                    continue
                if spec.pipeline is not None:
                    ok, final_val, err = spec.pipeline.run(raw)
                    if not ok:
                        errors.setdefault(fname, []).append(err or "Pipeline failed")
                        continue
                    sealed_value = final_val
                else:
                    try:
                        sealed_value = facet.seal(raw)
                    except Exception as exc:
                        errors.setdefault(fname, []).append(str(exc))
                        continue
            else:
                if spec.pipeline is not None:
                    ok, final_val, err = spec.pipeline.run(raw)
                    if not ok:
                        errors.setdefault(fname, []).append(err or "Pipeline failed")
                        continue
                    sealed_value = final_val
                else:
                    try:
                        cast_value = facet.cast(raw)
                        sealed_value = facet.seal(cast_value)
                    except Exception as exc:
                        errors.setdefault(fname, []).append(str(exc))
                        continue

            validated[fname] = sealed_value

        return errors, validated

    async def validate_async(
        self,
        data: Any,
        *,
        strict: bool | None = None,
        partial: bool = False,
        context: dict[str, Any] | None = None,
        _depth: int = 0,
    ) -> tuple[dict[str, list[str]], dict[str, Any]]:
        """
        Async counterpart of :meth:`validate` — awaits nested async wards.

        The structural pass is pure CPU work and identical in both modes, so
        this method runs :meth:`validate` once with an accumulator attached,
        then drains the nested Contracts that declared
        ``@ward(mode="async")``. There is no second traversal and no duplicated
        field loop.

        Args:
            data: Mapping-like inbound payload.
            strict: Override the Contract's ``Spec.strict`` setting.
            partial: Skip required-field errors for absent keys.
            context: Contextual data; resolution source for ``Inject`` facets.
            _depth: Internal nested-Contract recursion counter.

        Returns:
            ``(errors, validated)``, with any nested async ward failures merged
            in at the failing Contract's path.

        See Also:
            :meth:`validate` — the synchronous entry point, which rejects
            nested async wards rather than skipping them.
        """
        pending: list[Any] = []
        errors, validated = self.validate(
            data,
            strict=strict,
            partial=partial,
            context=context,
            _depth=_depth,
            _async_pending=pending,
        )
        if errors or not pending:
            return errors, validated

        for path, nested_cls, inst, data_obj in pending:
            await nested_cls._run_ward_phase_async(inst, data_obj, _sync_already_run=True)
            if inst._errors:
                merge_nested_errors(errors, path, inst._errors)

        return errors, validated

    def to_json_schema(self) -> dict[str, Any]:
        """Produces a JSON Schema 2020-12 dict representation."""
        if self._json_schema_cache is not None:
            return self._json_schema_cache

        properties = {}
        required = []
        defs = {}

        for fname, spec in self.fields.items():
            facet = spec.facet
            sch = facet.to_schema()

            if spec.pipeline is not None:
                for rune in spec.pipeline.runes:
                    if rune.is_facet:
                        sub_sch = rune.fn.to_schema()
                        for k, v in sub_sch.items():
                            if k not in ("type", "title", "description") or k not in sch:
                                sch[k] = v

            nested_cls, nested_many = resolve_nested(facet)
            if nested_cls is not None:
                cls_name = nested_cls.__name__
                if cls_name not in defs:
                    defs[cls_name] = {}  # temporary placeholder
                    defs[cls_name] = nested_cls._sigil.to_json_schema()
                    if "$defs" in defs[cls_name]:
                        sub_defs = defs[cls_name].pop("$defs")
                        defs.update(sub_defs)

                ref_dict = {"$ref": f"#/$defs/{cls_name}"}
                if nested_many:
                    sch = {"type": "array", "items": ref_dict}
                else:
                    sch = ref_dict

            multiple_of = getattr(facet, "multiple_of", None)
            if multiple_of is not None:
                sch["multipleOf"] = multiple_of

            from aquilia.contracts.facets import ChoiceFacet

            if isinstance(facet, ChoiceFacet):
                allowed = getattr(facet, "allowed_values", ())
                if len(allowed) == 1:
                    sch["const"] = allowed[0]
                    sch.pop("enum", None)
                elif len(allowed) > 1:
                    sch["enum"] = list(allowed)

            from aquilia.contracts.facets import PolymorphicFacet

            if isinstance(facet, PolymorphicFacet):
                choices_schemas = []
                for choice in facet.choices:
                    choices_schemas.append(choice.to_schema())
                sch = {"oneOf": choices_schemas}
                disc = getattr(facet, "discriminator_field", None)
                if disc:
                    sch["discriminator"] = {"propertyName": disc}

            properties[fname] = sch
            if spec.required:
                required.append(fname)

        schema: dict[str, Any] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "properties": properties,
        }
        if required:
            schema["required"] = required
        if defs:
            schema["$defs"] = defs

        self._json_schema_cache = schema
        return schema

    def diff(self, other: Sigil) -> SigilDiff:
        """Compare constraints structurally between Contract versions."""
        if self.content_hash == other.content_hash:
            return SigilDiff(added_fields=[], removed_fields=[], changed_fields={}, breaking=False)

        added = []
        removed = []
        changed = {}
        breaking = False

        # Removed fields
        for fname in self.fields:
            if fname not in other.fields:
                removed.append(fname)
                breaking = True

        # Added fields
        for fname in other.fields:
            if fname not in self.fields:
                added.append(fname)
                if other.fields[fname].required:
                    breaking = True

        # Changed fields
        for fname, spec_self in self.fields.items():
            if fname not in other.fields:
                continue
            spec_other = other.fields[fname]

            self_shape = serialize_facet_shape(spec_self.facet)
            other_shape = serialize_facet_shape(spec_other.facet)

            if self_shape != other_shape or spec_self.required != spec_other.required:
                field_breaking = False

                if not spec_self.required and spec_other.required:
                    field_breaking = True

                self_dict = dict(self_shape)
                other_dict = dict(other_shape)

                # Check constraint narrowing
                # min_length
                try:
                    s_val = self_dict.get("min_length")
                    o_val = other_dict.get("min_length")
                    if o_val is not None and (s_val is None or int(o_val) > int(s_val)):
                        field_breaking = True
                except Exception:
                    pass

                # max_length
                try:
                    s_val = self_dict.get("max_length")
                    o_val = other_dict.get("max_length")
                    if o_val is not None and (s_val is None or int(o_val) < int(s_val)):
                        field_breaking = True
                except Exception:
                    pass

                # min_value
                try:
                    s_val = self_dict.get("min_value")
                    o_val = other_dict.get("min_value")
                    if o_val is not None and (s_val is None or float(o_val) > float(s_val)):
                        field_breaking = True
                except Exception:
                    pass

                # max_value
                try:
                    s_val = self_dict.get("max_value")
                    o_val = other_dict.get("max_value")
                    if o_val is not None and (s_val is None or float(o_val) < float(s_val)):
                        field_breaking = True
                except Exception:
                    pass

                if type(spec_self.facet) != type(spec_other.facet):
                    field_breaking = True

                if field_breaking:
                    breaking = True

                changed[fname] = FieldDiff(
                    was=repr(self_dict),
                    now=repr(other_dict),
                    breaking=field_breaking,
                )

        return SigilDiff(
            added_fields=added,
            removed_fields=removed,
            changed_fields=changed,
            breaking=breaking,
        )


# ---------------------------------------------------------------------------
# Diff Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FieldDiff:
    was: str
    now: str
    breaking: bool


@dataclass(frozen=True, slots=True)
class SigilDiff:
    added_fields: list[str]
    removed_fields: list[str]
    changed_fields: dict[str, FieldDiff]
    breaking: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def serialize_facet_shape(facet: Any) -> list[tuple[str, str]]:
    """Determine shape constraints of a facet for hash computation."""
    exclude = {
        "_order",
        "name",
        "contract",
        "_bound",
        "validators",
        "default",
        "default_factory",
        "label",
        "help_text",
        "source",
        "_required",
    }
    shape = {}
    for k, v in facet.__dict__.items():
        if k in exclude or k.startswith("_"):
            continue
        if hasattr(v, "__name__"):
            shape[k] = v.__name__
        else:
            shape[k] = repr(v)
    return sorted(shape.items())


def check_strict_type(facet: Any, value: Any) -> bool:
    """
    Type-check a value without coercion, for ``Spec.strict`` Contracts.

    Args:
        facet: The declaring facet.
        value: The raw inbound value.

    Returns:
        True if ``value`` already has the facet's declared Python type.
        Unknown/custom facet types return True — strictness is only enforced
        for the built-in scalar and container facets.

    Notes:
        Strict mode deliberately skips :meth:`Facet.cast`, so any normalization
        a facet performs while casting (trimming, case folding, alias
        resolution) does **not** run. "Strict" means "no coercion at all",
        not "the same pipeline with tighter checks".
    """
    if isinstance(facet, TextFacet):
        return isinstance(value, str)
    if isinstance(facet, IntFacet):
        return isinstance(value, int) and not isinstance(value, bool)
    if isinstance(facet, FloatFacet):
        return isinstance(value, (float, int)) and not isinstance(value, bool)
    if isinstance(facet, BoolFacet):
        return isinstance(value, bool)
    if isinstance(facet, DecimalFacet):
        return isinstance(value, Decimal)
    if isinstance(facet, DateTimeFacet):
        return isinstance(value, datetime)
    if isinstance(facet, DateFacet):
        return isinstance(value, date) and not isinstance(value, datetime)
    if isinstance(facet, TimeFacet):
        return isinstance(value, time)
    if isinstance(facet, DurationFacet):
        return isinstance(value, timedelta)
    if isinstance(facet, UUIDFacet):
        return isinstance(value, uuid.UUID)
    if isinstance(facet, ListFacet):
        return isinstance(value, (list, tuple))
    if isinstance(facet, DictFacet):
        return isinstance(value, dict)
    return True


def adapt_input(data: Any) -> Any:
    """
    Normalize a supported input object into a mapping the pipeline can read.

    Mapping-like payloads (``dict``, ``Mapping``, ``MultiDict``, ``FormData``)
    are returned unchanged — the common path costs one ``isinstance`` check.
    Everything else is adapted only if it is a recognized structured type:

    ==================== =============================================
    Input                Adapted via
    ==================== =============================================
    dataclass instance   ``__dataclass_fields__`` (shallow, by design)
    attrs instance       ``__attrs_attrs__``
    TypedDict instance   already a ``dict``; no adaptation needed
    ==================== =============================================

    ``TypedDict`` instances are plain dicts at runtime, so they pass through
    the mapping branch and need no special case.

    Adaptation is shallow: nested dataclasses stay as objects and are handled
    by the nested-Contract branch, which reads attributes directly. Using
    ``dataclasses.asdict`` would deep-convert and lose that, and would also
    copy every nested structure on every request.

    Args:
        data: Any inbound payload.

    Returns:
        A mapping-like object, or ``data`` unchanged when it is not a
        recognized structured type (the caller reports that as an error).
    """
    if is_mapping_like(data):
        return data

    fields = getattr(type(data), "__dataclass_fields__", None)
    if fields is not None:
        return {name: getattr(data, name) for name in fields if hasattr(data, name)}

    attrs_fields = getattr(type(data), "__attrs_attrs__", None)
    if attrs_fields is not None:
        return {a.name: getattr(data, a.name) for a in attrs_fields if hasattr(data, a.name)}

    return data


def is_mapping_like(val: Any) -> bool:
    """True if ``val`` can be read as a field mapping (dict/Mapping/MultiDict/FormData)."""
    if _MAPPING_LIKE_TYPES is None:
        _init_validation_types()
    return isinstance(val, _MAPPING_LIKE_TYPES)


def get_keys(data: Any) -> set[str]:
    """Collect the top-level keys of any mapping-like inbound payload."""
    if _MAPPING_LIKE_TYPES is None:
        _init_validation_types()

    if isinstance(data, (dict, Mapping)):
        return set(data.keys())
    if _MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS):
        return set(data.keys())
    if _FORMDATA_CLS is not None and isinstance(data, _FORMDATA_CLS):
        return set(data.fields.keys()) | set(data.files.keys())
    return set()


def get_field_value(data: Any, fname: str, facet: Any) -> Any:
    """
    Read one field's raw value out of an inbound payload.

    Handles the several shapes a request body can take: plain mappings,
    ``MultiDict`` query/form data (where a list field arrives as repeated keys
    or as ``field[]``), and multipart ``FormData`` (where files live in a
    separate namespace from scalar fields).

    Args:
        data: The inbound payload.
        fname: Facet name to look up.
        facet: The facet, consulted to decide list/file handling.

    Returns:
        The raw value, or ``UNSET`` when the key is absent.

    Performance:
        Called once per field per validation. Type references are resolved from
        module scope rather than re-imported per call.
    """
    # Fast path: an exact dict, which is what a parsed JSON body always is.
    # `type() is dict` rather than isinstance -- it cannot match MultiDict (a
    # MutableMapping) or FormData (not a mapping at all), both of which need the
    # alternate-key handling below, and it skips the collections.abc.Mapping ABC
    # dispatch that costs 54.9 ns against dict's 7.9 ns. The "[]" key is only
    # built when the plain name misses, so the common case allocates nothing.
    # Runs before _init_validation_types() because it needs none of those globals.
    if type(data) is dict:
        value = data.get(fname, UNSET)
        if value is not UNSET:
            return value
        return data.get(f"{fname}[]", UNSET)

    if _MAPPING_LIKE_TYPES is None:
        _init_validation_types()

    keys_to_try = [fname, f"{fname}[]"]

    if isinstance(data, (dict, Mapping)) and not (_MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS)):
        for k in keys_to_try:
            if k in data:
                return data[k]
        return UNSET

    is_list_facet = isinstance(facet, ListFacet) or getattr(facet, "many", False)

    if is_list_facet:
        child_facet = getattr(facet, "child", None)
        nested_cls = get_nested_contract_cls(child_facet) if child_facet else None

        if nested_cls is not None:
            all_keys = []
            if _MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS):
                all_keys = list(data.keys())
            elif _FORMDATA_CLS is not None and isinstance(data, _FORMDATA_CLS):
                all_keys = list(data.fields.keys()) | list(data.files.keys())

            indices = set()
            regexes = _FIELD_REGEX_CACHE.get(fname)
            if regexes is None:
                escaped = re.escape(fname)
                regexes = (re.compile(rf"^{escaped}\[(\d+)\]"), re.compile(rf"^{escaped}\.(\d+)"))
                _FIELD_REGEX_CACHE[fname] = regexes
            pattern1, pattern2 = regexes

            for k in all_keys:
                m1 = pattern1.match(k)
                if m1:
                    indices.add(int(m1.group(1)))
                else:
                    m2 = pattern2.match(k)
                    if m2:
                        indices.add(int(m2.group(1)))

            if indices:
                sorted_indices = sorted(list(indices))
                results = []
                for idx in sorted_indices:
                    prefix1 = f"{fname}[{idx}]"
                    prefix2 = f"{fname}.{idx}"
                    nested_val = extract_nested_mapping(data, prefix1)
                    if nested_val is UNSET:
                        nested_val = extract_nested_mapping(data, prefix2)
                    if nested_val is not UNSET:
                        results.append(nested_val)
                return results

            for k in keys_to_try:
                val = _get_single_val(data, k, _FORMDATA_CLS, _MULTIDICT_CLS)
                if isinstance(val, str) and val.strip().startswith("[") and val.strip().endswith("]"):
                    try:
                        import json

                        parsed = json.loads(val)
                        if isinstance(parsed, list):
                            return parsed
                    except Exception:
                        pass
            return UNSET

        is_file_list = isinstance(child_facet, FileFacet) if child_facet else False

        if is_file_list:
            if _FORMDATA_CLS is not None and isinstance(data, _FORMDATA_CLS):
                for k in keys_to_try:
                    if k in data.files:
                        return data.get_all_files(k)

        if _FORMDATA_CLS is not None and isinstance(data, _FORMDATA_CLS):
            for k in keys_to_try:
                if k in data.fields:
                    return data.get_all_fields(k)
        elif _MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS):
            for k in keys_to_try:
                if k in data:
                    return data.get_all(k)

        for k in keys_to_try:
            val = _get_single_val(data, k, _FORMDATA_CLS, _MULTIDICT_CLS)
            if isinstance(val, str) and val.strip().startswith("[") and val.strip().endswith("]"):
                try:
                    import json

                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass

        for k in keys_to_try:
            val = _get_single_val(data, k, _FORMDATA_CLS, _MULTIDICT_CLS)
            if val is not UNSET:
                return [val]

        return UNSET

    if isinstance(facet, FileFacet):
        if _FORMDATA_CLS is not None and isinstance(data, _FORMDATA_CLS):
            for k in keys_to_try:
                if k in data.files:
                    return data.get_file(k)
                if k in data.fields:
                    return data.get_field(k)
        elif _MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS):
            for k in keys_to_try:
                if k in data:
                    return data.get(k)
        return UNSET

    nested_cls = get_nested_contract_cls(facet)
    if nested_cls is not None:
        nested_val = extract_nested_mapping(data, fname)
        if nested_val is not UNSET:
            return nested_val
        return UNSET

    for k in keys_to_try:
        val = _get_single_val(data, k, _FORMDATA_CLS, _MULTIDICT_CLS)
        if val is not UNSET:
            if val == "":
                if not isinstance(facet, TextFacet):
                    if facet.allow_null:
                        return None
                    if not facet.required:
                        return UNSET
                    return None
                else:
                    if facet.allow_null:
                        return None
                    if not facet.required:
                        return UNSET
            return val

    return UNSET


def _get_single_val(data: Any, key: str, form_data_cls: Any, multi_dict_cls: Any) -> Any:

    if form_data_cls is not None and isinstance(data, form_data_cls):
        if key in data.fields:
            return data.fields.get(key)
        if key in data.files:
            return data.get_file(key)
    elif multi_dict_cls is not None and isinstance(data, multi_dict_cls):
        if key in data:
            return data.get(key)
    return UNSET


def extract_nested_mapping(data: Any, prefix: str) -> Any:
    from collections.abc import Mapping

    if _MAPPING_LIKE_TYPES is None:
        _init_validation_types()

    dot_prefix = f"{prefix}."
    bracket_prefix = f"{prefix}["

    if _FORMDATA_CLS is not None and isinstance(data, _FORMDATA_CLS):
        nested_fields = _MULTIDICT_CLS() if _MULTIDICT_CLS is not None else {}
        nested_files = {}

        for k in data.fields:
            if k.startswith(dot_prefix):
                sub_key = k[len(dot_prefix) :]
                for v in data.fields.get_all(k):
                    nested_fields.add(sub_key, v)
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix) : -1]
                for v in data.fields.get_all(k):
                    nested_fields.add(sub_key, v)

        for k, file_list in data.files.items():
            if k.startswith(dot_prefix):
                sub_key = k[len(dot_prefix) :]
                nested_files[sub_key] = file_list
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix) : -1]
                nested_files[sub_key] = file_list

        if len(nested_fields) > 0 or len(nested_files) > 0:
            return _FORMDATA_CLS(fields=nested_fields, files=nested_files)

        val = UNSET
        if prefix in data.fields:
            val = data.fields.get(prefix)
        elif prefix in data.files:
            val = data.get_file(prefix)

        if isinstance(val, str):
            try:
                import json

                parsed = json.loads(val)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except Exception:
                pass
        return val

    elif _MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS):
        nested_fields = _MULTIDICT_CLS()
        for k in data:
            if k.startswith(dot_prefix):
                sub_key = k[len(dot_prefix) :]
                for v in data.get_all(k):
                    nested_fields.add(sub_key, v)
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix) : -1]
                for v in data.get_all(k):
                    nested_fields.add(sub_key, v)
        if len(nested_fields) > 0:
            return nested_fields

        val = data.get(prefix) if prefix in data else UNSET
        if isinstance(val, str):
            try:
                import json

                parsed = json.loads(val)
                if isinstance(parsed, (dict, list)):
                    return parsed
            except Exception:
                pass
        return val

    elif isinstance(data, (dict, Mapping)):
        if prefix in data:
            return data[prefix]

        nested_dict = {}
        for k, v in data.items():
            if k.startswith(dot_prefix):
                sub_key = k[len(dot_prefix) :]
                nested_dict[sub_key] = v
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix) : -1]
                nested_dict[sub_key] = v
        if nested_dict:
            return nested_dict
        return UNSET

    return UNSET


def extract_flat_list_mapping(data: Any) -> list[Any] | None:
    from collections.abc import Mapping

    if _MAPPING_LIKE_TYPES is None:
        _init_validation_types()

    if not is_mapping_like(data):
        return None

    all_keys = []
    if (
        isinstance(data, (dict, Mapping))
        and not (_MULTIDICT_CLS is not None and isinstance(data, _MULTIDICT_CLS))
        or _MULTIDICT_CLS is not None
        and isinstance(data, _MULTIDICT_CLS)
    ):
        all_keys = list(data.keys())
    elif _FORMDATA_CLS is not None and isinstance(data, _FORMDATA_CLS):
        all_keys = list(data.fields.keys()) | list(data.files.keys())

    indices = set()
    for k in all_keys:
        m1 = _EXTRACT_FLAT_P1.match(k)
        if m1:
            indices.add(int(m1.group(1)))
        else:
            m2 = _EXTRACT_FLAT_P2.match(k)
            if m2:
                indices.add(int(m2.group(1)))

    if not indices:
        return None

    sorted_indices = sorted(list(indices))
    results = []
    for idx in sorted_indices:
        prefix1 = f"[{idx}]"
        prefix2 = f"{idx}"

        nested_val = extract_nested_mapping(data, prefix1)
        if nested_val is UNSET:
            nested_val = extract_nested_mapping(data, prefix2)
        if nested_val is not UNSET:
            results.append(nested_val)
    return results


_NESTED_FACET_TYPES: tuple[type, ...] | None = None


def _nested_facet_types() -> tuple[type, ...]:
    """
    Lazily resolve ``(NestedContractFacet, LazyContractFacet)`` once per process.

    ``annotations`` imports ``core``, which imports this module, so these types
    cannot be imported at module scope. Resolving them once and caching keeps
    the per-field cost of :func:`get_nested_contract_cls` to a global lookup
    rather than a ``sys.modules`` round-trip on every field of every request.
    """
    global _NESTED_FACET_TYPES
    if _NESTED_FACET_TYPES is None:
        from aquilia.contracts.annotations import LazyContractFacet, NestedContractFacet

        _NESTED_FACET_TYPES = (NestedContractFacet, LazyContractFacet)
    return _NESTED_FACET_TYPES


def is_nested_facet(facet: Any) -> bool:
    """
    Whether a facet wraps a nested Contract, without resolving it.

    Used at class-body evaluation time, where a forward reference cannot be
    resolved yet — the Contract it names is very often the one currently being
    built, so it is not in the registry until this call returns.

    Args:
        facet: Any facet.

    Returns:
        True for a nested-Contract facet, or a container whose child is one.
    """
    nested_cls, lazy_cls = _nested_facet_types()
    if isinstance(facet, (nested_cls, lazy_cls)):
        return True
    return isinstance(getattr(facet, "child", None), (nested_cls, lazy_cls))


def get_nested_contract_cls(facet: Any) -> type | None:
    """
    Resolve the Contract class a nested facet wraps, if any.

    Args:
        facet: Any facet.

    Returns:
        The target Contract class, or ``None`` if this facet does not wrap one
        (or wraps a forward reference that is still unresolvable).

    See Also:
        :func:`resolve_nested` — also reports whether the relation is to-many,
        and looks through container facets.
    """
    return resolve_nested(facet)[0]


def resolve_nested(facet: Any) -> tuple[type | None, bool]:
    """
    Resolve a facet's nested Contract and whether it holds many of them.

    A to-many nested relation has two spellings that build different facets::

        items = NestedContractFacet(ItemContract, many=True)   # many on the facet
        items: list[ItemContract] = None                       # ListFacet(child=...)

    Both mean the same thing, so both must reach the same validation path.
    Treating only the first as nested left the second running structural
    validation alone — the child's wards and ``validate()`` hook never ran, and
    the async-ward detection reported ``False`` for a Contract that had them.

    Args:
        facet: Any facet.

    Returns:
        ``(contract_cls, is_many)``. ``contract_cls`` is ``None`` when the facet
        wraps no Contract, or wraps a forward reference that cannot yet resolve.

    Examples:
        >>> resolve_nested(NestedContractFacet(ItemContract, many=True))
        (ItemContract, True)
        >>> resolve_nested(ListFacet(child=NestedContractFacet(ItemContract)))
        (ItemContract, True)
    """
    direct = _direct_nested_cls(facet)
    if direct is not None:
        return direct, bool(getattr(facet, "many", False))

    child = getattr(facet, "child", None)
    if child is not None:
        nested = _direct_nested_cls(child)
        if nested is not None:
            return nested, True

    return None, False


def _direct_nested_cls(facet: Any) -> type | None:
    """
    Contract class a facet wraps directly, without looking at containers.

    A forward reference that cannot resolve yields ``None`` rather than
    propagating: callers ask this to decide how to *route* a field, and a
    Contract still being constructed must not fail its own class body.
    """
    nested_cls, lazy_cls = _nested_facet_types()

    if isinstance(facet, nested_cls):
        return facet.target
    if isinstance(facet, lazy_cls):
        try:
            resolved = facet._get_resolved()
        except RegistryFault:
            return None
        if resolved is not None:
            return resolved.target
    return None


def merge_nested_errors(
    errors: dict[str, Any],
    path: tuple[str, ...],
    nested_errors: dict[str, Any],
) -> None:
    """
    Splice a nested Contract's errors into the outer error mapping at ``path``.

    Args:
        errors: The outer error mapping, mutated in place.
        path: Field path of the nested Contract, e.g. ``("author",)`` or
            ``("items", "2")`` for the third element of a to-many field.
        nested_errors: The nested Contract's own error mapping.

    Side Effects:
        Mutates ``errors``.
    """
    if not path:
        _merge_error_maps(errors, nested_errors)
        return

    cursor = errors
    for segment in path[:-1]:
        nxt = cursor.get(segment)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[segment] = nxt
        cursor = nxt

    leaf = path[-1]
    existing = cursor.get(leaf)
    if isinstance(existing, dict):
        _merge_error_maps(existing, nested_errors)
    else:
        cursor[leaf] = nested_errors


def _merge_error_maps(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Merge ``source`` error entries into ``target``, concatenating lists."""
    for key, value in source.items():
        existing = target.get(key)
        if isinstance(existing, list) and isinstance(value, list):
            existing.extend(value)
        elif existing is None:
            target[key] = value


def run_nested_contract(
    nested_cls: type,
    data: Any,
    *,
    strict: bool | None = None,
    partial: bool = False,
    context: dict[str, Any] | None = None,
    _depth: int = 0,
    _async_pending: list[Any] | None = None,
    _path: tuple[str, ...] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Validate a nested Contract through its *full* pipeline.

    Structural validation alone is not sufficient: a nested Contract may
    declare ``@ward`` methods and an object-level ``validate()`` override, and
    those express business rules (authorization checks, cross-field
    invariants) exactly as they do at the top level. Recursing into
    ``nested_cls._sigil.validate()`` runs only the structural pass and
    silently skips both, so a nested Contract's rules would never be enforced.

    Args:
        nested_cls: The nested Contract class.
        data: Mapping-like payload for the nested Contract.
        strict: Forwarded strict-mode override.
        partial: Forwarded PATCH semantics flag.
        context: Forwarded contextual data.
        _depth: Nesting depth, already incremented by the caller.
        _async_pending: Accumulator for nested Contracts with async wards. See
            :meth:`Sigil.validate`.
        _path: Dotted path of this Contract within the outer payload.

    Returns:
        ``(errors, validated)`` — the same shape :meth:`Sigil.validate`
        returns, so the caller's error handling is unchanged.

    Raises:
        ContractAsyncMismatchFault: If the nested Contract declares an async
            ward and ``_async_pending`` is ``None`` (synchronous entry point).

    See Also:
        :meth:`Sigil.validate`, :meth:`Sigil.validate_async`
    """

    from aquilia.contracts.exceptions import ContractAsyncMismatchFault

    errors, validated = nested_cls._sigil.validate(
        data,
        strict=strict,
        partial=partial,
        context=context,
        _depth=_depth,
        _async_pending=_async_pending,
        _path=_path,
    )
    if errors:
        return errors, validated

    has_async = any(wm.mode == "async" for wm in nested_cls._ward_methods)
    if has_async and _async_pending is None:
        raise ContractAsyncMismatchFault(
            f"Nested Contract '{nested_cls.__name__}' contains async wards and must be "
            f"validated using is_sealed_async()."
        )

    inst = nested_cls(data=data, context=context)
    inst._errors = {}
    data_obj = DataObject(validated)

    nested_cls._run_ward_phase(inst, data_obj)
    if not inst._errors:
        data_obj = nested_cls._run_validate_hook(inst, data_obj)

    if has_async:
        # Sync phases passed; the async wards are drained by the async driver,
        # which reports any errors against this Contract's path.
        _async_pending.append((_path, nested_cls, inst, data_obj))  # type: ignore[union-attr]

    if inst._errors:
        return inst._errors, {}
    return {}, dict(data_obj)


def build_sigil(cls: type) -> Sigil:
    """Construct Sigil configuration from Contract class definitions."""
    from aquilia.contracts.lenses import Lens

    fields = {}
    for fname, facet in cls._all_facets.items():
        # is_nested_facet() rather than an isinstance check: a ``list[Item]``
        # annotation builds ``ListFacet(child=NestedContractFacet)``, which is
        # every bit as nested as ``NestedContractFacet(Item, many=True)``. It
        # deliberately does not resolve — a forward reference here usually
        # names the Contract whose class body is still executing.
        is_nested = is_nested_facet(facet)
        is_lens_field = isinstance(facet, Lens)

        # Retrieve pipeline associated if annotation parsed it
        pipeline = getattr(facet, "_pipeline", None)

        fields[fname] = FieldSpec(
            name=fname,
            facet=facet,
            required=facet.required,
            default=facet.default,
            default_factory=getattr(facet, "default_factory", None),
            pipeline=pipeline,
            is_nested_contract=is_nested,
            is_lens=is_lens_field,
        )

    # Extract Spec details
    spec = getattr(cls, "_spec", None)
    strict = getattr(spec, "strict", False) if spec else False
    revision = getattr(spec, "revision", None) if spec else None
    migrate_from = getattr(spec, "migrate_from", {}) if spec else {}
    migrate_step = getattr(cls, "migrate_step", None)
    discriminator = getattr(spec, "discriminator", None) if spec else None

    ward_methods = tuple(getattr(cls, "_ward_methods", ()))

    return Sigil(
        fields=fields,
        ward_methods=ward_methods,
        strict=strict,
        revision=revision,
        migrate_from=migrate_from,
        migrate_step=migrate_step,
        discriminator=discriminator,
    )
