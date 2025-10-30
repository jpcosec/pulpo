# Graph Validation Strategy

**Date:** 2025-10-30
**Status:** Comprehensive Validation Design
**Scope:** Complete validation of MCG, OHG, and DFG

---

## User Feedback

**Requirement:** "About the graph_validation go with all"

This means: Implement **comprehensive validation** checking all possible errors, not minimal checks.

---

## Graph Types & Validation Requirements

### 1. Model Composition Graph (MCG) Validation

#### 1.1 Cycle Detection
```python
def validate_mcg_no_cycles(mcg: ModelCompositionGraph) -> List[ValidationError]:
    """Detect circular model relationships."""
    errors = []

    # Example:
    # ModelA → ModelB → ModelC → ModelA (CYCLE!)

    for model in mcg.nodes:
        visited = set()
        rec_stack = set()

        if has_cycle(model, visited, rec_stack):
            errors.append(
                MCGError(
                    code="CYCLE_DETECTED",
                    model=model,
                    message=f"Model {model} is part of circular dependency"
                )
            )

    return errors
```

#### 1.2 Type Validation
```python
def validate_mcg_types(mcg: ModelCompositionGraph) -> List[ValidationError]:
    """Validate field types are resolvable."""
    errors = []

    for model in mcg.nodes:
        for field_name, field_type in model.fields.items():
            # Check if type is built-in or registered model
            if not is_resolvable_type(field_type):
                errors.append(
                    MCGError(
                        code="UNRESOLVABLE_TYPE",
                        model=model,
                        field=field_name,
                        type=field_type,
                        message=f"Field {field_name} has unresolvable type {field_type}"
                    )
                )

            # Check if reference is to another model
            if isinstance(field_type, ModelReference):
                if not mcg.has_model(field_type.name):
                    errors.append(
                        MCGError(
                            code="MISSING_MODEL_REFERENCE",
                            model=model,
                            field=field_name,
                            referenced_model=field_type.name,
                            message=f"Field {field_name} references non-existent model {field_type.name}"
                        )
                    )

    return errors
```

#### 1.3 Naming Validation
```python
def validate_mcg_names(mcg: ModelCompositionGraph) -> List[ValidationError]:
    """Validate model names follow conventions."""
    errors = []

    for model in mcg.nodes:
        # Check naming conventions
        if not model.name[0].isupper():
            errors.append(
                MCGError(
                    code="INVALID_NAME_FORMAT",
                    model=model,
                    message=f"Model name must start with uppercase: {model.name}"
                )
            )

        # Check for special characters
        if not model.name.replace("_", "").isalnum():
            errors.append(
                MCGError(
                    code="INVALID_NAME_CHARACTERS",
                    model=model,
                    message=f"Model name contains invalid characters: {model.name}"
                )
            )

        # Check for reserved words
        if is_reserved_word(model.name):
            errors.append(
                MCGError(
                    code="RESERVED_NAME",
                    model=model,
                    message=f"Model name {model.name} is reserved"
                )
            )

    return errors
```

#### 1.4 Schema Validation
```python
def validate_mcg_schema(mcg: ModelCompositionGraph) -> List[ValidationError]:
    """Validate model schema completeness."""
    errors = []

    for model in mcg.nodes:
        # Every model needs MongoDB collection name
        if not hasattr(model, "collection_name"):
            errors.append(
                MCGError(
                    code="MISSING_COLLECTION_NAME",
                    model=model,
                    message=f"Model {model.name} missing collection name in Settings"
                )
            )

        # Every model needs primary key
        if not model.has_primary_key():
            errors.append(
                MCGError(
                    code="MISSING_PRIMARY_KEY",
                    model=model,
                    message=f"Model {model.name} missing primary key (should inherit from Document)"
                )
            )

        # Check all required fields have descriptions
        for field_name, field in model.fields.items():
            if not field.description:
                errors.append(
                    MCGError(
                        code="MISSING_FIELD_DESCRIPTION",
                        model=model,
                        field=field_name,
                        message=f"Field {model.name}.{field_name} missing description"
                    )
                )

    return errors
```

---

### 2. Operation Hierarchy Graph (OHG) Validation

#### 2.1 Cycle Detection
```python
def validate_ohg_no_cycles(ohg: OperationHierarchyGraph) -> List[ValidationError]:
    """Detect circular operation dependencies."""
    errors = []

    # Example:
    # pipeline.fetch → pipeline.transform → pipeline.load → pipeline.fetch (CYCLE!)

    for operation in ohg.nodes:
        if has_circular_dependency(operation, ohg):
            errors.append(
                OHGError(
                    code="CIRCULAR_DEPENDENCY",
                    operation=operation,
                    message=f"Operation {operation.name} is part of circular dependency"
                )
            )

    return errors
```

