"""Type definitions for registry graph."""

from typing import Literal

NodeType = Literal["datamodel", "task", "flow"]
EdgeType = Literal[
    # DataModel ↔ DataModel
    "HAS_RELATION", "CONTAINS_LIST", "INHERITS_FROM",
    # Task → DataModel
    "READS", "WRITES", "DELETES",
    # Task → Task
    "DEPENDS_ON", "RUNS_PARALLEL",
    # Flow → Flow
    "CONTAINS_SUBFLOW",
    # Flow → Task
    "CONTAINS_TASK"
]
