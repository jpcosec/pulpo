"""Generation module - Phase 2: Graph → Code.

This module handles:
- init: CLI generation, config files, graph visualization
- compile: Full code generation (API, UI, workflows, Docker)
"""

from .codegen import compile_all

__all__ = [
    "compile_all",
]
