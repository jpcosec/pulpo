from __future__ import annotations

import functools
import traceback
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from .registries import ModelInfo, ModelRegistry, OperationMetadata, OperationRegistry


def datamodel(
    *,
    name: str,
    description: str | None = None,
    tags: list[str] | None = None,
    ui: dict[str, Any] | None = None,
    indexes: list[Any] | None = None,  # documentation hint only
    relations: list[dict[str, Any]] | None = None,
):
    """Decorator to register a data model for CRUD/UI generation.

    Usage:
        @datamodel(name="Job", tags=["jobs"])  # on top of a Beanie Document class
        class Job(Document):
            ...
    """

    def _wrap(document_cls: type[Any]) -> type[Any]:
        info = ModelInfo(
            name=name,
            document_cls=document_cls,
            description=description,
            ui_hints=ui or {},
            tags=tags or [],
            relations=relations or getattr(document_cls, "relations", lambda: [])(),
            searchable_fields=getattr(document_cls, "searchable_fields", []),
            sortable_fields=getattr(document_cls, "sortable_fields", []),
        )
        # Attach metadata on the class for convenience
        document_cls._registry_info = info
        ModelRegistry.register(info)
        return document_cls

    return _wrap


def operation(
    *,
    name: str,
    description: str,
    category: str,
    inputs: type[BaseModel],
    outputs: type[BaseModel],
    tags: list[str] | None = None,
    permissions: list[str] | None = None,
    async_enabled: bool = False,
    models_in: list[str] | None = None,
    models_out: list[str] | None = None,
    stage: str | None = None,
):
    """Decorator to register an operation with typed input/output schemas.

    Accepts either a bare async function or an OperationBase instance/class.

    Operations are automatically tracked and orchestrated by Prefect when using
    hierarchical naming convention (e.g., "flow.step.substep").
    """

    def _wrap(func_or_cls: Any) -> Any:
        fn: Callable[..., Any]

        # If a class is passed, expect it to provide a `run()` coroutine method.
        if hasattr(func_or_cls, "run") and callable(func_or_cls.run):
            fn = func_or_cls.run
        else:
            fn = func_or_cls

        # Register metadata
        meta = OperationMetadata(
            name=name,
            description=description,
            category=category,
            input_schema=inputs,
            output_schema=outputs,
            function=fn,
            tags=tags or [],
            permissions=permissions or [],
            async_enabled=async_enabled,
            models_in=models_in or [],
            models_out=models_out or [],
            stage=stage,
        )
        OperationRegistry.register(meta)

        # Return original function/class for direct invocation if needed
        # Prefect handles orchestration and observability automatically
        return func_or_cls

    return _wrap
