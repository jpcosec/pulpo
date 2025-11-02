"""Discover datamodels and operations via main entrypoint import.

This script imports a project's main.py file to trigger decorator execution,
which populates the ModelRegistry and OperationRegistry.

Usage:
    python -m scripts.discovery_main /path/to/project/main.py
    python -m scripts.discovery_main .  # Use main.py in current dir
"""

import importlib.util
import sys
from pathlib import Path


def discover_via_main(main_path: Path) -> tuple[list, list]:
    """Discover models/operations by importing main.py entrypoint.

    Args:
        main_path: Path to main.py file or directory containing it

    Returns:
        Tuple of (models, operations) lists from registries

    Raises:
        FileNotFoundError: If main.py not found
        ImportError: If main.py cannot be imported
    """
    # Resolve main.py path
    if main_path.is_dir():
        main_file = main_path / "main.py"
    else:
        main_file = main_path

    if not main_file.exists():
        raise FileNotFoundError(f"main.py not found at {main_file}")

    # Add parent directory to path for imports
    project_dir = main_file.parent
    project_dir_str = str(project_dir)
    if project_dir_str not in sys.path:
        sys.path.insert(0, project_dir_str)

    print(f"🔍 Discovery via Main Entrypoint:")
    print(f"   ├─ Project: {project_dir}")
    print(f"   └─ Entrypoint: {main_file.name}\n")

    # Import main.py to trigger decorators
    try:
        spec = importlib.util.spec_from_file_location("main", main_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["main"] = module
            spec.loader.exec_module(module)
            print(f"   ✓ Imported: {main_file.name}\n")
        else:
            raise ImportError(f"Cannot create module spec for {main_file}")
    except Exception as e:
        print(f"   ✗ Failed to import {main_file}: {e}\n", file=sys.stderr)
        raise

    # Read from registries (populated by imports)
    from core.registries import ModelRegistry, OperationRegistry

    models = ModelRegistry.list_all()
    operations = OperationRegistry.list_all()

    return models, operations


def main():
    """Main entry point for discovery."""
    import os

    # Get project directory from first argument or current directory
    if len(sys.argv) > 1:
        main_path = Path(sys.argv[1]).absolute()
    else:
        main_path = Path.cwd()

    print(f"\n=== Discovery via Main Entrypoint ===\n")

    try:
        # Discover via main.py import
        models, operations = discover_via_main(main_path)

        # Display discovered models
        print(f"📦 Discovered Models ({len(models)}):")
        if models:
            for model in models:
                surfaces = model.get("surfaces", [])
                surfaces_str = f" [{', '.join(surfaces)}]" if surfaces else ""
                print(f"   ├─ {model.name}{surfaces_str}")
                if model.description:
                    print(f"   │  └─ {model.description}")
        else:
            print("   └─ No models found\n")

        # Display discovered operations
        print(f"\n🔧 Discovered Operations ({len(operations)}):")
        if operations:
            for op in operations:
                category = op.category if op.category else ""
                category_str = f" ({category})" if category else ""
                surfaces = op.get("surfaces", [])
                surfaces_str = f" [{', '.join(surfaces)}]" if surfaces else ""
                print(f"   ├─ {op.name}{category_str}{surfaces_str}")
                if op.description:
                    print(f"   │  └─ {op.description}")
        else:
            print("   └─ No operations found\n")

        # Summary
        print(f"\n✅ Discovery complete!")
        print(f"   ├─ Models: {len(models)}")
        print(f"   ├─ Operations: {len(operations)}")
        print(f"   └─ Next: python main.py compile\n")

        return 0 if (models or operations) else 1

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        print(
            f"\nUsage: python -m scripts.discovery_main /path/to/project/main.py",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
