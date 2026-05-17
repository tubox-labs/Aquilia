# Mlops CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq pack save` | `aq pack save MODEL_PATH [--name VALUE] [--version VALUE] [--framework VALUE] [--env-lock VALUE] [--output VALUE] [--sign-key VALUE]` | Package a model into an .aquilia archive. |
| `aq pack inspect` | `aq pack inspect ARCHIVE_PATH` | Display manifest of an .aquilia archive. |
| `aq pack verify` | `aq pack verify ARCHIVE_PATH [--key VALUE]` | Verify the signature of an .aquilia archive. |
| `aq pack push` | `aq pack push ARCHIVE_PATH [--registry VALUE] [--tag VALUE]` | Push a pack to a remote registry. |
| `aq model serve` | `aq model serve MODEL_PATH [--runtime VALUE] [--host VALUE] [--port VALUE] [--batch-size VALUE] [--batch-latency-ms VALUE]` | Serve a model with the built-in inference server. |
| `aq model health` | `aq model health [--url VALUE]` | Check model server health. |
| `aq mlops-deploy rollout` | `aq mlops-deploy rollout MODEL_NAME [--from-version VALUE] [--to-version VALUE] [--strategy VALUE] [--steps VALUE] [--error-threshold VALUE]` | Start a progressive rollout. |
| `aq mlops-deploy ci-template` | `aq mlops-deploy ci-template [--registry VALUE] [--output VALUE]` | Generate CI/CD templates (GitHub Actions + Dockerfile). |
| `aq observe drift` | `aq observe drift REFERENCE_CSV CURRENT_CSV [--method VALUE] [--threshold VALUE]` | Detect data drift between reference and current datasets. |
| `aq observe metrics` | `aq observe metrics [--format VALUE]` | Export current metrics. |
| `aq export onnx` | `aq export onnx MODEL_PATH [--output VALUE] [--opset VALUE]` | Export a PyTorch model to ONNX. |
| `aq export edge` | `aq export edge MODEL_PATH [--target VALUE] [--output VALUE]` | Export model for edge deployment. |
| `aq plugin list` | `aq plugin list` | List discovered plugins. |
| `aq plugin install` | `aq plugin install PACKAGE_NAME` | Install a plugin from PyPI. |
| `aq plugin uninstall` | `aq plugin uninstall PACKAGE_NAME` | Uninstall a plugin. |
| `aq plugin search` | `aq plugin search QUERY [--verified-only]` | Search the plugin marketplace. |
| `aq lineage show` | `aq lineage show [--format VALUE]` | Show the full model lineage graph. |
| `aq lineage ancestors` | `aq lineage ancestors MODEL_ID` | Show all ancestors (transitive parents) of a model. |
| `aq lineage descendants` | `aq lineage descendants MODEL_ID` | Show all descendants (derived models) of a model. |
| `aq lineage path` | `aq lineage path FROM_MODEL TO_MODEL` | Find derivation path between two models. |
| `aq experiment create` | `aq experiment create EXPERIMENT_ID [--description VALUE] [--arm VALUE]` | Create a new A/B experiment. |
| `aq experiment list` | `aq experiment list` | List all experiments. |
| `aq experiment conclude` | `aq experiment conclude EXPERIMENT_ID [--winner VALUE]` | Conclude an experiment and optionally declare a winner. |
| `aq experiment summary` | `aq experiment summary EXPERIMENT_ID` | Show detailed experiment summary with per-arm metrics. |

## Detailed Commands

### `aq pack save`

Package a model into an .aquilia archive.

```bash
aq pack save MODEL_PATH [--name VALUE] [--version VALUE] [--framework VALUE] [--env-lock VALUE] [--output VALUE] [--sign-key VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `name` | `--name, -n` | True | `not set` | Model name |
| Option | `version` | `--version, -V` | True | `not set` | Semantic version |
| Option | `framework` | `--framework, -f` | False | `custom` | Model framework |
| Option | `env_lock` | `--env-lock` | False | `not set` | Path to requirements.txt or conda lock |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `sign_key` | `--sign-key` | False | `not set` | HMAC key or path to RSA private key for signing |

### `aq pack inspect`

Display manifest of an .aquilia archive.

```bash
aq pack inspect ARCHIVE_PATH
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |  |

### `aq pack verify`

Verify the signature of an .aquilia archive.

