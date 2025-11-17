"""Pulpo Framework CLI: Analysis and code generation.

This CLI provides:
- Analysis: Inspect models/operations without generating code
- Generation: Create project artifacts (CLI, config, code)

For operational commands (services, db, workflows), use the GENERATED project CLI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from ..analysis.registries import ModelRegistry, OperationRegistry


class CLI:
    """Framework CLI for Pulpo.

    Responsibilities:
    - Discover and inspect @datamodel and @operation decorators
    - Validate and lint user code
    - Generate graphs and documentation
    - Generate project CLI and code artifacts

    Does NOT:
    - Start/stop services (use generated ./main CLI)
    - Execute operations (use generated ./main CLI)
    - Manage database (use generated ./main CLI)

    Usage:
        # Analysis (no generation needed)
        pulpo list-models
        pulpo inspect operation create_user
        pulpo validate
        pulpo draw-graphs

        # Generation
        pulpo init        # First time: generate CLI + config
        pulpo compile     # Generate all code
    """

    def __init__(
        self,
        verbose: bool = False,
    ):
        """Initialize Framework CLI.

        Args:
            verbose: Verbose output (default: False)
        """
        self.verbose = verbose
        self.console = Console()

        # Fresh discovery on instantiation
        self.model_registry = ModelRegistry()
        self.operation_registry = OperationRegistry()

    # =========================================================================
    # ANALYSIS COMMANDS - Work without generated code
    # =========================================================================

    def list_models(self) -> list[str]:
        """List all discovered @datamodel classes.

        Returns:
            List of model names

        Example:
            >>> cli = CLI()
            >>> models = cli.list_models()
            >>> print(models)
            ['User', 'Product', 'Order']
        """
        models = self.model_registry.list_all()
        names = [m.name for m in models]

        if self.verbose:
            self.console.print(f"[cyan]Found {len(names)} models[/cyan]")
            for name in names:
                self.console.print(f"  - {name}")

        return sorted(names)

    def list_operations(self) -> list[str]:
        """List all discovered @operation functions.

        Returns:
            List of operation names

        Example:
            >>> cli = CLI()
            >>> ops = cli.list_operations()
            >>> print(ops)
            ['create_user', 'update_product', 'process_order']
        """
        operations = self.operation_registry.list_all()
        names = [op.name for op in operations]

        if self.verbose:
            self.console.print(f"[cyan]Found {len(names)} operations[/cyan]")
            for name in names:
                self.console.print(f"  - {name}")

        return sorted(names)

    def inspect_model(self, name: str) -> dict[str, Any]:
        """Inspect a specific model.

        Args:
            name: Model name

        Returns:
            Dictionary with model metadata

        Example:
            >>> cli = CLI()
            >>> info = cli.inspect_model("User")
            >>> print(info['fields'])
        """
        model = self.model_registry.get(name)
        if not model:
            raise ValueError(f"Model '{name}' not found")

        info = {
            "name": model.name,
            "description": model.description,
            "searchable_fields": list(model.searchable_fields),
            "sortable_fields": list(model.sortable_fields),
            "ui_hints": model.ui_hints,
        }

        if self.verbose:
            self.console.print(f"[cyan]Model: {model.name}[/cyan]")
            self.console.print(f"Description: {model.description}")
            self.console.print(f"Searchable: {', '.join(model.searchable_fields)}")

        return info

    def inspect_operation(self, name: str) -> dict[str, Any]:
        """Inspect a specific operation.

        Args:
            name: Operation name

        Returns:
            Dictionary with operation metadata

        Example:
            >>> cli = CLI()
            >>> info = cli.inspect_operation("create_user")
            >>> print(info['inputs'])
        """
        operation = self.operation_registry.get(name)
        if not operation:
            raise ValueError(f"Operation '{name}' not found")

        info = {
            "name": operation.name,
            "description": operation.description,
            "category": operation.category,
            "input_schema": operation.input_schema.__name__,
            "output_schema": operation.output_schema.__name__,
        }

        if self.verbose:
            self.console.print(f"[cyan]Operation: {operation.name}[/cyan]")
            self.console.print(f"Description: {operation.description}")
            self.console.print(f"Category: {operation.category}")
            self.console.print(f"Input: {operation.input_schema.__name__}")
            self.console.print(f"Output: {operation.output_schema.__name__}")

        return info

    def list_operations_by_category(self) -> dict[str, list[str]]:
        """Group operations by category.

        Returns:
            Dictionary mapping category to operation names

        Example:
            >>> cli = CLI()
            >>> by_cat = cli.list_operations_by_category()
            >>> print(by_cat['user-management'])
            ['create_user', 'update_user']
        """
        operations = self.operation_registry.list_all()
        by_category: dict[str, list[str]] = {}

        for op in operations:
            category = op.category or "uncategorized"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(op.name)

        if self.verbose:
            self.console.print("[cyan]Operations by category:[/cyan]")
            for cat, ops in sorted(by_category.items()):
                self.console.print(f"  {cat}: {len(ops)} operations")

        return by_category

    def validate(self, strict: bool = False) -> list[str]:
        """Validate models and operations.

        Args:
            strict: Enable strict mode with all checks

        Returns:
            List of validation errors (empty if valid)

        Example:
            >>> cli = CLI()
            >>> errors = cli.validate()
            >>> if errors:
            >>>     print("Validation failed:", errors)
        """
        from ..analysis.validation.linter import DataModelLinter

        errors = []

        # Lint models
        linter = DataModelLinter()
        for model in self.model_registry.list_all():
            model_errors = linter.lint_model(model)
            errors.extend(model_errors)

        # Lint operations
        for op in self.operation_registry.list_all():
            op_errors = linter.lint_operation(op)
            errors.extend(op_errors)

        if self.verbose:
            if errors:
                self.console.print(f"[red]Found {len(errors)} errors[/red]")
                for error in errors:
                    self.console.print(f"  - {error}")
            else:
                self.console.print("[green]✓ All validations passed[/green]")

        return errors

    def draw_graphs(self, output_dir: Path | None = None) -> Path:
        """Generate Mermaid diagrams for models and operations.

        Args:
            output_dir: Output directory (default: docs/)

        Returns:
            Path to generated graphs directory

        Example:
            >>> cli = CLI()
            >>> graphs_dir = cli.draw_graphs()
            >>> print(f"Graphs generated in {graphs_dir}")
        """
        from ..analysis.graphs.graph_generator import MermaidGraphGenerator

        output_dir = output_dir or Path("docs")
        output_dir.mkdir(parents=True, exist_ok=True)

        graph_gen = MermaidGraphGenerator(output_dir)
        models = self.model_registry.list_all()
        operations = self.operation_registry.list_all()

        graph_gen.generate_all(models, operations)
        graph_gen.create_architecture_index(len(models), len(operations))

        if self.verbose:
            self.console.print(f"[green]✓ Graphs generated in {output_dir}/[/green]")

        return output_dir

    def show_flow(self, operation_name: str) -> None:
        """Show data flow for a specific operation.

        Args:
            operation_name: Name of operation to analyze

        Example:
            >>> cli = CLI()
            >>> cli.show_flow("create_user")
        """
        from core.analysis.dataflow.dataflow import DataFlowAnalyzer, OperationMetadata as DFOperationMetadata

        operation = self.operation_registry.get(operation_name)
        if not operation:
            raise ValueError(f"Operation '{operation_name}' not found")

        self.console.print(f"\n[bold cyan]Data Flow Analysis: {operation.name}[/bold cyan]\n")

        # Show basic operation info
        self.console.print(f"[yellow]Operation Details:[/yellow]")
        self.console.print(f"  Name:        {operation.name}")
        self.console.print(f"  Category:    {operation.category}")
        self.console.print(f"  Input:       {operation.input_schema.__name__}")
        self.console.print(f"  Output:      {operation.output_schema.__name__}")
        self.console.print(f"  Async:       {operation.async_enabled}")

        # Show models used
        if operation.models_in or operation.models_out:
            self.console.print(f"\n[yellow]Data Models:[/yellow]")
            if operation.models_in:
                self.console.print(f"  Reads:       {', '.join(operation.models_in)}")
            if operation.models_out:
                self.console.print(f"  Writes:      {', '.join(operation.models_out)}")

        # Analyze dependencies with all operations
        all_operations = self.operation_registry.list_all()
        df_operations = [DFOperationMetadata(op) for op in all_operations]

        try:
            analysis = DataFlowAnalyzer.analyze(df_operations)

            # Show dependencies
            deps = analysis["dependencies"].get(operation.name, [])
            if deps:
                self.console.print(f"\n[yellow]Dependencies (runs after):[/yellow]")
                for dep in deps:
                    self.console.print(f"  → {dep}")
            else:
                self.console.print(f"\n[yellow]Dependencies:[/yellow] None (can run first)")

            # Show dependents
            graph = analysis["graph"]
            dependents = graph.get_dependents(operation.name)
            if dependents:
                self.console.print(f"\n[yellow]Dependents (runs before):[/yellow]")
                for dep in dependents:
                    self.console.print(f"  → {dep}")

            # Show execution order position
            exec_order = analysis["execution_order"]
            if operation.name in exec_order:
                position = exec_order.index(operation.name) + 1
                total = len(exec_order)
                self.console.print(f"\n[yellow]Execution Order:[/yellow] {position} of {total}")

            # Show parallel group
            parallel_groups = analysis["parallel_groups"]
            for i, group in enumerate(parallel_groups):
                if operation.name in group:
                    if len(group) > 1:
                        self.console.print(f"\n[yellow]Parallel Group {i}:[/yellow]")
                        for op_name in group:
                            marker = "●" if op_name == operation.name else "○"
                            self.console.print(f"  {marker} {op_name}")
                    break

        except Exception as e:
            self.console.print(f"\n[red]Error analyzing data flow: {e}[/red]")

        self.console.print()

    def summary(self) -> str:
        """Show summary of discovered models and operations.

        Returns:
            Summary string

        Example:
            >>> cli = CLI()
            >>> print(cli.summary())
        """
        models = self.model_registry.list_all()
        operations = self.operation_registry.list_all()

        summary = f"""