#### 2.2 Naming Validation
```python
def validate_ohg_names(ohg: OperationHierarchyGraph) -> List[ValidationError]:
    """Validate operation names follow conventions."""
    errors = []

    for operation in ohg.nodes:
        # Must use hierarchical naming (domain.category.operation)
        parts = operation.name.split(".")
        if len(parts) < 2:
            errors.append(
                OHGError(
                    code="NON_HIERARCHICAL_NAME",
                    operation=operation,
                    message=f"Operation must use hierarchical naming (domain.category.operation): {operation.name}"
                )
            )

        # Each part must be valid identifier
        for part in parts:
            if not part.isidentifier():
                errors.append(
                    OHGError(
                        code="INVALID_NAME_PART",
                        operation=operation,
                        message=f"Operation name part '{part}' is not valid identifier"
                    )
                )

            # No uppercase letters (convention)
            if part != part.lower():
                errors.append(
                    OHGError(
                        code="UPPERCASE_IN_NAME",
                        operation=operation,
                        message=f"Operation name should use lowercase: {operation.name}"
                    )
                )

        # Check for duplicate names
        # (handled in uniqueness check below)

    return errors
```

#### 2.3 Containment Validation
```python
def validate_ohg_containment(ohg: OperationHierarchyGraph) -> List[ValidationError]:
    """Validate operation hierarchy structure."""
    errors = []

    # Check that parent operations exist if referencing hierarchy
    for operation in ohg.nodes:
        parts = operation.name.split(".")
        if len(parts) > 1:
            parent_name = ".".join(parts[:-1])
            if not ohg.has_operation(parent_name):
                # Parent operation doesn't exist - this is OK if it's implicit
                # but should warn if it's referenced
                pass

    # Check that child operations are contained in parent
    for parent in ohg.nodes:
        for child in ohg.children(parent):
            # Check naming hierarchy
            if not child.name.startswith(parent.name + "."):
                errors.append(
                    OHGError(
                        code="CONTAINMENT_VIOLATION",
                        operation=child,
                        parent=parent,
                        message=f"Child {child.name} not properly contained in parent {parent.name}"
                    )
                )

    return errors
```

#### 2.4 Type Signature Validation
```python
def validate_ohg_signatures(ohg: OperationHierarchyGraph) -> List[ValidationError]:
    """Validate operation input/output types."""
    errors = []

    for operation in ohg.nodes:
        # Check input model exists
        if operation.inputs and not is_valid_type(operation.inputs):
            errors.append(
                OHGError(
                    code="INVALID_INPUT_TYPE",
                    operation=operation,
                    message=f"Operation {operation.name} has invalid input type {operation.inputs}"
                )
            )

        # Check output model exists
        if operation.outputs and not is_valid_type(operation.outputs):
            errors.append(
                OHGError(
                    code="INVALID_OUTPUT_TYPE",
                    operation=operation,
                    message=f"Operation {operation.name} has invalid output type {operation.outputs}"
                )
            )

        # If operation is async, inputs/outputs must be serializable
        if operation.is_async:
            if not is_serializable(operation.inputs):
                errors.append(
                    OHGError(
                        code="UNSERIALIZABLE_INPUT",
                        operation=operation,
                        message=f"Operation {operation.name} input type not serializable for async"
                    )
                )

    return errors
```

#### 2.5 Uniqueness Validation
```python
def validate_ohg_uniqueness(ohg: OperationHierarchyGraph) -> List[ValidationError]:
    """Validate no duplicate operation names."""
    errors = []

    seen = {}
    for operation in ohg.nodes:
        if operation.name in seen:
            errors.append(
                OHGError(
                    code="DUPLICATE_OPERATION",
                    operation=operation,
                    previous=seen[operation.name],
                    message=f"Duplicate operation name: {operation.name}"
                )
            )
        seen[operation.name] = operation

    return errors
```

---

### 3. Data Flow Graph (DFG) Validation

#### 3.1 Model Reference Validation
```python
def validate_dfg_references(dfg: DataFlowGraph) -> List[ValidationError]:
    """Validate all model references exist."""
    errors = []

    for node in dfg.nodes:
        # Check model references in operations
        if hasattr(node, "models_in"):
            for model_name in node.models_in:
                if not ModelRegistry.has_model(model_name):
                    errors.append(
                        DFGError(
                            code="MISSING_INPUT_MODEL",
                            operation=node,
                            model=model_name,
                            message=f"Operation {node.name} references non-existent input model {model_name}"
                        )
                    )

        if hasattr(node, "models_out"):
            for model_name in node.models_out:
                if not ModelRegistry.has_model(model_name):
                    errors.append(
                        DFGError(
                            code="MISSING_OUTPUT_MODEL",
                            operation=node,
                            model=model_name,
                            message=f"Operation {node.name} references non-existent output model {model_name}"
                        )
                    )

    return errors
```

