"""System prompt builder for the deep agent."""

from __future__ import annotations


def build_system_prompt(custom: str = "", skills_section: str = "") -> str:
    """Build the full system prompt from custom instructions and skills listing."""
    parts: list[str] = []

    if custom:
        parts.append(custom)

    if skills_section:
        parts.append(skills_section)

    return "\n\n".join(parts) if parts else ""
