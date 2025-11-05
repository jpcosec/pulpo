# Registry Graph Design - Persistent Graph Architecture

## Problem Statement

**Current Architecture:**
- Registries are simple dicts (`dict[str, ModelInfo]`)
- Graph is built on-demand during `compile`
- No early error detection
- Hard to visualize relationships before code generation

**Proposed Architecture:**
- Build graph during `init` (not `compile`)
- Persist graph to disk in queryable format
- Enable early validation and visualization
- Support complex queries on relationships

---

## Graph Schema

### Node Types (3 types)

1. **DataModel**: Data entities from `@datamodel`
2. **Task**: Individual operations from `@operation`
3. **Flow**: Hierarchical grouping from operation naming (split by `.`)

### Edge Types (5 categories)

1. **DataModel → DataModel**:
   - `HAS_RELATION`: Foreign key relationship
   - `CONTAINS_LIST`: List/array of objects
   - `INHERITS_FROM`: Class inheritance

2. **Task → DataModel**:
   - `READS`: Task reads this model
   - `WRITES`: Task creates/updates this model
   - `DELETES`: Task removes this model

3. **Task → Task**:
   - `DEPENDS_ON`: Sequential dependency (A must run before B)
   - `RUNS_PARALLEL`: Can run in parallel (same inputs/outputs)

4. **Flow → Flow**:
   - `CONTAINS_SUBFLOW`: Hierarchical containment (e.g., `user` → `user.create`)

5. **Flow → Task**:
   - `CONTAINS_TASK`: Flow contains this task

---

## File Format: JSON Graph Format

### Location
```
.pulpo/
  registry_graph.json       # Main graph file
  registry_graph.mmd        # Mermaid export (auto-generated)
  registry_graph.dot        # GraphViz export (auto-generated)
```

### Schema (registry_graph.json)

```json
{
  "metadata": {
    "version": "1.0.0",
    "generated_at": "2025-11-05T10:30:00Z",
    "project_name": "my-pulpo-project",
    "pulpo_version": "0.1.0"
  },

  "nodes": {
    "dm:User": {
      "type": "datamodel",
      "name": "User",
      "class_name": "User",
      "module": "models.user",
      "fields": {
        "id": {"type": "str", "required": true},
        "name": {"type": "str", "required": true},
        "email": {"type": "str", "required": true},
        "posts": {"type": "list[Post]", "required": false}
      },
      "searchable_fields": ["name", "email"],
      "sortable_fields": ["name", "created_at"],
      "description": "User account model"
    },

    "dm:Post": {
      "type": "datamodel",
      "name": "Post",
      "class_name": "Post",
      "module": "models.post",
      "fields": {
        "id": {"type": "str", "required": true},
        "title": {"type": "str", "required": true},
        "author_id": {"type": "str", "required": true}
      },
      "description": "Blog post model"
    },

    "task:create_user": {
      "type": "task",
      "name": "create_user",
      "full_name": "user.create_user",
      "flow_path": "user.create",
      "category": "user",
      "async": true,
      "input_schema": "CreateUserInput",
      "output_schema": "User",
      "description": "Create a new user account",
      "tags": ["auth", "user"],
      "permissions": ["admin"]
    },

    "task:validate_email": {
      "type": "task",
      "name": "validate_email",
      "full_name": "user.create.validate_email",
      "flow_path": "user.create.validate",
      "category": "user",
      "async": false,
      "input_schema": "EmailInput",
      "output_schema": "ValidationResult"
    },

    "flow:user": {
      "type": "flow",
      "name": "user",
      "full_path": "user",
      "level": 0,
      "parent_flow": null,
      "description": "User management flows"
    },

    "flow:user.create": {
      "type": "flow",
      "name": "create",
      "full_path": "user.create",
      "level": 1,
      "parent_flow": "user",
      "description": "User creation flow"
    }
  },

  "edges": [
    {
      "id": "e1",
      "type": "HAS_RELATION",
      "source": "dm:User",
      "target": "dm:Post",
      "properties": {
        "field_name": "posts",
        "cardinality": "one-to-many",
        "foreign_key": "author_id",
        "cascade_delete": true
      }
    },

    {
      "id": "e2",
      "type": "WRITES",
      "source": "task:create_user",
      "target": "dm:User",
      "properties": {
        "operation": "create",
        "fields_written": ["id", "name", "email"]
      }
    },

    {
      "id": "e3",
      "type": "READS",
      "source": "task:validate_email",
      "target": "dm:User",
      "properties": {
        "fields_read": ["email"],
        "operation": "query"
      }
    },

    {
      "id": "e4",
      "type": "DEPENDS_ON",
      "source": "task:create_user",
      "target": "task:validate_email",
      "properties": {
        "data_passed": ["User"],
        "reason": "create_user needs validated email"
      }
    },

    {
      "id": "e5",
      "type": "CONTAINS_SUBFLOW",
      "source": "flow:user",
      "target": "flow:user.create",
      "properties": {
        "hierarchy_level": 1
      }
    },

    {
      "id": "e6",
      "type": "CONTAINS_TASK",
      "source": "flow:user.create",
      "target": "task:create_user",
      "properties": {
        "task_order": 1
      }
    }
  ],

  "indexes": {
    "by_type": {
      "datamodel": ["dm:User", "dm:Post"],
      "task": ["task:create_user", "task:validate_email"],
      "flow": ["flow:user", "flow:user.create"]
    },
    "by_flow": {
      "user": ["task:create_user"],
      "user.create": ["task:create_user", "task:validate_email"]
    },
    "by_category": {
      "user": ["task:create_user", "task:validate_email"]
    }
  },

  "validation": {
    "has_cycles": false,
    "errors": [],
    "warnings": [
      {
        "type": "unused_datamodel",
        "node": "dm:Post",
        "message": "DataModel 'Post' is not used by any task"
      }
    ]
  }
}
```

