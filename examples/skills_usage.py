"""
Example: Using skills with the deep agent.

Demonstrates all three ways to load skills:
  1. From disk directories (production pattern)
  2. Inline Skill objects (testing / programmatic)
  3. From raw SKILL.md text (loading from URLs / databases)

Also shows how the progressive disclosure flow works:
  - At startup: only skill names + descriptions go into system prompt
  - At runtime: agent calls read_skill() to load full instructions
  - During execution: agent calls read_skill_resource() for supporting files
"""

import asyncio
from pathlib import Path

from pydantic_ai_deepagents import create_deep_agent, Skill, load_skill_from_text


async def main():
    # ── Option 1: Load skills from disk ──────────────────────────────────
    # This is the standard production pattern. Point at one or more
    # directories containing skill subdirectories.

    skills_dir = Path(__file__).parent.parent / "example_skills"

    agent, deps = create_deep_agent(
        system_prompt="You are an expert analyst and developer.",
        skills=[skills_dir],
    )

    print("=" * 60)
    print("SKILLS LOADED FROM DISK:")
    print("=" * 60)
    for name, skill in sorted(deps.skills.items()):
        print(f"  {name}: {skill.description[:60]}...")
        if skill.resources:
            for res in sorted(skill.resources):
                print(f"    └── {res}")
    print()

    # ── Option 2: Inline Skill objects ───────────────────────────────────
    # Useful for testing or when skills are generated programmatically.

    inline_skill = Skill(
        name="email-drafting",
        description="Draft professional emails. Use when asked to write, "
        "reply to, or improve an email.",
        instructions="""
# Email Drafting Skill

## Workflow
1. Identify the purpose (request, follow-up, announcement, etc.)
2. Determine the tone (formal, friendly, urgent)
3. Draft the email with: clear subject line, concise body, specific CTA
4. Save to `email_draft.md`

## Structure
- **Subject line**: < 50 characters, specific and actionable
- **Opening**: 1 sentence establishing context
- **Body**: 2-3 short paragraphs max
- **Closing**: Clear next step or call to action
- **Sign-off**: Match the tone
""",
        source_path="<inline>",
    )

    agent2, deps2 = create_deep_agent(
        system_prompt="You are an executive assistant.",
        inline_skills=[inline_skill],
    )

    print("INLINE SKILL LOADED:")
    print(f"  {inline_skill.name}: {inline_skill.description[:60]}...")
    print()

    # ── Option 3: Load from raw text ─────────────────────────────────────
    # Useful when loading skills from a URL, database, or API.

    raw_skill_md = """\
---
name: meeting-notes
description: Structure and summarise meeting notes. Use when asked to process, clean up, or summarise meeting notes or transcripts.
license: MIT
---

# Meeting Notes Skill

## Workflow
1. Read the raw notes / transcript
2. Extract: attendees, date, key decisions, action items, open questions
3. Write structured notes to `meeting_notes_structured.md`

## Output Format

### Meeting: (title)
**Date:** (date) | **Attendees:** (list)

#### Decisions Made
- (decision 1)
- (decision 2)

#### Action Items
| Owner | Action | Due |
|-------|--------|-----|
| Name  | Task   | Date|

#### Open Questions
- (question 1)
"""

    text_skill = load_skill_from_text("meeting-notes", raw_skill_md, source="<example>")

    agent3, deps3 = create_deep_agent(
        system_prompt="You are a project coordinator.",
        inline_skills=[text_skill],
    )

    print("TEXT-LOADED SKILL:")
    print(f"  {text_skill.name}: {text_skill.description[:60]}...")
    print()

    # ── Option 4: Combine all sources ────────────────────────────────────
    # Later sources override earlier ones (last-wins), and inline_skills
    # override disk-discovered skills.

    agent4, deps4 = create_deep_agent(
        system_prompt="You are a versatile assistant with many skills.",
        skills=[skills_dir],
        inline_skills=[inline_skill, text_skill],
    )

    print("COMBINED SKILLS (disk + inline):")
    for name in sorted(deps4.skills):
        src = deps4.skills[name].source_path
        print(f"  {name} (from {src})")
    print()

    # ── Show what the system prompt looks like ───────────────────────────
    # The agent's system prompt contains a compact listing of skills.
    # Let's inspect it.

    from pydantic_ai_deepagents.skills import build_skills_prompt_section

    section = build_skills_prompt_section(deps4.skills)
    print("=" * 60)
    print("SKILLS SECTION IN SYSTEM PROMPT:")
    print("=" * 60)
    print(section)

    # ── Simulate what the agent does ─────────────────────────────────────
    # When the agent sees a request matching a skill, it:
    #   1. Calls read_skill("skill-name") → gets full instructions
    #   2. Follows the instructions
    #   3. Optionally calls read_skill_resource() for supporting files

    print("\n" + "=" * 60)
    print("SIMULATED SKILL ACTIVATION (read_skill):")
    print("=" * 60)
    from unittest.mock import MagicMock

    mock_ctx = MagicMock()
    mock_ctx.deps = deps4

    from pydantic_ai_deepagents.tools.skills import read_skill, read_skill_resource

    result = await read_skill(mock_ctx, "code-review")
    print(result[:500] + "\n...")

    print("\n" + "=" * 60)
    print("SIMULATED RESOURCE LOAD (read_skill_resource):")
    print("=" * 60)

    result = await read_skill_resource(mock_ctx, "code-review", "references/REVIEW_TEMPLATE.md")
    print(result[:500] + "\n...")


if __name__ == "__main__":
    asyncio.run(main())
