"""
Rest module models (Aquilia ORM).
Production-grade model with UUID primary keys, column indexes, composite indexes, and unique constraints.
"""

from aquilia.models import (
    BooleanField,
    CharField,
    DateTimeField,
    Index,
    IntegerField,
    JSONField,
    Model,
    TextField,
    UniqueConstraint,
    UUIDField,
)


class Rest(Model):
    """
    Production-grade Rest model matching generated manifest declaration.
    Uses UUID primary keys, field-level indexes, composite indexes, and database constraints.
    """

    table = "rest_articles"

    id = UUIDField(auto=True, primary_key=True)
    title = CharField(max_length=200, null=False)
    content = TextField(null=False)
    category = CharField(max_length=50, default="general", db_index=True)
    author_email = CharField(max_length=254, null=False, db_index=True)
    tags = JSONField(default=list)
    status = CharField(max_length=20, default="draft", db_index=True)
    is_featured = BooleanField(default=False)
    read_count = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["category", "status"], name="idx_rest_cat_status"),
            Index(fields=["author_email", "created_at"], name="idx_rest_author_date"),
        ]
        constraints = [
            UniqueConstraint(fields=["title", "author_email"], name="uniq_rest_title_author"),
        ]

    def __repr__(self) -> str:
        return f"<Rest id={self.id} title={self.title!r}>"