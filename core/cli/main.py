"""Main CLI entrypoint for Jobhunter.

Auto-generates commands from OperationRegistry.
"""

import sys

import typer
from rich.console import Console

from core.cli.commands import lint, ops

app = typer.Typer(
    name="jobhunter",
    help="JobHunter AI - Automated Job Application Platform",
    no_args_is_help=True,
    add_completion=True,
)

console = Console()


# Register command groups
app.add_typer(ops.app, name="ops", help="Execute registered operations")
app.add_typer(lint.lint_app, name="lint", help="Lint datamodels and operations")


@app.command()
def version():
    """Show version information."""
    from core.cli import __version__

    console.print(f"[bold blue]JobHunter CLI[/bold blue] version {__version__}")


@app.command()
def init(
    db_host: str = typer.Option("localhost", help="Database host"),
    db_port: int = typer.Option(27017, help="Database port"),
):
    """Initialize Jobhunter configuration."""
    console.print("[yellow]Initializing Jobhunter...[/yellow]")

    # Create .env file if it doesn't exist
    from pathlib import Path

    env_path = Path(".env")
    if env_path.exists():
        console.print("[red]Error: .env file already exists[/red]")
        raise typer.Exit(1)

    env_content = f"""# JobHunter Configuration

# Database (MongoDB only)
MONGODB_URI=mongodb://{db_host}:{db_port}
MONGODB_DATABASE=jobhunter

# OpenAI (optional)
OPENAI_API_KEY=

# Anthropic (optional)
ANTHROPIC_API_KEY=

# Logging
LOG_LEVEL=INFO
"""

    env_path.write_text(env_content)
    console.print("[green]✓[/green] Created .env file")
    console.print("[green]✓[/green] Jobhunter initialized successfully!")
    console.print("\n[yellow]Next steps:[/yellow]")
    console.print("1. Edit .env to add your API keys")
    console.print("2. Run 'jobhunter ops list' to see available operations")


@app.command()
def ui(
    port: int = typer.Option(3000, help="Port to run UI on"),
    dev: bool = typer.Option(False, help="Run in development mode"),
):
    """Launch the web UI (frontend)."""
    import os
    from pathlib import Path

    frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "jobhunter-ui"

    if not frontend_dir.exists():
        console.print("[red]Error: Frontend directory not found[/red]")
        console.print(f"Expected at: {frontend_dir}")
        raise typer.Exit(1)

    console.print(f"[yellow]Starting web UI on port {port}...[/yellow]")

    if dev:
        # Development mode: run npm start
        os.chdir(frontend_dir)
        os.system("npm start")
    else:
        # Production mode: serve build
        build_dir = frontend_dir / "build"
        if not build_dir.exists():
            console.print("[red]Error: Build directory not found. Run 'npm run build' first.[/red]")
            raise typer.Exit(1)

        # Simple HTTP server
        os.chdir(build_dir)
        os.system(f"python -m http.server {port}")


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
