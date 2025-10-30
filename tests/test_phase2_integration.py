"""
Integration tests for Phase 2: Prefect flow generation.

Tests the complete flow from operations → flow definitions → generated code.
"""

import pytest
from pathlib import Path
from pydantic import BaseModel, Field

from core.decorators import datamodel, operation
from core.cli_interface import CLI
from core.hierarchy import HierarchyParser
from core.orchestration.dataflow import OperationMetadata, DataFlowAnalyzer
from core.orchestration.compiler import OrchestrationCompiler
from core.orchestration.prefect_codegen import PrefectCodeGenerator


# Test fixtures: Define a simple hierarchy for testing

class RawJobs(BaseModel):
    """Raw job listings."""

    title: str
    company: str
    url: str


class CleanedJobs(BaseModel):
    """Cleaned job listings."""

    title: str
    company: str


def test_hierarchy_parser_with_operation_names():
    """Test that HierarchyParser handles hierarchical operation names."""
    names = [
        "scraping.stepstone.fetch",
        "scraping.linkedin.fetch",
        "scraping.merge",
        "parsing.clean_text",
        "parsing.validate",
        "validate",
    ]

    # Test parsing
    parsed = HierarchyParser.parse("scraping.stepstone.fetch")
    assert parsed.hierarchy == ["scraping", "stepstone", "fetch"]
    assert parsed.parent == "scraping.stepstone"
    assert parsed.level == 3
    assert not parsed.is_standalone

    # Test grouping by parent
    grouped = HierarchyParser.group_by_parent(names)
    assert len(grouped["scraping.stepstone"]) == 1
    assert len(grouped["scraping"]) == 1  # merge
    assert len(grouped[None]) == 1  # validate (standalone)

    # Test grouping by root
    by_root = HierarchyParser.group_by_root(names)
    assert len(by_root["scraping"]) == 3
    assert len(by_root["parsing"]) == 2
    assert len(by_root["validate"]) == 1


