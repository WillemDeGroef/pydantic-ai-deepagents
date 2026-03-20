"""
Shared dependency context injected into every tool call via Pydantic AI's RunContext.

This replaces LangGraph's AgentState + BackendProtocol with a single
dataclass that holds the virtual filesystem, todo list, and conversation
metadata the agent accumulates during a run.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TodoItem:
    """A single planning item the agent tracks."""

    id: int
    description: str
    status: str = "pending"  # pending | in_progress | done


@dataclass
class FileEntry:
    """In-memory virtual file."""

    content: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class Skill:
    """
    A loaded agent skill following the Agent Skills specification.

    Skills use progressive disclosure:
      1. Discovery — only name + description go into the system prompt
      2. Activation — full instructions loaded on-demand via read_skill tool
      3. Execution — agent follows the instructions, may read supporting files

    See: https://agentskills.io/specification
    """

    name: str
    description: str
    instructions: str  # full markdown body (below frontmatter)
    source_path: str  # directory this skill was loaded from
    # Optional metadata from YAML frontmatter
    license: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    # Supporting files in the skill directory (relative path → content)
    resources: dict[str, str] = field(default_factory=dict)


@dataclass
class DeepAgentDeps:
    """
    Runtime dependencies available to every tool via RunContext[DeepAgentDeps].

    Mirrors the Deep Agents pattern of a virtual filesystem + todo list that
    lives *in agent state* so the LLM can offload long context there.
    """

    # ── virtual filesystem (in-memory, keyed by relative path) ──────────
    files: dict[str, FileEntry] = field(default_factory=dict)

    # ── planning state ──────────────────────────────────────────────────
    todos: list[TodoItem] = field(default_factory=list)
    _next_todo_id: int = field(default=1, repr=False)

    # ── skills registry ─────────────────────────────────────────────────
    skills: dict[str, Skill] = field(default_factory=dict)

    # ── optional: local disk workspace (for real file I/O) ──────────────
    workspace: Path | None = None

    # ── sub-agent config ────────────────────────────────────────────────
    model_name: str = "anthropic:claude-sonnet-4-20250514"
    max_sub_agent_depth: int = 2
    _current_depth: int = field(default=0, repr=False)

    # ── context management ───────────────────────────────────────────────
    total_tokens_estimate: int = field(default=0, repr=False)
    max_context_chars: int = 100_000
    context_config: Any = (
        None  # typed as ContextConfig at runtime; Any avoids circular import
    )
    _compact_requested: int = field(default=0, repr=False)

    def next_todo_id(self) -> int:
        tid = self._next_todo_id
        self._next_todo_id += 1
        return tid

    def use_disk(self) -> bool:
        return self.workspace is not None

    def resolve_path(self, rel: str) -> Path:
        """Resolve a relative path safely inside the workspace."""
        if self.workspace is None:
            raise ValueError("No workspace configured for disk operations")
        resolved = (self.workspace / rel).resolve()
        if not str(resolved).startswith(str(self.workspace.resolve())):
            raise PermissionError(f"Path traversal blocked: {rel}")
        return resolved
