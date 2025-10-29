from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DataModelBase:
    """Optional mixin for Beanie documents to provide relation hints.

    This is domain-agnostic and purely descriptive.
    """

    searchable_fields: list[str] = []
    sortable_fields: list[str] = []

    @classmethod
    def relations(cls) -> list[dict]:
        """Return relation hints (override in models if desired).

        Example:
            {"name": "applications", "target": "Application", "cardinality": "many", "via": "job_id"}
        """
        return []

    @classmethod
    def indexes(cls) -> list[dict]:
        """Return index definitions (override in models if desired).

        Example:
            [{"keys": [("field_name", 1)]}]
        """
        return []


class OperationBase(ABC):
    """Base class for operations. All operations are async-first."""

    @abstractmethod
    async def run(self, input_model: Any) -> Any:
        """Execute the operation and return a typed output model."""
