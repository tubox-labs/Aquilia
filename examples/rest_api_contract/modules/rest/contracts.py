"""
Aquilia REST API Contracts Definition using Annotated and Field syntax.

Exposes type-annotation-driven request/response contracts, schemas,
validation rules, projections, computed methods, and OpenAPI schema generators.
"""

import uuid
from datetime import datetime
from typing import Annotated, Any

from aquilia import Contract
from aquilia.contracts import Field, computed

from .models import Rest

# ── Choices ─────────────────────────────────────────────────────────────
STATUS_CHOICES = ["draft", "published", "archived"]
CATEGORY_CHOICES = ["tech", "science", "design", "general"]


class RestContract(Contract):
    """
    Primary contract matching generated name for input/output validation and model imprinting.
    Using Annotated and Field syntax with UUID primary keys.
    """

    id: Annotated[uuid.UUID | str | None, Field(read_only=True, required=False)] = None
    title: Annotated[str, Field(min_length=5, max_length=200)]
    content: Annotated[str, Field(min_length=10, max_length=10000)]
    category: Annotated[str, Field(choices=CATEGORY_CHOICES, default="general")]
    author_email: Annotated[str, Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")]
    tags: Annotated[list[str], Field(default_factory=list)]
    status: Annotated[str, Field(choices=STATUS_CHOICES, default="draft")]
    is_featured: Annotated[bool, Field(default=False)]
    read_count: Annotated[int, Field(default=0, read_only=True)]
    created_at: Annotated[datetime | None, Field(read_only=True, required=False)] = None

    @computed
    def word_count(self, instance: Any) -> int:
        content = getattr(instance, "content", "") or ""
        return len(content.split())

    @computed
    def summary_snippet(self, instance: Any) -> str:
        content = getattr(instance, "content", "") or ""
        return content[:100] + "..." if len(content) > 100 else content

    class Spec:
        model = Rest
        projections = {
            "summary": [
                "id",
                "title",
                "category",
                "author_email",
                "status",
                "is_featured",
                "read_count",
                "summary_snippet",
                "created_at",
            ],
            "detail": [
                "id",
                "title",
                "content",
                "category",
                "author_email",
                "tags",
                "status",
                "is_featured",
                "read_count",
                "word_count",
                "created_at",
            ],
        }


class CreateArticleContract(RestContract):
    """Inbound creation contract with Spec.model binding for imprint."""

    class Spec:
        model = Rest


class UpdateArticleContract(Contract):
    """Inbound update contract with Spec.model binding for imprint."""

    title: Annotated[str | None, Field(min_length=5, max_length=200, required=False)] = None
    content: Annotated[str | None, Field(min_length=10, max_length=10000, required=False)] = None
    category: Annotated[str | None, Field(choices=CATEGORY_CHOICES, required=False)] = None
    author_email: Annotated[str | None, Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$", required=False)] = None
    tags: Annotated[list[str] | None, Field(required=False)] = None
    status: Annotated[str | None, Field(choices=STATUS_CHOICES, required=False)] = None
    is_featured: Annotated[bool | None, Field(required=False)] = None

    class Spec:
        model = Rest


class QueryArticleContract(Contract):
    """Query parameter contract."""

    page: Annotated[int, Field(ge=1, default=1)]
    limit: Annotated[int, Field(ge=1, le=100, default=10)]
    search: Annotated[str | None, Field(max_length=100, required=False)] = None
    category: Annotated[str | None, Field(choices=CATEGORY_CHOICES, required=False)] = None
    status: Annotated[str | None, Field(choices=STATUS_CHOICES, required=False)] = None
    ordering: Annotated[str, Field(choices=["created_at", "-created_at", "title", "-title"], default="-created_at")]
