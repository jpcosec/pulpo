"""Analysis module - Phase 1: Code → Graph.

This module handles:
- Decorator discovery (@datamodel, @operation)
- Registry management (ModelRegistry, OperationRegistry)
- Graph generation (Mermaid visualization)
- Dataflow analysis
- Validation and linting
"""

from .decorators import datamodel, operation
from .registries import ModelRegistry, OperationRegistry

__all__ = [
    "datamodel",
    "operation",
    "ModelRegistry",
    "OperationRegistry",
]
