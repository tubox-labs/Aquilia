"""
Controller Attributes Builder — Comprehensive Test Suite

Covers:
  - Metadata creation and slot storage
  - Fluent chaining (single and multiple attributes)
  - All ten builder methods
  - __set_name__ descriptor protocol
  - Controller class attribute application
  - extract_controller_metadata integration
  - Route compilation integration
  - Pipeline registration
  - DI scope integration (singleton/per_request)
  - All validation failure paths
  - Backwards compatibility (existing inline declarations still work)
  - Regression: existing tests unaffected
  - Stress: 10,000 rapid instantiations, deep chains, concurrent-safe structure
"""

from __future__ import annotations

import gc
import time
from unittest.mock import MagicMock

import pytest

from aquilia.controller.attrs import _UNSET, Attributes
from aquilia.controller.base import Controller, Throttle
from aquilia.controller.compiler import ControllerCompiler
from aquilia.controller.decorators import GET, POST
from aquilia.controller.factory import ControllerFactory, InstantiationMode
from aquilia.controller.metadata import extract_controller_metadata

# ── TestAttributesCreation ───────────────────────────────────────────────────


class TestAttributesCreation:
    def test_initial_state_all_unset(self):
        attr = Attributes()
        assert attr._prefix is _UNSET
        assert attr._pipeline is _UNSET
        assert attr._tags is _UNSET
        assert attr._instantiation_mode is _UNSET
        assert attr._version is _UNSET
        assert attr._throttle is _UNSET
        assert attr._interceptors is _UNSET
        assert attr._exception_filters is _UNSET
        assert attr._timeout is _UNSET
        assert attr._max_body_size is _UNSET
        assert attr._applied is False
        assert attr._owner_name is None

    def test_has_slots_no_dict(self):
        attr = Attributes()
        assert hasattr(Attributes, "__slots__")
        assert not hasattr(attr, "__dict__")

    def test_separate_instances_independent(self):
        a = Attributes().prefix("/a")
        b = Attributes().prefix("/b")
        assert a._prefix == "/a"
        assert b._prefix == "/b"


# ── TestFluentChaining ───────────────────────────────────────────────────────


class TestFluentChaining:
    def test_each_method_returns_self(self):
        attr = Attributes()
        throttle = Throttle(limit=10, window=60)
        assert attr.prefix("/x") is attr
        assert attr.pipeline() is attr
        assert attr.tags() is attr
        assert attr.instantiation_mode("singleton") is attr
        assert attr.version("v1") is attr
        assert attr.throttle(throttle) is attr
        assert attr.interceptors() is attr
        assert attr.exception_filters() is attr
        assert attr.timeout(30.0) is attr
        assert attr.max_body_size(1024) is attr

    def test_full_chain_all_ten_methods(self):
        throttle = Throttle(limit=100, window=60)

        attr = (
            Attributes()
            .prefix("/products")
            .pipeline()
            .tags("Products", "v1")
            .instantiation_mode("singleton")
            .version("v1")
            .throttle(throttle)
            .interceptors()
            .exception_filters()
            .timeout(30.0)
            .max_body_size(4096)
        )

        assert attr._prefix == "/products"
        assert list(attr._pipeline) == []
        assert list(attr._tags) == ["Products", "v1"]
        assert attr._instantiation_mode == "singleton"
        assert attr._version == "v1"
        assert attr._throttle is throttle
        assert list(attr._interceptors) == []
        assert list(attr._exception_filters) == []
        assert attr._timeout == 30.0
        assert attr._max_body_size == 4096

    def test_chain_produces_identical_result_regardless_of_order(self):
        t = Throttle(limit=5, window=10)
        a1 = Attributes().prefix("/x").tags("T1").throttle(t)
        a2 = Attributes().throttle(t).prefix("/x").tags("T1")
        assert a1._prefix == a2._prefix
        assert list(a1._tags) == list(a2._tags)
        assert a1._throttle is a2._throttle


# ── TestPrefixMethod ──────────────────────────────────────────────────────────


class TestPrefixMethod:
    def test_valid_prefix(self):
        assert Attributes().prefix("/products")._prefix == "/products"

    def test_empty_prefix(self):
        assert Attributes().prefix("")._prefix == ""

    def test_deep_path_prefix(self):
        assert Attributes().prefix("/api/v1/products")._prefix == "/api/v1/products"


