from __future__ import annotations

import tempfile
from pathlib import Path

from aquilia.i18n import I18nConfig, I18nService, MemoryCatalog
from aquilia.mail import MailEnvelope
from aquilia.mail.providers import ConsoleProvider
from aquilia.templates import TemplateEngine, TemplateLoader


async def run() -> dict:
    catalog = MemoryCatalog(
        {
            "en": {"messages": {"welcome": "Welcome, {name}!"}},
            "fr": {"messages": {"welcome": "Bienvenue, {name}!"}},
        }
    )
    i18n = I18nService(
        I18nConfig(default_locale="en", available_locales=["en", "fr"], fallback_locale="en"),
        catalog=catalog,
    )
    translated = i18n.t("messages.welcome", locale="fr", name="Asha")

    with tempfile.TemporaryDirectory() as tmp:
        template_dir = Path(tmp)
        (template_dir / "welcome.html").write_text("<p>{{ message }}</p>", encoding="utf-8")
        templates = TemplateEngine(TemplateLoader(search_paths=[str(template_dir)]))
        html = await templates.render("welcome.html", {"message": translated})

    envelope = MailEnvelope(
        from_email="noreply@example.test",
        to=["asha@example.test"],
        subject="Welcome",
        body_text=translated,
    )
    envelope.compute_digest()
    provider = ConsoleProvider()
    await provider.initialize()
    result = await provider.send(envelope)
    await provider.shutdown()
    return {
        "translation": translated,
        "html": html,
        "mail_status": result.status.value,
        "digest_prefix": envelope.digest[:12],
    }
