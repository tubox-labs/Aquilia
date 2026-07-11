"""
Regression tests for Dep() vs request body precedence.

Bug: When a controller handler declares a Contract-typed parameter with
``Dep(callable)`` as a default value, the request body was overriding the
dependency result.

Fix: metadata.py's _extract_method_params() now checks param.default for
Dep(...) BEFORE checking _is_contract_type(). engine.py's _bind_parameters()
dep branch now falls back to param.default for Dep descriptor lookup.

Covers:
  - Contract dependency winning over request body
  - Non-contract dependency injection via Dep default
  - Async dependency providers
  - Sync dependency providers
  - Multiple parameters with mixed Dep + body-bound contracts
  - Dep default with Annotated[T, Dep(...)] parity
  - Missing/None dependency returns
  - Backward compatibility: body parsing for non-Dep contracts
  - Metadata source classification correctness
  - Engine _bind_parameters integration
"""

from __future__ import annotations

import inspect
import json
from typing import Annotated

import pytest

from aquilia.contracts import Contract
from aquilia.controller.base import Controller, RequestCtx
from aquilia.controller.decorators import POST
from aquilia.controller.engine import ControllerEngine
from aquilia.controller.factory import ControllerFactory
from aquilia.controller.metadata import (
    _has_dep_default,
    extract_controller_metadata,
)
from aquilia.di.core import Container
from aquilia.di.dep import Dep
from aquilia.di.request_dag import RequestDAG
from aquilia.request import Request

# ═══════════════════════════════════════════════════════════════════════════
#  Test Contracts
# ═══════════════════════════════════════════════════════════════════════════


class SimpleContract(Contract):
    slug: str
    title: str = "default"


class OrderItemBP(Contract):
    product_id: int
    qty: int
    price: float


class OrderBP(Contract):
    items: list
    total: float


class TagBP(Contract):
    name: str
    color: str = "blue"


# ═══════════════════════════════════════════════════════════════════════════
#  Dependency Providers (sync + async)
# ═══════════════════════════════════════════════════════════════════════════


async def get_simple_async() -> SimpleContract:
    """Async provider: returns a Contract with fixed data."""
    bp = SimpleContract(data={"slug": "from-dep", "title": "Dep Title"})
    bp.is_sealed(raise_fault=True)
    return bp


def get_simple_sync() -> SimpleContract:
    """Sync provider: returns a Contract with fixed data."""
    bp = SimpleContract(data={"slug": "sync-dep", "title": "Sync Title"})
    bp.is_sealed(raise_fault=True)
    return bp


async def get_tag_async() -> TagBP:
    """Async provider for TagBP."""
    bp = TagBP(data={"name": "injected-tag", "color": "red"})
    bp.is_sealed(raise_fault=True)
    return bp


def get_tag_sync() -> TagBP:
    """Sync provider for TagBP."""
    bp = TagBP(data={"name": "sync-tag", "color": "green"})
    bp.is_sealed(raise_fault=True)
    return bp


async def get_none_dep() -> SimpleContract | None:
    """Provider that returns None."""
    return None


async def get_string_dep() -> str:
    """Non-contract provider returning a string."""
    return "injected-string"


def get_int_sync() -> int:
    """Sync non-contract provider returning an int."""
    return 42


# ═══════════════════════════════════════════════════════════════════════════
#  Controllers
# ═══════════════════════════════════════════════════════════════════════════