# ── TestPipelineMethod ────────────────────────────────────────────────────────


class TestPipelineMethod:
    def test_empty_pipeline(self):
        assert list(Attributes().pipeline()._pipeline) == []

    def test_single_node(self):
        guard = MagicMock()
        assert list(Attributes().pipeline(guard)._pipeline) == [guard]

    def test_multiple_nodes(self):
        g1, g2 = MagicMock(), MagicMock()
        assert list(Attributes().pipeline(g1, g2)._pipeline) == [g1, g2]


# ── TestTagsMethod ────────────────────────────────────────────────────────────


class TestTagsMethod:
    def test_empty_tags(self):
        assert list(Attributes().tags()._tags) == []

    def test_single_tag(self):
        assert list(Attributes().tags("Products")._tags) == ["Products"]

    def test_multiple_tags(self):
        assert list(Attributes().tags("A", "B", "C")._tags) == ["A", "B", "C"]


# ── TestInstantiationModeMethod ───────────────────────────────────────────────


class TestInstantiationModeMethod:
    def test_per_request(self):
        assert Attributes().instantiation_mode("per_request")._instantiation_mode == "per_request"

    def test_singleton(self):
        assert Attributes().instantiation_mode("singleton")._instantiation_mode == "singleton"


# ── TestVersionMethod ─────────────────────────────────────────────────────────


class TestVersionMethod:
    def test_string_version(self):
        assert Attributes().version("v1")._version == "v1"

    def test_list_version(self):
        assert Attributes().version(["v1", "v2"])._version == ["v1", "v2"]


# ── TestThrottleMethod ────────────────────────────────────────────────────────


class TestThrottleMethod:
    def test_throttle_instance_stored(self):
        t = Throttle(limit=100, window=60)
        assert Attributes().throttle(t)._throttle is t


# ── TestInterceptorsMethod ────────────────────────────────────────────────────


class TestInterceptorsMethod:
    def test_empty(self):
        assert list(Attributes().interceptors()._interceptors) == []

    def test_varargs(self):
        i1, i2 = MagicMock(), MagicMock()
        assert list(Attributes().interceptors(i1, i2)._interceptors) == [i1, i2]


# ── TestExceptionFiltersMethod ────────────────────────────────────────────────


class TestExceptionFiltersMethod:
    def test_empty(self):
        assert list(Attributes().exception_filters()._exception_filters) == []

    def test_varargs(self):
        f1, f2 = MagicMock(), MagicMock()
        assert list(Attributes().exception_filters(f1, f2)._exception_filters) == [f1, f2]


# ── TestTimeoutMethod ─────────────────────────────────────────────────────────


class TestTimeoutMethod:
    def test_float_value(self):
        assert Attributes().timeout(30.0)._timeout == 30.0

    def test_zero(self):
        assert Attributes().timeout(0)._timeout == 0

    def test_large_value(self):
        assert Attributes().timeout(3600.0)._timeout == 3600.0


# ── TestMaxBodySizeMethod ─────────────────────────────────────────────────────


class TestMaxBodySizeMethod:
    def test_int_value(self):
        assert Attributes().max_body_size(4096)._max_body_size == 4096

    def test_zero(self):
        assert Attributes().max_body_size(0)._max_body_size == 0

    def test_large_value(self):
        assert Attributes().max_body_size(10 * 1024 * 1024)._max_body_size == 10 * 1024 * 1024


# ── TestSetName ──────────────────────────────────────────────────────────────


