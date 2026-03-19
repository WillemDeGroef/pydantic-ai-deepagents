"""Filesystem tools — read_file, write_file, edit_file, list_files, grep_files."""

from __future__ import annotations

import fnmatch
import time

from pydantic_ai import RunContext

from pydantic_ai_deepagents.deps import DeepAgentDeps, FileEntry


async def read_file(
    ctx: RunContext[DeepAgentDeps],
    path: str,
) -> str:
    """Read the contents of a file from the virtual filesystem or workspace."""
    deps = ctx.deps

    if deps.use_disk():
        resolved = deps.resolve_path(path)
        if not resolved.exists():
            return f"Error: File not found: {path}"
        return resolved.read_text(encoding="utf-8")

    entry = deps.files.get(path)
    if entry is None:
        available = ", ".join(sorted(deps.files.keys())) if deps.files else "(none)"
        return f"Error: File not found: {path}\nAvailable files: {available}"
    return entry.content


async def write_file(
    ctx: RunContext[DeepAgentDeps],
    path: str,
    content: str,
) -> str:
    """Write content to a file in the virtual filesystem or workspace."""
    deps = ctx.deps

    if deps.use_disk():
        resolved = deps.resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"

    now = time.time()
    if path in deps.files:
        deps.files[path].content = content
        deps.files[path].updated_at = now
    else:
        deps.files[path] = FileEntry(content=content, created_at=now, updated_at=now)

    return f"Wrote {len(content)} chars to {path}"


async def edit_file(
    ctx: RunContext[DeepAgentDeps],
    path: str,
    old_string: str,
    new_string: str,
) -> str:
    """Replace the first occurrence of old_string with new_string in a file."""
    deps = ctx.deps

    if deps.use_disk():
        resolved = deps.resolve_path(path)
        if not resolved.exists():
            return f"Error: File not found: {path}"
        text = resolved.read_text(encoding="utf-8")
        if old_string not in text:
            return f"Error: old_string not found in {path}"
        text = text.replace(old_string, new_string, 1)
        resolved.write_text(text, encoding="utf-8")
        return f"Edited {path}"

    entry = deps.files.get(path)
    if entry is None:
        return f"Error: File not found: {path}"
    if old_string not in entry.content:
        return f"Error: old_string not found in {path}"
    entry.content = entry.content.replace(old_string, new_string, 1)
    entry.updated_at = time.time()
    return f"Edited {path}"


async def list_files(
    ctx: RunContext[DeepAgentDeps],
    pattern: str = "*",
) -> str:
    """List files matching a glob pattern."""
    deps = ctx.deps

    if deps.use_disk() and deps.workspace is not None:
        matches = sorted(
            str(p.relative_to(deps.workspace))
            for p in deps.workspace.rglob(pattern)
            if p.is_file()
        )
    else:
        matches = sorted(p for p in deps.files if fnmatch.fnmatch(p, pattern))

    if not matches:
        return "No files found."
    return "\n".join(matches)


async def grep_files(
    ctx: RunContext[DeepAgentDeps],
    search: str,
    pattern: str = "*",
) -> str:
    """Search for a string in files matching a glob pattern."""
    deps = ctx.deps
    results: list[str] = []

    if deps.use_disk() and deps.workspace is not None:
        for file_path in deps.workspace.rglob(pattern):
            if not file_path.is_file():
                continue
            try:
                text = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if search in line:
                    rel = str(file_path.relative_to(deps.workspace))
                    results.append(f"{rel}:{i}: {line}")
    else:
        for file_path, entry in sorted(deps.files.items()):
            if not fnmatch.fnmatch(file_path, pattern):
                continue
            for i, line in enumerate(entry.content.splitlines(), 1):
                if search in line:
                    results.append(f"{file_path}:{i}: {line}")

    if not results:
        return f"No matches for '{search}'."
    return "\n".join(results)
