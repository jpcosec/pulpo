#!/usr/bin/env python3
"""Generate a standalone CLI executable from registered operations.

Generates: run_cache/cli/<project_name> (executable)

This creates a fast, self-contained CLI script with:
- No runtime dependency on the framework
- Immediate availability after compilation
- Auto-generated commands from @operation decorators
"""

from __future__ import annotations

from textwrap import dedent

from ...analysis.registries import OperationRegistry


def generate_cli_script() -> str:
    """Generate a complete CLI script from registered operations."""

    operations = OperationRegistry.list_all()

    # Build operations list
    ops_list = []
    for op in operations:
        ops_list.append(dedent(f'''
        {{
            "name": "{op.name}",
            "description": "{op.description}",
            "category": "{op.category}",
            "input_schema": "{op.input_schema.__name__}",
            "output_schema": "{op.output_schema.__name__}",
        }}
        '''))

    operations_json = "[" + ",".join(ops_list) + "]"

    # Generate the CLI script
    cli_script = dedent(f'''#!/usr/bin/env python3
    """Generated CLI - Auto-generated at compile time.

    ⚠️  DO NOT EDIT MANUALLY - Changes will be overwritten!
        Regenerate with: make compile

    This CLI is generated from @operation decorated functions.
    It provides quick access to all registered operations.
    """

    import sys
    import json
    from pathlib import Path

    # Operations registered at compile time
    OPERATIONS = {operations_json}

    def list_operations():
        """List all registered operations."""
        print("\\n📋 Registered Operations:\\n")
        for op in OPERATIONS:
            print(f"  {{op['name']:<30}} - {{op['description']}}")
        print(f"\\n📊 Total: {{len(OPERATIONS)}} operations")
        print("\\nUsage: ./jobhunter <operation_name> --help\\n")

    def show_operation(name: str):
        """Show details for a specific operation."""
        for op in OPERATIONS:
            if op['name'] == name:
                print(f"\\n📝 Operation: {{op['name']}}")
                print(f"   Description: {{op['description']}}")
                print(f"   Category: {{op['category']}}")
                print(f"   Input: {{op['input_schema']}}")
                print(f"   Output: {{op['output_schema']}}")
                print()
                return
        print(f"❌ Operation '{{name}}' not found")

    def main():
        """Main CLI entry point."""
        if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h', 'help'):
            print("\\n🚀 Generated CLI\\n")
            list_operations()
            return

        command = sys.argv[1]

        if command == "list":
            list_operations()
        elif command == "inspect" and len(sys.argv) > 2:
            show_operation(sys.argv[2])
        else:
            print(f"❌ Unknown command: {{command}}")
            print("\\nAvailable commands: list, inspect <name>\\n")

    if __name__ == "__main__":
        main()
    ''')

    return cli_script


def write_cli():
    """Write generated CLI to .run_cache/cli/jobhunter."""
    output_dir = Path(".run_cache/cli")
    output_dir.mkdir(parents=True, exist_ok=True)

    cli_file = output_dir / "jobhunter"
    cli_file.write_text(generate_cli_script())

    # Make executable
    cli_file.chmod(0o755)

    print(f"✅ Generated CLI: {cli_file}")
    print("   Usage: .run_cache/cli/jobhunter --help")
    print("   Or: ./.run_cache/cli/jobhunter list")


if __name__ == "__main__":
    write_cli()
