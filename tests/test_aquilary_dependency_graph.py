import pytest

from aquilia.aquilary.errors import DependencyCycleError
from aquilia.aquilary.graph import DependencyGraph


def test_dependency_graph_basic_dag():
    """Test basic topological sort on a simple DAG."""
    g = DependencyGraph()
    # auth has no dependencies
    g.add_node("auth", [])
    # dashboard depends on auth
    g.add_node("dashboard", ["auth"])
    # payment depends on auth and dashboard
    g.add_node("payment", ["auth", "dashboard"])

    assert g.get_load_order() == ["auth", "dashboard", "payment"]
    assert g.get_roots() == ["auth"]
    assert sorted(g.get_leaves()) == ["payment"]


def test_dependency_graph_complex_dag():
    """Test complex DAG with multiple branches and levels."""
    g = DependencyGraph()
    g.add_node("core", [])
    g.add_node("auth", ["core"])
    g.add_node("billing", ["core"])
    g.add_node("dashboard", ["auth", "billing"])
    g.add_node("reports", ["dashboard"])

    order = g.get_load_order()
    # verify dependency constraint: each node appears after its dependencies
    indices = {name: idx for idx, name in enumerate(order)}
    assert indices["core"] < indices["auth"]
    assert indices["core"] < indices["billing"]
    assert indices["auth"] < indices["dashboard"]
    assert indices["billing"] < indices["dashboard"]
    assert indices["dashboard"] < indices["reports"]

    assert g.get_roots() == ["core"]
    assert g.get_leaves() == ["reports"]


def test_dependency_graph_parallel_layers():
    """Test resolution of parallel execution layers."""
    g = DependencyGraph()
    g.add_node("core", [])
    g.add_node("auth", ["core"])
    g.add_node("billing", ["core"])
    g.add_node("analytics", [])

    layers = g.get_layers()
    # Layer 0: nodes with no dependencies (core, analytics)
    assert set(layers[0]) == {"core", "analytics"}
    # Layer 1: nodes depending only on Layer 0 (auth, billing)
    assert set(layers[1]) == {"auth", "billing"}


def test_dependency_graph_transitive_dependencies():
    """Test transitive dependency closure resolution."""
    g = DependencyGraph()
    g.add_node("core", [])
    g.add_node("auth", ["core"])
    g.add_node("dashboard", ["auth"])
    g.add_node("reports", ["dashboard"])

    assert g.get_transitive_dependencies("reports") == {"core", "auth", "dashboard"}
    assert g.get_transitive_dependencies("dashboard") == {"core", "auth"}
    assert g.get_transitive_dependencies("core") == set()


def test_dependency_graph_cycle_detection():
    """Test that circular dependencies raise DependencyCycleError."""
    g = DependencyGraph()
    g.add_node("auth", ["dashboard"])
    g.add_node("dashboard", ["payment"])
    g.add_node("payment", ["auth"])

    with pytest.raises(DependencyCycleError) as exc:
        g.get_load_order()

    assert "Circular dependency detected" in str(exc.value)
    # The cycle should contain the involved modules
    assert set(exc.value.cycle).issubset({"auth", "dashboard", "payment"})


def test_dependency_graph_self_loop_detection():
    """Test that a self-loop (depends on itself) raises DependencyCycleError."""
    g = DependencyGraph()
    g.add_node("auth", ["auth"])

    # Verify Tarjan finds the cycle
    assert g.find_cycle() == ["auth", "auth"]

    # Verify Kahn/Tarjan raises circular dependency exception
    with pytest.raises(DependencyCycleError) as exc:
        g.get_load_order()

    assert "Circular dependency detected: auth → auth → auth" in str(exc.value)
    assert exc.value.cycle == ["auth", "auth"]
