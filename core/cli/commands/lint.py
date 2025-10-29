"""Linting command for datamodels and operations."""

import typer

from ...linter import DataModelLinter

lint_app = typer.Typer(help="Lint datamodels and operations")


@lint_app.command()
def check(
    fix: bool = typer.Option(False, "--fix", "-f", help="Auto-fix common issues (future feature)"),
    level: str = typer.Option(
        "warning",
        "--level",
        "-l",
        help="Minimum issue level to report (error, warning, info)",
    ),
    format: str = typer.Option("text", "--format", help="Output format (text, json, summary)"),
) -> None:
    """Check datamodels and operations for errors and anti-patterns.

    Detects:
    - Type/naming mismatches (list[str] when should be list[Model])
    - Missing documentation
    - Spelling/grammar errors
    - Orphaned models
    - Unknown model references
    """
    typer.echo("🔍 Linting datamodels and operations...\n")

    linter = DataModelLinter()
    errors = linter.lint()

    # Filter by level
    level_priority = {"error": 0, "warning": 1, "info": 2}
    threshold = level_priority.get(level, 1)
    filtered_errors = [e for e in errors if level_priority.get(e.level, 2) <= threshold]

    linter.errors = filtered_errors
    report = linter.report(format=format)
    typer.echo(report)

    # Exit with error code if there are errors
    error_count = sum(1 for e in filtered_errors if e.level == "error")
    if error_count > 0:
        raise typer.Exit(code=1)
