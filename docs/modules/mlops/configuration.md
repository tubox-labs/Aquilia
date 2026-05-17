# MLOps Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `LineageNode` | `aquilia/mlops/_structures.py` | model_id: str, version: str, framework: str, created_at: float, metadata: dict[str, Any], parents: list[str], children: list[str] | A single node in the model lineage graph. |
| `ExperimentArm` | `aquilia/mlops/_structures.py` | name: str, model_version: str, weight: float, metrics: dict[str, float], request_count: int | One arm of an A/B experiment. |
| `Experiment` | `aquilia/mlops/_structures.py` | experiment_id: str, description: str, arms: list[ExperimentArm], status: str, created_at: float, metadata: dict[str, Any] | A/B experiment definition. |
| `TensorSpec` | `aquilia/mlops/_types.py` | name: str, dtype: DType, shape: list[Any] | Describes a single tensor in the inference signature. |
| `BlobRef` | `aquilia/mlops/_types.py` | path: str, digest: str, size: int | Reference to a blob inside a modelpack. |
| `Provenance` | `aquilia/mlops/_types.py` | git_sha: str, dataset_snapshot: str, dockerfile: str, build_timestamp: str | Provenance metadata for reproducibility. |
| `LLMConfig` | `aquilia/mlops/_types.py` | model_type: ModelType, max_seq_length: int, max_new_tokens: int, max_batch_tokens: int, kv_cache_max_mb: int, tensor_parallel: int, pipeline_parallel: int, dtype: str, device: DeviceType, trust_remote_code: bool, tokenizer_name: str, chat_template: str, ... | Configuration specific to LLM/SLM model serving. |
| `ModelpackManifest` | `aquilia/mlops/_types.py` | name: str, version: str, framework: str, entrypoint: str, inputs: list[TensorSpec], outputs: list[TensorSpec], env_lock: str, provenance: Provenance, blobs: list[BlobRef], created_at: str, signed_by: str, metadata: dict[str, Any], ... | Complete manifest for a modelpack artifact. |
| `InferenceRequest` | `aquilia/mlops/_types.py` | request_id: str, inputs: dict[str, Any], parameters: dict[str, Any], timestamp: float, priority: int, stream: bool, max_tokens: int, timeout_ms: float | A single inference request. |
| `InferenceResult` | `aquilia/mlops/_types.py` | request_id: str, outputs: dict[str, Any], latency_ms: float, metadata: dict[str, Any], token_count: int, prompt_tokens: int, finish_reason: str | Result of a single inference. |
| `StreamChunk` | `aquilia/mlops/_types.py` | request_id: str, token: str, token_id: int, is_finished: bool, finish_reason: str, cumulative_tokens: int, latency_ms: float | A single chunk in a streaming inference response. |
| `BatchRequest` | `aquilia/mlops/_types.py` | requests: list[InferenceRequest], batch_id: str | Aggregated batch of inference requests. |
| `PlacementScore` | `aquilia/mlops/_types.py` | node_id: str, device_affinity: float, memory_fit: float, current_load: float, cold_start_cost: float, total: float | Score for scheduler placement decisions. |
| `RolloutConfig` | `aquilia/mlops/_types.py` | from_version: str, to_version: str, strategy: RolloutStrategy, percentage: int, metric: str, threshold: float, auto_rollback: bool, step_interval_seconds: int | Configuration for a traffic rollout. |
| `DriftReport` | `aquilia/mlops/_types.py` | method: DriftMethod, score: float, threshold: float, is_drifted: bool, feature_scores: dict[str, float], window_start: str, window_end: str | Result of a drift detection analysis. |
| `CircuitBreakerConfig` | `aquilia/mlops/_types.py` | failure_threshold: int, success_threshold: int, timeout_seconds: float, half_open_max_calls: int | Configuration for inference circuit breaker. |
| `TokenUsage` | `aquilia/mlops/_types.py` | prompt_tokens: int, completion_tokens: int, total_tokens: int, tokens_per_second: float, time_to_first_token_ms: float, kv_cache_usage_mb: float | Token usage tracking for LLM inference. |
| `RouteDefinition` | `aquilia/mlops/api/route_generator.py` | method: str, path: str, handler: Callable, model_name: str, description: str | A generated route definition ready for controller compilation. |
| `MLOpsConfig` | `aquilia/mlops/di/providers.py` | See class attributes and constructor methods. | Typed configuration for MLOps DI registration. |
| `PipelineContext` | `aquilia/mlops/engine/pipeline.py` | request_id: str, model_name: str, model_version: str, trace_id: str, start_time: float, stage_timings: dict[str, float], metadata: dict[str, Any] | Per-request context flowing through the pipeline. |
| `FeatureAttribution` | `aquilia/mlops/explain/hooks.py` | name: str, value: float, base_value: float | Single feature's contribution. |
| `Explanation` | `aquilia/mlops/explain/hooks.py` | method: ExplainMethod, attributions: list[FeatureAttribution], prediction: Any, extra: dict[str, Any] | Complete explanation for one prediction. |
| `PIIMatch` | `aquilia/mlops/explain/privacy.py` | kind: PIIKind, start: int, end: int, text: str | Configuration or typed data class. |
| `ModelManifestEntry` | `aquilia/mlops/manifest/config.py` | name: str, class_path: str, version: str, device: str, batch_size: int, max_batch_latency_ms: float, warmup_requests: int, workers: int, timeout_ms: float, artifacts_dir: str, supports_streaming: bool, tags: list[str], ... | Configuration for a single model from the manifest. |
| `MLOpsManifestConfig` | `aquilia/mlops/manifest/config.py` | enabled: bool, default_device: str, default_workers: int, default_batch_size: int, default_max_batch_latency_ms: float, default_timeout_ms: float, route_prefix: str, models: list[ModelManifestEntry] | Parsed ``[mlops]`` configuration from Aquilia workspace config. |
| `MetricPoint` | `aquilia/mlops/observe/metrics.py` | name: str, value: float, labels: dict[str, str], timestamp: float | Single metric data point. |
| `ExportResult` | `aquilia/mlops/optimizer/export.py` | target: str, output_path: str, size_bytes: int, notes: list[str] | Result of an edge export. |
| `OptimizationResult` | `aquilia/mlops/optimizer/pipeline.py` | original_size_bytes: int, optimized_size_bytes: int, original_path: str, optimized_path: str, preset: str, compression_ratio: float, notes: list[str] | Result of an optimization pass. |
| `ModelBundle` | `aquilia/mlops/orchestrator/persistence.py` | name: str, version: str, weights_path: Path, metadata: dict[str, Any], framework: str, dtype: str | A complete model bundle ready for persistence. |
| `ModelConfig` | `aquilia/mlops/orchestrator/registry.py` | device: str, batch_size: int, max_batch_latency_ms: float, warmup_requests: int, workers: int, timeout_ms: float, artifacts_dir: str, metadata: dict[str, Any] | Per-model configuration (from manifest or decorator). |
| `ModelEntry` | `aquilia/mlops/orchestrator/registry.py` | name: str, version: str, model_class: Any, config: ModelConfig, state: ModelState, registered_at: float, supports_streaming: bool, tags: list[str] | Registry entry for a single model version. |
| `CanaryConfig` | `aquilia/mlops/orchestrator/router.py` | canary_version: str, base_version: str, percentage: float | Active canary configuration for a model. |
| `PluginDescriptor` | `aquilia/mlops/plugins/host.py` | name: str, version: str, module: str, state: PluginState, instance: Any, error: str &#124; None, metadata: dict[str, Any] | Configuration or typed data class. |
| `MarketplaceEntry` | `aquilia/mlops/plugins/marketplace.py` | name: str, version: str, description: str, author: str, pypi_name: str, homepage: str, tags: list[str], downloads: int, verified: bool | Configuration or typed data class. |
| `RolloutState` | `aquilia/mlops/release/rollout.py` | id: str, config: RolloutConfig, phase: RolloutPhase, current_percentage: int, steps_completed: int, started_at: float, completed_at: float, metrics_history: list[dict[str, Any]], error: str | Current state of a rollout. |
| `DeviceInfo` | `aquilia/mlops/runtime/device_manager.py` | name: str, kind: DeviceKind, index: int, total_memory_mb: float, available_memory_mb: float, is_available: bool, metadata: dict[str, Any] | Snapshot of a single compute device. |
| `ScalingPolicy` | `aquilia/mlops/scheduler/autoscaler.py` | min_replicas: int, max_replicas: int, target_concurrency: float, target_latency_p95_ms: float, scale_up_threshold: float, scale_down_threshold: float, cooldown_seconds: int, window_seconds: float, bucket_width: float, target_gpu_utilization: float, gpu_scale_up_threshold: float, gpu_scale_down_threshold: float, ... | Autoscaling policy definition. |
| `ScalingDecision` | `aquilia/mlops/scheduler/autoscaler.py` | current_replicas: int, desired_replicas: int, reason: str, metrics: dict[str, float] | Output of a scaling evaluation. |
| `NodeInfo` | `aquilia/mlops/scheduler/placement.py` | node_id: str, device_type: str, total_memory_mb: float, available_memory_mb: float, current_load: float, gpu_available: bool, models_loaded: list[str], gpu_memory_total_mb: float, gpu_memory_available_mb: float, gpu_utilization: float, gpu_name: str, compute_capability: str | Information about a compute node. |
| `PlacementRequest` | `aquilia/mlops/scheduler/placement.py` | model_name: str, model_size_mb: float, preferred_device: str, gpu_required: bool, gpu_memory_required_mb: float, model_type: str, quantized: bool, min_compute_capability: str | Request for model placement. |
| `Role` | `aquilia/mlops/security/rbac.py` | name: str, permissions: set[Permission], description: str | A named role with a set of permissions. |
| `RouteTarget` | `aquilia/mlops/serving/router.py` | version: str, weight: float, handler: Callable &#124; None, request_count: int, error_count: int, total_latency_ms: float | A model version target with associated weight. |

## Common Entry Points

- `MLOpsIntegration`
- `MLOpsConfig`
- `Runtime configuration dataclasses`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
