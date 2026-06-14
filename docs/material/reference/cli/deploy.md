# aq deploy

Generate and execute production deployment files. Includes an interactive wizard and individual sub-command generators for each deployment artifact. Introspects the live workspace to tailor output.

## Usage

```bash
aq deploy [SUBCOMMAND] [OPTIONS]
```

Running `aq deploy` without a subcommand launches an **interactive wizard**.

## Global Options

| Option      | Alias | Description                                   | Default |
| ----------- | ----- | --------------------------------------------- | ------- |
| `--force`   | `-f`  | Overwrite existing files                      | `False` |
| `--dry-run` |       | Preview without writing files                 | `False` |
| `--yes`     | `-y`  | Skip interactive prompts, use all defaults    | `False` |

## Interactive Wizard

Steps:

1. **Workspace detection** — introspects live workspace for modules, DB driver, cache, WebSocket support
2. **Select artifacts** — choose from Dockerfile, Compose, Kubernetes, Nginx, CI/CD, Monitoring, .env, Makefile
3. **Configure options** — CI provider, dev Dockerfile, monitoring inclusion, output directory
4. **Execution options** — optionally build, deploy, and audit after generation
5. **Review & confirm**
6. **Generate files**
7. **Execute deployment** (if selected)

## Subcommands

### `aq deploy dockerfile`

Generate production-ready multi-stage Dockerfiles.

```bash
aq deploy dockerfile [OPTIONS]
```

| Option     | Alias | Description                                       | Default |
| ---------- | ----- | ------------------------------------------------- | ------- |
| `--dev`    |       | Also generate `Dockerfile.dev` with hot-reload    | `False` |
| `--output` | `-o`  | Output directory                                  | `.`     |

Generates:

- `Dockerfile` — multi-stage build with non-root user, tini init, BuildKit cache
- `.dockerignore` — optimized build context
- `Dockerfile.dev` — development variant with hot-reload (with `--dev`)

```bash
aq deploy dockerfile
aq deploy dockerfile --dev
aq deploy -f dockerfile   # Force overwrite
```

### `aq deploy compose`

Generate `docker-compose.yml` with auto-detected services.

```bash
aq deploy compose [OPTIONS]
```

| Option          | Description                                          | Default |
| --------------- | ---------------------------------------------------- | ------- |
| `--monitoring`  | Include Prometheus + Grafana services                | `False` |
| `--dev`         | Also generate `docker-compose.dev.yml`               | `False` |
| `--output`      | `-o` Output directory                                 | `.`     |

Auto-detects and configures services for PostgreSQL, MySQL, Redis, Nginx, monitoring, and mail based on workspace configuration. Uses Docker Compose profiles for optional services.

```bash
aq deploy compose
aq deploy compose --monitoring
aq deploy compose --dev
```

### `aq deploy kubernetes`

Generate full Kubernetes manifest suite.

```bash
aq deploy kubernetes [OPTIONS]
```

| Option     | Alias | Description         | Default |
| ---------- | ----- | ------------------- | ------- |
| `--output` | `-o`  | Output directory    | `k8s`   |

Generates:

- `namespace.yaml`
- `deployment.yaml`
- `service.yaml`
- `ingress.yaml`
- `hpa.yaml` (HorizontalPodAutoscaler)
- `pdb.yaml` (PodDisruptionBudget)
- `network-policy.yaml`
- `configmap.yaml`
- `secret.yaml`
- `service-account.yaml`
- `pvc.yaml` (PersistentVolumeClaim)
- `cronjob-maintenance.yaml`
- `kustomization.yaml`

```bash
aq deploy kubernetes
aq deploy kubernetes -o deploy/k8s
```

### `aq deploy nginx`

Generate Nginx reverse-proxy configuration.

```bash
aq deploy nginx [OPTIONS]
```

| Option     | Alias | Description                | Default        |
| ---------- | ----- | -------------------------- | -------------- |
| `--output` | `-o`  | Output directory           | `deploy/nginx` |

Includes:

- Rate limiting configuration
- Security headers (HSTS, CSP, XSS protection)
- Gzip compression
- WebSocket upgrade support
- Upstream keepalive
- HTTPS block with modern TLS configuration (commented)
- SSL certificate directory placeholder

