from aquilia.models import Model
from aquilia.models.fields import BooleanField, CharField, DateTimeField, TextField


class SupportTicket(Model):
    table = "support_tickets"

    key = CharField(max_length=32, unique=True)
    customer_email = CharField(max_length=255)
    subject = CharField(max_length=160)
    body = TextField(null=True)
    priority = CharField(max_length=16, default="normal")
    assigned_to = CharField(max_length=120, null=True)
    resolved = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["resolved", "-created_at"]
