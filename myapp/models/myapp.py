"""
Myapp models — Aquilia ORM.

Define your database models here. Models are auto-discovered
when ``auto_discover=True`` in the workspace or module manifest.

Usage:
    from models.myapp import MyappItem

    # Create
    item = await MyappItem.objects.create(name="Example")

    # Query
    items = await MyappItem.objects.all()
    item  = await MyappItem.objects.get(id=1)

    # Filter
    active = await MyappItem.objects.filter(active=True)
"""

from aquilia.models import Model
from aquilia.models.fields import (
    AutoField,
    CharField,
    TextField,
    BooleanField,
    DateTimeField,
)


class MyappItem(Model):
    """Example model for the myapp workspace."""

    table = "myapp_items"

    id = AutoField(primary_key=True)
    name = CharField(max_length=255)
    description = TextField(blank=True, default="")
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __repr__(self):
        return f"<MyappItem id={self.id} name={self.name!r}>"