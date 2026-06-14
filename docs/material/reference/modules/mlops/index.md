# MLOps Module

> `aquilia.mlops` — Model lifecycle management

The MLOps module provides model packaging, registry management, serving, rollout engine, plugins, lineage tracking, experiments, and export — all available as an optional extra (`aquilia[mlops]`).

## When to Use

Use the MLOps module when you need:

- Packaging ML models for deployment
- Model registry management
- Canary/blue-green model rollout
- Experiment tracking
- Model lineage and provenance

## Key Capabilities

| Capability | Description |
|---|---|
| Model Registry | Versioned model storage and retrieval |
| Rollout Engine | Gradual model deployment with traffic splitting |
| Plugins | Extensible model pipeline plugins |
| Export | Model export in standard formats |
| Lineage | Model training provenance tracking |
| Experiments | Experiment tracking and comparison |

## CLI Usage

```bash
# Package a model
aq pack model.pkl --name sentiment-v2

# Deploy a model
aq mlops-deploy sentiment-v2 --stage canary --traffic 10%

# Observe model performance
aq observe sentiment-v2

# Export model
aq export sentiment-v2 --format onnx

# Plugin management
aq plugin install my-custom-plugin

# Lineage tracking
aq lineage sentiment-v2

# Experiment management
aq experiment list
```

## Installation

```bash
pip install aquilia[mlops]
```

## Related Modules

- [artifacts](../artifacts/index.md) — Model artifacts for deployment
- [cli](../cli/index.md) — MLOps CLI commands
- [storage](../storage/index.md) — Model storage backends