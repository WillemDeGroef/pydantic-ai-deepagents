"""Sub-agent tool — task."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from pydantic_ai_deepagents.deps import DeepAgentDeps


async def task(
    ctx: RunContext[DeepAgentDeps],
    description: str,
) -> str:
    """
    Delegate a task to a sub-agent.

    The sub-agent shares the same virtual filesystem and todo list but runs
    as a separate conversation. Use this for independent subtasks that can
    be completed without further user input.
    """
    deps = ctx.deps

    if deps._current_depth >= deps.max_sub_agent_depth:
        return (
            f"Error: Maximum sub-agent depth ({deps.max_sub_agent_depth}) reached. "
            "Complete this task directly instead of delegating."
        )

    sub_agent: Agent[DeepAgentDeps, str] = Agent(
        deps.model_name,
        deps_type=DeepAgentDeps,
        system_prompt="You are a sub-agent. Complete the given task concisely.",
    )

    sub_deps = DeepAgentDeps(
        files=deps.files,
        todos=deps.todos,
        skills=deps.skills,
        workspace=deps.workspace,
        model_name=deps.model_name,
        max_sub_agent_depth=deps.max_sub_agent_depth,
        _current_depth=deps._current_depth + 1,
    )

    result = await sub_agent.run(description, deps=sub_deps)
    return result.output
