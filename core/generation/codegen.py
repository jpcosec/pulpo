"""Code generation orchestration.

Main entry point for all code generation.
Coordinates init and compile phases.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from ..config.manager import ConfigManager
from ..analysis.graphs.graph_generator import MermaidGraphGenerator
from ..analysis.registries import ModelRegistry, OperationRegistry
from .compile.api_generator import FastAPIGenerator
from .compile.ui_generator import (
    TypeScriptUIConfigGenerator,
    CopyAndGenerateFrontend,
)


def _discover_and_import_items(project_dir: Path) -> None:
    """Discover and import all @datamodel and @operation items.

    This function imports Python modules to trigger decorator execution,
    which populates ModelRegistry and OperationRegistry.

    Args:
        project_dir: Path to project directory
    """
    # Load config to get model/operation directories
    config_path = project_dir / ".pulpo.yml"
    if config_path.exists():
        try:
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

    # Import all model files
    for model_dir in models_dirs:
        model_path = project_dir / model_dir
        if not model_path.exists():
            continue

        for py_file in sorted(model_path.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"models.{py_file.stem}", py_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            except Exception as e:
                print(f"   ✗ Failed to import {py_file}: {e}", file=sys.stderr)

    # Import all operation files
    for ops_dir in operations_dirs:
        ops_path = project_dir / ops_dir
        if not ops_path.exists():
            continue

        for py_file in sorted(ops_path.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"operations.{py_file.stem}", py_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            except Exception as e:
                print(f"   ✗ Failed to import {py_file}: {e}", file=sys.stderr)


def compile_all(project_dir: Path | None = None):
    """Compile all code generators from models and operations.

    This is the main entry point for the COMPILE phase.
    It discovers decorators and generates all code artifacts.

    Args:
        project_dir: Project directory (defaults to cwd or CONFIG_FILE env var)

    Generates:
        - API routes (run_cache/generated_api.py)
        - UI configs (run_cache/generated_ui_config.ts)
        - Frontend (run_cache/generated_frontend/)
        - CLI (run_cache/cli/<project>)
        - Graphs (docs/)
    """
    import os

    # Get project directory
    if project_dir is None:
        config_file = os.environ.get("CONFIG_FILE", ".")
        config_path = Path(config_file).absolute()
        project_dir = config_path.parent if config_path.is_file() else config_path
    else:
        project_dir = Path(project_dir).absolute()

    os.chdir(project_dir)

    print("\n=== COMPILE: Code Generation ===\n")
    print(f"📂 Project: {project_dir}\n")

    # DISCOVERY: Import models and operations
    print("🔍 Discovering models and operations...")
    _discover_and_import_items(project_dir)
    print("   ✅ Discovery complete\n")

    models = ModelRegistry.list_all()
    operations = OperationRegistry.list_all()
    print(f"📦 Found: {len(models)} models, {len(operations)} operations\n")

    # Get project name from config
    config_path = project_dir / ".pulpo.yml"
    project_name = "pulpo-app"
    if config_path.exists():
        try:
            config_mgr = ConfigManager(config_path)
            config = config_mgr.load()
            project_name = config.get("project_name", "pulpo-app")
        except Exception:
            pass

    # BUILD GRAPH: Construct registry graph
    print("🔗 Building registry graph...")
    try:
        from ..analysis.graph_builder import build_graph_from_registries, save_graph_to_project

        graph = build_graph_from_registries(project_name)

        # Validate graph
        is_valid, errors, warnings = graph.validate()

        if errors:
            print("\n❌ Graph validation errors:")
            for error in errors:
                print(f"  • {error}")
            print("\nFix these errors before continuing.\n")
            sys.exit(1)

        if warnings:
            print("\n⚠️  Graph validation warnings:")
            for warning in warnings:
                print(f"  • {warning}")
            print()

        # Save graph
        graph_path = save_graph_to_project(graph, project_dir)
        print(f"   ✅ Graph saved to {graph_path.relative_to(project_dir)}")

        # Show graph stats
        node_counts = {}
        for node_id, data in graph.graph.nodes(data=True):
            node_type = data.get("type", "unknown")
            node_counts[node_type] = node_counts.get(node_type, 0) + 1

        print(f"   📊 Graph: {len(graph.graph.nodes)} nodes, {len(graph.graph.edges)} edges")
        for node_type, count in sorted(node_counts.items()):
            print(f"      • {node_type}: {count}")
        print()

    except Exception as e:
        print(f"   ⚠️  Graph building failed: {e}")
        print("   Continuing without graph...\n")

    # GENERATION: Run all generators
    print("🔨 Generating code...\n")

    # 1. API
    api_gen = FastAPIGenerator(project_name=project_name)
    api_file = api_gen.generate()

    # 2. UI Config
    ui_gen = TypeScriptUIConfigGenerator()
    ui_file = ui_gen.generate()

    # 3. Frontend
    frontend_gen = CopyAndGenerateFrontend()
    frontend_dir = frontend_gen.generate()

    # 4. CLI (moved to init in future)
    print("\n→ Generating CLI...")
    from .init.cli_generator import generate_cli_script
    cli_dir = Path("run_cache/cli")
    cli_dir.mkdir(parents=True, exist_ok=True)
    cli_file = cli_dir / project_name

    cli_script = generate_cli_script()
    cli_file.write_text(cli_script)
    cli_file.chmod(0o755)
    print(f"  ✓ Generated {cli_file}")

    # 5. Architecture graphs
    print("\n→ Generating architecture diagrams...")
    try:
        docs_dir = project_dir / "docs"
        graph_gen = MermaidGraphGenerator(docs_dir)
        graph_gen.generate_all(models, operations)
        graph_gen.create_architecture_index(len(models), len(operations))
        print(f"  ✓ Graphs in {docs_dir}/")
    except Exception as e:
        print(f"  ⚠️  Graph generation failed: {e}")

    # 6. Debug: registry.json
    print("\n→ Generating debug files...")
    try:
        registry_file = Path("run_cache/registry.json")
        registry_data = {
            "models": [
                {
                    "name": m.name,
                    "description": m.description,
                    "fields": list(m.searchable_fields),
                }
                for m in models
            ],
            "operations": [
                {
                    "name": op.name,
                    "description": op.description,
                    "category": op.category,
                }
                for op in operations
            ],
        }
        registry_file.write_text(json.dumps(registry_data, indent=2))
        print(f"  ✓ registry.json")
    except Exception as e:
        print(f"  ⚠️  registry.json failed: {e}")

    print("\n=== Code Generation Complete ===")
    print("\nGenerated:")
    print(f"  ✓ {api_file}")
    print(f"  ✓ {ui_file}")
    print(f"  ✓ {frontend_dir}/")
    print(f"  ✓ {cli_file}")
    print(f"  ✓ docs/")


__all__ = ["compile_all"]
