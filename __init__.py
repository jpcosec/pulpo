"""PulpoCore - Agnostic framework for building full-stack applications."""

__version__ = "0.7.0"
__author__ = "PulpoCore Team"
__license__ = "MIT"

# Main exports for easy import
from core.decorators import datamodel, operation
from core.registries import ModelRegistry, OperationRegistry

__all__ = [
    "datamodel",
    "operation",
    "ModelRegistry",
    "OperationRegistry",
]
