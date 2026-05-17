---
name: aquilia-template-mail-i18n
description: "Build Aquilia templates, mail, and i18n workflows. Use for sandboxed Jinja templates, template loaders/context/bytecode cache/security, mail providers/messages/envelopes, i18n catalogs/locales/plurals/extraction/compile, and related CLI commands."
---

# Aquilia Template Mail I18n

## Purpose
Implement UI/content delivery workflows that combine templates, mail, and localization using Aquilia subsystems.

## Trigger Conditions
Use for `Integration.templates`, `TemplatesIntegration`, Jinja rendering, template security, static tags, mail providers, test emails, localized content, i18n extraction, and catalog compilation.

## Inputs
- Template search paths, cache mode, sandbox flag, context processors.
- Mail provider config: console, file, SMTP, SES, or SendGrid.
- Locales, translation directories, source dirs, output catalog path, plural behavior.

## Execution Flow
1. Configure templates globally with `TemplatesIntegration` or `Integration.templates.*` and module templates with `TemplateConfig`.
2. Use `TemplateManager`/engine integration through DI or controller helpers where available.
3. Build mail with `MailIntegration`, provider objects, `MailAuth`, messages, envelopes, and `MailService`.
4. Configure i18n through `Workspace.i18n(...)` or `Integration.i18n(...)`; use CLI `aq i18n init/check/inspect/extract/coverage/compile`.
5. Test with console/file mail providers and in-memory template/cache settings before external providers.

## Constraints
- Keep templates sandboxed unless there is a verified reason not to.
- Do not put provider secrets in source; use env-backed auth fields.
- i18n extraction should merge by default unless the user explicitly wants overwrite behavior.

## Implementation Anchors
`aquilia/templates/`, `aquilia/mail/`, `aquilia/i18n/`, `aquilia/cli/commands/mail.py`, `aquilia/cli/commands/i18n.py`, `examples/templates_portal_app/`, `examples/mail_notifications_app/`, `examples/i18n_content_app/`.

## Examples
- Add `TemplatesIntegration(search_paths=["templates"], cache="memory", sandbox=True)`.
- Send a notification through a console mail provider in development.
- Run `aq i18n extract --source-dirs modules,controllers --output locales/en/messages.json`.

## Failure Handling
Template faults should include template path/context without leaking secrets. Mail provider failures should preserve envelope status. Missing locale keys should be surfaced by i18n check/coverage before runtime.
