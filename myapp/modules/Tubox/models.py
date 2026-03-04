"""
Tubox module models (Aquilia ORM).

Define your database models here using the Aquilia Model system.
Models are auto-discovered and registered when ``auto_discover=True``
in the manifest.

Usage:
    # Query
    items = await Tubox.objects.all()
    item = await Tubox.objects.get(id=1)

    # Create
    item = await Tubox.objects.create(name="Example")

    # Filter
    items = await Tubox.objects.filter(active=True)
"""

from aquilia.models import Model
from aquilia.models.fields import (
    AutoField,
    CharField,
    TextField,
    BooleanField,
    DateTimeField,
)


class Tubox(Model):
    """
    Tubox model.

    Table: tubox
    """
    table = "tubox"

    id = AutoField(primary_key=True)
    name = CharField(max_length=255)
    description = TextField(blank=True, default="")
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __repr__(self):
        return f"<Tubox id={self.id} name={self.name!r}>"