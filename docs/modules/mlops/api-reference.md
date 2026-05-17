# Mlops API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/mlops/__init__.py` | 317 | 0 | 0 | Aquilia MLOps Platform |
| `aquilia/mlops/_structures.py` | 1374 | 17 | 0 | MLOps Data Structures -- High-performance primitives for ML pipelines. |
| `aquilia/mlops/_types.py` | 746 | 30 | 0 | Aquilia MLOps Platform -- Shared type definitions. |
| `aquilia/mlops/api/__init__.py` | 14 | 0 | 0 | Aquilia MLOps API Layer. |
| `aquilia/mlops/api/blueprints.py` | 403 | 26 | 0 | MLOps Blueprints -- Aquilia Blueprint definitions for all MLOps data types. |
| `aquilia/mlops/api/functional.py` | 113 | 0 | 1 | Functional Serving -- ``@serve`` decorator for minimal model definitions. |
| `aquilia/mlops/api/model_class.py` | 207 | 1 | 2 | AquiliaModel -- declarative base class and ``@model`` decorator. |
| `aquilia/mlops/api/route_generator.py` | 250 | 2 | 0 | Route Generator -- auto-generate Aquilia controller endpoints per model. |
| `aquilia/mlops/di/providers.py` | 597 | 1 | 1 | MLOps DI Integration -- Wires all MLOps services into Aquilia's DI container. |
| `aquilia/mlops/engine/__init__.py` | 31 | 0 | 0 | Aquilia MLOps Execution Engine. |
| `aquilia/mlops/engine/faults.py` | 644 | 40 | 0 | MLOps Fault Domain -- Structured error handling for the entire ML pipeline. |
| `aquilia/mlops/engine/hooks.py` | 177 | 1 | 8 | Pipeline Hooks -- decorator-based lifecycle and inference hooks. |
| `aquilia/mlops/engine/lifecycle.py` | 355 | 0 | 2 | MLOps Lifecycle Hooks -- Startup / shutdown integration with Aquilia's LifecycleCoordinator. |
| `aquilia/mlops/engine/module.py` | 111 | 1 | 0 | MLOps Aquilary Module -- register MLOps as an Aquilary application module. |
| `aquilia/mlops/engine/pipeline.py` | 313 | 2 | 0 | Inference Pipeline -- async preprocess → batch/infer → postprocess pipeline. |
| `aquilia/mlops/explain/__init__.py` | 1 | 0 | 0 | Explainability and privacy hooks. |
| `aquilia/mlops/explain/hooks.py` | 251 | 5 | 1 | Explainability hooks -- SHAP & LIME wrappers with a unified interface. |
| `aquilia/mlops/explain/privacy.py` | 197 | 5 | 0 | Privacy helpers -- PII redaction, differential privacy noise, and input sanitisation transforms for inference payloads. |
| `aquilia/mlops/manifest/__init__.py` | 15 | 0 | 0 | Aquilia MLOps Manifest Configuration. |
| `aquilia/mlops/manifest/config.py` | 159 | 2 | 1 | Manifest Config -- parse ``[mlops]`` config from Aquilia workspace config. |
| `aquilia/mlops/manifest/schema.py` | 116 | 1 | 2 | Manifest Schema Validation for MLOps configuration. |
| `aquilia/mlops/observe/__init__.py` | 1 | 0 | 0 | Observability: metrics, drift detection, logging. |
| `aquilia/mlops/observe/drift.py` | 324 | 1 | 0 | Drift detection -- PSI, KS-test, and distribution tracking. |
| `aquilia/mlops/observe/logger.py` | 108 | 1 | 0 | Feature and prediction logger. |
| `aquilia/mlops/observe/metrics.py` | 253 | 2 | 0 | Prometheus-compatible metrics collector. |
| `aquilia/mlops/optimizer/__init__.py` | 1 | 0 | 0 | Optimization pipeline: quantize, prune, export. |
| `aquilia/mlops/optimizer/export.py` | 197 | 2 | 1 | Edge export utilities -- TFLite, CoreML, quantized ONNX. |
| `aquilia/mlops/optimizer/pipeline.py` | 169 | 2 | 0 | Optimization Pipeline -- orchestrates quantization, pruning, fusion, compilation. |
| `aquilia/mlops/orchestrator/__init__.py` | 22 | 0 | 0 | Aquilia MLOps Model Orchestrator. |
| `aquilia/mlops/orchestrator/loader.py` | 520 | 2 | 0 | Model Loader -- lazy loading, hot reload, and lifecycle state management. |
| `aquilia/mlops/orchestrator/orchestrator.py` | 263 | 1 | 0 | Model Orchestrator -- top-level façade for ML inference. |
| `aquilia/mlops/orchestrator/persistence.py` | 163 | 6 | 0 | Model Persistence System -- Robust loading and saving for production models. |
| `aquilia/mlops/orchestrator/registry.py` | 264 | 3 | 0 | Model Registry -- in-memory metadata-only registry for ML models. |
| `aquilia/mlops/orchestrator/router.py` | 154 | 2 | 0 | Version Router -- routes inference requests to the correct model version. |
| `aquilia/mlops/orchestrator/versioning.py` | 100 | 1 | 0 | Version Manager -- semantic versioning, promotion, and rollback. |
| `aquilia/mlops/pack/__init__.py` | 1 | 0 | 0 | Modelpack builder and content store. |
| `aquilia/mlops/pack/builder.py` | 319 | 1 | 0 | Modelpack Builder -- Creates ``.aquilia`` archive artifacts. |
| `aquilia/mlops/pack/content_store.py` | 111 | 1 | 0 | Content-addressable blob store. |
| `aquilia/mlops/pack/manifest_schema.py` | 161 | 0 | 1 | JSON Schema for modelpack ``manifest.json``. |
| `aquilia/mlops/pack/signer.py` | 132 | 3 | 2 | Artifact signing and verification. |
| `aquilia/mlops/plugins/__init__.py` | 1 | 0 | 0 | Plugin system and marketplace. |
| `aquilia/mlops/plugins/example_plugin.py` | 66 | 1 | 0 | Example Aquilia MLOps plugin -- demonstrates how to write a plugin. |
| `aquilia/mlops/plugins/host.py` | 230 | 4 | 0 | Plugin host -- discovers, loads, and manages lifecycle of MLOps plugins. |
| `aquilia/mlops/plugins/marketplace.py` | 134 | 2 | 0 | Plugin marketplace -- lightweight discovery & installation of community and first-party MLOps plugins from a remote index. |
| `aquilia/mlops/registry/__init__.py` | 1 | 0 | 0 | Registry service and storage adapters. |
| `aquilia/mlops/registry/models.py` | 181 | 1 | 0 | Registry data models -- SQLite backend (default). |
| `aquilia/mlops/registry/service.py` | 301 | 4 | 0 | Registry Service -- HTTP API for publishing, fetching and managing modelpacks. |
| `aquilia/mlops/registry/storage/__init__.py` | 1 | 0 | 0 | Storage adapter implementations. |
| `aquilia/mlops/registry/storage/base.py` | 31 | 1 | 0 | Base storage adapter -- abstract interface for blob backends. |
| `aquilia/mlops/registry/storage/filesystem.py` | 55 | 1 | 0 | Filesystem storage adapter -- stores blobs on local disk. |
| `aquilia/mlops/registry/storage/s3.py` | 100 | 1 | 0 | S3 / MinIO storage adapter for registry blob storage. |
| `aquilia/mlops/release/__init__.py` | 1 | 0 | 0 | Release management: rollouts, CI/CD. |
| `aquilia/mlops/release/ci.py` | 153 | 0 | 2 | CI/CD templates and GitHub Actions configuration. |
| `aquilia/mlops/release/rollout.py` | 185 | 3 | 0 | Release rollout engine -- canary, A/B, shadow traffic management. |
| `aquilia/mlops/runtime/__init__.py` | 1 | 0 | 0 | Runtime adapters for model inference. |
| `aquilia/mlops/runtime/base.py` | 343 | 4 | 1 | Runtime base -- abstract interface for inference backends. |
| `aquilia/mlops/runtime/bento_exporter.py` | 75 | 1 | 0 | BentoML exporter -- generates BentoML-compatible service bundles. |
| `aquilia/mlops/runtime/device_manager.py` | 335 | 3 | 0 | Device Manager -- auto-detection, fallback, monitoring, and locking for compute devices (CPU, CUDA, MPS, NPU). |
| `aquilia/mlops/runtime/executor.py` | 238 | 2 | 0 | Inference Executor -- offloads blocking inference to thread/process pools. |
| `aquilia/mlops/runtime/onnx_runtime.py` | 137 | 1 | 0 | ONNX Runtime adapter -- high-performance inference via onnxruntime. |
| `aquilia/mlops/runtime/python_runtime.py` | 500 | 1 | 0 | Python in-process runtime -- loads and runs models natively in Python. |
| `aquilia/mlops/runtime/torchserve_exporter.py` | 91 | 1 | 0 | TorchServe exporter -- generates TorchServe-compatible model archives. |
| `aquilia/mlops/runtime/triton_adapter.py` | 101 | 1 | 0 | Triton Inference Server adapter. |
| `aquilia/mlops/scheduler/__init__.py` | 1 | 0 | 0 | Autoscaling and placement scheduling. |
| `aquilia/mlops/scheduler/autoscaler.py` | 319 | 3 | 0 | Autoscaler -- K8s HPA metrics exporter and scaling policy engine. |
| `aquilia/mlops/scheduler/placement.py` | 196 | 3 | 0 | Hardware-aware placement scheduler. |
| `aquilia/mlops/security/__init__.py` | 1 | 0 | 0 | Security: signing, encryption, RBAC. |
| `aquilia/mlops/security/encryption.py` | 37 | 1 | 0 | Encryption at rest for registry blobs. |
| `aquilia/mlops/security/rbac.py` | 111 | 3 | 0 | RBAC for registry operations. |
| `aquilia/mlops/security/signing.py` | 91 | 2 | 0 | Security -- artifact signing, verification, and encryption at rest. |
| `aquilia/mlops/serving/__init__.py` | 1 | 0 | 0 | Model serving layer. |
| `aquilia/mlops/serving/batching.py` | 382 | 1 | 0 | Dynamic Batching Scheduler. |
| `aquilia/mlops/serving/controllers.py` | 800 | 1 | 0 | MLOps Controller -- HTTP endpoints for model serving, registry, and observability. |
| `aquilia/mlops/serving/middleware.py` | 296 | 0 | 5 | MLOps Middleware -- Inference metrics, rate limiting, and circuit breaker integration as Aquilia middleware. |
| `aquilia/mlops/serving/router.py` | 221 | 2 | 0 | Traffic router -- canary, A/B, shadow, sticky routing for model deployments. |
| `aquilia/mlops/serving/server.py` | 514 | 2 | 0 | Model Serving Server -- dev and production serving with typed endpoints. |

## Public Exports

