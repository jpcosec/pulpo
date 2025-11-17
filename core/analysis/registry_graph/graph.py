"""Core RegistryGraph - uses composition pattern."""

from pathlib import Path
from typing import Any

try:
    import networkx as nx
except ImportError:
    raise ImportError("NetworkX is required. Install with: pip install networkx")

from .node_manager import NodeManager
from .edge_manager import EdgeManager
from .query_engine import QueryEngine
from .validator import GraphValidator
from .persistence import GraphPersistence
from .exporters import GraphExporters


class RegistryGraph:
    """Persistent graph of models, tasks, and flows.

    Uses composition pattern to delegate responsibilities to specialized managers.
    Each manager handles a single aspect of graph operations.

    Attributes:
        project_name: Name of the project
        graph: NetworkX DiGraph instance
        metadata: Graph metadata (version, timestamps, etc.)
        nodes: NodeManager for node operations
        edges: EdgeManager for edge operations
        queries: QueryEngine for graph queries
        validator: GraphValidator for validation
        persistence: GraphPersistence for save/load
        exporters: GraphExporters for format exports
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

        # Composition: delegate to specialized managers
        self.nodes = NodeManager(self.graph)
        self.edges = EdgeManager(self.graph)
        self.queries = QueryEngine(self.graph)
        self.validator = GraphValidator(self.graph)
        self.persistence = GraphPersistence(self.graph, self.metadata)
        self.exporters = GraphExporters(self.graph)

    # ========== Facade Methods (delegate to managers) ==========

    # Node operations
    def add_datamodel(self, *args, **kwargs) -> str:
        """Add DataModel node. See NodeManager.add_datamodel()."""
        return self.nodes.add_datamodel(*args, **kwargs)

    def add_task(self, *args, **kwargs) -> str:
        """Add Task node. See NodeManager.add_task()."""
        return self.nodes.add_task(*args, **kwargs)

    def add_flow(self, *args, **kwargs) -> str:
        """Add Flow node. See NodeManager.add_flow()."""
        return self.nodes.add_flow(*args, **kwargs)

    # Edge operations
    def add_edge(self, *args, **kwargs) -> str:
        """Add edge. See EdgeManager.add_edge()."""
        return self.edges.add_edge(*args, **kwargs)

    # Query operations
    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get node by ID. See QueryEngine.get_node()."""
        return self.queries.get_node(node_id)

    def get_nodes_by_type(self, node_type: str) -> list[str]:
        """Get nodes by type. See QueryEngine.get_nodes_by_type()."""
        return self.queries.get_nodes_by_type(node_type)

    def get_tasks_by_flow(self, flow_path: str) -> list[str]:
        """Get tasks in flow. See QueryEngine.get_tasks_by_flow()."""
        return self.queries.get_tasks_by_flow(flow_path)

    def get_task_dependencies(self, task_id: str) -> list[str]:
        """Get task dependencies. See QueryEngine.get_task_dependencies()."""
        return self.queries.get_task_dependencies(task_id)

    def get_task_dependents(self, task_id: str) -> list[str]:
        """Get task dependents. See QueryEngine.get_task_dependents()."""
        return self.queries.get_task_dependents(task_id)

    def get_datamodels_read_by_task(self, task_id: str) -> list[str]:
        """Get models read by task. See QueryEngine.get_datamodels_read_by_task()."""
        return self.queries.get_datamodels_read_by_task(task_id)

    def get_datamodels_written_by_task(self, task_id: str) -> list[str]:
        """Get models written by task. See QueryEngine.get_datamodels_written_by_task()."""
        return self.queries.get_datamodels_written_by_task(task_id)

    def get_related_datamodels(self, datamodel_id: str) -> list[tuple[str, str]]:
        """Get related models. See QueryEngine.get_related_datamodels()."""
        return self.queries.get_related_datamodels(datamodel_id)

    def get_execution_order(self) -> list[str]:
        """Get execution order. See QueryEngine.get_execution_order()."""
        return self.queries.get_execution_order()

    def get_parallel_groups(self) -> list[list[str]]:
        """Get parallel groups. See QueryEngine.get_parallel_groups()."""
        return self.queries.get_parallel_groups()

    # Validation
    def validate(self) -> tuple[bool, list[str], list[str]]:
        """Validate graph. See GraphValidator.validate()."""
        return self.validator.validate()

    # Persistence
    def save(self, path: Path) -> None:
        """Save graph. See GraphPersistence.save()."""
        # Include validation results in save
        self.metadata["validation"] = {
            "has_errors": len(self.validator.errors) > 0,
            "errors": self.validator.errors,
            "warnings": self.validator.warnings
        }
        self.persistence.save(path)

    @classmethod
    def load(cls, path: Path) -> "RegistryGraph":
        """Load graph. See GraphPersistence.load()."""
        return GraphPersistence.load(path)

    # Export
    def export_mermaid(self, output_path: Path) -> None:
        """Export to Mermaid. See GraphExporters.export_mermaid()."""
        self.exporters.export_mermaid(output_path)

    def export_dot(self, output_path: Path) -> None:
        """Export to DOT. See GraphExporters.export_dot()."""
        self.exporters.export_dot(output_path)
