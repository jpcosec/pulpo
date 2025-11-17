"""Unit tests for ModelRegistry and OperationRegistry.

Tests the framework's core registry system that stores model and operation metadata.
"""

import pytest

from core.analysis.registries import ModelRegistry, OperationRegistry


@pytest.mark.unit
class TestModelRegistry:
    """Test ModelRegistry functionality."""

    def test_register_model(self, mock_model_metadata):
        """Test registering a model."""
        # Given: Clean registry (via reset_registries fixture)
        assert len(ModelRegistry.models) == 0

        # When: Registering a model
        ModelRegistry.register("TestModel", mock_model_metadata)

        # Then: Model is in registry
        assert len(ModelRegistry.models) == 1
        assert "TestModel" in ModelRegistry.models
        assert ModelRegistry.models["TestModel"] == mock_model_metadata

    def test_get_model(self, mock_model_metadata):
        """Test retrieving a model from registry."""
        # Given: A registered model
        ModelRegistry.register("TestModel", mock_model_metadata)

        # When: Getting the model
        model = ModelRegistry.get("TestModel")

        # Then: Correct model is returned
        assert model == mock_model_metadata
        assert model["name"] == "TestModel"

    def test_get_nonexistent_model(self):
        """Test getting a model that doesn't exist."""
        # When: Getting nonexistent model
        model = ModelRegistry.get("NonExistent")

        # Then: Returns None
        assert model is None

    def test_get_all_models(self, mock_model_metadata):
        """Test getting all models."""
        # Given: Multiple models
        ModelRegistry.register("Model1", {**mock_model_metadata, "name": "Model1"})
        ModelRegistry.register("Model2", {**mock_model_metadata, "name": "Model2"})

        # When: Getting all models
        all_models = ModelRegistry.get_all()

        # Then: All models returned
        assert len(all_models) == 2
        assert "Model1" in all_models
        assert "Model2" in all_models

    def test_list_model_names(self, mock_model_metadata):
        """Test listing model names."""
        # Given: Multiple models
        ModelRegistry.register("TaskModel", mock_model_metadata)
        ModelRegistry.register("CategoryModel", mock_model_metadata)

        # When: Listing names
        names = ModelRegistry.list_names()

        # Then: Correct names returned
        assert len(names) == 2
        assert "TaskModel" in names
        assert "CategoryModel" in names

    def test_duplicate_registration_overwrites(self, mock_model_metadata):
        """Test that registering same model twice overwrites."""
        # Given: A registered model
        ModelRegistry.register("TestModel", mock_model_metadata)

        # When: Registering same model with different data
        new_metadata = {**mock_model_metadata, "description": "Updated description"}
        ModelRegistry.register("TestModel", new_metadata)

        # Then: Model is overwritten
        assert len(ModelRegistry.models) == 1
        model = ModelRegistry.get("TestModel")
        assert model["description"] == "Updated description"


@pytest.mark.unit
class TestOperationRegistry:
    """Test OperationRegistry functionality."""

    def test_register_operation(self, mock_operation_metadata):
        """Test registering an operation."""
        # Given: Clean registry
        assert len(OperationRegistry.operations) == 0

        # When: Registering an operation
        OperationRegistry.register("test.operation.simple", mock_operation_metadata)

        # Then: Operation is in registry
        assert len(OperationRegistry.operations) == 1
        assert "test.operation.simple" in OperationRegistry.operations

    def test_get_operation(self, mock_operation_metadata):
        """Test retrieving an operation."""
        # Given: A registered operation
        OperationRegistry.register("test.op", mock_operation_metadata)

        # When: Getting the operation
        op = OperationRegistry.get("test.op")

        # Then: Correct operation returned
        assert op == mock_operation_metadata
        assert op["name"] == "test.operation.simple"

    def test_get_all_operations(self, mock_operation_metadata):
        """Test getting all operations."""
        # Given: Multiple operations
        OperationRegistry.register("op1", {**mock_operation_metadata, "name": "op1"})
        OperationRegistry.register("op2", {**mock_operation_metadata, "name": "op2"})

        # When: Getting all operations
        all_ops = OperationRegistry.get_all()

        # Then: All operations returned
        assert len(all_ops) == 2
        assert "op1" in all_ops
        assert "op2" in all_ops

    def test_get_by_category(self, mock_operation_metadata):
        """Test filtering operations by category."""
        # Given: Operations in different categories
        OperationRegistry.register("test.op1", {**mock_operation_metadata, "category": "analysis"})
        OperationRegistry.register("test.op2", {**mock_operation_metadata, "category": "import"})
        OperationRegistry.register("test.op3", {**mock_operation_metadata, "category": "analysis"})

        # When: Getting operations by category
        analysis_ops = OperationRegistry.get_by_category("analysis")

        # Then: Only matching category returned
        assert len(analysis_ops) == 2
        assert "test.op1" in analysis_ops
        assert "test.op3" in analysis_ops
        assert "test.op2" not in analysis_ops

    def test_list_categories(self, mock_operation_metadata):
        """Test listing unique categories."""
        # Given: Operations in different categories
        OperationRegistry.register("op1", {**mock_operation_metadata, "category": "analysis"})
        OperationRegistry.register("op2", {**mock_operation_metadata, "category": "import"})
        OperationRegistry.register("op3", {**mock_operation_metadata, "category": "analysis"})
        OperationRegistry.register("op4", {**mock_operation_metadata, "category": "export"})

        # When: Listing categories
        categories = OperationRegistry.list_categories()

        # Then: Unique categories returned
        assert len(categories) == 3
        assert "analysis" in categories
        assert "import" in categories
        assert "export" in categories


@pytest.mark.unit
def test_registries_are_independent():
    """Test that ModelRegistry and OperationRegistry are independent."""
    # Given: Data in both registries
    ModelRegistry.register("TestModel", {"name": "TestModel"})
    OperationRegistry.register("test.op", {"name": "test.op"})

    # Then: Registries remain independent
    assert len(ModelRegistry.models) == 1
    assert len(OperationRegistry.operations) == 1
    assert "TestModel" not in OperationRegistry.operations
    assert "test.op" not in ModelRegistry.models
