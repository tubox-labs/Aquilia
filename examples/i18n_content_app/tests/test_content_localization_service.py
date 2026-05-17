from examples.i18n_content_app.modules.content.services import ContentLocalizationService


def test_landing_copy_negotiates_locale_and_pluralizes():
    service = ContentLocalizationService()
    copy = service.landing_copy(accept_language="es,en;q=0.8", name="Ana", count=3)

    assert copy["locale"] == "es"
    assert copy["welcome"] == "Bienvenido, Ana!"
    assert copy["items"] == "3 articulos"


def test_missing_keys_return_key_for_safe_development_defaults():
    service = ContentLocalizationService()
    assert service.missing_key("messages.unknown") == "messages.unknown"
