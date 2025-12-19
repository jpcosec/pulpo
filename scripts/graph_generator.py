#!/usr/bin/env python3
"""Standalone script to generate Mermaid diagrams from metadata.

This script generates two types of diagrams:
1. Operation Flow Graph: Models as nodes, operations as directed edges
2. Model Relations Graph: Shows field-level relationships between models

Usage:
    # Generate from discovered models/operations
    python core/scripts/graph_generator.py

    # Specify output directory
    python core/scripts/graph_generator.py --output-dir docs/graphs

    # Just operation flow
    python core/scripts/graph_generator.py --flow-only

    # Just model relationships
    python core/scripts/graph_generator.py --relations-only

    # Verbose mode
    python core/scripts/graph_generator.py -v

Output:
    - operation-flow.md: Operation flow diagram
    - model-relationships.md: Model relationships diagram
    - README.md: Index with overview
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.graph_generator import MermaidGraphGenerator
from core.analysis.registries import ModelRegistry, OperationRegistry


def discover_and_register(project_dir: Path | None = None):
    """Auto-discover and import models and operations from project.

    Args:
        project_dir: Project directory to scan (default: current directory)

    Returns:
        Tuple of (models, operations) - already registered in registries
    """
    if project_dir is None:
        project_dir = Path.cwd()

    project_dir = project_dir.resolve()

    # Look for .jobhunter.yml config file
    config_file = project_dir / ".jobhunter.yml"

    if config_file.exists():
        print(f"→ Found project config: {config_file}")

        try:
            import importlib.util

            from core.config_manager import ConfigManager

            config_mgr = ConfigManager(config_file, project_root=project_dir)
            config = config_mgr.load()
            models_dirs, ops_dirs = config_mgr.get_discovery_dirs()

            print(f"  → Scanning: {', '.join(models_dirs)} (models), {', '.join(ops_dirs)} (operations)")

            # Add project directory to sys.path temporarily
            if str(project_dir) not in sys.path:
                sys.path.insert(0, str(project_dir))

            # Import all Python files in these directories to trigger decorators
            imported_count = 0
            for models_dir in models_dirs:
                model_path = project_dir / models_dir
                if model_path.exists():
                    for py_file in model_path.glob("*.py"):
                        if py_file.name.startswith("_"):
                            continue
                        try:
                            # Load module using importlib
                            module_name = f"{models_dir}.{py_file.stem}"
                            spec = importlib.util.spec_from_file_location(module_name, py_file)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                sys.modules[module_name] = module
                                spec.loader.exec_module(module)
                                imported_count += 1
                        except Exception as e:
                            print(f"    ⚠ Could not import {py_file.name}: {e}")

            for ops_dir in ops_dirs:
                ops_path = project_dir / ops_dir
                if ops_path.exists():
                    for py_file in ops_path.glob("*.py"):
                        if py_file.name.startswith("_"):
                            continue
                        try:
                            # Load module using importlib
                            module_name = f"{ops_dir}.{py_file.stem}"
                            spec = importlib.util.spec_from_file_location(module_name, py_file)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                sys.modules[module_name] = module
                                spec.loader.exec_module(module)
                                imported_count += 1
                        except Exception as e:
                            print(f"    ⚠ Could not import {py_file.name}: {e}")

            print(f"  ✓ Imported {imported_count} modules")

        except Exception as e:
            print(f"  ⚠ Config-based discovery failed: {e}")
            if "-v" in sys.argv or "--verbose" in sys.argv:
                import traceback
                traceback.print_exc()

    # Return what's in the registries (after imports)
    models = ModelRegistry.list_all()
    operations = OperationRegistry.list_all()

    print(f"  ✓ Registered: {len(models)} models, {len(operations)} operations")

    return models, operations


def generate_graphs(
    output_dir: Path,
    flow_only: bool = False,
    relations_only: bool = False,
    verbose: bool = False,
) -> tuple[Path | None, Path | None, Path | None]:
    """Generate Mermaid diagrams.

    Args:
        output_dir: Directory to save generated files
        flow_only: Only generate operation flow
        relations_only: Only generate model relationships
        verbose: Print detailed information

    Returns:
        Tuple of (flow_file, relations_file, index_file) or None if skipped
    """
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get data from registries (after discovery)
    models = ModelRegistry.list_all()
    operations = OperationRegistry.list_all()

    if verbose:
        print("\n📊 Registry State:")
        print(f"   Models: {len(models)}")
        print(f"   Operations: {len(operations)}")

        if models:
            print("\n📦 Models:")
            for model in models:
                print(f"   - {model.name}: {model.document_cls.__name__}")

        if operations:
            print("\n⚙️  Operations:")
            for op in operations:
                print(f"   - {op.name} ({op.category}): {op.description}")

    # Check if we have data
    if not models and not operations:
        print("\n❌ No models or operations found!")
        print("   Make sure decorators are imported before running this script.")
        return None, None, None

    # Create generator
    generator = MermaidGraphGenerator(output_dir)

    # Generate requested diagrams
    flow_file = None
    relations_file = None
    index_file = None

    print(f"\n→ Generating diagrams in {output_dir}/")

    if not relations_only:
        print("  → Generating operation flow...")
        try:
            flow_file = generator.generate_operation_flow(models, operations)
            print(f"    ✓ Created {flow_file.name}")

            if verbose:
                _print_file_preview(flow_file)

        except Exception as e:
            print(f"    ✗ Failed to generate operation flow: {e}")

    if not flow_only:
        print("  → Generating model relationships...")
        try:
            relations_file = generator.generate_model_relationships(models)
            print(f"    ✓ Created {relations_file.name}")

            if verbose:
                _print_file_preview(relations_file)

        except Exception as e:
            print(f"    ✗ Failed to generate model relationships: {e}")

    # Generate index
    print("  → Generating index...")
    try:
        index_file = generator.create_architecture_index(
            num_models=len(models),
            num_operations=len(operations),
        )
        print(f"    ✓ Created {index_file.name}")

    except Exception as e:
        print(f"    ✗ Failed to generate index: {e}")

    return flow_file, relations_file, index_file


def _print_file_preview(file_path: Path, max_lines: int = 15):
    """Print preview of generated file.

    Args:
        file_path: Path to file
        max_lines: Maximum lines to show
    """
    try:
        lines = file_path.read_text().splitlines()
        print(f"\n    Preview of {file_path.name}:")
        print("    " + "=" * 60)
        for i, line in enumerate(lines[:max_lines]):
            print(f"    {line}")
        if len(lines) > max_lines:
            print(f"    ... ({len(lines) - max_lines} more lines)")
        print("    " + "=" * 60)
    except Exception as e:
        print(f"    (Could not preview: {e})")


def print_summary(
    flow_file: Path | None,
    relations_file: Path | None,
    index_file: Path | None,
):
    """Print generation summary.

    Args:
        flow_file: Path to operation flow file
        relations_file: Path to model relationships file
        index_file: Path to index file
    """
    print("\n" + "=" * 70)
    print("✓ Graph Generation Complete")
    print("=" * 70)

    if flow_file:
        print("\n📊 Operation Flow:")
        print(f"   {flow_file.absolute()}")

    if relations_file:
        print("\n🔗 Model Relationships:")
        print(f"   {relations_file.absolute()}")

    if index_file:
        print("\n📖 Index:")
        print(f"   {index_file.absolute()}")

    print("\n💡 Tip: View these files in any Markdown viewer that supports Mermaid")
    print("   (GitHub, GitLab, VS Code with Markdown Preview Mermaid extension, etc.)")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Mermaid diagrams from @datamodel and @operation decorators",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all diagrams to default location
  python core/scripts/graph_generator.py

  # Generate to specific directory
  python core/scripts/graph_generator.py --output-dir run_cache/graphs

  # Only operation flow
  python core/scripts/graph_generator.py --flow-only

  # Only model relationships
  python core/scripts/graph_generator.py --relations-only

  # Verbose output
  python core/scripts/graph_generator.py -v
        """,
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("docs"),
        help="Output directory for generated files (default: docs/)",
    )

    parser.add_argument(
        "--project-dir",
        "-p",
        type=Path,
        default=None,
        help="Project directory to scan for models/operations (default: current directory)",
    )

    parser.add_argument(
        "--flow-only",
        action="store_true",
        help="Only generate operation flow diagram",
    )

    parser.add_argument(
        "--relations-only",
        action="store_true",
        help="Only generate model relationships diagram",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed information",
    )

    parser.add_argument(
        "--no-discover",
        action="store_true",
        help="Skip auto-discovery (use already registered models/operations)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.flow_only and args.relations_only:
        print("❌ Error: Cannot specify both --flow-only and --relations-only")
        sys.exit(1)

    print("=" * 70)
    print("🎨 Mermaid Graph Generator")
    print("=" * 70)

    # Discover models and operations
    if not args.no_discover:
        try:
            discover_and_register(args.project_dir)
        except Exception as e:
            print(f"⚠ Warning: Discovery failed: {e}")
            print("  Continuing with already registered models/operations...")
    else:
        print("→ Using already registered models/operations")

    # Generate graphs
    try:
        flow_file, relations_file, index_file = generate_graphs(
            output_dir=args.output_dir,
            flow_only=args.flow_only,
            relations_only=args.relations_only,
            verbose=args.verbose,
        )

        # Print summary
        if flow_file or relations_file or index_file:
            print_summary(flow_file, relations_file, index_file)
            sys.exit(0)
        else:
            print("\n❌ No files generated")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