---

## Implementation: RegistryGraph Class

```python
# core/analysis/registry_graph.py

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal
from dataclasses import dataclass, field
from datetime import datetime

import networkx as nx

NodeType = Literal["datamodel", "task", "flow"]
EdgeType = Literal[
    "HAS_RELATION", "CONTAINS_LIST", "INHERITS_FROM",  # DataModel → DataModel
    "READS", "WRITES", "DELETES",                       # Task → DataModel
    "DEPENDS_ON", "RUNS_PARALLEL",                      # Task → Task
    "CONTAINS_SUBFLOW",                                 # Flow → Flow
    "CONTAINS_TASK"                                     # Flow → Task
]


@dataclass
class GraphNode:
    """Base class for graph nodes."""
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

    This graph is built during `pulpo init` and persisted to disk.
    It enables:
    - Early error detection (before compile)
    - Visualization of relationships
    - Complex queries on data flow
    - Validation of graph integrity
    """

    def __init__(self, project_name: str):
        """Initialize empty graph."""
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

    def add_datamodel(
        self,
        name: str,
        class_name: str,
        module: str,
        fields: dict[str, Any],
        **properties
    ) -> str:
        """Add DataModel node."""
        node_id = f"dm:{name}"
        self.graph.add_node(
            node_id,
            type="datamodel",
            name=name,
            class_name=class_name,
            module=module,
            fields=fields,
            **properties
        )
        return node_id

    def add_task(
        self,
        name: str,
        full_name: str,
        flow_path: str,
        category: str,
        **properties
    ) -> str:
        """Add Task node."""
        node_id = f"task:{name}"
        self.graph.add_node(
            node_id,
            type="task",
            name=name,
            full_name=full_name,
            flow_path=flow_path,
            category=category,
            **properties
        )
        return node_id

    def add_flow(
        self,
        name: str,
        full_path: str,
        level: int,
        parent_flow: str | None = None,
        **properties
    ) -> str:
        """Add Flow node."""
        node_id = f"flow:{full_path}"
        self.graph.add_node(
            node_id,
            type="flow",
            name=name,
            full_path=full_path,
            level=level,
            parent_flow=parent_flow,
            **properties
        )
        return node_id

    # ========== Edge Management ==========

    def add_edge(
        self,
        edge_type: EdgeType,
        source: str,
        target: str,
        **properties
    ) -> str:
        """Add edge between nodes."""
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
        """Get node by ID."""
        if node_id in self.graph:
            return dict(self.graph.nodes[node_id])
        return None

    def get_tasks_by_flow(self, flow_path: str) -> list[str]:
        """Get all tasks in a flow."""
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
        """Get tasks this task depends on."""
        deps = []
        for source, _, data in self.graph.in_edges(task_id, data=True):
            if data.get("type") == "DEPENDS_ON":
                deps.append(source)
        return deps

    def get_datamodels_read_by_task(self, task_id: str) -> list[str]:
        """Get DataModels read by this task."""
        models = []
        for _, target, data in self.graph.out_edges(task_id, data=True):
            if data.get("type") == "READS":
                models.append(target)
        return models

    def get_datamodels_written_by_task(self, task_id: str) -> list[str]:
        """Get DataModels written by this task."""
        models = []
        for _, target, data in self.graph.out_edges(task_id, data=True):
            if data.get("type") == "WRITES":
                models.append(target)
        return models

    def get_related_datamodels(self, datamodel_id: str) -> list[tuple[str, str]]:
        """Get DataModels related to this one.

        Returns:
            List of (relation_type, target_model_id)
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

        Returns:
            (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Check for cycles in task dependencies
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                errors.append(f"Circular dependencies detected: {cycles}")
        except nx.NetworkXNoCycle:
            pass  # No cycles, good

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
                    warnings.append(f"DataModel '{data['name']}' is not used by any task")

        # Check for orphan tasks (no flow)
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == "task":
                has_flow = False
                for source, _, edge_data in self.graph.in_edges(node_id, data=True):
                    if edge_data.get("type") == "CONTAINS_TASK":
                        has_flow = True
                        break

                if not has_flow:
                    warnings.append(f"Task '{data['name']}' is not contained in any flow")

        self.validation_errors = errors
        self.validation_warnings = warnings

        return len(errors) == 0, errors, warnings

    # ========== Topological Sort ==========

    def get_execution_order(self) -> list[str]:
        """Get tasks in execution order (topological sort).

        Returns:
            List of task IDs in execution order
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

        Returns:
            List of groups, where each group can run in parallel
        """
        execution_order = self.get_execution_order()

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
        """Save graph to JSON file."""
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
                    "properties": {k: v for k, v in data.items() if k not in ("id", "type")}
                }
                for i, (source, target, data) in enumerate(self.graph.edges(data=True))
            ],
            "indexes": self._build_indexes(),
            "validation": {
                "has_cycles": len(self.validation_errors) > 0,
                "errors": self.validation_errors,
                "warnings": self.validation_warnings
            }
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "RegistryGraph":
        """Load graph from JSON file."""
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
        """Build indexes for fast lookups."""
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
        """Export graph to Mermaid format."""
        lines = ["graph TD"]

        # Add nodes
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("type")
            name = data.get("name", node_id)

            if node_type == "datamodel":
                lines.append(f'    {node_id}["{name}\\nDataModel"]')
            elif node_type == "task":
                lines.append(f'    {node_id}("{name}\\nTask")')
            elif node_type == "flow":
                lines.append(f'    {node_id}{{{{{name}\\nFlow}}}}')

        # Add edges
        for source, target, data in self.graph.edges(data=True):
            edge_type = data.get("type", "")
            lines.append(f'    {source} -->|{edge_type}| {target}')

        output_path.write_text("\n".join(lines))

    def export_dot(self, output_path: Path) -> None:
        """Export graph to GraphViz DOT format."""
        nx.drawing.nx_pydot.write_dot(self.graph, output_path)
```

