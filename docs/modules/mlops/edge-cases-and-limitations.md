# MLOps Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `MLOpsFault` | `aquilia/mlops/engine/faults.py` | Base fault for all MLOps operations. |
| `PackFault` | `aquilia/mlops/engine/faults.py` | Base fault for model packaging. |
| `PackBuildFault` | `aquilia/mlops/engine/faults.py` | Model pack build failed. |
| `PackIntegrityFault` | `aquilia/mlops/engine/faults.py` | Blob integrity check failed (SHA-256 mismatch) or structural issue. |
| `PackSignatureFault` | `aquilia/mlops/engine/faults.py` | Artifact signature verification failed. |
| `RegistryFault` | `aquilia/mlops/engine/faults.py` | Base fault for registry operations. |
| `RegistryConnectionFault` | `aquilia/mlops/engine/faults.py` | Cannot connect to registry backend. |
| `PackNotFoundFault` | `aquilia/mlops/engine/faults.py` | Requested modelpack not found in registry. |
| `ImmutabilityViolationFault` | `aquilia/mlops/engine/faults.py` | Attempted to overwrite an immutable artifact. |
| `ServingFault` | `aquilia/mlops/engine/faults.py` | Base fault for model serving. |
| `RuntimeLoadFault` | `aquilia/mlops/engine/faults.py` | Model failed to load into runtime. |
| `InferenceFault` | `aquilia/mlops/engine/faults.py` | Inference failed for a request. |
| `BatchTimeoutFault` | `aquilia/mlops/engine/faults.py` | Batch processing exceeded deadline. |
| `WarmupFault` | `aquilia/mlops/engine/faults.py` | Model warm-up failed. |
| `ObserveFault` | `aquilia/mlops/engine/faults.py` | Base fault for observability. |
| `DriftDetectionFault` | `aquilia/mlops/engine/faults.py` | Drift detection computation failed. |
| `MetricsExportFault` | `aquilia/mlops/engine/faults.py` | Metrics export/scrape failed. |
| `RolloutFault` | `aquilia/mlops/engine/faults.py` | Base fault for release management. |
| `RolloutAdvanceFault` | `aquilia/mlops/engine/faults.py` | Rollout advancement failed due to metric degradation. |
| `AutoRollbackFault` | `aquilia/mlops/engine/faults.py` | Automatic rollback triggered. |
| `SchedulerFault` | `aquilia/mlops/engine/faults.py` | Base fault for scheduling. |
| `PlacementFault` | `aquilia/mlops/engine/faults.py` | No suitable node found for model placement. |
| `ScalingFault` | `aquilia/mlops/engine/faults.py` | Scaling operation failed. |
| `MLOpsSecurityFault` | `aquilia/mlops/engine/faults.py` | Base fault for MLOps security. |
| `SigningFault` | `aquilia/mlops/engine/faults.py` | Artifact signing failed. |
| `PermissionDeniedFault` | `aquilia/mlops/engine/faults.py` | User lacks required RBAC permission. |
| `EncryptionFault` | `aquilia/mlops/engine/faults.py` | Encryption / decryption operation failed. |
| `PluginFault` | `aquilia/mlops/engine/faults.py` | Base fault for plugin operations. |
| `PluginLoadFault` | `aquilia/mlops/engine/faults.py` | Plugin failed to load. |
| `PluginHookFault` | `aquilia/mlops/engine/faults.py` | Plugin hook execution failed. |
| `CircuitBreakerFault` | `aquilia/mlops/engine/faults.py` | Base fault for circuit breaker events. |
| `CircuitBreakerOpenFault` | `aquilia/mlops/engine/faults.py` | Circuit breaker is OPEN -- requests are being rejected. |
| `CircuitBreakerExhaustedFault` | `aquilia/mlops/engine/faults.py` | Circuit breaker half-open probe failed -- returning to OPEN state. |
| `RateLimitFault` | `aquilia/mlops/engine/faults.py` | Request rejected due to rate limiting. |
| `StreamingFault` | `aquilia/mlops/engine/faults.py` | Base fault for streaming inference. |
| `StreamInterruptedFault` | `aquilia/mlops/engine/faults.py` | Streaming generation was interrupted (client disconnect, timeout, etc.). |
| `TokenLimitExceededFault` | `aquilia/mlops/engine/faults.py` | Token generation exceeded max_tokens limit. |
| `MemoryFault` | `aquilia/mlops/engine/faults.py` | Base fault for memory management. |
| `MemorySoftLimitFault` | `aquilia/mlops/engine/faults.py` | Memory usage crossed soft limit -- eviction candidates available. |
| `MemoryHardLimitFault` | `aquilia/mlops/engine/faults.py` | Memory usage crossed hard limit -- requests must be rejected. |
| `ManifestValidationError` | `aquilia/mlops/manifest/schema.py` | Raised when manifest validation fails. |
| `SignatureError` | `aquilia/mlops/pack/signer.py` | Raised when signature verification fails. |
| `RegistryError` | `aquilia/mlops/registry/service.py` | Base error for registry operations (kept for backward compatibility). |
| `PackNotFoundError` | `aquilia/mlops/registry/service.py` | Raised when a modelpack is not found (kept for backward compatibility). |
| `ImmutabilityError` | `aquilia/mlops/registry/service.py` | Raised when attempting to overwrite an immutable artifact (kept for backward compatibility). |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/mlops/__init__.py`: Aquilia MLOps Platform
- `aquilia/mlops/_structures.py`: MLOps Data Structures -- High-performance primitives for ML pipelines.
- `aquilia/mlops/_types.py`: Aquilia MLOps Platform -- Shared type definitions.
- `aquilia/mlops/api/__init__.py`: Aquilia MLOps API Layer.
- `aquilia/mlops/api/blueprints.py`: MLOps Blueprints -- Aquilia Blueprint definitions for all MLOps data types.
- `aquilia/mlops/api/functional.py`: Functional Serving -- ``@serve`` decorator for minimal model definitions.
- `aquilia/mlops/api/model_class.py`: AquiliaModel -- declarative base class and ``@model`` decorator.
- `aquilia/mlops/api/route_generator.py`: Route Generator -- auto-generate Aquilia controller endpoints per model.
- `aquilia/mlops/di/providers.py`: MLOps DI Integration -- Wires all MLOps services into Aquilia's DI container.
- `aquilia/mlops/engine/__init__.py`: Aquilia MLOps Execution Engine.
- `aquilia/mlops/engine/faults.py`: MLOps Fault Domain -- Structured error handling for the entire ML pipeline.
- `aquilia/mlops/engine/hooks.py`: Pipeline Hooks -- decorator-based lifecycle and inference hooks.
- `aquilia/mlops/engine/lifecycle.py`: MLOps Lifecycle Hooks -- Startup / shutdown integration with Aquilia's
- `aquilia/mlops/engine/module.py`: MLOps Aquilary Module -- register MLOps as an Aquilary application module.
- `aquilia/mlops/engine/pipeline.py`: Inference Pipeline -- async preprocess -> batch/infer -> postprocess pipeline.
- `aquilia/mlops/explain/__init__.py`: Explainability and privacy hooks.
- `aquilia/mlops/explain/hooks.py`: Explainability hooks -- SHAP & LIME wrappers with a unified interface.
- `aquilia/mlops/explain/privacy.py`: Privacy helpers -- PII redaction, differential privacy noise, and
- `aquilia/mlops/manifest/__init__.py`: Aquilia MLOps Manifest Configuration.
- `aquilia/mlops/manifest/config.py`: Manifest Config -- parse ``[mlops]`` config from Aquilia workspace config.
- `aquilia/mlops/manifest/schema.py`: Manifest Schema Validation for MLOps configuration.
- `aquilia/mlops/observe/__init__.py`: Observability: metrics, drift detection, logging.
- `aquilia/mlops/observe/drift.py`: Drift detection -- PSI, KS-test, and distribution tracking.
- `aquilia/mlops/observe/logger.py`: Feature and prediction logger.
- `aquilia/mlops/observe/metrics.py`: Prometheus-compatible metrics collector.
- `aquilia/mlops/optimizer/__init__.py`: Optimization pipeline: quantize, prune, export.
- `aquilia/mlops/optimizer/export.py`: Edge export utilities -- TFLite, CoreML, quantized ONNX.
- `aquilia/mlops/optimizer/pipeline.py`: Optimization Pipeline -- orchestrates quantization, pruning, fusion, compilation.
- `aquilia/mlops/orchestrator/__init__.py`: Aquilia MLOps Model Orchestrator.
- `aquilia/mlops/orchestrator/loader.py`: Model Loader -- lazy loading, hot reload, and lifecycle state management.
- `aquilia/mlops/orchestrator/orchestrator.py`: Model Orchestrator -- top-level façade for ML inference.
- `aquilia/mlops/orchestrator/persistence.py`: Model Persistence System -- Robust loading and saving for production models.
- `aquilia/mlops/orchestrator/registry.py`: Model Registry -- in-memory metadata-only registry for ML models.
- `aquilia/mlops/orchestrator/router.py`: Version Router -- routes inference requests to the correct model version.
- `aquilia/mlops/orchestrator/versioning.py`: Version Manager -- semantic versioning, promotion, and rollback.
- `aquilia/mlops/pack/__init__.py`: Modelpack builder and content store.
- `aquilia/mlops/pack/builder.py`: Modelpack Builder -- Creates ``.aquilia`` archive artifacts.
- `aquilia/mlops/pack/content_store.py`: Content-addressable blob store.
- `aquilia/mlops/pack/manifest_schema.py`: JSON Schema for modelpack ``manifest.json``.
- `aquilia/mlops/pack/signer.py`: Artifact signing and verification.
- `aquilia/mlops/plugins/__init__.py`: Plugin system and marketplace.
- `aquilia/mlops/plugins/example_plugin.py`: Example Aquilia MLOps plugin -- demonstrates how to write a plugin.
- `aquilia/mlops/plugins/host.py`: Plugin host -- discovers, loads, and manages lifecycle of MLOps plugins.
- `aquilia/mlops/plugins/marketplace.py`: Plugin marketplace -- lightweight discovery & installation of community
- `aquilia/mlops/registry/__init__.py`: Registry service and storage adapters.
- `aquilia/mlops/registry/models.py`: Registry data models -- SQLite backend (default).
- `aquilia/mlops/registry/service.py`: Registry Service -- HTTP API for publishing, fetching and managing modelpacks.
- `aquilia/mlops/registry/storage/__init__.py`: Storage adapter implementations.
- `aquilia/mlops/registry/storage/base.py`: Base storage adapter -- abstract interface for blob backends.
- `aquilia/mlops/registry/storage/filesystem.py`: Filesystem storage adapter -- stores blobs on local disk.
- `aquilia/mlops/registry/storage/s3.py`: S3 / MinIO storage adapter for registry blob storage.
- `aquilia/mlops/release/__init__.py`: Release management: rollouts, CI/CD.
- `aquilia/mlops/release/ci.py`: CI/CD templates and GitHub Actions configuration.
- `aquilia/mlops/release/rollout.py`: Release rollout engine -- canary, A/B, shadow traffic management.
- `aquilia/mlops/runtime/__init__.py`: Runtime adapters for model inference.
- `aquilia/mlops/runtime/base.py`: Runtime base -- abstract interface for inference backends.
- `aquilia/mlops/runtime/bento_exporter.py`: BentoML exporter -- generates BentoML-compatible service bundles.
- `aquilia/mlops/runtime/device_manager.py`: Device Manager -- auto-detection, fallback, monitoring, and locking for
- `aquilia/mlops/runtime/executor.py`: Inference Executor -- offloads blocking inference to thread/process pools.
- `aquilia/mlops/runtime/onnx_runtime.py`: ONNX Runtime adapter -- high-performance inference via onnxruntime.
- `aquilia/mlops/runtime/python_runtime.py`: Python in-process runtime -- loads and runs models natively in Python.
- `aquilia/mlops/runtime/torchserve_exporter.py`: TorchServe exporter -- generates TorchServe-compatible model archives.
- `aquilia/mlops/runtime/triton_adapter.py`: Triton Inference Server adapter.
- `aquilia/mlops/scheduler/__init__.py`: Autoscaling and placement scheduling.
- `aquilia/mlops/scheduler/autoscaler.py`: Autoscaler -- K8s HPA metrics exporter and scaling policy engine.
- `aquilia/mlops/scheduler/placement.py`: Hardware-aware placement scheduler.
- `aquilia/mlops/security/__init__.py`: Security: signing, encryption, RBAC.
- `aquilia/mlops/security/encryption.py`: Encryption at rest for registry blobs.
- `aquilia/mlops/security/rbac.py`: RBAC for registry operations.
- `aquilia/mlops/security/signing.py`: Security -- artifact signing, verification, and encryption at rest.
- `aquilia/mlops/serving/__init__.py`: Model serving layer.
- `aquilia/mlops/serving/batching.py`: Dynamic Batching Scheduler.
- `aquilia/mlops/serving/controllers.py`: MLOps Controller -- HTTP endpoints for model serving, registry, and observability.
- `aquilia/mlops/serving/middleware.py`: MLOps Middleware -- Inference metrics, rate limiting, and circuit breaker
- `aquilia/mlops/serving/router.py`: Traffic router -- canary, A/B, shadow, sticky routing for model deployments.
- `aquilia/mlops/serving/server.py`: Model Serving Server -- dev and production serving with typed endpoints.
