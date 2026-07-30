"""
Aquilia Contract Lenses -- depth-controlled relational views.

A Lens lets a Contract expose related model data through another
Contract, with cycle detection, depth limits, and projection selection.

Naming:
    - "Lens" because it provides a focused *view* into related data,
      like an optical lens adjusting what you see.
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from .exceptions import LensCycleFault, LensUnresolvedFault
from .facets import Facet

if TYPE_CHECKING:
    from .core import Contract


__all__ = ["Lens"]


class Lens(Facet):
    """
    A relational facet that projects related model data through a target Contract.

    Purpose:
        Provides depth-controlled, cycle-safe relational views over foreign keys, one-to-one, and to-many relations.
        Enables structured representation of related entities with optional projection selection (e.g., ``UserContract["public"]``).

    Lifecycle:
        1. **Class Creation**: Bound to a parent ``Contract`` as a class attribute.
        2. **Contract Instantiation**: Configured with target Contract class, cardinality (``many``), and max recursion depth.
        3. **Outbound Serialization**: Invoked during ``contract.data`` or ``contract.to_dict()`` to extract and transform related instances.

    Execution Order:
        1. Inspect input relation value (single instance or iterable).
        2. Verify recursion depth against ``max_depth`` (returns primary key fallback if exceeded).
        3. Check for target Contract class IDs in ``_seen`` recursion tracker (raises ``LensCycleFault`` if circular).
        4. Check for un-awaited ORM managers (raises ``LensUnresolvedFault`` in sync path if un-prefetched).
        5. Instantiate target Contract for child instance(s) and invoke ``to_dict()``.
        6. Return molded dictionary or list of dictionaries.

    Parameters:
        target (type[Contract] | _ProjectedRef | None):
            Target ``Contract`` class or projected reference (e.g. ``UserContract["summary"]``).
        many (bool, optional):
            If ``True``, treats the relation as a to-many collection. Defaults to ``False``.
        depth (int, optional):
            Maximum permissible relational traversal depth. Defaults to ``3``.
        projection (str, optional):
            Name of specific target contract projection to apply. Defaults to ``None``.
        **kwargs:
            Base Facet keyword arguments (``source``, ``read_only``, etc.). Lenses default to ``read_only=True``.

    Returns:
        Lens: An initialized relational facet descriptor.

    Exceptions:
        LensCycleFault: Raised if a circular dependency is detected in the Lens traversal graph.
        LensUnresolvedFault: Raised in synchronous ``mold()`` if an un-awaited ORM relation manager is encountered.
        LensDepthFault: Raised if recursion limit is exceeded when depth checks are configured strictly.

    Notes:
        - Read-Only by Default: Lenses represent outbound relational projections and are marked read-only by default.
        - Supports both synchronous ``mold()`` and asynchronous ``mold_async()`` for ORM manager resolution.

    Internal Behaviour:
        Maintains an internal ``_seen`` set of active Contract class Object IDs across recursive steps to detect reference cycles.

    Edge Cases:
        - If ``value`` is ``None``, returns ``None`` without instantiating child contracts.
        - When max depth is reached, returns raw primary key attributes (``id`` or ``pk``) instead of expanding full nested objects.

    Examples:
        >>> class OrderContract(Contract):
        ...     customer = Lens(UserContract["public"], depth=2)
        ...     items = Lens(OrderItemContract, many=True, depth=2)
    """

    _type_name = "object"

    def __init__(
        self,
        target: type[Contract] | _ProjectedRef | None = None,
        *,
        many: bool = False,
        depth: int = 3,
        projection: str | None = None,
        **kwargs,
    ):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

        # Handle ProjectedRef (from Contract["projection_name"])
        if isinstance(target, _ProjectedRef):
            self._target_cls = target.contract_cls
            self._projection = target.projection
        else:
            self._target_cls = target
            self._projection = projection

        self.many = many
        self.max_depth = depth

    @property
    def target(self) -> type[Contract] | None:
        return self._target_cls

    def python_type(self) -> str:
        """A Lens molds to a plain dict (or a list of them for ``many=True``)."""
        return "list[dict[str, Any]]" if self.many else "dict[str, Any]"

    def bind(self, name: str, contract: Contract) -> None:
        super().bind(name, contract)
        # If source not explicitly set, try to match model FK attribute
        if self.source == name and hasattr(contract, "_spec"):
            spec = contract._spec
            if spec and spec.model:
                model_fields = getattr(spec.model, "_fields", {})
                if name in model_fields:
                    # Check if it's a relation field
                    mf = model_fields[name]
                    if hasattr(mf, "to"):
                        # It's a FK/M2M -- source is the attribute name
                        pass

    def mold(self, value: Any, *, _depth: int = 0, _seen: set | None = None) -> Any:
        """
        Mold related data through the target Contract.

        Args:
            value: Related model instance(s), or an already-materialized list.
            _depth: Current nesting depth (internal).
            _seen: Set of Contract class ids already in the chain (internal,
                cycle detection).

        Returns:
            A dict for a to-one relation, a list of dicts for ``many=True``, or
            a bare primary key once ``depth`` is exhausted.

        Raises:
            LensCycleFault: If the same target Contract reappears in the chain.
            LensUnresolvedFault: If ``many=True`` receives an un-awaited
                related manager/queryset. This path is synchronous and cannot
                await the ORM, so the relation must be prefetched (or already
                materialized to a list) before serialization.

        Examples:
        ```
            Prefetch to-many relations before rendering::

                order = await Order.objects.prefetch_related("items").get(pk=1)
                OrderContract(instance=order).data

            Or materialize explicitly::

                order.items = await order.items.all()
                OrderContract(instance=order).data
        ```
        Notes:
            An unresolved relation raises rather than yielding ``[]``: an empty
            list is indistinguishable from "this record genuinely has no
            related rows", which silently ships wrong data to clients. Failing
            loudly at development time is the safer default.
        """
        if value is None:
            return None

        if _seen is None:
            _seen = set()

        # Cycle detection
        target_id = id(self._target_cls)
        if target_id in _seen:
            raise LensCycleFault(
                [cls.__name__ for cls in _seen] + [self._target_cls.__name__]
                if hasattr(self._target_cls, "__name__")
                else ["<unknown>"]
            )

        # Depth check
        if _depth >= self.max_depth:
            # At max depth, return PK only
            if self.many:
                if self._is_unresolved_manager(value):
                    raise LensUnresolvedFault(self.name or "<unbound>")
                return [self._pk_fallback(item) for item in value]
            return self._pk_fallback(value)

        new_seen = _seen | {target_id}

        if self.many:
            if self._is_unresolved_manager(value):
                raise LensUnresolvedFault(self.name or "<unbound>")
            return [self._mold_single(item, _depth=_depth + 1, _seen=new_seen) for item in value]
        return self._mold_single(value, _depth=_depth + 1, _seen=new_seen)

    @staticmethod
    def _is_unresolved_manager(value: Any) -> bool:
        """
        Detect an un-awaited related manager / queryset.

        Aquilia's ``RelatedManager.all()`` is a coroutine, so such an object
        cannot be iterated from this synchronous path. Anything exposing an
        ``all`` attribute or async iteration but no synchronous ``__iter__``
        is treated as unresolved.
        """
        if isinstance(value, (list, tuple, set, frozenset)):
            return False
        if hasattr(value, "all"):
            return True
        return hasattr(value, "__aiter__") and not hasattr(value, "__iter__")

    def _mold_single(self, instance: Any, *, _depth: int, _seen: set) -> dict[str, Any]:
        """Mold a single related instance through the target Contract."""
        if self._target_cls is None:
            # No target contract -- fall back to dict/PK
            return self._pk_fallback(instance)

        bp = self._target_cls(instance=instance, projection=self._projection)
        return bp.to_dict(_depth=_depth, _seen=_seen)

    async def mold_async(self, value: Any, *, _depth: int = 0, _seen: set | None = None) -> Any:
        """
        Async counterpart of :meth:`mold` — resolves un-awaited ORM relations.

        Aquilia's ``RelatedManager.all()`` is a coroutine, so a to-many relation
        that was not prefetched cannot be read from the synchronous path. This
        method awaits it instead of raising, making
        :meth:`~aquilia.contracts.core.Contract.to_dict_async` usable directly
        on a lazily-loaded instance.

        Args:
            value: Related model instance(s), an already-materialized list, or
                an un-awaited related manager.
            _depth: Current nesting depth (internal).
            _seen: Contract class ids already in the chain (internal).

        Returns:
            A dict for a to-one relation, a list of dicts for ``many=True``, or
            a bare primary key once ``depth`` is exhausted.

        Raises:
            LensCycleFault: If the same target Contract reappears in the chain.

        Examples:
        ```
            Serialize without prefetching::

                order = await Order.objects.get(pk=1)
                await OrderContract(instance=order).to_dict_async()
        ```
        Performance:
            Each unresolved to-many relation costs one query at the point it is
            reached — the N+1 pattern. Prefetching still gives the better plan;
            this path exists so that lazy relations are *correct* rather than
            an error, not so that prefetching becomes unnecessary.
        """
        if value is None:
            return None

        if _seen is None:
            _seen = set()

        target_id = id(self._target_cls)
        if target_id in _seen:
            raise LensCycleFault(
                [cls.__name__ for cls in _seen] + [self._target_cls.__name__]
                if hasattr(self._target_cls, "__name__")
                else ["<unknown>"]
            )

        if self.many:
            value = await self._resolve_manager(value)

        if _depth >= self.max_depth:
            # At max depth, return PK only
            if self.many:
                return [self._pk_fallback(item) for item in value]
            return self._pk_fallback(value)

        new_seen = _seen | {target_id}

        if self.many:
            return [await self._mold_single_async(item, _depth=_depth + 1, _seen=new_seen) for item in value]
        return await self._mold_single_async(value, _depth=_depth + 1, _seen=new_seen)

    @classmethod
    async def _resolve_manager(cls, value: Any) -> Any:
        """
        Materialize an un-awaited related manager into a list.

        Args:
            value: A related manager, an async iterable, or an
                already-materialized sequence.

        Returns:
            A sequence safe to iterate synchronously.
        """
        if not cls._is_unresolved_manager(value):
            return value

        if hasattr(value, "all"):
            resolved = value.all()
            if inspect.isawaitable(resolved):
                resolved = await resolved
            if not cls._is_unresolved_manager(resolved):
                return resolved
            value = resolved

        if hasattr(value, "__aiter__"):
            return [item async for item in value]
        return value

    async def _mold_single_async(self, instance: Any, *, _depth: int, _seen: set) -> dict[str, Any]:
        """Mold a single related instance through the target Contract, async."""
        if self._target_cls is None:
            return self._pk_fallback(instance)

        bp = self._target_cls(instance=instance, projection=self._projection)
        return await bp.to_dict_async(_depth=_depth, _seen=_seen)

    @staticmethod
    def _pk_fallback(instance: Any) -> Any:
        """Fall back to PK when depth is exceeded or no target Contract."""
        if instance is None:
            return None
        if isinstance(instance, dict):
            return instance.get("id", instance.get("pk"))
        pk = getattr(instance, "pk", None)
        if pk is not None:
            return pk
        return getattr(instance, "id", None)

    def extract(self, instance: Any) -> Any:
        """Extract related data from the instance."""
        if self.source == "*":
            return instance

        # Handle dotted sources
        parts = self.source.split(".") if self.source else []
        obj = instance
        for part in parts:
            if obj is None:
                return None
            obj = obj.get(part) if isinstance(obj, dict) else getattr(obj, part, None)
        return obj

    def to_schema(self) -> dict[str, Any]:
        """Generate JSON Schema with $ref for the target Contract."""
        if self._target_cls is None:
            return {"type": "object"}

        ref_name = self._target_cls.__name__
        if self._projection:
            ref_name = f"{ref_name}_{self._projection}"

        if self.many:
            return {
                "type": "array",
                "items": {"$ref": f"#/components/schemas/{ref_name}"},
            }
        return {"$ref": f"#/components/schemas/{ref_name}"}


class _ProjectedRef:
    """
    Internal: holds a Contract class + projection name.

    Created by ``Contract["projection_name"]`` subscript syntax.
    """

    __slots__ = ("contract_cls", "projection")

    def __init__(self, contract_cls: type[Contract], projection: str):
        self.contract_cls = contract_cls
        self.projection = projection

    def __repr__(self) -> str:
        return f"{self.contract_cls.__name__}[{self.projection!r}]"
