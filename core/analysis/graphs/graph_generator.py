"""Generate Mermaid diagrams for operation flows and model relationships.

Provides visualization of:
1. Operation Flow: Models as nodes, operations as edges
2. Model Relationships: Foreign keys and references between models
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class MermaidGraphGenerator:
    """Generate Mermaid diagrams from registry data."""

    def __init__(self, output_dir: Path = Path("docs")):
        """Initialize generator.

        Args:
            output_dir: Directory to save diagrams
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_operation_flow(
        self,
        models: list[Any],
        operations: list[Any],
    ) -> Path:
        """Generate operation flow diagram.

        Models are nodes, operations are edges showing data flow.

        Args:
            models: List of ModelRegistry entries
            operations: List of OperationRegistry entries

        Returns:
            Path to generated file
        """
        lines = [
            "# Operation Flow Graph",
            "",
            "```mermaid",
            "graph LR",
        ]

        # Add model nodes
        for model in models:
            model_name = model.name
            lines.append(f'    {model_name}["{model_name}"]')

        # Add operation edges
        for op in operations:
            models_in = getattr(op, "models_in", [])
            models_out = getattr(op, "models_out", [])
            description = getattr(op, "description", op.name)

            # Create edges from input models through operation to output models
            for model_in in models_in:
                for model_out in models_out:
                    edge_label = op.name
                    lines.append(f"    {model_in} -->|{edge_label}| {model_out}")

        lines.extend(
            [
                "```",
                "",
                "## Legend",
                "",
                "- **Nodes**: Data models (@datamodel decorated classes)",
                "- **Edges**: Operations (@operation decorated functions)",
                "- **Labels**: Operation names",
                "",
                "## Operations Detail",
                "",
            ]
        )

        # Add operation details
        for op in operations:
            models_in = getattr(op, "models_in", [])
            models_out = getattr(op, "models_out", [])
            description = getattr(op, "description", "No description")
            category = getattr(op, "category", "general")

            lines.extend(
                [
                    f"### {op.name}",
                    "",
                    f"**Description**: {description}",
                    f"**Category**: {category}",
                ]
            )

            if models_in:
                lines.append(f"**Input Models**: {', '.join(models_in)}")
            else:
                lines.append("**Input Models**: None")

            if models_out:
                lines.append(f"**Output Models**: {', '.join(models_out)}")
            else:
                lines.append("**Output Models**: None")

            lines.append("")

        content = "\n".join(lines)
        output_file = self.output_dir / "operation-flow.md"
        output_file.write_text(content)

        return output_file

    def generate_model_relationships(
        self,
        models: list[Any],
    ) -> Path:
        """Generate model relationships diagram showing hierarchy and composition.

        Shows how models relate to each other (one-to-many, foreign keys, etc).

        Args:
            models: List of ModelRegistry entries

        Returns:
            Path to generated file
        """
        # Build relationship map by inspecting model fields
        relationships: dict[str, list[dict]] = {}
        model_names = {m.name for m in models}

        for model in models:
            model_name = model.name
            relationships[model_name] = []

            doc_cls = getattr(model, "document_cls", None)
            if doc_cls and hasattr(doc_cls, "model_fields"):
                try:
                    for field_name, field_info in doc_cls.model_fields.items():
                        field_type_str = str(field_info.annotation)

                        # Check for list[ModelName] - one-to-many
                        if "list" in field_type_str.lower():
                            for model_name_check in model_names:
                                if model_name_check in field_type_str:
                                    relationships[model_name].append(
                                        {
                                            "field": field_name,
                                            "target": model_name_check,
                                            "type": "one-to-many",  # This model has many of the target
                                            "description": field_info.description
                                            or f"List of {model_name_check}",
                                        }
                                    )
                                    break

                        # Check for simple string references - foreign key
                        elif "str" in field_type_str and not field_name.endswith("_id"):
                            for model_name_check in model_names:
                                if model_name_check.lower() in field_name.lower():
                                    relationships[model_name].append(
                                        {
                                            "field": field_name,
                                            "target": model_name_check,
                                            "type": "many-to-one",  # This model references one target
                                            "description": field_info.description
                                            or f"Reference to {model_name_check}",
                                        }
                                    )
                                    break
                except Exception:
                    pass

        # Generate Mermaid ER diagram - just relationships, no field details
        lines = [
            "# Model Relationships",
            "",
            "```mermaid",
            "erDiagram",
        ]

        # Add all models as entities (empty for cleaner diagram)
        for model in models:
            lines.append(f"    {model.name} {{}}")

        # Add relationships
        added_rels = set()
        for source_model, rels in relationships.items():
            for rel in rels:
                target = rel["target"]
                rel_type = rel["type"]

                # Use different Mermaid syntax for different relationship types
                if rel_type == "one-to-many":
                    # source ||--o{ target
                    rel_key = f"{source_model}||--o{{{target}"
                    if rel_key not in added_rels:
                        lines.append(f'    {source_model} ||--o{{ {target} : "{rel["field"]}"')
                        added_rels.add(rel_key)
                elif rel_type == "many-to-one":
                    # source }o--|| target
                    rel_key = f"{source_model}}}o--||{target}"
                    if rel_key not in added_rels:
                        lines.append(f'    {source_model} }}o--|| {target} : "{rel["field"]}"')
                        added_rels.add(rel_key)

        lines.extend(
            [
                "```",
                "",
                "## Legend",
                "",
                "- **Entities**: Data models (@datamodel decorated classes)",
                "- **Relationships**: How models connect",
                "  - `||--o{` = One-to-many (parent has many children)",
                "  - `}o--||` = Many-to-one (child belongs to parent)",
                "- **Labels**: Field names that create the relationships",
                "",
                "## Model Composition",
                "",
            ]
        )

        # Add detailed relationship descriptions
        for model in models:
            if relationships.get(model.name):
                lines.extend(
                    [
                        f"### {model.name}",
                        "",
                    ]
                )
                for rel in relationships[model.name]:
                    rel_type = rel["type"]
                    if rel_type == "one-to-many":
                        lines.append(f"- **has many** `{rel['target']}` via field `{rel['field']}`")
                    else:
                        lines.append(
                            f"- **belongs to** `{rel['target']}` via field `{rel['field']}`"
                        )
                lines.append("")

        lines.extend(
            [
                "```",
                "",
                "## Model Details",
                "",
            ]
        )

        # Add detailed model info
        for model in models:
            model_name = model.name
            description = getattr(model, "description", "No description")

            lines.extend(
                [
                    f"### {model_name}",
                    "",
                    f"{description}",
                    "",
                    "**Fields**:",
                    "",
                ]
            )

            doc_cls = getattr(model, "document_cls", None)
            if doc_cls and hasattr(doc_cls, "model_fields"):
                try:
                    for field_name, field_info in doc_cls.model_fields.items():
                        field_type = str(field_info.annotation)
                        field_desc = getattr(field_info, "description", "")
                        lines.append(f"- `{field_name}`: {field_type} - {field_desc}")
                except Exception:
                    pass

            # Add relationships for this model
            if model_name in relationships and relationships[model_name]:
                rels = relationships[model_name]
                lines.append("")
                lines.append("**Relationships**:")
                for rel in rels:
                    rel_type = rel["type"]
                    target = rel["target"]
                    field = rel["field"]
                    if rel_type == "one-to-many":
                        lines.append(f"- has many `{target}` via `{field}`")
                    else:
                        lines.append(f"- belongs to `{target}` via `{field}`")

            lines.append("")

        content = "\n".join(lines)
        output_file = self.output_dir / "model-relationships.md"
        output_file.write_text(content)

        return output_file

    def generate_all(
        self,
        models: list[Any],
        operations: list[Any],
    ) -> tuple[Path, Path]:
        """Generate all diagrams.

        Args:
            models: List of ModelRegistry entries
            operations: List of OperationRegistry entries

        Returns:
            Tuple of (operation_flow_file, model_relationships_file)
        """
        operation_flow = self.generate_operation_flow(models, operations)
        model_relationships = self.generate_model_relationships(models)

        return operation_flow, model_relationships

    def create_architecture_index(self, num_models: int, num_operations: int) -> Path:
        """Create index file for architecture documentation.

        Args:
            num_models: Number of models
            num_operations: Number of operations

        Returns:
            Path to created file
        """
        content = f"""# Architecture Documentation

Generated automatically from your `@datamodel` and `@operation` decorators.

## Overview

- **Models**: {num_models}
- **Operations**: {num_operations}

## Diagrams

### [Operation Flow](./operation-flow.md)
Shows how operations connect data models. Models are nodes, operations are edges showing data transformation paths.

### [Model Relationships](./model-relationships.md)
Shows foreign keys and references between models. Displays data dependencies and entity relationships.

## How to Update

1. Modify your `@datamodel` or `@operation` decorators
2. Run `make compile`
3. Graphs will be regenerated automatically

## Legend

- **@datamodel**: Decorated classes become nodes (models)
- **@operation**: Decorated functions become edges (transformations)
- **models_in/models_out**: Define which models an operation connects
"""
        index_file = self.output_dir / "README.md"
        index_file.write_text(content)

        return index_file
