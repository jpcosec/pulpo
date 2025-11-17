"""Graph persistence (save/load)."""

import json
from pathlib import Path
from datetime import datetime
from typing import Any

try:
    import networkx as nx
except ImportError:
    raise ImportError("NetworkX is required. Install with: pip install networkx")


class GraphPersistence:
    """Handles save/load operations."""

    def __init__(self, graph: nx.DiGraph, metadata: dict[str, Any]):
        """Initialize persistence manager.

        Args:
            graph: NetworkX graph to persist
            metadata: Graph metadata
        """
        self._graph = graph
        self._metadata = metadata

    def save(self, path: Path) -> None:
        """Save graph to JSON file.

        Args:
            path: Path to save file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        self._metadata["generated_at"] = datetime.utcnow().isoformat()

        data = {
            "metadata": self._metadata,
            "nodes": self._serialize_nodes(),
            "edges": self._serialize_edges(),
            "indexes": self._build_indexes(),
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(path: Path):
        """Load graph from JSON file.

        Args:
            path: Path to load file

        Returns:
            RegistryGraph instance
        """
        with open(path) as f:
            data = json.load(f)

        # Import here to avoid circular dependency
        from .graph import RegistryGraph

        graph = RegistryGraph(data["metadata"]["project_name"])
        graph.metadata = data["metadata"]

        # Rebuild graph
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

        # Restore validation state
        if "validation" in data:
            graph.validator.errors = data["validation"].get("errors", [])
            graph.validator.warnings = data["validation"].get("warnings", [])

        return graph

    def _serialize_nodes(self) -> dict[str, Any]:
        """Convert nodes to JSON-serializable format.

        Returns:
            Dict mapping node IDs to node data
        """
        return {
            node_id: dict(data)
            for node_id, data in self._graph.nodes(data=True)
        }

    def _serialize_edges(self) -> list[dict[str, Any]]:
        """Convert edges to JSON-serializable format.

        Returns:
            List of edge dicts
        """
        return [
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
            for i, (source, target, data) in enumerate(self._graph.edges(data=True))
        ]

    def _build_indexes(self) -> dict[str, Any]:
        """Build lookup indexes.

        Returns:
            Dict of indexes for fast lookups
        """
        indexes = {
            "by_type": {},
            "by_flow": {},
            "by_category": {}
        }

        # Index by type
        for node_id, data in self._graph.nodes(data=True):
            node_type = data.get("type")
            if node_type not in indexes["by_type"]:
                indexes["by_type"][node_type] = []
            indexes["by_type"][node_type].append(node_id)

        # Index tasks by flow
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") == "task":
                flow_path = data.get("flow_path")
                if flow_path:
                    if flow_path not in indexes["by_flow"]:
                        indexes["by_flow"][flow_path] = []
                    indexes["by_flow"][flow_path].append(node_id)

        # Index tasks by category
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") == "task":
                category = data.get("category")
                if category:
                    if category not in indexes["by_category"]:
                        indexes["by_category"][category] = []
                    indexes["by_category"][category].append(node_id)

        return indexes
