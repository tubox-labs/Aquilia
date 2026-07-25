"""
Brutal regression test suite for Annotated[Any, Inject("token")] DI resolution and RequestDAG.
"""

from typing import Annotated, Any

import pytest

from aquilia.di import (
    Container,
    Dep,
    Inject,
    RequestDAG,
    auto_inject,
    inject,
)


class CrossAppService:
    def __init__(self, name: str = "cross_app"):
        self.name = name

    def get_status(self) -> str:
        return "active"


class UserRepo:
    def __init__(self):
        self.driver = "sql"


class ConsumerService:
    def __init__(
        self,
        cross_app: Annotated[Any, Inject("modules.auth.services:CrossAppService")],
    ):
        self.cross_app = cross_app


@pytest.mark.asyncio
async def test_annotated_string_token_resolve_sync_and_async():
    container = Container()
    svc = CrossAppService("auth_service")
    await container.register_instance("modules.auth.services:CrossAppService", svc)

    # Resolve async
    resolved_async = await container.resolve_async(
        Annotated[Any, Inject("modules.auth.services:CrossAppService")]
    )
    assert resolved_async is svc
    assert resolved_async.get_status() == "active"

    # Resolve sync
    resolved_sync = container.resolve(
        Annotated[Any, Inject("modules.auth.services:CrossAppService")]
    )
    assert resolved_sync is svc


@pytest.mark.asyncio
async def test_annotated_with_inject_factory_function():
    container = Container()
    svc = CrossAppService("auth_service")
    await container.register_instance("modules.auth.services:CrossAppService", svc)

    # Test inject() helper function
    resolved = await container.resolve_async(
        Annotated[Any, inject("modules.auth.services:CrossAppService")]
    )
    assert resolved is svc


@pytest.mark.asyncio
async def test_annotated_type_and_tags_and_optional():
    container = Container()

    repo_primary = UserRepo()
    repo_primary.driver = "primary_db"

    repo_replica = UserRepo()
    repo_replica.driver = "replica_db"

    await container.register_instance(UserRepo, repo_primary, tag="primary")
    await container.register_instance(UserRepo, repo_replica, tag="replica")

    # Tagged resolution via Annotated
    res_primary = await container.resolve_async(Annotated[UserRepo, Inject(tag="primary")])
    assert res_primary.driver == "primary_db"

    res_replica = await container.resolve_async(Annotated[UserRepo, Inject(tag="replica")])
    assert res_replica.driver == "replica_db"

    # Optional resolution when missing
    res_opt = await container.resolve_async(
        Annotated[Any, Inject("non_existent_token", optional=True)]
    )
    assert res_opt is None


@pytest.mark.asyncio
async def test_direct_inject_instance_as_token():
    container = Container()
    svc = CrossAppService("direct_inject")
    await container.register_instance("modules.auth.services:CrossAppService", svc)

    inject_marker = Inject("modules.auth.services:CrossAppService")

    assert container.is_registered(inject_marker)

    resolved = await container.resolve_async(inject_marker)
    assert resolved is svc


@pytest.mark.asyncio
async def test_class_provider_constructor_injection_with_annotated_string_token():
    container = Container()
    svc = CrossAppService("auth_service")
    await container.register_instance("modules.auth.services:CrossAppService", svc)

    # Register ConsumerService class provider
    container.bind(ConsumerService, ConsumerService)

    consumer = await container.resolve_async(ConsumerService)
    assert isinstance(consumer, ConsumerService)
    assert consumer.cross_app is svc
    assert consumer.cross_app.name == "auth_service"


@pytest.mark.asyncio
async def test_factory_provider_with_annotated_string_token():
    container = Container()
    svc = CrossAppService("auth_service")
    await container.register_instance("modules.auth.services:CrossAppService", svc)

    async def create_client(
        cross_app: Annotated[Any, Inject("modules.auth.services:CrossAppService")]
    ):
        return {"client_for": cross_app.name}

    from aquilia.di.providers import FactoryProvider

    provider = FactoryProvider(create_client)
    container.register(provider)

    res = await container.resolve_async(
        f"{create_client.__module__}.{create_client.__qualname__}"
    )
    assert res == {"client_for": "auth_service"}


@pytest.mark.asyncio
async def test_request_dag_resolve_annotated_string_token():
    container = Container()
    svc = CrossAppService("dag_service")
    await container.register_instance("modules.auth.services:CrossAppService", svc)

    dag = RequestDAG(container)

    # Resolve bare Dep container lookup with Annotated string token
    res = await dag.resolve(
        Dep(), Annotated[Any, Inject("modules.auth.services:CrossAppService")]
    )
    assert res is svc


