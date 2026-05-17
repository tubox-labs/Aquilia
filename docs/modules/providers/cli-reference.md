# Providers CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq deploy dockerfile` | `aq deploy dockerfile [--dev] [--mlops] [--output VALUE] [--force] [--dry-run]` | Generate production-ready Dockerfiles. |
| `aq deploy compose` | `aq deploy compose [--dev] [--monitoring] [--output VALUE] [--force] [--dry-run]` | Generate docker-compose.yml for the workspace. |
| `aq deploy kubernetes` | `aq deploy kubernetes [--output VALUE] [--mlops] [--force] [--dry-run]` | Generate production Kubernetes manifests. |
| `aq deploy nginx` | `aq deploy nginx [--output VALUE] [--force] [--dry-run]` | Generate Nginx reverse-proxy configuration. |
| `aq deploy ci` | `aq deploy ci [--provider VALUE] [--output VALUE] [--force] [--dry-run]` | Generate CI/CD pipeline configuration. |
| `aq deploy monitoring` | `aq deploy monitoring [--output VALUE] [--force] [--dry-run]` | Generate monitoring configuration (Prometheus + Grafana). |
| `aq deploy env` | `aq deploy env [--output VALUE] [--force] [--dry-run]` | Generate .env.example template with all Aquilia settings. |
| `aq deploy all` | `aq deploy all [--output VALUE] [--monitoring VALUE] [--ci-provider VALUE] [--force] [--dry-run]` | Generate ALL deployment files at once. |
| `aq deploy makefile` | `aq deploy makefile [--output VALUE] [--force] [--dry-run]` | Generate a self-documenting Makefile for dev & ops tasks. |
| `aq deploy render` | `aq deploy render [--image VALUE] [--region VALUE] [--plan VALUE] [--num-instances VALUE] [--service-name VALUE] [--destroy] [--status] [--force] [--dry-run]` | Deploy to Render PaaS with a single command. |
| `aq provider render env list` | `aq provider render env list [--service VALUE]` | List all environment variables for a Render service. |
| `aq provider render env set` | `aq provider render env set NAME [VALUE] [--service VALUE]` | Create or update an environment variable on a Render service. |
| `aq provider render env delete` | `aq provider render env delete NAME [--service VALUE]` | Delete an environment variable from a Render service. |
| `aq provider login` | `aq provider login PROVIDER_NAME [--token VALUE] [--region VALUE]` | Login to a cloud provider. |
| `aq provider logout` | `aq provider logout PROVIDER_NAME` | Logout from a cloud provider. |
| `aq provider status` | `aq provider status PROVIDER_NAME` | Show cloud provider authentication status. |

## Detailed Commands

### `aq deploy dockerfile`

Generate production-ready Dockerfiles.

```bash
aq deploy dockerfile [--dev] [--mlops] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `dev_mode` | `--dev` | False | `False` | Generate development Dockerfile (with hot-reload) |
| Option | `mlops_mode` | `--mlops` | False | `False` | Generate MLOps model-serving Dockerfile |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy compose`

Generate docker-compose.yml for the workspace.

```bash
aq deploy compose [--dev] [--monitoring] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `dev_mode` | `--dev` | False | `False` | Also generate docker-compose.dev.yml |
| Option | `monitoring` | `--monitoring` | False | `False` | Include Prometheus + Grafana services |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy kubernetes`

Generate production Kubernetes manifests.

```bash
aq deploy kubernetes [--output VALUE] [--mlops] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `k8s` | Output directory |
| Option | `mlops` | `--mlops` | False | `False` | Force include MLOps manifests |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy nginx`

Generate Nginx reverse-proxy configuration.

```bash
aq deploy nginx [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `deploy/nginx` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy ci`

Generate CI/CD pipeline configuration.

```bash
aq deploy ci [--provider VALUE] [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `provider` | `--provider` | False | `github` | CI provider |
| Option | `output` | `--output, -o` | False | `` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy monitoring`

Generate monitoring configuration (Prometheus + Grafana).

```bash
aq deploy monitoring [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `deploy` | Output base directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy env`

Generate .env.example template with all Aquilia settings.

```bash
aq deploy env [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy all`

Generate ALL deployment files at once.

```bash
aq deploy all [--output VALUE] [--monitoring VALUE] [--ci-provider VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` | Output base directory |
| Option | `monitoring` | `--monitoring` | False | `True` | Include monitoring (default: yes) |
| Option | `ci_provider` | `--ci-provider` | False | `github` | CI/CD provider |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy makefile`

Generate a self-documenting Makefile for dev & ops tasks.

```bash
aq deploy makefile [--output VALUE] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `output` | `--output, -o` | False | `.` | Output directory |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq deploy render`

Deploy to Render PaaS with a single command.

```bash
aq deploy render [--image VALUE] [--region VALUE] [--plan VALUE] [--num-instances VALUE] [--service-name VALUE] [--destroy] [--status] [--force] [--dry-run]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `image` | `--image, -i` | False | `` | Docker image to deploy (e.g. registry/myapp:latest) |
| Option | `region` | `--region, -r` | False | `` | Deployment region (oregon, frankfurt, ohio, virginia, singapore) |
| Option | `plan` | `--plan` | False | `` | Render plan |
| Option | `num_instances` | `--num-instances` | False | `` | Number of instances |
| Option | `service_name` | `--service-name` | False | `` | Render service name (default: workspace name) |
| Option | `destroy` | `--destroy` | False | `False` | Destroy the deployed service |
| Option | `show_status` | `--status` | False | `False` | Show deployment status |
| Option | `force` | `--force, -f` | False | `False` | Overwrite existing files |
| Option | `dry_run` | `--dry-run` | False | `False` | Preview without writing files |

### `aq provider render env list`

List all environment variables for a Render service.

```bash
aq provider render env list [--service VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `service` | `--service, -s` | True | `not set` | Render service name |

### `aq provider render env set`

Create or update an environment variable on a Render service.

```bash
aq provider render env set NAME [VALUE] [--service VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Argument | `value` | `value` | False | `not set` |  |
| Option | `service` | `--service, -s` | True | `not set` | Render service name |

### `aq provider render env delete`

Delete an environment variable from a Render service.

```bash
aq provider render env delete NAME [--service VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `name` | `name` | True | `not set` |  |
| Option | `service` | `--service, -s` | True | `not set` | Render service name |

### `aq provider login`

Login to a cloud provider.

```bash
aq provider login PROVIDER_NAME [--token VALUE] [--region VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |  |
| Option | `token` | `--token, -t` | False | `` | API token (reads from stdin if omitted) |
| Option | `region` | `--region, -r` | False | `oregon` | Default deployment region |

### `aq provider logout`

Logout from a cloud provider.

```bash
aq provider logout PROVIDER_NAME
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |  |

### `aq provider status`

Show cloud provider authentication status.

```bash
aq provider status PROVIDER_NAME
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `provider_name` | `provider_name` | True | `not set` |  |

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
