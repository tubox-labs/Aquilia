# aq mail

Test, inspect, and validate Aquilia's mail configuration. Supports sending test emails to verify provider setup.

## Usage

```bash
aq mail <SUBCOMMAND> [OPTIONS]
```

## Subcommands

### aq mail check

Validate mail configuration and report issues.

```bash
aq mail check
```

Reports:

- Enablement status
- Default sender address
- Subject prefix
- Console backend status
- Configured providers with type and enabled state
- Security settings (DKIM, TLS requirement, PII redaction)

Warns about:

- Default sender set to `noreply@localhost`
- No providers and console backend disabled

### aq mail send-test

Send a test email to verify provider configuration.

```bash
aq mail send-test <TO> [OPTIONS]
```

| Option      | Description        | Default                   |
| ----------- | ------------------ | ------------------------- |
| `--subject` | Email subject      | `Aquilia Mail Test`       |
| `--body`    | Email body         | Auto-generated test body  |

```bash
aq mail send-test user@example.com
aq mail send-test admin@site.com --subject="Deploy Notification"
aq mail send-test test@example.com --body="Custom test body"
```

### aq mail inspect

Display current mail configuration as JSON.

```bash
aq mail inspect
```

## Examples

```bash
aq mail check
aq mail send-test user@example.com
aq mail send-test admin@site.com --subject="Hello" --body="Testing mail config"
aq mail inspect
```

## See Also

- [Mail Integration](/reference/modules/mail/index/) — Mail module API reference
- [Configuration: Mail](/reference/configuration/index/) — Mail configuration options