Pulpo Framework Summary
=======================
Models: {len(models)}
Operations: {len(operations)}
Categories: {len(self.list_operations_by_category())}
        """.strip()

        if self.verbose:
            self.console.print(summary)

        return summary

    # =========================================================================
    # GENERATION COMMANDS - Create code artifacts
    # =========================================================================

    def init(self, project_dir: Path | None = None) -> None:
        """Initialize new project (first-time setup).

        Generates:
        - CLI executable (./main)
        - Configuration file (.pulpo.yml)
        - Initial graphs (docs/)

        Args:
            project_dir: Project directory (default: current directory)

        Example:
            >>> cli = CLI()
            >>> cli.init()
            # Creates ./main, .pulpo.yml, docs/
        """
        from ..generation.init.cli_generator import generate_cli_script
        from ..generation.init.project_init import init_project as init_proj

        project_dir = project_dir or Path.cwd()

        if self.verbose:
            self.console.print(f"[cyan]Initializing project in {project_dir}[/cyan]")

        # 1. Generate project config
        init_proj(project_dir)

        # 2. Generate CLI executable
        cli_dir = project_dir / "run_cache" / "cli"
        cli_dir.mkdir(parents=True, exist_ok=True)

        # Get project name from config
        from ..config.manager import ConfigManager
        config_path = project_dir / ".pulpo.yml"
        project_name = "main"
        if config_path.exists():
            try:
                config_mgr = ConfigManager(config_path)
                config = config_mgr.load()
                project_name = config.get("project_name", "main")
            except Exception:
                pass

        cli_file = cli_dir.parent.parent / project_name
        cli_script = generate_cli_script()
        cli_file.write_text(cli_script)
        cli_file.chmod(0o755)

        # 3. Generate initial graphs
        self.draw_graphs(project_dir / "docs")

        if self.verbose:
            self.console.print(f"[green]✓ Project initialized[/green]")
            self.console.print(f"  - CLI: {cli_file}")
            self.console.print(f"  - Config: {config_path}")
            self.console.print(f"  - Graphs: {project_dir / 'docs'}/")

    def compile(self, project_dir: Path | None = None) -> None:
        """Generate all code artifacts from models and operations.

        Generates:
        - API routes (run_cache/generated_api.py)
        - UI configuration (run_cache/generated_frontend/)
        - Prefect workflows (run_cache/prefect_flows.py)
        - Project CLI (./main)
        - Graphs (docs/)

        Args:
            project_dir: Project directory (default: current directory)

        Example:
            >>> cli = CLI()
            >>> cli.compile()
            # Generates all code in run_cache/
        """
        from ..generation.codegen import compile_all

        project_dir = project_dir or Path.cwd()

        if self.verbose:
            self.console.print(f"[cyan]Compiling project in {project_dir}[/cyan]")

        compile_all(project_dir)

        if self.verbose:
            self.console.print("[green]✓ Compilation complete[/green]")

    # =========================================================================
    # INFO & HELP
    # =========================================================================

    def check_version(self) -> dict[str, str]:
        """Check Pulpo version.

        Returns:
            Dictionary with version info

        Example:
            >>> cli = CLI()
            >>> version = cli.check_version()
            >>> print(version['pulpo'])
        """
        from ... import __version__

        version_info = {
            "pulpo": __version__,
            "python": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
        }

        if self.verbose:
            self.console.print(f"[cyan]Pulpo version: {version_info['pulpo']}[/cyan]")
            self.console.print(f"Python version: {version_info['python']}")

        return version_info


__all__ = ["CLI"]
