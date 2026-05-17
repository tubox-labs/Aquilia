# MLOps API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `RingBuffer` | `aquilia/mlops/_structures.py` | Generic[T] | Fixed-capacity circular buffer backed by a pre-allocated list. |
| `LRUCache` | `aquilia/mlops/_structures.py` | Generic[KT, VT] | O(1) get / put / evict cache backed by :class:`OrderedDict`. |
| `AtomicCounter` | `aquilia/mlops/_structures.py` | object | Thread-safe monotonic counter (integers only). |
| `ExponentialDecay` | `aquilia/mlops/_structures.py` | object | EWMA (Exponentially Weighted Moving Average). |
| `SlidingWindow` | `aquilia/mlops/_structures.py` | object | Time-bucketed sliding window for rate/latency tracking. |
| `TopKHeap` | `aquilia/mlops/_structures.py` | Generic[KT] | Maintains the top-K elements by score using a dict + sort-on-read |
| `BloomFilter` | `aquilia/mlops/_structures.py` | object | Space-efficient probabilistic set for fast negative lookups. |
| `ConsistentHash` | `aquilia/mlops/_structures.py` | object | Jump-consistent hash for sticky model-to-node routing. |
| `LineageNode` | `aquilia/mlops/_structures.py` | object | A single node in the model lineage graph. |
| `ModelLineageDAG` | `aquilia/mlops/_structures.py` | object | Directed acyclic graph tracking model derivation relationships. |
| `ExperimentArm` | `aquilia/mlops/_structures.py` | object | One arm of an A/B experiment. |
| `Experiment` | `aquilia/mlops/_structures.py` | object | A/B experiment definition. |
| `ExperimentLedger` | `aquilia/mlops/_structures.py` | object | Records A/B experiment assignments and collects per-arm metrics. |
| `CircuitBreaker` | `aquilia/mlops/_structures.py` | object | Three-state circuit breaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED). |
| `TokenBucketRateLimiter` | `aquilia/mlops/_structures.py` | object | Token-bucket rate limiter for inference request throttling. |
| `AdaptiveBatchQueue` | `aquilia/mlops/_structures.py` | Generic[T] | Priority-aware batch queue with adaptive sizing for LLM serving. |
| `MemoryTracker` | `aquilia/mlops/_structures.py` | object | Tracks memory allocations for model serving with watermark alerts. |
| `DType` | `aquilia/mlops/_types.py` | str, Enum | Centralized DType system for Aquilia MLOps. |
| `Framework` | `aquilia/mlops/_types.py` | str, Enum | Supported ML frameworks. |
| `RuntimeKind` | `aquilia/mlops/_types.py` | str, Enum | Available runtime backends. |
| `QuantizePreset` | `aquilia/mlops/_types.py` | str, Enum | Quantization presets. |
| `ExportTarget` | `aquilia/mlops/_types.py` | str, Enum | Edge export targets. |
| `BatchingStrategy` | `aquilia/mlops/_types.py` | str, Enum | Batching strategy modes. |
| `RolloutStrategy` | `aquilia/mlops/_types.py` | str, Enum | Release rollout strategies. |
| `DriftMethod` | `aquilia/mlops/_types.py` | str, Enum | Drift detection methods. |
| `ModelType` | `aquilia/mlops/_types.py` | str, Enum | Model type classification for serving strategy selection. |
| `InferenceMode` | `aquilia/mlops/_types.py` | str, Enum | Inference execution modes. |
| `DeviceType` | `aquilia/mlops/_types.py` | str, Enum | Compute device types. |
| `CircuitState` | `aquilia/mlops/_types.py` | str, Enum | Circuit breaker states. |
| `TensorSpec` | `aquilia/mlops/_types.py` | object | Describes a single tensor in the inference signature. |
| `BlobRef` | `aquilia/mlops/_types.py` | object | Reference to a blob inside a modelpack. |
| `Provenance` | `aquilia/mlops/_types.py` | object | Provenance metadata for reproducibility. |
| `LLMConfig` | `aquilia/mlops/_types.py` | object | Configuration specific to LLM/SLM model serving. |
| `ModelpackManifest` | `aquilia/mlops/_types.py` | object | Complete manifest for a modelpack artifact. |
| `InferenceRequest` | `aquilia/mlops/_types.py` | object | A single inference request. |
| `InferenceResult` | `aquilia/mlops/_types.py` | object | Result of a single inference. |
| `StreamChunk` | `aquilia/mlops/_types.py` | object | A single chunk in a streaming inference response. |
| `BatchRequest` | `aquilia/mlops/_types.py` | object | Aggregated batch of inference requests. |
| `PlacementScore` | `aquilia/mlops/_types.py` | object | Score for scheduler placement decisions. |
| `RolloutConfig` | `aquilia/mlops/_types.py` | object | Configuration for a traffic rollout. |
| `DriftReport` | `aquilia/mlops/_types.py` | object | Result of a drift detection analysis. |
| `CircuitBreakerConfig` | `aquilia/mlops/_types.py` | object | Configuration for inference circuit breaker. |
| `TokenUsage` | `aquilia/mlops/_types.py` | object | Token usage tracking for LLM inference. |
| `StorageAdapter` | `aquilia/mlops/_types.py` | Protocol | Protocol for blob storage backends. |
| `Runtime` | `aquilia/mlops/_types.py` | Protocol | Protocol for model runtime backends. |
| `StreamingRuntime` | `aquilia/mlops/_types.py` | Protocol | Protocol for runtimes that support streaming inference (LLMs). |
| `PluginHook` | `aquilia/mlops/_types.py` | Protocol | Protocol for plugin lifecycle hooks. |
| `TensorSpecBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates and renders tensor specifications. |
| `BlobRefBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates blob references. |
| `ProvenanceBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates provenance metadata. |
| `ModelpackManifestBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Full manifest blueprint with deep validation. |
| `InferenceRequestBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates incoming inference request payloads. |
| `InferenceResultBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders inference results for API responses. |
| `DriftReportBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders drift detection reports. |
| `RolloutConfigBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates rollout configuration payloads. |
| `RolloutStateBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders rollout state for API responses. |
| `ScalingPolicyBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates autoscaler policy configuration. |
| `NodeInfoBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates compute node registration payloads. |
| `PlacementRequestBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates model placement request payloads. |
| `PluginDescriptorBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders plugin descriptor for API responses. |
| `MetricsSummaryBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders metrics summary for API responses. |
| `LLMConfigBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates LLM configuration payloads. |
| `StreamChunkBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders a single streaming token/chunk for SSE responses. |
| `TokenUsageBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders token usage statistics for LLM inference. |
| `LLMInferenceRequestBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates incoming LLM inference request payloads. |
| `LLMInferenceResultBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders LLM inference results including token metrics. |
| `ChatMessageBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates a single chat message. |
| `ChatRequestBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Validates chat-style LLM request payloads. |
| `ChatResponseBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders chat-style LLM response. |
| `CircuitBreakerStatusBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders circuit breaker state for API responses. |
| `RateLimiterStatusBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders rate limiter state for API responses. |
| `MemoryStatusBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders memory tracker state for API responses. |
| `ModelCapabilitiesBlueprint` | `aquilia/mlops/api/blueprints.py` | Blueprint | Renders model capabilities for API responses. |
| `AquiliaModel` | `aquilia/mlops/api/model_class.py` | object | Base class for Aquilia ML models. |
| `RouteDefinition` | `aquilia/mlops/api/route_generator.py` | object | A generated route definition ready for controller compilation. |
| `RouteGenerator` | `aquilia/mlops/api/route_generator.py` | object | Generates HTTP route definitions from registered models. |
| `MLOpsConfig` | `aquilia/mlops/di/providers.py` | object | Typed configuration for MLOps DI registration. |
| `MLOpsFault` | `aquilia/mlops/engine/faults.py` | Fault | Base fault for all MLOps operations. |
| `PackFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for model packaging. |
| `PackBuildFault` | `aquilia/mlops/engine/faults.py` | PackFault | Model pack build failed. |
| `PackIntegrityFault` | `aquilia/mlops/engine/faults.py` | PackFault | Blob integrity check failed (SHA-256 mismatch) or structural issue. |
| `PackSignatureFault` | `aquilia/mlops/engine/faults.py` | PackFault | Artifact signature verification failed. |
| `RegistryFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for registry operations. |
| `RegistryConnectionFault` | `aquilia/mlops/engine/faults.py` | RegistryFault | Cannot connect to registry backend. |
| `PackNotFoundFault` | `aquilia/mlops/engine/faults.py` | RegistryFault | Requested modelpack not found in registry. |
| `ImmutabilityViolationFault` | `aquilia/mlops/engine/faults.py` | RegistryFault | Attempted to overwrite an immutable artifact. |
| `ServingFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for model serving. |
| `RuntimeLoadFault` | `aquilia/mlops/engine/faults.py` | ServingFault | Model failed to load into runtime. |
| `InferenceFault` | `aquilia/mlops/engine/faults.py` | ServingFault | Inference failed for a request. |
| `BatchTimeoutFault` | `aquilia/mlops/engine/faults.py` | ServingFault | Batch processing exceeded deadline. |
| `WarmupFault` | `aquilia/mlops/engine/faults.py` | ServingFault | Model warm-up failed. |
| `ObserveFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for observability. |
| `DriftDetectionFault` | `aquilia/mlops/engine/faults.py` | ObserveFault | Drift detection computation failed. |
| `MetricsExportFault` | `aquilia/mlops/engine/faults.py` | ObserveFault | Metrics export/scrape failed. |
| `RolloutFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for release management. |
| `RolloutAdvanceFault` | `aquilia/mlops/engine/faults.py` | RolloutFault | Rollout advancement failed due to metric degradation. |
| `AutoRollbackFault` | `aquilia/mlops/engine/faults.py` | RolloutFault | Automatic rollback triggered. |
| `SchedulerFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for scheduling. |
| `PlacementFault` | `aquilia/mlops/engine/faults.py` | SchedulerFault | No suitable node found for model placement. |
| `ScalingFault` | `aquilia/mlops/engine/faults.py` | SchedulerFault | Scaling operation failed. |
| `MLOpsSecurityFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for MLOps security. |
| `SigningFault` | `aquilia/mlops/engine/faults.py` | MLOpsSecurityFault | Artifact signing failed. |
| `PermissionDeniedFault` | `aquilia/mlops/engine/faults.py` | MLOpsSecurityFault | User lacks required RBAC permission. |
| `EncryptionFault` | `aquilia/mlops/engine/faults.py` | MLOpsSecurityFault | Encryption / decryption operation failed. |
| `PluginFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for plugin operations. |
| `PluginLoadFault` | `aquilia/mlops/engine/faults.py` | PluginFault | Plugin failed to load. |
| `PluginHookFault` | `aquilia/mlops/engine/faults.py` | PluginFault | Plugin hook execution failed. |
| `CircuitBreakerFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for circuit breaker events. |
| `CircuitBreakerOpenFault` | `aquilia/mlops/engine/faults.py` | CircuitBreakerFault | Circuit breaker is OPEN -- requests are being rejected. |
| `CircuitBreakerExhaustedFault` | `aquilia/mlops/engine/faults.py` | CircuitBreakerFault | Circuit breaker half-open probe failed -- returning to OPEN state. |
| `RateLimitFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Request rejected due to rate limiting. |
| `StreamingFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for streaming inference. |
| `StreamInterruptedFault` | `aquilia/mlops/engine/faults.py` | StreamingFault | Streaming generation was interrupted (client disconnect, timeout, etc.). |
| `TokenLimitExceededFault` | `aquilia/mlops/engine/faults.py` | StreamingFault | Token generation exceeded max_tokens limit. |
| `MemoryFault` | `aquilia/mlops/engine/faults.py` | MLOpsFault | Base fault for memory management. |
| `MemorySoftLimitFault` | `aquilia/mlops/engine/faults.py` | MemoryFault | Memory usage crossed soft limit -- eviction candidates available. |
| `MemoryHardLimitFault` | `aquilia/mlops/engine/faults.py` | MemoryFault | Memory usage crossed hard limit -- requests must be rejected. |
| `HookRegistry` | `aquilia/mlops/engine/hooks.py` | object | Collected hooks from a model class. |
| `MLOpsManifest` | `aquilia/mlops/engine/module.py` | object | Aquilary-compatible manifest for the MLOps subsystem. |
| `PipelineContext` | `aquilia/mlops/engine/pipeline.py` | object | Per-request context flowing through the pipeline. |
| `InferencePipeline` | `aquilia/mlops/engine/pipeline.py` | object | Async inference pipeline with hooks and metrics. |
| `ExplainMethod` | `aquilia/mlops/explain/hooks.py` | str, Enum | Public class. |
| `FeatureAttribution` | `aquilia/mlops/explain/hooks.py` | object | Single feature's contribution. |
| `Explanation` | `aquilia/mlops/explain/hooks.py` | object | Complete explanation for one prediction. |
| `SHAPExplainer` | `aquilia/mlops/explain/hooks.py` | object | Wraps ``shap.KernelExplainer``, ``shap.TreeExplainer`` or |
| `LIMEExplainer` | `aquilia/mlops/explain/hooks.py` | object | Wraps ``lime.lime_tabular.LimeTabularExplainer`` (default) or |
| `PIIKind` | `aquilia/mlops/explain/privacy.py` | str, Enum | Public class. |
| `PIIMatch` | `aquilia/mlops/explain/privacy.py` | object | Public class. |
| `PIIRedactor` | `aquilia/mlops/explain/privacy.py` | object | Scans text for PII and replaces matches with a configurable placeholder. |
| `LaplaceNoise` | `aquilia/mlops/explain/privacy.py` | object | Adds calibrated Laplace noise to numeric values. |
| `InputSanitiser` | `aquilia/mlops/explain/privacy.py` | object | Pipeline of transforms applied to inference payloads before they |
| `ModelManifestEntry` | `aquilia/mlops/manifest/config.py` | object | Configuration for a single model from the manifest. |
| `MLOpsManifestConfig` | `aquilia/mlops/manifest/config.py` | object | Parsed ``[mlops]`` configuration from Aquilia workspace config. |
| `ManifestValidationError` | `aquilia/mlops/manifest/schema.py` | ValueError | Raised when manifest validation fails. |
| `DriftDetector` | `aquilia/mlops/observe/drift.py` | object | Model drift detection engine. |
| `PredictionLogger` | `aquilia/mlops/observe/logger.py` | object | Logs feature/prediction pairs for monitoring, debugging, and retraining. |
| `MetricPoint` | `aquilia/mlops/observe/metrics.py` | object | Single metric data point. |
| `MetricsCollector` | `aquilia/mlops/observe/metrics.py` | object | In-process metrics collector with Prometheus text format export. |
| `ExportResult` | `aquilia/mlops/optimizer/export.py` | object | Result of an edge export. |
| `EdgeExporter` | `aquilia/mlops/optimizer/export.py` | object | Export models to edge-friendly formats. |
| `OptimizationResult` | `aquilia/mlops/optimizer/pipeline.py` | object | Result of an optimization pass. |
| `OptimizationPipeline` | `aquilia/mlops/optimizer/pipeline.py` | object | Runs a sequence of optimization passes on model files. |
| `LoadedModel` | `aquilia/mlops/orchestrator/loader.py` | object | Container for a loaded model instance and its associated resources. |
| `ModelLoader` | `aquilia/mlops/orchestrator/loader.py` | object | Manages model instantiation, loading, unloading, and hot reload. |
| `ModelOrchestrator` | `aquilia/mlops/orchestrator/orchestrator.py` | object | Top-level inference façade. |
| `ModelBundle` | `aquilia/mlops/orchestrator/persistence.py` | object | A complete model bundle ready for persistence. |
| `ModelLoader` | `aquilia/mlops/orchestrator/persistence.py` | abc.ABC | Abstract base class for framework-specific model loaders. |
| `ModelSaver` | `aquilia/mlops/orchestrator/persistence.py` | abc.ABC | Abstract base class for framework-specific model savers. |
| `PyTorchModelLoader` | `aquilia/mlops/orchestrator/persistence.py` | ModelLoader | Production-grade PyTorch model loader. |
| `PyTorchModelSaver` | `aquilia/mlops/orchestrator/persistence.py` | ModelSaver | Production-grade PyTorch model saver. |
| `ModelPersistenceManager` | `aquilia/mlops/orchestrator/persistence.py` | object | Orchestrates high-level model persistence operations. |
| `ModelConfig` | `aquilia/mlops/orchestrator/registry.py` | object | Per-model configuration (from manifest or decorator). |
| `ModelEntry` | `aquilia/mlops/orchestrator/registry.py` | object | Registry entry for a single model version. |
| `ModelRegistry` | `aquilia/mlops/orchestrator/registry.py` | object | In-memory metadata-only model registry. |
| `CanaryConfig` | `aquilia/mlops/orchestrator/router.py` | object | Active canary configuration for a model. |
| `VersionRouter` | `aquilia/mlops/orchestrator/router.py` | object | Routes inference requests to the correct model version. |
| `VersionManager` | `aquilia/mlops/orchestrator/versioning.py` | object | Version Management for ML models. |
| `ModelpackBuilder` | `aquilia/mlops/pack/builder.py` | object | Builds a modelpack archive from local files. |
| `ContentStore` | `aquilia/mlops/pack/content_store.py` | object | Local filesystem content-addressable blob store. |
| `SignatureError` | `aquilia/mlops/pack/signer.py` | Exception | Raised when signature verification fails. |
| `HMACSigner` | `aquilia/mlops/pack/signer.py` | object | HMAC-SHA256 signer for modelpack archives. |
| `RSASigner` | `aquilia/mlops/pack/signer.py` | object | RSA signer using ``cryptography`` (already an Aquilia dependency). |
| `HealthCheckPlugin` | `aquilia/mlops/plugins/example_plugin.py` | object | Minimal example plugin implementing the ``PluginHook`` protocol. |
| `PluginState` | `aquilia/mlops/plugins/host.py` | str, Enum | Public class. |
| `PluginDescriptor` | `aquilia/mlops/plugins/host.py` | object | Public class. |
| `PluginHookProtocol` | `aquilia/mlops/plugins/host.py` | Protocol | Minimal interface a plugin must satisfy. |
| `PluginHost` | `aquilia/mlops/plugins/host.py` | object | Central plugin manager. |
| `MarketplaceEntry` | `aquilia/mlops/plugins/marketplace.py` | object | Public class. |
| `PluginMarketplace` | `aquilia/mlops/plugins/marketplace.py` | object | Browse and install plugins from a remote JSON index. |
| `RegistryDB` | `aquilia/mlops/registry/models.py` | object | Async SQLite backend for registry metadata. |
| `RegistryError` | `aquilia/mlops/registry/service.py` | Exception | Base error for registry operations (kept for backward compatibility). |
| `PackNotFoundError` | `aquilia/mlops/registry/service.py` | RegistryError | Raised when a modelpack is not found (kept for backward compatibility). |
| `ImmutabilityError` | `aquilia/mlops/registry/service.py` | RegistryError | Raised when attempting to overwrite an immutable artifact (kept for backward compatibility). |
| `RegistryService` | `aquilia/mlops/registry/service.py` | object | Modelpack registry service. |
| `BaseStorageAdapter` | `aquilia/mlops/registry/storage/base.py` | abc.ABC | Abstract base for blob storage backends. |
| `FilesystemStorageAdapter` | `aquilia/mlops/registry/storage/filesystem.py` | BaseStorageAdapter | Store blobs on local filesystem in a content-addressable layout. |
| `S3StorageAdapter` | `aquilia/mlops/registry/storage/s3.py` | BaseStorageAdapter | Store blobs in an S3-compatible bucket. |
| `RolloutPhase` | `aquilia/mlops/release/rollout.py` | str, Enum | Public class. |
| `RolloutState` | `aquilia/mlops/release/rollout.py` | object | Current state of a rollout. |
| `RolloutEngine` | `aquilia/mlops/release/rollout.py` | object | Manages progressive rollouts with metric-based gating. |
| `ModelState` | `aquilia/mlops/runtime/base.py` | str, Enum | Lifecycle states for a model runtime. |
| `InvalidStateTransition` | `aquilia/mlops/runtime/base.py` | RuntimeError | Raised when an illegal state transition is attempted. |
| `BaseRuntime` | `aquilia/mlops/runtime/base.py` | abc.ABC | Abstract runtime for model inference. |
| `BaseStreamingRuntime` | `aquilia/mlops/runtime/base.py` | BaseRuntime | Abstract runtime that adds streaming inference for LLM/SLM models. |
| `BentoExporter` | `aquilia/mlops/runtime/bento_exporter.py` | BaseRuntime | Export modelpacks to BentoML service format. |
| `DeviceKind` | `aquilia/mlops/runtime/device_manager.py` | str, Enum | Hardware device categories. |
| `DeviceInfo` | `aquilia/mlops/runtime/device_manager.py` | object | Snapshot of a single compute device. |
| `DeviceManager` | `aquilia/mlops/runtime/device_manager.py` | object | Centralized device management for ML runtimes. |
| `PoolKind` | `aquilia/mlops/runtime/executor.py` | str, Enum | Executor pool types. |
| `InferenceExecutor` | `aquilia/mlops/runtime/executor.py` | object | Async-compatible executor for CPU/GPU-bound inference work. |
| `ONNXRuntimeAdapter` | `aquilia/mlops/runtime/onnx_runtime.py` | BaseRuntime | ONNX Runtime inference adapter. |
| `PythonRuntime` | `aquilia/mlops/runtime/python_runtime.py` | BaseStreamingRuntime | In-process Python runtime with LLM streaming support. |
| `TorchServeExporter` | `aquilia/mlops/runtime/torchserve_exporter.py` | BaseRuntime | Export modelpacks to TorchServe ``.mar`` format and |
| `TritonAdapter` | `aquilia/mlops/runtime/triton_adapter.py` | BaseRuntime | Triton Inference Server adapter. |
| `ScalingPolicy` | `aquilia/mlops/scheduler/autoscaler.py` | object | Autoscaling policy definition. |
| `ScalingDecision` | `aquilia/mlops/scheduler/autoscaler.py` | object | Output of a scaling evaluation. |
| `Autoscaler` | `aquilia/mlops/scheduler/autoscaler.py` | object | Autoscaling engine for model serving deployments. |
| `NodeInfo` | `aquilia/mlops/scheduler/placement.py` | object | Information about a compute node. |
| `PlacementRequest` | `aquilia/mlops/scheduler/placement.py` | object | Request for model placement. |
| `PlacementScheduler` | `aquilia/mlops/scheduler/placement.py` | object | Greedy placement scheduler with soft device affinity. |
| `BlobEncryptor` | `aquilia/mlops/security/encryption.py` | object | Encrypts / decrypts blob data at rest using Fernet (AES-128-CBC). |
| `Permission` | `aquilia/mlops/security/rbac.py` | str, Enum | Registry permissions. |
| `Role` | `aquilia/mlops/security/rbac.py` | object | A named role with a set of permissions. |
| `RBACManager` | `aquilia/mlops/security/rbac.py` | object | Role-based access control for registry operations. |
| `ArtifactSigner` | `aquilia/mlops/security/signing.py` | object | Signs and verifies modelpack artifacts. |
| `EncryptionManager` | `aquilia/mlops/security/signing.py` | object | Encryption at rest for registry blob storage. |
| `DynamicBatcher` | `aquilia/mlops/serving/batching.py` | object | Async dynamic batching scheduler. |
| `MLOpsController` | `aquilia/mlops/serving/controllers.py` | Controller | Controller for MLOps HTTP API. |
| `RouteTarget` | `aquilia/mlops/serving/router.py` | object | A model version target with associated weight. |
| `TrafficRouter` | `aquilia/mlops/serving/router.py` | object | Routes inference requests across model version targets. |
| `WarmupStrategy` | `aquilia/mlops/serving/server.py` | object | Pre-inference warm-up to eliminate cold-start latency. |
| `ModelServingServer` | `aquilia/mlops/serving/server.py` | object | High-level model serving server. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `serve` | `aquilia/mlops/api/functional.py` | `def serve(name: str, version: str = 'v1', device: str = 'auto', batch_size: int = 16, max_batch_latency_ms: float = 50.0, workers: int = 4, tags: list[str] &#124; None = None) -> Callable` | Decorator that wraps a function into a registered model. |
| `set_global_registry` | `aquilia/mlops/api/model_class.py` | `def set_global_registry(registry: Any) -> None` | Set the global model registry (called by DI providers). |
| `model` | `aquilia/mlops/api/model_class.py` | `def model(name: str, version: str = 'v1', device: str = 'auto', batch_size: int = 16, max_batch_latency_ms: float = 50.0, warmup_requests: int = 0, workers: int = 4, timeout_ms: float = 30000.0, tags: list[str] &#124; None = None, supports_streaming: bool = False) -> Callable[[type[T]], type[T]]` | Decorator that registers an ``AquiliaModel`` subclass with the model registry. |
| `register_mlops_providers` | `aquilia/mlops/di/providers.py` | `def register_mlops_providers(container: Container, config: dict[str, Any] &#124; None = None) -> None` | Register all MLOps services as DI providers. |
| `on_load` | `aquilia/mlops/engine/hooks.py` | `def on_load(fn: F) -> F` | Mark method as a post-load lifecycle hook. |
| `on_unload` | `aquilia/mlops/engine/hooks.py` | `def on_unload(fn: F) -> F` | Mark method as a pre-unload lifecycle hook. |
| `preprocess` | `aquilia/mlops/engine/hooks.py` | `def preprocess(fn: F) -> F` | Mark method as input preprocessor. |
| `postprocess` | `aquilia/mlops/engine/hooks.py` | `def postprocess(fn: F) -> F` | Mark method as output postprocessor. |
| `before_predict` | `aquilia/mlops/engine/hooks.py` | `def before_predict(fn: F) -> F` | Mark method as a before-prediction hook. |
| `after_predict` | `aquilia/mlops/engine/hooks.py` | `def after_predict(fn: F) -> F` | Mark method as an after-prediction hook. |
| `on_error` | `aquilia/mlops/engine/hooks.py` | `def on_error(fn: F) -> F` | Mark method as an inference error handler. |
| `collect_hooks` | `aquilia/mlops/engine/hooks.py` | `def collect_hooks(instance: Any) -> HookRegistry` | Scan an object instance for decorated hook methods. |
| `mlops_on_startup` | `aquilia/mlops/engine/lifecycle.py` | `async def mlops_on_startup(config: dict[str, Any] &#124; None = None, di_container: Any = None) -> None` | MLOps startup hook. |
| `mlops_on_shutdown` | `aquilia/mlops/engine/lifecycle.py` | `async def mlops_on_shutdown(config: dict[str, Any] &#124; None = None, di_container: Any = None) -> None` | MLOps shutdown hook. |
| `create_explainer` | `aquilia/mlops/explain/hooks.py` | `def create_explainer(method: ExplainMethod, predict_fn: Callable, data: Any, feature_names: Sequence[str] &#124; None = None, **kwargs: Any) -> SHAPExplainer &#124; LIMEExplainer` | Factory that returns the right explainer for the requested method. |
| `parse_mlops_config` | `aquilia/mlops/manifest/config.py` | `def parse_mlops_config(config: dict[str, Any]) -> MLOpsManifestConfig` | Parse an ``[mlops]`` config dict into ``MLOpsManifestConfig``. |
| `validate_manifest_config` | `aquilia/mlops/manifest/schema.py` | `def validate_manifest_config(config: MLOpsManifestConfig) -> list[str]` | Validate a parsed manifest config. |
| `validate_and_raise` | `aquilia/mlops/manifest/schema.py` | `def validate_and_raise(config: MLOpsManifestConfig) -> None` | Validate and raise ``ManifestValidationError`` if invalid. |
| `profile_model` | `aquilia/mlops/optimizer/export.py` | `async def profile_model(model_path: str, target_device: str = 'cpu') -> dict[str, Any]` | Estimate latency and memory for a model on a target device. |
| `validate_manifest` | `aquilia/mlops/pack/manifest_schema.py` | `def validate_manifest(data: dict) -> list[str]` | Validate manifest dict against schema. |
| `sign_archive` | `aquilia/mlops/pack/signer.py` | `async def sign_archive(archive_path: str, signer: HMACSigner &#124; RSASigner, output_sig_path: str &#124; None = None) -> str` | Sign a modelpack archive and write signature file. |
| `verify_archive` | `aquilia/mlops/pack/signer.py` | `async def verify_archive(archive_path: str, sig_path: str, signer: HMACSigner &#124; RSASigner) -> bool` | Verify a modelpack archive against its signature file. |
| `generate_ci_workflow` | `aquilia/mlops/release/ci.py` | `def generate_ci_workflow(output_dir: str = '.github/workflows') -> str` | Generate GitHub Actions workflow file. |
| `generate_dockerfile` | `aquilia/mlops/release/ci.py` | `def generate_dockerfile(output_dir: str = '.') -> str` | Generate Dockerfile for model serving. |
| `select_runtime` | `aquilia/mlops/runtime/base.py` | `def select_runtime(manifest: ModelpackManifest, preferred: str &#124; None = None, gpu_available: bool = False) -> BaseRuntime` | Select the best runtime for the given manifest. |
| `register_mlops_middleware` | `aquilia/mlops/serving/middleware.py` | `def register_mlops_middleware(stack: MiddlewareStack, metrics_collector: Any = None, rate_limiter: Any = None, circuit_breaker: Any = None, fault_engine: Any = None, path_prefix: str = '/mlops') -> None` | Register all MLOps middleware with proper scope and priority |
| `mlops_metrics_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_metrics_middleware(metrics_collector: Any, path_prefix: str = '/mlops') -> Callable` | Create an inference metrics middleware. |
| `mlops_request_id_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_request_id_middleware() -> Callable` | Middleware that injects a unique request ID into the context. |
| `mlops_rate_limit_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_rate_limit_middleware(rate_limiter: Any, path_prefix: str = '/mlops', status_code: int = 429, fault_engine: Any = None) -> Callable` | Rate-limiting middleware using a token-bucket rate limiter. |
| `mlops_circuit_breaker_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_circuit_breaker_middleware(circuit_breaker: Any, path_prefix: str = '/mlops/predict', status_code: int = 503, fault_engine: Any = None) -> Callable` | Circuit-breaker middleware for inference endpoints. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `T` | `aquilia/mlops/_structures.py` | `TypeVar('T')` |
| `KT` | `aquilia/mlops/_structures.py` | `TypeVar('KT', bound=Hashable)` |
| `VT` | `aquilia/mlops/_structures.py` | `TypeVar('VT')` |
| `T` | `aquilia/mlops/api/model_class.py` | `TypeVar('T', bound='AquiliaModel')` |
| `F` | `aquilia/mlops/engine/hooks.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `_HOOK_ATTR` | `aquilia/mlops/engine/hooks.py` | `'__mlops_hook__'` |
| `_BUILTIN_PATTERNS` | `aquilia/mlops/explain/privacy.py` | `dict[PIIKind, re.Pattern]` |
| `MANIFEST_SCHEMA` | `aquilia/mlops/pack/manifest_schema.py` | `dict` |
| `ENTRYPOINT_GROUP` | `aquilia/mlops/plugins/host.py` | `'aquilia_mlops_plugin'` |
| `DEFAULT_INDEX_URL` | `aquilia/mlops/plugins/marketplace.py` | `'https://plugins.aquilia.dev/v1/index.json'` |
| `GITHUB_ACTIONS_WORKFLOW` | `aquilia/mlops/release/ci.py` | `'# Aquilia MLOps CI/CD Pipeline\n# Auto-generated by: aq ci generate\n\nname: Aquilia Model CI/CD\n\non:\n  push:\n    branches: [main, master]\n    paths:\n   ` |
| `DOCKERFILE_TEMPLATE` | `aquilia/mlops/release/ci.py` | `'# Aquilia Model Serving Container\n# Auto-generated by: aq ci generate\n\nFROM python:3.11-slim AS base\n\nWORKDIR /app\n\n# Install system deps\nRUN apt-get u` |
| `_TRANSITIONS` | `aquilia/mlops/runtime/base.py` | `dict[ModelState, set]` |
| `T` | `aquilia/mlops/runtime/executor.py` | `TypeVar('T')` |
| `VIEWER` | `aquilia/mlops/security/rbac.py` | `Role(name='viewer', permissions={Permission.PACK_READ}, description='Read-only access to modelpacks')` |
| `DEVELOPER` | `aquilia/mlops/security/rbac.py` | `Role(name='developer', permissions={Permission.PACK_READ, Permission.PACK_WRITE, Permission.PACK_SIGN}, description='Read/write access to modelpacks')` |
| `DEPLOYER` | `aquilia/mlops/security/rbac.py` | `Role(name='deployer', permissions={Permission.PACK_READ, Permission.PACK_PROMOTE, Permission.ROLLOUT_MANAGE}, description='Deploy and manage rollouts')` |
| `ADMIN` | `aquilia/mlops/security/rbac.py` | `Role(name='admin', permissions=set(Permission), description='Full registry administration')` |
| `BUILTIN_ROLES` | `aquilia/mlops/security/rbac.py` | `{r.name: r for r in [VIEWER, DEVELOPER, DEPLOYER, ADMIN]}` |

