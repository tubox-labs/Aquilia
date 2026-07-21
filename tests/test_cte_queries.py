import pytest
from aquilia.models import Q
from aquilia.models.cte import CTE, RecursiveCTE, CTEReference

def test_cte_as_sql():
    q = Q('users', None, None)
    q = q.filter(is_active=True)
    cte = q.cte('active_users')
    sql, params = cte.as_sql('sqlite')
    assert sql == '"active_users" AS (SELECT * FROM "users" WHERE ("is_active" = ?))'
    assert params == [True]

def test_with_cte_query():
    q = Q('users', None, None).filter(is_active=True)
    cte = q.cte('active_users')
    main_q = Q('active_users', None, None).with_cte(cte)
    sql, params = main_q._build_select()
    assert sql == 'WITH "active_users" AS (SELECT * FROM "users" WHERE ("is_active" = ?)) SELECT * FROM "active_users"'
    assert params == [True]

def test_recursive_cte():
    q = Q('folder', None, None)
    result = q.recursive_cte(
        name='folder_tree',
        anchor=lambda q: q.filter(parent_id__isnull=True),
        recursive=lambda cte: Q('folder', None, None).filter(parent_id=cte.col('id')),
    )
    sql, params = result._build_select()
    assert sql.startswith('WITH RECURSIVE "folder_tree" AS (SELECT * FROM "folder" WHERE ("parent_id" IS NULL) UNION ALL SELECT * FROM "folder" WHERE ("parent_id" = "folder_tree"."id")) SELECT * FROM "folder_tree"')
    
