"""Discover datamodels and operations using imports.

This script imports Python modules to trigger decorator execution,
which populates the ModelRegistry and OperationRegistry.
"""

import importlib.util
import sys
from pathlib import Path


def discover_and_import(project_dir: Path) -> tuple[list, list]:
    """Discover and import models/operations from project directories.

    Args:
        project_dir: Path to project directory

    Returns:
        Tuple of (models, operations) lists from registries
    """
    # Load config to get model/operation directories
    config_path = project_dir / ".pulpo.yml"
    if config_path.exists():
        try:
            from core.config.manager import ConfigManager

            config_mgr = ConfigManager(config_path, project_root=project_dir)
            config = config_mgr.load()
            models_dirs, operations_dirs = config_mgr.get_discovery_dirs()
        except Exception as e:
            print(f"⚠️  Could not load config: {e}", file=sys.stderr)
            models_dirs = ["models"]
            operations_dirs = ["operations"]
    else:
        models_dirs = ["models"]
        operations_dirs = ["operations"]

    # Add project directory to path for imports
    project_dir_str = str(project_dir)
    if project_dir_str not in sys.path:
        sys.path.insert(0, project_dir_str)

    print(f"🔍 Discovery Configuration:")
    print(f"   ├─ Project: {project_dir}")
    print(f"   ├─ Models: {', '.join(models_dirs)}")
    print(f"   └─ Operations: {', '.join(operations_dirs)}\n")

    # Import all model files
    model_count = 0
    for model_dir in models_dirs:
        model_path = project_dir / model_dir
        if not model_path.exists():
            print(f"⚠️  Model directory not found: {model_path}")
            continue

        for py_file in sorted(model_path.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            try:
                # Dynamically import the file
                spec = importlib.util.spec_from_file_location(f"models.{py_file.stem}", py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    model_count += 1
                    print(f"   ✓ Imported: {model_dir}/{py_file.name}")
            except Exception as e:
                print(f"   ✗ Failed to import {py_file}: {e}", file=sys.stderr)

    # Import all operation files
    op_count = 0
    for ops_dir in operations_dirs:
        ops_path = project_dir / ops_dir
        if not ops_path.exists():
            print(f"⚠️  Operations directory not found: {ops_path}")
            continue

        for py_file in sorted(ops_path.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            try:
                # Dynamically import the file
                spec = importlib.util.spec_from_file_location(f"operations.{py_file.stem}", py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    op_count += 1
                    print(f"   ✓ Imported: {ops_dir}/{py_file.name}")
            except Exception as e:
                print(f"   ✗ Failed to import {py_file}: {e}", file=sys.stderr)

    print(f"\n📊 Imported {model_count} model files, {op_count} operation files\n")

    # Now read from registries (populated by imports)
    from core.analysis.registries import ModelRegistry, OperationRegistry

    models = ModelRegistry.list_all()
    operations = OperationRegistry.list_all()

    return models, operations


def main():
    """Main entry point for discovery."""
    import os

    # Get project directory from CONFIG_FILE env var or first argument
    config_file = os.environ.get("CONFIG_FILE")
    if config_file:
        config_path = Path(config_file).absolute()
        project_dir = config_path.parent if config_path.is_file() else config_path
    elif len(sys.argv) > 1:
        project_dir = Path(sys.argv[1]).absolute()
    else:
        project_dir = Path.cwd()

    print(f"\n=== Discovery via Imports ===\n")

    # Discover and import
    models, operations = discover_and_import(project_dir)

    # Display discovered models
    print(f"📦 Discovered Models ({len(models)}):")
    if models:
        for model in models:
            surfaces = model.get("surfaces", [])
            surfaces_str = f" [{', '.join(surfaces)}]" if surfaces else ""
            print(f"   ├─ {model['name']}{surfaces_str}")
            if model.get("description"):
                print(f"   │  └─ {model['description']}")
    else:
        print("   └─ No models found\n")

    # Display discovered operations
    print(f"\n🔧 Discovered Operations ({len(operations)}):")
    if operations:
        for op in operations:
            category = op.get("category", "")
            category_str = f" ({category})" if category else ""
            surfaces = op.get("surfaces", [])
            surfaces_str = f" [{', '.join(surfaces)}]" if surfaces else ""
            print(f"   ├─ {op['name']}{category_str}{surfaces_str}")
            if op.get("description"):
                print(f"   │  └─ {op['description']}")
    else:
        print("   └─ No operations found\n")

    # Summary
    print(f"\n✅ Discovery complete!")
    print(f"   ├─ Models: {len(models)}")
    print(f"   ├─ Operations: {len(operations)}")
    print(f"   └─ Next: make compile\n")

    return 0 if (models or operations) else 1


if __name__ == "__main__":
    sys.exit(main())
