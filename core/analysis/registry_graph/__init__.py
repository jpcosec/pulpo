"""Registry Graph - Persistent graph of models, tasks, and flows.

This package provides a clean, modular architecture for managing the registry graph
using the Single Responsibility Principle.

Main class:
    RegistryGraph: Core graph that delegates to specialized managers

Managers:
    NodeManager: Handles node creation (DataModel, Task, Flow)
    EdgeManager: Handles edge creation (relationships)
    QueryEngine: Handles graph queries
    GraphValidator: Handles validation
    GraphPersistence: Handles save/load
    GraphExporters: Handles exports (Mermaid, DOT)

Example:
    >>> from core.analysis.registry_graph import RegistryGraph
    >>> graph = RegistryGraph("my-project")
    >>> graph.add_datamodel("User", class_name="User", module="models.user", fields={})
    >>> graph.add_task("create_user", full_name="user.create_user", flow_path="user", category="user")
    >>> graph.add_edge("WRITES", "task:create_user", "dm:User")
    >>> is_valid, errors, warnings = graph.validate()
    >>> graph.save(Path(".pulpo/registry_graph.json"))
"""

from .graph import RegistryGraph
from .types import NodeType, EdgeType

__all__ = ["RegistryGraph", "NodeType", "EdgeType"]