---

## Workflow: When to Build/Update Graph

### During `pulpo init`

```python
# core/generation/init/project_init.py

from core.analysis.registry_graph import RegistryGraph

def initialize_project():
    # ... existing init code ...

    # Build initial graph
    graph = RegistryGraph(project_name)

    # Add example nodes/edges for templates
    graph.add_flow("example", "example", level=0)

    # Save graph
    graph_path = project_root / ".pulpo" / "registry_graph.json"
    graph.save(graph_path)

    # Export visualizations
    graph.export_mermaid(project_root / ".pulpo" / "registry_graph.mmd")

    print("✅ Created registry graph")
```

### During Discovery (AST/Import Scan)

```python
# core/analysis/discovery/import_scanner.py

from core.analysis.registry_graph import RegistryGraph

def discover_and_build_graph(project_root: Path):
    """Discover models/operations and build graph."""

    # Load existing graph or create new
    graph_path = project_root / ".pulpo" / "registry_graph.json"
    if graph_path.exists():
        graph = RegistryGraph.load(graph_path)
    else:
        graph = RegistryGraph(project_name="unknown")

    # Discover models
    for model_info in discover_models():
        # Add DataModel node
        graph.add_datamodel(
            name=model_info.name,
            class_name=model_info.document_cls.__name__,
            module=model_info.document_cls.__module__,
            fields=extract_fields(model_info.document_cls),
            searchable_fields=model_info.searchable_fields,
            sortable_fields=model_info.sortable_fields
        )

        # Add relations
        for relation in model_info.relations:
            target_model = relation["target"]
            graph.add_edge(
                "HAS_RELATION",
                f"dm:{model_info.name}",
                f"dm:{target_model}",
                field_name=relation["name"],
                cardinality=relation.get("cardinality", "one"),
                foreign_key=relation.get("via")
            )

    # Discover operations
    for op_meta in discover_operations():
        # Extract flow hierarchy from name
        # e.g., "user.create.validate_email" → flows: ["user", "user.create"]
        flow_parts = op_meta.name.split(".")

        # Create flow nodes
        for i in range(len(flow_parts) - 1):
            flow_path = ".".join(flow_parts[:i+1])
            parent_flow = ".".join(flow_parts[:i]) if i > 0 else None

            graph.add_flow(
                name=flow_parts[i],
                full_path=flow_path,
                level=i,
                parent_flow=parent_flow
            )

        # Create task node
        task_id = graph.add_task(
            name=op_meta.name,
            full_name=op_meta.name,
            flow_path=".".join(flow_parts[:-1]) if len(flow_parts) > 1 else "",
            category=op_meta.category,
            async_enabled=op_meta.async_enabled,
            input_schema=op_meta.input_schema.__name__,
            output_schema=op_meta.output_schema.__name__,
            description=op_meta.description
        )

        # Link task to flow
        if len(flow_parts) > 1:
            flow_id = f"flow:{'.'.join(flow_parts[:-1])}"
            graph.add_edge("CONTAINS_TASK", flow_id, task_id)

        # Add task → datamodel edges
        for model_in in op_meta.models_in:
            graph.add_edge("READS", task_id, f"dm:{model_in}")

        for model_out in op_meta.models_out:
            graph.add_edge("WRITES", task_id, f"dm:{model_out}")

    # Build task dependencies from data flow
    for task_id in [n for n, d in graph.graph.nodes(data=True) if d.get("type") == "task"]:
        # Find tasks that produce what this task consumes
        models_read = graph.get_datamodels_read_by_task(task_id)

        for model_id in models_read:
            # Find tasks that write this model
            for other_task_id in [n for n, d in graph.graph.nodes(data=True) if d.get("type") == "task"]:
                if model_id in graph.get_datamodels_written_by_task(other_task_id):
                    if task_id != other_task_id:
                        graph.add_edge(
                            "DEPENDS_ON",
                            task_id,
                            other_task_id,
                            data_passed=[model_id.replace("dm:", "")]
                        )

    # Validate graph
    is_valid, errors, warnings = graph.validate()

    if errors:
        print("❌ Graph validation errors:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("⚠️  Graph validation warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    # Save graph
    graph.save(graph_path)
    graph.export_mermaid(project_root / ".pulpo" / "registry_graph.mmd")
    graph.export_dot(project_root / ".pulpo" / "registry_graph.dot")

    print(f"✅ Registry graph updated ({len(graph.graph.nodes)} nodes, {len(graph.graph.edges)} edges)")

    return graph
```

