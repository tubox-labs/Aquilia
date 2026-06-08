from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, FileProvider, MailIntegration

workspace = (
    Workspace("mail-notifications-app", version="1.0.0", description="Mail notification workflow")
    .runtime(mode="dev", host="127.0.0.1", port=8064, reload=True)
    .module(Module("notifications", version="1.0.0").route_prefix("/notifications").tags("mail"))
    .integrate(MailIntegration(default_from="noreply@example.test", providers=[FileProvider(name="file", output_dir="var/mail")]))
    .integrate(DiIntegration(auto_wire=True))
)