## Detailed Classes And Methods

### Class: `RingBuffer`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[T]`
- Summary: Fixed-capacity circular buffer backed by a pre-allocated list.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `append` | `def append(self, value: T) -> None` |  | Method. |
| `extend` | `def extend(self, values: Sequence[T]) -> None` |  | Method. |
| `clear` | `def clear(self) -> None` |  | Method. |
| `capacity` | `def capacity(self) -> int` | property | Method. |
| `last` | `def last(self) -> T` |  | Return the most recently appended element. |
| `to_list` | `def to_list(self) -> list[T]` |  | Method. |
| `percentile` | `def percentile(self, p: float) -> float` |  | Compute the *p*-th percentile (0-100) over numeric elements. |

### Class: `LRUCache`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[KT, VT]`
- Summary: O(1) get / put / evict cache backed by :class:`OrderedDict`.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: KT, default: VT &#124; None = None) -> VT &#124; None` |  | Method. |
| `put` | `def put(self, key: KT, value: VT) -> None` |  | Method. |
| `invalidate` | `def invalidate(self, key: KT) -> bool` |  | Method. |
| `clear` | `def clear(self) -> None` |  | Method. |
| `hit_rate` | `def hit_rate(self) -> float` | property | Method. |
| `stats` | `def stats(self) -> dict[str, Any]` | property | Method. |

### Class: `AtomicCounter`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Thread-safe monotonic counter (integers only).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `inc` | `def inc(self, n: int = 1) -> int` |  | Method. |
| `dec` | `def dec(self, n: int = 1) -> int` |  | Method. |
| `value` | `def value(self) -> int` | property | Method. |
| `reset` | `def reset(self, to: int = 0) -> None` |  | Method. |

### Class: `ExponentialDecay`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: EWMA (Exponentially Weighted Moving Average).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `update` | `def update(self, sample: float) -> float` |  | Method. |
| `value` | `def value(self) -> float` | property | Method. |
| `reset` | `def reset(self) -> None` |  | Method. |

### Class: `SlidingWindow`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Time-bucketed sliding window for rate/latency tracking.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, value: float = 1.0, *, ts: float &#124; None = None) -> None` |  | Method. |
| `count` | `def count(self, *, ts: float &#124; None = None) -> int` |  | Method. |
| `total` | `def total(self, *, ts: float &#124; None = None) -> float` |  | Method. |
| `rate` | `def rate(self, *, ts: float &#124; None = None) -> float` |  | Events per second over the window. |
| `mean` | `def mean(self, *, ts: float &#124; None = None) -> float` |  | Method. |
| `clear` | `def clear(self) -> None` |  | Method. |

### Class: `TopKHeap`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[KT]`
- Summary: Maintains the top-K elements by score using a dict + sort-on-read

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `push` | `def push(self, key: KT, score: float) -> None` |  | Method. |
| `top` | `def top(self) -> list[tuple[KT, float]]` |  | Method. |