def test_data_flow_analyzer_detects_dependencies():
    """Test that DataFlowAnalyzer correctly infers dependencies from data models."""
    # Create operations with data flow
    ops = [
        OperationMetadata(type("", (), {
            "name": "scraping.stepstone.fetch",
            "models_in": [],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
        OperationMetadata(type("", (), {
            "name": "scraping.linkedin.fetch",
            "models_in": [],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
        OperationMetadata(type("", (), {
            "name": "scraping.merge",
            "models_in": ["RawJobs"],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
        OperationMetadata(type("", (), {
            "name": "parsing.clean",
            "models_in": ["RawJobs"],
            "models_out": ["CleanedJobs"],
            "function": lambda: None,
        })()),
    ]

    # Analyze data flow
    graph = DataFlowAnalyzer.build_dependency_graph(ops)

    # merge depends on both fetch operations
    merge_deps = graph.get_dependencies("scraping.merge")
    assert "scraping.stepstone.fetch" in merge_deps
    assert "scraping.linkedin.fetch" in merge_deps

    # clean depends on merge (gets RawJobs from it)
    clean_deps = graph.get_dependencies("parsing.clean")
    assert "scraping.merge" in clean_deps

    # No cycles
    assert not graph.has_cycle()


def test_parallel_group_detection():
    """Test that operations with same inputs/outputs are detected as parallel."""
    ops = [
        OperationMetadata(type("", (), {
            "name": "scraping.stepstone.fetch",
            "models_in": [],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
        OperationMetadata(type("", (), {
            "name": "scraping.linkedin.fetch",
            "models_in": [],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
    ]

    groups = DataFlowAnalyzer.find_parallel_groups(ops)

    # Both should be in same parallel group (same inputs/outputs)
    assert len(groups) == 1
    assert set(groups[0]) == {"scraping.stepstone.fetch", "scraping.linkedin.fetch"}


def test_orchestration_compiler_creates_flows():
    """Test that OrchestrationCompiler generates flow definitions."""
    ops = [
        OperationMetadata(type("", (), {
            "name": "scraping.stepstone.fetch",
            "models_in": [],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
        OperationMetadata(type("", (), {
            "name": "scraping.merge",
            "models_in": ["RawJobs"],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
    ]

    compiler = OrchestrationCompiler()
    orchestration = compiler.compile(ops)

    # Should have flows
    assert len(orchestration.flows) > 0

    # Should be valid
    assert orchestration.is_valid

    # Should have flow for scraping hierarchy
    scraping_flows = [f for f in orchestration.flows if f.hierarchy_path.startswith("scraping")]
    assert len(scraping_flows) > 0


def test_prefect_code_generation():
    """Test that PrefectCodeGenerator produces valid Python code."""
    ops = [
        OperationMetadata(type("", (), {
            "name": "scraping.fetch",
            "models_in": [],
            "models_out": ["RawJobs"],
            "function": lambda: None,
        })()),
    ]

    compiler = OrchestrationCompiler()
    orchestration = compiler.compile(ops)

    generator = PrefectCodeGenerator()
    flow_codes = generator.generate_all_flows(orchestration)

    # Should generate code
    assert len(flow_codes) > 0

    # Code should be valid Python
    for flow_name, code in flow_codes.items():
        try:
            compile(code, f"<{flow_name}>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated invalid Python for {flow_name}: {e}")


def test_cli_compile_generates_flows():
    """Test that CLI.compile() generates Prefect flows to run_cache when operations exist."""
    from core.registries import OperationRegistry

    # Manually register an operation (simulating what @operation decorator does)
    op_meta = type("", (), {
        "name": "test.op",
        "models_in": [],
        "models_out": ["TestModel"],
        "function": lambda: None,
    })()

    # Create a test metadata object
    test_op = type("OperationMetadata", (), {
        "name": "test.op",
        "description": "Test operation",
        "category": "test",
        "input_schema": BaseModel,
        "output_schema": BaseModel,
        "function": async_dummy,
        "tags": [],
        "permissions": [],
        "async_enabled": True,
        "models_in": [],
        "models_out": ["TestModel"],
        "stage": None,
    })()

    # Register it
    OperationRegistry.register(test_op)

    try:
        # Create CLI (will discover the registered operation)
        cli = CLI(run_cache_dir="test_run_cache", verbose=False)

        # Check that operation was discovered
        ops = cli.list_operations()
        assert "test.op" in ops, f"Operation not discovered. Found: {ops}"

        # Compile should generate Prefect flows
        cache_dir = cli.compile()

        # Check that orchestration directory was created
        orch_dir = cache_dir / "orchestration"
        assert orch_dir.exists(), "orchestration/ directory not created"
        assert (orch_dir / "__init__.py").exists(), "__init__.py not created"

        # Flows should be generated
        flow_files = list(orch_dir.glob("*_flow.py"))
        assert len(flow_files) > 0, f"No flow files generated in {orch_dir}"

    finally:
        # Clean up
        OperationRegistry.clear()
        import shutil
        if Path("test_run_cache").exists():
            shutil.rmtree("test_run_cache")


async def async_dummy():
    """Dummy async function for testing."""
    return {"result": "test"}


def test_hierarchy_parser_standalone_operations():
    """Test that standalone operations (no parent) are handled correctly."""
    names = ["validate", "cleanup", "logging"]

    # All should be standalone
    for name in names:
        parsed = HierarchyParser.parse(name)
        assert parsed.is_standalone
        assert parsed.parent is None
        assert parsed.level == 1

    # Group by parent
    grouped = HierarchyParser.group_by_parent(names)
    assert None in grouped
    assert len(grouped[None]) == 3


def test_topological_sort_respects_dependencies():
    """Test that topological sort produces correct execution order."""
    ops = [
        OperationMetadata(type("", (), {
            "name": "step1",
            "models_in": [],
            "models_out": ["A"],
            "function": lambda: None,
        })()),
        OperationMetadata(type("", (), {
            "name": "step2",
            "models_in": ["A"],
            "models_out": ["B"],
            "function": lambda: None,
        })()),
        OperationMetadata(type("", (), {
            "name": "step3",
            "models_in": ["B"],
            "models_out": ["C"],
            "function": lambda: None,
        })()),
    ]

    order = DataFlowAnalyzer.topological_sort(ops)

    # step1 must come before step2
    assert order.index("step1") < order.index("step2")
    # step2 must come before step3
    assert order.index("step2") < order.index("step3")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
