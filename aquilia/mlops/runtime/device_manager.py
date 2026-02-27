"""
Device Manager — auto-detection, fallback, monitoring, and locking for
compute devices (CPU, CUDA, MPS, NPU).

The DeviceManager is a singleton-style service wired through DI that
every runtime and executor consults when placing a model on hardware.

Features:
- Auto-detect all available devices at startup
- Fallback chain: user-preferred → auto-detected → CPU
- Per-device memory monitoring (CUDA via torch, CPU via psutil/os)
- Device locking to prevent concurrent loads from overwhelming GPU memory
- Thread-safe via asyncio.Lock per device

Usage::

    dm = DeviceManager()
    await dm.initialize()
    device = await dm.select_device("auto")
    async with dm.acquire(device):
        await runtime.load()
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aquilia.mlops.runtime.device_manager")


class DeviceKind(str, Enum):
    """Hardware device categories."""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"
    NPU = "npu"
    TPU = "tpu"


@dataclass
class DeviceInfo:
    """Snapshot of a single compute device."""
    name: str                              # e.g. "cuda:0", "cpu", "mps"
    kind: DeviceKind
    index: int = 0                         # GPU index (0 for non-GPU)
    total_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    is_available: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def utilization(self) -> float:
        """Memory utilization ratio (0.0–1.0)."""
        if self.total_memory_mb <= 0:
            return 0.0
        return 1.0 - (self.available_memory_mb / self.total_memory_mb)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "index": self.index,
            "total_memory_mb": round(self.total_memory_mb, 2),
            "available_memory_mb": round(self.available_memory_mb, 2),
            "utilization": round(self.utilization(), 4),
            "is_available": self.is_available,
        }


class DeviceManager:
    """
    Centralized device management for ML runtimes.

    Discovers available compute devices, tracks memory, and provides
    a locking mechanism so that concurrent model loads don't fight
    over GPU memory.
    """

    def __init__(self) -> None:
        self._devices: Dict[str, DeviceInfo] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._initialized: bool = False
        self._default_device: str = "cpu"

    # ── Lifecycle ────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Detect all available devices and populate the registry."""
        if self._initialized:
            return

        # CPU is always available
        cpu_info = self._detect_cpu()
        self._devices["cpu"] = cpu_info
        self._locks["cpu"] = asyncio.Lock()

        # CUDA devices
        cuda_devices = self._detect_cuda()
        for dev in cuda_devices:
            self._devices[dev.name] = dev
            self._locks[dev.name] = asyncio.Lock()

        # Apple Silicon MPS
        mps_info = self._detect_mps()
        if mps_info:
            self._devices["mps"] = mps_info
            self._locks["mps"] = asyncio.Lock()

        # Choose best default
        if cuda_devices:
            self._default_device = cuda_devices[0].name
        elif mps_info:
            self._default_device = "mps"
        else:
            self._default_device = "cpu"

        self._initialized = True
        logger.info(
            "DeviceManager initialized: %d device(s), default=%s",
            len(self._devices), self._default_device,
        )

    # ── Device Selection ─────────────────────────────────────────────

    async def select_device(
        self,
        preference: str = "auto",
        memory_required_mb: float = 0.0,
    ) -> str:
        """
        Select the best device for a model load.

        Fallback chain:
        1. If ``preference`` is a specific device name and it's available → use it.
        2. If ``preference`` is ``"auto"`` → pick the best available device.
        3. If the preferred device has insufficient memory → fall back to CPU.
        4. CPU is always the final fallback.
        """
        if not self._initialized:
            await self.initialize()

        # Specific device requested
        if preference != "auto":
            dev = self._devices.get(preference)
            if dev and dev.is_available:
                if memory_required_mb <= 0 or dev.available_memory_mb >= memory_required_mb:
                    return dev.name
                logger.warning(
                    "Device %s has insufficient memory (%.0f MB available, "
                    "%.0f MB required); falling back",
                    preference, dev.available_memory_mb, memory_required_mb,
                )
            else:
                logger.warning(
                    "Requested device %s not available; falling back", preference,
                )

        # Auto-select: prefer GPU with most available memory
        best: Optional[DeviceInfo] = None
        for dev in self._devices.values():
            if not dev.is_available or dev.kind == DeviceKind.CPU:
                continue
            if memory_required_mb > 0 and dev.available_memory_mb < memory_required_mb:
                continue
            if best is None or dev.available_memory_mb > best.available_memory_mb:
                best = dev

        if best:
            return best.name

        # Final fallback
        return "cpu"

    # ── Device Locking ───────────────────────────────────────────────

    class _DeviceGuard:
        """Async context manager that holds a device lock."""

        __slots__ = ("_lock",)

        def __init__(self, lock: asyncio.Lock) -> None:
            self._lock = lock

        async def __aenter__(self) -> None:
            await self._lock.acquire()

        async def __aexit__(self, *exc: Any) -> None:
            self._lock.release()

    def acquire(self, device_name: str) -> "_DeviceGuard":
        """
        Acquire an exclusive lock on a device.

        Use as an async context manager::

            async with device_manager.acquire("cuda:0"):
                await runtime.load()
        """
        lock = self._locks.get(device_name)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[device_name] = lock
        return self._DeviceGuard(lock)

    # ── Monitoring ───────────────────────────────────────────────────

    async def refresh(self, device_name: Optional[str] = None) -> None:
        """Refresh memory stats for one or all devices."""
        targets = (
            [self._devices[device_name]] if device_name and device_name in self._devices
            else list(self._devices.values())
        )
        for dev in targets:
            if dev.kind == DeviceKind.CUDA:
                self._refresh_cuda(dev)
            elif dev.kind == DeviceKind.CPU:
                self._refresh_cpu(dev)

    def get_device(self, name: str) -> Optional[DeviceInfo]:
        """Get info for a specific device."""
        return self._devices.get(name)

    def list_devices(self) -> List[DeviceInfo]:
        """Return all known devices."""
        return list(self._devices.values())

    @property
    def default_device(self) -> str:
        return self._default_device

    def summary(self) -> Dict[str, Any]:
        """Return a summary dict suitable for health check responses."""
        return {
            "default_device": self._default_device,
            "devices": {name: dev.to_dict() for name, dev in self._devices.items()},
        }

    # ── Detection Helpers ────────────────────────────────────────────

    @staticmethod
    def _detect_cpu() -> DeviceInfo:
        total_mb = 0.0
        avail_mb = 0.0
        try:
            import psutil
            vm = psutil.virtual_memory()
            total_mb = vm.total / (1024 * 1024)
            avail_mb = vm.available / (1024 * 1024)
        except ImportError:
            # Fallback: read /proc/meminfo on Linux or sysctl on macOS
            try:
                pages = os.sysconf("SC_PHYS_PAGES")
                page_size = os.sysconf("SC_PAGE_SIZE")
                total_mb = (pages * page_size) / (1024 * 1024)
                avail_mb = total_mb * 0.5  # rough estimate
            except (ValueError, OSError):
                pass
        return DeviceInfo(
            name="cpu",
            kind=DeviceKind.CPU,
            total_memory_mb=total_mb,
            available_memory_mb=avail_mb,
            is_available=True,
        )

    @staticmethod
    def _detect_cuda() -> List[DeviceInfo]:
        devices: List[DeviceInfo] = []
        try:
            import torch
            if not torch.cuda.is_available():
                return devices
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                total = props.total_mem / (1024 * 1024)
                # Use memory_reserved as a proxy for allocated
                allocated = torch.cuda.memory_allocated(i) / (1024 * 1024)
                devices.append(DeviceInfo(
                    name=f"cuda:{i}",
                    kind=DeviceKind.CUDA,
                    index=i,
                    total_memory_mb=total,
                    available_memory_mb=total - allocated,
                    is_available=True,
                    metadata={"gpu_name": props.name},
                ))
        except ImportError:
            pass
        return devices

    @staticmethod
    def _detect_mps() -> Optional[DeviceInfo]:
        try:
            import torch
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return DeviceInfo(
                    name="mps",
                    kind=DeviceKind.MPS,
                    is_available=True,
                    metadata={"backend": "Apple Metal Performance Shaders"},
                )
        except ImportError:
            pass
        return None

    @staticmethod
    def _refresh_cuda(dev: DeviceInfo) -> None:
        try:
            import torch
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(dev.index) / (1024 * 1024)
                dev.available_memory_mb = dev.total_memory_mb - allocated
        except ImportError:
            pass

    @staticmethod
    def _refresh_cpu(dev: DeviceInfo) -> None:
        try:
            import psutil
            vm = psutil.virtual_memory()
            dev.available_memory_mb = vm.available / (1024 * 1024)
        except ImportError:
            pass