### Class: `BloomFilter`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Space-efficient probabilistic set for fast negative lookups.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, item: str) -> None` |  | Method. |
| `size_bytes` | `def size_bytes(self) -> int` | property | Method. |
| `clear` | `def clear(self) -> None` |  | Method. |

### Class: `ConsistentHash`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Jump-consistent hash for sticky model-to-node routing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `bucket` | `def bucket(self, key: str) -> int` |  | Method. |
| `add_bucket` | `def add_bucket(self) -> int` |  | Method. |
| `remove_bucket` | `def remove_bucket(self) -> int` |  | Method. |
| `num_buckets` | `def num_buckets(self) -> int` | property | Method. |

### Class: `LineageNode`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single node in the model lineage graph.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_id` | `str` |  |
| `version` | `str` |  |
| `framework` | `str` | `''` |
| `created_at` | `float` | `field(default_factory=time.time)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `parents` | `list[str]` | `field(default_factory=list)` |
| `children` | `list[str]` | `field(default_factory=list)` |

### Class: `ModelLineageDAG`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Directed acyclic graph tracking model derivation relationships.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_model` | `def add_model(self, model_id: str, version: str, *, framework: str = '', parents: list[str] &#124; None = None, metadata: dict[str, Any] &#124; None = None) -> LineageNode` |  | Method. |
| `ancestors` | `def ancestors(self, model_id: str) -> list[str]` |  | All transitive ancestors (BFS). |
| `descendants` | `def descendants(self, model_id: str) -> list[str]` |  | All transitive descendants (BFS). |
| `path` | `def path(self, from_id: str, to_id: str) -> list[str] &#124; None` |  | Find shortest derivation path from ``from_id`` -> ``to_id``. |
| `roots` | `def roots(self) -> list[str]` |  | Models with no parents (base models). |
| `leaves` | `def leaves(self) -> list[str]` |  | Models with no children (leaf / production models). |
| `get` | `def get(self, model_id: str) -> LineageNode &#124; None` |  | Method. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialise the full DAG for storage / visualisation. |

### Class: `ExperimentArm`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: One arm of an A/B experiment.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `model_version` | `str` |  |
| `weight` | `float` | `0.5` |
| `metrics` | `dict[str, float]` | `field(default_factory=dict)` |
| `request_count` | `int` | `0` |

### Class: `Experiment`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A/B experiment definition.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `experiment_id` | `str` |  |
| `description` | `str` | `''` |
| `arms` | `list[ExperimentArm]` | `field(default_factory=list)` |
| `status` | `str` | `'active'` |
| `created_at` | `float` | `field(default_factory=time.time)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `ExperimentLedger`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Records A/B experiment assignments and collects per-arm metrics.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create` | `def create(self, experiment_id: str, *, description: str = '', arms: list[dict[str, Any]] &#124; None = None, metadata: dict[str, Any] &#124; None = None) -> Experiment` |  | Method. |
| `assign` | `def assign(self, experiment_id: str, request_id: str) -> str` |  | Deterministically assign a request to an experiment arm. |
| `record` | `def record(self, experiment_id: str, arm_name: str, metric: str, value: float) -> None` |  | Record a metric observation for an experiment arm (running average). |
| `get` | `def get(self, experiment_id: str) -> Experiment &#124; None` |  | Method. |
| `list_active` | `def list_active(self) -> list[Experiment]` |  | Method. |
| `conclude` | `def conclude(self, experiment_id: str, winner: str = '') -> None` |  | Mark experiment as completed, optionally recording the winning arm. |
| `pause` | `def pause(self, experiment_id: str) -> None` |  | Method. |
| `resume` | `def resume(self, experiment_id: str) -> None` |  | Method. |
| `summary` | `def summary(self, experiment_id: str) -> dict[str, Any]` |  | Get experiment summary with per-arm metrics. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `CircuitBreaker`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Three-state circuit breaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `state` | `def state(self) -> str` | property | Method. |
| `allow_request` | `def allow_request(self) -> bool` |  | Check if a request should be allowed through. |
| `record_success` | `def record_success(self) -> None` |  | Record a successful request. |
| `record_failure` | `def record_failure(self) -> None` |  | Record a failed request. |
| `reset` | `def reset(self) -> None` |  | Force reset to closed state. |
| `force_open` | `def force_open(self) -> None` |  | Force the circuit breaker into OPEN state (reject all requests). |
| `force_close` | `def force_close(self) -> None` |  | Force the circuit breaker into CLOSED state (allow all requests). |
| `force_half_open` | `def force_half_open(self) -> None` |  | Force the circuit breaker into HALF_OPEN state (limited probes). |
| `stats` | `def stats(self) -> dict[str, Any]` | property | Method. |

### Class: `TokenBucketRateLimiter`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Token-bucket rate limiter for inference request throttling.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `acquire` | `def acquire(self, tokens: int = 1) -> bool` |  | Try to consume tokens. Returns True if allowed. |
| `acquire_wait_time` | `def acquire_wait_time(self, tokens: int = 1) -> float` |  | Return seconds to wait before tokens become available, 0 if available now. |
| `available` | `def available(self) -> float` | property | Method. |
| `stats` | `def stats(self) -> dict[str, Any]` | property | Method. |
| `reset` | `def reset(self) -> None` |  | Method. |

### Class: `AdaptiveBatchQueue`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[T]`
- Summary: Priority-aware batch queue with adaptive sizing for LLM serving.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `put` | `def put(self, item: T, priority: int = 0, token_estimate: int = 1) -> bool` |  | Enqueue an item. Returns False if queue is at capacity (backpressure). |
| `drain` | `def drain(self, max_items: int = 0, max_tokens: int = 0) -> list[T]` |  | Drain items from the queue respecting token budget and/or max items. |
| `peek_token_total` | `def peek_token_total(self) -> int` |  | Total estimated tokens currently in the queue. |
| `stats` | `def stats(self) -> dict[str, Any]` | property | Method. |

### Class: `MemoryTracker`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Tracks memory allocations for model serving with watermark alerts.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `allocate` | `def allocate(self, name: str, size_mb: int) -> bool` |  | Allocate memory for a model. Returns False if hard limit would be exceeded. |
| `release` | `def release(self, name: str) -> int` |  | Release memory for a model. Returns freed MB. |
| `current_usage_mb` | `def current_usage_mb(self) -> int` | property | Method. |
| `is_above_soft_limit` | `def is_above_soft_limit(self) -> bool` | property | Method. |
| `is_above_hard_limit` | `def is_above_hard_limit(self) -> bool` | property | Method. |
| `available_mb` | `def available_mb(self) -> int` | property | Method. |
| `largest_model` | `def largest_model(self) -> tuple[str, int] &#124; None` |  | Return the name and size of the largest allocated model. |
| `eviction_candidates` | `def eviction_candidates(self) -> list[tuple[str, int]]` |  | Return models sorted by size ascending (smallest first) for eviction. |
| `stats` | `def stats(self) -> dict[str, Any]` | property | Method. |

### Class: `DType`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Centralized DType system for Aquilia MLOps.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `FLOAT64` |  | `'float64'` |
| `FLOAT32` |  | `'float32'` |
| `FLOAT16` |  | `'float16'` |
| `BFLOAT16` |  | `'bfloat16'` |
| `INT64` |  | `'int64'` |
| `INT32` |  | `'int32'` |
| `INT16` |  | `'int16'` |
| `INT8` |  | `'int8'` |
| `UINT8` |  | `'uint8'` |
| `BOOL` |  | `'bool'` |
| `STRING` |  | `'string'` |
| `OBJECT` |  | `'object'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_floating` | `def is_floating(self) -> bool` | property | Method. |
| `is_integer` | `def is_integer(self) -> bool` | property | Method. |
| `itemsize` | `def itemsize(self) -> int` | property | Returns size in bytes. |
| `from_numpy` | `def from_numpy(cls, dtype: Any) -> DType` | classmethod | Convert numpy dtype to MLOps DType. |
| `from_torch` | `def from_torch(cls, dtype: Any) -> DType` | classmethod | Convert torch dtype to MLOps DType. |
| `to_torch` | `def to_torch(self) -> Any` |  | Convert to torch dtype. |
| `validate` | `def validate(self, value: Any) -> bool` |  | Runtime validation of a value against this DType. |

### Class: `Framework`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Supported ML frameworks.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PYTORCH` |  | `'pytorch'` |
| `TENSORFLOW` |  | `'tensorflow'` |
| `ONNX` |  | `'onnx'` |
| `SKLEARN` |  | `'sklearn'` |
| `XGBOOST` |  | `'xgboost'` |
| `LIGHTGBM` |  | `'lightgbm'` |
| `HUGGINGFACE` |  | `'huggingface'` |
| `VLLM` |  | `'vllm'` |
| `LLAMACPP` |  | `'llamacpp'` |
| `CTRANSFORMERS` |  | `'ctransformers'` |
| `CUSTOM` |  | `'custom'` |

### Class: `RuntimeKind`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Available runtime backends.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PYTHON` |  | `'python'` |
| `ONNXRUNTIME` |  | `'onnxruntime'` |
| `TRITON` |  | `'triton'` |
| `TORCHSERVE` |  | `'torchserve'` |
| `BENTOML` |  | `'bentoml'` |
| `VLLM` |  | `'vllm'` |
| `LLAMACPP` |  | `'llamacpp'` |
| `TGI` |  | `'tgi'` |

### Class: `QuantizePreset`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Quantization presets.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `MOBILE` |  | `'mobile'` |
| `EDGE` |  | `'edge'` |
| `FP16` |  | `'fp16'` |
| `BF16` |  | `'bf16'` |
| `INT8` |  | `'int8'` |
| `INT4` |  | `'int4'` |
| `DYNAMIC` |  | `'dynamic'` |
| `GGUF_Q4` |  | `'gguf_q4'` |
| `GGUF_Q5` |  | `'gguf_q5'` |
| `GGUF_Q8` |  | `'gguf_q8'` |
| `AWQ` |  | `'awq'` |
| `GPTQ` |  | `'gptq'` |

### Class: `ExportTarget`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Edge export targets.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `TFLITE` |  | `'tflite'` |
| `COREML` |  | `'coreml'` |
| `ONNX_QUANTIZED` |  | `'onnx-quantized'` |
| `TENSORRT` |  | `'tensorrt'` |
| `TVM` |  | `'tvm'` |
| `GGUF` |  | `'gguf'` |
| `CTRANSLATE2` |  | `'ctranslate2'` |

### Class: `BatchingStrategy`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Batching strategy modes.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SIZE` |  | `'size'` |
| `TIME` |  | `'time'` |
| `HYBRID` |  | `'hybrid'` |
| `CONTINUOUS` |  | `'continuous'` |
| `ADAPTIVE` |  | `'adaptive'` |

### Class: `RolloutStrategy`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Release rollout strategies.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CANARY` |  | `'canary'` |
| `AB_TEST` |  | `'ab_test'` |
| `SHADOW` |  | `'shadow'` |
| `BLUE_GREEN` |  | `'blue_green'` |
| `ROLLING` |  | `'rolling'` |

### Class: `DriftMethod`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Drift detection methods.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PSI` |  | `'psi'` |
| `KS_TEST` |  | `'ks_test'` |
| `DISTRIBUTION` |  | `'distribution'` |
| `EMBEDDING` |  | `'embedding'` |
| `PERPLEXITY` |  | `'perplexity'` |

### Class: `ModelType`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Model type classification for serving strategy selection.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CLASSICAL_ML` |  | `'classical_ml'` |
| `DEEP_LEARNING` |  | `'deep_learning'` |
| `SLM` |  | `'slm'` |
| `LLM` |  | `'llm'` |
| `VISION` |  | `'vision'` |
| `MULTIMODAL` |  | `'multimodal'` |
| `EMBEDDING` |  | `'embedding'` |
| `CUSTOM` |  | `'custom'` |

### Class: `InferenceMode`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Inference execution modes.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SYNC` |  | `'sync'` |
| `ASYNC` |  | `'async'` |
| `STREAMING` |  | `'streaming'` |
| `BATCH` |  | `'batch'` |

### Class: `DeviceType`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Compute device types.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CPU` |  | `'cpu'` |
| `CUDA` |  | `'cuda'` |
| `MPS` |  | `'mps'` |
| `NPU` |  | `'npu'` |
| `TPU` |  | `'tpu'` |
| `AUTO` |  | `'auto'` |

### Class: `CircuitState`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Circuit breaker states.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CLOSED` |  | `'closed'` |
| `OPEN` |  | `'open'` |
| `HALF_OPEN` |  | `'half_open'` |

### Class: `TensorSpec`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Describes a single tensor in the inference signature.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `dtype` | `DType` |  |
| `shape` | `list[Any]` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> TensorSpec` | classmethod | Method. |

### Class: `BlobRef`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Reference to a blob inside a modelpack.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `path` | `str` |  |
| `digest` | `str` |  |
| `size` | `int` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> BlobRef` | classmethod | Method. |

### Class: `Provenance`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Provenance metadata for reproducibility.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `git_sha` | `str` | `''` |
| `dataset_snapshot` | `str` | `''` |
| `dockerfile` | `str` | `''` |
| `build_timestamp` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> Provenance` | classmethod | Method. |

### Class: `LLMConfig`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configuration specific to LLM/SLM model serving.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_type` | `ModelType` | `ModelType.CUSTOM` |
| `max_seq_length` | `int` | `4096` |
| `max_new_tokens` | `int` | `2048` |
| `max_batch_tokens` | `int` | `32768` |
| `kv_cache_max_mb` | `int` | `2048` |
| `tensor_parallel` | `int` | `1` |
| `pipeline_parallel` | `int` | `1` |
| `dtype` | `str` | `'float16'` |
| `device` | `DeviceType` | `DeviceType.AUTO` |
| `trust_remote_code` | `bool` | `False` |
| `tokenizer_name` | `str` | `''` |
| `chat_template` | `str` | `''` |
| `rope_scaling` | `dict[str, Any] &#124; None` | `None` |
| `stop_sequences` | `list[str]` | `field(default_factory=list)` |
| `temperature` | `float` | `1.0` |
| `top_p` | `float` | `1.0` |
| `top_k` | `int` | `50` |
| `repetition_penalty` | `float` | `1.0` |
| `stream_chunk_size` | `int` | `1` |
| `prefix_caching` | `bool` | `True` |
| `speculative_decoding` | `bool` | `False` |
| `draft_model` | `str` | `''` |
| `draft_tokens` | `int` | `5` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> LLMConfig` | classmethod | Method. |

### Class: `ModelpackManifest`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete manifest for a modelpack artifact.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `framework` | `str` |  |
| `entrypoint` | `str` |  |
| `inputs` | `list[TensorSpec]` | `field(default_factory=list)` |
| `outputs` | `list[TensorSpec]` | `field(default_factory=list)` |
| `env_lock` | `str` | `'env.lock'` |
| `provenance` | `Provenance` | `field(default_factory=Provenance)` |
| `blobs` | `list[BlobRef]` | `field(default_factory=list)` |
| `created_at` | `str` | `''` |
| `signed_by` | `str` | `''` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `model_type` | `str` | `'custom'` |
| `llm_config` | `LLMConfig &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> ModelpackManifest` | classmethod | Method. |
| `content_digest` | `def content_digest(self) -> str` |  | Compute a content-addressable digest for this manifest. |
| `is_llm` | `def is_llm(self) -> bool` | property | Check if this manifest represents an LLM/SLM. |

### Class: `InferenceRequest`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single inference request.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` | `str` |  |
| `inputs` | `dict[str, Any]` |  |
| `parameters` | `dict[str, Any]` | `field(default_factory=dict)` |
| `timestamp` | `float` | `field(default_factory=time.time)` |
| `priority` | `int` | `0` |
| `stream` | `bool` | `False` |
| `max_tokens` | `int` | `0` |
| `timeout_ms` | `float` | `0.0` |

### Class: `InferenceResult`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of a single inference.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` | `str` |  |
| `outputs` | `dict[str, Any]` |  |
| `latency_ms` | `float` | `0.0` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `token_count` | `int` | `0` |
| `prompt_tokens` | `int` | `0` |
| `finish_reason` | `str` | `''` |

### Class: `StreamChunk`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A single chunk in a streaming inference response.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` | `str` |  |
| `token` | `str` |  |
| `token_id` | `int` | `0` |
| `is_finished` | `bool` | `False` |
| `finish_reason` | `str` | `''` |
| `cumulative_tokens` | `int` | `0` |
| `latency_ms` | `float` | `0.0` |

### Class: `BatchRequest`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Aggregated batch of inference requests.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `requests` | `list[InferenceRequest]` |  |
| `batch_id` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `size` | `def size(self) -> int` | property | Method. |
| `total_tokens` | `def total_tokens(self) -> int` | property | Estimate total token budget for LLM batches. |

### Class: `PlacementScore`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Score for scheduler placement decisions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `node_id` | `str` |  |
| `device_affinity` | `float` | `0.0` |
| `memory_fit` | `float` | `0.0` |
| `current_load` | `float` | `0.0` |
| `cold_start_cost` | `float` | `0.0` |
| `total` | `float` | `0.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compute` | `def compute(self, w1: float = 0.3, w2: float = 0.3, w3: float = 0.25, w4: float = 0.15) -> float` |  | Method. |

### Class: `RolloutConfig`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configuration for a traffic rollout.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `from_version` | `str` |  |
| `to_version` | `str` |  |
| `strategy` | `RolloutStrategy` | `RolloutStrategy.CANARY` |
| `percentage` | `int` | `10` |
| `metric` | `str` | `'latency_p95'` |
| `threshold` | `float` | `0.0` |
| `auto_rollback` | `bool` | `True` |
| `step_interval_seconds` | `int` | `300` |

### Class: `DriftReport`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of a drift detection analysis.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `method` | `DriftMethod` |  |
| `score` | `float` |  |
| `threshold` | `float` |  |
| `is_drifted` | `bool` |  |
| `feature_scores` | `dict[str, float]` | `field(default_factory=dict)` |
| `window_start` | `str` | `''` |
| `window_end` | `str` | `''` |

### Class: `CircuitBreakerConfig`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configuration for inference circuit breaker.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `failure_threshold` | `int` | `5` |
| `success_threshold` | `int` | `3` |
| `timeout_seconds` | `float` | `30.0` |
| `half_open_max_calls` | `int` | `3` |

