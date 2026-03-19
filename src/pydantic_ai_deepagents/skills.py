"""
Skills manager — discovers and loads skills from directories.

Follows the Agent Skills specification (https://agentskills.io/specification):
  - Each skill is a directory containing a SKILL.md file
  - SKILL.md has YAML frontmatter (name, description) + markdown body
  - Supporting files (scripts/, references/, assets/) are loaded lazily

The loading pattern mirrors Deep Agents' SkillsMiddleware:
  1. Scan source directories for SKILL.md files
  2. Parse YAML frontmatter → extract name + description
  3. Inject compact listing into system prompt (discovery)
  4. Agent loads full instructions on-demand via read_skill tool (activation)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic_ai_deepagents.deps import Skill


# ── YAML frontmatter parser (minimal, no PyYAML dependency) ─────────────

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(.*?)\n---\s*\n(.*)",
    re.DOTALL,
)

_YAML_LINE_RE = re.compile(r"^(\w[\w\-]*):\s*(.+)$")


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """
    Parse a minimal YAML frontmatter block from a SKILL.md file.

    Returns (metadata_dict, markdown_body).
    Handles simple key: value pairs and quoted strings.
    For nested structures, install PyYAML and replace this.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        # No frontmatter — treat entire file as body
        return {}, text

    yaml_block = match.group(1)
    body = match.group(2)

    meta: dict[str, Any] = {}
    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _YAML_LINE_RE.match(line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            # Strip quotes
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            meta[key] = val

    return meta, body


# ── Skill loading ───────────────────────────────────────────────────────


def load_skill_from_directory(skill_dir: Path) -> Skill | None:
    """
    Load a single skill from a directory containing SKILL.md.

    Returns None if the directory doesn't contain a valid SKILL.md.
    """
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return None

    text = skill_file.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)

    name = meta.get("name", skill_dir.name)
    description = meta.get("description", "")

    if not name:
        return None

    # Load supporting resource files (non-recursive, common extensions)
    resources: dict[str, str] = {}
    resource_extensions = {".md", ".txt", ".py", ".sh", ".json", ".yaml", ".yml"}
    for child in skill_dir.iterdir():
        if child.name == "SKILL.md":
            continue
        if child.is_file() and child.suffix in resource_extensions:
            try:
                resources[child.name] = child.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
        elif child.is_dir() and child.name in ("scripts", "references", "assets"):
            # Load files from standard subdirectories
            for sub_file in child.iterdir():
                if sub_file.is_file() and sub_file.suffix in resource_extensions:
                    try:
                        rel = f"{child.name}/{sub_file.name}"
                        resources[rel] = sub_file.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue

    return Skill(
        name=name,
        description=description,
        instructions=body.strip(),
        source_path=str(skill_dir),
        license=meta.get("license"),
        metadata={
            k: v for k, v in meta.items() if k not in ("name", "description", "license")
        },
        resources=resources,
    )


def load_skill_from_text(name: str, text: str, source: str = "<inline>") -> Skill:
    """
    Load a skill from raw SKILL.md text content.

    Useful for in-memory skills or loading from URLs/databases.
    """
    meta, body = _parse_frontmatter(text)
    return Skill(
        name=meta.get("name", name),
        description=meta.get("description", ""),
        instructions=body.strip(),
        source_path=source,
        license=meta.get("license"),
        metadata={
            k: v for k, v in meta.items() if k not in ("name", "description", "license")
        },
    )


def discover_skills(
    sources: list[str | Path],
) -> dict[str, Skill]:
    """
    Discover and load skills from multiple source directories.

    Each source is a directory that contains skill subdirectories.
    Later sources override earlier ones (last-wins precedence),
    matching Deep Agents' layering behavior.

    Example layout:
        skills/
        ├── web-research/
        │   └── SKILL.md
        ├── code-review/
        │   ├── SKILL.md
        │   └── scripts/
        │       └── review.py
        └── data-analysis/
            ├── SKILL.md
            ├── scripts/
            │   └── analysis_template.py
            └── references/
                └── REFERENCE.md
    """
    skills: dict[str, Skill] = {}

    for source in sources:
        source_path = Path(source)
        if not source_path.is_dir():
            continue

        # Check if this directory itself is a skill (contains SKILL.md)
        if (source_path / "SKILL.md").exists():
            skill = load_skill_from_directory(source_path)
            if skill:
                skills[skill.name] = skill
            continue

        # Otherwise scan subdirectories for skills
        for child in sorted(source_path.iterdir()):
            if not child.is_dir():
                continue
            skill = load_skill_from_directory(child)
            if skill:
                skills[skill.name] = skill

    return skills


# ── System prompt injection ─────────────────────────────────────────────


def build_skills_prompt_section(skills: dict[str, Skill]) -> str:
    """
    Build the compact skills listing for the system prompt.

    This is the "discovery" phase — only name + description are shown.
    The agent must call `read_skill` to load full instructions.
    """
    if not skills:
        return ""

    lines = [
        "## Available Skills",
        "",
        "You have access to the following skills. Each skill provides "
        "specialised instructions for a specific task type. To use a skill, "
        "call `read_skill` with the skill name to load its full instructions, "
        "then follow them.",
        "",
    ]

    for name, skill in sorted(skills.items()):
        desc = skill.description or "(no description)"
        resource_count = len(skill.resources)
        extras = f" [{resource_count} resource files]" if resource_count else ""
        lines.append(f"- **{name}**: {desc}{extras}")

    lines.append("")
    lines.append(
        "When a user request matches a skill's description, activate it with "
        "`read_skill` before proceeding. You can combine multiple skills in "
        "a single task."
    )

    return "\n".join(lines)
