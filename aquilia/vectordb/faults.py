"""
AquilaVectorDB — Fault Classes.

Typed, structured fault classes for the vector database subsystem.
Every framework-domain failure in ``aquilia.vectordb`` raises a ``VectorFault``
subclass — never a raw ``ValueError`` / ``RuntimeError`` / ``TypeError``.

Domains:
    VECTORDB — Vector store schema, lookup, engine, and GPU faults.

Notes:
    Fault ``code`` values are stable and are the supported assertion target in
    tests; message text is not.  See ``docs/vectordb/faults.md``.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

# ============================================================================
# Domain
# ============================================================================

VECTORDB_DOMAIN = FaultDomain.custom("vectordb", "Vector database faults")


# ============================================================================
# Base
# ============================================================================


class VectorFault(Fault):
    """Base fault for the vector database subsystem."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=VECTORDB_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


# ============================================================================
# Dependency
# ============================================================================


class VectorNotInstalledFault(VectorFault):
    """
    The ``elips`` package is not installed.

    ``elips`` is an optional extra, so importing :mod:`aquilia.vectordb` on an
    install without it must produce an actionable fault rather than a bare
    ``ModuleNotFoundError`` several frames deep.

    Args:
        reason: Underlying import error text.
    """

    def __init__(self, reason: str = "", **kwargs):
        detail = f" ({reason})" if reason else ""
        super().__init__(
            code="VECTOR_NOT_INSTALLED",
            message=(
                f"aquilia.vectordb requires the 'elips' package{detail}. "
                f"Install it with: pip install 'aquilia[vectordb]'"
            ),
            severity=Severity.FATAL,
            retryable=False,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


# ============================================================================
# Schema / declaration
# ============================================================================


class VectorSchemaFault(VectorFault):
    """
    A ``VectorModel`` declaration is invalid.

    Raised at class-creation time by ``VectorModelMeta`` — an unroutable
    annotation, a duplicate slot marker, a nested ``dict`` payload, or a
    ``Meta.dimension`` that disagrees with a ``Dimension()`` marker or a
    ``VectorField(dimension=...)`` declaration.

    Notes:
        Failing at class creation rather than at first write is deliberate:
        a mis-declared model is a static defect, and discovering it during an
        ingest would leave a half-populated collection behind.

    Args:
        model: Model class name.
        reason: What is structurally wrong with the declaration.
    """

    def __init__(self, model: str, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_SCHEMA_INVALID",
            message=f"Invalid vector model {model!r}: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"model": model, "reason": reason, **kwargs.get("metadata", {})},
        )


class VectorEncodingFault(VectorFault):
    """
    A payload value could not be encoded into the elips metadata space.

    ``MetaValue`` is ``bool | int | float | str`` and flat — no nesting, no
    lists.  Values outside that set are encoded by a codec (§2.5 of the
    implementation plan); this fault is raised when no codec applies or when
    the configured codec rejects the value.

    Args:
        model: Model class name.
        attr: Attribute that failed to encode.
        reason: Why encoding failed.
    """

    def __init__(self, model: str, attr: str, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_ENCODING_FAILED",
            message=f"Cannot encode {model}.{attr}: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={
                "model": model,
                "attr": attr,
                "reason": reason,
                **kwargs.get("metadata", {}),
            },
        )


class VectorValidationFault(VectorFault):
    """
    One or more field values failed validation.

    Wraps the ``ValidationError`` raised by the shared validators in
    ``aquilia/models/fields/validators.py`` so both model worlds report
    constraint violations through their own fault domain.

    Two call shapes, because both are genuinely useful:

    * single-field — ``VectorValidationFault(model, attr="x", reason="too long")``,
      raised by an individual validator;
    * multi-field — ``VectorValidationFault(model, errors={"x": "...", "y": "..."})``,
      raised by ``VectorModel.validate()``, which collects every failure before
      raising so one round trip reports the whole picture.

    Args:
        model: Model class name.
        attr: Attribute that failed, for the single-field form.
        reason: Validator message, for the single-field form.
        errors: ``{attribute: message}``, for the multi-field form.
        validator_code: The validator's stable ``code`` (e.g. ``"min_length"``).
    """

    def __init__(
        self,
        model: str,
        *,
        attr: str = "",
        reason: str = "",
        errors: dict[str, str] | None = None,
        validator_code: str = "",
        **kwargs,
    ):
        collected = dict(errors or {})
        if attr and reason:
            collected.setdefault(attr, reason)

        if len(collected) == 1:
            only_attr, only_reason = next(iter(collected.items()))
            message = f"{model}.{only_attr}: {only_reason}"
        else:
            detail = "; ".join(f"{k}: {v}" for k, v in sorted(collected.items()))
            message = f"{model} has {len(collected)} invalid field(s) — {detail}"

        super().__init__(
            code="VECTOR_VALIDATION_FAILED",
            message=message,
            severity=Severity.ERROR,
            retryable=False,
            public=True,
            metadata={
                "model": model,
                "errors": collected,
                "validator_code": validator_code,
                **kwargs.get("metadata", {}),
            },
        )

    @property
    def errors(self) -> dict[str, str]:
        """The ``{attribute: message}`` map of every failure."""
        return dict(self.metadata.get("errors", {}))


