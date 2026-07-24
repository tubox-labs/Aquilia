"""
Dependency graph analysis with Tarjan's algorithm for cycle detection.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass
class GraphNode:
    """Dependency graph node."""

    name: str
    dependencies: list[str] = field(default_factory=list)

    # Tarjan's algorithm state
    index: int | None = None
    lowlink: int | None = None
    on_stack: bool = False

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GraphNode):
            return NotImplemented
        return self.name == other.name


class DependencyGraph:
    """
    Dependency graph with cycle detection and topological sorting.

    Uses Tarjan's strongly connected components algorithm for O(V+E) cycle detection.
    """

    def __init__(self):
        self._nodes: dict[str, GraphNode] = {}
        self._adjacency: dict[str, list[str]] = {}

    def add_node(self, name: str, dependencies: list[str]) -> None:
        """
        Add node to graph.

        Args:
            name: Node name
            dependencies: List of dependency names
        """
        node = GraphNode(name=name, dependencies=dependencies)
        self._nodes[name] = node
        self._adjacency[name] = dependencies

        # Ensure all dependencies exist as nodes
        for dep in dependencies:
            if dep not in self._nodes:
                self._nodes[dep] = GraphNode(name=dep)
                self._adjacency[dep] = []

    def topological_sort(self) -> list[str]:
        """
        Compute topological sort of graph (dependency order).

        Returns:
            List of node names in dependency order (dependencies first)

        Raises:
            DependencyCycleError: If cycle detected
        """
        # Check for cycles first
        cycle = self.find_cycle()
        if cycle:
            from .errors import DependencyCycleError

            raise DependencyCycleError(cycle=cycle)

        # Kahn's algorithm for topological sort
        in_degree: dict[str, int] = {name: 0 for name in self._nodes}

        for _name, deps in self._adjacency.items():
            for dep in deps:
                in_degree[dep] += 1

        # Start with nodes that have no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            node_name = queue.pop(0)
            result.append(node_name)

            # Process dependencies
            for dep_name in self._adjacency.get(node_name, []):
                in_degree[dep_name] -= 1
                if in_degree[dep_name] == 0:
                    queue.append(dep_name)

        # Reverse to get dependency-first order
        res = list(reversed(result))
        if len(res) != len(self._nodes):
            from .errors import DependencyCycleError

            cycle = self.find_cycle() or list(self._nodes.keys())
            raise DependencyCycleError(cycle=cycle)
        return res

    def find_cycle(self) -> list[str] | None:
        """
        Find cycle in graph using Tarjan's algorithm.

        Returns:
            List of node names forming cycle, or None if no cycle

        Implementation note
        -------------------
        BUG FIX (audit \u00a711 #3): the previous implementation used a
        recursive inner function (strongconnect) which risked RecursionError
        on deep-but-acyclic dependency chains due to CPython's default
        recursion limit (~1000 frames).  This version uses an explicit work-
        stack so depth is limited only by heap memory, not the call stack.
        Semantics are identical to the recursive Tarjan SCC algorithm.
        """
        index_counter = [0]
        stack: list[str] = []
        lowlinks: dict[str, int] = {}
        index: dict[str, int] = {}
        on_stack: set[str] = set()
        cycles: list[list[str]] = []

        # Work-stack entry: (node_name, iterator_over_its_neighbours, started)
        # 'started' is True once we have assigned index/lowlink to this node.
        def _strongconnect_iterative(root: str) -> None:
            # Each frame: (node_name, dep_iterator)
            frame_stack: list[tuple[str, Iterator[str]]] = []

            def _enter(node_name: str) -> None:
                index[node_name] = index_counter[0]
                lowlinks[node_name] = index_counter[0]
                index_counter[0] += 1
                stack.append(node_name)
                on_stack.add(node_name)
                frame_stack.append((node_name, iter(self._adjacency.get(node_name, []))))

            _enter(root)

            while frame_stack:
                node_name, dep_iter = frame_stack[-1]

                try:
                    dep_name = next(dep_iter)
                except StopIteration:
                    # All neighbours processed — check if this is an SCC root.
                    frame_stack.pop()
                    if frame_stack:
                        parent_name = frame_stack[-1][0]
                        lowlinks[parent_name] = min(lowlinks[parent_name], lowlinks[node_name])
                    if lowlinks[node_name] == index[node_name]:
                        component: list[str] = []
                        while True:
                            w = stack.pop()
                            on_stack.remove(w)
                            component.append(w)
                            if w == node_name:
                                break
                        if len(component) > 1:
                            cycles.append(component)
                        elif len(component) == 1:
                            single = component[0]
                            if single in self._adjacency.get(single, []):
                                cycles.append([single, single])
                    continue

                if dep_name not in index:
                    _enter(dep_name)
                elif dep_name in on_stack:
                    lowlinks[node_name] = min(lowlinks[node_name], index[dep_name])

        for node_name in self._nodes:
            if node_name not in index:
                _strongconnect_iterative(node_name)

        if cycles:
            return cycles[0]
        return None

    def get_dependencies(self, node_name: str) -> list[str]:
        """
        Get direct dependencies of node.

        Args:
            node_name: Node name

        Returns:
            List of dependency names
        """
        return self._adjacency.get(node_name, [])

    def get_transitive_dependencies(self, node_name: str) -> set[str]:
        """
        Get transitive closure of dependencies.

        Args:
            node_name: Node name

        Returns:
            Set of all transitive dependency names

        Implementation note
        -------------------
        BUG FIX (audit \u00a711 #3 companion): the previous recursive visit()
        also risked RecursionError on deep chains.  Replaced with iterative
        DFS using an explicit work-stack.
        """
        visited: set[str] = set()
        work_stack = list(self._adjacency.get(node_name, []))
        while work_stack:
            current = work_stack.pop()
            if current in visited:
                continue
            visited.add(current)
            work_stack.extend(self._adjacency.get(current, []))
        visited.discard(node_name)  # Remove self
        return visited

    def get_dependents(self, node_name: str) -> list[str]:
        """
        Get nodes that depend on given node (reverse dependencies).

        Args:
            node_name: Node name

        Returns:
            List of dependent node names
        """
        dependents: list[str] = []
        for name, deps in self._adjacency.items():
            if node_name in deps:
                dependents.append(name)
        return dependents

    def to_dict(self) -> dict[str, list[str]]:
        """
        Export graph as adjacency dict.

        Returns:
            Dict mapping node names to dependency lists
        """
        return self._adjacency.copy()

    def to_dot(self) -> str:
        """
        Export graph as DOT format for visualization.

        Returns:
            DOT graph string
        """
        lines = ["digraph dependencies {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=rounded];")

        # Add nodes
        for name in self._nodes:
            lines.append(f'  "{name}";')

        # Add edges
        for name, deps in self._adjacency.items():
            for dep in deps:
                lines.append(f'  "{name}" -> "{dep}";')

        lines.append("}")
        return "\n".join(lines)

    def get_load_order(self) -> list[str]:
        """
        Get load order (topological sort).

        Alias for topological_sort().

        Returns:
            List of node names in load order
        """
        return self.topological_sort()

    def validate(self) -> tuple[bool, list[str] | None]:
        """
        Validate graph for cycles.

        Returns:
            Tuple of (is_valid, cycle_if_invalid)
        """
        cycle = self.find_cycle()
        return (cycle is None, cycle)

    def get_roots(self) -> list[str]:
        """
        Get root nodes (no dependencies).

        Returns:
            List of root node names
        """
        roots: list[str] = []
        for name, deps in self._adjacency.items():
            if not deps:
                roots.append(name)
        return roots

    def get_leaves(self) -> list[str]:
        """
        Get leaf nodes (no dependents).

        Returns:
            List of leaf node names
        """
        has_dependents: set[str] = set()
        for deps in self._adjacency.values():
            has_dependents.update(deps)

        leaves: list[str] = []
        for name in self._nodes:
            if name not in has_dependents:
                leaves.append(name)

        return leaves

    def get_layers(self) -> list[list[str]]:
        """
        Get dependency layers (parallel execution groups).

        Returns:
            List of layers, each layer contains nodes that can be loaded in parallel
        """
        layers: list[list[str]] = []
        remaining = set(self._nodes.keys())
        loaded: set[str] = set()

        while remaining:
            # Find nodes whose dependencies are all loaded
            layer: list[str] = []
            for name in remaining:
                deps = set(self._adjacency.get(name, []))
                if deps.issubset(loaded):
                    layer.append(name)

            if not layer:
                # Cycle detected
                break

            layers.append(layer)
            remaining -= set(layer)
            loaded.update(layer)

        return layers

    def __len__(self) -> int:
        """Get number of nodes in graph."""
        return len(self._nodes)

    def __contains__(self, name: str) -> bool:
        """Check if node exists in graph."""
        return name in self._nodes

    def __repr__(self) -> str:
        return f"DependencyGraph({len(self._nodes)} nodes)"
