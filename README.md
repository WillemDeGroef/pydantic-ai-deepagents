# Deep Agent — Pydantic AI

A Pydantic AI re-implementation of the [LangChain Deep Agents](https://github.com/langchain-ai/deepagents) pattern, which itself was reverse-engineered from Claude Code's architecture.

## What is this?

LangChain's Deep Agents project identified four architectural pillars that make Claude Code effective at complex, multi-step tasks. This project recreates those pillars using **Pydantic AI** instead of LangChain/LangGraph:

| Pillar | Deep Agents (LangChain) | This Project (Pydantic AI) |
|---|---|---|
| **Planning** | `TodoListMiddleware` — no-op tool for context engineering | `write_todos` / `read_todos` — same pattern, injected via `RunContext` |
| **Filesystem** | `FilesystemMiddleware` with `BackendProtocol` | `read_file`, `write_file`, `edit_file`, `list_files`, `grep_files` — in-memory or disk-backed |
| **Sub-agents** | `SubAgentMiddleware` + `task` tool | `task` tool that spawns fresh `pydantic_ai.Agent` with shared filesystem |
| **Skills** | `SkillsMiddleware` — scans directories, injects names into prompt, lazy-loads | `discover_skills()` + `read_skill` / `read_skill_resource` tools — same progressive disclosure |
| **System Prompt** | Claude Code–inspired prompt with tool usage guidelines | Same approach — detailed instructions on planning, filesystem usage, delegation, skills |
| **Context Mgmt** | `SummarizationMiddleware` with auto-compaction | Filesystem-as-memory pattern + output truncation |

## Installation

```bash
pip install pydantic-ai-deepagents
```

## Quickstart

```python
import asyncio
from pydantic_ai_deepagents import create_deep_agent

async def main():
    agent, deps = create_deep_agent(
        system_prompt="You are a research assistant.",
    )

    result = await agent.run(
        "Research X and write your findings to notes.md",
        deps=deps,
    )

    print(result.output)

    # Check what files the agent created
    for path, entry in deps.files.items():
        print(f"{path}: {len(entry.content)} chars")

asyncio.run(main())
```

## Customisation

### Custom model

```python
agent, deps = create_deep_agent(
    model="openai:gpt-4o",  # or any pydantic-ai model string
)
```

### Custom tools

```python
from pydantic_ai import RunContext
from pydantic_ai_deepagents import DeepAgentDeps

async def search_web(ctx: RunContext[DeepAgentDeps], query: str) -> str:
    """Search the web for information."""
    # your implementation
    return "results..."

agent, deps = create_deep_agent(tools=[search_web])
```

### Disk-backed workspace with shell

```python
from pathlib import Path

agent, deps = create_deep_agent(
    workspace=Path("./my_workspace"),
    enable_shell=True,
)
```

### Sub-agent depth control

```python
agent, deps = create_deep_agent(
    max_sub_agent_depth=3,  # allow 3 levels of nesting
    enable_subagents=True,
)
```

## Skills

Skills follow the open [Agent Skills specification](https://agentskills.io/specification) with **progressive disclosure**:

1. **Discovery** — at startup, only skill names + descriptions go into the system prompt
2. **Activation** — the agent calls `read_skill("skill-name")` to load full instructions on demand
3. **Execution** — the agent follows the instructions, optionally loading resource files

### Loading skills

```python
# From directories
agent, deps = create_deep_agent(skills=["./skills/"])

# Inline
from pydantic_ai_deepagents import Skill
agent, deps = create_deep_agent(inline_skills=[Skill(
    name="my-skill", description="...", instructions="...", source_path="<inline>",
)])

# From raw SKILL.md text
from pydantic_ai_deepagents import load_skill_from_text
skill = load_skill_from_text("my-skill", open("SKILL.md").read())
agent, deps = create_deep_agent(inline_skills=[skill])
```

### Example skills included

The `example_skills/` directory contains three ready-to-use skills:

- **web-research** — structured research workflow with synthesis
- **code-review** — multi-pass review (correctness, security, maintainability, performance)
- **data-analysis** — data profiling, cleaning, analysis, and reporting

## Credits

- [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) — the original Deep Agents implementation
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — the architecture that inspired it all
- [Pydantic AI](https://ai.pydantic.dev/) — the agent framework used here
