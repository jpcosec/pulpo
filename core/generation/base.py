"""Base class for code generators.

All generators inherit from CodeGenerator which provides:
- Hash-based change detection
- Automatic regeneration when metadata changes
- Consistent output directory management
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..analysis.registries import ModelRegistry, OperationRegistry


class CodeGenerator:
    """Base class for code generators."""

    def __init__(self, output_dir: Path = Path(".run_cache")):
        """Initialize generator with output directory."""
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)

    def get_metadata_hash(self) -> str:
        """Get hash of current registry state to detect changes."""
        models_data = [
            {
                "name": m.name,
                "searchable": m.searchable_fields,
                "sortable": m.sortable_fields,
                "ui": m.ui_hints,
            }
            for m in ModelRegistry.list_all()
        ]

        ops_data = [
            {
                "name": op.name,
                "category": op.category,
                "inputs": op.input_schema.__name__,
                "outputs": op.output_schema.__name__,
            }
            for op in OperationRegistry.list_all()
        ]

        combined = json.dumps({"models": models_data, "ops": ops_data}, sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()[:12]

    def needs_regeneration(self, output_file: Path) -> bool:
        """Check if output file needs regeneration."""
        if not output_file.exists():
            return True

        # Check if hash has changed
        hash_file = output_file.with_suffix(".hash")
        if not hash_file.exists():
            return True

        current_hash = self.get_metadata_hash()
        stored_hash = hash_file.read_text().strip()

        return current_hash != stored_hash

    def save_hash(self, output_file: Path) -> None:
        """Save current metadata hash."""
        hash_file = output_file.with_suffix(".hash")
        hash_file.write_text(self.get_metadata_hash())
