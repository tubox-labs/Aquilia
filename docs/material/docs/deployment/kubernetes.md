# Kubernetes Deployment

Aquilia generates complete, production-ready Kubernetes manifests via `aq deploy kubernetes`. The `KubernetesGenerator` introspects your workspace and produces a full suite of K8s resources, orchestrated with Kustomize.

## Quick Start

```bash
# Generate all Kubernetes manifests
aq deploy kubernetes

# Custom output directory
aq deploy kubernetes -o deploy/k8s

# Preview without writing files
aq deploy kubernetes --dry-run

# Force overwrite existing manifests
aq deploy kubernetes --force

# Apply to cluster
kubectl apply -k k8s/

# Or with kustomize build
kustomize build k8s/ | kubectl apply -f -
```

This generates:

```
k8s/
├── namespace.yaml              # Namespace definition
├── deployment.yaml             # App deployment with init containers
├── service.yaml                # ClusterIP service
├── ingress.yaml                # Ingress with TLS
├── hpa.yaml                    # Horizontal Pod Autoscaler
├── pdb.yaml                    # Pod Disruption Budget
├── network-policy.yaml          # Network policy
├── configmap.yaml              # Application config
├── secret.yaml                 # Secrets (templates only)
├── serviceaccount.yaml         # Dedicated service account
├── pvc.yaml                    # Persistent Volume Claim
├── cronjob-migrations.yaml     # Scheduled maintenance
└── kustomization.yaml           # Kustomize orchestration
```

## Generated Resources

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: myapp
  labels:
    app.kubernetes.io/name: myapp
    app.kubernetes.io/managed-by: aquilia-cli
```

### Deployment

The deployment includes init containers for database readiness and pre-start checks:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: myapp
  labels:
    app.kubernetes.io/name: myapp
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      serviceAccountName: myapp-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      initContainers:
        - name: check-db-ready
          image: postgres:16-alpine
          command:
            - sh
            - -c
            - |
              until pg_isready -h $DATABASE_HOST -p $DATABASE_PORT -U $DATABASE_USER; do
                echo "Waiting for database..."
                sleep 2
              done
          envFrom:
            - secretRef:
                name: myapp-secrets
      containers:
        - name: app
          image: myapp:latest
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - configMapRef:
                name: myapp-config
            - secretRef:
                name: myapp-secrets
          env:
            - name: AQUILIA_ENV
              value: "prod"
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
            timeoutSeconds: 3
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 2
```

### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
  namespace: myapp
  labels:
    app.kubernetes.io/name: myapp
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
    - name: http
      port: 80
      targetPort: 8000
      protocol: TCP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  namespace: myapp
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - myapp.example.com
      secretName: myapp-tls
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 80
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp
  namespace: myapp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

### Pod Disruption Budget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp
  namespace: myapp
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: myapp
```

### Network Policy

Restricts ingress and egress traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: myapp
  namespace: myapp
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - port: 6379
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: myapp-config
  namespace: myapp
data:
  AQUILIA_ENV: "prod"
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  DATABASE_PORT: "5432"
  REDIS_HOST: "redis.default.svc.cluster.local"
  REDIS_PORT: "6379"
```

### Secret

!!! warning "Secrets are generated as templates"
    The generated `secret.yaml` contains placeholder values. **Replace all placeholders** before deploying:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: myapp-secrets
  namespace: myapp
type: Opaque
stringData:
  SECRET_KEY: "replace-with-real-secret"
  DATABASE_URL: "replace-with-real-database-url"
  REDIS_URL: "replace-with-real-redis-url"
```

For production, use an external secrets manager or vault:

```bash
# Using kubectl to create a secret from environment variables
kubectl create secret generic myapp-secrets \
  --namespace=myapp \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=DATABASE_URL=postgres://user:pass@host:5432/db \
  --from-literal=REDIS_URL=redis://:password@host:6379/0 \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: myapp
```

### Persistent Volume Claim

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myapp-data
  namespace: myapp
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

### CronJob (Maintenance)

For periodic maintenance tasks like database cleanup:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: myapp-maintenance
  namespace: myapp
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: myapp-sa
          containers:
            - name: maintenance
              image: myapp:latest
              command:
                - python
                - -m
                - aquilia.cli
                - migrate
          restartPolicy: OnFailure
```

## Health Probes

The deployment configures both **liveness** and **readiness** probes:

| Probe | Path | Purpose | Failure Action |
|-------|------|---------|---------------|
| **Liveness** | `/health` | Is the app running? | Restart container |
| **Readiness** | `/health` | Is the app ready to serve? | Remove from service |

Configure your health endpoint to differentiate between liveness and readiness:

```python
# In your controller
@GET("/health")
async def health(self, ctx: RequestCtx):
    # Liveness: just check the app is running
    # Readiness: check database, cache, etc.
    return Response.json({
        "status": "healthy",
        "checks": {
            "database": "ok",
            "cache": "ok",
        }
    })
```

## Kustomize Integration

The generated `kustomization.yaml` ties all resources together:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: myapp

labels:
  - pairs:
      app.kubernetes.io/name: myapp
      app.kubernetes.io/managed-by: aquilia-cli

resources:
  - configmap.yaml
  - cronjob-migrations.yaml
  - deployment.yaml
  - hpa.yaml
  - ingress.yaml
  - namespace.yaml
  - network-policy.yaml
  - pdb.yaml
  - pvc.yaml
  - secret.yaml
  - service.yaml
  - serviceaccount.yaml
```

Apply everything:

```bash
kubectl apply -k k8s/
```

### Environment-Specific Overlays

Create overlays for different environments:

```
k8s/
├── base/
│   ├── kustomization.yaml
│   └── ... (all resources)
└── overlays/
    ├── staging/
    │   ├── kustomization.yaml
    │   └── patches/
    └── production/
        ├── kustomization.yaml
        └── patches/
```

Example `overlays/production/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: myapp-production

resources:
  - ../../base

patches:
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: myapp
      spec:
        replicas: 5
    target:
      kind: Deployment

images:
  - name: myapp
    newTag: v1.1.2
```

## Full Deploy Workflow (Interactive)

The `aq deploy` interactive wizard handles the complete flow:

```bash
aq deploy
```

The wizard guides you through:

1. **Workspace introspection** — detects modules, database driver, cache, WebSockets
2. **Artefact selection** — choose which manifests to generate
3. **Configuration** — CI provider, dev mode options, monitoring
4. **Execution** — optionally build Docker image, run compose, apply K8s manifests
5. **Review & confirm** — review before generating
6. **Generate** — write all files
7. **Execute** — run deployment actions

Non-interactive deploy everything:

```bash
aq deploy -y                    # Generate and execute with defaults
aq deploy all                   # Generate all deployment files
aq deploy all --ci-provider=both --force  # Both CI providers, overwrite
```

## Best Practices

1. **Never commit secrets** — use sealed secrets or external secret stores.
2. **Set resource requests and limits** — prevents noisy neighbor issues.
3. **Configure PDBs** — ensures availability during voluntary disruptions.
4. **Use NetworkPolicies** — restrict pod-to-pod communication to the minimum.
5. **Pin image tags** — use specific tags (`v1.1.2`) rather than `latest` for reproducibility.
6. **Configure both liveness and readiness probes** — different semantics, different intervals.
7. **Use init containers for database readiness** — prevents crash loops during DB startup.
8. **Run as non-root** — the generated deployment sets `runAsNonRoot: true`.
9. **Set pod anti-affinity** — spread replicas across nodes for HA (add to the deployment manually).
10. **Use Kustomize overlays** — keep base clean and overlay environment differences.