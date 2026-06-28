"""
Aquilia Blueprint Sigil -- compiled schema IR.

A Sigil is built once per Blueprint class and stored as ``cls._sigil``.
It is the compiled, immutable representation of the schema.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import uuid
from typing import Any, Callable

from .exceptions import CastFault, SealFault
from .pipeline import Pipeline

__all__ = ["Sigil", "FieldSpec", "SigilDiff", "FieldDiff", "build_sigil"]


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
        "is_nested_blueprint",
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
        is_nested_blueprint: bool = False,
        is_lens: bool = False,
    ):
        self.name = name
        self.facet = facet
        self.required = required
        self.default = default
        self.default_factory = default_factory
        self.pipeline = pipeline
        self.is_nested_blueprint = is_nested_blueprint
        self.is_lens = is_lens

    def __repr__(self) -> str:
        return f"<FieldSpec '{self.name}' type={type(self.facet).__name__}>"


class Sigil:
    """Immutable compiled representation of a Blueprint validation schema."""

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
    ) -> tuple[dict[str, list[str]], dict[str, Any]]:
        """Validate input data against this schema. Never raises."""
        errors: dict[str, list[str]] = {}
        validated: dict[str, Any] = {}
        context = context or {}
        is_strict = self.strict if strict is None else strict

        # Run migrations sequentially if revision context matches
        if self.revision is not None and self.migrate_from and is_mapping_like(data):
            data_rev = None
            if isinstance(data, dict):
                data_rev = data.get("__revision__")
            elif hasattr(data, "get"):
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
                            raise ValueError(f"Missing migration path from revision {current_rev} to {next_rev}")

        from .facets import UNSET, Computed, Constant, Inject

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
                    errors.setdefault(fname, []).append("This field is required")
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
                errors.setdefault(fname, []).append("This field may not be null")
                continue

            # Recursive nested blueprints check
            nested_cls = get_nested_blueprint_cls(facet)
            if nested_cls is not None:
                is_many = getattr(facet, "many", False)
                if is_many:
                    if not isinstance(raw, (list, tuple)):
                        errors.setdefault(fname, []).append("Expected a list of items")
                        continue
                    list_errors = {}
                    list_validated = []
                    for idx, item in enumerate(raw):
                        if not is_mapping_like(item):
                            list_errors[str(idx)] = {"__all__": ["Expected a dictionary"]}
                            continue
                        sub_errors, sub_validated = nested_cls._sigil.validate(
                            item, strict=strict, partial=partial, context=context
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
                    if not is_mapping_like(raw):
                        errors.setdefault(fname, []).append("Expected a dictionary")
                        continue
                    sub_errors, sub_validated = nested_cls._sigil.validate(
                        raw, strict=strict, partial=partial, context=context
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
                        f"Invalid type: expected {type(facet).__name__.replace('Facet', '').lower()}"
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

            nested_cls = get_nested_blueprint_cls(facet)
            if nested_cls is not None:
                cls_name = nested_cls.__name__
                if cls_name not in defs:
                    defs[cls_name] = {}  # temporary placeholder
                    defs[cls_name] = nested_cls._sigil.to_json_schema()
                    if "$defs" in defs[cls_name]:
                        sub_defs = defs[cls_name].pop("$defs")
                        defs.update(sub_defs)

                ref_dict = {"$ref": f"#/$defs/{cls_name}"}
                if getattr(facet, "many", False):
                    sch = {"type": "array", "items": ref_dict}
                else:
                    sch = ref_dict

            multiple_of = getattr(facet, "multiple_of", None)
            if multiple_of is not None:
                sch["multipleOf"] = multiple_of

            from .facets import ChoiceFacet
            if isinstance(facet, ChoiceFacet):
                allowed = getattr(facet, "allowed_values", ())
                if len(allowed) == 1:
                    sch["const"] = allowed[0]
                    sch.pop("enum", None)
                elif len(allowed) > 1:
                    sch["enum"] = list(allowed)

            from .facets import PolymorphicFacet
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
        """Compare constraints structurally between Blueprint versions."""
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
        "blueprint",
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
    """Type-check values strictly without casting/coercion."""
    from .facets import (
        BoolFacet,
        ChoiceFacet,
        DateFacet,
        DateTimeFacet,
        DecimalFacet,
        DictFacet,
        DurationFacet,
        FloatFacet,
        IntFacet,
        ListFacet,
        TextFacet,
        TimeFacet,
        UUIDFacet,
    )

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


def is_mapping_like(val: Any) -> bool:
    from collections.abc import Mapping
    try:
        from .._datastructures import MultiDict
    except ImportError:
        MultiDict = None
    try:
        from .._uploads import FormData
    except ImportError:
        FormData = None

    types = [dict, Mapping]
    if MultiDict is not None:
        types.append(MultiDict)
    if FormData is not None:
        types.append(FormData)
    return isinstance(val, tuple(types))


def get_keys(data: Any) -> set[str]:
    from collections.abc import Mapping
    try:
        from .._datastructures import MultiDict
    except ImportError:
        MultiDict = None
    try:
        from .._uploads import FormData
    except ImportError:
        FormData = None

    if isinstance(data, (dict, Mapping)):
        return set(data.keys())
    if MultiDict is not None and isinstance(data, MultiDict):
        return set(data.keys())
    if FormData is not None and isinstance(data, FormData):
        return set(data.fields.keys()) | set(data.files.keys())
    return set()


def get_field_value(data: Any, fname: str, facet: Any) -> Any:
    from collections.abc import Mapping
    from .facets import UNSET, ListFacet, FileFacet, TextFacet
    try:
        from .._datastructures import MultiDict
    except ImportError:
        MultiDict = None
    try:
        from .._uploads import FormData
    except ImportError:
        FormData = None

    keys_to_try = [fname, f"{fname}[]"]

    if isinstance(data, (dict, Mapping)) and not (MultiDict is not None and isinstance(data, MultiDict)):
        for k in keys_to_try:
            if k in data:
                return data[k]
        return UNSET

    is_list_facet = isinstance(facet, ListFacet) or getattr(facet, "many", False)

    if is_list_facet:
        child_facet = getattr(facet, "child", None)
        nested_cls = get_nested_blueprint_cls(child_facet) if child_facet else None

        if nested_cls is not None:
            all_keys = []
            if MultiDict is not None and isinstance(data, MultiDict):
                all_keys = list(data.keys())
            elif FormData is not None and isinstance(data, FormData):
                all_keys = list(data.fields.keys()) | list(data.files.keys())
            
            indices = set()
            import re
            pattern1 = re.compile(rf"^{re.escape(fname)}\[(\d+)\]")
            pattern2 = re.compile(rf"^{re.escape(fname)}\.(\d+)")
            
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
                val = _get_single_val(data, k, FormData, MultiDict)
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
            if FormData is not None and isinstance(data, FormData):
                for k in keys_to_try:
                    if k in data.files:
                        return data.get_all_files(k)
        
        if FormData is not None and isinstance(data, FormData):
            for k in keys_to_try:
                if k in data.fields:
                    return data.get_all_fields(k)
        elif MultiDict is not None and isinstance(data, MultiDict):
            for k in keys_to_try:
                if k in data:
                    return data.get_all(k)
        
        for k in keys_to_try:
            val = _get_single_val(data, k, FormData, MultiDict)
            if isinstance(val, str) and val.strip().startswith("[") and val.strip().endswith("]"):
                try:
                    import json
                    parsed = json.loads(val)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
        
        for k in keys_to_try:
            val = _get_single_val(data, k, FormData, MultiDict)
            if val is not UNSET:
                return [val]

        return UNSET

    if isinstance(facet, FileFacet):
        if FormData is not None and isinstance(data, FormData):
            for k in keys_to_try:
                if k in data.files:
                    return data.get_file(k)
                if k in data.fields:
                    return data.get_field(k)
        elif MultiDict is not None and isinstance(data, MultiDict):
            for k in keys_to_try:
                if k in data:
                    return data.get(k)
        return UNSET

    nested_cls = get_nested_blueprint_cls(facet)
    if nested_cls is not None:
        nested_val = extract_nested_mapping(data, fname)
        if nested_val is not UNSET:
            return nested_val
        return UNSET

    for k in keys_to_try:
        val = _get_single_val(data, k, FormData, MultiDict)
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


def _get_single_val(data: Any, key: str, FormData: Any, MultiDict: Any) -> Any:
    from .facets import UNSET
    if FormData is not None and isinstance(data, FormData):
        if key in data.fields:
            return data.fields.get(key)
        if key in data.files:
            return data.get_file(key)
    elif MultiDict is not None and isinstance(data, MultiDict):
        if key in data:
            return data.get(key)
    return UNSET


def extract_nested_mapping(data: Any, prefix: str) -> Any:
    from collections.abc import Mapping
    from .facets import UNSET
    try:
        from .._datastructures import MultiDict
    except ImportError:
        MultiDict = None
    try:
        from .._uploads import FormData
    except ImportError:
        FormData = None

    dot_prefix = f"{prefix}."
    bracket_prefix = f"{prefix}["

    if FormData is not None and isinstance(data, FormData):
        nested_fields = MultiDict() if MultiDict is not None else {}
        nested_files = {}

        for k in data.fields:
            if k.startswith(dot_prefix):
                sub_key = k[len(dot_prefix):]
                for v in data.fields.get_all(k):
                    nested_fields.add(sub_key, v)
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix):-1]
                for v in data.fields.get_all(k):
                    nested_fields.add(sub_key, v)

        for k, file_list in data.files.items():
            if k.startswith(dot_prefix):
                sub_key = k[len(dot_prefix):]
                nested_files[sub_key] = file_list
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix):-1]
                nested_files[sub_key] = file_list

        if len(nested_fields) > 0 or len(nested_files) > 0:
            return FormData(fields=nested_fields, files=nested_files)
        
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

    elif MultiDict is not None and isinstance(data, MultiDict):
        nested_fields = MultiDict()
        for k in data:
            if k.startswith(dot_prefix):
                sub_key = k[len(dot_prefix):]
                for v in data.get_all(k):
                    nested_fields.add(sub_key, v)
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix):-1]
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
                sub_key = k[len(dot_prefix):]
                nested_dict[sub_key] = v
            elif k.startswith(bracket_prefix) and k.endswith("]"):
                sub_key = k[len(bracket_prefix):-1]
                nested_dict[sub_key] = v
        if nested_dict:
            return nested_dict
        return UNSET

    return UNSET


def extract_flat_list_mapping(data: Any) -> list[Any] | None:
    from collections.abc import Mapping
    from .facets import UNSET
    try:
        from .._datastructures import MultiDict
    except ImportError:
        MultiDict = None
    try:
        from .._uploads import FormData
    except ImportError:
        FormData = None

    if not is_mapping_like(data):
        return None

    all_keys = []
    if isinstance(data, (dict, Mapping)) and not (MultiDict is not None and isinstance(data, MultiDict)):
        all_keys = list(data.keys())
    elif MultiDict is not None and isinstance(data, MultiDict):
        all_keys = list(data.keys())
    elif FormData is not None and isinstance(data, FormData):
        all_keys = list(data.fields.keys()) | list(data.files.keys())

    import re
    pattern1 = re.compile(r"^\[(\d+)\]")
    pattern2 = re.compile(r"^(\d+)\b")

    indices = set()
    for k in all_keys:
        m1 = pattern1.match(k)
        if m1:
            indices.add(int(m1.group(1)))
        else:
            m2 = pattern2.match(k)
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


def get_nested_blueprint_cls(facet: Any) -> type | None:
    """Retrieve nested blueprint class if facet wraps one."""
    from .annotations import LazyBlueprintFacet, NestedBlueprintFacet

    if isinstance(facet, NestedBlueprintFacet):
        return facet.target
    if isinstance(facet, LazyBlueprintFacet):
        resolved = facet._get_resolved()
        if resolved is not None:
            return resolved.target
    return None


def build_sigil(cls: type) -> Sigil:
    """Construct Sigil configuration from Blueprint class definitions."""
    from .annotations import LazyBlueprintFacet, NestedBlueprintFacet
    from .lenses import Lens

    fields = {}
    for fname, facet in cls._all_facets.items():
        is_nested = isinstance(facet, (NestedBlueprintFacet, LazyBlueprintFacet))
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
            is_nested_blueprint=is_nested,
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
