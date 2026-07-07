"""
Aquilia Model Options -- parsed from inner Meta class.

Contains the Options class which stores model metadata like
table_name, ordering, indexes, constraints, abstract, etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


__all__ = ["Options"]


class Options:
    """
    Parsed model options from inner Meta class.

    Attributes:
        table_name: Database table name
        ordering: Default query ordering
        indexes: Composite indexes
        constraints: Unique constraints
        abstract: Whether model is abstract (no table)
        verbose_name: Human-readable model name
        verbose_name_plural: Human-readable plural
        app_label: Owning module name
        unique_together: Legacy: list of field tuples
        select_on_save: Re-SELECT after save to get DB-computed fields
        managed: Whether migrations manage this table (default True)
        default_permissions: Default permissions to create
        permissions: Extra permissions
        db_tablespace: Tablespace for the table (PostgreSQL)
        get_latest_by: Field(s) for latest() shortcut
        order_with_respect_to: FK field for ordering
        default_related_name: Default related_name template
        required_db_features: Backend features required
        required_db_vendor: Backend vendor required (e.g., "postgresql")
    """

    __slots__ = (
        "table_name",
        "ordering",
        "indexes",
        "constraints",
        "abstract",
        "verbose_name",
        "verbose_name_plural",
        "app_label",
        "unique_together",
        "select_on_save",
        "managed",
        "default_permissions",
        "permissions",
        "db_tablespace",
        "get_latest_by",
        "order_with_respect_to",
        "default_related_name",
        "required_db_features",
        "required_db_vendor",
        "proxy",
        "_model_cls",
    )

    def __init__(
        self,
        model_name: str,
        meta: type | None = None,
        table_attr: str | None = None,
    ):
        """
        Parse a model's inner ``Meta`` class (if any) into concrete,
        always-present attributes with sensible defaults.

        Called once per model class by ``ModelMeta.__new__()`` -- never
        instantiated directly by user code.

        Args:
            model_name: The model class's ``__name__`` (e.g. ``"User"``).
                Used to derive defaults for ``table_name`` (lowercased),
                ``verbose_name``, and ``verbose_name_plural`` when ``Meta``
                doesn't specify them.
            meta: The raw inner ``class Meta: ...`` object popped from the
                model's class body by the metaclass, or ``None`` if the
                model declared no ``Meta``. Every attribute below is read
                via ``getattr(meta, "...", default)``, so an incomplete
                ``Meta`` (only setting e.g. ``ordering``) still gets
                defaults for everything else.
            table_attr: The value of a class-level ``table``, ``table_name``,
                or ``__tablename__`` attribute on the model, if the model
                declared one. Takes precedence over ``Meta.table`` /
                ``Meta.table_name`` / ``Meta.__tablename__`` when both are
                present, and over the ``model_name.lower()`` fallback.

        Resulting table name precedence (highest to lowest):
        ``table_attr`` -> ``meta.table`` -> ``meta.table_name`` ->
        ``meta.__tablename__`` -> ``model_name.lower()``.

        Every other option (``ordering``, ``indexes``, ``constraints``,
        ``abstract``, ``verbose_name(_plural)``, ``app_label``,
        ``unique_together``, ``select_on_save``, ``managed``,
        ``default_permissions``, ``permissions``, ``db_tablespace``,
        ``get_latest_by``, ``order_with_respect_to``,
        ``default_related_name``, ``required_db_features``,
        ``required_db_vendor``, ``proxy``) is read straight off ``meta``
        with the type-appropriate empty/False/None default documented in
        the class docstring above. ``_model_cls`` starts unset (``None``)
        and is populated later, once the owning model class exists.
        """
        self.table_name = (
            table_attr
            or (
                getattr(meta, "table", None)
                or getattr(meta, "table_name", None)
                or getattr(meta, "__tablename__", None)
                if meta
                else None
            )
            or model_name.lower()
        )
        self.ordering: list[str] = getattr(meta, "ordering", []) if meta else []
        self.indexes: list = getattr(meta, "indexes", []) if meta else []
        self.constraints: list = getattr(meta, "constraints", []) if meta else []
        self.abstract: bool = getattr(meta, "abstract", False) if meta else False
        self.verbose_name: str = getattr(meta, "verbose_name", model_name) if meta else model_name
        self.verbose_name_plural: str = (
            getattr(meta, "verbose_name_plural", f"{self.verbose_name}s") if meta else f"{model_name}s"
        )
        self.app_label: str = getattr(meta, "app_label", "") if meta else ""
        self.unique_together: list[tuple[str, ...]] = getattr(meta, "unique_together", []) if meta else []
        # Enhanced options
        self.select_on_save: bool = getattr(meta, "select_on_save", False) if meta else False
        self.managed: bool = getattr(meta, "managed", True) if meta else True
        self.default_permissions: tuple[str, ...] = (
            getattr(meta, "default_permissions", ("add", "change", "delete", "view"))
            if meta
            else ("add", "change", "delete", "view")
        )
        self.permissions: list[tuple[str, str]] = getattr(meta, "permissions", []) if meta else []
        self.db_tablespace: str = getattr(meta, "db_tablespace", "") if meta else ""
        self.get_latest_by: str | None = getattr(meta, "get_latest_by", None) if meta else None
        self.order_with_respect_to: str | None = getattr(meta, "order_with_respect_to", None) if meta else None
        self.default_related_name: str | None = getattr(meta, "default_related_name", None) if meta else None
        self.required_db_features: list[str] = getattr(meta, "required_db_features", []) if meta else []
        self.required_db_vendor: str | None = getattr(meta, "required_db_vendor", None) if meta else None
        self.proxy: bool = getattr(meta, "proxy", False) if meta else False
        self._model_cls = None

    @property
    def label(self) -> str:
        """Return app_label.ModelName style label."""
        if self.app_label:
            return f"{self.app_label}.{self.verbose_name}"
        return self.verbose_name

    @property
    def label_lower(self) -> str:
        """Return app_label.model_name style label (lowercase)."""
        return self.label.lower()

    def __repr__(self) -> str:
        """Debug representation showing table name and any non-default flags/options set."""
        parts = [f"table={self.table_name!r}"]
        if self.abstract:
            parts.append("abstract=True")
        if self.ordering:
            parts.append(f"ordering={self.ordering!r}")
        if self.app_label:
            parts.append(f"app_label={self.app_label!r}")
        if not self.managed:
            parts.append("managed=False")
        return f"<Options: {', '.join(parts)}>"
