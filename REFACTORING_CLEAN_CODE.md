# Clean Code Refactoring Plan

## Current Problems

### 1. RegistryGraph violates SRP (663 lines, 22 methods)

**Current:**
```python
class RegistryGraph:
    # Node management
    def add_node()
    def add_datamodel()
    def add_task()
    def add_flow()

    # Edge management
    def add_edge()

    # Queries (7 methods!)
    def get_node()
    def get_nodes_by_type()
    def get_tasks_by_flow()
    def get_task_dependencies()
    def get_task_dependents()
    def get_datamodels_read_by_task()
    def get_datamodels_written_by_task()
    def get_related_datamodels()

    # Validation
    def validate()

    # Topological sort
    def get_execution_order()
    def get_parallel_groups()

    # Persistence
    def save()
    def load()
    def _build_indexes()

    # Export
    def export_mermaid()
    def export_dot()
```

---

## Proposed Refactoring

### Split into 6 Small Classes (SRP)

```
core/analysis/registry_graph/
├── __init__.py
├── graph.py              # Core graph (100 lines)
├── node_manager.py       # Node operations (80 lines)
├── edge_manager.py       # Edge operations (60 lines)
├── query_engine.py       # Queries (150 lines)
├── validator.py          # Validation (100 lines)
├── persistence.py        # Save/load (120 lines)
└── exporters.py          # Mermaid, DOT (100 lines)
```

---

### 1. Core Graph (graph.py - 100 lines)

```python
"""Core graph structure."""

import networkx as nx
from typing import Any

class RegistryGraph:
    """Lightweight graph container.

    Delegates operations to specialized managers.
    """

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.graph = nx.DiGraph()
        self.metadata = {
            "version": "1.0.0",
            "project_name": project_name,
        }

        # Composition over inheritance
        self.nodes = NodeManager(self.graph)
        self.edges = EdgeManager(self.graph)
        self.queries = QueryEngine(self.graph)
        self.validator = GraphValidator(self.graph)
        self.persistence = GraphPersistence(self.graph, self.metadata)
        self.exporters = GraphExporters(self.graph)

    # Facade methods (delegate to managers)
    def add_datamodel(self, *args, **kwargs):
        return self.nodes.add_datamodel(*args, **kwargs)

    def add_task(self, *args, **kwargs):
        return self.nodes.add_task(*args, **kwargs)

    def validate(self):
        return self.validator.validate()

    def save(self, path):
        return self.persistence.save(path)

    @classmethod
    def load(cls, path):
        return GraphPersistence.load(path)
```

**Benefits:**
- ✅ Only 40 lines
- ✅ Single responsibility: composition
- ✅ Easy to test each manager independently

---

### 2. Node Manager (node_manager.py - 80 lines)

```python
"""Manages graph nodes."""

from typing import Any
import networkx as nx
from .types import NodeType

class NodeManager:
    """Handles node creation and management."""

    def __init__(self, graph: nx.DiGraph):
        self._graph = graph

    def add_node(
        self,
        node_type: NodeType,
        node_id: str,
        **properties: Any
    ) -> str:
        """Generic node creation (extensible)."""
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
        """Add DataModel node."""
        return self.add_node(
            "datamodel",
            f"dm:{name}",
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
        """Add Task node."""
        return self.add_node(
            "task",
            f"task:{name}",
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
        """Add Flow node."""
        return self.add_node(
            "flow",
            f"flow:{full_path}",
            name=name,
            full_path=full_path,
            level=level,
            parent_flow=parent_flow,
            **properties
        )
```

**Benefits:**
- ✅ Single responsibility: node creation
- ✅ ~80 lines
- ✅ Easy to extend (add new node types)

---

### 3. Edge Manager (edge_manager.py - 60 lines)

```python
"""Manages graph edges."""

from typing import Any
import networkx as nx
from .types import EdgeType

class EdgeManager:
    """Handles edge creation."""

    def __init__(self, graph: nx.DiGraph):
        self._graph = graph
        self._edge_counter = 0

    def add_edge(
        self,
        edge_type: EdgeType,
        source: str,
        target: str,
        **properties: Any
    ) -> str:
        """Add edge between nodes."""
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
```

**Benefits:**
- ✅ Single responsibility: edge creation
- ✅ ~30 lines
- ✅ Simple, focused

---

### 4. Query Engine (query_engine.py - 150 lines)

