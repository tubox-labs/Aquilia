"""
Controller Engine - Executes controller methods with full integration.

Integrates with:
- DI system for controller instantiation
- Auth system for identity binding
- Session system for session state
- Flow pipeline for guard/transform/hook execution
- Effect system for automatic effect lifecycle
- Middleware for pipeline execution
- Faults for error handling
- Clearance system for declarative access control
- Throttling / rate limiting
- Interceptors (before/after handler)
- Exception filters (structured error handling)
- Handler execution timeouts
"""

import asyncio
import contextlib
import inspect
import logging
from typing import Any

from ..di import Container
from ..request import Request
from ..response import Response
from .base import Controller, RequestCtx, _reset_current_request_ctx, _set_current_request_ctx
from .compiler import CompiledRoute
from .factory import ControllerFactory, InstantiationMode


class ControllerEngine:
    """
    Executes controller methods with complete integration.

    Responsibilities:
    - Instantiate controllers via DI
    - Build RequestCtx with auth, session, state
    - Execute pipelines (class-level + method-level)
    - Bind path/query/body parameters
    - Handle errors via faults system
    - Lifecycle management
    - Throttle enforcement
    - Interceptor before/after hooks
    - Exception filter dispatch
    - Handler execution timeouts
    """

    # Class-level caches shared across instances
    _signature_cache: dict[Any, inspect.Signature] = {}
    _pipeline_param_cache: dict[int, set] = {}  # id(callable) -> set of param names
    _has_lifecycle_hooks: dict[type, tuple] = {}  # class -> (has_on_request, has_on_response)
    _simple_route_cache: dict[int, bool] = {}  # id(route) -> is_simple
    _clearance_cache: dict[int, Any] = {}  # id(route) -> merged Clearance or None

    def __init__(
        self,
        factory: ControllerFactory,
        enable_lifecycle: bool = True,
        fault_engine: Any | None = None,
        effect_registry: Any | None = None,
        clearance_engine: Any | None = None,
    ):
        self.factory = factory
        self.enable_lifecycle = enable_lifecycle
        self.fault_engine = fault_engine
        self.effect_registry = effect_registry
        self.clearance_engine = clearance_engine
        self.logger = logging.getLogger("aquilia.controller.engine")
        self._lifecycle_initialized: set[type] = set()

    async def execute(
        self,
        route: CompiledRoute,
        request: Request,
        path_params: dict[str, Any],
        container: Container,
    ) -> Response:
        """
        Execute a controller route.

        Performance (v2):
        - Fast path for monkeypatched handlers (no lifecycle, no DI).
        - Skip lifecycle init check for per-request controllers.
        - Build RequestCtx inline without extra method call for simple cases.
        - Cache inspect.signature results via _bind_parameters.

        v3 additions:
        - Throttle enforcement (class + route level)
        - Interceptor before/after hooks
        - Exception filter dispatch
        - Handler execution timeouts
        - Request body size limit enforcement
        """
        controller_class = route.controller_class
        route_metadata = route.route_metadata

        # Fast path: monkeypatched handler (OpenAPI docs, admin routes, etc.)
        if hasattr(route, "handler") and callable(route.handler):
            ctx = RequestCtx(
                request=request,
                identity=request.state.get("identity"),
                session=request.state.get("session"),
                auth=request.state.get("auth"),
                container=container,
                state=request.state,
            )
            ctx_token = _set_current_request_ctx(ctx)
            try:
                # Inject any path params the handler declares as positional args
                if path_params:
                    import inspect as _inspect

                    try:
                        sig = _inspect.signature(route.handler)
                        extra = {k: v for k, v in path_params.items() if k in sig.parameters}
                    except (ValueError, TypeError):
                        extra = {}
                    result = await route.handler(request, ctx, **extra)
                else:
                    result = await route.handler(request, ctx)
                return self._to_response(result)
            finally:
                _reset_current_request_ctx(ctx_token)

        # Build RequestCtx
        ctx = RequestCtx(
            request=request,
            identity=request.state.get("identity"),
            session=request.state.get("session"),
            auth=request.state.get("auth"),
            container=container,
            state=request.state,
        )
        ctx_token = _set_current_request_ctx(ctx)

        try:
            # ── Throttle enforcement ──
            throttle_response = self._check_throttle(controller_class, route_metadata, request)
            if throttle_response is not None:
                return throttle_response

            # ── Body size limit enforcement ──
            max_body = getattr(controller_class, "max_body_size", 0)
            if max_body > 0:
                content_length = 0
                if hasattr(request, "headers"):
                    hdrs = request.headers
                    cl = hdrs.get("content-length") if hasattr(hdrs, "get") else None
                    if cl:
                        with contextlib.suppress(ValueError, TypeError):
                            content_length = int(cl)
                if content_length > max_body:
                    from ..faults.domains import PayloadTooLargeFault

                    raise PayloadTooLargeFault(
                        detail=f"Request body too large ({content_length} bytes, max {max_body})",
                    )

            # Singleton lifecycle init (once per controller class)
            is_singleton = getattr(controller_class, "instantiation_mode", "per_request") == "singleton"
            if self.enable_lifecycle and is_singleton and controller_class not in self._lifecycle_initialized:
                await self._init_controller_lifecycle(controller_class, container)
                self._lifecycle_initialized.add(controller_class)

            # Instantiate controller
            controller = await self.factory.create(
                controller_class,
                mode=InstantiationMode.PER_REQUEST,
                request_container=container,
                ctx=ctx,
            )

            # Execute class-level pipeline via FlowPipeline
            if route.controller_metadata.pipeline:
                pipeline_result = await self._execute_flow_pipeline(
                    route.controller_metadata.pipeline,
                    request,
                    ctx,
                    controller,
                    pipeline_name=f"{controller_class.__name__}.class_pipeline",
                )
                if isinstance(pipeline_result, Response):
                    return pipeline_result

            # Execute method-level pipeline via FlowPipeline
            if route_metadata.pipeline:
                pipeline_result = await self._execute_flow_pipeline(
                    route_metadata.pipeline,
                    request,
                    ctx,
                    controller,
                    pipeline_name=f"{controller_class.__name__}.{route_metadata.handler_name}",
                )
                if isinstance(pipeline_result, Response):
                    return pipeline_result

            # Get handler method
            handler_method = getattr(controller, route_metadata.handler_name)

            # ── Clearance evaluation ──
            # Check class-level + method-level clearance requirements
            clearance_result = await self._evaluate_clearance(
                route,
                controller_class,
                handler_method,
                request,
                ctx,
            )
            if isinstance(clearance_result, Response):
                return clearance_result

            # ── Fast path for simple handlers ──
            # Handlers with no pipeline, no blueprint, and only ctx/path params
            # can skip the full _bind_parameters machinery.
            route_id = id(route)
            is_simple = ControllerEngine._simple_route_cache.get(route_id)
            if is_simple is None:
                params = route_metadata.parameters
                has_blueprint = getattr(route_metadata, "request_blueprint", None) or getattr(
                    route_metadata, "response_blueprint", None
                )
                has_filters_or_pagination = (
                    getattr(route_metadata, "filterset_class", None)
                    or getattr(route_metadata, "filterset_fields", None)
                    or getattr(route_metadata, "search_fields", None)
                    or getattr(route_metadata, "ordering_fields", None)
                    or getattr(route_metadata, "pagination_class", None)
                    or getattr(route_metadata, "renderer_classes", None)
                )
                is_simple = (
                    not route.controller_metadata.pipeline
                    and not route_metadata.pipeline
                    and not has_blueprint
                    and not has_filters_or_pagination
                    and (not params or all(p.name == "ctx" or p.source == "path" for p in params))
                )
                ControllerEngine._simple_route_cache[route_id] = is_simple

            if is_simple:
                # Direct call -- skip _bind_parameters, lifecycle hooks, blueprint
                try:
                    # Signature-aware call
                    sig = self._get_cached_signature(handler_method)
                    has_ctx = "ctx" in sig.parameters or "context" in sig.parameters

                    final_kwargs = {**path_params}
                    if has_ctx:
                        ctx_key = "ctx" if "ctx" in sig.parameters else "context"
                        final_kwargs[ctx_key] = ctx

                    # Run interceptors before
                    interceptors = self._get_interceptors(controller_class, route_metadata)
                    for interceptor in interceptors:
                        short = await self._safe_call(interceptor.before, ctx)
                        if isinstance(short, Response):
                            return short

                    result = await self._execute_with_timeout(
                        handler_method, controller_class, route_metadata, **final_kwargs
                    )

                    # Run interceptors after
                    for interceptor in reversed(interceptors):
                        result = await self._safe_call(interceptor.after, ctx, result)

                    return self._to_response(result)
                except Exception as e:
                    # Try exception filters first
                    filtered = await self._apply_exception_filters(e, controller_class, route_metadata, ctx)
                    if filtered is not None:
                        return filtered

                    self.logger.error(
                        f"Error executing {controller_class.__name__}.{route_metadata.handler_name}: {e}",
                        exc_info=True,
                    )
                    if self.fault_engine:
                        try:
                            app_name = getattr(route, "app_name", None)
                            rid = request.state.get("request_id") if isinstance(request.state, dict) else None
                            await self.fault_engine.process(
                                e,
                                app=app_name,
                                route=route.full_path,
                                request_id=rid,
                            )
                        except Exception:
                            pass
                    raise

            # Bind parameters
            kwargs, request_dag = await self._bind_parameters(
                route_metadata,
                request,
                ctx,
                path_params,
                container,
            )

            # Execute handler
            try:
                # Check lifecycle hooks (cached per class)
                # We check if the method is actually OVERRIDDEN from Controller base,
                # since Controller defines on_request/on_response as no-ops.
                hooks = ControllerEngine._has_lifecycle_hooks.get(controller_class)
                if hooks is None:
                    has_on_request = "on_request" in controller_class.__dict__ or any(
                        "on_request" in B.__dict__
                        for B in controller_class.__mro__[1:]
                        if B is not Controller and B is not object
                    )
                    has_on_response = "on_response" in controller_class.__dict__ or any(
                        "on_response" in B.__dict__
                        for B in controller_class.__mro__[1:]
                        if B is not Controller and B is not object
                    )
                    hooks = (has_on_request, has_on_response)
                    ControllerEngine._has_lifecycle_hooks[controller_class] = hooks

                has_on_request, has_on_response = hooks

                if has_on_request:
                    await self._safe_call(controller.on_request, ctx)

                # Run interceptors before handler
                interceptors = self._get_interceptors(controller_class, route_metadata)
                for interceptor in interceptors:
                    short = await self._safe_call(interceptor.before, ctx)
                    if isinstance(short, Response):
                        return short

                # Signature-aware call
                sig = self._get_cached_signature(handler_method)
                has_ctx = "ctx" in sig.parameters or "context" in sig.parameters
                if has_ctx:
                    ctx_key = "ctx" if "ctx" in sig.parameters else "context"
                    kwargs[ctx_key] = ctx

                result = await self._execute_with_timeout(handler_method, controller_class, route_metadata, **kwargs)

                # Run interceptors after handler (in reverse order)
                for interceptor in reversed(interceptors):
                    result = await self._safe_call(interceptor.after, ctx, result)

                result = await self._apply_filters_and_pagination(result, route_metadata, request)
                result = self._apply_response_blueprint(result, route_metadata, ctx)
                response = self._apply_content_negotiation(result, route_metadata, request)
                if response is None:
                    response = self._to_response(result)

                if has_on_response:
                    await self._safe_call(controller.on_response, ctx, response)

                return response

            except Exception as e:
                # Try exception filters first
                filtered = await self._apply_exception_filters(e, controller_class, route_metadata, ctx)
                if filtered is not None:
                    return filtered

                self.logger.error(
                    f"Error executing {controller_class.__name__}.{route_metadata.handler_name}: {e}",
                    exc_info=True,
                )
                if self.fault_engine:
                    try:
                        app_name = getattr(route, "app_name", None)
                        rid = request.state.get("request_id") if isinstance(request.state, dict) else None
                        await self.fault_engine.process(
                            e,
                            app=app_name,
                            route=route.full_path,
                            request_id=rid,
                        )
                    except Exception:
                        pass
                raise
            finally:
                # Teardown generator deps from RequestDAG
                if request_dag is not None:
                    await request_dag.teardown()
        finally:
            _reset_current_request_ctx(ctx_token)

    async def _init_controller_lifecycle(
        self,
        controller_class: type,
        container: Container,
    ):
        """Initialize controller lifecycle hooks (startup)."""
        # Create temporary instance for lifecycle
        temp_instance = await self.factory.create(
            controller_class,
            mode=InstantiationMode.SINGLETON,
            request_container=container,
        )

        if hasattr(temp_instance, "on_startup"):
            try:
                # Build a minimal context for startup (no actual request yet)
                from ..request import Request as RequestClass

                dummy_request = RequestClass(
                    scope={"type": "http", "method": "GET", "path": "/", "query_string": b"", "headers": []},
                    receive=lambda: None,
                )
                ctx = RequestCtx(request=dummy_request, identity=None, session=None, container=container, state={})
                await self._safe_call(temp_instance.on_startup, ctx)
            except Exception as e:
                self.logger.error(
                    f"Error in on_startup for {controller_class.__name__}: {e}",
                    exc_info=True,
                )

    async def shutdown_controller(self, controller_class: type, container: Container):
        """Execute controller shutdown hooks."""
        if controller_class not in self._lifecycle_initialized:
            return

        temp_instance = await self.factory.create(
            controller_class,
            mode=InstantiationMode.SINGLETON,
            request_container=container,
        )

        if hasattr(temp_instance, "on_shutdown"):
            try:
                # Build a minimal context for shutdown (consistent with on_startup)
                from ..request import Request as RequestClass

                dummy_request = RequestClass(
                    scope={"type": "http", "method": "GET", "path": "/", "query_string": b"", "headers": []},
                    receive=lambda: None,
                )
                ctx = RequestCtx(request=dummy_request, identity=None, session=None, container=container, state={})
                await self._safe_call(temp_instance.on_shutdown, ctx)
            except Exception as e:
                self.logger.error(
                    f"Error in on_shutdown for {controller_class.__name__}: {e}",
                    exc_info=True,
                )

        self._lifecycle_initialized.discard(controller_class)

    async def _evaluate_clearance(
        self,
        route: CompiledRoute,
        controller_class: type,
        handler_method: Any,
        request: Request,
        ctx: RequestCtx,
    ) -> Response | None:
        """
        Evaluate clearance requirements for a controller route.

        Merges class-level and method-level clearance descriptors,
        then evaluates the merged clearance against the request context.

        Returns a 401/403 Response if denied, None if allowed.
        """
        from ..auth.clearance import (
            ClearanceEngine,
            _build_clearance_denied_response,
            build_merged_clearance,
        )

        # Cache clearance per route
        route_id = id(route)
        cached = ControllerEngine._clearance_cache.get(route_id)
        if cached is ...:  # Sentinel: already checked, no clearance
            return None

        if cached is None:
            merged = build_merged_clearance(controller_class, handler_method)
            if merged is None:
                ControllerEngine._clearance_cache[route_id] = ...
                return None
            ControllerEngine._clearance_cache[route_id] = merged
            cached = merged

        # Use configured engine or create one
        engine = self.clearance_engine or ClearanceEngine()

        identity = ctx.identity
        verdict = await engine.evaluate(cached, identity, request, ctx)

        if not verdict.granted:
            return _build_clearance_denied_response(cached, verdict, request)

        # Store verdict in ctx for downstream use
        if isinstance(ctx.state, dict):
            ctx.state["clearance_verdict"] = verdict

        return None

    async def _execute_flow_pipeline(
        self,
        pipeline_list: list[Any],
        request: Request,
        ctx: RequestCtx,
        controller: Controller,
        *,
        pipeline_name: str = "controller_pipeline",
    ) -> Response | None:
        """
        Execute a pipeline list via the FlowPipeline engine.

        Bridges controller pipeline syntax with the full Flow pipeline system.
        Handles FlowNodes, FlowGuards, and legacy callables.
        """
        from ..flow import (
            FlowContext,
            FlowStatus,
            from_pipeline_list,
        )

        # Convert pipeline list to FlowPipeline
        flow_pipeline = from_pipeline_list(pipeline_list, name=pipeline_name)

        if len(flow_pipeline) == 0:
            return None

        # Build FlowContext from RequestCtx
        flow_ctx = FlowContext(
            request=request,
            container=ctx.container,
            identity=ctx.identity,
            session=ctx.session,
            state=dict(ctx.state) if ctx.state else {},
        )

        # Inject controller into flow context state for pipeline nodes
        flow_ctx.set("controller", controller)

        # Execute via FlowPipeline
        result = await flow_pipeline.execute(flow_ctx, self.effect_registry)

        # Propagate state changes back to RequestCtx
        if result.context:
            for key, value in result.context.state.items():
                if key != "controller":
                    ctx.state[key] = value

            # Guards may set identity either on FlowContext.identity or in
            # FlowContext.state["identity"] (legacy dict-style guard behavior).
            propagated_identity = result.context.state.get("identity", result.context.identity)
            if propagated_identity is not None:
                ctx.identity = propagated_identity
                if isinstance(request.state, dict):
                    request.state["identity"] = propagated_identity

            if "authenticated" in result.context.state and isinstance(request.state, dict):
                request.state["authenticated"] = result.context.state["authenticated"]

            # Make acquired effects available in request state
            if result.context.effects and isinstance(request.state, dict):
                request.state["effects"] = result.context.effects

        # Handle result
        if result.status == FlowStatus.GUARDED:
            if result.value and isinstance(result.value, Response):
                return result.value
            if result.error:
                # Guard raised an exception -- re-raise for fault engine
                raise result.error
            from ..faults.domains import ForbiddenFault

            raise ForbiddenFault(
                detail=f"Pipeline guard blocked request in {pipeline_name}",
            )

        if result.status == FlowStatus.ERROR:
            if result.error:
                raise result.error
            from ..faults.domains import InternalServerErrorFault

            raise InternalServerErrorFault(
                detail=f"Pipeline error in {pipeline_name}",
            )

        if result.status == FlowStatus.TIMEOUT:
            from ..faults.domains import GatewayTimeoutFault

            raise GatewayTimeoutFault(
                detail=f"Pipeline timeout in {pipeline_name}",
            )

        # SUCCESS -- continue to handler
        return None

    async def _bind_parameters(
        self,
        route_metadata,
        request: Request,
        ctx: RequestCtx,
        path_params: dict[str, Any],
        container: Container,
    ) -> tuple[dict[str, Any], Any]:
        """
        Bind parameters from request to handler arguments.

        Returns:
            Tuple of (kwargs dict, RequestDAG or None).
            The DAG must be torndown after handler execution.

        Sources:
        - Path parameters
        - Query parameters
        - Request body (JSON/form)
        - DI container
        - Dep() descriptors (resolved via RequestDAG)
        - Special: ctx, request
        - **Blueprint subclasses**: Auto-parsed, cast+sealed from request body

        When a parameter is typed as a ``Blueprint`` subclass, the engine
        will:
        1. Parse the request body (JSON or form)
        2. Create the Blueprint with ``data=body, context={request, container}``
        3. Call ``is_sealed(raise_fault=True)``
        4. Inject the Blueprint instance or ``.validated_data``

        If the parameter name is ``blueprint`` or ends with ``_blueprint``
        or ``_bp``, the full Blueprint instance is injected. Otherwise,
        ``blueprint.validated_data`` is injected.

        If a ``request_blueprint`` is declared on the route decorator,
        it takes precedence and is used for body parsing.
        """
        kwargs = {}
        request_dag = None  # Lazy -- created only if handler uses Dep()

        # Check for request_blueprint from decorator metadata
        decorator_request_blueprint = getattr(route_metadata, "request_blueprint", None)
        if decorator_request_blueprint is None:
            raw_meta = getattr(route_metadata, "_raw_metadata", None)
            if raw_meta and isinstance(raw_meta, dict):
                decorator_request_blueprint = raw_meta.get("request_blueprint")

        # Track if body has been consumed by a blueprint
        _body_consumed = False
        _body_cache = None

        async def _get_body():
            nonlocal _body_cache
            if _body_cache is not None:
                return _body_cache
            try:
                _body_cache = await request.json()
            except Exception:
                try:
                    _body_cache = await request.form()
                except Exception:
                    _body_cache = {}
            return _body_cache

        for param in route_metadata.parameters:
            param_name = param.name

            # Skip ctx/context (injected directly in execute)
            if param_name in ("ctx", "context"):
                continue

            # ── Blueprint injection ──────────────────────────────────────
            # If the parameter type is a Blueprint subclass, auto-parse
            # the request body through it.
            param_is_blueprint = self._is_blueprint_class(param.type)

            use_blueprint = None

            if param_is_blueprint:
                use_blueprint = param.type
            elif (
                decorator_request_blueprint
                and self._is_blueprint_class(decorator_request_blueprint)
                and param.source == "body"
                and not _body_consumed
            ):
                use_blueprint = decorator_request_blueprint

            # ── Blueprint body binding ───────────────────────────────────
            if use_blueprint is not None and not _body_consumed:
                body = await _get_body()
                _body_consumed = True

                # Build context with request + container
                bp_context = {"request": request}
                if container:
                    bp_context["container"] = container
                if ctx.identity:
                    bp_context["identity"] = ctx.identity

                # Handle ProjectedRef (Blueprint["projection"])
                projection = None
                bp_cls = use_blueprint
                try:
                    from aquilia.blueprints.lenses import _ProjectedRef

                    if isinstance(use_blueprint, _ProjectedRef):
                        projection = use_blueprint.projection
                        bp_cls = use_blueprint.blueprint_cls
                except ImportError:
                    pass

                # Determine if PATCH → partial
                is_partial = request.method == "PATCH"

                bp_instance = bp_cls(
                    data=body,
                    partial=is_partial,
                    projection=projection,
                    context=bp_context,
                )
                bp_instance.is_sealed(raise_fault=True)

                # Inject the FULL Blueprint instance if:
                # 1. The parameter is explicitly typed as a Blueprint subclass
                # 2. The parameter name suggests it wants the instance
                inject_instance = (
                    param_is_blueprint
                    or param_name == "blueprint"
                    or param_name.endswith("_blueprint")
                    or param_name.endswith("_bp")
                )

                if inject_instance:
                    kwargs[param_name] = bp_instance
                else:
                    kwargs[param_name] = bp_instance.validated_data
                continue

            # Path parameters
            if param.source == "path":
                if param_name in path_params:
                    kwargs[param_name] = path_params[param_name]
                elif not param.required and param.default is not inspect.Parameter.empty:
                    kwargs[param_name] = param.default

            # Query parameters
            elif param.source == "query":
                value = request.query_param(param_name)
                if value is not None:
                    # Cast to expected type (SEC-CTRL-01: catch cast errors)
                    try:
                        kwargs[param_name] = self._cast_value(value, param.type)
                    except (ValueError, TypeError) as cast_err:
                        from ..faults.domains import RoutingFault

                        raise RoutingFault(
                            code="INVALID_QUERY_PARAM",
                            message=f"Invalid query parameter '{param_name}': {cast_err}",
                            public=True,
                            metadata={"param": param_name, "value": value},
                        ) from cast_err
                elif not param.required and param.default is not inspect.Parameter.empty:
                    kwargs[param_name] = param.default

            # Body (for POST/PUT/PATCH)
            elif param.source == "body":
                if request.method in ("POST", "PUT", "PATCH"):
                    try:
                        body = await _get_body()
                        # If the parameter type is a plain dict (Dict[str, Any]) or
                        # the body itself is not a dict, inject the whole body.
                        # Otherwise, if the body contains a key matching param_name,
                        # extract that field (legacy behaviour for named body fields).
                        import typing as _t
                        from typing import get_origin as _go

                        _raw_type = param.type
                        # Unwrap Optional[Dict] → Dict
                        try:
                            if _go(_raw_type) is _t.Union:
                                _args = _t.get_args(_raw_type)
                                _non_none = [a for a in _args if a is not type(None)]
                                if len(_non_none) == 1:
                                    _raw_type = _non_none[0]
                        except Exception:
                            pass
                        _is_dict_type = _go(_raw_type) is dict or _raw_type is dict
                        if _is_dict_type:
                            # Inject the full JSON body as the dict param
                            kwargs[param_name] = body if isinstance(body, dict) else {}
                        elif isinstance(body, dict) and param_name in body:
                            kwargs[param_name] = body[param_name]
                        elif not param.required and param.default is not inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                    except Exception:
                        if not param.required and param.default is not inspect.Parameter.empty:
                            kwargs[param_name] = param.default

            # Dep resolution (via RequestDAG)
            elif param.source == "dep":
                try:
                    from typing import Annotated, get_args, get_origin

                    from aquilia.di.dep import _extract_dep_from_annotation
                    from aquilia.di.request_dag import RequestDAG

                    dep_meta = _extract_dep_from_annotation(param.type)
                    if dep_meta is not None:
                        if request_dag is None:
                            request_dag = RequestDAG(container, request)
                        # Get base type from Annotated
                        base_type = param.type
                        if get_origin(param.type) is Annotated:
                            base_type = get_args(param.type)[0]
                        value = await request_dag.resolve(dep_meta, base_type)
                        kwargs[param_name] = value
                    else:
                        # Fallback to container resolve if Dep not extractable
                        resolve_token = param.type if param.type is not inspect.Parameter.empty else param_name
                        value = await container.resolve_async(resolve_token, optional=not param.required)
                        if value is not None:
                            kwargs[param_name] = value
                        elif not param.required and param.default is not inspect.Parameter.empty:
                            kwargs[param_name] = param.default
                except Exception:
                    if not param.required and param.default is not inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise

            # DI injection
            elif param.source == "di":
                try:
                    # For Session and Identity, we use optional=True so we can raise our own Faults
                    is_session_param = param_name == "session" or (
                        hasattr(param.type, "__name__") and param.type.__name__ == "Session"
                    )

                    is_identity_param = param_name == "identity" or (
                        hasattr(param.type, "__name__") and param.type.__name__ == "Identity"
                    )

                    is_optional = not param.required or is_session_param or is_identity_param

                    # Resolve by type if available, otherwise by name
                    resolve_token = param.type if param.type is not inspect.Parameter.empty else param_name
                    value = await container.resolve_async(resolve_token, optional=is_optional)

                    if is_session_param and value is None:
                        # Try to resolve session proactively
                        try:
                            from aquilia.sessions import SessionEngine

                            engine = await container.resolve_async(SessionEngine)
                            value = await engine.resolve(request)
                            # Update context and request for downstream handlers/decorators
                            ctx.session = value
                            request.state["session"] = value
                        except Exception:
                            pass

                    # ENFORCEMENT: If this is a Session, and it's None, but requested as required
                    # then raise SessionRequiredFault.
                    if value is None and param.required:
                        if is_session_param:
                            from aquilia.sessions.decorators import SessionRequiredFault

                            raise SessionRequiredFault()
                        elif is_identity_param:
                            from aquilia.auth.faults import AUTH_REQUIRED

                            raise AUTH_REQUIRED()

                    if value is not None:
                        kwargs[param_name] = value
                    elif not param.required and param.default is not inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                except Exception as e:
                    # Reraise session/auth faults
                    from aquilia.auth.faults import AUTH_REQUIRED
                    from aquilia.sessions.decorators import SessionRequiredFault

                    if isinstance(e, (SessionRequiredFault, AUTH_REQUIRED)):
                        raise

                    if not param.required and param.default is not inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        # Re-raise original error if it's not handled
                        raise

        return kwargs, request_dag

    def _cast_value(self, value: str, annotation: Any) -> Any:
        """Cast string value to target type.

        Raises BadRequestFault with a user-friendly message on bad input
        (SEC-CTRL-01: was previously uncaught).
        """
        try:
            if annotation is int or annotation == "int":
                return int(value)
            elif annotation is float or annotation == "float":
                return float(value)
            elif annotation is bool or annotation == "bool":
                return value.lower() in ("true", "1", "yes")
            else:
                return value
        except (ValueError, TypeError) as exc:
            from ..faults.domains import BadRequestFault

            raise BadRequestFault(
                message=(f"Invalid value {value!r} for expected type {getattr(annotation, '__name__', annotation)}"),
                detail=(f"Invalid value {value!r} for expected type {getattr(annotation, '__name__', annotation)}"),
            ) from exc

    _blueprint_base_class = None  # Cached Blueprint class

    def _is_blueprint_class(self, annotation: Any) -> bool:
        """Check if annotation is a Blueprint subclass or ProjectedRef."""
        if ControllerEngine._blueprint_base_class is None:
            try:
                from aquilia.blueprints.core import Blueprint

                ControllerEngine._blueprint_base_class = Blueprint
            except ImportError:
                ControllerEngine._blueprint_base_class = type(None)  # sentinel
                return False

        base = ControllerEngine._blueprint_base_class
        if base is type(None):
            return False

        # Check for ProjectedRef (Blueprint["projection"])
        try:
            from aquilia.blueprints.lenses import _ProjectedRef

            if isinstance(annotation, _ProjectedRef):
                return True
        except ImportError:
            pass

        return isinstance(annotation, type) and issubclass(annotation, base) and annotation is not base

    def _apply_response_blueprint(
        self,
        result: Any,
        route_metadata: Any,
        ctx: RequestCtx,
    ) -> Any:
        """Auto-mold handler return value via response_blueprint."""
        # Fast path: check direct attribute first
        response_blueprint = getattr(route_metadata, "response_blueprint", None)
        if response_blueprint is None:
            raw_meta = getattr(route_metadata, "_raw_metadata", None)
            if raw_meta and isinstance(raw_meta, dict):
                response_blueprint = raw_meta.get("response_blueprint")

        if response_blueprint is None:
            return result

        # Don't re-mold Response objects
        if isinstance(result, Response):
            return result

        try:
            from aquilia.blueprints.integration import render_blueprint_response

            many = isinstance(result, (list, tuple))
            return render_blueprint_response(
                response_blueprint,
                data=result,
                many=many,
            )
        except ImportError:
            self.logger.warning("Blueprint system not available. Returning raw result.")
            return result
        except Exception as e:
            self.logger.warning(f"Response Blueprint molding failed: {e}. Returning raw result.")
            return result

    async def _apply_filters_and_pagination(
        self,
        result: Any,
        route_metadata: Any,
        request: Request,
    ) -> Any:
        """
        Apply FilterSet / SearchFilter / OrderingFilter / Pagination
        to the handler's return value.

        Only activates when the route has filtering/pagination metadata
        AND the result is a list (or QuerySet-like object).
        """

        # Resolve metadata attrs (direct or _raw_metadata fallback)
        def _meta(key):
            v = getattr(route_metadata, key, None)
            if v is None:
                raw = getattr(route_metadata, "_raw_metadata", None)
                if raw and isinstance(raw, dict):
                    v = raw.get(key)
            return v

        filterset_class = _meta("filterset_class")
        filterset_fields = _meta("filterset_fields")
        search_fields = _meta("search_fields")
        ordering_fields = _meta("ordering_fields")
        pagination_class = _meta("pagination_class")

        has_filters = any(
            [
                filterset_class,
                filterset_fields,
                search_fields,
                ordering_fields,
            ]
        )

        if not has_filters and not pagination_class:
            return result

        # Don't filter/paginate Response objects
        if isinstance(result, Response):
            return result

        try:
            from .filters import filter_data as _filter_data
            from .pagination import BasePagination  # noqa: F401
        except ImportError:
            return result

        # Check if result is a list-like (in-memory) or a queryset
        is_queryset = hasattr(result, "filter") and hasattr(result, "all")
        is_list = isinstance(result, (list, tuple))

        if not is_list and not is_queryset:
            return result

        # ── Apply filters ────────────────────────────────────────────
        if has_filters:
            if is_queryset:
                try:
                    from .filters import filter_queryset as _filter_qs

                    result = await _filter_qs(
                        result,
                        request,
                        filterset_class=filterset_class,
                        filterset_fields=filterset_fields,
                        search_fields=search_fields,
                        ordering_fields=ordering_fields,
                    )
                except Exception as e:
                    self.logger.warning(f"QuerySet filtering failed: {e}")
            elif is_list:
                result = _filter_data(
                    list(result),
                    request,
                    filterset_class=filterset_class,
                    filterset_fields=filterset_fields,
                    search_fields=search_fields,
                    ordering_fields=ordering_fields,
                )

        # ── Apply pagination ─────────────────────────────────────────
        if pagination_class:
            try:
                paginator = pagination_class() if isinstance(pagination_class, type) else pagination_class
                if hasattr(result, "all") and hasattr(paginator, "paginate_queryset"):
                    result = await paginator.paginate_queryset(result, request)
                else:
                    # Materialise queryset if needed
                    if hasattr(result, "all"):
                        items = await result.all()
                        data = [i.to_dict() if hasattr(i, "to_dict") else i for i in items]
                    else:
                        data = list(result)
                    result = paginator.paginate_list(data, request)
            except Exception as e:
                self.logger.warning(f"Pagination failed: {e}")

        return result

    def _apply_content_negotiation(
        self,
        result: Any,
        route_metadata: Any,
        request: Request,
    ) -> Response | None:
        """
        Select a renderer via content negotiation and build a Response.

        Returns ``None`` if no renderer_classes are configured (default
        path uses ``_to_response``), or a fully-rendered ``Response``.
        """
        # Already a Response -- skip
        if isinstance(result, Response):
            return result

        renderer_classes = getattr(route_metadata, "renderer_classes", None)
        if renderer_classes is None:
            raw = getattr(route_metadata, "_raw_metadata", None)
            if raw and isinstance(raw, dict):
                renderer_classes = raw.get("renderer_classes")

        if not renderer_classes:
            return None  # caller falls through to _to_response

        try:
            from .renderers import BaseRenderer, ContentNegotiator
        except ImportError:
            return None

        # Instantiate renderer classes if they are types
        instances = []
        for rc in renderer_classes:
            if isinstance(rc, type) and issubclass(rc, BaseRenderer):
                instances.append(rc())
            elif isinstance(rc, BaseRenderer):
                instances.append(rc)

        if not instances:
            return None

        negotiator = ContentNegotiator(renderers=instances)
        renderer, media_type = negotiator.select_renderer(request)

        body = renderer.render(
            result,
            request=request,
            response_status=200,
        )

        content_type = media_type
        if renderer.charset:
            content_type = f"{media_type}; charset={renderer.charset}"

        return Response(
            content=body,
            status=200,
            media_type=content_type,
        )

    # Cache for coroutine function checks
    _is_coro_cache: dict[int, bool] = {}  # id(func) -> is_coroutine

    def _get_cached_signature(self, func: Any) -> inspect.Signature:
        """Get and cache function signature."""
        # For bound methods, use the underlying function to get a stable ID
        # and avoid "self" issues if any.
        target = func
        if hasattr(func, "__func__"):
            target = func.__func__

        fid = id(target)
        sig = ControllerEngine._signature_cache.get(fid)
        if sig is None:
            sig = inspect.signature(target)
            ControllerEngine._signature_cache[fid] = sig
        return sig

    async def _safe_call(self, func: Any, *args, **kwargs) -> Any:
        """Safely call function (sync or async)."""
        fid = id(func)
        is_coro = ControllerEngine._is_coro_cache.get(fid)
        if is_coro is None:
            is_coro = inspect.iscoroutinefunction(func)
            ControllerEngine._is_coro_cache[fid] = is_coro

        if is_coro:
            return await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result

    # ── Throttle ─────────────────────────────────────────────────────

    def _check_throttle(
        self,
        controller_class: type,
        route_metadata: Any,
        request: Request,
    ) -> Response | None:
        """
        Check rate limits at controller and route level.

        Returns a 429 Response if throttled, None if allowed.
        """
        # Route-level throttle takes precedence
        route_throttle = (
            getattr(route_metadata, "_raw_metadata", {}).get("throttle")
            if hasattr(route_metadata, "_raw_metadata")
            else None
        )
        if route_throttle is None:
            route_throttle = getattr(route_metadata, "throttle", None)
        class_throttle = getattr(controller_class, "throttle", None)

        throttle = route_throttle or class_throttle
        if throttle is None:
            return None

        if not throttle.check(request):
            return Response.json(
                {"error": "Too many requests", "retry_after": throttle.retry_after},
                status=429,
                headers={"Retry-After": str(throttle.retry_after)},
            )
        return None

    # ── Interceptors ─────────────────────────────────────────────────

    def _get_interceptors(
        self,
        controller_class: type,
        route_metadata: Any,
    ) -> list[Any]:
        """
        Collect interceptors from the controller class AND route metadata.

        SEC-CTRL-05: Now merges route-level interceptors with class-level.
        Route-level interceptors execute after class-level interceptors.

        Returns a list of Interceptor instances.
        """
        class_interceptors = getattr(controller_class, "interceptors", []) or []

        # Collect route-level interceptors from metadata
        route_interceptors = []
        if route_metadata is not None:
            # Check raw metadata dict
            raw_meta = getattr(route_metadata, "_raw_metadata", None)
            if raw_meta and isinstance(raw_meta, dict):
                route_interceptors = raw_meta.get("interceptors", []) or []
            # Also check direct attribute
            if not route_interceptors:
                route_interceptors = getattr(route_metadata, "interceptors", []) or []

        return list(class_interceptors) + list(route_interceptors)

    # ── Exception Filters ────────────────────────────────────────────

    async def _apply_exception_filters(
        self,
        exception: Exception,
        controller_class: type,
        route_metadata: Any,
        ctx: RequestCtx,
    ) -> Response | None:
        """
        Try to handle an exception through exception filters.

        SEC-CTRL-06: Now logs filter failures instead of silently swallowing.
        Also merges route-level exception filters with class-level.

        Returns a Response if handled, None if the exception should propagate.
        """
        class_filters = getattr(controller_class, "exception_filters", []) or []

        # Merge route-level filters
        route_filters = []
        if route_metadata is not None:
            raw_meta = getattr(route_metadata, "_raw_metadata", None)
            if raw_meta and isinstance(raw_meta, dict):
                route_filters = raw_meta.get("exception_filters", []) or []
            if not route_filters:
                route_filters = getattr(route_metadata, "exception_filters", []) or []

        filters = list(class_filters) + list(route_filters)
        exc_type = type(exception)

        for ef in filters:
            catches = getattr(ef, "catches", [])
            if not catches or any(issubclass(exc_type, c) for c in catches):
                try:
                    result = await self._safe_call(ef.catch, exception, ctx)
                    if isinstance(result, Response):
                        return result
                except Exception as filter_err:
                    # SEC-CTRL-06: Log instead of silently swallowing
                    self.logger.error(
                        "ExceptionFilter %s.catch() failed while handling %s: %s",
                        type(ef).__name__,
                        type(exception).__name__,
                        filter_err,
                        exc_info=True,
                    )

        return None

    # ── Timeout ──────────────────────────────────────────────────────

    async def _execute_with_timeout(
        self,
        handler: Any,
        controller_class: type,
        route_metadata: Any,
        **kwargs,
    ) -> Any:
        """
        Execute handler with optional timeout.

        Route-level timeout takes precedence over class-level.
        """
        # Route-level timeout
        route_timeout = (
            getattr(route_metadata, "_raw_metadata", {}).get("timeout")
            if hasattr(route_metadata, "_raw_metadata")
            else None
        )
        if route_timeout is None:
            route_timeout = getattr(route_metadata, "timeout", None)
        class_timeout = getattr(controller_class, "timeout", 0)

        timeout = route_timeout if route_timeout is not None else class_timeout

        if timeout and timeout > 0:
            try:
                return await asyncio.wait_for(
                    self._safe_call(handler, **kwargs),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # SEC-CTRL-13: Use structured fault instead of raw TimeoutError
                from ..faults.domains import FlowCancelledFault

                raise FlowCancelledFault(
                    reason=f"timeout ({timeout}s)",
                    metadata={
                        "controller": controller_class.__name__,
                        "handler": getattr(handler, "__name__", str(handler)),
                        "timeout": timeout,
                    },
                )
        else:
            return await self._safe_call(handler, **kwargs)

    # ── Cache Management ─────────────────────────────────────────────

    @classmethod
    def clear_caches(cls):
        """
        Clear all class-level caches.

        Call during testing teardown or hot-reload to prevent stale state
        and memory leaks in long-running applications.
        """
        cls._signature_cache.clear()
        cls._pipeline_param_cache.clear()
        cls._has_lifecycle_hooks.clear()
        cls._simple_route_cache.clear()
        cls._clearance_cache.clear()
        cls._is_coro_cache.clear()

    def _to_response(self, result: Any) -> Response:
        """Convert handler result to Response.

        SEC-CTRL-03: no longer uses str(result) fallback which could
        leak internal object representations.
        """
        if isinstance(result, Response):
            return result
        elif isinstance(result, (dict, list, tuple)):
            return Response.json(result)
        elif isinstance(result, str):
            return Response(result, media_type="text/plain")
        elif result is None:
            return Response("", status=204)
        elif isinstance(result, (int, float, bool)):
            return Response.json({"result": result})
        else:
            # SEC-CTRL-03: Do NOT serialize unknown types via str().
            # Log the type server-side and return a generic error.
            self.logger.warning(
                "Handler returned unsupported type %s; returning generic JSON envelope. "
                "Consider returning a dict, list, str, or Response.",
                type(result).__name__,
            )
            # Try JSON-safe serialization via __dict__ or generic wrapper
            if hasattr(result, "__dict__"):
                try:
                    return Response.json(result.__dict__)
                except (TypeError, ValueError):
                    pass
            return Response.json(
                {"error": "Unsupported response type"},
                status=500,
            )