### Class: `TokenUsage`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Token usage tracking for LLM inference.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `prompt_tokens` | `int` | `0` |
| `completion_tokens` | `int` | `0` |
| `total_tokens` | `int` | `0` |
| `tokens_per_second` | `float` | `0.0` |
| `time_to_first_token_ms` | `float` | `0.0` |
| `kv_cache_usage_mb` | `float` | `0.0` |

### Class: `StorageAdapter`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for blob storage backends.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes) -> str` |  | Store blob, return storage path. |
| `get_blob` | `async def get_blob(self, digest: str) -> bytes` |  | Retrieve blob by digest. |
| `has_blob` | `async def has_blob(self, digest: str) -> bool` |  | Check if blob exists. |
| `delete_blob` | `async def delete_blob(self, digest: str) -> None` |  | Delete blob. |
| `list_blobs` | `async def list_blobs(self) -> list[str]` |  | List all blob digests. |

### Class: `Runtime`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for model runtime backends.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` |  | Prepare runtime with modelpack artifacts. |
| `load` | `async def load(self) -> None` |  | Load model into memory. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` |  | Run inference on a batch. |
| `health` | `async def health(self) -> dict[str, Any]` |  | Health check. |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Collect runtime metrics. |
| `unload` | `async def unload(self) -> None` |  | Unload model and free resources. |

### Class: `StreamingRuntime`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for runtimes that support streaming inference (LLMs).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` |  | Method. |
| `load` | `async def load(self) -> None` |  | Method. |
| `unload` | `async def unload(self) -> None` |  | Method. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` |  | Non-streaming inference. |
| `stream_infer` | `async def stream_infer(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]` |  | Stream tokens one at a time. |
| `health` | `async def health(self) -> dict[str, Any]` |  | Method. |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Method. |
| `token_usage` | `async def token_usage(self) -> TokenUsage` |  | Return current token usage stats. |
| `memory_info` | `async def memory_info(self) -> dict[str, Any]` |  | Return memory/device usage info. |

### Class: `PluginHook`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for plugin lifecycle hooks.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_load` | `async def on_load(self, context: dict[str, Any]) -> None` |  | Method. |
| `on_prepare` | `async def on_prepare(self, manifest: ModelpackManifest) -> None` |  | Method. |
| `on_infer` | `async def on_infer(self, batch: BatchRequest, results: list[InferenceResult]) -> None` |  | Method. |
| `on_stream_chunk` | `async def on_stream_chunk(self, chunk: StreamChunk) -> None` |  | Method. |
| `on_unload` | `async def on_unload(self) -> None` |  | Method. |

### Class: `TensorSpecBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates and renders tensor specifications.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `TextFacet(max_length=128)` |
| `dtype` |  | `TextFacet(max_length=32)` |
| `shape` |  | `ListFacet(required=True)` |

### Class: `BlobRefBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates blob references.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `path` |  | `TextFacet(max_length=512)` |
| `digest` |  | `TextFacet(max_length=128)` |
| `size` |  | `IntFacet(min_value=0)` |

### Class: `ProvenanceBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates provenance metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `git_sha` |  | `TextFacet(max_length=64, required=False, default='')` |
| `dataset_snapshot` |  | `TextFacet(max_length=256, required=False, default='')` |
| `dockerfile` |  | `TextFacet(max_length=256, required=False, default='')` |
| `build_timestamp` |  | `TextFacet(max_length=64, required=False, default='')` |

### Class: `ModelpackManifestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Full manifest blueprint with deep validation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `TextFacet(max_length=256)` |
| `version` |  | `TextFacet(max_length=64)` |
| `framework` |  | `ChoiceFacet(choices=[f.value for f in Framework], required=False, default='custom')` |
| `entrypoint` |  | `TextFacet(max_length=256, required=False, default='')` |
| `env_lock` |  | `TextFacet(max_length=128, required=False, default='env.lock')` |
| `created_at` |  | `TextFacet(required=False, default='')` |
| `signed_by` |  | `TextFacet(max_length=256, required=False, default='')` |
| `metadata` |  | `DictFacet(required=False, default=dict)` |

### Class: `InferenceRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates incoming inference request payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` |  | `TextFacet(max_length=128)` |
| `inputs` |  | `DictFacet(required=True)` |
| `parameters` |  | `DictFacet(required=False, default=dict)` |

### Class: `InferenceResultBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders inference results for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` |  | `ReadOnly()` |
| `outputs` |  | `DictFacet()` |
| `latency_ms` |  | `FloatFacet(min_value=0.0)` |
| `metadata` |  | `DictFacet(required=False, default=dict)` |

### Class: `DriftReportBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders drift detection reports.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `method` |  | `ChoiceFacet(choices=[m.value for m in DriftMethod])` |
| `score` |  | `FloatFacet()` |
| `threshold` |  | `FloatFacet()` |
| `is_drifted` |  | `BoolFacet()` |
| `feature_scores` |  | `DictFacet(required=False, default=dict)` |
| `window_start` |  | `TextFacet(required=False, default='')` |
| `window_end` |  | `TextFacet(required=False, default='')` |

### Class: `RolloutConfigBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates rollout configuration payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `from_version` |  | `TextFacet(max_length=64)` |
| `to_version` |  | `TextFacet(max_length=64)` |
| `strategy` |  | `ChoiceFacet(choices=[s.value for s in RolloutStrategy], required=False, default='canary')` |
| `percentage` |  | `IntFacet(min_value=0, max_value=100, required=False, default=10)` |
| `metric` |  | `TextFacet(max_length=64, required=False, default='latency_p95')` |
| `threshold` |  | `FloatFacet(required=False, default=0.0)` |
| `auto_rollback` |  | `BoolFacet(required=False, default=True)` |
| `step_interval_seconds` |  | `IntFacet(min_value=1, required=False, default=300)` |

### Class: `RolloutStateBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders rollout state for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` |  | `ReadOnly()` |
| `phase` |  | `ReadOnly()` |
| `current_percentage` |  | `IntFacet()` |
| `steps_completed` |  | `IntFacet()` |
| `started_at` |  | `FloatFacet()` |
| `completed_at` |  | `FloatFacet()` |
| `error` |  | `TextFacet(required=False, default='')` |

### Class: `ScalingPolicyBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates autoscaler policy configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `min_replicas` |  | `IntFacet(min_value=0, required=False, default=1)` |
| `max_replicas` |  | `IntFacet(min_value=1, required=False, default=10)` |
| `target_concurrency` |  | `FloatFacet(min_value=0.1, required=False, default=10.0)` |
| `target_latency_p95_ms` |  | `FloatFacet(min_value=0.0, required=False, default=100.0)` |
| `scale_up_threshold` |  | `FloatFacet(min_value=0.0, max_value=1.0, required=False, default=0.8)` |
| `scale_down_threshold` |  | `FloatFacet(min_value=0.0, max_value=1.0, required=False, default=0.3)` |
| `cooldown_seconds` |  | `IntFacet(min_value=0, required=False, default=60)` |

### Class: `NodeInfoBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates compute node registration payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `node_id` |  | `TextFacet(max_length=128)` |
| `device_type` |  | `ChoiceFacet(choices=['cpu', 'gpu', 'npu'], required=False, default='cpu')` |
| `total_memory_mb` |  | `FloatFacet(min_value=0.0, required=False, default=0.0)` |
| `available_memory_mb` |  | `FloatFacet(min_value=0.0, required=False, default=0.0)` |
| `current_load` |  | `FloatFacet(min_value=0.0, max_value=1.0, required=False, default=0.0)` |
| `gpu_available` |  | `BoolFacet(required=False, default=False)` |

### Class: `PlacementRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates model placement request payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` |  | `TextFacet(max_length=256)` |
| `model_size_mb` |  | `FloatFacet(min_value=0.0)` |
| `preferred_device` |  | `ChoiceFacet(choices=['cpu', 'gpu', 'npu', 'any'], required=False, default='any')` |
| `gpu_required` |  | `BoolFacet(required=False, default=False)` |

### Class: `PluginDescriptorBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders plugin descriptor for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `ReadOnly()` |
| `version` |  | `ReadOnly()` |
| `module` |  | `ReadOnly()` |
| `state` |  | `ReadOnly()` |
| `error` |  | `TextFacet(required=False, default='')` |
| `metadata` |  | `DictFacet(required=False, default=dict)` |

### Class: `MetricsSummaryBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders metrics summary for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` |  | `ReadOnly()` |
| `model_version` |  | `ReadOnly()` |

### Class: `LLMConfigBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates LLM configuration payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `max_tokens` |  | `IntFacet(min_value=1, required=False, default=512)` |
| `temperature` |  | `FloatFacet(min_value=0.0, max_value=2.0, required=False, default=1.0)` |
| `top_k` |  | `IntFacet(min_value=1, required=False, default=50)` |
| `top_p` |  | `FloatFacet(min_value=0.0, max_value=1.0, required=False, default=1.0)` |
| `repetition_penalty` |  | `FloatFacet(min_value=0.0, required=False, default=1.0)` |
| `stop_sequences` |  | `ListFacet(required=False, default=list)` |
| `context_length` |  | `IntFacet(min_value=1, required=False, default=2048)` |
| `dtype` |  | `TextFacet(max_length=16, required=False, default='float16')` |
| `device_map` |  | `TextFacet(max_length=32, required=False, default='auto')` |
| `quantize` |  | `ChoiceFacet(choices=[q.value for q in QuantizePreset], required=False, default='none')` |
| `trust_remote_code` |  | `BoolFacet(required=False, default=False)` |

### Class: `StreamChunkBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders a single streaming token/chunk for SSE responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` |  | `ReadOnly()` |
| `token` |  | `TextFacet(required=False, default='')` |
| `token_index` |  | `IntFacet(min_value=0)` |
| `finish_reason` |  | `TextFacet(required=False, default='')` |
| `logprob` |  | `FloatFacet(required=False)` |

### Class: `TokenUsageBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders token usage statistics for LLM inference.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `prompt_tokens` |  | `IntFacet(min_value=0)` |
| `completion_tokens` |  | `IntFacet(min_value=0)` |
| `total_tokens` |  | `IntFacet(min_value=0)` |

### Class: `LLMInferenceRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates incoming LLM inference request payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` |  | `TextFacet(max_length=128)` |
| `inputs` |  | `DictFacet(required=True)` |
| `parameters` |  | `DictFacet(required=False, default=dict)` |
| `priority` |  | `IntFacet(min_value=0, max_value=10, required=False, default=5)` |
| `stream` |  | `BoolFacet(required=False, default=False)` |
| `max_tokens` |  | `IntFacet(min_value=1, required=False, default=512)` |
| `timeout_ms` |  | `FloatFacet(min_value=0.0, required=False, default=30000.0)` |
| `temperature` |  | `FloatFacet(min_value=0.0, max_value=2.0, required=False, default=1.0)` |
| `top_k` |  | `IntFacet(min_value=1, required=False, default=50)` |

### Class: `LLMInferenceResultBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders LLM inference results including token metrics.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` |  | `ReadOnly()` |
| `outputs` |  | `DictFacet()` |
| `latency_ms` |  | `FloatFacet(min_value=0.0)` |
| `token_count` |  | `IntFacet(min_value=0, required=False, default=0)` |
| `prompt_tokens` |  | `IntFacet(min_value=0, required=False, default=0)` |
| `finish_reason` |  | `TextFacet(required=False, default='')` |
| `metadata` |  | `DictFacet(required=False, default=dict)` |
| `usage` |  | `DictFacet(required=False, default=dict)` |

### Class: `ChatMessageBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates a single chat message.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `role` |  | `ChoiceFacet(choices=['system', 'user', 'assistant', 'function'], required=True)` |
| `content` |  | `TextFacet(required=True)` |
| `name` |  | `TextFacet(max_length=64, required=False, default='')` |

### Class: `ChatRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates chat-style LLM request payloads.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `messages` |  | `ListFacet(required=True)` |
| `model` |  | `TextFacet(max_length=256, required=False, default='')` |
| `stream` |  | `BoolFacet(required=False, default=False)` |
| `max_tokens` |  | `IntFacet(min_value=1, required=False, default=512)` |
| `temperature` |  | `FloatFacet(min_value=0.0, max_value=2.0, required=False, default=1.0)` |
| `top_k` |  | `IntFacet(min_value=1, required=False, default=50)` |
| `top_p` |  | `FloatFacet(min_value=0.0, max_value=1.0, required=False, default=1.0)` |
| `stop` |  | `ListFacet(required=False, default=list)` |

### Class: `ChatResponseBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders chat-style LLM response.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` |  | `ReadOnly()` |
| `model` |  | `ReadOnly()` |
| `choices` |  | `ListFacet()` |
| `usage` |  | `DictFacet(required=False, default=dict)` |
| `created` |  | `FloatFacet(required=False)` |

### Class: `CircuitBreakerStatusBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders circuit breaker state for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `state` |  | `ChoiceFacet(choices=['closed', 'open', 'half_open'])` |
| `failure_count` |  | `IntFacet(min_value=0)` |
| `success_count` |  | `IntFacet(min_value=0)` |
| `total_requests` |  | `IntFacet(min_value=0)` |
| `total_rejections` |  | `IntFacet(min_value=0)` |
| `last_failure_time` |  | `FloatFacet(required=False, default=0.0)` |

### Class: `RateLimiterStatusBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders rate limiter state for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `rate_rps` |  | `FloatFacet(min_value=0.0)` |
| `capacity` |  | `IntFacet(min_value=0)` |
| `available_tokens` |  | `FloatFacet(min_value=0.0)` |

### Class: `MemoryStatusBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders memory tracker state for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `current_mb` |  | `FloatFacet(min_value=0.0)` |
| `soft_limit_mb` |  | `FloatFacet(min_value=0.0)` |
| `hard_limit_mb` |  | `FloatFacet(min_value=0.0)` |
| `utilization_pct` |  | `FloatFacet(min_value=0.0, max_value=100.0)` |
| `exceeds_soft` |  | `BoolFacet()` |
| `exceeds_hard` |  | `BoolFacet()` |

### Class: `ModelCapabilitiesBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders model capabilities for API responses.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` |  | `ReadOnly()` |
| `model_type` |  | `ChoiceFacet(choices=[t.value for t in ModelType], required=False, default='SLM')` |
| `supports_streaming` |  | `BoolFacet(required=False, default=False)` |
| `supports_chat` |  | `BoolFacet(required=False, default=False)` |
| `inference_modes` |  | `ListFacet(required=False, default=list)` |
| `device` |  | `TextFacet(required=False, default='cpu')` |
| `max_context_length` |  | `IntFacet(min_value=0, required=False, default=0)` |

### Class: `AquiliaModel`

- Source: `aquilia/mlops/api/model_class.py`
- Bases: `object`
- Summary: Base class for Aquilia ML models.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `async def load(self, artifacts_dir: str, device: str) -> None` |  | Load model weights / artifacts into memory. |
| `unload` | `async def unload(self) -> None` |  | Release model resources. Called during shutdown or hot reload. |
| `predict` | `async def predict(self, inputs: dict[str, Any]) -> dict[str, Any]` |  | Run inference on preprocessed inputs. |
| `preprocess` | `async def preprocess(self, inputs: dict[str, Any]) -> dict[str, Any]` |  | Transform raw inputs before prediction. |
| `postprocess` | `async def postprocess(self, outputs: dict[str, Any]) -> dict[str, Any]` |  | Transform prediction outputs before returning to client. |
| `health` | `async def health(self) -> dict[str, Any]` |  | Custom health check. |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Custom metrics. |

### Class: `RouteDefinition`

- Source: `aquilia/mlops/api/route_generator.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A generated route definition ready for controller compilation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `method` | `str` |  |
| `path` | `str` |  |
| `handler` | `Callable` |  |
| `model_name` | `str` | `''` |
| `description` | `str` | `''` |

### Class: `RouteGenerator`

- Source: `aquilia/mlops/api/route_generator.py`
- Bases: `object`
- Summary: Generates HTTP route definitions from registered models.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate` | `def generate(self) -> list[RouteDefinition]` |  | Generate all route definitions for all registered models. |
| `route_table` | `def route_table(self) -> list[dict[str, str]]` |  | Return a human-readable route table. |

### Class: `MLOpsConfig`

- Source: `aquilia/mlops/di/providers.py`
- Bases: `object`
- Summary: Typed configuration for MLOps DI registration.

### Class: `MLOpsFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `Fault`
- Summary: Base fault for all MLOps operations.

### Class: `PackFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for model packaging.

### Class: `PackBuildFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PackFault`
- Summary: Model pack build failed.

### Class: `PackIntegrityFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PackFault`
- Summary: Blob integrity check failed (SHA-256 mismatch) or structural issue.

### Class: `PackSignatureFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PackFault`
- Summary: Artifact signature verification failed.

### Class: `RegistryFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for registry operations.

### Class: `RegistryConnectionFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RegistryFault`
- Summary: Cannot connect to registry backend.

### Class: `PackNotFoundFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RegistryFault`
- Summary: Requested modelpack not found in registry.

### Class: `ImmutabilityViolationFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RegistryFault`
- Summary: Attempted to overwrite an immutable artifact.

### Class: `ServingFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for model serving.

### Class: `RuntimeLoadFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Model failed to load into runtime.

### Class: `InferenceFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Inference failed for a request.

### Class: `BatchTimeoutFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Batch processing exceeded deadline.

### Class: `WarmupFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Model warm-up failed.

### Class: `ObserveFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for observability.

### Class: `DriftDetectionFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ObserveFault`
- Summary: Drift detection computation failed.

### Class: `MetricsExportFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ObserveFault`
- Summary: Metrics export/scrape failed.

### Class: `RolloutFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for release management.

### Class: `RolloutAdvanceFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RolloutFault`
- Summary: Rollout advancement failed due to metric degradation.

### Class: `AutoRollbackFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RolloutFault`
- Summary: Automatic rollback triggered.

### Class: `SchedulerFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for scheduling.

### Class: `PlacementFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `SchedulerFault`
- Summary: No suitable node found for model placement.

### Class: `ScalingFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `SchedulerFault`
- Summary: Scaling operation failed.

