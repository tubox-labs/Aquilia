"""
Controllers for rest Module.
Uses native Aquilia Contracts (declared via Annotated + Field) for request validation, model imprinting, and response molding.
Demonstrates PageNumberPagination from aquilia.controller.pagination.
"""

from aquilia import (
    DELETE,
    GET,
    PATCH,
    POST,
    Controller,
    Response,
)
from aquilia.controller.pagination import PageNumberPagination

from .contracts import (
    CreateArticleContract,
    QueryArticleContract,
    RestContract,
    UpdateArticleContract,
)
from .services import RestService


class RestController(Controller):
    """
    HTTP Controller for REST API Contract demonstration.
    Class name matches generated manifest declaration.
    """

    prefix = "/articles"
    tags = ["rest"]

    def __init__(self, service: RestService) -> None:
        self.service = service

    @POST(
        "/",
        status_code=201,
        summary="Create Article via Imprint",
        description="Validates request with CreateArticleContract and imprints to Rest model",
        request_contract=CreateArticleContract,
        response_contract=RestContract["summary"],
    )
    async def create_article(self, body: CreateArticleContract):
        """Create a new article by imprinting sealed contract data onto a model instance."""
        return await self.service.create(body)

    @GET(
        "/",
        summary="List Articles with PageNumberPagination",
        description="Retrieves a paginated list of articles using PageNumberPagination",
        pagination_class=PageNumberPagination,
        response_contract=RestContract["summary"],
    )
    async def list_articles(self, query: QueryArticleContract):
        """List articles using PageNumberPagination and contract query validation."""
        q = query.validated_data if hasattr(query, "validated_data") else query
        articles, total = await self.service.list_articles(
            page=q.get("page", 1),
            limit=q.get("limit", 10),
            search=q.get("search"),
            category=q.get("category"),
            status=q.get("status"),
            ordering=q.get("ordering", "-created_at"),
        )
        return articles

    @GET(
        "/<id:str>",
        summary="Get Article Detail",
        description="Retrieves detailed view of an article by UUID",
        response_contract=RestContract["detail"],
    )
    async def get_article(self, id: str):
        """Get article detail by UUID string ID."""
        return await self.service.get_by_id(id)

    @PATCH(
        "/<id:str>",
        summary="Update Article via Imprint",
        description="Partially updates an article by imprinting contract data onto an existing model",
        request_contract=UpdateArticleContract,
        response_contract=RestContract["detail"],
    )
    async def update_article(self, id: str, body: UpdateArticleContract):
        """Partially update an article by UUID."""
        return await self.service.update(id, body)

    @DELETE(
        "/<id:str>",
        status_code=204,
        summary="Delete Article",
        description="Deletes an article by UUID",
    )
    async def delete_article(self, id: str) -> Response:
        """Delete an article by UUID."""
        await self.service.delete(id)
        return {"response": f"Item({id}) deleted"}