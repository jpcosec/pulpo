"""Pulpo CLI: Dynamic discovery interface for models and operations.

The CLI class provides programmatic access to framework functionality:
- Dynamic discovery of @datamodel and @operation decorators
- Inspection methods (no compilation needed)
- Full-stack methods (auto-compile as needed)
- Smart run_cache management
"""

from __future__ import annotations

import inspect
import shutil
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .registries import ModelRegistry, OperationRegistry


class CLI:
    """Programmatic CLI interface for Pulpo framework.

    Provides methods for discovering, inspecting, and running models and operations.

    Usage:
        cli = CLI()  # Fresh discovery on instantiation

        # Inspect (no compilation)
        cli.list_models()
        cli.inspect_operation("my_op")
        cli.draw_graphs()

        # Full stack (auto-compiles if needed)
        cli.api()  # Starts FastAPI
        cli.prefect()  # Starts Prefect with flows
    """

    def __init__(
        self,
        run_cache_dir: str | Path = "run_cache",
        auto_compile: bool = True,
        verbose: bool = False,
    ):
        """Initialize CLI with fresh discovery.

        Args:
            run_cache_dir: Directory for generated artifacts (default: run_cache/)
            auto_compile: Auto-compile before operations needing it (default: True)
            verbose: Verbose output (default: False)
        """
        self.run_cache_dir = Path(run_cache_dir)
        self.auto_compile = auto_compile
        self.verbose = verbose
        self.console = Console()

        # Fresh discovery on instantiation
        self.model_registry = ModelRegistry()
        self.operation_registry = OperationRegistry()

    # =========================================================================
    # Category 1: Inspection Methods (No run_cache needed)
    # =========================================================================

    def list_models(self) -> list[str]:
        """List all registered models.

        Returns:
            List of model names from decorators.

        Example:
            >>> cli = CLI()
            >>> models = cli.list_models()
            >>> print(models)
            ['Job', 'User', 'Company']
        """
        models = self.model_registry.list_all()
        names = [m.name for m in models]

        if self.verbose:
            self.console.print(f"[cyan]Found {len(names)} models[/cyan]")
            for name in names:
                self.console.print(f"  - {name}")

        return sorted(names)

    def list_operations(self) -> list[str]:
        """List all registered operations.

        Returns:
            List of operation names from decorators.

        Example:
            >>> cli = CLI()
            >>> ops = cli.list_operations()
            >>> print(ops)
            ['search_jobs', 'create_user', 'process_batch']
        """
        ops = self.operation_registry.list_all()
        names = [o.name for o in ops]

        if self.verbose:
            self.console.print(f"[cyan]Found {len(names)} operations[/cyan]")
            for name in names:
                self.console.print(f"  - {name}")

        return sorted(names)

    def inspect_model(self, name: str) -> dict[str, Any]:
        """Get detailed information about a model.

        Args:
            name: Model name.

        Returns:
            Dictionary with model metadata (name, description, fields, etc.).

        Raises:
            ValueError: If model not found.

        Example:
            >>> cli = CLI()
            >>> info = cli.inspect_model("Job")
            >>> print(info['description'])
        """
        model = self.model_registry.get(name)
        if not model:
            raise ValueError(f"Model '{name}' not found. Available: {self.list_models()}")

        # Build field info
        fields = {}
        if hasattr(model.document_cls, "model_fields"):
            # Pydantic v2
            for field_name, field_info in model.document_cls.model_fields.items():
                fields[field_name] = {
                    "type": str(field_info.annotation),
                    "required": field_info.is_required(),
                }
        elif hasattr(model.document_cls, "__fields__"):
            # Pydantic v1 / Beanie
            for field_name, field_info in model.document_cls.__fields__.items():
                fields[field_name] = {
                    "type": str(field_info.outer_type_),
                    "required": field_info.required,
                }

        return {
            "name": model.name,
            "description": model.description,
            "tags": model.tags,
            "fields": fields,
            "searchable_fields": model.searchable_fields,
            "sortable_fields": model.sortable_fields,
            "ui_hints": model.ui_hints,
            "relations": model.relations,
        }

    def inspect_operation(self, name: str) -> dict[str, Any]:
        """Get detailed information about an operation.

        Args:
            name: Operation name.

        Returns:
            Dictionary with operation metadata (name, description, inputs, outputs, etc.).

        Raises:
            ValueError: If operation not found.

        Example:
            >>> cli = CLI()
            >>> info = cli.inspect_operation("search_jobs")
            >>> print(info['description'])
        """
        op = self.operation_registry.get(name)
        if not op:
            raise ValueError(
                f"Operation '{name}' not found. Available: {self.list_operations()}"
            )

        # Get input/output schema info
        input_fields = {}
        if hasattr(op.input_schema, "model_fields"):
            # Pydantic v2
            for field_name, field_info in op.input_schema.model_fields.items():
                input_fields[field_name] = str(field_info.annotation)
        elif hasattr(op.input_schema, "__fields__"):
            # Pydantic v1
            for field_name, field_info in op.input_schema.__fields__.items():
                input_fields[field_name] = str(field_info.outer_type_)

        output_fields = {}
        if hasattr(op.output_schema, "model_fields"):
            for field_name, field_info in op.output_schema.model_fields.items():
                output_fields[field_name] = str(field_info.annotation)
        elif hasattr(op.output_schema, "__fields__"):
            for field_name, field_info in op.output_schema.__fields__.items():
                output_fields[field_name] = str(field_info.outer_type_)

        # Check if async
        is_async = inspect.iscoroutinefunction(op.function)

        return {
            "name": op.name,
            "description": op.description,
            "category": op.category,
            "async": is_async,
            "tags": op.tags,
            "permissions": op.permissions,
            "inputs": input_fields,
            "outputs": output_fields,
            "models_in": op.models_in,
            "models_out": op.models_out,
            "stage": op.stage,
        }

    def list_operations_by_category(self) -> dict[str, list[str]]:
        """List operations grouped by category.

        Returns:
            Dictionary mapping category names to operation lists.

        Example:
            >>> cli = CLI()
            >>> cats = cli.list_operations_by_category()
            >>> print(cats['data_processing'])
            ['clean_text', 'validate_data']
        """
        ops = self.operation_registry.list_all()
        categories: dict[str, list[str]] = {}

        for op in ops:
            if op.category not in categories:
                categories[op.category] = []
            categories[op.category].append(op.name)

        # Sort operations within each category
        for cat in categories:
            categories[cat] = sorted(categories[cat])

        return dict(sorted(categories.items()))

    def get_model_registry(self) -> ModelRegistry:
        """Get the model registry instance.

        Returns:
            ModelRegistry with all discovered models.

        Example:
            >>> cli = CLI()
            >>> registry = cli.get_model_registry()
            >>> model = registry.get("Job")
        """
        return self.model_registry

    def get_operation_registry(self) -> OperationRegistry:
        """Get the operation registry instance.

        Returns:
            OperationRegistry with all discovered operations.

        Example:
            >>> cli = CLI()
            >>> registry = cli.get_operation_registry()
            >>> op = registry.get("search_jobs")
        """
        return self.operation_registry

    def draw_graphs(self) -> Path:
        """Generate data relationship graphs.

        Creates visual representations of model relationships.
        Outputs to run_cache/graphs/ (creates if needed).

        Returns:
            Path to generated graphs directory.

        Example:
            >>> cli = CLI()
            >>> graphs_dir = cli.draw_graphs()
            >>> print(f"Graphs at {graphs_dir}")
        """
        from .graph_generator import MermaidGraphGenerator

        self.run_cache_dir.mkdir(parents=True, exist_ok=True)
        graphs_dir = self.run_cache_dir / "graphs"
        graphs_dir.mkdir(parents=True, exist_ok=True)

        generator = MermaidGraphGenerator(self.model_registry, self.operation_registry)
        data_graph = generator.generate_data_graph()

        graph_file = graphs_dir / "data_relationships.mmd"
        graph_file.write_text(data_graph)

        if self.verbose:
            self.console.print(f"[green]✓[/green] Generated data graph: {graph_file}")

        return graphs_dir

    def draw_operationflow(self) -> Path:
        """Generate operation flow graphs.

        Creates visual representations of operation dependencies and hierarchy.
        Outputs to run_cache/graphs/ (creates if needed).

        Returns:
            Path to generated graphs directory.

        Example:
            >>> cli = CLI()
            >>> graphs_dir = cli.draw_operationflow()
        """
        from .graph_generator import MermaidGraphGenerator

        self.run_cache_dir.mkdir(parents=True, exist_ok=True)
        graphs_dir = self.run_cache_dir / "graphs"
        graphs_dir.mkdir(parents=True, exist_ok=True)

        generator = MermaidGraphGenerator(self.model_registry, self.operation_registry)
        flow_graph = generator.generate_operation_flow()

        flow_file = graphs_dir / "operation_flow.mmd"
        flow_file.write_text(flow_graph)

        if self.verbose:
            self.console.print(f"[green]✓[/green] Generated operation flow: {flow_file}")

        return graphs_dir

    def docs(self) -> Path:
        """Generate documentation from decorators.

        Creates markdown documentation for all models and operations.
        Outputs to run_cache/docs/ (creates if needed).

        Returns:
            Path to generated docs directory.

        Example:
            >>> cli = CLI()
            >>> docs_dir = cli.docs()
        """
        self.run_cache_dir.mkdir(parents=True, exist_ok=True)
        docs_dir = self.run_cache_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Generate models documentation
        models_doc = "# Models\n\n"
        for model in self.model_registry.list_all():
            models_doc += f"## {model.name}\n\n"
            if model.description:
                models_doc += f"{model.description}\n\n"
            if model.tags:
                models_doc += f"**Tags:** {', '.join(model.tags)}\n\n"

        models_file = docs_dir / "models.md"
        models_file.write_text(models_doc)

        # Generate operations documentation
        ops_doc = "# Operations\n\n"
        for op in self.operation_registry.list_all():
            ops_doc += f"## {op.name}\n\n"
            ops_doc += f"**Category:** {op.category}\n\n"
            ops_doc += f"{op.description}\n\n"
            if op.tags:
                ops_doc += f"**Tags:** {', '.join(op.tags)}\n\n"

        ops_file = docs_dir / "operations.md"
        ops_file.write_text(ops_doc)

        if self.verbose:
            self.console.print(
                f"[green]✓[/green] Generated documentation in {docs_dir}"
            )

        return docs_dir

    def check_version(self) -> dict[str, str]:
        """Check version information and compatibility.

        Returns:
            Dictionary with version information.

        Example:
            >>> cli = CLI()
            >>> versions = cli.check_version()
            >>> print(f"Framework: {versions['framework']}")
        """
        from . import __version__

        return {
            "framework": __version__,
            "python": __import__("sys").version.split()[0],
        }

    def summary(self) -> str:
        """Get a text summary of the current state.

        Returns:
            Formatted summary string.

        Example:
            >>> cli = CLI()
            >>> print(cli.summary())
        """
        models = self.list_models()
        ops = self.list_operations()
        cats = self.list_operations_by_category()

        summary = f"""
Pulpo Framework Summary
======================

Models: {len(models)}
  {', '.join(models) if models else '(none)'}

Operations: {len(ops)}
  By category:
"""
        for cat, cat_ops in cats.items():
            summary += f"    {cat}: {len(cat_ops)} operations\n"

        summary += f"\nrun_cache: {self.run_cache_dir.exists()}"

        return summary

    # =========================================================================
    # Category 2: Full-Stack Methods (Auto-compile if needed)
    # =========================================================================

    def _ensure_compiled(self) -> None:
        """Ensure run_cache exists with compiled artifacts.

        Calls compile() if run_cache doesn't exist.
        """
        if not self.run_cache_dir.exists() and self.auto_compile:
            if self.verbose:
                self.console.print(
                    f"[yellow]run_cache not found, compiling...[/yellow]"
                )
            self.compile()

    def compile(self) -> Path:
        """Compile all artifacts to run_cache.

        Generates:
        - generated_api.py (FastAPI routes)
        - generated_ui_config.ts (TypeScript config)
        - generated_database.py (Database models)
        - orchestration/ (Prefect flows)
        - graphs/ (Mermaid diagrams)
        - docs/ (Markdown docs)

        Returns:
            Path to run_cache directory.

        Example:
            >>> cli = CLI()
            >>> cache_dir = cli.compile()
            >>> print(f"Generated at {cache_dir}")
        """
        self.run_cache_dir.mkdir(parents=True, exist_ok=True)

        if self.verbose:
            self.console.print(f"[cyan]Compiling to {self.run_cache_dir}...[/cyan]")

        # Generate all artifacts
        try:
            from .codegen import compile_all

            compile_all()
            if self.verbose:
                self.console.print("[green]✓[/green] Compilation complete")

            # Generate Prefect flows
            self._compile_prefect_flows()

        except Exception as e:
            self.console.print(f"[red]✗[/red] Compilation failed: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            raise

        return self.run_cache_dir

    def _compile_prefect_flows(self) -> None:
        """Generate Prefect flows from operations.

        Internal helper called by compile() to generate flow definitions.
        Creates orchestration/ directory with flow definitions.
        """
        try:
            from .orchestration.dataflow import OperationMetadata as DataFlowOpMeta
            from .orchestration.compiler import OrchestrationCompiler
            from .orchestration.prefect_codegen import PrefectCodeGenerator

            # Get all operations and convert to data flow metadata
            operations = self.operation_registry.list_all()

            if not operations:
                if self.verbose:
                    self.console.print(
                        "[yellow]No operations found, skipping Prefect flow generation[/yellow]"
                    )
                return

            # Convert to data flow metadata
            dataflow_ops = [DataFlowOpMeta(op) for op in operations]

            # Compile to flows
            compiler = OrchestrationCompiler()
            orchestration = compiler.compile(dataflow_ops)

            if not orchestration.flows:
                if self.verbose:
                    self.console.print(
                        "[yellow]No flows generated from operations[/yellow]"
                    )
                return

            # Generate code
            generator = PrefectCodeGenerator()
            flow_codes = generator.generate_all_flows(orchestration)

            # Create orchestration directory
            orch_dir = self.run_cache_dir / "orchestration"
            orch_dir.mkdir(parents=True, exist_ok=True)

            # Ensure orchestration is a package
            (orch_dir / "__init__.py").touch()

            # Write flow files
            for flow_name, code in flow_codes.items():
                flow_file = orch_dir / f"{flow_name}.py"
                flow_file.write_text(code)

                if self.verbose:
                    self.console.print(f"[green]✓[/green] Generated {flow_name}")

            # Generate registry file
            registry_code = generator.generate_flow_registry(orchestration)
            registry_file = orch_dir / "registry.py"
            registry_file.write_text(registry_code)

            if self.verbose:
                self.console.print(
                    f"[green]✓[/green] Generated {len(orchestration.flows)} Prefect flows"
                )

        except ImportError as e:
            # Prefect or orchestration modules not available
            if self.verbose:
                self.console.print(
                    f"[yellow]Skipping Prefect flow generation: {e}[/yellow]"
                )
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to generate Prefect flows: {e}[/yellow]")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def build(self) -> None:
        """Build Docker images for the stack.

        Requires: run_cache/ must exist (calls compile() first if needed)

        Example:
            >>> cli = CLI()
            >>> cli.build()  # Starts building Docker images
        """
        self._ensure_compiled()

        if self.verbose:
            self.console.print("[cyan]Building Docker images...[/cyan]")

        # TODO: Implement Docker build logic
        self.console.print("[yellow]Docker build not yet implemented[/yellow]")

    def api(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Serve FastAPI application.

        Requires: run_cache/ (auto-compiles if needed)

        Args:
            host: Host to bind to (default: 0.0.0.0)
            port: Port to bind to (default: 8000)

        Example:
            >>> cli = CLI()
            >>> cli.api()  # Starts API server on http://localhost:8000
        """
        self._ensure_compiled()

        if self.verbose:
            self.console.print(
                f"[cyan]Starting API on {host}:{port}...[/cyan]"
            )

        try:
            import uvicorn
            # Import generated API from run_cache
            run_cache_path = self.run_cache_dir / "generated_api.py"
            if not run_cache_path.exists():
                raise FileNotFoundError(
                    f"Generated API not found at {run_cache_path}. Run compile first."
                )

            # Add run_cache to path and import
            import sys
            sys.path.insert(0, str(self.run_cache_dir))
            from generated_api import app

            uvicorn.run(app, host=host, port=port)
        except ImportError:
            self.console.print(
                "[red]Error: uvicorn not installed. Install with: pip install uvicorn[/red]"
            )
            raise
        except Exception as e:
            self.console.print(f"[red]Error starting API: {e}[/red]")
            raise

    def init(self) -> None:
        """Initialize database and other services.

        Requires: run_cache/ (auto-compiles if needed)

        Example:
            >>> cli = CLI()
            >>> cli.init()  # Initializes database
        """
        self._ensure_compiled()

        if self.verbose:
            self.console.print("[cyan]Initializing database...[/cyan]")

        # Initialize database via Makefile target
        self.db("init")

    def prefect(self, command: str = "start") -> None:
        """Manage Prefect service.

        Requires: run_cache/orchestration/ (auto-compiles if needed)

        Args:
            command: "start", "stop", "restart", "logs", or "status"

        Example:
            >>> cli = CLI()
            >>> cli.prefect("start")  # Start Prefect server
            >>> cli.prefect("logs")   # Show Prefect logs
            >>> cli.prefect("stop")   # Stop Prefect
        """
        self._ensure_compiled()

        if self.verbose:
            self.console.print(f"[cyan]Prefect: {command}...[/cyan]")

        try:
            import subprocess

            # Try to use Makefile target first
            result = subprocess.run(
                ["make", f"prefect-{command}"],
                cwd=".",
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                if result.stdout:
                    self.console.print(result.stdout)
                if self.verbose:
                    self.console.print(f"[green]✓[/green] Prefect {command} complete")
            else:
                # Makefile command might not exist, show message
                self.console.print(
                    f"[yellow]Prefect {command} not available via Makefile[/yellow]"
                )
                if result.stderr:
                    self.console.print(result.stderr)

        except FileNotFoundError:
            self.console.print("[yellow]Makefile not found[/yellow]")
        except subprocess.TimeoutExpired:
            self.console.print("[red]Prefect command timed out[/red]")
        except Exception as e:
            self.console.print(f"[red]Error managing Prefect: {e}[/red]")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def db(self, command: str = "start") -> None:
        """Manage database service.

        Args:
            command: "start", "stop", "status", "init", "backup", "restore"

        Example:
            >>> cli = CLI()
            >>> cli.db("start")    # Start database
            >>> cli.db("init")     # Initialize database
            >>> cli.db("status")   # Check database status
        """
        if self.verbose:
            self.console.print(f"[cyan]Database: {command}...[/cyan]")

        try:
            import subprocess

            # Try Makefile target first
            result = subprocess.run(
                ["make", f"db-{command}"],
                cwd=".",
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                if result.stdout:
                    self.console.print(result.stdout)
                if self.verbose:
                    self.console.print(f"[green]✓[/green] Database {command} complete")
            else:
                self.console.print(
                    f"[yellow]Database {command} not available via Makefile[/yellow]"
                )
                if result.stderr:
                    self.console.print(result.stderr)

        except Exception as e:
            self.console.print(f"[red]Error managing database: {e}[/red]")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def ui(self, command: str = "start") -> None:
        """Manage UI service.

        Args:
            command: "start", "stop", "build", "dev", "logs"

        Example:
            >>> cli = CLI()
            >>> cli.ui("dev")      # Start UI development server
            >>> cli.ui("build")    # Build UI for production
            >>> cli.ui("logs")     # Show UI logs
        """
        if self.verbose:
            self.console.print(f"[cyan]UI: {command}...[/cyan]")

        try:
            import subprocess

            # Try Makefile target first
            result = subprocess.run(
                ["make", f"ui-{command}"],
                cwd=".",
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode == 0:
                if result.stdout:
                    self.console.print(result.stdout)
                if self.verbose:
                    self.console.print(f"[green]✓[/green] UI {command} complete")
            else:
                self.console.print(
                    f"[yellow]UI {command} not available via Makefile[/yellow]"
                )
                if result.stderr:
                    self.console.print(result.stderr)

        except Exception as e:
            self.console.print(f"[red]Error managing UI: {e}[/red]")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def interact(self) -> None:
        """Start interactive Python shell with CLI context.

        Requires: run_cache/ (auto-compiles if needed)

        Example:
            >>> cli = CLI()
            >>> cli.interact()  # Starts interactive shell
        """
        self._ensure_compiled()

        if self.verbose:
            self.console.print("[cyan]Starting interactive shell...[/cyan]")

        # TODO: Implement interactive shell
        self.console.print("[yellow]Interactive shell not yet implemented[/yellow]")

    def up(self) -> None:
        """Start all services (database, API, Prefect, UI).

        Starts services in dependency order using Makefile targets.

        Example:
            >>> cli = CLI()
            >>> cli.up()  # Start all services
        """
        if self.verbose:
            self.console.print("[cyan]Starting all services...[/cyan]")

        try:
            import subprocess

            # Try to use Makefile "up" target
            result = subprocess.run(
                ["make", "up"],
                cwd=".",
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                if result.stdout:
                    self.console.print(result.stdout)
                if self.verbose:
                    self.console.print("[green]✓[/green] All services started")
            else:
                self.console.print("[yellow]Failed to start services via Makefile[/yellow]")
                if result.stderr:
                    self.console.print(result.stderr)

        except FileNotFoundError:
            self.console.print("[yellow]Makefile not found[/yellow]")
        except subprocess.TimeoutExpired:
            self.console.print("[red]Service startup timed out[/red]")
        except Exception as e:
            self.console.print(f"[red]Error starting services: {e}[/red]")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def down(self) -> None:
        """Stop all services (database, API, Prefect, UI).

        Stops services in reverse dependency order using Makefile targets.

        Example:
            >>> cli = CLI()
            >>> cli.down()  # Stop all services
        """
        if self.verbose:
            self.console.print("[cyan]Stopping all services...[/cyan]")

        try:
            import subprocess

            # Try to use Makefile "down" target
            result = subprocess.run(
                ["make", "down"],
                cwd=".",
                capture_output=True,
                text=True,
                timeout=600,
            )

            if result.returncode == 0:
                if result.stdout:
                    self.console.print(result.stdout)
                if self.verbose:
                    self.console.print("[green]✓[/green] All services stopped")
            else:
                self.console.print("[yellow]Failed to stop services via Makefile[/yellow]")
                if result.stderr:
                    self.console.print(result.stderr)

        except FileNotFoundError:
            self.console.print("[yellow]Makefile not found[/yellow]")
        except subprocess.TimeoutExpired:
            self.console.print("[red]Service shutdown timed out[/red]")
        except Exception as e:
            self.console.print(f"[red]Error stopping services: {e}[/red]")
            if self.verbose:
                import traceback

                traceback.print_exc()

    def clean(self) -> None:
        """Remove generated artifacts (run_cache).

        Safe to call - compile() will regenerate if needed.

        Example:
            >>> cli = CLI()
            >>> cli.clean()  # Removes run_cache/
        """
        if self.run_cache_dir.exists():
            shutil.rmtree(self.run_cache_dir)
            if self.verbose:
                self.console.print(
                    f"[green]✓[/green] Removed {self.run_cache_dir}"
                )
        else:
            if self.verbose:
                self.console.print(f"[yellow]Nothing to clean - {self.run_cache_dir} not found[/yellow]")
