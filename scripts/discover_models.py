"""Discover datamodels in the project."""

import sys
from pathlib import Path

from core.config_manager import ConfigManager
from core.registries import ModelRegistry


def main():
    """Discover and list all datamodels."""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "."
    config_path = Path(config_file)

    try:
        # Load config and get discovery directories
        config_mgr = ConfigManager(config_path / ".jobhunter.yml", project_root=config_path)
        config = config_mgr.load()
        models_dirs, _ = config_mgr.get_discovery_dirs()

        # Change to project root so imports work
        old_cwd = Path.cwd()
        import os
        os.chdir(config_path)

        # Import and register models
        for model_dir in models_dirs:
            model_path = Path(model_dir)
            if model_path.exists():
                sys.path.insert(0, str(config_path))
                for py_file in model_path.glob("*.py"):
                    if py_file.name != "__init__.py":
                        try:
                            module_name = f"{model_dir.replace('/', '.')}.{py_file.stem}"
                            __import__(module_name)
                        except Exception as e:
                            print(f"   ⚠️  Failed to import {py_file}: {e}", file=sys.stderr)

        if ModelRegistry._models:
            print(f"\n✅ Found {len(ModelRegistry._models)} datamodels:\n")
            for model_name, model_meta in ModelRegistry._models.items():
                print(f"   • {model_name}")
                if hasattr(model_meta, 'description') and model_meta.description:
                    print(f"     {model_meta.description}")
        else:
            print("\n⚠️  No datamodels found. Check your models directory.")
    except FileNotFoundError:
        print("❌ Config file not found. Run 'make setup-project' first.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error discovering models: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
