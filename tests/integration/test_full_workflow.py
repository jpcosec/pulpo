"""Integration tests for full Pulpo workflow.

Tests the complete pipeline:
1. Model/operation definition (@datamodel, @operation decorators)
2. Registration in registries
3. Graph building
4. Validation
5. Code generation (structure only, not execution)

Uses sample fixtures from todo-app patterns.
"""

import pytest
import importlib
import sys
from pathlib import Path

from core.analysis.registries import ModelRegistry, OperationRegistry
from core.analysis.graph_builder import build_graph_from_registries


@pytest.mark.integration
class TestFullWorkflowWithFixtures:
    """Test complete workflow using todo-app-style fixtures."""

    def test_import_sample_models(self, sample_models_module):
        """Test that sample models can be imported and register themselves."""
        # When: Importing sample models module
        models_mod = importlib.import_module(sample_models_module)

        # Then: Models are registered
        assert len(ModelRegistry.models) > 0
        assert "Category" in ModelRegistry.models
        assert "Task" in ModelRegistry.models
        assert "Alarm" in ModelRegistry.models

        # And: Model metadata is complete
        task_meta = ModelRegistry.get("Task")
        assert task_meta["name"] == "Task"
        assert task_meta["description"] == "Task with dependencies and computed fields"
        assert "test" in task_meta["tags"]

    def test_import_sample_operations(self, sample_operations_module):
        """Test that sample operations can be imported and register themselves."""
        # When: Importing sample operations module
        ops_mod = importlib.import_module(sample_operations_module)

        # Then: Operations are registered
        assert len(OperationRegistry.operations) > 0
        assert "tasks.analysis.check_needed" in OperationRegistry.operations
        assert "tasks.analysis.next_by_urgency" in OperationRegistry.operations
        assert "tasks.loader.markdown" in OperationRegistry.operations

        # And: Operation metadata is complete
        check_meta = OperationRegistry.get("tasks.analysis.check_needed")
        assert check_meta["name"] == "tasks.analysis.check_needed"
        assert check_meta["category"] == "task-analysis"
        assert "Task" in check_meta["models_in"]

    def test_build_graph_from_fixtures(self, sample_models_module, sample_operations_module):
        """Test building graph from imported fixtures."""
        # Given: Imported models and operations
        importlib.import_module(sample_models_module)
        importlib.import_module(sample_operations_module)

        # When: Building graph
        graph = build_graph_from_registries("todo-app-test")

        # Then: Graph contains expected nodes
        assert graph.graph.number_of_nodes() > 0

        # DataModel nodes
        models = graph.get_nodes_by_type("datamodel")
        model_names = [node[1]["name"] for node in models]
        assert "Task" in model_names
        assert "Category" in model_names

        # Task nodes (operations)
        tasks = graph.get_nodes_by_type("task")
        assert len(tasks) > 0

        # Flow nodes (categories)
        flows = graph.get_nodes_by_type("flow")
        assert len(flows) > 0

    def test_validate_graph_from_fixtures(self, sample_models_module, sample_operations_module):
        """Test validating graph built from fixtures."""
        # Given: Graph from fixtures
        importlib.import_module(sample_models_module)
        importlib.import_module(sample_operations_module)
        graph = build_graph_from_registries("todo-app-test")

        # When: Validating graph
        is_valid, errors, warnings = graph.validate()

        # Then: Validation runs successfully
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

        # If there are errors, they should be specific
        if not is_valid:
            for error in errors:
                assert isinstance(error, str)
                assert len(error) > 0

    def test_graph_queries_with_fixtures(self, sample_models_module, sample_operations_module):
        """Test querying graph built from fixtures."""
        # Given: Graph from fixtures
        importlib.import_module(sample_models_module)
        importlib.import_module(sample_operations_module)
        graph = build_graph_from_registries("todo-app-test")

        # When: Querying tasks by flow
        flows = graph.get_nodes_by_type("flow")
        if flows:
            flow_name = flows[0][1].get("name") or flows[0][1].get("full_path")
            tasks = graph.get_tasks_by_flow(flow_name)

            # Then: Tasks are returned
            assert isinstance(tasks, list)

        # When: Getting all datamodels
        datamodels = graph.get_nodes_by_type("datamodel")

        # Then: Expected models are present
        assert len(datamodels) >= 3  # Category, Task, Alarm minimum

    def test_operation_categorization(self, sample_operations_module):
        """Test that operations are correctly categorized."""
        # Given: Imported operations
        importlib.import_module(sample_operations_module)

        # When: Getting operations by category
        analysis_ops = OperationRegistry.get_by_category("task-analysis")
        import_ops = OperationRegistry.get_by_category("task-import")
        prioritization_ops = OperationRegistry.get_by_category("task-prioritization")

        # Then: Operations are in correct categories
        assert len(analysis_ops) >= 1
        assert "tasks.analysis.check_needed" in analysis_ops

        assert len(import_ops) >= 1
        assert "tasks.loader.markdown" in import_ops

        if prioritization_ops:
            assert "tasks.analysis.next_by_urgency" in prioritization_ops

    def test_models_have_complete_metadata(self, sample_models_module):
        """Test that model metadata is complete."""
        # Given: Imported models
        importlib.import_module(sample_models_module)

        # When: Getting Task model metadata
        task_meta = ModelRegistry.get("Task")

        # Then: All required metadata fields present
        assert "name" in task_meta
        assert "description" in task_meta
        assert "tags" in task_meta
        assert task_meta["name"] == "Task"
        assert len(task_meta["description"]) > 0

    def test_operations_have_complete_metadata(self, sample_operations_module):
        """Test that operation metadata is complete."""
        # Given: Imported operations
        importlib.import_module(sample_operations_module)

        # When: Getting operation metadata
        check_meta = OperationRegistry.get("tasks.analysis.check_needed")

        # Then: All required metadata fields present
        assert "name" in check_meta
        assert "description" in check_meta
        assert "category" in check_meta
        assert "models_in" in check_meta
        assert "models_out" in check_meta
        assert check_meta["name"] == "tasks.analysis.check_needed"
        assert len(check_meta["description"]) > 0