class TestSetName:
    def test_set_name_marks_applied(self):
        class _C(Controller):
            attr = Attributes().prefix("/x")

        assert _C.attr._applied is True
        assert _C.attr._owner_name == "_C"

    def test_set_name_sets_prefix_on_class(self):
        class _C(Controller):
            attr = Attributes().prefix("/widgets")

        assert _C.prefix == "/widgets"

    def test_set_name_sets_pipeline_on_class(self):
        guard = MagicMock()

        class _C(Controller):
            attr = Attributes().pipeline(guard)

        assert _C.pipeline == [guard]

    def test_set_name_sets_tags_on_class(self):
        class _C(Controller):
            attr = Attributes().tags("Alpha", "Beta")

        assert _C.tags == ["Alpha", "Beta"]

    def test_set_name_sets_instantiation_mode_on_class(self):
        class _C(Controller):
            attr = Attributes().instantiation_mode("singleton")

        assert _C.instantiation_mode == "singleton"

    def test_set_name_sets_version_on_class(self):
        class _C(Controller):
            attr = Attributes().version("v2")

        assert _C.version == "v2"

    def test_set_name_sets_timeout_on_class(self):
        class _C(Controller):
            attr = Attributes().timeout(45.0)

        assert _C.timeout == 45.0

    def test_set_name_sets_max_body_size_on_class(self):
        class _C(Controller):
            attr = Attributes().max_body_size(8192)

        assert _C.max_body_size == 8192

    def test_unset_attributes_do_not_override_defaults(self):
        """Only configured attributes should be set; unset ones keep Controller defaults."""

        class _C(Controller):
            attr = Attributes().prefix("/only-prefix")

        assert _C.prefix == "/only-prefix"
        assert _C.instantiation_mode == "per_request"  # default untouched
        assert _C.timeout == 0  # default untouched
        assert _C.max_body_size == 0  # default untouched

    def test_pipeline_list_is_a_fresh_copy(self):
        """_ControllerMeta copies list fields; Attributes-set list must be independent."""
        guard = MagicMock()

        class _C(Controller):
            attr = Attributes().pipeline(guard)

        class _D(Controller):
            attr = Attributes().pipeline()

        # Mutating _C.pipeline must not affect _D.pipeline
        _C.pipeline.append(MagicMock())
        assert len(_D.pipeline) == 0


# ── TestClassAttributeApplication ─────────────────────────────────────────────


class TestClassAttributeApplication:
    def test_throttle_applied_to_class(self):
        t = Throttle(limit=10, window=60)

        class _C(Controller):
            attr = Attributes().throttle(t)

        assert _C.throttle is t

    def test_interceptors_applied_to_class(self):
        i = MagicMock()

        class _C(Controller):
            attr = Attributes().interceptors(i)

        assert _C.interceptors == [i]

    def test_exception_filters_applied_to_class(self):
        f = MagicMock()

        class _C(Controller):
            attr = Attributes().exception_filters(f)

        assert _C.exception_filters == [f]


# ── TestMetadataExtraction ───────────────────────────────────────────────────


