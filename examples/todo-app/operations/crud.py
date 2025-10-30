"""CRUD operations for todo items."""

from pydantic import BaseModel, Field

from core.decorators import operation


class CreateTodoInput(BaseModel):
    """Input for creating a todo."""

    title: str = Field(..., description="Task title")
    description: str = Field(default="", description="Task description")
    created_by: str = Field(..., description="Username creating the todo")


class CreateTodoOutput(BaseModel):
    """Output from creating a todo."""

    success: bool = Field(..., description="Whether creation succeeded")
    todo_id: str = Field(..., description="ID of created todo")
    message: str = Field(..., description="Status message")


@operation(
    name="todos.crud.create",
    description="Create a new todo item",
    inputs=CreateTodoInput,
    outputs=CreateTodoOutput,
    models_in=["User"],
    models_out=["Todo"]
)
async def create_todo(input_data: CreateTodoInput) -> CreateTodoOutput:
    """Create a new todo item and add to list."""
    return CreateTodoOutput(
        success=True,
        todo_id="todo_123_created",
        message=f"Created todo: {input_data.title}"
    )


class ReadTodoInput(BaseModel):
    """Input for reading a todo."""

    todo_id: str = Field(..., description="ID of todo to read")


class ReadTodoOutput(BaseModel):
    """Output from reading a todo."""

    todo_id: str = Field(..., description="Todo ID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Current status")
    created_by: str = Field(..., description="Creator username")


@operation(
    name="todos.crud.read",
    description="Read a todo item by ID",
    inputs=ReadTodoInput,
    outputs=ReadTodoOutput,
    models_in=["Todo"],
    models_out=["Todo"]
)
async def read_todo(input_data: ReadTodoInput) -> ReadTodoOutput:
    """Read and return a todo item."""
    return ReadTodoOutput(
        todo_id=input_data.todo_id,
        title="Sample Todo",
        description="This is a sample todo",
        status="pending",
        created_by="user123"
    )


class UpdateTodoInput(BaseModel):
    """Input for updating a todo."""

    todo_id: str = Field(..., description="ID of todo to update")
    title: str = Field(default=None, description="New title (optional)")
    description: str = Field(default=None, description="New description (optional)")


class UpdateTodoOutput(BaseModel):
    """Output from updating a todo."""

    success: bool = Field(..., description="Whether update succeeded")
    updated_fields: list[str] = Field(..., description="Fields that were updated")
    message: str = Field(..., description="Status message")


@operation(
    name="todos.crud.update",
    description="Update a todo item",
    inputs=UpdateTodoInput,
    outputs=UpdateTodoOutput,
    models_in=["Todo"],
    models_out=["Todo"]
)
async def update_todo(input_data: UpdateTodoInput) -> UpdateTodoOutput:
    """Update fields of an existing todo."""
    updated = []
    if input_data.title:
        updated.append("title")
    if input_data.description:
        updated.append("description")

    return UpdateTodoOutput(
        success=True,
        updated_fields=updated,
        message=f"Updated todo {input_data.todo_id}"
    )


class DeleteTodoInput(BaseModel):
    """Input for deleting a todo."""

    todo_id: str = Field(..., description="ID of todo to delete")


class DeleteTodoOutput(BaseModel):
    """Output from deleting a todo."""

    success: bool = Field(..., description="Whether deletion succeeded")
    deleted_id: str = Field(..., description="ID of deleted todo")
    message: str = Field(..., description="Status message")


@operation(
    name="todos.crud.delete",
    description="Delete a todo item",
    inputs=DeleteTodoInput,
    outputs=DeleteTodoOutput,
    models_in=["Todo"],
    models_out=[]
)
async def delete_todo(input_data: DeleteTodoInput) -> DeleteTodoOutput:
    """Delete a todo item from the list."""
    return DeleteTodoOutput(
        success=True,
        deleted_id=input_data.todo_id,
        message=f"Deleted todo {input_data.todo_id}"
    )
