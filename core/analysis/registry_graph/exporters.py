"""Graph export to various formats."""

from pathlib import Path

try:
    import networkx as nx
except ImportError:
    raise ImportError("NetworkX is required. Install with: pip install networkx")


class GraphExporters:
    """Handles graph exports to Mermaid, DOT, etc."""

    def __init__(self, graph: nx.DiGraph):
        """Initialize exporters.

        Args:
            graph: NetworkX graph to export
        """
        self._graph = graph

    def export_mermaid(self, output_path: Path) -> None:
        """Export graph to Mermaid format.

        Args:
            output_path: Path to save Mermaid file
        """
        lines = ["graph TD", ""]

        # Add nodes
        for node_id, data in self._graph.nodes(data=True):
            lines.append(self._format_mermaid_node(node_id, data))

        lines.append("")

        # Add edges
        for source, target, data in self._graph.edges(data=True):
            lines.append(self._format_mermaid_edge(source, target, data))

        output_path.write_text("\n".join(lines))

    def export_dot(self, output_path: Path) -> None:
        """Export graph to GraphViz DOT format.

        Args:
            output_path: Path to save DOT file

        Raises:
            ImportError: If pydot is not installed
        """
        try:
            from networkx.drawing.nx_pydot import write_dot
            write_dot(self._graph, output_path)
        except ImportError:
            raise ImportError("pydot required for DOT export. Install with: pip install pydot")

    def _format_mermaid_node(self, node_id: str, data: dict) -> str:
        """Format node for Mermaid diagram.

        Args:
            node_id: Node identifier
            data: Node data

        Returns:
            Mermaid node string
        """
        node_type = data.get("type")
        name = data.get("name", node_id)
        clean_id = node_id.replace(":", "_")

        if node_type == "datamodel":
            return f'    {clean_id}["{name}<br/>DataModel"]'
        elif node_type == "task":
            return f'    {clean_id}("{name}<br/>Task")'
        elif node_type == "flow":
            return f'    {clean_id}{{{{{name}<br/>Flow}}}}'

        return f'    {clean_id}["{name}"]'

    def _format_mermaid_edge(self, source: str, target: str, data: dict) -> str:
        """Format edge for Mermaid diagram.

        Args:
            source: Source node ID
            target: Target node ID
            data: Edge data

        Returns:
            Mermaid edge string
        """
        edge_type = data.get("type", "")
        source_clean = source.replace(":", "_")
        target_clean = target.replace(":", "_")
        return f'    {source_clean} -->|{edge_type}| {target_clean}'