---

## Benefits

### 1. Early Error Detection

```python
# During `pulpo init` - BEFORE compile
graph = RegistryGraph.load(".pulpo/registry_graph.json")
is_valid, errors, warnings = graph.validate()

if errors:
    print("❌ Cannot compile - fix these errors first:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

# Example errors caught early:
# - "Circular dependency: create_user → validate_email → create_user"
# - "Task 'send_email' reads DataModel 'Email' which doesn't exist"
# - "Flow 'user.create' contains no tasks"
```

### 2. Visualization Before Compile

```bash
# View graph before generating any code
pulpo graph view

# Opens .pulpo/registry_graph.mmd in viewer
# Shows all relationships, flows, dependencies
```

### 3. Complex Queries

```python
# Find all tasks that modify a specific model
tasks = graph.find_tasks_modifying("User")

# Find execution path between two tasks
path = nx.shortest_path(graph.graph, "task:scrape_jobs", "task:send_notification")

# Find all unused datamodels
unused = [
    node_id for node_id, data in graph.graph.nodes(data=True)
    if data["type"] == "datamodel" and graph.graph.in_degree(node_id) == 0
]

# Get subgraph for specific flow
user_flow = graph.get_subgraph_by_flow("user.create")
```

### 4. Better Debugging

```bash
# Why is this task running before that one?
pulpo graph why task:send_email --before task:create_user

# Output:
# send_email runs before create_user because:
#   1. send_email WRITES dm:Email
#   2. create_user READS dm:Email
#   3. Therefore: create_user DEPENDS_ON send_email
```

