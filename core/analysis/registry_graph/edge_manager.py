"""Edge management for registry graph."""

from typing import Any

try:
    import networkx as nx
except ImportError:
    raise ImportError("NetworkX is required. Install with: pip install networkx")

from .types import EdgeType


class EdgeManager:
    """Manages graph edges (relationships)."""

    def __init__(self, graph: nx.DiGraph):
        """Initialize edge manager.

        Args:
            graph: NetworkX graph to manage edges in
        """
        self._graph = graph
        self._edge_counter = 0

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
        edge_id = f"e_{self._edge_counter}"
        self._edge_counter += 1

        self._graph.add_edge(
            source,
            target,
            id=edge_id,
            type=edge_type,
            **properties
        )
        return edge_id
