"""Registry Graph - Persistent graph of models, tasks, and flows.

This module implements a persistent graph representation of the project's
data models, operations (tasks), and hierarchical flows. The graph is built
during discovery and persisted to disk for validation and visualization.

Example:
    >>> from core.analysis.registry_graph import RegistryGraph
    >>> graph = RegistryGraph("my-project")
    >>>
    >>> # Add nodes
    >>> graph.add_datamodel("User", class_name="User", module="models.user", fields={})
    >>> graph.add_task("create_user", full_name="user.create_user", flow_path="user", category="user")
    >>>
    >>> # Add relationships
    >>> graph.add_edge("WRITES", "task:create_user", "dm:User")
    >>>
    >>> # Validate
    >>> is_valid, errors, warnings = graph.validate()
    >>>
    >>> # Save
    >>> graph.save(Path(".pulpo/registry_graph.json"))
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal
from dataclasses import dataclass, field
from datetime import datetime

try:
    import networkx as nx
except ImportError:
    raise ImportError(
        "NetworkX is required for RegistryGraph. Install with: pip install networkx"
    )

NodeType = Literal["datamodel", "task", "flow"]
EdgeType = Literal[
    # DataModel ↔ DataModel
    "HAS_RELATION", "CONTAINS_LIST", "INHERITS_FROM",
    # Task → DataModel
    "READS", "WRITES", "DELETES",
    # Task → Task
    "DEPENDS_ON", "RUNS_PARALLEL",
    # Flow → Flow
    "CONTAINS_SUBFLOW",
    # Flow → Task
    "CONTAINS_TASK"
]


@dataclass
class GraphNode:
    """Graph node with type and properties."""
    id: str
    type: NodeType
    name: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """Graph edge with type and properties."""
    id: str
    type: EdgeType
    source: str
    target: str
    properties: dict[str, Any] = field(default_factory=dict)


class RegistryGraph:
    """Persistent graph of models, tasks, and flows.

    This graph is built during discovery (init/scan) and persisted to disk.
    It enables:
    - Early error detection (before compile)
    - Visualization of relationships
    - Complex queries on data flow
    - Validation of graph integrity

    Attributes:
        project_name: Name of the project
        graph: NetworkX DiGraph instance
        metadata: Graph metadata (version, timestamps, etc.)
        validation_errors: List of validation errors
        validation_warnings: List of validation warnings
    """

    def __init__(self, project_name: str):
        """Initialize empty graph.

        Args:
            project_name: Name of the project
        """
        self.project_name = project_name
        self.graph = nx.DiGraph()
        self.metadata = {
            "version": "1.0.0",
            "generated_at": None,
            "project_name": project_name,
        }
        self.validation_errors: list[str] = []
        self.validation_warnings: list[str] = []

    # ========== Node Management ==========

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
        self.graph.add_node(
            node_id,
            type=node_type,
            **properties
        )
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

    # ========== Edge Management ==========

    def add_edge(
        self,
        edge_type: EdgeType,
        source: str,
        target: str,
        **properties: Any
    ) -> str:
        """Add edge between nodes.

        Args:
            edge_type: Type of relationship
            source: Source node ID
            target: Target node ID
            **properties: Additional edge properties

        Returns:
            Edge ID
        """
        edge_id = f"e_{len(self.graph.edges)}"
        self.graph.add_edge(
            source,
            target,
            id=edge_id,
            type=edge_type,
            **properties
        )
        return edge_id

    # ========== Queries ==========

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node data dict or None if not found
        """
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def get_nodes_by_type(self, node_type: NodeType) -> list[str]:
        """Get all nodes of a specific type.

        Args:
            node_type: Type to filter by

        Returns:
            List of node IDs
        """
        return [
            node_id
            for node_id, data in self.graph.nodes(data=True)
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
        if flow_id not in self.graph:
            return []

        # Find all tasks connected via CONTAINS_TASK
        tasks = []
        for _, target, data in self.graph.out_edges(flow_id, data=True):
            if data.get("type") == "CONTAINS_TASK":
                tasks.append(target)
        return tasks

    def get_task_dependencies(self, task_id: str) -> list[str]:
        """Get tasks this task depends on.

        Args:
            task_id: Task identifier

        Returns:
            List of task IDs this task depends on
        """
        deps = []
        for source, _, data in self.graph.in_edges(task_id, data=True):
            if data.get("type") == "DEPENDS_ON":
                deps.append(source)
        return deps

    def get_task_dependents(self, task_id: str) -> list[str]:
        """Get tasks that depend on this task.

        Args:
            task_id: Task identifier

        Returns:
            List of task IDs that depend on this task
        """
        dependents = []
        for _, target, data in self.graph.out_edges(task_id, data=True):
            if data.get("type") == "DEPENDS_ON":
                dependents.append(target)
        return dependents

    def get_datamodels_read_by_task(self, task_id: str) -> list[str]:
        """Get DataModels read by this task.

        Args:
            task_id: Task identifier

        Returns:
            List of DataModel IDs
        """
        models = []
        for _, target, data in self.graph.out_edges(task_id, data=True):
            if data.get("type") == "READS":
                models.append(target)
        return models

    def get_datamodels_written_by_task(self, task_id: str) -> list[str]:
        """Get DataModels written by this task.

        Args:
            task_id: Task identifier

        Returns:
            List of DataModel IDs
        """
        models = []
        for _, target, data in self.graph.out_edges(task_id, data=True):
            if data.get("type") == "WRITES":
                models.append(target)
        return models

    def get_related_datamodels(self, datamodel_id: str) -> list[tuple[str, str]]:
        """Get DataModels related to this one.

        Args:
            datamodel_id: DataModel identifier

        Returns:
            List of (relation_type, target_model_id) tuples
        """
        relations = []
        for _, target, data in self.graph.out_edges(datamodel_id, data=True):
            edge_type = data.get("type")
            if edge_type in ("HAS_RELATION", "CONTAINS_LIST", "INHERITS_FROM"):
                relations.append((edge_type, target))
        return relations

    # ========== Validation ==========

    def validate(self) -> tuple[bool, list[str], list[str]]:
        """Validate graph integrity.

        Checks:
        - Circular dependencies in task graph
        - Unused DataModels
        - Orphan tasks (not in any flow)

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Check for cycles in task dependencies
        try:
            # Build subgraph of only task dependencies
            task_deps = nx.DiGraph()
            for source, target, data in self.graph.edges(data=True):
                if data.get("type") == "DEPENDS_ON":
                    task_deps.add_edge(source, target)

            cycles = list(nx.simple_cycles(task_deps))
            if cycles:
                for cycle in cycles:
                    cycle_str = " → ".join(cycle + [cycle[0]])
                    errors.append(f"Circular dependency detected: {cycle_str}")
        except Exception as e:
            errors.append(f"Error checking cycles: {e}")

        # Check for unused DataModels
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "datamodel":
                # Check if any task reads/writes this model
                has_usage = False
                for _, _, edge_data in self.graph.in_edges(node_id, data=True):
                    if edge_data.get("type") in ("READS", "WRITES", "DELETES"):
                        has_usage = True
                        break

                if not has_usage:
                    warnings.append(
                        f"DataModel '{data.get('name', node_id)}' is not used by any task"
                    )

        # Check for orphan tasks (no flow)
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "task":
                has_flow = False
                for source, _, edge_data in self.graph.in_edges(node_id, data=True):
                    if edge_data.get("type") == "CONTAINS_TASK":
                        has_flow = True
                        break

                if not has_flow:
                    warnings.append(
                        f"Task '{data.get('name', node_id)}' is not contained in any flow"
                    )

        self.validation_errors = errors
        self.validation_warnings = warnings

        return len(errors) == 0, errors, warnings

    # ========== Topological Sort ==========

    def get_execution_order(self) -> list[str]:
        """Get tasks in execution order (topological sort).

        Returns:
            List of task IDs in execution order

        Raises:
            ValueError: If circular dependencies exist
        """
        # Filter graph to only task dependencies
        task_graph = nx.DiGraph()
        for source, target, data in self.graph.edges(data=True):
            if data.get("type") == "DEPENDS_ON":
                task_graph.add_edge(source, target)

        try:
            return list(nx.topological_sort(task_graph))
        except nx.NetworkXError as e:
            raise ValueError(f"Cannot compute execution order: {e}")

    def get_parallel_groups(self) -> list[list[str]]:
        """Get tasks grouped by execution level (parallel groups).

        Tasks in the same group can run in parallel (no dependencies between them).

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

    # ========== Persistence ==========

    def save(self, path: Path) -> None:
        """Save graph to JSON file.

        Args:
            path: Path to save file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        self.metadata["generated_at"] = datetime.utcnow().isoformat()

        # Convert networkx graph to JSON-serializable format
        data = {
            "metadata": self.metadata,
            "nodes": {
                node_id: dict(data)
                for node_id, data in self.graph.nodes(data=True)
            },
            "edges": [
                {
                    "id": data.get("id", f"e{i}"),
                    "type": data.get("type"),
                    "source": source,
                    "target": target,
                    "properties": {
                        k: v for k, v in data.items()
                        if k not in ("id", "type")
                    }
                }
                for i, (source, target, data) in enumerate(self.graph.edges(data=True))
            ],
            "indexes": self._build_indexes(),
            "validation": {
                "has_errors": len(self.validation_errors) > 0,
                "errors": self.validation_errors,
                "warnings": self.validation_warnings
            }
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "RegistryGraph":
        """Load graph from JSON file.

        Args:
            path: Path to load file

        Returns:
            RegistryGraph instance
        """
        with open(path) as f:
            data = json.load(f)

        graph = cls(data["metadata"]["project_name"])
        graph.metadata = data["metadata"]

        # Rebuild networkx graph
        for node_id, node_data in data["nodes"].items():
            graph.graph.add_node(node_id, **node_data)

        for edge in data["edges"]:
            graph.graph.add_edge(
                edge["source"],
                edge["target"],
                id=edge["id"],
                type=edge["type"],
                **edge.get("properties", {})
            )

        graph.validation_errors = data.get("validation", {}).get("errors", [])
        graph.validation_warnings = data.get("validation", {}).get("warnings", [])

        return graph

    def _build_indexes(self) -> dict[str, Any]:
        """Build indexes for fast lookups.

        Returns:
            Dict of indexes
        """
        indexes = {
            "by_type": {},
            "by_flow": {},
            "by_category": {}
        }

        # Index by type
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("type")
            if node_type not in indexes["by_type"]:
                indexes["by_type"][node_type] = []
            indexes["by_type"][node_type].append(node_id)

        # Index tasks by flow
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "task":
                flow_path = data.get("flow_path")
                if flow_path:
                    if flow_path not in indexes["by_flow"]:
                        indexes["by_flow"][flow_path] = []
                    indexes["by_flow"][flow_path].append(node_id)

        # Index tasks by category
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "task":
                category = data.get("category")
                if category:
                    if category not in indexes["by_category"]:
                        indexes["by_category"][category] = []
                    indexes["by_category"][category].append(node_id)

        return indexes

    # ========== Export ==========

    def export_mermaid(self, output_path: Path) -> None:
        """Export graph to Mermaid format.

        Args:
            output_path: Path to save Mermaid file
        """
        lines = ["graph TD"]
        lines.append("")

        # Add nodes
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("type")
            name = data.get("name", node_id)

            if node_type == "datamodel":
                lines.append(f'    {node_id.replace(":", "_")}["{name}<br/>DataModel"]')
            elif node_type == "task":
                lines.append(f'    {node_id.replace(":", "_")}("{name}<br/>Task")')
            elif node_type == "flow":
                lines.append(f'    {node_id.replace(":", "_")}{{{{{name}<br/>Flow}}}}')

        lines.append("")

        # Add edges
        for source, target, data in self.graph.edges(data=True):
            edge_type = data.get("type", "")
            source_clean = source.replace(":", "_")
            target_clean = target.replace(":", "_")
            lines.append(f'    {source_clean} -->|{edge_type}| {target_clean}')

        output_path.write_text("\n".join(lines))

    def export_dot(self, output_path: Path) -> None:
        """Export graph to GraphViz DOT format.

        Args:
            output_path: Path to save DOT file
        """
        try:
            from networkx.drawing.nx_pydot import write_dot
            write_dot(self.graph, output_path)
        except ImportError:
            raise ImportError(
                "pydot is required for DOT export. Install with: pip install pydot"
            )