#### 3.2 Type Matching Validation
```python
def validate_dfg_type_matching(dfg: DataFlowGraph) -> List[ValidationError]:
    """Validate data types match between operations."""
    errors = []

    # For each edge (operation producing data → operation consuming it)
    for edge in dfg.edges:
        source_op = edge.source
        target_op = edge.target

        # Check if output types match input types
        if source_op.output_type != target_op.input_type:
            errors.append(
                DFGError(
                    code="TYPE_MISMATCH",
                    source_operation=source_op,
                    target_operation=target_op,
                    source_type=source_op.output_type,
                    target_type=target_op.input_type,
                    message=f"Data type mismatch: {source_op.name} outputs {source_op.output_type} "
                           f"but {target_op.name} expects {target_op.input_type}"
                )
            )

    return errors
```

#### 3.3 Data Lineage Validation
```python
def validate_dfg_lineage(dfg: DataFlowGraph) -> List[ValidationError]:
    """Validate data lineage and provenance."""
    errors = []

    for model in dfg.data_nodes:
        # Check that model has at least one producer (unless source data)
        producers = dfg.producers(model)
        if not producers and not model.is_source:
            errors.append(
                DFGError(
                    code="NO_PRODUCER",
                    model=model,
                    message=f"Model {model.name} has no producer operation"
                )
            )

        # Check that model has at least one consumer (unless sink data)
        consumers = dfg.consumers(model)
        if not consumers and not model.is_sink:
            errors.append(
                DFGError(
                    code="NO_CONSUMER",
                    model=model,
                    message=f"Model {model.name} has no consumer operation (dead data)"
                )
            )

    return errors
```

#### 3.4 Transformation Validation
```python
def validate_dfg_transformations(dfg: DataFlowGraph) -> List[ValidationError]:
    """Validate data transformations are valid."""
    errors = []

    for edge in dfg.edges:
        source_op = edge.source
        target_op = edge.target

        # Check that field mappings are valid
        if hasattr(edge, "field_mapping"):
            for source_field, target_field in edge.field_mapping.items():
                # Verify source field exists
                if not source_op.has_output_field(source_field):
                    errors.append(
                        DFGError(
                            code="INVALID_SOURCE_FIELD",
                            operation=source_op,
                            field=source_field,
                            message=f"Operation {source_op.name} doesn't output field {source_field}"
                        )
                    )

                # Verify target field exists
                if not target_op.has_input_field(target_field):
                    errors.append(
                        DFGError(
                            code="INVALID_TARGET_FIELD",
                            operation=target_op,
                            field=target_field,
                            message=f"Operation {target_op.name} doesn't accept field {target_field}"
                        )
                    )

    return errors
```

---

## Complete Validation Pipeline

### Validation Order

```python
class GraphValidator:
    def validate_all(self, project) -> ValidationReport:
        """Run all validations in order."""

        report = ValidationReport()

        # 1. MCG Validation
        mcg = project.build_mcg()
        report.add(self.validate_mcg(mcg))

        # 2. OHG Validation
        ohg = project.build_ohg()
        report.add(self.validate_ohg(ohg))

        # 3. DFG Validation
        dfg = project.build_dfg()
        report.add(self.validate_dfg(dfg))

        # 4. Cross-Graph Validation
        report.add(self.validate_cross_graphs(mcg, ohg, dfg))

        return report

    def validate_mcg(self, mcg) -> List[ValidationError]:
        errors = []
        errors.extend(validate_mcg_no_cycles(mcg))
        errors.extend(validate_mcg_types(mcg))
        errors.extend(validate_mcg_names(mcg))
        errors.extend(validate_mcg_schema(mcg))
        return errors

    def validate_ohg(self, ohg) -> List[ValidationError]:
        errors = []
        errors.extend(validate_ohg_no_cycles(ohg))
        errors.extend(validate_ohg_names(ohg))
        errors.extend(validate_ohg_containment(ohg))
        errors.extend(validate_ohg_signatures(ohg))
        errors.extend(validate_ohg_uniqueness(ohg))
        return errors

    def validate_dfg(self, dfg) -> List[ValidationError]:
        errors = []
        errors.extend(validate_dfg_references(dfg))
        errors.extend(validate_dfg_type_matching(dfg))
        errors.extend(validate_dfg_lineage(dfg))
        errors.extend(validate_dfg_transformations(dfg))
        return errors

    def validate_cross_graphs(self, mcg, ohg, dfg) -> List[ValidationError]:
        """Cross-graph validation."""
        errors = []

        # Operations reference models that exist
        for op in ohg.nodes:
            for model_name in op.models_in + op.models_out:
                if not mcg.has_model(model_name):
                    errors.append(...)

        # All operations in DFG have OHG nodes
        for node in dfg.operation_nodes:
            if not ohg.has_operation(node.name):
                errors.append(...)

        return errors
```

