# aq provider

Manage cloud provider authentication and configuration. Currently supports **Render** PaaS for Docker-based cloud hosting.

## Usage

```bash
aq provider <COMMAND> [OPTIONS]
```

## Commands

### aq provider login

Authenticate with a cloud provider. Stores API tokens securely using Surp-encrypted storage with AES-256-GCM encryption and HMAC-SHA256 integrity protection.

```bash
aq provider login <PROVIDER> [OPTIONS]
```

| Argument    | Description                       | Choices     |
| ----------- | --------------------------------- | ----------- |
| `PROVIDER`  | Provider name                     | `render`    |

| Option      | Alias | Description                                      | Default  |
| ----------- | ----- | ------------------------------------------------ | -------- |
| `--token`   | `-t`  | API token (reads from stdin if omitted/PIPE)     | prompts  |
| `--region`  | `-r`  | Default deployment region                        | `oregon` |

```bash
# Interactive login
aq provider login render

# With explicit token
aq provider login render --token rnd_xxxxx

# Read token from pipe
echo $RENDER_TOKEN | aq provider login render --token -

# Custom region
aq provider login render --region frankfurt
```

The login process:

1. Validates the API token against Render's API
2. Retrieves account owner information
3. Encrypts and stores credentials locally

### aq provider logout

Securely remove stored credentials.

```bash
aq provider logout <PROVIDER>
```

Credentials are overwritten with random data before deletion for secure erasure.

```bash
aq provider logout render
```

### aq provider status

Show cloud provider authentication status and connectivity.

```bash
aq provider status <PROVIDER>
```

Displays:

- Credential configuration status
- Stored workspace and region
- Connectivity check to provider API
- List of deployed services with status indicators

Service status indicators:

- `● live` / `● deployed` — running (green)
- `● deploying` / `● building` — in progress (cyan)
- `● failed` / `● error` — failure (red)
- `○ <other>` — unknown state (yellow)

```bash
aq provider status render
```

### aq provider render env

Manage environment variables on Render services.

```bash
aq provider render env <SUBCOMMAND> [OPTIONS]
```

#### aq provider render env list

List environment variables for a service.

```bash
aq provider render env list --service <SERVICE_NAME>
```

#### aq provider render env set

Create or update an environment variable.

```bash
aq provider render env set <NAME> [VALUE] --service <SERVICE_NAME>
```

If `VALUE` is omitted, you will be prompted securely.

```bash
aq provider render env set DATABASE_URL "postgres://..." --service my-api
aq provider render env set API_KEY --service my-api
```

#### aq provider render env delete

Delete an environment variable.

```bash
aq provider render env delete <NAME> --service <SERVICE_NAME>
```

```bash
aq provider render env delete MY_VAR --service my-api
```

## Credential Storage

Credentials are stored using the **Surp binary format** with:

- **Encryption**: AES-256-GCM with machine-derived keys
- **Integrity**: HMAC-SHA256 tamper detection
- **Location**: `~/.aquilia/providers/render/credentials.surp`

!!! danger "Security"
    API tokens are **never** stored in plain text, logged to console output, or committed to version control. Tokens are encrypted before any disk write.

## Examples

```bash
# Full Render workflow
aq provider login render
aq provider status render
aq provider render env list --service my-api
aq provider render env set DATABASE_URL "postgres://..." --service my-api
aq provider render env delete OLD_VAR --service my-api
aq provider logout render
```

## See Also

- [`aq deploy render`](deploy.md) — Deploy to Render in one command