@pytest.mark.integration
class TestGraphPersistence:
    """Test graph save/load functionality."""

    def test_save_and_load_graph(self, sample_models_module, tmp_path):
        """Test saving and loading graph."""
        # Given: Graph from fixtures
        importlib.import_module(sample_models_module)
        graph = build_graph_from_registries("test-project")

        # When: Saving graph
        save_path = tmp_path / "test_graph.json"
        graph.save(save_path)

        # Then: File is created
        assert save_path.exists()
        assert save_path.stat().st_size > 0

        # When: Loading graph
        from core.analysis.registry_graph.persistence import GraphPersistence
        loaded_graph = GraphPersistence.load(save_path)

        # Then: Graph is restored
        assert loaded_graph.metadata["project_name"] == "test-project"
        assert loaded_graph.graph.number_of_nodes() == graph.graph.number_of_nodes()

    def test_graph_export_mermaid(self, sample_models_module, tmp_path):
        """Test exporting graph to Mermaid format."""
        # Given: Graph from fixtures
        importlib.import_module(sample_models_module)
        graph = build_graph_from_registries("test-project")

        # When: Exporting to Mermaid
        mermaid_path = tmp_path / "graph.mmd"
        graph.export_mermaid(mermaid_path)

        # Then: File is created with content
        assert mermaid_path.exists()
        content = mermaid_path.read_text()
        assert len(content) > 0
        assert "graph" in content.lower() or "flowchart" in content.lower()

    def test_graph_export_dot(self, sample_models_module, tmp_path):
        """Test exporting graph to DOT format."""
        # Given: Graph from fixtures
        importlib.import_module(sample_models_module)
        graph = build_graph_from_registries("test-project")

        # When: Exporting to DOT
        dot_path = tmp_path / "graph.dot"
        graph.export_dot(dot_path)

        # Then: File is created with DOT syntax
        assert dot_path.exists()
        content = dot_path.read_text()
        assert len(content) > 0
        assert "digraph" in content or "graph" in content


@pytest.mark.integration
@pytest.mark.slow
def test_end_to_end_workflow(sample_models_module, sample_operations_module, tmp_path):
    """Test complete end-to-end workflow from decorators to graph export."""
    # Step 1: Import models and operations
    importlib.import_module(sample_models_module)
    importlib.import_module(sample_operations_module)

    # Verify registries populated
    assert len(ModelRegistry.models) >= 3
    assert len(OperationRegistry.operations) >= 3

    # Step 2: Build graph
    graph = build_graph_from_registries("todo-app-e2e")

    # Verify graph structure
    assert graph.graph.number_of_nodes() > 0
    assert len(graph.get_nodes_by_type("datamodel")) >= 3
    assert len(graph.get_nodes_by_type("task")) >= 3

    # Step 3: Validate graph
    is_valid, errors, warnings = graph.validate()

    # Verify validation ran
    assert isinstance(is_valid, bool)

    # Step 4: Save graph
    save_path = tmp_path / "e2e_graph.json"
    graph.save(save_path)

    # Verify saved
    assert save_path.exists()

    # Step 5: Export visualizations
    mermaid_path = tmp_path / "e2e_graph.mmd"
    graph.export_mermaid(mermaid_path)

    dot_path = tmp_path / "e2e_graph.dot"
    graph.export_dot(dot_path)

    # Verify exports
    assert mermaid_path.exists()
    assert dot_path.exists()

    # Step 6: Reload and verify
    from core.analysis.registry_graph.persistence import GraphPersistence
    loaded_graph = GraphPersistence.load(save_path)

    assert loaded_graph.metadata["project_name"] == "todo-app-e2e"
    assert loaded_graph.graph.number_of_nodes() == graph.graph.number_of_nodes()
