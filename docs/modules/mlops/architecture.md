# Mlops Architecture

Model operations platform: modelpacks, serving, registries, runtimes, orchestration, observability, rollout, optimization, plugins, scheduler, and security.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/mlops/__init__.py` | 317 | 0 | 0 | Aquilia MLOps Platform |
| `aquilia/mlops/_structures.py` | 1374 | 17 | 0 | MLOps Data Structures -- High-performance primitives for ML pipelines. |
| `aquilia/mlops/_types.py` | 746 | 30 | 0 | Aquilia MLOps Platform -- Shared type definitions. |
| `aquilia/mlops/api/__init__.py` | 14 | 0 | 0 | Aquilia MLOps API Layer. |
| `aquilia/mlops/api/contracts.py` | 403 | 26 | 0 | MLOps Contracts -- Aquilia Contract definitions for all MLOps data types. |
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

## Internal Shape

`mlops` has 76 Python files, 212 public classes, 30 public module-level functions, and 24 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 24 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.._types` | 20 |
| `.base` | 7 |
| `.._structures` | 5 |
| `.registry` | 5 |
| `..engine.faults` | 4 |
| `..runtime.base` | 4 |
| `.config` | 2 |
| `.hooks` | 2 |
| `.loader` | 2 |
| `.model_class` | 2 |
| `.orchestrator` | 2 |
| `.router` | 2 |
| `..engine.hooks` | 1 |
| `..engine.pipeline` | 1 |
| `..pack.content_store` | 1 |
| `..pack.manifest_schema` | 1 |
| `..serving.router` | 1 |
| `._structures` | 1 |
| `._types` | 1 |
| `.api` | 1 |
| `.api.route_generator` | 1 |
| `.batching` | 1 |
| `.content_store` | 1 |
| `.di.providers` | 1 |
| `.engine` | 1 |
| `.engine.faults` | 1 |
| `.engine.hooks` | 1 |
| `.engine.lifecycle` | 1 |
| `.functional` | 1 |
| `.manifest` | 1 |
| `.models` | 1 |
| `.observe.drift` | 1 |
| `.observe.metrics` | 1 |
| `.pack.builder` | 1 |
| `.pack.content_store` | 1 |
| `.persistence` | 1 |
| `.pipeline` | 1 |
| `.plugins.host` | 1 |
| `.registry.service` | 1 |
| `.runtime.base` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 58 |
| `logging` | 49 |
| `typing` | 40 |
| `collections` | 24 |
| `dataclasses` | 21 |
| `time` | 21 |
| `pathlib` | 12 |
| `enum` | 9 |
| `asyncio` | 7 |
| `hashlib` | 6 |
| `contextlib` | 5 |
| `json` | 5 |
| `importlib` | 4 |
| `inspect` | 4 |
| `random` | 4 |
| `abc` | 3 |
| `math` | 3 |
| `os` | 3 |
| `uuid` | 3 |
| `numpy` | 2 |
| `shutil` | 2 |
| `threading` | 2 |
| `concurrent` | 1 |
| `datetime` | 1 |
| `heapq` | 1 |
| `hmac` | 1 |
| `io` | 1 |
| `pickle` | 1 |
| `re` | 1 |
| `subprocess` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `LLMConfig` | `aquilia/mlops/_types.py` | Configuration specific to LLM/SLM model serving. |
| `RolloutConfig` | `aquilia/mlops/_types.py` | Configuration for a traffic rollout. |
| `CircuitBreakerConfig` | `aquilia/mlops/_types.py` | Configuration for inference circuit breaker. |
| `StorageAdapter` | `aquilia/mlops/_types.py` | Protocol for blob storage backends. |
| `PluginHook` | `aquilia/mlops/_types.py` | Protocol for plugin lifecycle hooks. |
| `RolloutConfigContract` | `aquilia/mlops/api/contracts.py` | Validates rollout configuration payloads. |
| `ScalingPolicyContract` | `aquilia/mlops/api/contracts.py` | Validates autoscaler policy configuration. |
| `PluginDescriptorContract` | `aquilia/mlops/api/contracts.py` | Renders plugin descriptor for API responses. |
| `LLMConfigContract` | `aquilia/mlops/api/contracts.py` | Validates LLM configuration payloads. |
| `MLOpsConfig` | `aquilia/mlops/di/providers.py` | Typed configuration for MLOps DI registration. |
| `RegistryFault` | `aquilia/mlops/engine/faults.py` | Base fault for registry operations. |
| `RegistryConnectionFault` | `aquilia/mlops/engine/faults.py` | Cannot connect to registry backend. |
| `PluginFault` | `aquilia/mlops/engine/faults.py` | Base fault for plugin operations. |
| `PluginLoadFault` | `aquilia/mlops/engine/faults.py` | Plugin failed to load. |
| `PluginHookFault` | `aquilia/mlops/engine/faults.py` | Plugin hook execution failed. |
| `HookRegistry` | `aquilia/mlops/engine/hooks.py` | Collected hooks from a model class. |
| `MLOpsManifestConfig` | `aquilia/mlops/manifest/config.py` | Parsed ``[mlops]`` configuration from Aquilia workspace config. |
| `ModelLoader` | `aquilia/mlops/orchestrator/loader.py` | Manages model instantiation, loading, unloading, and hot reload. |
| `ModelLoader` | `aquilia/mlops/orchestrator/persistence.py` | Abstract base class for framework-specific model loaders. |
| `PyTorchModelLoader` | `aquilia/mlops/orchestrator/persistence.py` | Production-grade PyTorch model loader. |
| `ModelPersistenceManager` | `aquilia/mlops/orchestrator/persistence.py` | Orchestrates high-level model persistence operations. |
| `ModelConfig` | `aquilia/mlops/orchestrator/registry.py` | Per-model configuration (from manifest or decorator). |
| `ModelRegistry` | `aquilia/mlops/orchestrator/registry.py` | In-memory metadata-only model registry. |
| `CanaryConfig` | `aquilia/mlops/orchestrator/router.py` | Active canary configuration for a model. |
| `VersionRouter` | `aquilia/mlops/orchestrator/router.py` | Routes inference requests to the correct model version. |
| `VersionManager` | `aquilia/mlops/orchestrator/versioning.py` | Version Management for ML models. |
| `ContentStore` | `aquilia/mlops/pack/content_store.py` | Local filesystem content-addressable blob store. |
| `HealthCheckPlugin` | `aquilia/mlops/plugins/example_plugin.py` | Minimal example plugin implementing the ``PluginHook`` protocol. |
| `PluginState` | `aquilia/mlops/plugins/host.py` |  |
| `PluginDescriptor` | `aquilia/mlops/plugins/host.py` |  |
| `PluginHookProtocol` | `aquilia/mlops/plugins/host.py` | Minimal interface a plugin must satisfy. |
| `PluginHost` | `aquilia/mlops/plugins/host.py` | Central plugin manager. |
| `PluginMarketplace` | `aquilia/mlops/plugins/marketplace.py` | Browse and install plugins from a remote JSON index. |
| `RegistryDB` | `aquilia/mlops/registry/models.py` | Async SQLite backend for registry metadata. |
| `RegistryError` | `aquilia/mlops/registry/service.py` | Base error for registry operations (kept for backward compatibility). |
| `RegistryService` | `aquilia/mlops/registry/service.py` | Modelpack registry service. |
| `BaseStorageAdapter` | `aquilia/mlops/registry/storage/base.py` | Abstract base for blob storage backends. |
| `FilesystemStorageAdapter` | `aquilia/mlops/registry/storage/filesystem.py` | Store blobs on local filesystem in a content-addressable layout. |
| `S3StorageAdapter` | `aquilia/mlops/registry/storage/s3.py` | Store blobs in an S3-compatible bucket. |
| `RolloutEngine` | `aquilia/mlops/release/rollout.py` | Manages progressive rollouts with metric-based gating. |
| `DeviceManager` | `aquilia/mlops/runtime/device_manager.py` | Centralized device management for ML runtimes. |
| `ONNXRuntimeAdapter` | `aquilia/mlops/runtime/onnx_runtime.py` | ONNX Runtime inference adapter. |
| `TritonAdapter` | `aquilia/mlops/runtime/triton_adapter.py` | Triton Inference Server adapter. |
| `ScalingPolicy` | `aquilia/mlops/scheduler/autoscaler.py` | Autoscaling policy definition. |
| `RBACManager` | `aquilia/mlops/security/rbac.py` | Role-based access control for registry operations. |
| `EncryptionManager` | `aquilia/mlops/security/signing.py` | Encryption at rest for registry blob storage. |
| `MLOpsController` | `aquilia/mlops/serving/controllers.py` | Controller for MLOps HTTP API. |
| `TrafficRouter` | `aquilia/mlops/serving/router.py` | Routes inference requests across model version targets. |

