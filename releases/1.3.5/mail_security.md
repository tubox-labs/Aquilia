# Mail Security, MIME & Templates — Aquilia v1.3.5

The mail subsystem's message construction, signing, logging, and templating were consolidated and hardened. MIME assembly now lives in one place shared by every provider, DKIM signing is real, log output redacts personal data on request, and the ATS template engine gained a documented filter set with autoescaping on by default.

---

## Shared MIME Assembly

Every provider previously built its own MIME message, which meant header handling, attachment encoding, and multipart structure drifted between SMTP, SES, SendGrid, and the file/console backends. `aquilia/mail/mime.py` is now the single implementation:

```python
from aquilia.mail import build_mime_message, message_to_bytes, sign_dkim

build_mime_message(envelope, *, extra_headers=None)   # -> MIMEMultipart
message_to_bytes(msg, security=None)                  # -> bytes, DKIM-signed if configured
sign_dkim(raw_message, security)                      # -> bytes
```

`build_mime_message()` produces a `multipart/mixed` message with a generated `Message-ID` and Aquilia tracking headers — `X-Aquilia-Envelope-ID`, plus trace and tenant IDs when set. Attachment payloads are read from envelope metadata, so an envelope reloaded on another worker still carries its attachments. The `extra_headers` argument is merged last, letting a provider add its own header (an ESP configuration set, for example) without forking the builder.

`extract_domain(email)` is also exported, used for per-domain rate limiting and DKIM domain defaulting.

### Why it matters

Bugs fixed in one provider now apply to all of them, and the `X-Aquilia-Envelope-ID` header is emitted consistently — which is what lets provider webhooks correlate a bounce back to the exact envelope. See [Bounce Handling & Suppression](bounces_suppression.md).

---

## DKIM Signing

DKIM signing is applied at the byte level, immediately before transmission, so the signature covers exactly what the provider receives.

```python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    dkim_enabled=True,
    dkim_domain="example.com",
    dkim_selector="aquilia",
)
```

| Option | Default | Purpose |
|---|---|---|
| `dkim_enabled` | `False` | Sign outbound mail |
| `dkim_domain` | `None` | Signing domain (`d=`). Required when enabled |
| `dkim_selector` | `"aquilia"` | Selector (`s=`); must match your DNS TXT record |
| `dkim_private_key_path` | `None` | Path to the PEM private key |
| `dkim_private_key_env` | `"AQUILIA_DKIM_PRIVATE_KEY"` | Environment variable holding the PEM key |

Signing requires the `dkimpy` package:

```bash
pip install aquilia[mail-dkim]
```

**DKIM failures raise at send time rather than shipping an unsigned message.** Silently sending unsigned mail would defeat the purpose — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or an error.

Because that failure is at send time, `aq mail check` now validates the configuration up front:

```
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
```

---

## TLS Enforcement

`require_tls` defaults to `True`. SMTP delivery negotiates STARTTLS and aborts rather than transmitting credentials or message content in cleartext. Disable only for a local development relay.

---

## XOAUTH2 Authentication

`MailAuth.oauth2()` supports SMTP providers that require bearer tokens (Gmail, Microsoft 365):

```python
Integration.mail(
    auth=MailAuth.oauth2(
        client_id="...",
        client_secret_env="MAIL_OAUTH_SECRET",
        access_token_env="MAIL_OAUTH_TOKEN",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://mail.google.com/",
    ),
    providers=[...],
)
```

Aquilia does not perform the token exchange. Supply a currently valid token — literally or through `access_token_env` — from whatever component owns the refresh cycle. `token_url`, `scope`, and `refresh_token` are recorded for that component's use. The token is presented to SMTP via the XOAUTH2 mechanism.

---

## PII Redaction in Logs

Mail logs contain recipient addresses by nature. `pii_redaction` masks them:

```python
Integration.mail(pii_redaction=True, ...)
```

```python
from aquilia.mail import redact_email, redact_pii

redact_email("alice@example.com")               # "a***e@example.com"
redact_pii("contact alice@example.com", enabled=True)
```

Local parts are masked while the domain is preserved, so logs remain useful for diagnosing a domain-wide delivery problem without recording individual identities. Off by default — enabling it reduces debuggability, which should be a deliberate choice.

---

## ATS Templates

The mail template engine (`<< expression >>` syntax, distinct from the Jinja engine used for HTML views) gained a documented public API and filter set.

```python
from aquilia.mail.template import configure, register_filter, render_string, render_template, FILTERS

configure(template_dirs=["mail_templates"])
render_string(template_text, context, *, autoescape=True)
render_template(template_name, context, *, template_dirs=None, autoescape=None)
register_filter(name, fn)
```

### Autoescaping

**Interpolated values are HTML-escaped by default.** A username containing `<script>` cannot inject markup into an HTML mail body.

```python
render_string("<p><< name >></p>", {"name": "<script>alert(1)</script>"})
# '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'
```

Two escape hatches:

- The `safe` filter, for a value that is known-good markup: `<< body|safe >>`
- `autoescape=False`, for plain-text bodies and subject headers, where escaping would corrupt output (`&amp;` in a subject line)

Subject rendering uses `autoescape=False` internally for exactly this reason.

### Built-in filters

`currency`, `default`, `escape`, `join`, `length`, `lower`, `safe`, `title`, `trim`, `truncate`, `upper`.

```
<< total|currency("EUR") >>        →  EUR 12.50
<< blurb|truncate(5) >>            →  abcde…
<< tags|join(", ") >>
<< nickname|default("friend") >>
<< name|trim|title >>
```

Filters compose left to right. Arguments must be literals — no expressions — so a template cannot execute arbitrary code.

Register your own:

```python
register_filter("shout", lambda v: f"{v}!!!")
```

### Control flow is rejected, loudly

Jinja-style control tags (`[[% if %]]`, `[[% for %]]`) are **not** supported and raise `MailTemplateFault` rather than being passed through. Shipping a raw `[[% if %]]` token to a recipient's inbox is worse than failing the render. Build conditional content in Python and pass the result in the context.

### Error behavior

- Unknown filter, malformed filter arguments, or a control-flow tag → `MailTemplateFault`
- A missing context variable renders as empty rather than raising, so an optional field does not break a send
- Dotted lookups work against dicts and objects: `<< user.name >>`

---

## Provider Changes

All providers now build messages through the shared MIME layer:

- **SMTP** — restructured around shared MIME assembly, byte-level DKIM signing, STARTTLS enforcement, and XOAUTH2 authentication.
- **SES** — sends the fully assembled raw message, preserving custom headers and the DKIM signature.
- **SendGrid** — consistent header handling and attachment encoding.
- **Console / File** — render the same MIME structure as production providers, so what you inspect in development matches what ships.

---

## Compatibility

Backward compatible. `require_tls` already defaulted to `True`. DKIM, PII redaction, and OAuth2 are opt-in. Template rendering already autoescaped; this release documents the behavior and the filter set rather than changing it. Provider configuration and `EmailMessage` signatures are unchanged.

The one behavior worth calling out: with `dkim_enabled=True` and a broken configuration, sends now **fail** instead of shipping unsigned mail. Run `aq mail check` after enabling DKIM.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [CLI Changes](cli.md)
- [Migration Guide](migration.md)
