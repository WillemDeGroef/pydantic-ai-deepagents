"""Shell execution tool — execute."""

from __future__ import annotations

import asyncio

from pydantic_ai import RunContext

from pydantic_ai_deepagents.deps import DeepAgentDeps


async def execute(
    ctx: RunContext[DeepAgentDeps],
    command: str,
    timeout: int = 30,
) -> str:
    """
    Execute a shell command in the workspace directory.

    Only available when a workspace is configured. Commands are run with
    a timeout to prevent hanging.
    """
    deps = ctx.deps

    if deps.workspace is None:
        return "Error: No workspace configured. Shell execution requires a workspace."

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(deps.workspace),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        return f"Error: Command timed out after {timeout}s"

    output_parts: list[str] = []
    if stdout:
        output_parts.append(stdout.decode(errors="replace"))
    if stderr:
        output_parts.append(f"STDERR:\n{stderr.decode(errors='replace')}")
    if proc.returncode != 0:
        output_parts.append(f"Exit code: {proc.returncode}")

    return "\n".join(output_parts) if output_parts else "(no output)"