`AdaptiveBatchQueue`, `AquiliaModel`, `AtomicCounter`, `AutoRollbackFault`, `BaseRuntime`, `BaseStreamingRuntime`, `BatchRequest`, `BatchTimeoutFault`, `BatchingStrategy`, `BlobRef`, `BloomFilter`, `CircuitBreaker`, `CircuitBreakerConfig`, `CircuitBreakerExhaustedFault`, `CircuitBreakerFault`, `CircuitBreakerOpenFault`, `CircuitState`, `ConsistentHash`, `ContentStore`, `DeviceInfo`, `DeviceKind`, `DeviceManager`, `DeviceType`, `DriftDetectionFault`, `DriftDetector`, `DriftMethod`, `DriftReport`, `DynamicBatcher`, `EncryptionFault`, `Experiment`, `ExperimentArm`, `ExperimentLedger`, `ExponentialDecay`, `ExportTarget`, `Framework`, `HookRegistry`, `ImmutabilityViolationFault`, `InferenceExecutor`, `InferenceFault`, `InferenceMode`, `InferencePipeline`, `InferenceRequest`, `InferenceResult`, `InvalidStateTransition`, `LLMConfig`, `LRUCache`, `LineageNode`, `MLOpsConfig`, `MLOpsController`, `MLOpsFault`, `MLOpsManifestConfig`, `MemoryFault`, `MemoryHardLimitFault`, `MemorySoftLimitFault`, `MemoryTracker`, `MetricsCollector`, `MetricsExportFault`, `ModelEntry`, `ModelLineageDAG`, `ModelLoader`, `ModelManifestEntry`, `ModelOrchestrator`, `ModelRegistry`, `ModelServingServer`, `ModelState`, `ModelType`, `ModelpackBuilder`, `ModelpackManifest`, `PackBuildFault`, `PackIntegrityFault`, `PackNotFoundFault`, `PackSignatureFault`, `PermissionDeniedFault`, `PlacementFault`, `PlacementScore`, `PluginHook`, `PluginHookFault`, `PluginHost`, `PluginLoadFault`, `PoolKind`, `Provenance`, `PythonRuntime`, `QuantizePreset`, `RateLimitFault`, `RegistryConnectionFault`, `RegistryService`, `RingBuffer`, `RolloutAdvanceFault`, `RolloutConfig`, `RolloutStrategy`, `RouteDefinition`, `RouteGenerator`, `Runtime`, `RuntimeKind`, `RuntimeLoadFault`, `ScalingFault`, `SigningFault`, `SlidingWindow`, `StorageAdapter`, `StreamChunk`, `StreamInterruptedFault`, `StreamingFault`, `StreamingRuntime`, `TensorSpec`, `TokenBucketRateLimiter`, `TokenLimitExceededFault`, `TokenUsage`, `TopKHeap`, `VersionManager`, `VersionRouter`, `WarmupFault`, `WarmupStrategy`, `after_predict`, `before_predict`, `collect_hooks`, `mlops_circuit_breaker_middleware`, `mlops_metrics_middleware`, `mlops_on_shutdown`, `mlops_on_startup`, `mlops_rate_limit_middleware`, `mlops_request_id_middleware`, `model`, `on_error`, `on_load`, `on_unload`, `parse_mlops_config`, `postprocess`, `preprocess`, `register_mlops_middleware`, `register_mlops_providers`, `serve`, `validate_manifest_config`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `RingBuffer` | `aquilia/mlops/_structures.py` | Generic[T] | Fixed-capacity circular buffer backed by a pre-allocated list. |
| `LRUCache` | `aquilia/mlops/_structures.py` | Generic[KT, VT] | O(1) get / put / evict cache backed by :class:`OrderedDict`. |
| `AtomicCounter` | `aquilia/mlops/_structures.py` | object | Thread-safe monotonic counter (integers only). |
| `ExponentialDecay` | `aquilia/mlops/_structures.py` | object | EWMA (Exponentially Weighted Moving Average). |
| `SlidingWindow` | `aquilia/mlops/_structures.py` | object | Time-bucketed sliding window for rate/latency tracking. |
| `TopKHeap` | `aquilia/mlops/_structures.py` | Generic[KT] | Maintains the top-K elements by score using a dict + sort-on-read strategy (optimal for K ≤ ~1000). |
| `BloomFilter` | `aquilia/mlops/_structures.py` | object | Space-efficient probabilistic set for fast negative lookups. |
| `ConsistentHash` | `aquilia/mlops/_structures.py` | object | Jump-consistent hash for sticky model-to-node routing. |
| `LineageNode` | `aquilia/mlops/_structures.py` | object | A single node in the model lineage graph. |
| `ModelLineageDAG` | `aquilia/mlops/_structures.py` | object | Directed acyclic graph tracking model derivation relationships. |
| `ExperimentArm` | `aquilia/mlops/_structures.py` | object | One arm of an A/B experiment. |
| `Experiment` | `aquilia/mlops/_structures.py` | object | A/B experiment definition. |
| `ExperimentLedger` | `aquilia/mlops/_structures.py` | object | Records A/B experiment assignments and collects per-arm metrics. |
| `CircuitBreaker` | `aquilia/mlops/_structures.py` | object | Three-state circuit breaker (CLOSED → OPEN → HALF_OPEN → CLOSED). |
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
| `ExplainMethod` | `aquilia/mlops/explain/hooks.py` | str, Enum |  |
| `FeatureAttribution` | `aquilia/mlops/explain/hooks.py` | object | Single feature's contribution. |
| `Explanation` | `aquilia/mlops/explain/hooks.py` | object | Complete explanation for one prediction. |
| `SHAPExplainer` | `aquilia/mlops/explain/hooks.py` | object | Wraps ``shap.KernelExplainer``, ``shap.TreeExplainer`` or ``shap.DeepExplainer`` behind a single ``explain()`` call. |
| `LIMEExplainer` | `aquilia/mlops/explain/hooks.py` | object | Wraps ``lime.lime_tabular.LimeTabularExplainer`` (default) or ``lime.lime_text.LimeTextExplainer`` behind a single ``explain()`` call. |
| `PIIKind` | `aquilia/mlops/explain/privacy.py` | str, Enum |  |
| `PIIMatch` | `aquilia/mlops/explain/privacy.py` | object |  |
| `PIIRedactor` | `aquilia/mlops/explain/privacy.py` | object | Scans text for PII and replaces matches with a configurable placeholder. |
| `LaplaceNoise` | `aquilia/mlops/explain/privacy.py` | object | Adds calibrated Laplace noise to numeric values. |
| `InputSanitiser` | `aquilia/mlops/explain/privacy.py` | object | Pipeline of transforms applied to inference payloads before they reach the model. |
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
| `PluginState` | `aquilia/mlops/plugins/host.py` | str, Enum |  |
| `PluginDescriptor` | `aquilia/mlops/plugins/host.py` | object |  |
| `PluginHookProtocol` | `aquilia/mlops/plugins/host.py` | Protocol | Minimal interface a plugin must satisfy. |
| `PluginHost` | `aquilia/mlops/plugins/host.py` | object | Central plugin manager. |
| `MarketplaceEntry` | `aquilia/mlops/plugins/marketplace.py` | object |  |
| `PluginMarketplace` | `aquilia/mlops/plugins/marketplace.py` | object | Browse and install plugins from a remote JSON index. |
| `RegistryDB` | `aquilia/mlops/registry/models.py` | object | Async SQLite backend for registry metadata. |
| `RegistryError` | `aquilia/mlops/registry/service.py` | Exception | Base error for registry operations (kept for backward compatibility). |
| `PackNotFoundError` | `aquilia/mlops/registry/service.py` | RegistryError | Raised when a modelpack is not found (kept for backward compatibility). |
| `ImmutabilityError` | `aquilia/mlops/registry/service.py` | RegistryError | Raised when attempting to overwrite an immutable artifact (kept for backward compatibility). |
| `RegistryService` | `aquilia/mlops/registry/service.py` | object | Modelpack registry service. |
| `BaseStorageAdapter` | `aquilia/mlops/registry/storage/base.py` | abc.ABC | Abstract base for blob storage backends. |
| `FilesystemStorageAdapter` | `aquilia/mlops/registry/storage/filesystem.py` | BaseStorageAdapter | Store blobs on local filesystem in a content-addressable layout. |
| `S3StorageAdapter` | `aquilia/mlops/registry/storage/s3.py` | BaseStorageAdapter | Store blobs in an S3-compatible bucket. |
| `RolloutPhase` | `aquilia/mlops/release/rollout.py` | str, Enum |  |
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
| `TorchServeExporter` | `aquilia/mlops/runtime/torchserve_exporter.py` | BaseRuntime | Export modelpacks to TorchServe ``.mar`` format and optionally forward inference via TorchServe REST API. |
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

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `serve` | `aquilia/mlops/api/functional.py` | `def serve(name: str, version: str='v1', device: str='auto', batch_size: int=16, max_batch_latency_ms: float=50.0, workers: int=4, tags: list[str] \| None=None)` | Decorator that wraps a function into a registered model. |
| `set_global_registry` | `aquilia/mlops/api/model_class.py` | `def set_global_registry(registry: Any)` | Set the global model registry (called by DI providers). |
| `model` | `aquilia/mlops/api/model_class.py` | `def model(name: str, version: str='v1', device: str='auto', batch_size: int=16, max_batch_latency_ms: float=50.0, warmup_requests: int=0, workers: int=4, timeout_ms: float=30000.0, tags: list[str] \| None=None, supports_streaming: bool=False)` | Decorator that registers an ``AquiliaModel`` subclass with the model registry. |
| `register_mlops_providers` | `aquilia/mlops/di/providers.py` | `def register_mlops_providers(container: Container, config: dict[str, Any] \| None=None)` | Register all MLOps services as DI providers. |
| `on_load` | `aquilia/mlops/engine/hooks.py` | `def on_load(fn: F)` | Mark method as a post-load lifecycle hook. |
| `on_unload` | `aquilia/mlops/engine/hooks.py` | `def on_unload(fn: F)` | Mark method as a pre-unload lifecycle hook. |
| `preprocess` | `aquilia/mlops/engine/hooks.py` | `def preprocess(fn: F)` | Mark method as input preprocessor. |
| `postprocess` | `aquilia/mlops/engine/hooks.py` | `def postprocess(fn: F)` | Mark method as output postprocessor. |
| `before_predict` | `aquilia/mlops/engine/hooks.py` | `def before_predict(fn: F)` | Mark method as a before-prediction hook. |
| `after_predict` | `aquilia/mlops/engine/hooks.py` | `def after_predict(fn: F)` | Mark method as an after-prediction hook. |
| `on_error` | `aquilia/mlops/engine/hooks.py` | `def on_error(fn: F)` | Mark method as an inference error handler. |
| `collect_hooks` | `aquilia/mlops/engine/hooks.py` | `def collect_hooks(instance: Any)` | Scan an object instance for decorated hook methods. |
| `mlops_on_startup` | `aquilia/mlops/engine/lifecycle.py` | `async def mlops_on_startup(config: dict[str, Any] \| None=None, di_container: Any=None)` | MLOps startup hook. |
| `mlops_on_shutdown` | `aquilia/mlops/engine/lifecycle.py` | `async def mlops_on_shutdown(config: dict[str, Any] \| None=None, di_container: Any=None)` | MLOps shutdown hook. |
| `create_explainer` | `aquilia/mlops/explain/hooks.py` | `def create_explainer(method: ExplainMethod, predict_fn: Callable, data: Any, feature_names: Sequence[str] \| None=None, **kwargs: Any)` | Factory that returns the right explainer for the requested method. |
| `parse_mlops_config` | `aquilia/mlops/manifest/config.py` | `def parse_mlops_config(config: dict[str, Any])` | Parse an ``[mlops]`` config dict into ``MLOpsManifestConfig``. |
| `validate_manifest_config` | `aquilia/mlops/manifest/schema.py` | `def validate_manifest_config(config: MLOpsManifestConfig)` | Validate a parsed manifest config. |
| `validate_and_raise` | `aquilia/mlops/manifest/schema.py` | `def validate_and_raise(config: MLOpsManifestConfig)` | Validate and raise ``ManifestValidationError`` if invalid. |
| `profile_model` | `aquilia/mlops/optimizer/export.py` | `async def profile_model(model_path: str, target_device: str='cpu')` | Estimate latency and memory for a model on a target device. |
| `validate_manifest` | `aquilia/mlops/pack/manifest_schema.py` | `def validate_manifest(data: dict)` | Validate manifest dict against schema. |
| `sign_archive` | `aquilia/mlops/pack/signer.py` | `async def sign_archive(archive_path: str, signer: HMACSigner \| RSASigner, output_sig_path: str \| None=None)` | Sign a modelpack archive and write signature file. |
| `verify_archive` | `aquilia/mlops/pack/signer.py` | `async def verify_archive(archive_path: str, sig_path: str, signer: HMACSigner \| RSASigner)` | Verify a modelpack archive against its signature file. |
| `generate_ci_workflow` | `aquilia/mlops/release/ci.py` | `def generate_ci_workflow(output_dir: str='.github/workflows')` | Generate GitHub Actions workflow file. |
| `generate_dockerfile` | `aquilia/mlops/release/ci.py` | `def generate_dockerfile(output_dir: str='.')` | Generate Dockerfile for model serving. |
| `select_runtime` | `aquilia/mlops/runtime/base.py` | `def select_runtime(manifest: ModelpackManifest, preferred: str \| None=None, gpu_available: bool=False)` | Select the best runtime for the given manifest. |
| `register_mlops_middleware` | `aquilia/mlops/serving/middleware.py` | `def register_mlops_middleware(stack: MiddlewareStack, metrics_collector: Any=None, rate_limiter: Any=None, circuit_breaker: Any=None, fault_engine: Any=None, path_prefix: str='/mlops')` | Register all MLOps middleware with proper scope and priority on an Aquilia :class:`~aquilia.middleware.MiddlewareStack`. |
| `mlops_metrics_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_metrics_middleware(metrics_collector: Any, path_prefix: str='/mlops')` | Create an inference metrics middleware. |
| `mlops_request_id_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_request_id_middleware()` | Middleware that injects a unique request ID into the context. |
| `mlops_rate_limit_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_rate_limit_middleware(rate_limiter: Any, path_prefix: str='/mlops', status_code: int=429, fault_engine: Any=None)` | Rate-limiting middleware using a token-bucket rate limiter. |
| `mlops_circuit_breaker_middleware` | `aquilia/mlops/serving/middleware.py` | `def mlops_circuit_breaker_middleware(circuit_breaker: Any, path_prefix: str='/mlops/predict', status_code: int=503, fault_engine: Any=None)` | Circuit-breaker middleware for inference endpoints. |

## Constants And Module Flags

| Name | Source | Value or Type |
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
| `GITHUB_ACTIONS_WORKFLOW` | `aquilia/mlops/release/ci.py` | `'# Aquilia MLOps CI/CD Pipeline\n# Auto-generated by: aq ci generate\n\nname: Aquilia Model CI/CD\n\non:\n  push:\n    branches: [main, master]\n    paths:\n      - \'models/**\'\n      - \'manifest.json\'\n  pull_request:\n    branches: [main, master]\n  workflow_dispatch:\n\njobs:\n  build-modelpack:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Set up Python\n        uses: actions/setup-python@v5\n        with:\n          python-version: \'3.11\'\n\n      - name: Install dependencies\n        run: \|\n          pip install -e ".[dev]"\n          pip install aquilia\n\n      - name: Validate manifest\n        run: aq validate\n\n      - name: Run model unit tests\n        run: pytest tests/ -v --tb=short\n\n      - name: Build modelpack\n        run: aq pack save --name ${{ github.event.repository.name }} --version v${{ github.run_number }}\n\n      - name: Smoke test (local serve)\n        run: \|\n          aq serve --model *.aquilia --timeout 30 --smoke-test\n\n      - name: Upload modelpack artifact\n        uses: actions/upload-artifact@v4\n        with:\n          name: modelpack\n          path: \'*.aquilia\'\n\n  publish:\n    needs: build-modelpack\n    if: github.ref == \'refs/heads/main\'\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/download-artifact@v4\n        with:\n          name: modelpack\n\n      - name: Publish to registry\n        run: \|\n          aq pack push *.aquilia \\\n            --registry ${{ secrets.AQUILIA_REGISTRY_URL }} \\\n            --token ${{ secrets.AQUILIA_REGISTRY_TOKEN }}\n\n  deploy-staging:\n    needs: publish\n    if: github.ref == \'refs/heads/main\'\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n\n      - name: Deploy to staging\n        run: \|\n          aq deploy \\\n            registry://${{ github.event.repository.name }}:latest \\\n            --to k8s \\\n            --namespace staging \\\n            --replicas 1\n        env:\n          KUBECONFIG: ${{ secrets.KUBECONFIG }}\n'` |
| `DOCKERFILE_TEMPLATE` | `aquilia/mlops/release/ci.py` | `'# Aquilia Model Serving Container\n# Auto-generated by: aq ci generate\n\nFROM python:3.11-slim AS base\n\nWORKDIR /app\n\n# Install system deps\nRUN apt-get update && apt-get install -y --no-install-recommends \\\n    curl \\\n    && rm -rf /var/lib/apt/lists/*\n\n# Install Python deps\nCOPY requirements.txt env.lock* ./\nRUN pip install --no-cache-dir -r requirements.txt 2>/dev/null \|\| true\nRUN pip install --no-cache-dir aquilia\n\n# Copy model artifacts\nCOPY *.aquilia ./\nRUN aq pack inspect *.aquilia\n\n# Expose serving port\nEXPOSE 8080\n\n# Health check\nHEALTHCHECK --interval=30s --timeout=5s --retries=3 \\\n    CMD curl -f http://localhost:8080/health \|\| exit 1\n\n# Run model server\nCMD ["aq", "serve", "--bind", "0.0.0.0:8080"]\n\nLABEL org.opencontainers.image.source="aquilia-mlops"\n'` |
| `_TRANSITIONS` | `aquilia/mlops/runtime/base.py` | `dict[ModelState, set]` |
| `T` | `aquilia/mlops/runtime/executor.py` | `TypeVar('T')` |
| `VIEWER` | `aquilia/mlops/security/rbac.py` | `Role(name='viewer', permissions={Permission.PACK_READ}, description='Read-only access to modelpacks')` |
| `DEVELOPER` | `aquilia/mlops/security/rbac.py` | `Role(name='developer', permissions={Permission.PACK_READ, Permission.PACK_WRITE, Permission.PACK_SIGN}, description='Read/write access to modelpacks')` |
| `DEPLOYER` | `aquilia/mlops/security/rbac.py` | `Role(name='deployer', permissions={Permission.PACK_READ, Permission.PACK_PROMOTE, Permission.ROLLOUT_MANAGE}, description='Deploy and manage rollouts')` |
| `ADMIN` | `aquilia/mlops/security/rbac.py` | `Role(name='admin', permissions=set(Permission), description='Full registry administration')` |
| `BUILTIN_ROLES` | `aquilia/mlops/security/rbac.py` | `{r.name: r for r in [VIEWER, DEVELOPER, DEPLOYER, ADMIN]}` |

