"""
MLOps Blueprints -- Aquilia Blueprint definitions for all MLOps data types.

Uses ``aquilia.blueprints`` for declarative validation, coercion,
and output rendering across the entire ML pipeline.

Blueprints::

    ModelpackManifestBlueprint  -- validate / render manifest JSON
    InferenceRequestBlueprint   -- validate incoming inference payloads
    InferenceResultBlueprint    -- render inference results
    DriftReportBlueprint        -- render drift detection reports
    RolloutConfigBlueprint      -- validate rollout configuration
    RolloutStateBlueprint       -- render rollout state
    ScalingPolicyBlueprint      -- validate autoscaler policy
    PluginDescriptorBlueprint   -- render plugin metadata
    NodeInfoBlueprint           -- validate node registration
    PlacementRequestBlueprint   -- validate placement requests
    ProvenanceBlueprint         -- validate provenance metadata
"""

from __future__ import annotations

from aquilia.blueprints import (
    Blueprint,
    TextFacet,
    IntFacet,
    FloatFacet,
    BoolFacet,
    ListFacet,
    DictFacet,
    ChoiceFacet,
    DateTimeFacet,
    JSONFacet,
    ReadOnly,
)

from .._types import (
    Framework,
    RuntimeKind,
    BatchingStrategy,
    RolloutStrategy,
    DriftMethod,
    QuantizePreset,
    ModelType,
    InferenceMode,
    DeviceType,
)


# ── TensorSpec ───────────────────────────────────────────────────────────

class TensorSpecBlueprint(Blueprint):
    """Validates and renders tensor specifications."""
    name = TextFacet(max_length=128)
    dtype = TextFacet(max_length=32)
    shape = ListFacet(required=True)


# ── BlobRef ──────────────────────────────────────────────────────────────

class BlobRefBlueprint(Blueprint):
    """Validates blob references."""
    path = TextFacet(max_length=512)
    digest = TextFacet(max_length=128)
    size = IntFacet(min_value=0)


# ── Provenance ───────────────────────────────────────────────────────────

class ProvenanceBlueprint(Blueprint):
    """Validates provenance metadata."""
    git_sha = TextFacet(max_length=64, required=False, default="")
    dataset_snapshot = TextFacet(max_length=256, required=False, default="")
    dockerfile = TextFacet(max_length=256, required=False, default="")
    build_timestamp = TextFacet(max_length=64, required=False, default="")


# ── ModelpackManifest ────────────────────────────────────────────────────

class ModelpackManifestBlueprint(Blueprint):
    """
    Full manifest blueprint with deep validation.

    Usage::

        bp = ModelpackManifestBlueprint(data=manifest_dict)
        if bp.is_sealed():
            manifest = bp.validated_data
        else:
            raise PackBuildFault(str(bp.errors))
    """
    name = TextFacet(max_length=256)
    version = TextFacet(max_length=64)
    framework = ChoiceFacet(
        choices=[f.value for f in Framework],
        required=False,
        default="custom",
    )
    entrypoint = TextFacet(max_length=256, required=False, default="")
    env_lock = TextFacet(max_length=128, required=False, default="env.lock")
    created_at = TextFacet(required=False, default="")
    signed_by = TextFacet(max_length=256, required=False, default="")
    metadata = DictFacet(required=False, default=dict)


# ── InferenceRequest ─────────────────────────────────────────────────────

class InferenceRequestBlueprint(Blueprint):
    """
    Validates incoming inference request payloads.

    Used by the serving controller to validate HTTP request bodies
    before dispatching to the batcher.
    """
    request_id = TextFacet(max_length=128)
    inputs = DictFacet(required=True)
    parameters = DictFacet(required=False, default=dict)


# ── InferenceResult ──────────────────────────────────────────────────────

class InferenceResultBlueprint(Blueprint):
    """Renders inference results for API responses."""
    request_id = ReadOnly()
    outputs = DictFacet()
    latency_ms = FloatFacet(min_value=0.0)
    metadata = DictFacet(required=False, default=dict)


# ── DriftReport ──────────────────────────────────────────────────────────

class DriftReportBlueprint(Blueprint):
    """Renders drift detection reports."""
    method = ChoiceFacet(choices=[m.value for m in DriftMethod])
    score = FloatFacet()
    threshold = FloatFacet()
    is_drifted = BoolFacet()
    feature_scores = DictFacet(required=False, default=dict)
    window_start = TextFacet(required=False, default="")
    window_end = TextFacet(required=False, default="")


# ── RolloutConfig ────────────────────────────────────────────────────────

