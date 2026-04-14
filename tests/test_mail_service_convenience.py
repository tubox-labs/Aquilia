from __future__ import annotations

import pytest

from aquilia.mail.service import asend_mail, send_mail


def test_send_mail_forwards_attachments_to_email_message(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class DummyMessage:
        def __init__(self, **kwargs):
            captured["attachments"] = kwargs.get("attachments")

        def send(self, fail_silently: bool = False) -> str | None:
            captured["fail_silently"] = fail_silently
            return "env-sync"

    monkeypatch.setattr("aquilia.mail.message.EmailMessage", DummyMessage)

    attachments = [("report.txt", b"hello", "text/plain")]
    result = send_mail(
        subject="Subject",
        body="Body",
        to="user@example.com",
        attachments=attachments,
        fail_silently=True,
    )

    assert result == "env-sync"
    assert captured["attachments"] == attachments
    assert captured["fail_silently"] is True


@pytest.mark.asyncio
async def test_asend_mail_forwards_attachments_to_email_message(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class DummyMessage:
        def __init__(self, **kwargs):
            captured["attachments"] = kwargs.get("attachments")

        async def asend(self, fail_silently: bool = False) -> str | None:
            captured["fail_silently"] = fail_silently
            return "env-async"

    monkeypatch.setattr("aquilia.mail.message.EmailMessage", DummyMessage)

    attachments = [("invoice.pdf", b"pdf-bytes", "application/pdf")]
    result = await asend_mail(
        subject="Subject",
        body="Body",
        to=["user@example.com"],
        attachments=attachments,
    )

    assert result == "env-async"
    assert captured["attachments"] == attachments
    assert captured["fail_silently"] is False