## Detailed Classes And Methods

### `RingBuffer`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[T]`
- Summary: Fixed-capacity circular buffer backed by a pre-allocated list.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `append` | `def append(self, value: T)` |  |
| `extend` | `def extend(self, values: Sequence[T])` |  |
| `clear` | `def clear(self)` |  |
| `capacity` | `def capacity(self)` |  |
| `last` | `def last(self)` | Return the most recently appended element. |
| `to_list` | `def to_list(self)` |  |
| `percentile` | `def percentile(self, p: float)` | Compute the *p*-th percentile (0–100) over numeric elements. |

### `LRUCache`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[KT, VT]`
- Summary: O(1) get / put / evict cache backed by :class:`OrderedDict`.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, key: KT, default: VT \| None=None)` |  |
| `put` | `def put(self, key: KT, value: VT)` |  |
| `invalidate` | `def invalidate(self, key: KT)` |  |
| `clear` | `def clear(self)` |  |
| `hit_rate` | `def hit_rate(self)` |  |
| `stats` | `def stats(self)` |  |

### `AtomicCounter`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Thread-safe monotonic counter (integers only).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `inc` | `def inc(self, n: int=1)` |  |
| `dec` | `def dec(self, n: int=1)` |  |
| `value` | `def value(self)` |  |
| `reset` | `def reset(self, to: int=0)` |  |

### `ExponentialDecay`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: EWMA (Exponentially Weighted Moving Average).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `update` | `def update(self, sample: float)` |  |
| `value` | `def value(self)` |  |
| `reset` | `def reset(self)` |  |

### `SlidingWindow`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Time-bucketed sliding window for rate/latency tracking.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, value: float=1.0, *, ts: float \| None=None)` |  |
| `count` | `def count(self, *, ts: float \| None=None)` |  |
| `total` | `def total(self, *, ts: float \| None=None)` |  |
| `rate` | `def rate(self, *, ts: float \| None=None)` | Events per second over the window. |
| `mean` | `def mean(self, *, ts: float \| None=None)` |  |
| `clear` | `def clear(self)` |  |

### `TopKHeap`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[KT]`
- Summary: Maintains the top-K elements by score using a dict + sort-on-read strategy (optimal for K ≤ ~1000).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `push` | `def push(self, key: KT, score: float)` |  |
| `top` | `def top(self)` |  |

### `BloomFilter`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Space-efficient probabilistic set for fast negative lookups.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, item: str)` |  |
| `size_bytes` | `def size_bytes(self)` |  |
| `clear` | `def clear(self)` |  |

### `ConsistentHash`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Jump-consistent hash for sticky model-to-node routing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `bucket` | `def bucket(self, key: str)` |  |
| `add_bucket` | `def add_bucket(self)` |  |
| `remove_bucket` | `def remove_bucket(self)` |  |
| `num_buckets` | `def num_buckets(self)` |  |

### `LineageNode`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: A single node in the model lineage graph.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `model_id` | `str` | `` |
| `version` | `str` | `` |
| `framework` | `str` | `''` |
| `created_at` | `float` | `field(default_factory=time.time)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `parents` | `list[str]` | `field(default_factory=list)` |
| `children` | `list[str]` | `field(default_factory=list)` |

### `ModelLineageDAG`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Directed acyclic graph tracking model derivation relationships.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_model` | `def add_model(self, model_id: str, version: str, *, framework: str='', parents: list[str] \| None=None, metadata: dict[str, Any] \| None=None)` |  |
| `ancestors` | `def ancestors(self, model_id: str)` | All transitive ancestors (BFS). |
| `descendants` | `def descendants(self, model_id: str)` | All transitive descendants (BFS). |
| `path` | `def path(self, from_id: str, to_id: str)` | Find shortest derivation path from ``from_id`` → ``to_id``. |
| `roots` | `def roots(self)` | Models with no parents (base models). |
| `leaves` | `def leaves(self)` | Models with no children (leaf / production models). |
| `get` | `def get(self, model_id: str)` |  |
| `to_dict` | `def to_dict(self)` | Serialise the full DAG for storage / visualisation. |

### `ExperimentArm`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: One arm of an A/B experiment.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `model_version` | `str` | `` |
| `weight` | `float` | `0.5` |
| `metrics` | `dict[str, float]` | `field(default_factory=dict)` |
| `request_count` | `int` | `0` |

### `Experiment`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: A/B experiment definition.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `experiment_id` | `str` | `` |
| `description` | `str` | `''` |
| `arms` | `list[ExperimentArm]` | `field(default_factory=list)` |
| `status` | `str` | `'active'` |
| `created_at` | `float` | `field(default_factory=time.time)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### `ExperimentLedger`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Records A/B experiment assignments and collects per-arm metrics.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create` | `def create(self, experiment_id: str, *, description: str='', arms: list[dict[str, Any]] \| None=None, metadata: dict[str, Any] \| None=None)` |  |
| `assign` | `def assign(self, experiment_id: str, request_id: str)` | Deterministically assign a request to an experiment arm. |
| `record` | `def record(self, experiment_id: str, arm_name: str, metric: str, value: float)` | Record a metric observation for an experiment arm (running average). |
| `get` | `def get(self, experiment_id: str)` |  |
| `list_active` | `def list_active(self)` |  |
| `conclude` | `def conclude(self, experiment_id: str, winner: str='')` | Mark experiment as completed, optionally recording the winning arm. |
| `pause` | `def pause(self, experiment_id: str)` |  |
| `resume` | `def resume(self, experiment_id: str)` |  |
| `summary` | `def summary(self, experiment_id: str)` | Get experiment summary with per-arm metrics. |
| `to_dict` | `def to_dict(self)` |  |

### `CircuitBreaker`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Three-state circuit breaker (CLOSED → OPEN → HALF_OPEN → CLOSED).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `state` | `def state(self)` |  |
| `allow_request` | `def allow_request(self)` | Check if a request should be allowed through. |
| `record_success` | `def record_success(self)` | Record a successful request. |
| `record_failure` | `def record_failure(self)` | Record a failed request. |
| `reset` | `def reset(self)` | Force reset to closed state. |
| `force_open` | `def force_open(self)` | Force the circuit breaker into OPEN state (reject all requests). |
| `force_close` | `def force_close(self)` | Force the circuit breaker into CLOSED state (allow all requests). |
| `force_half_open` | `def force_half_open(self)` | Force the circuit breaker into HALF_OPEN state (limited probes). |
| `stats` | `def stats(self)` |  |

### `TokenBucketRateLimiter`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Token-bucket rate limiter for inference request throttling.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `acquire` | `def acquire(self, tokens: int=1)` | Try to consume tokens. Returns True if allowed. |
| `acquire_wait_time` | `def acquire_wait_time(self, tokens: int=1)` | Return seconds to wait before tokens become available, 0 if available now. |
| `available` | `def available(self)` |  |
| `stats` | `def stats(self)` |  |
| `reset` | `def reset(self)` |  |

### `AdaptiveBatchQueue`

- Source: `aquilia/mlops/_structures.py`
- Bases: `Generic[T]`
- Summary: Priority-aware batch queue with adaptive sizing for LLM serving.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `put` | `def put(self, item: T, priority: int=0, token_estimate: int=1)` | Enqueue an item. Returns False if queue is at capacity (backpressure). Higher priority values are dequeued first. |
| `drain` | `def drain(self, max_items: int=0, max_tokens: int=0)` | Drain items from the queue respecting token budget and/or max items. |
| `peek_token_total` | `def peek_token_total(self)` | Total estimated tokens currently in the queue. |
| `stats` | `def stats(self)` |  |

### `MemoryTracker`

- Source: `aquilia/mlops/_structures.py`
- Bases: `object`
- Summary: Tracks memory allocations for model serving with watermark alerts.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `allocate` | `def allocate(self, name: str, size_mb: int)` | Allocate memory for a model. Returns False if hard limit would be exceeded. |
| `release` | `def release(self, name: str)` | Release memory for a model. Returns freed MB. |
| `current_usage_mb` | `def current_usage_mb(self)` |  |
| `is_above_soft_limit` | `def is_above_soft_limit(self)` |  |
| `is_above_hard_limit` | `def is_above_hard_limit(self)` |  |
| `available_mb` | `def available_mb(self)` |  |
| `largest_model` | `def largest_model(self)` | Return the name and size of the largest allocated model. |
| `eviction_candidates` | `def eviction_candidates(self)` | Return models sorted by size ascending (smallest first) for eviction. |
| `stats` | `def stats(self)` |  |

### `DType`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Centralized DType system for Aquilia MLOps.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `FLOAT64` | `` | `'float64'` |
| `FLOAT32` | `` | `'float32'` |
| `FLOAT16` | `` | `'float16'` |
| `BFLOAT16` | `` | `'bfloat16'` |
| `INT64` | `` | `'int64'` |
| `INT32` | `` | `'int32'` |
| `INT16` | `` | `'int16'` |
| `INT8` | `` | `'int8'` |
| `UINT8` | `` | `'uint8'` |
| `BOOL` | `` | `'bool'` |
| `STRING` | `` | `'string'` |
| `OBJECT` | `` | `'object'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_floating` | `def is_floating(self)` |  |
| `is_integer` | `def is_integer(self)` |  |
| `itemsize` | `def itemsize(self)` | Returns size in bytes. |
| `from_numpy` | `def from_numpy(cls, dtype: Any)` | Convert numpy dtype to MLOps DType. |
| `from_torch` | `def from_torch(cls, dtype: Any)` | Convert torch dtype to MLOps DType. |
| `to_torch` | `def to_torch(self)` | Convert to torch dtype. |
| `validate` | `def validate(self, value: Any)` | Runtime validation of a value against this DType. |

### `Framework`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Supported ML frameworks.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PYTORCH` | `` | `'pytorch'` |
| `TENSORFLOW` | `` | `'tensorflow'` |
| `ONNX` | `` | `'onnx'` |
| `SKLEARN` | `` | `'sklearn'` |
| `XGBOOST` | `` | `'xgboost'` |
| `LIGHTGBM` | `` | `'lightgbm'` |
| `HUGGINGFACE` | `` | `'huggingface'` |
| `VLLM` | `` | `'vllm'` |
| `LLAMACPP` | `` | `'llamacpp'` |
| `CTRANSFORMERS` | `` | `'ctransformers'` |
| `CUSTOM` | `` | `'custom'` |

### `RuntimeKind`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Available runtime backends.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PYTHON` | `` | `'python'` |
| `ONNXRUNTIME` | `` | `'onnxruntime'` |
| `TRITON` | `` | `'triton'` |
| `TORCHSERVE` | `` | `'torchserve'` |
| `BENTOML` | `` | `'bentoml'` |
| `VLLM` | `` | `'vllm'` |
| `LLAMACPP` | `` | `'llamacpp'` |
| `TGI` | `` | `'tgi'` |

### `QuantizePreset`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Quantization presets.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `MOBILE` | `` | `'mobile'` |
| `EDGE` | `` | `'edge'` |
| `FP16` | `` | `'fp16'` |
| `BF16` | `` | `'bf16'` |
| `INT8` | `` | `'int8'` |
| `INT4` | `` | `'int4'` |
| `DYNAMIC` | `` | `'dynamic'` |
| `GGUF_Q4` | `` | `'gguf_q4'` |
| `GGUF_Q5` | `` | `'gguf_q5'` |
| `GGUF_Q8` | `` | `'gguf_q8'` |
| `AWQ` | `` | `'awq'` |
| `GPTQ` | `` | `'gptq'` |

### `ExportTarget`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Edge export targets.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `TFLITE` | `` | `'tflite'` |
| `COREML` | `` | `'coreml'` |
| `ONNX_QUANTIZED` | `` | `'onnx-quantized'` |
| `TENSORRT` | `` | `'tensorrt'` |
| `TVM` | `` | `'tvm'` |
| `GGUF` | `` | `'gguf'` |
| `CTRANSLATE2` | `` | `'ctranslate2'` |

### `BatchingStrategy`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Batching strategy modes.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SIZE` | `` | `'size'` |
| `TIME` | `` | `'time'` |
| `HYBRID` | `` | `'hybrid'` |
| `CONTINUOUS` | `` | `'continuous'` |
| `ADAPTIVE` | `` | `'adaptive'` |

### `RolloutStrategy`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Release rollout strategies.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CANARY` | `` | `'canary'` |
| `AB_TEST` | `` | `'ab_test'` |
| `SHADOW` | `` | `'shadow'` |
| `BLUE_GREEN` | `` | `'blue_green'` |
| `ROLLING` | `` | `'rolling'` |

### `DriftMethod`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Drift detection methods.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PSI` | `` | `'psi'` |
| `KS_TEST` | `` | `'ks_test'` |
| `DISTRIBUTION` | `` | `'distribution'` |
| `EMBEDDING` | `` | `'embedding'` |
| `PERPLEXITY` | `` | `'perplexity'` |

