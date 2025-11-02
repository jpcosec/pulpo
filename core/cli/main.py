"""Main CLI entrypoint for Pulpo framework.

Provides both programmatic (CLI class) and Typer-based CLI interfaces.
"""

import sys

import typer
from rich.console import Console

from ..cli_interface import CLI
from .commands import lint, ops

app = typer.Typer(
    name="pulpo",
    help="Pulpo Core Framework - Auto-generate APIs, UIs, and Orchestration from decorators",
    no_args_is_help=True,
    add_completion=True,
)

console = Console()

# Global CLI instance for Typer commands
_cli_instance: CLI | None = None


def get_cli() -> CLI:
    """Get or create the global CLI instance."""
    global _cli_instance
    if _cli_instance is None:
        _cli_instance = CLI(verbose=False)
    return _cli_instance


# Register command groups
app.add_typer(ops.app, name="ops", help="Execute registered operations")
app.add_typer(lint.lint_app, name="lint", help="Lint datamodels and operations")


@app.command()
def version():
    """Show version information."""
    cli = get_cli()
    versions = cli.check_version()
    console.print(f"[bold blue]Pulpo Framework[/bold blue] version {versions['framework']}")
    console.print(f"[dim]Python {versions['python']}[/dim]")


@app.command()
def status():
    """Show current project status."""
    cli = get_cli()
    summary = cli.summary()
    console.print(summary)


@app.command()
def models():
    """List registered models."""
    cli = get_cli()
    models_list = cli.list_models()

    if not models_list:
        console.print("[yellow]No models registered[/yellow]")
        return

    table = typer.echo
    console.print("[bold]Registered Models:[/bold]")
    for model_name in models_list:
        info = cli.inspect_model(model_name)
        console.print(f"  [cyan]{model_name}[/cyan]")
        if info.get("description"):
            console.print(f"    {info['description']}")


@app.command()
def graph(
    from_scan: bool = typer.Option(
        False,
        "--from-scan",
        help="Generate graphs from file scan (codebase-wide) instead of registries"
    ),
):
    """Generate relationship graphs.

    Default: Uses current registries (from main.py imports).
    With --from-scan: Scans entire codebase for models/operations.
    """
    cli = get_cli()
    console.print("[cyan]Generating graphs...[/cyan]")
    try:
        if from_scan:
            console.print("[dim]Scanning codebase for models/operations...[/dim]")
        graphs_dir = cli.draw_graphs()
        console.print(f"[green]✓[/green] Generated graphs in {graphs_dir}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def flows(
    from_scan: bool = typer.Option(
        False,
        "--from-scan",
        help="Generate flows from file scan (codebase-wide) instead of registries"
    ),
):
    """Generate operation flow diagrams.

    Default: Uses current registries (from main.py imports).
    With --from-scan: Scans entire codebase for operations.
    """
    cli = get_cli()
    console.print("[cyan]Generating operation flows...[/cyan]")
    try:
        if from_scan:
            console.print("[dim]Scanning codebase for operations...[/dim]")
        flows_dir = cli.draw_operationflow()
        console.print(f"[green]✓[/green] Generated flows in {flows_dir}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def docs():
    """Generate documentation."""
    cli = get_cli()
    console.print("[cyan]Generating documentation...[/cyan]")
    docs_dir = cli.docs()
    console.print(f"[green]✓[/green] Generated docs in {docs_dir}")


@app.command()
def compile():
    """Compile all artifacts to run_cache."""
    cli = get_cli()
    console.print("[cyan]Compiling...[/cyan]")
    cache_dir = cli.compile()
    console.print(f"[green]✓[/green] Compiled to {cache_dir}")


@app.command()
def api(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """Start FastAPI server."""
    cli = get_cli()
    console.print(f"[cyan]Starting API on {host}:{port}...[/cyan]")
    try:
        cli.api(host=host, port=port)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def init(
    db_host: str = typer.Option("localhost", help="Database host"),
    db_port: int = typer.Option(27017, help="Database port"),
):
    """Initialize database and services."""
    cli = get_cli()
    console.print("[cyan]Initializing services...[/cyan]")
    try:
        cli.init()
        console.print("[green]✓[/green] Services initialized")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def up():
    """Start all services (database, API, Prefect, UI)."""
    cli = get_cli()
    console.print("[cyan]Starting all services...[/cyan]")
    try:
        cli.up()
        console.print("[green]✓[/green] All services started")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def down():
    """Stop all services."""
    cli = get_cli()
    console.print("[cyan]Stopping all services...[/cyan]")
    try:
        cli.down()
        console.print("[green]✓[/green] All services stopped")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def prefect(
    command: str = typer.Argument("start", help="prefect command: start, stop, restart, logs, status"),
):
    """Manage Prefect orchestration server."""
    cli = get_cli()
    try:
        cli.prefect(command)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def db(
    command: str = typer.Argument("status", help="database command: start, stop, init, status, logs"),
):
    """Manage database service."""
    cli = get_cli()
    try:
        cli.db(command)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def clean():
    """Remove generated artifacts (run_cache)."""
    cli = get_cli()
    console.print("[cyan]Removing generated artifacts...[/cyan]")
    try:
        cli.clean()
        console.print("[green]✓[/green] Cleaned run_cache/")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ui(
    port: int = typer.Option(3000, help="Port to run UI on"),
):
    """Launch the web UI."""
    import os
    from pathlib import Path

    frontend_dir = Path(__file__).parent.parent.parent / "frontend_template"

    if not frontend_dir.exists():
        console.print("[red]Error: Frontend directory not found[/red]")
        console.print(f"Expected at: {frontend_dir}")
        raise typer.Exit(1)

    console.print(f"[cyan]Starting web UI on port {port}...[/cyan]")

    # Simple HTTP server
    build_dir = frontend_dir / "build"
    if build_dir.exists():
        os.chdir(build_dir)
        os.system(f"python -m http.server {port}")
    else:
        console.print("[yellow]Frontend not built. Serve frontend_template directory:[/yellow]")
        os.chdir(frontend_dir)
        os.system(f"python -m http.server {port}")


@app.command()
def help(
    topic: str = typer.Argument(None, help="Topic: 'datamodel', 'operation', 'cli', 'architecture', etc."),
):
    """Show documentation about Pulpo framework.

    Usage:
        pulpo help datamodel          # Show @datamodel decorator docs
        pulpo help operation          # Show @operation decorator docs
        pulpo help cli                # Show CLI architecture docs
        pulpo help architecture       # Show framework architecture
        pulpo help                    # List available topics
    """
    from ..doc_helper import DocHelper, format_doc_output

    doc_helper = DocHelper()

    if not topic:
        # List available topics
        console.print("[bold]Available Documentation Topics:[/bold]\n")
        console.print("[cyan]Framework Documentation:[/cyan]")
        for t in doc_helper.list_framework_docs():
            console.print(f"  • pulpo help {t}")
        console.print()
        console.print("[dim]Tip: Run from a project directory to see model and operation documentation[/dim]")
        return

    # Get and display documentation
    doc_content = doc_helper.get_framework_doc(topic)
    if doc_content:
        console.print(format_doc_output(doc_content))
    else:
        console.print(f"[red]Error:[/red] Topic '{topic}' not found")
        console.print("\nAvailable topics:")
        for t in doc_helper.list_framework_docs():
            console.print(f"  • {t}")
        raise typer.Exit(1)


def main():
    """Main CLI entrypoint."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
