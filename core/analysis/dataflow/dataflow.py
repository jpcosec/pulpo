"""
Data Flow Analyzer for Pulpo Operations

Analyzes the data flowing between operations to automatically detect:
- Operation dependencies (implicit in data flow)
- Parallelizable groups (operations with same inputs/outputs)
- Execution order (topological sort)

Core principle: Operation flow is implicit in data flow.
- If Operation B inputs what Operation A outputs, then B depends on A
- If multiple operations output the same data, they can run in parallel
"""

from typing import Any, Optional
from dataclasses import dataclass, field

from ..registries import OperationMetadata as RegistryOperationMetadata


@dataclass
class DataModel:
    """Represents a data model used by operations."""

    name: str
    """Name of the data model."""

    @property
    def qualified_name(self) -> str:
        """Return qualified name for comparison."""
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, DataModel):
            return self.name == other.name
        return self.name == other


class OperationMetadata:
    """Metadata about an operation for data flow analysis.

    Wraps registry.OperationMetadata to provide data flow analysis methods.
    """

    def __init__(self, op: RegistryOperationMetadata):
        """Initialize from registry metadata."""
        self.name = op.name
        self.inputs = op.models_in  # Input data models
        self.outputs = op.models_out  # Output data models
        self._registry_meta = op

    @property
    def has_inputs(self) -> bool:
        """Whether operation accepts inputs."""
        return len(self.inputs) > 0

    @property
    def has_outputs(self) -> bool:
        """Whether operation produces outputs."""
        return len(self.outputs) > 0

    def can_run_parallel_with(self, other: "OperationMetadata") -> bool:
        """Check if this operation can run in parallel with another.

        Two operations can run in parallel if they:
        1. Have the same inputs (consume same data)
        2. Have the same outputs (produce same data)
        3. Have no dependency relationship
        """
        return (
            set(self.inputs) == set(other.inputs)
            and set(self.outputs) == set(other.outputs)
        )


@dataclass
class DependencyEdge:
    """Represents a dependency relationship between operations."""

    source: str
    """Operation that produces data."""

    target: str
    """Operation that consumes data."""

    data_models: list[str] = field(default_factory=list)
    """Data models transmitted along this edge."""

    @property
    def is_valid(self) -> bool:
        """Whether edge is valid (has at least one data model)."""
        return len(self.data_models) > 0


