import pytest
from typing import Any

from aquilia.controller import (
    Resource,
    ReadOnlyResource,
    CRUDResource,
    action,
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
)
from aquilia.controller.metadata import extract_controller_metadata

class User:
    pass

class BaseUserResource(Resource[User]):
    prefix = "/users"
    
    @action(["POST"], detail=True)
    async def activate(self, ctx: Any, id: int) -> dict:
        return {"status": "active"}

class CustomIdResource(Resource[User]):
    prefix = "/custom"
    id_type = "uuid"
    
    async def list(self, ctx: Any) -> list:
        return []
        
    async def retrieve(self, ctx: Any, id: str) -> dict:
        return {}
        
    @action(detail=True, url_path="deactivate")
    async def deactivate(self, ctx: Any, id: str) -> dict:
        return {}

class FullCRUDResource(CRUDResource[User]):
    prefix = "/full"
    
    async def list(self, ctx: Any) -> list: return []
    async def retrieve(self, ctx: Any, id: int) -> dict: return {}
    async def create(self, ctx: Any) -> dict: return {}
    async def update(self, ctx: Any, id: int) -> dict: return {}
    async def partial_update(self, ctx: Any, id: int) -> dict: return {}
    async def destroy(self, ctx: Any, id: int) -> None: pass

class OnlyReadResource(ReadOnlyResource[User]):
    prefix = "/read"
    
    async def list(self, ctx: Any) -> list: return []
    async def retrieve(self, ctx: Any, id: int) -> dict: return {}

def test_resource_generates_no_routes_without_methods():
    meta = extract_controller_metadata(BaseUserResource, "tests")
    routes = meta.routes
    assert len(routes) == 1
    r = routes[0]
    assert r.http_method == "POST"
    assert r.full_path == "/users/{id:int}/activate"
    assert r.handler_name == "activate"

def test_custom_id_resource():
    meta = extract_controller_metadata(CustomIdResource, "tests")
    routes = { (r.http_method, r.full_path): r.handler_name for r in meta.routes }
    
    assert len(routes) == 3
    assert ("GET", "/custom") in routes
    assert ("GET", "/custom/{id:uuid}") in routes
    assert ("GET", "/custom/{id:uuid}/deactivate") in routes

def test_crud_resource():
    meta = extract_controller_metadata(FullCRUDResource, "tests")
    routes = { (r.http_method, r.full_path): r.handler_name for r in meta.routes }
    
    assert len(routes) == 6
    assert ("GET", "/full") in routes
    assert ("GET", "/full/{id:int}") in routes
    assert ("POST", "/full") in routes
    assert ("PUT", "/full/{id:int}") in routes
    assert ("PATCH", "/full/{id:int}") in routes
    assert ("DELETE", "/full/{id:int}") in routes
    
    assert routes[("GET", "/full")] == "list"
    assert routes[("GET", "/full/{id:int}")] == "retrieve"

def test_readonly_resource():
    meta = extract_controller_metadata(OnlyReadResource, "tests")
    routes = { (r.http_method, r.full_path): r.handler_name for r in meta.routes }
    
    assert len(routes) == 2
    assert ("GET", "/read") in routes
    assert ("GET", "/read/{id:int}") in routes

def test_compiler_compiles_resource():
    from aquilia.controller.compiler import ControllerCompiler
    compiler = ControllerCompiler()
    compiled = compiler.compile_controller(FullCRUDResource)
    
    assert len(compiled.routes) == 6
    paths = [r.full_path for r in compiled.routes]
    assert "/full/" in paths or "/full" in paths
    assert "/full/{id:int}" in paths