```python
"""Graph query operations."""

from typing import Any
import networkx as nx

class QueryEngine:
    """Handles graph queries."""

    def __init__(self, graph: nx.DiGraph):
        self._graph = graph

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get node by ID."""
        if node_id in self._graph:
            return dict(self._graph.nodes[node_id])
        return None

    def get_nodes_by_type(self, node_type: str) -> list[str]:
        """Get all nodes of a specific type."""
        return [
            node_id
            for node_id, data in self._graph.nodes(data=True)
            if data.get("type") == node_type
        ]

    def get_tasks_by_flow(self, flow_path: str) -> list[str]:
        """Get all tasks in a flow."""
        flow_id = f"flow:{flow_path}"
        if flow_id not in self._graph:
            return []

        return [
            target
            for _, target, data in self._graph.out_edges(flow_id, data=True)
            if data.get("type") == "CONTAINS_TASK"
        ]

    def get_task_dependencies(self, task_id: str) -> list[str]:
        """Get tasks this task depends on."""
        return [
            source
            for source, _, data in self._graph.in_edges(task_id, data=True)
            if data.get("type") == "DEPENDS_ON"
        ]

    def get_task_dependents(self, task_id: str) -> list[str]:
        """Get tasks that depend on this task."""
        return [
            target
            for _, target, data in self._graph.out_edges(task_id, data=True)
            if data.get("type") == "DEPENDS_ON"
        ]

    # ... more query methods
```

**Benefits:**
- ✅ Single responsibility: queries
- ✅ ~150 lines (all query methods)
- ✅ Easy to add new queries

---

### 5. Validator (validator.py - 100 lines)

```python
"""Graph validation."""

import networkx as nx

class GraphValidator:
    """Validates graph integrity."""

    def __init__(self, graph: nx.DiGraph):
        self._graph = graph
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate(self) -> tuple[bool, list[str], list[str]]:
        """Run all validations."""
        self.errors = []
        self.warnings = []

        self._check_cycles()
        self._check_unused_models()
        self._check_orphan_tasks()

        return len(self.errors) == 0, self.errors, self.warnings

    def _check_cycles(self) -> None:
        """Check for circular dependencies."""
        task_deps = nx.DiGraph()
        for source, target, data in self._graph.edges(data=True):
            if data.get("type") == "DEPENDS_ON":
                task_deps.add_edge(source, target)

        try:
            cycles = list(nx.simple_cycles(task_deps))
            for cycle in cycles:
                cycle_str = " → ".join(cycle + [cycle[0]])
                self.errors.append(f"Circular dependency: {cycle_str}")
        except Exception as e:
            self.errors.append(f"Error checking cycles: {e}")

    def _check_unused_models(self) -> None:
        """Check for unused DataModels."""
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") != "datamodel":
                continue

            has_usage = any(
                edge_data.get("type") in ("READS", "WRITES", "DELETES")
                for _, _, edge_data in self._graph.in_edges(node_id, data=True)
            )

            if not has_usage:
                self.warnings.append(
                    f"DataModel '{data.get('name')}' is not used by any task"
                )

    def _check_orphan_tasks(self) -> None:
        """Check for tasks not in any flow."""
        for node_id, data in self._graph.nodes(data=True):
            if data.get("type") != "task":
                continue

            has_flow = any(
                edge_data.get("type") == "CONTAINS_TASK"
                for _, _, edge_data in self._graph.in_edges(node_id, data=True)
            )

            if not has_flow:
                self.warnings.append(
                    f"Task '{data.get('name')}' is not in any flow"
                )
```

**Benefits:**
- ✅ Single responsibility: validation
- ✅ ~100 lines
- ✅ Easy to add new validations

---

### 6. Persistence (persistence.py - 120 lines)

```python
"""Graph persistence (save/load)."""

import json
from pathlib import Path
from datetime import datetime
import networkx as nx

class GraphPersistence:
    """Handles save/load operations."""

    def __init__(self, graph: nx.DiGraph, metadata: dict):
        self._graph = graph
        self._metadata = metadata

    def save(self, path: Path) -> None:
        """Save graph to JSON."""
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
    def load(path: Path) -> "RegistryGraph":
        """Load graph from JSON."""
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

        return graph

    def _serialize_nodes(self) -> dict:
        """Convert nodes to JSON-serializable format."""
        return {
            node_id: dict(data)
            for node_id, data in self._graph.nodes(data=True)
        }

    def _serialize_edges(self) -> list:
        """Convert edges to JSON-serializable format."""
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

    def _build_indexes(self) -> dict:
        """Build lookup indexes."""
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

        # ... more indexing

        return indexes
```

**Benefits:**
- ✅ Single responsibility: persistence
- ✅ ~120 lines
- ✅ Easy to add new formats (YAML, etc.)

---

### 7. Exporters (exporters.py - 100 lines)

```python
"""Graph export to various formats."""

from pathlib import Path
import networkx as nx

class GraphExporters:
    """Handles graph exports."""

    def __init__(self, graph: nx.DiGraph):
        self._graph = graph

    def export_mermaid(self, output_path: Path) -> None:
        """Export to Mermaid format."""
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
        """Export to GraphViz DOT format."""
        try:
            from networkx.drawing.nx_pydot import write_dot
            write_dot(self._graph, output_path)
        except ImportError:
            raise ImportError("pydot required for DOT export")

    def _format_mermaid_node(self, node_id: str, data: dict) -> str:
        """Format node for Mermaid."""
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
        """Format edge for Mermaid."""
        edge_type = data.get("type", "")
        source_clean = source.replace(":", "_")
        target_clean = target.replace(":", "_")
        return f'    {source_clean} -->|{edge_type}| {target_clean}'
```

