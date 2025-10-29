"""
Pulpo Core Framework

A metadata-driven framework for auto-generating APIs, UIs, CLIs, and Prefect orchestration
from decorators.
"""

from .base import DataModelBase, OperationBase
from .cli_interface import CLI
from .codegen import compile_all
from .decorators import datamodel, operation
from .linter import DataModelLinter, run_linter
from .registries import ModelRegistry, OperationRegistry

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