### Class: `MLOpsSecurityFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for MLOps security.

### Class: `SigningFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsSecurityFault`
- Summary: Artifact signing failed.

### Class: `PermissionDeniedFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsSecurityFault`
- Summary: User lacks required RBAC permission.

### Class: `EncryptionFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsSecurityFault`
- Summary: Encryption / decryption operation failed.

### Class: `PluginFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for plugin operations.

### Class: `PluginLoadFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PluginFault`
- Summary: Plugin failed to load.

### Class: `PluginHookFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PluginFault`
- Summary: Plugin hook execution failed.

### Class: `CircuitBreakerFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for circuit breaker events.

### Class: `CircuitBreakerOpenFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `CircuitBreakerFault`
- Summary: Circuit breaker is OPEN -- requests are being rejected.

### Class: `CircuitBreakerExhaustedFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `CircuitBreakerFault`
- Summary: Circuit breaker half-open probe failed -- returning to OPEN state.

### Class: `RateLimitFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Request rejected due to rate limiting.

### Class: `StreamingFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for streaming inference.

### Class: `StreamInterruptedFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `StreamingFault`
- Summary: Streaming generation was interrupted (client disconnect, timeout, etc.).

### Class: `TokenLimitExceededFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `StreamingFault`
- Summary: Token generation exceeded max_tokens limit.

### Class: `MemoryFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for memory management.

### Class: `MemorySoftLimitFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MemoryFault`
- Summary: Memory usage crossed soft limit -- eviction candidates available.

### Class: `MemoryHardLimitFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MemoryFault`
- Summary: Memory usage crossed hard limit -- requests must be rejected.

### Class: `HookRegistry`