class RolloutConfigBlueprint(Blueprint):
    """Validates rollout configuration payloads."""
    from_version = TextFacet(max_length=64)
    to_version = TextFacet(max_length=64)
    strategy = ChoiceFacet(
        choices=[s.value for s in RolloutStrategy],
        required=False,
        default="canary",
    )
    percentage = IntFacet(min_value=0, max_value=100, required=False, default=10)
    metric = TextFacet(max_length=64, required=False, default="latency_p95")
    threshold = FloatFacet(required=False, default=0.0)
    auto_rollback = BoolFacet(required=False, default=True)
    step_interval_seconds = IntFacet(min_value=1, required=False, default=300)


# ── RolloutState ─────────────────────────────────────────────────────────

class RolloutStateBlueprint(Blueprint):
    """Renders rollout state for API responses."""
    id = ReadOnly()
    phase = ReadOnly()
    current_percentage = IntFacet()
    steps_completed = IntFacet()
    started_at = FloatFacet()
    completed_at = FloatFacet()
    error = TextFacet(required=False, default="")


# ── ScalingPolicy ────────────────────────────────────────────────────────

class ScalingPolicyBlueprint(Blueprint):
    """Validates autoscaler policy configuration."""
    min_replicas = IntFacet(min_value=0, required=False, default=1)
    max_replicas = IntFacet(min_value=1, required=False, default=10)
    target_concurrency = FloatFacet(min_value=0.1, required=False, default=10.0)
    target_latency_p95_ms = FloatFacet(min_value=0.0, required=False, default=100.0)
    scale_up_threshold = FloatFacet(min_value=0.0, max_value=1.0, required=False, default=0.8)
    scale_down_threshold = FloatFacet(min_value=0.0, max_value=1.0, required=False, default=0.3)
    cooldown_seconds = IntFacet(min_value=0, required=False, default=60)


# ── NodeInfo ─────────────────────────────────────────────────────────────

class NodeInfoBlueprint(Blueprint):
    """Validates compute node registration payloads."""
    node_id = TextFacet(max_length=128)
    device_type = ChoiceFacet(choices=["cpu", "gpu", "npu"], required=False, default="cpu")
    total_memory_mb = FloatFacet(min_value=0.0, required=False, default=0.0)
    available_memory_mb = FloatFacet(min_value=0.0, required=False, default=0.0)
    current_load = FloatFacet(min_value=0.0, max_value=1.0, required=False, default=0.0)
    gpu_available = BoolFacet(required=False, default=False)


# ── PlacementRequest ────────────────────────────────────────────────────

class PlacementRequestBlueprint(Blueprint):
    """Validates model placement request payloads."""
    model_name = TextFacet(max_length=256)
    model_size_mb = FloatFacet(min_value=0.0)
    preferred_device = ChoiceFacet(
        choices=["cpu", "gpu", "npu", "any"],
        required=False,
        default="any",
    )
    gpu_required = BoolFacet(required=False, default=False)


# ── Plugin ───────────────────────────────────────────────────────────────

class PluginDescriptorBlueprint(Blueprint):
    """Renders plugin descriptor for API responses."""
    name = ReadOnly()
    version = ReadOnly()
    module = ReadOnly()
    state = ReadOnly()
    error = TextFacet(required=False, default="")
    metadata = DictFacet(required=False, default=dict)


# ── Metrics ──────────────────────────────────────────────────────────────

class MetricsSummaryBlueprint(Blueprint):
    """Renders metrics summary for API responses."""
    model_name = ReadOnly()
    model_version = ReadOnly()
    # All other metrics are dynamic, rendered via DictFacet


# ── LLM / Streaming Blueprints ──────────────────────────────────────────

class LLMConfigBlueprint(Blueprint):
    """Validates LLM configuration payloads."""
    max_tokens = IntFacet(min_value=1, required=False, default=512)
    temperature = FloatFacet(min_value=0.0, max_value=2.0, required=False, default=1.0)
    top_k = IntFacet(min_value=1, required=False, default=50)
    top_p = FloatFacet(min_value=0.0, max_value=1.0, required=False, default=1.0)
    repetition_penalty = FloatFacet(min_value=0.0, required=False, default=1.0)
    stop_sequences = ListFacet(required=False, default=list)
    context_length = IntFacet(min_value=1, required=False, default=2048)
    dtype = TextFacet(max_length=16, required=False, default="float16")
    device_map = TextFacet(max_length=32, required=False, default="auto")
    quantize = ChoiceFacet(
        choices=[q.value for q in QuantizePreset],
        required=False,
        default="none",
    )
    trust_remote_code = BoolFacet(required=False, default=False)