@pytest.mark.asyncio
async def test_auto_inject_with_annotated_string_token():
    container = Container()
    svc = CrossAppService("auto_inject_service")
    await container.register_instance("modules.auth.services:CrossAppService", svc)

    from aquilia.di.compat import clear_request_container, set_request_container

    set_request_container(container)
    try:
        @auto_inject
        async def my_handler(
            cross_app: Annotated[Any, Inject("modules.auth.services:CrossAppService")]
        ):
            return cross_app.name

        res = await my_handler()
        assert res == "auto_inject_service"
    finally:
        clear_request_container()


@pytest.mark.asyncio
async def test_cross_app_linked_container_annotated_token():
    auth_container = Container()
    auth_svc = CrossAppService("linked_auth_svc")
    await auth_container.register_instance("modules.auth.services:CrossAppService", auth_svc)

    billing_container = Container()
    billing_container.add_dependency_link("auth", auth_container)

    # Billing container resolves auth service from linked container
    resolved = await billing_container.resolve_async(
        Annotated[Any, Inject("modules.auth.services:CrossAppService")]
    )
    assert resolved is auth_svc
    assert resolved.name == "linked_auth_svc"


@pytest.mark.asyncio
async def test_user_reported_dashboard_controller_injection():
    from aquilia.controller import Controller
    from aquilia.controller.factory import ControllerFactory
    from aquilia.faults.integrations.di import patch_di_container

    patch_di_container()

    class DashboardService:
        pass

    class TemplateEngine:
        pass

    class DashboardController(Controller):
        prefix = "/"
        tags = ["dashboard"]

        def __init__(
            self,
            service: DashboardService,
            templates: TemplateEngine,
            cross_app: Annotated[Any, Inject("modules.auth.services:CrossAppService")],
        ) -> None:
            self.service = service or DashboardService
            self.templates = templates
            self.cross_app = cross_app

    container = Container()
    cross_app_svc = CrossAppService("dashboard_cross_app")
    await container.register_instance("modules.auth.services:CrossAppService", cross_app_svc)
    await container.register_instance(DashboardService, DashboardService())
    await container.register_instance(TemplateEngine, TemplateEngine())

    factory = ControllerFactory(app_container=container)
    ctrl = await factory.create(DashboardController)
    assert ctrl.cross_app is cross_app_svc
    assert ctrl.cross_app.name == "dashboard_cross_app"


@pytest.mark.asyncio
async def test_importlib_dynamic_string_token_fallback():
    from aquilia.di.providers import ClassProvider

    class LocalDummy:
        pass

    container = Container()
    # Register Container class provider ONLY under class type
    provider = ClassProvider(LocalDummy, scope="app")
    container.register(provider)

    # Resolve using string import path token (not pre-registered as string)
    module_path = f"{LocalDummy.__module__}:{LocalDummy.__qualname__}"
    resolved = await container.resolve_async(Annotated[Any, Inject(module_path)])
    assert isinstance(resolved, LocalDummy)


class OuterNamespace:
    class NestedService:
        pass


@pytest.mark.asyncio
async def test_nested_class_importlib_dynamic_resolution():
    from aquilia.di.providers import ClassProvider

    container = Container()
    provider = ClassProvider(OuterNamespace.NestedService, scope="app")
    container.register(provider)

    # 1. Colon with nested dot: 'tests.test_di_annotated_inject_fix:OuterNamespace.NestedService'
    token_colon = f"{OuterNamespace.NestedService.__module__}:OuterNamespace.NestedService"
    resolved_colon = await container.resolve_async(Annotated[Any, Inject(token_colon)])
    assert isinstance(resolved_colon, OuterNamespace.NestedService)

    # 2. Pure dot format: 'tests.test_di_annotated_inject_fix.OuterNamespace.NestedService'
    token_dot = f"{OuterNamespace.NestedService.__module__}.OuterNamespace.NestedService"
    resolved_dot = await container.resolve_async(Annotated[Any, Inject(token_dot)])
    assert isinstance(resolved_dot, OuterNamespace.NestedService)


@pytest.mark.asyncio
async def test_multi_dot_last_separator_swap():
    from aquilia.di.providers import ClassProvider

    container = Container()
    provider = ClassProvider(OuterNamespace.NestedService, scope="app")
    # Register explicitly under colon format
    colon_token = f"{OuterNamespace.NestedService.__module__}:OuterNamespace.NestedService"
    await container.register_instance(colon_token, OuterNamespace.NestedService())

    # Request via multi-dot format: 'tests.test_di_annotated_inject_fix.OuterNamespace.NestedService'
    # Swapping last dot transforms it to colon_token above
    dot_token = f"{OuterNamespace.NestedService.__module__}.OuterNamespace.NestedService"
    resolved = await container.resolve_async(Annotated[Any, Inject(dot_token)])
    assert isinstance(resolved, OuterNamespace.NestedService)
