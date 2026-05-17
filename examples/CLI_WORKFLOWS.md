# Aquilia CLI Workflow Examples

These examples use actual command groups, flags, and options from `aquilia/cli/__main__.py`.

## Workspace And Module Scaffolding

```bash
aq init workspace billing-api --minimal
cd billing-api
aq add module invoices --route-prefix=/invoices --fault-domain=INVOICES -y
aq generate controller Invoice --prefix=/invoices --resource=invoice
```

Expected behavior: `workspace.py` is created first, `modules/invoices/` is added next, and generated controllers must be registered through the module manifest.

## Development Loop

```bash
aq validate
aq discover
aq discover --sync --dry-run
aq run --mode=dev --port=8010
aq test --coverage
```

Use `aq validate --strict` in CI before build/deploy jobs.

## Production Runtime

```bash
aq compile --output=dist
aq freeze --output=dist --sign
aq serve --bind=0.0.0.0:8000 --workers=4 --use-gunicorn
```

`aq serve` uses uvicorn by default. `--use-gunicorn` enables Gunicorn with the Uvicorn worker.

## Inspection And Discovery

```bash
aq inspect routes
aq inspect di
aq inspect modules
aq inspect faults
aq inspect config
aq analytics
aq doctor --json
```

Use these commands after module changes to confirm the compiled runtime view.

## Database And Models

```bash
aq db makemigrations --app=projects
aq db migrate --plan
aq db migrate
aq db showmigrations
aq db sqlmigrate 0001_initial
aq db status
aq db dump --emit=sql
aq db inspectdb --table=users --output=models/generated.py
```

If `--database-url` is omitted, Aquilia attempts to detect it from `workspace.py`.

## Cache, Mail, I18n, And WebSockets

```bash
aq cache check
aq cache inspect
aq cache stats
aq cache clear --namespace=http

aq mail check
aq mail inspect
aq mail send-test ops@example.com --subject="Smoke" --body="Mail provider is configured"

aq i18n init --locales=en,fr,de
aq i18n extract --source-dirs modules,templates --output locales/en/messages.json
aq i18n coverage
aq i18n compile --directory locales --output artifacts/locales

aq ws inspect
aq ws gen-client --lang=ts --out=clients/chat.ts
aq ws broadcast --namespace=/chat --room=lobby --event=system.notice --payload='{"text":"deploy"}'
```

## Admin

```bash
aq admin check
aq admin setup
aq admin createsuperuser --username=admin --email=admin@example.com
aq admin listusers --active-only
```

Admin login requires sessions. `aq admin check` reports missing session, static, template, database, and local tooling requirements.

## Deployment Generators

```bash
aq deploy dockerfile --dev --dry-run
aq deploy compose --monitoring --force
aq deploy kubernetes --output=k8s
aq deploy ci --provider=github
aq deploy all --monitoring --ci-provider=github --force
aq deploy render --service-name=billing-api --status
```

Use `--dry-run` first when generating deployment files into an existing workspace.

## Artifacts

```bash
aq artifact list --dir=artifacts
aq artifact inspect catalog-routes --version=1.0.0
aq artifact verify-all --json-output
aq artifact export --output=bundle.aq.json --name=catalog-routes
aq artifact import bundle.aq.json
aq artifact stats
```

## Providers And Render

```bash
aq provider login render --token="$RENDER_API_KEY" --region=oregon
aq provider status render
aq provider render env list --service=billing-api
aq provider render env set AQ_ENV prod --service=billing-api
aq provider logout render
```

## MLOps

```bash
aq pack save model.pkl --name=fraud-detector --version=1.0.0 --framework=sklearn
aq pack inspect fraud-detector-1.0.0.aqmodel
aq pack verify fraud-detector-1.0.0.aqmodel --key="$MODEL_SIGNING_KEY"
aq model serve fraud-detector-1.0.0.aqmodel --runtime=python --port=9000
aq model health --url=http://localhost:9000
aq mlops-deploy rollout fraud-detector --from-version=1.0.0 --to-version=1.1.0 --strategy=canary
aq observe metrics --format=prometheus
aq lineage show --format=json
aq experiment create homepage-ranking --arm=control:v1:0.5 --arm=treatment:v2:0.5
```

Optional MLOps dependencies are required for runtime-specific model export or inference backends.
