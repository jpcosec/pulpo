"""
Orchestration Compiler for Pulpo

Compiles operations into Prefect flow definitions based on hierarchical structure
and data flow dependencies.

Architecture:
1. Parse all operations and their data models
2. Build dependency graph from data flow
3. Group operations by hierarchical parent
4. Detect parallel execution groups
5. Create flow definitions (one per hierarchy level)
"""

from dataclasses import dataclass, field
from typing import Optional

from .dataflow import DataFlowAnalyzer, DataFlowGraph, OperationMetadata


@dataclass
class FlowDefinition:
    """Definition of a Prefect flow to be generated."""

    name: str
    """Flow name (e.g., "scraping_flow", "scraping_stepstone_flow")."""

    operations: list[str] = field(default_factory=list)
    """List of operation names in this flow."""

    hierarchy_path: str = ""
    """Hierarchy path defining this flow (e.g., "scraping.stepstone")."""

    hierarchy_level: int = 0
    """Depth in hierarchy (1 for root, 2 for first subflow, etc)."""

    is_standalone: bool = False
    """Whether this is a flow for standalone operations."""

    parallel_groups: list[list[str]] = field(default_factory=list)
    """Groups of operations that can run in parallel."""

    dependencies: dict[str, list[str]] = field(default_factory=dict)
    """op_name -> [depends_on] mapping."""

    @property
    def has_operations(self) -> bool:
        """Whether flow contains any operations."""
        return len(self.operations) > 0

    @property
    def can_execute(self) -> bool:
        """Whether flow can be executed (has operations and valid structure)."""
        return self.has_operations and not self._has_circular_dependencies()

    def _has_circular_dependencies(self) -> bool:
        """Check if this flow's operations have circular dependencies."""
        # Build adjacency for operations in this flow only
        adj = {op: [] for op in self.operations}
        for op, deps in self.dependencies.items():
            if op in adj:
                adj[op] = [d for d in deps if d in self.operations]

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in adj:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False


@dataclass
class Orchestration:
    """Complete orchestration of all flows."""

    flows: list[FlowDefinition] = field(default_factory=list)
    """All flow definitions."""

    graph: Optional[DataFlowGraph] = None
    """Data flow graph for reference."""

    operation_metadata: dict[str, OperationMetadata] = field(default_factory=dict)
    """Metadata for all operations."""

    @property
    def total_operations(self) -> int:
        """Total number of operations across all flows."""
        return len(self.operation_metadata)

    @property
    def total_flows(self) -> int:
        """Total number of flows to generate."""
        return len(self.flows)

    @property
    def is_valid(self) -> bool:
        """Whether orchestration is valid (all flows can execute)."""
        return all(flow.can_execute for flow in self.flows)

    def get_flow(self, name: str) -> Optional[FlowDefinition]:
        """Get flow by name."""
        for flow in self.flows:
            if flow.name == name:
                return flow
        return None

    def get_flows_for_hierarchy(self, hierarchy_path: str) -> list[FlowDefinition]:
        """Get all flows in a hierarchy (including subflows)."""
        return [f for f in self.flows if f.hierarchy_path.startswith(hierarchy_path)]


