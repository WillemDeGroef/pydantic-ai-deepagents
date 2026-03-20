"""System prompt builder for the deep agent."""

from __future__ import annotations


CONTEXT_MANAGEMENT_SECTION = """\
## Context Management

This agent has automatic context compression enabled. When the conversation \
grows long, the system will:
1. **Offload large tool results** to the virtual filesystem (keeping a preview)
2. **Strip write/edit arguments** from older messages (data is already saved)
3. **Summarize older history** if context usage exceeds thresholds

You can manually trigger compression using the `compact_conversation` tool \
with a tier level (1-3). Use the virtual filesystem (`write_file`) for large \
outputs instead of returning them inline — this keeps context lean.
"""


def build_system_prompt(
    custom: str = "",
    skills_section: str = "",
    include_context_management: bool = True,
) -> str:
    """Build the full system prompt from custom instructions and skills listing."""
    parts: list[str] = []

    if custom:
        parts.append(custom)

    if include_context_management:
        parts.append(CONTEXT_MANAGEMENT_SECTION)

    if skills_section:
        parts.append(skills_section)

    return "\n\n".join(parts) if parts else ""