**Benefits:**
- ✅ Single responsibility: exports
- ✅ ~100 lines
- ✅ Easy to add new formats (Neo4j, etc.)

---

## Benefits of Refactoring

### Before (Current)
```
registry_graph.py: 663 lines, 1 class, 22 methods
```

### After (Proposed)
```
registry_graph/
├── graph.py:          100 lines, 1 class,  8 methods
├── node_manager.py:    80 lines, 1 class,  4 methods
├── edge_manager.py:    60 lines, 1 class,  1 method
├── query_engine.py:   150 lines, 1 class,  8 methods
├── validator.py:      100 lines, 1 class,  4 methods
├── persistence.py:    120 lines, 1 class,  5 methods
└── exporters.py:      100 lines, 1 class,  4 methods
─────────────────────────────────────────────────────
Total:                 710 lines, 7 classes, 34 methods
```

### Metrics Comparison

| Metric | Before | After | Clean Code? |
|--------|--------|-------|-------------|
| **Max file size** | 663 lines | 150 lines | ✅ YES |
| **Methods per class** | 22 | 8 max | ✅ YES |
| **Single responsibility** | ❌ NO | ✅ YES | ✅ YES |
| **Testability** | ❌ Hard | ✅ Easy | ✅ YES |
| **Extensibility** | 🟡 OK | ✅ Great | ✅ YES |

---

## Other Files to Refactor

### 1. interface.py - show_flow() (80 lines → 30 lines)

```python
# Current
def show_flow(self, operation_name: str) -> None:
    # 80 lines of mixed logic

# Refactored
class FlowVisualizer:
    def show(self, operation_name: str) -> None:
        self._show_header(operation)
        self._show_details(operation)
        self._show_dependencies(operation)
        self._show_execution_info(operation)

    def _show_header(self, op): ...  # 5 lines
    def _show_details(self, op): ...  # 10 lines
    def _show_dependencies(self, op): ...  # 10 lines
    def _show_execution_info(self, op): ...  # 10 lines
```

### 2. cli_generator.py - db_seed() (55 lines → 25 lines)

```python
# Current
def db_seed():
    # 55 lines of seed file discovery + execution

# Refactored
class SeedRunner:
    def run(self):
        files = self._discover_seed_files()
        self._execute_seeds(files)

    def _discover_seed_files(self): ...  # 15 lines
    def _execute_seeds(self, files): ...  # 10 lines
```

---

## Implementation Priority

### Phase 1: Critical (Do First)
1. ✅ Split RegistryGraph into 7 classes
2. ✅ Extract FlowVisualizer from interface.py
3. ✅ Extract SeedRunner from cli_generator.py

### Phase 2: Important
4. Add unit tests for each manager
5. Replace generic try/except with specific exceptions
6. Add interfaces/protocols for dependency injection

### Phase 3: Nice to Have
7. Extract graph_builder logic into smaller functions
8. Add logging instead of print statements
9. Add dependency injection container

---

## Testing After Refactoring

```python
# Easy to test individual components

def test_node_manager():
    graph = nx.DiGraph()
    manager = NodeManager(graph)

    node_id = manager.add_datamodel("User", ...)
    assert node_id == "dm:User"
    assert graph.nodes[node_id]["type"] == "datamodel"

def test_validator():
    graph = nx.DiGraph()
    graph.add_edge("A", "B", type="DEPENDS_ON")
    graph.add_edge("B", "A", type="DEPENDS_ON")  # Cycle!

    validator = GraphValidator(graph)
    is_valid, errors, warnings = validator.validate()

    assert not is_valid
    assert "Circular dependency" in errors[0]

def test_exporter():
    graph = nx.DiGraph()
    graph.add_node("dm:User", type="datamodel", name="User")

    exporter = GraphExporters(graph)
    exporter.export_mermaid(Path("test.mmd"))

    content = Path("test.mmd").read_text()
    assert "dm_User" in content
    assert "DataModel" in content
```

---

## Summary

### Current Code Quality: 🟡 6/10

**Good:**
- ✅ Type hints
- ✅ Docstrings
- ✅ Descriptive names
- ✅ Works correctly

**Bad:**
- ❌ Violates SRP (RegistryGraph does 7 things)
- ❌ Files too large (663 lines)
- ❌ Classes too large (22 methods)
- ❌ Functions too long (80 lines)
- ❌ Hard to test (tight coupling)

### After Refactoring: ✅ 9/10

**Improvements:**
- ✅ SRP: Each class does one thing
- ✅ Small files (< 150 lines each)
- ✅ Small classes (< 8 methods each)
- ✅ Small functions (< 20 lines each)
- ✅ Easy to test (loose coupling)
- ✅ Easy to extend (composition)

---

## Next Steps

¿Quieres que implemente este refactoring? Tomaría ~2 horas pero el código quedaría mucho más limpio y mantenible.
