from aquilia import AppManifest
from aquilia.manifest import BackgroundTaskConfig, FaultHandlingConfig

manifest = AppManifest(
    name="notifications",
    version="1.0.0",
    description="Notification task and mail module",
    controllers=["modules.notifications.controllers:NotificationsController"],
    services=["modules.notifications.services:NotificationService"],
    background_tasks=BackgroundTaskConfig(tasks=["modules.notifications.tasks:send_order_receipt"], default_queue="mail"),
    imports=["accounts"],
    base_path="modules.notifications",
    tags=["notifications", "mail", "tasks"],
    faults=FaultHandlingConfig(default_domain="NOTIFICATIONS", strategy="propagate"),
)

__all__ = ["manifest"]