### `ModelType`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Model type classification for serving strategy selection.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CLASSICAL_ML` | `` | `'classical_ml'` |
| `DEEP_LEARNING` | `` | `'deep_learning'` |
| `SLM` | `` | `'slm'` |
| `LLM` | `` | `'llm'` |
| `VISION` | `` | `'vision'` |
| `MULTIMODAL` | `` | `'multimodal'` |
| `EMBEDDING` | `` | `'embedding'` |
| `CUSTOM` | `` | `'custom'` |

### `InferenceMode`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Inference execution modes.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SYNC` | `` | `'sync'` |
| `ASYNC` | `` | `'async'` |
| `STREAMING` | `` | `'streaming'` |
| `BATCH` | `` | `'batch'` |

### `DeviceType`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Compute device types.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CPU` | `` | `'cpu'` |
| `CUDA` | `` | `'cuda'` |
| `MPS` | `` | `'mps'` |
| `NPU` | `` | `'npu'` |
| `TPU` | `` | `'tpu'` |
| `AUTO` | `` | `'auto'` |

### `CircuitState`

- Source: `aquilia/mlops/_types.py`
- Bases: `str, Enum`
- Summary: Circuit breaker states.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CLOSED` | `` | `'closed'` |
| `OPEN` | `` | `'open'` |
| `HALF_OPEN` | `` | `'half_open'` |

### `TensorSpec`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Describes a single tensor in the inference signature.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `dtype` | `DType` | `` |
| `shape` | `list[Any]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |

### `BlobRef`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Reference to a blob inside a modelpack.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `path` | `str` | `` |
| `digest` | `str` | `` |
| `size` | `int` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |

### `Provenance`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Provenance metadata for reproducibility.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `git_sha` | `str` | `''` |
| `dataset_snapshot` | `str` | `''` |
| `dockerfile` | `str` | `''` |
| `build_timestamp` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |

### `LLMConfig`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Configuration specific to LLM/SLM model serving.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
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
| `rope_scaling` | `dict[str, Any] \| None` | `None` |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |

### `ModelpackManifest`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Complete manifest for a modelpack artifact.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |
| `framework` | `str` | `` |
| `entrypoint` | `str` | `` |
| `inputs` | `list[TensorSpec]` | `field(default_factory=list)` |
| `outputs` | `list[TensorSpec]` | `field(default_factory=list)` |
| `env_lock` | `str` | `'env.lock'` |
| `provenance` | `Provenance` | `field(default_factory=Provenance)` |
| `blobs` | `list[BlobRef]` | `field(default_factory=list)` |
| `created_at` | `str` | `''` |
| `signed_by` | `str` | `''` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `model_type` | `str` | `'custom'` |
| `llm_config` | `LLMConfig \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |
| `content_digest` | `def content_digest(self)` | Compute a content-addressable digest for this manifest. |
| `is_llm` | `def is_llm(self)` | Check if this manifest represents an LLM/SLM. |

### `InferenceRequest`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: A single inference request.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `request_id` | `str` | `` |
| `inputs` | `dict[str, Any]` | `` |
| `parameters` | `dict[str, Any]` | `field(default_factory=dict)` |
| `timestamp` | `float` | `field(default_factory=time.time)` |
| `priority` | `int` | `0` |
| `stream` | `bool` | `False` |
| `max_tokens` | `int` | `0` |
| `timeout_ms` | `float` | `0.0` |

### `InferenceResult`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Result of a single inference.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `request_id` | `str` | `` |
| `outputs` | `dict[str, Any]` | `` |
| `latency_ms` | `float` | `0.0` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `token_count` | `int` | `0` |
| `prompt_tokens` | `int` | `0` |
| `finish_reason` | `str` | `''` |

### `StreamChunk`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: A single chunk in a streaming inference response.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `request_id` | `str` | `` |
| `token` | `str` | `` |
| `token_id` | `int` | `0` |
| `is_finished` | `bool` | `False` |
| `finish_reason` | `str` | `''` |
| `cumulative_tokens` | `int` | `0` |
| `latency_ms` | `float` | `0.0` |

### `BatchRequest`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Aggregated batch of inference requests.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `requests` | `list[InferenceRequest]` | `` |
| `batch_id` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `size` | `def size(self)` |  |
| `total_tokens` | `def total_tokens(self)` | Estimate total token budget for LLM batches. |

### `PlacementScore`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Score for scheduler placement decisions.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `node_id` | `str` | `` |
| `device_affinity` | `float` | `0.0` |
| `memory_fit` | `float` | `0.0` |
| `current_load` | `float` | `0.0` |
| `cold_start_cost` | `float` | `0.0` |
| `total` | `float` | `0.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compute` | `def compute(self, w1: float=0.3, w2: float=0.3, w3: float=0.25, w4: float=0.15)` |  |

### `RolloutConfig`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Configuration for a traffic rollout.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `from_version` | `str` | `` |
| `to_version` | `str` | `` |
| `strategy` | `RolloutStrategy` | `RolloutStrategy.CANARY` |
| `percentage` | `int` | `10` |
| `metric` | `str` | `'latency_p95'` |
| `threshold` | `float` | `0.0` |
| `auto_rollback` | `bool` | `True` |
| `step_interval_seconds` | `int` | `300` |

### `DriftReport`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Result of a drift detection analysis.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `method` | `DriftMethod` | `` |
| `score` | `float` | `` |
| `threshold` | `float` | `` |
| `is_drifted` | `bool` | `` |
| `feature_scores` | `dict[str, float]` | `field(default_factory=dict)` |
| `window_start` | `str` | `''` |
| `window_end` | `str` | `''` |

### `CircuitBreakerConfig`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Configuration for inference circuit breaker.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `failure_threshold` | `int` | `5` |
| `success_threshold` | `int` | `3` |
| `timeout_seconds` | `float` | `30.0` |
| `half_open_max_calls` | `int` | `3` |

### `TokenUsage`

- Source: `aquilia/mlops/_types.py`
- Bases: `object`
- Summary: Token usage tracking for LLM inference.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `prompt_tokens` | `int` | `0` |
| `completion_tokens` | `int` | `0` |
| `total_tokens` | `int` | `0` |
| `tokens_per_second` | `float` | `0.0` |
| `time_to_first_token_ms` | `float` | `0.0` |
| `kv_cache_usage_mb` | `float` | `0.0` |

### `StorageAdapter`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Summary: Protocol for blob storage backends.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes)` | Store blob, return storage path. |
| `get_blob` | `async def get_blob(self, digest: str)` | Retrieve blob by digest. |
| `has_blob` | `async def has_blob(self, digest: str)` | Check if blob exists. |
| `delete_blob` | `async def delete_blob(self, digest: str)` | Delete blob. |
| `list_blobs` | `async def list_blobs(self)` | List all blob digests. |

### `Runtime`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Summary: Protocol for model runtime backends.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` | Prepare runtime with modelpack artifacts. |
| `load` | `async def load(self)` | Load model into memory. |
| `infer` | `async def infer(self, batch: BatchRequest)` | Run inference on a batch. |
| `health` | `async def health(self)` | Health check. |
| `metrics` | `async def metrics(self)` | Collect runtime metrics. |
| `unload` | `async def unload(self)` | Unload model and free resources. |

### `StreamingRuntime`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Summary: Protocol for runtimes that support streaming inference (LLMs).
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` |  |
| `load` | `async def load(self)` |  |
| `unload` | `async def unload(self)` |  |
| `infer` | `async def infer(self, batch: BatchRequest)` | Non-streaming inference. |
| `stream_infer` | `async def stream_infer(self, request: InferenceRequest)` | Stream tokens one at a time. |
| `health` | `async def health(self)` |  |
| `metrics` | `async def metrics(self)` |  |
| `token_usage` | `async def token_usage(self)` | Return current token usage stats. |
| `memory_info` | `async def memory_info(self)` | Return memory/device usage info. |

### `PluginHook`

- Source: `aquilia/mlops/_types.py`
- Bases: `Protocol`
- Summary: Protocol for plugin lifecycle hooks.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_load` | `async def on_load(self, context: dict[str, Any])` |  |
| `on_prepare` | `async def on_prepare(self, manifest: ModelpackManifest)` |  |
| `on_infer` | `async def on_infer(self, batch: BatchRequest, results: list[InferenceResult])` |  |
| `on_stream_chunk` | `async def on_stream_chunk(self, chunk: StreamChunk)` |  |
| `on_unload` | `async def on_unload(self)` |  |

### `TensorSpecBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates and renders tensor specifications.

### `BlobRefBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates blob references.

### `ProvenanceBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates provenance metadata.

### `ModelpackManifestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Full manifest blueprint with deep validation.

### `InferenceRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates incoming inference request payloads.

### `InferenceResultBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders inference results for API responses.

### `DriftReportBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders drift detection reports.

### `RolloutConfigBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates rollout configuration payloads.

### `RolloutStateBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders rollout state for API responses.

### `ScalingPolicyBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates autoscaler policy configuration.

### `NodeInfoBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates compute node registration payloads.

### `PlacementRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates model placement request payloads.

### `PluginDescriptorBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders plugin descriptor for API responses.

### `MetricsSummaryBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders metrics summary for API responses.

### `LLMConfigBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates LLM configuration payloads.

### `StreamChunkBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders a single streaming token/chunk for SSE responses.

### `TokenUsageBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders token usage statistics for LLM inference.

### `LLMInferenceRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates incoming LLM inference request payloads.

### `LLMInferenceResultBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders LLM inference results including token metrics.

### `ChatMessageBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates a single chat message.

### `ChatRequestBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Validates chat-style LLM request payloads.

### `ChatResponseBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders chat-style LLM response.

### `CircuitBreakerStatusBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders circuit breaker state for API responses.

### `RateLimiterStatusBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders rate limiter state for API responses.

### `MemoryStatusBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders memory tracker state for API responses.

### `ModelCapabilitiesBlueprint`

- Source: `aquilia/mlops/api/blueprints.py`
- Bases: `Blueprint`
- Summary: Renders model capabilities for API responses.

### `AquiliaModel`

- Source: `aquilia/mlops/api/model_class.py`
- Bases: `object`
- Summary: Base class for Aquilia ML models.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `async def load(self, artifacts_dir: str, device: str)` | Load model weights / artifacts into memory. |
| `unload` | `async def unload(self)` | Release model resources. Called during shutdown or hot reload. |
| `predict` | `async def predict(self, inputs: dict[str, Any])` | Run inference on preprocessed inputs. |
| `preprocess` | `async def preprocess(self, inputs: dict[str, Any])` | Transform raw inputs before prediction. |
| `postprocess` | `async def postprocess(self, outputs: dict[str, Any])` | Transform prediction outputs before returning to client. |
| `health` | `async def health(self)` | Custom health check. |
| `metrics` | `async def metrics(self)` | Custom metrics. |

### `RouteDefinition`

- Source: `aquilia/mlops/api/route_generator.py`
- Bases: `object`
- Summary: A generated route definition ready for controller compilation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `method` | `str` | `` |
| `path` | `str` | `` |
| `handler` | `Callable` | `` |
| `model_name` | `str` | `''` |
| `description` | `str` | `''` |

### `RouteGenerator`

- Source: `aquilia/mlops/api/route_generator.py`
- Bases: `object`
- Summary: Generates HTTP route definitions from registered models.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate` | `def generate(self)` | Generate all route definitions for all registered models. |
| `route_table` | `def route_table(self)` | Return a human-readable route table. |

### `MLOpsConfig`

- Source: `aquilia/mlops/di/providers.py`
- Bases: `object`
- Summary: Typed configuration for MLOps DI registration.

### `MLOpsFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `Fault`
- Summary: Base fault for all MLOps operations.

### `PackFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for model packaging.

### `PackBuildFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PackFault`
- Summary: Model pack build failed.

### `PackIntegrityFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PackFault`
- Summary: Blob integrity check failed (SHA-256 mismatch) or structural issue.

### `PackSignatureFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PackFault`
- Summary: Artifact signature verification failed.

### `RegistryFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for registry operations.

### `RegistryConnectionFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RegistryFault`
- Summary: Cannot connect to registry backend.

### `PackNotFoundFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RegistryFault`
- Summary: Requested modelpack not found in registry.

### `ImmutabilityViolationFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RegistryFault`
- Summary: Attempted to overwrite an immutable artifact.

### `ServingFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for model serving.

### `RuntimeLoadFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Model failed to load into runtime.

### `InferenceFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Inference failed for a request.

### `BatchTimeoutFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Batch processing exceeded deadline.

### `WarmupFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ServingFault`
- Summary: Model warm-up failed.

### `ObserveFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for observability.

### `DriftDetectionFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ObserveFault`
- Summary: Drift detection computation failed.

### `MetricsExportFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `ObserveFault`
- Summary: Metrics export/scrape failed.

### `RolloutFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for release management.

### `RolloutAdvanceFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RolloutFault`
- Summary: Rollout advancement failed due to metric degradation.

### `AutoRollbackFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `RolloutFault`
- Summary: Automatic rollback triggered.

### `SchedulerFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for scheduling.

### `PlacementFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `SchedulerFault`
- Summary: No suitable node found for model placement.

### `ScalingFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `SchedulerFault`
- Summary: Scaling operation failed.

### `MLOpsSecurityFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for MLOps security.

### `SigningFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsSecurityFault`
- Summary: Artifact signing failed.

### `PermissionDeniedFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsSecurityFault`
- Summary: User lacks required RBAC permission.

### `EncryptionFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsSecurityFault`
- Summary: Encryption / decryption operation failed.

### `PluginFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for plugin operations.

### `PluginLoadFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PluginFault`
- Summary: Plugin failed to load.

### `PluginHookFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `PluginFault`
- Summary: Plugin hook execution failed.

### `CircuitBreakerFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for circuit breaker events.

### `CircuitBreakerOpenFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `CircuitBreakerFault`
- Summary: Circuit breaker is OPEN -- requests are being rejected.

### `CircuitBreakerExhaustedFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `CircuitBreakerFault`
- Summary: Circuit breaker half-open probe failed -- returning to OPEN state.

