"""
Context management — three-tier compression to keep conversation history within LLM limits.

Tier 1: Offload large tool results to virtual filesystem, keep preview
Tier 2: Strip write/edit tool call args (data already persisted)
Tier 3: Summarize older conversation history via LLM
"""

from __future__ import annotations

import dataclasses
import json
import time
from dataclasses import dataclass

from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from pydantic_ai_deepagents.deps import DeepAgentDeps, FileEntry


@dataclass
class ContextConfig:
    """Configurable thresholds for context compression."""

    tier1_token_threshold: int = 20_000
    tier2_capacity_ratio: float = 0.85
    tier3_capacity_ratio: float = 0.95
    max_context_tokens: int = 100_000
    preview_lines: int = 10
    auto_compress: bool = True
    summarization_model: str | None = None


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def estimate_message_tokens(messages: list[ModelMessage]) -> int:
    """Estimate total tokens across a message list."""
    total = 0
    for msg in messages:
        for part in msg.parts:
            if isinstance(part, (TextPart, UserPromptPart)):
                total += estimate_tokens(str(part.content))
            elif isinstance(part, ToolReturnPart):
                total += estimate_tokens(str(part.content))
            elif isinstance(part, ToolCallPart):
                total += estimate_tokens(str(part.args) if part.args else "")
            else:
                total += estimate_tokens(str(part))
    return total


class ContextManager:
    """Manages three-tier context compression for long-running agent conversations."""

    def __init__(self, config: ContextConfig, deps: DeepAgentDeps) -> None:
        self.config = config
        self.deps = deps

    def _capacity_ratio(self, messages: list[ModelMessage]) -> float:
        tokens = estimate_message_tokens(messages)
        return (
            tokens / self.config.max_context_tokens
            if self.config.max_context_tokens > 0
            else 0.0
        )

    def offload_large_results(self, messages: list[ModelMessage]) -> list[ModelMessage]:
        """Tier 1: Replace large tool results with filesystem reference + preview."""
        threshold = self.config.tier1_token_threshold
        result: list[ModelMessage] = []

        for msg in messages:
            if not isinstance(msg, ModelRequest):
                result.append(msg)
                continue

            modified = False
            new_parts = []
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    content_str = str(part.content)
                    if estimate_tokens(content_str) > threshold:
                        # Save full content to virtual filesystem
                        tool_id = part.tool_call_id or part.tool_name
                        path = f"_context/tool_returns/{tool_id}.txt"
                        now = time.time()
                        self.deps.files[path] = FileEntry(
                            content=content_str,
                            created_at=now,
                            updated_at=now,
                        )
                        # Build preview
                        lines = content_str.splitlines()
                        preview = "\n".join(lines[: self.config.preview_lines])
                        replacement = (
                            f"[Content offloaded to virtual filesystem: {path}]\n"
                            f"Preview ({self.config.preview_lines} lines):\n{preview}"
                        )
                        new_parts.append(dataclasses.replace(part, content=replacement))
                        modified = True
                    else:
                        new_parts.append(part)
                else:
                    new_parts.append(part)

            if modified:
                result.append(dataclasses.replace(msg, parts=new_parts))
            else:
                result.append(msg)

        return result

    def strip_write_args(self, messages: list[ModelMessage]) -> list[ModelMessage]:
        """Tier 2: Strip large args from older write/edit tool calls."""
        result: list[ModelMessage] = []
        write_tools = {"write_file", "edit_file"}

        # Keep last 3 request-response pairs untouched
        boundary = max(0, len(messages) - 6)

        for i, msg in enumerate(messages):
            if i >= boundary or not isinstance(msg, ModelResponse):
                result.append(msg)
                continue

            modified = False
            new_parts = []
            for part in msg.parts:
                if isinstance(part, ToolCallPart) and part.tool_name in write_tools:
                    # Keep only the path key
                    args = part.args
                    if isinstance(args, dict):
                        stripped = {
                            "path": args.get("path", "unknown"),
                            "_note": "args stripped by context manager",
                        }
                    elif isinstance(args, str):
                        try:
                            parsed = json.loads(args)
                            stripped = json.dumps(
                                {
                                    "path": parsed.get("path", "unknown"),
                                    "_note": "args stripped by context manager",
                                }
                            )
                        except (json.JSONDecodeError, AttributeError):
                            stripped = args
                    else:
                        stripped = args
                    new_parts.append(dataclasses.replace(part, args=stripped))
                    modified = True
                else:
                    new_parts.append(part)

            if modified:
                result.append(dataclasses.replace(msg, parts=new_parts))
            else:
                result.append(msg)

        return result

    async def summarize(self, messages: list[ModelMessage]) -> list[ModelMessage]:
        """Tier 3: Summarize older history, keep recent messages."""
        from pydantic_ai import Agent

        # Save full history backup
        timestamp = int(time.time())
        backup_path = f"_context/history_{timestamp}.json"
        serialized = ModelMessagesTypeAdapter.dump_json(messages).decode()
        now = time.time()
        self.deps.files[backup_path] = FileEntry(
            content=serialized,
            created_at=now,
            updated_at=now,
        )

        # Split: keep last 3 request-response pairs
        keep_count = min(6, len(messages))
        older = messages[: len(messages) - keep_count]
        recent = messages[len(messages) - keep_count :]

        if not older:
            return messages

        # Serialize older messages for summarization
        older_text = ModelMessagesTypeAdapter.dump_json(older).decode()

        model = self.config.summarization_model or self.deps.model_name
        summarizer: Agent[None, str] = Agent(
            model,
            system_prompt=(
                "You are a conversation summarizer. Given a JSON-serialized conversation history, "
                "produce a concise summary that preserves: key decisions made, files created/modified, "
                "current task status, and any important context. Be factual and brief."
            ),
        )

        summary_result = await summarizer.run(
            f"Summarize this conversation history:\n\n{older_text[:50_000]}"
        )

        summary_msg = ModelRequest(
            parts=[
                UserPromptPart(
                    content=(
                        f"[Context summary — full history saved to {backup_path}]\n\n"
                        f"{summary_result.output}"
                    ),
                )
            ],
        )

        return [summary_msg] + list(recent)

    async def maybe_compress(self, messages: list[ModelMessage]) -> list[ModelMessage]:
        """Apply compression tiers as needed based on current capacity."""
        if not self.config.auto_compress:
            return messages

        ratio = self._capacity_ratio(messages)

        # Always apply tier 1 (cheap, no LLM call)
        messages = self.offload_large_results(messages)

        if ratio >= self.config.tier2_capacity_ratio:
            messages = self.strip_write_args(messages)

        if ratio >= self.config.tier3_capacity_ratio:
            messages = await self.summarize(messages)

        return messages

    async def apply_tier(
        self, messages: list[ModelMessage], tier: int
    ) -> list[ModelMessage]:
        """Apply a specific tier of compression (for manual triggering)."""
        if tier >= 1:
            messages = self.offload_large_results(messages)
        if tier >= 2:
            messages = self.strip_write_args(messages)
        if tier >= 3:
            messages = await self.summarize(messages)
        return messages
