import datetime
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Annotated

import pytest

from aquilia._datastructures import MultiDict
from aquilia.blueprints import Blueprint
from aquilia.blueprints.integration import bind_blueprint_to_request
from aquilia.controller import GET, Controller
from aquilia.controller.engine import ControllerEngine
from aquilia.controller.factory import ControllerFactory
from aquilia.controller.metadata import extract_controller_metadata
from aquilia.di import Container
from aquilia.di.dep import Cookie, Path, Query


class StatusEnum(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class PriorityEnum(IntEnum):
    HIGH = 1
    LOW = 2


class SearchBlueprint(Blueprint):
    title: str
    tags: list[str]
    nums: set[int]
    priority: PriorityEnum


class MockRequest:
    def __init__(self, query_params=None, headers=None, cookies=None, path_params=None, body=None):
        self.query_params = query_params or MultiDict()
        self.headers = headers or {}
        self.cookies = cookies or {}
        self.path_params = path_params or {}
        self._body = body or {}
        self.method = "GET"
        self.state = {}

    def cookie(self, name):
        return self.cookies.get(name)

    def query_param(self, name):
        return self.query_params.get(name)

    async def json(self):
        return self._body

    async def form(self):
        return self._body


@pytest.mark.asyncio
async def test_blueprint_from_query_params():
    qps = MultiDict()
    qps.add("title", "Aquilia Unified")
    qps.add("tags", "python")
    qps.add("tags", "di")
    qps.add("nums", "42")
    qps.add("nums", "43")
    qps.add("priority", "1")  # Coerces to PriorityEnum.HIGH (IntEnum)

    req = MockRequest(query_params=qps)
    bp = await bind_blueprint_to_request(SearchBlueprint, req)

    assert bp.is_sealed() is True
    assert bp.title == "Aquilia Unified"
    assert bp.tags == ["python", "di"]
    assert bp.nums == {42, 43}
    assert bp.priority == PriorityEnum.HIGH


@pytest.mark.asyncio
async def test_di_parameter_casting_and_extractors():
    class TestController(Controller):
        @GET("/test/{id}")
        async def handler(
            self,
            id: Annotated[int, Path()],
            dt: Annotated[datetime.datetime, Query("date")],
            dec: Annotated[Decimal, Query("dec")],
            active: Annotated[bool, Query("active")],
            items: Annotated[list[int], Query("item")],
            tags: Annotated[set[str], Query("tag")],
            pair: Annotated[tuple[float, ...], Query("pair")],
            status: Annotated[StatusEnum, Query("status")],
            cookie_val: Annotated[str, Cookie("session_id", default="guest")],
        ):
            return {
                "id": id,
                "dt": dt,
                "dec": dec,
                "active": active,
                "items": items,
                "tags": tags,
                "pair": pair,
                "status": status,
                "cookie_val": cookie_val,
            }

    qps = MultiDict()
    qps.add("date", "2026-06-29T12:00:00Z")  # Zulu format DateTime
    qps.add("dec", "12.34")
    qps.add("active", "yes")  # Truthy boolean coercion
    qps.add("item", "1")
    qps.add("item", "2")
    qps.add("tag", "a")
    qps.add("tag", "b")
    qps.add("pair", "1.5")
    qps.add("pair", "2.5")
    qps.add("status", "ACTIVE")

    req = MockRequest(query_params=qps, path_params={"id": "999"}, cookies={"session_id": "token-123"})

    compiler = ControllerEngine(ControllerFactory())
    meta = extract_controller_metadata(TestController, "test:Controller")
    route_meta = meta.routes[0]

    container = Container()
    ctx = type("RequestCtx", (), {"request": req})()

    kwargs, _ = await compiler._bind_parameters(route_meta, req, ctx, path_params={"id": "999"}, container=container)

    assert kwargs["id"] == 999
    assert kwargs["dt"] == datetime.datetime(2026, 6, 29, 12, 0, tzinfo=datetime.timezone.utc)
    assert kwargs["dec"] == Decimal("12.34")
    assert kwargs["active"] is True
    assert kwargs["items"] == [1, 2]
    assert kwargs["tags"] == {"a", "b"}
    assert kwargs["pair"] == (1.5, 2.5)
    assert kwargs["status"] == StatusEnum.ACTIVE
    assert kwargs["cookie_val"] == "token-123"