### `RateLimitFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Request rejected due to rate limiting.

### `StreamingFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for streaming inference.

### `StreamInterruptedFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `StreamingFault`
- Summary: Streaming generation was interrupted (client disconnect, timeout, etc.).

### `TokenLimitExceededFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `StreamingFault`
- Summary: Token generation exceeded max_tokens limit.

### `MemoryFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MLOpsFault`
- Summary: Base fault for memory management.

### `MemorySoftLimitFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MemoryFault`
- Summary: Memory usage crossed soft limit -- eviction candidates available.

### `MemoryHardLimitFault`

- Source: `aquilia/mlops/engine/faults.py`
- Bases: `MemoryFault`
- Summary: Memory usage crossed hard limit -- requests must be rejected.

### `HookRegistry`

- Source: `aquilia/mlops/engine/hooks.py`
- Bases: `object`
- Summary: Collected hooks from a model class.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, kind: str)` | Get hooks by kind name. |
| `has` | `def has(self, kind: str)` | Check if any hooks of this kind are registered. |
| `summary` | `def summary(self)` | Return counts of registered hooks per kind. |

### `MLOpsManifest`

- Source: `aquilia/mlops/engine/module.py`
- Bases: `object`
- Summary: Aquilary-compatible manifest for the MLOps subsystem.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `` | `'mlops'` |
| `version` | `` | `'1.0.0'` |
| `description` | `` | `'Aquilia MLOps Platform -- model packaging, registry, serving & observability'` |
| `depends_on` | `list[str]` | `[]` |
| `controllers` | `list[str]` | `['aquilia.mlops.serving.controllers.MLOpsController']` |
| `services` | `list[str]` | `['aquilia.mlops.registry.service.RegistryService', 'aquilia.mlops.observe.metrics.MetricsCollector', 'aquilia.mlops.observe.drift.DriftDetector', 'aquilia.mlops.observe.logger.PredictionLogger', 'aquilia.mlops.serving.server.ModelServingServer', 'aquilia.mlops.serving.batching.DynamicBatcher', 'aquilia.mlops.plugins.host.PluginHost', 'aquilia.mlops.release.rollout.RolloutEngine', 'aquilia.mlops.scheduler.autoscaler.Autoscaler', 'aquilia.mlops.scheduler.placement.PlacementScheduler', 'aquilia.mlops.security.rbac.RBACManager', 'aquilia.mlops.security.signing.ArtifactSigner', 'aquilia.mlops.security.encryption.EncryptionManager', 'aquilia.mlops._structures.CircuitBreaker', 'aquilia.mlops._structures.TokenBucketRateLimiter', 'aquilia.mlops._structures.MemoryTracker']` |
| `effects` | `list[str]` | `['CacheEffect:mlops', 'CacheEffect:mlops.registry']` |
| `fault_domains` | `list[str]` | `['mlops', 'mlops.pack', 'mlops.registry', 'mlops.serving', 'mlops.observe', 'mlops.release', 'mlops.scheduler', 'mlops.security', 'mlops.plugin', 'mlops.resilience', 'mlops.streaming', 'mlops.memory']` |
| `middleware` | `list[tuple[str, dict]]` | `[('aquilia.mlops.serving.middleware.mlops_request_id_middleware', {'scope': 'app:mlops', 'priority': 5}), ('aquilia.mlops.serving.middleware.mlops_rate_limit_middleware', {'scope': 'app:mlops', 'priority': 10}), ('aquilia.mlops.serving.middleware.mlops_circuit_breaker_middleware', {'scope': 'app:mlops', 'priority': 20}), ('aquilia.mlops.serving.middleware.mlops_metrics_middleware', {'scope': 'app:mlops', 'priority': 30})]` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_startup` | `async def on_startup(config: dict[str, Any] \| None=None, **kwargs: Any)` |  |
| `on_shutdown` | `async def on_shutdown(**kwargs: Any)` |  |

### `PipelineContext`

- Source: `aquilia/mlops/engine/pipeline.py`
- Bases: `object`
- Summary: Per-request context flowing through the pipeline.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `request_id` | `str` | `` |
| `model_name` | `str` | `''` |
| `model_version` | `str` | `''` |
| `trace_id` | `str` | `''` |
| `start_time` | `float` | `field(default_factory=time.monotonic)` |
| `stage_timings` | `dict[str, float]` | `field(default_factory=dict)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### `InferencePipeline`

- Source: `aquilia/mlops/engine/pipeline.py`
- Bases: `object`
- Summary: Async inference pipeline with hooks and metrics.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `execute` | `async def execute(self, request: InferenceRequest, model_name: str='', model_version: str='')` | Execute the full inference pipeline for a single request. |
| `execute_batch` | `async def execute_batch(self, requests: list[InferenceRequest], model_name: str='', model_version: str='')` | Execute the pipeline for multiple requests concurrently. |

### `ExplainMethod`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `str, Enum`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SHAP_KERNEL` | `` | `'shap_kernel'` |
| `SHAP_TREE` | `` | `'shap_tree'` |
| `SHAP_DEEP` | `` | `'shap_deep'` |
| `LIME_TABULAR` | `` | `'lime_tabular'` |
| `LIME_TEXT` | `` | `'lime_text'` |
| `LIME_IMAGE` | `` | `'lime_image'` |

### `FeatureAttribution`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Summary: Single feature's contribution.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `value` | `float` | `` |
| `base_value` | `float` | `` |

### `Explanation`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Summary: Complete explanation for one prediction.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `method` | `ExplainMethod` | `` |
| `attributions` | `list[FeatureAttribution]` | `` |
| `prediction` | `Any` | `None` |
| `extra` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `top_k` | `def top_k(self)` | Top 10 features by absolute attribution. |
| `to_dict` | `def to_dict(self)` |  |

### `SHAPExplainer`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Summary: Wraps ``shap.KernelExplainer``, ``shap.TreeExplainer`` or ``shap.DeepExplainer`` behind a single ``explain()`` call.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `explain` | `def explain(self, instance: Any, **kwargs: Any)` | Compute SHAP values for *instance* (single row). |

### `LIMEExplainer`

- Source: `aquilia/mlops/explain/hooks.py`
- Bases: `object`
- Summary: Wraps ``lime.lime_tabular.LimeTabularExplainer`` (default) or ``lime.lime_text.LimeTextExplainer`` behind a single ``explain()`` call.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `explain` | `def explain(self, instance: Any, **kwargs: Any)` | Explain a single instance. |

### `PIIKind`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `str, Enum`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `EMAIL` | `` | `'email'` |
| `PHONE` | `` | `'phone'` |
| `SSN` | `` | `'ssn'` |
| `CREDIT_CARD` | `` | `'credit_card'` |
| `IP_ADDRESS` | `` | `'ip_address'` |
| `CUSTOM` | `` | `'custom'` |

### `PIIMatch`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `kind` | `PIIKind` | `` |
| `start` | `int` | `` |
| `end` | `int` | `` |
| `text` | `str` | `` |

### `PIIRedactor`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Summary: Scans text for PII and replaces matches with a configurable placeholder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `scan` | `def scan(self, text: str)` | Return all PII matches found in *text*. |
| `redact` | `def redact(self, text: str)` | Return *text* with all PII replaced. |
| `redact_dict` | `def redact_dict(self, data: dict[str, Any])` | Recursively redact string values in a dict. |

### `LaplaceNoise`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Summary: Adds calibrated Laplace noise to numeric values.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_noise` | `def add_noise(self, value: float)` | Return *value* + Laplace(0, scale). |
| `add_noise_array` | `def add_noise_array(self, values: Sequence[float])` |  |

### `InputSanitiser`

- Source: `aquilia/mlops/explain/privacy.py`
- Bases: `object`
- Summary: Pipeline of transforms applied to inference payloads before they reach the model.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_transform` | `def add_transform(self, fn: Callable[[dict[str, Any]], dict[str, Any]])` |  |
| `sanitise` | `def sanitise(self, payload: dict[str, Any])` |  |
| `default` | `def default(cls)` | Pre-configured sanitiser with PII redaction. |

### `ModelManifestEntry`

- Source: `aquilia/mlops/manifest/config.py`
- Bases: `object`
- Summary: Configuration for a single model from the manifest.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `class_path` | `str` | `` |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve_class` | `def resolve_class(self)` | Import and return the model class from its dotted path. |
| `to_config_dict` | `def to_config_dict(self)` | Convert to a config dict for ModelRegistry.register(). |

### `MLOpsManifestConfig`

- Source: `aquilia/mlops/manifest/config.py`
- Bases: `object`
- Summary: Parsed ``[mlops]`` configuration from Aquilia workspace config.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `default_device` | `str` | `'auto'` |
| `default_workers` | `int` | `4` |
| `default_batch_size` | `int` | `16` |
| `default_max_batch_latency_ms` | `float` | `50.0` |
| `default_timeout_ms` | `float` | `30000.0` |
| `route_prefix` | `str` | `'/mlops'` |
| `models` | `list[ModelManifestEntry]` | `field(default_factory=list)` |

### `ManifestValidationError`

- Source: `aquilia/mlops/manifest/schema.py`
- Bases: `ValueError`
- Summary: Raised when manifest validation fails.

### `DriftDetector`

- Source: `aquilia/mlops/observe/drift.py`
- Bases: `object`
- Summary: Model drift detection engine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `set_reference` | `def set_reference(self, data: dict[str, Sequence[float]])` | Set the reference (training) distribution. |
| `detect` | `def detect(self, current: dict[str, Sequence[float]], window_start: str='', window_end: str='')` | Run drift detection against the reference distribution. |
| `check` | `def check(self, reference: Sequence[float], current: Sequence[float], feature_name: str='feature')` | Quick single-feature drift check (no need to set reference first). |

### `PredictionLogger`

- Source: `aquilia/mlops/observe/logger.py`
- Bases: `object`
- Summary: Logs feature/prediction pairs for monitoring, debugging, and retraining.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `set_sink` | `def set_sink(self, sink: Callable[[dict[str, Any]], None])` | Set a custom log sink function. |
| `log` | `def log(self, request: InferenceRequest, result: InferenceResult, *, force: bool=False)` | Log a request/result pair (subject to sampling). |
| `get_log_count` | `def get_log_count(self)` |  |

### `MetricPoint`

- Source: `aquilia/mlops/observe/metrics.py`
- Bases: `object`
- Summary: Single metric data point.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `value` | `float` | `` |
| `labels` | `dict[str, str]` | `field(default_factory=dict)` |
| `timestamp` | `float` | `field(default_factory=time.time)` |

### `MetricsCollector`

- Source: `aquilia/mlops/observe/metrics.py`
- Bases: `object`
- Summary: In-process metrics collector with Prometheus text format export.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `total_inferences` | `def total_inferences(self)` | Total number of inference requests processed. |
| `total_tokens` | `def total_tokens(self)` | Total tokens generated across all requests. |
| `inc` | `def inc(self, name: str, value: float=1.0)` | Increment a counter. |
| `set_gauge` | `def set_gauge(self, name: str, value: float)` | Set a gauge value. |
| `observe` | `def observe(self, name: str, value: float)` | Record a histogram observation (bounded ring buffer). |
| `inc_for_model` | `def inc_for_model(self, model_name: str, name: str, value: float=1.0)` | Increment a counter scoped to a specific model. |
| `observe_for_model` | `def observe_for_model(self, model_name: str, name: str, value: float)` | Record a histogram observation scoped to a specific model. |
| `model_summary` | `def model_summary(self, model_name: str)` | Get metrics summary scoped to a specific model. |
| `record_inference` | `def record_inference(self, latency_ms: float, batch_size: int=1, error: bool=False, model_name: str='', token_count: int=0, prompt_tokens: int=0, streaming: bool=False, time_to_first_token_ms: float=0.0)` | Record an inference event (convenience method). |
| `hot_models` | `def hot_models(self, k: int=10)` | Return the top-K most-active models. |
| `percentile` | `def percentile(self, name: str, p: float)` | Compute p-th percentile for a histogram metric. |
| `ewma` | `def ewma(self, name: str)` | Return the EWMA-smoothed value for a metric. |
| `get_summary` | `def get_summary(self)` | Get a summary of all metrics as a dict. |
| `to_prometheus` | `def to_prometheus(self)` | Export all metrics in Prometheus text exposition format. |
| `reset` | `def reset(self)` | Reset all metrics. |

### `ExportResult`

- Source: `aquilia/mlops/optimizer/export.py`
- Bases: `object`
- Summary: Result of an edge export.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `target` | `str` | `` |
| `output_path` | `str` | `` |
| `size_bytes` | `int` | `` |
| `notes` | `list[str]` | `` |

### `EdgeExporter`

- Source: `aquilia/mlops/optimizer/export.py`
- Bases: `object`
- Summary: Export models to edge-friendly formats.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `export` | `async def export(self, model_path: str, target: ExportTarget, output_dir: str='.', optimize: bool=True)` | Export model to edge target format. |

### `OptimizationResult`

- Source: `aquilia/mlops/optimizer/pipeline.py`
- Bases: `object`
- Summary: Result of an optimization pass.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `original_size_bytes` | `int` | `` |
| `optimized_size_bytes` | `int` | `` |
| `original_path` | `str` | `` |
| `optimized_path` | `str` | `` |
| `preset` | `str` | `` |
| `compression_ratio` | `float` | `0.0` |
| `notes` | `list[str]` | `None` |

### `OptimizationPipeline`

- Source: `aquilia/mlops/optimizer/pipeline.py`
- Bases: `object`
- Summary: Runs a sequence of optimization passes on model files.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `run` | `async def run(self, model_path: str, preset: QuantizePreset=QuantizePreset.DYNAMIC, output_dir: str='.')` | Run optimization pipeline. |

### `LoadedModel`

- Source: `aquilia/mlops/orchestrator/loader.py`
- Bases: `object`
- Summary: Container for a loaded model instance and its associated resources.

### `ModelLoader`