class DataFlowGraph:
    """Represents the dependency graph of operations."""

    def __init__(self):
        """Initialize empty graph."""
        self.operations: dict[str, OperationMetadata] = {}
        self.edges: list[DependencyEdge] = []
        self._adjacency: dict[str, list[str]] = {}  # op_name -> [depends_on]
        self._reverse_adjacency: dict[str, list[str]] = {}  # op_name -> [dependents]

    def add_operation(self, metadata: OperationMetadata) -> None:
        """Add operation to graph."""
        self.operations[metadata.name] = metadata
        if metadata.name not in self._adjacency:
            self._adjacency[metadata.name] = []
        if metadata.name not in self._reverse_adjacency:
            self._reverse_adjacency[metadata.name] = []

    def add_dependency(self, source: str, target: str, data_models: list[str]) -> None:
        """Add dependency: target depends on source via data_models."""
        edge = DependencyEdge(source=source, target=target, data_models=data_models)
        self.edges.append(edge)

        # Update adjacency lists
        if source not in self._adjacency:
            self._adjacency[source] = []
        if target not in self._adjacency:
            self._adjacency[target] = []
        if source not in self._reverse_adjacency:
            self._reverse_adjacency[source] = []
        if target not in self._reverse_adjacency:
            self._reverse_adjacency[target] = []

        self._adjacency[target].append(source)
        self._reverse_adjacency[source].append(target)

    def get_dependencies(self, op_name: str) -> list[str]:
        """Get operations that must run before this one."""
        return self._adjacency.get(op_name, [])

    def get_dependents(self, op_name: str) -> list[str]:
        """Get operations that depend on this one."""
        return self._reverse_adjacency.get(op_name, [])

    def has_cycle(self) -> bool:
        """Check if graph has cycles (would be invalid)."""
        visited = set()
        rec_stack = set()

        def has_cycle_util(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    if has_cycle_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.operations:
            if node not in visited:
                if has_cycle_util(node):
                    return True

        return False

    def topological_sort(self) -> list[str]:
        """Return operations in topological order (respecting dependencies)."""
        if self.has_cycle():
            raise ValueError("Circular dependency detected in operation graph")

        visited = set()
        result = []

        def visit(node):
            if node in visited:
                return
            visited.add(node)

            # Visit dependencies first
            for dep in self.get_dependencies(node):
                visit(dep)

            result.append(node)

        # Visit all nodes
        for node in self.operations:
            visit(node)

        return result

    def find_parallel_groups(self) -> list[list[str]]:
        """Find groups of operations that can run in parallel.

        Returns list of groups. Each group can run in parallel.
        Groups are in dependency order (earlier groups have no dependencies).
        """
        # Group by execution level (topological distance from start)
        levels = {}
        visited = set()

        def get_level(op_name):
            if op_name in levels:
                return levels[op_name]

            deps = self.get_dependencies(op_name)
            if not deps:
                levels[op_name] = 0
            else:
                levels[op_name] = max(get_level(d) for d in deps) + 1

            return levels[op_name]

        # Calculate levels for all operations
        for op_name in self.operations:
            get_level(op_name)

        # Group by level
        level_groups = {}
        for op_name, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(op_name)

        # Return groups sorted by level
        return [level_groups[level] for level in sorted(level_groups.keys())]


class DataFlowAnalyzer:
    """Analyzes data flow between operations to detect dependencies."""

    @staticmethod
    def build_dependency_graph(
        operations: list[OperationMetadata],
    ) -> DataFlowGraph:
        """Build dependency graph from operations.

        Args:
            operations: List of operation metadata

        Returns:
            DataFlowGraph representing dependencies
        """
        graph = DataFlowGraph()

        # Add all operations to graph
        for op in operations:
            graph.add_operation(op)

        # Build output -> operations mapping
        output_producers: dict[str, list[str]] = {}
        for op in operations:
            for output in op.outputs:
                if output not in output_producers:
                    output_producers[output] = []
                output_producers[output].append(op.name)

        # For each operation, find what it depends on
        for op in operations:
            for input_model in op.inputs:
                # Find operations that output this input
                producers = output_producers.get(input_model, [])

                for producer_name in producers:
                    # Skip self-loops (operation transforming same data model)
                    if producer_name == op.name:
                        continue

                    # Add dependency: op depends on producer
                    graph.add_dependency(
                        source=producer_name,
                        target=op.name,
                        data_models=[input_model],
                    )

        return graph

    @staticmethod
    def find_parallel_groups(operations: list[OperationMetadata]) -> list[list[str]]:
        """Find groups of operations that can run in parallel.

        Operations can run in parallel if:
        1. They have the same inputs
        2. They have the same outputs
        3. No other dependencies prevent it

        Args:
            operations: List of operation metadata

        Returns:
            List of groups (each group can run in parallel)
        """
        graph = DataFlowAnalyzer.build_dependency_graph(operations)
        return graph.find_parallel_groups()

    @staticmethod
    def topological_sort(operations: list[OperationMetadata]) -> list[str]:
        """Return operation names in execution order.

        Args:
            operations: List of operation metadata

        Returns:
            List of operation names in topological order

        Raises:
            ValueError: If circular dependency detected
        """
        graph = DataFlowAnalyzer.build_dependency_graph(operations)
        return graph.topological_sort()

    @staticmethod
    def validate_dataflow(operations: list[OperationMetadata]) -> tuple[bool, str]:
        """Validate that data flow is acyclic and consistent.

        Args:
            operations: List of operation metadata

        Returns:
            Tuple of (is_valid, error_message)
        """
        graph = DataFlowAnalyzer.build_dependency_graph(operations)

        if graph.has_cycle():
            return False, "Circular dependency detected in operation graph"

        return True, ""

    @staticmethod
    def analyze(operations: list[OperationMetadata]) -> dict:
        """Comprehensive analysis of data flow.

        Args:
            operations: List of operation metadata

        Returns:
            Dictionary with analysis results
        """
        graph = DataFlowAnalyzer.build_dependency_graph(operations)
        is_valid, error = DataFlowAnalyzer.validate_dataflow(operations)

        return {
            "is_valid": is_valid,
            "error": error if not is_valid else None,
            "graph": graph,
            "execution_order": graph.topological_sort() if is_valid else [],
            "parallel_groups": graph.find_parallel_groups() if is_valid else [],
            "total_operations": len(operations),
            "dependencies": {
                op.name: graph.get_dependencies(op.name) for op in operations
            },
        }
