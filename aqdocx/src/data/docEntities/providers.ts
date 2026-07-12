import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'provider.RenderIntegration',
    type: 'class',
    title: 'RenderIntegration',
    description: 'Typed Render deployment configuration for workspace.py. Defines region, compute plan, instance count, custom health check paths, and private registry credentials.',
    signature: 'class RenderIntegration:\n    service_name: str | None = None\n    region: str = "oregon"\n    plan: str = "starter"\n    num_instances: int = 1\n    image: str | None = None\n    health_path: str = "/_health"\n    auto_deploy: str = "no"\n    registry_credential_id: str | None = None\n    enabled: bool = True',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/providers/render',
    source: { file: 'aquilia/integrations/render.py', line: 12 }
  },
  {
    id: 'provider.RenderClient',
    type: 'class',
    title: 'RenderClient',
    description: 'Synchronous REST client for the Render API v1. Integrates retry with exponential backoff and rate-limit awareness using only standard library urllib. Covers services, deploys, env vars, Postgres, Key-Value (Redis), projects, custom domains, log streams, and metrics.',
    signature: 'class RenderClient:\n    def __init__(self, token: str, *, base_url: str = "https://api.render.com", timeout: int = 30, max_retries: int = 3)\n    def validate_token(self) -> bool\n    def list_services(self, **filters) -> list[RenderService]\n    def create_service(self, payload: dict) -> RenderService\n    def update_service(self, service_id: str, payload: dict) -> RenderService\n    def trigger_deploy(self, service_id: str, *, clear_cache: str = "do_not_clear") -> RenderDeploy\n    def get_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy',
    language: 'python',
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/providers/render',
    source: { file: 'aquilia/providers/render/client.py', line: 141 }
  },
  {
    id: 'provider.RenderDeployer',
    type: 'class',
    title: 'RenderDeployer',
    description: 'Full-lifecycle Render deployment orchestrator. Builds production Docker images, pushes them to remote registries, syncs env vars and secret files, configures autoscaling and HTTP headers, triggers deploys, polls until live, and generates rollbacks upon failure.',
    signature: 'class RenderDeployer:\n    def __init__(self, client: RenderClient, workspace_root: Path, config: RenderDeployConfig, *, on_step: Callable | None = None, dry_run: bool = False)\n    def deploy(self) -> DeployResult',
    language: 'python',
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/providers/render',
    source: { file: 'aquilia/providers/render/deployer.py', line: 91 }
  },
  {
    id: 'provider.RenderCredentialStore',
    type: 'class',
    title: 'RenderCredentialStore',
    description: 'Military-grade credential store for local developer environments. Persists API tokens in credentials.surp, encrypting payload with AES-256-GCM and signing with HMAC-SHA512 based on machine-derived platform key derivation (PBKDF2-HMAC-SHA512). Prevents replays, truncation, and downgrade attacks.',
    signature: 'class RenderCredentialStore:\n    def __init__(self, directory: Path | None = None)\n    def save(self, token: str, owner_name: str, default_region: str, metadata: dict | None = None) -> None\n    def load(self) -> str | None\n    def clear(self) -> None\n    def is_configured(self) -> bool\n    def status(self) -> dict',
    language: 'python',
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/providers/security',
    source: { file: 'aquilia/providers/render/store.py', line: 81 }
  },
  {
    id: 'provider.RenderDeployConfig',
    type: 'class',
    title: 'RenderDeployConfig',
    description: 'Dataclass representing the deployment options for a Render service. Maps workspace settings (port, worker count, DB/cache/auth modules) into a standard Render service configuration payload.',
    signature: 'class RenderDeployConfig(Contract):\n    service_name: str = ""\n    service_type: RenderServiceType = RenderServiceType.WEB_SERVICE\n    owner_id: str | None = None\n    image: str = ""\n    plan: RenderPlan = RenderPlan.STARTER\n    region: str = "oregon"\n    num_instances: int = 1\n    autoscaling: RenderAutoscaling = None\n    port: int = 8000\n    health_check_path: str = "/_health"\n    env_vars: list[RenderEnvVar] = None\n    disk: RenderDisk | None = None\n    headers: list[RenderHeaderRule] = None\n    redirect_rules: list[RenderRedirectRule] = None\n    registry_credential_id: str | None = None',
    language: 'python',
    status: 'stable',
    version: 'v2.0+',
    docsHref: '/docs/providers/render',
    source: { file: 'aquilia/providers/render/types.py', line: 1046 }
  },
  {
    id: 'cli.deploy_render',
    type: 'cli',
    title: 'aq deploy render',
    description: 'Compiles the project, validates workspace configurations (using aq doctor and aq validate), builds the Docker production image, pushes it to the registry, configures environment vars, custom headers, and deploys it to Render.',
    signature: 'aq deploy render [--image VALUE] [--region VALUE] [--plan VALUE] [--num-instances VALUE] [--service-name VALUE] [--destroy] [--status] [--force] [--dry-run]',
    language: 'bash',
    parameters: [
      { name: '--image, -i', type: 'option', description: 'Docker image path (registry/name:tag) to deploy.' },
      { name: '--region, -r', type: 'option', description: 'Deployment region (e.g. frankfurt, oregon, singapore).' },
      { name: '--plan', type: 'option', description: 'Compute plan (free, starter, standard, pro, pro_plus).' },
      { name: '--num-instances', type: 'option', description: 'Explicit number of container instances.' },
      { name: '--service-name', type: 'option', description: 'Service name override in Render.' },
      { name: '--destroy', type: 'option', description: 'Tear down the deployed service and resources.' },
      { name: '--status', type: 'option', description: 'Query and print the status of the current deployment.' },
      { name: '--dry-run', type: 'option', description: 'Synthesize config and payload without mutating resources or registry.' }
    ],
    example: {
      code: 'aq deploy render --region frankfurt --plan pro --num-instances 3',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/providers/cli'
  },
  {
    id: 'cli.provider_login_render',
    type: 'cli',
    title: 'aq provider login render',
    description: 'Authenticates with the Render API, verifies the bearer token by checking account owners, and saves the credentials securely.',
    signature: 'aq provider login render [--token VALUE] [--region VALUE]',
    language: 'bash',
    parameters: [
      { name: '--token, -t', type: 'option', description: 'API token (omitting prompts for stdin/password input).' },
      { name: '--region, -r', type: 'option', description: 'Default region to initialize for workspace (default: oregon).' }
    ],
    example: {
      code: 'aq provider login render --token rnd_xxxxxx',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/providers/cli'
  },
  {
    id: 'cli.provider_status_render',
    type: 'cli',
    title: 'aq provider status render',
    description: 'Reads local credentials, verifies decryption integrity, tests connection to the Render API endpoint, and displays account ownership details.',
    signature: 'aq provider status render',
    language: 'bash',
    example: {
      code: 'aq provider status render',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/providers/cli'
  },
  {
    id: 'cli.provider_logout_render',
    type: 'cli',
    title: 'aq provider logout render',
    description: 'Securely logs out of Render. Overwrites the credentials file (credentials.surp) with random data before unlinking to prevent data recovery.',
    signature: 'aq provider logout render',
    language: 'bash',
    example: {
      code: 'aq provider logout render',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/providers/cli'
  },
  {
    id: 'cli.provider_render_env_set',
    type: 'cli',
    title: 'aq provider render env set',
    description: 'Sets or updates environment variables in a Render service directly from the terminal.',
    signature: 'aq provider render env set KEY VALUE --service SERVICE_NAME',
    language: 'bash',
    parameters: [
      { name: 'KEY', type: 'argument', description: 'The environment variable key.' },
      { name: 'VALUE', type: 'argument', description: 'The environment variable value.' },
      { name: '--service, -s', type: 'option', description: 'Render service name to modify.' }
    ],
    example: {
      code: 'aq provider render env set DATABASE_URL "postgresql://..." --service my-app',
      language: 'bash'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/providers/cli'
  }
])
