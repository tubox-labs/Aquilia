"""
Aquilia MLOps Platform

Production-grade ML serving with TorchServe-class capabilities and
FastAPI-level simplicity -- fully integrated with the Aquilia framework.

Quick start (class-based)::

    from aquilia.mlops import AquiliaModel, model

    @model(name="sentiment", version="v1")
    class SentimentModel(AquiliaModel):
        async def load(self, artifacts_dir, device):
            self.pipeline = load_pipeline(artifacts_dir)

        async def predict(self, inputs):
            return {"sentiment": self.pipeline(inputs["text"])}

Quick start (functional)::

    from aquilia.mlops import serve

    @serve(name="echo", version="v1")
    async def echo_model(inputs: dict) -> dict:
        return {"echo": inputs.get("text", "")}
"""

from ._types import (
    # Enums
    Framework,
    RuntimeKind,
    QuantizePreset,
    ExportTarget,
    BatchingStrategy,
    RolloutStrategy,
    DriftMethod,
    ModelType,
    InferenceMode,
    DeviceType,
    CircuitState,
    # Data classes
    TensorSpec,
    BlobRef,
    Provenance,
    LLMConfig,
    ModelpackManifest,
    InferenceRequest,
    InferenceResult,
    StreamChunk,
    BatchRequest,
    PlacementScore,
    RolloutConfig,
    DriftReport,
    CircuitBreakerConfig,
    TokenUsage,
    # Protocols
    StorageAdapter,
    Runtime,
    StreamingRuntime,
    PluginHook,
)

from ._structures import (
    RingBuffer,
    LRUCache,
    AtomicCounter,
    ExponentialDecay,
    SlidingWindow,
    TopKHeap,
    BloomFilter,
    ConsistentHash,
    ModelLineageDAG,
    LineageNode,
    ExperimentLedger,
    Experiment,
    ExperimentArm,
    CircuitBreaker,
    TokenBucketRateLimiter,
    AdaptiveBatchQueue,
    MemoryTracker,
)

from .pack.builder import ModelpackBuilder
from .pack.content_store import ContentStore
from .registry.service import RegistryService
from .runtime.base import BaseRuntime, BaseStreamingRuntime, ModelState, InvalidStateTransition
from .runtime.python_runtime import PythonRuntime
from .runtime.device_manager import DeviceManager, DeviceInfo, DeviceKind
from .runtime.executor import InferenceExecutor, PoolKind
from .serving.server import ModelServingServer, WarmupStrategy
from .serving.batching import DynamicBatcher
from .observe.metrics import MetricsCollector
from .observe.drift import DriftDetector
from .plugins.host import PluginHost

# New serving architecture
from .engine import InferencePipeline
from .engine.hooks import (
    before_predict, after_predict, on_error,
    on_load, on_unload, preprocess, postprocess,
    HookRegistry, collect_hooks,
)
from .orchestrator import (
    ModelOrchestrator, ModelRegistry, ModelEntry,
    VersionManager, VersionRouter, ModelLoader,
)
from .api import AquiliaModel, model, serve
from .api.route_generator import RouteGenerator, RouteDefinition
from .manifest import (
    MLOpsManifestConfig, ModelManifestEntry, parse_mlops_config,
    validate_manifest_config,
)

# Integration modules
from .engine.faults import (
    MLOpsFault,
    PackBuildFault,
    PackIntegrityFault,
    PackSignatureFault,
    RegistryConnectionFault,
    PackNotFoundFault,
    ImmutabilityViolationFault,
    InferenceFault,
    BatchTimeoutFault,
    RuntimeLoadFault,
    WarmupFault,
    DriftDetectionFault,
    MetricsExportFault,
    RolloutAdvanceFault,
    AutoRollbackFault,
    PlacementFault,
    ScalingFault,
    SigningFault,
    PermissionDeniedFault,
    EncryptionFault,
    PluginLoadFault,
    PluginHookFault,
    # Resilience faults
    CircuitBreakerFault,
    CircuitBreakerOpenFault,
    CircuitBreakerExhaustedFault,
    RateLimitFault,
    # Streaming faults
    StreamingFault,
    StreamInterruptedFault,
    TokenLimitExceededFault,
    # Memory faults
    MemoryFault,
    MemorySoftLimitFault,
    MemoryHardLimitFault,
)
from .di.providers import register_mlops_providers, MLOpsConfig
from .serving.controllers import MLOpsController
from .serving.middleware import (
    mlops_metrics_middleware,
    mlops_request_id_middleware,
    mlops_rate_limit_middleware,
    mlops_circuit_breaker_middleware,
    register_mlops_middleware,
)
from .engine.lifecycle import mlops_on_startup, mlops_on_shutdown