class DepPrecedenceController(Controller):
    prefix = "/test"

    # The original bug case: Contract-typed param with Dep default
    @POST("/contract-dep")
    async def contract_dep(
        self,
        ctx: RequestCtx,
        orders: OrderBP,
        article: SimpleContract = Dep(get_simple_async),
    ):
        return {
            "order_total": orders.total,
            "article_slug": article.slug if hasattr(article, "slug") else str(article),
        }

    # Sync dependency provider
    @POST("/contract-dep-sync")
    async def contract_dep_sync(
        self,
        ctx: RequestCtx,
        orders: OrderBP,
        article: SimpleContract = Dep(get_simple_sync),
    ):
        return {
            "order_total": orders.total,
            "article_slug": article.slug if hasattr(article, "slug") else str(article),
        }

    # Multiple Dep defaults
    @POST("/multi-dep")
    async def multi_dep(
        self,
        ctx: RequestCtx,
        orders: OrderBP,
        article: SimpleContract = Dep(get_simple_async),
        tag: TagBP = Dep(get_tag_async),
    ):
        return {
            "order_total": orders.total,
            "article_slug": article.slug if hasattr(article, "slug") else str(article),
            "tag_name": tag.name if hasattr(tag, "name") else str(tag),
        }

    # Mixed: one body-bound contract + one Dep contract + one sync Dep contract
    @POST("/mixed-deps")
    async def mixed_deps(
        self,
        ctx: RequestCtx,
        orders: OrderBP,
        article: SimpleContract = Dep(get_simple_async),
        tag: TagBP = Dep(get_tag_sync),
    ):
        return {
            "order_total": orders.total,
            "article_slug": article.slug,
            "tag_name": tag.name,
            "tag_color": tag.color,
        }

    # Non-contract Dep default (string)
    @POST("/non-bp-dep")
    async def non_bp_dep(
        self,
        ctx: RequestCtx,
        orders: OrderBP,
        label: str = Dep(get_string_dep),
    ):
        return {"order_total": orders.total, "label": label}

    # Non-contract Dep default (int, sync)
    @POST("/non-bp-dep-sync")
    async def non_bp_dep_sync(
        self,
        ctx: RequestCtx,
        orders: OrderBP,
        count: int = Dep(get_int_sync),
    ):
        return {"order_total": orders.total, "count": count}

    # No Dep -- standard body-bound contract (backward compat)
    @POST("/body-only")
    async def body_only(
        self,
        ctx: RequestCtx,
        article: SimpleContract,
    ):
        return {"slug": article.slug, "title": article.title}

    # Has only a Dep param, no body-bound params (for testing empty body)
    @POST("/dep-only")
    async def dep_only(
        self,
        ctx: RequestCtx,
        label: str = Dep(get_string_dep),
    ):
        return {"label": label}


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════


def make_request(
    method: str = "POST",
    body: dict | None = None,
    content_type: str = "application/json",
) -> Request:
    """Create a mock Request with JSON body."""
    headers = {}
    if content_type:
        headers["content-type"] = content_type

    body_bytes = b""
    if body is not None:
        body_bytes = json.dumps(body).encode("utf-8")

    headers["content-length"] = str(len(body_bytes))

    scope = {
        "type": "http",
        "method": method,
        "path": "/",
        "query_string": b"",
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
    }

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    return Request(scope=scope, receive=receive)


def make_container() -> Container:
    """Create a minimal DI container for testing."""
    return Container()


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 1: Metadata Source Classification
# ═══════════════════════════════════════════════════════════════════════════


class TestHasDepDefault:
    """Unit tests for the _has_dep_default helper."""

    def test_dep_default_detected(self):
        """Dep(...) default value is detected."""
        sig = inspect.signature(DepPrecedenceController.contract_dep)
        param = sig.parameters["article"]
        assert _has_dep_default(param) is True

    def test_no_default_not_detected(self):
        """Parameter without default is not detected."""
        sig = inspect.signature(DepPrecedenceController.body_only)
        param = sig.parameters["article"]
        assert _has_dep_default(param) is False

    def test_non_dep_default_not_detected(self):
        """Non-Dep default value is not detected."""
        # Create a mock param with a string default
        param = type("P", (), {"default": "hello"})()
        assert _has_dep_default(param) is False

    def test_none_default_not_detected(self):
        """None default value is not detected."""
        param = type("P", (), {"default": None})()
        assert _has_dep_default(param) is False

    def test_empty_default_not_detected(self):
        """inspect.Parameter.empty default is not detected."""
        param = type("P", (), {"default": inspect.Parameter.empty})()
        assert _has_dep_default(param) is False