```bash
aq pack verify ARCHIVE_PATH [--key VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |  |
| Option | `key` | `--key` | True | `not set` | HMAC key or path to RSA public key |

### `aq pack push`

Push a pack to a remote registry.

```bash
aq pack push ARCHIVE_PATH [--registry VALUE] [--tag VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `archive_path` | `archive_path` | True | `not set` |  |
| Option | `registry` | `--registry, -r` | False | `http://localhost:8080` | Registry URL |
| Option | `tag` | `--tag, -t` | False | `not set` | Additional tags |

### `aq model serve`

Serve a model with the built-in inference server.

```bash
aq model serve MODEL_PATH [--runtime VALUE] [--host VALUE] [--port VALUE] [--batch-size VALUE] [--batch-latency-ms VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `runtime` | `--runtime, -r` | False | `python` |  |
| Option | `host` | `--host` | False | `0.0.0.0` | Bind host |
| Option | `port` | `--port, -p` | False | `9000` | Bind port |
| Option | `batch_size` | `--batch-size` | False | `1` | Max batch size |
| Option | `batch_latency_ms` | `--batch-latency-ms` | False | `50` | Max batch wait (ms) |

### `aq model health`

Check model server health.

```bash
aq model health [--url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `url` | `--url` | False | `http://localhost:9000` | Server URL |

### `aq mlops-deploy rollout`

Start a progressive rollout.

```bash
aq mlops-deploy rollout MODEL_NAME [--from-version VALUE] [--to-version VALUE] [--strategy VALUE] [--steps VALUE] [--error-threshold VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_name` | `model_name` | True | `not set` |  |
| Option | `from_version` | `--from-version` | True | `not set` | Current version |
| Option | `to_version` | `--to-version` | True | `not set` | Target version |
| Option | `strategy` | `--strategy` | False | `canary` |  |
| Option | `steps` | `--steps` | False | `5` | Number of rollout phases |
| Option | `error_threshold` | `--error-threshold` | False | `0.05` | Auto-rollback error rate |

### `aq mlops-deploy ci-template`

Generate CI/CD templates (GitHub Actions + Dockerfile).

```bash
aq mlops-deploy ci-template [--registry VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `registry` | `--registry` | False | `ghcr.io/my-org/models` | Container registry |
| Option | `output` | `--output, -o` | False | `.` | Output directory |

### `aq observe drift`

Detect data drift between reference and current datasets.

```bash
aq observe drift REFERENCE_CSV CURRENT_CSV [--method VALUE] [--threshold VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `reference_csv` | `reference_csv` | True | `not set` |  |
| Argument | `current_csv` | `current_csv` | True | `not set` |  |
| Option | `method` | `--method` | False | `psi` |  |
| Option | `threshold` | `--threshold` | False | `0.2` | Drift alert threshold |

### `aq observe metrics`

Export current metrics.

```bash
aq observe metrics [--format VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `fmt` | `--format` | False | `json` |  |

### `aq export onnx`

Export a PyTorch model to ONNX.

```bash
aq export onnx MODEL_PATH [--output VALUE] [--opset VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `output` | `--output, -o` | True | `not set` | Output .onnx path |
| Option | `opset` | `--opset` | False | `17` | ONNX opset version |

### `aq export edge`

Export model for edge deployment.

```bash
aq export edge MODEL_PATH [--target VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_path` | `model_path` | True | `not set` |  |
| Option | `target` | `--target` | True | `not set` |  |
| Option | `output` | `--output, -o` | True | `not set` |  |

### `aq plugin list`

List discovered plugins.

```bash
aq plugin list
```

### `aq plugin install`

Install a plugin from PyPI.

```bash
aq plugin install PACKAGE_NAME
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `package_name` | `package_name` | True | `not set` |  |

### `aq plugin uninstall`

Uninstall a plugin.

```bash
aq plugin uninstall PACKAGE_NAME
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `package_name` | `package_name` | True | `not set` |  |

### `aq plugin search`

Search the plugin marketplace.

```bash
aq plugin search QUERY [--verified-only]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `query` | `query` | True | `not set` |  |
| Option | `verified_only` | `--verified-only` | False | `False` | Only show verified plugins |

### `aq lineage show`

Show the full model lineage graph.

```bash
aq lineage show [--format VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `fmt` | `--format` | False | `tree` |  |

### `aq lineage ancestors`

Show all ancestors (transitive parents) of a model.

```bash
aq lineage ancestors MODEL_ID
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_id` | `model_id` | True | `not set` |  |

### `aq lineage descendants`

Show all descendants (derived models) of a model.

```bash
aq lineage descendants MODEL_ID
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `model_id` | `model_id` | True | `not set` |  |

### `aq lineage path`

Find derivation path between two models.

```bash
aq lineage path FROM_MODEL TO_MODEL
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `from_model` | `from_model` | True | `not set` |  |
| Argument | `to_model` | `to_model` | True | `not set` |  |

### `aq experiment create`

Create a new A/B experiment.

```bash
aq experiment create EXPERIMENT_ID [--description VALUE] [--arm VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |  |
| Option | `description` | `--description, -d` | False | `` | Experiment description |
| Option | `arm` | `--arm, -a` | False | `not set` | Arm spec: name:version:weight (e.g. control:v1:0.5) |

### `aq experiment list`

List all experiments.

```bash
aq experiment list
```

### `aq experiment conclude`

Conclude an experiment and optionally declare a winner.

```bash
aq experiment conclude EXPERIMENT_ID [--winner VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |  |
| Option | `winner` | `--winner, -w` | False | `` | Winning arm name |

### `aq experiment summary`

Show detailed experiment summary with per-arm metrics.

```bash
aq experiment summary EXPERIMENT_ID
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `experiment_id` | `experiment_id` | True | `not set` |  |

## General Commands Useful For This Module

| Command | Why it matters |
| --- | --- |
| `aq validate` | Validates workspace manifests and catches invalid component paths. |
| `aq doctor` | Runs environment, workspace, manifest, registry, integration, and deployment diagnostics. |
| `aq inspect config` | Shows resolved config after workspace/env merging. |
| `aq inspect modules` | Lists discovered modules. |
| `aq inspect routes` | Shows compiled routes when the module contributes controllers. |
| `aq run` | Starts the dev server and executes startup wiring. |

## Error Behavior

- Click handles missing required arguments and invalid options before command callbacks run.
- Most operational commands require `workspace.py`; the root CLI guard allows help/version/init/doctor without it.
- Commands that touch external providers, databases, or files can fail with subsystem-specific faults or provider errors.
