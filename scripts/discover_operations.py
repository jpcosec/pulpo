"""Discover operations in the project."""

import sys
from pathlib import Path

from core.config_manager import ConfigManager
from core.analysis.registries import OperationRegistry


def main():
    """Discover and list all operations."""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "."
    config_path = Path(config_file)

    try:
        # Load config and get discovery directories
        config_mgr = ConfigManager(config_path / ".jobhunter.yml", project_root=config_path)
        config = config_mgr.load()
        _, ops_dirs = config_mgr.get_discovery_dirs()

        # Change to project root so imports work
        old_cwd = Path.cwd()
        import os
        os.chdir(config_path)

        # Import and register operations
        for ops_dir in ops_dirs:
            ops_path = Path(ops_dir)
            if ops_path.exists():
                sys.path.insert(0, str(config_path))
                for py_file in ops_path.glob("*.py"):
                    if py_file.name != "__init__.py":
                        try:
                            module_name = f"{ops_dir.replace('/', '.')}.{py_file.stem}"
                            __import__(module_name)
                        except Exception as e:
                            print(f"   ⚠️  Failed to import {py_file}: {e}", file=sys.stderr)

        if OperationRegistry._ops:
            print(f"\n✅ Found {len(OperationRegistry._ops)} operations:\n")
            for op_name, op_meta in OperationRegistry._ops.items():
                print(f"   • {op_name}")
                if hasattr(op_meta, 'description') and op_meta.description:
                    print(f"     {op_meta.description}")
        else:
            print("\n⚠️  No operations found. Check your operations directory.")
    except FileNotFoundError:
        print("❌ Config file not found. Run 'make setup-project' first.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error discovering operations: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
