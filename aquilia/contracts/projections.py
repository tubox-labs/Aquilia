"""
Aquilia Contract Projections -- named, reusable field subsets.

A Projection is a named subset of facets -- like a SQL view over a model.
Instead of repeating ``fields = [...]`` everywhere, define projections
once and select them at route level.

Naming:
    - "Projection" because it projects a subset of the model's facets
      onto the output, like a database projection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .exceptions import ProjectionFault

if TYPE_CHECKING:
    pass


__all__ = ["ProjectionRegistry"]


class ProjectionRegistry:
    """
    Manages named field projections for a Contract class.

    Purpose:
        Provides named, reusable field subsets for contracts (analogous to database views or GraphQL field selections).
        Enables endpoints to request specific views (e.g. ``"summary"``, ``"detail"``, ``"minimal"``) without creating separate classes.

    Lifecycle:
        1. **Class Creation**: Instantiated and populated by ``ContractMeta.__new__`` from ``Spec.projections``.
        2. **Runtime Resolution**: Queried during ``contract.data`` or ``Contract["projection"]`` to resolve active field names.

    Execution Order:
        1. Parse projection definitions during ``configure()``.
        2. Resolve special keywords (``"__all__"``, ``"__minimal__"``, exclusion prefixes ``"-field"``).
        3. Store immutable ``frozenset[str]`` mapping for each projection name.
        4. During ``resolve(name)``, return corresponding frozenset or raise ``ProjectionFault``.

    Parameters:
        None directly on ``__init__``. Configuration occurs via ``configure()``.

    Returns:
        ProjectionRegistry: An initialized registry instance.

    Exceptions:
        ProjectionFault: Raised during ``resolve()`` if an unrecognized projection name is requested.

    Notes:
        - Thread-Safe: Stored projection sets are immutable ``frozenset`` instances.
        - Supports exclusion lists: ``["-password", "-secret"]`` expands to all non-write-only facets minus excluded ones.

    Internal Behaviour:
        Filters out write-only fields from default ``"__all__"`` projections to prevent accidental credential leaking in output.

    Edge Cases:
        - An empty field list in a projection is valid and produces an empty dictionary output rather than defaulting to all fields.

    Examples:
        >>> class Spec:
        ...     projections = {
        ...         "summary": ["id", "name"],
        ...         "public": ["-password", "-security_answer"],
        ...         "full": "__all__",
        ...     }
        ...     default_projection = "summary"
    """

    def __init__(self):
        self._projections: dict[str, frozenset[str]] = {}
        self._exclusion_projections: dict[str, frozenset[str]] = {}
        self._default: str | None = None
        self._all_facets: frozenset[str] = frozenset()

    def configure(
        self,
        projections: dict[str, str | list[str]] | None,
        default: str | None,
        all_facet_names: set[str],
        write_only_names: set[str],
        minimal_names: set[str] | None = None,
    ) -> None:
        """
        Configure named projections from Spec class declarations.

        Purpose:
            Compiles raw projection dict definitions into pre-computed, immutable frozensets of facet names.

        Lifecycle:
            Executed once per Contract class during metaclass construction in ``ContractMeta.__new__``.

        Execution Order:
            1. Compute ``_all_facets`` by subtracting write-only field names from all facet names.
            2. Compute minimal projection set (primary keys and read-only facets).
            3. Iterate through raw projections dictionary and construct matching frozensets.
            4. Establish default projection name.

        Parameters:
            projections (dict[str, str | list[str]] | None):
                Mapping of projection name to field list, exclusion list, or keyword string.
            default (str | None):
                Name of default projection.
            all_facet_names (set[str]):
                Complete set of facet names declared on the Contract.
            write_only_names (set[str]):
                Set of write-only facet names to exclude from output projections.
            minimal_names (set[str] | None, optional):
                Explicit facet names defining the ``"__minimal__"`` projection.

        Returns:
            None

        Exceptions:
            None.
        """
        self._all_facets = frozenset(all_facet_names - write_only_names)

        if minimal_names is None:
            minimal_names = {n for n in ("id", "pk") if n in all_facet_names}
        minimal = frozenset(minimal_names) & self._all_facets

        if projections is None:
            # No projections defined -- create a default "__all__" projection
            self._projections["__all__"] = self._all_facets
            self._default = "__all__"
            return

        for name, fields in projections.items():
            if fields == "__all__":
                self._projections[name] = self._all_facets
            elif fields == "__minimal__":
                self._projections[name] = minimal
            elif isinstance(fields, (list, tuple)):
                # Check for exclusion syntax
                includes = []
                excludes = []
                for f in fields:
                    if isinstance(f, str) and f.startswith("-"):
                        excludes.append(f[1:])
                    else:
                        includes.append(f)

                if excludes and not includes:
                    # Exclusion-only: all facets minus excluded
                    self._projections[name] = frozenset(self._all_facets - frozenset(excludes))
                elif includes:
                    self._projections[name] = frozenset(includes)
                else:
                    self._projections[name] = self._all_facets
            else:
                # Single field name or other
                self._projections[name] = frozenset([str(fields)])

        self._default = default or next(iter(self._projections), None)

    def resolve(self, name: str | None = None) -> frozenset[str]:
        """
        Resolve a projection name to a set of valid facet names.

        Purpose:
            Looks up and returns the exact subset of facet names associated with a named projection.

        Lifecycle:
            Invoked during contract molding, output serialization, and schema generation.

        Execution Order:
            1. If ``name`` is ``None``, fall back to default projection name.
            2. If default name is also ``None``, return all available non-write-only facets.
            3. Look up projection name in internal registry dict.
            4. If not found, raise ``ProjectionFault``.

        Parameters:
            name (str | None, optional):
                Requested projection name (e.g. ``"summary"``). Defaults to ``None``.

        Returns:
            frozenset[str]: Immutable set of allowed facet names.

        Exceptions:
            ProjectionFault: If ``name`` is not registered in this registry.

        Examples:
            >>> registry.resolve("summary")
            frozenset({'id', 'name'})
        """
        if name is None:
            name = self._default
        if name is None:
            return self._all_facets

        if name not in self._projections:
            raise ProjectionFault(name, list(self._projections.keys()))

        return self._projections[name]

    @property
    def default_name(self) -> str | None:
        """Name of default projection."""
        return self._default

    @property
    def available(self) -> list[str]:
        """List of all registered projection names."""
        return list(self._projections.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._projections

    def __repr__(self) -> str:
        return f"<ProjectionRegistry projections={list(self._projections.keys())} default={self._default!r}>"
