"""
Migration: 20260305_173921_admingroup_adminlogentry_adminpermission_and_3_more
Generated: 2026-03-05T17:39:21.476963+00:00
Models: AdminGroup, AdminLogEntry, AdminPermission, AdminSession, AdminUser, ContentType
"""

from aquilia.models.migration_dsl import (
    CreateIndex, CreateModel,
    columns as C,
)


class Meta:
    revision = "20260305_173921"
    slug = "admingroup_adminlogentry_adminpermission_and_3_more"
    models = ['AdminGroup', 'AdminLogEntry', 'AdminPermission', 'AdminSession', 'AdminUser', 'ContentType']


operations = [
    CreateModel(
        name='AdminGroup',
        table='admin_groups',
        fields=[
            C.varchar("name", 150, unique=True),
            C.auto("id"),
        ],
    ),
    CreateModel(
        name='AdminLogEntry',
        table='admin_log_entries',
        fields=[
            C.timestamp("action_time"),
            C.integer("user_id"),
            C.integer("content_type_id", null=True),
            C.varchar("object_id", 255, null=True),
            C.varchar("object_repr", 200, default=''),
            C.integer("action_flag"),
            C.text("change_message", default=''),
            C.auto("id"),
        ],
    ),
    CreateIndex(
        name='idx_log_entry_time', table='admin_log_entries',
        columns=['action_time'], unique=False,
    ),
    CreateIndex(
        name='idx_log_entry_user_time', table='admin_log_entries',
        columns=['user_id', 'action_time'], unique=False,
    ),
    CreateIndex(
        name='idx_log_entry_ct_obj', table='admin_log_entries',
        columns=['content_type_id', 'object_id'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_log_entries_action_time', table='admin_log_entries',
        columns=['action_time'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_log_entries_user_id', table='admin_log_entries',
        columns=['user_id'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_log_entries_content_type_id', table='admin_log_entries',
        columns=['content_type_id'], unique=False,
    ),
    CreateModel(
        name='AdminPermission',
        table='admin_permissions',
        fields=[
            C.varchar("name", 255),
            C.varchar("codename", 100),
            C.integer("content_type_id"),
            C.auto("id"),
        ],
    ),
    CreateIndex(
        name='idx_permission_codename', table='admin_permissions',
        columns=['codename'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_permissions_codename', table='admin_permissions',
        columns=['codename'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_permissions_content_type_id', table='admin_permissions',
        columns=['content_type_id'], unique=False,
    ),
    CreateModel(
        name='AdminSession',
        table='admin_sessions',
        fields=[
            C.varchar("session_key", 40, unique=True),
            C.text("session_data", default=''),
            C.timestamp("expire_date"),
            C.auto("id"),
        ],
    ),
    CreateIndex(
        name='idx_admin_session_key', table='admin_sessions',
        columns=['session_key'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_session_expire', table='admin_sessions',
        columns=['expire_date'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_sessions_session_key', table='admin_sessions',
        columns=['session_key'], unique=True,
    ),
    CreateIndex(
        name='idx_admin_sessions_expire_date', table='admin_sessions',
        columns=['expire_date'], unique=False,
    ),
    CreateModel(
        name='AdminUser',
        table='admin_users',
        fields=[
            C.varchar("username", 150, unique=True),
            C.varchar("email", 254, default=''),
            C.text("password_hash"),
            C.varchar("first_name", 150, default=''),
            C.varchar("last_name", 150, default=''),
            C.boolean("is_superuser", default=False),
            C.boolean("is_staff", default=True),
            C.boolean("is_active", default=True),
            C.timestamp("last_login", null=True),
            C.timestamp("date_joined"),
            C.varchar("avatar_path", 512, null=True, default=''),
            C.text("bio", null=True, default=''),
            C.varchar("phone", 32, null=True, default=''),
            C.varchar("timezone", 64, null=True, default='UTC'),
            C.varchar("locale", 16, null=True, default='en'),
            C.auto("id"),
        ],
    ),
    CreateIndex(
        name='idx_admin_user_username', table='admin_users',
        columns=['username'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_user_email', table='admin_users',
        columns=['email'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_user_active_staff', table='admin_users',
        columns=['is_active', 'is_staff'], unique=False,
    ),
    CreateModel(
        name='ContentType',
        table='admin_content_types',
        fields=[
            C.varchar("app_label", 100),
            C.varchar("model", 100),
            C.auto("id"),
        ],
    ),
    CreateIndex(
        name='idx_content_type_lookup', table='admin_content_types',
        columns=['app_label', 'model'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_content_types_app_label', table='admin_content_types',
        columns=['app_label'], unique=False,
    ),
    CreateIndex(
        name='idx_admin_content_types_model', table='admin_content_types',
        columns=['model'], unique=False,
    ),
]