- Source: `aquilia/mlops/engine/hooks.py`
- Bases: `object`
- Summary: Collected hooks from a model class.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, kind: str) -> list[Callable]` |  | Get hooks by kind name. |
| `has` | `def has(self, kind: str) -> bool` |  | Check if any hooks of this kind are registered. |
| `summary` | `def summary(self) -> dict[str, int]` |  | Return counts of registered hooks per kind. |

### Class: `MLOpsManifest`

- Source: `aquilia/mlops/engine/module.py`
- Bases: `object`
- Summary: Aquilary-compatible manifest for the MLOps subsystem.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `'mlops'` |
| `version` |  | `'1.0.0'` |
| `description` |  | `'Aquilia MLOps Platform -- model packaging, registry, serving & observability'` |
| `depends_on` | `list[str]` | `[]` |
| `controllers` | `list[str]` | `['aquilia.mlops.serving.controllers.MLOpsController']` |
| `services` | `list[str]` | `['aquilia.mlops.registry.service.RegistryService', 'aquilia.mlops.observe.metrics.MetricsCollector', 'aquilia.mlops.observe.drift.DriftDetector', 'aquilia.mlops.observe.logger.PredictionLogger', 'aquilia.mlops.serving.server.ModelServingServer', 'aquilia.mlops.serving.batching.DynamicBatcher', 'aquilia.mlops.plugins.host.PluginHost', 'aquilia.mlops.release.rollout.RolloutEngine', 'aquilia.mlops.scheduler.autoscaler.Autoscaler', 'aquilia.mlops.scheduler.placement.PlacementScheduler', 'aquilia.mlops.security.rbac.RBACManager', 'aquilia.mlops.security.signing.ArtifactSigner', 'aquilia.mlops.security.encryption.EncryptionManager', 'aquilia.mlops._structures.CircuitBreaker', 'aquilia.mlops._structures.TokenBucketRateLimiter', 'aquilia.mlops._structures.MemoryTracker']` |
| `effects` | `list[str]` | `['CacheEffect:mlops', 'CacheEffect:mlops.registry']` |
| `fault_domains` | `list[str]` | `['mlops', 'mlops.pack', 'mlops.registry', 'mlops.serving', 'mlops.observe', 'mlops.release', 'mlops.scheduler', 'mlops.security', 'mlops.plugin', 'mlops.resilience', 'mlops.streaming', 'mlops.memory']` |
| `middleware` | `list[tuple[str, dict]]` | `[('aquilia.mlops.serving.middleware.mlops_request_id_middleware', {'scope': 'app:mlops', 'priority': 5}), ('aquilia.mlops.serving.middleware.mlops_rate_limit_middleware', {'scope': 'app:mlops', 'priority': 10}), ('aquilia.mlops.serving.middleware.mlops_circuit_breaker_middleware', {'scope': 'app:mlops', 'priority': 20}), ('aquilia.mlops.serving.middleware.mlops_metrics_middleware', {'scope': 'app:mlops', 'priority': 30})]` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `on_startup` | `async def on_startup(config: dict[str, Any] &#124; None = None, **kwargs: Any) -> None` | staticmethod | Method. |
| `on_shutdown` | `async def on_shutdown(**kwargs: Any) -> None` | staticmethod | Method. |

### Class: `PipelineContext`

- Source: `aquilia/mlops/engine/pipeline.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Per-request context flowing through the pipeline.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request_id` | `str` |  |
| `model_name` | `str` | `''` |
| `model_version` | `str` | `''` |
| `trace_id` | `str` | `''` |
| `start_time` | `float` | `field(default_factory=time.monotonic)` |
| `stage_timings` | `dict[str, float]` | `field(default_factory=dict)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `InferencePipeline`

- Source: `aquilia/mlops/engine/pipeline.py`
- Bases: `object`
- Summary: Async inference pipeline with hooks and metrics.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `execute` | `async def execute(self, request: InferenceRequest, model_name: str = '', model_version: str = '') -> InferenceResult` |  | Execute the full inference pipeline for a single request. |
| `execute_batch` | `async def execute_batch(self, requests: list[InferenceRequest], model_name: str = '', model_version: str = '') -> list[InferenceResult]` |  | Execute the pipeline for multiple requests concurrently. |

### Class: `ExplainMethod`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `str, Enum`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `SHAP_KERNEL` |  | `'shap_kernel'` |
| `SHAP_TREE` |  | `'shap_tree'` |
| `SHAP_DEEP` |  | `'shap_deep'` |
| `LIME_TABULAR` |  | `'lime_tabular'` |
| `LIME_TEXT` |  | `'lime_text'` |
| `LIME_IMAGE` |  | `'lime_image'` |

### Class: `FeatureAttribution`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Single feature's contribution.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `value` | `float` |  |
| `base_value` | `float` |  |

### Class: `Explanation`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete explanation for one prediction.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `method` | `ExplainMethod` |  |
| `attributions` | `list[FeatureAttribution]` |  |
| `prediction` | `Any` | `None` |
| `extra` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `top_k` | `def top_k(self) -> list[FeatureAttribution]` | property | Top 10 features by absolute attribution. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `SHAPExplainer`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Summary: Wraps ``shap.KernelExplainer``, ``shap.TreeExplainer`` or

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `explain` | `def explain(self, instance: Any, **kwargs: Any) -> Explanation` |  | Compute SHAP values for *instance* (single row). |

### Class: `LIMEExplainer`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Summary: Wraps ``lime.lime_tabular.LimeTabularExplainer`` (default) or

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `explain` | `def explain(self, instance: Any, **kwargs: Any) -> Explanation` |  | Explain a single instance. |

### Class: `PIIKind`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `str, Enum`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `EMAIL` |  | `'email'` |
| `PHONE` |  | `'phone'` |
| `SSN` |  | `'ssn'` |
| `CREDIT_CARD` |  | `'credit_card'` |
| `IP_ADDRESS` |  | `'ip_address'` |
| `CUSTOM` |  | `'custom'` |

### Class: `PIIMatch`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Decorators: `dataclass`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `kind` | `PIIKind` |  |
| `start` | `int` |  |
| `end` | `int` |  |
| `text` | `str` |  |

### Class: `PIIRedactor`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Summary: Scans text for PII and replaces matches with a configurable placeholder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `scan` | `def scan(self, text: str) -> list[PIIMatch]` |  | Return all PII matches found in *text*. |
| `redact` | `def redact(self, text: str) -> str` |  | Return *text* with all PII replaced. |
| `redact_dict` | `def redact_dict(self, data: dict[str, Any]) -> dict[str, Any]` |  | Recursively redact string values in a dict. |

### Class: `LaplaceNoise`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Summary: Adds calibrated Laplace noise to numeric values.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_noise` | `def add_noise(self, value: float) -> float` |  | Return *value* + Laplace(0, scale). |
| `add_noise_array` | `def add_noise_array(self, values: Sequence[float]) -> list[float]` |  | Method. |

### Class: `InputSanitiser`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Summary: Pipeline of transforms applied to inference payloads before they

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_transform` | `def add_transform(self, fn: Callable[[dict[str, Any]], dict[str, Any]]) -> InputSanitiser` |  | Method. |
| `sanitise` | `def sanitise(self, payload: dict[str, Any]) -> dict[str, Any]` |  | Method. |
| `default` | `def default(cls) -> InputSanitiser` | classmethod | Pre-configured sanitiser with PII redaction. |

### Class: `ModelManifestEntry`

- Source: `aquilia/mlops/manifest/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configuration for a single model from the manifest.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `class_path` | `str` |  |
| `version` | `str` | `'v1'` |
| `device` | `str` | `'auto'` |
| `batch_size` | `int` | `16` |
| `max_batch_latency_ms` | `float` | `50.0` |
| `warmup_requests` | `int` | `0` |
| `workers` | `int` | `4` |
| `timeout_ms` | `float` | `30000.0` |
| `artifacts_dir` | `str` | `''` |
| `supports_streaming` | `bool` | `False` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve_class` | `def resolve_class(self) -> Any` |  | Import and return the model class from its dotted path. |
| `to_config_dict` | `def to_config_dict(self) -> dict[str, Any]` |  | Convert to a config dict for ModelRegistry.register(). |

### Class: `MLOpsManifestConfig`

- Source: `aquilia/mlops/manifest/config.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed ``[mlops]`` configuration from Aquilia workspace config.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `default_device` | `str` | `'auto'` |
| `default_workers` | `int` | `4` |
| `default_batch_size` | `int` | `16` |
| `default_max_batch_latency_ms` | `float` | `50.0` |
| `default_timeout_ms` | `float` | `30000.0` |
| `route_prefix` | `str` | `'/mlops'` |
| `models` | `list[ModelManifestEntry]` | `field(default_factory=list)` |

### Class: `ManifestValidationError`

- Source: `aquilia/mlops/manifest/schema.py`
- Bases: `ValueError`
- Summary: Raised when manifest validation fails.

### Class: `DriftDetector`

- Source: `aquilia/mlops/observe/drift.py`
- Bases: `object`
- Summary: Model drift detection engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `set_reference` | `def set_reference(self, data: dict[str, Sequence[float]]) -> None` |  | Set the reference (training) distribution. |
| `detect` | `def detect(self, current: dict[str, Sequence[float]], window_start: str = '', window_end: str = '') -> DriftReport` |  | Run drift detection against the reference distribution. |
| `check` | `def check(self, reference: Sequence[float], current: Sequence[float], feature_name: str = 'feature') -> DriftReport` |  | Quick single-feature drift check (no need to set reference first). |

### Class: `PredictionLogger`

- Source: `aquilia/mlops/observe/logger.py`
- Bases: `object`
- Summary: Logs feature/prediction pairs for monitoring, debugging, and retraining.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `set_sink` | `def set_sink(self, sink: Callable[[dict[str, Any]], None]) -> None` |  | Set a custom log sink function. |
| `log` | `def log(self, request: InferenceRequest, result: InferenceResult, *, force: bool = False) -> bool` |  | Log a request/result pair (subject to sampling). |
| `get_log_count` | `def get_log_count(self) -> int` |  | Method. |

### Class: `MetricPoint`

- Source: `aquilia/mlops/observe/metrics.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Single metric data point.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `value` | `float` |  |
| `labels` | `dict[str, str]` | `field(default_factory=dict)` |
| `timestamp` | `float` | `field(default_factory=time.time)` |

### Class: `MetricsCollector`

- Source: `aquilia/mlops/observe/metrics.py`
- Bases: `object`
- Summary: In-process metrics collector with Prometheus text format export.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `total_inferences` | `def total_inferences(self) -> int` | property | Total number of inference requests processed. |
| `total_tokens` | `def total_tokens(self) -> int` | property | Total tokens generated across all requests. |
| `inc` | `def inc(self, name: str, value: float = 1.0) -> None` |  | Increment a counter. |
| `set_gauge` | `def set_gauge(self, name: str, value: float) -> None` |  | Set a gauge value. |
| `observe` | `def observe(self, name: str, value: float) -> None` |  | Record a histogram observation (bounded ring buffer). |
| `inc_for_model` | `def inc_for_model(self, model_name: str, name: str, value: float = 1.0) -> None` |  | Increment a counter scoped to a specific model. |
| `observe_for_model` | `def observe_for_model(self, model_name: str, name: str, value: float) -> None` |  | Record a histogram observation scoped to a specific model. |
| `model_summary` | `def model_summary(self, model_name: str) -> dict[str, Any]` |  | Get metrics summary scoped to a specific model. |
| `record_inference` | `def record_inference(self, latency_ms: float, batch_size: int = 1, error: bool = False, model_name: str = '', token_count: int = 0, prompt_tokens: int = 0, streaming: bool = False, time_to_first_token_ms: float = 0.0) -> None` |  | Record an inference event (convenience method). |
| `hot_models` | `def hot_models(self, k: int = 10) -> list` |  | Return the top-K most-active models. |
| `percentile` | `def percentile(self, name: str, p: float) -> float` |  | Compute p-th percentile for a histogram metric. |
| `ewma` | `def ewma(self, name: str) -> float` |  | Return the EWMA-smoothed value for a metric. |
| `get_summary` | `def get_summary(self) -> dict[str, Any]` |  | Get a summary of all metrics as a dict. |
| `to_prometheus` | `def to_prometheus(self) -> str` |  | Export all metrics in Prometheus text exposition format. |
| `reset` | `def reset(self) -> None` |  | Reset all metrics. |

### Class: `ExportResult`

- Source: `aquilia/mlops/optimizer/export.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of an edge export.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `target` | `str` |  |
| `output_path` | `str` |  |
| `size_bytes` | `int` |  |
| `notes` | `list[str]` |  |

### Class: `EdgeExporter`

- Source: `aquilia/mlops/optimizer/export.py`
- Bases: `object`
- Summary: Export models to edge-friendly formats.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `export` | `async def export(self, model_path: str, target: ExportTarget, output_dir: str = '.', optimize: bool = True) -> ExportResult` |  | Export model to edge target format. |

### Class: `OptimizationResult`

- Source: `aquilia/mlops/optimizer/pipeline.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of an optimization pass.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `original_size_bytes` | `int` |  |
| `optimized_size_bytes` | `int` |  |
| `original_path` | `str` |  |
| `optimized_path` | `str` |  |
| `preset` | `str` |  |
| `compression_ratio` | `float` | `0.0` |
| `notes` | `list[str]` | `None` |

### Class: `OptimizationPipeline`

- Source: `aquilia/mlops/optimizer/pipeline.py`
- Bases: `object`
- Summary: Runs a sequence of optimization passes on model files.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `run` | `async def run(self, model_path: str, preset: QuantizePreset = QuantizePreset.DYNAMIC, output_dir: str = '.') -> OptimizationResult` |  | Run optimization pipeline. |

### Class: `LoadedModel`

- Source: `aquilia/mlops/orchestrator/loader.py`
- Bases: `object`
- Summary: Container for a loaded model instance and its associated resources.

### Class: `ModelLoader`

- Source: `aquilia/mlops/orchestrator/loader.py`
- Bases: `object`
- Summary: Manages model instantiation, loading, unloading, and hot reload.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `ensure_loaded` | `async def ensure_loaded(self, name: str, version: str) -> LoadedModel` |  | Ensure a model is loaded and return its ``LoadedModel``. |
| `hot_reload` | `async def hot_reload(self, name: str, new_version: str) -> LoadedModel` |  | Hot-reload a model to a new version. |
| `unload` | `async def unload(self, name: str, version: str) -> bool` |  | Unload a specific model version. |
| `unload_all` | `async def unload_all(self) -> None` |  | Unload all loaded models (shutdown). |
| `is_loaded` | `def is_loaded(self, name: str, version: str) -> bool` |  | Check if a model version is currently loaded. |
| `get_loaded` | `def get_loaded(self, name: str, version: str) -> LoadedModel &#124; None` |  | Get a loaded model instance if available. |
| `loaded_models` | `def loaded_models(self) -> list[str]` |  | List all currently loaded model keys. |
| `summary` | `def summary(self) -> dict[str, Any]` |  | Summary for health endpoints. |

### Class: `ModelOrchestrator`

- Source: `aquilia/mlops/orchestrator/orchestrator.py`
- Bases: `object`
- Summary: Top-level inference façade.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `predict` | `async def predict(self, model_name: str, inputs: dict[str, Any], parameters: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, request_id: str = '') -> InferenceResult` |  | Run a prediction through the full orchestrated pipeline. |
| `predict_batch` | `async def predict_batch(self, model_name: str, batch_inputs: list[dict[str, Any]], parameters: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None) -> list[InferenceResult]` |  | Run batch predictions. |
| `stream_predict` | `async def stream_predict(self, model_name: str, inputs: dict[str, Any], parameters: dict[str, Any] &#124; None = None, headers: dict[str, str] &#124; None = None, request_id: str = '') -> AsyncIterator[StreamChunk]` |  | Stream inference for LLM models. |
| `get_health` | `async def get_health(self, model_name: str &#124; None = None) -> dict[str, Any]` |  | Get health status for one model or all models. |
| `get_metrics` | `async def get_metrics(self, model_name: str &#124; None = None) -> dict[str, Any]` |  | Get metrics for one model or all models. |
| `list_models` | `async def list_models(self) -> list[dict[str, Any]]` |  | List all registered models with their status. |
| `reload_model` | `async def reload_model(self, model_name: str, version: str) -> dict[str, Any]` |  | Hot-reload a model to a specific version. |
| `unload_model` | `async def unload_model(self, model_name: str, version: str &#124; None = None) -> bool` |  | Unload a specific model version. |
| `shutdown` | `async def shutdown(self) -> None` |  | Graceful shutdown -- unload all models. |

### Class: `ModelBundle`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A complete model bundle ready for persistence.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `weights_path` | `Path` |  |
| `metadata` | `dict[str, Any]` |  |
| `framework` | `str` |  |
| `dtype` | `str` |  |

### Class: `ModelLoader`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `abc.ABC`
- Summary: Abstract base class for framework-specific model loaders.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `def load(self, path: Path, **kwargs) -> Any` | abc.abstractmethod | Load model from path. |

### Class: `ModelSaver`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `abc.ABC`
- Summary: Abstract base class for framework-specific model savers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save` | `def save(self, model: Any, path: Path, **kwargs) -> None` | abc.abstractmethod | Save model to path. |

### Class: `PyTorchModelLoader`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `ModelLoader`
- Summary: Production-grade PyTorch model loader.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `def load(self, path: Path, device: str = 'cpu', **kwargs) -> Any` |  | Method. |

### Class: `PyTorchModelSaver`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `ModelSaver`
- Summary: Production-grade PyTorch model saver.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save` | `def save(self, model: Any, path: Path, **kwargs) -> None` |  | Method. |

### Class: `ModelPersistenceManager`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `object`
- Summary: Orchestrates high-level model persistence operations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register_framework` | `def register_framework(self, name: str, loader: ModelLoader, saver: ModelSaver)` |  | Method. |
| `save_bundle` | `async def save_bundle(self, bundle: ModelBundle) -> Path` |  | Save a complete model bundle. |
| `load_model` | `async def load_model(self, name: str, version: str, device: str = 'cpu') -> Any` |  | Load a model by name and version. |

### Class: `ModelConfig`

- Source: `aquilia/mlops/orchestrator/registry.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Per-model configuration (from manifest or decorator).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `device` | `str` | `'auto'` |
| `batch_size` | `int` | `16` |
| `max_batch_latency_ms` | `float` | `50.0` |
| `warmup_requests` | `int` | `0` |
| `workers` | `int` | `4` |
| `timeout_ms` | `float` | `30000.0` |
| `artifacts_dir` | `str` | `''` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_dict` | `def from_dict(cls, d: dict[str, Any]) -> ModelConfig` | classmethod | Method. |

### Class: `ModelEntry`

- Source: `aquilia/mlops/orchestrator/registry.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Registry entry for a single model version.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `model_class` | `Any` |  |
| `config` | `ModelConfig` | `field(default_factory=ModelConfig)` |
| `state` | `ModelState` | `ModelState.UNLOADED` |
| `registered_at` | `float` | `field(default_factory=time.time)` |
| `supports_streaming` | `bool` | `False` |
| `tags` | `list[str]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `key` | `def key(self) -> str` | property | Unique key for this model version. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize for API responses. |

### Class: `ModelRegistry`

- Source: `aquilia/mlops/orchestrator/registry.py`
- Bases: `object`
- Summary: In-memory metadata-only model registry.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `async def register(self, name: str, model_class: Any, version: str = 'v1', config: dict[str, Any] &#124; None = None, supports_streaming: bool = False, tags: list[str] &#124; None = None, set_active: bool = True) -> ModelEntry` |  | Register a model (metadata only -- no loading). |
| `register_sync` | `def register_sync(self, name: str, model_class: Any, version: str = 'v1', config: dict[str, Any] &#124; None = None, supports_streaming: bool = False, tags: list[str] &#124; None = None, set_active: bool = True) -> ModelEntry` |  | Synchronous registration (for use at import time via decorators). |
| `get` | `def get(self, name: str, version: str &#124; None = None) -> ModelEntry &#124; None` |  | Get a model entry by name and optional version. |
| `get_active_version` | `def get_active_version(self, name: str) -> str &#124; None` |  | Get the active version for a model. |
| `list_models` | `def list_models(self) -> list[str]` |  | List all unique model names. |
| `list_versions` | `def list_versions(self, name: str) -> list[str]` |  | List all versions of a model. |
| `list_entries` | `def list_entries(self) -> list[ModelEntry]` |  | List all model entries. |
| `has` | `def has(self, name: str, version: str &#124; None = None) -> bool` |  | Check if a model (and optionally a specific version) is registered. |
| `update_state` | `def update_state(self, name: str, version: str, state: ModelState) -> None` |  | Update the lifecycle state of a model entry. |
| `set_active_version` | `async def set_active_version(self, name: str, version: str) -> bool` |  | Set the active version for a model. |
| `unregister` | `async def unregister(self, name: str, version: str) -> bool` |  | Remove a model version from the registry. |
| `summary` | `def summary(self) -> dict[str, Any]` |  | Summary for health/debug endpoints. |

### Class: `CanaryConfig`

- Source: `aquilia/mlops/orchestrator/router.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Active canary configuration for a model.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `canary_version` | `str` |  |
| `base_version` | `str` |  |
| `percentage` | `float` | `10.0` |

### Class: `VersionRouter`

- Source: `aquilia/mlops/orchestrator/router.py`
- Bases: `object`
- Summary: Routes inference requests to the correct model version.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `VERSION_HEADER` |  | `'x-model-version'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `route` | `async def route(self, model_name: str, headers: dict[str, str] &#124; None = None, metadata: dict[str, Any] &#124; None = None) -> str` |  | Resolve which model version should handle this request. |
| `set_canary` | `def set_canary(self, model_name: str, canary_version: str, percentage: float = 10.0, base_version: str &#124; None = None) -> None` |  | Configure canary routing for a model. |
| `clear_canary` | `def clear_canary(self, model_name: str) -> None` |  | Remove canary routing for a model. |
| `get_canary` | `def get_canary(self, model_name: str) -> CanaryConfig &#124; None` |  | Get the active canary config for a model. |
| `has_canary` | `def has_canary(self, model_name: str) -> bool` |  | Check if a canary is active for a model. |
| `summary` | `def summary(self) -> dict[str, Any]` |  | Canary routing summary. |

### Class: `VersionManager`

- Source: `aquilia/mlops/orchestrator/versioning.py`
- Bases: `object`
- Summary: Version Management for ML models.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `promote` | `async def promote(self, name: str, from_version: str, to_tag: str = 'active') -> bool` |  | Promote a model version to the active slot. |
| `rollback` | `async def rollback(self, name: str) -> str &#124; None` |  | Roll back to the previous active version. |
| `history` | `def history(self, name: str) -> list[str]` |  | Return the version rollback history for a model. |
| `can_rollback` | `def can_rollback(self, name: str) -> bool` |  | Check if a rollback is available. |

### Class: `ModelpackBuilder`

- Source: `aquilia/mlops/pack/builder.py`
- Bases: `object`
- Summary: Builds a modelpack archive from local files.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_model` | `def add_model(self, path: str, *, framework: str &#124; None = None, entrypoint: bool = True) -> ModelpackBuilder` |  | Add a model file to the pack. |
| `add_file` | `def add_file(self, path: str) -> ModelpackBuilder` |  | Add an auxiliary file to the pack. |
| `add_env_lock` | `def add_env_lock(self, path: str) -> ModelpackBuilder` |  | Set the environment lock file. |
| `set_signature` | `def set_signature(self, inputs: list[TensorSpec], outputs: list[TensorSpec]) -> ModelpackBuilder` |  | Set the inference signature. |
| `set_provenance` | `def set_provenance(self, git_sha: str = '', dataset_snapshot: str = '', dockerfile: str = '') -> ModelpackBuilder` |  | Set provenance metadata. |
| `set_metadata` | `def set_metadata(self, **kwargs: Any) -> ModelpackBuilder` |  | Set arbitrary metadata key-value pairs. |
| `save` | `async def save(self, output_dir: str = '.', *, content_store: ContentStore &#124; None = None, sign_key: str &#124; None = None) -> str` |  | Build the ``.aquilia`` archive and return its path. |
| `unpack` | `async def unpack(archive_path: str, output_dir: str = '.') -> ModelpackManifest` | staticmethod | Unpack a ``.aquilia`` archive and return its manifest. |
| `inspect` | `async def inspect(archive_path: str) -> ModelpackManifest` | staticmethod | Read manifest from archive without full extraction. |

### Class: `ContentStore`

- Source: `aquilia/mlops/pack/content_store.py`
- Bases: `object`
- Summary: Local filesystem content-addressable blob store.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `store` | `async def store(self, digest: str, data: bytes) -> str` |  | Store blob by digest. Idempotent -- skips if already exists. |
| `retrieve` | `async def retrieve(self, digest: str) -> bytes` |  | Retrieve blob by digest. |
| `exists` | `async def exists(self, digest: str) -> bool` |  | Check if blob exists. |
| `delete` | `async def delete(self, digest: str) -> None` |  | Delete blob by digest. |
| `list_digests` | `async def list_digests(self) -> list[str]` |  | List all stored blob digests. |
| `gc` | `async def gc(self, referenced_digests: set[str]) -> int` |  | Garbage-collect unreferenced blobs. |
| `size_bytes` | `def size_bytes(self) -> int` | property | Total size of all stored blobs in bytes. |

### Class: `SignatureError`

- Source: `aquilia/mlops/pack/signer.py`
- Bases: `Exception`
- Summary: Raised when signature verification fails.

### Class: `HMACSigner`

- Source: `aquilia/mlops/pack/signer.py`
- Bases: `object`
- Summary: HMAC-SHA256 signer for modelpack archives.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign` | `def sign(self, data: bytes) -> str` |  | Produce an HMAC-SHA256 hex signature. |
| `verify` | `def verify(self, data: bytes, signature: str) -> bool` |  | Verify an HMAC-SHA256 hex signature. |

### Class: `RSASigner`

- Source: `aquilia/mlops/pack/signer.py`
- Bases: `object`
- Summary: RSA signer using ``cryptography`` (already an Aquilia dependency).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign` | `def sign(self, data: bytes) -> bytes` |  | Sign data with RSA private key. |
| `verify` | `def verify(self, data: bytes, signature: bytes) -> bool` |  | Verify RSA signature with public key. |

### Class: `HealthCheckPlugin`

- Source: `aquilia/mlops/plugins/example_plugin.py`
- Bases: `object`
- Summary: Minimal example plugin implementing the ``PluginHook`` protocol.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` |  | `'health-check'` |
| `version` |  | `'0.1.0'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `activate` | `def activate(self, ctx: dict[str, Any]) -> None` |  | Method. |
| `deactivate` | `def deactivate(self) -> None` |  | Method. |
| `stats` | `def stats(self) -> dict[str, Any]` |  | Method. |

### Class: `PluginState`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `str, Enum`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `DISCOVERED` |  | `'discovered'` |
| `LOADED` |  | `'loaded'` |
| `ACTIVATED` |  | `'activated'` |
| `DEACTIVATED` |  | `'deactivated'` |
| `ERROR` |  | `'error'` |

### Class: `PluginDescriptor`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `object`
- Decorators: `dataclass`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `module` | `str` |  |
| `state` | `PluginState` | `PluginState.DISCOVERED` |
| `instance` | `Any` | `None` |
| `error` | `str &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `PluginHookProtocol`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `Protocol`
- Summary: Minimal interface a plugin must satisfy.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `activate` | `def activate(self, ctx: dict[str, Any]) -> None` |  | Method. |
| `deactivate` | `def deactivate(self) -> None` |  | Method. |

### Class: `PluginHost`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `object`
- Summary: Central plugin manager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `discover_entrypoints` | `def discover_entrypoints(self) -> list[PluginDescriptor]` |  | Scan installed packages for plugins. |
| `register` | `def register(self, plugin: Any) -> PluginDescriptor` |  | Manually register a plugin class or instance. |
| `load` | `def load(self, name: str) -> PluginDescriptor` |  | Import and instantiate a discovered plugin. |
| `activate` | `def activate(self, name: str, ctx: dict[str, Any] &#124; None = None) -> None` |  | Activate a loaded plugin. |
| `deactivate` | `def deactivate(self, name: str) -> None` |  | Deactivate a running plugin. |
| `activate_all` | `def activate_all(self, ctx: dict[str, Any] &#124; None = None) -> None` |  | Method. |
| `deactivate_all` | `def deactivate_all(self) -> None` |  | Method. |
| `on` | `def on(self, event: str, callback: Callable) -> None` |  | Register a hook callback for *event*. |
| `emit` | `def emit(self, event: str, **kwargs: Any) -> list[Any]` |  | Fire all callbacks for *event* and collect results. |
| `list_plugins` | `def list_plugins(self) -> list[PluginDescriptor]` |  | Method. |
| `get` | `def get(self, name: str) -> PluginDescriptor &#124; None` |  | Method. |
| `active_plugins` | `def active_plugins(self) -> list[PluginDescriptor]` | property | Method. |

### Class: `MarketplaceEntry`

- Source: `aquilia/mlops/plugins/marketplace.py`
- Bases: `object`
- Decorators: `dataclass`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `version` | `str` |  |
| `description` | `str` |  |
| `author` | `str` |  |
| `pypi_name` | `str` |  |
| `homepage` | `str` | `''` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `downloads` | `int` | `0` |
| `verified` | `bool` | `False` |

### Class: `PluginMarketplace`

- Source: `aquilia/mlops/plugins/marketplace.py`
- Bases: `object`
- Summary: Browse and install plugins from a remote JSON index.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `fetch_index` | `async def fetch_index(self) -> list[MarketplaceEntry]` |  | Download the plugin index. |
| `search` | `def search(self, query: str, *, tags: list[str] &#124; None = None, verified_only: bool = False) -> list[MarketplaceEntry]` |  | Search the cached index. |
| `install` | `def install(self, entry_or_name: MarketplaceEntry &#124; str) -> bool` |  | Install a plugin via pip. |
| `uninstall` | `def uninstall(self, pypi_name: str) -> bool` |  | Uninstall a plugin package. |

### Class: `RegistryDB`

- Source: `aquilia/mlops/registry/models.py`
- Bases: `object`
- Summary: Async SQLite backend for registry metadata.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Create tables if they don't exist. |
| `close` | `async def close(self) -> None` |  | Method. |
| `insert_pack` | `async def insert_pack(self, name: str, tag: str, digest: str, manifest_json: str, signed_by: str = '') -> None` |  | Insert a pack record. Ignores if digest already exists. |
| `get_pack` | `async def get_pack(self, name: str, tag: str) -> dict[str, Any] &#124; None` |  | Get pack by name:tag via the tags table. |
| `get_pack_by_digest` | `async def get_pack_by_digest(self, digest: str) -> dict[str, Any] &#124; None` |  | Get pack by content digest. |
| `list_versions` | `async def list_versions(self, name: str) -> list[dict[str, Any]]` |  | List all versions (tags) of a named pack. |
| `list_packs` | `async def list_packs(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]` |  | List distinct pack names with latest tag info. |
| `upsert_tag` | `async def upsert_tag(self, name: str, tag: str, digest: str) -> None` |  | Insert or update a tag pointer. |
| `delete_tag` | `async def delete_tag(self, name: str, tag: str) -> None` |  | Delete a tag. |
| `insert_blob` | `async def insert_blob(self, digest: str, size: int, storage_path: str = '') -> None` |  | Track a blob in the registry. |

### Class: `RegistryError`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `Exception`
- Summary: Base error for registry operations (kept for backward compatibility).

### Class: `PackNotFoundError`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `RegistryError`
- Summary: Raised when a modelpack is not found (kept for backward compatibility).

### Class: `ImmutabilityError`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `RegistryError`
- Summary: Raised when attempting to overwrite an immutable artifact (kept for backward compatibility).

### Class: `RegistryService`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `object`
- Summary: Modelpack registry service.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Initialize database schema. |
| `close` | `async def close(self) -> None` |  | Close database connections. |
| `publish` | `async def publish(self, manifest: ModelpackManifest, blobs: dict[str, bytes] &#124; None = None, *, force: bool = False) -> str` |  | Publish a modelpack to the registry. |
| `fetch` | `async def fetch(self, name: str, tag: str = 'latest') -> ModelpackManifest` |  | Fetch a modelpack manifest by name and tag. |
| `fetch_by_digest` | `async def fetch_by_digest(self, digest: str) -> ModelpackManifest` |  | Fetch a modelpack by its content digest (LRU-cached). |
| `cache_stats` | `def cache_stats(self) -> dict[str, Any]` | property | Return LRU cache hit/miss statistics. |
| `list_versions` | `async def list_versions(self, name: str) -> list[dict[str, Any]]` |  | List all versions of a modelpack. |
| `list_packs` | `async def list_packs(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]` |  | List all modelpacks. |
| `promote` | `async def promote(self, name: str, tag: str, target_tag: str) -> None` |  | Promote a modelpack tag to another tag (e.g., staging -> production). |
| `delete` | `async def delete(self, name: str, tag: str) -> None` |  | Delete a modelpack tag (admin only). |
| `verify` | `async def verify(self, name: str, tag: str) -> dict[str, Any]` |  | Verify integrity of a modelpack. |

### Class: `BaseStorageAdapter`

- Source: `aquilia/mlops/registry/storage/base.py`
- Bases: `abc.ABC`
- Summary: Abstract base for blob storage backends.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes) -> str` | abc.abstractmethod | Store a blob, return storage path or URI. |
| `get_blob` | `async def get_blob(self, digest: str) -> bytes` | abc.abstractmethod | Retrieve a blob by digest. |
| `has_blob` | `async def has_blob(self, digest: str) -> bool` | abc.abstractmethod | Check if a blob exists. |
| `delete_blob` | `async def delete_blob(self, digest: str) -> None` | abc.abstractmethod | Delete a blob. |
| `list_blobs` | `async def list_blobs(self) -> list[str]` | abc.abstractmethod | List all blob digests. |

### Class: `FilesystemStorageAdapter`

- Source: `aquilia/mlops/registry/storage/filesystem.py`
- Bases: `BaseStorageAdapter`
- Summary: Store blobs on local filesystem in a content-addressable layout.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes) -> str` |  | Method. |
| `get_blob` | `async def get_blob(self, digest: str) -> bytes` |  | Method. |
| `has_blob` | `async def has_blob(self, digest: str) -> bool` |  | Method. |
| `delete_blob` | `async def delete_blob(self, digest: str) -> None` |  | Method. |
| `list_blobs` | `async def list_blobs(self) -> list[str]` |  | Method. |

### Class: `S3StorageAdapter`

- Source: `aquilia/mlops/registry/storage/s3.py`
- Bases: `BaseStorageAdapter`
- Summary: Store blobs in an S3-compatible bucket.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes) -> str` |  | Method. |
| `get_blob` | `async def get_blob(self, digest: str) -> bytes` |  | Method. |
| `has_blob` | `async def has_blob(self, digest: str) -> bool` |  | Method. |
| `delete_blob` | `async def delete_blob(self, digest: str) -> None` |  | Method. |
| `list_blobs` | `async def list_blobs(self) -> list[str]` |  | Method. |

### Class: `RolloutPhase`

- Source: `aquilia/mlops/release/rollout.py`
- Bases: `str, Enum`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PENDING` |  | `'pending'` |
| `IN_PROGRESS` |  | `'in_progress'` |
| `PAUSED` |  | `'paused'` |
| `COMPLETED` |  | `'completed'` |
| `ROLLED_BACK` |  | `'rolled_back'` |
| `FAILED` |  | `'failed'` |

### Class: `RolloutState`

- Source: `aquilia/mlops/release/rollout.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Current state of a rollout.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` |  |
| `config` | `RolloutConfig` |  |
| `phase` | `RolloutPhase` | `RolloutPhase.PENDING` |
| `current_percentage` | `int` | `0` |
| `steps_completed` | `int` | `0` |
| `started_at` | `float` | `0.0` |
| `completed_at` | `float` | `0.0` |
| `metrics_history` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `error` | `str` | `''` |

### Class: `RolloutEngine`

- Source: `aquilia/mlops/release/rollout.py`
- Bases: `object`
- Summary: Manages progressive rollouts with metric-based gating.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `start` | `async def start(self, config: RolloutConfig) -> RolloutState` |  | Start a new rollout. |
| `advance` | `async def advance(self, rollout_id: str, percentage: int &#124; None = None) -> RolloutState` |  | Advance a rollout to a higher canary percentage. |
| `complete` | `async def complete(self, rollout_id: str) -> RolloutState` |  | Complete a rollout (100% traffic to new version). |
| `rollback` | `async def rollback(self, rollout_id: str, reason: str = '') -> RolloutState` |  | Rollback a rollout to the original version. |
| `get_rollout` | `def get_rollout(self, rollout_id: str) -> RolloutState &#124; None` |  | Method. |
| `list_rollouts` | `def list_rollouts(self) -> list[RolloutState]` |  | Method. |

### Class: `ModelState`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `str, Enum`
- Summary: Lifecycle states for a model runtime.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `UNLOADED` |  | `'unloaded'` |
| `PREPARED` |  | `'prepared'` |
| `LOADING` |  | `'loading'` |
| `LOADED` |  | `'loaded'` |
| `FAILED` |  | `'failed'` |
| `UNLOADING` |  | `'unloading'` |

### Class: `InvalidStateTransition`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `RuntimeError`
- Summary: Raised when an illegal state transition is attempted.

### Class: `BaseRuntime`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `abc.ABC`
- Summary: Abstract runtime for model inference.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `state` | `def state(self) -> ModelState` | property | Current model lifecycle state. |
| `is_loaded` | `def is_loaded(self) -> bool` | property | Backward-compatible loaded check. |
| `manifest` | `def manifest(self) -> ModelpackManifest &#124; None` | property | Method. |
| `device` | `def device(self) -> str` | property | Method. |
| `last_error` | `def last_error(self) -> str &#124; None` | property | Method. |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` | abc.abstractmethod | Prepare runtime with model artifacts (download, validate). |
| `load` | `async def load(self) -> None` | abc.abstractmethod | Load model into memory / accelerator. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` | abc.abstractmethod | Run inference on a batch of requests. |
| `preprocess` | `async def preprocess(self, raw_input: dict[str, Any]) -> dict[str, Any]` |  | Transform raw request inputs before inference. |
| `postprocess` | `async def postprocess(self, raw_output: dict[str, Any]) -> dict[str, Any]` |  | Transform raw model outputs before returning to the client. |
| `health` | `async def health(self) -> dict[str, Any]` |  | Health check. |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Collect runtime-specific metrics. |
| `unload` | `async def unload(self) -> None` |  | Unload model and free resources. |
| `memory_info` | `async def memory_info(self) -> dict[str, Any]` |  | Return memory / device usage info (override in subclasses). |

### Class: `BaseStreamingRuntime`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `BaseRuntime`
- Summary: Abstract runtime that adds streaming inference for LLM/SLM models.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `stream_infer` | `async def stream_infer(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]` | abc.abstractmethod | Stream tokens one at a time. Must be an async generator. |
| `token_usage` | `async def token_usage(self) -> TokenUsage` |  | Return lifetime token usage statistics. |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Extended metrics including token stats. |

### Class: `BentoExporter`

- Source: `aquilia/mlops/runtime/bento_exporter.py`
- Bases: `BaseRuntime`
- Summary: Export modelpacks to BentoML service format.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` |  | Method. |
| `load` | `async def load(self) -> None` |  | Method. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` |  | Method. |
| `export_bento` | `async def export_bento(self, output_dir: str = '.') -> str` |  | Export a BentoML-compatible service file. |

### Class: `DeviceKind`

- Source: `aquilia/mlops/runtime/device_manager.py`
- Bases: `str, Enum`
- Summary: Hardware device categories.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CPU` |  | `'cpu'` |
| `CUDA` |  | `'cuda'` |
| `MPS` |  | `'mps'` |
| `NPU` |  | `'npu'` |
| `TPU` |  | `'tpu'` |

### Class: `DeviceInfo`

- Source: `aquilia/mlops/runtime/device_manager.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Snapshot of a single compute device.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `kind` | `DeviceKind` |  |
| `index` | `int` | `0` |
| `total_memory_mb` | `float` | `0.0` |
| `available_memory_mb` | `float` | `0.0` |
| `is_available` | `bool` | `True` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `utilization` | `def utilization(self) -> float` |  | Memory utilization ratio (0.0-1.0). |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `DeviceManager`

- Source: `aquilia/mlops/runtime/device_manager.py`
- Bases: `object`
- Summary: Centralized device management for ML runtimes.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Detect all available devices and populate the registry. |
| `select_device` | `async def select_device(self, preference: str = 'auto', memory_required_mb: float = 0.0) -> str` |  | Select the best device for a model load. |
| `acquire` | `def acquire(self, device_name: str) -> _DeviceGuard` |  | Acquire an exclusive lock on a device. |
| `refresh` | `async def refresh(self, device_name: str &#124; None = None) -> None` |  | Refresh memory stats for one or all devices. |
| `get_device` | `def get_device(self, name: str) -> DeviceInfo &#124; None` |  | Get info for a specific device. |
| `list_devices` | `def list_devices(self) -> list[DeviceInfo]` |  | Return all known devices. |
| `default_device` | `def default_device(self) -> str` | property | Method. |
| `summary` | `def summary(self) -> dict[str, Any]` |  | Return a summary dict suitable for health check responses. |

### Class: `PoolKind`

- Source: `aquilia/mlops/runtime/executor.py`
- Bases: `str, Enum`
- Summary: Executor pool types.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `THREAD` |  | `'thread'` |
| `PROCESS` |  | `'process'` |

### Class: `InferenceExecutor`

- Source: `aquilia/mlops/runtime/executor.py`
- Bases: `object`
- Summary: Async-compatible executor for CPU/GPU-bound inference work.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `start` | `async def start(self) -> None` |  | Create the underlying executor pool. |
| `shutdown` | `async def shutdown(self, timeout: float = 30.0) -> None` |  | Gracefully shut down the executor. |
| `submit` | `async def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T` |  | Submit a blocking callable and return its result asynchronously. |
| `is_running` | `def is_running(self) -> bool` | property | Method. |
| `active_tasks` | `def active_tasks(self) -> int` | property | Method. |
| `max_workers` | `def max_workers(self) -> int` | property | Method. |
| `metrics` | `def metrics(self) -> dict` |  | Return executor metrics for health/monitoring endpoints. |

### Class: `ONNXRuntimeAdapter`

- Source: `aquilia/mlops/runtime/onnx_runtime.py`
- Bases: `BaseRuntime`
- Summary: ONNX Runtime inference adapter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` |  | Method. |
| `load` | `async def load(self) -> None` |  | Method. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` |  | Method. |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Method. |
| `unload` | `async def unload(self) -> None` |  | Method. |

### Class: `PythonRuntime`

- Source: `aquilia/mlops/runtime/python_runtime.py`
- Bases: `BaseStreamingRuntime`
- Summary: In-process Python runtime with LLM streaming support.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` |  | Prepare runtime: validate manifest, detect device. |
| `load` | `async def load(self) -> None` |  | Load model into memory, transitioning through LOADING -> LOADED. |
| `unload` | `async def unload(self) -> None` |  | Unload model and free resources. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` |  | Method. |
| `stream_infer` | `async def stream_infer(self, request: InferenceRequest) -> AsyncIterator[StreamChunk]` |  | Stream tokens one at a time for LLM inference. |
| `preprocess` | `async def preprocess(self, raw_input: dict[str, Any]) -> dict[str, Any]` |  | Default preprocessing -- identity pass-through. |
| `postprocess` | `async def postprocess(self, raw_output: dict[str, Any]) -> dict[str, Any]` |  | Default postprocessing -- identity pass-through. |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Method. |
| `memory_info` | `async def memory_info(self) -> dict[str, Any]` |  | Return GPU/CPU memory info. |
| `set_predict_fn` | `def set_predict_fn(self, fn: Callable) -> None` |  | Set a custom prediction function. |

### Class: `TorchServeExporter`

- Source: `aquilia/mlops/runtime/torchserve_exporter.py`
- Bases: `BaseRuntime`
- Summary: Export modelpacks to TorchServe ``.mar`` format and

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` |  | Method. |
| `load` | `async def load(self) -> None` |  | Method. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` |  | Method. |
| `export_mar` | `async def export_mar(self, output_dir: str = '.') -> str` |  | Export a TorchServe-compatible ``.mar`` archive. |

### Class: `TritonAdapter`

- Source: `aquilia/mlops/runtime/triton_adapter.py`
- Bases: `BaseRuntime`
- Summary: Triton Inference Server adapter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str) -> None` |  | Method. |
| `load` | `async def load(self) -> None` |  | Method. |
| `infer` | `async def infer(self, batch: BatchRequest) -> list[InferenceResult]` |  | Method. |
| `unload` | `async def unload(self) -> None` |  | Method. |

### Class: `ScalingPolicy`

- Source: `aquilia/mlops/scheduler/autoscaler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Autoscaling policy definition.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `min_replicas` | `int` | `1` |
| `max_replicas` | `int` | `10` |
| `target_concurrency` | `float` | `10.0` |
| `target_latency_p95_ms` | `float` | `100.0` |
| `scale_up_threshold` | `float` | `0.8` |
| `scale_down_threshold` | `float` | `0.3` |
| `cooldown_seconds` | `int` | `60` |
| `window_seconds` | `float` | `60.0` |
| `bucket_width` | `float` | `5.0` |
| `target_gpu_utilization` | `float` | `0.75` |
| `gpu_scale_up_threshold` | `float` | `0.85` |
| `gpu_scale_down_threshold` | `float` | `0.3` |
| `target_tokens_per_second` | `float` | `0.0` |
| `token_scale_up_factor` | `float` | `0.8` |
| `token_scale_down_factor` | `float` | `0.3` |

### Class: `ScalingDecision`

- Source: `aquilia/mlops/scheduler/autoscaler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Output of a scaling evaluation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `current_replicas` | `int` |  |
| `desired_replicas` | `int` |  |
| `reason` | `str` |  |
| `metrics` | `dict[str, float]` | `field(default_factory=dict)` |

### Class: `Autoscaler`

- Source: `aquilia/mlops/scheduler/autoscaler.py`
- Bases: `object`
- Summary: Autoscaling engine for model serving deployments.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `record_request` | `def record_request(self, latency_ms: float = 0.0, error: bool = False, tokens: int = 0) -> None` |  | Record a single request into the sliding windows. |
| `record_gpu_utilization` | `def record_gpu_utilization(self, utilization: float) -> None` |  | Record GPU utilization (0.0-1.0) into the sliding window. |
| `window_rps` | `def window_rps(self) -> float` | property | Current requests-per-second from the sliding window. |
| `window_avg_latency` | `def window_avg_latency(self) -> float` | property | Average latency across the current window. |
| `window_error_rate` | `def window_error_rate(self) -> float` | property | Error rate in the current window. |
| `window_stats` | `def window_stats(self) -> dict[str, float]` | property | Summary of windowed metrics. |
| `evaluate` | `def evaluate(self, metrics: dict[str, float] &#124; None = None) -> ScalingDecision` |  | Evaluate current metrics and decide on scaling. |
| `apply` | `def apply(self, decision: ScalingDecision) -> None` |  | Apply a scaling decision (update internal state). |
| `generate_hpa_manifest` | `def generate_hpa_manifest(self, deployment_name: str, namespace: str = 'default') -> dict[str, Any]` |  | Generate a Kubernetes HorizontalPodAutoscaler manifest. |

### Class: `NodeInfo`

- Source: `aquilia/mlops/scheduler/placement.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Information about a compute node.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `node_id` | `str` |  |
| `device_type` | `str` | `'cpu'` |
| `total_memory_mb` | `float` | `0.0` |
| `available_memory_mb` | `float` | `0.0` |
| `current_load` | `float` | `0.0` |
| `gpu_available` | `bool` | `False` |
| `models_loaded` | `list[str]` | `field(default_factory=list)` |
| `gpu_memory_total_mb` | `float` | `0.0` |
| `gpu_memory_available_mb` | `float` | `0.0` |
| `gpu_utilization` | `float` | `0.0` |
| `gpu_name` | `str` | `''` |
| `compute_capability` | `str` | `''` |

### Class: `PlacementRequest`

- Source: `aquilia/mlops/scheduler/placement.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Request for model placement.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `model_name` | `str` |  |
| `model_size_mb` | `float` |  |
| `preferred_device` | `str` | `'any'` |
| `gpu_required` | `bool` | `False` |
| `gpu_memory_required_mb` | `float` | `0.0` |
| `model_type` | `str` | `'SLM'` |
| `quantized` | `bool` | `False` |
| `min_compute_capability` | `str` | `''` |

### Class: `PlacementScheduler`

- Source: `aquilia/mlops/scheduler/placement.py`
- Bases: `object`
- Summary: Greedy placement scheduler with soft device affinity.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register_node` | `def register_node(self, node: NodeInfo) -> None` |  | Register a compute node. |
| `unregister_node` | `def unregister_node(self, node_id: str) -> None` |  | Remove a node. |
| `update_node` | `def update_node(self, node_id: str, **kwargs: Any) -> None` |  | Update node metrics. |
| `place` | `def place(self, request: PlacementRequest) -> PlacementScore &#124; None` |  | Find the best node for a model placement request. |
| `rebalance` | `def rebalance(self) -> list[dict[str, Any]]` |  | Suggest rebalancing moves to improve load distribution. |

### Class: `BlobEncryptor`

- Source: `aquilia/mlops/security/encryption.py`
- Bases: `object`
- Summary: Encrypts / decrypts blob data at rest using Fernet (AES-128-CBC).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `encrypt` | `def encrypt(self, data: bytes) -> bytes` |  | Method. |
| `decrypt` | `def decrypt(self, token: bytes) -> bytes` |  | Method. |
| `key` | `def key(self) -> bytes` | property | Method. |
| `from_key` | `def from_key(cls, key: bytes) -> BlobEncryptor` | classmethod | Method. |

### Class: `Permission`

- Source: `aquilia/mlops/security/rbac.py`
- Bases: `str, Enum`
- Summary: Registry permissions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PACK_READ` |  | `'pack:read'` |
| `PACK_WRITE` |  | `'pack:write'` |
| `PACK_DELETE` |  | `'pack:delete'` |
| `PACK_PROMOTE` |  | `'pack:promote'` |
| `PACK_SIGN` |  | `'pack:sign'` |
| `REGISTRY_ADMIN` |  | `'registry:admin'` |
| `PLUGIN_INSTALL` |  | `'plugin:install'` |
| `ROLLOUT_MANAGE` |  | `'rollout:manage'` |

### Class: `Role`

- Source: `aquilia/mlops/security/rbac.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A named role with a set of permissions.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `permissions` | `set[Permission]` | `field(default_factory=set)` |
| `description` | `str` | `''` |

### Class: `RBACManager`

- Source: `aquilia/mlops/security/rbac.py`
- Bases: `object`
- Summary: Role-based access control for registry operations.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `assign_role` | `def assign_role(self, user_id: str, role_name: str) -> None` |  | Method. |
| `revoke_role` | `def revoke_role(self, user_id: str, role_name: str) -> None` |  | Method. |
| `check_permission` | `def check_permission(self, user_id: str, permission: Permission) -> bool` |  | Method. |
| `get_user_permissions` | `def get_user_permissions(self, user_id: str) -> set[Permission]` |  | Method. |
| `add_role` | `def add_role(self, role: Role) -> None` |  | Method. |

### Class: `ArtifactSigner`

- Source: `aquilia/mlops/security/signing.py`
- Bases: `object`
- Summary: Signs and verifies modelpack artifacts.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign` | `async def sign(self, archive_path: str) -> str` |  | Sign an archive and return signature path. |
| `verify` | `async def verify(self, archive_path: str, sig_path: str) -> bool` |  | Verify an archive signature. |

### Class: `EncryptionManager`

- Source: `aquilia/mlops/security/signing.py`
- Bases: `object`
- Summary: Encryption at rest for registry blob storage.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `encrypt` | `def encrypt(self, data: bytes) -> bytes` |  | Encrypt data. |
| `decrypt` | `def decrypt(self, token: bytes) -> bytes` |  | Decrypt data. |
| `key` | `def key(self) -> bytes` | property | Method. |

### Class: `DynamicBatcher`

- Source: `aquilia/mlops/serving/batching.py`
- Bases: `object`
- Summary: Async dynamic batching scheduler.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `start` | `async def start(self) -> None` |  | Start the background batcher coroutine. |
| `stop` | `async def stop(self) -> None` |  | Stop the batcher and drain remaining requests. |
| `submit` | `async def submit(self, request: InferenceRequest) -> InferenceResult` |  | Submit a single request and wait for its result. |
| `metrics` | `def metrics(self) -> dict[str, float]` |  | Return batcher metrics. |

### Class: `MLOpsController`

- Source: `aquilia/mlops/serving/controllers.py`
- Bases: `Controller`
- Summary: Controller for MLOps HTTP API.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `prefix` |  | `'/mlops'` |
| `tags` | `list[str]` | `['mlops']` |
| `instantiation_mode` |  | `'singleton'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `health` | `async def health(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Platform health check -- ``GET /mlops/health``. |
| `predict` | `async def predict(self, body: dict[str, Any], ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Single inference -- ``POST /mlops/predict``. |
| `stream_predict` | `async def stream_predict(self, body: dict[str, Any], ctx: RequestCtx &#124; None = None)` | POST | Streaming inference -- ``POST /mlops/stream``. |
| `chat` | `async def chat(self, body: dict[str, Any], ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Chat-style inference -- ``POST /mlops/chat``. |
| `circuit_breaker_status` | `async def circuit_breaker_status(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Circuit breaker status -- ``GET /mlops/circuit-breaker``. |
| `rate_limit_status` | `async def rate_limit_status(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Rate limiter status -- ``GET /mlops/rate-limit``. |
| `memory_status` | `async def memory_status(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Memory tracker status -- ``GET /mlops/memory``. |
| `model_capabilities` | `async def model_capabilities(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Model capabilities -- ``GET /mlops/capabilities``. |
| `metrics` | `async def metrics(self, fmt: str = 'json', ctx: RequestCtx &#124; None = None) -> Any` | GET | Metrics export -- ``GET /mlops/metrics``. |
| `list_models` | `async def list_models(self, limit: int = 100, offset: int = 0, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | List registered models -- ``GET /mlops/models``. |
| `get_model` | `async def get_model(self, name: str, tag: str = 'latest', ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Get model details -- ``GET /mlops/models/{name}``. |
| `load_model` | `async def load_model(self, name: str, body: dict[str, Any] = None, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Load a model into memory -- ``POST /mlops/models/{name}/load``. |
| `unload_model` | `async def unload_model(self, name: str, body: dict[str, Any] = None, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Unload a model from memory -- ``POST /mlops/models/{name}/unload``. |
| `reload_model` | `async def reload_model(self, name: str, body: dict[str, Any] = None, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Hot-reload a model to a new version -- ``POST /mlops/models/{name}/reload``. |
| `model_health` | `async def model_health(self, name: str, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Health check for a specific model -- ``GET /mlops/models/{name}/health``. |
| `model_metrics` | `async def model_metrics(self, name: str, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Metrics for a specific model -- ``GET /mlops/models/{name}/metrics``. |
| `start_rollout` | `async def start_rollout(self, body: dict[str, Any], ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Start a rollout -- ``POST /mlops/models/{name}/rollout``. |
| `list_rollouts` | `async def list_rollouts(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | List rollouts -- ``GET /mlops/rollouts``. |
| `drift_status` | `async def drift_status(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Drift detection status -- ``GET /mlops/drift``. |
| `list_plugins` | `async def list_plugins(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | List plugins -- ``GET /mlops/plugins``. |
| `liveness` | `async def liveness(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | K8s liveness probe -- ``GET /mlops/healthz``. |
| `readiness` | `async def readiness(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | K8s readiness probe -- ``GET /mlops/readyz``. |
| `lineage` | `async def lineage(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Model lineage DAG -- ``GET /mlops/lineage``. |
| `lineage_ancestors` | `async def lineage_ancestors(self, model_id: str, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Ancestors of a model -- ``GET /mlops/lineage/{model_id}/ancestors``. |
| `lineage_descendants` | `async def lineage_descendants(self, model_id: str, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Descendants of a model -- ``GET /mlops/lineage/{model_id}/descendants``. |
| `list_experiments` | `async def list_experiments(self, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | List experiments -- ``GET /mlops/experiments``. |
| `create_experiment` | `async def create_experiment(self, body: dict[str, Any], ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Create experiment -- ``POST /mlops/experiments``. |
| `conclude_experiment` | `async def conclude_experiment(self, experiment_id: str, winner: str = '', ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | POST | Conclude experiment -- ``POST /mlops/experiments/{id}/conclude``. |
| `hot_models` | `async def hot_models(self, k: int = 10, ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Top-K hot models -- ``GET /mlops/hot-models``. |
| `list_artifacts` | `async def list_artifacts(self, kind: str = '', store_dir: str = 'artifacts', ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | List artifacts -- ``GET /mlops/artifacts``. |
| `inspect_artifact` | `async def inspect_artifact(self, name: str, version: str = '', store_dir: str = 'artifacts', ctx: RequestCtx &#124; None = None) -> dict[str, Any]` | GET | Inspect artifact -- ``GET /mlops/artifacts/{name}``. |

### Class: `RouteTarget`

- Source: `aquilia/mlops/serving/router.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A model version target with associated weight.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `version` | `str` |  |
| `weight` | `float` |  |
| `handler` | `Callable &#124; None` | `None` |
| `request_count` | `int` | `0` |
| `error_count` | `int` | `0` |
| `total_latency_ms` | `float` | `0.0` |

### Class: `TrafficRouter`

- Source: `aquilia/mlops/serving/router.py`
- Bases: `object`
- Summary: Routes inference requests across model version targets.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_target` | `def add_target(self, version: str, weight: float, handler: Callable &#124; None = None) -> None` |  | Register a model version as a routing target. |
| `remove_target` | `def remove_target(self, version: str) -> None` |  | Remove a routing target. |
| `set_strategy` | `def set_strategy(self, strategy: RolloutStrategy) -> None` |  | Set the routing strategy. |
| `set_canary_percentage` | `def set_canary_percentage(self, version: str, percentage: int) -> None` |  | Set canary percentage for a specific version. |
| `route` | `def route(self, request_id: str = '') -> str` |  | Select a target version for the given request. |
| `route_sticky` | `def route_sticky(self, key: str) -> str` |  | Sticky routing via consistent hashing. |
| `record_result` | `def record_result(self, version: str, latency_ms: float, error: bool = False) -> None` |  | Record a result for metrics tracking. |
| `hot_models` | `def hot_models(self, k: int = 10) -> list[tuple]` |  | Return the top-K most-requested model versions. |
| `should_rollback` | `def should_rollback(self, config: RolloutConfig) -> bool` |  | Check if rollback should be triggered based on metrics. |
| `get_metrics` | `def get_metrics(self) -> dict[str, dict[str, float]]` |  | Get per-version metrics. |

### Class: `WarmupStrategy`

- Source: `aquilia/mlops/serving/server.py`
- Bases: `object`
- Summary: Pre-inference warm-up to eliminate cold-start latency.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_payload` | `def generate_payload(self, manifest: ModelpackManifest) -> dict[str, Any]` |  | Build a synthetic input from the manifest's tensor specs. |

### Class: `ModelServingServer`

- Source: `aquilia/mlops/serving/server.py`
- Bases: `object`
- Summary: High-level model serving server.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `start` | `async def start(self) -> None` |  | Prepare and load the model, warm up, start the batcher. |
| `stop` | `async def stop(self, drain_timeout_s: float &#124; None = None) -> None` |  | Stop the server gracefully. |
| `predict` | `async def predict(self, inputs: dict[str, Any], parameters: dict[str, Any] &#124; None = None, request_id: str &#124; None = None, priority: int = 0, max_tokens: int = 0, timeout_ms: float = 0.0) -> InferenceResult` |  | Submit a single prediction request. |
| `stream_predict` | `async def stream_predict(self, inputs: dict[str, Any], parameters: dict[str, Any] &#124; None = None, request_id: str &#124; None = None, max_tokens: int = 0) -> AsyncIterator[StreamChunk]` |  | Submit a streaming prediction request (LLM token-by-token output). |
| `liveness` | `async def liveness(self) -> dict[str, Any]` |  | K8s liveness probe -- ``GET /healthz``. |
| `readiness` | `async def readiness(self) -> dict[str, Any]` |  | K8s readiness probe -- ``GET /readyz``. |
| `health` | `async def health(self) -> dict[str, Any]` |  | Full health check endpoint data (backward compat). |
| `metrics` | `async def metrics(self) -> dict[str, float]` |  | Prometheus-compatible metrics. |
| `circuit_breaker` | `def circuit_breaker(self) -> CircuitBreaker` | property | Access the circuit breaker for external inspection. |
| `rate_limiter` | `def rate_limiter(self) -> TokenBucketRateLimiter &#124; None` | property | Access the rate limiter for external inspection. |
| `memory_tracker` | `def memory_tracker(self) -> MemoryTracker &#124; None` | property | Access the memory tracker for external inspection. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `serve` | `aquilia/mlops/api/functional.py` | `def serve(name: str, version: str = 'v1', device: str = 'auto', batch_size: int = 16, max_batch_latency_ms: float = 50.0, workers: int = 4, tags: list[str] &#124; None = None) -> Callable` | Decorator that wraps a function into a registered model. |
| `set_global_registry` | `aquilia/mlops/api/model_class.py` | `def set_global_registry(registry: Any) -> None` | Set the global model registry (called by DI providers). |
| `model` | `aquilia/mlops/api/model_class.py` | `def model(name: str, version: str = 'v1', device: str = 'auto', batch_size: int = 16, max_batch_latency_ms: float = 50.0, warmup_requests: int = 0, workers: int = 4, timeout_ms: float = 30000.0, tags: list[str] &#124; None = None, supports_streaming: bool = False) -> Callable[[type[T]], type[T]]` | Decorator that registers an ``AquiliaModel`` subclass with the model registry. |
| `register_mlops_providers` | `aquilia/mlops/di/providers.py` | `def register_mlops_providers(container: Container, config: dict[str, Any] &#124; None = None) -> None` | Register all MLOps services as DI providers. |
| `on_load` | `aquilia/mlops/engine/hooks.py` | `def on_load(fn: F) -> F` | Mark method as a post-load lifecycle hook. |
| `on_unload` | `aquilia/mlops/engine/hooks.py` | `def on_unload(fn: F) -> F` | Mark method as a pre-unload lifecycle hook. |
| `preprocess` | `aquilia/mlops/engine/hooks.py` | `def preprocess(fn: F) -> F` | Mark method as input preprocessor. |
| `postprocess` | `aquilia/mlops/engine/hooks.py` | `def postprocess(fn: F) -> F` | Mark method as output postprocessor. |
| `before_predict` | `aquilia/mlops/engine/hooks.py` | `def before_predict(fn: F) -> F` | Mark method as a before-prediction hook. |
| `after_predict` | `aquilia/mlops/engine/hooks.py` | `def after_predict(fn: F) -> F` | Mark method as an after-prediction hook. |
| `on_error` | `aquilia/mlops/engine/hooks.py` | `def on_error(fn: F) -> F` | Mark method as an inference error handler. |
| `collect_hooks` | `aquilia/mlops/engine/hooks.py` | `def collect_hooks(instance: Any) -> HookRegistry` | Scan an object instance for decorated hook methods. |
| `mlops_on_startup` | `aquilia/mlops/engine/lifecycle.py` | `async def mlops_on_startup(config: dict[str, Any] &#124; None = None, di_container: Any = None) -> None` | MLOps startup hook. |
| `mlops_on_shutdown` | `aquilia/mlops/engine/lifecycle.py` | `async def mlops_on_shutdown(config: dict[str, Any] &#124; None = None, di_container: Any = None) -> None` | MLOps shutdown hook. |
| `create_explainer` | `aquilia/mlops/explain/hooks.py` | `def create_explainer(method: ExplainMethod, predict_fn: Callable, data: Any, feature_names: Sequence[str] &#124; None = None, **kwargs: Any) -> SHAPExplainer &#124; LIMEExplainer` | Factory that returns the right explainer for the requested method. |
| `parse_mlops_config` | `aquilia/mlops/manifest/config.py` | `def parse_mlops_config(config: dict[str, Any]) -> MLOpsManifestConfig` | Parse an ``[mlops]`` config dict into ``MLOpsManifestConfig``. |
| `validate_manifest_config` | `aquilia/mlops/manifest/schema.py` | `def validate_manifest_config(config: MLOpsManifestConfig) -> list[str]` | Validate a parsed manifest config. |
| `validate_and_raise` | `aquilia/mlops/manifest/schema.py` | `def validate_and_raise(config: MLOpsManifestConfig) -> None` | Validate and raise ``ManifestValidationError`` if invalid. |
| `profile_model` | `aquilia/mlops/optimizer/export.py` | `async def profile_model(model_path: str, target_device: str = 'cpu') -> dict[str, Any]` | Estimate latency and memory for a model on a target device. |
| `validate_manifest` | `aquilia/mlops/pack/manifest_schema.py` | `def validate_manifest(data: dict) -> list[str]` | Validate manifest dict against schema. |
| `sign_archive` | `aquilia/mlops/pack/signer.py` | `async def sign_archive(archive_path: str, signer: HMACSigner &#124; RSASigner, output_sig_path: str &#124; None = None) -> str` | Sign a modelpack archive and write signature file. |
| `verify_archive` | `aquilia/mlops/pack/signer.py` | `async def verify_archive(archive_path: str, sig_path: str, signer: HMACSigner &#124; RSASigner) -> bool` | Verify a modelpack archive against its signature file. |
| `generate_ci_workflow` | `aquilia/mlops/release/ci.py` | `def generate_ci_workflow(output_dir: str = '.github/workflows') -> str` | Generate GitHub Actions workflow file. |
| `generate_dockerfile` | `aquilia/mlops/release/ci.py` | `def generate_dockerfile(output_dir: str = '.') -> str` | Generate Dockerfile for model serving. |
| `select_runtime` | `aquilia/mlops/runtime/base.py` | `def select_runtime(manifest: ModelpackManifest, preferred: str &#124; None = None, gpu_available: bool = False) -> BaseRuntime` | Select the best runtime for the given manifest. |
| `register_mlops_middleware` | `aquilia/mlops/serving/middleware.py` | `def register_mlops_middleware(stack: MiddlewareStack, metrics_collector: Any = None, rate_limiter: Any = None, circuit_breaker: Any = None, fault_engine: Any = None, path_prefix: str = '/mlops') -> None` | Register all MLOps middleware with proper scope and priority |
| `mlops_metrics_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_metrics_middleware(metrics_collector: Any, path_prefix: str = '/mlops') -> Callable` | Create an inference metrics middleware. |
| `mlops_request_id_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_request_id_middleware() -> Callable` | Middleware that injects a unique request ID into the context. |
| `mlops_rate_limit_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_rate_limit_middleware(rate_limiter: Any, path_prefix: str = '/mlops', status_code: int = 429, fault_engine: Any = None) -> Callable` | Rate-limiting middleware using a token-bucket rate limiter. |
| `mlops_circuit_breaker_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_circuit_breaker_middleware(circuit_breaker: Any, path_prefix: str = '/mlops/predict', status_code: int = 503, fault_engine: Any = None) -> Callable` | Circuit-breaker middleware for inference endpoints. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `T` | `aquilia/mlops/_structures.py` | `TypeVar('T')` |
| `KT` | `aquilia/mlops/_structures.py` | `TypeVar('KT', bound=Hashable)` |
| `VT` | `aquilia/mlops/_structures.py` | `TypeVar('VT')` |
| `T` | `aquilia/mlops/api/model_class.py` | `TypeVar('T', bound='AquiliaModel')` |
| `F` | `aquilia/mlops/engine/hooks.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `_HOOK_ATTR` | `aquilia/mlops/engine/hooks.py` | `'__mlops_hook__'` |
| `_BUILTIN_PATTERNS` | `aquilia/mlops/explain/privacy.py` | `dict[PIIKind, re.Pattern]` |
| `MANIFEST_SCHEMA` | `aquilia/mlops/pack/manifest_schema.py` | `dict` |
| `ENTRYPOINT_GROUP` | `aquilia/mlops/plugins/host.py` | `'aquilia_mlops_plugin'` |
| `DEFAULT_INDEX_URL` | `aquilia/mlops/plugins/marketplace.py` | `'https://plugins.aquilia.dev/v1/index.json'` |
| `GITHUB_ACTIONS_WORKFLOW` | `aquilia/mlops/release/ci.py` | `'# Aquilia MLOps CI/CD Pipeline\n# Auto-generated by: aq ci generate\n\nname: Aquilia Model CI/CD\n\non:\n  push:\n    branches: [main, master]\n    paths:\n   ` |
| `DOCKERFILE_TEMPLATE` | `aquilia/mlops/release/ci.py` | `'# Aquilia Model Serving Container\n# Auto-generated by: aq ci generate\n\nFROM python:3.11-slim AS base\n\nWORKDIR /app\n\n# Install system deps\nRUN apt-get u` |
| `_TRANSITIONS` | `aquilia/mlops/runtime/base.py` | `dict[ModelState, set]` |
| `T` | `aquilia/mlops/runtime/executor.py` | `TypeVar('T')` |
| `VIEWER` | `aquilia/mlops/security/rbac.py` | `Role(name='viewer', permissions={Permission.PACK_READ}, description='Read-only access to modelpacks')` |
| `DEVELOPER` | `aquilia/mlops/security/rbac.py` | `Role(name='developer', permissions={Permission.PACK_READ, Permission.PACK_WRITE, Permission.PACK_SIGN}, description='Read/write access to modelpacks')` |
| `DEPLOYER` | `aquilia/mlops/security/rbac.py` | `Role(name='deployer', permissions={Permission.PACK_READ, Permission.PACK_PROMOTE, Permission.ROLLOUT_MANAGE}, description='Deploy and manage rollouts')` |
| `ADMIN` | `aquilia/mlops/security/rbac.py` | `Role(name='admin', permissions=set(Permission), description='Full registry administration')` |
| `BUILTIN_ROLES` | `aquilia/mlops/security/rbac.py` | `{r.name: r for r in [VIEWER, DEVELOPER, DEPLOYER, ADMIN]}` |
