"""Documentation helper for extracting docstrings from models and operations.

This module provides utilities to extract and format docstrings from:
- Framework documentation (Pulpo core docs)
- Project models (@datamodel decorated classes)
- Project operations (@operation decorated functions)

Usage:
    from core.doc_helper import DocHelper

    helper = DocHelper()

    # Get framework documentation
    framework_docs = helper.get_framework_doc("datamodel")
    print(framework_docs)

    # Get project model documentation
    model_docs = helper.get_model_docs("User")
    print(model_docs)

    # Get operation documentation
    op_docs = helper.get_operation_docs("users.create")
    print(op_docs)

    # List all available documentation
    all_docs = helper.list_all_docs()
    for doc in all_docs:
        print(doc)
"""

import inspect
from pathlib import Path
from typing import Optional

from ..analysis.registries import ModelRegistry, OperationRegistry


class DocHelper:
    """Helper for extracting and formatting documentation."""

    def __init__(self):
        """Initialize documentation helper."""
        self.framework_dir = Path(__file__).parent.parent / "docs"
        self.model_registry = ModelRegistry()
        self.operation_registry = OperationRegistry()

    # ========================================================================
    # Framework Documentation
    # ========================================================================

    def get_framework_doc(self, topic: str) -> Optional[str]:
        """Get framework documentation by topic.

        Args:
            topic: Documentation topic (e.g., "datamodel", "operation", "cli", "architecture")

        Returns:
            Documentation content or None if not found
        """
        # Map topics to doc files
        topic_map = {
            "datamodel": "DATAMODEL_DECORATOR.md",
            "operation": "OPERATION_DECORATOR.md",
            "cli": "CLI_ARCHITECTURE.md",
            "architecture": "ARCHITECTURE_OVERVIEW.md",
            "orchestration": "ORCHESTRATION.md",
            "caching": "CACHING_AND_OPTIMIZATION.md",
            "code-generation": "CODE_GENERATION_FLOW.md",
            "error-handling": "ERROR_HANDLING.md",
            "linting": "LINTER_GUIDE.md",
        }

        doc_file = topic_map.get(topic.lower())
        if not doc_file:
            return None

        doc_path = self.framework_dir / doc_file
        if doc_path.exists():
            try:
                return doc_path.read_text()
            except Exception as e:
                return f"Error reading documentation: {e}"

        return None

    def list_framework_docs(self) -> list[str]:
        """List available framework documentation topics.

        Returns:
            List of available documentation topics
        """
        return [
            "datamodel",
            "operation",
            "cli",
            "architecture",
            "orchestration",
            "caching",
            "code-generation",
            "error-handling",
            "linting",
        ]

    # ========================================================================
    # Model Documentation
    # ========================================================================

    def get_model_docs(self, model_name: str) -> Optional[str]:
        """Get documentation for a model.

        Extracts docstring from the model class and metadata from decorator.

        Args:
            model_name: Model name (e.g., "User", "Post")

        Returns:
            Formatted documentation or None if not found
        """
        model = self.model_registry.get(model_name)
        if not model:
            return None

        lines = []

        # Title
        lines.append(f"# Model: {model.name}")

        # Description
        if model.description:
            lines.append(f"\n{model.description}")

        # Class docstring
        doc_cls = model.document_cls
        if doc_cls.__doc__:
            lines.append(f"\n{doc_cls.__doc__}")

        # Metadata
        lines.append("\n## Metadata")
        if model.tags:
            lines.append(f"- **Tags**: {', '.join(model.tags)}")
        if model.searchable_fields:
            lines.append(f"- **Searchable**: {', '.join(model.searchable_fields)}")
        if model.sortable_fields:
            lines.append(f"- **Sortable**: {', '.join(model.sortable_fields)}")

        # Fields
        fields = self._get_model_fields(doc_cls)
        if fields:
            lines.append("\n## Fields")
            for field_name, field_info in fields.items():
                lines.append(f"- **{field_name}**: {field_info['type']}")
                if field_info.get("description"):
                    lines.append(f"  {field_info['description']}")

        # CRUD Endpoints
        lines.append("\n## Auto-Generated CRUD Endpoints")
        lines.append(f"- `GET /{model.name.lower()}s` - List all {model.name.lower()}s")
        lines.append(f"- `POST /{model.name.lower()}s` - Create new {model.name.lower()}")
        lines.append(f"- `GET /{model.name.lower()}s/{{id}}` - Get specific {model.name.lower()}")
        lines.append(f"- `PUT /{model.name.lower()}s/{{id}}` - Update {model.name.lower()}")
        lines.append(f"- `DELETE /{model.name.lower()}s/{{id}}` - Delete {model.name.lower()}")

        return "\n".join(lines)

    def list_model_docs(self) -> list[str]:
        """List all available model documentation.

        Returns:
            List of model names
        """
        models = self.model_registry.list_all()
        return [m.name for m in sorted(models, key=lambda x: x.name)]

    # ========================================================================
    # Operation Documentation
    # ========================================================================

    def get_operation_docs(self, operation_name: str) -> Optional[str]:
        """Get documentation for an operation.

        Extracts docstring from the operation function and metadata from decorator.

        Args:
            operation_name: Operation name (e.g., "users.create", "posts.list")

        Returns:
            Formatted documentation or None if not found
        """
        op = self.operation_registry.get(operation_name)
        if not op:
            return None

        lines = []

        # Title
        lines.append(f"# Operation: {op.name}")

        # Description
        if op.description:
            lines.append(f"\n{op.description}")

        # Function docstring (if available)
        if hasattr(op, "func") and op.func.__doc__:
            lines.append(f"\n{op.func.__doc__}")

        # Metadata
        lines.append("\n## Metadata")
        if op.category:
            lines.append(f"- **Category**: {op.category}")

        # Input/Output
        if op.input_schema:
            lines.append(
                f"- **Input**: `{op.input_schema.__name__}` - "
                + (op.input_schema.__doc__ or "")
            )
        if op.output_schema:
            lines.append(
                f"- **Output**: `{op.output_schema.__name__}` - "
                + (op.output_schema.__doc__ or "")
            )

        # Models affected
        if op.models_in or op.models_out:
            lines.append("\n## Model Relationships")
            if op.models_in:
                lines.append(f"- **Reads**: {', '.join(op.models_in)}")
            if op.models_out:
                lines.append(f"- **Writes**: {', '.join(op.models_out)}")

        # API Endpoint
        lines.append("\n## API Endpoint")
        lines.append(f"```\nPOST /operations/{op.name}\n```")

        # CLI Command
        parts = op.name.split(".")
        if len(parts) >= 3:
            lines.append(f"\n## CLI Command")
            lines.append(f"```\n./main ops {' '.join(parts[1:])}\n```")

        return "\n".join(lines)

    def list_operation_docs(self) -> list[str]:
        """List all available operation documentation.

        Returns:
            List of operation names
        """
        ops = self.operation_registry.list_all()
        return [o.name for o in sorted(ops, key=lambda x: x.name)]

    # ========================================================================
    # Combined Documentation
    # ========================================================================

    def list_all_docs(self) -> dict[str, list[str]]:
        """List all available documentation.

        Returns:
            Dict with 'framework', 'models', 'operations' keys
        """
        return {
            "framework": self.list_framework_docs(),
            "models": self.list_model_docs(),
            "operations": self.list_operation_docs(),
        }

    def get_doc(self, doc_type: str, doc_name: str) -> Optional[str]:
        """Get documentation by type and name.

        Args:
            doc_type: Type of documentation ('framework', 'model', 'operation')
            doc_name: Name of the documentation

        Returns:
            Documentation content or None if not found
        """
        if doc_type == "framework":
            return self.get_framework_doc(doc_name)
        elif doc_type == "model":
            return self.get_model_docs(doc_name)
        elif doc_type == "operation":
            return self.get_operation_docs(doc_name)

        return None

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _get_model_fields(self, doc_cls) -> dict:
        """Extract field information from a model class.

        Args:
            doc_cls: The document class

        Returns:
            Dict of field info
        """
        fields = {}

        if hasattr(doc_cls, "model_fields"):
            # Pydantic v2
            for field_name, field_info in doc_cls.model_fields.items():
                fields[field_name] = {
                    "type": str(field_info.annotation),
                    "description": field_info.description or "",
                }
        elif hasattr(doc_cls, "__fields__"):
            # Pydantic v1 / Beanie
            for field_name, field_info in doc_cls.__fields__.items():
                fields[field_name] = {
                    "type": str(field_info.outer_type_),
                    "description": field_info.field_info.description or "",
                }

        return fields


def format_doc_output(doc_content: str, max_width: int = 80) -> str:
    """Format documentation for terminal display.

    Args:
        doc_content: Documentation content to format
        max_width: Maximum width for terminal

    Returns:
        Formatted documentation
    """
    # For now, just return as-is
    # Could add fancy terminal formatting here (colors, wrapping, etc.)
    return doc_content