class OrchestrationCompiler:
    """Compiles operations into Prefect flows."""

    def __init__(self):
        """Initialize compiler."""
        self.operations: dict[str, OperationMetadata] = {}

    def compile(
        self, operations: list[OperationMetadata]
    ) -> Orchestration:
        """Compile operations into flow definitions.

        Args:
            operations: List of operation metadata

        Returns:
            Orchestration with flow definitions

        Raises:
            ValueError: If invalid structure detected
        """
        self.operations = {op.name: op for op in operations}

        # Validate data flow
        is_valid, error = DataFlowAnalyzer.validate_dataflow(operations)
        if not is_valid:
            raise ValueError(f"Invalid data flow: {error}")

        # Build dependency graph
        graph = DataFlowAnalyzer.build_dependency_graph(operations)

        # Group operations by hierarchy
        flows = self._create_flows(operations, graph)

        return Orchestration(
            flows=flows, graph=graph, operation_metadata=self.operations
        )

    def _create_flows(
        self, operations: list[OperationMetadata], graph: DataFlowGraph
    ) -> list[FlowDefinition]:
        """Create flow definitions from operations and data flow graph.

        Strategy:
        1. Group operations by their immediate parent (hierarchy level)
        2. Create one flow definition per unique parent
        3. Group standalones into a single standalones_flow
        4. Detect parallel groups within each flow
        """
        from ..hierarchy import HierarchyParser

        # Group operations by parent
        grouped = HierarchyParser.group_by_parent([op.name for op in operations])

        flows = []

        # Process grouped operations
        for parent, op_names in grouped.items():
            if parent is None:
                # Standalones
                flow = self._create_standalone_flow(op_names, graph)
            else:
                # Grouped by parent
                flow = self._create_parent_flow(parent, op_names, graph)

            if flow:
                flows.append(flow)

        return flows

    def _create_parent_flow(
        self,
        parent: str,
        op_names: list[str],
        graph: DataFlowGraph,
    ) -> FlowDefinition:
        """Create flow for operations under a parent.

        Args:
            parent: Parent hierarchy path (e.g., "scraping.stepstone")
            op_names: List of operation names in this parent
            graph: Data flow graph

        Returns:
            FlowDefinition for this parent
        """
        from ..hierarchy import HierarchyParser

        # Create flow name from parent
        # "scraping.stepstone" -> "scraping_stepstone_flow"
        flow_name = parent.replace(".", "_") + "_flow"
        hierarchy_level = HierarchyParser.get_level(parent)

        # Detect parallel groups
        op_metadata = [self.operations[op] for op in op_names]
        parallel_groups = self._find_parallel_groups_in_flow(op_metadata, graph)

        # Build dependencies for operations in this flow
        dependencies = {}
        for op in op_names:
            deps = graph.get_dependencies(op)
            # Only include dependencies within this flow
            internal_deps = [d for d in deps if d in op_names]
            dependencies[op] = internal_deps

        return FlowDefinition(
            name=flow_name,
            operations=op_names,
            hierarchy_path=parent,
            hierarchy_level=hierarchy_level,
            is_standalone=False,
            parallel_groups=parallel_groups,
            dependencies=dependencies,
        )

    def _create_standalone_flow(
        self,
        op_names: list[str],
        graph: DataFlowGraph,
    ) -> FlowDefinition:
        """Create flow for standalone operations (no parent).

        Args:
            op_names: List of standalone operation names
            graph: Data flow graph

        Returns:
            FlowDefinition for standalones
        """
        # Detect parallel groups
        op_metadata = [self.operations[op] for op in op_names]
        parallel_groups = self._find_parallel_groups_in_flow(op_metadata, graph)

        # Build dependencies
        dependencies = {}
        for op in op_names:
            deps = graph.get_dependencies(op)
            # Only include dependencies within standalones
            internal_deps = [d for d in deps if d in op_names]
            dependencies[op] = internal_deps

        return FlowDefinition(
            name="standalones_flow",
            operations=op_names,
            hierarchy_path="",
            hierarchy_level=0,
            is_standalone=True,
            parallel_groups=parallel_groups,
            dependencies=dependencies,
        )

    def _find_parallel_groups_in_flow(
        self,
        op_metadata: list[OperationMetadata],
        graph: DataFlowGraph,
    ) -> list[list[str]]:
        """Find parallel execution groups within a flow.

        Operations in the same flow that have:
        1. Same input data models
        2. Same output data models
        3. No dependencies on each other

        Args:
            op_metadata: Operations in the flow
            graph: Data flow graph

        Returns:
            List of parallel groups (each group can run in parallel)
        """
        op_names = [op.name for op in op_metadata]
        if len(op_names) <= 1:
            return [[op] for op in op_names]

        # Find operations that can run in parallel
        groups = []
        used = set()

        for i, op1 in enumerate(op_metadata):
            if op1.name in used:
                continue

            group = [op1.name]
            used.add(op1.name)

            # Find all operations that can run parallel with op1
            for op2 in op_metadata[i + 1 :]:
                if op2.name in used:
                    continue

                if op1.can_run_parallel_with(op2):
                    group.append(op2.name)
                    used.add(op2.name)

            groups.append(group)

        return groups

    def compile_to_flows(
        self, operations: list[OperationMetadata]
    ) -> dict[str, FlowDefinition]:
        """Compile operations to a dict of flow definitions.

        Args:
            operations: List of operation metadata

        Returns:
            Dictionary mapping flow name to FlowDefinition
        """
        orchestration = self.compile(operations)
        return {flow.name: flow for flow in orchestration.flows}
