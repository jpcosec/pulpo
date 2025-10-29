"""
JobHunter Core Framework

A metadata-driven framework for auto-generating APIs, UIs, and CLIs from decorators.
"""

from core.base import DataModelBase, OperationBase
from core.codegen import compile_all
from core.decorators import datamodel, operation
from core.linter import DataModelLinter, run_linter
from core.registries import ModelRegistry, OperationRegistry

__all__ = [
    "DataModelBase",
    "OperationBase",
    "datamodel",
    "operation",
    "ModelRegistry",
    "OperationRegistry",
    "compile_all",
    "DataModelLinter",
    "run_linter",
]

__version__ = "0.6.0"
