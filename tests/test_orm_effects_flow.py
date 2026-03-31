"""
Comprehensive Regression Tests — ORM, Effects, and Flow Systems
================================================================

Tests all changes made during the ORM audit fix and the Effect/Flow
pipeline integration:

Module 1: ORM Expression System
    - F(), Value(), RawSQL(), Col(), Star(), CombinedExpression
    - When/Case, Subquery, Exists, OuterRef, ExpressionWrapper
    - Func, Cast, Coalesce, Greatest, Least, NullIf
    - String funcs: Length, Upper, Lower, Trim, LTrim, RTrim, Concat, Left, Right, Substr, Replace
    - Math funcs: Abs, Round, Power
    - Date: Now, OrderBy
    - QNode composition (AND / OR / NOT)
    - _build_filter_clause

Module 2: ORM Manager System
    - BaseManager descriptor protocol
    - Manager forwarding
    - Manager.from_queryset()
    - QuerySet

Module 3: ORM Fields & Mixins
    - NullableMixin, UniqueMixin, IndexedMixin, AutoNowMixin
    - ChoiceMixin, EncryptedMixin
    - SmallAutoField, VarcharField regression

Module 4: Effect System
    - Effect, EffectKind, EffectProvider
    - DBTx, CacheEffect, QueueEffect, HTTPEffect, StorageEffect tokens
    - EffectRegistry lifecycle (register, initialize, acquire, release, finalize)
    - EffectRegistry metrics, health_check, list_effects
    - QueueProvider, HTTPProvider, StorageProvider
    - CacheHandle, QueueHandle, HTTPHandle, StorageHandle
    - MockEffectProvider, MockEffectRegistry

Module 5: Flow Pipeline System
    - FlowNodeType, FlowStatus enums
    - FlowContext (state, effects, cleanup, dispose, timing)
    - FlowNode (type, callable, priority, effects, @requires auto-extract)
    - FlowResult (status, value, error, guard, timings)
    - FlowError
    - @requires decorator, get_required_effects
    - Layer / LayerComposition (topological sort, circular detection)
    - FlowPipeline builder (guard, transform, handler, hook, effect)
    - FlowPipeline execution: 5-phase, guard short-circuit, transform merge, handler, hooks
    - FlowPipeline effect acquisition / release lifecycle
    - FlowPipeline compose / | operator
    - FlowPipeline timeout via execute_with_timeout
    - EffectScope
    - Factory functions: pipeline, guard, transform, handler, hook
    - from_pipeline_list bridge
    - MockFlowContext

Module 6: Integration
    - EffectMiddleware / FlowContextMiddleware import
    - EffectSubsystem import
    - __init__.py re-exports (all symbols accessible from top-level)
"""

import asyncio
import inspect
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


# ════════════════════════════════════════════════════════════════════════
# MODULE 1: ORM EXPRESSION SYSTEM
# ════════════════════════════════════════════════════════════════════════


class TestExpressionF:
    """Test F() field reference expressions."""

    def test_f_simple(self):
        from aquilia.models.expression import F

        f = F("price")
        sql, params = f.as_sql()
        assert sql == '"price"'
        assert params == []

    def test_f_double_underscore(self):
        from aquilia.models.expression import F

        f = F("author__name")
        sql, params = f.as_sql()
        assert sql == '"author"."name"'
        assert params == []

    def test_f_repr(self):
        from aquilia.models.expression import F

        assert repr(F("name")) == "F('name')"

    def test_f_asc(self):
        from aquilia.models.expression import F

        order = F("name").asc()
        sql, params = order.as_sql()
        assert "ASC" in sql
        assert "DESC" not in sql

    def test_f_desc(self):
        from aquilia.models.expression import F

        order = F("name").desc()
        sql, params = order.as_sql()
        assert "DESC" in sql

    def test_f_desc_nulls_last(self):
        from aquilia.models.expression import F

        order = F("name").desc(nulls_last=True)
        sql, _ = order.as_sql()
        assert "NULLS LAST" in sql

    def test_f_asc_nulls_first(self):
        from aquilia.models.expression import F

        order = F("name").asc(nulls_first=True)
        sql, _ = order.as_sql()
        assert "NULLS FIRST" in sql


class TestExpressionValue:
    """Test Value() literal expressions."""

    def test_value_int(self):
        from aquilia.models.expression import Value

        sql, params = Value(42).as_sql()
        assert sql == "?"
        assert params == [42]

    def test_value_string(self):
        from aquilia.models.expression import Value

        sql, params = Value("hello").as_sql()
        assert sql == "?"
        assert params == ["hello"]

    def test_value_none(self):
        from aquilia.models.expression import Value

        sql, params = Value(None).as_sql()
        assert sql == "NULL"
        assert params == []

    def test_value_repr(self):
        from aquilia.models.expression import Value

        assert repr(Value(42)) == "Value(42)"


class TestExpressionRawSQL:
    """Test RawSQL expressions."""

    def test_raw_sql_no_params(self):
        from aquilia.models.expression import RawSQL

        sql, params = RawSQL("COALESCE(price, 0)").as_sql()
        assert sql == "COALESCE(price, 0)"
        assert params == []

    def test_raw_sql_with_params(self):
        from aquilia.models.expression import RawSQL

        sql, params = RawSQL("price * ?", [1.1]).as_sql()
        assert sql == "price * ?"
        assert params == [1.1]


class TestExpressionCol:
    """Test Col() table.column expressions."""

    def test_col(self):
        from aquilia.models.expression import Col

        sql, params = Col("users", "id").as_sql()
        assert sql == '"users"."id"'
        assert params == []


class TestExpressionStar:
    """Test Star (SELECT *) expression."""

    def test_star(self):
        from aquilia.models.expression import Star

        sql, params = Star().as_sql()
        assert sql == "*"
        assert params == []


class TestCombinedExpression:
    """Test arithmetic combinations of expressions."""

    def test_f_plus_int(self):
        from aquilia.models.expression import F

        expr = F("views") + 1
        sql, params = expr.as_sql()
        assert '"views"' in sql
        assert "+" in sql
        assert params == [1]

    def test_f_minus_f(self):
        from aquilia.models.expression import F

        expr = F("price") - F("cost")
        sql, params = expr.as_sql()
        assert "-" in sql
        assert params == []

    def test_f_mul_value(self):
        from aquilia.models.expression import F, Value

        expr = F("price") * Value(0.9)
        sql, params = expr.as_sql()
        assert "*" in sql
        assert params == [0.9]

    def test_f_div(self):
        from aquilia.models.expression import F

        expr = F("total") / F("count")
        sql, params = expr.as_sql()
        assert "/" in sql

    def test_f_mod(self):
        from aquilia.models.expression import F

        expr = F("id") % 10
        sql, params = expr.as_sql()
        assert "%" in sql
        assert params == [10]

    def test_neg(self):
        from aquilia.models.expression import F

        expr = -F("balance")
        sql, params = expr.as_sql()
        assert "-" in sql

    def test_radd(self):
        from aquilia.models.expression import F

        expr = 10 + F("offset")
        sql, params = expr.as_sql()
        assert "+" in sql
        assert params == [10]

    def test_rsub(self):
        from aquilia.models.expression import F

        expr = 100 - F("used")
        sql, params = expr.as_sql()
        assert "-" in sql
        assert params == [100]

    def test_rmul(self):
        from aquilia.models.expression import F

        expr = 2 * F("value")
        sql, params = expr.as_sql()
        assert "*" in sql
        assert params == [2]

    def test_rtruediv(self):
        from aquilia.models.expression import F

        expr = 100 / F("divisor")
        sql, params = expr.as_sql()
        assert "/" in sql
        assert params == [100]

    def test_rmod(self):
        from aquilia.models.expression import F

        expr = 100 % F("modulus")
        sql, params = expr.as_sql()
        assert "%" in sql
        assert params == [100]


