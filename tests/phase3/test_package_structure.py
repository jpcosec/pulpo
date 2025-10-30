"""
Phase 3 Iteration 1: Package Structure & Installation Tests

Tests that Pulpo can be installed and imported correctly.
Validates the package structure and entry points.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestPackageInstallation:
    """Test package can be installed via pip."""

    def test_package_installable_via_pip(self):
        """Test that package can be installed with: pip install -e ."""
        # Get the pulpo package directory
        pulpo_root = Path(__file__).parent.parent.parent

        # Try to install in editable mode
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(pulpo_root)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"Installation failed: {result.stderr}"
        assert "Successfully installed" in result.stdout or "already satisfied" in result.stdout.lower()

    def test_imports_work_from_external_project(self):
        """Test imports work outside package directory."""
        # Ensure we can import from anywhere
        try:
            from pulpo import CLI
            from pulpo import datamodel
            from pulpo import operation
        except ImportError as e:
            pytest.fail(f"Failed to import from pulpo: {e}")

    def test_all_core_imports_accessible(self):
        """Test all core submodules can be imported."""
        # Test various import paths
        imports_to_test = [
            ("core.hierarchy", "HierarchyParser"),
            ("core.orchestration.dataflow", "DataFlowAnalyzer"),
            ("core.orchestration.compiler", "OrchestrationCompiler"),
            ("core.orchestration.sync_async", "SyncAsyncDetector"),
            ("core.orchestration.prefect_codegen", "PrefectCodeGenerator"),
            ("core.registries", "OperationRegistry"),
            ("core.registries", "ModelRegistry"),
            ("core.cli_interface", "CLI"),
        ]

        for module_name, class_name in imports_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                pytest.fail(f"Failed to import {class_name} from {module_name}: {e}")

    def test_pulpo_command_available(self):
        """Test that 'pulpo' CLI command is available."""
        # Check that the entry point is registered
        result = subprocess.run(
            ["python", "-m", "core.cli.main", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, f"CLI help failed: {result.stderr}"
        assert "Commands:" in result.stdout or "commands" in result.stdout.lower()

    def test_package_metadata_correct(self):
        """Test package metadata is correct in pyproject.toml."""
        import tomllib

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"

        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)

        # Check package name and version
        assert pyproject["tool"]["poetry"]["name"] == "pulpocore"
        assert pyproject["tool"]["poetry"]["version"] == "0.6.0"

        # Check entry point
        assert "pulpo" in pyproject["tool"]["poetry"]["scripts"]
        assert "core.cli.main:main" in pyproject["tool"]["poetry"]["scripts"]["pulpo"]


class TestImportPatterns:
    """Test various import patterns work correctly."""

    def test_from_pulpo_import_cli(self):
        """Test: from pulpo import CLI"""
        try:
            from pulpo import CLI
            assert CLI is not None
            assert hasattr(CLI, "compile")
            assert hasattr(CLI, "up")
        except Exception as e:
            pytest.fail(f"Import failed: {e}")

    def test_from_pulpo_import_decorators(self):
        """Test: from pulpo import datamodel, operation"""
        try:
            from pulpo import datamodel, operation
            assert datamodel is not None
            assert operation is not None
            assert callable(datamodel)
            assert callable(operation)
        except Exception as e:
            pytest.fail(f"Import failed: {e}")

    def test_from_pulpo_import_registries(self):
        """Test: from pulpo import ModelRegistry, OperationRegistry"""
        try:
            from pulpo import ModelRegistry, OperationRegistry
            assert ModelRegistry is not None
            assert OperationRegistry is not None
        except Exception as e:
            pytest.fail(f"Import failed: {e}")

    def test_core_submodule_imports(self):
        """Test direct core submodule imports."""
        try:
            from core.hierarchy import HierarchyParser
            from core.orchestration.dataflow import DataFlowAnalyzer
            from core.orchestration.compiler import OrchestrationCompiler
            from core.orchestration.sync_async import SyncAsyncDetector
            from core.orchestration.prefect_codegen import PrefectCodeGenerator

            # Verify they're actually importable
            assert HierarchyParser is not None
            assert DataFlowAnalyzer is not None
            assert OrchestrationCompiler is not None
            assert SyncAsyncDetector is not None
            assert PrefectCodeGenerator is not None
        except Exception as e:
            pytest.fail(f"Core module import failed: {e}")


class TestPackageStructure:
    """Test the package directory structure."""

    def test_required_directories_exist(self):
        """Test that all required directories exist."""
        pulpo_root = Path(__file__).parent.parent.parent

        required_dirs = [
            "core",
            "core/orchestration",
            "core/cli",
            "tests",
            "tests/phase3",
            "plan_docs",
        ]

        for dir_name in required_dirs:
            dir_path = pulpo_root / dir_name
            assert dir_path.exists() and dir_path.is_dir(), f"Missing directory: {dir_name}"

    def test_required_files_exist(self):
        """Test that all required files exist."""
        pulpo_root = Path(__file__).parent.parent.parent

        required_files = [
            "pyproject.toml",
            "README.md",
            "core/__init__.py",
            "core/cli_interface.py",
            "core/cli/main.py",
            "core/decorators.py",
            "core/registries.py",
            "core/hierarchy.py",
            "core/orchestration/__init__.py",
            "core/orchestration/dataflow.py",
            "core/orchestration/compiler.py",
            "core/orchestration/sync_async.py",
            "core/orchestration/prefect_codegen.py",
        ]

        for file_name in required_files:
            file_path = pulpo_root / file_name
            assert file_path.exists() and file_path.is_file(), f"Missing file: {file_name}"

    def test_init_files_present(self):
        """Test that __init__.py files are present in all packages."""
        pulpo_root = Path(__file__).parent.parent.parent

        packages = [
            "core",
            "core/orchestration",
            "core/cli",
            "tests/phase3",
            "tests/integration",
            "tests/fixtures",
        ]

        for package in packages:
            init_file = pulpo_root / package / "__init__.py"
            assert init_file.exists(), f"Missing __init__.py in {package}"


class TestModuleContent:
    """Test that key modules contain expected content."""

    def test_cli_interface_has_methods(self):
        """Test CLI class has required methods."""
        from core.cli_interface import CLI

        required_methods = [
            "compile",
            "up",
            "down",
            "prefect",
            "db",
            "api",
            "ui",
            "init",
            "clean",
            "list_models",
            "list_operations",
            "inspect_model",
            "inspect_operation",
        ]

        for method_name in required_methods:
            assert hasattr(CLI, method_name), f"CLI missing method: {method_name}"

    def test_hierarchy_parser_has_methods(self):
        """Test HierarchyParser has required methods."""
        from core.hierarchy import HierarchyParser

        required_methods = [
            "parse",
            "get_parent",
            "get_level",
            "is_standalone",
            "group_by_parent",
            "group_by_root",
            "build_hierarchy_tree",
        ]

        for method_name in required_methods:
            assert hasattr(HierarchyParser, method_name), f"HierarchyParser missing method: {method_name}"

    def test_data_flow_analyzer_has_methods(self):
        """Test DataFlowAnalyzer has required methods."""
        from core.orchestration.dataflow import DataFlowAnalyzer

        required_methods = [
            "build_dependency_graph",
            "find_parallel_groups",
            "topological_sort",
            "validate_dataflow",
        ]

        for method_name in required_methods:
            assert hasattr(DataFlowAnalyzer, method_name), f"DataFlowAnalyzer missing method: {method_name}"

    def test_orchestration_compiler_has_methods(self):
        """Test OrchestrationCompiler has required methods."""
        from core.orchestration.compiler import OrchestrationCompiler

        assert hasattr(OrchestrationCompiler, "compile"), "OrchestrationCompiler missing compile method"

    def test_sync_async_detector_has_methods(self):
        """Test SyncAsyncDetector has required methods."""
        from core.orchestration.sync_async import SyncAsyncDetector

        required_methods = ["is_async", "is_sync", "wrap_if_sync", "detect_and_wrap"]

        for method_name in required_methods:
            assert hasattr(SyncAsyncDetector, method_name), f"SyncAsyncDetector missing method: {method_name}"

    def test_prefect_codegen_has_methods(self):
        """Test PrefectCodeGenerator has required methods."""
        from core.orchestration.prefect_codegen import PrefectCodeGenerator

        required_methods = ["generate_all_flows", "generate_flow"]

        for method_name in required_methods:
            assert hasattr(PrefectCodeGenerator, method_name), f"PrefectCodeGenerator missing method: {method_name}"
