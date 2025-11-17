"""Build RegistryGraph from discovered models and operations.

This module provides functions to build a RegistryGraph from ModelRegistry
and OperationRegistry after discovery.
"""

from __future__ import annotations

from pathlib import Path

from .registries import ModelRegistry, OperationRegistry
from .registry_graph import RegistryGraph


def build_graph_from_registries(project_name: str) -> RegistryGraph:
    """Build RegistryGraph from current registries.

    Args:
        project_name: Name of the project

    Returns:
        RegistryGraph populated with models, tasks, and flows
    """
    graph = RegistryGraph(project_name)

    # Add DataModel nodes
    for model_info in ModelRegistry.list_all():
        # Extract fields from document class
        fields = _extract_fields_from_class(model_info.document_cls)

        graph.add_datamodel(
            name=model_info.name,
            class_name=model_info.document_cls.__name__,
            module=model_info.document_cls.__module__,
            fields=fields,
            searchable_fields=model_info.searchable_fields,
            sortable_fields=model_info.sortable_fields,
            description=model_info.description or "",
            tags=model_info.tags,
        )

        # Add relations between DataModels
        for relation in model_info.relations:
            target_model = relation.get("target")
            if target_model:
                graph.add_edge(
                    "HAS_RELATION",
                    f"dm:{model_info.name}",
                    f"dm:{target_model}",
                    field_name=relation.get("name"),
                    cardinality=relation.get("cardinality", "one"),
                    foreign_key=relation.get("via"),
                )

    # Extract flows and tasks from operations
    flows_created = set()

    for op_meta in OperationRegistry.list_all():
        # Extract flow hierarchy from operation name
        # e.g., "user.create.validate_email" → flows: ["user", "user.create"]
        flow_parts = op_meta.name.split(".")

        # Create flow nodes
        for i in range(len(flow_parts) - 1):
            flow_path = ".".join(flow_parts[:i + 1])

            if flow_path not in flows_created:
                parent_flow = ".".join(flow_parts[:i]) if i > 0 else None

                graph.add_flow(
                    name=flow_parts[i],
                    full_path=flow_path,
                    level=i,
                    parent_flow=parent_flow,
                )
                flows_created.add(flow_path)

                # Add flow hierarchy edge
                if parent_flow:
                    graph.add_edge(
                        "CONTAINS_SUBFLOW",
                        f"flow:{parent_flow}",
                        f"flow:{flow_path}",
                        hierarchy_level=i
                    )

        # Create task node
        task_id = graph.add_task(
            name=op_meta.name,
            full_name=op_meta.name,
            flow_path=".".join(flow_parts[:-1]) if len(flow_parts) > 1 else "",
            category=op_meta.category,
            async_enabled=op_meta.async_enabled,
            input_schema=op_meta.input_schema.__name__ if op_meta.input_schema else "None",
            output_schema=op_meta.output_schema.__name__ if op_meta.output_schema else "None",
            description=op_meta.description or "",
            tags=op_meta.tags,
            permissions=op_meta.permissions,
        )

        # Link task to flow
        if len(flow_parts) > 1:
            flow_path = ".".join(flow_parts[:-1])
            flow_id = f"flow:{flow_path}"
            graph.add_edge("CONTAINS_TASK", flow_id, task_id)

        # Add task → datamodel edges
        for model_in in op_meta.models_in:
            dm_id = f"dm:{model_in}"
            if dm_id in graph.graph:  # Only add if model exists
                graph.add_edge("READS", task_id, dm_id)

        for model_out in op_meta.models_out:
            dm_id = f"dm:{model_out}"
            if dm_id in graph.graph:  # Only add if model exists
                graph.add_edge("WRITES", task_id, dm_id)

    # Build task dependencies from data flow
    _build_task_dependencies(graph)

    return graph


def _extract_fields_from_class(cls: type) -> dict[str, dict[str, str]]:
    """Extract field definitions from a class.

    Args:
        cls: Class to extract fields from

    Returns:
        Dict mapping field names to field info
    """
    fields = {}

    # Try to get fields from Pydantic/Beanie model
    if hasattr(cls, "__fields__"):
        # Pydantic v1
        for field_name, field_info in cls.__fields__.items():
            fields[field_name] = {
                "type": str(field_info.type_),
                "required": field_info.required,
            }
    elif hasattr(cls, "model_fields"):
        # Pydantic v2
        for field_name, field_info in cls.model_fields.items():
            fields[field_name] = {
                "type": str(field_info.annotation),
                "required": field_info.is_required(),
            }
    elif hasattr(cls, "__annotations__"):
        # Fallback: use type annotations
        for field_name, field_type in cls.__annotations__.items():
            fields[field_name] = {
                "type": str(field_type),
                "required": True,  # Can't determine from annotations alone
            }

    return fields


def _build_task_dependencies(graph: RegistryGraph) -> None:
    """Build DEPENDS_ON edges between tasks based on data flow.

    A task B depends on task A if:
    - Task A writes a model M
    - Task B reads model M

    Args:
        graph: RegistryGraph to add dependencies to
    """
    # Get all task nodes
    task_nodes = [
        (node_id, data)
        for node_id, data in graph.graph.nodes(data=True)
        if data.get("type") == "task"
    ]

    # For each task, find what models it reads
    for task_id, task_data in task_nodes:
        models_read = graph.get_datamodels_read_by_task(task_id)

        # For each model this task reads, find tasks that write it
        for model_id in models_read:
            for other_task_id, other_task_data in task_nodes:
                if task_id == other_task_id:
                    continue  # Skip self

                models_written = graph.get_datamodels_written_by_task(other_task_id)

                # If other task writes this model, create dependency
                if model_id in models_written:
                    # task_id depends on other_task_id
                    graph.add_edge(
                        "DEPENDS_ON",
                        task_id,
                        other_task_id,
                        data_passed=[model_id.replace("dm:", "")],
                        reason=f"{task_id} reads {model_id} written by {other_task_id}"
                    )


def save_graph_to_project(graph: RegistryGraph, project_root: Path) -> Path:
    """Save graph and exports to project directory.

    Args:
        graph: RegistryGraph to save
        project_root: Project root directory

    Returns:
        Path to saved JSON file
    """
    pulpo_dir = project_root / ".pulpo"
    pulpo_dir.mkdir(exist_ok=True)

    # Save JSON
    json_path = pulpo_dir / "registry_graph.json"
    graph.save(json_path)

    # Export Mermaid
    mmd_path = pulpo_dir / "registry_graph.mmd"
    graph.export_mermaid(mmd_path)

    # Export DOT (optional, requires pydot)
    try:
        dot_path = pulpo_dir / "registry_graph.dot"
        graph.export_dot(dot_path)
    except ImportError:
        pass  # Skip DOT export if pydot not installed

    return json_path


def load_graph_from_project(project_root: Path) -> RegistryGraph | None:
    """Load graph from project directory.

    Args:
        project_root: Project root directory

    Returns:
        RegistryGraph if exists, None otherwise
    """
    json_path = project_root / ".pulpo" / "registry_graph.json"

    if not json_path.exists():
        return None

    return RegistryGraph.load(json_path)
