"""Planning tools — write_todos, read_todos."""

from __future__ import annotations

from pydantic_ai import RunContext

from pydantic_ai_deepagents.deps import DeepAgentDeps, TodoItem


async def write_todos(
    ctx: RunContext[DeepAgentDeps],
    todos: list[dict[str, str]],
) -> str:
    """
    Write or update the todo list for planning purposes.

    Each todo should have a 'description' and optionally a 'status'
    (pending, in_progress, or done). Existing todos are replaced.
    """
    deps = ctx.deps
    deps.todos.clear()
    deps._next_todo_id = 1

    for item in todos:
        tid = deps.next_todo_id()
        deps.todos.append(
            TodoItem(
                id=tid,
                description=item.get("description", ""),
                status=item.get("status", "pending"),
            )
        )

    return f"Updated todo list with {len(deps.todos)} items."


async def read_todos(
    ctx: RunContext[DeepAgentDeps],
) -> str:
    """Read the current todo list."""
    deps = ctx.deps

    if not deps.todos:
        return "No todos yet. Use `write_todos` to create a plan."

    lines = ["## Todo List", ""]
    for todo in deps.todos:
        marker = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}.get(
            todo.status, "[ ]"
        )
        lines.append(f"- {marker} #{todo.id}: {todo.description}")

    return "\n".join(lines)
