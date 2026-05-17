from __future__ import annotations

from pathlib import Path
from typing import Any

from aquilia.mail import EmailMessage
from aquilia.mail.envelope import MailEnvelope
from aquilia.mail.providers import ProviderResultStatus
from aquilia.mail.providers.file import FileProvider


class NotificationService:
    def __init__(self, output_dir: str | Path = "/tmp/aquilia_example_mail") -> None:
        self.provider = FileProvider(name="file", output_dir=str(output_dir))
        self._started = False

    async def startup(self) -> None:
        if not self._started:
            await self.provider.initialize()
            self._started = True

    async def shutdown(self) -> None:
        if self._started:
            await self.provider.shutdown()
            self._started = False

    def build_welcome_message(self, email: str, name: str) -> tuple[MailEnvelope, dict[str, bytes]]:
        message = EmailMessage(
            subject=f"Welcome, {name}",
            body=f"Hello {name}, your workspace is ready.",
            from_email="noreply@example.test",
            to=[email],
            tenant_id="example",
            headers={"X-Workflow": "welcome"},
        )
        message.attach("getting-started.txt", b"Open the dashboard and invite your team.", "text/plain")
        return message.build_envelope(default_from="noreply@example.test")

    async def send_welcome(self, email: str, name: str) -> dict[str, Any]:
        await self.startup()
        envelope, blobs = self.build_welcome_message(email, name)
        for digest, data in blobs.items():
            envelope.metadata[f"blob:{digest}"] = data
        result = await self.provider.send(envelope)
        return {
            "envelope_id": envelope.id,
            "provider_status": result.status.value,
            "sent": result.status == ProviderResultStatus.SUCCESS,
            "subject": envelope.subject,
            "to": envelope.to,
        }
