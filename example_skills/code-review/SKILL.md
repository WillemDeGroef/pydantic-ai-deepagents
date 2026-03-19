---
name: code-review
description: Systematic code review process. Use when asked to review code, find bugs, suggest improvements, or assess code quality.
license: MIT
---

# Code Review Skill

## When to Use

Activate this skill when the user asks you to:
- Review code for bugs, security issues, or quality
- Suggest improvements to existing code
- Assess whether code follows best practices
- Prepare a code review report

## Workflow

### Step 1: Understand the context

1. Read the code files using `read_file` or `list_files`
2. Identify the language, framework, and purpose
3. Create a plan with `write_todos` listing files to review

### Step 2: Multi-pass review

Perform the review in passes, writing findings to `review_findings.md`:

**Pass 1 — Correctness**
- Logic errors and edge cases
- Off-by-one errors
- Null/undefined handling
- Error handling completeness
- Race conditions (concurrent code)

**Pass 2 — Security**
- Input validation and sanitisation
- Authentication and authorisation gaps
- Injection vulnerabilities (SQL, XSS, command)
- Secrets or credentials in code
- Dependency vulnerabilities (known patterns)

**Pass 3 — Maintainability**
- Naming clarity and consistency
- Function/method length and complexity
- DRY violations (duplicated logic)
- Missing or misleading comments
- Test coverage gaps

**Pass 4 — Performance**
- Unnecessary allocations or copies
- N+1 query patterns
- Missing caching opportunities
- Algorithmic complexity concerns

### Step 3: Prioritise and report

1. Read back `review_findings.md`
2. Categorise each finding: 🔴 Critical, 🟡 Warning, 🔵 Suggestion
3. Write the final report to `code_review_report.md` using the template
   in `references/REVIEW_TEMPLATE.md`

## Guidelines

- Be specific: reference file names, line numbers, and exact code
- Suggest concrete fixes, not just problems
- Acknowledge what the code does well
- Prioritise findings by impact
