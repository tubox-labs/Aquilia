"""
Artifact fault types — structured fault domain for the artifacts subsystem.

These faults are raised (or logged, depending on ``on_corrupt`` policy)
whenever the artifact store encounters an unrecoverable state:

- ``ArtifactCorruptFault`` — file exists but content is unreadable/tampered
- ``ArtifactStaleFault`` — file exists but its schema_version is incompatible
- ``ArtifactLockTimeoutFault`` — couldn't acquire the advisory file lock
- ``ArtifactTransactionFault`` — multi-artifact transaction commit failed

Policy variants
---------------
Each artifact type can choose its own ``on_corrupt`` policy:

``"raise"``
    Raise ``ArtifactCorruptFault``.  Correct for deploy-critical artifacts
    (frozen registry manifest) where silent regeneration would be dangerous.

``"warn_and_reset"``
    Emit a :func:`warnings.warn` and return ``None`` (cache miss), triggering
    a clean rebuild on the caller's side.  Correct for disposable caches
    (discovery cache, template bytecode) where rebuilding is cheap.

``"reset"``
    Silently return ``None``.  Use only for ephemeral derived artifacts
    (in-process caches, test doubles) where even a warning is noise.
"""

from __future__ import annotations

from aquilia.faults.core import Fault, FaultDomain, Severity

# Custom fault domain for the artifacts subsystem
ARTIFACTS_DOMAIN = FaultDomain.custom("ARTIFACTS", description="Artifact store and integrity faults")


class ArtifactFault(Fault):
    """Base class for all artifact subsystem faults."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        metadata: dict | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            domain=ARTIFACTS_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=False,
            metadata=metadata or {},
        )


class ArtifactCorruptFault(ArtifactFault):
    """
    An artifact file exists on disk but its content cannot be trusted.

    Causes:
    - JSON parse failure (truncated write from a previous run)
    - HMAC mismatch (tampered or bit-flipped content)
    - Envelope ``format`` marker doesn't match ``"aquilia-artifact"``
    - Missing required envelope fields

    This fault is raised only when the artifact type's ``on_corrupt``
    policy is ``"raise"``.  For ``"warn_and_reset"`` or ``"reset"``
    policies, the store returns ``None`` instead.
    """

    def __init__(self, path: str, reason: str) -> None:
        super().__init__(
            code="ARTIFACT_CORRUPT",
            message=f"Artifact at '{path}' is corrupt and cannot be loaded: {reason}",
            severity=Severity.ERROR,
            metadata={"path": path, "reason": reason},
        )
        self.path = path
        self.reason = reason


class ArtifactStaleFault(ArtifactFault):
    """
    An artifact's ``schema_version`` is incompatible with the current reader.

    This is raised (or triggers a clean rebuild, depending on policy) when
    the on-disk ``schema_version`` doesn't match the registered type's
    expected version.  This is distinct from ``ArtifactCorruptFault``:
    the file is intact, but the format has changed in a way the current
    code doesn't understand.
    """

    def __init__(self, path: str, stored: str, expected: str) -> None:
        super().__init__(
            code="ARTIFACT_STALE",
            message=(
                f"Artifact at '{path}' has schema_version {stored!r}; "
                f"this build requires {expected!r}.  Will rebuild from scratch."
            ),
            severity=Severity.WARN,
            metadata={"path": path, "stored_version": stored, "expected_version": expected},
        )
        self.path = path
        self.stored_version = stored
        self.expected_version = expected


class ArtifactLockTimeoutFault(ArtifactFault):
    """
    The advisory file lock for an artifact could not be acquired within
    the configured timeout.

    This is usually caused by a long-running parallel process that holds
    the exclusive write lock (e.g. two concurrent ``aq discover`` runs).
    """

    def __init__(self, path: str, timeout: float) -> None:
        super().__init__(
            code="ARTIFACT_LOCK_TIMEOUT",
            message=f"Could not acquire lock on artifact '{path}' within {timeout:.1f}s",
            severity=Severity.ERROR,
            retryable=True,
            metadata={"path": path, "timeout": timeout},
        )
        self.path = path
        self.timeout = timeout


class ArtifactTransactionFault(ArtifactFault):
    """
    A multi-artifact transaction failed to commit all staged writes.

    When this fault is raised, the transaction has been rolled back: all
    staged writes were discarded and the original artifacts are intact.
    This is the correct behavior for the migration-file/schema-snapshot
    pair (§3.6): either both are written or neither is.
    """

    def __init__(self, reason: str, staged_types: list[str]) -> None:
        super().__init__(
            code="ARTIFACT_TRANSACTION_FAILED",
            message=f"Artifact transaction failed: {reason}. Staged types: {staged_types}",
            severity=Severity.ERROR,
            metadata={"reason": reason, "staged_types": staged_types},
        )
        self.staged_types = staged_types
