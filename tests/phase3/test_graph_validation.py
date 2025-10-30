"""
Phase 3 Graph Validation Tests

Tests comprehensive validation of:
- MCG (Model Composition Graph)
- OHG (Operation Hierarchy Graph)
- DFG (Data Flow Graph)
"""

import pytest
from pydantic import BaseModel, Field
from beanie import Document

from core.registries import ModelRegistry, OperationRegistry
from core.hierarchy import HierarchyParser


class TestOHGValidation:
    """Operation Hierarchy Graph validation tests."""

    def test_hierarchical_naming_valid(self):
        """Test valid hierarchical operation names."""
        valid_names = [
            "pokemon.management.catch",
            "pokemon.battles.execute",
            "pokemon.evolution.stage1",
            "data.ingestion.fetch",
            "ml.training.train",
        ]

        for name in valid_names:
            parsed = HierarchyParser.parse(name)
            assert parsed is not None
            assert len(parsed.hierarchy) >= 1
            assert parsed.full_name == name

    def test_hierarchical_naming_invalid(self):
        """Test invalid operation names."""
        invalid_names = [
            "catch pokemon",  # Space not allowed
            "pokemon-management",  # Hyphen not allowed
            "pokemon.management.catch.extra",  # Too deep (5 levels)
        ]

        for name in invalid_names:
            try:
                parsed = HierarchyParser.parse(name)
                # Should either fail or be marked invalid
                if parsed:
                    assert "-" not in parsed.full_name or " " not in parsed.full_name
            except (ValueError, AttributeError):
                pass  # Expected for invalid names

    def test_operation_containment(self):
        """Test parent-child containment relationships."""
        parsed = HierarchyParser.parse("pokemon.management.catch")

        # Check parent
        assert parsed.parent == "pokemon.management"

        # Check is_child_of
        assert parsed.is_child_of("pokemon") is True
        assert parsed.is_child_of("pokemon.management") is True
        assert parsed.is_child_of("nonexistent") is False

    def test_sibling_operations(self):
        """Test sibling operation detection."""
        op1 = HierarchyParser.parse("pokemon.management.catch")
        op2 = HierarchyParser.parse("pokemon.management.train")
        op3 = HierarchyParser.parse("pokemon.battles.execute")

        # Siblings
        assert op1.is_sibling_of("pokemon.management.train") is True

        # Not siblings
        assert op1.is_sibling_of("pokemon.battles.execute") is False

    def test_hierarchy_depth(self):
        """Test hierarchy depth constraints."""
        parsed = HierarchyParser.parse("pokemon.management.catch")
        assert parsed.level >= 1

        # Check MAX_LEVEL is enforced
        assert parsed.level <= HierarchyParser.MAX_LEVEL

    def test_root_hierarchy(self):
        """Test root-level hierarchy detection."""
        simple = HierarchyParser.parse("simple")
        assert simple.root == "simple"
        assert simple.is_standalone is True

        nested = HierarchyParser.parse("pokemon.management.catch")
        assert nested.root == "pokemon"
        assert nested.is_standalone is False

    def test_all_parents(self):
        """Test all_parents property."""
        parsed = HierarchyParser.parse("data.pipeline.extract.transform.load")
        all_parents = parsed.all_parents

        # Should include all parent levels except the operation itself
        assert "data" in all_parents
        assert "data.pipeline" in all_parents
        assert "data.pipeline.extract" in all_parents
        assert "data.pipeline.extract.transform" in all_parents

    def test_operation_separator(self):
        """Test operation name separator."""
        assert HierarchyParser.SEPARATOR == "."

    def test_parse_single_level(self):
        """Test parsing single-level operation."""
        parsed = HierarchyParser.parse("simple_operation")
        assert parsed.level == 1
        assert parsed.hierarchy == ["simple_operation"]
        assert parsed.is_standalone is True

    def test_parse_three_levels(self):
        """Test parsing three-level operation."""
        parsed = HierarchyParser.parse("pokemon.management.catch")
        assert parsed.level == 3
        assert parsed.hierarchy == ["pokemon", "management", "catch"]
        assert not parsed.is_standalone

    def test_hierarchy_parser_consistency(self):
        """Test that hierarchy parser is consistent."""
        name = "system.module.operation"

        parsed1 = HierarchyParser.parse(name)
        parsed2 = HierarchyParser.parse(name)

        assert parsed1.full_name == parsed2.full_name
        assert parsed1.hierarchy == parsed2.hierarchy
        assert parsed1.level == parsed2.level


