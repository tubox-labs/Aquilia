import pytest
from aquilia.models import F, Sum, Window, Rank, DenseRank, RowNumber, Ntile, Lag, Lead, FirstValue, LastValue, NthValue, FrameType, FrameBound, WindowFrame

def test_rank_as_sql():
    expr = Window(Rank(), partition_by=['country'], order_by='-score')
    sql, params = expr.as_sql('sqlite')
    assert sql == 'RANK() OVER (PARTITION BY "country" ORDER BY "score" DESC)'
    assert params == []

def test_sum_window_as_sql():
    expr = Window(Sum('amount'), partition_by='category', order_by='created_at')
    sql, params = expr.as_sql('sqlite')
    assert sql == 'SUM("amount") OVER (PARTITION BY "category" ORDER BY "created_at" ASC)'
    assert params == []

def test_window_frame():
    frame = WindowFrame(FrameType.ROWS, FrameBound.unbounded_preceding(), FrameBound.current_row())
    expr = Window(Sum('amount'), order_by='created_at', frame=frame)
    sql, params = expr.as_sql('sqlite')
    assert sql == 'SUM("amount") OVER (ORDER BY "created_at" ASC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)'
    assert params == []

def test_lag_lead():
    expr = Window(Lag('score', 2, 0), order_by='created_at')
    sql, params = expr.as_sql('sqlite')
    assert sql == 'LAG("score", ?, ?) OVER (ORDER BY "created_at" ASC)'
    assert params == [2, 0]

def test_ntile():
    expr = Window(Ntile(4), order_by='score')
    sql, params = expr.as_sql('sqlite')
    assert sql == 'NTILE(?) OVER (ORDER BY "score" ASC)'
    assert params == [4]

