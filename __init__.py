"""Pulpo Core - Agnostic framework for building full-stack applications.

A metadata-driven code generation framework with hierarchical orchestration
for building APIs, UIs, CLIs, and Prefect flows from decorators.
"""

__version__ = "0.6.0"
__author__ = "Pulpo Team"
__license__ = "MIT"

# Main exports for easy import
from core.analysis.decorators import datamodel, operation
from core.analysis.registries import ModelRegistry, OperationRegistry

__all__ = [
    # Decorators
    "datamodel",
    "operation",
    # Registries
    "ModelRegistry",
    "OperationRegistry",
]