class TestOrderBy:
    """Test OrderBy directive."""

    def test_orderby_asc(self):
        from aquilia.models.expression import F, OrderBy

        ob = OrderBy(F("name"), descending=False)
        sql, _ = ob.as_sql()
        assert sql.endswith("ASC")

    def test_orderby_desc(self):
        from aquilia.models.expression import F, OrderBy

        ob = OrderBy(F("name"), descending=True)
        sql, _ = ob.as_sql()
        assert "DESC" in sql

    def test_orderby_nulls_first(self):
        from aquilia.models.expression import F, OrderBy

        ob = OrderBy(F("x"), descending=False, nulls_first=True)
        sql, _ = ob.as_sql()
        assert "NULLS FIRST" in sql

    def test_orderby_nulls_last(self):
        from aquilia.models.expression import F, OrderBy

        ob = OrderBy(F("x"), descending=False, nulls_first=False)
        sql, _ = ob.as_sql()
        assert "NULLS LAST" in sql

    def test_orderby_repr(self):
        from aquilia.models.expression import F, OrderBy

        ob = OrderBy(F("name"), descending=True)
        r = repr(ob)
        assert "DESC" in r


class TestWhenCase:
    """Test When/Case conditional expressions."""

    def test_when_dict_condition(self):
        from aquilia.models.expression import When, Value

        w = When(condition={"status": "active"}, then=Value(1))
        sql, params = w.as_sql()
        assert "WHEN" in sql
        assert "THEN" in sql
        assert params == ["active", 1]

    def test_when_string_condition(self):
        from aquilia.models.expression import When, Value

        w = When(condition="age > 18", then=Value("adult"))
        sql, params = w.as_sql()
        assert "age > 18" in sql
        assert params == ["adult"]

    def test_case(self):
        from aquilia.models.expression import Case, When, Value

        c = Case(
            When(condition={"status": "active"}, then=Value("A")),
            When(condition={"status": "inactive"}, then=Value("I")),
            default=Value("U"),
        )
        sql, params = c.as_sql()
        assert "CASE" in sql
        assert "END" in sql
        assert "ELSE" in sql

    def test_case_no_default(self):
        from aquilia.models.expression import Case, When, Value

        c = Case(When(condition="1=1", then=Value(0)))
        sql, params = c.as_sql()
        assert "CASE" in sql
        assert "ELSE" not in sql


class TestSubqueryExists:
    """Test Subquery and Exists expressions."""

    def test_subquery_raw_string(self):
        from aquilia.models.expression import Subquery

        s = Subquery("SELECT id FROM orders")
        sql, _ = s.as_sql()
        assert "(SELECT id FROM orders)" == sql

    def test_exists_raw_string(self):
        from aquilia.models.expression import Exists

        e = Exists("SELECT 1 FROM orders WHERE user_id = ?")
        sql, _ = e.as_sql()
        assert "EXISTS" in sql

    def test_outer_ref(self):
        from aquilia.models.expression import OuterRef

        o = OuterRef("id")
        sql, _ = o.as_sql()
        assert '"id"' in sql
        assert "OuterRef" in repr(o)


class TestExpressionWrapper:
    """Test ExpressionWrapper."""

    def test_wrapper_passthrough(self):
        from aquilia.models.expression import ExpressionWrapper, F

        wrapped = ExpressionWrapper(F("price") + F("tax"))
        sql, _ = wrapped.as_sql()
        assert "+" in sql


class TestFuncExpressions:
    """Test Func-based expressions."""

    def test_func_generic(self):
        from aquilia.models.expression import Func, F

        f = Func("UPPER", F("name"))
        sql, _ = f.as_sql()
        assert sql == 'UPPER("name")'

    def test_cast(self):
        from aquilia.models.expression import Cast, F

        c = Cast(F("price"), "INTEGER")
        sql, _ = c.as_sql()
        assert "CAST" in sql
        assert "INTEGER" in sql

    def test_coalesce(self):
        from aquilia.models.expression import Coalesce, F, Value

        c = Coalesce(F("nickname"), F("name"), Value("Anonymous"))
        sql, params = c.as_sql()
        assert "COALESCE" in sql
        assert params == ["Anonymous"]

    def test_greatest_sqlite(self):
        from aquilia.models.expression import Greatest, F, Value

        g = Greatest(F("a"), F("b"), Value(0))
        sql, params = g.as_sql("sqlite")
        assert "MAX(" in sql  # SQLite uses MAX

    def test_greatest_postgres(self):
        from aquilia.models.expression import Greatest, F, Value

        g = Greatest(F("a"), F("b"))
        sql, _ = g.as_sql("postgresql")
        assert "GREATEST(" in sql

    def test_least_sqlite(self):
        from aquilia.models.expression import Least, F, Value

        l = Least(F("a"), F("b"), Value(100))
        sql, _ = l.as_sql("sqlite")
        assert "MIN(" in sql

    def test_nullif(self):
        from aquilia.models.expression import NullIf, F, Value

        n = NullIf(F("value"), Value(0))
        sql, params = n.as_sql()
        assert "NULLIF" in sql
        assert params == [0]


class TestStringFunctions:
    """Test Django-style string function expressions."""

    def test_length(self):
        from aquilia.models.expression import Length

        sql, _ = Length("name").as_sql()
        assert "LENGTH" in sql

    def test_upper(self):
        from aquilia.models.expression import Upper

        sql, _ = Upper("name").as_sql()
        assert "UPPER" in sql

    def test_lower(self):
        from aquilia.models.expression import Lower

        sql, _ = Lower("name").as_sql()
        assert "LOWER" in sql

    def test_trim(self):
        from aquilia.models.expression import Trim

        sql, _ = Trim("name").as_sql()
        assert "TRIM" in sql

    def test_ltrim(self):
        from aquilia.models.expression import LTrim

        sql, _ = LTrim("name").as_sql()
        assert "LTRIM" in sql

    def test_rtrim(self):
        from aquilia.models.expression import RTrim

        sql, _ = RTrim("name").as_sql()
        assert "RTRIM" in sql

    def test_concat_sqlite(self):
        from aquilia.models.expression import Concat, F, Value

        c = Concat(F("first"), Value(" "), F("last"))
        sql, params = c.as_sql("sqlite")
        assert "||" in sql
        assert params == [" "]

    def test_concat_mysql(self):
        from aquilia.models.expression import Concat, F, Value

        c = Concat(F("first"), Value(" "), F("last"))
        sql, _ = c.as_sql("mysql")
        assert "CONCAT(" in sql

    def test_left_sqlite(self):
        from aquilia.models.expression import Left

        l = Left("name", 3)
        sql, params = l.as_sql("sqlite")
        assert "SUBSTR" in sql
        assert 3 in params

    def test_right_sqlite(self):
        from aquilia.models.expression import Right

        r = Right("domain", 3)
        sql, _ = r.as_sql("sqlite")
        assert "SUBSTR" in sql
        assert "-3" in sql

    def test_substr(self):
        from aquilia.models.expression import Substr

        s = Substr("name", 1, 3)
        sql, params = s.as_sql()
        assert "SUBSTR" in sql

    def test_replace(self):
        from aquilia.models.expression import Replace, Value

        r = Replace("email", Value("@old.com"), Value("@new.com"))
        sql, params = r.as_sql()
        assert "REPLACE" in sql


class TestMathFunctions:
    """Test math function expressions."""

    def test_abs(self):
        from aquilia.models.expression import Abs, F

        sql, _ = Abs(F("diff")).as_sql()
        assert "ABS" in sql

    def test_round(self):
        from aquilia.models.expression import Round

        r = Round("price", 2)
        sql, params = r.as_sql()
        assert "ROUND" in sql
        assert 2 in params

    def test_power(self):
        from aquilia.models.expression import Power

        p = Power("value", 2)
        sql, params = p.as_sql()
        assert "POWER" in sql

    def test_now_sqlite(self):
        from aquilia.models.expression import Now

        sql, _ = Now().as_sql("sqlite")
        assert "DATETIME" in sql

    def test_now_postgres(self):
        from aquilia.models.expression import Now

        sql, _ = Now().as_sql("postgresql")
        assert "NOW()" in sql


