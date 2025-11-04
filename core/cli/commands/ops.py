"""Auto-generated CLI commands from OperationRegistry.

This module dynamically generates Typer commands for all registered operations.
"""

import asyncio
import inspect
import json

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ...registries import OperationRegistry

# Note: core.examples was removed - only user project operations are available
# Operations are discovered and imported from user projects via the generated API

app = typer.Typer(
    name="ops",
    help="Execute registered operations",
    no_args_is_help=True,
)

console = Console()


@app.command(name="list")
def list_operations(
    category: str | None = typer.Option(None, help="Filter by category"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """List all registered operations."""
    operations = OperationRegistry.list_all()

    if category:
        operations = [op for op in operations if op.category == category]

    if not operations:
        console.print("[yellow]No operations found[/yellow]")
        return

    if json_output:
        data = [
            {
                "name": op.name,
                "description": op.description,
                "category": op.category,
                "tags": op.tags,
            }
            for op in operations
        ]
        console.print(JSON(json.dumps(data, indent=2)))
        return

    # Group by category
    by_category: dict[str, list] = {}
    for op in operations:
        cat = op.category or "other"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(op)

    for cat, ops in sorted(by_category.items()):
        table = Table(title=f"[bold cyan]{cat.upper()}[/bold cyan]", show_header=True)
        table.add_column("Operation", style="bold blue")
        table.add_column("Description", style="white")
        table.add_column("Tags", style="dim")

        for op in sorted(ops, key=lambda x: x.name):
            tags = ", ".join(op.tags) if op.tags else ""
            table.add_row(op.name, op.description, tags)

        console.print(table)
        console.print()

    console.print(f"[green]Total operations: {len(operations)}[/green]")


@app.command(name="inspect")
def inspect_operation(
    operation_name: str = typer.Argument(..., help="Operation name to inspect"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Inspect details of a specific operation."""
    op = OperationRegistry.get(operation_name)

    if not op:
        console.print(f"[red]Error: Operation '{operation_name}' not found[/red]")
        raise typer.Exit(1)

    if json_output:
        data = {
            "name": op.name,
            "description": op.description,
            "category": op.category,
            "tags": op.tags,
            "permissions": op.permissions,
            "async_enabled": op.async_enabled,
            "input_schema": _schema_to_dict(op.input_schema),
            "output_schema": _schema_to_dict(op.output_schema),
        }
        console.print(JSON(json.dumps(data, indent=2)))
        return

    # Rich output
    console.print(Panel(f"[bold blue]{op.name}[/bold blue]", title="Operation"))
    console.print(f"[bold]Description:[/bold] {op.description}")
    console.print(f"[bold]Category:[/bold] {op.category}")

    if op.tags:
        console.print(f"[bold]Tags:[/bold] {', '.join(op.tags)}")

    if op.permissions:
        console.print(f"[bold]Permissions:[/bold] {', '.join(op.permissions)}")

    console.print(f"[bold]Async:[/bold] {op.async_enabled}")

    # Input schema
    console.print("\n[bold cyan]Input Schema:[/bold cyan]")
    _print_schema(op.input_schema)

    # Output schema
    console.print("\n[bold cyan]Output Schema:[/bold cyan]")
    _print_schema(op.output_schema)


@app.command(name="run")
def run_operation(
    operation_name: str = typer.Argument(..., help="Operation name to execute"),
    params_json: str | None = typer.Option(None, "--params", help="JSON params"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Execute a registered operation.

    Examples:
        pulpo ops run scrape_jobs --params '{"source": "stepstone", "keywords": "python developer", "limit": 10}'
        pulpo ops run list_jobs --params '{"limit": 5}' --json
        pulpo ops run get_active_profile --json
    """
    op = OperationRegistry.get(operation_name)

    if not op:
        console.print(f"[red]Error: Operation '{operation_name}' not found[/red]")
        console.print("\n[yellow]Available operations:[/yellow]")
        for available_op in sorted(OperationRegistry.list_all(), key=lambda x: x.name):
            console.print(f"  • {available_op.name}")
        raise typer.Exit(1)

    # Parse input parameters
    try:
        if params_json:
            params_dict = json.loads(params_json)
        else:
            params_dict = {}

        # Validate against input schema
        input_data = op.input_schema(**params_dict)

    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in --params: {e}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error: Invalid input parameters: {e}[/red]")
        console.print("\n[yellow]Expected schema:[/yellow]")
        _print_schema(op.input_schema)
        raise typer.Exit(1) from e

    # Execute operation
    try:
        if verbose:
            console.print(f"[dim]Executing operation: {operation_name}[/dim]")
            console.print(f"[dim]Parameters: {input_data.model_dump()}[/dim]")

        # Initialize database if needed
        _ensure_db_initialized()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Running {operation_name}...", total=None)

            # Run the operation
            if inspect.iscoroutinefunction(op.function):
                result = asyncio.run(op.function(input_data))
            else:
                result = op.function(input_data)

            progress.update(task, completed=True)

        # Validate output
        if not isinstance(result, op.output_schema):
            result = op.output_schema(**result) if isinstance(result, dict) else result

        # Display result
        if json_output:
            console.print(JSON(result.model_dump_json(indent=2)))
        else:
            _print_result(operation_name, result, verbose=verbose)

    except Exception as e:
        console.print(f"[red]Error executing operation: {e}[/red]")
        if verbose:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1) from e


def _ensure_db_initialized():
    """Ensure database is initialized before running operations."""
    from pathlib import Path

    # Check if .env exists
    env_path = Path(".env")
    if not env_path.exists():
        console.print("[yellow]Warning: .env file not found[/yellow]")
        console.print("[yellow]Run 'pulpo init' to create configuration[/yellow]")
        # Continue anyway - operations might not need DB

    # Try to initialize database connection
    try:

        pass

        # This is a lazy check - actual init happens in operations
        # Just make sure the models are imported
    except Exception as e:
        if "DB" in str(e).upper():
            console.print(f"[yellow]Warning: Could not initialize database: {e}[/yellow]")


def _schema_to_dict(schema: type[BaseModel]) -> dict:
    """Convert Pydantic schema to dict representation."""
    return schema.model_json_schema()


def _print_schema(schema: type[BaseModel]):
    """Pretty print a Pydantic schema."""
    table = Table(show_header=True, show_lines=True)
    table.add_column("Field", style="bold")
    table.add_column("Type", style="cyan")
    table.add_column("Required", style="yellow")
    table.add_column("Default", style="green")
    table.add_column("Description", style="white")

    for field_name, field_info in schema.model_fields.items():
        field_type = str(field_info.annotation).replace("typing.", "")
        required = "Yes" if field_info.is_required() else "No"
        default = str(field_info.default) if field_info.default is not None else "-"
        description = field_info.description or "-"

        table.add_row(field_name, field_type, required, default, description)

    console.print(table)


def _print_result(operation_name: str, result: BaseModel, verbose: bool = False):
    """Pretty print operation result."""
    result_dict = result.model_dump()

    # Check if operation succeeded
    success = result_dict.get("success", True)
    error = result_dict.get("error") or result_dict.get("error_message")

    if not success or error:
        console.print("[red]✗[/red] Operation failed")
        if error:
            console.print(f"[red]Error: {error}[/red]")
        return

    # Success!
    console.print("[green]✓[/green] Operation completed successfully")

    # Display key results
    console.print()

    # Special handling for common result patterns
    if "count" in result_dict:
        console.print(f"[bold]Count:[/bold] {result_dict['count']}")

    if "total" in result_dict:
        console.print(f"[bold]Total:[/bold] {result_dict['total']}")

    if "execution_time" in result_dict:
        console.print(f"[bold]Execution Time:[/bold] {result_dict['execution_time']:.2f}s")

    if "message" in result_dict and result_dict["message"]:
        console.print(f"[bold]Message:[/bold] {result_dict['message']}")

    # Display list results
    list_keys = [k for k in result_dict.keys() if isinstance(result_dict[k], list)]
    for key in list_keys:
        items = result_dict[key]
        if items and len(items) > 0:
            console.print(f"\n[bold cyan]{key.replace('_', ' ').title()}:[/bold cyan]")

            # Check if items are dicts (can make table)
            if isinstance(items[0], dict):
                _print_table_from_dicts(items, max_rows=10 if not verbose else None)
            else:
                for item in items[: 10 if not verbose else None]:
                    console.print(f"  • {item}")

                if not verbose and len(items) > 10:
                    console.print(f"  [dim]... and {len(items) - 10} more[/dim]")

    # Display other fields
    skip_keys = {
        "success",
        "error",
        "error_message",
        "message",
        "count",
        "total",
        "execution_time",
    } | set(list_keys)

    other_fields = {k: v for k, v in result_dict.items() if k not in skip_keys and v is not None}

    if other_fields and verbose:
        console.print("\n[bold cyan]Additional Fields:[/bold cyan]")
        for key, value in other_fields.items():
            console.print(f"[bold]{key}:[/bold] {value}")


def _print_table_from_dicts(items: list[dict], max_rows: int | None = None):
    """Print a table from a list of dictionaries."""
    if not items:
        return

    # Determine columns from first item
    columns = list(items[0].keys())

    # Limit columns to reasonable number
    if len(columns) > 6:
        columns = columns[:6]

    table = Table(show_header=True)
    for col in columns:
        table.add_column(col.replace("_", " ").title(), overflow="fold")

    # Add rows
    display_items = items[:max_rows] if max_rows else items
    for item in display_items:
        row = [str(item.get(col, ""))[:50] for col in columns]  # Limit cell width
        table.add_row(*row)

    console.print(table)

    if max_rows and len(items) > max_rows:
        console.print(f"[dim]... and {len(items) - max_rows} more rows[/dim]")