class TestMetadataSourceClassification:
    """Tests that _extract_method_params classifies Dep-defaulted params correctly."""

    def test_contract_with_dep_default_classified_as_dep(self):
        """Contract-typed param with Dep default gets source='dep', not 'body'."""
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "contract_dep")

        # Find the 'article' parameter
        article_param = next(p for p in route.parameters if p.name == "article")
        assert article_param.source == "dep", (
            f"Expected source='dep', got source='{article_param.source}'. "
            "Contract-typed params with Dep defaults must be classified as 'dep'."
        )

    def test_body_contract_without_dep_classified_as_body(self):
        """Contract-typed param WITHOUT Dep default stays source='body'."""
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "contract_dep")

        orders_param = next(p for p in route.parameters if p.name == "orders")
        assert orders_param.source == "body"

    def test_multiple_dep_defaults_all_classified(self):
        """Multiple Dep-defaulted params all get source='dep'."""
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "multi_dep")

        article_param = next(p for p in route.parameters if p.name == "article")
        tag_param = next(p for p in route.parameters if p.name == "tag")
        orders_param = next(p for p in route.parameters if p.name == "orders")

        assert article_param.source == "dep"
        assert tag_param.source == "dep"
        assert orders_param.source == "body"

    def test_non_contract_dep_default_classified_as_dep(self):
        """Non-Contract param with Dep default gets source='dep'."""
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "non_bp_dep")

        label_param = next(p for p in route.parameters if p.name == "label")
        assert label_param.source == "dep"

    def test_sync_dep_default_classified_as_dep(self):
        """Sync Dep provider default is also classified as 'dep'."""
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "contract_dep_sync")

        article_param = next(p for p in route.parameters if p.name == "article")
        assert article_param.source == "dep"

    def test_backward_compat_body_only(self):
        """Body-only contract (no Dep) is still classified as 'body'."""
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "body_only")

        article_param = next(p for p in route.parameters if p.name == "article")
        assert article_param.source == "body"


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 2: Engine _bind_parameters Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestDepPrecedenceBinding:
    """Integration tests: engine._bind_parameters resolves Dep correctly."""

    @pytest.mark.asyncio
    async def test_dep_wins_over_request_body(self):
        """Core bug fix: Dep-provided Contract is NOT overridden by request body."""
        body = {
            "items": [{"product_id": 1, "qty": 2, "price": 10.0}],
            "total": 20.0,
            "slug": "from-body",
            "title": "Body Title",
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)
        container = make_container()

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "contract_dep")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, container)

        # The article param should come from Dep(get_simple_async), NOT from body
        assert "article" in kwargs
        article = kwargs["article"]
        assert hasattr(article, "slug"), f"Expected Contract instance, got {type(article)}"
        assert article.slug == "from-dep", (
            f"Expected slug='from-dep' from Dep, got slug='{article.slug}'. "
            "Request body is still overriding the dependency!"
        )
        assert article.validated_data["title"] == "Dep Title"

        # orders should still come from body
        assert "orders" in kwargs
        assert kwargs["orders"].total == 20.0

        if dag is not None:
            await dag.teardown()

    @pytest.mark.asyncio
    async def test_sync_dep_provider_resolved(self):
        """Sync Dep provider is resolved correctly."""
        body = {
            "items": [{"product_id": 1, "qty": 1, "price": 5.0}],
            "total": 5.0,
            "slug": "body-slug",
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)
        container = make_container()

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "contract_dep_sync")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, container)

        article = kwargs["article"]
        assert article.slug == "sync-dep"
        assert article.validated_data["title"] == "Sync Title"

        if dag is not None:
            await dag.teardown()

    @pytest.mark.asyncio
    async def test_multiple_dep_params_resolved(self):
        """Multiple Dep-defaulted params are all resolved independently."""
        body = {
            "items": [{"product_id": 1, "qty": 1, "price": 10.0}],
            "total": 10.0,
            "slug": "body-slug",
            "name": "body-tag",
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)
        container = make_container()

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "multi_dep")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, container)

        # Both should come from deps, not body
        assert kwargs["article"].slug == "from-dep"
        assert kwargs["tag"].name == "injected-tag"
        assert kwargs["tag"].validated_data["color"] == "red"

        # orders from body
        assert kwargs["orders"].total == 10.0

        if dag is not None:
            await dag.teardown()

    @pytest.mark.asyncio
    async def test_mixed_async_sync_deps(self):
        """Mixed async + sync Dep providers both resolve correctly."""
        body = {
            "items": [{"product_id": 1, "qty": 1, "price": 15.0}],
            "total": 15.0,
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)
        container = make_container()

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "mixed_deps")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, container)

        # article = async dep
        assert kwargs["article"].slug == "from-dep"
        # tag = sync dep
        assert kwargs["tag"].name == "sync-tag"
        assert kwargs["tag"].validated_data["color"] == "green"

        if dag is not None:
            await dag.teardown()

    @pytest.mark.asyncio
    async def test_non_contract_dep_resolved(self):
        """Non-contract type with Dep default is resolved correctly."""
        body = {
            "items": [{"product_id": 1, "qty": 1, "price": 10.0}],
            "total": 10.0,
            "label": "from-body",
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)
        container = make_container()

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "non_bp_dep")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, container)

        assert kwargs["label"] == "injected-string"

        if dag is not None:
            await dag.teardown()

    @pytest.mark.asyncio
    async def test_non_contract_sync_dep_resolved(self):
        """Non-contract sync Dep provider resolves correctly."""
        body = {
            "items": [{"product_id": 1, "qty": 1, "price": 10.0}],
            "total": 10.0,
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)
        container = make_container()

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "non_bp_dep_sync")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, container)

        assert kwargs["count"] == 42

        if dag is not None:
            await dag.teardown()


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 3: Backward Compatibility
# ═══════════════════════════════════════════════════════════════════════════