class TestQNode:
    """Test QNode composition for complex WHERE clauses."""

    def test_qnode_simple(self):
        from aquilia.models.query import QNode

        q = QNode(name="Alice")
        sql, params = q._build_sql()
        assert '"name"' in sql
        assert params == ["Alice"]

    def test_qnode_and(self):
        from aquilia.models.query import QNode

        q = QNode(active=True) & QNode(role="admin")
        sql, params = q._build_sql()
        assert "AND" in sql

    def test_qnode_or(self):
        from aquilia.models.query import QNode

        q = QNode(name="Alice") | QNode(name="Bob")
        sql, params = q._build_sql()
        assert "OR" in sql

    def test_qnode_negate(self):
        from aquilia.models.query import QNode

        q = ~QNode(banned=True)
        sql, params = q._build_sql()
        assert "NOT" in sql

    def test_qnode_complex(self):
        from aquilia.models.query import QNode

        q = (QNode(active=True) & QNode(role="admin")) | QNode(is_super=True)
        sql, params = q._build_sql()
        assert "OR" in sql
        assert "AND" in sql

    def test_qnode_repr(self):
        from aquilia.models.query import QNode

        r = repr(QNode(x=1))
        assert "QNode" in r


class TestBuildFilterClause:
    """Test _build_filter_clause with various lookup types."""

    def test_exact(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("name", "Alice")
        assert '"name"' in sql
        assert "Alice" in params

    def test_gt_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("age__gt", 18)
        assert ">" in sql
        assert 18 in params

    def test_gte_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("age__gte", 21)
        assert ">=" in sql

    def test_lt_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("price__lt", 100)
        assert "<" in sql

    def test_lte_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("price__lte", 50)
        assert "<=" in sql

    def test_ne_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("status__ne", "deleted")
        assert "!=" in sql

    def test_isnull_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("email__isnull", True)
        assert "NULL" in sql.upper()

    def test_in_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("id__in", [1, 2, 3])
        assert "IN" in sql

    def test_contains_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("name__contains", "ali")
        assert "LIKE" in sql

    def test_startswith_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("name__startswith", "A")
        assert "LIKE" in sql

    def test_endswith_lookup(self):
        from aquilia.models.query import _build_filter_clause

        sql, params = _build_filter_clause("email__endswith", ".com")
        assert "LIKE" in sql

    def test_f_expression_filter(self):
        from aquilia.models.query import _build_filter_clause
        from aquilia.models.expression import F

        sql, params = _build_filter_clause("balance__gt", F("min_balance"))
        assert '"min_balance"' in sql
        assert ">" in sql


# ════════════════════════════════════════════════════════════════════════
# MODULE 2: ORM MANAGER SYSTEM
# ════════════════════════════════════════════════════════════════════════


class TestBaseManager:
    """Test BaseManager descriptor protocol."""

    def test_manager_class_access(self):
        from aquilia.models.manager import BaseManager

        mgr = BaseManager()

        class DummyModel:
            objects = mgr

        # set_name is called by Python automatically
        assert mgr._model_cls is DummyModel

    def test_manager_instance_access_raises(self):
        from aquilia.models.manager import BaseManager

        mgr = BaseManager()

        class DummyModel:
            objects = mgr

        with pytest.raises(AttributeError):
            DummyModel().objects

    def test_manager_repr(self):
        from aquilia.models.manager import Manager

        mgr = Manager()
        r = repr(mgr)
        assert "unbound" in r


class TestManagerFromQuerySet:
    """Test Manager.from_queryset()."""

    def test_from_queryset_creates_subclass(self):
        from aquilia.models.manager import Manager, QuerySet

        class CustomQS(QuerySet):
            def active(self):
                return self.get_queryset().filter(active=True)

        CustomManager = Manager.from_queryset(CustomQS)
        assert issubclass(CustomManager, Manager)
        assert hasattr(CustomManager, "active")

    def test_from_queryset_custom_name(self):
        from aquilia.models.manager import Manager, QuerySet

        class MyQS(QuerySet):
            pass

        Mgr = Manager.from_queryset(MyQS, "CustomName")
        assert Mgr.__name__ == "CustomName"


# ════════════════════════════════════════════════════════════════════════
# MODULE 3: ORM FIELDS & MIXINS
# ════════════════════════════════════════════════════════════════════════


class TestFieldMixins:
    """Test field mixins."""

    def test_nullable_mixin_defaults(self):
        from aquilia.models.fields.mixins import NullableMixin
        from aquilia.models.fields import CharField

        class NullableChar(NullableMixin, CharField):
            pass

        f = NullableChar(max_length=100)
        assert f.null is True
        assert f.blank is True

    def test_unique_mixin(self):
        from aquilia.models.fields.mixins import UniqueMixin
        from aquilia.models.fields import CharField

        class UniqueChar(UniqueMixin, CharField):
            pass

        f = UniqueChar(max_length=255)
        assert f.unique is True

    def test_indexed_mixin(self):
        from aquilia.models.fields.mixins import IndexedMixin
        from aquilia.models.fields import CharField

        class IndexedChar(IndexedMixin, CharField):
            pass

        f = IndexedChar(max_length=100)
        assert f.db_index is True

    def test_autonow_mixin(self):
        from aquilia.models.fields.mixins import AutoNowMixin
        from aquilia.models.fields import DateTimeField

        class AutoNowDT(AutoNowMixin, DateTimeField):
            pass

        f = AutoNowDT()
        assert f.auto_now is True

    def test_choice_mixin(self):
        from aquilia.models.fields.mixins import ChoiceMixin

        class StatusField(ChoiceMixin):
            choices = [("active", "Active"), ("inactive", "Inactive")]

        f = StatusField()
        assert f.get_display("active") == "Active"
        assert f.get_display("inactive") == "Inactive"
        assert f.get_display("unknown") == "unknown"
        assert f.choice_values == ["active", "inactive"]

    def test_encrypted_mixin_base64_fallback(self):
        import warnings
        from aquilia.models.fields.mixins import EncryptedMixin

        # Reset encryption state
        EncryptedMixin._encryption_backend = None
        EncryptedMixin._decryption_backend = None
        EncryptedMixin._fernet_instance = None

        enc = EncryptedMixin()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            encoded = enc.to_db("secret")
        decoded = enc.to_python(encoded)
        assert decoded == "secret"

    def test_encrypted_mixin_none(self):
        from aquilia.models.fields.mixins import EncryptedMixin

        enc = EncryptedMixin()
        assert enc.to_db(None) is None
        assert enc.to_python(None) is None

    def test_encrypted_mixin_custom_backend(self):
        from aquilia.models.fields.mixins import EncryptedMixin

        EncryptedMixin.configure_encryption(
            encrypt=lambda s: s[::-1],
            decrypt=lambda s: s[::-1],
        )
        enc = EncryptedMixin()
        assert enc.to_db("hello") == "olleh"
        assert enc.to_python("olleh") == "hello"

        # Reset
        EncryptedMixin._encryption_backend = None
        EncryptedMixin._decryption_backend = None
        EncryptedMixin._fernet_instance = None


class TestSmallAutoVarchar:
    """Regression: SmallAutoField and VarcharField (from test_missing_fields)."""

    def test_small_auto_field(self):
        from aquilia.models.fields import SmallAutoField, FieldValidationError

        field = SmallAutoField(primary_key=True)
        assert field.primary_key is True
        assert field._field_type == "SMALLAUTO"
        assert field.sql_type("sqlite") == "INTEGER"
        assert "SMALLSERIAL" in field.sql_type("postgresql").upper()
        assert field.validate(None) is None
        assert field.validate(150) == 150
        assert field.validate("150") == 150
        with pytest.raises(FieldValidationError):
            field.validate(50000)

    def test_varchar_field(self):
        from aquilia.models.fields import VarcharField, FieldValidationError

        field = VarcharField(max_length=200)
        assert field.max_length == 200
        assert field._field_type == "VARCHAR"
        assert field.sql_type() == "VARCHAR(200)"
        assert field.validate("test") == "test"
        with pytest.raises(FieldValidationError):
            field.validate("a" * 201)


# ════════════════════════════════════════════════════════════════════════
# MODULE 4: EFFECT SYSTEM
# ════════════════════════════════════════════════════════════════════════


class TestEffectTokens:
    """Test Effect tokens and EffectKind enum."""

    def test_effect_kind_values(self):
        from aquilia.effects import EffectKind

        assert EffectKind.DB.value == "db"
        assert EffectKind.CACHE.value == "cache"
        assert EffectKind.QUEUE.value == "queue"

    def test_dbtx_token(self):
        from aquilia.effects import DBTx

        token = DBTx()
        assert token.name == "DBTx"

    def test_cache_effect_token(self):
        from aquilia.effects import CacheEffect

        token = CacheEffect()
        assert token.name == "Cache"

    def test_queue_effect_token(self):
        from aquilia.effects import QueueEffect

        token = QueueEffect()
        assert token.name == "Queue"

    def test_http_effect_token(self):
        from aquilia.effects import HTTPEffect

        token = HTTPEffect()
        assert token.name == "HTTP"

    def test_storage_effect_token(self):
        from aquilia.effects import StorageEffect

        token = StorageEffect()
        assert token.name == "Storage"


class TestEffectRegistry:
    """Test EffectRegistry lifecycle."""

    @pytest.fixture
    def registry(self):
        from aquilia.effects import EffectRegistry

        return EffectRegistry()

    def test_register_and_has(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        provider = MockEffectProvider(return_value="conn")
        registry.register("db", provider)
        assert registry.has_effect("db")
        assert not registry.has_effect("unknown")

    def test_get_provider(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        provider = MockEffectProvider()
        registry.register("db", provider)
        assert registry.get_provider("db") is provider

    def test_get_provider_missing_raises(self, registry):
        from aquilia.faults.domains import EffectFault

        with pytest.raises(EffectFault):
            registry.get_provider("nonexistent")

    def test_unregister(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        provider = MockEffectProvider()
        registry.register("db", provider)
        removed = registry.unregister("db")
        assert removed is provider
        assert not registry.has_effect("db")

    def test_list_effects(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        registry.register("db", MockEffectProvider())
        registry.register("cache", MockEffectProvider())
        effects = registry.list_effects()
        assert "db" in effects
        assert "cache" in effects
        assert len(effects) == 2

    def test_metrics_initialized(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        registry.register("db", MockEffectProvider())
        metrics = registry.get_metrics()
        assert "db" in metrics
        assert metrics["db"]["acquires"] == 0
        assert metrics["db"]["releases"] == 0
        assert metrics["db"]["errors"] == 0

    @pytest.mark.asyncio
    async def test_initialize_all(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider()
        registry.register("db", p)
        await registry.initialize_all()
        assert p._initialized is True

    @pytest.mark.asyncio
    async def test_finalize_all(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider()
        registry.register("db", p)
        await registry.initialize_all()
        await registry.finalize_all()
        assert p._finalized is True

    @pytest.mark.asyncio
    async def test_acquire_release(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(return_value="connection")
        registry.register("db", p)
        resource = await registry.acquire("db")
        assert resource == "connection"
        assert p.acquire_count == 1

        await registry.release("db", resource)
        assert p.release_count == 1

    @pytest.mark.asyncio
    async def test_acquire_tracks_metrics(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(return_value="conn")
        registry.register("db", p)
        await registry.acquire("db")
        await registry.acquire("db")
        metrics = registry.get_metrics()
        assert metrics["db"]["acquires"] == 2

    @pytest.mark.asyncio
    async def test_acquire_error_tracks_metrics(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(acquire_side_effect=RuntimeError("fail"))
        registry.register("db", p)
        with pytest.raises(RuntimeError):
            await registry.acquire("db")
        metrics = registry.get_metrics()
        assert metrics["db"]["errors"] == 1

    @pytest.mark.asyncio
    async def test_health_check(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        registry.register("db", MockEffectProvider())
        await registry.initialize_all()
        health = await registry.health_check()
        assert health["initialized"] is True
        assert health["provider_count"] == 1
        assert "db" in health["providers"]

    def test_repr(self, registry):
        from aquilia.testing.effects import MockEffectProvider

        registry.register("db", MockEffectProvider())
        r = repr(registry)
        assert "EffectRegistry" in r
        assert "db" in r


class TestMockEffectProvider:
    """Test MockEffectProvider."""

    @pytest.mark.asyncio
    async def test_basic_acquire(self):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(return_value="value")
        result = await p.acquire()
        assert result == "value"
        assert p.acquire_count == 1

    @pytest.mark.asyncio
    async def test_sequence_returns(self):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(return_sequence=["a", "b", "c"])
        assert await p.acquire() == "a"
        assert await p.acquire() == "b"
        assert await p.acquire() == "c"
        assert await p.acquire() == "c"  # last repeats

    @pytest.mark.asyncio
    async def test_acquire_side_effect(self):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(acquire_side_effect=ValueError("boom"))
        with pytest.raises(ValueError, match="boom"):
            await p.acquire()

    @pytest.mark.asyncio
    async def test_release_tracking(self):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(return_value="res")
        r = await p.acquire()
        await p.release(r, success=True)
        assert p.release_count == 1
        assert p.released_resources == [("res", True)]

    @pytest.mark.asyncio
    async def test_call_history(self):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(return_value="x")
        await p.acquire(mode="read")
        await p.release("x")
        assert len(p.call_history) == 2
        assert p.call_history[0].action == "acquire"
        assert p.call_history[0].mode == "read"
        assert p.call_history[1].action == "release"

    @pytest.mark.asyncio
    async def test_reset(self):
        from aquilia.testing.effects import MockEffectProvider

        p = MockEffectProvider(return_value="v")
        await p.acquire()
        await p.release("v")
        p.reset()
        assert p.acquire_count == 0
        assert p.release_count == 0
        assert p.call_history == []


class TestMockEffectRegistry:
    """Test MockEffectRegistry."""

    def test_register_mock(self):
        from aquilia.testing.effects import MockEffectRegistry

        reg = MockEffectRegistry()
        mock = reg.register_mock("DBTx", return_value="fake_conn")
        assert reg.has_effect("DBTx")
        assert mock.return_value == "fake_conn"

    def test_auto_stub_missing(self):
        from aquilia.testing.effects import MockEffectRegistry

        reg = MockEffectRegistry()
        # Access unregistered effect — auto-creates mock
        provider = reg.get_provider("NewEffect")
        assert provider is not None

    def test_get_mock(self):
        from aquilia.testing.effects import MockEffectRegistry

        reg = MockEffectRegistry()
        reg.register_mock("Cache", return_value="cache_handle")
        mock = reg.get_mock("Cache")
        assert mock is not None
        assert mock.return_value == "cache_handle"

    def test_reset_all(self):
        from aquilia.testing.effects import MockEffectRegistry, MockEffectProvider

        reg = MockEffectRegistry()
        reg.register_mock("a")
        reg.register_mock("b")
        # Simulate usage
        reg.get_mock("a").acquire_count = 5
        reg.get_mock("b").release_count = 3
        reg.reset_all()
        assert reg.get_mock("a").acquire_count == 0
        assert reg.get_mock("b").release_count == 0


# ════════════════════════════════════════════════════════════════════════
# MODULE 5: FLOW PIPELINE SYSTEM
# ════════════════════════════════════════════════════════════════════════


class TestFlowEnums:
    """Test Flow enums and constants."""

    def test_flow_node_types(self):
        from aquilia.flow import FlowNodeType

        assert FlowNodeType.GUARD == "guard"
        assert FlowNodeType.TRANSFORM == "transform"
        assert FlowNodeType.HANDLER == "handler"
        assert FlowNodeType.HOOK == "hook"
        assert FlowNodeType.EFFECT == "effect"
        assert FlowNodeType.MIDDLEWARE == "middleware"

    def test_flow_status(self):
        from aquilia.flow import FlowStatus

        assert FlowStatus.SUCCESS == "success"
        assert FlowStatus.GUARDED == "guarded"
        assert FlowStatus.ERROR == "error"
        assert FlowStatus.TIMEOUT == "timeout"
        assert FlowStatus.CANCELLED == "cancelled"

    def test_priority_constants(self):
        from aquilia.flow import (
            PRIORITY_CRITICAL,
            PRIORITY_AUTH,
            PRIORITY_VALIDATE,
            PRIORITY_TRANSFORM,
            PRIORITY_DEFAULT,
            PRIORITY_ENRICH,
            PRIORITY_LOG,
            PRIORITY_CLEANUP,
        )

        assert PRIORITY_CRITICAL < PRIORITY_AUTH < PRIORITY_VALIDATE
        assert PRIORITY_VALIDATE < PRIORITY_TRANSFORM < PRIORITY_DEFAULT
        assert PRIORITY_DEFAULT < PRIORITY_ENRICH < PRIORITY_LOG < PRIORITY_CLEANUP


class TestFlowContext:
    """Test FlowContext."""

    def test_init_defaults(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext()
        assert ctx.request is None
        assert ctx.container is None
        assert ctx.state == {}
        assert ctx.identity is None
        assert ctx.session is None
        assert ctx.effects == {}
        assert ctx._cleanup == []

    def test_state_access(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext(state={"key": "val"})
        assert ctx.get("key") == "val"
        assert ctx.get("missing", "default") == "default"
        ctx.set("new", 42)
        assert ctx["new"] == 42
        assert "new" in ctx

    def test_state_dict_interface(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext()
        ctx["a"] = 1
        ctx["b"] = 2
        assert ctx["a"] == 1
        assert "b" in ctx

    def test_effect_access(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext()
        ctx.effects["db"] = "connection"
        assert ctx.get_effect("db") == "connection"
        assert ctx.has_effect("db")
        assert not ctx.has_effect("cache")

    def test_effect_missing_raises(self):
        from aquilia.flow import FlowContext
        from aquilia.faults.domains import EffectFault

        ctx = FlowContext()
        with pytest.raises(EffectFault, match="not acquired"):
            ctx.get_effect("missing")

    def test_elapsed_ms(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext()
        time.sleep(0.05)  # Use longer sleep for Windows timer resolution
        assert ctx.elapsed_ms > 0

    @pytest.mark.asyncio
    async def test_cleanup_lifo(self):
        from aquilia.flow import FlowContext

        order = []
        ctx = FlowContext()
        ctx.add_cleanup(
            lambda: asyncio.coroutine(lambda: order.append(1))() if False else asyncio.sleep(0, result=order.append(1))
        )
        ctx.add_cleanup(
            lambda: asyncio.coroutine(lambda: order.append(2))() if False else asyncio.sleep(0, result=order.append(2))
        )

        # Use proper async callbacks
        async def cb1():
            order.clear()

        async def cb2():
            order.append("a")

        async def cb3():
            order.append("b")

        ctx2 = FlowContext()
        ctx2.add_cleanup(cb2)
        ctx2.add_cleanup(cb3)
        await ctx2.dispose()
        # LIFO: cb3 runs first, then cb2
        assert order == ["b", "a"]

    def test_to_dict(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext(identity="user123", state={"role": "admin"})
        d = ctx.to_dict()
        assert d["identity"] == "user123"
        assert d["role"] == "admin"

    def test_repr(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext()
        ctx.effects["db"] = "conn"
        r = repr(ctx)
        assert "FlowContext" in r
        assert "db" in r

    def test_metadata(self):
        from aquilia.flow import FlowContext

        ctx = FlowContext()
        assert "node_trace" in ctx.metadata
        assert "timings" in ctx.metadata
        assert "acquired_effects" in ctx.metadata


class TestFlowNode:
    """Test FlowNode dataclass."""

    def test_node_creation(self):
        from aquilia.flow import FlowNode, FlowNodeType, PRIORITY_DEFAULT

        node = FlowNode(
            type=FlowNodeType.HANDLER,
            callable=lambda ctx: None,
            name="test_handler",
        )
        assert node.type == FlowNodeType.HANDLER
        assert node.name == "test_handler"
        assert node.priority == PRIORITY_DEFAULT

    def test_node_auto_extract_requires(self):
        from aquilia.flow import FlowNode, FlowNodeType, requires

        @requires("DBTx", "Cache")
        async def my_handler(ctx):
            pass

        node = FlowNode(
            type=FlowNodeType.HANDLER,
            callable=my_handler,
            name="my_handler",
        )
        assert "DBTx" in node.effects
        assert "Cache" in node.effects


class TestFlowResult:
    """Test FlowResult."""

    def test_success_result(self):
        from aquilia.flow import FlowResult, FlowStatus

        r = FlowResult(status=FlowStatus.SUCCESS, value={"ok": True})
        assert r.is_success
        assert not r.is_guarded

    def test_guarded_result(self):
        from aquilia.flow import FlowResult, FlowStatus

        r = FlowResult(status=FlowStatus.GUARDED)
        assert r.is_guarded
        assert not r.is_success


class TestFlowError:
    """Test FlowError."""

    def test_flow_error(self):
        from aquilia.flow import FlowError

        err = FlowError("something failed", cause=ValueError("inner"))
        assert "something failed" in str(err)
        assert err.cause is not None


class TestRequiresDecorator:
    """Test @requires decorator."""

    def test_basic_requires(self):
        from aquilia.flow import requires, get_required_effects

        @requires("DBTx")
        async def handler(ctx):
            pass

        assert get_required_effects(handler) == ["DBTx"]

    def test_multiple_requires(self):
        from aquilia.flow import requires, get_required_effects

        @requires("DBTx", "Cache")
        async def handler(ctx):
            pass

        effects = get_required_effects(handler)
        assert "DBTx" in effects
        assert "Cache" in effects

    def test_stacked_requires(self):
        from aquilia.flow import requires, get_required_effects

        @requires("Cache")
        @requires("DBTx")
        async def handler(ctx):
            pass

        effects = get_required_effects(handler)
        assert "DBTx" in effects
        assert "Cache" in effects

    def test_no_requires(self):
        from aquilia.flow import get_required_effects

        async def handler(ctx):
            pass

        assert get_required_effects(handler) == []


class TestLayer:
    """Test Layer and LayerComposition."""

    def test_layer_creation(self):
        from aquilia.flow import Layer

        l = Layer(name="db", factory=lambda: "provider")
        assert l.name == "db"
        assert l.deps == []

    @pytest.mark.asyncio
    async def test_layer_build(self):
        from aquilia.flow import Layer

        l = Layer(name="db", factory=lambda: "db_provider")
        result = await l.build({})
        assert result == "db_provider"
        assert l._built is True

    @pytest.mark.asyncio
    async def test_layer_build_cached(self):
        from aquilia.flow import Layer

        count = {"n": 0}

        def factory():
            count["n"] += 1
            return f"provider_{count['n']}"

        l = Layer(name="db", factory=factory)
        r1 = await l.build({})
        r2 = await l.build({})
        assert r1 == r2  # Cached
        assert count["n"] == 1

    @pytest.mark.asyncio
    async def test_layer_with_deps(self):
        from aquilia.flow import Layer

        l = Layer(name="cache", factory=lambda db: f"cache_using_{db}", deps=["db"])
        result = await l.build({"db": "pg_conn"})
        assert result == "cache_using_pg_conn"

    def test_layer_merge(self):
        from aquilia.flow import Layer, LayerComposition

        l1 = Layer(name="a", factory=lambda: "a")
        l2 = Layer(name="b", factory=lambda: "b")
        comp = Layer.merge(l1, l2)
        assert isinstance(comp, LayerComposition)
        assert len(comp.layers) == 2

    def test_layer_provide(self):
        from aquilia.flow import Layer, LayerComposition

        base = Layer(name="config", factory=lambda: {"url": "pg://localhost"})
        dependent = Layer(name="db", factory=lambda config: f"db({config})", deps=["config"])
        comp = Layer.provide(dependent, base)
        assert isinstance(comp, LayerComposition)


class TestLayerComposition:
    """Test LayerComposition topological sort and build."""

    def test_resolve_build_order(self):
        from aquilia.flow import Layer, LayerComposition

        l1 = Layer(name="config", factory=lambda: {})
        l2 = Layer(name="db", factory=lambda config=None: "db", deps=["config"])
        l3 = Layer(name="cache", factory=lambda db=None: "cache", deps=["db"])
        comp = LayerComposition([l3, l1, l2])  # Intentionally unordered
        order = comp._resolve_build_order()
        assert order.index("config") < order.index("db")
        assert order.index("db") < order.index("cache")

    def test_circular_dependency_detected(self):
        from aquilia.flow import Layer, LayerComposition, FlowError

        l1 = Layer(name="a", factory=lambda: None, deps=["b"])
        l2 = Layer(name="b", factory=lambda: None, deps=["a"])
        comp = LayerComposition([l1, l2])
        with pytest.raises(FlowError, match="Circular"):
            comp._resolve_build_order()

    @pytest.mark.asyncio
    async def test_build_all(self):
        from aquilia.flow import Layer, LayerComposition

        l1 = Layer(name="config", factory=lambda: {"url": "sqlite://"})
        l2 = Layer(name="db", factory=lambda config=None: f"db({config})", deps=["config"])
        comp = LayerComposition([l1, l2])
        providers = await comp.build_all()
        assert "config" in providers
        assert "db" in providers

    @pytest.mark.asyncio
    async def test_build_all_with_initial_deps(self):
        from aquilia.flow import Layer, LayerComposition

        l = Layer(name="db", factory=lambda env=None: f"db({env})", deps=["env"])
        comp = LayerComposition([l])
        providers = await comp.build_all(initial_deps={"env": "production"})
        assert providers["db"] == "db(production)"

    @pytest.mark.asyncio
    async def test_build_all_missing_dep_raises(self):
        from aquilia.flow import Layer, LayerComposition, FlowError

        l = Layer(name="db", factory=lambda: None, deps=["missing"])
        comp = LayerComposition([l])
        with pytest.raises(FlowError, match="unresolved"):
            await comp.build_all()


class TestFlowPipelineBuilder:
    """Test FlowPipeline builder API."""

    def test_pipeline_creation(self):
        from aquilia.flow import FlowPipeline

        p = FlowPipeline("test")
        assert p.name == "test"
        assert p._nodes == []

    def test_guard_returns_self(self):
        from aquilia.flow import FlowPipeline

        p = FlowPipeline("test")
        result = p.guard(lambda ctx: True, name="g")
        assert result is p

    def test_builder_chain(self):
        from aquilia.flow import FlowPipeline

        p = (
            FlowPipeline("test")
            .guard(lambda ctx: True, name="auth")
            .transform(lambda ctx: ctx, name="norm")
            .handler(lambda ctx: {"ok": True}, name="main")
            .hook(lambda ctx, result=None: None, name="log")
        )
        assert len(p._nodes) == 4

    def test_builder_types_assigned(self):
        from aquilia.flow import FlowPipeline, FlowNodeType

        p = (
            FlowPipeline("test")
            .guard(lambda ctx: True, name="g")
            .transform(lambda ctx: ctx, name="t")
            .handler(lambda ctx: None, name="h")
            .hook(lambda ctx: None, name="k")
            .effect(lambda ctx: None, name="e")
            .middleware(lambda ctx: None, name="m")
        )
        types = {n.type for n in p._nodes}
        assert FlowNodeType.GUARD in types
        assert FlowNodeType.TRANSFORM in types
        assert FlowNodeType.HANDLER in types
        assert FlowNodeType.HOOK in types
        assert FlowNodeType.EFFECT in types
        assert FlowNodeType.MIDDLEWARE in types

    def test_compose(self):
        from aquilia.flow import FlowPipeline

        p1 = FlowPipeline("a").guard(lambda ctx: True, name="g1")
        p2 = FlowPipeline("b").handler(lambda ctx: None, name="h1")
        composed = p1.compose(p2)
        assert len(composed._nodes) == 2
        assert "a" in composed.name
        assert "b" in composed.name

    def test_pipe_operator(self):
        from aquilia.flow import FlowPipeline

        p1 = FlowPipeline("a").guard(lambda ctx: True, name="g1")
        p2 = FlowPipeline("b").handler(lambda ctx: None, name="h1")
        composed = p1 | p2
        assert len(composed._nodes) == 2


class TestFlowPipelineExecution:
    """Test FlowPipeline execution — the 5-phase cycle."""

    @pytest.mark.asyncio
    async def test_simple_success(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def my_handler(ctx):
            return {"user": "alice"}

        p = FlowPipeline("test").handler(my_handler, name="create_user")
        result = await p.execute(FlowContext())

        assert result.status == FlowStatus.SUCCESS
        assert result.value == {"user": "alice"}
        assert "create_user" in result.timings

    @pytest.mark.asyncio
    async def test_guard_passes(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def guard(ctx):
            return True  # pass

        async def handler(ctx):
            return "ok"

        p = FlowPipeline("test").guard(guard, name="g").handler(handler, name="h")
        result = await p.execute(FlowContext())
        assert result.status == FlowStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_guard_blocks(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def guard(ctx):
            return False  # block

        async def handler(ctx):
            return "should not run"

        p = FlowPipeline("test").guard(guard, name="blocker").handler(handler, name="h")
        result = await p.execute(FlowContext())
        assert result.status == FlowStatus.GUARDED
        assert result.guard is not None
        assert result.guard.name == "blocker"
        assert result.value is None

    @pytest.mark.asyncio
    async def test_guard_exception_is_guarded(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def bad_guard(ctx):
            raise PermissionError("denied")

        p = FlowPipeline("test").guard(bad_guard, name="auth").handler(lambda ctx: None, name="h")
        result = await p.execute(FlowContext())
        assert result.status == FlowStatus.GUARDED
        assert isinstance(result.error, PermissionError)

    @pytest.mark.asyncio
    async def test_transform_updates_state(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def add_role(ctx):
            return {"role": "admin"}

        async def handler(ctx):
            return {"role": ctx.get("role")}

        p = FlowPipeline("test").transform(add_role, name="add_role").handler(handler, name="h")
        result = await p.execute(FlowContext())
        assert result.status == FlowStatus.SUCCESS
        assert result.value == {"role": "admin"}

    @pytest.mark.asyncio
    async def test_hooks_run_after_handler(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        trace = []

        async def handler(ctx):
            trace.append("handler")
            return "result"

        async def hook1(ctx):
            trace.append("hook1")

        async def hook2(ctx):
            trace.append("hook2")

        p = (
            FlowPipeline("test")
            .handler(handler, name="h")
            .hook(hook1, name="k1", priority=70)
            .hook(hook2, name="k2", priority=71)
        )
        result = await p.execute(FlowContext())
        assert result.status == FlowStatus.SUCCESS
        assert trace == ["handler", "hook1", "hook2"]

    @pytest.mark.asyncio
    async def test_error_status(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def bad_handler(ctx):
            raise RuntimeError("boom")

        p = FlowPipeline("test").handler(bad_handler, name="h")
        result = await p.execute(FlowContext())
        assert result.status == FlowStatus.ERROR
        assert isinstance(result.error, RuntimeError)

    @pytest.mark.asyncio
    async def test_node_condition(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus, FlowNode, FlowNodeType

        trace = []

        async def conditional_guard(ctx):
            trace.append("ran")
            return True  # allow pipeline to continue

        p = FlowPipeline("test")
        p.guard(
            conditional_guard,
            name="cond",
            condition=lambda ctx: ctx.state.get("run_guard") is True,
        )
        p.handler(lambda ctx: "ok", name="h")

        # Without flag — guard condition is False, guard skipped
        result = await p.execute(FlowContext())
        assert trace == []
        assert result.status == FlowStatus.SUCCESS

        # With flag — guard condition is True, guard runs
        result = await p.execute(FlowContext(state={"run_guard": True}))
        assert trace == ["ran"]
        assert result.status == FlowStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execution_order(self):
        """Guards < Transforms < Effects < Handler < Hooks."""
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        order = []

        async def g(ctx):
            order.append("guard")
            return True

        async def t(ctx):
            order.append("transform")

        async def e(ctx):
            order.append("effect")

        async def h(ctx):
            order.append("handler")
            return "done"

        async def k(ctx):
            order.append("hook")

        p = (
            FlowPipeline("order_test")
            .hook(k, name="k")
            .handler(h, name="h")
            .effect(e, name="e")
            .transform(t, name="t")
            .guard(g, name="g")
        )
        result = await p.execute(FlowContext())
        assert result.status == FlowStatus.SUCCESS
        assert order == ["guard", "transform", "effect", "handler", "hook"]

    @pytest.mark.asyncio
    async def test_timings_populated(self):
        from aquilia.flow import FlowPipeline, FlowContext

        async def handler(ctx):
            return "ok"

        p = FlowPipeline("test").handler(handler, name="main")
        result = await p.execute(FlowContext())
        assert "main" in result.timings
        assert "__total__" in result.timings
        assert all(isinstance(v, float) for v in result.timings.values())


class TestFlowPipelineEffectLifecycle:
    """Test FlowPipeline automatic effect acquisition and release."""

    @pytest.mark.asyncio
    async def test_effects_acquired_and_released(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus, requires
        from aquilia.testing.effects import MockEffectRegistry

        registry = MockEffectRegistry()
        db_mock = registry.register_mock("DBTx", return_value="db_conn")

        @requires("DBTx")
        async def handler(ctx):
            assert ctx.has_effect("DBTx")
            assert ctx.get_effect("DBTx") == "db_conn"
            return "saved"

        p = FlowPipeline("test").handler(handler, name="h")
        result = await p.execute(FlowContext(), effect_registry=registry)

        assert result.status == FlowStatus.SUCCESS
        assert result.value == "saved"
        assert db_mock.acquire_count == 1
        assert db_mock.release_count == 1

    @pytest.mark.asyncio
    async def test_effects_released_on_error(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus, requires
        from aquilia.testing.effects import MockEffectRegistry

        registry = MockEffectRegistry()
        db_mock = registry.register_mock("DBTx", return_value="conn")

        @requires("DBTx")
        async def handler(ctx):
            raise RuntimeError("fail")

        p = FlowPipeline("test").handler(handler, name="h")
        result = await p.execute(FlowContext(), effect_registry=registry)

        assert result.status == FlowStatus.ERROR
        assert db_mock.acquire_count == 1
        # Effects should be released even on error
        assert db_mock.release_count == 1

    @pytest.mark.asyncio
    async def test_multiple_effects(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus, requires
        from aquilia.testing.effects import MockEffectRegistry

        registry = MockEffectRegistry()
        db_mock = registry.register_mock("DBTx", return_value="db")
        cache_mock = registry.register_mock("Cache", return_value="cache")

        @requires("DBTx", "Cache")
        async def handler(ctx):
            return {
                "db": ctx.get_effect("DBTx"),
                "cache": ctx.get_effect("Cache"),
            }

        p = FlowPipeline("test").handler(handler, name="h")
        result = await p.execute(FlowContext(), effect_registry=registry)

        assert result.status == FlowStatus.SUCCESS
        assert result.value["db"] == "db"
        assert result.value["cache"] == "cache"

    @pytest.mark.asyncio
    async def test_no_registry_still_works(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def handler(ctx):
            return "ok"

        p = FlowPipeline("test").handler(handler, name="h")
        result = await p.execute(FlowContext())  # No registry
        assert result.status == FlowStatus.SUCCESS


class TestFlowPipelineTimeout:
    """Test pipeline timeout."""

    @pytest.mark.asyncio
    async def test_timeout(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def slow_handler(ctx):
            await asyncio.sleep(10)
            return "done"

        p = FlowPipeline("test").handler(slow_handler, name="h")
        result = await p.execute_with_timeout(FlowContext(), timeout=0.05)
        # asyncio.wait_for cancels the inner task → execute() catches
        # CancelledError and returns CANCELLED before TimeoutError propagates
        assert result.status in (FlowStatus.TIMEOUT, FlowStatus.CANCELLED)

    @pytest.mark.asyncio
    async def test_no_timeout(self):
        from aquilia.flow import FlowPipeline, FlowContext, FlowStatus

        async def fast_handler(ctx):
            return "fast"

        p = FlowPipeline("test").handler(fast_handler, name="h")
        result = await p.execute_with_timeout(FlowContext(), timeout=5.0)
        assert result.status == FlowStatus.SUCCESS


class TestEffectScope:
    """Test EffectScope async context manager."""

    @pytest.mark.asyncio
    async def test_scope_acquire_release(self):
        from aquilia.flow import EffectScope
        from aquilia.testing.effects import MockEffectRegistry

        registry = MockEffectRegistry()
        db_mock = registry.register_mock("DBTx", return_value="conn")

        async with EffectScope(registry, ["DBTx"]) as scope:
            assert "DBTx" in scope
            assert scope["DBTx"] == "conn"

        assert db_mock.acquire_count == 1
        assert db_mock.release_count == 1

    @pytest.mark.asyncio
    async def test_scope_release_on_error(self):
        from aquilia.flow import EffectScope
        from aquilia.testing.effects import MockEffectRegistry

        registry = MockEffectRegistry()
        db_mock = registry.register_mock("DBTx", return_value="conn")

        with pytest.raises(ValueError):
            async with EffectScope(registry, ["DBTx"]) as scope:
                raise ValueError("boom")

        assert db_mock.release_count == 1


class TestFactoryFunctions:
    """Test flow factory functions."""

    def test_pipeline_factory(self):
        from aquilia.flow import pipeline

        p = pipeline("test")
        assert p.name == "test"

    def test_guard_factory(self):
        from aquilia.flow import guard, FlowNodeType

        node = guard(lambda ctx: True, name="auth", priority=20)
        assert node.type == FlowNodeType.GUARD
        assert node.name == "auth"

    def test_transform_factory(self):
        from aquilia.flow import transform, FlowNodeType

        node = transform(lambda ctx: ctx, name="norm")
        assert node.type == FlowNodeType.TRANSFORM

    def test_handler_factory(self):
        from aquilia.flow import handler, FlowNodeType

        node = handler(lambda ctx: None, name="main")
        assert node.type == FlowNodeType.HANDLER

    def test_hook_factory(self):
        from aquilia.flow import hook, FlowNodeType

        node = hook(lambda ctx: None, name="log")
        assert node.type == FlowNodeType.HOOK


class TestFromPipelineList:
    """Test from_pipeline_list bridge."""

    def test_from_pipeline_list(self):
        from aquilia.flow import from_pipeline_list, FlowNode, FlowNodeType, PRIORITY_AUTH

        node1 = FlowNode(type=FlowNodeType.GUARD, callable=lambda ctx: True, name="g")
        node2 = FlowNode(type=FlowNodeType.TRANSFORM, callable=lambda ctx: ctx, name="t")

        p = from_pipeline_list([node1, node2], name="from_list")
        assert p.name == "from_list"
        assert len(p._nodes) == 2

    def test_from_pipeline_list_with_callables(self):
        from aquilia.flow import from_pipeline_list

        async def my_guard(ctx):
            return True

        async def my_handler(ctx):
            return "ok"

        p = from_pipeline_list([my_guard, my_handler])
        # Callables are treated as HANDLER by default
        assert len(p._nodes) == 2

    @pytest.mark.asyncio
    async def test_from_pipeline_list_class_token_resolves_dependencies(self):
        from aquilia.di import Container
        from aquilia.di.providers import ValueProvider
        from aquilia.flow import FlowContext, FlowStatus, from_pipeline_list

        class Dependency:
            def __init__(self):
                self.value = "ok"

        class ClassTokenGuard:
            def __init__(self, dep: Dependency):
                self.dep = dep

            async def __call__(self, context: dict[str, Any]) -> dict[str, Any]:
                context["dep_value"] = self.dep.value
                return context

        container = Container(scope="request")
        container.register(ValueProvider(value=Dependency(), token=Dependency, scope="request"))

        pipeline = from_pipeline_list([ClassTokenGuard], name="class-token")
        result = await pipeline.execute(FlowContext(container=container))

        assert result.status == FlowStatus.SUCCESS
        assert result.context is not None
        assert result.context.state["dep_value"] == "ok"

    @pytest.mark.asyncio
    async def test_from_pipeline_list_class_token_instantiated_once_per_execution(self):
        from aquilia.flow import FlowContext, FlowStatus, from_pipeline_list

        class StatelessGuard:
            init_count = 0

            def __init__(self):
                StatelessGuard.init_count += 1

            async def __call__(self, context: dict[str, Any]) -> dict[str, Any]:
                context["guard_hit"] = context.get("guard_hit", 0) + 1
                return context

        pipeline = from_pipeline_list([StatelessGuard, StatelessGuard], name="class-token-cache")
        result = await pipeline.execute(FlowContext())

        assert result.status == FlowStatus.SUCCESS
        assert result.context is not None
        assert result.context.state["guard_hit"] == 2
        assert StatelessGuard.init_count == 1

    @pytest.mark.asyncio
    async def test_from_pipeline_list_class_token_missing_provider_raises_di_fault(self):
        from aquilia.flow import FlowContext, FlowStatus, from_pipeline_list
        from aquilia.faults.domains import DIResolutionFault

        class MissingDependency:
            pass

        class GuardWithDependency:
            def __init__(self, dep: MissingDependency):
                self.dep = dep

            async def __call__(self, context: dict[str, Any]) -> dict[str, Any]:
                return context

        pipeline = from_pipeline_list([GuardWithDependency], name="class-token-missing-di")
        result = await pipeline.execute(FlowContext())

        assert result.status == FlowStatus.GUARDED
        assert isinstance(result.error, DIResolutionFault)


class TestMockFlowContext:
    """Test MockFlowContext helper."""

    def test_from_registry(self):
        from aquilia.testing.effects import MockEffectRegistry, MockFlowContext

        registry = MockEffectRegistry()
        registry.register_mock("DBTx", return_value="fake_conn")

        ctx = MockFlowContext.from_registry(registry, identity="user123")
        assert ctx.identity == "user123"
        assert ctx.effects["DBTx"] == "fake_conn"
        assert ctx.get_effect("DBTx") == "fake_conn"

    def test_create(self):
        from aquilia.testing.effects import MockFlowContext

        ctx = MockFlowContext.create(
            effects={"Cache": "cache_handle"},
            identity="admin",
            state={"role": "superadmin"},
        )
        assert ctx.get_effect("Cache") == "cache_handle"
        assert ctx.identity == "admin"
        assert ctx.get("role") == "superadmin"


# ════════════════════════════════════════════════════════════════════════
# MODULE 6: INTEGRATION — IMPORTS & EXPORTS
# ════════════════════════════════════════════════════════════════════════


class TestIntegrationImports:
    """Test that all new modules are importable."""

    def test_effect_middleware_import(self):
        from aquilia.middleware_ext.effect_middleware import EffectMiddleware, FlowContextMiddleware

        assert EffectMiddleware is not None
        assert FlowContextMiddleware is not None

    def test_effect_subsystem_import(self):
        from aquilia.subsystems.effects import EffectSubsystem

        assert EffectSubsystem is not None

    def test_middleware_ext_init_exports(self):
        from aquilia.middleware_ext import EffectMiddleware, FlowContextMiddleware

        assert EffectMiddleware is not None

    def test_subsystems_init_exports(self):
        from aquilia.subsystems import EffectSubsystem

        assert EffectSubsystem is not None


class TestTopLevelExports:
    """Verify all new symbols are accessible from `import aquilia`."""

    def test_flow_exports(self):
        import aquilia

        flow_symbols = [
            "FlowNode",
            "FlowNodeType",
            "FlowContext",
            "FlowPipeline",
            "FlowResult",
            "FlowStatus",
            "FlowError",
            "Layer",
            "LayerComposition",
            "EffectScope",
            "requires",
            "get_required_effects",
            "pipeline",
            "guard",
            "transform",
            "handler",
            "hook",
            "from_pipeline_list",
            "PRIORITY_CRITICAL",
            "PRIORITY_AUTH",
            "PRIORITY_VALIDATE",
            "PRIORITY_TRANSFORM",
            "PRIORITY_DEFAULT",
            "PRIORITY_ENRICH",
            "PRIORITY_LOG",
            "PRIORITY_CLEANUP",
        ]
        for sym in flow_symbols:
            assert hasattr(aquilia, sym), f"Missing from aquilia: {sym}"

    def test_effect_exports(self):
        import aquilia

        effect_symbols = [
            "Effect",
            "EffectKind",
            "EffectProvider",
            "EffectRegistry",
            "DBTx",
            "CacheEffect",
            "QueueEffect",
            "HTTPEffect",
            "StorageEffect",
            "DBTxProvider",
            "CacheProvider",
            "QueueProvider",
            "HTTPProvider",
            "StorageProvider",
        ]
        for sym in effect_symbols:
            assert hasattr(aquilia, sym), f"Missing from aquilia: {sym}"

    def test_flow_guard_exports(self):
        import aquilia

        guard_symbols = [
            "FlowGuard",
            "RequireAuthGuard",
            "RequireScopesGuard",
            "RequireRolesGuard",
            "RequirePermissionGuard",
            "RequirePolicyGuard",
            "ControllerGuardAdapter",
            "require_auth",
            "require_scopes",
            "require_roles",
            "require_permission",
        ]
        for sym in guard_symbols:
            assert hasattr(aquilia, sym), f"Missing from aquilia: {sym}"

    def test_all_in_dunder_all(self):
        import aquilia

        all_list = aquilia.__all__
        critical_symbols = [
            "FlowPipeline",
            "FlowContext",
            "FlowResult",
            "EffectRegistry",
            "Layer",
            "requires",
            "RequireAuthGuard",
            "require_auth",
        ]
        for sym in critical_symbols:
            assert sym in all_list, f"Missing from __all__: {sym}"


class TestExportIntegrity:
    """Verify exported classes match their module definitions."""

    def test_flow_pipeline_is_class(self):
        from aquilia import FlowPipeline

        assert inspect.isclass(FlowPipeline)

    def test_effect_registry_is_class(self):
        from aquilia import EffectRegistry

        assert inspect.isclass(EffectRegistry)

    def test_requires_is_function(self):
        from aquilia import requires

        assert callable(requires)

    def test_pipeline_is_function(self):
        from aquilia import pipeline

        assert callable(pipeline)

    def test_flow_guard_is_class(self):
        from aquilia import FlowGuard

        assert inspect.isclass(FlowGuard)

    def test_layer_is_class(self):
        from aquilia import Layer

        assert inspect.isclass(Layer)