- Source: `aquilia/mlops/orchestrator/loader.py`
- Bases: `object`
- Summary: Manages model instantiation, loading, unloading, and hot reload.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `ensure_loaded` | `async def ensure_loaded(self, name: str, version: str)` | Ensure a model is loaded and return its ``LoadedModel``. |
| `hot_reload` | `async def hot_reload(self, name: str, new_version: str)` | Hot-reload a model to a new version. |
| `unload` | `async def unload(self, name: str, version: str)` | Unload a specific model version. |
| `unload_all` | `async def unload_all(self)` | Unload all loaded models (shutdown). |
| `is_loaded` | `def is_loaded(self, name: str, version: str)` | Check if a model version is currently loaded. |
| `get_loaded` | `def get_loaded(self, name: str, version: str)` | Get a loaded model instance if available. |
| `loaded_models` | `def loaded_models(self)` | List all currently loaded model keys. |
| `summary` | `def summary(self)` | Summary for health endpoints. |

### `ModelOrchestrator`

- Source: `aquilia/mlops/orchestrator/orchestrator.py`
- Bases: `object`
- Summary: Top-level inference façade.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `predict` | `async def predict(self, model_name: str, inputs: dict[str, Any], parameters: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, request_id: str='')` | Run a prediction through the full orchestrated pipeline. |
| `predict_batch` | `async def predict_batch(self, model_name: str, batch_inputs: list[dict[str, Any]], parameters: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None)` | Run batch predictions. |
| `stream_predict` | `async def stream_predict(self, model_name: str, inputs: dict[str, Any], parameters: dict[str, Any] \| None=None, headers: dict[str, str] \| None=None, request_id: str='')` | Stream inference for LLM models. |
| `get_health` | `async def get_health(self, model_name: str \| None=None)` | Get health status for one model or all models. |
| `get_metrics` | `async def get_metrics(self, model_name: str \| None=None)` | Get metrics for one model or all models. |
| `list_models` | `async def list_models(self)` | List all registered models with their status. |
| `reload_model` | `async def reload_model(self, model_name: str, version: str)` | Hot-reload a model to a specific version. |
| `unload_model` | `async def unload_model(self, model_name: str, version: str \| None=None)` | Unload a specific model version. |
| `shutdown` | `async def shutdown(self)` | Graceful shutdown -- unload all models. |

### `ModelBundle`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `object`
- Summary: A complete model bundle ready for persistence.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |
| `weights_path` | `Path` | `` |
| `metadata` | `dict[str, Any]` | `` |
| `framework` | `str` | `` |
| `dtype` | `str` | `` |

### `ModelLoader`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `abc.ABC`
- Summary: Abstract base class for framework-specific model loaders.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `def load(self, path: Path, **kwargs)` | Load model from path. |

### `ModelSaver`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `abc.ABC`
- Summary: Abstract base class for framework-specific model savers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save` | `def save(self, model: Any, path: Path, **kwargs)` | Save model to path. |

### `PyTorchModelLoader`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `ModelLoader`
- Summary: Production-grade PyTorch model loader.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `def load(self, path: Path, device: str='cpu', **kwargs)` |  |

### `PyTorchModelSaver`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `ModelSaver`
- Summary: Production-grade PyTorch model saver.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save` | `def save(self, model: Any, path: Path, **kwargs)` |  |

### `ModelPersistenceManager`

- Source: `aquilia/mlops/orchestrator/persistence.py`
- Bases: `object`
- Summary: Orchestrates high-level model persistence operations.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register_framework` | `def register_framework(self, name: str, loader: ModelLoader, saver: ModelSaver)` |  |
| `save_bundle` | `async def save_bundle(self, bundle: ModelBundle)` | Save a complete model bundle. |
| `load_model` | `async def load_model(self, name: str, version: str, device: str='cpu')` | Load a model by name and version. |

### `ModelConfig`

- Source: `aquilia/mlops/orchestrator/registry.py`
- Bases: `object`
- Summary: Per-model configuration (from manifest or decorator).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `from_dict` | `def from_dict(cls, d: dict[str, Any])` |  |

### `ModelEntry`

- Source: `aquilia/mlops/orchestrator/registry.py`
- Bases: `object`
- Summary: Registry entry for a single model version.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |
| `model_class` | `Any` | `` |
| `config` | `ModelConfig` | `field(default_factory=ModelConfig)` |
| `state` | `ModelState` | `ModelState.UNLOADED` |
| `registered_at` | `float` | `field(default_factory=time.time)` |
| `supports_streaming` | `bool` | `False` |
| `tags` | `list[str]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `key` | `def key(self)` | Unique key for this model version. |
| `to_dict` | `def to_dict(self)` | Serialize for API responses. |

### `ModelRegistry`

- Source: `aquilia/mlops/orchestrator/registry.py`
- Bases: `object`
- Summary: In-memory metadata-only model registry.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `async def register(self, name: str, model_class: Any, version: str='v1', config: dict[str, Any] \| None=None, supports_streaming: bool=False, tags: list[str] \| None=None, set_active: bool=True)` | Register a model (metadata only -- no loading). |
| `register_sync` | `def register_sync(self, name: str, model_class: Any, version: str='v1', config: dict[str, Any] \| None=None, supports_streaming: bool=False, tags: list[str] \| None=None, set_active: bool=True)` | Synchronous registration (for use at import time via decorators). |
| `get` | `def get(self, name: str, version: str \| None=None)` | Get a model entry by name and optional version. |
| `get_active_version` | `def get_active_version(self, name: str)` | Get the active version for a model. |
| `list_models` | `def list_models(self)` | List all unique model names. |
| `list_versions` | `def list_versions(self, name: str)` | List all versions of a model. |
| `list_entries` | `def list_entries(self)` | List all model entries. |
| `has` | `def has(self, name: str, version: str \| None=None)` | Check if a model (and optionally a specific version) is registered. |
| `update_state` | `def update_state(self, name: str, version: str, state: ModelState)` | Update the lifecycle state of a model entry. |
| `set_active_version` | `async def set_active_version(self, name: str, version: str)` | Set the active version for a model. |
| `unregister` | `async def unregister(self, name: str, version: str)` | Remove a model version from the registry. |
| `summary` | `def summary(self)` | Summary for health/debug endpoints. |

### `CanaryConfig`

- Source: `aquilia/mlops/orchestrator/router.py`
- Bases: `object`
- Summary: Active canary configuration for a model.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `canary_version` | `str` | `` |
| `base_version` | `str` | `` |
| `percentage` | `float` | `10.0` |

### `VersionRouter`

- Source: `aquilia/mlops/orchestrator/router.py`
- Bases: `object`
- Summary: Routes inference requests to the correct model version.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `VERSION_HEADER` | `` | `'x-model-version'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `route` | `async def route(self, model_name: str, headers: dict[str, str] \| None=None, metadata: dict[str, Any] \| None=None)` | Resolve which model version should handle this request. |
| `set_canary` | `def set_canary(self, model_name: str, canary_version: str, percentage: float=10.0, base_version: str \| None=None)` | Configure canary routing for a model. |
| `clear_canary` | `def clear_canary(self, model_name: str)` | Remove canary routing for a model. |
| `get_canary` | `def get_canary(self, model_name: str)` | Get the active canary config for a model. |
| `has_canary` | `def has_canary(self, model_name: str)` | Check if a canary is active for a model. |
| `summary` | `def summary(self)` | Canary routing summary. |

### `VersionManager`

- Source: `aquilia/mlops/orchestrator/versioning.py`
- Bases: `object`
- Summary: Version Management for ML models.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `promote` | `async def promote(self, name: str, from_version: str, to_tag: str='active')` | Promote a model version to the active slot. |
| `rollback` | `async def rollback(self, name: str)` | Roll back to the previous active version. |
| `history` | `def history(self, name: str)` | Return the version rollback history for a model. |
| `can_rollback` | `def can_rollback(self, name: str)` | Check if a rollback is available. |

### `ModelpackBuilder`

- Source: `aquilia/mlops/pack/builder.py`
- Bases: `object`
- Summary: Builds a modelpack archive from local files.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_model` | `def add_model(self, path: str, *, framework: str \| None=None, entrypoint: bool=True)` | Add a model file to the pack. |
| `add_file` | `def add_file(self, path: str)` | Add an auxiliary file to the pack. |
| `add_env_lock` | `def add_env_lock(self, path: str)` | Set the environment lock file. |
| `set_signature` | `def set_signature(self, inputs: list[TensorSpec], outputs: list[TensorSpec])` | Set the inference signature. |
| `set_provenance` | `def set_provenance(self, git_sha: str='', dataset_snapshot: str='', dockerfile: str='')` | Set provenance metadata. |
| `set_metadata` | `def set_metadata(self, **kwargs: Any)` | Set arbitrary metadata key-value pairs. |
| `save` | `async def save(self, output_dir: str='.', *, content_store: ContentStore \| None=None, sign_key: str \| None=None)` | Build the ``.aquilia`` archive and return its path. |
| `unpack` | `async def unpack(archive_path: str, output_dir: str='.')` | Unpack a ``.aquilia`` archive and return its manifest. |
| `inspect` | `async def inspect(archive_path: str)` | Read manifest from archive without full extraction. |

### `ContentStore`

- Source: `aquilia/mlops/pack/content_store.py`
- Bases: `object`
- Summary: Local filesystem content-addressable blob store.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `store` | `async def store(self, digest: str, data: bytes)` | Store blob by digest. Idempotent -- skips if already exists. |
| `retrieve` | `async def retrieve(self, digest: str)` | Retrieve blob by digest. |
| `exists` | `async def exists(self, digest: str)` | Check if blob exists. |
| `delete` | `async def delete(self, digest: str)` | Delete blob by digest. |
| `list_digests` | `async def list_digests(self)` | List all stored blob digests. |
| `gc` | `async def gc(self, referenced_digests: set[str])` | Garbage-collect unreferenced blobs. |
| `size_bytes` | `def size_bytes(self)` | Total size of all stored blobs in bytes. |

### `SignatureError`

- Source: `aquilia/mlops/pack/signer.py`
- Bases: `Exception`
- Summary: Raised when signature verification fails.

### `HMACSigner`

- Source: `aquilia/mlops/pack/signer.py`
- Bases: `object`
- Summary: HMAC-SHA256 signer for modelpack archives.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign` | `def sign(self, data: bytes)` | Produce an HMAC-SHA256 hex signature. |
| `verify` | `def verify(self, data: bytes, signature: str)` | Verify an HMAC-SHA256 hex signature. |

### `RSASigner`

- Source: `aquilia/mlops/pack/signer.py`
- Bases: `object`
- Summary: RSA signer using ``cryptography`` (already an Aquilia dependency).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign` | `def sign(self, data: bytes)` | Sign data with RSA private key. |
| `verify` | `def verify(self, data: bytes, signature: bytes)` | Verify RSA signature with public key. |

### `HealthCheckPlugin`

- Source: `aquilia/mlops/plugins/example_plugin.py`
- Bases: `object`
- Summary: Minimal example plugin implementing the ``PluginHook`` protocol.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `` | `'health-check'` |
| `version` | `` | `'0.1.0'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `activate` | `def activate(self, ctx: dict[str, Any])` |  |
| `deactivate` | `def deactivate(self)` |  |
| `stats` | `def stats(self)` |  |

### `PluginState`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `str, Enum`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DISCOVERED` | `` | `'discovered'` |
| `LOADED` | `` | `'loaded'` |
| `ACTIVATED` | `` | `'activated'` |
| `DEACTIVATED` | `` | `'deactivated'` |
| `ERROR` | `` | `'error'` |

### `PluginDescriptor`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `object`
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |
| `module` | `str` | `` |
| `state` | `PluginState` | `PluginState.DISCOVERED` |
| `instance` | `Any` | `None` |
| `error` | `str \| None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### `PluginHookProtocol`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `Protocol`
- Summary: Minimal interface a plugin must satisfy.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `activate` | `def activate(self, ctx: dict[str, Any])` |  |
| `deactivate` | `def deactivate(self)` |  |

### `PluginHost`

- Source: `aquilia/mlops/plugins/host.py`
- Bases: `object`
- Summary: Central plugin manager.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `discover_entrypoints` | `def discover_entrypoints(self)` | Scan installed packages for plugins. |
| `register` | `def register(self, plugin: Any)` | Manually register a plugin class or instance. |
| `load` | `def load(self, name: str)` | Import and instantiate a discovered plugin. |
| `activate` | `def activate(self, name: str, ctx: dict[str, Any] \| None=None)` | Activate a loaded plugin. |
| `deactivate` | `def deactivate(self, name: str)` | Deactivate a running plugin. |
| `activate_all` | `def activate_all(self, ctx: dict[str, Any] \| None=None)` |  |
| `deactivate_all` | `def deactivate_all(self)` |  |
| `on` | `def on(self, event: str, callback: Callable)` | Register a hook callback for *event*. |
| `emit` | `def emit(self, event: str, **kwargs: Any)` | Fire all callbacks for *event* and collect results. |
| `list_plugins` | `def list_plugins(self)` |  |
| `get` | `def get(self, name: str)` |  |
| `active_plugins` | `def active_plugins(self)` |  |

### `MarketplaceEntry`

- Source: `aquilia/mlops/plugins/marketplace.py`
- Bases: `object`
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |
| `description` | `str` | `` |
| `author` | `str` | `` |
| `pypi_name` | `str` | `` |
| `homepage` | `str` | `''` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `downloads` | `int` | `0` |
| `verified` | `bool` | `False` |

### `PluginMarketplace`

- Source: `aquilia/mlops/plugins/marketplace.py`
- Bases: `object`
- Summary: Browse and install plugins from a remote JSON index.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `fetch_index` | `async def fetch_index(self)` | Download the plugin index. |
| `search` | `def search(self, query: str, *, tags: list[str] \| None=None, verified_only: bool=False)` | Search the cached index. |
| `install` | `def install(self, entry_or_name: MarketplaceEntry \| str)` | Install a plugin via pip. |
| `uninstall` | `def uninstall(self, pypi_name: str)` | Uninstall a plugin package. |

### `RegistryDB`

- Source: `aquilia/mlops/registry/models.py`
- Bases: `object`
- Summary: Async SQLite backend for registry metadata.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Create tables if they don't exist. |
| `close` | `async def close(self)` |  |
| `insert_pack` | `async def insert_pack(self, name: str, tag: str, digest: str, manifest_json: str, signed_by: str='')` | Insert a pack record. Ignores if digest already exists. |
| `get_pack` | `async def get_pack(self, name: str, tag: str)` | Get pack by name:tag via the tags table. |
| `get_pack_by_digest` | `async def get_pack_by_digest(self, digest: str)` | Get pack by content digest. |
| `list_versions` | `async def list_versions(self, name: str)` | List all versions (tags) of a named pack. |
| `list_packs` | `async def list_packs(self, limit: int=100, offset: int=0)` | List distinct pack names with latest tag info. |
| `upsert_tag` | `async def upsert_tag(self, name: str, tag: str, digest: str)` | Insert or update a tag pointer. |
| `delete_tag` | `async def delete_tag(self, name: str, tag: str)` | Delete a tag. |
| `insert_blob` | `async def insert_blob(self, digest: str, size: int, storage_path: str='')` | Track a blob in the registry. |

### `RegistryError`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `Exception`
- Summary: Base error for registry operations (kept for backward compatibility).

### `PackNotFoundError`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `RegistryError`
- Summary: Raised when a modelpack is not found (kept for backward compatibility).

### `ImmutabilityError`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `RegistryError`
- Summary: Raised when attempting to overwrite an immutable artifact (kept for backward compatibility).

### `RegistryService`

- Source: `aquilia/mlops/registry/service.py`
- Bases: `object`
- Summary: Modelpack registry service.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize database schema. |
| `close` | `async def close(self)` | Close database connections. |
| `publish` | `async def publish(self, manifest: ModelpackManifest, blobs: dict[str, bytes] \| None=None, *, force: bool=False)` | Publish a modelpack to the registry. |
| `fetch` | `async def fetch(self, name: str, tag: str='latest')` | Fetch a modelpack manifest by name and tag. |
| `fetch_by_digest` | `async def fetch_by_digest(self, digest: str)` | Fetch a modelpack by its content digest (LRU-cached). |
| `cache_stats` | `def cache_stats(self)` | Return LRU cache hit/miss statistics. |
| `list_versions` | `async def list_versions(self, name: str)` | List all versions of a modelpack. |
| `list_packs` | `async def list_packs(self, limit: int=100, offset: int=0)` | List all modelpacks. |
| `promote` | `async def promote(self, name: str, tag: str, target_tag: str)` | Promote a modelpack tag to another tag (e.g., staging → production). |
| `delete` | `async def delete(self, name: str, tag: str)` | Delete a modelpack tag (admin only). |
| `verify` | `async def verify(self, name: str, tag: str)` | Verify integrity of a modelpack. |

### `BaseStorageAdapter`

- Source: `aquilia/mlops/registry/storage/base.py`
- Bases: `abc.ABC`
- Summary: Abstract base for blob storage backends.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes)` | Store a blob, return storage path or URI. |
| `get_blob` | `async def get_blob(self, digest: str)` | Retrieve a blob by digest. |
| `has_blob` | `async def has_blob(self, digest: str)` | Check if a blob exists. |
| `delete_blob` | `async def delete_blob(self, digest: str)` | Delete a blob. |
| `list_blobs` | `async def list_blobs(self)` | List all blob digests. |

