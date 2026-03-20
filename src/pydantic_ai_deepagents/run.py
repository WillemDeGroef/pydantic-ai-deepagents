"""
ManagedAgent — wraps a pydantic-ai Agent with automatic context management.

Maintains message history externally and applies compression between turns,
since pydantic-ai's built-in run_chat manages its own history internally.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from pydantic_ai import AgentRunResult

from pydantic_ai_deepagents.context import (
    ContextConfig,
    ContextManager,
    estimate_message_tokens,
)
from pydantic_ai_deepagents.deps import DeepAgentDeps


class ManagedAgent:
    """Agent wrapper that applies context compression between turns."""

    def __init__(
        self,
        agent: Agent[DeepAgentDeps, str],
        deps: DeepAgentDeps,
        context_config: ContextConfig | None = None,
    ) -> None:
        self.agent = agent
        self.deps = deps
        self.context_config = context_config or ContextConfig()
        self.context_manager = ContextManager(self.context_config, deps)
        self.message_history: list[ModelMessage] = []

    async def run(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> AgentRunResult[str]:
        """Run a single turn with automatic context management.

        Pre-run: compress history if needed.
        Run: execute agent with compressed history.
        Post-run: apply tier 1 to new tool returns, handle compact requests.
        """
        # Pre-run: auto-compress if enabled
        if self.message_history:
            self.message_history = await self.context_manager.maybe_compress(
                self.message_history
            )

        # Run agent with current history
        result = await self.agent.run(
            prompt,
            deps=self.deps,
            message_history=self.message_history if self.message_history else None,
            **kwargs,
        )

        # Capture new messages (includes history + new messages from this turn)
        self.message_history = list(result.all_messages())

        # Post-run: apply tier 1 to new tool returns
        self.message_history = self.context_manager.offload_large_results(
            self.message_history
        )

        # Post-run: handle manual compact_conversation requests
        if self.deps._compact_requested > 0:
            tier = self.deps._compact_requested
            self.deps._compact_requested = 0
            self.message_history = await self.context_manager.apply_tier(
                self.message_history, tier
            )

        # Update token estimate on deps
        self.deps.total_tokens_estimate = estimate_message_tokens(self.message_history)

        return result


async def run_with_context(
    agent: Agent[DeepAgentDeps, str],
    prompt: str,
    deps: DeepAgentDeps,
    message_history: list[ModelMessage] | None = None,
    context_config: ContextConfig | None = None,
    **kwargs: Any,
) -> tuple[AgentRunResult[str], list[ModelMessage]]:
    """Standalone function for single-shot context-managed runs.

    Returns (result, compressed_messages) so the caller can maintain history.
    """
    config = context_config or ContextConfig()
    manager = ContextManager(config, deps)

    messages = list(message_history) if message_history else []

    # Pre-compress
    if messages:
        messages = await manager.maybe_compress(messages)

    result = await agent.run(
        prompt,
        deps=deps,
        message_history=messages if messages else None,
        **kwargs,
    )

    # Capture and compress
    all_msgs = list(result.all_messages())
    all_msgs = manager.offload_large_results(all_msgs)

    deps.total_tokens_estimate = estimate_message_tokens(all_msgs)

    return result, all_msgs
