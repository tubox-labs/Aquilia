"""
Aquilia MLOps Platform

Production-grade ML serving with TorchServe-class capabilities --
fully integrated with the Aquilia framework.

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

from ._structures import (
    AdaptiveBatchQueue,
    AtomicCounter,
    BloomFilter,
    CircuitBreaker,
    ConsistentHash,
    Experiment,
    ExperimentArm,
    ExperimentLedger,
    ExponentialDecay,
    LineageNode,
    LRUCache,
    MemoryTracker,
    ModelLineageDAG,
    RingBuffer,
    SlidingWindow,
    TokenBucketRateLimiter,
    TopKHeap,
)
from ._types import (
    BatchingStrategy,
    BatchRequest,
    BlobRef,
    CircuitBreakerConfig,
    CircuitState,
    DeviceType,
    DriftMethod,
    DriftReport,
    ExportTarget,
    # Enums
    Framework,
    InferenceMode,
    InferenceRequest,
    InferenceResult,
    LLMConfig,
    ModelpackManifest,
    ModelType,
    PlacementScore,
    PluginHook,
    Provenance,
    QuantizePreset,
    RolloutConfig,
    RolloutStrategy,
    Runtime,
    RuntimeKind,
    # Protocols
    StorageAdapter,
    StreamChunk,
    StreamingRuntime,
    # Data classes
    TensorSpec,
    TokenUsage,
)
from .api import AquiliaModel, model, serve
from .api.route_generator import RouteDefinition, RouteGenerator
from .di.providers import MLOpsConfig, register_mlops_providers

# New serving architecture
from .engine import InferencePipeline

# Integration modules
from .engine.faults import (
    AutoRollbackFault,
    BatchTimeoutFault,
    CircuitBreakerExhaustedFault,
    # Resilience faults
    CircuitBreakerFault,
    CircuitBreakerOpenFault,
    DriftDetectionFault,
    EncryptionFault,
    ImmutabilityViolationFault,
    InferenceFault,
    # Memory faults
    MemoryFault,
    MemoryHardLimitFault,
    MemorySoftLimitFault,
    MetricsExportFault,
    MLOpsFault,
    PackBuildFault,
    PackIntegrityFault,
    PackNotFoundFault,
    PackSignatureFault,
    PermissionDeniedFault,
    PlacementFault,
    PluginHookFault,
    PluginLoadFault,
    RateLimitFault,
    RegistryConnectionFault,
    RolloutAdvanceFault,
    RuntimeLoadFault,
    ScalingFault,
    SigningFault,
    # Streaming faults
    StreamingFault,
    StreamInterruptedFault,
    TokenLimitExceededFault,
    WarmupFault,
)
from .engine.hooks import (
    HookRegistry,
    after_predict,
    before_predict,
    collect_hooks,
    on_error,
    on_load,
    on_unload,
    postprocess,
    preprocess,
)
from .engine.lifecycle import mlops_on_shutdown, mlops_on_startup
from .manifest import (
    MLOpsManifestConfig,
    ModelManifestEntry,
    parse_mlops_config,
    validate_manifest_config,
)
from .observe.drift import DriftDetector
from .observe.metrics import MetricsCollector
from .orchestrator import (
    ModelEntry,
    ModelLoader,
    ModelOrchestrator,
    ModelRegistry,
    VersionManager,
    VersionRouter,
)
from .pack.builder import ModelpackBuilder
from .pack.content_store import ContentStore
from .plugins.host import PluginHost
from .registry.service import RegistryService
from .runtime.base import BaseRuntime, BaseStreamingRuntime, InvalidStateTransition, ModelState
from .runtime.device_manager import DeviceInfo, DeviceKind, DeviceManager
from .runtime.executor import InferenceExecutor, PoolKind
from .runtime.python_runtime import PythonRuntime
from .serving.batching import DynamicBatcher
from .serving.controllers import MLOpsController
from .serving.middleware import (
    mlops_circuit_breaker_middleware,
    mlops_metrics_middleware,
    mlops_rate_limit_middleware,
    mlops_request_id_middleware,
    register_mlops_middleware,
)
from .serving.server import ModelServingServer, WarmupStrategy

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