---

## Comparison: Before vs After

| Aspect | Before (Dicts) | After (Graph) |
|--------|---------------|---------------|
| **Error Detection** | During compile | During init ✅ |
| **Visualization** | Generate mermaid on-demand | Always available ✅ |
| **Queries** | Limited (by name only) | Rich (NetworkX) ✅ |
| **Relationships** | Implicit (in metadata) | Explicit (edges) ✅ |
| **Validation** | Manual | Automatic ✅ |
| **Format** | Python dicts | JSON (versionable) ✅ |
| **Debugging** | Hard to trace dependencies | Easy graph traversal ✅ |
| **Persistence** | In-memory only | Saved to disk ✅ |

---

## File Format Decision

**Recommendation: JSON + NetworkX**

**Why JSON?**
- ✅ Human-readable
- ✅ Git-friendly (diffs work)
- ✅ No extra dependencies
- ✅ Easy to export to other formats
- ✅ Can use NetworkX for complex queries

**Why not SQLite?**
- ❌ Binary format (not git-friendly)
- ❌ Harder to inspect/debug
- ❌ Overkill for typical graph sizes (< 10,000 nodes)

**Why not GraphML/XML?**
- ❌ Verbose
- ❌ Less human-readable
- ✅ But we can EXPORT to GraphML for compatibility

---

## Next Steps

1. **Implement RegistryGraph class** (core/analysis/registry_graph.py)
2. **Update discovery to build graph** (ast_scanner.py, import_scanner.py)
3. **Integrate with `pulpo init`** (project_init.py)
4. **Add CLI commands**:
   - `pulpo graph view` - Open graph visualization
   - `pulpo graph validate` - Validate graph integrity
   - `pulpo graph query <query>` - Run queries on graph
5. **Update compile to use graph** (codegen.py reads from graph)

---

## Example: Complete Flow

```bash
# 1. Initialize project
pulpo init
# Creates .pulpo/registry_graph.json with initial structure

# 2. User writes models and operations
# models/user.py, operations/user_ops.py

# 3. Discover and update graph
pulpo scan
# Scans code, builds graph, validates, saves to .pulpo/

# Output:
# ✅ Found 3 DataModels: User, Post, Comment
# ✅ Found 5 Tasks: create_user, validate_email, create_post, ...
# ✅ Built 2 Flows: user, post
# ✅ Detected 4 dependencies
# ⚠️  Warning: DataModel 'Comment' is not used by any task
# ✅ Registry graph updated (8 nodes, 12 edges)

# 4. Visualize graph
pulpo graph view
# Opens Mermaid diagram showing all relationships

# 5. Validate before compile
pulpo graph validate
# Checks for cycles, orphans, unused models

# 6. Compile (uses graph)
pulpo compile
# Reads .pulpo/registry_graph.json
# Generates code based on graph structure
```

---

## Summary

**Key Innovation**: Registry AS a graph (not dict + graph built on-demand)

**Benefits**:
1. **Early validation** - Catch errors in `init`, not `compile`
2. **Always-on visualization** - Graph exists on disk, viewable anytime
3. **Rich queries** - NetworkX enables complex graph traversal
4. **Better debugging** - Trace dependencies easily
5. **Persistence** - JSON format is git-friendly and human-readable

**File Structure**:
```
.pulpo/
  registry_graph.json       # Source of truth
  registry_graph.mmd        # Mermaid export
  registry_graph.dot        # GraphViz export
```

**Graph Schema**:
- **3 node types**: DataModel, Task, Flow
- **5 edge categories**: Relations, Data access, Dependencies, Containment, Hierarchy
- **JSON format**: Human-readable, git-friendly, NetworkX-compatible
