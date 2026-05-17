from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="notifications",
    version="1.0.0",
    description="Notification module using Aquilia EmailMessage and file provider delivery.",
    controllers=["modules.notifications.controllers:NotificationsController"],
    services=["modules.notifications.services:NotificationService"],
    exports=["modules.notifications.services:NotificationService"],
    tags=["mail", "notifications"],
)