# ============================================================================
# Query
# ============================================================================


class VectorEQLFault(VectorFault):
    """
    An EQL filter string could not be parsed.

    EQL reaches the framework from operators and config files — a CLI
    ``--where``, a saved view — so the fault carries the character offset,
    letting a caller point at the offending column instead of rejecting the
    whole expression as "invalid".

    Notes:
        ``public=True``: an admin search box can surface the parse error to the
        person who typed it. The expression is user input, not internal state.

    Args:
        expression: The EQL source that failed.
        reason: What the parser expected.
        position: Zero-based character offset of the failure.
    """

    def __init__(self, expression: str, reason: str, position: int = 0, **kwargs):
        caret = " " * position + "^" if 0 <= position <= len(expression) else ""
        detail = f"\n  {expression}\n  {caret}" if caret else ""
        super().__init__(
            code="VECTOR_EQL_INVALID",
            message=f"Invalid EQL filter at position {position}: {reason}{detail}",
            severity=Severity.ERROR,
            retryable=False,
            public=True,
            metadata={
                "expression": expression,
                "reason": reason,
                "position": position,
                **kwargs.get("metadata", {}),
            },
        )


class VectorChunkingFault(VectorFault):
    """
    A document could not be split into chunks.

    Raised at chunker construction for a configuration that cannot terminate
    (``chunk_overlap >= chunk_size`` would advance zero characters per step),
    and at split time when a document cannot be divided as configured.

    Args:
        reason: What is wrong with the configuration or the document.
        model: Model class name, when scoped to one.
    """

    def __init__(self, reason: str, model: str = "", **kwargs):
        scope = f" for {model}" if model else ""
        super().__init__(
            code="VECTOR_CHUNKING_INVALID",
            message=f"Invalid chunking configuration{scope}: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, "model": model, **kwargs.get("metadata", {})},
        )


