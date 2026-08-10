"""
AquilaVectorDB — GPU capability probing and policy.

elips builds its GPU support conditionally at the C-extension level. On a
CPU-only build the ``Gpu*`` classes are *absent from the module*, not merely
inert, so nothing here may import a GPU symbol at module scope — every access
goes through :func:`_elips` inside a function body. That is what keeps
``import aquilia.vectordb`` working on a CPU-only install.

Two states are tracked separately and never collapsed:

``built``
    The wheel was compiled with GPU bindings (``elips.has_gpu``). Compile-time.

``available``
    A usable device is actually present (``elips.accelerators()`` is non-empty).
    Runtime.

A GPU-enabled wheel on a machine with no device is a normal, supported
condition. Reporting it as a single "no GPU" boolean makes it undiagnosable,
which is why :class:`GpuInfo` keeps both and the fault messages name which one
failed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from aquilia.vectordb.configs import GpuOptions
from aquilia.vectordb.faults import VectorGpuUnavailableFault

logger = logging.getLogger("aquilia.vectordb.gpu")


def _elips() -> Any:
    """Import ``elips`` lazily, converting absence into a typed fault."""
    from aquilia.vectordb._compat import require_elips

    return require_elips()


@dataclass(frozen=True)
class DeviceInfo:
    """
    A single detected accelerator.

    Args:
        index: Device ordinal.
        name: Device name, e.g. ``"Apple M4"``.
        backend: Driving backend — ``"metal"``, ``"cuda"``, ``"hip"``,
            ``"sycl"``, or ``"vulkan"``.
        total_memory_bytes: Total device memory.
        free_memory_bytes: Currently free device memory.
        unified_memory: Whether host and device share one address space (Apple
            silicon). When true, transfers are far cheaper and
            larger-than-VRAM indexes become practical.
        supports_fp16: Whether half-precision search is available.
    """

    index: int
    name: str
    backend: str
    total_memory_bytes: int
    free_memory_bytes: int
    unified_memory: bool
    supports_fp16: bool

    @property
    def memory_gb(self) -> float:
        """Total device memory in GiB."""
        return self.total_memory_bytes / (1024.0**3)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for health output and ``aq vectordb gpu status``."""
        return {
            "index": self.index,
            "name": self.name,
            "backend": self.backend,
            "total_memory_bytes": self.total_memory_bytes,
            "free_memory_bytes": self.free_memory_bytes,
            "memory_gb": round(self.memory_gb, 2),
            "unified_memory": self.unified_memory,
            "supports_fp16": self.supports_fp16,
        }