class TestBackwardCompatibility:
    """Ensure existing body-bound Contract behavior is preserved."""

    @pytest.mark.asyncio
    async def test_body_contract_without_dep_still_works(self):
        """Contract param without Dep default still parses from body."""
        body = {"slug": "hello-world", "title": "Hello World"}
        req = make_request(body=body)
        ctx = RequestCtx(request=req)

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "body_only")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, make_container())

        assert "article" in kwargs
        article = kwargs["article"]
        assert article.slug == "hello-world"
        assert article.validated_data["title"] == "Hello World"

        if dag is not None:
            await dag.teardown()

    @pytest.mark.asyncio
    async def test_body_contract_in_mixed_handler_still_works(self):
        """Body-bound contract (orders) in handler with Dep params still parses correctly."""
        body = {
            "items": [{"product_id": 99, "qty": 3, "price": 29.99}],
            "total": 89.97,
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "contract_dep")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, make_container())

        orders = kwargs["orders"]
        assert orders.total == 89.97

        if dag is not None:
            await dag.teardown()


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 4: Edge Cases
# ═══════════════════════════════════════════════════════════════════════════


class TestDepEdgeCases:
    """Edge cases for Dep default resolution."""

    @pytest.mark.asyncio
    async def test_dep_result_not_contaminated_by_body_fields(self):
        """Even if body contains fields matching the Dep-provided Contract, Dep wins."""
        body = {
            "items": [],
            "total": 0,
            # These fields match SimpleContract fields but should NOT affect Dep result
            "slug": "MALICIOUS-OVERRIDE",
            "title": "SHOULD-NOT-APPEAR",
        }
        req = make_request(body=body)
        ctx = RequestCtx(request=req)

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "contract_dep")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, make_container())

        article = kwargs["article"]
        assert article.slug == "from-dep"
        assert article.validated_data["title"] == "Dep Title"
        assert article.slug != "MALICIOUS-OVERRIDE"

        if dag is not None:
            await dag.teardown()

    @pytest.mark.asyncio
    async def test_dep_with_empty_body(self):
        """Dep resolution works even when request body is empty."""
        req = make_request(body={})
        ctx = RequestCtx(request=req)

        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(DepPrecedenceController, "test:DepPrec")
        route = next(r for r in meta.routes if r.handler_name == "dep_only")

        kwargs, dag = await engine._bind_parameters(route, req, ctx, {}, make_container())

        assert kwargs["label"] == "injected-string"

        if dag is not None:
            await dag.teardown()

    def test_annotated_dep_still_classified_as_dep(self):
        """Annotated[T, Dep(...)] style still works (regression guard)."""

        class AnnotatedDepCtrl(Controller):
            @POST("/annotated")
            async def handler(
                self,
                ctx: RequestCtx,
                article: Annotated[SimpleContract, Dep(get_simple_async)],
            ):
                return {}

        meta = extract_controller_metadata(AnnotatedDepCtrl, "test:AnnotDep")
        route = meta.routes[0]
        article_param = next(p for p in route.parameters if p.name == "article")
        assert article_param.source == "dep"


