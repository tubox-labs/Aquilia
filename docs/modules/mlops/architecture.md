# MLOps Architecture

## Runtime Role

The native model operations platform for model definitions, serving, registries, runtime execution, batching, scheduling, rollout, observability, model packs, plugins, security, and deployment assets.

The implementation is split across 76 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 58 |
| `logging` | 49 |
| `typing` | 40 |
| `collections` | 24 |
| `_types` | 21 |
| `dataclasses` | 21 |
| `time` | 21 |
| `pathlib` | 12 |
| `engine` | 10 |
| `enum` | 9 |
| `runtime` | 8 |
| `asyncio` | 7 |
| `base` | 7 |
| `_structures` | 6 |
| `aquilia` | 6 |
| `hashlib` | 6 |
| `registry` | 6 |
| `contextlib` | 5 |
| `json` | 5 |
| `serving` | 5 |
| `importlib` | 4 |
| `inspect` | 4 |
| `pack` | 4 |
| `random` | 4 |
| `abc` | 3 |
| `math` | 3 |
| `os` | 3 |
| `uuid` | 3 |
| `api` | 2 |
| `config` | 2 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