### `FilesystemStorageAdapter`

- Source: `aquilia/mlops/registry/storage/filesystem.py`
- Bases: `BaseStorageAdapter`
- Summary: Store blobs on local filesystem in a content-addressable layout.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes)` |  |
| `get_blob` | `async def get_blob(self, digest: str)` |  |
| `has_blob` | `async def has_blob(self, digest: str)` |  |
| `delete_blob` | `async def delete_blob(self, digest: str)` |  |
| `list_blobs` | `async def list_blobs(self)` |  |

### `S3StorageAdapter`

- Source: `aquilia/mlops/registry/storage/s3.py`
- Bases: `BaseStorageAdapter`
- Summary: Store blobs in an S3-compatible bucket.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `put_blob` | `async def put_blob(self, digest: str, data: bytes)` |  |
| `get_blob` | `async def get_blob(self, digest: str)` |  |
| `has_blob` | `async def has_blob(self, digest: str)` |  |
| `delete_blob` | `async def delete_blob(self, digest: str)` |  |
| `list_blobs` | `async def list_blobs(self)` |  |

### `RolloutPhase`

- Source: `aquilia/mlops/release/rollout.py`
- Bases: `str, Enum`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PENDING` | `` | `'pending'` |
| `IN_PROGRESS` | `` | `'in_progress'` |
| `PAUSED` | `` | `'paused'` |
| `COMPLETED` | `` | `'completed'` |
| `ROLLED_BACK` | `` | `'rolled_back'` |
| `FAILED` | `` | `'failed'` |

### `RolloutState`

- Source: `aquilia/mlops/release/rollout.py`
- Bases: `object`
- Summary: Current state of a rollout.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str` | `` |
| `config` | `RolloutConfig` | `` |
| `phase` | `RolloutPhase` | `RolloutPhase.PENDING` |
| `current_percentage` | `int` | `0` |
| `steps_completed` | `int` | `0` |
| `started_at` | `float` | `0.0` |
| `completed_at` | `float` | `0.0` |
| `metrics_history` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `error` | `str` | `''` |

### `RolloutEngine`

- Source: `aquilia/mlops/release/rollout.py`
- Bases: `object`
- Summary: Manages progressive rollouts with metric-based gating.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `start` | `async def start(self, config: RolloutConfig)` | Start a new rollout. |
| `advance` | `async def advance(self, rollout_id: str, percentage: int \| None=None)` | Advance a rollout to a higher canary percentage. |
| `complete` | `async def complete(self, rollout_id: str)` | Complete a rollout (100% traffic to new version). |
| `rollback` | `async def rollback(self, rollout_id: str, reason: str='')` | Rollback a rollout to the original version. |
| `get_rollout` | `def get_rollout(self, rollout_id: str)` |  |
| `list_rollouts` | `def list_rollouts(self)` |  |

### `ModelState`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `str, Enum`
- Summary: Lifecycle states for a model runtime.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `UNLOADED` | `` | `'unloaded'` |
| `PREPARED` | `` | `'prepared'` |
| `LOADING` | `` | `'loading'` |
| `LOADED` | `` | `'loaded'` |
| `FAILED` | `` | `'failed'` |
| `UNLOADING` | `` | `'unloading'` |

### `InvalidStateTransition`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `RuntimeError`
- Summary: Raised when an illegal state transition is attempted.

### `BaseRuntime`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `abc.ABC`
- Summary: Abstract runtime for model inference.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `state` | `def state(self)` | Current model lifecycle state. |
| `is_loaded` | `def is_loaded(self)` | Backward-compatible loaded check. |
| `manifest` | `def manifest(self)` |  |
| `device` | `def device(self)` |  |
| `last_error` | `def last_error(self)` |  |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` | Prepare runtime with model artifacts (download, validate). |
| `load` | `async def load(self)` | Load model into memory / accelerator. |
| `infer` | `async def infer(self, batch: BatchRequest)` | Run inference on a batch of requests. |
| `preprocess` | `async def preprocess(self, raw_input: dict[str, Any])` | Transform raw request inputs before inference. |
| `postprocess` | `async def postprocess(self, raw_output: dict[str, Any])` | Transform raw model outputs before returning to the client. |
| `health` | `async def health(self)` | Health check. |
| `metrics` | `async def metrics(self)` | Collect runtime-specific metrics. |
| `unload` | `async def unload(self)` | Unload model and free resources. |
| `memory_info` | `async def memory_info(self)` | Return memory / device usage info (override in subclasses). |

### `BaseStreamingRuntime`

- Source: `aquilia/mlops/runtime/base.py`
- Bases: `BaseRuntime`
- Summary: Abstract runtime that adds streaming inference for LLM/SLM models.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `stream_infer` | `async def stream_infer(self, request: InferenceRequest)` | Stream tokens one at a time. Must be an async generator. |
| `token_usage` | `async def token_usage(self)` | Return lifetime token usage statistics. |
| `metrics` | `async def metrics(self)` | Extended metrics including token stats. |

### `BentoExporter`

- Source: `aquilia/mlops/runtime/bento_exporter.py`
- Bases: `BaseRuntime`
- Summary: Export modelpacks to BentoML service format.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` |  |
| `load` | `async def load(self)` |  |
| `infer` | `async def infer(self, batch: BatchRequest)` |  |
| `export_bento` | `async def export_bento(self, output_dir: str='.')` | Export a BentoML-compatible service file. |

### `DeviceKind`

- Source: `aquilia/mlops/runtime/device_manager.py`
- Bases: `str, Enum`
- Summary: Hardware device categories.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CPU` | `` | `'cpu'` |
| `CUDA` | `` | `'cuda'` |
| `MPS` | `` | `'mps'` |
| `NPU` | `` | `'npu'` |
| `TPU` | `` | `'tpu'` |

### `DeviceInfo`

- Source: `aquilia/mlops/runtime/device_manager.py`
- Bases: `object`
- Summary: Snapshot of a single compute device.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `kind` | `DeviceKind` | `` |
| `index` | `int` | `0` |
| `total_memory_mb` | `float` | `0.0` |
| `available_memory_mb` | `float` | `0.0` |
| `is_available` | `bool` | `True` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `utilization` | `def utilization(self)` | Memory utilization ratio (0.0–1.0). |
| `to_dict` | `def to_dict(self)` |  |

### `DeviceManager`

- Source: `aquilia/mlops/runtime/device_manager.py`
- Bases: `object`
- Summary: Centralized device management for ML runtimes.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Detect all available devices and populate the registry. |
| `select_device` | `async def select_device(self, preference: str='auto', memory_required_mb: float=0.0)` | Select the best device for a model load. |
| `acquire` | `def acquire(self, device_name: str)` | Acquire an exclusive lock on a device. |
| `refresh` | `async def refresh(self, device_name: str \| None=None)` | Refresh memory stats for one or all devices. |
| `get_device` | `def get_device(self, name: str)` | Get info for a specific device. |
| `list_devices` | `def list_devices(self)` | Return all known devices. |
| `default_device` | `def default_device(self)` |  |
| `summary` | `def summary(self)` | Return a summary dict suitable for health check responses. |

### `PoolKind`

- Source: `aquilia/mlops/runtime/executor.py`
- Bases: `str, Enum`
- Summary: Executor pool types.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `THREAD` | `` | `'thread'` |
| `PROCESS` | `` | `'process'` |

### `InferenceExecutor`

- Source: `aquilia/mlops/runtime/executor.py`
- Bases: `object`
- Summary: Async-compatible executor for CPU/GPU-bound inference work.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `start` | `async def start(self)` | Create the underlying executor pool. |
| `shutdown` | `async def shutdown(self, timeout: float=30.0)` | Gracefully shut down the executor. |
| `submit` | `async def submit(self, fn: Callable[..., T], *args: Any, **kwargs: Any)` | Submit a blocking callable and return its result asynchronously. |
| `is_running` | `def is_running(self)` |  |
| `active_tasks` | `def active_tasks(self)` |  |
| `max_workers` | `def max_workers(self)` |  |
| `metrics` | `def metrics(self)` | Return executor metrics for health/monitoring endpoints. |

### `ONNXRuntimeAdapter`

- Source: `aquilia/mlops/runtime/onnx_runtime.py`
- Bases: `BaseRuntime`
- Summary: ONNX Runtime inference adapter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` |  |
| `load` | `async def load(self)` |  |
| `infer` | `async def infer(self, batch: BatchRequest)` |  |
| `metrics` | `async def metrics(self)` |  |
| `unload` | `async def unload(self)` |  |

### `PythonRuntime`

- Source: `aquilia/mlops/runtime/python_runtime.py`
- Bases: `BaseStreamingRuntime`
- Summary: In-process Python runtime with LLM streaming support.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` | Prepare runtime: validate manifest, detect device. |
| `load` | `async def load(self)` | Load model into memory, transitioning through LOADING → LOADED. |
| `unload` | `async def unload(self)` | Unload model and free resources. |
| `infer` | `async def infer(self, batch: BatchRequest)` |  |
| `stream_infer` | `async def stream_infer(self, request: InferenceRequest)` | Stream tokens one at a time for LLM inference. |
| `preprocess` | `async def preprocess(self, raw_input: dict[str, Any])` | Default preprocessing -- identity pass-through. |
| `postprocess` | `async def postprocess(self, raw_output: dict[str, Any])` | Default postprocessing -- identity pass-through. |
| `metrics` | `async def metrics(self)` |  |
| `memory_info` | `async def memory_info(self)` | Return GPU/CPU memory info. |
| `set_predict_fn` | `def set_predict_fn(self, fn: Callable)` | Set a custom prediction function. |

### `TorchServeExporter`

