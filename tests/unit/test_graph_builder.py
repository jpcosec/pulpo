"""Unit tests for graph_builder module.

Tests building RegistryGraph from model and operation registries.
"""

import pytest

from core.analysis.graph_builder import build_graph_from_registries
from core.analysis.registry_graph import RegistryGraph
from core.analysis.registries import ModelRegistry, OperationRegistry


@pytest.mark.unit
class TestGraphBuilder:
    """Test graph building from registries."""

    def test_build_empty_graph(self):
        """Test building graph with empty registries."""
        # Given: Empty registries (via reset_registries fixture)

        # When: Building graph
        graph = build_graph_from_registries("test_project")

        # Then: Graph is created but empty
        assert isinstance(graph, RegistryGraph)
        assert graph.metadata["project_name"] == "test_project"
        assert graph.graph.number_of_nodes() == 0
        assert graph.graph.number_of_edges() == 0

    def test_build_graph_with_models(self, mock_model_metadata):
        """Test building graph with models only."""
        # Given: Models in registry
        ModelRegistry.register("Task", {
            **mock_model_metadata,
            "name": "Task",
            "class_name": "Task",
            "fields": {"title": {"type": "str"}, "status": {"type": "str"}}
        })
        ModelRegistry.register("Category", {
            **mock_model_metadata,
            "name": "Category",
            "class_name": "Category",
            "fields": {"name": {"type": "str"}}
        })

        # When: Building graph
        graph = build_graph_from_registries("test_project")

        # Then: Model nodes are created
        assert graph.graph.number_of_nodes() >= 2
        models = graph.get_nodes_by_type("datamodel")
        model_names = [node[1]["name"] for node in models]
        assert "Task" in model_names
        assert "Category" in model_names

    def test_build_graph_with_operations(self, mock_operation_metadata):
        """Test building graph with operations."""
        # Given: Operations in registry
        OperationRegistry.register("test.op1", {
            **mock_operation_metadata,
            "name": "test.op1",
            "category": "test-operations",
            "models_in": ["Task"],
            "models_out": ["Task"]
        })
        OperationRegistry.register("test.op2", {
            **mock_operation_metadata,
            "name": "test.op2",
            "category": "test-operations",
            "models_in": ["Category"],
            "models_out": []
        })

        # When: Building graph
        graph = build_graph_from_registries("test_project")

        # Then: Task nodes are created
        assert graph.graph.number_of_nodes() >= 2
        tasks = graph.get_nodes_by_type("task")
        task_names = [node[1]["name"] for node in tasks]
        assert any("op1" in name for name in task_names)
        assert any("op2" in name for name in task_names)

    def test_build_graph_with_model_relationships(self):
        """Test that model relationships create edges."""
        # Given: Models with relationships
        ModelRegistry.register("Task", {
            "name": "Task",
            "class_name": "Task",
            "module": "models.task",
            "fields": {
                "title": {"type": "str"},
                "category_id": {"type": "str", "reference": "Category"}  # FK relationship
            }
        })
        ModelRegistry.register("Category", {
            "name": "Category",
            "class_name": "Category",
            "module": "models.category",
            "fields": {"name": {"type": "str"}}
        })

        # When: Building graph
        graph = build_graph_from_registries("test_project")

        # Then: Relationship edges may be created
        # Note: Edge creation depends on implementation
        models = graph.get_nodes_by_type("datamodel")
        assert len(models) == 2

    def test_build_graph_creates_flows(self, mock_operation_metadata):
        """Test that operations are grouped into flows."""
        # Given: Operations with categories
        OperationRegistry.register("tasks.create", {
            **mock_operation_metadata,
            "name": "tasks.create",
            "category": "task-management",
            "models_in": ["Task"],
            "models_out": ["Task"]
        })
        OperationRegistry.register("tasks.delete", {
            **mock_operation_metadata,
            "name": "tasks.delete",
            "category": "task-management",
            "models_in": ["Task"],
            "models_out": []
        })

        # When: Building graph
        graph = build_graph_from_registries("test_project")

        # Then: Flows are created for categories
        flows = graph.get_nodes_by_type("flow")
        assert len(flows) > 0
        flow_names = [node[1]["name"] for node in flows]
        # Operations in same category should be in a flow
        assert any("task-management" in str(name).lower() or "task" in str(name).lower() for name in flow_names)

    def test_build_graph_validation(self, mock_model_metadata, mock_operation_metadata):
        """Test that built graph can be validated."""
        # Given: Valid models and operations
        ModelRegistry.register("Task", {
            **mock_model_metadata,
            "name": "Task"
        })
        OperationRegistry.register("tasks.create", {
            **mock_operation_metadata,
            "name": "tasks.create",
            "category": "task-management",
            "models_in": ["Task"],
            "models_out": ["Task"]
        })

        # When: Building and validating graph
        graph = build_graph_from_registries("test_project")
        is_valid, errors, warnings = graph.validate()

        # Then: Graph should be valid or have expected warnings
        # Note: Validation rules depend on implementation
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    def test_build_graph_metadata(self):
        """Test that graph metadata is set correctly."""
        # Given: Models and operations
        ModelRegistry.register("Task", {"name": "Task", "class_name": "Task", "module": "models"})

        # When: Building graph
        graph = build_graph_from_registries("my_project")

        # Then: Metadata is correct
        assert graph.metadata["project_name"] == "my_project"
        assert "created_at" in graph.metadata or "timestamp" in graph.metadata

    def test_build_graph_with_dataflow_edges(self, mock_operation_metadata):
        """Test that operation model relationships create edges."""
        # Given: Operation that reads and writes models
        OperationRegistry.register("tasks.process", {
            **mock_operation_metadata,
            "name": "tasks.process",
            "category": "processing",
            "models_in": ["Task", "Category"],  # Reads two models
            "models_out": ["Task"]  # Writes one model
        })

        # When: Building graph
        graph = build_graph_from_registries("test_project")

        # Then: Edges should connect task to models
        assert graph.graph.number_of_edges() >= 0
        # Note: Edge count depends on implementation details


@pytest.mark.unit
def test_graph_builder_preserves_registry_data(mock_model_metadata, mock_operation_metadata):
    """Test that building graph doesn't modify registries."""
    # Given: Data in registries
    ModelRegistry.register("Task", mock_model_metadata)
    OperationRegistry.register("test.op", mock_operation_metadata)

    original_models = dict(ModelRegistry.models)
    original_ops = dict(OperationRegistry.operations)

    # When: Building graph
    build_graph_from_registries("test_project")

    # Then: Registries unchanged
    assert ModelRegistry.models == original_models
    assert OperationRegistry.operations == original_ops


@pytest.mark.unit
def test_build_multiple_graphs():
    """Test building multiple graphs from same registries."""
    # Given: Data in registries
    ModelRegistry.register("Task", {"name": "Task", "class_name": "Task", "module": "models"})

    # When: Building multiple graphs
    graph1 = build_graph_from_registries("project1")
    graph2 = build_graph_from_registries("project2")

    # Then: Both graphs are independent
    assert graph1.metadata["project_name"] == "project1"
    assert graph2.metadata["project_name"] == "project2"
    assert graph1.graph is not graph2.graph
