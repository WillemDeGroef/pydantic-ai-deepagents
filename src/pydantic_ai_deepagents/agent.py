"""
Agent factory — the main entry point for creating a deep agent.

This is the Pydantic AI equivalent of LangChain's `create_deep_agent()`.
It assembles the system prompt, discovers skills, registers all tools,
and returns a configured Agent ready to .run().
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_ai import Agent

from pydantic_ai_deepagents.deps import DeepAgentDeps, Skill
from pydantic_ai_deepagents.prompt import build_system_prompt
from pydantic_ai_deepagents.skills import (
    discover_skills,
    build_skills_prompt_section,
)
from pydantic_ai_deepagents.tools.planning import write_todos, read_todos
from pydantic_ai_deepagents.tools.filesystem import (
    read_file,
    write_file,
    edit_file,
    list_files,
    grep_files,
)
from pydantic_ai_deepagents.tools.skills import (
    read_skill,
    list_skills,
    read_skill_resource,
)
from pydantic_ai_deepagents.tools.subagent import task
from pydantic_ai_deepagents.tools.shell import execute
from pydantic_ai_deepagents.tools.context import compact_conversation
from pydantic_ai_deepagents.context import ContextConfig
from pydantic_ai_deepagents.run import ManagedAgent


def create_deep_agent(
    *,
    model: str = "anthropic:claude-sonnet-4-20250514",
    system_prompt: str = "",
    tools: list[Any] | None = None,
    skills: list[str | Path] | None = None,
    inline_skills: list[Skill] | None = None,
    enable_shell: bool = False,
    enable_subagents: bool = True,
    enable_context_management: bool = True,
    context_config: ContextConfig | None = None,
    workspace: Path | None = None,
    max_sub_agent_depth: int = 2,
) -> tuple[Agent[DeepAgentDeps, str], DeepAgentDeps]:
    """
    Create a deep agent with planning, filesystem, skills, sub-agents,
    and optionally shell access.

    This mirrors LangChain's `create_deep_agent()` but uses Pydantic AI.

    Args:
        model: Model identifier (e.g. "anthropic:claude-sonnet-4-20250514",
               "openai:gpt-4o"). Any pydantic-ai compatible model string.
        system_prompt: Custom instructions injected into the system prompt.
        tools: Additional custom tools (callables) to register.
        skills: List of directories to scan for skills. Each directory
                should contain skill subdirectories with SKILL.md files.
                Later sources override earlier ones (last-wins precedence).
        inline_skills: Pre-built Skill objects to register directly.
                       Useful for in-memory or programmatically created skills.
        enable_shell: Whether to enable the `execute` shell tool.
        enable_subagents: Whether to enable the `task` sub-agent tool.
        enable_context_management: Whether to enable context compression tools.
        context_config: Configuration for context compression thresholds.
        workspace: Optional disk directory for real file I/O and shell.
        max_sub_agent_depth: How many levels deep sub-agents can nest.

    Returns:
        (agent, deps) tuple. Run the agent with:
            result = await agent.run("your prompt", deps=deps)
    """
    # ── Discover and load skills ─────────────────────────────────────────
    loaded_skills: dict[str, Skill] = {}

    if skills:
        loaded_skills = discover_skills(skills)

    if inline_skills:
        for skill in inline_skills:
            loaded_skills[skill.name] = skill

    # ── Build system prompt with skills listing ──────────────────────────
    skills_section = build_skills_prompt_section(loaded_skills)
    full_prompt = build_system_prompt(system_prompt, skills_section)

    agent: Agent[DeepAgentDeps, str] = Agent(
        model,
        deps_type=DeepAgentDeps,
        system_prompt=full_prompt,
    )

    # ── Core tools: planning ────────────────────────────────────────────
    agent.tool(write_todos)
    agent.tool(read_todos)

    # ── Core tools: filesystem ──────────────────────────────────────────
    agent.tool(read_file)
    agent.tool(write_file)
    agent.tool(edit_file)
    agent.tool(list_files)
    agent.tool(grep_files)

    # ── Skills tools (always registered, graceful when no skills) ───────
    agent.tool(read_skill)
    agent.tool(list_skills)
    agent.tool(read_skill_resource)

    # ── Optional: sub-agent delegation ──────────────────────────────────
    if enable_subagents:
        agent.tool(task)

    # ── Optional: context management ─────────────────────────────────────
    if enable_context_management:
        agent.tool(compact_conversation)

    # ── Optional: shell execution ───────────────────────────────────────
    if enable_shell or workspace is not None:
        agent.tool(execute)

    # ── Custom tools ────────────────────────────────────────────────────
    if tools:
        for tool_fn in tools:
            agent.tool(tool_fn)

    # ── Build deps ──────────────────────────────────────────────────────
    ctx_config = context_config if enable_context_management else None

    deps = DeepAgentDeps(
        workspace=workspace,
        model_name=model,
        max_sub_agent_depth=max_sub_agent_depth,
        skills=loaded_skills,
        context_config=ctx_config,
    )

    return agent, deps


def create_managed_agent(
    **kwargs: Any,
) -> ManagedAgent:
    """Create a deep agent wrapped with automatic context management.

    Accepts the same arguments as create_deep_agent().
    Returns a ManagedAgent that compresses context between turns.
    """
    context_config = kwargs.pop("context_config", None) or ContextConfig()
    kwargs.setdefault("enable_context_management", True)
    kwargs["context_config"] = context_config

    agent, deps = create_deep_agent(**kwargs)
    return ManagedAgent(agent, deps, context_config)