__all__ = [
    # Types -- Enums
    "Framework",
    "RuntimeKind",
    "QuantizePreset",
    "ExportTarget",
    "BatchingStrategy",
    "RolloutStrategy",
    "DriftMethod",
    "ModelType",
    "InferenceMode",
    "DeviceType",
    "CircuitState",
    # Types -- Data classes
    "TensorSpec",
    "BlobRef",
    "Provenance",
    "LLMConfig",
    "ModelpackManifest",
    "InferenceRequest",
    "InferenceResult",
    "StreamChunk",
    "BatchRequest",
    "PlacementScore",
    "RolloutConfig",
    "DriftReport",
    "CircuitBreakerConfig",
    "TokenUsage",
    # Types -- Protocols
    "StorageAdapter",
    "Runtime",
    "StreamingRuntime",
    "PluginHook",
    # Data Structures
    "RingBuffer",
    "LRUCache",
    "AtomicCounter",
    "ExponentialDecay",
    "SlidingWindow",
    "TopKHeap",
    "BloomFilter",
    "ConsistentHash",
    "ModelLineageDAG",
    "LineageNode",
    "ExperimentLedger",
    "Experiment",
    "ExperimentArm",
    "CircuitBreaker",
    "TokenBucketRateLimiter",
    "AdaptiveBatchQueue",
    "MemoryTracker",
    # Core classes
    "ModelpackBuilder",
    "ContentStore",
    "RegistryService",
    "BaseRuntime",
    "BaseStreamingRuntime",
    "ModelState",
    "InvalidStateTransition",
    "PythonRuntime",
    "DeviceManager",
    "DeviceInfo",
    "DeviceKind",
    "InferenceExecutor",
    "PoolKind",
    "ModelServingServer",
    "WarmupStrategy",
    "DynamicBatcher",
    "MetricsCollector",
    "DriftDetector",
    "PluginHost",
    # New Serving Architecture
    "InferencePipeline",
    "before_predict",
    "after_predict",
    "on_error",
    "on_load",
    "on_unload",
    "preprocess",
    "postprocess",
    "HookRegistry",
    "collect_hooks",
    "ModelOrchestrator",
    "ModelRegistry",
    "ModelEntry",
    "VersionManager",
    "VersionRouter",
    "ModelLoader",
    "AquiliaModel",
    "model",
    "serve",
    "RouteGenerator",
    "RouteDefinition",
    "MLOpsManifestConfig",
    "ModelManifestEntry",
    "parse_mlops_config",
    "validate_manifest_config",
    # Faults
    "MLOpsFault",
    "PackBuildFault",
    "PackIntegrityFault",
    "PackSignatureFault",
    "RegistryConnectionFault",
    "PackNotFoundFault",
    "ImmutabilityViolationFault",
    "InferenceFault",
    "BatchTimeoutFault",
    "RuntimeLoadFault",
    "WarmupFault",
    "DriftDetectionFault",
    "MetricsExportFault",
    "RolloutAdvanceFault",
    "AutoRollbackFault",
    "PlacementFault",
    "ScalingFault",
    "SigningFault",
    "PermissionDeniedFault",
    "EncryptionFault",
    "PluginLoadFault",
    "PluginHookFault",
    "CircuitBreakerFault",
    "CircuitBreakerOpenFault",
    "CircuitBreakerExhaustedFault",
    "RateLimitFault",
    "StreamingFault",
    "StreamInterruptedFault",
    "TokenLimitExceededFault",
    "MemoryFault",
    "MemorySoftLimitFault",
    "MemoryHardLimitFault",
    # DI
    "register_mlops_providers",
    "MLOpsConfig",
    # Controller
    "MLOpsController",
    # Middleware
    "mlops_metrics_middleware",
    "mlops_request_id_middleware",
    "mlops_rate_limit_middleware",
    "mlops_circuit_breaker_middleware",
    "register_mlops_middleware",
    # Lifecycle
    "mlops_on_startup",
    "mlops_on_shutdown",
]
