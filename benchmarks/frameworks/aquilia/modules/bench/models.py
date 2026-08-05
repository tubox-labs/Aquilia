from __future__ import annotations

from aquilia.models import Model
from aquilia.models.fields_module import CharField, IntegerField


class World(Model):
    table = "world"

    id = IntegerField(primary_key=True)
    randomNumber = IntegerField()


class Fortune(Model):
    table = "fortune"

    id = IntegerField(primary_key=True)
    message = CharField(max_length=2048)
