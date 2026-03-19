"""
Skill tools — read_skill, list_skills, read_skill_resource.

These implement the "activation" and "execution" phases of
progressive skill disclosure:

  1. Discovery — skill names/descriptions injected into system prompt (automatic)
  2. Activation — `read_skill` loads full SKILL.md instructions on demand
  3. Execution — `read_skill_resource` loads supporting files as needed

This mirrors Deep Agents' SkillsMiddleware, where skills are lazy-loaded
to keep the context window lean. The agent sees a compact listing at startup
and only pulls in full instructions when it decides a skill is relevant.
"""

from __future__ import annotations

from pydantic_ai import RunContext

from pydantic_ai_deepagents.deps import DeepAgentDeps


async def read_skill(
    ctx: RunContext[DeepAgentDeps],
    skill_name: str,
) -> str:
    """
    Load the full instructions for a skill.

    Call this when a user request matches a skill's description. The skill's
    complete SKILL.md instructions will be returned so you can follow them.

    Available skills are listed in your system prompt. Use `list_skills` to
    see the full list with descriptions.
    """
    deps = ctx.deps
    skill = deps.skills.get(skill_name)
    if skill is None:
        available = ", ".join(sorted(deps.skills.keys())) if deps.skills else "(none)"
        return (
            f"Error: Skill '{skill_name}' not found.\n"
            f"Available skills: {available}\n\n"
            "Use `list_skills` to see descriptions."
        )

    parts = [
        f"# Skill: {skill.name}",
        "",
    ]
    if skill.description:
        parts.append(f"> {skill.description}")
        parts.append("")

    parts.append(skill.instructions)

    # List available resources the agent can load
    if skill.resources:
        parts.append("")
        parts.append("## Available Resource Files")
        parts.append("")
        parts.append("Use `read_skill_resource` to load any of these files:")
        for resource_name in sorted(skill.resources.keys()):
            content = skill.resources[resource_name]
            line_count = content.count("\n") + 1
            parts.append(f"  - `{resource_name}` ({line_count} lines)")

    return "\n".join(parts)


async def list_skills(
    ctx: RunContext[DeepAgentDeps],
) -> str:
    """
    List all available skills with their descriptions.

    Use this to see what skills are available before activating one with
    `read_skill`.
    """
    deps = ctx.deps

    if not deps.skills:
        return "No skills are currently loaded."

    lines = ["## Available Skills", ""]
    for name, skill in sorted(deps.skills.items()):
        desc = skill.description or "(no description)"
        resource_count = len(skill.resources)
        extras = []
        if resource_count:
            extras.append(f"{resource_count} resource files")
        if skill.license:
            extras.append(f"license: {skill.license}")
        extra_str = f" ({', '.join(extras)})" if extras else ""
        lines.append(f"- **{name}**: {desc}{extra_str}")

    lines.append(f"\nTotal: {len(deps.skills)} skills loaded")
    lines.append("\nCall `read_skill(skill_name)` to load full instructions.")
    return "\n".join(lines)


async def read_skill_resource(
    ctx: RunContext[DeepAgentDeps],
    skill_name: str,
    resource_name: str,
) -> str:
    """
    Load a supporting resource file from a skill's directory.

    Skills can bundle scripts, reference documents, templates, and other
    files. Use `read_skill` first to see which resources are available,
    then call this to load a specific one.

    Args:
        skill_name: Name of the skill that owns the resource.
        resource_name: Filename or relative path of the resource
                       (e.g. "helper.py", "scripts/extract.py",
                       "references/REFERENCE.md").
    """
    deps = ctx.deps
    skill = deps.skills.get(skill_name)
    if skill is None:
        return f"Error: Skill '{skill_name}' not found."

    content = skill.resources.get(resource_name)
    if content is None:
        available = (
            ", ".join(sorted(skill.resources.keys())) if skill.resources else "(none)"
        )
        return (
            f"Error: Resource '{resource_name}' not found in skill '{skill_name}'.\n"
            f"Available resources: {available}"
        )

    # Return with line numbers
    numbered = []
    for i, line in enumerate(content.splitlines(), 1):
        numbered.append(f"  {i}\t{line}")

    header = f"## {skill_name} / {resource_name}\n"
    return header + "\n".join(numbered)
