from aquilia import AppManifest
from aquilia.manifest import BackgroundTaskConfig, FaultHandlingConfig

manifest = AppManifest(
    name="jobs",
    version="1.0.0",
    description="Background task module",
    controllers=["modules.jobs.controllers:JobsController"],
    services=["modules.jobs.services:JobsService"],
    background_tasks=BackgroundTaskConfig(
        tasks=[
            "modules.jobs.tasks:send_welcome_email",
            "modules.jobs.tasks:rebuild_daily_report",
            "modules.jobs.tasks:cleanup_old_jobs",
        ],
        default_queue="default",
    ),
    base_path="modules.jobs",
    tags=["tasks"],
    faults=FaultHandlingConfig(default_domain="JOBS", strategy="propagate"),
)

__all__ = ["manifest"]
