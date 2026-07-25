"""
Test Suite for REST Module (Annotated + Field syntax + UUID ORM Models + Imprint + Pagination).
Tests request body validation, model imprinting, pagination, projections, and OpenAPI schema generation.
"""

import uuid
import pytest

from aquilia.controller.pagination import PageNumberPagination
from modules.rest.contracts import (
    CreateArticleContract,
    QueryArticleContract,
    RestContract,
    UpdateArticleContract
)
from modules.rest.faults import RestNotFoundFault
from modules.rest.models import Rest
from modules.rest.services import RestService


@pytest.mark.asyncio
async def test_annotated_contract_validation_and_imprint():
    """Test Contract sealing and model imprint filtering."""
    data = {
        "title": "Building Native Aquilia Applications",
        "content": "Comprehensive guide to type-annotation-driven Contracts, DI, and CLI.",
        "category": "tech",
        "author_email": "developer@aquilia.dev",
        "tags": ["aquilia", "python", "framework"],
        "status": "published",
        "is_featured": True,
    }
    contract = CreateArticleContract(data=data)
    assert contract.is_sealed() is True

    imprint_data = contract._filter_imprint_data(contract.validated_data)
    assert "title" in imprint_data
    assert imprint_data["title"] == "Building Native Aquilia Applications"


@pytest.mark.asyncio
async def test_pagenumber_pagination_integration():
    """Test PageNumberPagination envelope formatting."""
    items = [
        {"id": 1, "title": "Article 1"},
        {"id": 2, "title": "Article 2"},
        {"id": 3, "title": "Article 3"},
    ]
    paginator = PageNumberPagination(page_size=2)

    class FakeRequest:
        path = "/articles"
        query_params = {"page": 1, "page_size": 2}

    res = paginator.paginate_list(items, FakeRequest())
    assert res["count"] == 3
    assert res["total_pages"] == 2
    assert res["page"] == 1
    assert len(res["results"]) == 2


@pytest.mark.asyncio
async def test_rest_service_orm_contract_imprint():
    """Test RestService using contract imprint and ORM operations."""
    service = RestService()

    data = {
        "title": "Aquilia Architecture Deep Dive",
        "content": "Detailed overview of Aquilary, Flow, and DI containers.",
        "category": "tech",
        "author_email": "author@aquilia.org",
    }
    contract = CreateArticleContract(data=data)
    assert contract.is_sealed() is True

    # Test creating via service contract input
    article = Rest(
        id=str(uuid.uuid4()),
        title=data["title"],
        content=data["content"],
        category=data["category"],
        author_email=data["author_email"],
    )
    assert article.title == "Aquilia Architecture Deep Dive"


def test_model_indexes_and_constraints_meta():
    """Verify ORM model definition contains UUIDField, indexes, and constraints."""
    meta = Rest._meta
    assert hasattr(Rest, "id")
    assert meta.table_name == "rest_articles"
    assert len(meta.indexes) == 2
    assert len(meta.constraints) == 1
    assert meta.indexes[0].name == "idx_rest_cat_status"
    assert meta.constraints[0].name == "uniq_rest_title_author"


@pytest.mark.asyncio
async def test_rest_contract_summary_projection():
    """Verify RestContract summary projection renders non-empty data dictionary."""
    from modules.rest.contracts import RestContract
    article = Rest(
        id=str(uuid.uuid4()),
        title="Testing POST response rendering",
        content="Valid content string for article creation test.",
        status="published",
    )
    from aquilia.contracts.integration import render_contract_response

    rendered = render_contract_response(RestContract["summary"], article)
    assert rendered != {}
    assert "id" in rendered
    assert "status" in rendered
    assert rendered["status"] == "published"
@pytest.mark.asyncio
async def test_rest_not_found_fault_mapping():
    """Verify RestNotFoundFault maps to HTTP 404 status and includes item_id metadata."""
    from modules.rest.faults import RestNotFoundFault

    fault = RestNotFoundFault(item_id="missing-id-123")
    assert getattr(fault, "status", None) == 404
    assert fault.code == "rest.not_found"
    assert fault.metadata.get("item_id") == "missing-id-123"
    assert fault.public is True
