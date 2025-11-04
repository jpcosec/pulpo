"""Autodiscover datamodels and operations without importing them.

Uses AST parsing to find @datamodel and @operation decorators.
No imports are performed - this is pure static analysis.
"""

import ast
import json
import sys
from pathlib import Path
from typing import Any


class DecoratorFinder(ast.NodeVisitor):
    """Find @datamodel and @operation decorated classes/functions."""

    def __init__(self):
        self.models = []
        self.operations = []
        self.current_file = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions looking for @datamodel."""
        for decorator in node.decorator_list:
            if self._is_decorator(decorator, "datamodel"):
                model_info = self._extract_class_info(node)
                self.models.append(model_info)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions looking for @operation."""
        for decorator in node.decorator_list:
            if self._is_decorator(decorator, "operation"):
                op_info = self._extract_function_info(node)
                self.operations.append(op_info)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions looking for @operation."""
        for decorator in node.decorator_list:
            if self._is_decorator(decorator, "operation"):
                op_info = self._extract_function_info(node)
                self.operations.append(op_info)
        self.generic_visit(node)

    @staticmethod
    def _is_decorator(decorator: ast.expr, name: str) -> bool:
        """Check if a decorator matches the given name."""
        if isinstance(decorator, ast.Name):
            return decorator.id == name
        if isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id == name
        return False

    def _extract_class_info(self, node: ast.ClassDef) -> dict[str, Any]:
        """Extract information from a datamodel class."""
        docstring = ast.get_docstring(node) or ""

        # Extract first line as description
        description = docstring.split("\n")[0].strip() if docstring else ""

        return {
            "type": "model",
            "name": node.name,
            "file": str(self.current_file),
            "line": node.lineno,
            "description": description,
            "docstring": docstring,
        }

    def _extract_function_info(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
        """Extract information from an operation function."""
        docstring = ast.get_docstring(node) or ""

        # Extract first line as description
        description = docstring.split("\n")[0].strip() if docstring else ""

        # Get function signature (parameters)
        args = [arg.arg for arg in node.args.args if arg.arg != "self"]

        return {
            "type": "operation",
            "name": node.name,
            "file": str(self.current_file),
            "line": node.lineno,
            "description": description,
            "docstring": docstring,
            "parameters": args,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }


def autodiscover(
    config_path: Path,
    models_dirs: list[str] | None = None,
    operations_dirs: list[str] | None = None,
) -> dict[str, Any]:
    """Discover all @datamodel and @operation decorated items.

    Args:
        config_path: Path to .jobhunter.yml directory
        models_dirs: List of model directories (relative to config_path)
        operations_dirs: List of operation directories (relative to config_path)

    Returns:
        Dictionary with 'models' and 'operations' lists
    """
    if models_dirs is None:
        models_dirs = ["models"]
    if operations_dirs is None:
        operations_dirs = ["operations"]

    finder = DecoratorFinder()
    results = {"models": [], "operations": []}

    # Scan model directories
    for model_dir in models_dirs:
        model_path = config_path / model_dir
        if not model_path.exists():
            continue

        for py_file in sorted(model_path.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                finder.current_file = py_file
                finder.visit(tree)
            except SyntaxError as e:
                print(f"⚠️  Syntax error in {py_file}: {e}", file=sys.stderr)

    results["models"] = finder.models
    finder.models = []  # Reset for operations

    # Scan operation directories
    for ops_dir in operations_dirs:
        ops_path = config_path / ops_dir
        if not ops_path.exists():
            continue

        for py_file in sorted(ops_path.glob("*.py")):
            if py_file.name == "__init__.py":
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                finder.current_file = py_file
                finder.visit(tree)
            except SyntaxError as e:
                print(f"⚠️  Syntax error in {py_file}: {e}", file=sys.stderr)

    results["operations"] = finder.operations

    return results


def main() -> None:
    """Main entry point for autodiscovery."""
    config_file = sys.argv[1] if len(sys.argv) > 1 else "."
    config_path = Path(config_file)

    if not config_path.is_dir():
        print(f"❌ Config path is not a directory: {config_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Import config manager to get discovery paths
        from core.config_manager import ConfigManager

        config_mgr = ConfigManager(config_path / ".jobhunter.yml", project_root=config_path)
        config = config_mgr.load()
        models_dirs, ops_dirs = config_mgr.get_discovery_dirs()

        # Run autodiscovery
        results = autodiscover(config_path, models_dirs, ops_dirs)

        # Print results
        print(f"🔍 Discovery Results (pwd: {config_path.absolute()})\n")
        print("📋 Config: .jobhunter.yml")
        print(f"   ├─ Models Dir: {', '.join(models_dirs)}")
        print(f"   ├─ Operations Dir: {', '.join(ops_dirs)}")
        print(f"   └─ Ports: {config.get('ports', {})}\n")

        # Print models
        if results["models"]:
            print(f"📦 Models to be discovered ({len(results['models'])}):")
            for model in results["models"]:
                print(f"   ├─ {model['file']}")
                print(f"   │  └─ @datamodel {model['name']}")
                if model["description"]:
                    print(f"   │     {model['description']}")
        else:
            print("📦 Models: None found\n")

        # Print operations
        if results["operations"]:
            print(f"\n🔧 Operations to be discovered ({len(results['operations'])}):")
            for op in results["operations"]:
                print(f"   ├─ {op['file']}")
                print(f"   │  └─ @operation {op['name']}")
                if op["description"]:
                    print(f"   │     {op['description']}")
        else:
            print("\n🔧 Operations: None found\n")

        # Generate CLI preview
        if results["operations"]:
            print("\n🖥️  CLI Commands Preview:")
            for op in results["operations"]:
                params = " ".join([f"--{p} <value>" for p in op["parameters"]])
                print(f"   $ jobhunter {op['name']} {params}".strip())

        print(f"\n✅ Autodiscovery complete! ({len(results['models'])} models, {len(results['operations'])} operations)")
        print("   Next: make compile")

        # Output JSON for programmatic use
        print("\n" + json.dumps(results, indent=2))

    except FileNotFoundError:
        print("❌ Config file not found: .jobhunter.yml", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during autodiscovery: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
