"""
Tests for deep integration between Aquilia's DI system (RequestDAG/Dep)
and Aquilia's Blueprint system.
"""

import pytest
import asyncio
from typing import Annotated

from aquilia.di.core import Container
from aquilia.di.request_dag import RequestDAG
from aquilia.di.dep import Dep, Header, Query, Body
from aquilia.blueprints.core import Blueprint
from aquilia.blueprints.facets import TextFacet, IntFacet
from aquilia.blueprints.exceptions import SealFault

pytestmark = pytest.mark.asyncio(loop_scope="function")

# --- Dummy Request Setup ---

class DummyRequest:
    def __init__(self, headers=None, query=None, body=None):
        self.headers = headers or {}
        self.query_params = query or {}
        self._body = body or {}
        self._body_cache = self._body

    async def json(self):
        return self._body

    def query_param(self, name):
        return self.query_params.get(name)

    def content_type(self):
        return "application/json"
        
    def is_json(self):
        return True

# --- Test Blueprints ---

class PaginationBlueprint(Blueprint):
    """A blueprint that extracts its data completely from Query params."""
    page = IntFacet(default=Query("page", default=1))
    limit = IntFacet(default=Query("limit", default=25), max_value=100)
    
class MetadataBlueprint(Blueprint):
    """A blueprint that mixes Header, Query, and Body."""
    user_agent = TextFacet(default=Header("User-Agent", required=True))
    trace_id = TextFacet(default=Header("X-Trace-Id", default="no-trace", required=False), required=False)
    search = TextFacet(default=Query("q", default=""), required=False)
    payload_name = TextFacet(required=True)  # implicitly from body


# --- Tests ---

class TestBlueprintDIIntegration:
    async def test_request_dag_resolves_blueprint(self):
        """Test RequestDAG automatically instantiating a Blueprint subclass."""
        container = Container(scope="app")
        request = DummyRequest(
            query={"page": "2", "limit": "50"}
        )
        dag = RequestDAG(container, request)

        # A dummy handler that depends on the blueprint
        async def my_handler(params: PaginationBlueprint):
            return params

        dep = Dep(my_handler)
        
        result = await dag.resolve(dep, type(None))
        
        assert isinstance(result, PaginationBlueprint)
        assert result.validated_data["page"] == 2
        assert result.validated_data["limit"] == 50
        
    async def test_blueprint_instance_injection(self):
        """Test that injecting a blueprint gives the instance."""
        container = Container(scope="app")
        request = DummyRequest(
            query={"page": "3", "limit": "10"}
        )
        dag = RequestDAG(container, request)

        async def my_handler(pagination_blueprint: PaginationBlueprint):
            return pagination_blueprint

        dep = Dep(my_handler)
        result = await dag.resolve(dep, type(None))
        
        assert isinstance(result, PaginationBlueprint)
        assert result.validated_data["page"] == 3
        assert result.validated_data["limit"] == 10

    async def test_blueprint_mixed_extraction(self):
        """Test extraction from Header, Query, and Body simultaneously."""
        container = Container(scope="app")
        request = DummyRequest(
            headers={"user-agent": "Aquilia-Agent/1.0"},
            query={"q": "hello world"},
            body={"payload_name": "My Payload"}
        )
        dag = RequestDAG(container, request)

        async def metadata_handler(data: MetadataBlueprint):
            return data

        dep = Dep(metadata_handler)
        try:
            result = await dag.resolve(dep, type(None))
        except Exception as exc:
            if hasattr(exc, "errors"):
                print("Validation Errors:", exc.errors)
            raise exc
        
        assert isinstance(result, MetadataBlueprint)
        assert result.validated_data["user_agent"] == "Aquilia-Agent/1.0"
        assert result.validated_data["search"] == "hello world"
        assert result.validated_data["payload_name"] == "My Payload"
        assert result.validated_data["trace_id"] == "no-trace"  # from default

    async def test_blueprint_missing_required_extraction(self):
        """Test missing required Header throws validation error directly in Blueprint."""
        container = Container(scope="app")
        # Missing user-agent header
        request = DummyRequest(
            body={"payload_name": "My Payload"}
        )
        dag = RequestDAG(container, request)

        async def failing_handler(data: MetadataBlueprint):
            return data

        dep = Dep(failing_handler)
        
        with pytest.raises(SealFault) as exc:
            await dag.resolve(dep, type(None))
            
        assert "user_agent" in exc.value.field_errors