class VectorQueryFault(VectorFault):
    """
    A ``VectorQuery`` was used incorrectly.

    Raised by the truthiness / ``len()`` guards, by ``.top()`` on a
    metadata-only query (which is insertion-ordered, not distance-ordered),
    and by terminals invoked in a mode that cannot serve them.

    Args:
        reason: What the caller did, and what to call instead.
    """

    def __init__(self, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_QUERY_INVALID",
            message=reason,
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class VectorLookupFault(VectorFault):
    """
    A filter lookup cannot be compiled to an ``elips.Filter``.

    Three cases, all of which would otherwise return silently wrong records:

    * ``__isnull`` — elips has no null concept; an absent metadata key simply
      does not match, so the lookup has no faithful translation.
    * range lookups over ``Decimal`` — stored as strings, where a
      lexicographic compare is wrong (``"9" > "10"``).
    * an unknown lookup suffix.

    Args:
        lookup: The offending lookup expression, e.g. ``"score__isnull"``.
        reason: Why it cannot be compiled.
    """

    def __init__(self, lookup: str, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_LOOKUP_UNSUPPORTED",
            message=f"Unsupported lookup {lookup!r}: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"lookup": lookup, "reason": reason, **kwargs.get("metadata", {})},
        )


class VectorNotFoundFault(VectorFault):
    """
    A record lookup found nothing where exactly one record was required.

    Raised by ``VectorModel.get()`` and ``VectorQuery.one()``.

    Args:
        model: Model class name.
        key: The record key that was not found, when the lookup was by key.
    """

    def __init__(self, model: str, key: str | None = None, **kwargs):
        where = f" with key {key!r}" if key else " matching the query"
        super().__init__(
            code="VECTOR_NOT_FOUND",
            message=f"No {model} record found{where}",
            severity=Severity.ERROR,
            retryable=False,
            public=True,
            metadata={"model": model, "key": key, **kwargs.get("metadata", {})},
        )


class VectorMultipleFoundFault(VectorFault):
    """
    ``VectorQuery.one()`` matched more than one record.

    Args:
        model: Model class name.
        count: How many records matched.
    """

    def __init__(self, model: str, count: int, **kwargs):
        super().__init__(
            code="VECTOR_MULTIPLE_FOUND",
            message=f"Expected exactly one {model} record, found {count}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"model": model, "count": count, **kwargs.get("metadata", {})},
        )


# ============================================================================
# Store / engine
# ============================================================================


class VectorStoreFault(VectorFault):
    """
    A vector store operation failed at the elips layer.

    Wraps ``elips.StorageError`` and its siblings — a sealed vault, a closed
    handle, a failed write.  Retryable, because the caller may reasonably
    re-attempt after reopening.

    Args:
        store: Store alias or directory the failure applies to.
        operation: Operation that failed, e.g. ``"write"``.
        reason: Underlying error text.
    """

    def __init__(self, store: str, operation: str, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_STORE_ERROR",
            message=f"Vector store {store!r} failed during {operation!r}: {reason}",
            severity=Severity.ERROR,
            retryable=True,
            metadata={
                "store": store,
                "operation": operation,
                "reason": reason,
                **kwargs.get("metadata", {}),
            },
        )


class VectorLockFault(VectorFault):
    """
    Another process already holds the writer lock on this directory.

    elips takes ``flock(LOCK_EX|LOCK_NB)`` on ``<dir>/LOCK`` at open, so one
    ``Engine`` per directory per process is a hard constraint.  With
    ``workers > 1`` every worker after the first hits this.

    Notes:
        This is why ``VectorDBSubsystem`` is ``_required = True`` whenever a
        store is configured: a vector store that silently failed to open would
        serve empty search results, which is worse than not booting.

    Args:
        path: Database directory whose lock is held.
        reason: Underlying ``LockConflict`` text.
    """

    def __init__(self, path: str, reason: str = "", **kwargs):
        detail = f": {reason}" if reason else ""
        super().__init__(
            code="VECTOR_LOCK_CONFLICT",
            message=(
                f"Vector store directory {path!r} is already locked by another process{detail}. "
                f"elips is single-writer per directory — run a single worker, or give each "
                f"worker its own store path."
            ),
            severity=Severity.FATAL,
            retryable=False,
            metadata={"path": path, "reason": reason, **kwargs.get("metadata", {})},
        )


class VectorDimensionFault(VectorFault):
    """
    A vector's length does not match the store's configured dimension.

    Dimension is database-global in elips (``Config.dimension``), so this is
    also raised when two models that would share an engine declare different
    dimensions.

    Args:
        expected: Configured dimension.
        actual: Dimension actually supplied.
        context: Where the mismatch was detected.
    """

    def __init__(self, expected: int, actual: int, context: str = "", **kwargs):
        where = f" ({context})" if context else ""
        super().__init__(
            code="VECTOR_DIMENSION_MISMATCH",
            message=f"Vector dimension mismatch{where}: store expects {expected}, got {actual}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={
                "expected": expected,
                "actual": actual,
                "context": context,
                **kwargs.get("metadata", {}),
            },
        )


class VectorConfigFault(VectorFault):
    """
    Vector store configuration is invalid or inconsistent with disk state.

    Wraps ``elips.ConfigError`` — a metric or index change against a persisted
    directory, an unusable codec, a store alias no model references.

    Args:
        reason: What is wrong with the configuration.
        store: Store alias, when the fault is scoped to one.
    """

    def __init__(self, reason: str, store: str = "", **kwargs):
        scope = f" for store {store!r}" if store else ""
        super().__init__(
            code="VECTOR_CONFIG_INVALID",
            message=f"Invalid vector store configuration{scope}: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, "store": store, **kwargs.get("metadata", {})},
        )