```bash
aq deploy nginx
aq deploy nginx -o config/nginx
```

### `aq deploy ci`

Generate CI/CD pipeline configuration.

```bash
aq deploy ci [OPTIONS]
```

| Option       | Description                       | Default   |
| ------------ | --------------------------------- | --------- |
| `--provider` | CI provider: `github` or `gitlab` | `github`  |
| `--output`   | `-o` Output directory              | auto      |

Generates workflows with stages:

- **Lint** — ruff check
- **Test** — pytest with coverage
- **Security** — Trivy container scan, dependency audit
- **Build** — Docker image build
- **Deploy** — deployment step
- **Aquilia-specific** — manifest validation, artifact verification

```bash
aq deploy ci
aq deploy ci --provider=github
aq deploy ci --provider=gitlab
```

### `aq deploy monitoring`

Generate Prometheus and Grafana provisioning.

```bash
aq deploy monitoring [OPTIONS]
```

| Option     | Alias | Description                | Default  |
| ---------- | ----- | -------------------------- | -------- |
| `--output` | `-o`  | Output base directory      | `deploy` |

Generates:

- `prometheus/prometheus.yml` — scrape configuration auto-configured from detected modules
- `grafana/provisioning/datasources/datasource.yml` — Prometheus datasource
- `grafana/provisioning/dashboards/dashboards.yml` — dashboard provisioning

```bash
aq deploy monitoring
aq deploy monitoring -o infra/
```

### `aq deploy env`

Generate `.env.example` template with all Aquilia settings.

```bash
aq deploy env [OPTIONS]
```

| Option     | Alias | Description          | Default |
| ---------- | ----- | -------------------- | ------- |
| `--output` | `-o`  | Output directory     | `.`     |

Scans workspace for enabled components and generates comprehensive template including:

- Database URL (db-driver-aware default)
- Telemetry/OTel configuration
- CORS settings
- Monitoring endpoints
- Mail configuration
- Session secrets

```bash
aq deploy env
aq deploy env --force
```

### `aq deploy makefile`

Generate a `Makefile` with dev, build, and deploy targets.

```bash
aq deploy makefile [OPTIONS]
```

| Option     | Alias | Description          | Default |
| ---------- | ----- | -------------------- | ------- |
| `--output` | `-o`  | Output directory     | `.`     |

### `aq deploy all`

Generate **all** deployment files at once.

```bash
aq deploy all [OPTIONS]
```

| Option           | Description                                      | Default   |
| ---------------- | ------------------------------------------------ | --------- |
| `--output`       | `-o` Output base directory                        | `.`       |
| `--monitoring`   | Include monitoring (default: yes)                 | `True`    |
| `--ci-provider`  | CI/CD provider: `github`, `gitlab`, or `both`     | `github`  |

```bash
aq deploy all
aq deploy all -o deploy/
aq deploy all --ci-provider=both --force
aq deploy all --dry-run
```

### `aq deploy render`

Deploy to Render PaaS in one command.

```bash
aq deploy render [OPTIONS]
```

Requires prior authentication via [`aq provider login render`](provider.md).

## Execution Actions

When using the interactive wizard, you can optionally execute deployment actions after generation:

| Action           | Command                          |
| ---------------- | -------------------------------- |
| `docker-build`   | `docker build -t <name>:latest .`|
| `compose-up`     | `docker compose up -d`           |
| `k8s-apply`      | `kubectl apply -k k8s/`         |
| `monitoring-up`  | `docker compose --profile monitoring up -d` |
| `compose-audit`  | `docker compose ps`              |

## Examples

```bash
# Interactive deploy wizard
aq deploy

# Non-interactive, generate everything
aq deploy -y

# Preview all changes
aq deploy --dry-run

# Generate specific artifacts
aq deploy dockerfile --dev
aq deploy compose --monitoring
aq deploy kubernetes -o deploy/k8s
aq deploy nginx
aq deploy ci --provider=github
aq deploy monitoring -o infra/
aq deploy env --force
aq deploy all -o deploy/ --ci-provider=both

# Force overwrite existing files
aq deploy all -f
```

## See Also

- [`aq provider`](provider.md) — Cloud provider authentication
- [`aq serve`](serve.md) — Start the production server