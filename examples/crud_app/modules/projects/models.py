from aquilia.models import Model
from aquilia.models.fields import BooleanField, CharField, DateTimeField, TextField


class Project(Model):
    table = "projects"

    key = CharField(max_length=32, unique=True)
    name = CharField(max_length=160)
    summary = TextField(null=True)
    owner_email = CharField(max_length=255)
    status = CharField(max_length=32, default="planned")
    archived = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