class VectorTransactionFault(VectorFault):
    """
    A transactional write is not expressible.

    ``TransactionVault`` exposes only ``place`` / ``erase`` — there is no
    ``place_document``.  A text-only record therefore cannot be written inside
    a transaction, and the fault is raised at enqueue time so the error sits
    next to its cause rather than surfacing at commit.

    Args:
        reason: Why the record cannot be enqueued.
    """

    def __init__(self, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_TRANSACTION_INVALID",
            message=f"Invalid vector transaction: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class VectorEmbedderFault(VectorFault):
    """
    Text-first work was requested without a usable embedder.

    Also raised when a configured embedder returns the wrong number of vectors
    for a batch, which would otherwise misalign vectors against records.

    Args:
        reason: What is missing or wrong.
        model: Model class name, when scoped to one.
    """

    def __init__(self, reason: str, model: str = "", **kwargs):
        scope = f" for {model}" if model else ""
        super().__init__(
            code="VECTOR_EMBEDDER_UNAVAILABLE",
            message=f"Embedder unavailable{scope}: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, "model": model, **kwargs.get("metadata", {})},
        )


class VectorEmbedderMismatchFault(VectorFault):
    """
    The configured embedder does not match the one the database was built with.

    The embedder fingerprint is part of a persisted elips database's identity.
    Boot pre-checks it with ``elips.describe_local_embedder()`` so this surfaces
    as a named mismatch instead of an opaque ``ConfigError`` at open.

    Args:
        expected: Fingerprint the on-disk database expects.
        actual: Fingerprint the current configuration resolves to.
        path: Database directory.
    """

    def __init__(self, expected: str, actual: str, path: str = "", **kwargs):
        where = f" at {path!r}" if path else ""
        super().__init__(
            code="VECTOR_EMBEDDER_MISMATCH",
            message=(
                f"Embedder fingerprint mismatch{where}: database was built with {expected!r}, "
                f"configuration resolves to {actual!r}. Rebuild the store with "
                f"'aq vectordb rebuild' to re-embed under the new model."
            ),
            severity=Severity.FATAL,
            retryable=False,
            metadata={
                "expected": expected,
                "actual": actual,
                "path": path,
                **kwargs.get("metadata", {}),
            },
        )


class VectorRegistryFault(VectorFault):
    """
    A registry lookup or binding failed.

    Raised when a model references an unconfigured store, when a query runs
    before the subsystem has bound an engine, or when two models collide on
    ``(store, collection)``.

    Args:
        reason: What went wrong.
        model: Model class name, when scoped to one.
    """

    def __init__(self, reason: str, model: str = "", **kwargs):
        scope = f" for {model}" if model else ""
        super().__init__(
            code="VECTOR_REGISTRY_ERROR",
            message=f"Vector registry error{scope}: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, "model": model, **kwargs.get("metadata", {})},
        )


# ============================================================================
# GPU
# ============================================================================


class VectorGpuUnavailableFault(VectorFault):
    """
    GPU acceleration was required but is not available.

    ``built`` and ``available`` are distinct states and the message says which
    one failed: a GPU-enabled wheel on a machine with no device is a normal,
    supported condition, and collapsing the two makes it undiagnosable.

    Args:
        reason: Which precondition failed.
        policy: The configured GPU policy that demanded a device.
    """

    def __init__(self, reason: str, policy: str = "require_gpu", **kwargs):
        super().__init__(
            code="VECTOR_GPU_UNAVAILABLE",
            message=f"GPU policy {policy!r} cannot be satisfied: {reason}",
            severity=Severity.FATAL,
            retryable=False,
            metadata={"reason": reason, "policy": policy, **kwargs.get("metadata", {})},
        )


class VectorGpuFault(VectorFault):
    """
    A query ran on CPU while ``fallback="require"`` demanded the GPU.

    elips falls back at query time even under ``GpuPolicy.require_gpu``
    (ADR-GPU-008), so "same API, possibly slower" is the default.  This fault
    exists for deployments where that is unacceptable; the check is opt-in
    because it costs an ``explain_seek`` per query.

    Args:
        reason: What the planner reported.
        collection: Collection the query targeted.
    """

    def __init__(self, reason: str, collection: str = "", **kwargs):
        scope = f" on {collection!r}" if collection else ""
        super().__init__(
            code="VECTOR_GPU_FALLBACK",
            message=f"Query{scope} fell back to CPU under fallback='require': {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, "collection": collection, **kwargs.get("metadata", {})},
        )


__all__ = [
    "VECTORDB_DOMAIN",
    "VectorConfigFault",
    "VectorDimensionFault",
    "VectorEQLFault",
    "VectorEmbedderFault",
    "VectorEmbedderMismatchFault",
    "VectorEncodingFault",
    "VectorFault",
    "VectorGpuFault",
    "VectorGpuUnavailableFault",
    "VectorLockFault",
    "VectorLookupFault",
    "VectorMultipleFoundFault",
    "VectorNotFoundFault",
    "VectorNotInstalledFault",
    "VectorQueryFault",
    "VectorRegistryFault",
    "VectorSchemaFault",
    "VectorStoreFault",
    "VectorTransactionFault",
    "VectorValidationFault",
]
