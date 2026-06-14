# Cloud Deployment

Aquilia provides native integration with **Render**, a zero-config Docker-based cloud platform. The `aq provider` and `aq deploy render` commands handle authentication, environment management, and one-command deployments.

## Render Provider

Render is a Platform-as-a-Service that runs Docker containers with automatic HTTPS, managed databases, and zero-downtime deploys.

### Supported Features

- **One-command deploy**: `aq deploy render` builds, pushes, and deploys
- **Credential management**: Encrypted token storage with AES-256-GCM + HMAC-SHA256
- **Environment variables**: Set, list, and delete via CLI
- **Service status**: View deployment state, URLs, and health
- **Service lifecycle**: Create, update, suspend, and destroy services
- **Multi-region**: Oregon, Frankfurt, Ohio, Virginia, Singapore
- **Plan selection**: Free, Starter, Standard, Pro, Pro Plus

## Authentication

### Login

```bash
# Interactive login (prompts for API key)
aq provider login render

# With token
aq provider login render --token rnd_your_api_key_here

# Pipe token from stdin
echo $RENDER_TOKEN | aq provider login render --token -

# Specify default region
aq provider login render --region frankfurt
```

Get your Render API key from: [dashboard.render.com/account/settings#api-keys](https://dashboard.render.com/account/settings#api-keys)

The token is encrypted with a machine-derived key and signed with HMAC-SHA256. Tokens are never stored in plain text or logged.

### Credential Status

```bash
aq provider status render
```

Output:

```
Render · Status
Provider authentication & connectivity

── Credentials ──
  Configured:  yes
  Path:        ~/.aquilia/render/credentials.surp
  Workspace:   My Workspace
  Region:      oregon
  Stored at:   2026-06-14 10:30:00

── Connectivity ──
  [ok] Connected to Render API

── Services (3) ──
  ● live    my-api
  ● live    my-worker
  ● deploying  my-backend
```

### Logout

```bash
aq provider logout render
```

This securely deletes stored credentials by overwriting with random data before unlinking.

## Managing Environment Variables

Render env vars are set directly on services:

```bash
# List all env vars for a service
aq provider render env list --service my-api

# Set a variable
aq provider render env set DATABASE_URL "postgres://user:pass@host/db" --service my-api

# Set a secret (prompts for value)
aq provider render env set API_KEY --service my-api

# Delete a variable
aq provider render env delete MY_VAR --service my-api
```

## Deploy to Render

### One-Command Deploy

```bash
# Interactive deploy (prompts for options)
aq deploy render

# Deploy specific image
aq deploy render --image ghcr.io/myorg/myapp:v1.2.3

# Deploy to specific region with plan
aq deploy render --region frankfurt --plan pro --num-instances 3

# Preview without deploying
aq deploy render --dry-run

# Check deployment status
aq deploy render --status

# Tear down service
aq deploy render --destroy
```

### Deployment Pipeline

The `aq deploy render` command orchestrates the full pipeline:

1. **Authenticate** — reads stored Render credentials
2. **Introspect** — scans your workspace for modules, services, and configuration
3. **Configure** — builds a `RenderDeployConfig` from workspace context
4. **Build & Push** — builds the Docker image and pushes to the registry
5. **Create/Update** — creates or updates the Render service
6. **Sync Env Vars** — uploads env vars (with auto-generated secrets for sensitive fields)
7. **Wait for Live** — polls until the deployment is live

### Interactive Deployment

When running `aq deploy render` interactively, you'll be prompted for:

```
Docker image:                    docker.io/myapp:latest
Deployment region:
  > oregon (US West)
    frankfurt (EU)
    ohio (US East)
    virginia (US East)
    singapore (Asia)

Render plan:
    free (shared CPU, 512MB RAM)
  > starter (0.5 CPU, 512MB RAM)
    standard (1 CPU, 2GB RAM)
    pro (2 CPU, 4GB RAM)
    pro_plus (4 CPU, 8GB RAM)

Number of instances:             1
```

### Deployment Plans

| Plan | CPU | RAM | Best for |
|------|-----|-----|----------|
| **Free** | Shared | 512 MB | Hobby projects, demos |
| **Starter** | 0.5 | 512 MB | Small APIs, prototypes |
| **Standard** | 1 | 2 GB | Production APIs |
| **Pro** | 2 | 4 GB | High-traffic services |
| **Pro Plus** | 4 | 8 GB | Compute-heavy workloads |

### Deployment Regions

| Region | Location | Code |
|--------|----------|------|
| Oregon | US West | `oregon` |
| Frankfurt | EU Central | `frankfurt` |
| Ohio | US East | `ohio` |
| Virginia | US East | `virginia` |
| Singapore | Asia Pacific | `singapore` |

### Deployment Configuration Detail

Before deploying, you'll see a summary:

```
Deployment Configuration
─────────────────────────
  Service:       myapp
  Image:         docker.io/myapp:latest
  Region:        frankfurt
  Plan:          pro
  Instances:     3
  Port:          8000
  Health check:  /health
  Env vars:      12

── Auto-generated secrets (3) ──
  SECRET_KEY     auto-generated
  JWT_SECRET     auto-generated
  API_KEY        auto-generated
```

### Status Check

```bash
aq deploy render --status
```

Shows the service status, latest deployment info, and live URL:

```
Render · myapp
Deployment status

── Service ──
  Status:      ● live
  Service ID:  srv-abc123
  Plan:        pro
  Region:      frankfurt
  URL:         https://myapp.onrender.com

── Latest Deploy ──
  Deploy ID:   dep-xyz789
  Status:      ● live
  Created:     2026-06-14 12:00:00 UTC
```

### Destroy a Service

```bash
aq deploy render --destroy
```

!!! danger "This is irreversible"
    Destroy removes the service and all its deploy history from Render.

## Environment Variables on Render

The `RenderDeployer` automatically syncs environment variables from your workspace configuration. Variables marked with `generate_value: yes` get auto-generated values (random hex strings).

### Manual Env Var Management

```bash
# List
aq provider render env list --service myapp

# Set
aq provider render env set DATABASE_URL "postgres://..." --service myapp
aq provider render env set API_KEY --service myapp  # Prompts for value

# Delete
aq provider render env delete DEPRECATED_VAR --service myapp
```

### Typical Environment Variables

| Variable | Value | Source |
|----------|-------|--------|
| `AQUILIA_ENV` | `prod` | Auto-set |
| `SECRET_KEY` | Random 64-char hex | Auto-generated |
| `DATABASE_URL` | Full connection string | Config or manual |
| `REDIS_URL` | Redis connection string | Config or manual |
| `CORS_ORIGINS` | Comma-separated list | Config |
| `LOG_LEVEL` | `info` | Config |

## Full Deployment Workflow

A typical deployment workflow:

```bash
# 1. One-time setup
aq provider login render

# 2. Generate deployment files (optional)
aq deploy all

# 3. Build and push Docker image
docker build -t myapp:latest .
docker tag myapp:latest ghcr.io/myorg/myapp:v1.2.0
docker push ghcr.io/myorg/myapp:v1.2.0

# 4. Deploy to Render
aq deploy render --image ghcr.io/myorg/myapp:v1.2.0 --region oregon --plan standard

# 5. Set environment variables
aq provider render env set DATABASE_URL "postgres://..." --service myapp
aq provider render env set REDIS_URL "redis://..." --service myapp

# 6. Verify deployment
aq deploy render --status

# 7. Check live URL
curl https://myapp.onrender.com/health
```

## Credential Storage

Credentials are stored using the Aquilia **Surp binary format**:

- **Encryption**: AES-256-GCM with a machine-derived key
- **Integrity**: HMAC-SHA256 signature for tamper detection
- **Location**: `~/.aquilia/render/credentials.surp`
- **Secure deletion**: Overwritten with random data before unlinking

## Troubleshooting

### "Not authenticated"

```bash
aq provider login render
```

### "Could not decrypt credentials"

The machine key has changed. Re-authenticate:

```bash
aq provider login render
```

### "Service not found"

The service hasn't been deployed yet or the name doesn't match:

```bash
aq deploy render status --service-name my-correct-name
```

### "Deployment failed"

Check the error messages and:

1. Verify `docker build .` succeeds locally
2. Verify the Docker image is pushed and accessible
3. Check the Render dashboard for specific errors
4. Ensure required env vars are set

### "Image not found"

Make sure the image is pushed to a registry Render can access:

```bash
# Push to Docker Hub
docker tag myapp:latest docker.io/username/myapp:latest
docker push docker.io/username/myapp:latest

# Or use GitHub Container Registry
docker tag myapp:latest ghcr.io/username/myapp:latest
docker push ghcr.io/username/myapp:latest
```

## Best Practices

1. **Authenticate first** — `aq provider login render` before any Render commands.
2. **Use specific image tags** — prefer `v1.2.0` over `latest` for reproducible deployments.
3. **Let Aquilia generate secrets** — variables marked `generate_value: yes` get strong random values.
4. **Set env vars after deploy** — use `aq provider render env set` to configure services.
5. **Check status** — use `aq deploy render --status` to monitor deployments.
6. **Use health checks** — Render auto-monitors your `/health` endpoint.
7. **Choose regions close to users** — minimizes latency.
8. **Start with `starter` plan** — upgrade later when you know your resource needs.
9. **Never commit credentials** — the CLI encrypts tokens; `.surp` files are gitignored by default.
10. **Use non-interactive mode in CI** — `aq deploy render --image IMAGE -y` for automated pipelines.