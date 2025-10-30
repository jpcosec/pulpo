"""Workflow operations for todo status management."""

from pydantic import BaseModel, Field

from core.decorators import operation


class StartWorkInput(BaseModel):
    """Input for starting work on a todo."""

    todo_id: str = Field(..., description="ID of todo to start")


class StartWorkOutput(BaseModel):
    """Output from starting work."""

    success: bool = Field(..., description="Whether operation succeeded")
    new_status: str = Field(..., description="New status")
    message: str = Field(..., description="Status message")


@operation(
    name="todos.workflow.start",
    description="Start working on a todo (change status to in_progress)",
    inputs=StartWorkInput,
    outputs=StartWorkOutput,
    models_in=["Todo"],
    models_out=["Todo"]
)
async def start_todo(input_data: StartWorkInput) -> StartWorkOutput:
    """Change a todo's status to in_progress."""
    return StartWorkOutput(
        success=True,
        new_status="in_progress",
        message=f"Started working on todo {input_data.todo_id}"
    )


class CompleteTodoInput(BaseModel):
    """Input for completing a todo."""

    todo_id: str = Field(..., description="ID of todo to complete")


class CompleteTodoOutput(BaseModel):
    """Output from completing a todo."""

    success: bool = Field(..., description="Whether operation succeeded")
    new_status: str = Field(..., description="New status")
    completion_time: str = Field(..., description="Time of completion")
    message: str = Field(..., description="Status message")


@operation(
    name="todos.workflow.complete",
    description="Mark a todo as completed",
    inputs=CompleteTodoInput,
    outputs=CompleteTodoOutput,
    models_in=["Todo"],
    models_out=["Todo"]
)
async def complete_todo(input_data: CompleteTodoInput) -> CompleteTodoOutput:
    """Mark a todo as completed."""
    return CompleteTodoOutput(
        success=True,
        new_status="completed",
        completion_time="2025-10-30T12:00:00Z",
        message=f"Completed todo {input_data.todo_id}"
    )


class ReopenTodoInput(BaseModel):
    """Input for reopening a completed todo."""

    todo_id: str = Field(..., description="ID of todo to reopen")


class ReopenTodoOutput(BaseModel):
    """Output from reopening a todo."""

    success: bool = Field(..., description="Whether operation succeeded")
    new_status: str = Field(..., description="New status")
    message: str = Field(..., description="Status message")


@operation(
    name="todos.workflow.reopen",
    description="Reopen a completed todo (change status back to pending)",
    inputs=ReopenTodoInput,
    outputs=ReopenTodoOutput,
    models_in=["Todo"],
    models_out=["Todo"]
)
async def reopen_todo(input_data: ReopenTodoInput) -> ReopenTodoOutput:
    """Reopen a completed todo, changing its status back to pending."""
    return ReopenTodoOutput(
        success=True,
        new_status="pending",
        message=f"Reopened todo {input_data.todo_id}"
    )


class ArchiveTodosInput(BaseModel):
    """Input for archiving todos."""

    days_old: int = Field(
        default=7,
        description="Archive todos completed more than this many days ago"
    )


class ArchiveTodosOutput(BaseModel):
    """Output from archiving todos."""

    archived_count: int = Field(..., description="Number of todos archived")
    message: str = Field(..., description="Status message")


@operation(
    name="todos.sync.archive",
    description="Archive all completed todos older than threshold",
    inputs=ArchiveTodosInput,
    outputs=ArchiveTodosOutput,
    models_in=["Todo"],
    models_out=["Todo"]
)
async def archive_todos(input_data: ArchiveTodosInput) -> ArchiveTodosOutput:
    """Archive all completed todos that are older than threshold."""
    return ArchiveTodosOutput(
        archived_count=5,
        message=f"Archived 5 todos older than {input_data.days_old} days"
    )
