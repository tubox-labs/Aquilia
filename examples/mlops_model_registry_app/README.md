# MLOps Model Registry App

## Purpose

Demonstrates model metadata registration, local `AquiliaModel` inference, progressive rollout state, and plugin host registration.

## Architecture

- `workspace.py` enables `MLOpsIntegration` with an in-memory registry backend.
- `MLOpsRegistryService` owns `ModelRegistry`, `RolloutEngine`, and `PluginHost`.
- `SentimentModel` subclasses `AquiliaModel` and implements `predict()`.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/mlops_model_registry_app -q
```

## Run

```bash
cd examples/mlops_model_registry_app
python -m uvicorn runtime:app --reload --port 8071
```

## Expected Behavior

The service can register a model version, perform deterministic local inference, advance a rollout, and list a manually registered plugin.

## Common Pitfalls

- Registry registration stores metadata; runtime loading is handled separately by loader/orchestrator components.
- Keep model artifacts local or mocked in examples unless credentials are required explicitly.

## Extension Ideas

Add modelpack building, filesystem registry storage, drift metrics, request batching, and generated serving routes.

## Related APIs

`AquiliaModel`, `ModelRegistry`, `RolloutEngine`, `RolloutConfig`, `PluginHost`, `MLOpsIntegration`.
