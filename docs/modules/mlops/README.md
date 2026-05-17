# mlops Module

## Purpose

Native model operations platform. Use this module for model declarations, serving, registries, runtimes, batching, scheduling, rollout, drift detection, observability, security, model packs, plugins, and deployment manifests.

## Source Coverage

- Python files: 76
- Public classes: 212
- Dataclasses: 41
- Enums: 20
- Public functions: 30

## How It Fits In Aquilia

1. Import the package from `aquilia.mlops` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `RingBuffer` | `aquilia/mlops/_structures.py` | Fixed-capacity circular buffer backed by a pre-allocated list. |
| `LRUCache` | `aquilia/mlops/_structures.py` | O(1) get / put / evict cache backed by :class:`OrderedDict`. |
| `AtomicCounter` | `aquilia/mlops/_structures.py` | Thread-safe monotonic counter (integers only). |
| `ExponentialDecay` | `aquilia/mlops/_structures.py` | EWMA (Exponentially Weighted Moving Average). |
| `SlidingWindow` | `aquilia/mlops/_structures.py` | Time-bucketed sliding window for rate/latency tracking. |
| `TopKHeap` | `aquilia/mlops/_structures.py` | Maintains the top-K elements by score using a dict + sort-on-read |
| `BloomFilter` | `aquilia/mlops/_structures.py` | Space-efficient probabilistic set for fast negative lookups. |
| `ConsistentHash` | `aquilia/mlops/_structures.py` | Jump-consistent hash for sticky model-to-node routing. |
| `LineageNode` | `aquilia/mlops/_structures.py` | A single node in the model lineage graph. |
| `ModelLineageDAG` | `aquilia/mlops/_structures.py` | Directed acyclic graph tracking model derivation relationships. |
| `ExperimentArm` | `aquilia/mlops/_structures.py` | One arm of an A/B experiment. |
| `Experiment` | `aquilia/mlops/_structures.py` | A/B experiment definition. |
| `ExperimentLedger` | `aquilia/mlops/_structures.py` | Records A/B experiment assignments and collects per-arm metrics. |
| `CircuitBreaker` | `aquilia/mlops/_structures.py` | Three-state circuit breaker (CLOSED -> OPEN -> HALF_OPEN -> CLOSED). |
| `TokenBucketRateLimiter` | `aquilia/mlops/_structures.py` | Token-bucket rate limiter for inference request throttling. |
| `AdaptiveBatchQueue` | `aquilia/mlops/_structures.py` | Priority-aware batch queue with adaptive sizing for LLM serving. |
| `MemoryTracker` | `aquilia/mlops/_structures.py` | Tracks memory allocations for model serving with watermark alerts. |
| `DType` | `aquilia/mlops/_types.py` | Centralized DType system for Aquilia MLOps. |
| `Framework` | `aquilia/mlops/_types.py` | Supported ML frameworks. |
| `RuntimeKind` | `aquilia/mlops/_types.py` | Available runtime backends. |
| `QuantizePreset` | `aquilia/mlops/_types.py` | Quantization presets. |
| `ExportTarget` | `aquilia/mlops/_types.py` | Edge export targets. |
| `BatchingStrategy` | `aquilia/mlops/_types.py` | Batching strategy modes. |
| `RolloutStrategy` | `aquilia/mlops/_types.py` | Release rollout strategies. |
| `DriftMethod` | `aquilia/mlops/_types.py` | Drift detection methods. |
| `ModelType` | `aquilia/mlops/_types.py` | Model type classification for serving strategy selection. |
| `InferenceMode` | `aquilia/mlops/_types.py` | Inference execution modes. |
| `DeviceType` | `aquilia/mlops/_types.py` | Compute device types. |
| `CircuitState` | `aquilia/mlops/_types.py` | Circuit breaker states. |
| `TensorSpec` | `aquilia/mlops/_types.py` | Describes a single tensor in the inference signature. |
| `BlobRef` | `aquilia/mlops/_types.py` | Reference to a blob inside a modelpack. |
| `Provenance` | `aquilia/mlops/_types.py` | Provenance metadata for reproducibility. |
| `LLMConfig` | `aquilia/mlops/_types.py` | Configuration specific to LLM/SLM model serving. |
| `ModelpackManifest` | `aquilia/mlops/_types.py` | Complete manifest for a modelpack artifact. |
| `InferenceRequest` | `aquilia/mlops/_types.py` | A single inference request. |
| `InferenceResult` | `aquilia/mlops/_types.py` | Result of a single inference. |
| `StreamChunk` | `aquilia/mlops/_types.py` | A single chunk in a streaming inference response. |
| `BatchRequest` | `aquilia/mlops/_types.py` | Aggregated batch of inference requests. |
| `PlacementScore` | `aquilia/mlops/_types.py` | Score for scheduler placement decisions. |
| `RolloutConfig` | `aquilia/mlops/_types.py` | Configuration for a traffic rollout. |
| `DriftReport` | `aquilia/mlops/_types.py` | Result of a drift detection analysis. |
| `CircuitBreakerConfig` | `aquilia/mlops/_types.py` | Configuration for inference circuit breaker. |
| `TokenUsage` | `aquilia/mlops/_types.py` | Token usage tracking for LLM inference. |
| `StorageAdapter` | `aquilia/mlops/_types.py` | Protocol for blob storage backends. |
| `Runtime` | `aquilia/mlops/_types.py` | Protocol for model runtime backends. |
| `StreamingRuntime` | `aquilia/mlops/_types.py` | Protocol for runtimes that support streaming inference (LLMs). |
| `PluginHook` | `aquilia/mlops/_types.py` | Protocol for plugin lifecycle hooks. |
| `MLOpsConfig` | `aquilia/mlops/di/providers.py` | Typed configuration for MLOps DI registration. |
| `DynamicBatcher` | `aquilia/mlops/serving/batching.py` | Async dynamic batching scheduler. |
| `MLOpsController` | `aquilia/mlops/serving/controllers.py` | Controller for MLOps HTTP API. |
| `RouteTarget` | `aquilia/mlops/serving/router.py` | A model version target with associated weight. |
| `TrafficRouter` | `aquilia/mlops/serving/router.py` | Routes inference requests across model version targets. |
| `WarmupStrategy` | `aquilia/mlops/serving/server.py` | Pre-inference warm-up to eliminate cold-start latency. |
| `ModelServingServer` | `aquilia/mlops/serving/server.py` | High-level model serving server. |
| `ExplainMethod` | `aquilia/mlops/explain/hooks.py` | Public class. |
| `FeatureAttribution` | `aquilia/mlops/explain/hooks.py` | Single feature's contribution. |
| `Explanation` | `aquilia/mlops/explain/hooks.py` | Complete explanation for one prediction. |
| `SHAPExplainer` | `aquilia/mlops/explain/hooks.py` | Wraps ``shap.KernelExplainer``, ``shap.TreeExplainer`` or |
| `LIMEExplainer` | `aquilia/mlops/explain/hooks.py` | Wraps ``lime.lime_tabular.LimeTabularExplainer`` (default) or |
| `PIIKind` | `aquilia/mlops/explain/privacy.py` | Public class. |
| `PIIMatch` | `aquilia/mlops/explain/privacy.py` | Public class. |
| `PIIRedactor` | `aquilia/mlops/explain/privacy.py` | Scans text for PII and replaces matches with a configurable placeholder. |
| `LaplaceNoise` | `aquilia/mlops/explain/privacy.py` | Adds calibrated Laplace noise to numeric values. |
| `InputSanitiser` | `aquilia/mlops/explain/privacy.py` | Pipeline of transforms applied to inference payloads before they |
| `ExportResult` | `aquilia/mlops/optimizer/export.py` | Result of an edge export. |
| `EdgeExporter` | `aquilia/mlops/optimizer/export.py` | Export models to edge-friendly formats. |
| `OptimizationResult` | `aquilia/mlops/optimizer/pipeline.py` | Result of an optimization pass. |
| `OptimizationPipeline` | `aquilia/mlops/optimizer/pipeline.py` | Runs a sequence of optimization passes on model files. |
| `BlobEncryptor` | `aquilia/mlops/security/encryption.py` | Encrypts / decrypts blob data at rest using Fernet (AES-128-CBC). |
| `Permission` | `aquilia/mlops/security/rbac.py` | Registry permissions. |
| `Role` | `aquilia/mlops/security/rbac.py` | A named role with a set of permissions. |
| `RBACManager` | `aquilia/mlops/security/rbac.py` | Role-based access control for registry operations. |
| `ArtifactSigner` | `aquilia/mlops/security/signing.py` | Signs and verifies modelpack artifacts. |
| `EncryptionManager` | `aquilia/mlops/security/signing.py` | Encryption at rest for registry blob storage. |
| `HealthCheckPlugin` | `aquilia/mlops/plugins/example_plugin.py` | Minimal example plugin implementing the ``PluginHook`` protocol. |
| `PluginState` | `aquilia/mlops/plugins/host.py` | Public class. |
| `PluginDescriptor` | `aquilia/mlops/plugins/host.py` | Public class. |
| `PluginHookProtocol` | `aquilia/mlops/plugins/host.py` | Minimal interface a plugin must satisfy. |
| `PluginHost` | `aquilia/mlops/plugins/host.py` | Central plugin manager. |
| `MarketplaceEntry` | `aquilia/mlops/plugins/marketplace.py` | Public class. |

