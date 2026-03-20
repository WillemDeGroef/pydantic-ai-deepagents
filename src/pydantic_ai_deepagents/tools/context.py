"""Context management tool — allows the agent to manually trigger compression."""

from __future__ import annotations

from pydantic_ai import RunContext

from pydantic_ai_deepagents.deps import DeepAgentDeps


async def compact_conversation(
    ctx: RunContext[DeepAgentDeps],
    tier: int = 0,
) -> str:
    """Compact the conversation history to free up context space.

    Args:
        tier: Compression level (0=auto, 1=offload large results,
              2=strip write args, 3=full summarization).
              Default 0 lets the system decide based on current usage.
    """
    tier = max(0, min(3, tier))
    ctx.deps._compact_requested = tier if tier > 0 else 1
    level_names = {
        0: "auto",
        1: "offload large results",
        2: "strip write args",
        3: "summarize history",
    }
    return (
        f"Context compaction requested (tier {ctx.deps._compact_requested}: "
        f"{level_names.get(ctx.deps._compact_requested, 'unknown')}). "
        f"Compression will be applied after this turn completes."
    )