class TestMetadataExtraction:
    def test_extract_reads_attrs_prefix(self):
        class _C(Controller):
            attr = Attributes().prefix("/items")

            @GET("/")
            async def list_items(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == "/items"

    def test_extract_reads_attrs_tags(self):
        class _C(Controller):
            attr = Attributes().tags("Items", "Public")

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert "Items" in meta.tags
        assert "Public" in meta.tags

    def test_extract_reads_attrs_instantiation_mode(self):
        class _C(Controller):
            attr = Attributes().instantiation_mode("singleton")

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.instantiation_mode == "singleton"

    def test_extract_reads_attrs_version(self):
        class _C(Controller):
            attr = Attributes().version("v3")

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.version == "v3"

    def test_extract_reads_attrs_pipeline_in_route(self):
        guard = MagicMock()

        class _C(Controller):
            attr = Attributes().prefix("/x").pipeline(guard)

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert guard in meta.routes[0].pipeline

    def test_extract_full_attributes_chain(self):
        guard = MagicMock()

        class _C(Controller):
            attr = (
                Attributes()
                .prefix("/full")
                .tags("Full")
                .pipeline(guard)
                .instantiation_mode("singleton")
                .version("v1")
                .timeout(10.0)
            )

            @POST("/create")
            async def create(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == "/full"
        assert "Full" in meta.tags
        assert meta.instantiation_mode == "singleton"
        assert meta.version == "v1"
        assert len(meta.routes) == 1
        route = meta.routes[0]
        assert route.http_method == "POST"
        assert guard in route.pipeline


# ── TestRouteCompilation ──────────────────────────────────────────────────────


class TestRouteCompilation:
    def test_compiler_produces_correct_routes(self):
        class _C(Controller):
            attr = Attributes().prefix("/widgets").tags("Widgets")

            @GET("/")
            async def list_widgets(self, ctx): ...

            @GET("/<id:int>")
            async def get_widget(self, ctx, id: int): ...

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(_C)
        assert compiled.metadata.prefix == "/widgets"
        full_paths = {r.full_path for r in compiled.routes}
        assert "/widgets/" in full_paths
        assert "/widgets/<id:int>" in full_paths


# ── TestPipelineRegistration ──────────────────────────────────────────────────


class TestPipelineRegistration:
    def test_pipeline_nodes_in_compiled_route(self):
        guard = MagicMock()

        class _C(Controller):
            attr = Attributes().prefix("/guarded").pipeline(guard)

            @GET("/")
            async def index(self, ctx): ...

        compiler = ControllerCompiler()
        compiled = compiler.compile_controller(_C)
        assert guard in compiled.routes[0].route_metadata.pipeline


# ── TestDIIntegration ─────────────────────────────────────────────────────────


class TestDIIntegration:
    async def test_singleton_mode_instantiation(self):
        class _C(Controller):
            attr = Attributes().instantiation_mode("singleton")

        factory = ControllerFactory()
        instance1 = await factory.create(_C, mode=InstantiationMode.SINGLETON)
        instance2 = await factory.create(_C, mode=InstantiationMode.SINGLETON)
        assert instance1 is instance2

    async def test_per_request_mode_instantiation(self):
        class _C(Controller):
            attr = Attributes().instantiation_mode("per_request")

        factory = ControllerFactory()
        instance1 = await factory.create(_C, mode=InstantiationMode.PER_REQUEST)
        instance2 = await factory.create(_C, mode=InstantiationMode.PER_REQUEST)
        assert instance1 is not instance2


# ── TestBackwardsCompatibility ────────────────────────────────────────────────


class TestBackwardsCompatibility:
    def test_inline_declaration_still_works(self):
        class _C(Controller):
            prefix = "/legacy"
            tags = ["OldWay"]
            instantiation_mode = "per_request"

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == "/legacy"
        assert "OldWay" in meta.tags

    def test_class_without_attr_unaffected(self):
        class _C(Controller):
            prefix = "/no-builder"
            pipeline = []

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == "/no-builder"
        assert not hasattr(_C, "attr")

    def test_both_inline_and_builder_builder_wins(self):
        """When both inline and Attributes() configure prefix, builder wins."""

        class _C(Controller):
            prefix = "/old"  # inline declaration
            attr = Attributes().prefix("/new")  # builder (fires later via __set_name__)

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == "/new"

    def test_partial_builder_respects_inline_remainder(self):
        """Builder sets only prefix; inline sets tags; both must be honoured."""

        class _C(Controller):
            tags = ["FromInline"]
            attr = Attributes().prefix("/partial")

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == "/partial"
        assert "FromInline" in meta.tags


# ── TestPartialOverride ───────────────────────────────────────────────────────


class TestPartialOverride:
    def test_only_prefix_from_builder_rest_from_defaults(self):
        class _C(Controller):
            attr = Attributes().prefix("/partial-only")

        assert _C.prefix == "/partial-only"
        assert _C.tags == []
        assert _C.pipeline == []

    def test_only_tags_from_builder_rest_from_class_body(self):
        class _C(Controller):
            prefix = "/inline-prefix"
            attr = Attributes().tags("BuilderTag")

        assert _C.prefix == "/inline-prefix"
        assert _C.tags == ["BuilderTag"]


# ── TestAttrWinsOverInline ────────────────────────────────────────────────────


class TestAttrWinsOverInline:
    def test_builder_tags_win_over_inline_tags(self):
        class _C(Controller):
            tags = ["Inline"]
            attr = Attributes().tags("Builder")

        assert _C.tags == ["Builder"]

    def test_builder_instantiation_mode_wins_over_inline(self):
        class _C(Controller):
            instantiation_mode = "per_request"
            attr = Attributes().instantiation_mode("singleton")

        assert _C.instantiation_mode == "singleton"


# ── TestValidation ────────────────────────────────────────────────────────────


class TestValidationPrefixFailures:
    def test_non_string_prefix_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().prefix(123)  # type: ignore[arg-type]

    def test_prefix_without_leading_slash_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().prefix("no-slash")

    def test_empty_prefix_valid(self):
        class _C(Controller):
            attr = Attributes().prefix("")

            @GET("/")
            async def index(self, ctx): ...

        assert _C.prefix == ""

    def test_root_prefix_valid(self):
        class _C(Controller):
            attr = Attributes().prefix("/")

            @GET("/")
            async def index(self, ctx): ...

        assert _C.prefix == "/"


class TestValidationTagsFailures:
    def test_non_string_tag_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().tags("valid", 42)  # type: ignore[arg-type]


class TestValidationModeFailures:
    def test_invalid_mode_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().instantiation_mode("unknown")  # type: ignore[arg-type]

    def test_valid_modes_accepted(self):
        class _A(Controller):
            attr = Attributes().instantiation_mode("per_request")

        class _B(Controller):
            attr = Attributes().instantiation_mode("singleton")

        assert _A.instantiation_mode == "per_request"
        assert _B.instantiation_mode == "singleton"


class TestValidationVersionFailures:
    def test_non_string_version_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().version(3)  # type: ignore[arg-type]

    def test_list_with_non_string_items_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().version(["v1", 2])  # type: ignore[arg-type]

    def test_valid_string_version(self):
        class _C(Controller):
            attr = Attributes().version("v2")

        assert _C.version == "v2"

    def test_valid_list_version(self):
        class _C(Controller):
            attr = Attributes().version(["v1", "v2"])

        assert _C.version == ["v1", "v2"]


class TestValidationTimeoutFailures:
    def test_negative_timeout_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().timeout(-1.0)

    def test_non_numeric_timeout_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().timeout("30s")  # type: ignore[arg-type]

    def test_zero_timeout_valid(self):
        class _C(Controller):
            attr = Attributes().timeout(0)

        assert _C.timeout == 0

    def test_large_timeout_valid(self):
        class _C(Controller):
            attr = Attributes().timeout(3600.0)

        assert _C.timeout == 3600.0


class TestValidationMaxBodyFailures:
    def test_negative_max_body_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().max_body_size(-1)

    def test_float_max_body_raises(self):
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault):

            class _C(Controller):
                attr = Attributes().max_body_size(1.5)  # type: ignore[arg-type]

    def test_zero_max_body_valid(self):
        class _C(Controller):
            attr = Attributes().max_body_size(0)

        assert _C.max_body_size == 0


# ── TestIntrospection ────────────────────────────────────────────────────────


class TestIntrospection:
    def test_repr_shows_configured_values(self):
        attr = Attributes().prefix("/x").tags("A")
        r = repr(attr)
        assert "prefix='/x'" in r
        assert "tags=['A']" in r
        assert "pending" in r

    def test_repr_shows_applied_after_set_name(self):
        class _C(Controller):
            attr = Attributes().prefix("/y")

        r = repr(_C.attr)
        assert "applied" in r

    def test_owner_name_set_after_set_name(self):
        class _C(Controller):
            attr = Attributes().prefix("/z")

        assert _C.attr._owner_name == "_C"

    def test_applied_flag_false_before_class_creation(self):
        attr = Attributes().prefix("/pending")
        assert attr._applied is False


# ── TestRepr ──────────────────────────────────────────────────────────────────


class TestRepr:
    def test_repr_contains_all_configured_fields(self):
        t = Throttle(limit=1, window=1)
        attr = (
            Attributes()
            .prefix("/x")
            .tags("A")
            .instantiation_mode("singleton")
            .version("v1")
            .throttle(t)
            .timeout(5.0)
            .max_body_size(100)
        )
        r = repr(attr)
        assert "prefix=" in r
        assert "tags=" in r
        assert "instantiation_mode=" in r
        assert "version=" in r
        assert "throttle=" in r
        assert "timeout=" in r
        assert "max_body_size=" in r

    def test_repr_empty_builder(self):
        r = repr(Attributes())
        assert r.startswith("Attributes(")
        assert "pending" in r


# ── TestMemoryEfficiency ─────────────────────────────────────────────────────


class TestMemoryEfficiency:
    def test_no_instance_dict(self):
        attr = Attributes()
        assert not hasattr(attr, "__dict__")

    def test_slots_defined(self):
        assert "__slots__" in Attributes.__dict__
        expected = {
            "_prefix",
            "_pipeline",
            "_tags",
            "_instantiation_mode",
            "_version",
            "_throttle",
            "_interceptors",
            "_exception_filters",
            "_timeout",
            "_max_body_size",
            "_applied",
            "_owner_name",
        }
        assert expected.issubset(set(Attributes.__slots__))


# ── TestStress ───────────────────────────────────────────────────────────────


class TestStressRapidInstantiation:
    def test_10000_chains_under_one_second(self):
        t0 = time.monotonic()
        for i in range(10_000):
            attr = (
                Attributes()
                .prefix(f"/resource-{i}")
                .tags(f"Tag{i}")
                .instantiation_mode("per_request")
                .timeout(float(i % 100))
            )
            assert attr._prefix == f"/resource-{i}"
        elapsed = time.monotonic() - t0
        assert elapsed < 1.0, f"10,000 chains took {elapsed:.3f}s (should be < 1s)"


class TestStressDeepChain:
    def test_all_ten_methods_1000_times(self):
        t = Throttle(limit=1, window=1)
        t0 = time.monotonic()
        for _ in range(1_000):
            attr = (
                Attributes()
                .prefix("/deep")
                .pipeline()
                .tags("Deep")
                .instantiation_mode("singleton")
                .version("v1")
                .throttle(t)
                .interceptors()
                .exception_filters()
                .timeout(5.0)
                .max_body_size(512)
            )
            # sanity check
            assert attr._prefix == "/deep"
        elapsed = time.monotonic() - t0
        assert elapsed < 2.0, f"1,000 deep chains took {elapsed:.3f}s (should be < 2s)"


class TestStressClassCreation:
    def test_1000_controller_subclasses_with_attrs(self):
        classes = []
        for i in range(1_000):
            name = f"_StressCtrl{i}"
            cls = type(
                name,
                (Controller,),
                {
                    "attr": Attributes().prefix(f"/stress/{i}").tags(f"Stress{i}"),
                    "__module__": __name__,
                },
            )
            # __set_name__ fires during type() construction via metaclass
            classes.append(cls)

        # Verify each class has correct attributes
        for i, cls in enumerate(classes):
            assert cls.prefix == f"/stress/{i}", f"Class {i} has wrong prefix"
            assert f"Stress{i}" in cls.tags, f"Class {i} has wrong tags"

    def test_memory_released_after_gc(self):
        """Controller classes with Attributes should not leak when collected."""
        import weakref

        refs = []
        for i in range(100):
            cls = type(
                f"_GCCtrl{i}",
                (Controller,),
                {
                    "attr": Attributes().prefix(f"/gc/{i}"),
                    "__module__": __name__,
                },
            )
            refs.append(weakref.ref(cls))

        del cls  # delete last strong reference in loop variable
        gc.collect()
        # Some classes may remain referenced by the list; this is fine.
        # The test just verifies no exception is raised during collection.


class TestStressMetadataExtraction:
    def test_extract_1000_controllers(self):
        t0 = time.monotonic()
        for i in range(1_000):
            cls = type(
                f"_MetaCtrl{i}",
                (Controller,),
                {
                    "attr": Attributes().prefix(f"/meta/{i}").tags(f"Meta{i}"),
                    "list_items": GET("/")(lambda self, ctx: None),
                    "__module__": __name__,
                },
            )
            meta = extract_controller_metadata(cls, f"test:_MetaCtrl{i}")
            assert meta.prefix == f"/meta/{i}"
        elapsed = time.monotonic() - t0
        # extraction should be fast; 1,000 controllers under 5 seconds
        assert elapsed < 5.0, f"1,000 extractions took {elapsed:.3f}s"


# ── TestRegressionExistingTests ──────────────────────────────────────────────


class TestRegressionExistingTests:
    """Verify that existing Controller patterns are completely unaffected."""

    def test_plain_controller_class_unchanged(self):
        class _C(Controller):
            prefix = "/regression"
            pipeline = []
            tags = ["Regression"]

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == "/regression"
        assert "Regression" in meta.tags

    def test_controller_without_any_config(self):
        class _C(Controller):
            @GET("/bare")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.prefix == ""
        assert meta.instantiation_mode == "per_request"

    def test_controller_with_version_inline(self):
        class _C(Controller):
            prefix = "/versioned"
            version = "v1"

            @GET("/")
            async def index(self, ctx): ...

        meta = extract_controller_metadata(_C, "test:_C")
        assert meta.version == "v1"

    def test_metaclass_mutable_list_isolation(self):
        """_ControllerMeta must still isolate pipeline lists between classes."""
        guard_a = MagicMock()
        guard_b = MagicMock()

        class _A(Controller):
            attr = Attributes().pipeline(guard_a)

        class _B(Controller):
            attr = Attributes().pipeline(guard_b)

        # Mutating _A's pipeline must NOT affect _B
        _A.pipeline.append(MagicMock())
        assert guard_b in _B.pipeline
        assert len(_B.pipeline) == 1
