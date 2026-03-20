__version__ = "0.1.0"

from pydantic_ai_deepagents.agent import create_deep_agent, create_managed_agent
from pydantic_ai_deepagents.context import ContextConfig, ContextManager
from pydantic_ai_deepagents.deps import DeepAgentDeps, Skill
from pydantic_ai_deepagents.run import ManagedAgent, run_with_context
from pydantic_ai_deepagents.skills import load_skill_from_text

__all__ = [
    "__version__",
    "ContextConfig",
    "ContextManager",
    "DeepAgentDeps",
    "ManagedAgent",
    "Skill",
    "create_deep_agent",
    "create_managed_agent",
    "load_skill_from_text",
    "run_with_context",
]
