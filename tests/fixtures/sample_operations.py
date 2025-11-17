"""Sample operations extracted from todo-app for testing.

These are fixtures for testing Pulpo framework functionality.
They mirror the structure of real operations without importing the actual project.
"""

from typing import Optional
from pydantic import BaseModel, Field

from core.decorators import operation
from .sample_models import Task, TaskStatusEnum


# Input/Output schemas
class CheckNeededTasksInput(BaseModel):
    """Input for checking ready tasks."""

    status_filter: Optional[str] = Field(
        default="pending",
        description="Status filter"
    )


class TaskSummary(BaseModel):
    """Task summary output."""

    task_id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    importance_rate: int = Field(..., description="Importance 0-5")
    urgency: float = Field(..., description="Urgency 0-10")


class CheckNeededTasksOutput(BaseModel):
    """Output for checking tasks."""

    tasks: list[TaskSummary] = Field(..., description="Ready tasks")
    count: int = Field(..., description="Task count")
    message: str = Field(..., description="Status message")


class NextTaskInput(BaseModel):
    """Input for next task recommendation."""

    limit: int = Field(default=5, ge=1, le=20, description="Max tasks")
    exclude_ids: list[str] = Field(default_factory=list, description="Exclude IDs")


class NextTaskOutput(BaseModel):
    """Output for next task."""

    tasks: list[TaskSummary] = Field(..., description="Recommended tasks")
    message: str = Field(..., description="Reasoning")


class LoadDocumentInput(BaseModel):
    """Input for document loading."""

    content: str = Field(..., description="Document content")
    category_id: Optional[str] = Field(default=None, description="Category ID")
    importance_rate: int = Field(default=0, ge=0, le=5, description="Default importance")


class LoadOutput(BaseModel):
    """Output from document loading."""

    created_count: int = Field(..., description="Tasks created")
    message: str = Field(..., description="Result message")
    task_ids: list[str] = Field(..., description="Created task IDs")


# Simple read operation
@operation(
    name="tasks.analysis.check_needed",
    description="Find tasks ready to start (dependencies completed)",
    category="task-analysis",
    inputs=CheckNeededTasksInput,
    outputs=CheckNeededTasksOutput,
    models_in=["Task"],
    models_out=["Task"]
)
async def check_needed_tasks(input_data: CheckNeededTasksInput) -> CheckNeededTasksOutput:
    """Check which tasks are ready to start.

    Tests:
    - Operation decorator parsing
    - Async function handling
    - Input/output schema validation
    - models_in/models_out tracking
    """
    query = {"status": input_data.status_filter or "pending"}
    available_tasks = await Task.find(query).to_list()

    needed = []
    for task in available_tasks:
        if not task.dependencies:
            needed.append(task)
        else:
            all_deps_done = True
            for dep_link in task.dependencies:
                dep_task = await dep_link.fetch()
                if dep_task.status != TaskStatusEnum.COMPLETED:
                    all_deps_done = False
                    break
            if all_deps_done:
                needed.append(task)

    task_summaries = [
        TaskSummary(
            task_id=str(task.id),
            title=task.title,
            importance_rate=task.importance_rate,
            urgency=task.urgency
        )
        for task in needed
    ]

    return CheckNeededTasksOutput(
        tasks=task_summaries,
        count=len(task_summaries),
        message=f"Found {len(task_summaries)} tasks ready"
    )


# Read operation with sorting
@operation(
    name="tasks.analysis.next_by_urgency",
    description="Get next task sorted by urgency",
    category="task-prioritization",
    inputs=NextTaskInput,
    outputs=NextTaskOutput,
    models_in=["Task"],
    models_out=["Task"]
)
async def next_by_urgency(input_data: NextTaskInput) -> NextTaskOutput:
    """Get tasks sorted by urgency.

    Tests:
    - Multiple operations in same category
    - Complex query filters
    - Sorting logic
    """
    query = {
        "status": {"$in": ["pending", "in_progress"]},
        "_id": {"$nin": [id for id in input_data.exclude_ids]}
    }

    tasks = await Task.find(query).to_list()
    sorted_tasks = sorted(tasks, key=lambda t: t.urgency, reverse=True)
    sorted_tasks = sorted_tasks[:input_data.limit]

    task_summaries = [
        TaskSummary(
            task_id=str(task.id),
            title=task.title,
            importance_rate=task.importance_rate,
            urgency=task.urgency
        )
        for task in sorted_tasks
    ]

    return NextTaskOutput(
        tasks=task_summaries,
        message="Tasks sorted by urgency"
    )


# Write operation
@operation(
    name="tasks.loader.markdown",
    description="Load tasks from Markdown checkboxes",
    category="task-import",
    inputs=LoadDocumentInput,
    outputs=LoadOutput,
    models_in=["Task"],
    models_out=["Task"]
)
async def load_markdown(input_data: LoadDocumentInput) -> LoadOutput:
    """Parse Markdown and create tasks.

    Tests:
    - Write operation (creates data)
    - Regex parsing
    - Batch document creation
    """
    import re

    pattern = r"^- \[([ xX])\]\s+(.+)$"
    matches = re.findall(pattern, input_data.content, re.MULTILINE)

    tasks_data = [
        {"title": title.strip(), "completed": status.lower() == "x"}
        for status, title in matches
    ]

    created_ids = []
    for task_data in tasks_data:
        task = Task(
            title=task_data["title"],
            status=TaskStatusEnum.COMPLETED if task_data["completed"] else TaskStatusEnum.PENDING,
            category_id=input_data.category_id,
            importance_rate=input_data.importance_rate
        )
        result = await task.insert()
        created_ids.append(str(result.id))

    return LoadOutput(
        created_count=len(created_ids),
        message=f"Loaded {len(created_ids)} tasks from Markdown",
        task_ids=created_ids
    )


# Delete operation
@operation(
    name="tasks.management.archive_completed",
    description="Archive all completed tasks",
    category="task-management",
    inputs=BaseModel,
    outputs=BaseModel,
    models_in=["Task"],
    models_out=[]
)
async def archive_completed() -> dict:
    """Archive completed tasks.

    Tests:
    - Delete operation
    - No input schema (uses BaseModel)
    - Empty models_out
    """
    completed = await Task.find({"status": TaskStatusEnum.COMPLETED}).to_list()
    count = len(completed)

    for task in completed:
        await task.delete()

    return {"archived_count": count, "message": f"Archived {count} tasks"}
