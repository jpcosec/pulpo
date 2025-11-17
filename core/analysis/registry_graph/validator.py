"""Graph validation."""

try:
    import networkx as nx
except ImportError:
    raise ImportError("NetworkX is required. Install with: pip install networkx")


class GraphValidator:
    """Validates graph integrity."""

    def __init__(self, graph: nx.DiGraph):
        """Initialize validator.

        Args:
            graph: NetworkX graph to validate
        """
        self._graph = graph
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self) -> tuple[bool, list[str], list[str]]:
        """Run all validations.

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        self._check_cycles()
        self._check_unused_models()
        self._check_orphan_tasks()

        return len(self.errors) == 0, self.errors, self.warnings

    def _check_cycles(self) -> None:
        """Check for circular dependencies in task graph."""
        # Build subgraph of only task dependencies
        task_deps = nx.DiGraph()
        for source, target, data in self._graph.edges(data=True):
            if data.get("type") == "DEPENDS_ON":
                task_deps.add_edge(source, target)

        try:
            cycles = list(nx.simple_cycles(task_deps))
            for cycle in cycles:
                cycle_str = " → ".join(cycle + [cycle[0]])
                self.errors.append(f"Circular dependency detected: {cycle_str}")
        except Exception as e:
            self.errors.append(f"Error checking cycles: {e}")

    def _check_unused_models(self) -> None:
        """Check for DataModels not used by any task."""
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") != "datamodel":
                continue

            # Check if any task reads/writes this model
            has_usage = any(
                edge_data.get("type") in ("READS", "WRITES", "DELETES")
                for _, _, edge_data in self._graph.in_edges(node_id, data=True)
            )

            if not has_usage:
                self.warnings.append(
                    f"DataModel '{data.get('name', node_id)}' is not used by any task"
                )

    def _check_orphan_tasks(self) -> None:
        """Check for tasks not contained in any flow."""
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") != "task":
                continue

            # Check if task is in a flow
            has_flow = any(
                edge_data.get("type") == "CONTAINS_TASK"
                for _, _, edge_data in self._graph.in_edges(node_id, data=True)
            )

            if not has_flow:
                self.warnings.append(
                    f"Task '{data.get('name', node_id)}' is not contained in any flow"
                )
