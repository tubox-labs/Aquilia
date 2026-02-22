"""
Migration: 20260222_084848_usersmodel
Generated: 2026-02-22T08:48:48.371847+00:00
Models: UsersModel
"""

from aquilia.models.migration_dsl import (
    CreateIndex, CreateModel,
    columns as C,
)


class Meta:
    revision = "20260222_084848"
    slug = "usersmodel"
    models = ['UsersModel']


operations = [
    CreateModel(
        name='UsersModel',
        table='users',
        fields=[
            C.auto("id"),
            C.varchar("username", 225, default='unknown'),
            C.text("name"),
            C.varchar("email", 225, unique=True),
            C.varchar("password", 225),
            C.integer("active", default=False),
            C.timestamp("created_at"),
        ],
    ),
    CreateIndex(
        name='idx_users_email', table='users',
        columns=['email'], unique=False,
    ),
]
