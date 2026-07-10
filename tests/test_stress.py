import time

from aquilia.contracts import Contract


def test_high_nesting_depth_validation():
    # Construct a chain of nested contracts to verify depth limits or handling
    class Level5(Contract):
        val: int

    class Level4(Contract):
        child: Level5

    class Level3(Contract):
        child: Level4

    class Level2(Contract):
        child: Level3

    class Level1(Contract):
        child: Level2

    payload = {"child": {"child": {"child": {"child": {"val": 42}}}}}

    bp = Level1(data=payload)
    assert bp.is_sealed() is True
    assert bp.validated_data["child"]["child"]["child"]["child"]["val"] == 42


def test_concurrency_stress_parallel_validation():
    class StressBP(Contract):
        name: str
        value: int

        def validate_hook(self, data):
            # Simulate a small I/O delay to demonstrate ThreadPoolExecutor benefits
            time.sleep(0.001)
            return data

    rows = [{"name": f"user_{i}", "value": i} for i in range(100)]

    # Test sequential validation
    start_seq = time.perf_counter()
    seq_outcomes = StressBP.seal_many(rows, parallel=False)
    duration_seq = time.perf_counter() - start_seq

    assert len(seq_outcomes) == 100
    assert all(o.ok for o in seq_outcomes)

    # Test parallel validation
    start_par = time.perf_counter()
    par_outcomes = StressBP.seal_many(rows, parallel=True)
    duration_par = time.perf_counter() - start_par

    assert len(par_outcomes) == 100
    assert all(o.ok for o in par_outcomes)
