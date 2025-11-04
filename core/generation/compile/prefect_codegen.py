"""
Prefect Code Generator for Pulpo

Generates Prefect @flow and @task decorators from flow definitions.

Produces valid Python code that:
1. Defines tasks for each operation
2. Creates flows that orchestrate tasks
3. Handles parallel execution via asyncio.gather
4. Manages dependencies via data flow
"""

from textwrap import indent
from typing import Optional

from .compiler import FlowDefinition, Orchestration


class PrefectCodeGenerator:
    """Generates Prefect flow code from flow definitions."""

    # Indentation level (in spaces)
    INDENT = 4

    def __init__(self, operation_import_path: str = "run_cache.operations"):
        """Initialize code generator.

        Args:
            operation_import_path: Import path for operations
                (e.g., "run_cache.operations" or "user_project.operations")
        """
        self.operation_import_path = operation_import_path

    def generate_all_flows(self, orchestration: Orchestration) -> dict[str, str]:
        """Generate code for all flows in orchestration.

        Args:
            orchestration: Complete orchestration

        Returns:
            Dictionary mapping flow_name to generated code
        """
        result = {}

        for flow_def in orchestration.flows:
            code = self.generate_flow(flow_def, orchestration)
            result[flow_def.name] = code

        return result

    def generate_flow(
        self,
        flow_def: FlowDefinition,
        orchestration: Orchestration,
    ) -> str:
        """Generate code for a single flow.

        Args:
            flow_def: Flow definition
            orchestration: Parent orchestration (for operation metadata)

        Returns:
            Generated Python code
        """
        if not flow_def.has_operations:
            return self._generate_empty_flow(flow_def)

        # Generate imports
        imports = self._generate_imports(flow_def, orchestration)

        # Generate task definitions
        tasks = self._generate_tasks(flow_def, orchestration)

        # Generate flow definition
        flow = self._generate_flow_definition(flow_def, orchestration)

        # Generate main block
        main = self._generate_main_block(flow_def)

        # Combine all sections
        sections = [imports, "", tasks, "", flow, "", main]
        code = "\n".join(section for section in sections if section)

        return code

    def _generate_imports(
        self,
        flow_def: FlowDefinition,
        orchestration: Orchestration,
    ) -> str:
        """Generate import statements.

        Args:
            flow_def: Flow definition
            orchestration: Orchestration

        Returns:
            Import statements as string
        """
        lines = [
            '"""Auto-generated Prefect flow for operations."""',
            "",
            "import asyncio",
            "from prefect import flow, task",
            "from core.analysis.registries import OperationRegistry",
        ]

        return "\n".join(lines)

    def _generate_tasks(
        self,
        flow_def: FlowDefinition,
        orchestration: Orchestration,
    ) -> str:
        """Generate @task definitions for operations.

        Args:
            flow_def: Flow definition
            orchestration: Orchestration

        Returns:
            Task definitions as string
        """
        tasks = []

        for op_name in flow_def.operations:
            op_metadata = orchestration.operation_metadata.get(op_name)
            if not op_metadata:
                continue

            # Generate task name (operation.name.with.dots -> operation_name_with_dots_task)
            task_name = op_name.replace(".", "_") + "_task"

            # Generate task signature
            params = ", ".join(op_metadata.inputs) if op_metadata.inputs else ""
            return_type = "dict"  # Simplified: assume all operations return dict

            if op_metadata.inputs:
                sig = f"async def {task_name}({params}) -> {return_type}:"
            else:
                sig = f"async def {task_name}() -> {return_type}:"

            # Generate task body
            docstring = self._indent(f'"""Wrapped task for {op_name}."""')
            lines = [
                "@task",
                sig,
                docstring,
            ]

            # Call the operation via registry
            call_args = ", ".join(op_metadata.inputs) if op_metadata.inputs else ""
            operation_var = op_name.replace(".", "_")

            lines.append(self._indent(f'op = OperationRegistry.get("{op_name}")'))
            lines.append(self._indent(f'if not op or not op.function:'))
            lines.append(self._indent(f'    raise RuntimeError("Operation {op_name} not found in registry")'))

            if call_args:
                call = f"return await op.function({call_args})"
            else:
                call = f"return await op.function()"

            lines.append(self._indent(call))

            tasks.append("\n".join(lines))

        return "\n\n".join(tasks)

    def _generate_flow_definition(
        self,
        flow_def: FlowDefinition,
        orchestration: Orchestration,
    ) -> str:
        """Generate @flow definition.

        Args:
            flow_def: Flow definition
            orchestration: Orchestration

        Returns:
            Flow definition as string
        """
        # Build flow signature
        return_type = "dict"  # Simplified: assume flows return dict
        flow_sig = f"async def {flow_def.name}() -> {return_type}:"

        hierarchy_desc = flow_def.hierarchy_path or "standalone"
        flow_docstring = self._indent(f'"""Auto-generated flow for {hierarchy_desc} operations."""')
        lines = [
            "@flow",
            flow_sig,
            flow_docstring,
        ]

        # Generate flow body
        body = self._generate_flow_body(flow_def, orchestration)
        lines.append(self._indent(body))

        return "\n".join(lines)

    def _generate_flow_body(
        self,
        flow_def: FlowDefinition,
        orchestration: Orchestration,
    ) -> str:
        """Generate the body of a flow function.

        Handles:
        1. Parallel execution groups (asyncio.gather)
        2. Sequential dependencies (await task())
        3. Data passing between tasks

        Args:
            flow_def: Flow definition
            orchestration: Orchestration

        Returns:
            Flow body as string
        """
        lines = []

        if not flow_def.parallel_groups:
            # All operations are sequential
            for op_name in flow_def.operations:
                task_name = op_name.replace(".", "_") + "_task"
                lines.append(f"await {task_name}()")

            if lines:
                lines.append("return None")

            return "\n".join(lines)

        # Handle parallel groups
        var_names = {}  # op_name -> variable name to store result
        var_counter = 0

        for group in flow_def.parallel_groups:
            if len(group) == 1:
                # Single operation, execute directly
                op_name = group[0]
                task_name = op_name.replace(".", "_") + "_task"

                # Check if this operation has dependencies
                deps = flow_def.dependencies.get(op_name, [])
                internal_deps = [d for d in deps if d in flow_def.operations]

                if internal_deps:
                    # Has dependencies, pass results
                    dep_args = ", ".join(
                        var_names.get(d, d) for d in internal_deps
                    )
                    lines.append(f"{op_name}_result = await {task_name}({dep_args})")
                else:
                    # No dependencies
                    lines.append(f"{op_name}_result = await {task_name}()")

                var_names[op_name] = f"{op_name}_result"

            else:
                # Multiple operations in parallel
                task_calls = []
                for op_name in group:
                    task_name = op_name.replace(".", "_") + "_task"

                    # Check dependencies
                    deps = flow_def.dependencies.get(op_name, [])
                    internal_deps = [d for d in deps if d in flow_def.operations]

                    if internal_deps:
                        dep_args = ", ".join(
                            var_names.get(d, d) for d in internal_deps
                        )
                        task_calls.append(f"{task_name}({dep_args})")
                    else:
                        task_calls.append(f"{task_name}()")

                # Generate asyncio.gather call
                task_calls_str = ",\n".join(
                    self._indent(tc) for tc in task_calls
                )
                var_assignments = ", ".join(
                    f"{op}_result" for op in group
                )

                lines.append(f"{var_assignments} = await asyncio.gather(")
                lines.append(task_calls_str + ",")
                lines.append(")")

                # Store variable names
                for op_name in group:
                    var_names[op_name] = f"{op_name}_result"

        # Return the last result
        if var_names:
            last_op = flow_def.operations[-1]
            last_var = var_names.get(last_op, f"{last_op}_result")
            lines.append(f"return {last_var}")
        else:
            lines.append("return None")

        return "\n".join(lines)

    def _generate_main_block(self, flow_def: FlowDefinition) -> str:
        """Generate main block for testing.

        Args:
            flow_def: Flow definition

        Returns:
            Main block as string
        """
        return f'''if __name__ == "__main__":
{self._indent(f"{flow_def.name}()")}'''

    def _generate_empty_flow(self, flow_def: FlowDefinition) -> str:
        """Generate an empty flow (no operations).

        Args:
            flow_def: Flow definition

        Returns:
            Empty flow code
        """
        imports = [
            '"""Auto-generated empty Prefect flow."""',
            "",
            "from prefect import flow",
        ]

        empty_docstring = self._indent('"""Empty flow - no operations."""')
        flow_code = [
            "@flow",
            f"async def {flow_def.name}() -> None:",
            empty_docstring,
            self._indent("pass"),
        ]

        main = f'''if __name__ == "__main__":
{self._indent(f"{flow_def.name}()")}'''

        sections = ["\n".join(imports), "", "\n".join(flow_code), "", main]
        return "\n".join(section for section in sections if section)

    def _indent(self, text: str, level: int = 1) -> str:
        """Indent text by given level.

        Args:
            text: Text to indent
            level: Indentation level

        Returns:
            Indented text
        """
        return indent(text, " " * (self.INDENT * level))

    def generate_flow_registry(self, orchestration: Orchestration) -> str:
        """Generate a registry of all flows for easy importing.

        Args:
            orchestration: Complete orchestration

        Returns:
            Generated Python code for registry
        """
        flow_names = [flow.name for flow in orchestration.flows]

        imports = []
        for flow_name in flow_names:
            # Assume flows are in separate files or same file
            imports.append(f"from .{flow_name} import {flow_name}")

        exports = [f"    {flow_name}," for flow_name in flow_names]

        code = f'''"""Registry of all Prefect flows."""

{chr(10).join(imports)}

__all__ = [
{chr(10).join(exports)}
]

# Access flows by name
flows_by_name = {{
{chr(10).join(f'    "{name}": {name},' for name in flow_names)}
}}
'''

        return code