@dataclass(frozen=True)
class GpuInfo:
    """
    Snapshot of GPU capability.

    Attributes:
        built: The elips build carries GPU bindings.
        available: At least one usable device was detected.
        devices: Detected devices.
        error: Why probing failed, when it did. A probe failure is reported
            rather than raised — an unreadable driver should degrade a
            ``prefer_gpu`` store to CPU, not crash the process.
    """

    built: bool
    available: bool
    devices: tuple[DeviceInfo, ...] = ()
    error: str | None = None

    def device(self, index: int | None) -> DeviceInfo | None:
        """Return the device with ``index``, or the first one when ``None``."""
        if not self.devices:
            return None
        if index is None:
            return self.devices[0]
        for dev in self.devices:
            if dev.index == index:
                return dev
        return None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for health output and ``aq vectordb gpu status``."""
        return {
            "built": self.built,
            "available": self.available,
            "devices": [d.to_dict() for d in self.devices],
            "error": self.error,
        }


@dataclass
class _ProbeCache:
    """Process-wide probe cache.

    Device enumeration initializes a backend, which is neither free nor
    idempotent-cheap; several stores booting at once should not each pay for it.
    """

    value: GpuInfo | None = field(default=None)


_CACHE = _ProbeCache()


def probe(*, refresh: bool = False) -> GpuInfo:
    """
    Detect GPU capability.

    Args:
        refresh: Re-probe instead of returning the cached snapshot. Device
            *presence* does not change within a process, so the cache is
            correct; free-memory figures do drift, which is what this is for.

    Returns:
        A :class:`GpuInfo`. Never raises for a missing GPU — absence is a
        normal outcome, reported in the returned value.
    """
    if _CACHE.value is not None and not refresh:
        return _CACHE.value

    try:
        elips = _elips()
    except Exception as exc:
        info = GpuInfo(built=False, available=False, error=str(exc))
        _CACHE.value = info
        return info

    built = bool(getattr(elips, "has_gpu", False))
    if not built:
        info = GpuInfo(built=False, available=False)
        _CACHE.value = info
        return info

    try:
        specs = elips.accelerators()
    except Exception as exc:
        logger.warning("GPU probe failed, treating as CPU-only: %s", exc)
        info = GpuInfo(built=True, available=False, error=str(exc))
        _CACHE.value = info
        return info

    devices = tuple(
        DeviceInfo(
            index=spec.index,
            name=spec.name,
            backend=spec.backend,
            total_memory_bytes=spec.memory_bytes,
            free_memory_bytes=spec.free_memory_bytes,
            unified_memory=spec.unified_memory,
            supports_fp16=spec.supports_fp16,
        )
        for spec in specs
    )

    info = GpuInfo(built=True, available=bool(devices), devices=devices)
    _CACHE.value = info
    return info


def reset_probe_cache() -> None:
    """Clear the cached probe. For tests that simulate differing hardware."""
    _CACHE.value = None


def resolve(options: GpuOptions, *, store: str = "") -> GpuInfo:
    """
    Enforce a store's GPU policy against detected hardware.

    Args:
        options: The store's GPU options.
        store: Store alias, for fault and log messages.

    Returns:
        The :class:`GpuInfo` used for the decision.

    Raises:
        VectorGpuUnavailableFault: When ``policy="require_gpu"`` cannot be
            satisfied, or a requested ``device`` ordinal does not exist.
            Boot fails rather than quietly serving from CPU, because a
            deployment that asked for GPU has capacity assumptions that a
            silent downgrade would violate.
    """
    info = probe()
    scope = f" (store {store!r})" if store else ""

    if options.policy == "cpu_only":
        return info

    if options.policy == "require_gpu":
        if not info.built:
            raise VectorGpuUnavailableFault(
                reason=(
                    f"the installed elips build has no GPU bindings{scope}. Install a "
                    f"GPU-enabled elips build, or set policy='prefer_gpu' to allow CPU."
                ),
                policy=options.policy,
            )
        if not info.available:
            detail = f" ({info.error})" if info.error else ""
            raise VectorGpuUnavailableFault(
                reason=(
                    f"elips has GPU bindings but no usable device was detected{scope}{detail}. "
                    f"Set policy='prefer_gpu' to allow CPU execution."
                ),
                policy=options.policy,
            )
        if options.device is not None and info.device(options.device) is None:
            found = ", ".join(str(d.index) for d in info.devices) or "none"
            raise VectorGpuUnavailableFault(
                reason=f"device {options.device} not found{scope}; available ordinals: {found}",
                policy=options.policy,
            )
        return info

    # prefer_gpu — degrade, but say so. A silent downgrade is the failure mode
    # that gets discovered as a latency regression weeks later.
    if not info.available:
        why = "no GPU bindings in this elips build" if not info.built else "no usable device detected"
        logger.warning("GPU requested%s but %s — running on CPU", scope, why)
    elif options.device is not None and info.device(options.device) is None:
        logger.warning(
            "GPU device %s not found%s — letting elips select a device",
            options.device,
            scope,
        )

    return info


def build_config(options: GpuOptions, *, store: str = "") -> Any | None:
    """
    Translate :class:`GpuOptions` into a native ``elips.GpuConfig``.

    Args:
        options: The store's GPU options.
        store: Store alias, for fault and log messages.

    Returns:
        A configured ``elips.GpuConfig``, or ``None`` when GPU must not be
        attached — ``cpu_only``, an unsupported build, or no device present.

    Notes:
        Every GPU name is resolved through ``getattr`` inside this body. The
        ``has_gpu`` guard has to come first because ``connect(gpu=...)`` itself
        raises when the build lacks GPU bindings.
    """
    info = resolve(options, store=store)

    if options.policy == "cpu_only" or not info.built or not info.available:
        return None

    elips = _elips()
    cfg = elips.GpuConfig()

    policy_enum = getattr(elips, "GpuPolicy", None)
    if policy_enum is not None:
        if options.device is not None and info.device(options.device) is not None:
            # `specific` is what pins an ordinal; setting device_index under
            # `auto` leaves selection to elips and the pin is ignored.
            cfg.policy = getattr(policy_enum, "specific", policy_enum.prefer_gpu)
            cfg.device_index = options.device
        else:
            cfg.policy = getattr(policy_enum, options.policy, policy_enum.prefer_gpu)

    if options.memory_budget_mb:
        cfg.device_memory_pool_mb = int(options.memory_budget_mb)

    device = info.device(options.device)
    if device is not None and device.unified_memory:
        # On unified-memory parts (Apple silicon) host and device share one
        # address space, so telling elips avoids staging copies that would
        # otherwise be pure overhead.
        cfg.unified_memory = True

    return cfg


def check_plan(plan: Any, options: GpuOptions, *, collection: str = "") -> None:
    """
    Enforce ``fallback`` policy against a query plan.

    elips falls back to CPU at query time even under ``require_gpu``
    (ADR-GPU-008), so "same API, possibly slower" is the default contract. This
    is the opt-in check for deployments where it is not acceptable.

    Args:
        plan: The ``elips.QueryPlan`` returned by ``explain``.
        options: The store's GPU options.
        collection: Collection name, for the fault message.

    Raises:
        VectorGpuFault: When ``fallback="require"`` and the plan ran on CPU.
    """
    if options.policy == "cpu_only" or options.fallback == "allow":
        return

    if getattr(plan, "gpu_index", False):
        return

    strategy = getattr(plan, "strategy", "unknown")
    reason = f"planner selected {strategy!r} on the CPU index"

    if options.fallback == "warn":
        logger.warning("Vector query on %r fell back to CPU: %s", collection or "?", reason)
        return

    from aquilia.vectordb.faults import VectorGpuFault

    raise VectorGpuFault(reason=reason, collection=collection)


__all__ = [
    "DeviceInfo",
    "GpuInfo",
    "build_config",
    "check_plan",
    "probe",
    "reset_probe_cache",
    "resolve",
]