# ═══════════════════════════════════════════════════════════════════════════
#  SECTION 5: RequestDAG Direct Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestRequestDAGDepResolution:
    """Direct tests for RequestDAG resolving Dep descriptors."""

    @pytest.mark.asyncio
    async def test_async_dep_resolved_via_dag(self):
        """Dep(async_callable) is resolved through the DAG."""
        container = make_container()
        dag = RequestDAG(container, request=None)

        dep = Dep(get_simple_async)
        result = await dag.resolve(dep, SimpleContract)

        assert isinstance(result, SimpleContract)
        assert result.slug == "from-dep"

        await dag.teardown()

    @pytest.mark.asyncio
    async def test_sync_dep_resolved_via_dag(self):
        """Dep(sync_callable) is resolved through the DAG."""
        container = make_container()
        dag = RequestDAG(container, request=None)

        dep = Dep(get_simple_sync)
        result = await dag.resolve(dep, SimpleContract)

        assert isinstance(result, SimpleContract)
        assert result.slug == "sync-dep"

        await dag.teardown()

    @pytest.mark.asyncio
    async def test_dep_caching_in_dag(self):
        """Dep results are cached within a single request DAG."""
        call_count = 0

        async def counting_dep() -> str:
            nonlocal call_count
            call_count += 1
            return f"result-{call_count}"

        container = make_container()
        dag = RequestDAG(container, request=None)

        dep = Dep(counting_dep, cached=True)
        result1 = await dag.resolve(dep, str)
        result2 = await dag.resolve(dep, str)

        assert result1 == result2
        assert call_count == 1

        await dag.teardown()

    @pytest.mark.asyncio
    async def test_dep_uncached_resolves_each_time(self):
        """Dep(cached=False) is resolved fresh each time."""
        call_count = 0

        async def counting_dep() -> str:
            nonlocal call_count
            call_count += 1
            return f"result-{call_count}"

        container = make_container()
        dag = RequestDAG(container, request=None)

        dep = Dep(counting_dep, cached=False)
        result1 = await dag.resolve(dep, str)
        result2 = await dag.resolve(dep, str)

        assert result1 != result2
        assert call_count == 2

        await dag.teardown()


# ═══════════════════════════════════════════════════════════════════════════
#  Test Annotated Extraction (Header, Query, Body, Dep) with Contracts
# ═══════════════════════════════════════════════════════════════════════════


class OrderContract(Contract):
    total: float
    items: list[str]


class ArticleContract(Contract):
    id: int
    title: str


from aquilia.di.dep import Body, Header, Query


