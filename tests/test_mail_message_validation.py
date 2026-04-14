from __future__ import annotations

import pytest

from aquilia.mail.faults import MailValidationFault
from aquilia.mail.message import EmailMessage


def test_email_message_accepts_single_to_string() -> None:
    msg = EmailMessage(subject="Hello", body="Body", to="alice@example.com")
    assert msg.to == ["alice@example.com"]


def test_email_message_accepts_single_cc_and_bcc_strings() -> None:
    msg = EmailMessage(
        subject="Hello",
        body="Body",
        to=["alice@example.com"],
        cc="bob@example.com",
        bcc="carol@example.com",
    )
    assert msg.cc == ["bob@example.com"]
    assert msg.bcc == ["carol@example.com"]


def test_email_message_rejects_invalid_single_to_string() -> None:
    with pytest.raises(MailValidationFault):
        EmailMessage(subject="Hello", body="Body", to="not-an-email")