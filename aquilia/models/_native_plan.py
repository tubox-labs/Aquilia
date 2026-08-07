"""Compile a model + row shape into a native RowPlan, when it is safe to.

Owns **eligibility** for hydration (``docs/models-engine/04`` §2.3). The rules
are stricter than validation's, because the failure mode is worse: a hydration
defect corrupts ``_original_values``, and ``save()`` then silently skips columns
that did change. That is data loss, and no existing test would catch it, because
today's tests hydrate and save through the same code path.

So the conservative rule is absolute: any doubt at all, and the whole batch runs
in Python.
"""

from __future__ import annotations

from typing import Any

from aquilia._dataengine_loader import DATAENGINE_NATIVE, native_module

__all__ = ["row_plan_for", "plan_cache_size"]

# (model_class, row_key_tuple) -> RowPlan or None.
#
# The key includes the actual row keys, not just the class: row shape varies with
# only()/defer()/values(), and a plan compiled for one projection is wrong for
# another. Bounded by the number of distinct projections an app uses, which is
# static per codebase (03 §11).
_PLAN_CACHE: dict[tuple, Any] = {}


def plan_cache_size() -> int:
    """Distinct (model, row shape) pairs analysed. Used by the cache-bound test."""
    return len(_PLAN_CACHE)


def _field_type_code(field: Any, tc: Any) -> int | None:
    """Map a Field class to its TypeCode, or None when it is not representable.

    Exact-type checks rather than isinstance: a subclass may override
    ``to_python``, and the base conversion would then be wrong.
    """
    from aquilia.models import fields_module as fm

    exact = type(field)

    # Str-like: to_python is a passthrough for all of these.
    if exact in (
        fm.CharField,
        fm.TextField,
        fm.EmailField,
        fm.SlugField,
        fm.URLField,
        fm.VarcharField,
        fm.CICharField,
        fm.CIEmailField,
        fm.CITextField,
    ):
        return tc.STR
    if exact in (
        fm.IntegerField,
        fm.BigIntegerField,
        fm.SmallIntegerField,
        fm.PositiveIntegerField,
        fm.PositiveSmallIntegerField,
        fm.PositiveBigIntegerField,
    ):
        return tc.INT
    if exact in (fm.AutoField, fm.BigAutoField, fm.SmallAutoField):
        return tc.INT
    if exact is fm.FloatField:
        return tc.FLOAT
    if exact is fm.BooleanField:
        return tc.BOOL
    if exact is fm.DateField:
        return tc.DATE
    if exact is fm.DateTimeField:
        return tc.DATETIME
    if exact is fm.TimeField:
        return tc.TIME
    if exact is fm.DecimalField:
        return tc.DECIMAL
    if exact is fm.UUIDField:
        return tc.UUID
    if exact is fm.JSONField:
        return tc.JSON
    if exact is fm.BinaryField:
        return tc.BYTES
    return None


def _model_is_eligible(model_cls: type) -> bool:
    """Model-level conditions, checked once per plan."""
    from aquilia.models.base import Model

    # A guard variant is produced BY hydration; hydrating into one would
    # double-wrap.
    if getattr(model_cls, "__deferred_guard__", False):
        return False

    # A custom __new__ may do work that cls.__new__(cls) would skip.
    if model_cls.__new__ is not Model.__new__:
        return False

    return True


def _field_is_eligible(field: Any) -> bool:
    """Field-level conditions. Each is a place user code could run.

    Note what is NOT checked here: ``to_python``. Eight of the built-in field
    types override it -- Boolean, Date, DateTime, Time, Decimal, UUID, JSON,
    Binary -- so 04 §2.3.3's "no field overrides to_python" rule, applied
    literally, would reject every field the TypeCode table exists to serve and
    leave the engine idle.

    The protection that rule is reaching for comes from ``_field_type_code``
    instead: it matches ``type(field) is X`` exactly, so a *user* subclass of
    CharField is unrecognised and its plan is rejected. Each built-in's
    ``to_python`` is then reproduced exactly in ``convert_hydrate`` -- including
    the blank-string-to-None rule and JSONField's return-invalid-input-as-is
    behaviour, both of which differ from the contracts-side conversions.
    """
    from aquilia.models.fields_module import Field

    # __set__/__get__ are the descriptor protocol the plan bypasses by writing
    # instance.__dict__ directly. An override there is a real behaviour change,
    # and no built-in field has one.
    if getattr(type(field), "__set__", None) is not Field.__set__:
        return False
    if getattr(type(field), "__get__", None) is not Field.__get__:
        return False
    return True


def _build_plan(model_cls: type, row_keys: tuple[str, ...]) -> Any:
    de = native_module()
    if de is None:
        return None

    if not _model_is_eligible(model_cls):
        return None

    col_to_attr = getattr(model_cls, "_col_to_attr", None)
    non_m2m = getattr(model_cls, "_non_m2m_fields", None)
    if not col_to_attr or non_m2m is None:
        return None

    fk_attrs = getattr(model_cls, "_fk_attrs", frozenset())
    tc = de.TypeCode
    plan = de.RowPlan()

    seen: set[str] = set()
    for key in row_keys:
        mapping = col_to_attr.get(key)
        if mapping is None:
            # Unmapped keys -- annotations, aggregates, select_related aliases --
            # are skipped silently by from_row. Rather than reproduce that
            # skipping, treat their presence as ineligible: select_related needs
            # column splitting that lives in Python (query.py), and getting that
            # subtly wrong is not worth the speed.
            return None
        attr_name, field = mapping
        if not _field_is_eligible(field):
            return None
        code = _field_type_code(field, tc)
        if code is None:
            return None

        flags = de.ColumnFlags.FK_WRAP if attr_name in fk_attrs else 0
        plan.add(key, attr_name, code, flags)
        seen.add(attr_name)

    # Deferred fields require the guard-class swap, which changes the instance's
    # __class__. Excluded from v1: only()/defer() is the exception rather than
    # the rule, and an absent column must never become None -- it would be
    # indistinguishable from a real SQL NULL (04 §3.3).
    if len(seen) != len(non_m2m):
        return None

    if len(plan) == 0:
        return None

    from aquilia.models.relations import RelatedNotLoaded

    plan.set_model(model_cls, RelatedNotLoaded, model_cls.__name__)
    return plan


def row_plan_for(model_cls: type, row_keys: tuple[str, ...]) -> Any:
    """Return the cached RowPlan for a (model, row shape), or None."""
    if not DATAENGINE_NATIVE:
        return None

    cache_key = (model_cls, row_keys)
    try:
        return _PLAN_CACHE[cache_key]
    except KeyError:
        pass
    except TypeError:
        # Unhashable row keys: not a shape this cache can serve.
        return None

    try:
        plan = _build_plan(model_cls, row_keys)
    except Exception:
        # Compilation is an optimisation, never a correctness requirement.
        plan = None

    _PLAN_CACHE[cache_key] = plan
    return plan