---

## Validation Error Types

```python
@dataclass
class ValidationError:
    code: str                    # Error code (e.g., "CYCLE_DETECTED")
    graph_type: str             # "MCG", "OHG", or "DFG"
    severity: str               # "ERROR" or "WARNING"
    message: str                # Human-readable message
    context: Dict[str, Any]     # Error context (model, field, etc.)
    suggestion: str             # How to fix it

# Examples:
errors = [
    ValidationError(
        code="CYCLE_DETECTED",
        graph_type="MCG",
        severity="ERROR",
        message="Model A references B, B references C, C references A",
        context={"models": ["A", "B", "C"]},
        suggestion="Remove one relationship to break the cycle"
    ),
    ValidationError(
        code="NON_HIERARCHICAL_NAME",
        graph_type="OHG",
        severity="ERROR",
        message="Operation 'catch_pokemon' should use hierarchical naming",
        context={"operation": "catch_pokemon"},
        suggestion="Rename to 'pokemon.management.catch'"
    ),
    ValidationError(
        code="MISSING_MODEL_REFERENCE",
        graph_type="DFG",
        severity="ERROR",
        message="Operation 'process' outputs to non-existent model 'Result'",
        context={"operation": "process", "model": "Result"},
        suggestion="Create @datamodel(name='Result') or remove reference"
    ),
]
```

---

## Testing Validation

```python
def test_mcg_cycle_detection():
    """Test MCG detects circular relationships."""
    mcg = ModelCompositionGraph()
    mcg.add_model("A")
    mcg.add_model("B")
    mcg.add_model("C")
    mcg.add_edge("A", "B")  # A → B
    mcg.add_edge("B", "C")  # B → C
    mcg.add_edge("C", "A")  # C → A (cycle!)

    errors = validate_mcg_no_cycles(mcg)
    assert len(errors) == 3  # One for each node in cycle

def test_ohg_hierarchical_naming():
    """Test OHG enforces hierarchical naming."""
    ohg = OperationHierarchyGraph()

    # Invalid: flat naming
    ohg.add_operation("catch_pokemon")

    errors = validate_ohg_names(ohg)
    assert any(e.code == "NON_HIERARCHICAL_NAME" for e in errors)

def test_dfg_type_matching():
    """Test DFG validates type consistency."""
    dfg = DataFlowGraph()
    dfg.add_operation("source", output_type="int")
    dfg.add_operation("sink", input_type="str")
    dfg.add_edge("source", "sink")

    errors = validate_dfg_type_matching(dfg)
    assert any(e.code == "TYPE_MISMATCH" for e in errors)
```

---

## Implementation Checklist

- [ ] Create `core/validators/mcg_validator.py` with all MCG checks
- [ ] Create `core/validators/ohg_validator.py` with all OHG checks
- [ ] Create `core/validators/dfg_validator.py` with all DFG checks
- [ ] Create `core/validators/cross_graph_validator.py` for multi-graph validation
- [ ] Create `ValidationError` dataclass with all fields
- [ ] Create `ValidationReport` class for collecting errors
- [ ] Add validation to compile pipeline (pre-generation check)
- [ ] Add validation to lint command (CLI tool)
- [ ] Create comprehensive test suite for all validations
- [ ] Document all error codes and fixes

---

## CLI Integration

```bash
# Check for validation errors
pulpo lint
# Output:
# ❌ CYCLE_DETECTED in MCG: Model A → B → C → A
# ❌ NON_HIERARCHICAL_NAME in OHG: "catch_pokemon" should be "pokemon.management.catch"
# ⚠️  MISSING_FIELD_DESCRIPTION in MCG: Pokemon.health missing description
# ✅ All validations passed!

# Compile only if validation passes
pulpo compile  # Fails if validation errors present
```

---

## Next Phase: Docker Integration Testing

Once graphs are validated, Docker-based tests will verify actual execution.

See: **DOCKER_INTEGRATION_TESTING_STRATEGY.md**

---