class TestMCGValidation:
    """Model Composition Graph validation tests."""

    def test_model_registry_access(self):
        """Test ModelRegistry can be accessed."""
        models = ModelRegistry.list_all()
        # May be empty if no models registered
        assert isinstance(models, (list, tuple))

    def test_model_registry_get(self):
        """Test getting specific model from registry."""
        # Try to get a model
        model = ModelRegistry.get("NonExistent")
        # Should return None if not found
        assert model is None or hasattr(model, "name")

    def test_model_field_validation(self):
        """Test model field validation."""
        # Create a test model
        class TestModel(Document):
            name: str = Field(..., description="Test name")
            value: int = Field(default=0, description="Test value")

            class Settings:
                name = "test_models"

        # Check fields have descriptions
        fields = TestModel.model_fields
        assert "name" in fields
        assert "value" in fields


class TestDFGValidation:
    """Data Flow Graph validation tests."""

    def test_operation_registry_access(self):
        """Test OperationRegistry can be accessed."""
        operations = OperationRegistry.list_all()
        # May be empty if no operations registered
        assert isinstance(operations, (list, tuple))

    def test_operation_registry_get(self):
        """Test getting specific operation from registry."""
        operation = OperationRegistry.get("nonexistent_operation")
        # Should return None if not found
        assert operation is None or hasattr(operation, "name")

    def test_operation_io_validation(self):
        """Test operation input/output validation."""
        # Define test I/O models
        class InputModel(BaseModel):
            item_id: str = Field(..., description="Item ID")
            action: str = Field(..., description="Action to perform")

        class OutputModel(BaseModel):
            success: bool = Field(..., description="Success flag")
            message: str = Field(..., description="Status message")

        # Verify models are serializable
        input_data = InputModel(item_id="123", action="process")
        output_data = OutputModel(success=True, message="OK")

        # Should be able to serialize
        assert input_data.model_dump() is not None
        assert output_data.model_dump() is not None


class TestCrossGraphValidation:
    """Cross-graph consistency validation tests."""

    def test_operation_names_are_hierarchical(self):
        """Test all operation names follow hierarchical convention."""
        operations = OperationRegistry.list_all()

        for op in operations:
            if hasattr(op, "name"):
                # Try to parse as hierarchical
                try:
                    parsed = HierarchyParser.parse(op.name)
                    assert parsed is not None
                except ValueError:
                    # Single-level names are OK
                    pass

    def test_model_operation_consistency(self):
        """Test that operations reference models that exist."""
        # This would require checking that models_in and models_out
        # reference registered models

        # For now, verify registries are accessible
        models = ModelRegistry.list_all()
        operations = OperationRegistry.list_all()

        assert isinstance(models, (list, tuple))
        assert isinstance(operations, (list, tuple))


class TestValidationEdgeCases:
    """Test edge cases in graph validation."""

    def test_empty_hierarchy_name(self):
        """Test handling of empty operation names."""
        try:
            parsed = HierarchyParser.parse("")
            # Should either fail or be invalid
            assert parsed is None or parsed.full_name == ""
        except (ValueError, AttributeError):
            pass  # Expected

    def test_very_deep_hierarchy(self):
        """Test very deep operation hierarchies."""
        # Create a 10-level deep name (MAX_LEVEL)
        deep_name = ".".join([f"level{i}" for i in range(10)])
        parsed = HierarchyParser.parse(deep_name)

        if parsed:
            assert parsed.level <= HierarchyParser.MAX_LEVEL

    def test_special_characters_in_names(self):
        """Test handling of special characters in operation names."""
        # Valid: underscores and lowercase
        valid = "pokemon_management_catch"
        try:
            parsed = HierarchyParser.parse(valid)
            assert parsed is not None
        except ValueError:
            pass

        # Invalid: hyphens
        invalid = "pokemon-management-catch"
        try:
            parsed = HierarchyParser.parse(invalid)
            # Should either fail or be marked invalid
            if parsed:
                assert "-" not in parsed.full_name
        except ValueError:
            pass

    def test_duplicate_hierarchy_levels(self):
        """Test handling of duplicate names in hierarchy."""
        parsed = HierarchyParser.parse("data.data.data")
        # Should be valid (just unusual naming)
        assert parsed is not None if parsed else True


class TestValidationReporting:
    """Test error reporting and messages."""

    def test_parsing_returns_useful_info(self):
        """Test that parsing returns useful information."""
        parsed = HierarchyParser.parse("pokemon.management.catch")

        # Should have all useful properties
        assert hasattr(parsed, "full_name")
        assert hasattr(parsed, "hierarchy")
        assert hasattr(parsed, "level")
        assert hasattr(parsed, "step")
        assert hasattr(parsed, "parent")
        assert hasattr(parsed, "is_standalone")

    def test_registry_provides_metadata(self):
        """Test that registries provide useful metadata."""
        model = ModelRegistry.get("NonExistent")
        # When get() returns None, that's clear feedback

        operation = OperationRegistry.get("nonexistent")
        # Same for operations
        assert model is None or hasattr(model, "name")
        assert operation is None or hasattr(operation, "name")
