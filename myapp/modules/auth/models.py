"""
Auth module models (Aquilia ORM).

Define your database models here using the Aquilia Model system.
Models are auto-discovered and registered when ``auto_discover=True``
in the manifest.

Usage:
    # Query
    items = await Auth.objects.all()
    item = await Auth.objects.get(id=1)

    # Create
    item = await Auth.objects.create(name="Example")

    # Filter
    items = await Auth.objects.filter(active=True)
"""

from aquilia.models import Model
from aquilia.models.fields import (
    AutoField,
    CharField,
    TextField,
    BooleanField,
    DateTimeField,
)


class Auth(Model):
    """
    Auth model.

    Table: auth
    """
    table = "auth"

    id = AutoField(primary_key=True)
    name = CharField(max_length=255)
    description = TextField(blank=True, default="")
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __repr__(self):
        return f"<Auth id={self.id} name={self.name!r}>"