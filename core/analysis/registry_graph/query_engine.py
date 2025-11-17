"""Query operations for registry graph."""

from typing import Any

try:
    import networkx as nx
except ImportError:
    raise ImportError("NetworkX is required. Install with: pip install networkx")


class QueryEngine:
    """Handles graph queries."""

    def __init__(self, graph: nx.DiGraph):
        """Initialize query engine.

        Args:
            graph: NetworkX graph to query
        """
        self._graph = graph

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node data dict or None if not found
        """
        if node_id in self._graph:
            return dict(self._graph.nodes[node_id])
        return None

    def get_nodes_by_type(self, node_type: str) -> list[str]:
        """Get all nodes of a specific type.

        Args:
            node_type: Type to filter by

        Returns:
            List of node IDs
        """
        return [
            node_id
            for node_id, data in self._graph.nodes(data=True)
            if data.get("type") == node_type
        ]

    def get_tasks_by_flow(self, flow_path: str) -> list[str]:
        """Get all tasks in a flow.

        Args:
            flow_path: Flow path (e.g., "user.create")

        Returns:
            List of task IDs
        """
        flow_id = f"flow:{flow_path}"
        if flow_id not in self._graph:
            return []

        return [
            target
            for _, target, data in self._graph.out_edges(flow_id, data=True)
            if data.get("type") == "CONTAINS_TASK"
        ]

    def get_task_dependencies(self, task_id: str) -> list[str]:
        """Get tasks this task depends on.

        Args:
            task_id: Task identifier

        Returns:
            List of task IDs this task depends on
        """
        return [
            source
            for source, _, data in self._graph.in_edges(task_id, data=True)
            if data.get("type") == "DEPENDS_ON"
        ]

    def get_task_dependents(self, task_id: str) -> list[str]:
        """Get tasks that depend on this task.

        Args:
            task_id: Task identifier

        Returns:
            List of task IDs that depend on this task
        """
        return [
            target
            for _, target, data in self._graph.out_edges(task_id, data=True)
            if data.get("type") == "DEPENDS_ON"
        ]

    def get_datamodels_read_by_task(self, task_id: str) -> list[str]:
        """Get DataModels read by this task.

        Args:
            task_id: Task identifier

        Returns:
            List of DataModel IDs
        """
        return [
            target
            for _, target, data in self._graph.out_edges(task_id, data=True)
            if data.get("type") == "READS"
        ]

    def get_datamodels_written_by_task(self, task_id: str) -> list[str]:
        """Get DataModels written by this task.

        Args:
            task_id: Task identifier

        Returns:
            List of DataModel IDs
        """
        return [
            target
            for _, target, data in self._graph.out_edges(task_id, data=True)
            if data.get("type") == "WRITES"
        ]

    def get_related_datamodels(self, datamodel_id: str) -> list[tuple[str, str]]:
        """Get DataModels related to this one.

        Args:
            datamodel_id: DataModel identifier

        Returns:
            List of (relation_type, target_model_id) tuples
        """
        relations = []
        for _, target, data in self._graph.out_edges(datamodel_id, data=True):
            edge_type = data.get("type")
            if edge_type in ("HAS_RELATION", "CONTAINS_LIST", "INHERITS_FROM"):
                relations.append((edge_type, target))
        return relations

    def get_execution_order(self) -> list[str]:
        """Get tasks in execution order (topological sort).

        Returns:
            List of task IDs in execution order

        Raises:
            ValueError: If circular dependencies exist
        """
        # Filter graph to only task dependencies
        task_graph = nx.DiGraph()
        for source, target, data in self._graph.edges(data=True):
            if data.get("type") == "DEPENDS_ON":
                task_graph.add_edge(source, target)

        try:
            return list(nx.topological_sort(task_graph))
        except nx.NetworkXError as e:
            raise ValueError(f"Cannot compute execution order: {e}")

    def get_parallel_groups(self) -> list[list[str]]:
        """Get tasks grouped by execution level.

        Tasks in the same group can run in parallel.

        Returns:
            List of groups, where each group can run in parallel
        """
        try:
            execution_order = self.get_execution_order()
        except ValueError:
            return []

        # Compute level for each task
        levels: dict[str, int] = {}
        for task_id in execution_order:
            deps = self.get_task_dependencies(task_id)
            if not deps:
                levels[task_id] = 0
            else:
                levels[task_id] = max(levels.get(d, 0) for d in deps) + 1

        # Group by level
        level_groups: dict[int, list[str]] = {}
        for task_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(task_id)

        return [level_groups[level] for level in sorted(level_groups.keys())]