Only the first 80 classes are shown here. See the file inventory for the rest of the package.

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `register_mlops_providers` | `aquilia/mlops/di/providers.py` | Register all MLOps services as DI providers. |
| `register_mlops_middleware` | `aquilia/mlops/serving/middleware.py` | Register all MLOps middleware with proper scope and priority |
| `mlops_metrics_middleware` | `aquilia/mlops/serving/middleware.py` | Create an inference metrics middleware. |
| `mlops_request_id_middleware` | `aquilia/mlops/serving/middleware.py` | Middleware that injects a unique request ID into the context. |
| `mlops_rate_limit_middleware` | `aquilia/mlops/serving/middleware.py` | Rate-limiting middleware using a token-bucket rate limiter. |
| `mlops_circuit_breaker_middleware` | `aquilia/mlops/serving/middleware.py` | Circuit-breaker middleware for inference endpoints. |
| `create_explainer` | `aquilia/mlops/explain/hooks.py` | Factory that returns the right explainer for the requested method. |
| `profile_model` | `aquilia/mlops/optimizer/export.py` | Estimate latency and memory for a model on a target device. |
| `parse_mlops_config` | `aquilia/mlops/manifest/config.py` | Parse an ``[mlops]`` config dict into ``MLOpsManifestConfig``. |
| `validate_manifest_config` | `aquilia/mlops/manifest/schema.py` | Validate a parsed manifest config. |
| `validate_and_raise` | `aquilia/mlops/manifest/schema.py` | Validate and raise ``ManifestValidationError`` if invalid. |
| `select_runtime` | `aquilia/mlops/runtime/base.py` | Select the best runtime for the given manifest. |
| `validate_manifest` | `aquilia/mlops/pack/manifest_schema.py` | Validate manifest dict against schema. |
| `sign_archive` | `aquilia/mlops/pack/signer.py` | Sign a modelpack archive and write signature file. |
| `verify_archive` | `aquilia/mlops/pack/signer.py` | Verify a modelpack archive against its signature file. |
| `generate_ci_workflow` | `aquilia/mlops/release/ci.py` | Generate GitHub Actions workflow file. |
| `generate_dockerfile` | `aquilia/mlops/release/ci.py` | Generate Dockerfile for model serving. |
| `serve` | `aquilia/mlops/api/functional.py` | Decorator that wraps a function into a registered model. |
| `set_global_registry` | `aquilia/mlops/api/model_class.py` | Set the global model registry (called by DI providers). |
| `model` | `aquilia/mlops/api/model_class.py` | Decorator that registers an ``AquiliaModel`` subclass with the model registry. |
| `on_load` | `aquilia/mlops/engine/hooks.py` | Mark method as a post-load lifecycle hook. |
| `on_unload` | `aquilia/mlops/engine/hooks.py` | Mark method as a pre-unload lifecycle hook. |
| `preprocess` | `aquilia/mlops/engine/hooks.py` | Mark method as input preprocessor. |
| `postprocess` | `aquilia/mlops/engine/hooks.py` | Mark method as output postprocessor. |
| `before_predict` | `aquilia/mlops/engine/hooks.py` | Mark method as a before-prediction hook. |
| `after_predict` | `aquilia/mlops/engine/hooks.py` | Mark method as an after-prediction hook. |
| `on_error` | `aquilia/mlops/engine/hooks.py` | Mark method as an inference error handler. |
| `collect_hooks` | `aquilia/mlops/engine/hooks.py` | Scan an object instance for decorated hook methods. |
| `mlops_on_startup` | `aquilia/mlops/engine/lifecycle.py` | MLOps startup hook. |
| `mlops_on_shutdown` | `aquilia/mlops/engine/lifecycle.py` | MLOps shutdown hook. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/mlops/__init__.py` | Aquilia MLOps Platform |
| `aquilia/mlops/_structures.py` | MLOps Data Structures -- High-performance primitives for ML pipelines. |
| `aquilia/mlops/_types.py` | Aquilia MLOps Platform -- Shared type definitions. |
| `aquilia/mlops/api/__init__.py` | Aquilia MLOps API Layer. |
| `aquilia/mlops/api/blueprints.py` | MLOps Blueprints -- Aquilia Blueprint definitions for all MLOps data types. |
| `aquilia/mlops/api/functional.py` | Functional Serving -- ``@serve`` decorator for minimal model definitions. |
| `aquilia/mlops/api/model_class.py` | AquiliaModel -- declarative base class and ``@model`` decorator. |
| `aquilia/mlops/api/route_generator.py` | Route Generator -- auto-generate Aquilia controller endpoints per model. |
| `aquilia/mlops/di/providers.py` | MLOps DI Integration -- Wires all MLOps services into Aquilia's DI container. |
| `aquilia/mlops/engine/__init__.py` | Aquilia MLOps Execution Engine. |
| `aquilia/mlops/engine/faults.py` | MLOps Fault Domain -- Structured error handling for the entire ML pipeline. |
| `aquilia/mlops/engine/hooks.py` | Pipeline Hooks -- decorator-based lifecycle and inference hooks. |
| `aquilia/mlops/engine/lifecycle.py` | MLOps Lifecycle Hooks -- Startup / shutdown integration with Aquilia's |
| `aquilia/mlops/engine/module.py` | MLOps Aquilary Module -- register MLOps as an Aquilary application module. |
| `aquilia/mlops/engine/pipeline.py` | Inference Pipeline -- async preprocess -> batch/infer -> postprocess pipeline. |
| `aquilia/mlops/explain/__init__.py` | Explainability and privacy hooks. |
| `aquilia/mlops/explain/hooks.py` | Explainability hooks -- SHAP & LIME wrappers with a unified interface. |
| `aquilia/mlops/explain/privacy.py` | Privacy helpers -- PII redaction, differential privacy noise, and |
| `aquilia/mlops/manifest/__init__.py` | Aquilia MLOps Manifest Configuration. |
| `aquilia/mlops/manifest/config.py` | Manifest Config -- parse ``[mlops]`` config from Aquilia workspace config. |
| `aquilia/mlops/manifest/schema.py` | Manifest Schema Validation for MLOps configuration. |
| `aquilia/mlops/observe/__init__.py` | Observability: metrics, drift detection, logging. |
| `aquilia/mlops/observe/drift.py` | Drift detection -- PSI, KS-test, and distribution tracking. |
| `aquilia/mlops/observe/logger.py` | Feature and prediction logger. |
| `aquilia/mlops/observe/metrics.py` | Prometheus-compatible metrics collector. |
| `aquilia/mlops/optimizer/__init__.py` | Optimization pipeline: quantize, prune, export. |
| `aquilia/mlops/optimizer/export.py` | Edge export utilities -- TFLite, CoreML, quantized ONNX. |
| `aquilia/mlops/optimizer/pipeline.py` | Optimization Pipeline -- orchestrates quantization, pruning, fusion, compilation. |
| `aquilia/mlops/orchestrator/__init__.py` | Aquilia MLOps Model Orchestrator. |
| `aquilia/mlops/orchestrator/loader.py` | Model Loader -- lazy loading, hot reload, and lifecycle state management. |
| `aquilia/mlops/orchestrator/orchestrator.py` | Model Orchestrator -- top-level façade for ML inference. |
| `aquilia/mlops/orchestrator/persistence.py` | Model Persistence System -- Robust loading and saving for production models. |
| `aquilia/mlops/orchestrator/registry.py` | Model Registry -- in-memory metadata-only registry for ML models. |
| `aquilia/mlops/orchestrator/router.py` | Version Router -- routes inference requests to the correct model version. |
| `aquilia/mlops/orchestrator/versioning.py` | Version Manager -- semantic versioning, promotion, and rollback. |
| `aquilia/mlops/pack/__init__.py` | Modelpack builder and content store. |
| `aquilia/mlops/pack/builder.py` | Modelpack Builder -- Creates ``.aquilia`` archive artifacts. |
| `aquilia/mlops/pack/content_store.py` | Content-addressable blob store. |
| `aquilia/mlops/pack/manifest_schema.py` | JSON Schema for modelpack ``manifest.json``. |
| `aquilia/mlops/pack/signer.py` | Artifact signing and verification. |
| `aquilia/mlops/plugins/__init__.py` | Plugin system and marketplace. |
| `aquilia/mlops/plugins/example_plugin.py` | Example Aquilia MLOps plugin -- demonstrates how to write a plugin. |
| `aquilia/mlops/plugins/host.py` | Plugin host -- discovers, loads, and manages lifecycle of MLOps plugins. |
| `aquilia/mlops/plugins/marketplace.py` | Plugin marketplace -- lightweight discovery & installation of community |
| `aquilia/mlops/registry/__init__.py` | Registry service and storage adapters. |
| `aquilia/mlops/registry/models.py` | Registry data models -- SQLite backend (default). |
| `aquilia/mlops/registry/service.py` | Registry Service -- HTTP API for publishing, fetching and managing modelpacks. |
| `aquilia/mlops/registry/storage/__init__.py` | Storage adapter implementations. |
| `aquilia/mlops/registry/storage/base.py` | Base storage adapter -- abstract interface for blob backends. |
| `aquilia/mlops/registry/storage/filesystem.py` | Filesystem storage adapter -- stores blobs on local disk. |
| `aquilia/mlops/registry/storage/s3.py` | S3 / MinIO storage adapter for registry blob storage. |
| `aquilia/mlops/release/__init__.py` | Release management: rollouts, CI/CD. |
| `aquilia/mlops/release/ci.py` | CI/CD templates and GitHub Actions configuration. |
| `aquilia/mlops/release/rollout.py` | Release rollout engine -- canary, A/B, shadow traffic management. |
| `aquilia/mlops/runtime/__init__.py` | Runtime adapters for model inference. |
| `aquilia/mlops/runtime/base.py` | Runtime base -- abstract interface for inference backends. |
| `aquilia/mlops/runtime/bento_exporter.py` | BentoML exporter -- generates BentoML-compatible service bundles. |
| `aquilia/mlops/runtime/device_manager.py` | Device Manager -- auto-detection, fallback, monitoring, and locking for |
| `aquilia/mlops/runtime/executor.py` | Inference Executor -- offloads blocking inference to thread/process pools. |
| `aquilia/mlops/runtime/onnx_runtime.py` | ONNX Runtime adapter -- high-performance inference via onnxruntime. |
| `aquilia/mlops/runtime/python_runtime.py` | Python in-process runtime -- loads and runs models natively in Python. |
| `aquilia/mlops/runtime/torchserve_exporter.py` | TorchServe exporter -- generates TorchServe-compatible model archives. |
| `aquilia/mlops/runtime/triton_adapter.py` | Triton Inference Server adapter. |
| `aquilia/mlops/scheduler/__init__.py` | Autoscaling and placement scheduling. |
| `aquilia/mlops/scheduler/autoscaler.py` | Autoscaler -- K8s HPA metrics exporter and scaling policy engine. |
| `aquilia/mlops/scheduler/placement.py` | Hardware-aware placement scheduler. |
| `aquilia/mlops/security/__init__.py` | Security: signing, encryption, RBAC. |
| `aquilia/mlops/security/encryption.py` | Encryption at rest for registry blobs. |
| `aquilia/mlops/security/rbac.py` | RBAC for registry operations. |
| `aquilia/mlops/security/signing.py` | Security -- artifact signing, verification, and encryption at rest. |
| `aquilia/mlops/serving/__init__.py` | Model serving layer. |
| `aquilia/mlops/serving/batching.py` | Dynamic Batching Scheduler. |
| `aquilia/mlops/serving/controllers.py` | MLOps Controller -- HTTP endpoints for model serving, registry, and observability. |
| `aquilia/mlops/serving/middleware.py` | MLOps Middleware -- Inference metrics, rate limiting, and circuit breaker |
| `aquilia/mlops/serving/router.py` | Traffic router -- canary, A/B, shadow, sticky routing for model deployments. |
| `aquilia/mlops/serving/server.py` | Model Serving Server -- dev and production serving with typed endpoints. |

## Testing Pointers

Search `tests/` for `mlops` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