class StreamChunkBlueprint(Blueprint):
    """Renders a single streaming token/chunk for SSE responses."""
    request_id = ReadOnly()
    token = TextFacet(required=False, default="")
    token_index = IntFacet(min_value=0)
    finish_reason = TextFacet(required=False, default="")
    logprob = FloatFacet(required=False)


class TokenUsageBlueprint(Blueprint):
    """Renders token usage statistics for LLM inference."""
    prompt_tokens = IntFacet(min_value=0)
    completion_tokens = IntFacet(min_value=0)
    total_tokens = IntFacet(min_value=0)


class LLMInferenceRequestBlueprint(Blueprint):
    """
    Validates incoming LLM inference request payloads.

    Extends InferenceRequestBlueprint with LLM-specific fields.
    """
    request_id = TextFacet(max_length=128)
    inputs = DictFacet(required=True)
    parameters = DictFacet(required=False, default=dict)
    # LLM-specific
    priority = IntFacet(min_value=0, max_value=10, required=False, default=5)
    stream = BoolFacet(required=False, default=False)
    max_tokens = IntFacet(min_value=1, required=False, default=512)
    timeout_ms = FloatFacet(min_value=0.0, required=False, default=30000.0)
    temperature = FloatFacet(min_value=0.0, max_value=2.0, required=False, default=1.0)
    top_k = IntFacet(min_value=1, required=False, default=50)


class LLMInferenceResultBlueprint(Blueprint):
    """Renders LLM inference results including token metrics."""
    request_id = ReadOnly()
    outputs = DictFacet()
    latency_ms = FloatFacet(min_value=0.0)
    token_count = IntFacet(min_value=0, required=False, default=0)
    prompt_tokens = IntFacet(min_value=0, required=False, default=0)
    finish_reason = TextFacet(required=False, default="")
    metadata = DictFacet(required=False, default=dict)
    usage = DictFacet(required=False, default=dict)


class ChatMessageBlueprint(Blueprint):
    """Validates a single chat message."""
    role = ChoiceFacet(choices=["system", "user", "assistant", "function"], required=True)
    content = TextFacet(required=True)
    name = TextFacet(max_length=64, required=False, default="")


class ChatRequestBlueprint(Blueprint):
    """
    Validates chat-style LLM request payloads.

    Compatible with OpenAI-style chat completions API.
    """
    messages = ListFacet(required=True)
    model = TextFacet(max_length=256, required=False, default="")
    stream = BoolFacet(required=False, default=False)
    max_tokens = IntFacet(min_value=1, required=False, default=512)
    temperature = FloatFacet(min_value=0.0, max_value=2.0, required=False, default=1.0)
    top_k = IntFacet(min_value=1, required=False, default=50)
    top_p = FloatFacet(min_value=0.0, max_value=1.0, required=False, default=1.0)
    stop = ListFacet(required=False, default=list)


class ChatResponseBlueprint(Blueprint):
    """Renders chat-style LLM response."""
    id = ReadOnly()
    model = ReadOnly()
    choices = ListFacet()
    usage = DictFacet(required=False, default=dict)
    created = FloatFacet(required=False)


class CircuitBreakerStatusBlueprint(Blueprint):
    """Renders circuit breaker state for API responses."""
    state = ChoiceFacet(choices=["closed", "open", "half_open"])
    failure_count = IntFacet(min_value=0)
    success_count = IntFacet(min_value=0)
    total_requests = IntFacet(min_value=0)
    total_rejections = IntFacet(min_value=0)
    last_failure_time = FloatFacet(required=False, default=0.0)


class RateLimiterStatusBlueprint(Blueprint):
    """Renders rate limiter state for API responses."""
    rate_rps = FloatFacet(min_value=0.0)
    capacity = IntFacet(min_value=0)
    available_tokens = FloatFacet(min_value=0.0)


class MemoryStatusBlueprint(Blueprint):
    """Renders memory tracker state for API responses."""
    current_mb = FloatFacet(min_value=0.0)
    soft_limit_mb = FloatFacet(min_value=0.0)
    hard_limit_mb = FloatFacet(min_value=0.0)
    utilization_pct = FloatFacet(min_value=0.0, max_value=100.0)
    exceeds_soft = BoolFacet()
    exceeds_hard = BoolFacet()


class ModelCapabilitiesBlueprint(Blueprint):
    """Renders model capabilities for API responses."""
    model_name = ReadOnly()
    model_type = ChoiceFacet(choices=[t.value for t in ModelType], required=False, default="SLM")
    supports_streaming = BoolFacet(required=False, default=False)
    supports_chat = BoolFacet(required=False, default=False)
    inference_modes = ListFacet(required=False, default=list)
    device = TextFacet(required=False, default="cpu")
    max_context_length = IntFacet(min_value=0, required=False, default=0)