- Source: `aquilia/mlops/runtime/torchserve_exporter.py`
- Bases: `BaseRuntime`
- Summary: Export modelpacks to TorchServe ``.mar`` format and optionally forward inference via TorchServe REST API.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` |  |
| `load` | `async def load(self)` |  |
| `infer` | `async def infer(self, batch: BatchRequest)` |  |
| `export_mar` | `async def export_mar(self, output_dir: str='.')` | Export a TorchServe-compatible ``.mar`` archive. |

### `TritonAdapter`

- Source: `aquilia/mlops/runtime/triton_adapter.py`
- Bases: `BaseRuntime`
- Summary: Triton Inference Server adapter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `prepare` | `async def prepare(self, manifest: ModelpackManifest, model_dir: str)` |  |
| `load` | `async def load(self)` |  |
| `infer` | `async def infer(self, batch: BatchRequest)` |  |
| `unload` | `async def unload(self)` |  |

### `ScalingPolicy`

- Source: `aquilia/mlops/scheduler/autoscaler.py`
- Bases: `object`
- Summary: Autoscaling policy definition.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

### `ScalingDecision`

- Source: `aquilia/mlops/scheduler/autoscaler.py`
- Bases: `object`
- Summary: Output of a scaling evaluation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `current_replicas` | `int` | `` |
| `desired_replicas` | `int` | `` |
| `reason` | `str` | `` |
| `metrics` | `dict[str, float]` | `field(default_factory=dict)` |

### `Autoscaler`

- Source: `aquilia/mlops/scheduler/autoscaler.py`
- Bases: `object`
- Summary: Autoscaling engine for model serving deployments.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `record_request` | `def record_request(self, latency_ms: float=0.0, error: bool=False, tokens: int=0)` | Record a single request into the sliding windows. |
| `record_gpu_utilization` | `def record_gpu_utilization(self, utilization: float)` | Record GPU utilization (0.0-1.0) into the sliding window. |
| `window_rps` | `def window_rps(self)` | Current requests-per-second from the sliding window. |
| `window_avg_latency` | `def window_avg_latency(self)` | Average latency across the current window. |
| `window_error_rate` | `def window_error_rate(self)` | Error rate in the current window. |
| `window_stats` | `def window_stats(self)` | Summary of windowed metrics. |
| `evaluate` | `def evaluate(self, metrics: dict[str, float] \| None=None)` | Evaluate current metrics and decide on scaling. |
| `apply` | `def apply(self, decision: ScalingDecision)` | Apply a scaling decision (update internal state). |
| `generate_hpa_manifest` | `def generate_hpa_manifest(self, deployment_name: str, namespace: str='default')` | Generate a Kubernetes HorizontalPodAutoscaler manifest. |

### `NodeInfo`

- Source: `aquilia/mlops/scheduler/placement.py`
- Bases: `object`
- Summary: Information about a compute node.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `node_id` | `str` | `` |
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

### `PlacementRequest`

- Source: `aquilia/mlops/scheduler/placement.py`
- Bases: `object`
- Summary: Request for model placement.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `model_name` | `str` | `` |
| `model_size_mb` | `float` | `` |
| `preferred_device` | `str` | `'any'` |
| `gpu_required` | `bool` | `False` |
| `gpu_memory_required_mb` | `float` | `0.0` |
| `model_type` | `str` | `'SLM'` |
| `quantized` | `bool` | `False` |
| `min_compute_capability` | `str` | `''` |

### `PlacementScheduler`

- Source: `aquilia/mlops/scheduler/placement.py`
- Bases: `object`
- Summary: Greedy placement scheduler with soft device affinity.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register_node` | `def register_node(self, node: NodeInfo)` | Register a compute node. |
| `unregister_node` | `def unregister_node(self, node_id: str)` | Remove a node. |
| `update_node` | `def update_node(self, node_id: str, **kwargs: Any)` | Update node metrics. |
| `place` | `def place(self, request: PlacementRequest)` | Find the best node for a model placement request. |
| `rebalance` | `def rebalance(self)` | Suggest rebalancing moves to improve load distribution. |

### `BlobEncryptor`

- Source: `aquilia/mlops/security/encryption.py`
- Bases: `object`
- Summary: Encrypts / decrypts blob data at rest using Fernet (AES-128-CBC).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `encrypt` | `def encrypt(self, data: bytes)` |  |
| `decrypt` | `def decrypt(self, token: bytes)` |  |
| `key` | `def key(self)` |  |
| `from_key` | `def from_key(cls, key: bytes)` |  |

### `Permission`

- Source: `aquilia/mlops/security/rbac.py`
- Bases: `str, Enum`
- Summary: Registry permissions.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PACK_READ` | `` | `'pack:read'` |
| `PACK_WRITE` | `` | `'pack:write'` |
| `PACK_DELETE` | `` | `'pack:delete'` |
| `PACK_PROMOTE` | `` | `'pack:promote'` |
| `PACK_SIGN` | `` | `'pack:sign'` |
| `REGISTRY_ADMIN` | `` | `'registry:admin'` |
| `PLUGIN_INSTALL` | `` | `'plugin:install'` |
| `ROLLOUT_MANAGE` | `` | `'rollout:manage'` |

### `Role`

- Source: `aquilia/mlops/security/rbac.py`
- Bases: `object`
- Summary: A named role with a set of permissions.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `permissions` | `set[Permission]` | `field(default_factory=set)` |
| `description` | `str` | `''` |

### `RBACManager`

- Source: `aquilia/mlops/security/rbac.py`
- Bases: `object`
- Summary: Role-based access control for registry operations.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `assign_role` | `def assign_role(self, user_id: str, role_name: str)` |  |
| `revoke_role` | `def revoke_role(self, user_id: str, role_name: str)` |  |
| `check_permission` | `def check_permission(self, user_id: str, permission: Permission)` |  |
| `get_user_permissions` | `def get_user_permissions(self, user_id: str)` |  |
| `add_role` | `def add_role(self, role: Role)` |  |

### `ArtifactSigner`

- Source: `aquilia/mlops/security/signing.py`
- Bases: `object`
- Summary: Signs and verifies modelpack artifacts.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign` | `async def sign(self, archive_path: str)` | Sign an archive and return signature path. |
| `verify` | `async def verify(self, archive_path: str, sig_path: str)` | Verify an archive signature. |

### `EncryptionManager`

- Source: `aquilia/mlops/security/signing.py`
- Bases: `object`
- Summary: Encryption at rest for registry blob storage.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `encrypt` | `def encrypt(self, data: bytes)` | Encrypt data. |
| `decrypt` | `def decrypt(self, token: bytes)` | Decrypt data. |
| `key` | `def key(self)` |  |

### `DynamicBatcher`

- Source: `aquilia/mlops/serving/batching.py`
- Bases: `object`
- Summary: Async dynamic batching scheduler.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `start` | `async def start(self)` | Start the background batcher coroutine. |
| `stop` | `async def stop(self)` | Stop the batcher and drain remaining requests. |
| `submit` | `async def submit(self, request: InferenceRequest)` | Submit a single request and wait for its result. |
| `metrics` | `def metrics(self)` | Return batcher metrics. |

### `MLOpsController`

- Source: `aquilia/mlops/serving/controllers.py`
- Bases: `Controller`
- Summary: Controller for MLOps HTTP API.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `prefix` | `` | `'/mlops'` |
| `tags` | `list[str]` | `['mlops']` |
| `instantiation_mode` | `` | `'singleton'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `health` | `async def health(self, ctx: RequestCtx \| None=None)` | Platform health check -- ``GET /mlops/health``. |
| `predict` | `async def predict(self, body: dict[str, Any], ctx: RequestCtx \| None=None)` | Single inference -- ``POST /mlops/predict``. |
| `stream_predict` | `async def stream_predict(self, body: dict[str, Any], ctx: RequestCtx \| None=None)` | Streaming inference -- ``POST /mlops/stream``. |
| `chat` | `async def chat(self, body: dict[str, Any], ctx: RequestCtx \| None=None)` | Chat-style inference -- ``POST /mlops/chat``. |
| `circuit_breaker_status` | `async def circuit_breaker_status(self, ctx: RequestCtx \| None=None)` | Circuit breaker status -- ``GET /mlops/circuit-breaker``. |
| `rate_limit_status` | `async def rate_limit_status(self, ctx: RequestCtx \| None=None)` | Rate limiter status -- ``GET /mlops/rate-limit``. |
| `memory_status` | `async def memory_status(self, ctx: RequestCtx \| None=None)` | Memory tracker status -- ``GET /mlops/memory``. |
| `model_capabilities` | `async def model_capabilities(self, ctx: RequestCtx \| None=None)` | Model capabilities -- ``GET /mlops/capabilities``. |
| `metrics` | `async def metrics(self, fmt: str='json', ctx: RequestCtx \| None=None)` | Metrics export -- ``GET /mlops/metrics``. |
| `list_models` | `async def list_models(self, limit: int=100, offset: int=0, ctx: RequestCtx \| None=None)` | List registered models -- ``GET /mlops/models``. |
| `get_model` | `async def get_model(self, name: str, tag: str='latest', ctx: RequestCtx \| None=None)` | Get model details -- ``GET /mlops/models/{name}``. |
| `load_model` | `async def load_model(self, name: str, body: dict[str, Any]=None, ctx: RequestCtx \| None=None)` | Load a model into memory -- ``POST /mlops/models/{name}/load``. |
| `unload_model` | `async def unload_model(self, name: str, body: dict[str, Any]=None, ctx: RequestCtx \| None=None)` | Unload a model from memory -- ``POST /mlops/models/{name}/unload``. |
| `reload_model` | `async def reload_model(self, name: str, body: dict[str, Any]=None, ctx: RequestCtx \| None=None)` | Hot-reload a model to a new version -- ``POST /mlops/models/{name}/reload``. |
| `model_health` | `async def model_health(self, name: str, ctx: RequestCtx \| None=None)` | Health check for a specific model -- ``GET /mlops/models/{name}/health``. |
| `model_metrics` | `async def model_metrics(self, name: str, ctx: RequestCtx \| None=None)` | Metrics for a specific model -- ``GET /mlops/models/{name}/metrics``. |
| `start_rollout` | `async def start_rollout(self, body: dict[str, Any], ctx: RequestCtx \| None=None)` | Start a rollout -- ``POST /mlops/models/{name}/rollout``. |
| `list_rollouts` | `async def list_rollouts(self, ctx: RequestCtx \| None=None)` | List rollouts -- ``GET /mlops/rollouts``. |
| `drift_status` | `async def drift_status(self, ctx: RequestCtx \| None=None)` | Drift detection status -- ``GET /mlops/drift``. |
| `list_plugins` | `async def list_plugins(self, ctx: RequestCtx \| None=None)` | List plugins -- ``GET /mlops/plugins``. |
| `liveness` | `async def liveness(self, ctx: RequestCtx \| None=None)` | K8s liveness probe -- ``GET /mlops/healthz``. |
| `readiness` | `async def readiness(self, ctx: RequestCtx \| None=None)` | K8s readiness probe -- ``GET /mlops/readyz``. |
| `lineage` | `async def lineage(self, ctx: RequestCtx \| None=None)` | Model lineage DAG -- ``GET /mlops/lineage``. |
| `lineage_ancestors` | `async def lineage_ancestors(self, model_id: str, ctx: RequestCtx \| None=None)` | Ancestors of a model -- ``GET /mlops/lineage/{model_id}/ancestors``. |
| `lineage_descendants` | `async def lineage_descendants(self, model_id: str, ctx: RequestCtx \| None=None)` | Descendants of a model -- ``GET /mlops/lineage/{model_id}/descendants``. |
| `list_experiments` | `async def list_experiments(self, ctx: RequestCtx \| None=None)` | List experiments -- ``GET /mlops/experiments``. |
| `create_experiment` | `async def create_experiment(self, body: dict[str, Any], ctx: RequestCtx \| None=None)` | Create experiment -- ``POST /mlops/experiments``. |
| `conclude_experiment` | `async def conclude_experiment(self, experiment_id: str, winner: str='', ctx: RequestCtx \| None=None)` | Conclude experiment -- ``POST /mlops/experiments/{id}/conclude``. |
| `hot_models` | `async def hot_models(self, k: int=10, ctx: RequestCtx \| None=None)` | Top-K hot models -- ``GET /mlops/hot-models``. |
| `list_artifacts` | `async def list_artifacts(self, kind: str='', store_dir: str='artifacts', ctx: RequestCtx \| None=None)` | List artifacts -- ``GET /mlops/artifacts``. |
| `inspect_artifact` | `async def inspect_artifact(self, name: str, version: str='', store_dir: str='artifacts', ctx: RequestCtx \| None=None)` | Inspect artifact -- ``GET /mlops/artifacts/{name}``. |

### `RouteTarget`

- Source: `aquilia/mlops/serving/router.py`
- Bases: `object`
- Summary: A model version target with associated weight.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `version` | `str` | `` |
| `weight` | `float` | `` |
| `handler` | `Callable \| None` | `None` |
| `request_count` | `int` | `0` |
| `error_count` | `int` | `0` |
| `total_latency_ms` | `float` | `0.0` |

### `TrafficRouter`

- Source: `aquilia/mlops/serving/router.py`
- Bases: `object`
- Summary: Routes inference requests across model version targets.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_target` | `def add_target(self, version: str, weight: float, handler: Callable \| None=None)` | Register a model version as a routing target. |
| `remove_target` | `def remove_target(self, version: str)` | Remove a routing target. |
| `set_strategy` | `def set_strategy(self, strategy: RolloutStrategy)` | Set the routing strategy. |
| `set_canary_percentage` | `def set_canary_percentage(self, version: str, percentage: int)` | Set canary percentage for a specific version. |
| `route` | `def route(self, request_id: str='')` | Select a target version for the given request. |
| `route_sticky` | `def route_sticky(self, key: str)` | Sticky routing via consistent hashing. |
| `record_result` | `def record_result(self, version: str, latency_ms: float, error: bool=False)` | Record a result for metrics tracking. |
| `hot_models` | `def hot_models(self, k: int=10)` | Return the top-K most-requested model versions. |
| `should_rollback` | `def should_rollback(self, config: RolloutConfig)` | Check if rollback should be triggered based on metrics. |
| `get_metrics` | `def get_metrics(self)` | Get per-version metrics. |

### `WarmupStrategy`

- Source: `aquilia/mlops/serving/server.py`
- Bases: `object`
- Summary: Pre-inference warm-up to eliminate cold-start latency.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate_payload` | `def generate_payload(self, manifest: ModelpackManifest)` | Build a synthetic input from the manifest's tensor specs. |

### `ModelServingServer`

- Source: `aquilia/mlops/serving/server.py`
- Bases: `object`
- Summary: High-level model serving server.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `start` | `async def start(self)` | Prepare and load the model, warm up, start the batcher. |
| `stop` | `async def stop(self, drain_timeout_s: float \| None=None)` | Stop the server gracefully. |
| `predict` | `async def predict(self, inputs: dict[str, Any], parameters: dict[str, Any] \| None=None, request_id: str \| None=None, priority: int=0, max_tokens: int=0, timeout_ms: float=0.0)` | Submit a single prediction request. |
| `stream_predict` | `async def stream_predict(self, inputs: dict[str, Any], parameters: dict[str, Any] \| None=None, request_id: str \| None=None, max_tokens: int=0)` | Submit a streaming prediction request (LLM token-by-token output). |
| `liveness` | `async def liveness(self)` | K8s liveness probe -- ``GET /healthz``. |
| `readiness` | `async def readiness(self)` | K8s readiness probe -- ``GET /readyz``. |
| `health` | `async def health(self)` | Full health check endpoint data (backward compat). |
| `metrics` | `async def metrics(self)` | Prometheus-compatible metrics. |
| `circuit_breaker` | `def circuit_breaker(self)` | Access the circuit breaker for external inspection. |
| `rate_limiter` | `def rate_limiter(self)` | Access the rate limiter for external inspection. |
| `memory_tracker` | `def memory_tracker(self)` | Access the memory tracker for external inspection. |
