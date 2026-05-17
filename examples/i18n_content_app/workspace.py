from aquilia import Integration, Module, Workspace

workspace = (
    Workspace("i18n-content-app", version="1.0.0", description="Localized content and pluralization reference")
    .runtime(mode="dev", host="127.0.0.1", port=8065, reload=True)
    .module(Module("content", version="1.0.0").route_prefix("/content").tags("i18n"))
    .i18n(default_locale="en", available_locales=["en", "es", "fr"], catalog_dirs=["locales"], missing_key_strategy="return_key")
    .integrate(Integration.di(auto_wire=True))
)