# Define dependency provider returning a Contract at module scope
async def get_article(
    article_id: Annotated[int, Query("article_id")],
) -> ArticleContract:
    # Simulated db lookup
    bp = ArticleContract(data={"id": article_id, "title": "Aquilia Guide"})
    bp.is_sealed(raise_fault=True)
    return bp


# Define Controller at module scope
class BriefController(Controller):
    @POST("/order")
    async def order(
        self,
        ctx: RequestCtx,
        orders: OrderContract,
        header: Annotated[str, Header("content-type")],
        article: ArticleContract = Dep(get_article),
    ):
        return {
            "header": header,
            "order_total": orders.total,
            "item_count": len(orders.items),
            "article": {
                "id": article.id,
                "title": article.title,
            },
        }


class UserProfile(Contract):
    username: str
    email: str


async def get_user_profile(
    profile: Annotated[UserProfile, Body()],
) -> UserProfile:
    return profile


class TestAnnotatedExtractorDI:
    """Covers extraction using Annotated[T, Header/Query/Body] and Dep containing Contracts."""

    @pytest.mark.asyncio
    async def test_controller_header_query_body_and_dep_with_contracts(self):
        from aquilia.controller.engine import ControllerEngine
        from aquilia.controller.metadata import extract_controller_metadata

        # Build mock request
        body_bytes = json.dumps({"total": 99.9, "items": ["book", "pen"]}).encode("utf-8")
        headers = {
            "content-type": "application/json",
            "content-length": str(len(body_bytes)),
        }
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/order",
            "headers": [(k.encode("utf-8"), v.encode("utf-8")) for k, v in headers.items()],
            "query_string": b"article_id=42",
        }

        async def receive():
            return {
                "type": "http.request",
                "body": body_bytes,
                "more_body": False,
            }

        req = Request(scope, receive)
        ctx = RequestCtx(req)
        req.state["container"] = make_container()

        # Engine execution with ControllerFactory
        engine = ControllerEngine(ControllerFactory())
        meta = extract_controller_metadata(BriefController, "tests:BriefController")
        route_meta = meta.get_route("POST", "/order")

        assert route_meta is not None

        # Verify metadata source classifications
        sources = {p.name: p.source for p in route_meta.parameters}
        assert sources["orders"] == "body"
        assert sources["header"] == "dep"
        assert sources["article"] == "dep"

        # Execute parameter binding & calling
        kwargs, _ = await engine._bind_parameters(
            route_meta,
            req,
            ctx,
            path_params={},
            container=req.state["container"],
        )

        assert kwargs["header"] == "application/json"
        assert isinstance(kwargs["orders"], OrderContract)
        assert kwargs["orders"].total == 99.9
        assert isinstance(kwargs["article"], ArticleContract)
        assert kwargs["article"].id == 42
        assert kwargs["article"].title == "Aquilia Guide"

        # Safe call execution
        controller_instance = BriefController()
        result = await engine._safe_call(controller_instance.order, ctx, **kwargs)
        assert result == {
            "header": "application/json",
            "order_total": 99.9,
            "item_count": 2,
            "article": {
                "id": 42,
                "title": "Aquilia Guide",
            },
        }

    @pytest.mark.asyncio
    async def test_sub_dependency_annotated_body_contract_extraction(self):
        container = make_container()
        body_bytes = json.dumps({"username": "alex", "email": "alex@example.com"}).encode("utf-8")
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [(b"content-type", b"application/json")],
        }

        async def receive():
            return {
                "type": "http.request",
                "body": body_bytes,
                "more_body": False,
            }

        req = Request(scope, receive)
        dag = RequestDAG(container, request=req)

        dep = Dep(get_user_profile)
        resolved = await dag.resolve(dep, UserProfile)
        assert isinstance(resolved, UserProfile)
        assert resolved.username == "alex"
        assert resolved.email == "alex@example.com"

        await dag.teardown()