## Error Handling

Fault/error classes defined here:

`MLOpsFault`, `PackFault`, `PackBuildFault`, `PackIntegrityFault`, `PackSignatureFault`, `RegistryFault`, `RegistryConnectionFault`, `PackNotFoundFault`, `ImmutabilityViolationFault`, `ServingFault`, `RuntimeLoadFault`, `InferenceFault`, `BatchTimeoutFault`, `WarmupFault`, `ObserveFault`, `DriftDetectionFault`, `MetricsExportFault`, `RolloutFault`, `RolloutAdvanceFault`, `AutoRollbackFault`, `SchedulerFault`, `PlacementFault`, `ScalingFault`, `MLOpsSecurityFault`, `SigningFault`, `PermissionDeniedFault`, `EncryptionFault`, `PluginFault`, `PluginLoadFault`, `PluginHookFault`, `CircuitBreakerFault`, `CircuitBreakerOpenFault`, `CircuitBreakerExhaustedFault`, `RateLimitFault`, `StreamingFault`, `StreamInterruptedFault`, `TokenLimitExceededFault`, `MemoryFault`, `MemorySoftLimitFault`, `MemoryHardLimitFault`, `ManifestValidationError`, `SignatureError`, `RegistryError`, `PackNotFoundError`, `ImmutabilityError`
