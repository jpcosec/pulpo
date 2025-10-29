from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass
class ModelInfo:
    """Registered model information for CRUD/UI generation.

    Attributes:
        name: Public name used in surfaces (e.g., "Job").
        document_cls: Beanie/Pydantic model class.
        description: Optional human-readable description of the model.
        ui_hints: Optional UI metadata (groups, widgets, visibility, order).
        tags: Optional tags for grouping.
        relations: Optional relation hints for UI/graph.
        searchable_fields: Optional list of searchable field names.
        sortable_fields: Optional list of sortable field names.
    """

    name: str
    document_cls: type[Any]
    description: str | None = None
    ui_hints: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    searchable_fields: list[str] = field(default_factory=list)
    sortable_fields: list[str] = field(default_factory=list)


@dataclass
class OperationMetadata:
    """Metadata describing a registered operation."""

    name: str
    description: str
    category: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    function: Callable[..., Any] | Any
    tags: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    async_enabled: bool = False
    models_in: list[str] = field(default_factory=list)
    models_out: list[str] = field(default_factory=list)
    stage: str | None = None


class ModelRegistry:
    """Global registry for models (define-once source of truth)."""

    _models: dict[str, ModelInfo] = {}

    @classmethod
    def register(cls, info: ModelInfo) -> None:
        if info.name in cls._models:
            raise ValueError(f"Model '{info.name}' already registered")
        cls._models[info.name] = info

    @classmethod
    def get(cls, name: str) -> ModelInfo | None:
        return cls._models.get(name)

    @classmethod
    def list_all(cls) -> list[ModelInfo]:
        return list(cls._models.values())

    @classmethod
    def clear(cls) -> None:
        cls._models.clear()


class OperationRegistry:
    """Global registry for operations (define-once source of truth)."""

    _ops: dict[str, OperationMetadata] = {}

    @classmethod
    def register(cls, meta: OperationMetadata) -> None:
        if meta.name in cls._ops:
            raise ValueError(f"Operation '{meta.name}' already registered")
        cls._ops[meta.name] = meta

    @classmethod
    def get(cls, name: str) -> OperationMetadata | None:
        return cls._ops.get(name)

    @classmethod
    def list_all(cls) -> list[OperationMetadata]:
        return list(cls._ops.values())

    @classmethod
    def by_category(cls, category: str) -> list[OperationMetadata]:
        return [op for op in cls._ops.values() if op.category == category]

    @classmethod
    def clear(cls) -> None:
        cls._ops.clear()
