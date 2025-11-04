"""
Pulpo Core Framework

A metadata-driven framework for auto-generating APIs, UIs, CLIs, and Prefect orchestration
from decorators.

Architecture:
- analysis/: Discovery, graph generation, validation (Phase 1: Code → Graph)
- generation/: Code generation from graphs (Phase 2: Graph → Code)
- config/: Configuration management
- cli/: CLI interface for the framework
"""

from .base import DataModelBase, OperationBase
from .cli.interface import CLI
from .generation.codegen import compile_all
from .analysis.decorators import datamodel, operation
from .analysis.validation.linter import DataModelLinter, run_linter
from .analysis.registries import ModelRegistry, OperationRegistry

__all__ = [
    # Decorators
    "datamodel",
    "operation",
    # Registries
    "ModelRegistry",
    "OperationRegistry",
    # CLI Interface
    "CLI",
    # Base classes
    "DataModelBase",
    "OperationBase",
    # Code generation
    "compile_all",
    # Linting
    "DataModelLinter",
    "run_linter",
]

__version__ = "0.6.0"
