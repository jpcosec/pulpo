"""Node management for registry graph."""

from typing import Any

try:
    import networkx as nx
except ImportError:
    raise ImportError("NetworkX is required. Install with: pip install networkx")

from .types import NodeType


class NodeManager:
    """Manages graph nodes (DataModel, Task, Flow)."""

    def __init__(self, graph: nx.DiGraph):
        """Initialize node manager.

        Args:
            graph: NetworkX graph to manage nodes in
        """
        self._graph = graph

    def add_node(
        self,
        node_type: NodeType,
        node_id: str,
        **properties: Any
    ) -> str:
        """Add generic node to graph (extensible).

        Args:
            node_type: Type of node (datamodel, task, flow)
            node_id: Unique node identifier
            **properties: Additional node properties

        Returns:
            Node ID
        """
        self._graph.add_node(node_id, type=node_type, **properties)
        return node_id

    def add_datamodel(
        self,
        name: str,
        class_name: str,
        module: str,
        fields: dict[str, Any],
        **properties: Any
    ) -> str:
        """Add DataModel node.

        Args:
            name: Model name (e.g., "User")
            class_name: Python class name
            module: Python module path
            fields: Dict of field definitions
            **properties: Additional properties (searchable_fields, etc.)

        Returns:
            Node ID (e.g., "dm:User")
        """
        node_id = f"dm:{name}"
        return self.add_node(
            "datamodel",
            node_id,
            name=name,
            class_name=class_name,
            module=module,
            fields=fields,
            **properties
        )

    def add_task(
        self,
        name: str,
        full_name: str,
        flow_path: str,
        category: str,
        **properties: Any
    ) -> str:
        """Add Task node.

        Args:
            name: Task name (e.g., "create_user")
            full_name: Full hierarchical name (e.g., "user.create_user")
            flow_path: Parent flow path (e.g., "user.create")
            category: Task category
            **properties: Additional properties (async, input_schema, etc.)

        Returns:
            Node ID (e.g., "task:create_user")
        """
        node_id = f"task:{name}"
        return self.add_node(
            "task",
            node_id,
            name=name,
            full_name=full_name,
            flow_path=flow_path,
            category=category,
            **properties
        )

    def add_flow(
        self,
        name: str,
        full_path: str,
        level: int,
        parent_flow: str | None = None,
        **properties: Any
    ) -> str:
        """Add Flow node.

        Args:
            name: Flow name (e.g., "create")
            full_path: Full hierarchical path (e.g., "user.create")
            level: Hierarchy level (0 = root)
            parent_flow: Parent flow path (None for root)
            **properties: Additional properties

        Returns:
            Node ID (e.g., "flow:user.create")
        """
        node_id = f"flow:{full_path}"
        return self.add_node(
            "flow",
            node_id,
            name=name,
            full_path=full_path,
            level=level,
            parent_flow=parent_flow,
            **properties
        )
