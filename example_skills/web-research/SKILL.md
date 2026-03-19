---
name: web-research
description: Structured approach to conducting thorough web research. Use when asked to research a topic, gather information, or produce a report requiring external knowledge.
license: MIT
---

# Web Research Skill

## When to Use

Activate this skill when the user asks you to:
- Research a topic or question
- Gather information from multiple angles
- Produce a report, briefing, or summary requiring broad knowledge
- Compare or contrast multiple subjects

## Workflow

### Step 1: Define the research scope

Before searching, write a plan using `write_todos`:
- What specific questions need answering?
- What perspectives or angles should be covered?
- What is the desired output format?

### Step 2: Gather information

For each research question:
1. Search for information using available tools
2. Write raw findings to a file (e.g. `research_raw_{topic}.md`)
3. Note the source/basis for each finding

### Step 3: Synthesise

1. Read back your raw findings files
2. Identify key themes, contradictions, and gaps
3. Write a structured synthesis to `research_synthesis.md`

### Step 4: Produce output

1. Transform the synthesis into the user's requested format
2. Include a "Key Findings" section at the top
3. Note any areas where information was limited or contradictory
4. Save final output to a well-named file

## Quality Checklist

- [ ] Multiple angles/perspectives covered
- [ ] Contradictions and limitations noted
- [ ] Sources and reasoning documented
- [ ] Output matches requested format
- [ ] Key findings highlighted at the top
